
import sqlite3
import json
import os

def check_raw_stats():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'war_room.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get a match with raw_stats
    cursor.execute("""
        SELECT m.id, m.raw_stats, m.map
        FROM matches m
        WHERE m.raw_stats IS NOT NULL AND m.raw_stats != '{}'
        ORDER BY date DESC
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if not row:
        print("No matches with raw_stats found.")
        return

    print(f"--- MATCH: {row['id']} ({row['map']}) ---")
    
    try:
        stats = json.loads(row['raw_stats'])
    except:
        print("Failed to parse raw_stats json")
        return

    print("\n[TOP LEVEL KEYS]")
    print(list(stats.keys()))
    
    if 'bans' in stats:
        print("\n[BANS DETAILS]")
        print(stats['bans']) # Could be list or dict
        
    if 'picks' in stats:
        print("\n[PICKS DETAILS]")
        print(json.dumps(stats['picks'], indent=2))
        
    conn.close()

if __name__ == "__main__":
    check_raw_stats()
