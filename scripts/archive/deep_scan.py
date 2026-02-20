
import sqlite3
import os
from collections import defaultdict

def find_specialist_candidates():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'war_room.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Identify user (Discerning)
    user_name = "Discerning" # We know this from previous step
    
    print(f"--- DEEP SCAN FOR {user_name} ---")
    
    # 1. Map Specialists (High WR on specific pools)
    cursor.execute("""
        SELECT p.hero, m.map, COUNT(*) as games, SUM(CASE WHEN p.win = 1 THEN 1 ELSE 0 END) as wins
        FROM match_players p
        JOIN matches m ON p.match_id = m.id
        WHERE p.player_name = ?
        GROUP BY p.hero, m.map
        HAVING games >= 4
        ORDER BY (CAST(wins AS FLOAT) / games) DESC
    """, (user_name,))
    
    rows = cursor.fetchall()
    print("\n[MAP SPECIALIST CANDIDATES] (>60% WR on specific sector)")
    for r in rows:
        wr = (r['wins'] / r['games']) * 100
        if wr >= 60.0:
            print(f"- {r['hero']} on {r['map']}: {wr:.1f}% ({r['wins']}/{r['games']})")

    # 2. High Volume Veterans (>50% WR, >30 games) - excluding top 3 already known
    print("\n[VETERAN CANDIDATES] (Reliable Backbone)")
    cursor.execute("""
        SELECT hero, COUNT(*) as games, SUM(CASE WHEN win = 1 THEN 1 ELSE 0 END) as wins
        FROM match_players
        WHERE player_name = ?
        GROUP BY hero
        HAVING games >= 20
        ORDER BY games DESC
    """, (user_name,))
    
    vets = cursor.fetchall()
    known_elites = ["Gazlowe", "Kharazim", "Raynor"]
    
    for r in vets:
        hero = r['hero']
        wr = (r['wins'] / r['games']) * 100
        if hero not in known_elites and wr > 48.0:
            print(f"- {hero}: {wr:.1f}% WR over {r['games']} games")
            
    conn.close()

if __name__ == "__main__":
    find_specialist_candidates()
