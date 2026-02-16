import os
import time
import json
from pathlib import Path
from datetime import datetime
from api.logger import ColoredLogger
from api.services.replay_parser import parse_replay
from api.services.replay_parser.header import get_match_id
from api.services.database import DatabaseManager
from api.services.quota_manager import QuotaManager
from agents.hooks_manager import HooksManager, HookResponse
from agents.hooks import context_injector_hook, summary_validator_hook, cache_manager_hook, store_in_cache
from api.services.mechanical_analysis_service import MechanicalAnalysisService

class ReplayService:
    def __init__(self):
        self.db = DatabaseManager()
        self.quota = QuotaManager()
        self._intel_service = None  # Lazy-loaded
        self.hooks = self._init_hooks()  # Initialize hooks system
        self._replay_dir_cache = None

    def _find_replay_file(self, match_id):
        """Attempts to find the physical .StormReplay file for a given match_id."""
        if not self._replay_dir_cache:
            # Re-use discovery logic from replay_watcher
            home = Path.home()
            search_paths = [
                home / "Library/Application Support/Blizzard/Heroes of the Storm",
                home / "Documents/Heroes of the Storm",
            ]
            for base_path in search_paths:
                if base_path.exists():
                    for replay_dir in base_path.rglob("Replays/Multiplayer"):
                        if replay_dir.is_dir():
                            self._replay_dir_cache = replay_dir
                            break
                if self._replay_dir_cache: break
        
        if self._replay_dir_cache:
            # Scan the directory (this can be slow if there are thousands, but usually okay for deep analysis)
            for f in self._replay_dir_cache.glob("*.StormReplay"):
                if get_match_id(str(f)) == match_id:
                    return str(f)
        return None
    
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
                    analysis_result = self.analyze_match(result['match_id'], force=True, replay_path=temp_path)
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

    def _generate_match_summary(self, match_data, forensics=None, max_retries=3, force=False):
        """Generate a clinical forensic AI summary for a match (Mode B: FORENSIC AUDIT).
        
        Args:
            match_data: Match data dictionary
            forensics: Optional forensic analysis data (e.g. Stitches hooks)
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
        advanced = match_data.get('advanced_stats', {})
        
        if not intel_service.model:
            return None

        # --- DATA PREPARATION (STRICT VALIDATION) ---
        valid_hero_names = [p['hero'] for p in players]
        
        # Build Talent Tree for ALL players
        all_talents = {}
        for p in players:
             all_talents[p['hero']] = [t['talent_name'] for t in p.get('talents', [])]

        # Extract Forensics if available
        mech_stats = ""
        social_stats = ""
        tactical_timeline_data = ""
        if forensics:
             # Mechanics
             m_list = [f"{m['label']}: {m['value']}" for m in forensics.get('mechanics', [])]
             mech_stats = " | ".join(m_list)
             
             # Social Logic (Focus)
             soc = forensics.get('social_mechanics', {})
             focus = soc.get('most_targeted_enemy', 'None')
             social_stats = f"Most Targeted Enemy: {focus}"

             # Tactical Highlights (Timeline)
             highlights = forensics.get('tactical_highlights', [])
             h_lines = [f"[{h['time']}] {h['event']} (Victim: {h['victim']})" for h in highlights]
             tactical_timeline_data = "\n".join(h_lines)

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
        solo_kills = user_core_stats.get('SoloKill', 0)
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

        # Stitches Specific Context
        stitches_context = ""
        if 'Stitches' in hero:
             hooks_thrown = user_player.get('kv_stats', {}).get('HooksThrown', 
                            user_player.get('stats', {}).get('HooksThrown', 0))
             stitches_context = f"- STITCHES SPECIFIC: {hooks_thrown} Hooks Thrown (Note: Landed count unavailable, judge based on Takedowns)"

        # 4. Forensic Timeline Correlation (Deaths vs Objectives)
        merc_events = advanced.get('merc_captures', [])
        boss_events = advanced.get('boss_captures', [])
        structure_events = advanced.get('structure_destructions', [])
        player_deaths = advanced.get('player_deaths', [])

        user_pid = None
        for i, p in enumerate(players):
            if p.get('name') == user_player.get('name') and p.get('hero') == user_player.get('hero'):
                user_pid = i + 1
                break
        
        # Fallback to just hero match if name+hero match failed
        if not user_pid:
            for i, p in enumerate(players):
                if p.get('hero') == hero:
                    user_pid = i + 1
                    break

        user_kills_timeline = []
        user_deaths_timeline = []
        
        # Priority 1: Forensic Highlights (High Accuracy for Stitches)
        if forensics:
            highlights = forensics.get('tactical_highlights', [])
            for h in highlights:
                if h.get('type') == 'KILL' or (h.get('type') == 'HOOK' and h.get('lethal')):
                    user_kills_timeline.append(f"{h['time']}: Killed {h['victim']}")
            
            # Dedicated Death Highlights
            d_highlights = forensics.get('death_highlights', [])
            for dh in d_highlights:
                user_deaths_timeline.append(f"{dh['time']}: Killed by {dh.get('killer', 'Enemy')}")

        # Priority 2: Raw Death Events (Fallback/Support)
        for d in player_deaths:
            ts = self.fmt_ms(d['timestamp'])
            
            victim_p = players[d['victim_pid'] - 1] if 0 < d['victim_pid'] <= len(players) else None
            killer_p = players[d['killer_pid'] - 1] if d['killer_pid'] and 0 < d['killer_pid'] <= len(players) else None
            
            if d['killer_pid'] == user_pid:
                # Check if already added
                if not any(ts in entry for entry in user_kills_timeline):
                    user_kills_timeline.append(f"{ts}: Killed {victim_p['hero'] if victim_p else 'Unknown'}")
            
            if d['victim_pid'] == user_pid:
                # Check if already added
                if not any(ts in entry for entry in user_deaths_timeline):
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
        # (Same logic as before, just kept for context)
        logs_found = len(user_kills_timeline)
        forensic_alert = ""
        if solo_kills > logs_found:
            forensic_alert = f"""
