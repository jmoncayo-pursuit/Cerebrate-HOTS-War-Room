
import sqlite3
import json
import os
from collections import Counter

def analyze_medals():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'war_room.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Analyze for Discerning
    player_name = 'Discerning'
    
    cursor.execute("""
        SELECT p.stats, m.map
        FROM match_players p
        JOIN matches m ON p.match_id = m.id
        WHERE p.player_name = ? AND p.stats IS NOT NULL
    """, (player_name,))
    
    rows = cursor.fetchall()
    
    medal_counts = Counter()
    total_games = len(rows)
    
    award_map = {
        'EndOfMatchAwardMostCurseDamageDoneBoolean': 'Master of the Curse (Cannoneer)',
        'EndOfMatchAwardMostCoinsPaidBoolean': 'Blackheart\'s Bosun (Coins)',
        'EndOfMatchAwardMostGemsTurnedInBoolean': 'Spider Queen\'s Consort (Gems)',
        'EndOfMatchAwardMostImmortalDamageBoolean': 'Immortal Slayer',
        'EndOfMatchAwardMostDamageToPlantsBoolean': 'Garden Terrorist',
        'EndOfMatchAwardMostNukeDamageDoneBoolean': 'Da Bomb (Nukes)',
        'EndOfMatchAwardMostDragonShrinesCapturedBoolean': 'Dragon Master',
        'EndOfMatchAwardMostTimeInTempleBoolean': 'Temple Guardian',
        'EndOfMatchAwardMostAltarDamageDone': 'Altar Guardian',
        'EndOfMatchAwardMVPBoolean': 'MVP'
    }
    
    for r in rows:
        try:
            stats = json.loads(r['stats'])
            for key, label in award_map.items():
                if stats.get(key) == 1 or stats.get(key) is True:
                    medal_counts[label] += 1
        except:
            continue
            
    print(f"--- MEDAL ANALYSIS FOR {player_name.upper()} ---")
    print(f"Total Games Analyzed: {total_games}")
    print("\n[OBJECTIVE SPECIALIST AWARDS]")
    for award, count in medal_counts.most_common():
        print(f"- {award}: {count} times")
        
    conn.close()

if __name__ == "__main__":
    analyze_medals()
