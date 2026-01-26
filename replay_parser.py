
import sys
import os
import json
import mpyq
import unicodedata

# Shim for 'imp' module (removed in Python 3.12)
# heroprotocol relies on it.
try:
    import imp
except ImportError:
    import types
    import importlib.util
    import importlib.machinery
    
    # Create a mock imp module
    imp = types.ModuleType('imp')
    sys.modules['imp'] = imp
    
    # Implement find_module
    def find_module(name, path=None):
        if path:
            for p in path:
                target = os.path.join(p, name + ".py")
                if os.path.exists(target):
                    return open(target, 'r'), target, ('.py', 'r', 1)
        raise ImportError(f"No module named {name}")

    imp.find_module = find_module

    # Implement load_module using importlib
    def load_module(name, file, filename, description):
        loader = importlib.machinery.SourceFileLoader(name, filename)
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module
        
    imp.load_module = load_module
    imp.load_source = load_module # Alias just in case

TALENTS_DB = None

# Parser version - increment when parser logic changes
PARSER_VERSION = "3.1"  # Logic upgrade: BoE Immortal Dmg + Stat Indentation fixes

try:
    from api.logger import ColoredLogger
except ImportError:
    # Fallback for standalone usage
    class ColoredLogger:
        @staticmethod
        def info(msg, service="DEBUG"): print(f"[{service}] {msg}")
        @staticmethod
        def success(msg, service="DEBUG"): print(f"[{service}] {msg}")
        @staticmethod
        def warn(msg, service="DEBUG"): print(f"[{service}] {msg}")
        @staticmethod
        def error(msg, service="DEBUG"): print(f"[{service}] {msg}")
        @staticmethod
        def processing(msg, service="DEBUG"): print(f"[{service}] {msg}")

def load_talent_data():
    global TALENTS_DB
    if TALENTS_DB is not None: return

    try:
        from database_manager import DatabaseManager
        db = DatabaseManager()
        TALENTS_DB = db.get_kv('talents')
        if TALENTS_DB:
            return
            
        # Fallback to file for safety or during development
        paths = ['src/data/talents.json', 'data/talents.json']
        for p in paths:
            if os.path.exists(p):
                with open(p, 'r') as f:
                    TALENTS_DB = json.load(f)
                return
        TALENTS_DB = {}
    except Exception as e:
        ColoredLogger.error(f"Error loading talents from SQL: {e}", "PARSER")
        TALENTS_DB = {}

def get_talent_from_index(hero_name, index, talent_db):
    if not talent_db or not hero_name: return None
    
    # Hero name mapping (Display -> Key)
    hero_key = None
    h_clean = hero_name.lower().replace(' ','').replace('.','').replace("'","")
    
    for k in talent_db.keys():
        k_clean = k.lower().replace(' ','').replace('.','').replace("'","")
        if k_clean == h_clean:
            hero_key = k
            break
            
    # Try internal map fallbacks if needed (e.g. Crusader -> Johanna)
    if not hero_key:
         # simple mapping attempt
         internal_map = {"crusader":"johanna", "amazon":"cassia", "barbarian":"sonya", "traitorhero":"varian", "necromancer":"xul", "wizard":"li-ming", "d3wizard":"li-ming", "witchdoctor":"nazeebo"}
         mapped = internal_map.get(hero_name.lower())
         if mapped:
             for k in talent_db.keys():
                if k.lower() == mapped:
                    hero_key = k
                    break

    if not hero_key: return None
    
    hero_talents = talent_db[hero_key]
    
    # 1-based index flattening
    curr = 0
    # Sort Tiers 1, 4, 7, 10, 13, 16, 20 (keys are strings "1", "2"...)
    # Actually keys in json are "1", "2"... corresponding to Tier Index (1-7)? Or Level?
    # View file 1182 saw "1", "2", "3"... "7".
    tiers = sorted(hero_talents.keys(), key=lambda x: int(x) if x.isdigit() else 99)
    for t in tiers:
        cols = hero_talents[t]
        sorted_cols = sorted(cols.keys(), key=lambda x: int(x) if x.isdigit() else 99)
        for c in sorted_cols:
            if curr == index:
                return cols[c].get('tooltipId')
            curr += 1
    return None

    def find_module(name, path=None):
        # print(f"DEBUG: find_module name={name} path={path}")
        if path:
            for directory in path:
                # Look for .py file
                file_path = os.path.join(directory, name + ".py")
                if os.path.exists(file_path):
                    # print(f"DEBUG: Found {file_path}")
                    fp = open(file_path, 'r')
                    return (fp, file_path, (".py", "r", imp.PY_SOURCE))
        
        # Fallback to standard importlib
        try:
             spec = importlib.util.find_spec(name, path)
             if spec is None:
                 raise ImportError(f"No module named {name}")
             return (None, spec.origin, ("", "", imp.PY_SOURCE))
        except Exception as e:
             raise ImportError(f"No module named {name} ({e})")

    def load_module(name, file, pathname, description):
        if file:
            file.close() # importlib handles opening
        
        try:
            spec = importlib.util.spec_from_file_location(name, pathname)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                return module
        except Exception as e:
            raise ImportError(f"Failed to load module {name} from {pathname}: {e}")
            
    imp.load_source = load_source
    imp.find_module = find_module
    imp.load_module = load_module
    imp.PY_SOURCE = 1
    imp.PKG_DIRECTORY = 5

from heroprotocol.versions import build, latest

def get_match_id(replay_path):
    """Fast function to get just the match ID from a replay header."""
    try:
        if not os.path.exists(replay_path): return None
        archive = mpyq.MPQArchive(replay_path)
        header = latest().decode_replay_header(archive.header['user_data']['content'])
        
        # Consistent with ID logic in parse_replay
        import hashlib
        id_components = [
            str(header.get('m_randomValue', '')),
            str(header.get('m_signature', '')),
            str(header.get('m_timeUTC', 0)),
            str(header.get('m_elapsedGameLoops', 0)),
            str(header.get('m_version', {}).get('m_baseBuild', 0))
        ]
        return hashlib.md5('_'.join(id_components).encode()).hexdigest()[:16]
    except:
        return None