**FORENSIC ALERT (KILL MISMATCH):**
- Scoreboard reports {solo_kills} kills, but only {logs_found} events were found in the raw log.
- INSTRUCTION: Trust the Scoreboard ({solo_kills}) for total count, but mention the timeline gaps if relevant.
"""

        # 7. Strategic Audit Prompt (Forensic Persona)
        ColoredLogger.info(f"Generating audit with {len(players)} players, {len(user_kills_timeline)} kills found.", "REPLAY")
        prompt = f"""## Mode B: STRATEGIC FORENSIC AUDIT
You are the Cerebrate Strategic Analyst. Perform a clinical audit with high tactical energy. 
Focus on **FORCE MULTIPLIERS** and **STRATEGIC GAPS**.

**STRICT VALIDATION PROTOCOL (DO NOT HALLUCINATE):**
- **VALID HEROES ONLY**: You may ONLY mention these heroes: {", ".join(valid_hero_names)}. If a name is not in this list, do NOT use it.
- **FACTUAL TALENTS**: Use the provided 'Talent Tree' to verify builds. Do not guess meta talents.
- **NO GENERIC ADVICE**: Advice must be specific to the {hero} mechanics and the enemies present.

**COMMANDER PERFORMANCE DATA (TRUTH SCALE):**
- Map: {map_name}
- Hero: {hero}
- Result: {result}
- Game Duration: {duration}
- Solo Kills: {solo_kills} (Truth Scale)
- Kill Streak: {kill_streak}
- Mercenary Captures: {personal_mercs} personal / {team_merc_count} team
- Minion XP Contribution: {minion_xp} (Lane Presence)
- Downtime: {downtime} (Time Dead)
{f"- MECHANICS (STITCHES): {mech_stats}" if mech_stats else ""}
{stitches_context if stitches_context else ""}
{f"- SOCIAL FOCUS: {social_stats}" if social_stats else ""}
{f"- CRITICAL: {user_dc_event}" if user_dc_event else ""}

**REQUIRED TACTICAL LOG (EXTRACTED FROM REPLAY):**
You MUST process every single event in this log into the 'areas_for_improvement' JSON section. 
- For 'Deaths', you MUST include all {user_core_stats.get('Deaths', 0)} deaths. Mention the Killer Hero.
- For 'Your Kills', you MUST include all {solo_kills} solo kills.

**User Death Log:**
{chr(10).join(user_deaths_timeline) if user_deaths_timeline else "None recorded."}

**User Kill Log:**
{chr(10).join(user_kills_timeline) if user_kills_timeline else "None recorded."}

**TACTICAL ENGAGEMENT TIMELINE (FORENSIC DATA):**
{tactical_timeline_data if tactical_timeline_data else "None recorded via forensic scan."}

**DRAFT COMPOSITION:**
- Team Allies: {", ".join([f"{p['hero']} ({p['name']})" for p in user_team])}
- Team Enemies: {", ".join([f"{p['hero']} ({p['name']})" for p in enemy_team])}

**TEAM STATS:**
- Your Team: {team_stats['own']['kills']} K/ {team_stats['own']['deaths']} D
- Enemy Team: {team_stats['enemy']['kills']} K/ {team_stats['enemy']['deaths']} D
- User Participation: {contribution['HeroDamage']}% Hero Dmg / {contribution['ExperienceContribution']}% XP

