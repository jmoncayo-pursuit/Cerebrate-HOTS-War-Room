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
from api.summary_schema import SUMMARY_SCHEMA_VERSION
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

            # Banner context (who was banner = highest MMR; carry vs carry)
            adv = result.get('advanced_stats', {})
            bans = adv.get('bans', [])
            user_name = result.get('user_name') or ''
            players = result.get('players', [])
            user_player = next((p for p in players if (p.get('name') or '').lower() == user_name.lower()), players[0] if players else None)
            user_team = user_player.get('team') if user_player else None
            user_was_banner = False
            enemy_banner_name = None
            if user_team is not None and bans:
                user_was_banner = any(
                    b.get('team') == user_team and (b.get('banned_by') or '').strip() == user_name.strip()
                    for b in bans
                )
                enemy_banner = next((b.get('banned_by') for b in bans if b.get('team') != user_team and b.get('banned_by')), None)
                if enemy_banner:
                    enemy_banner_name = enemy_banner.strip() or None
            adv['user_was_banner'] = user_was_banner
            adv['enemy_banner_name'] = enemy_banner_name

            # 4. Database Ingestion
            db_data = {
                'id': result['match_id'],
                'map': result['map'],
                'hero': result['hero'],
                'result': result['result'].upper(), # WIN/LOSS
                'date': result['timestamp_iso'],
                'duration': result['game_length'],
                'players': result['players'],
                'advanced_stats': adv,
                'user_was_banner': 1 if user_was_banner else 0,
                'enemy_banner_name': enemy_banner_name,
                'pipeline_version': 'GOLD_2026_V1',
                'raw_stats': {
                    'game_mode': result.get('game_mode'),
                    'is_ranked': result.get('is_ranked')
                }
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

    def reparse_match(self, match_id):
        """
        Re-parse a match's replay file to refresh advanced_stats (picks), players (disconnected),
        and banner fields. Preserves existing analysis. Returns dict with success and optional error.
        """
        rows = self.db.get_matches(match_id=match_id, include_players=True, include_details=True)
        if not rows:
            return {"success": False, "error": "Match not found"}
        existing = rows[0]
        path = self._find_replay_file(match_id)
        if not path:
            return {"success": False, "error": "Replay file not found"}
        try:
            result = parse_replay(path)
        except Exception as e:
            ColoredLogger.error(f"Reparse parse error: {e}", "REPLAY")
            return {"success": False, "error": str(e)}
        if not result or result.get("status") == "error":
            return {"success": False, "error": result.get("message", "Parse failed")}
        adv = result.get("advanced_stats", {})
        bans = adv.get("bans", [])
        user_name = result.get("user_name") or ""
        players = result.get("players", [])
        user_player = next((p for p in players if (p.get("name") or "").lower() == user_name.lower()), players[0] if players else None)
        user_team = user_player.get("team") if user_player else None
        user_was_banner = False
        enemy_banner_name = None
        if user_team is not None and bans:
            user_was_banner = any(
                b.get("team") == user_team and (b.get("banned_by") or "").strip() == user_name.strip()
                for b in bans
            )
            enemy_banner = next((b.get("banned_by") for b in bans if b.get("team") != user_team and b.get("banned_by")), None)
            if enemy_banner:
                enemy_banner_name = enemy_banner.strip() or None
        adv["user_was_banner"] = user_was_banner
        adv["enemy_banner_name"] = enemy_banner_name
        existing_analysis = existing.get("analysis") or {}
        if isinstance(existing_analysis, str):
            try:
                existing_analysis = json.loads(existing_analysis)
            except Exception:
                existing_analysis = {}
        winning_team = next((p["team"] for p in result.get("players", []) if p.get("win")), None)
        if winning_team is None:
            winning_team = existing.get("winning_team")
        db_data = {
            "id": result["match_id"],
            "map": result["map"],
            "hero": result["hero"],
            "result": result["result"].upper(),
            "date": result.get("timestamp_iso") or existing.get("date"),
            "duration": result.get("game_length") or existing.get("duration"),
            "winning_team": winning_team,
            "players": result["players"],
            "advanced_stats": adv,
            "user_was_banner": 1 if user_was_banner else 0,
            "enemy_banner_name": enemy_banner_name,
            "pipeline_version": getattr(self, "PIPELINE_VERSION", "GOLD_2026_V1"),
            "raw_stats": {"game_mode": result.get("game_mode"), "is_ranked": result.get("is_ranked")},
            "analysis": existing_analysis,
        }
        try:
            self.db.upsert_match(db_data)
        except Exception as e:
            ColoredLogger.error(f"Reparse upsert error: {e}", "REPLAY")
            return {"success": False, "error": str(e)}
        ColoredLogger.success(f"Reparse complete: {match_id}", "REPLAY")
        return {"success": True, "match_id": match_id}

    def fmt_ms(self, s): 
        """Format seconds to MM:SS."""
        if s is None: return "0:00"
        if isinstance(s, str): return s
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


        if not intel_service:
            return None
        
        map_name = match_data.get('map', 'Unknown')
        hero = match_data.get('hero', 'Unknown')
        result = match_data.get('result', 'UNKNOWN')
        duration = match_data.get('duration', 'Unknown')
        game_length = match_data.get('game_length', 0)
        
        players = match_data.get('players', [])
        advanced = match_data.get('advanced_stats') or match_data.get('raw_stats') or {}
        
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
        hero_specific_context = ""
        if forensics:
             # Mechanics
             m_list = [f"{m['label']}: {m['value']}" for m in forensics.get('mechanics', [])]
             mech_stats = " | ".join(m_list)
             
             # Social Logic (Focus)
             soc = forensics.get('social_mechanics', {})
             focus = soc.get('most_targeted_enemy', 'None')
             social_stats = f"Most Targeted Enemy: {focus}"

             # Quest Progression
             quest = forensics.get('quest_progression', {})
             if quest:
                 q_name = quest.get('name', 'Quest')
                 q_val = quest.get('value', 0)
                 q_verdict = quest.get('verdict', 'N/A')
                 hero_specific_context += f"- QUEST: {q_name} | Progress: {q_val} {quest.get('stat', 'units')} | Milestone Status: {q_verdict}\n"

             # Tactical Highlights (Timeline)
             highlights = forensics.get('tactical_highlights', [])
             h_lines = [f"[{h.get('time', 0)}] {h.get('event') or 'Event'} (Victim: {h.get('victim') or 'Enemy'})" for h in highlights]
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

        if 'Stitches' in hero:
             hooks_thrown = user_player.get('kv_stats', {}).get('HooksThrown', 
                            user_player.get('stats', {}).get('HooksThrown', 0))
             hero_specific_context += f"- STITCHES SPECIFIC: {hooks_thrown} Hooks Thrown (Note: Landed count unavailable, judge based on Takedowns)\n"
        
        # Globe Quest Context
        globe_heroes = ['Stitches', 'Tyrael', 'Jaina', 'Muradin', 'Chen', 'Diablo']
        globes = user_core_stats.get('RegenerationGlobe', 0)
        if (hero in globe_heroes or globes > 0) and "GLOBE" not in hero_specific_context:
            hero_specific_context += f"- GLOBE COLLECTION: {globes} Regeneration Globes collected. If the user took a globe quest (like 'Hungry for More' or 'Fingers of Frost'), mention if they hit a strong milestone (usually 20-30+ globes).\n"

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
                if h.get('type') == 'KILL' or (h.get('type') == 'HOOK' and h.get('lethal')) or h.get('type') == 'GLOBE':
                    action = "Killed" if h.get('lethal') else ("Struck" if h.get('type') == 'GLOBE' else "Aggressed")
                    ts = self.fmt_ms(h.get('time', 0))
                    user_kills_timeline.append(f"{ts}: {action} {h.get('victim') or 'Enemy Hero'}")
            
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

        # 6. Level Lead Analysis (for macro pressure attribution)
        level_milestones = advanced.get('level_milestones', {})
        level_context = ""
        if level_milestones:
            user_team_id = user_player['team']
            enemy_team_id = 1 - user_team_id
            user_l10 = level_milestones.get(user_team_id, {}).get(10)
            enemy_l10 = level_milestones.get(enemy_team_id, {}).get(10)
            if user_l10 and enemy_l10:
                lead_sec = enemy_l10 - user_l10
                if lead_sec > 0:
                    level_context = f"- Level 10 Lead: Your team hit Level 10 {lead_sec:.1f}s BEFORE enemy ({self.fmt_ms(user_l10)} vs {self.fmt_ms(enemy_l10)}). This early advantage was driven by macro pressure (XP generation)."
                elif lead_sec < 0:
                    level_context = f"- Level 10 Gap: Enemy team hit Level 10 {abs(lead_sec):.1f}s BEFORE your team ({self.fmt_ms(enemy_l10)} vs {self.fmt_ms(user_l10)})."
            user_l20 = level_milestones.get(user_team_id, {}).get(20)
            enemy_l20 = level_milestones.get(enemy_team_id, {}).get(20)
            if user_l20 and enemy_l20:
                lead20_sec = enemy_l20 - user_l20
                if lead20_sec > 0:
                    level_context += f" Level 20 Lead: Your team hit Level 20 {lead20_sec:.1f}s BEFORE enemy ({self.fmt_ms(user_l20)} vs {self.fmt_ms(enemy_l20)})."
                elif lead20_sec < 0:
                    level_context += f" Level 20 Gap: Enemy team hit Level 20 {abs(lead20_sec):.1f}s BEFORE your team ({self.fmt_ms(enemy_l20)} vs {self.fmt_ms(user_l20)})."

        # 7. Kill Verification Alert
        # (Same logic as before, just kept for context)
        logs_found = len(user_kills_timeline)
        forensic_alert = ""
        if solo_kills > logs_found:
            forensic_alert = f"""
**FORENSIC ALERT (KILL MISMATCH):**
- Scoreboard reports {solo_kills} kills, but only {logs_found} events were found in the raw log.
- INSTRUCTION: Trust the Scoreboard ({solo_kills}) for total count, but mention the timeline gaps if relevant.
"""

        # 7. Strategic Audit Prompt (Forensic Persona - GOLD STANDARD)
        ColoredLogger.info(f"Generating audit with {len(players)} players, {len(user_kills_timeline)} kills found.", "REPLAY")
        prompt = f"""## Mode B: STRATEGIC FORENSIC AUDIT (GOLD STANDARD)
You are the Cerebrate Strategic Analyst. Perform a clinical audit with high tactical energy.

**STRICT GOLD STANDARD REQUIREMENTS:**
1. **PLAIN LANGUAGE**: Use clear, direct terms only. NEVER use: "Theoretical Value Delta", "Unified Throughput", "Pure Soak", "Force Multiplier", "Additive Link", "Macro Anchor", "Attrition Scaling". Instead say: "the main problem", "healing/damage output", "lane XP", "your impact", "combo potential", "macro pressure", "sustained presence". Explain cause and effect in plain English.
2. **CAUSAL ANALYSIS**: Do not just say WHAT happened. Explain WHY it happened and the COST. (e.g., "This choice traded ~5,200 Healing Per Minute for siege damage—equivalent to removing 1.5x of a Valla's health pool from team sustain.")
3. **SPECIFIC NUMBERS**: You MUST cite specific stats from the data below (XP, Healing, Siege, Timestamps). When mentioning level leads (e.g. "1-level lead by minute 7"), infer from Level 10 timing: if your team hit Level 10 significantly before enemy, you had an early lead. Do NOT fabricate specific minute timestamps unless Level 10 data supports it.
4. **ATTRIBUTION**: When the user contributed {contribution['ExperienceContribution']}% of team XP and {minion_xp:,} minion XP, attribute macro pressure to the user (not "the team").
5. **VERBOSE & FORENSIC**: Your summary MUST be 3-5 detail-heavy sentences. No 1-sentence summaries.
6. **STRICT HERO VALIDATION**: You may ONLY mention these heroes: {", ".join(valid_hero_names)}.
7. **ALWAYS IDENTIFY CRITICAL MISTAKE**: Even in dominant wins, you MUST identify what prevented carrying harder. Look for opportunity costs: missed rotations, suboptimal positioning windows, untapped macro potential, or failure to capitalize on enemy mistakes. NEVER output "None detected" or "No mistakes" for critical_mistake.
8. **FORMATTING - CRITICAL**:
   a) NEVER wrap hero names in **bold**. Write hero names as plain text (e.g. "Muradin" not "**Muradin**"). The UI auto-renders hero names with icons.
   b) When using bold for non-hero terms, ALWAYS put a space before the opening ** and after the closing ** (e.g. "your **Experience Contribution** drove" NOT "your**Experience Contribution**drove").
   c) Do NOT output unpaired asterisks. Every ** must have a matching closing **.
9. **WIN CONDITION MUST BE SPECIFIC**: Do NOT give generic advice like "die less", "position better", "collect more globes", "be more disciplined", or "focus on objectives". Instead, cite SPECIFIC data: which objective at what timestamp, which enemy hero to focus/avoid, which rotation timing to change, with numbers. Example: "At the 12:00 Immortal, rotating 15s earlier would have secured the race by ~8000 HP. Focus burst on Anduin first to eliminate healing before committing to Li-Ming."

**GOLD STANDARD EXAMPLE:**
"Despite the loss, your performance was strong. Your {user_core_stats.get('ExperienceContribution', 0):,} Experience Contribution included {minion_xp:,} minion XP, proving you drove level progression. However, during the {map_name} objective, positioning too far from the focus target cost you ~35% of your healing output, and that teamfight attrition cost the game."

**COMMANDER PERFORMANCE DATA (TRUTH SCALE):**
- Map: {map_name}
- Hero: {hero}
- Result: {result}
- Game Duration: {duration}
- Solo Kills: {solo_kills} (Truth Scale)
- Kill Streak: {kill_streak}
- Experience Contribution: {user_core_stats.get('ExperienceContribution', 0):,} ({contribution['ExperienceContribution']}% of team total)
- Minion XP: {minion_xp:,} — Your isolated lane XP, proving your macro pressure (not team's)
- When you contributed {contribution['ExperienceContribution']}% of team XP and {minion_xp:,} minion XP, that is your macro pressure (not the team's).
- Mercenary Captures: {personal_mercs} personal / {team_merc_count} team
- Downtime: {downtime} (Time Dead)
{level_context if level_context else ""}
{f"{hero_specific_context}" if hero_specific_context else ""}
{f"- SOCIAL FOCUS: {social_stats}" if social_stats else ""}
{f"- CRITICAL: {user_dc_event}" if user_dc_event else ""}

**REQUIRED TACTICAL LOG (EXTRACTED FROM REPLAY):**
You MUST process every single event in this log into the 'areas_for_improvement' JSON section. 
- For 'Deaths', you MUST include all {user_core_stats.get('Deaths', 0)} deaths. Mention the Killer Hero and context.
- For 'Your Kills', you MUST include all {solo_kills} solo kills with timestamps.

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
- When you contributed {contribution['ExperienceContribution']}% of team XP and {minion_xp:,} minion XP, that is your macro pressure (not the team's).

**OUTPUT SCHEMA (STRICT JSON ONLY):**
```json
{{
    "verdict": "{result}",
    "summary": "3-5 sentences explaining WHY you won/lost, using concrete data and plain language. No jargon.",
    "key_insights": {{
        "deaths": {user_core_stats.get('Deaths', 0)},
        "kill_streak": "{kill_streak}",
        "mercenary_camps": {personal_mercs},
        "pure_soak": "{minion_xp:,}",
        "globes": {globes},
        "downtime": "{downtime}",
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
                {{ "time": "MM:SS", "victim": "HeroName", "context": "Forensic proof" }}
            ] 
        }}
    ],
    "critical_mistake": "REQUIRED: Even in dominant wins, identify the ONE action/decision that prevented carrying harder. Examples: 'Positioning at X:XX cost 2 potential kills', 'Missing macro rotation at Y:YY denied 500 XP', 'Not capitalizing on enemy cooldowns at Z:ZZ extended game by 2 minutes'. If no clear mistake exists, identify the highest-opportunity-cost decision (e.g., 'Could have rotated earlier to secure objective 30s faster'). NEVER say 'None detected' or 'No mistakes'.",
    "win_condition": "REQUIRED: Must reference specific data from this match — enemy hero to exploit/avoid, rotation timing, objective timing, or stat threshold. NEVER give generic advice like 'die less', 'position better', 'collect more globes', 'be more disciplined'. Example: 'At the 12:00 Immortal, rotating 15s earlier secures the race. Focus burst on Anduin first (weakest with 3 deaths) before engaging Li-Ming.'"
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
                try:
                    res_text = response.text.strip()
                    ColoredLogger.info(f"FORENSIC AUDIT GENERATED for {hero} on {map_name} (attempt {attempt + 1}/{max_retries})", "REPLAY")
                    
                    analysis = self._parse_json_response(res_text)


                    if not analysis:
                        raise ValueError("Failed to parse analysis JSON")
                    
                    pass
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
1. **Team labels**: NEVER use "Team 0" or "Team 1". Always use "Your team" for the commander's side and "Enemy team" for the opposite side. The commander (user) is on the team with hero: {user_player.get('hero', '')}.
2. **Highlight Rivalries**: Identify if a specific enemy neutralized the user multiple times.
3. **Teammate Synergy**: Note if an ally performance was notably high or low.
4. **Neural Briefing Correlation**: Did players in your notes live up to their reputation?
5. **Tone**: Forensic but 'notable' (highlight interesting human patterns).
6. **Instruction**: If you are commenting on a teammate performance as a 'failure' or 'asset', be specific about their stats relative to the user.

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
            
            # Clean text removed
            return social
        except:
            return None

    def get_match_history(self, limit=50, include_details=False, search=None, hero=None, since=None, match_id=None):
        return self.db.get_matches(limit=limit, include_details=include_details, search=search, hero=hero, since=since, match_id=match_id)

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
        
        # 6. No AI-generated social insights (overview/rivalry) — Personnel tab uses match data: DCs, banner
        if summary and summary.get('success'):
            results = summary['analysis']
            # Attach schema version so Healer can detect when summaries need re-audit
            results['summary_version'] = SUMMARY_SCHEMA_VERSION
            if forensics:
                results['forensics'] = forensics
            
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



