import sys
import os
import json
from datetime import datetime
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from database_manager import DatabaseManager

def main():
    print("--- Rebuilding Player Profile from SQL ---")
    db = DatabaseManager()
    matches = db.get_matches(limit=10000)
    
    if not matches:
        print("No matches found in database.")
        return

    # Constants
    SEASON_START = '2025-09-01'
    USER_HANDLE = os.environ.get('PLAYER_NAME', 'Player')

    # Stats containers
    lifetime = {'wins': 0, 'losses': 0, 'games': 0}
    season = {'wins': 0, 'losses': 0, 'games': 0}
    hero_stats = defaultdict(lambda: {'wins': 0, 'losses': 0, 'games': 0, 'last_played': None})
    
    print(f"Analyzing {len(matches)} matches...")

    # Analyze matches
    for m in matches:
        date = m.get('timestamp_iso') or m.get('date')
        if not date: continue
        
        result = m.get('result')
        hero = m.get('hero') # This is the hero played by the user (from parsed metadata)
        
        # Verify it's a valid match
        if not hero or not result:
            continue
            
        is_win = (result == 'WIN')
        
        # Global stats
        lifetime['games'] += 1
        if is_win: lifetime['wins'] += 1
        else: lifetime['losses'] += 1
        
        # Season stats
        if date >= SEASON_START:
            season['games'] += 1
            if is_win: season['wins'] += 1
            else: season['losses'] += 1
            
        # Hero stats
        hero_stats[hero]['games'] += 1
        if is_win: hero_stats[hero]['wins'] += 1
        else: hero_stats[hero]['losses'] += 1
        
        # Track last played
        if not hero_stats[hero]['last_played'] or date > hero_stats[hero]['last_played']:
            hero_stats[hero]['last_played'] = date

    # Calculate Rates
    lifetime['win_rate'] = round((lifetime['wins']/lifetime['games'])*100, 1) if lifetime['games'] > 0 else 0
    season['win_rate'] = round((season['wins']/season['games'])*100, 1) if season['games'] > 0 else 0
    
    # Format Hero Stats for Verified Data
    formatted_hero_stats = {}
    for hero, stats in hero_stats.items():
        wr = round((stats['wins']/stats['games'])*100, 1) if stats['games'] > 0 else 0
        formatted_hero_stats[hero] = {
            'lifetime': {
                'games': stats['games'],
                'wins': stats['wins'],
                'win_rate': wr,
                'last_played': stats['last_played']
            },
            'verified_season_2025_3': { # Fallback verified data from parser
                'games': stats['games'] if stats['last_played'] >= SEASON_START else 0, # Rough approx if needed
                'wins': stats['wins'] if stats['last_played'] >= SEASON_START else 0,
                'verified_date': datetime.now().isoformat()
            }
        }

    # --- MERGE WITH VERIFIED SOURCES ---
    # Load 'sources_blizzard_verified' from KV
    verified_sources_raw = db.get_kv('sources_blizzard_verified')
    verified_lifetime = None
    
    # Normalize input to list
    verification_list = []
    if isinstance(verified_sources_raw, dict):
        verification_list = verified_sources_raw.get('verifications', [])
    elif isinstance(verified_sources_raw, list):
        verification_list = verified_sources_raw
        
    if verification_list:
        # Find latest lifetime entry
        lifetime_entries = [e for e in verification_list if e.get('stat_type') == 'lifetime']
        if lifetime_entries:
            # Sort by timestamp desc
            entry = sorted(lifetime_entries, key=lambda x: x.get('timestamp', ''), reverse=True)[0]
            
            # Calculate aggregate wins/losses from hero breakdown
            v_wins = 0
            v_losses = 0
            v_games = 0
            
            for h in entry.get('hero_stats', []):
                g = h.get('games', 0)
                wr = h.get('wr', 0)
                
                # Sanitize inputs (some were strings or empty)
                if isinstance(g, str): 
                     if g.isdigit(): g = int(g)
                     else: g = 0
                if isinstance(wr, str):
                     try:
                         # Remove % if present
                         wr = float(wr.replace('%', ''))
                     except:
                         wr = 0.0
                
                if g > 0:
                    w = int(round(g * (wr / 100.0)))
                    l = g - w
                    v_wins += w
                    v_losses += l
                    v_games += g
            
            if v_games > 0:
                verified_lifetime = {
                    'games': v_games,
                    'wins': v_wins,
                    'losses': v_losses,
                    'win_rate': round((v_wins/v_games)*100, 1)
                }
                print(f"   Found Verified Lifetime: {v_games} games ({verified_lifetime['win_rate']}%) from {entry.get('timestamp')}")

    # Construct Profile
    # Preserve existing fields like talent_builds if they exist
    existing_profile = db.get_kv('player_profile') or {}
    
    # Sanitize placeholders
    saved_rank = existing_profile.get('current_rank') or existing_profile.get('rank_data', {}).get('storm_league', {}).get('current_rank')
    if saved_rank == 'Diamond 2' or saved_rank == 'Unranked': saved_rank = 'RANK NOT SYNCED'
    
    saved_level = existing_profile.get('rank_data', {}).get('account_level')
    if saved_level == 999: saved_level = 0

    # Decision: verified_lifetime is the TRUTH for 'lifetime' key
    
    final_lifetime = {
        'total_games': lifetime['games'],
        'wins': lifetime['wins'],
        'losses': lifetime['losses'],
        'win_rate': lifetime['win_rate']
    }
    
    if verified_lifetime:
         final_lifetime = {
            'total_games': verified_lifetime['games'],
            'wins': verified_lifetime['wins'],
            'losses': verified_lifetime['losses'],
            'win_rate': verified_lifetime['win_rate']
         }

    profile = {
        'battletag': existing_profile.get('battletag', os.environ.get('PLAYER_BATTLE_TAG', 'Player#1234')),
        'name': existing_profile.get('name', os.environ.get('PLAYER_NAME', 'Player')),
        'rank_data': {
            'account_level': saved_level or 0,
            'storm_league': {
                'current_rank': saved_rank or 'RANK NOT SYNCED',
                'season_2025_3': {  
                    'total_games': season['games'],
                    'wins': season['wins'],
                    'losses': season['losses'],
                    'win_rate': season['win_rate']
                },
                'lifetime': final_lifetime
            },
            'last_updated': datetime.now().isoformat()
        },
        'hero_stats': formatted_hero_stats, # We could merge verified here too, but start with top level
        'talent_builds': existing_profile.get('talent_builds', {}),
        'storm_league_audit': existing_profile.get('storm_league_audit', {}),
        'config': existing_profile.get('config', {
            'active_season': {
                'slug': 'season_2025_3',
                'name': 'Season 3 2025',
                'start_date': '2025-09-01'
            }
        })
    }
    
    # Save
    db.set_kv('player_profile', profile)
    print(f"✅ Profile updated in DB.")
    print(f"   Lifetime Games: {final_lifetime['total_games']} ({final_lifetime['win_rate']}%)")
    print(f"   Season Games:   {season['games']} ({season['win_rate']}%)")
    print(f"   Heroes Tracked: {len(hero_stats)}")

if __name__ == "__main__":
    main()
