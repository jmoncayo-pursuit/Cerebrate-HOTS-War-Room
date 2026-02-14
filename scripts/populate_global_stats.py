
import sqlite3
import json
import os
import sys

# Ensure we can import from api
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.services.database import DatabaseManager

def populate_global_stats():
    print("Initializing Global Stats Population...")
    db = DatabaseManager()
    
    with db._get_connection() as conn:
        print("Calculating hero stats from match_players...")
        # Calculate stats from all match history
        stats_query = """
            SELECT 
                hero,
                COUNT(*) as games_played,
                SUM(win) as wins,
                AVG(hero_level) as avg_level
            FROM match_players
            GROUP BY hero
        """
        rows = conn.execute(stats_query).fetchall()
        
        print(f"Found {len(rows)} heroes to update.")
        
        count = 0
        for row in rows:
            hero = row['hero']
            games = row['games_played']
            wins = row['wins']
            avg_lvl = row['avg_level'] or 1.0
            
            if games == 0: continue
            
            wr = round((wins / games) * 100, 1)
            
            # Insert into global_meta_stats
            conn.execute("""
                INSERT OR REPLACE INTO global_meta_stats (hero, games_played, win_rate, kda, avg_level, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (hero, games, wr, 0.0, avg_lvl)) # KDA is expensive to calc in batch without parsing JSON, setting to 0 for now or could parse
            
            count += 1
            
        print(f"Successfully populated {count} entries in global_meta_stats.")
        conn.commit()

if __name__ == "__main__":
    populate_global_stats()
