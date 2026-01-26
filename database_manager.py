import sqlite3
import json
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Use absolute path relative to this file to be bulletproof
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, 'src', 'data', 'cerebrate.db')
        else:
            self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the database schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            # Matches Table - Primary metadata and parsed results
            conn.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    id TEXT PRIMARY KEY,
                    map TEXT,
                    result TEXT,
                    hero TEXT,
                    date TEXT,
                    timestamp_iso TEXT,
                    game_length INTEGER,
                    analysis_json TEXT,
                    advanced_stats_json TEXT,
                    talent_build TEXT,
                    pipeline_version TEXT,
                    raw_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Migrate existing tables: Add columns if they don't exist
            try:
                conn.execute('ALTER TABLE matches ADD COLUMN talent_build TEXT')
            except sqlite3.OperationalError: pass
            
            try:
                conn.execute('ALTER TABLE matches ADD COLUMN pipeline_version TEXT')
            except sqlite3.OperationalError: pass
            
            # Players Table - Performance data per player per match
            conn.execute('''
                CREATE TABLE IF NOT EXISTS match_players (
                    match_id TEXT,
                    name TEXT,
                    hero TEXT,
                    team INTEGER,
                    winner BOOLEAN,
                    stats_json TEXT,
                    talents_json TEXT,
                    banking_ledger_json TEXT,
                    PRIMARY KEY (match_id, name, hero),
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                )
            ''')
            
            # Migrate existing tables: Add banking_ledger_json column if it doesn't exist
            try:
                conn.execute('ALTER TABLE match_players ADD COLUMN banking_ledger_json TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Advice Log Table - Record AI recommendations and user feedback
            conn.execute('''
                CREATE TABLE IF NOT EXISTS advice_log (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    match_id TEXT,
                    map TEXT,
                    hero TEXT,
                    advice_type TEXT,
                    content TEXT,
                    rating INTEGER,
                    feedback TEXT,
                    outcome TEXT,
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                )
            ''')

            # Strategies Table - Map/Hero specific strategic notes
            conn.execute('''
                CREATE TABLE IF NOT EXISTS strategies (
                    id TEXT PRIMARY KEY,
                    category TEXT,
                    key TEXT,
                    content_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Global Meta Stats - For comparison and "Spam These" logic
            conn.execute('''
                CREATE TABLE IF NOT EXISTS global_meta_stats (
                    hero TEXT PRIMARY KEY,
                    win_rate REAL,
                    popularity REAL,
                    ban_rate REAL,
                    games_played INTEGER,
                    builds_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Summary Grades Table - Referee system quality control
            conn.execute('''
                CREATE TABLE IF NOT EXISTS summary_grades (
                    match_id TEXT PRIMARY KEY,
                    attempt_number INTEGER,
                    strategic_accuracy INTEGER,
                    persona_consistency INTEGER,
                    map_specific_insight INTEGER,
                    overall_score REAL,
                    feedback TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Gold Standard Examples Table - Few-shot learning examples
            conn.execute('''
                CREATE TABLE IF NOT EXISTS gold_standard_examples (
                    id TEXT PRIMARY KEY,
                    map TEXT,
                    hero TEXT,
                    result TEXT,
                    gold_summary TEXT,
                    gold_verdict TEXT,
                    quality_score INTEGER DEFAULT 5,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # KV Store for arbitrary profile data and cache
            conn.execute('''
                CREATE TABLE IF NOT EXISTS kv_store (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            
            # Personal Hero Stats - Derived from match history and profile
            conn.execute('''
                CREATE TABLE IF NOT EXISTS hero_stats (
                    hero TEXT PRIMARY KEY,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    mmr REAL DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    last_played TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Match Player Talents - Flattened talent choices for SQL analysis
            conn.execute('''
                CREATE TABLE IF NOT EXISTS match_player_talents (
                    match_id TEXT,
                    player_name TEXT,
                    hero TEXT,
                    level INTEGER,
                    talent_id TEXT,
                    talent_name TEXT,
                    PRIMARY KEY (match_id, player_name, hero, level),
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                )
            ''')
            
            # Indices for lightning-fast lookups
            conn.execute('CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_matches_hero ON matches(hero)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_matches_map ON matches(map)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_advice_match ON advice_log(match_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_strategies_key ON strategies(key)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_gold_standards_map ON gold_standard_examples(map)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_gold_standards_active ON gold_standard_examples(active)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_player_talents_hero ON match_player_talents(hero)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_player_talents_name ON match_player_talents(talent_name)')
            
            conn.commit()

    def upsert_match(self, match_data):
        """Insert or update a match and its player records."""
        # Handle both 'id' and 'match_id' for parser compatibility
        match_id = match_data.get('id') or match_data.get('match_id')
        if not match_id:
            return False

        with self._get_connection() as conn:
            try:
                # Identify User's Talent Build
                user_hero = match_data.get('hero')
                user_talents = []
                players = match_data.get('players', [])
                
                # First try to find by specific name if available
                user_name = os.environ.get('PLAYER_NAME', 'Discerning')
                user_found = False
                for p in players:
                    if p.get('name') == user_name and p.get('hero') == user_hero:
                        user_talents = p.get('talents', [])
                        user_found = True
                        break
                
                # Fallback to just hero if name not found
                if not user_found and user_hero:
                    for p in players:
                        if p.get('hero') == user_hero:
                            user_talents = p.get('talents', [])
                            break
                
                talent_build_str = ""
                if user_talents:
                    # Map to T123... format
                    # Get talent mapping from DB
                    t_rows = conn.execute("SELECT talent_id, tier, sort_order FROM talents WHERE hero = ?", (user_hero,)).fetchall()
                    t_map = {row['talent_id']: dict(row) for row in t_rows}
                    
                    build = ["0"] * 7
                    for t in user_talents:
                        t_id = t.get('talent_name')
                        if t_id in t_map:
                            tier = t_map[t_id]['tier']
                            order = t_map[t_id]['sort_order']
                            if 1 <= tier <= 7:
                                build[tier-1] = str(order)
                    talent_build_str = "T" + "".join(build)

                # 1. Insert Match
                conn.execute('''
                    INSERT INTO matches (
                        id, map, result, hero, date, timestamp_iso, 
                        game_length, analysis_json, advanced_stats_json, talent_build, 
                        pipeline_version, raw_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        map=excluded.map,
                        result=excluded.result,
                        hero=excluded.hero,
                        date=excluded.date,
                        timestamp_iso=excluded.timestamp_iso,
                        game_length=excluded.game_length,
                        analysis_json=excluded.analysis_json,
                        advanced_stats_json=excluded.advanced_stats_json,
                        talent_build=excluded.talent_build,
                        pipeline_version=excluded.pipeline_version,
                        raw_json=excluded.raw_json
                ''', (
                    match_id, 
                    match_data.get('map'),
                    match_data.get('result'),
                    match_data.get('hero'),
                    match_data.get('date') or match_data.get('timestamp_iso'),
                    match_data.get('timestamp_iso') or match_data.get('date'),
                    match_data.get('game_length'),
                    json.dumps(match_data.get('analysis', {})),
                    json.dumps(match_data.get('advanced_stats', {})),
                    talent_build_str,
                    match_data.get('pipeline_version') or "1.0.0",
                    json.dumps(match_data.get('raw_json', {}))
                ))

                # 2. Insert Players and Talents
                for p in players:
                    p_name = p.get('name')
                    p_hero = p.get('hero')
                    conn.execute('''
                        INSERT INTO match_players (
                            match_id, name, hero, team, winner, stats_json, talents_json, banking_ledger_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(match_id, name, hero) DO UPDATE SET
                            team=excluded.team,
                            winner=excluded.winner,
                            stats_json=excluded.stats_json,
                            talents_json=excluded.talents_json,
                            banking_ledger_json=excluded.banking_ledger_json
                    ''', (
                        match_id,
                        p_name,
                        p_hero,
                        p.get('team'),
                        p.get('winner'),
                        json.dumps(p.get('stats', p.get('kv_stats', {}))),
                        json.dumps(p.get('talents', [])),
                        json.dumps(p.get('banking_ledger', []))
                    ))

                    # Insert Talents into flattened table
                    talents = p.get('talents', [])
                    for t in talents:
                        # Replays don't always give level, we infer from common tiers or skip level if unknown
                        # A better approach is to store level if provided, otherwise using 'level' as a unique slot index
                        # In Hots replays, talents come in levels 1, 4, 7, 10, 13, 16, 20
                        t_lvl = t.get('level') or t.get('index') or 0
                        conn.execute('''
                            INSERT OR REPLACE INTO match_player_talents (
                                match_id, player_name, hero, level, talent_id, talent_name
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            match_id,
                            p_name,
                            p_hero,
                            t_lvl,
                            t.get('talent_id'),
                            t.get('talent_name')
                        ))
                
                conn.commit()
                return True
            except Exception as e:
                print(f"Database upsert error: {e}")
                return False

    def get_match_count(self, hero=None, map_name=None):
        """Get total count of matches matching filters (for pagination)."""
        query = "SELECT COUNT(*) FROM matches WHERE 1=1"
        params = []
        
        if hero:
            query += " AND hero = ?"
            params.append(hero)
        if map_name:
            query += " AND map = ?"
            params.append(map_name)
        
        with self._get_connection() as conn:
            result = conn.execute(query, params).fetchone()
            return result[0] if result else 0
    
    def get_matches(self, limit=100, offset=0, hero=None, map_name=None, include_players=True, match_id=None):
        """Query matches with filters."""
        query = "SELECT * FROM matches WHERE 1=1"
        params = []
        
        if match_id:
            query += " AND id = ?"
            params.append(match_id)
        if hero:
            query += " AND hero = ?"
            params.append(hero)
        if map_name:
            query += " AND map = ?"
            params.append(map_name)
            
        query += " ORDER BY date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            matches = []
            for row in rows:
                m = dict(row)
                # Reconstruct JSON fields
                m['analysis'] = json.loads(m['analysis_json']) if m['analysis_json'] else {}
                m['advanced_stats'] = json.loads(m['advanced_stats_json']) if m['advanced_stats_json'] else {}
                
                # Ensure both date and timestamp_iso are present for frontend compatibility
                if not m.get('timestamp_iso') and m.get('date'):
                    m['timestamp_iso'] = m['date']
                if not m.get('date') and m.get('timestamp_iso'):
                    m['date'] = m['timestamp_iso']
                
                if include_players:
                    # Fetch players for this match
                    players = conn.execute('SELECT * FROM match_players WHERE match_id = ?', (m['id'],)).fetchall()
                    m['players'] = []
                    for p_row in players:
                        p = dict(p_row)
                        p['stats'] = json.loads(p['stats_json']) if p['stats_json'] else {}
                        p['talents'] = json.loads(p['talents_json']) if p['talents_json'] else []
                        p['banking_ledger'] = json.loads(p['banking_ledger_json']) if p.get('banking_ledger_json') else []
                        # Clean up internal JSON fields
                        p.pop('stats_json', None)
                        p.pop('talents_json', None)
                        p.pop('banking_ledger_json', None)
                        m['players'].append(p)
                else:
                    m['players'] = []
                
                # Clean up internal JSON fields (frontend doesn't need them)
                m.pop('analysis_json', None)
                m.pop('advanced_stats_json', None)
                
                matches.append(m)
            return matches

    def get_recent_matches(self, limit=7):
        """Compatibility wrapper for legacy calls."""
        return self.get_matches(limit=limit)

    def get_stats_summary(self):
        """Get high-level stats for AI context without dumping thousands of rows."""
        with self._get_connection() as conn:
            total_matches = conn.execute('SELECT COUNT(*) FROM matches').fetchone()[0]
            hero_counts = conn.execute('SELECT hero, COUNT(*) as games, SUM(CASE WHEN result="WIN" THEN 1 ELSE 0 END) as wins FROM matches GROUP BY hero').fetchall()
            map_counts = conn.execute('SELECT map, COUNT(*) as games, SUM(CASE WHEN result="WIN" THEN 1 ELSE 0 END) as wins FROM matches GROUP BY map').fetchall()
            
            return {
                "total_records": total_matches,
                "hero_performance": [dict(h) for h in hero_counts],
                "map_performance": [dict(m) for m in map_counts]
            }

    def save_match(self, match_data):
        """Forward to upsert_match for legacy compatibility."""
        return self.upsert_match(match_data)
        
    def set_kv(self, key, value):
        with self._get_connection() as conn:
            conn.execute('INSERT OR REPLACE INTO kv_store (key, value) VALUES (?, ?)', (key, json.dumps(value)))
            conn.commit()
            
    def get_kv(self, key):
        with self._get_connection() as conn:
            row = conn.execute('SELECT value FROM kv_store WHERE key = ?', (key,)).fetchone()
            return json.loads(row[0]) if row else None

    def get_hero_map_stats(self, hero):
        """Aggregate map statistics for a specific hero from match history."""
        with self._get_connection() as conn:
            rows = conn.execute('''
                SELECT map, COUNT(*) as games, SUM(CASE WHEN result="WIN" THEN 1 ELSE 0 END) as wins
                FROM matches
                WHERE hero = ?
                GROUP BY map
            ''', (hero,)).fetchall()
            
            stats = []
            for row in rows:
                games = row['games']
                wins = row['wins']
                stats.append({
                    "map": row['map'],
                    "games_played": games,
                    "win_rate": (wins / games) * 100 if games > 0 else 0,
                    "source": "Replay Archive"
                })
            return stats

    def save_summary_grade(self, match_id, attempt_number, grades, feedback):
        """Save referee grading results for a match summary."""
        with self._get_connection() as conn:
            overall = (grades.get('strategic_accuracy', 0) + 
                      grades.get('persona_consistency', 0) + 
                      grades.get('map_specific_insight', 0)) / 3.0
            conn.execute('''
                INSERT OR REPLACE INTO summary_grades 
                (match_id, attempt_number, strategic_accuracy, persona_consistency, 
                 map_specific_insight, overall_score, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (match_id, attempt_number, 
                  grades.get('strategic_accuracy', 0),
                  grades.get('persona_consistency', 0),
                  grades.get('map_specific_insight', 0),
                  overall, feedback))
            conn.commit()
    
    def get_summary_grade(self, match_id):
        """Get the latest grade for a match summary."""
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT * FROM summary_grades WHERE match_id = ? ORDER BY attempt_number DESC LIMIT 1',
                (match_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def save_gold_standard(self, example_id, map_name, hero, result, summary, verdict, quality_score=5):
        """Save a gold standard example for few-shot learning."""
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO gold_standard_examples
                (id, map, hero, result, gold_summary, gold_verdict, quality_score, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', (example_id, map_name, hero, result, summary, verdict, quality_score))
            conn.commit()
    
    def get_gold_standards(self, map_name=None, hero=None, result=None, limit=5):
        """Get gold standard examples for few-shot learning."""
        with self._get_connection() as conn:
            query = 'SELECT * FROM gold_standard_examples WHERE active = 1'
            params = []
            
            if map_name:
                query += ' AND map = ?'
                params.append(map_name)
            if hero:
                query += ' AND hero = ?'
                params.append(hero)
            if result:
                query += ' AND result = ?'
                params.append(result)
            
            query += ' ORDER BY quality_score DESC, created_at DESC LIMIT ?'
            params.append(limit)
            
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
    
    def get_top_builds(self, hero, limit=5):
        """Find best-performing talent builds for a hero from match history."""
        with self._get_connection() as conn:
            # Check if talent_build column has any data
            has_build_data = conn.execute('SELECT COUNT(*) FROM matches WHERE hero = ? AND talent_build != ""', (hero,)).fetchone()[0] > 0
            
            if has_build_data:
                rows = conn.execute('''
                    SELECT talent_build as build_code, COUNT(*) as games, SUM(CASE WHEN result="WIN" THEN 1 ELSE 0 END) as wins
                    FROM matches
                    WHERE hero = ? AND talent_build != ""
                    GROUP BY talent_build
                    HAVING games >= 1
                    ORDER BY wins DESC, games DESC
                    LIMIT ?
                ''', (hero, limit)).fetchall()
                
                return [{
                    "build_code": row['build_code'],
                    "games": row['games'],
                    "win_rate": round((row['wins'] / row['games']) * 100, 1) if row['games'] > 0 else 0
                } for row in rows]
            else:
                # Fallback to reconstructing from match_players (legacy or other players)
                rows = conn.execute('''
                    SELECT mp.talents_json, COUNT(*) as games, SUM(CASE WHEN m.result="WIN" THEN 1 ELSE 0 END) as wins
                    FROM match_players mp
                    JOIN matches m ON mp.match_id = m.id
                    WHERE mp.hero = ?
                    GROUP BY mp.talents_json
                    HAVING games >= 2
                    ORDER BY wins DESC, games DESC
                    LIMIT ?
                ''', (hero, limit)).fetchall()
                
                # Mapping helper
                t_rows = conn.execute("SELECT talent_id, tier, sort_order FROM talents WHERE hero = ?", (hero,)).fetchall()
                t_map = {row['talent_id']: dict(row) for row in t_rows}
                
                builds = []
                for row in rows:
                    games = row['games']
                    wins = row['wins']
                    try:
                        talents = json.loads(row['talents_json'])
                        build = ["0"] * 7
                        for t in talents:
                            t_id = t.get('talent_name')
                            if t_id in t_map:
                                tier = t_map[t_id]['tier']
                                order = t_map[t_id]['sort_order']
                                if 1 <= tier <= 7:
                                    build[tier-1] = str(order)
                        build_code = "T" + "".join(build)
                    except:
                        build_code = "UNKNOWN"
                        
                    builds.append({
                        "build_code": build_code,
                        "games": games,
                        "win_rate": round((wins / games) * 100, 1) if games > 0 else 0
                    })
                return builds
