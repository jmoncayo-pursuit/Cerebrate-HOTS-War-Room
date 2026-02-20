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
import re

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# HERO NAMES and MECHANICAL KEYWORDS for filtering directives (to keep them general)
HERO_LIST = [
    "Samuro", "Rexxar", "Misha", "Jaina", "Kael'thas", "Li-Ming", "Gazlowe", 
    "Azmodan", "Nazeebo", "Sylvanas", "Raynor", "Falstad", "Kharazim", 
    "Stitches", "Johanna", "Zagara", "Probius", "Abathur", "Murky", "Vikings"
]
LOCKED_KEYWORDS = [
    "image transmission", "misha", "animal husbandry", "vile infection", 
    "dragon knight", "polymorph", "phase shift", "turret", "sentinel", 
    "talent", "stack", "quest", "globe", "hero level", "cooldown", "mana",
    "hook", "devour", "gorge", "palm", "seven-sided", "insight", "iron fists"
]

def is_general(text):
    """Check if text is general enough (no hero names or specific abilities/mechanics)"""
    text_lower = text.lower()
    # Explicit Hero Names
    for hero in HERO_LIST:
        if hero.lower() in text_lower: return False
    
    # Mechanical Leakage
    for kw in LOCKED_KEYWORDS:
        if kw in text_lower: return False
    
    # No talent code patterns like [1211221]
    if re.search(r'\[[0-9]{7}\]', text): return False
    
    return True

