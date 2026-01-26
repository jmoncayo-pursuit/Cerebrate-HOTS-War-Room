import json
import os
import sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
from database_manager import DatabaseManager

def repair_profile():
    db = DatabaseManager()
    profile = db.get_kv('player_profile')
    if not profile:
        print("No profile found.")
        return

    hero_stats = profile.get('hero_stats', {})
    repaired_count = 0

    for hero, data in hero_stats.items():
        # Repair Season 2025_3
        s3 = data.get('verified_season_2025_3')
        if s3:
            wr = s3.get('wr') or s3.get('win_rate') or 0
            games = s3.get('games') or 0
            actual_wins = s3.get('wins', 0)
            
            # Check for sanity: if wins != round(games * wr/100)
            expected_wins = round(games * (wr / 100))
            if abs(actual_wins - expected_wins) > 1:
                print(f"🔧 Repairing {hero} S3: {actual_wins} wins -> {expected_wins} wins (based on {wr}% of {games} games)")
                s3['wins'] = expected_wins
                s3['losses'] = games - expected_wins
                repaired_count += 1

        # Repair Lifetime
        lifetime = data.get('verified_lifetime')
        if lifetime:
            wr = lifetime.get('wr') or lifetime.get('win_rate') or 0
            games = lifetime.get('games') or 0
            actual_wins = lifetime.get('wins', 0)
            
            expected_wins = round(games * (wr / 100))
            if abs(actual_wins - expected_wins) > 1:
                print(f"🔧 Repairing {hero} Lifetime: {actual_wins} wins -> {expected_wins} wins (based on {wr}% of {games} games)")
                lifetime['wins'] = expected_wins
                lifetime['losses'] = games - expected_wins
                repaired_count += 1

    if repaired_count > 0:
        db.set_kv('player_profile', profile)
        print(f"\n✅ Repaired {repaired_count} hero stat entries.")
    else:
        print("\n✅ All stats appear mathematically consistent.")

if __name__ == "__main__":
    repair_profile()
