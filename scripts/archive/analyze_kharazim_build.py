
import json
from collections import Counter
from api.services.database import DatabaseManager

def analyze_kharazim_wins(hero_name, map_name):
    db = DatabaseManager()
    matches = db.get_matches(limit=1000, hero=hero_name, map_name=map_name, include_players=True)
    
    winning_builds = []
    
    for m in matches:
        players = m.get('players', [])
        kharazim_players = [p for p in players if p['hero'] == hero_name]
        
        for p in kharazim_players:
            if p['win']:
                # Extract talent names or IDs
                # talents is a list of objects usually: [{'talent_name': '...', 'timestamp': ...}, ...]
                # We need to sort them by tier (level 1, 4, 7, 10, 13, 16, 20) roughly.
                # Since we don't have tier info directly in the JSON without looking up, 
                # we'll just gather the list of names.
                # However, for a "spec", user usually wants the standard 1,4,7... format.
                # We will list the talent names in order of acquisition (which is usually level order).
                
                # Check formatting
                talents = p.get('talents', [])
                # Sort by timestamp just in case
                talents.sort(key=lambda x: x['timestamp'])
                
                build_names = [t['talent_name'] for t in talents if t['talent_name']]
                if build_names:
                    winning_builds.append(tuple(build_names))

    if not winning_builds:
        print("No winning builds found.")
        return

    # Find most common build
    common_build = Counter(winning_builds).most_common(1)
    
    print(f"Analysis for {hero_name} on {map_name} (Winning Games):")
    if common_build:
        build, count = common_build[0]
        print(f"most_freq_build_count: {count}")
        print("Build Talents:")
        for t in build:
            print(f"- {t}")
            
    # Also print all unique winning builds to see variations
    print("\nAll Winning Variations:")
    for build, count in Counter(winning_builds).most_common():
        print(f"({count} games): {', '.join(build)}")

if __name__ == "__main__":
    analyze_kharazim_wins("Kharazim", "Garden of Terror")
