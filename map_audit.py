import sqlite3
import json
import sys

try:
    conn = sqlite3.connect('src/data/cerebrate.db')
    conn.row_factory = sqlite3.Row
    maps_query = conn.execute("SELECT DISTINCT map FROM matches WHERE map IS NOT NULL").fetchall()
    maps = [r['map'] for r in maps_query]
    
    results = {}
    for m in maps:
        rows = conn.execute("""
            SELECT hero, COUNT(*) as games, 
                   SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) as wins, 
                   ROUND(100.0 * SUM(CASE WHEN result='WIN' THEN 1 ELSE 0 END) / COUNT(*), 1) as wr 
            FROM matches 
            WHERE map=? 
            GROUP BY hero 
            ORDER BY wr DESC, games DESC 
            LIMIT 3
        """, (m,)).fetchall()
        results[m] = [dict(r) for r in rows]

    print(json.dumps(results, indent=2))
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
