
import sqlite3
import os
from collections import defaultdict

def find_elite_candidates():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'war_room.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query all matches for the user (assuming 'local' player identification or just aggregation by hero for now)
    # Since we can't easily identify "the user" without a specific ID, we'll look for heroes played frequently in the parsed replay set.
    # Usually, the parser tracks "local" user logic, but here we will aggregate stats for all heroes found in the DB
    # and filter for high game counts which usually implies the main player if the DB is single-user focused.
    # Actually, the DB contains ALL players. 
    # **CRITICAL**: We need to identify the user. 
    # In 'AlphaSpec.jsx', we used `profile.hero_stats`.
    # I should check if there's a stored profile or just assume the heroes with the most games are the user.
    # Let's check the KV store for 'player_profile' first.
    
    cursor.execute("SELECT value FROM kv_store WHERE key = 'player_profile'")
    row = cursor.fetchone()
    
    candidates = []
    
    if row:
        import json
        profile = json.loads(row[0])
        hero_stats = profile.get('hero_stats', {})
        
        print(f"Found profile for user: {profile.get('name', 'Unknown')}")
        
        for hero, data in hero_stats.items():
            # Check for recent verified stats first, fall back to lifetime
            # The structure in previous turns seemed to be `verified_season_2025_3` or similar.
            # Let's look for keys containing 'season' or just 'lifetime'.
            
            # Simple heuristic: look for best WR with > 5 games
            total_games = 0
            wins = 0
            
            # Try to aggregate from the nested structure if possible, or just print keys to debug.
            # Assuming 'data' might have 'games' and 'wr' directly or inside a season key.
            
            # Let's just dump the keys for the top 5 heroes by game count to see structure
            pass
            
            # actually, let's use the DB query I used before for Kharazim analysis,
            # but iterate over ALL heroes.
            # But the DB query before relied on "hero=Kharazim".
            # If I query everything, I get everyone.
            # I need to filter by the user's BattleTag if possible.
            # `profile['name']` might be it.
            
    # Alternative: Query match_players, grouping by BattleTag, finding the BattleTag with the most games (which is likely the user)
    # Then analyze that user's heroes.
    
    cursor.execute("""
        SELECT player_name, COUNT(*) as game_count 
        FROM match_players 
        GROUP BY player_name 
        ORDER BY game_count DESC 
        LIMIT 1
    """)
    user_row = cursor.fetchone()
    
    if not user_row:
        print("No match data found.")
        return

    user_name = user_row['player_name']
    print(f"Identified Primary Operator: {user_name} ({user_row['game_count']} games tracked)")
    
    cursor.execute("""
        SELECT hero, COUNT(*) as games, SUM(CASE WHEN win = 1 THEN 1 ELSE 0 END) as wins
        FROM match_players
        WHERE player_name = ?
        GROUP BY hero
        HAVING games >= 5
        ORDER BY (CAST(wins AS FLOAT) / games) DESC
    """, (user_name,))
    
    rows = cursor.fetchall()
    
    print("\n--- ELITE CANDIDATE SCAN ---")
    for r in rows:
        hero = r['hero']
        games = r['games']
        wins = r['wins']
        wr = (wins / games) * 100
        
        if wr > 55.0:
            print(f"CANDIDATE: {hero} | WR: {wr:.1f}% | Games: {games}")
            
    conn.close()

if __name__ == "__main__":
    find_elite_candidates()