**OUTPUT SCHEMA (STRICT JSON ONLY):**
```json
{{
    "verdict": "{result}",
    "summary": "3-5 sentences analyzing WHY you lost. Use specific killer names in context.",
    "key_insights": {{
        "kill_streak": "{kill_streak}",
        "mercenary_camps": {personal_mercs},
        "downtime": "{downtime}",
        "minion_xp": "{minion_xp}",
        "contribution_index": "{contribution['HeroDamage']}% Dmg / {contribution['ExperienceContribution']}% XP"
    }},
    "areas_for_improvement": [
        {{ 
            "title": "Deaths", 
            "items": [
                {{ "time": "MM:SS", "killer": "HeroName", "context": "Detailed breakdown using the Death Log" }}
            ] 
        }},
        {{ 
            "title": "Your Kills", 
            "items": [
                {{ "time": "MM:SS", "victim": "HeroName", "context": "Forensic proof (e.g., Lethal Hook or Direct Kill)" }},
                {{ "time": "SUMMARY", "victim": "Stats", "context": "{solo_kills} Solo Kills / {user_core_stats.get('Assists', 0)} Assists" }}
            ] 
        }}
    ],
    "critical_mistake": "The ONE mistake that led to the most attrition.",
    "win_condition": "How to handle these enemies next time."
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

    def _generate_social_insights(self, match_data, dcs=None, social_mechanics=None):
        """Generates a separate layer of social intelligence (rivalries, DCs, teammate synergy)."""
        intel_service = self._get_intel_service()
        
        players = match_data.get('players', [])
        user_player = next((p for p in players if 'Discerning' in p['name']), players[0])
        
        # 1. Social Context
        social_intel = self.db.get_kv('player_interactions') or {}
        user_briefings = {p['name']: social_intel[p['name']].get('aiStrategy') 
                         for p in players if p['name'] in social_intel}
        
        mech_context = ""
        if social_mechanics:
            mech_context = f"\n**MECHANICAL FOCUS (Aggression Logic):**\n{json.dumps(social_mechanics.get('focus_distribution', {}), indent=2)}\n"

        prompt = f"""## SOCIAL INSIGHTS ENGINE
Analyze the 'Neural Network' of this match. Focus on Human Factors.

**PERSONNEL:**
{json.dumps([{ 'name': p['name'], 'hero': p['hero'], 'team': p['team'], 'deaths': p.get('stats', {}).get('Deaths', 0) } for p in players], indent=2)}

**ESTABLISHED NEURAL LINKS (Your Notes):**
{json.dumps(user_briefings, indent=2)}

**TEAMMATE/ENEMY DISCONNECTS:**
{", ".join(dcs) if dcs else "None"}
{mech_context}
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

    def analyze_match(self, match_data, force=False, replay_path=None):
        """Forces or performs AI analysis on a match."""
        # Clean up match_data input as it might be an ID or a dictionary
        if isinstance(match_data, str):
            match_id = match_data
            match_data_rows = self.db.get_matches(match_id=match_id, include_players=True)
            if not match_data_rows or len(match_data_rows) == 0:
                return {"status": "error", "message": "Match not found"}
            match_data = match_data_rows[0]
        else:
            match_id = match_data.get('match_id')

        # 1. Quota Check
        if not force and not self.quota.can_make_request():
            return {"status": "quota_exceeded", "match_id": match_id}

        # 2. Check if already analyzed
        if not force and match_data.get('analysis') and match_data['analysis'] != {}:
            return {"status": "complete", "match_id": match_id, "analysis": match_data['analysis']}

        # 3. Dynamic Replay Discovery (for mechanical forensics)
        if not replay_path:
            replay_path = self._find_replay_file(match_id)

        # 4. RUN MECHANICAL FORENSICS (First, so we can use it in Summary)
        forensics = None
        social_mechanics = None
        if replay_path and os.path.exists(replay_path):
            try:
                hero = match_data.get('hero', '')
                forensics = MechanicalAnalysisService.analyze_replay(replay_path, hero)
                if forensics:
                    ColoredLogger.success(f"Mechanical Forensics ready for {hero}", "REPLAY")
                    social_mechanics = forensics.get('social_mechanics')
            except Exception as e:
                ColoredLogger.error(f"Forensics failed: {e}", "REPLAY")

        # 5. RUN FORENSIC AUDIT (Main Verdict) using Forensics Data
        summary = self._generate_match_summary(match_data, forensics=forensics, force=force)
        
        # 6. RUN SOCIAL INSIGHTS (Deep Social Network)
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
        
        social = self._generate_social_insights(match_data, dcs=teammate_enemy_dcs, social_mechanics=social_mechanics)
        
        if summary and summary.get('success'):
            results = summary['analysis']
            if forensics:
                results['forensics'] = forensics
            
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
        
        # FALLBACK: If summary failed but we have forensics, at least update those
        if forensics:
            current_results = match_data.get('analysis') or {}
            current_results['forensics'] = forensics
            self.db.update_match_analysis(match_id, current_results)
            return {"status": "complete_forensics_only", "match_id": match_id, "analysis": current_results}
        
        return {"status": "error", "match_id": match_id, "message": "Analysis generation failed"}



