
import sqlite3
import json
from datetime import datetime

def check_season_start():
    conn = sqlite3.connect('war_room.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all matches from 2026
    cursor.execute("""
        SELECT date, map, hero, result, raw_stats
        FROM matches 
        WHERE date LIKE '2026%'
        ORDER BY date ASC
    """)
    matches = cursor.fetchall()
    
    print(f"Total 2026 matches found: {len(matches)}")
    
    if matches:
        first_match = matches[0]
        print(f"First match of 2026: {first_match['date']} ({first_match['map']} - {first_match['hero']})")
        
        # Check for Ranked games
        ranked_matches = []
        for m in matches:
            is_ranked = False
            if m['raw_stats']:
                try:
                    stats = json.loads(m['raw_stats'])
                    # Check for 'is_ranked' flag or Ban data which implies ranked
                    if stats.get('is_ranked') or stats.get('IsRanked'):
                        is_ranked = True
                    elif 'Ban0' in stats or 'Ban1' in stats: # Heuristic for Draft modes
                        is_ranked = True
                    
                    # Also check game_mode if present
                    if stats.get('game_mode') == 'Storm League':
                        is_ranked = True
                except:
                    pass
            
            if is_ranked:
                ranked_matches.append(m)
        
        print(f"Total Ranked matches in 2026: {len(ranked_matches)}")
        if ranked_matches:
            print(f"First RANKED match of 2026: {ranked_matches[0]['date']} ({ranked_matches[0]['map']})")

    conn.close()

if __name__ == "__main__":
    check_season_start()
