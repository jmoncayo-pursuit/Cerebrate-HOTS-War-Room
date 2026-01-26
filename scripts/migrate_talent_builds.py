import sqlite3
import json
import os

def migrate_talent_builds():
    db_path = 'src/data/cerebrate.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all matches
    cursor.execute("SELECT id, hero FROM matches")
    matches = cursor.fetchall()

    for match in matches:
        match_id = match['id']
        hero = match['hero']
        
        # Get user's talents for this match
        # We assume 'Discerning' is the user as seen in previous queries
        cursor.execute("""
            SELECT talents_json 
            FROM match_players 
            WHERE match_id = ? AND (name = 'Discerning' OR hero = ?)
            LIMIT 1
        """, (match_id, hero))
        player_row = cursor.fetchone()
        
        if not player_row or not player_row['talents_json']:
            continue
            
        try:
            talents_list = json.loads(player_row['talents_json'])
            
            # Get talent mapping for this hero
            cursor.execute("SELECT talent_id, tier, sort_order FROM talents WHERE hero = ?", (hero,))
            t_rows = cursor.fetchall()
            t_map = {row['talent_id']: dict(row) for row in t_rows}
            
            build = ["0"] * 7
            for t in talents_list:
                t_id = t.get('talent_name')
                if t_id in t_map:
                    tier = t_map[t_id]['tier']
                    order = t_map[t_id]['sort_order']
                    if 1 <= tier <= 7:
                        build[tier-1] = str(order)
            
            talent_build_str = "T" + "".join(build)
            
            # Update match
            cursor.execute("UPDATE matches SET talent_build = ? WHERE id = ?", (talent_build_str, match_id))
            
        except Exception as e:
            print(f"Error migrating match {match_id}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_talent_builds()
