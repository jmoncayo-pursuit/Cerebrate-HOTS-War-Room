
import sqlite3
import json
import random
import time
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
        avoid_sectors = self._get_avoid_sectors(hero_name)
        
        # 3. Nemesis Analysis (Enemies)
        nemesis = self._get_nemesis(hero_name)
        
        # 4. Risk Analysis (Allies - Desyncs)
        risks = self._get_risks(hero_name)
        
        # 5. Medals
        medals = self._get_medals(hero_name)
        
        # 6. Generate Fluff
        codename = self._generate_codename(hero_name)
        verdict = self._generate_verdict(basic_stats['wr'], sectors)
        
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
            "avoidSectors": avoid_sectors,
            "risks": risks,
            "nemesis": nemesis,
            "recentPerformance": self._get_recent_performance(hero_name),
            "tacticalSummary": verdict,
            "statSources": {
                "overallWR": "SECURE_DATALINK",
                "totalGames": "SECURE_DATALINK",
                "sectors": "SECURE_DATALINK",
                "medals": "SECURE_DATALINK",
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
        query = """
            SELECT count(*), sum(case when result='WIN' then 1 else 0 end)
            FROM matches
            WHERE hero = ?
        """
        with self.db._get_connection() as conn:
            row = conn.execute(query, (hero,)).fetchone()
            games = row[0]
            wins = row[1]
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

    def _get_avoid_sectors(self, hero):
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

    def _generate_verdict(self, wr, sectors):
        status = "OPERATIONAL"
        if wr > 60: status = "GOLD STANDARD"
        elif wr < 45: status = "NEEDS REVIEW"
        
        analysis = "Subject demonstrates standard combat efficiency."
        if sectors:
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
            SELECT m.id, m.result, m.map, m.date, p.SoloKill, p.Deaths, p.Assists
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
                history.append({
                    "id": r[0],
                    "result": r[1],
                    "map": r[2],
                    "date": r[3],
                    "kills": r[4],
                    "deaths": r[5],
                    "assists": r[6]
                })
        return history

    def _estimated_level(self, hero):
        return 15 # Placeholder
