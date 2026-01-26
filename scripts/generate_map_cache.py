#!/usr/bin/env python3
"""
Pre-compute map recommendations for instant serving.
Regenerate this after each replay parse.
"""

import json
import os
import sys
from datetime import datetime
from collections import Counter

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def generate_map_recommendations(verbose=False):
    """Generate instant map recommendations from player data + strategies"""
    
    # Ensure parent directory is in path for imports (in case called as subprocess)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Load data
    # Try to load from database instead of JSON file
    from database_manager import DatabaseManager
    DB = DatabaseManager()
    profile_data = DB.get_kv('player_profile')
    if not profile_data:
        # Fallback to JSON if database doesn't have it
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        profile_json_path = os.path.join(parent_dir, 'src', 'data', 'player_profile.json')
        try:
            with open(profile_json_path, 'r') as f:
                profile_data = json.load(f)
        except FileNotFoundError:
            if verbose:
                print(f"⚠️  No player profile found in database or JSON file at {profile_json_path}")
            return
    
    profile = profile_data
    
    # Use absolute paths based on script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    config_path = os.path.join(parent_dir, 'src', 'data', 'cerebrate_config.json')
    hero_roles_path = os.path.join(parent_dir, 'src', 'data', 'hero_roles.json')
    
    # Try to load config from database first, then fallback to JSON
    config = DB.get_kv('cerebrate_config') or {}
    if not config:
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {"strategies": {}}  # Default empty config
        except (FileNotFoundError, json.JSONDecodeError):
            if verbose:
                print(f"⚠️  No cerebrate_config found in database or at {config_path}")
            config = {"strategies": {}}  # Default empty config
    
    # Load hero roles - check if file exists first
    if not os.path.exists(hero_roles_path):
        if verbose:
            print(f"⚠️  hero_roles.json not found at {hero_roles_path}, using empty roles")
        hero_roles_data = {}
    else:
        try:
            with open(hero_roles_path, 'r') as f:
                hero_roles_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            if verbose:
                print(f"⚠️  Error loading hero_roles.json, using empty roles")
            hero_roles_data = {}

    # 1. Load Pre-computed Forensics
    forensics = {"universal_nemeses": [], "counter_matrix": {}}
    nemesis_path = os.path.join(parent_dir, 'src', 'data', 'nemesis_forensics.json')
    if os.path.exists(nemesis_path):
        try:
            with open(nemesis_path, 'r') as f:
                forensics = json.load(f)
        except:
            pass
            
    universal_nemeses = forensics.get("universal_nemeses", [])
    counter_matrix = forensics.get("counter_matrix", {})
    
    # Hero -> Role mapping
    hero_to_role = {}
    for role, heroes in hero_roles_data.items():
        for hero in heroes:
            hero_to_role[hero] = role
    
    hero_map_stats = profile.get('hero_map_stats', {})
    strategies = config.get('strategies', {})
    global_bans = config.get('roster_constraints', {}).get('global_bans', [])

    # Global Fallback Builds (Indexing all known builds for fallback logic)
    global_hero_builds = {}
    def add_to_global(hero_obj):
        if not isinstance(hero_obj, dict): return
        name = hero_obj.get('name') or hero_obj.get('hero')
        code = hero_obj.get('code')
        if name and code:
            global_hero_builds[name] = {
                'code': code,
                'trigger': hero_obj.get('trigger', ''),
                'global': hero_obj.get('global', ''),
                'insight': hero_obj.get('insight', '') # Store for global reference if needed
            }

    for map_strat in strategies.values():
        add_to_global(map_strat.get('primary'))
        backups = map_strat.get('backups') or map_strat.get('backup')
        if isinstance(backups, list):
            for b in backups: add_to_global(b)
        elif isinstance(backups, dict):
            add_to_global(backups)

    maps = [
        'Infernal Shrines', 'Battlefield of Eternity', 'Dragon Shire',
        "Blackheart's Bay", 'Sky Temple', 'Tomb of the Spider Queen',
        'Alterac Pass', 'Volskaya Foundry', 'Garden of Terror',
        'Cursed Hollow', 'Towers of Doom', 'Braxis Holdout',
        'Hanamura Temple', 'Warhead Junction'
    ]
    
    recommendations = {}
    
    for map_name in maps:
        role_candidates = {role: [] for role in ['Tank', 'Healer', 'Ranged Assassin', 'Bruiser']}
        

        # Gather all user-compatible heroes for this map
        hero_stats = profile.get('hero_stats', {})
        for hero, hero_data in hero_stats.items():
            if hero in global_bans: continue
            role = hero_to_role.get(hero)
            if role not in role_candidates: continue
            
            # Check verified data first (priority: season > lifetime)
            verified_season = hero_data.get('verified_season_2025_3', {})
            verified_lifetime = hero_data.get('verified_lifetime', {})
            verified = hero_data.get('verified', {})  # Legacy fallback
            
            # Use the most recent/relevant verified data
            m_data = None
            source = None
            
            if verified_season and (verified_season.get('games') or 0) > 0:
                m_data = verified_season
                source = "[Verified S3]"
            elif verified_lifetime and (verified_lifetime.get('games') or 0) > 0:
                m_data = verified_lifetime
                source = "[Verified Lifetime]"
            elif verified and (verified.get('games') or 0) > 0:
                m_data = verified
                source = "[Verified]"
            
            # Fallback to hero_map_stats if no verified data
            if not m_data:
                map_stats = hero_map_stats.get(hero, {})
                for map_entry in map_stats.get('lifetime', []):
                    if map_entry.get('game_map') == map_name:
                        m_data = map_entry
                        source = "[Lifetime]"
                        break
            
            if m_data:
                # Handle both 'wr' and 'win_rate' keys
                wr = float(m_data.get('wr') or m_data.get('win_rate', 0))
                games = m_data.get('games') or m_data.get('games_played', 0)
                if games >= 1:
                    role_candidates[role].append({
                        'hero': hero, 'wr': wr, 'games': games,
                        'source': source
                    })

        final_recs = []
        map_strat = strategies.get(map_name, {})
        map_talent_map = {} # Store map-specific specialists from config
        
        def pull_map_talents(obj):
            if not obj: return
            name = obj.get('name') or obj.get('hero')
            if name: map_talent_map[name] = obj

        pull_map_talents(map_strat.get('primary'))
        for b in (map_strat.get('backups') or []):
            if isinstance(b, dict): pull_map_talents(b)

        # QUAD-ROLE MANDATE: Exactly 1 per core role
        for role in ['Tank', 'Healer', 'Ranged Assassin', 'Bruiser']:
            # A. Find User's Best for this Role+Map
            # Robustness Sort: Prioritize proven performance (Games) over raw WR variance
            candidates = role_candidates[role]
            
            def robustness_score(c):
                # Tier 1: Proven Winners (5+ games, >48% WR) - The Gold Standard
                if c['games'] >= 5 and c['wr'] >= 48:
                    return 2000 + (c['wr'] * 10) + c['games']
                # Tier 2: Emerging Patterns (3-4 games, >50% WR)
                if c['games'] >= 3 and c['wr'] >= 50:
                    return 1000 + (c['wr'] * 5)
                # Tier 3: Low Sample Anomalies (1-2 games) - Penalize heavily to avoid "1-0 100% WR" bait
                # We only want these if there are NO Tier 1/2 options.
                return c['wr'] # Raw WR (0-100)

            candidates.sort(key=robustness_score, reverse=True)
            best_user = candidates[0] if candidates else None
            
            # B. Find Meta Specialist for this Role+Map
            meta_spec = None
            for meta_name, meta_data in map_talent_map.items():
                if hero_to_role.get(meta_name) == role:
                    meta_spec = {
                        'hero': meta_name,
                        'role': role,
                        'wr': 0, # To be filled if user has played
                        'games': 0,
                        'source': '[Meta Specialist]',
                        'talent_code': meta_data.get('code', ''),
                        'trigger': meta_data.get('trigger', ''),
                        'insight': meta_data.get('insight', ''),
                        'global_wr': meta_data.get('global', '50%+'),
                        'is_meta': True
                    }
                    # If user has played the meta spec on this map, use their stats
                    user_meta_stats = next((c for c in role_candidates[role] if c['hero'] == meta_name), None)
                    if user_meta_stats:
                        meta_spec['wr'] = user_meta_stats['wr']
                        meta_spec['games'] = user_meta_stats['games']
                    break

            # C. DECISION ENGINE: Pick the best of either
            selection = None
            
            # Define "Proven": At least 3 games
            user_is_proven = best_user and best_user['games'] >= 3
            
            # Prefer Meta if:
            # 1. User has NO valid data for this role
            # 2. User's "best" is actually negative (<45%)
            # 3. User's "best" is unproven (<3 games) AND there is a strong Meta option
            should_use_meta = meta_spec and (
                not best_user or 
                best_user['wr'] < 45.0 or 
                (not user_is_proven)
            )

            if should_use_meta:
                selection = meta_spec
                # Only "Scout" if we have meaningful data (3+ games) and good performance
                if selection['games'] >= 3 and selection['wr'] >= 45.0:
                    selection['is_meta'] = False
                    selection['source'] = '[Proven Specialist]'
            
            elif best_user and (best_user['wr'] >= 40.0 or best_user['games'] >= 50):
                # Use User Best but pull map-specific insight if they are a specialist
                # REQUIREMENT: Must be at least 40% WR (unless they have massive experience > 50 games)
                t_data = map_talent_map.get(best_user['hero']) or global_hero_builds.get(best_user['hero'], {})
                insight = t_data.get('insight', '') if best_user['hero'] in map_talent_map else ''
                selection = {
                    'hero': best_user['hero'], 'role': role, 'wr': best_user['wr'], 'games': best_user['games'], 
                    'source': best_user['source'], 'talent_code': t_data.get('code', ''), 
                    'trigger': t_data.get('trigger', ''), 'insight': insight, 'is_meta': False
                }
            else:
                # Extreme Fallback - Overall Career
                role_all = []
                for h, s in hero_map_stats.items():
                    if hero_to_role.get(h) == role and h not in global_bans:
                        total_g = sum(d.get('games_played', d.get('games', 0)) for d in s.get('lifetime', []))
                        # Only recommend Overall fallback if they've played it a bit (>=3 games)
                        if total_g >= 3:
                            total_w = sum(d.get('games_played', d.get('games', 0)) * d.get('win_rate', 0) / 100 for d in s.get('lifetime', []))
                            role_all.append({'hero': h, 'wr': (total_w/total_g*100), 'games': total_g})
                
                if role_all:
                    best_tmp = sorted(role_all, key=lambda x: -x['wr'])[0]
                    t_data = global_hero_builds.get(best_tmp['hero'], {})
                    selection = {
                        'hero': best_tmp['hero'], 'role': role, 'wr': round(best_tmp['wr'], 1), 
                        'games': int(best_tmp['games']), 'source': '[Overall]',
                        'talent_code': t_data.get('code', ''), 'trigger': t_data.get('trigger', ''), 
                        'insight': '', 'is_meta': False
                    }
            
            # LAST RESORT: If we still have no selection (Fallback failed), pick Best User even if weak, or Generic
            if not selection:
                if best_user:
                     selection = {
                        'hero': best_user['hero'], 'role': role, 'wr': best_user['wr'], 'games': best_user['games'], 
                        'source': '[At Risk]' if best_user['wr'] < 40 else '[Low Confidence]', 
                        'talent_code': '', 
                        'trigger': '', 'insight': 'Map data suggests caution.', 'is_meta': False
                    }
                else:
                    # Absolute Zero state: Pick a Safe Meta hero for the role
                    safe_picks = {'Tank': 'Johanna', 'Healer': 'Anduin', 'Ranged Assassin': 'Raynor', 'Bruiser': 'Thrall'}
                    selection = {
                        'hero': safe_picks.get(role, 'Abathur'), 'role': role, 'wr': 0, 'games': 0,
                        'source': '[Generic Rec]', 'talent_code': '', 'trigger': '', 'insight': 'No data available.', 'is_meta': True
                    }

            if selection:
                final_recs.append(selection)

        # 3. True North Sorting (Tactical Priority)
        def rec_score(r):
            source_weight = 30 if r['source'] == '[Verified]' else 25 if r['source'] == '[Lifetime]' else 10 if r['source'] == '[Overall]' else 5
            return (source_weight, r['wr'], r['games'])
        final_recs.sort(key=rec_score, reverse=True)

        # 4. Draft Shield Bans (Targeted Protection with 'Protects' metadata)
        # Priority: 
        # A. Counter-threats to the specific recommended heroes
        # B. Map Meta powerhouses intersected with general nemeses
        rec_heroes = [h['hero'] for h in final_recs]
        
        personal_bans = []
        
        # Layer 1: Pick Shields (Identify who they protect)
        threat_protections = {} # { enemy_hero: [my_hero1, my_hero2] }
        for my_hero in rec_heroes:
            hero_counters = counter_matrix.get(my_hero, {})
            for en, count in hero_counters.items():
                if en not in rec_heroes:
                    if en not in threat_protections: threat_protections[en] = []
                    threat_protections[en].append(my_hero)
        
        # Sort threats by how many of our picks they counter
        sorted_threats = sorted(threat_protections.keys(), key=lambda x: len(threat_protections[x]), reverse=True)
        
        for threat in sorted_threats:
            if threat in universal_nemeses or threat in map_talent_map:
                personal_bans.append({
                    "hero": threat,
                    "reason": f"Protects {', '.join(threat_protections[threat][:2])}"
                })
            if len(personal_bans) >= 3: break
            
        # Fill remaining with Universal Nemeses
        if len(personal_bans) < 3:
            for n in universal_nemeses:
                if n not in [b['hero'] for b in personal_bans] and n not in rec_heroes:
                    personal_bans.append({
                        "hero": n,
                        "reason": "General Nemesis / Map Threat"
                    })
                if len(personal_bans) >= 3: break

        recommendations[map_name] = {
            'desc': map_strat.get('desc', 'Strategic priority required.'),
            'rules': map_strat.get('rules', []),
            'heroes': final_recs,
            'bans': personal_bans # Now a list of objects
        }
    
    cache_data = {'generated_at': datetime.now().isoformat(), 'recommendations': recommendations}
    # Save to SQLite KV Store
    DB.set_kv('map_recommendations_cache', cache_data)
    
    # Optional legacy file write
    try:
        cache_path = os.path.join(parent_dir, 'src', 'data', 'map_recommendations_cache.json')
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except:
        pass
    
    if verbose: print(f"✅ Mission Cache ready ({len(maps)} maps optimized)")
    return cache_data

if __name__ == '__main__':
    import sys
    verbose = "--verbose" in sys.argv
    generate_map_recommendations(verbose=verbose)
