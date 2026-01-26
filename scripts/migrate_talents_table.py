import sqlite3
import json
import os

def migrate_talents_to_table():
    db_path = 'src/data/cerebrate.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Scaling: Migrating all talents from JSON blobs to match_player_talents table...")

    # Get all player records
    cursor.execute("SELECT match_id, name, hero, talents_json FROM match_players")
    players = cursor.fetchall()

    count = 0
    for p in players:
        match_id = p['match_id']
        name = p['name']
        hero = p['hero']
        talents_json = p['talents_json']

        if not talents_json:
            continue

        try:
            talents = json.loads(talents_json)
            for t in talents:
                t_lvl = t.get('level') or t.get('index') or 0
                cursor.execute('''
                    INSERT OR REPLACE INTO match_player_talents (
                        match_id, player_name, hero, level, talent_id, talent_name
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    match_id,
                    name,
                    hero,
                    t_lvl,
                    t.get('talent_id'),
                    t.get('talent_name')
                ))
            count += 1
        except Exception as e:
            print(f"Error migrating player {name} in match {match_id}: {e}")

    conn.commit()
    conn.close()
    print(f"Migration complete. Processed {count} player records.")

if __name__ == "__main__":
    migrate_talents_to_table()
