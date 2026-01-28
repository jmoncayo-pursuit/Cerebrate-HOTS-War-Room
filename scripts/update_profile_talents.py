import sys
import os
import json
from datetime import datetime
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from api.services.database import DatabaseManager

def get_tier_from_index(index):
    # Standard HotS Talent Tiers
    tiers = {
        0: "1", 1: "4", 2: "7", 3: "10", 4: "13", 5: "16", 6: "20"
    }
    return tiers.get(index, "Unknown")

def main():
    print("--- Updating Profile Talent Stats (SQL) ---")
    db = DatabaseManager()
    
    # Load matches from DB
    matches = db.get_matches(limit=10000)
    if not matches:
        print("No matches found in database.")
        return

    # Load existing profile
    profile = db.get_kv('player_profile') or {}
    
    # Config
    CURRENT_SEASON_KEY = 'season_2025_3'
    SEASON_START_DATE = '2025-09-01'
    USER_HANDLE = profile.get('battletag', 'Discerning').split('#')[0]

    # Initialize stats structure
    # Structure: Hero -> Season/Lifetime -> Tier -> TalentName -> {games, wins}
    raw_stats = defaultdict(lambda: {
        'lifetime': defaultdict(lambda: defaultdict(lambda: {'games': 0, 'wins': 0})),
        CURRENT_SEASON_KEY: defaultdict(lambda: defaultdict(lambda: {'games': 0, 'wins': 0}))
    })

    processed_count = 0
    
    for match in matches:
        players = match.get('players', [])
        
        # Identify User
        user_player = None
        for p in players:
            if p.get('name') == USER_HANDLE:
                user_player = p
                break
        
        if not user_player:
            # Fallback: Try to match by hero if top-level hero field exists (legacy)
            match_hero = match.get('hero')
            if match_hero:
                for p in players:
                    if p.get('hero') == match_hero:
                        user_player = p
                        break
        
        if not user_player:
            continue

        hero_name = user_player.get('hero')
        if not hero_name:
            continue
            
        talents = user_player.get('talents', [])
        is_win = match.get('result') == 'WIN'
        match_date = match.get('date') or match.get('timestamp_iso')
        
        # Determine if season match
        is_season_match = False
        if match_date and match_date >= SEASON_START_DATE:
            is_season_match = True
            
        # Aggregate Stats
        # Talents is a list of objects usually? Or strings?
        # In match_history schema (from parser), 'talents' is a list of objects: {talent_name, timestamp, source}
        # But 'kv_stats' and 'stats' often have TierXTalent.
        # replay_parser extracts to 'talents' list in players.
        
        for i, talent_entry in enumerate(talents):
            t_name = None
            if isinstance(talent_entry, dict):
                t_name = talent_entry.get('talent_name')
            elif isinstance(talent_entry, str):
                t_name = talent_entry
            
            if not t_name: 
                continue
                
            tier = get_tier_from_index(i)
            if tier == "Unknown":
                continue
            
            # Update Lifetime
            raw_stats[hero_name]['lifetime'][tier][t_name]['games'] += 1
            if is_win:
                raw_stats[hero_name]['lifetime'][tier][t_name]['wins'] += 1
                
            # Update Season
            if is_season_match:
                raw_stats[hero_name][CURRENT_SEASON_KEY][tier][t_name]['games'] += 1
                if is_win:
                    raw_stats[hero_name][CURRENT_SEASON_KEY][tier][t_name]['wins'] += 1
        
        processed_count += 1

    print(f"Processed {processed_count} user matches.")

    # Format for Profile
    if 'hero_talent_stats' not in profile:
        profile['hero_talent_stats'] = {}
        
    updated_heroes = 0
    
    for hero, scopes in raw_stats.items():
        if hero not in profile['hero_talent_stats']:
            profile['hero_talent_stats'][hero] = {}
        
        profile['hero_talent_stats'][hero]['last_updated'] = datetime.now().isoformat().split('T')[0]
        
        for scope_name, tiers in scopes.items():
            formatted_scope = {}
            for tier, talents in tiers.items():
                formatted_scope[tier] = []
                for t_name, stats in talents.items():
                    games = stats['games']
                    wins = stats['wins']
                    wr = round((wins / games) * 100, 2) if games > 0 else 0
                    
                    formatted_scope[tier].append({
                        'name': t_name,
                        'games': games,
                        'wr': wr
                    })
                
                # Sort by games played desc
                formatted_scope[tier].sort(key=lambda x: x['games'], reverse=True)
                
            profile['hero_talent_stats'][hero][scope_name] = formatted_scope
            
        updated_heroes += 1
        
    # Save to DB
    db.set_kv('player_profile', profile)
    print(f"✅ Saved talent stats for {updated_heroes} heroes to DB.")

if __name__ == '__main__':
    main()
