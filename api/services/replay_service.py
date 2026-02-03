import os
import time
import json
from datetime import datetime
from api.logger import ColoredLogger
from api.services.replay_parser import parse_replay
from api.services.database import DatabaseManager
from api.services.quota_manager import QuotaManager

class ReplayService:
    def __init__(self):
        self.db = DatabaseManager()
        self.quota = QuotaManager()
        self._intel_service = None  # Lazy-loaded

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
            
            # 5. ANALYSIS - Always generate for immediate feedback
            analysis_result = None
            if success and self.quota.can_make_request():
                try:
                    # Note: We still highlight DCs in the prompt if they exist
                    analysis_result = self._generate_match_summary(db_data)
                    if analysis_result and analysis_result.get('success'):
                        self.db.update_match_analysis(result['match_id'], analysis_result['analysis'])
                        self.quota.record_request()
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

    def _generate_match_summary(self, match_data):
        """Generate a clinical forensic AI summary for a match (Mode B: FORENSIC AUDIT)."""
        intel_service = self._get_intel_service()
        if not intel_service:
            return None
        
        map_name = match_data.get('map', 'Unknown')
        hero = match_data.get('hero', 'Unknown')
        result = match_data.get('result', 'UNKNOWN')
        duration = match_data.get('duration', 'Unknown')
        game_length = match_data.get('game_length', 0)
        
        players = match_data.get('players', [])
        advanced = match_data.get('raw_stats', {})
        
        # 1. Forensic Extraction: Identify User & Teams
        user_player = None
        team_0 = []
        team_1 = []
        for p in players:
            if p.get('hero') == hero: user_player = p
            if p.get('team') == 0: team_0.append(p)
            else: team_1.append(p)
        
        if not user_player: return None
        
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

        # 4. Forensic Timeline Correlation (Deaths vs Objectives)
        merc_events = advanced.get('merc_captures', [])
        boss_events = advanced.get('boss_captures', [])
        structure_events = advanced.get('structure_destructions', [])
        
        # 5. Disconnects & Telemetry
        user_deaths_raw = user_player.get('death_timestamps', [])
        user_deaths_formatted = ", ".join([self.fmt_ms(d) for d in user_deaths_raw])
        
        teammate_enemy_dcs = []
        user_dc_event = None
        # 60 second grace period: ignore disconnects at the very end of the game
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
        
        # GROUND TRUTH: Count actual capture events, not unreliable individual player stats
        team_merc_count = len([m for m in merc_events if m.get('captured_by_team') == user_player['team']])
        enemy_merc_count = len([m for m in merc_events if m.get('captured_by_team') != user_player['team']])

        # 6. Personnel Context (Individual Teammate Metrics)
        teammate_performance = []
        for p in user_team:
            if p['name'] != user_player['name']:
                p_stats = p.get('stats', {})
                teammate_performance.append({
                    "name": p['name'],
                    "hero": p['hero'],
                    "deaths": p_stats.get('Deaths', 0),
                    "xp_contribution": p_stats.get('ExperienceContribution', 0),
                    "hero_damage": p_stats.get('HeroDamage', 0),
                    "siege_damage": p_stats.get('SiegeDamage', 0),
                    "death_timestamps": p.get('death_timestamps', [])
                })

        draft = {
            "allies": [{"hero": p['hero'], "name": p['name']} for p in user_team],
            "enemies": [{"hero": p['hero'], "name": p['name']} for p in enemy_team]
        }
        user_talents = user_player.get('talents', [])
        
        # 7. Strategic Audit Prompt (Clean)
        ColoredLogger.info(f"Generating audit with {len(players)} players and {len(merc_events)} merc events.", "REPLAY")
        prompt = f"""## Mode B: STRATEGIC FORENSIC AUDIT
You are the Cerebrate Strategic Analyst. Perform a clinical audit. Separate mechanical execution from **Strategic Trade-offs**.

**COMMANDER DATA:**
- Map: {map_name}
- Hero: {hero}
- Result: {result}
- Game Duration: {duration}
- DC Status: {user_dc_event if user_dc_event else "Stable Uplink"}

**DRAFT COMPOSITION & SEQUENCE:**
- Team Allies: {", ".join([f"{p['hero']} ({p['name']})" for p in draft['allies']])}
- Team Enemies: {", ".join([f"{p['hero']} ({p['name']})" for p in draft['enemies']])}
*Action: Perform 'Compositional Forensics'. Identify if the Draft Sequence decided the outcome. Assess if the user's hero was a correct response to the map/enemy.*

**TEAM PERFORMANCE MARKERS:**
- Your Team: {team_stats['own']['kills']} Kills, {team_stats['own']['deaths']} Deaths, {team_merc_count} Merc Captures.
- Enemy Team: {team_stats['enemy']['kills']} Kills, {team_stats['enemy']['deaths']} Deaths, {enemy_merc_count} Merc Captures.
- User Contribution: {contribution['HeroDamage']}% Hero Dmg, {contribution['SiegeDamage']}% Siege, {contribution['ExperienceContribution']}% XP.

**USER TALENT TIMELINE (SPEC AUDIT):**
{json.dumps(user_talents, indent=2)}

**FORENSIC TIMELINE (ADVANCED):**
- Team Merc Captures: {team_merc_count} (Detailed: {json.dumps(merc_events[:20], indent=2)})
- Enemy Merc Captures: {enemy_merc_count}
- Structure losses: {json.dumps([s for s in structure_events if s['destroyed_by_team'] != user_player['team']][:50], indent=2)}

**CORE OPERATIONAL PHILOSOPHY (COMMANDER'S DIRECTIVES):**
1. **The Signal Noise Lexicon**: Any signal termination (DC) that occurs at the 'Match Conclusion' (e.g., 24:14 in a 24:14 game) is **NOT a disconnect**. It is a system exit. Do not mention it or analyze it.
2. **The Mercenary Ground-Truth**: Use the `FORENSIC TIMELINE` counts explicitly.
3. **Draft Recognition**: If the enemy heroes were just a hard counter to yours (like Stitches vs Raynor), call it a 'DRAFT LOSS'.
4. **Speak Plain English**: Use simple, direct, human language. You are forbidden from using "aggregate attrition", "variance in player mortality", "combat units", or "neural sync" in the summary. Instead, say "total deaths", "some players died more than others", "teammates", or "teamwork". Speak like a veteran tactical advisor, not a laboratory computer.
5. **Data Isolation**: Only the current match data exists. No ghosts.
6. **Draft Order Context**: When discussing the draft, analyze the sequence of picks if possible (who was picked into whom).

**REQUIREMENTS:**
1. **Macro Trade-offs**: Explain if trades like "letting them have the objective to take a fort" were actually good or bad in plain words.
2. **Direct Feedback**: If the team failed to protect you, say it plainly.
3. **Talent Latency**: Group talent audits with "Level Spikes".
4. **Causal Trigger**: Identify the ONE big mistake that lost the game in one simple sentence.

**OUTPUT SCHEMA (STRICT JSON ONLY):**
```json
{{
    "verdict": "WIN" or "LOSS" or "DRAFT LOSS",
    "summary": "2-3 sentence strategic clinical overview. MANDATORY: If 'DC Status' is NOT 'Stable Uplink', you MUST mention the timestamp and impact.",
    "key_insights": {{
        "commander_kills": {user_core_stats.get('SoloKill', 0)},
        "personal_merc_caps": {user_core_stats.get('MercCampCaptures', 0)},
        "team_global_merc_caps": {team_merc_count},
        "enemy_global_merc_caps": {enemy_merc_count},
        "contribution_index": "{contribution['HeroDamage']}% Dmg / {contribution['ExperienceContribution']}% XP"
    }},
    "areas_for_improvement": "Identify Recurrent Strategic Patterns. Suggest Tactical Adjustments.",
    "critical_mistake": "Clinical identification of the primary strategic-based failure.",
    "win_condition": "One sentence defining the precise causal trigger for the match outcome."
}}
```
Do not include any text before or after the JSON block.
"""

        try:
            response = intel_service.model.generate_content([prompt])
            res_text = response.text.strip()
            ColoredLogger.info(f"FORENSIC AUDIT GENERATED for {hero} on {map_name}", "REPLAY")
            
            # Parse JSON
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            try:
                analysis = json.loads(res_text)
            except Exception as json_e:
                print(f"DEBUG: FAILED TO PARSE JSON. RAW TEXT: {res_text}")
                raise json_e
            return {'success': True, 'analysis': analysis}
        except Exception as e:
            ColoredLogger.warn(f"Forensic Audit parse error: {e}", "REPLAY")
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
2. **Teammate Synergy**: Note if an ally's performance was notably high or low.
3. **Neural Briefing Correlation**: Did players in your notes live up to their reputation?
4. **Tone**: Forensic but 'notable' (highlight interesting human patterns).
5. **Instruction**: If you are commenting on a teammate's performance as a 'failure' or 'asset', be specific about their stats relative to the user.

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
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            return json.loads(res_text)
        except:
            return None

    def get_match_history(self, limit=50, include_details=False):
        return self.db.get_matches(limit=limit, include_details=include_details)

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
        summary = self._generate_match_summary(match_data)
        
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
            if social:
                results['social_insights'] = social
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

