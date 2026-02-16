import sys
import types
import importlib.util
import importlib.machinery
import os

# --- FULL IMP SHIM START ---
if 'imp' not in sys.modules:
    imp = types.ModuleType('imp')
    sys.modules['imp'] = imp

    def find_module(name, path=None):
        if path is None:
            path = sys.path
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is None:
            raise ImportError(f"No module named {name}")
        return None, spec.origin, ('', '', 0)

    def load_module(name, file, pathname, description):
        spec = importlib.util.spec_from_file_location(name, pathname)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    imp.find_module = find_module
    imp.load_module = load_module
    imp.PY_SOURCE = 1
    imp.PKG_DIRECTORY = 5
# --- FULL IMP SHIM END ---

# Now import heroprotocol
from heroprotocol.versions import latest
import mpyq

replay_path = '/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-21 00.52.33 Dragon Shire.StormReplay'

try:
    print(f"Opening archive: {replay_path}")
    archive = mpyq.MPQArchive(replay_path)

    print("Reading details...")
    contents = archive.read_file('replay.details')
    details = latest().decode_replay_details(contents)
    
    players = {}
    user_pid = None
    
    print("\n--- PLAYERS ---")
    for i, p in enumerate(details['m_playerList']):
        name = p['m_name'].decode('utf-8')
        pid = i + 1 
        team = p['m_teamId']
        hero = p['m_hero'].decode('utf-8')
        players[pid] = {'name': name, 'team': team, 'hero': hero}
        print(f"Player {pid}: {name} ({hero}) - Team {team}")
        
        if name == 'Discerning':
            user_pid = pid
            
    print(f"\nUser 'Discerning' is Player ID: {user_pid}")
    
    print("Reading tracker events...")
    tracker_events = latest().decode_replay_tracker_events(archive.read_file('replay.tracker.events'))
    
    unit_tags = {}
    
    print(f"\n--- KILL LOG SCAN ---")
    
    for e in tracker_events:
        event = e['_event']
        gameloop = e['_gameloop']
        
        if event == 'NNet.Replay.Tracker.SUnitBornEvent':
            tag = e['m_unitTagIndex']
            u_type = e['m_unitTypeName'].decode('utf-8')
            c_pid = e.get('m_controlPlayerId')
            u_pid = e.get('m_upkeepPlayerId')
            unit_tags[tag] = {'type': u_type, 'c_pid': c_pid, 'u_pid': u_pid}
            
        elif event == 'NNet.Replay.Tracker.SUnitDiedEvent':
            victim_tag = e['m_unitTagIndex']
            if victim_tag in unit_tags:
                victim = unit_tags[victim_tag]
                
                # Check if it's a HERO death (has control PID)
                v_pid = victim.get('c_pid')
                if v_pid and v_pid in players:
                    
                    # Log EVERY hero death to see if we missed anything
                    timestamp = f"{int(gameloop / 16 / 60):02d}:{int((gameloop / 16) % 60):02d}"
                    victim_name = players[v_pid]['name']
                    victim_hero = players[v_pid]['hero']
                    
                    killer_pid = e.get('m_killerPlayerId')
                    killer_tag = e.get('m_killerUnitTagIndex')
                    
                    killer_desc = "Unknown"
                    k_pid = None
                    
                    if killer_pid:
                        k_pid = killer_pid
                        k_name = players.get(killer_pid, {}).get('name', f"P{killer_pid}")
                        k_hero = players.get(killer_pid, {}).get('hero', '?')
                        killer_desc = f"{k_hero} ({k_name})"
                    elif killer_tag and killer_tag in unit_tags:
                        k_unit = unit_tags[killer_tag]
                        k_u_type = k_unit['type']
                        k_pid = k_unit.get('c_pid') or k_unit.get('u_pid')
                        
                        owner_name = "Neutral"
                        if k_pid and k_pid in players:
                            owner_name = players[k_pid]['name']
                        
                        killer_desc = f"Unit: {k_u_type} [Owner: {owner_name}]"
                    
                    # Is this a kill for Discerning?
                    is_my_kill = (k_pid == user_pid)
                    prefix = ">>> [KILL CONFIRMED]" if is_my_kill else "    [Death Log]"
                    
                    print(f"{prefix} {timestamp}: {victim_hero} ({victim_name}) killed by {killer_desc}")

except Exception as e:
    import traceback
    traceback.print_exc()
