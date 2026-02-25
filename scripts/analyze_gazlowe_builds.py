import sqlite3
import json
import collections

def get_gazlowe_builds():
    conn = sqlite3.connect('src/data/nexus_core.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get talent mapping
    cursor.execute("SELECT talent_id, tier, sort_order FROM talents WHERE hero = 'Gazlowe'")
    talent_map = {row['talent_id']: row for row in cursor.fetchall()}

    # Get matches for Gazlowe (we only care about the user 'Discerning')
    # Actually, let's get all matches where the user was the one playing Gazlowe
    # The user name seems to be 'Discerning' based on previous queries
    
    query = """
    SELECT m.id, m.result, mp.talents_json
    FROM matches m
    JOIN match_players mp ON m.id = mp.match_id
    WHERE mp.hero = 'Gazlowe' AND mp.name = 'Discerning'
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    build_stats = collections.defaultdict(lambda: {'wins': 0, 'total': 0})

    for row in rows:
        match_id = row['id']
        result = row['result'].upper() == 'WIN'
        talents_json = row['talents_json']
        
        if not talents_json:
            continue
            
        try:
            talents_list = json.loads(talents_json)
            # Talent list is chronological. We need to map it to [T1, T4, T7, T10, T13, T16, T20]
            # Tiers are 1, 2, 3, 4, 5, 6, 7
            build = ["0"] * 7
            for t in talents_list:
                t_id = t.get('talent_name')
                if t_id in talent_map:
                    tier = talent_map[t_id]['tier'] # 1-indexed
                    sort_order = talent_map[t_id]['sort_order'] # 1-3 usually
                    if 1 <= tier <= 7:
                        build[tier-1] = str(sort_order)
            
            build_str = "T" + "".join(build)
            build_stats[build_str]['total'] += 1
            if result:
                build_stats[build_str]['wins'] += 1
        except Exception as e:
            print(f"Error processing match {match_id}: {e}")

    # Format results
    results = []
    for build, stats in build_stats.items():
        wr = (stats['wins'] / stats['total']) * 100 if stats['total'] > 0 else 0
        results.append({
            'build': build,
            'total': stats['total'],
            'wins': stats['wins'],
            'win_rate': wr
        })

    # Sort by games played
    results.sort(key=lambda x: x['total'], reverse=True)
    
    return results

if __name__ == "__main__":
    builds = get_gazlowe_builds()
    print(f"{'Build':<10} | {'Games':<5} | {'Wins':<5} | {'Win Rate':<10}")
    print("-" * 40)
    for b in builds:
        if b['total'] >= 1:
            print(f"{b['build']:<10} | {b['total']:<5} | {b['wins']:<5} | {b['win_rate']:.1f}%")
