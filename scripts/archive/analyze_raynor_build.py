
import json
from collections import Counter
from api.services.database import DatabaseManager

def analyze_raynor_wins(hero_name):
    db = DatabaseManager()
    # Get all matching games where user (Discerning) played Raynor
    # Since get_matches returns match details, and include_players=True gives us the players list,
    # we can filter for the name "Discerning" and hero "Raynor"
    
    matches = db.get_matches(limit=1000, hero=hero_name, include_players=True)
    
    winning_builds = []
    map_wins = Counter()
    
    player_name_target = "Discerning"
    
    for m in matches:
        players = m.get('players', [])
        # Find our specific user
        user_p = next((p for p in players if p['hero'] == hero_name and p.get('player_name') == player_name_target), None)
        
        if user_p and user_p['win']:
            map_name = m.get('map')
            map_wins[map_name] += 1
            
            talents = user_p.get('talents', [])
            talents.sort(key=lambda x: x['timestamp'])
            build_names = [t['talent_name'] for t in talents if t['talent_name']]
            if build_names:
                winning_builds.append(tuple(build_names))

    if not winning_builds:
        print("No winning builds found for Raynor.")
        return

    print(f"Analysis for {hero_name} (Winning Games):")
    print("\nTop Performing Maps:")
    for m, c in map_wins.most_common(3):
        print(f"- {m}: {c} wins")

    # Find most common build
    common_build = Counter(winning_builds).most_common(1)
    
    if common_build:
        build, count = common_build[0]
        print(f"\nSignature Spec ({count} wins):")
        print("Build Talents:")
        for t in build:
            print(f"- {t}")

if __name__ == "__main__":
    analyze_raynor_wins("Raynor")
