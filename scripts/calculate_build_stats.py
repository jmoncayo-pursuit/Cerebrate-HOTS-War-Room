#!/usr/bin/env python3
"""
Calculate build-specific win rates from match history using SQL.
Generates build_stats in KV store AND talent_builds in player_profile.
"""
import json
import os
import sys
from collections import defaultdict

# Add project root to path for database_manager
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from database_manager import DatabaseManager

def extract_build_from_player(player):
    """Extract talent build string from player data"""
    talents = []
    for tier in range(1, 8):
        # Check both stats and kv_stats
        talent_idx = (player.get('stats', {}).get(f'Tier{tier}Talent') or 
                     player.get('kv_stats', {}).get(f'Tier{tier}Talent') or 0)
        talents.append(str(talent_idx))
    
    build_str = ''.join(talents)
    
    # Return None if all zeros (no talent data)
    if build_str == '0000000':
        return None
    
    # Return None if incomplete (less than 7 characters)
    if len(build_str) < 7:
        return None
        
    return build_str

def main():
    """Calculate win rates per build per hero and update profile"""
    db = DatabaseManager()
    
    # Structure: {hero: {map: {build_code: {wins, losses, games}}}}
    build_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'losses': 0, 'games': 0})))
    
    # Structure for profile: {hero: {build_code: {wins, losses, games, wr}}}
    talent_builds = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'losses': 0, 'games': 0, 'wr': 0}))
    
    # Load all matches
    matches = db.get_matches(limit=10000)
    
    if not matches:
        print("❌ No matches found in database")
        return
    
    processed = 0
    skipped = 0
    
    for match in matches:
        map_name = match.get('map', '')
        hero = match.get('hero', '')
        result = match.get('result', '')
        players = match.get('players', [])
        
        if not map_name or not hero or not players:
            skipped += 1
            continue
        
        # Find the player who played this hero (usually the first player or named "Discerning")
        player = None
        for p in players:
            if p.get('hero') == hero or p.get('name') == 'Discerning':
                player = p
                break
        
        if not player:
            # Fallback to first player
            player = players[0] if players else None
        
        if not player:
            skipped += 1
            continue
        
        # Extract build
        build_str = extract_build_from_player(player)
        
        if not build_str:
            skipped += 1
            continue
        
        won = (result == 'WIN')
        
        # Update map-specific build stats
        build_stats[hero][map_name][build_str]['games'] += 1
        if won:
            build_stats[hero][map_name][build_str]['wins'] += 1
        else:
            build_stats[hero][map_name][build_str]['losses'] += 1
        
        # Update overall talent builds for profile
        talent_builds[hero][build_str]['games'] += 1
        if won:
            talent_builds[hero][build_str]['wins'] += 1
        else:
            talent_builds[hero][build_str]['losses'] += 1
        
        processed += 1
    
    # Calculate win rates for build_stats
    output_build_stats = {}
    for hero, maps in build_stats.items():
        output_build_stats[hero] = {}
        for map_name, builds in maps.items():
            output_build_stats[hero][map_name] = {}
            for build_key, stats in builds.items():
                wins = stats['wins']
                games = stats['games']
                wr = (wins / games * 100) if games > 0 else 0
                output_build_stats[hero][map_name][build_key] = {
                    'wins': wins,
                    'losses': stats['losses'],
                    'games': games,
                    'wr': round(wr, 1)
                }
    
    # Calculate win rates for talent_builds
    output_talent_builds = {}
    for hero, builds in talent_builds.items():
        output_talent_builds[hero] = {}
        for build_key, stats in builds.items():
            wins = stats['wins']
            games = stats['games']
            wr = (wins / games * 100) if games > 0 else 0
            output_talent_builds[hero][build_key] = {
                'wins': wins,
                'losses': stats['losses'],
                'games': games,
                'wr': round(wr, 1)
            }
    
    # Save build_stats to KV store
    db.set_kv('build_stats', output_build_stats)
    
    # Update player_profile with talent_builds
    profile = db.get_kv('player_profile') or {}
    profile['talent_builds'] = output_talent_builds
    db.set_kv('player_profile', profile)
    
    print(f"✅ Processed {processed} matches from SQL, skipped {skipped}")
    print(f"✅ Generated build stats for {len(output_build_stats)} heroes in KV store")
    print(f"✅ Updated talent_builds for {len(output_talent_builds)} heroes in player_profile")
    
    return output_build_stats

if __name__ == '__main__':
    main()
