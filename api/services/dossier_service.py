
import sqlite3
import json
import random
import time
import re
from collections import defaultdict

class DossierService:
    def __init__(self, db_manager):
        self.db = db_manager

    def get_manifest(self):
        """Returns list of heroes with cached dossiers."""
        with self.db._get_connection() as conn:
            rows = conn.execute("SELECT hero_name FROM hero_dossiers").fetchall()
            return [r[0] for r in rows]

    def generate_dossier(self, hero_name):
        """Generates a complete dossier for a hero with caching."""
        
        # 0. Get current stats to check freshness
        basic_stats = self._get_basic_stats(hero_name)
        if not basic_stats['games']:
            return None # No data
            
        current_match_count = basic_stats['games']
        
        # 1. Check Cache
        with self.db._get_connection() as conn:
            row = conn.execute("SELECT data, match_count_snapshot FROM hero_dossiers WHERE hero_name = ?", (hero_name,)).fetchone()
            if row:
                cached_data_json = row[0]
                cached_count = row[1]
                
                # If match count matches, return cached data
                if cached_count == current_match_count:
                    try:
                        return json.loads(cached_data_json)
                    except:
                        pass # Corrupt JSON, regenerate

        # 2. Map Sectors
        sectors = self._get_sector_performance(hero_name)
        training_sectors = self._get_training_sectors(hero_name)
        
        # 3. Nemesis Analysis (Enemies)
        nemesis = self._get_nemesis(hero_name)
        
        # 4. Risk Analysis (Allies - Desyncs)
        risks = self._get_risks(hero_name)
        
        # 5. Medals
        medals = self._get_medals(hero_name)
        
        # 6. Generate Fluff & AI Verdict
        codename = self._generate_codename(hero_name)
        
        # ELITE UPGRADE: AI-Generated Verdict based on stats
        from api.services.intelligence_service import IntelligenceService
        import os
        api_key = os.environ.get('GEMINI_API_KEY')
        verdict = None
        audit = None
        
        if api_key:
            intel = IntelligenceService(self.db, api_key)
            stats_context = f"""
            Hero: {hero_name}
            Overall WR: {basic_stats['wr']}%
            Total Games: {basic_stats['games']}
            Top Sectors: {json.dumps(sectors)}
            Training Sectors: {json.dumps(training_sectors)}
            Nemeses: {json.dumps(nemesis)}
            Risks: {json.dumps(risks)}
            Lethality Discovery: {json.dumps(self._get_lethality_analysis(hero_name))}
            """
            
            prompt = f"Perform a high-level tactical audit for {hero_name} based on these stats. Speak like a senior tactical advisor. Return JSON: {{\"verdict\": \"Subject is [STATUS]\", \"analysis\": \"Clinical overview\", \"status\": \"OPERATIONAL/GOLD STANDARD/NEEDS REVIEW\"}}"
            try:
                raw_verdict = intel.generate_chat_response(prompt, history=[{"role": "user", "parts": [stats_context]}])
                # Simple JSON extract
                json_match = re.search(r'(\{.*\})', raw_verdict, re.DOTALL)
                if json_match:
                    verdict = json.loads(json_match.group(1))
                else:
                    verdict = json.loads(raw_verdict)
            except Exception as e:
                print(f"AI Verdict/Audit Failure: {e}")
                verdict = self._generate_verdict(basic_stats['wr'], sectors, lethality=self._get_lethality_analysis(hero_name))
        else:
            verdict = self._generate_verdict(basic_stats['wr'], sectors, lethality=self._get_lethality_analysis(hero_name))
        
        # 7. Theme
        theme = self._get_theme(hero_name)

        dossier = {
            "hero": hero_name,
            "level": self._estimated_level(hero_name), 
            "overallWR": round(basic_stats['wr'], 1),
            "totalGames": basic_stats['games'],
            "rank": "Silver 4", # Placeholder, should come from profile
            "derivedRank": self._calculate_derived_rank(basic_stats['wr']),
            "clearanceLevel": self._calculate_clearance(basic_stats['games']),
            "codename": codename,
            "operationName": f"Operation {codename}",
            "roleDescription": self._get_role_desc(hero_name),
            "theme": theme,
            "medals": medals,
            "sectors": sectors,
            "trainingSectors": training_sectors,
            "risks": risks,
            "nemesis": nemesis,
            "recentPerformance": self._get_recent_performance(hero_name),
            "tacticalSummary": verdict,
            "forensics": self._get_hero_forensics(hero_name),
            "lethality": self._get_lethality_analysis(hero_name),
            "audit": audit, # PERSIST AUDIT
            "statSources": {
                "overallWR": "SECURE_DATALINK",
                "totalGames": "SECURE_DATALINK",
                "sectors": "SECURE_DATALINK",
                "medals": "SECURE_DATALINK",
                "forensics": "MECHANICAL_AUDIT",
                "lethality": "MECHANICAL_AUDIT",
                "tacticalSummary": "NEURAL_SYNTHESIS"
            }
        }
        
        # 8. Save to Cache
        try:
            with self.db._get_connection() as conn:
                conn.execute("""
                    INSERT INTO hero_dossiers (hero_name, data, last_updated, match_count_snapshot)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(hero_name) DO UPDATE SET
                        data = excluded.data,
                        last_updated = excluded.last_updated,
                        match_count_snapshot = excluded.match_count_snapshot
                """, (hero_name, json.dumps(dossier), time.time(), current_match_count))
        except Exception as e:
            print(f"Cache Save Error: {e}")
            
        return dossier


    def _get_basic_stats(self, hero):
        # Focus on "Seasonal" Performance (Last 30 games) instead of Lifetime
        query = """
            SELECT count(*), sum(case when result='WIN' then 1 else 0 end)
            FROM (
                SELECT result 
                FROM matches 
                WHERE hero = ? 
                ORDER BY date DESC 
                LIMIT 30
            ) as recent_matches
        """
        with self.db._get_connection() as conn:
            row = conn.execute(query, (hero,)).fetchone()
            games = row[0] if row[0] is not None else 0
            wins = row[1] if row[1] is not None else 0
            return {"games": games, "wins": wins, "wr": (wins/games*100) if games > 0 else 0}

    def _get_sector_performance(self, hero):
        # Top 3 Maps
        query = """
            SELECT map, count(*) as g, sum(case when result='WIN' then 1 else 0 end) as w
            FROM matches
            WHERE hero = ?
            GROUP BY map
            HAVING g >= 3
            ORDER BY (CAST(w AS FLOAT)/g) DESC
            LIMIT 3
        """
        sectors = []
        with self.db._get_connection() as conn:
            rows = conn.execute(query, (hero,)).fetchall()
            for r in rows:
                wr = (r[2]/r[1])*100
                status = "DOMINANT" if wr >= 60 else "EFFECTIVE" if wr >= 50 else "STABLE"
                sectors.append({"name": r[0], "wr": round(wr, 1), "status": status})
        return sectors

    def _get_training_sectors(self, hero):
        # Bottom 2 Maps
        query = """
            SELECT map, count(*) as g, sum(case when result='WIN' then 1 else 0 end) as w
            FROM matches
            WHERE hero = ?
            GROUP BY map
            HAVING g >= 3
            ORDER BY (CAST(w AS FLOAT)/g) ASC
            LIMIT 2
        """
        sectors = []
        with self.db._get_connection() as conn:
            rows = conn.execute(query, (hero,)).fetchall()
            for r in rows:
                wr = (r[2]/r[1])*100
                if wr < 45: # Only show if actually bad
                    sectors.append({"name": r[0], "wr": round(wr, 1)})
        return sectors

    def _get_nemesis(self, hero):
        # Enemies who beat us most (High Enemy Win Rate)
        # We need to find matches where we played 'hero', calculate enemy WR against us.
        query = """
            SELECT 
                enemy.hero,
                count(distinct matches.id) as games_against,
                sum(enemy.win) as enemy_wins
            FROM matches
            JOIN match_players user ON matches.id = user.match_id AND user.hero = matches.hero
            JOIN match_players enemy ON matches.id = enemy.match_id AND enemy.team != user.team
            WHERE matches.hero = ?
            GROUP BY enemy.hero
            HAVING games_against >= 3
            ORDER BY 
                games_against DESC, -- Prioritize sample size first
                (CAST(enemy_wins AS FLOAT) / games_against) DESC -- Then win rate
            LIMIT 3
        """
        nemesis = []
        with self.db._get_connection() as conn:
            rows = conn.execute(query, (hero,)).fetchall()
            for r in rows:
                games = r[1]
                enemy_wins = r[2]
                enemy_wr = (enemy_wins / games) * 100
                if enemy_wr > 50: # Only list if they actually beat us often
                    nemesis.append({
                        "name": r[0],
                        "type": "Counter", 
                        "wr": round(enemy_wr, 1), # This is THEIR win rate (Threat Level)
                        "games": games
                    })
        return nemesis

    def _get_risks(self, hero):
        # Allies we lose with (Low Ally Win Rate)
        query = """
            SELECT 
                ally.hero,
                count(distinct matches.id) as games_with,
                sum(ally.win) as wins_with
            FROM matches
            JOIN match_players user ON matches.id = user.match_id AND user.hero = matches.hero
            JOIN match_players ally ON matches.id = ally.match_id AND ally.team = user.team AND ally.hero != matches.hero
            WHERE matches.hero = ?
            GROUP BY ally.hero
            HAVING games_with >= 3
            ORDER BY 
                 games_with DESC, -- Prioritize sample size first
                 (CAST(wins_with AS FLOAT) / games_with) ASC -- Then low win rate
            LIMIT 3
        """
        risks = []
        with self.db._get_connection() as conn:
            rows = conn.execute(query, (hero,)).fetchall()
            for r in rows:
                games = r[1]
                wins = r[2]
                wr = (wins / games) * 100
                # Show even if WR is okay, if sample size is huge and it's our worst.
                # But typically risk means bad WR.
                if wr < 55: 
                     risks.append({
                        "name": r[0],
                        "wr": round(wr, 1), # Our win rate with them
                        "games": games
                    })
        return risks

    def _get_medals(self, hero):
        query = "SELECT stats FROM match_players WHERE hero = ? AND stats IS NOT NULL"
        medals = defaultdict(int)
        
        # Award mapping
        mapping = {
            'EndOfMatchAwardMVPBoolean': 'MVP',
            'EndOfMatchAwardMostKillsBoolean': 'Terminator',
            'EndOfMatchAwardMostSiegeDamageDoneBoolean': 'Siege Master',
            'EndOfMatchAwardMostHeroDamageDoneBoolean': 'Top Damage',
            'EndOfMatchAwardMostXPContributionBoolean': 'Macro God',
            'EndOfMatchAwardMostHealingBoolean': 'Main Healer',
            'EndOfMatchAwardMostCoinsPaidBoolean': 'Bosun Medal',
            'EndOfMatchAwardMostImmortalDamageBoolean': 'Immortal Slayer',
            'EndOfMatchAwardMostCurseDamageDoneBoolean': 'Curse Breaker',
             'EndOfMatchAwardMostGemsTurnedInBoolean': 'Gem Collector',
             'EndOfMatchAwardMostAltarDamageDone': 'Altar Guardian',
             'EndOfMatchAwardMostDamageToPlantsBoolean': 'Gardener'
        }
        
        with self.db._get_connection() as conn:
            rows = conn.execute(query, (hero,)).fetchall()
            for r in rows:
                try:
                    s = json.loads(r[0])
                    for key, label in mapping.items():
                        # Some are boolean true/false, some are 1/0
                        val = s.get(key)
                        if val == 1 or val is True:
                            medals[label] += 1
                except:
                    continue
        
        # Filter out 0s
        return {k: v for k, v in medals.items() if v > 0}

    def _generate_codename(self, hero):
        codenames = ["Valkyrie", "Juggernaut", "Phantom", "Sovereign", "Eclipse", "Vanguard"]
        return f"{random.choice(codenames)} Protocol"

    def _generate_verdict(self, wr, sectors, lethality=None):
        status = "OPERATIONAL"
        jump = lethality.get('jump', 0) if lethality else 0
        
        if jump > 15:
            status = "LETHALITY DRIVEN"
        elif wr > 60:
            status = "GOLD STANDARD"
        elif wr < 45:
            status = "HIGH POTENTIAL" if jump > 5 else "NEEDS REFINEMENT"
        
        analysis = "Subject demonstrates standard combat efficiency."
        if jump > 15:
            analysis = f"Strategic Discovery: Win probability increases by {jump}% when securing {lethality.get('threshold', 5)}+ kills. This is your primary agency lever."
        elif sectors:
            best_map = sectors[0]['name']
            analysis += f" Exceptional performance noted on {best_map}."
            
        return {
            "verdict": f"Subject is <span class='text-cyan-400 font-bold'>{status}</span>.",
            "analysis": analysis,
            "status": status
        }

    def _get_theme(self, hero):
        # Simple mapping
        role_colors = {
            'Warrior': 'red',
            'Tank': 'blue',
            'Healer': 'emerald',
            'Support': 'teal',
            'Assassin': 'purple'
        }
        # Default
        return {'primary': 'cyan', 'secondary': 'blue', 'gradient': 'from-cyan-600 to-blue-600'}

    def _get_role_desc(self, hero):
        return "Specialist"

    def _calculate_derived_rank(self, wr):
        if wr >= 60: return "Diamond Tier"
        if wr >= 55: return "Platinum Tier"
        if wr >= 50: return "Gold Tier"
        return "Silver Tier"

    def _calculate_clearance(self, games):
        if games > 100: return 10
        if games > 50: return 5
        return 1
        
    def _get_recent_performance(self, hero):
        """Pulls last 5 matches for this hero."""
        query = """
            SELECT m.id, m.result, m.map, m.date, p.stats
            FROM matches m
            JOIN match_players p ON m.id = p.match_id
            WHERE p.hero = ?
            ORDER BY m.date DESC
            LIMIT 5
        """
        history = []
        with self.db._get_connection() as conn:
            rows = conn.execute(query, (hero,)).fetchall()
            for r in rows:
                stats = {}
                try:
                    stats = json.loads(r[4]) if r[4] else {}
                except: pass
                
                history.append({
                    "id": r[0],
                    "result": r[1],
                    "map": r[2],
                    "date": r[3],
                    "kills": stats.get('SoloKill', 0),
                    "deaths": stats.get('Deaths', 0),
                    "assists": stats.get('Assists', 0)
                })
        return history

    def _get_hero_forensics(self, hero):
        """Aggregates mechanical forensics from past match analyses and generic telemetry."""
        query = """
            SELECT m.analysis, mp.stats
            FROM matches m
            LEFT JOIN match_players mp ON m.id = mp.match_id AND m.hero = mp.hero
            WHERE m.hero = ?
        """
        forensics_list = []
        stats_list = []
        with self.db._get_connection() as conn:
            rows = conn.execute(query, (hero,)).fetchall()
            for r in rows:
                if r[0]:  # analysis
                    try:
                        analysis = json.loads(r[0])
                        if 'forensics' in analysis:
                            forensics_list.append(analysis['forensics'])
                    except:
                        pass
                if r[1]:  # stats
                    try:
                        stats_list.append(json.loads(r[1]))
                    except:
                        pass
        
        if not stats_list and not forensics_list:
            return None
            
        game_count = len(stats_list) if stats_list else 1
        
        # Calculate Generic "Good" Stats
        total_gems = sum(s.get('GemsTurnedIn', 0) for s in stats_list)
        total_camps = sum(s.get('MercCampCaptures', 0) for s in stats_list)
        total_cc_time = sum(s.get('TimeCCdEnemyHeroes', 0) for s in stats_list)
        total_kda_kills = sum(s.get('Takedowns', 0) for s in stats_list)
        total_deaths = sum(s.get('Deaths', 0) for s in stats_list)
        outnumbered_deaths = sum(s.get('OutnumberedDeaths', 0) for s in stats_list)
        max_streak = max([s.get('HighestKillStreak', 0) for s in stats_list] + [0])
        
        summary_stats = []
        top_victims = []
        
        if hero == 'Stitches':
            total_hooks = 0
            landed_hooks = 0
            lethal_hooks = 0
            total_globes = 0
            
            for f in forensics_list:
                for m in f.get('mechanics', []):
                    if m['label'] == 'Hooks Thrown': total_hooks += m['value']
                    if m['label'] == 'Hooks Landed': landed_hooks += m['value']
                    if m['label'] == 'Lethal Hooks': lethal_hooks += m['value']
                q = f.get('quest_progression', {})
                if q: total_globes += q.get('value', 0)

            f_count = len(forensics_list) or 1
            summary_stats += [
                {"label": "Avg. Hook Accuracy", "value": f"{round((landed_hooks/max(1, total_hooks)*100), 1)}%"},
                {"label": "Total Lethal Hooks", "value": lethal_hooks},
                {"label": "Avg. Globes / Match", "value": round(total_globes/f_count, 1)}
            ]
            top_victims = self._get_to_victims_from_highlights(forensics_list)
        
        # Add Generic Good Stats (Fill up to 3)
        if total_gems > 0: summary_stats.append({"label": "Avg Gems Managed", "value": round(total_gems/game_count, 1)})
        if total_camps > 0: summary_stats.append({"label": "Avg Merc Captures", "value": round(total_camps/game_count, 1)})
        if total_cc_time > 0: summary_stats.append({"label": "Avg CC Time", "value": f"{round(total_cc_time/game_count, 1)}s"})
        if max_streak > 0: summary_stats.append({"label": "Max Kill Streak", "value": max_streak})
        
        # Fallback if no specific stats trigger
        if len(summary_stats) == 0:
            summary_stats.append({"label": "Avg Enemy Takedowns", "value": round(total_kda_kills/game_count, 1)})
            summary_stats.append({"label": "Matches Profiled", "value": game_count})
        
        # The Bad
        mortality_stats = [
            {"label": "Average Mortality", "value": round(total_deaths/game_count, 1)},
            {"label": "Total Sector Deaths", "value": total_deaths}
        ]
        if outnumbered_deaths > 0:
            mortality_stats.append({"label": "Outnumbered Executions", "value": outnumbered_deaths})
            
        return {
            "summary_stats": summary_stats[:3],
            "mortality_stats": mortality_stats[:3],
            "top_victims": top_victims
        }
            
    def _get_to_victims_from_highlights(self, forensics_list):
        victim_counts = defaultdict(int)
        for f in forensics_list:
            # Check highlights for kills
            for h in f.get('highlights', []):
                if 'Killed' in h.get('event', ''): # Simple text match if structured data missing
                    # This is fallback mostly, usually we have structured victim
                    pass
            
            # Better: Check the new 'forensic_death_log' if available or existing highlights
            # For now, let's look at the 'top_victims' list if it was pre-calculated in the match analysis
            # Or parse from the 'highlights' if they have victim fields
            for h in f.get('highlights', []):
                # We need a standardized way to track victims in the forensic object
                # If the forensic object has a 'kill_list', use that
                if 'victim' in h:
                    victim_counts[h['victim']] += 1
        
        sorted_victims = sorted(victim_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [{"name": name, "count": count} for name, count in sorted_victims]
            
        return None

    def _get_lethality_analysis(self, hero_name):
        """Analyze win rate correlation with kill thresholds."""
        with self.db._get_connection() as conn:
            # Query the high-threshold stats (>= 5 kills)
            query = """
                SELECT m.result, p.stats
                FROM match_players p JOIN matches m ON p.match_id = m.id
                WHERE p.hero = ?
            """
            rows = conn.execute(query, (hero_name,)).fetchall()
            
            high_wins = 0
            high_games = 0
            low_wins = 0
            low_games = 0
            
            for r in rows:
                try:
                    stats = json.loads(r[1])
                    kills = stats.get('SoloKill', 0)
                    is_win = 'WIN' in r[0].upper() or 'VICTORY' in r[0].upper()
                    if kills >= 5:
                        high_games += 1
                        if is_win: high_wins += 1
                    else:
                        low_games += 1
                        if is_win: low_wins += 1
                except: continue
                
            high_wr = round((high_wins / high_games * 100), 1) if high_games > 0 else 0
            low_wr = round((low_wins / low_games * 100), 1) if low_games > 0 else 0
            
            return {
                "high": {"games": high_games, "wins": high_wins, "wr": high_wr},
                "low": {"games": low_games, "wins": low_wins, "wr": low_wr},
                "threshold": 5,
                "jump": round(high_wr - low_wr) if high_games > 0 and low_games > 0 else 0
            }

    def _estimated_level(self, hero):
        return 15 # Placeholder
