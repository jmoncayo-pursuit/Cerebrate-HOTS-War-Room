
import sqlite3
import json
import os

def check_draft_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'war_room.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get a match with advanced stats
    cursor.execute("""
        SELECT m.id, m.advanced_stats, m.map
        FROM matches m
        WHERE m.advanced_stats IS NOT NULL AND m.advanced_stats != '{}'
        ORDER BY date DESC
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if not row:
        print("No matches with advanced stats found.")
        return

    print(f"--- MATCH: {row['id']} ({row['map']}) ---")
    stats = json.loads(row['advanced_stats'])
    
    print("\n[BANS STRUCTURE]")
    if 'bans' in stats:
        print(json.dumps(stats['bans'], indent=2))
    else:
        print("No bans found in advanced_stats.")

    print("\n[PICKS STRUCTURE?]")
    # Check if there is pick order info in advanced_stats or if we need to infer it
    print("Keys in advanced_stats:", list(stats.keys()))
    
    conn.close()

if __name__ == "__main__":
    check_draft_data()
