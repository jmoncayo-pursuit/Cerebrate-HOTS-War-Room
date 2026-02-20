import sys; import types; import importlib.util; import importlib.machinery; sys.modules['imp'] = types.ModuleType('imp'); from heroprotocol.versions import latest
import sys
import mpyq
from heroprotocol.versions import latest

# Setup imp shim (inline for standalone script)
import importlib.util
import importlib.machinery

def setup_imp_shim():
    imp = types.ModuleType('imp')
    sys.modules['imp'] = imp
    return imp

if 'imp' not in sys.modules:
    import types
    sys.modules['imp'] = setup_imp_shim()

# Replay Path
replay_path = '/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-21 00.52.33 Dragon Shire.StormReplay'

try:
    archive = mpyq.MPQArchive(replay_path)
    protocol = latest()
    
    # 1. Decode Details to get Player Map
    contents = archive.read_file('replay.details')
    details = protocol.decode_replay_details(contents)
    
    players = {}
    user_pid = None
    
    print("\n--- PLAYERS ---")
    for i, p in enumerate(details['m_playerList']):
        name = p['m_name'].decode('utf-8')
        pid = i + 1 # 1-based index for tracker events usually matches this
        toon_id = p['m_toon']['m_id']
        team = p['m_teamId']
        players[pid] = {'name': name, 'team': team, 'toon_id': toon_id, 'hero': p['m_hero'].decode('utf-8')}
        print(f"Player {pid}: {name} ({players[pid]['hero']}) - Team {team}")
        
        if name == 'Discerning':
            user_pid = pid
            
    print(f"\nUser 'Discerning' is Player ID: {user_pid}")
    
    # 2. Decode Tracker Events
    tracker_events = protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events'))
    
    unit_tags = {} # tag -> {type, control_pid, upkeep_pid}
    
    print(f"\nScanning for Hero Deaths...")
    
    killed_count = 0
    
    for e in tracker_events:
        event = e['_event']
        
        if event == 'NNet.Replay.Tracker.SUnitBornEvent':
            tag = e['m_unitTagIndex']
            u_type = e['m_unitTypeName'].decode('utf-8')
            c_pid = e.get('m_controlPlayerId')
            u_pid = e.get('m_upkeepPlayerId')
            
            unit_tags[tag] = {
                'type': u_type,
                'control_pid': c_pid,
                'upkeep_pid': u_pid
            }
            
        elif event == 'NNet.Replay.Tracker.SUnitDiedEvent':
            victim_tag = e['m_unitTagIndex']
            
            if victim_tag in unit_tags:
                victim = unit_tags[victim_tag]
                
                # Check if victim is a hero (usually has control_pid)
                # Filter for only Hero units (simplified check, might need specific names)
                if victim['control_pid']: 
                    v_pid = victim['control_pid']
                    
                    # Only map deaths of known players
                    victim_name = players.get(v_pid, {}).get('name', 'Unknown')
                    victim_hero = players.get(v_pid, {}).get('hero', 'Unknown')
                    
                    # Get Killer Info
                    killer_pid = e.get('m_killerPlayerId')
                    killer_tag = e.get('m_killerUnitTagIndex')
                    
                    killer_desc = "Minion/Structure/Unknown"
                    killer_real_pid = None
                    
                    if killer_pid:
                        killer_real_pid = killer_pid
                        k_name = players.get(killer_pid, {}).get('name', f"Player {killer_pid}")
                        k_hero = players.get(killer_pid, {}).get('hero', '?')
                        killer_desc = f"{k_name} ({k_hero})"
                        
                    elif killer_tag and killer_tag in unit_tags:
                        k_unit = unit_tags[killer_tag]
                        k_type = k_unit['type']
                        k_control = k_unit.get('control_pid')
                        k_upkeep = k_unit.get('upkeep_pid')
                        
                        killer_real_pid = k_control or k_upkeep
                        
                        owner_name = "Neutral"
                        if killer_real_pid:
                            owner_name = players.get(killer_real_pid, {}).get('name', f"Player {killer_real_pid}")
                            
                        killer_desc = f"Unit: {k_type} (Owner: {owner_name})"

                    # Print Event
                    gameloop = e['_gameloop']
                    timestamp = f"{int(gameloop / 16 / 60):02d}:{int((gameloop / 16) % 60):02d}"
                    
                    # Highlight if User is the Killer
                    is_user_kill = (killer_real_pid == user_pid)
                    prefix = ">>> USER KILL! " if is_user_kill else "    "
                    
                    print(f"{prefix}[{timestamp}] {victim_hero} ({victim_name}) killed by {killer_desc}")
                    
                    if is_user_kill:
                        killed_count += 1

    print(f"\nTotal Detected Kills by User ({user_pid}): {killed_count}")

except Exception as e:
    print(f"Error: {e}")
