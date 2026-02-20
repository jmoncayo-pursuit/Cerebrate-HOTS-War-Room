
import sqlite3
import json
import os
from collections import defaultdict, Counter

def analyze_blackhearts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'war_room.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    player_name = 'Discerning'
    target_map = "Blackheart's Bay"
    
    print(f"--- ANALYZING SECTOR: {target_map.upper()} ---")
    
    # Get all performances on this map
    cursor.execute("""
        SELECT p.hero, p.win, p.stats
        FROM match_players p
        JOIN matches m ON p.match_id = m.id
        WHERE p.player_name = ? AND m.map = ?
    """, (player_name, target_map))
    
    rows = cursor.fetchall()
    
    hero_stats = defaultdict(lambda: {'games': 0, 'wins': 0, 'coins': 0, 'damage': 0})
    
    for r in rows:
        h = r['hero']
        STATS = json.loads(r['stats']) if r['stats'] else {}
        
        hero_stats[h]['games'] += 1
        if r['win']:
            hero_stats[h]['wins'] += 1
            
        # Track specific map mechanics
        # 'Coins' might be under specific keys or generic medals
        # We saw "EndOfMatchAwardMostCoinsPaidBoolean" before.
        if STATS.get('EndOfMatchAwardMostCoinsPaidBoolean'):
             hero_stats[h]['coins'] += 1
             
        hero_stats[h]['damage'] += STATS.get('StructureDamage', 0)

    # Sort and Display
    print(f"\n[PRIMARY CARRIES] (Sort: Win Rate > 50%)")
    
    candidates = []
    for hero, data in hero_stats.items():
        if data['games'] < 2: continue # Filter noise
        wr = (data['wins'] / data['games']) * 100
        avg_dmg = data['damage'] / data['games']
        candidates.append((hero, wr, data['games'], data['coins'], avg_dmg))
        
    # Sort by WR descending
    candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    for c in candidates:
        hero, wr, games, coins, dmg = c
        is_carry = wr >= 50.0
        medal_str = f" | 🏴‍☠️ Bosun Medals: {coins}" if coins > 0 else ""
        print(f"{'🌟' if is_carry else '⚠️'} {hero}: {wr:.1f}% WR ({games} games) {medal_str}")
        
    conn.close()

if __name__ == "__main__":
    analyze_blackhearts()
