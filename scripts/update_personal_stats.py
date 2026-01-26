"""
Auto-update personal stats in personal_meta_notes.json from match history.

This script scans your match history and updates the personal_stats field
for each build you've played, providing data to substantiate or challenge
your subjective opinions.
"""

import json
import os
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
NOTES_FILE = os.path.join(PROJECT_ROOT, 'src/data', 'personal_meta_notes.json')
MATCH_HISTORY_FILE = os.path.join(PROJECT_ROOT, 'src/data', 'match_history.json')


import sys
sys.path.insert(0, PROJECT_ROOT)
from database_manager import DatabaseManager

def load_match_history():
    """Load match history from database."""
    db = DatabaseManager()
    return db.get_matches(limit=10000)


def identify_build(hero, talents):
    """
    Identify which build was used based on key talents.
    
    This is a simplified version - you'll need to customize this
    based on your actual build definitions.
    
    Returns: build_name or None
    """
    # Example: Malthael builds
    if hero == "Malthael":
        for talent in talents:
            if "TormentedSouls" in talent.get("talent_name", ""):
                return "TormentedSouls"
            if "LastRites" in talent.get("talent_name", ""):
                return "LastRites"
    
    # Example: Gazlowe builds
    if hero == "Gazlowe":
        for talent in talents:
            if "GoblinFusion" in talent.get("talent_name", ""):
                return "GoblinFusion"
            if "BigGameHunter" in talent.get("talent_name", ""):
                return "BigGameHunterTurret"
    
    return None


def calculate_build_stats(matches):
    """
    Calculate win/loss stats for each hero/build combination.
    
    Returns: dict of {hero: {build: {wins, losses, games, last_played}}}
    """
    stats = defaultdict(lambda: defaultdict(lambda: {
        "wins": 0,
        "losses": 0,
        "games": 0,
        "last_played": None
    }))
    
    for match in matches:
        hero = match.get("hero")
        if not hero:
            continue
        
        # Find player's talents
        player_talents = None
        target_name = os.environ.get('PLAYER_NAME', 'Player')
        for player in match.get("players", []):
            if player.get("name") == target_name:  # Your battletag
                player_talents = player.get("talents", [])
                break
        
        if not player_talents:
            continue
        
        build = identify_build(hero, player_talents)
        if not build:
            continue
        
        # Update stats
        is_win = match.get("outcome") == "Victory"
        stats[hero][build]["games"] += 1
        if is_win:
            stats[hero][build]["wins"] += 1
        else:
            stats[hero][build]["losses"] += 1
        
        # Update last played date
        match_date = match.get("timestamp_iso")
        if match_date:
            if not stats[hero][build]["last_played"] or match_date > stats[hero][build]["last_played"]:
                stats[hero][build]["last_played"] = match_date[:10]  # YYYY-MM-DD
    
    return stats


def update_personal_notes(build_stats):
    """
    Update personal_meta_notes in SQL with calculated stats.
    """
    db = DatabaseManager()
    notes = db.get_kv('personal_meta_notes') or {"heroes": {}}
    
    updated_count = 0
    
    for hero, builds in notes.get("heroes", {}).items():
        for build_name, build_data in builds.get("builds", {}).items():
            if hero in build_stats and build_name in build_stats[hero]:
                stats = build_stats[hero][build_name]
                
                # Calculate win rate
                games = stats["games"]
                wins = stats["wins"]
                win_rate = round((wins / games * 100), 1) if games > 0 else None
                
                # Update personal_stats
                build_data["personal_stats"] = {
                    "games_played": games,
                    "wins": wins,
                    "losses": stats["losses"],
                    "win_rate": win_rate,
                    "last_played": stats["last_played"],
                    "notes": f"Auto-updated from match history. {wins}-{stats['losses']} record."
                }
                
                updated_count += 1
                if updated_count < 20: # Limit spam
                    print(f"✅ Updated {hero} - {build_name}: {wins}-{stats['losses']} ({win_rate}% WR)")
    
    # Save updated notes to SQL
    db.set_kv('personal_meta_notes', notes)
    
    # Still write to file as backup/frontend compatibility for now
    try:
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=2)
    except:
        pass
    
    print(f"\n✅ Updated {updated_count} build(s) in personal_meta_notes")


def main():
    print("=== Personal Stats Auto-Updater ===\n")
    
    # Load match history
    matches = load_match_history()
    print(f"Loaded {len(matches)} matches from history\n")
    
    # Calculate stats
    build_stats = calculate_build_stats(matches)
    
    # Update notes file
    update_personal_notes(build_stats)
    
    print("\n💡 TIP: Run this script after uploading new replays to keep stats current")


if __name__ == "__main__":
    main()
