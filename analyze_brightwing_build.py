
import json
from collections import Counter
from api.services.database import DatabaseManager

def analyze_brightwing_wins():
    db = DatabaseManager()
    matches = db.get_matches(limit=1000, hero="Brightwing", include_players=True)
    
    winning_builds = []
    player_name_target = "Discerning"
    
    for m in matches:
        players = m.get('players', [])
        user_p = next((p for p in players if p['hero'] == "Brightwing" and p.get('player_name') == player_name_target), None)
        
        if user_p and user_p['win']:
            talents = user_p.get('talents', [])
            talents.sort(key=lambda x: x['timestamp'])
            build_names = [t['talent_name'] for t in talents if t['talent_name']]
            if build_names:
                winning_builds.append(tuple(build_names))

    if not winning_builds:
        print("No winning builds found for Brightwing.")
        return

    print("Analysis for Brightwing (Winning Games):")
    common_build = Counter(winning_builds).most_common(1)
    
    if common_build:
        build, count = common_build[0]
        print(f"\nSignature Spec ({count} wins):")
        print("Build Talents:")
        for t in build:
            print(f"- {t}")

if __name__ == "__main__":
    analyze_brightwing_wins()
