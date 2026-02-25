
import sqlite3
import json

def get_first_ranked_game():
    conn = sqlite3.connect('nexus_command_lab.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get matches from 2026 and examine raw_stats for bans
    cursor.execute("""
        SELECT date, map, hero, raw_stats
        FROM matches 
        WHERE date LIKE '2026%'
        ORDER BY date ASC
    """)
    matches = cursor.fetchall()
    
    first_ban_game = None
    
    for m in matches:
        raw = m['raw_stats']
        if raw and raw != '{}':
            try:
                stats = json.loads(raw)
                # Check for bans
                if 'bans' in stats and stats['bans'] and len(stats['bans']) > 0:
                    first_ban_game = m
                    break
            except:
                continue

    if first_ban_game:
        print(f"First 2026 match with BANS (likely Ranked): {first_ban_game['date']} ({first_ban_game['map']})")
    else:
        print("No 2026 matches with 'bans' array found in raw_stats.")
        
    conn.close()

if __name__ == "__main__":
    get_first_ranked_game()
