
import sqlite3
import json
import os
from collections import defaultdict

def analyze_towers_of_doom():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'war_room.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    player_name = 'Discerning'
    target_map = "Towers of Doom"
    target_hero = "Jaina"
    
    print(f"--- SECTOR ANALYSIS: {target_map.upper()} ---")
    
    # 1. Check Jaina specifically
    cursor.execute("""
        SELECT count(*) as games, sum(win) as wins
        FROM match_players p
        JOIN matches m ON p.match_id = m.id
        WHERE p.player_name = ? AND m.map = ? AND p.hero = ?
    """, (player_name, target_map, target_hero))
    
    jaina_row = cursor.fetchone()
    j_games = jaina_row['games']
    j_wins = jaina_row['wins']
    j_wr = (j_wins / j_games * 100) if j_games > 0 else 0
    
    print(f"\n[SUBJECT: JAINA]")
    print(f"Games: {j_games}")
    print(f"Win Rate: {j_wr:.1f}%")
    
    # 2. Find ACTUAL top performers on this map
    cursor.execute("""
        SELECT p.hero, count(*) as games, sum(win) as wins
        FROM match_players p
        JOIN matches m ON p.match_id = m.id
        WHERE p.player_name = ? AND m.map = ?
        GROUP BY p.hero
        HAVING games >= 2
        ORDER BY (CAST(sum(win) AS FLOAT) / count(*)) DESC, games DESC
    """, (player_name, target_map))
    
    rows = cursor.fetchall()
    
    print(f"\n[ACTUAL ELITE OPERATIVES for {target_map}]")
    for r in rows:
        wr = (r['wins'] / r['games']) * 100
        print(f"• {r['hero']}: {wr:.1f}% ({r['games']} games)")
        
    conn.close()

if __name__ == "__main__":
    analyze_towers_of_doom()
