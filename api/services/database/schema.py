SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS matches (
        id TEXT PRIMARY KEY,
        map TEXT,
        hero TEXT,
        result TEXT,
        date TEXT,
        duration TEXT,
        winning_team INTEGER,
        pipeline_version TEXT,
        analysis TEXT,
        raw_stats TEXT,
        metadata TEXT
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_matches_map ON matches(map)",
    "CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(date)",
    """
    CREATE TABLE IF NOT EXISTS match_players (
        match_id TEXT,
        player_name TEXT,
        toon_handle TEXT, -- Format: region-realm-id
        hero TEXT,
        team INTEGER,
        win INTEGER,
        hero_level INTEGER,
        account_level INTEGER,
        rank TEXT,
        stats TEXT,
        talents TEXT,
        FOREIGN KEY(match_id) REFERENCES matches(id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_player_match ON match_players(match_id)",
    "CREATE INDEX IF NOT EXISTS idx_player_hero ON match_players(hero)",
    "CREATE INDEX IF NOT EXISTS idx_player_name ON match_players(player_name)",
    "CREATE INDEX IF NOT EXISTS idx_player_toon ON match_players(toon_handle)",
    """
    CREATE TABLE IF NOT EXISTS kv_store (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS summary_grades (
         match_id TEXT,
         attempt_number INTEGER,
         grades TEXT,
         feedback TEXT,
         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
         PRIMARY KEY (match_id, attempt_number)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS gold_standards (
        id TEXT PRIMARY KEY,
        map_name TEXT,
        hero TEXT,
        result TEXT,
        summary TEXT,
        verdict TEXT,
        quality_score INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS global_meta_stats (
        hero TEXT PRIMARY KEY,
        games_played INTEGER,
        win_rate REAL,
        kda REAL,
        avg_level REAL,
        builds_json TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS strategies (
        id TEXT PRIMARY KEY,
        content_json TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS global_map_stats (
        map_name TEXT PRIMARY KEY,
        games_played INTEGER,
        wins INTEGER,
        losses INTEGER,
        win_rate REAL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS global_account_stats (
        key TEXT PRIMARY KEY,
        value REAL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS seasonal_map_stats (
        map_name TEXT PRIMARY KEY,
        games_played INTEGER,
        wins INTEGER,
        losses INTEGER,
        win_rate REAL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS social_profiles (
        toon_handle TEXT PRIMARY KEY,
        player_name TEXT, -- Last seen display name
        total_games INTEGER DEFAULT 0,
        games_as_teammate INTEGER DEFAULT 0,
        wins_as_teammate INTEGER DEFAULT 0,
        games_as_enemy INTEGER DEFAULT 0,
        wins_against INTEGER DEFAULT 0,
        kda_avg REAL,
        hero_pool TEXT, -- JSON Hero list
        tags TEXT, -- JSON Tags
        notes TEXT,
        last_seen DATETIME,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
]
