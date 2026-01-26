
import sqlite3
import json
import os

DB_PATH = "src/data/cerebrate.db"

def check_players():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT value FROM kv_store WHERE key = 'player_interactions'").fetchone()
    conn.close()
    
    if not row:
        print("No player_interactions found")
        return
        
    interactions = json.loads(row[0])
    target_names = ["RichAtreides", "pepecharly19", "SunDan", "Tvoun", "Chinaski", "JohnTitor", "TitanChicken", "elManny", "Zeratool"]
    
    print(f"Total interactions: {len(interactions)}")
    
    found = []
    for pid, data in interactions.items():
        name = data.get('name', '')
        if name in target_names:
            found.append((name, data))
            
    if not found:
        print("None of the target players found in database.")
    else:
        for name, data in found:
            print(f"Found: {name}")
            print(f"  With: {data.get('wins_with', 0)}/{data.get('total_with', 0)}")
            print(f"  Against: {data.get('wins_against', 0)}/{data.get('total_against', 0)}")

if __name__ == "__main__":
    check_players()
