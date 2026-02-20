
import sqlite3
import json
import os

def check_awards_structure():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'war_room.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get 5 random matches for Discerning to inspect stats structure
    cursor.execute("""
        SELECT m.map, p.hero, p.stats
        FROM match_players p
        JOIN matches m ON p.match_id = m.id
        WHERE p.player_name = 'Discerning' AND p.stats IS NOT NULL
        LIMIT 5
    """)
    
    rows = cursor.fetchall()
    
    print("--- STATS STRUCTURE INSPECTION ---")
    for r in rows:
        print(f"\nMap: {r['map']} | Hero: {r['hero']}")
        try:
            stats = json.loads(r['stats'])
            # Print keys to see if Award is there
            print("Keys:", list(stats.keys()))
            
            # Check for specific keys mentioned by user
            relevant_keys = ['MatchAwards', 'GemsTurnedIn', 'PhysicalDamage', 'SiegeDamage', 'StructureDamage']
            for k in relevant_keys:
                if k in stats:
                    print(f"- {k}: {stats[k]}")
                    
            # Sometimes detailed scores are nested?
            # Replay parsers often flatten them. Let's see.
        except:
            print("Could not parse stats JSON")
            
    conn.close()

if __name__ == "__main__":
    check_awards_structure()