def parse_replay(replay_path, options=None):
    """
    Parses a .StormReplay file and extracts key metrics for the Hardcore Coach analysis.
    Returns: A dictionary with 'map', 'players', 'winners', 'stats'.
    """
    load_talent_data()

    if not os.path.exists(replay_path):
        print(f"Error: Replay file not found: {replay_path}")
        return None

    try:
        archive = mpyq.MPQArchive(replay_path)

        # 1. Determine Protocol Version & Unique Match ID
        header_content = archive.header['user_data_header']['content']
        header = latest().decode_replay_header(header_content)
        base_build = header['m_version']['m_baseBuild']
        
        # Game Duration Logic
        game_loops = header.get('m_elapsedGameLoops', 0)
        game_duration_seconds = game_loops / 16.0
        minutes = int(game_duration_seconds // 60)
        seconds = int(game_duration_seconds % 60)
        time_played_str = f"{minutes}:{seconds:02d}"
        
        # Extract timestamp from replay (m_timeUTC is in Windows FILETIME format)
        # FILETIME = 100-nanosecond intervals since January 1, 1601 UTC
        time_utc = header.get('m_timeUTC', 0)
        if time_utc:
            # Convert Windows FILETIME to Unix timestamp
            # FILETIME epoch is 1601-01-01, Unix epoch is 1970-01-01
            # Difference is 116444736000000000 (100-nanosecond intervals)
            unix_timestamp = (time_utc - 116444736000000000) / 10000000
            from datetime import datetime, timezone
            match_datetime = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc)
            timestamp_iso = match_datetime.isoformat()
        else:
            # Fallback: Extract timestamp from filename
            # Replay filenames: "2025-12-29 05.06.53 Map.StormReplay" or "Replay 2025-12-29 14-30-45.StormReplay"
            import re
            from datetime import datetime, timezone
            filename = os.path.basename(replay_path)
            # Try to match "YYYY-MM-DD HH.MM.SS" or "YYYY-MM-DD HH-MM-SS" pattern
            match = re.search(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2})[.-](\d{2})[.-](\d{2})', filename)
            if match:
                year, month, day, hour, minute, second = match.groups()
                match_datetime = datetime(int(year), int(month), int(day), 
                                         int(hour), int(minute), int(second), 
                                         tzinfo=timezone.utc)
                timestamp_iso = match_datetime.isoformat()
            else:
                timestamp_iso = None
        
        # Generate unique match ID using multiple fields
        import hashlib
        id_components = [
            str(header.get('m_randomValue', '')),
            str(header.get('m_signature', '')),
            str(time_utc),
            str(game_loops),
            str(base_build)
        ]
        match_id = hashlib.md5('_'.join(id_components).encode()).hexdigest()[:16]

        # ColoredLogger.info(f"Loading replay (Build: {base_build}, Duration: {time_played_str})", "PARSER")
        protocol = latest()

        # EARLY QM CHECK - Do this BEFORE parsing details/tracker events
        try:
            init_data = protocol.decode_replay_initdata(archive.read_file('replay.initData'))
            game_desc = init_data.get('m_syncLobbyState', {}).get('m_gameDescription', {})
            
            # Extract game mode
            game_mode = game_desc.get('m_gameMode', b'').decode('utf-8') if isinstance(game_desc.get('m_gameMode'), bytes) else str(game_desc.get('m_gameMode', ''))
            is_ranked = game_desc.get('m_isRanked', False)
            
            
            
            # REJECT Quick Match immediately - DISABLED, Rely on Ban Detection
            # if not is_ranked and 'storm' not in game_mode.lower() and 'ranked' not in game_mode.lower():
            #     print(f"⚠️  REJECTED: Non-Storm League game (mode: '{game_mode}')")
            #     return {
            #         "status": "rejected",
            #         "message": f"Quick Match detected. Only Storm League replays are processed."
            #     }
        except Exception as e:
            print(f"WARNING: Could not determine game mode early: {e}")
            # Continue parsing - will check bans later as fallback
        
        # 2. Extract Details (Map, Players, Result)
        details = protocol.decode_replay_details(archive.read_file('replay.details'))
        
        map_name = details.get('m_title', b'').decode('utf-8')
        if not map_name:
            try:
                init_data = protocol.decode_replay_initdata(archive.read_file('replay.initData'))
                map_name = init_data['m_syncLobbyState']['m_gameDescription']['m_mapFileName'].decode('utf-8')
            except Exception:
                map_name = "Unknown Map"

        # REJECT ARAM and Brawl maps (Single-lane/Non-Competitive)
        non_sl_maps = [
            'lost cavern', 'silver city', 'industrial district', 'braxis outpost',
            'checkpoint', 'pull party', 'pool party', 'escape from braxis',
            'deadman\'s stand', 'sandbox', 'try me', 'blackheart\'s revenge',
            'haunted mines', 'tutorial', 'hallow\'s end', 'snow brawl'
        ]
        map_low = map_name.lower().replace(' ', '')
        if any(m.replace(' ', '') in map_low for m in non_sl_maps) or ('hanamura' in map_low and 'temple' not in map_low):
            ColoredLogger.warn(f"REJECTED: Non-competitive map '{map_name}' detected.", "PARSER")
            return {
                "status": "rejected",
                "message": f"Non-competitive map '{map_name}' ignored. Only Storm League battlegrounds are processed."
            }

        players = []
        winning_team = None 

        for p in details['m_playerList']:
            name = p['m_name'].decode('utf-8')
            team = p['m_teamId']
            result = p['m_result'] # 1 = Win, 2 = Loss
            if result == 1:
                winning_team = team
            
            hero = p['m_hero'].decode('utf-8')
            
            # Extract additional player info
            hero_level = p.get('m_heroLevel', 0)  # Hero mastery level
            account_level = p.get('m_playerLevel', 0)  # Account level
            
            # Rank is often missing from details, we will try to fill it from InitData later
            rank = None
            
            players.append({
                'name': name,
                'hero': hero,
                'team': team,
                'win': (result == 1),
                'hero_level': hero_level,
                'account_level': account_level,
                'rank': rank 
            })

        # 5. Extract Tracker Events (Stats: KDA, Talents, XP)
        
        tracker_events = protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events'))
        
        # Initialize stats containers (Range 0-16 for safety)
        stats_data = {i: {'stats': {}, 'talents': [], 'banking_ledger': [], 'current_balance': 0, 'last_collection_time': None} for i in range(0, 16)} 
        
        bans = []
        team_level_milestones = {0: {10: None, 20: None}, 1: {10: None, 20: None}}
        talent_event_count = 0
        
        # Trackers for map events
        if 'merc_captures' not in stats_data: stats_data['merc_captures'] = []
        if 'structure_destructions' not in stats_data: stats_data['structure_destructions'] = []
        if 'boss_captures' not in stats_data: stats_data['boss_captures'] = []
        if 'objective_events' not in stats_data: stats_data['objective_events'] = []
        
        # Boss engagement tracking for kill speed calculation
        active_boss_engagements = {}  # boss_unit_tag -> {'start_time': gameloop, 'team': team_id}
        
        # Unit tag tracking for death attribution
        unit_tags = {} # tag_index -> {type, player_id}
        
        # --- NEW: Extract Static Talents from InitData (Better IDs) ---
        try:
            init_data = protocol.decode_replay_initdata(archive.read_file('replay.initData'))
            lobby_state = init_data.get('m_syncLobbyState', {}).get('m_lobbyState', {})
            slots = lobby_state.get('m_slots', [])
            
            for slot in slots:
                # Find which player this slot belongs to
                # We need to map slot info to our players list. 
                # Slot has m_toon -> m_id (battletagish) or m_hero
                hero_name_bytes = slot.get('m_hero', b'')
                hero_name = hero_name_bytes.decode('utf-8') if isinstance(hero_name_bytes, bytes) else str(hero_name_bytes)
                
                # Try to get Name from m_toon?
                # structure: 'm_toon': {'m_region': 1, 'm_programId': 1796676232, 'm_realm': 1, 'm_id': 1234567}
                # No name directly usually.
                
                # Debug Names
                
                
                # Match to our players list by Hero (Primary)
                # Fallback: Can we match by index? 
                # replay.details m_playerList usually excludes observers so indices might mismatch if observers exist.
                # But 'slots' usually includes empty slots too?
                
                target_pid = None
                for i, p in enumerate(players):
                    # Robust Match: Ignore Case, Remove Spaces/Dots/Accents
                    def clean(s):
                        if not s: return ""
                        # Normalize unicode (accents) -> ASCII (e.g. Lúcio -> Lucio)
                        s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
                        return s.lower().replace('.','').replace(' ','').replace("'", "")
                    
                    # Manual Mappings for internal engine names to display names.
                    # These are REQUIRED for technical parity with Blizzard's engine.
                    internal_map = {
                        "tinker": "gazlowe",      # Legacy WC3 class name
                        "medic": "ltmorales",
                        "sgthammer": "sgthammer",
                        "witchdoctor": "nazeebo",
                        "crusader": "johanna",
                        "barbarian": "sonya", 
                        "demonhunter": "valla",
                        "monk": "kharazim",
                        "traitorhero": "varian",
                        "amazon": "cassia",
                        "wizard": "li-ming",
                        "d3wizard": "li-ming",
                        "butcher": "thebutcher",
                        "faeriedragon": "brightwing",
                        "necromancer": "xul",
                        "wanderer": "chen",
                        "dryad": "lunara",
                        "siegebreaker": "azmodan",
                        "firebat": "blaze",
                        "cryptlord": "anubarak",
                        "lichlord": "kelthuzad",
                        "nexuslord": "deathwing",
                        "nexushunter": "qhira",
                        "lostvikings": "lostvikings"
                    }
                    
                    p_hero_clean = clean(p['hero'])
                    s_hero_clean = clean(hero_name) # From InitData
                    mapped = internal_map.get(s_hero_clean, s_hero_clean)
                    
                    if p_hero_clean == mapped or p_hero_clean == s_hero_clean or (len(p_hero_clean) >= 3 and p_hero_clean in s_hero_clean):
                         target_pid = i + 1 
                         break
                
                if target_pid:
                    if 'm_talents' in slot:
                        talents = slot['m_talents']
                         
                        if isinstance(talents, list):
                            for talent in talents:
                                if isinstance(talent, dict):
                                    talent_id_bytes = talent.get('m_abilityLink', b'')
                                    talent_id = talent_id_bytes.decode('utf-8') if isinstance(talent_id_bytes, bytes) else str(talent_id_bytes)
                                    if talent_id:
                                        # EXCLUDE GARBAGE (Map Vehicles, Cosmetics)
                                        garbage = ['Vehicle', 'Mount', 'Hearthstone', 'Spray', 'Voice', 'Banner', 'Announcer', 'Skin', 'Portrait', 'Dragon', 'Terror', 'Triglav']
                                        stats_data[target_pid]['talents'].append({
                                            "timestamp": 0, # Static pick
                                            "talent_name": talent_id, # This is the good ID!
                                            "source": "init"
                                        })
                                        talent_event_count += 1
        except Exception as e:
            pass # Silent failure for InitData talents

        # DEBUG LOGGING
        debug_path = os.path.join(os.getcwd(), 'parser_debug.log')
        with open(debug_path, 'w') as f:
            f.write(f"Header Keys: {list(header.keys())}\n")
            f.write(f"Game Loops: {header.get('m_elapsedGameLoops')}\n")
            
            logged_upgrade = False
            logged_talent = False

            for event in tracker_events:
                event_type = event['_event']
                
                # --- UNIT TRACKING ---
                if 'SUnitBornEvent' in event_type:
                    tag = event.get('m_unitTagIndex')
                    if tag is not None:
                        u_type = event.get('m_unitTypeName', b'').decode('utf-8') if isinstance(event.get('m_unitTypeName'), bytes) else str(event.get('m_unitTypeName', ''))
                        u_pid = event.get('m_controlPlayerId', event.get('m_upkeepPlayerId'))
                        unit_tags[tag] = {'type': u_type, 'pid': u_pid}
                        
                        # Detect boss spawns (neutral units with "Boss" in type)
                        boss_keywords = ['Boss', 'GraveyardBoss', 'ArchangelSiege', 'WebweaverQueen', 'SlimeBoss']
                        if any(kw in u_type for kw in boss_keywords) and u_pid is None:
                            # Boss spawned, mark as available for engagement tracking
                            unit_tags[tag]['is_boss'] = True
                
                # --- BANS ---
                event_type = event['_event']
                
                # --- BANS ---
                # --- BANS ---
                if 'SHeroBannedEvent' in event_type:
                    # Attempt to identify the banning team
                    team_id = event.get('m_controllingTeam')
                    
                    # If not directly available, try via User ID
                    if team_id is None:
                        user_wrapper = event.get('_userid', {})
                        if isinstance(user_wrapper, dict):
                            uid = user_wrapper.get('m_userId')
                            # Map UserID to Team (UserID is usually 0-9)
                            if uid is not None and 0 <= uid < len(players):
                                team_id = players[uid]['team']
                    
                    ban_entry = {
                        'hero': event.get('m_hero', b'').decode('utf-8'),
                        'gameloop': event['_gameloop'],
                        'team': team_id
                    }
                    bans.append(ban_entry)

                # --- TALENTS (Legacy) ---
                elif 'STalentChosenEvent' in event_type:
                     if not logged_talent:
                         f.write(f"SAMPLE TALENT EVENT: {event}\n")
                         logged_talent = True

                     pid = event.get('m_controlPlayerId')
                     if pid is None: pid = event.get('m_userid')
                     
                     if pid is not None and pid in stats_data:
                          idx = event.get('m_talentNameIndex')
                          rich_id = None
                          if idx is not None:
                              # We need the hero name for this PID to look up in TALENTS_DB
                              # The players list is 0-indexed, pid is 1-indexed
                              player_idx = pid - 1
                              if 0 <= player_idx < len(players):
                                  hero_n = players[player_idx]['hero']
                                  rich_id = get_talent_from_index(hero_n, idx, TALENTS_DB)
                                  
                                  # EXCLUDE GARBAGE (Map Vehicles, Cosmetics)
                                  if rich_id:
                                      garbage = ['Vehicle', 'Mount', 'Hearthstone', 'Spray', 'Voice', 'Banner', 'Announcer', 'Skin', 'Portrait']
                                      if any(g in rich_id for g in garbage):
                                          continue

                          talent_data = {
                              "timestamp": round(event['_gameloop'] / 16.0, 1),
                              "talent_index": idx,
                              "talent_name": rich_id if rich_id else f"Talent Index {idx}",
                              "source": "tracker_legacy"
                          }
                          stats_data[pid]['talents'].append(talent_data)
                          talent_event_count += 1

                # --- UPGRADES (Modern Talents) ---
                elif 'SUpgradeEvent' in event_type:
                     if not logged_upgrade:
                         f.write(f"SAMPLE UPGRADE EVENT: {event}\n")
                         logged_upgrade = True
                         
                     pid = event.get('m_playerId')
                     if pid is None: pid = event.get('m_controlPlayerId')
                     if pid is None: pid = event.get('m_userid')

                     if pid is not None and pid in stats_data:
                         upgrade_name = event.get('m_upgradeTypeName', b'').decode('utf-8')
                         IGNORE_UPGRADES = {
                             'IsOnChaosTeam', 'IsOnOrderTeam', 'HeroRingMasteryUpgrade', 'GatesAreOpen', 
                             'MinionsAreSpawning', 'GameStart', 'TownStructureInvulnerable',
                             'Dazed', 'Stunned', 'Silence', 'Taunt', 'Polymorph',
                             'CreepColor', 'IsPlayer', 'IsAlliance', 'IsHorde', 'IsHuman',
                             'IsOrderPlayer', 'IsChaosPlayer', 'IsOrder', 'IsChaos'
                         }
                         
                         if upgrade_name and not any(ig in upgrade_name for ig in IGNORE_UPGRADES):
                             # EXCLUDE GARBAGE (Map Vehicles, Cosmetics)
                             garbage = ['Vehicle', 'Mount', 'Hearthstone', 'Spray', 'Voice', 'Banner', 'Announcer', 'Skin', 'Portrait', 'Dragon', 'Terror', 'Triglav']
                             if any(g in upgrade_name for g in garbage):
                                 continue
                             
                             # stats_data[pid]['talents'].append(...)
                             # Check if we have this from InitData already?
                             # InitData has "AbilityLink" (e.g. TracerRecall)
                             # UpgradeEvent has "UpgradeTypeName" (e.g. TracerRecall)
                             # usually they match!
                             
                             # We'll add it, but note the timestamp, which InitData lacks.
                             talent_data = {
                                 "timestamp": round(event['_gameloop'] / 16.0, 1),
                                 "talent_name": upgrade_name,
                                 "source": "tracker_modern"
                             }
                             stats_data[pid]['talents'].append(talent_data)
                             talent_event_count += 1

                elif 'SScoreResultEvent' in event_type:
                     for stat_entry in event.get('m_instanceList', []):
                         name_bytes = stat_entry.get('m_name')
                         if not name_bytes: continue
                         stat_name = name_bytes.decode('utf-8')
                         
                         values_by_player = stat_entry.get('m_values', [])
                         for i, val_list in enumerate(values_by_player):
                             if val_list and len(val_list) > 0:
                                 val = val_list[-1].get('m_value')
                                 pid = i + 1 
                                 if pid in stats_data:
                                     stats_data[pid]['stats'][stat_name] = val
                
                # --- STAT GAME EVENTS (Direct Map Data) ---
                elif 'SStatGameEvent' in event_type:
                    ename = event.get('m_eventName', b'').decode('utf-8')
                    
                    if ename == 'JungleCampCapture':
                        merc_timestamp = round(event['_gameloop'] / 16.0, 1)
                        data_map = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or []) + (event.get('m_fixedData') or [])}
                        str_map = {d.get('m_key', b'').decode('utf-8'): d.get('m_value', b'').decode('utf-8') for d in (event.get('m_stringData') or [])}
                        
                        team_raw = data_map.get('TeamID', 0)
                        team_id = 0 if team_raw == 4096 else 1 if team_raw == 8192 else None
                        
                        camp_type = str_map.get('CampType', 'Merc Camp')
                        
                        # Identify boss camps by CampType string
                        boss_keywords = ['Boss', 'GraveyardBoss', 'Archangel', 'Webweaver', 'SlimeBoss', 'SeedTerror']
                        is_boss = any(kw in camp_type for kw in boss_keywords)
                        
                        if is_boss:
                            # Boss capture - calculate kill speed from engagement tracking
                            kill_speed = None
                            participants = []
                            
                            # Find matching engagement by team and approximate timing
                            for boss_tag, engagement in list(active_boss_engagements.items()):
                                if engagement['team'] == team_id:
                                    # Calculate kill speed in seconds
                                    start_loop = engagement['start_gameloop']
                                    end_loop = event['_gameloop']
                                    kill_speed = round((end_loop - start_loop) / 16.0, 1)
                                    
                                    # Remove from active engagements
                                    del active_boss_engagements[boss_tag]
                                    break
                            
                            boss_event = {
                                'timestamp': merc_timestamp,
                                'captured_by_team': team_id,
                                'boss_type': camp_type,
                                'kill_speed_seconds': kill_speed,
                                'gameloop': event['_gameloop']
                            }
                            stats_data['boss_captures'].append(boss_event)
                        else:
                            # Regular merc camp
                            merc_event = {
                                'timestamp': merc_timestamp,
                                'captured_by_team': team_id,
                                'unit_name': camp_type,
                                'gameloop': event['_gameloop']
                            }
                            stats_data['merc_captures'].append(merc_event)
                        
                    elif ename == 'TownStructureDeath':
                        struct_timestamp = round(event['_gameloop'] / 16.0, 1)
                        str_map = {d.get('m_key', b'').decode('utf-8'): d.get('m_value', b'').decode('utf-8') for d in (event.get('m_stringData') or [])}
                        data_map = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or [])}
                        
                        # Identify destroying team from first killer
                        destroying_team = None
                        killers = [v for k, v in data_map.items() if k == 'KillingPlayer']
                        if isinstance(killers, list) and len(killers) > 0:
                            k_pid = killers[0]
                            if 0 <= (k_pid - 1) < len(players):
                                destroying_team = players[k_pid - 1]['team']
                        
                        struct_event = {
                            'timestamp': struct_timestamp,
                            'structure_type': str_map.get('UnitType', 'Structure'),
                            'destroyed_by_team': destroying_team,
                            'gameloop': event['_gameloop']
                        }
                        stats_data['structure_destructions'].append(struct_event)

                    elif ename == 'EndOfGameXPBreakdown':
                        data_map = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or []) + (event.get('m_fixedData') or [])}
                        pid = data_map.get('PlayerID')
                        if pid and pid in stats_data:
                            # These are scaled by 4096.0 in the replay file
                            stats_data[pid]['stats']['HeroXP'] = round(data_map.get('HeroXP', 0) / 4096.0)
                            stats_data[pid]['stats']['MinionXP'] = round(data_map.get('MinionXP', 0) / 4096.0)
                            stats_data[pid]['stats']['StructureXP'] = round(data_map.get('StructureXP', 0) / 4096.0)
                            stats_data[pid]['stats']['CreepXP'] = round(data_map.get('CreepXP', 0) / 4096.0)
                            stats_data[pid]['stats']['SiegeXP'] = round(data_map.get('SiegeXP', 0) / 4096.0)
                            stats_data[pid]['stats']['TrickleXP'] = round(data_map.get('TrickleXP', 0) / 4096.0)

                    elif ename in [
                        # Blackheart's Bay
                        'DoubloonsCollected', 'BlackheartDoubloonsCollected', 'BlackheartDoubloonsTurnedIn',
                        # Tomb of the Spider Queen
                        'GemsCollected', 'SoulGemsCollected', 'SoulGemsTurnedIn', 'GemsTurnedIn',
                        # Warhead Junction
                        'WarheadCollected', 'WarheadActivated', 'NukeCollected', 'NukeActivated',
                        # Cursed Hollow
                        'TributeCollected', 'TributeTurnedIn',
                        # Towers of Doom
                        'AltarDamageDone', 'AltarCaptured',
                        # Garden of Terror
                        'SeedsCollected', 'SeedsTurnedIn',
                        # Sky Temple
                        'TempleActivated', 'TempleCaptured',
                        # Battlefield of Eternity
                        'DamageDoneToImmortal'
                    ]:
                        data_map = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or []) + (event.get('m_fixedData') or [])}
                        pid = data_map.get('PlayerID')
                        if pid and pid in stats_data:
                            # Map event name to its stat key
                            mapping = {
                                # Blackheart's Bay
                                'DoubloonsCollected': 'BlackheartDoubloonsCollected',
                                'BlackheartDoubloonsCollected': 'BlackheartDoubloonsCollected',
                                'BlackheartDoubloonsTurnedIn': 'BlackheartDoubloonsTurnedIn',
                                'DoubloonsTurnedIn': 'BlackheartDoubloonsTurnedIn',
                                # Tomb of the Spider Queen
                                'GemsCollected': 'GemsCollected',
                                'SoulGemsCollected': 'GemsCollected',
                                'SoulGemsTurnedIn': 'GemsTurnedIn',
                                'GemsTurnedIn': 'GemsTurnedIn',
                                # Warhead Junction
                                'WarheadCollected': 'WarheadsCollected',
                                'NukeCollected': 'WarheadsCollected',
                                'WarheadActivated': 'WarheadsActivated',
                                'NukeActivated': 'WarheadsActivated',
                                # Cursed Hollow
                                'TributeCollected': 'TributesCollected',
                                'TributeTurnedIn': 'TributesTurnedIn',
                                # Towers of Doom
                                'AltarCaptured': 'AltarsCaptured',
                                'AltarDamageDone': 'AltarDamageDone',
                                # Garden of Terror
                                'SeedsCollected': 'SeedsCollected',
                                'SeedsTurnedIn': 'SeedsTurnedIn',
                                # Sky Temple
                                'TempleActivated': 'TemplesActivated',
                                'TempleCaptured': 'TemplesActivated',
                                # Battlefield of Eternity
                                'DamageDoneToImmortal': 'DamageDoneToImmortal'
                            }
                            stat_key = mapping.get(ename)
                            if stat_key:
                                # Add to existing or initialize
                                current = stats_data[pid]['stats'].get(stat_key, 0)
                                # Try multiple keys - different events use different field names
                                val = data_map.get('count') or data_map.get('amount') or data_map.get('value') or data_map.get('Count') or data_map.get('Amount') or data_map.get('Value') or 0
                                # If still 0 and it's a collection event, assume it's 1 (single event per coin)
                                if val == 0 and 'Collected' in ename:
                                    val = 1
                                stats_data[pid]['stats'][stat_key] = current + val
                                
                                # --- BANKING ANALYTICS (DISABLED - Replay format limitation) ---
                                LEDGER_TRACKED_STATS = [
                                    'BlackheartDoubloonsCollected', 'BlackheartDoubloonsTurnedIn',
                                    'GemsCollected', 'GemsTurnedIn',
                                    'WarheadsCollected', 'WarheadsActivated',
                                    'TributesCollected', 'TributesTurnedIn',
                                    'SeedsCollected', 'SeedsTurnedIn',
                                    'TemplesActivated',
                                ]
                                
                                if stat_key in LEDGER_TRACKED_STATS:
                                    current_time = round(event['_gameloop'] / 16.0, 1)
                                    balance = stats_data[pid].get('current_balance', 0)
                                    last_collection = stats_data[pid].get('last_collection_time')
                                    
                                    is_collection = any(keyword in stat_key for keyword in ['Collected'])
                                    is_turnin = any(keyword in stat_key for keyword in ['TurnedIn', 'Activated'])
                                    is_instant_use = stat_key in ['WarheadsActivated', 'TemplesActivated']
                                    
                                    hold_duration = None
                                    if not is_collection and not is_instant_use and last_collection is not None:
                                        hold_duration = round(current_time - last_collection, 1)
                                    
                                    if is_collection and not is_instant_use:
                                        balance += val
                                        stats_data[pid]['last_collection_time'] = current_time
                                    elif is_turnin and not is_instant_use:
                                        balance = max(0, balance - val)
                                        if balance == 0:
                                            stats_data[pid]['last_collection_time'] = None
                                        
                                    if not is_instant_use:
                                        stats_data[pid]['current_balance'] = balance
                                    
                                    ledger_entry = {
                                        't': current_time,
                                        'action': 'COLLECT' if is_collection else ('TURN_IN' if is_turnin else 'ACTIVATE'),
                                        'amount': val,
                                        'balance': balance if not is_instant_use else 0
                                    }
                                    if hold_duration is not None:
                                        ledger_entry['hold_duration'] = hold_duration
                                    
                                    stats_data[pid]['banking_ledger'].append(ledger_entry)

                    # --- GENERIC OBJECTIVE TRACKING (Forensics) ---
                    obj_keywords = ['Spawned', 'Captured', 'Killed', 'Activated', 'Collected', 'Start', 'End', 'Warning', 'Update']
                    if any(kw in ename for kw in obj_keywords) and ename not in ['JungleCampCapture', 'TownStructureDeath', 'EndOfGameXPBreakdown']:
                         # Coordinates often in fixedData
                         pt = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_fixedData') or [])}
                         stats_data['objective_events'].append({
                             'event_name': ename,
                             'timestamp': round(event['_gameloop'] / 16.0, 1),
                             'point': pt,
                             'gameloop': event['_gameloop']
                         })
                # --- BOSS DAMAGE TRACKING (for kill speed) ---
                elif 'SUnitDamageEvent' in event_type:
                    target_tag = event.get('m_targetUnitTagIndex')
                    attacker_pid = event.get('m_attackerPlayerId')
                    
                    if target_tag and attacker_pid and target_tag in unit_tags:
                        target_unit = unit_tags[target_tag]
                        # Check if target is a boss
                        if target_unit.get('is_boss') and target_tag not in active_boss_engagements:
                            # First damage to this boss - start tracking
                            if 1 <= attacker_pid <= 10:
                                attacker_team = players[attacker_pid - 1]['team']
                                active_boss_engagements[target_tag] = {
                                    'start_gameloop': event['_gameloop'],
                                    'team': attacker_team,
                                    'boss_type': target_unit['type']
                                }

                # --- POSITION TRACKING (Sampling for Forensics) ---
                elif 'SUnitPositionsEvent' in event_type:
                    first_tag = event.get('m_firstUnitIndex')
                    items = event.get('m_items')
                    current_time = round(event['_gameloop'] / 16.0, 1)  # Convert to seconds
                    if first_tag is not None and items:
                        tag = first_tag
                        for i in range(0, len(items), 3):
                            if i + 2 >= len(items): break
                            tag += items[i]
                            x = items[i+1]
                            y = items[i+2]
                            # Update last known position for this unit tag
                            unit_info = unit_tags.get(tag)
                            if unit_info and unit_info['pid']:
                                pid = unit_info['pid']
                                if pid in stats_data:
                                    # Initialize position_samples array if needed
                                    if 'position_samples' not in stats_data[pid]:
                                        stats_data[pid]['position_samples'] = []
                                    
                                    # Sample every 5 seconds to manage file size
                                    last_sample = stats_data[pid]['position_samples'][-1] if stats_data[pid]['position_samples'] else None
                                    if not last_sample or (current_time - last_sample['timestamp']) >= 5.0:
                                        stats_data[pid]['position_samples'].append({
                                            'timestamp': current_time,
                                            'x': x,
                                            'y': y
                                        })
                                    
                                    # Maintain backward compatibility with last_pos
                                    stats_data[pid]['last_pos'] = (x, y)

                # --- DEATH EVENTS (Enhanced with Kill Context) ---
                elif 'SUnitDiedEvent' in event_type:
                    unit_tag = event.get('m_unitTagIndex')
                    death_timestamp = round(event['_gameloop'] / 16.0, 1)
                    
                    # PSEUDO-HERO FILTER: Exclude vehicles and boss forms from hero death counts
                    EXCLUDE_UNIT_TYPES = ['MoltenCore', 'Vehicle', 'Dragon', 'Terror', 'Triglav', 'Shapeshift', 'Pet', 'Summon']
                    
                    # Identify victim from unit_tags
                    victim = unit_tags.get(unit_tag)
                    if victim and victim['pid'] is not None and 1 <= victim['pid'] <= 10:
                        # ONLY record Hero deaths, explicitly exclude non-hero forms
                        v_type = victim['type']
                        if 'Hero' in v_type and not any(ex in v_type for ex in EXCLUDE_UNIT_TYPES):
                            v_pid = victim['pid']
                            
                            # --- NEW: Banking Forensics (Drop tracking) ---
                            v_balance = stats_data[v_pid].get('current_balance', 0)
                            if v_balance > 0:
                                last_collection = stats_data[v_pid].get('last_collection_time')
                                hold_duration = None
                                if last_collection is not None:
                                    hold_duration = round(death_timestamp - last_collection, 1)
                                
                                ledger_entry = {
                                    't': death_timestamp,
                                    'action': 'DROPPED_ON_DEATH',
                                    'amount': v_balance,
                                    'balance': 0
                                }
                                if hold_duration is not None:
                                    ledger_entry['hold_duration'] = hold_duration
                                
                                stats_data[v_pid]['banking_ledger'].append(ledger_entry)
                                stats_data[v_pid]['current_balance'] = 0
                                stats_data[v_pid]['last_collection_time'] = None

                            # DE-DUPLICATE: Don't record multiple deaths for same unit tag in same second
                            if 'death_events' not in stats_data[v_pid]: stats_data[v_pid]['death_events'] = []
                            last_death = stats_data[v_pid]['death_events'][-1] if stats_data[v_pid]['death_events'] else None
                            if last_death and abs(last_death['timestamp'] - death_timestamp) < 2:
                                # Update existing record if new one has more killer info
                                if not last_death['killer_pid']:
                                    last_death['killer_pid'] = event.get('m_killerPlayerId')
                                continue

                            killer_pid = event.get('m_killerPlayerId')
                            killer_tag = event.get('m_killerUnitTagIndex')
                            killer_type = "Hero" if killer_pid else "Unknown"
                            
                            if not killer_pid and killer_tag in unit_tags:
                                killer_type = unit_tags[killer_tag]['type']
                            
                            death_info = {
                                'timestamp': death_timestamp,
                                'gameloop': event['_gameloop'],
                                'killer_pid': killer_pid,
                                'killer_type': killer_type,
                                'outnumbered': False # Default, will be synced if possible
                            }

                            # POSITION FORENSICS: Calculate distance to allies
                            pos = stats_data[v_pid].get('last_pos')
                            if pos:
                                distances = []
                                v_team = players[v_pid-1]['team'] if 1 <= v_pid <= 10 else None
                                for other_pid in range(1, 11):
                                    if other_pid != v_pid and other_pid in stats_data:
                                        other_team = players[other_pid-1]['team']
                                        if other_team == v_team:
                                            other_pos = stats_data[other_pid].get('last_pos')
                                            if other_pos:
                                                dist = ((pos[0]-other_pos[0])**2 + (pos[1]-other_pos[1])**2)**0.5
                                                distances.append(dist)
                                if distances:
                                    death_info['dist_to_nearest_ally'] = round(min(distances), 1)

                            stats_data[v_pid]['death_events'].append(death_info)
                        
                    # Original legacy tracking for structures if not caught by SStatGameEvent
                    unit_type = event.get('m_unitTypeName', b'').decode('utf-8') if isinstance(event.get('m_unitTypeName'), bytes) else str(event.get('m_unitTypeName', ''))
                    structure_keywords = ['TownTownHall', 'TownWall', 'TownGate', 'TownCannonTower', 'Fort', 'Keep', 'Core']
                    if any(kw in unit_type for kw in structure_keywords):
                        exists = any(abs(s['timestamp'] - death_timestamp) < 2 for s in stats_data['structure_destructions'])
                        if not exists:
                            killer_pid = event.get('m_killerPlayerId')
                            team = players[killer_pid-1]['team'] if killer_pid and 1 <= killer_pid <= 10 else None
                            stats_data['structure_destructions'].append({
                                'timestamp': death_timestamp,
                                'structure_type': unit_type,
                                'destroyed_by_team': team,
                                'gameloop': event['_gameloop']
                            })

        
        if True:  # Always process game events for Cho/Gall/TLV support
             
             try:
                 # Re-read archive? decoding game events is expensive but necessary
                 game_events = protocol.decode_replay_game_events(archive.read_file('replay.game.events'))
                 for event in game_events:
                     if event['_event'] == 'NNet.Game.SHeroTalentTreeSelectedEvent':
                         # {'m_index': 8, '_userid': {'m_userId': 3}, ...}
                         idx = event.get('m_index')
                         user_id = event.get('_userid', {}).get('m_userId')
                         if idx is not None and user_id is not None:
                             pid = user_id + 1
                             if pid in stats_data:
                                 # Get hero name from players list (pid is 1-indexed, players is 0-indexed)
                                 player_idx = pid - 1
                                 if 0 <= player_idx < len(players):
                                     hero_n = players[player_idx]['hero']
                                     rich_id = get_talent_from_index(hero_n, idx, TALENTS_DB)

                                     # EXCLUDE GARBAGE
                                     if rich_id:
                                         garbage = ['Vehicle', 'Mount', 'Hearthstone', 'Spray', 'Voice', 'Banner', 'Announcer', 'Skin', 'Portrait', 'Dragon', 'Terror', 'Triglav']
                                         if any(g in rich_id for g in garbage):
                                             pass
                                             continue

                                     stats_data[pid]['talents'].append({
                                         "timestamp": round(event['_gameloop'] / 16.0, 1),
                                         "talent_name": rich_id if rich_id else f"Talent Index {idx}",
                                         "source": "game_event"
                                     })
                                     talent_event_count += 1
             except Exception as e:
                 pass 
                 
        
        
        # FINAL QM CHECK: Storm League ALWAYS has bans, Quick Match NEVER does
        if len(bans) == 0:
            # Silent rejection - Quick Match detected
            return {
                "status": "rejected",
                "message": "Quick Match detected (no bans). Only Storm League replays are processed."
            }

        # --- POST-PROCESSING: Calculate Team Level Timestamps & Merge Talents ---
        for pid, data in stats_data.items():
            if not isinstance(pid, int): continue
            
            # Merge Talents Logic:
            # We want Rich IDs (from InitData/Modern) + Timestamps (from Tracker)
            # 1. Group by potentially similar names or just keep the best ones.
            # Simple approach: Prefer "Modern" > "Init" > "Legacy"
            
            # Map of normalized_name -> {data}
            merged_talents = {}
            
            for t in data['talents']:
                name = t['talent_name']
                # Skip generic "Talent X" if we have other data? 
                # Actually, "Talent X" is useless for UI images.
                
                # If we have a duplicate name, keep the one with a Non-Zero timestamp (from tracker)
                if name not in merged_talents:
                    merged_talents[name] = t
                else:
                    # Update timestamp if we have a better one
                    if t['timestamp'] > 0 and merged_talents[name]['timestamp'] == 0:
                         merged_talents[name]['timestamp'] = t['timestamp']
            
            # Filter out "Talent X" if we have real names?
            # Or just keep everything unique.
            # Real IDs usually don't have spaces (CamelCase).
            
            final_talents = list(merged_talents.values())
            
            # Remove "Talent X" entries if we have enough "Real" entries?
            # Or just let the UI handle it.
            # Let's just sort them.
            
            final_talents.sort(key=lambda x: x['timestamp'])
            data['talents'] = final_talents
            
            
            talents = data['talents']
            
            # Map PID to Team. Fallback logic.
            # Usually PID 1 = Index 0.
            p_index = pid - 1 if pid > 0 else 0
            
            if 0 <= p_index < len(players):
                 p_team = players[p_index]['team']
                 
                 if len(talents) >= 4:
                    t_time = talents[3]['timestamp']
                    current = team_level_milestones[p_team][10]
                    if current is None or (t_time > 0 and t_time < (current or 9999)):
                         if t_time > 60: # Sanity check, level 10 not in 1 min
                            team_level_milestones[p_team][10] = t_time
                        
                 if len(talents) >= 7:
                    t_time = talents[6]['timestamp']
                    current = team_level_milestones[p_team][20]
                    if current is None or (t_time > 0 and t_time < (current or 9999)):
                         if t_time > 120:
                            team_level_milestones[p_team][20] = t_time

        # 6. Merge Stats into Players List & Identify User
        likely_user = None
        highest_score = -1
        mvp_name = None

        for i, p in enumerate(players):
            # Try PID Mapping: i+1 (Standard)
            pid = i + 1
            stats_src = stats_data.get(pid, {'stats': {}, 'talents': []})
            
            # Fallback if 1-10 empty but 0-9 populated (common in some replays)
            if not stats_src['stats'] and not stats_src['talents']:
                 if i in stats_data and (stats_data[i]['stats'] or stats_data[i]['talents']):
                      stats_src = stats_data[i] # Use 0-based slot
            
            p['stats'] = stats_src['stats']
            p['talents'] = stats_src['talents']
            p['death_timestamps'] = stats_src.get('death_timestamps', [])
            p['death_events'] = stats_src.get('death_events', [])  # Enhanced: includes killer info
            p['pos_timeline'] = stats_src.get('position_samples', [])
            p['banking_ledger'] = stats_src.get('banking_ledger', [])
            
            # Detect User: Check for environment names or fallback
            user_name = os.environ.get('PLAYER_NAME', 'Player').lower()
            if user_name in p['name'].lower() or 'discerning' in p['name'].lower() or 'cerebrate' in p['name'].lower():
                likely_user = p['name']
            
            # Calculate Score for MVP Fallback
            score = p['stats'].get('HeroDamage', 0) + p['stats'].get('Healing', 0) + p['stats'].get('ExperienceContribution', 0)*2
            if p['win'] and score > highest_score:
                highest_score = score
                mvp_name = p['name']

            # Normalize Stats
            s = p['stats']
            def norm_time(val):
                return round(val / 1000.0, 1) if val > 1000 else val

            p['kv_stats'] = {
                # Basic Info
                'time_played': time_played_str,
                'Level': s.get('Level', 0),
                
                # KDA
                'Takedowns': s.get('Takedowns', 0),
                'Kills': s.get('SoloKill', 0), 
                'Assists': s.get('Assists', 0),
                'Deaths': s.get('Deaths', 0),
                'HighestKillStreak': s.get('HighestKillStreak', 0),
                'Multikill': s.get('Multikill', 0),
                
                # Damage Stats
                'HeroDamage': s.get('HeroDamage', 0),
                'SiegeDamage': s.get('SiegeDamage', 0),
                'StructureDamage': s.get('StructureDamage', 0),
                'MinionDamage': s.get('MinionDamage', 0),
                'CreepDamage': s.get('CreepDamage', 0),
                'SummonDamage': s.get('SummonDamage', 0),
                'DamageTaken': s.get('DamageTaken', 0),
                'PhysicalDamage': s.get('PhysicalDamage', 0),
                'SpellDamage': s.get('SpellDamage', 0),
                
                # Healing
                'Healing': s.get('Healing', 0),
                'SelfHealing': s.get('SelfHealing', 0),
                'ProtectionGivenToAllies': s.get('ProtectionGivenToAllies', 0),
                'ClutchHealsPerformed': s.get('ClutchHealsPerformed', 0),
                
                # Teamfight Stats
                'TeamfightHeroDamage': s.get('TeamfightHeroDamage', 0),
                'TeamfightDamageTaken': s.get('TeamfightDamageTaken', 0),
                'TeamfightHealingDone': s.get('TeamfightHealingDone', 0),
                'TeamfightEscapesPerformed': s.get('TeamfightEscapesPerformed', 0),
                'ObjTime': max(s.get('TimeOnPoint', 0), s.get('TimeInTemple', 0), s.get('TimeShapeshifted', 0), s.get('TimeInDragonShire', 0)),
                
                # CC Stats (normalized to seconds)
                'TimeCCdEnemyHeroes': norm_time(s.get('TimeCCdEnemyHeroes', 0)),
                'TimeStunningEnemyHeroes': norm_time(s.get('TimeStunningEnemyHeroes', 0)),
                'TimeRootingEnemyHeroes': norm_time(s.get('TimeRootingEnemyHeroes', 0)),
                'TimeSilencingEnemyHeroes': norm_time(s.get('TimeSilencingEnemyHeroes', 0)),
                
                # Macro Stats
                'XP': s.get('ExperienceContribution', 0),
                'HeroXP': s.get('HeroXP', 0),
                'MinionXP': s.get('MinionXP', 0) or (s.get('ExperienceContribution', 0) - (s.get('HeroXP', 0) / 5.0) - (s.get('StructureXP', 0) / 5.0)),
                'MercCampCaptures': s.get('MercCampCaptures', 0),
                'RegenGlobes': s.get('RegenGlobes', 0),
                'MinionKills': s.get('MinionKills', 0),
                'TimeSpentDead': s.get('TimeSpentDead', 0),
                'OnFireTimeOnFire': s.get('OnFireTimeOnFire', 0),
                
                # Other
                'OutnumberedDeaths': s.get('OutnumberedDeaths', 0),
                'EscapesPerformed': s.get('EscapesPerformed', 0),
                'VengeancesPerformed': s.get('VengeancesPerformed', 0),
                'TownKills': s.get('TownKills', 0),
                
                # Map-Specific Objective Stats
                'BlackheartDoubloonsCollected': s.get('BlackheartDoubloonsCollected', 0),
                'BlackheartDoubloonsTurnedIn': s.get('BlackheartDoubloonsTurnedIn', 0),
                'GemsCollected': s.get('GemsCollected', 0),
                'GemsTurnedIn': s.get('GemsTurnedIn', 0),
                'SeedsCollected': s.get('SeedsCollected', 0),
                'AltarDamageDone': s.get('AltarDamageDone', 0),
                'ImmortalDamage': s.get('DamageDoneToImmortal', 0),
            }
        
        # Final User Determination
        user_name = likely_user if likely_user else mvp_name
        user_player = next((p for p in players if p['name'] == user_name), players[0])
        user_won = winning_team is not None and user_player['team'] == winning_team

        return {
            "status": "success",
            "match_id": match_id,
            "map": map_name,
            "game_length": int(game_duration_seconds),  # Add game length in seconds
            "timestamp_iso": timestamp_iso,  # ISO format timestamp for proper date display
            "result": "Win" if user_won else "Loss",
            "hero": user_player['hero'],
            "players": players,
            "user_name": user_name, # Return explicit user
            "parser_version": PARSER_VERSION,  # Track parser version for incremental re-parsing
            "advanced_stats": {
                "bans": bans,
                "level_milestones": team_level_milestones,
                "structure_destructions": stats_data.get('structure_destructions', []),
                "merc_captures": stats_data.get('merc_captures', []),
                "boss_captures": stats_data.get('boss_captures', []),
                "objective_events": stats_data.get('objective_events', [])
            }
        }

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"PARSER ERROR: {e}")
        print(tb)
        return {"status": "error", "message": str(e), "traceback": tb}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        parse_replay(sys.argv[1])
