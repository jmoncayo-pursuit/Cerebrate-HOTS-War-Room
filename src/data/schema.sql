CREATE TABLE matches (
                    id TEXT PRIMARY KEY,
                    map TEXT,
                    result TEXT,
                    hero TEXT,
                    date TEXT,
                    timestamp_iso TEXT,
                    game_length INTEGER,
                    analysis_json TEXT,
                    advanced_stats_json TEXT,
                    raw_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                , talent_build TEXT);
CREATE TABLE match_players (
                    match_id TEXT,
                    name TEXT,
                    hero TEXT,
                    team INTEGER,
                    winner BOOLEAN,
                    stats_json TEXT,
                    talents_json TEXT, banking_ledger_json TEXT,
                    PRIMARY KEY (match_id, name, hero),
                    FOREIGN KEY (match_id) REFERENCES matches (id)
                );
CREATE INDEX idx_matches_date ON matches(date);
CREATE INDEX idx_matches_hero ON matches(hero);
CREATE INDEX idx_matches_map ON matches(map);
CREATE TABLE kv_store (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
CREATE TABLE advice_log (
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
                );
CREATE TABLE strategies (
                    id TEXT PRIMARY KEY,
                    category TEXT,
                    key TEXT,
                    content_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
CREATE TABLE global_meta_stats (
                    hero TEXT PRIMARY KEY,
                    win_rate REAL,
                    popularity REAL,
                    ban_rate REAL,
                    games_played INTEGER,
                    builds_json TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
CREATE INDEX idx_advice_match ON advice_log(match_id);
CREATE INDEX idx_strategies_key ON strategies(key);
CREATE TABLE hero_stats (
                    hero TEXT PRIMARY KEY,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0,
                    mmr REAL DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    last_played TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
CREATE TABLE talents (
                talent_id TEXT PRIMARY KEY,
                hero TEXT NOT NULL,
                tier INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                icon TEXT,
                sort_order INTEGER,
                cooldown TEXT,
                is_quest INTEGER DEFAULT 0
            );
CREATE INDEX idx_talents_hero_tier ON talents(hero, tier);
CREATE INDEX idx_talents_hero ON talents(hero);
CREATE TABLE heroes (
                hero_name TEXT PRIMARY KEY,
                role TEXT,
                universe TEXT,
                release_date TEXT,
                difficulty TEXT,
                type TEXT,
                stats_json TEXT,
                abilities_json TEXT
            );
CREATE INDEX idx_heroes_role ON heroes(role);
CREATE INDEX idx_heroes_universe ON heroes(universe);
CREATE TABLE hero_patches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hero TEXT NOT NULL,
                patch_version TEXT NOT NULL,
                patch_date TEXT,
                changes_json TEXT,
                UNIQUE(hero, patch_version)
            );
CREATE TABLE sqlite_sequence(name,seq);
CREATE INDEX idx_patches_hero ON hero_patches(hero);
CREATE INDEX idx_patches_version ON hero_patches(patch_version);
CREATE INDEX idx_patches_date ON hero_patches(patch_date);
CREATE TABLE summary_grades (
                    match_id TEXT PRIMARY KEY,
                    attempt_number INTEGER,
                    strategic_accuracy INTEGER,
                    persona_consistency INTEGER,
                    map_specific_insight INTEGER,
                    overall_score REAL,
                    feedback TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
CREATE TABLE gold_standard_examples (
                    id TEXT PRIMARY KEY,
                    map TEXT,
                    hero TEXT,
                    result TEXT,
                    gold_summary TEXT,
                    gold_verdict TEXT,
                    quality_score INTEGER DEFAULT 5,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
CREATE INDEX idx_gold_standards_map ON gold_standard_examples(map);
CREATE INDEX idx_gold_standards_active ON gold_standard_examples(active);
