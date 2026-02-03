import sqlite3
import json
import os
from datetime import datetime
from .schema import SCHEMA

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(base_dir, '..', '..', '..'))
            self.db_path = os.path.join(project_root, 'war_room.db')
        else:
            self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            for sql in SCHEMA:
                conn.execute(sql)
            conn.commit()

    def set_kv(self, key, value):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO kv_store (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (key, json.dumps(value))
            )

    def get_kv(self, key):
        with self._get_connection() as conn:
            row = conn.execute("SELECT value FROM kv_store WHERE key = ?", (key,)).fetchone()
            return json.loads(row['value']) if row else None

    def get_match_count(self, hero=None, map_name=None):
        query = "SELECT COUNT(*) FROM matches m"
        params = []
        if hero or map_name:
            query += " JOIN match_players p ON m.id = p.match_id WHERE 1=1"
            if hero:
                query += " AND p.hero = ?"; params.append(hero)
            if map_name:
                query += " AND m.map = ?"; params.append(map_name)
        with self._get_connection() as conn:
            return conn.execute(query, params).fetchone()[0]

    def get_matches(self, limit=100, offset=0, hero=None, map_name=None, include_players=True, match_id=None, include_details=False):
        query = "SELECT m.* FROM matches m"
        params = []
        if match_id:
            query += " WHERE m.id = ?"; params.append(match_id)
        elif hero:
            query += " JOIN match_players p ON m.id = p.match_id WHERE p.hero = ?"; params.append(hero)
            if map_name: query += " AND m.map = ?"; params.append(map_name)
        elif map_name:
            query += " WHERE m.map = ?"; params.append(map_name)
        
        query += " ORDER BY m.date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self._get_connection() as conn:
            matches = [dict(row) for row in conn.execute(query, params).fetchall()]
            
            # Alias duration to game_length for frontend compatibility
            for m in matches:
                if 'duration' in m and m['duration'] is not None:
                    try:
                        m['game_length'] = int(m['duration'])
                    except:
                        m['game_length'] = 0
                else:
                    m['game_length'] = 0
                    
            if include_players and matches:
                # 1. Collect all match IDs
                match_ids = [m['id'] for m in matches]
                placeholders = ','.join(['?'] * len(match_ids))
                
                # 2. Batch fetch all players for these matches
                p_query = f"SELECT * FROM match_players WHERE match_id IN ({placeholders})"
                all_players = conn.execute(p_query, match_ids).fetchall()
                
                # 3. Group players by match_id
                players_by_match = {}
                for p_row in all_players:
                    p = dict(p_row)
                    # Pre-process JSON fields
                    p['stats'] = json.loads(p['stats']) if p['stats'] else {}
                    p['talents'] = json.loads(p['talents']) if p['talents'] else []
                    
                    # Alias for frontend compatibility: restore name field
                    if 'player_name' in p:
                        p['name'] = p['player_name']
                    
                    m_id = p['match_id']
                    if m_id not in players_by_match:
                        players_by_match[m_id] = []
                    players_by_match[m_id].append(p)
                
                # 4. Attach to matches
                for match in matches:
                    match['players'] = players_by_match.get(match['id'], [])
                    
                    # Metadata flags for completeness checks without payload penalty
                    match['has_analysis'] = bool(match.get('analysis'))
                    match['has_raw_stats'] = bool(match.get('raw_stats'))

                    # DE-HOARDING: Only include heavy analysis/stats if explicitly requested
                    if include_details or match_id:
                        match['analysis'] = json.loads(match['analysis']) if match['analysis'] else {}
                        match['raw_stats'] = json.loads(match['raw_stats']) if match['raw_stats'] else {}
                    else:
                        match['analysis'] = None
                        match['raw_stats'] = None
            return matches

    def get_recent_matches(self, limit=7):
        return self.get_matches(limit=limit)

    def get_stats_summary(self):
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
            heroes = conn.execute("SELECT COUNT(DISTINCT hero) FROM match_players").fetchone()[0]
            return {"total_matches": total, "unique_heroes": heroes}

    def upsert_match(self, match_data):
        from .match_logic import execute_upsert
        return execute_upsert(self, match_data)

    def save_match(self, match_data):
        return self.upsert_match(match_data)

    def update_match_analysis(self, match_id, analysis_data):
        """Update the analysis field for an existing match."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE matches SET analysis = ? WHERE id = ?",
                (json.dumps(analysis_data), match_id)
            )
            conn.commit()
            return True


    def get_hero_map_stats(self, hero):
        query = """
            SELECT m.map as game_map, COUNT(*) as games, SUM(p.win) as wins
            FROM matches m JOIN match_players p ON m.id = p.match_id
            WHERE p.hero = ? GROUP BY m.map
        """
        with self._get_connection() as conn:
             rows = conn.execute(query, (hero,)).fetchall()
             return {row['game_map']: {"games": row['games'], "wins": row['wins'], "win_rate": round(row['wins']/row['games']*100, 1) if row['games'] > 0 else 0} for row in rows}

    def update_social_stats(self, match_id):
        """Update social profiles based on a newly inserted match."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            # 1. Get Commander (Discerning)
            commander = conn.execute("SELECT team, win, toon_handle FROM match_players WHERE match_id = ? AND player_name = 'Discerning'", (match_id,)).fetchone()
            if not commander: return # Only track if commander is in match
            
            commander_team = commander['team']
            commander_won = commander['win']
            commander_toon = commander['toon_handle']
            
            # 2. Update all other players
            others = conn.execute("SELECT player_name, toon_handle, hero, team, win, stats, disconnected, dc_timestamp FROM match_players WHERE match_id = ? AND toon_handle != ?", (match_id, commander_toon)).fetchall()
            for p in others:
                name = p['player_name']
                handle = p['toon_handle']
                if not handle or handle == "0-0-0": continue # Skip non-unique/AI
                
                # Check for existing profile
                row = conn.execute("SELECT total_games, hero_pool, tags, kda_avg, leaver_count FROM social_profiles WHERE toon_handle = ?", (handle,)).fetchone()
                
                # Calculate KDA
                try:
                    stats = json.loads(p['stats'])
                    kda = stats.get('Takedowns', 0) / max(1, stats.get('Deaths', 0))
                except: kda = 1.0

                if row:
                    # Update existing
                    total = row['total_games'] + 1
                    hero_pool = set(json.loads(row['hero_pool']))
                    hero_pool.add(p['hero'])
                    
                    # Update fields based on relationship
                    if p['team'] == commander_team:
                        # Update leaver status
                        new_leaver_count = row['leaver_count'] + (1 if p['disconnected'] else 0)
                        tags = json.loads(row['tags'] or '[]')
                        if new_leaver_count > 0 and 'Leaver' not in tags:
                            if 'Unreliable' not in tags: tags.append('Leaver')
                        
                        conn.execute("""
                            UPDATE social_profiles SET 
                                player_name = ?,
                                total_games = total_games + 1,
                                games_as_teammate = games_as_teammate + 1,
                                wins_as_teammate = wins_as_teammate + ?,
                                leaver_count = ?,
                                hero_pool = ?,
                                tags = ?,
                                kda_avg = (kda_avg * ? + ?) / ?,
                                last_seen = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE toon_handle = ?
                        """, (name, 1 if p['win'] else 0, new_leaver_count, json.dumps(list(hero_pool)), json.dumps(tags), row['total_games'], kda, total, handle))
                    else:
                        new_leaver_count = row['leaver_count'] + (1 if p['disconnected'] else 0)
                        tags = json.loads(row['tags'] or '[]')
                        if new_leaver_count > 0 and 'Leaver' not in tags:
                           if 'Unreliable' not in tags: tags.append('Leaver')

                        conn.execute("""
                            UPDATE social_profiles SET 
                                player_name = ?,
                                total_games = total_games + 1,
                                games_as_enemy = games_as_enemy + 1,
                                wins_against = wins_against + ?,
                                leaver_count = ?,
                                hero_pool = ?,
                                tags = ?,
                                kda_avg = (kda_avg * ? + ?) / ?,
                                last_seen = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE toon_handle = ?
                        """, (name, 1 if commander_won else 0, new_leaver_count, json.dumps(list(hero_pool)), json.dumps(tags), row['total_games'], kda, total, handle))
                else:
                    # Insert new
                    hero_pool = json.dumps([p['hero']])
                    is_leaver = 1 if p['disconnected'] else 0
                    tags = json.dumps(['Leaver']) if is_leaver else json.dumps([])
                    
                    if p['team'] == commander_team:
                        conn.execute("""
                            INSERT INTO social_profiles (toon_handle, player_name, total_games, games_as_teammate, wins_as_teammate, kda_avg, leaver_count, tags, hero_pool, last_seen)
                            VALUES (?, ?, 1, 1, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (handle, name, 1 if p['win'] else 0, kda, is_leaver, tags, hero_pool))
                    else:
                        conn.execute("""
                            INSERT INTO social_profiles (toon_handle, player_name, total_games, games_as_enemy, wins_against, kda_avg, leaver_count, tags, hero_pool, last_seen)
                            VALUES (?, ?, 1, 1, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (handle, name, 1 if commander_won else 0, kda, is_leaver, tags, hero_pool))
            conn.commit()

    def save_summary_grade(self, match_id, attempt_number, grades, feedback):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO summary_grades (match_id, attempt_number, grades, feedback) VALUES (?, ?, ?, ?)",
                (match_id, attempt_number, json.dumps(grades), feedback)
            )

    def get_summary_grade(self, match_id):
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM summary_grades WHERE match_id = ? ORDER BY attempt_number DESC LIMIT 1", (match_id,)).fetchone()
            if row:
                d = dict(row)
                d['grades'] = json.loads(d['grades'])
                return d
            return None

    def save_gold_standard(self, example_id, map_name, hero, result, summary, verdict, quality_score=5):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO gold_standards (id, map_name, hero, result, summary, verdict, quality_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (example_id, map_name, hero, result, summary, verdict, quality_score)
            )

    def get_gold_standards(self, map_name=None, hero=None, result=None, limit=5):
        query = "SELECT * FROM gold_standards WHERE 1=1"
        params = []
        if map_name: query += " AND map_name = ?"; params.append(map_name)
        if hero: query += " AND hero = ?"; params.append(hero)
        if result: query += " AND result = ?"; params.append(result)
        query += " ORDER BY quality_score DESC, timestamp DESC LIMIT ?"
        params.append(limit)
        with self._get_connection() as conn:
            return [dict(row) for row in conn.execute(query, params).fetchall()]

    def get_top_builds(self, hero, limit=5):
        query = """
            SELECT p.hero, p.talents, COUNT(*) as games, SUM(p.win) as wins
            FROM match_players p
            WHERE p.hero = ? AND p.talents IS NOT NULL AND p.talents != '[]'
            GROUP BY p.talents
            HAVING games >= 1
            ORDER BY wins DESC, games DESC
            LIMIT ?
        """
        with self._get_connection() as conn:
            rows = conn.execute(query, (hero, limit)).fetchall()
            builds = []
            for row in rows:
                d = dict(row)
                d['talents'] = json.loads(d['talents'])
                d['win_rate'] = round(d['wins'] / d['games'] * 100, 1)
                builds.append(d)
            return builds

    def get_social_profile(self, player_name):
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM social_profiles WHERE player_name = ?", (player_name,)).fetchone()
            if row:
                d = dict(row)
                d['hero_pool'] = json.loads(d['hero_pool']) if d['hero_pool'] else []
                d['tags'] = json.loads(d['tags']) if d['tags'] else []
                return d
            return None

    def get_social_network(self, min_games=2, limit=50):
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM social_profiles 
                WHERE total_games >= ? 
                ORDER BY total_games DESC LIMIT ?
            """, (min_games, limit)).fetchall()
            profiles = []
            for row in rows:
                d = dict(row)
                d['hero_pool'] = json.loads(d['hero_pool']) if d['hero_pool'] else []
                d['tags'] = json.loads(d['tags']) if d['tags'] else []
                profiles.append(d)
            return profiles
