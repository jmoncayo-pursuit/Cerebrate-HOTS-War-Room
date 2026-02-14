import os
import time
import json
from datetime import datetime
from api.logger import ColoredLogger
from api.services.replay_parser import parse_replay
from api.services.database import DatabaseManager
from api.services.quota_manager import QuotaManager
from agents.hooks_manager import HooksManager, HookResponse
from agents.hooks import context_injector_hook, summary_validator_hook, cache_manager_hook, store_in_cache

class ReplayService:
    def __init__(self):
        self.db = DatabaseManager()
        self.quota = QuotaManager()
        self._intel_service = None  # Lazy-loaded
        self.hooks = self._init_hooks()  # Initialize hooks system
    
    def _init_hooks(self):
        """Initialize hooks manager with default hooks"""
        hooks = HooksManager()
        
        # Register BeforeAnalysis hooks
        hooks.register_hook('BeforeAnalysis', 'cache_manager', cache_manager_hook, enabled=True)
        hooks.register_hook('BeforeAnalysis', 'context_injector', context_injector_hook, enabled=True)
        
        # Register AfterAnalysis hooks
        hooks.register_hook('AfterAnalysis', 'summary_validator', summary_validator_hook, 
                          enabled=True, max_retries=3)
        
        return hooks
    
    def clean_text(self, text):
        """Clean up formatting issues in AI-generated text."""
        if not isinstance(text, str):
            return text
        
        import re
        
        # 1. Flow period into previous word: "match ." -> "match."
        text = re.sub(r'\s+([.;])(?!\w)', r'\1', text)
        
        # 2. Join trailing period on new line to previous line: "match\n." -> "match."
        # This specifically addresses the "stray periods on their own lines" issue
        text = re.sub(r'(\w)\s*\n\s*([.;])', r'\1\2', text)
        
        # 3. Join lines that don't end in punctuation (if the next line starts with lowercase)
        # This fixes "broken sentences" split across multiple lines
        text = re.sub(r'([^.;!?\n])\n([a-z])', r'\1 \2', text)
        
        # 4. Collapse multiple spaces (but preserve newlines)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 5. Fix periods/semicolons followed by spaces then newline
        text = re.sub(r'([.;])\s+\n', r'\1\n', text)
        
        # 6. Handle escaped quotes and double-escaped newlines
        text = text.replace("\\'", "'")
        text = text.replace('\\\\n', '\n')
        
        # 7. Normalize paragraph breaks (max 2 newlines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _parse_json_response(self, text):
        """Extract and parse JSON from AI response text."""
        if not text:
            return None
        
        # Strip markdown blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(text)
        except Exception as e:
            ColoredLogger.error(f"JSON Parse Error: {e}", "REPLAY")
            # Fallback: try to find anything that looks like JSON
            try:
                start = text.find('{')
                end = text.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(text[start:end])
            except:
                pass
            return None

    def _get_intel_service(self):
        """Lazy-load IntelligenceService to avoid circular imports."""
        if self._intel_service is None:
            from api.services.intelligence_service import IntelligenceService
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key:
                self._intel_service = IntelligenceService(self.db, api_key)
        return self._intel_service

    def process_replay_file(self, replay_file):
        """Handle file upload, validation, parsing, and database storage."""
        filename = replay_file.filename
        
        # 1. Validation Filters
        if not filename.endswith('.StormReplay'):
             return {'error': 'Invalid file type'}, 400

        fname_low = filename.lower().replace(' ', '')
        # Blacklist check
        non_sl_maps = [
            'lostcavern', 'silvercity', 'industrialdistrict', 'braxisoutpost',
            'checkpoint', 'pullparty', 'poolparty', 'escapefrombraxis', 
            'deadmansstand', 'sandbox', 'tryme', 'blackheartsrevenge', 
            'hauntedmines', 'tutorial', 'hallowsend', 'snowbrawl'
        ]
        if any(m in fname_low for m in non_sl_maps):
            return {'error': 'Non-competitive map ignored'}, 400
        
        if 'hanamura' in fname_low and 'temple' not in fname_low:
             return {'error': 'Non-standard Hanamura maps are blacklisted'}, 400

        # 2. Quota Check
        if not self.quota.can_process_replay():
            return {'error': 'Daily quota exceeded', 'status': 'quota_exceeded'}, 429

        # 3. Temp Save & Parse
        temp_path = os.path.join("/tmp", filename)
        try:
            replay_file.save(temp_path)
            
            # Parse
            result = parse_replay(temp_path)
            if not result or result.get('status') == 'error':
                 os.remove(temp_path)
                 return {'error': result.get('message', 'Parsing failed'), 'traceback': result.get('traceback')}, 500
            
            if result.get('status') == 'rejected':
                 os.remove(temp_path)
                 return {'error': result.get('message')}, 400

            # 4. Database Ingestion
            db_data = {
                'id': result['match_id'],
                'map': result['map'],
                'hero': result['hero'],
                'result': result['result'].upper(), # WIN/LOSS
                'date': result['timestamp_iso'],
                'duration': result['game_length'],
                'players': result['players'],
                'advanced_stats': result.get('advanced_stats', {})
            }
            
            # Upsert
            success = self.db.upsert_match(db_data)
            
            # 5. ANALYSIS - Always generate full context (Forensic + Social)
            analysis_result = None
            if success and self.quota.can_make_request():
                try:
                    # analyze_match(force=True) triggers both Forensic Audit and Social Insights
                    analysis_result = self.analyze_match(result['match_id'], force=True)
                except Exception as e:
                    ColoredLogger.warn(f"Analysis generation failed: {e}", "REPLAY")

            
            os.remove(temp_path)
            return {
                'success': success, 
                'match_id': result['match_id'], 
                'hero': result['hero'], 
                'map': result['map'],
                'analysis_status': 'complete' if analysis_result else 'pending'
            }, 200

        except Exception as e:
            if os.path.exists(temp_path): os.remove(temp_path)
            ColoredLogger.error(f"Replay Service Error: {e}", "REPLAY")
            return {'error': str(e)}, 500

    def fmt_ms(self, s): 
        """Format seconds to MM:SS."""
        if s is None: return "0:00"
        return f"{int(s//60)}:{int(s%60):02d}"

    def _generate_match_summary(self, match_data, max_retries=3, force=False):
        """Generate a clinical forensic AI summary for a match (Mode B: FORENSIC AUDIT).
        
        Args:
            match_data: Match data dictionary
            max_retries: Maximum retry attempts if validation fails
        
        Returns:
            dict: Analysis summary or None if failed
        """
        intel_service = self._get_intel_service()
        # print "DEBUG: Entered _generate_match_summary. Intel Service: %s" % intel_service
        print(f"DEBUG: Entered _generate_match_summary. Intel Service: {intel_service}")

        if not intel_service:
            return None
        
        map_name = match_data.get('map', 'Unknown')
        hero = match_data.get('hero', 'Unknown')
        result = match_data.get('result', 'UNKNOWN')
        duration = match_data.get('duration', 'Unknown')
        game_length = match_data.get('game_length', 0)
        
        players = match_data.get('players', [])
        advanced = match_data.get('raw_stats', {})
        
        if not intel_service.model:
            return None

        # 1. Forensic Extraction: Identify User & Teams
        print(f"DEBUG: Analyzing match with {len(players)} players.")
        user_player = next((p for p in players if p.get('name') == 'Discerning' or p.get('name') == 'CerebrateUser'), None)
        if not user_player:
            print("DEBUG: User not found by name. Falling back to hero.")
            # Fallback to hero match if name not found
            for p in players:
                if p.get('hero') == hero:
                    user_player = p
                    break
        
        if not user_player:
            print("DEBUG: User not found by hero either.")
            return None
        print(f"DEBUG: User identified as {user_player.get('name')} ({user_player.get('hero')})")
        
        team_0 = [p for p in players if p.get('team') == 0]
        team_1 = [p for p in players if p.get('team') == 1]
        
        user_team = team_0 if user_player['team'] == 0 else team_1
        enemy_team = team_1 if user_player['team'] == 0 else team_0
        
        # 2. Team Performance Markers
        def sum_stat(team, key): return sum((p.get('stats', {}).get(key, 0) for p in team))
        
        team_stats = {
            "own": {
                "kills": sum_stat(user_team, 'SoloKill'),
                "deaths": sum_stat(user_team, 'Deaths'),
                "herodamage": sum_stat(user_team, 'HeroDamage'),
                "siegedamage": sum_stat(user_team, 'SiegeDamage'),
                "experiencecontribution": sum_stat(user_team, 'ExperienceContribution')
            },
            "enemy": {
                "kills": sum_stat(enemy_team, 'SoloKill'),
                "deaths": sum_stat(enemy_team, 'Deaths'),
                "herodamage": sum_stat(enemy_team, 'HeroDamage'),
                "siegedamage": sum_stat(enemy_team, 'SiegeDamage'),
                "experiencecontribution": sum_stat(enemy_team, 'ExperienceContribution')
            }
        }
        
        # 3. User Contribution %
        user_core_stats = user_player.get('stats', {})
        contribution = {}
        for k in ['HeroDamage', 'SiegeDamage', 'ExperienceContribution', 'SoloKill']:
            team_val = team_stats['own'][k.lower() if k != 'SoloKill' else 'kills']
            contribution[k] = round((user_core_stats.get(k, 0) / team_val * 100), 1) if team_val > 0 else 0

        # Rich Stats for UI Cards
        kill_streak = user_core_stats.get('HighestKillStreak', 0)
        downtime = self.fmt_ms(user_core_stats.get('TimeSpentDead', 0))
        minion_xp = user_core_stats.get('MinionXP', 0)
        solo_kills = user_core_stats.get('SoloKill', 0)
        personal_mercs = user_core_stats.get('MercCampCaptures', 0)

        # 4. Forensic Timeline Correlation (Deaths vs Objectives)
        merc_events = advanced.get('merc_captures', [])
        boss_events = advanced.get('boss_captures', [])
        structure_events = advanced.get('structure_destructions', [])
        player_deaths = advanced.get('player_deaths', [])

        user_pid = None
        for i, p in enumerate(players):
            if p.get('name') == user_player['name']:
                user_pid = i + 1
                break

        user_kills_timeline = []
        user_deaths_timeline = []
        for d in player_deaths:
            ts = self.fmt_ms(d['timestamp'])
            victim_p = players[d['victim_pid'] - 1] if 0 < d['victim_pid'] <= len(players) else None
            killer_p = players[d['killer_pid'] - 1] if d['killer_pid'] and 0 < d['killer_pid'] <= len(players) else None
            
            if d['killer_pid'] == user_pid:
                user_kills_timeline.append(f"{ts}: Killed {victim_p['hero'] if victim_p else 'Unknown'}")
            if d['victim_pid'] == user_pid:
                user_deaths_timeline.append(f"{ts}: Killed by {killer_p['hero'] if killer_p else 'Unknown'}")

        # 5. Disconnects & Telemetry
        teammate_enemy_dcs = []
        user_dc_event = None
        DC_GRACE_PERIOD = 60
        
        for p in players:
            if p.get('disconnected'):
                ts = p.get('dc_timestamp', 0)
                if ts < game_length - DC_GRACE_PERIOD:
                    time_str = self.fmt_ms(ts)
                    if p['name'] == user_player['name']:
                        user_dc_event = f"COMMANDER TACTICAL DISCONNECT at {time_str}"
                    else:
                        teammate_enemy_dcs.append(f"{p['name']} ({p['hero']}) at {time_str}")
        
        team_merc_count = len([m for m in merc_events if m.get('captured_by_team') == user_player['team']])
        enemy_merc_count = len([m for m in merc_events if m.get('captured_by_team') != user_player['team']])

        # 6. Kill Verification Alert
        solo_kills = user_core_stats.get('SoloKill', 0)
        logs_found = len(user_kills_timeline)
        forensic_alert = ""
        if solo_kills > logs_found:
            forensic_alert = f"""
**FORENSIC ALERT (KILL MISMATCH):**
- Scoreboard reports {solo_kills} kills, but only {logs_found} events were found in the raw log.
- REASON: Likely 'Ghost Deaths' (Tyrael Trait, Leoric, or Uther) where the final blow is system-attributed.
- INSTRUCTION: You MUST account for these {solo_kills - logs_found} missing kills in your summary and 'Your Kills' list. Label them based on context (e.g. 'Inferred via Scoreboard' or 'Teamfight Cleanup').
"""

        # 7. Strategic Audit Prompt (Forensic Persona)
        ColoredLogger.info(f"Generating audit with {len(players)} players, {len(user_kills_timeline)} kills found.", "REPLAY")
        prompt = f"""## Mode B: STRATEGIC FORENSIC AUDIT
You are the Cerebrate Strategic Analyst. Perform a clinical audit with high tactical energy. 
Focus on **FORCE MULTIPLIERS** and **STRATEGIC GAPS**.

**GOLD STANDARD EXAMPLE (FOR FORMAT & TONE):**
```json
{{
    "verdict": "WIN", 
    "summary": "**APEX PREDATOR (BLOOD MONK)**. You didn't just play healer; you were the lobby's **Top Fragger**. Securing **8 Solo Kills** as Kharazim is a statistical anomaly that utterly breaks standard match prediction models. You effectively operated as a third assassin while maintaining support duties.", 
    "key_insights": {{ "kill_streak": "8 Solo Kills (Lobby High)", "mercenary_camps": 10, "downtime": "1:05", "minion_xp": 22040, "contribution_index": "Top Fragger" }},
    "areas_for_improvement": [
        {{ "title": "Deaths", "items": [{{ "time": "18:34", "killer": "Zeratul", "context": "DeuceGenius" }}] }},
        {{ "title": "Your Kills", "items": [{{ "time": "08:51", "victim": "Anduin", "context": "lbran1" }}, {{ "time": "SUMMARY", "victim": "Stats", "context": "8 Total Solo Kills (Verify against Scoreboard)" }}] }}
    ],
    "critical_mistake": "The ONE specific mistake that shifted the momentum.",
    "win_condition": "Actionable advice on how to carry harder next time."
}}
```

**COMMANDER PERFORMANCE DATA (TRUTH SCALE):**
- Map: {map_name}
- Hero: {hero}
- Result: {result}
- Game Duration: {duration}
- Solo Kills: {solo_kills} (Lobby Impact)
- Kill Streak: {kill_streak}
- Mercenary Captures: {personal_mercs} personal / {team_merc_count} team
- Minion XP Contribution: {minion_xp} (Lane Presence)
- Downtime: {downtime} (Time Dead)
{f"- CRITICAL: {user_dc_event}" if user_dc_event else ""}

{forensic_alert}

**KILL/DEATH TIMELINE (RAW DATA):**
- YOUR KILLS: {", ".join(user_kills_timeline) if user_kills_timeline else "None recorded"}
- YOUR DEATHS: {", ".join(user_deaths_timeline) if user_deaths_timeline else "Zero Deaths (Pure Efficiency)"}

**DRAFT COMPOSITION & SEQUENCE:**
- Team Allies: {", ".join([f"{p['hero']} ({p['name']})" for p in [{"hero": p['hero'], "name": p['name']} for p in user_team]])}
- Team Enemies: {", ".join([f"{p['hero']} ({p['name']})" for p in [{"hero": p['hero'], "name": p['name']} for p in enemy_team]])}

**TEAM COMPARISON:**
- Your Team: {team_stats['own']['kills']} Kills, {team_stats['own']['deaths']} Deaths.
- Enemy Team: {team_stats['enemy']['kills']} Kills, {team_stats['enemy']['deaths']} Deaths.
- User Contribution: {contribution['HeroDamage']}% Hero Dmg, {contribution['SiegeDamage']}% Siege, {contribution['ExperienceContribution']}% XP.

**USER TALENT TIMELINE:**
{json.dumps(user_player.get('talents', []), indent=2)}

**CORE OPERATIONAL PHILOSOPHY:**
1. **The Forensic Persona**: You are an elite tactical advisor. Your tone is sharp, analytical, and impressed by high-skill anomalies. 
2. **Data Isolation**: Only use provided numbers. If there is a KILL MISMATCH (see above), use the Scoreboard count as the primary truth.
3. **No Hallucinations**: Do not mention heroes or locations that are not in the provided RAW DATA.

**OUTPUT SCHEMA (STRICT JSON ONLY):**
```json
{{
    "verdict": "WIN" or "LOSS" or "DRAFT LOSS",
    "summary": "3-5 high-impact sentences using SPECIFIC NUMBERS. Analyze WHY the result happened.",
    "key_insights": {{
        "kill_streak": "{kill_streak}",
        "mercenary_camps": {personal_mercs},
        "downtime": "{downtime}",
        "minion_xp": {minion_xp},
        "contribution_index": "{contribution['HeroDamage']}% Dmg / {contribution['ExperienceContribution']}% XP"
    }},
    "areas_for_improvement": [
        {{ 
            "title": "Deaths", 
            "items": [
                {{ "time": "MM:SS", "killer": "HeroName", "context": "Name of the player" }}
            ] 
        }},
        {{ 
            "title": "Your Kills", 
            "items": [
                {{ "time": "MM:SS", "victim": "HeroName", "context": "Name of the player" }},
                {{ "time": "SUMMARY", "victim": "Stats", "context": "{solo_kills} Solo Kills / {user_core_stats.get('Assists', 0)} Assists" }}
            ] 
        }}
    ],
    "critical_mistake": "The ONE specific mistake that shifted the momentum.",
    "win_condition": "Actionable advice on how to carry harder next time."
}}
```
Do not include any text before or after the JSON block.
"""

        # Execute BeforeAnalysis hooks
        hook_data = {
            'match_data': match_data,
            'db_manager': self.db,
            'force': force
        }
        before_response = self.hooks.execute_hooks('BeforeAnalysis', hook_data)
        
        # Check if cache hit
        if before_response.decision == HookResponse.SKIP:
            ColoredLogger.success("Using cached analysis", "HOOKS")
            return before_response.cached_result
        
        # Use modified data if hooks changed it
        if before_response.decision == HookResponse.MODIFY:
            hook_data = before_response.modified_data
            match_data = hook_data.get('match_data', match_data)
        
        # Store cache key for later
        cache_key = hook_data.get('_cache_key')
        
        # Retry loop for quality validation
        for attempt in range(max_retries):
            try:
                try:
                    response = intel_service.model.generate_content([prompt])
                except Exception as gen_e:
                    print(f"DEBUG: generate_content FAILED: {gen_e}")
                    raise gen_e
                res_text = response.text.strip()
                ColoredLogger.info(f"FORENSIC AUDIT GENERATED for {hero} on {map_name} (attempt {attempt + 1}/{max_retries})", "REPLAY")
                
                try:
                    analysis = self._parse_json_response(res_text)
                    if not analysis:
                        raise ValueError("Failed to parse analysis JSON")
                    
                    for key, value in analysis.items():
                        if isinstance(value, str):
                            analysis[key] = self.clean_text(value)
                        elif isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                if isinstance(subvalue, str):
                                    value[subkey] = self.clean_text(subvalue)
                        elif isinstance(value, list):
                            for i, item in enumerate(value):
                                if isinstance(item, str):
                                    value[i] = self.clean_text(item)
                                elif isinstance(item, dict):
                                    for subkey, subvalue in item.items():
                                        if isinstance(subvalue, str):
                                            item[subkey] = self.clean_text(subvalue)
                except Exception as json_e:
                    print(f"DEBUG: FAILED TO PARSE JSON. RAW TEXT: {res_text}")
                    raise json_e
                
                # Execute AfterAnalysis hooks
                after_hook_data = {
                    'summary': analysis,
                    'match_data': match_data
                }
                after_response = self.hooks.execute_hooks('AfterAnalysis', after_hook_data)
                
                if after_response.decision == HookResponse.DENY:
                    if attempt < max_retries - 1:
                        ColoredLogger.warn(
                            f"Validation failed (attempt {attempt + 1}/{max_retries}): {after_response.reason}",
                            "HOOKS"
                        )
                        # Add feedback to prompt for next attempt
                        prompt += f"\n\nPREVIOUS ATTEMPT FAILED VALIDATION:\n{after_response.reason}\n\nPlease correct these issues in your response."
                        continue
                    else:
                        ColoredLogger.error(
                            f"Validation failed after {max_retries} attempts: {after_response.reason}",
                            "HOOKS"
                        )
                        # Return anyway but log the failure
                        result = {'success': True, 'analysis': analysis, 'validation_failed': True}
                        if cache_key:
                            store_in_cache(cache_key, result)
                        return result
                
                # Validation passed
                result = {'success': True, 'analysis': analysis}
                
                # Store in cache if we have a cache key
                if cache_key:
                    store_in_cache(cache_key, result)
                
                return result
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                if attempt < max_retries - 1:
                    ColoredLogger.warn(f"Attempt {attempt + 1} failed: {e}, retrying...", "REPLAY")
                    continue
                else:
                    ColoredLogger.warn(f"Forensic Audit parse error after {max_retries} attempts: {e}", "REPLAY")
                    return None

    def _generate_social_insights(self, match_data, dcs=None):
        """Generates a separate layer of social intelligence (rivalries, DCs, teammate synergy)."""
        intel_service = self._get_intel_service()
        
        players = match_data.get('players', [])
        user_player = next((p for p in players if 'Discerning' in p['name']), players[0])
        
        # 1. Social Context
        social_intel = self.db.get_kv('player_interactions') or {}
        user_briefings = {p['name']: social_intel[p['name']].get('aiStrategy') 
                         for p in players if p['name'] in social_intel}
        
        prompt = f"""## SOCIAL INSIGHTS ENGINE
Analyze the 'Neural Network' of this match. Focus on Human Factors.

**PERSONNEL:**
{json.dumps([{ 'name': p['name'], 'hero': p['hero'], 'team': p['team'], 'deaths': p.get('stats', {}).get('Deaths', 0) } for p in players], indent=2)}

**ESTABLISHED NEURAL LINKS (Your Notes):**
{json.dumps(user_briefings, indent=2)}

**TEAMMATE/ENEMY DISCONNECTS:**
{", ".join(dcs) if dcs else "None"}

**REQUIREMENTS:**
1. **Highlight Rivalries**: Identify if a specific enemy neutralized the user multiple times.
2. **Teammate Synergy**: Note if an ally performance was notably high or low.
3. **Neural Briefing Correlation**: Did players in your notes live up to their reputation?
4. **Tone**: Forensic but 'notable' (highlight interesting human patterns).
5. **Instruction**: If you are commenting on a teammate performance as a 'failure' or 'asset', be specific about their stats relative to the user.

**OUTPUT SCHEMA (JSON ONLY):**
{{
    "social_summary": "1-2 sentence overview of the human factors.",
    "notable_nodes": [
        {{ "name": "PlayerName", "note": "Data-backed observation (e.g. 'Consistent synergy' or 'Systemic Desync')." }}
    ],
    "rivalry_factor": "Analysis of specific enemy pressure.",
    "dc_impact": "How disconnects altered player psychology/strategy."
}}
"""
        try:
            response = intel_service.model.generate_content([prompt])
            res_text = response.text.strip()
            social = self._parse_json_response(res_text)
            if not social:
                return None
            
            # Clean text in social insights
            for key, value in social.items():
                if isinstance(value, str):
                    social[key] = self.clean_text(value)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, str):
                            value[i] = self.clean_text(item)
                        elif isinstance(item, dict):
                            for subkey, subvalue in item.items():
                                if isinstance(subvalue, str):
                                    item[subkey] = self.clean_text(subvalue)
            return social
        except:
            return None

    def get_match_history(self, limit=50, include_details=False, search=None):
        return self.db.get_matches(limit=limit, include_details=include_details, search=search)

    def analyze_match(self, match_id, force=False):
        """Forces or performs AI analysis on a match."""
        match_data_rows = self.db.get_matches(match_id=match_id, include_players=True)
        if not match_data_rows or len(match_data_rows) == 0:
            return {"status": "error", "message": "Match not found"}
        match_data = match_data_rows[0]
        
        # 1. Quota Check
        if not force and not self.quota.can_make_request():
            return {"status": "quota_exceeded", "match_id": match_id}

        # 2. Check if already analyzed
        if not force and match_data.get('analysis') and match_data['analysis'] != {}:
            return {"status": "complete", "match_id": match_id, "analysis": match_data['analysis']}

        # 3. Force Re-parse logic (Optional)
        # (Assuming handled by separate trigger or standard flow)

        # 4. RUN FORENSIC AUDIT (Main Verdict)
        summary = self._generate_match_summary(match_data, force=force)
        
        # 5. RUN SOCIAL INSIGHTS (Deep Social Network)
        players = match_data.get('players', [])
        game_length = match_data.get('game_length', 0)
        DC_GRACE_PERIOD = 60
        
        teammate_enemy_dcs = []
        for p in players:
            if p.get('disconnected'):
                ts = p.get('dc_timestamp', 0)
                if ts < game_length - DC_GRACE_PERIOD:
                    # Ignore the user in social tab (already in summary)
                    if not ('Discerning' in p.get('name', '') or p.get('hero') == match_data.get('hero')):
                        teammate_enemy_dcs.append(f"{p.get('name')} ({p.get('hero')}) at {self.fmt_ms(ts)}")
        
        social = self._generate_social_insights(match_data, dcs=teammate_enemy_dcs)
        
        if summary and summary.get('success'):
            results = summary['analysis']
            
            # --- 🕵️ NEURAL AUDIT: Match Summary ---
            try:
                from agents.cerebrate_orchestrator import CerebrateOrchestrator
                intel = self._get_intel_service()
                orchestrator = CerebrateOrchestrator(call_gemini_api_fn=intel.generate_chat_response)
                
                # Context for audit includes core stats
                audit_context = {
                    'target_query': f"Analyze match on {match_data.get('map')}",
                    'target_context': f"Result: {match_data.get('result')}, Hero: {match_data.get('hero')}. Stats: {json.dumps(results.get('key_insights', {}))}",
                    'target_response': results.get('summary', ''),
                    'audit_type': 'CHAT'
                }
                summary_audit = orchestrator.agents['auditor'].analyze(match_id, audit_context)
                if summary_audit.get('success'):
                    results['audit'] = summary_audit.get('audit')
            except Exception as audit_err:
                ColoredLogger.warn(f"Match Summary Audit Failed: {audit_err}", "REPLAY")

            if social:
                results['social_insights'] = social
                
                # --- 🕵️ NEURAL AUDIT: Social Insights ---
                try:
                    social_audit_context = {
                        'target_query': "Social Intelligence Extraction",
                        'target_context': json.dumps([{ 'name': p['name'], 'hero': p['hero'], 'team': p['team'] } for p in players]),
                        'target_response': social.get('social_summary', ''),
                        'audit_type': 'SOCIAL'
                    }
                    social_audit = orchestrator.agents['auditor'].analyze(match_id, social_audit_context)
                    if social_audit.get('success'):
                        results['social_insights']['audit'] = social_audit.get('audit')
                except Exception as s_audit_err:
                    ColoredLogger.warn(f"Social Audit Failed: {s_audit_err}", "REPLAY")

                # PERSIST SOCIAL NOTES to Database
                try:
                    for node in social.get('notable_nodes', []):
                        p_name = node.get('name')
                        p_note = node.get('note')
                        if p_name and p_note:
                            # Update notes in social_profiles if exists
                            conn = self.db._get_connection()
                            conn.execute("UPDATE social_profiles SET notes = ? WHERE player_name = ?", (p_note, p_name))
                            conn.commit()
                except Exception as db_e:
                    ColoredLogger.warn(f"Social Persistence error: {db_e}", "REPLAY")
            
            self.db.update_match_analysis(match_id, results)
            self.quota.record_request()
            return {"status": "complete", "match_id": match_id, "analysis": results}
        
        return {"status": "error", "match_id": match_id, "message": "Analysis generation failed"}

