
import sqlite3
import json
from collections import defaultdict

conn = sqlite3.connect('war_room.db')
cursor = conn.cursor()
cursor.execute("SELECT hero, stats FROM match_players WHERE stats IS NOT NULL")
rows = cursor.fetchall()

hero_stats = defaultdict(list)
for hero, stats_json in rows:
    try:
        stats = json.loads(stats_json)
        hero_stats[hero].append(stats)
    except:
        continue

# Find interesting keys (non-standard ones)
standard_keys = {
    'AbilitiesFired', 'Assists', 'ClutchHealsPerformed', 'DamageTaken', 'Deaths', 
    'ExperienceContribution', 'GameScore', 'Healing', 'HeroDamage', 'Level', 
    'MetaExperience', 'MinionXP', 'SelfHealing', 'SiegeDamage', 'SoloKill', 
    'StructureDamage', 'Takedowns', 'TimeCCdEnemyHeroes', 'TimeSpentDead', 
    'TownKills', 'VengeancesPerformed'
}

for hero, stats_list in hero_stats.items():
    all_keys = set().union(*[s.keys() for s in stats_list])
    interesting = [k for k in all_keys if k not in standard_keys and not k.startswith('EndOfMatchAward')]
    if interesting:
        # Check frequency of these keys
        counts = {k: sum(1 for s in stats_list if k in s) for k in interesting}
        # Only show keys that appear in at least 20% of games for that hero
        common = [k for k, count in counts.items() if count / len(stats_list) > 0.2]
        if common:
            print(f"{hero}: {common}")
conn.close()
