import json

def execute_upsert(db, match_data):
    """
    Persist match and player data to SQLite.
    Expected keys: id (or match_id), map, date, game_length (or duration), players, etc.
    """
    m = match_data
    # Normalization
    mid = m.get('id') or m.get('match_id')
    date = m.get('date') or m.get('timestamp_iso')
    duration = m.get('game_length') or m.get('duration')
    
    with db._get_connection() as conn:
        # 1. Fetch existing analysis if it exists
        cursor = conn.execute("SELECT analysis FROM matches WHERE id = ?", (mid,))
        row = cursor.fetchone()
        existing_analysis = row['analysis'] if row and row['analysis'] else '{}'
        
        # 2. Decide which analysis to use
        new_analysis = m.get('analysis')
        final_analysis = json.dumps(new_analysis) if (new_analysis and new_analysis.get('verdict') != "ANALYSIS FAILED") else existing_analysis

        # 3. Insert/Replace Match
        conn.execute(
            "INSERT OR REPLACE INTO matches (id, map, hero, result, date, duration, winning_team, analysis, raw_stats) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                mid, m.get('map'), m.get('hero'), m.get('result'), date, duration, m.get('winning_team'),
                final_analysis, json.dumps(m.get('advanced_stats', {}))
            )
        )
        
        # Clear existing player data for this match
        conn.execute("DELETE FROM match_players WHERE match_id = ?", (mid,))
        
        # Insert Players
        for p in m.get('players', []):
            conn.execute(
                "INSERT INTO match_players (match_id, player_name, toon_handle, hero, team, win, hero_level, account_level, rank, stats, talents) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    mid, p['name'], p.get('toon_handle'), p['hero'], p['team'], 1 if p['win'] else 0,
                    p.get('hero_level'), p.get('account_level'), p.get('rank'),
                    json.dumps(p.get('stats', {})), json.dumps(p.get('talents', []))
                )
            )
        conn.commit()
    
    # Post-processing: Update Social Intelligence
    db.update_social_stats(mid)
    
    return True