def generate_map_recommendations(verbose=False):
    """Generate instant map recommendations from player data + strategies"""
    
    # Ensure parent directory is in path for imports (in case called as subprocess)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Load data
    # Try to load from database instead of JSON file
    from api.services.database import DatabaseManager
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

    # BRAIN INTEGRATION: Load research from .agent/brain
    brain_builds = {}
    brain_directives = {}
    brain_dir = os.path.join(parent_dir, '.agent', 'brain')
    
    if os.path.exists(brain_dir):
        if verbose: print("🧠 Syncing with Grandmaster Tactical Memory...")
        for filename in os.listdir(brain_dir):
            if filename.endswith('.md'):
                try:
                    with open(os.path.join(brain_dir, filename), 'r') as f:
                        content = f.read()
                        # Extract Builds: [CODE, HERO] or [TCODE, HERO] or [1311221,Hero]
                        build_matches = re.findall(r'\[(T?[0-9]{7}),\s*([A-Za-z.\'\s]+)\]', content)
                        for code, hero in build_matches:
                            brain_builds[hero.strip()] = code
                        
                        # Map Directives (ToD specific research)
                        if "Towers of Doom" in filename or ("Towers of Doom" in content and "Ammunition" in content):
                            brain_directives["Towers of Doom"] = [
                                "Prioritize Sapper camps (0:30, 2:00, 3:30) as 'Ammunition Generation'.",
                                "Double-soak Top and Mid lanes during Altar windows if playing high waveclear heroes.",
                                "Secure Core Shots from mercenaries to bypass final Altar cycles."
                            ]
                        if "Cursed Hollow" in content and "Grave Golem" in content:
                            brain_directives["Cursed Hollow"] = ["Rush Boss at Level 4 (2:30) if enemy is occupied with Tribute."]
                        if "Sky Temple" in content and "Ammunition" in content:
                             brain_directives["Sky Temple"] = ["Treat Temple shots as Strategic Ammunition; secure level 20 milestone before final temple."]
                except: continue

    # Global Fallback Builds (Indexing all known builds for fallback logic)
    global_hero_builds = {}
    def add_to_global(hero_obj):
        if not isinstance(hero_obj, dict): return
        name = hero_obj.get('name') or hero_obj.get('hero')
        code = hero_obj.get('code') or hero_obj.get('talent_code')
        if name and code:
            global_hero_builds[name] = code

    for map_strat in strategies.values():
        add_to_global(map_strat.get('primary'))
        backups = map_strat.get('backups') or map_strat.get('backup')
        if isinstance(backups, list):
            for b in backups: add_to_global(b)
        elif isinstance(backups, dict):
            add_to_global(backups)

    # Merge Brain Builds into Global (Brain takes priority)
    for hero, code in brain_builds.items():
        # Ensure T prefix
        clean_code = code.replace('[', '').replace(']', '').split(',')[0]
        if not clean_code.startswith('T'):
            clean_code = 'T' + clean_code
        global_hero_builds[hero] = clean_code

    maps = [
        'Infernal Shrines', 'Battlefield of Eternity', 'Dragon Shire',
        "Blackheart's Bay", 'Sky Temple', 'Tomb of the Spider Queen',
        'Alterac Pass', 'Volskaya Foundry', 'Garden of Terror',
        'Cursed Hollow', 'Towers of Doom', 'Braxis Holdout',
        'Hanamura Temple', 'Warhead Junction'
    ]
    
    recommendations = {}
    
    # Define Mages for the specific role requirement
    MAGES = ["Jaina", "Kael'thas", "Li-Ming", "Chromie", "Gul'dan", "Orphea", "Mephisto", "Tassadar", "Azmodan", "Nazeebo", "Sylvanas"]


    def get_map_directives(map_name):
        """Fetch general map directives from databases"""
        raw_dirs = []
        # 1. Try war_room.db
        try:
            query = "SELECT content_json FROM strategies WHERE id = ?"
            row = DB._get_connection().execute(query, (f"map_{map_name}",)).fetchone()
            if row:
                data = json.loads(row[0])
                raw_dirs.extend(data.get('directives', []))
        except: pass
            
        # 2. Try cerebrate.db
        try:
            import sqlite3
            c_db = sqlite3.connect(os.path.join(parent_dir, 'src', 'data', 'cerebrate.db'))
            query = "SELECT content_json FROM strategies WHERE key = ?"
            row = c_db.execute(query, (map_name,)).fetchone()
            c_db.close()
            if row:
                data = json.loads(row[0])
                primary = data.get('primary', {})
                # Skip primary insights as they are almost always hero-specific micro-advice
                # They will be displayed alongside the hero rec anyway.
                pass
                
                rules = data.get('rules', [])
                if isinstance(rules, list):
                    for r in rules:
                        if isinstance(r, dict): raw_dirs.append(r.get('content', ''))
                        else: raw_dirs.append(str(r))
                
                tactics = data.get('tactics')
                if tactics and isinstance(tactics, str):
                    # Split into sentences
                    sentences = re.split(r'[;.]', tactics)
                    raw_dirs.extend([s.strip() for s in sentences if len(s.strip()) > 10])
        except: pass
            
        # 3. Apply Brain Research Overrides (ALWAYS prioritize research-backed macro)
        if map_name in brain_directives:
            # Brain Research directives BYPASS the generality filter because they are hand-curated
            raw_dirs = brain_directives[map_name] + [d for d in raw_dirs if is_general(d)]
        else:
            raw_dirs = [d for d in raw_dirs if is_general(d)]
            
        # If too few, add core map macro fallbacks
        if len(raw_dirs) < 2:
            raw_dirs.extend([
                "Prioritize waveclear and XP soak during objective downtimes.",
                "Rotate 15s early to secure vision near objective spawn points."
            ])
            
        return raw_dirs[:4] # Keep it concise

    def get_carry_hover(map_name, role_recs):
        """Identify the absolute best 1st pick/auto-hover for this map"""
        all_recs = []
        for role, heroes in role_recs.items():
            all_recs.extend(heroes)
        
        # Sort by WR and Games to find the absolute beast
        all_recs.sort(key=lambda x: (x['wr'] >= 50, x['wr'] * (1 + 0.1 * min(x['games'], 20))), reverse=True)
        
        if all_recs:
            best = all_recs[0]
            if best['wr'] >= 55:
                # SPECIAL OVERRIDE: If ToD, Jaina is a strong carry hover even if WR low
                if map_name == "Towers of Doom":
                     return {"hero": "Jaina", "justification": "Map Specialist. Sapper Sniper strategy generates elite ammunition throughput."}
                return {
                    "hero": best['hero'],
                    "justification": f"Dominant {best['wr']:.1f}% WR ({best['games']}g). Strongest blind pick for {map_name}."
                }
            else:
                return {
                    "hero": best['hero'],
                    "justification": "Highest statistically verified win rate for your roster on this map."
                }
        return {"hero": "None", "justification": "Draft reactive based on team needs."}

    def get_personalized_bans(map_name):
        """Fetch heroes the user has lost to the most on this specific map"""
        try:
            # result='LOSS' in DB
            query = f"""
                SELECT mp.hero, COUNT(*) as losses 
                FROM matches m 
                JOIN match_players mp ON m.id = mp.match_id 
                WHERE m.map = ? AND m.result = 'LOSS' AND mp.win = 1 
                GROUP BY mp.hero 
                ORDER BY losses DESC 
                LIMIT 3
            """
            rows = DB._get_connection().execute(query, (map_name,)).fetchall()
            return [{"hero": r[0], "losses": r[1]} for r in rows]
        except:
            return []

    for map_name in maps:
        # PENTA-ROLE MANDATE: Exactly 2 per role (including Mage)
        roles_to_process = ['Tank', 'Healer', 'Ranged Assassin', 'Bruiser', 'Mage']
        role_candidates = {role: [] for role in roles_to_process}
        
        # Gather all user-compatible heroes for this map
        hero_stats = profile.get('hero_stats', {})
        for hero, hero_data in hero_stats.items():
            if hero in global_bans: continue
            
            # Identify role
            base_role = hero_to_role.get(hero)
            roles_to_assign = []
            
            if hero in MAGES:
                roles_to_assign.append('Mage')
            elif base_role in ['Tank', 'Healer', 'Bruiser']:
                roles_to_assign.append(base_role)
            elif base_role == 'Ranged Assassin':
                roles_to_assign.append('Ranged Assassin')
            
            if not roles_to_assign: continue
            
            # Check verified data
            verified_season = hero_data.get('verified_season_2025_3', {})
            verified_lifetime = hero_data.get('verified_lifetime', {})
            
            m_data = None
            source = "[Verified S3]"
            
            if verified_season and (verified_season.get('games') or 0) > 0:
                m_data = verified_season
                source = "[Verified S3]"
            elif verified_lifetime and (verified_lifetime.get('games') or 0) > 0:
                m_data = verified_lifetime
                source = "[Verified Lifetime]"
            
            if not m_data:
                map_stats = hero_map_stats.get(hero, {})
                for map_entry in map_stats.get('lifetime', []):
                    if map_entry.get('game_map') == map_name:
                        m_data = map_entry
                        source = "[Verified Map]"
                        break
            
            if m_data:
                wr = float(m_data.get('wr') or m_data.get('win_rate', 0))
                games = m_data.get('games') or m_data.get('games_played', 0)
                for r in roles_to_assign:
                    role_candidates[r].append({
                        'hero': hero, 'wr': wr, 'games': games,
                        'source': source
                    })

        final_recs = {role: [] for role in roles_to_process}
        map_strat = strategies.get(map_name, {})
        map_talent_map = {} 
        
        def pull_map_talents(obj):
            if not obj: return
            name = obj.get('name') or obj.get('hero')
            if name: map_talent_map[name] = obj

        pull_map_talents(map_strat.get('primary'))
        for b in (map_strat.get('backups') or []):
            if isinstance(b, dict): pull_map_talents(b)

        # SPECIAL OVERRIDE: Towers of Doom Specialist (Jaina)
        if map_name == "Towers of Doom":
             # Ensure Jaina is available in the pool even if she has low games, 
             # but don't fake her stats. 
             found = False
             for c in role_candidates['Mage']:
                 if c['hero'] == 'Jaina':
                     c['source'] = f"{c['source']} [Tactical Memory]"
                     c['insight'] = "Ammunition Generator: Sapper camps provide elite throughput."
                     found = True
                     break
             if not found:
                 role_candidates['Mage'].append({
                     'hero': 'Jaina', 'wr': 0, 'games': 0, 'source': '[Tactical Memory]',
                     'insight': "Ammunition Generator: Sapper camps provide elite throughput."
                 })

        # SELECTION ENGINE
        for role in roles_to_process:
            candidates = role_candidates[role]
            # SORTING LOGIC: 
            # 1. Experience Tier (>= 5 games) - Establish trust
            # 2. Performance Tier (>= 50% WR)
            # 3. Weighted score - WR * (1 + 0.1 * min(games, 10))
            # SPECIAL: Force Jaina to the top of Mage if it's ToD because of Research
            def get_sort_key(x):
                is_jaina_tod = (map_name == "Towers of Doom" and x['hero'] == "Jaina")
                return (
                    is_jaina_tod,
                    x['games'] >= 5, 
                    x['wr'] >= 50,
                    x['wr'] * (1 + 0.1 * min(x['games'], 10)),
                    x['games']
                )

            candidates.sort(key=get_sort_key, reverse=True)
            
            # Select Top 2
            for i in range(2):
                selection = None
                if i < len(candidates):
                    c = candidates[i]
                    # MANDATORY SPEC: Check Brain, then Map Strat, then Global
                    t_code = global_hero_builds.get(c['hero'], '')
                    
                    # Ensure T prefix for all codes
                    if t_code and not t_code.startswith('T'):
                        t_code = 'T' + t_code

                    # Hardcoded Backup Specs for Core Roster
                    if not t_code:
                        backup_specs = {
                            "Jaina": "T1311221", "Sylvanas": "T1231211", "Azmodan": "T1211213",
                            "Falstad": "T1212121", "Malthael": "T2112114", "Johanna": "T1221221",
                            "Stitches": "T1211213", "Lt. Morales": "T1211221", "Zagara": "T1231214"
                        }
                        t_code = backup_specs.get(c['hero'], "T0000000")

                    selection = {
                        'hero': c['hero'], 'wr': c['wr'], 'games': c['games'], 
                        'source': c['source'], 'talent_code': t_code, 
                        'insight': c.get('insight') or (map_talent_map.get(c['hero'], {}).get('insight', '') if c['hero'] in map_talent_map else '')
                    }
                else:
                    # Fallback to Meta for the role
                    selection = {
                        'hero': '[Meta Fallback]', 'wr': 0, 'games': 0, 
                        'source': '[Meta]', 'talent_code': '0000000', 'insight': 'Strategic necessity.'
                    }
                final_recs[role].append(selection)

        # ROLE SORTING: Sort the roles themselves by the max win rate in each category
        # This brings the user's best classes to the top
        def get_max_wr(role_name):
            recs = final_recs[role_name]
            return max([r['wr'] for r in recs]) if recs else 0
        
        sorted_roles = sorted(roles_to_process, key=get_max_wr, reverse=True)
        final_role_recs = {role: final_recs[role] for role in sorted_roles}

        # DRAFT SHIELD BANS (Personalized & Brief)
        rec_heroes = [h['hero'] for r in final_recs.values() for h in r]
        personal_bans = []
        
        # 1. Pull personalized "Nemesis" heroes for this specific map
        map_nemeses = get_personalized_bans(map_name)
        seen_bans = set()
        
        for n in map_nemeses:
            if n['hero'] not in seen_bans and n['hero'] not in rec_heroes:
                seen_bans.add(n['hero'])
                personal_bans.append({
                    "hero": n['hero'],
                    "priority": "HIGHEST" if len(personal_bans) == 0 else "HIGH" if len(personal_bans) == 1 else "MEDIUM",
                    "why": f"Killed you {n['losses']} times.",
                    "impact": "Deadly.",
                    "counter": "Prioritize."
                })

        # 2. Fallback to generic if we don't have enough personal data
        if len(personal_bans) < 3:
            ban_candidates = []
            for n in universal_nemeses: ban_candidates.append(n)
            for h in global_bans: ban_candidates.append(h)
            for h in map_strat.get('bans', []): ban_candidates.append(h)
            
            for b_name in ban_candidates:
                if b_name not in seen_bans and b_name not in rec_heroes:
                    seen_bans.add(b_name)
                    personal_bans.append({
                        "hero": b_name,
                        "priority": "HIGHEST" if len(personal_bans) == 0 else "HIGH" if len(personal_bans) == 1 else "MEDIUM",
                        "why": "Meta Threat.",
                        "impact": "Draft pressure.",
                        "counter": "Ban."
                    })
                if len(personal_bans) >= 3: break

        recommendations[map_name] = {
            'desc': map_strat.get('desc', 'Strategic priority required.'),
            'carry_hover': get_carry_hover(map_name, final_role_recs),
            'directives': get_map_directives(map_name),
            'role_recs': final_role_recs,
            'bans': personal_bans
        }
    
    cache_data = {'generated_at': datetime.now().isoformat(), 'recommendations': recommendations}
    # Save to SQLite KV Store
    DB.set_kv('map_recommendations_cache', cache_data)
    
    # Save legacy JSON
    try:
        cache_path = os.path.join(parent_dir, 'src', 'data', 'map_recommendations_cache.json')
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except: pass
    
    if verbose: print(f"✅ Mission Cache ready ({len(maps)} maps optimized)")
    
    return cache_data

if __name__ == '__main__':
    generate_map_recommendations(verbose="--verbose" in sys.argv)
