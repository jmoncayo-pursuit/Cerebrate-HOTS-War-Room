
import sqlite3
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.services.database import DatabaseManager

def analyze_matchup():
    heroes = {
        "blue": ["Kharazim", "Gazlowe", "Nazeebo", "E.T.C.", "Sgt. Hammer"],
        "red": ["Tychus", "Stitches", "Rehgar", "Gul'dan", "Dehaka"]
    }
    
    db = DatabaseManager()
    with db._get_connection() as conn:
        print("Analyzing Composition for Tomb of the Spider Queen...\n")
        
        # 1. Individual Hero Performance on Tomb
        print("--- Hero Performance on Tomb (Global Stats) ---")
        all_heroes = heroes["blue"] + heroes["red"]
        placeholders = ','.join(['?'] * len(all_heroes))
        
        query = f"""
            SELECT 
                p.hero, 
                COUNT(*) as games, 
                SUM(p.win) as wins
            FROM match_players p
            JOIN matches m ON p.match_id = m.id
            WHERE m.map LIKE '%Tomb%' AND p.hero IN ({placeholders})
            GROUP BY p.hero
        """
        
        rows = conn.execute(query, all_heroes).fetchall()
        stats = {row['hero']: row for row in rows}
        
        for team, team_heroes in heroes.items():
            print(f"\n{team.upper()} TEAM:")
            avg_wr = 0
            count = 0
            for h in team_heroes:
                s = stats.get(h)
                if s:
                    wr = round((s['wins'] / s['games']) * 100, 1)
                    print(f"- {h}: {wr}% ({s['games']} games)")
                    avg_wr += wr
                    count += 1
                else:
                    print(f"- {h}: No Data")
            
            if count > 0:
                print(f"  > Aggregate Win Probability: {round(avg_wr / count, 1)}%")

        # 2. Key Matchup: Hammer vs Stitches
        # (This would be complex to query directly without specific matchup tables, skipping for now)

if __name__ == "__main__":
    analyze_matchup()
