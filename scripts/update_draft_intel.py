#!/usr/bin/env python3
"""
Draft Intelligence Cache Generator
Calculates hero pool stats by role and map for instant AI recommendations
"""

import sys
import os

# Add project root to path (database_manager.py is in root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from database_manager import DatabaseManager
from collections import defaultdict
import json

# Role classifications
ROLES = {
    'Tank': ['Johanna', 'Muradin', 'Garrosh', 'Diablo', 'Anubarak', 'ETC', 'Arthas', 'Blaze', 'Stitches', 'Tyrael', 'Mei'],
    'Bruiser': ['Sonya', 'Artanis', 'Thrall', 'Ragnaros', 'Malthael', 'Imperius', 'Leoric', 'Dehaka', 'Yrel', 'Xul', 'D.Va', 'Rexxar', 'Chen', 'Gazlowe', 'Zarya', 'Varian'],
    'Healer': ['Kharazim', 'Rehgar', 'Brightwing', 'Lt. Morales', 'Malfurion', 'Uther', 'Anduin', 'Auriel', 'Deckard', 'Li Li', 'Lucio', 'Stukov', 'Tyrande', 'Whitemane', 'Alexstrasza', 'Ana'],
    'Ranged': ['Raynor', 'Valla', 'Jaina', "Kael'thas", 'Li-Ming', 'Chromie', 'Lunara', 'Cassia', 'Fenix', 'Greymane', 'Hanzo', 'Junkrat', 'Mephisto', 'Nazeebo', 'Orphea', 'Sylvanas', 'Tracer', 'Tychus', 'Zagara', 'Zuljin', 'Falstad', 'Gall']
}

def calculate_draft_intel():
    """Calculate comprehensive draft intelligence"""
    db = DatabaseManager()
    
    # Get all matches
    all_matches = db.get_matches(limit=10000)
    
    # Build map-specific hero stats
    map_hero_stats = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'games': 0}))
    overall_hero_stats = defaultdict(lambda: {'wins': 0, 'games': 0, 'role': None})
    
    # Determine role for each hero
    hero_to_role = {}
    for role, heroes in ROLES.items():
        for hero in heroes:
            hero_to_role[hero] = role
    
    for match in all_matches:
        hero = match.get('hero')
        map_name = match.get('map')
        result = match.get('result')
        
        if hero:
            # Overall stats
            overall_hero_stats[hero]['games'] += 1
            overall_hero_stats[hero]['role'] = hero_to_role.get(hero, 'Unknown')
            if result == 'WIN':
                overall_hero_stats[hero]['wins'] += 1
            
            # Map-specific stats
            if map_name:
                map_hero_stats[map_name][hero]['games'] += 1
                if result == 'WIN':
                    map_hero_stats[map_name][hero]['wins'] += 1
    
    # Build draft intel structure
    draft_intel = {
        'overall_hero_pool': {},
        'role_rankings': {},
        'map_recommendations': {},
        'meta': {
            'total_matches': len(all_matches),
            'last_updated': None
        }
    }
    
    # Overall hero pool
    for hero, stats in overall_hero_stats.items():
        if stats['games'] >= 1:
            wr = round((stats['wins'] / stats['games']) * 100, 1)
            draft_intel['overall_hero_pool'][hero] = {
                'wins': stats['wins'],
                'games': stats['games'],
                'wr': wr,
                'role': stats['role']
            }
    
    # Role rankings (best heroes per role)
    for role in ['Tank', 'Healer', 'Bruiser', 'Ranged']:
        role_heroes = []
        for hero, stats in overall_hero_stats.items():
            if stats['role'] == role and stats['games'] >= 1:
                wr = round((stats['wins'] / stats['games']) * 100, 1)
                role_heroes.append({
                    'hero': hero,
                    'wins': stats['wins'],
                    'games': stats['games'],
                    'wr': wr
                })
        
        # Sort by WR, then games
        role_heroes.sort(key=lambda x: (-x['wr'], -x['games']))
        draft_intel['role_rankings'][role] = role_heroes
    
    # Map-specific recommendations
    for map_name, hero_stats in map_hero_stats.items():
        map_recs = {
            'total_games': sum(s['games'] for s in hero_stats.values()),
            'by_role': {}
        }
        
        # Organize by role
        for role in ['Tank', 'Healer', 'Bruiser', 'Ranged']:
            role_heroes = []
            for hero, stats in hero_stats.items():
                if hero_to_role.get(hero) == role and stats['games'] >= 1:
                    map_wr = round((stats['wins'] / stats['games']) * 100, 1)
                    overall_stats = overall_hero_stats.get(hero, {'wins': 0, 'games': 0})
                    overall_wr = round((overall_stats['wins'] / overall_stats['games']) * 100, 1) if overall_stats['games'] > 0 else 0
                    
                    role_heroes.append({
                        'hero': hero,
                        'map_wins': stats['wins'],
                        'map_games': stats['games'],
                        'map_wr': map_wr,
                        'overall_wins': overall_stats['wins'],
                        'overall_games': overall_stats['games'],
                        'overall_wr': overall_wr
                    })
            
            # Sort by map WR, then map games
            role_heroes.sort(key=lambda x: (-x['map_wr'], -x['map_games']))
            map_recs['by_role'][role] = role_heroes
        
        draft_intel['map_recommendations'][map_name] = map_recs
    
    # Save to database
    db.set_kv('draft_intelligence', draft_intel)
    
    print(f"✅ Draft Intelligence Cache Updated")
    print(f"   Total Matches: {len(all_matches)}")
    print(f"   Heroes Tracked: {len(overall_hero_stats)}")
    print(f"   Maps Analyzed: {len(map_hero_stats)}")
    print(f"   Roles: {', '.join(ROLES.keys())}")
    
    return draft_intel

if __name__ == '__main__':
    calculate_draft_intel()
