
import sqlite3
import json

def detail_2026_matches():
    conn = sqlite3.connect('war_room.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get matches from 2026 and examine raw_stats
    cursor.execute("""
        SELECT date, map, hero, raw_stats, analysis
        FROM matches 
        WHERE date LIKE '2026%'
        ORDER BY date ASC
    """)
    matches = cursor.fetchall()
    
    print(f"Total 2026 matches: {len(matches)}")
    if matches:
        print(f"Sample First 5 Matches:")
        for i, m in enumerate(matches[:5]):
            raw_stats = m['raw_stats'] if m['raw_stats'] else "{}"
            try:
                stats = json.loads(raw_stats)
            except:
                stats = {}
            print(f"  Match {i+1}: {m['date']} - {m['map']} - {m['hero']}")
            print(f"    Raw Stats Keys: {list(stats.keys())[:10]}")
            if 'game_mode' in stats:
                print(f"    Game Mode: {stats['game_mode']}")
            if 'IsRanked' in stats:
                print(f"    IsRanked: {stats['IsRanked']}")

        print("\nSearching for potential season indicators in raw_stats...")
        ranked_start_date = None
        for m in matches:
            stats = json.loads(m['raw_stats'] or '{}')
            # Look for indicators
            if 'game_mode' in stats and stats['game_mode'] == 'Storm League':
                if not ranked_start_date:
                    ranked_start_date = m['date']
                    print(f"Found first 'Storm League' match: {m['date']}")
                    break
            if 'IsRanked' in stats and stats['IsRanked']:
                if not ranked_start_date:
                    ranked_start_date = m['date']
                    print(f"Found first 'IsRanked' match: {m['date']}")
                    break
                    
        # Also check metadata if present
        # ... (metadata column not in my initial memory schema but let's check if present)
        cursor.execute("PRAGMA table_info(matches)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'metadata' in cols:
             matches_meta = cursor.execute("SELECT date, metadata FROM matches WHERE date LIKE '2026%' AND metadata IS NOT NULL AND metadata != '{}' LIMIT 5").fetchall()
             if matches_meta:
                 print("\nMetadata samples found:")
                 for mm in matches_meta:
                     print(f"  {mm['date']}: {mm['metadata']}")

    conn.close()

if __name__ == "__main__":
    detail_2026_matches()
