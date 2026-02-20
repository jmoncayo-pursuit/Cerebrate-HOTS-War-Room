import sys
import os
import types
import importlib.util
import importlib.machinery
import unicodedata

# Shim for 'imp' module (removed in Python 3.12)
def setup_imp_shim():
    try:
        import imp
        return imp
    except ImportError:
        # Create a mock imp module
        imp = types.ModuleType('imp')
        sys.modules['imp'] = imp
        
        def find_module(name, path=None):
            if path:
                for directory in path:
                    file_path = os.path.join(directory, name + ".py")
                    if os.path.exists(file_path):
                        fp = open(file_path, 'r')
                        return (fp, file_path, (".py", "r", 1))
            raise ImportError(f"No module named {name}")

        def load_module(name, file, pathname, description):
            if file: file.close()
            loader = importlib.machinery.SourceFileLoader(name, pathname)
            spec = importlib.util.spec_from_loader(loader.name, loader)
            module = importlib.util.module_from_spec(spec)
            loader.exec_module(module)
            return module
            
        imp.find_module = find_module
        imp.load_module = load_module
        imp.load_source = load_module
        imp.PY_SOURCE = 1
        imp.PKG_DIRECTORY = 5
        return imp

def clean_text(s):
    if not s: return ""
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    return s.lower().replace('.','').replace(' ','').replace("'", "")

def get_hero_display_name(internal_name):
    """Maps Blizzard internal engine names to playable display names."""
    m = {
        "tinker": "Gazlowe",
        "medic": "Lt. Morales",
        "witchdoctor": "Nazeebo",
        "crusader": "Johanna",
        "barbarian": "Sonya", 
        "demonhunter": "Valla",
        "monk": "Kharazim",
        "traitorhero": "Varian",
        "amazon": "Cassia",
        "wizard": "Li-Ming",
        "d3wizard": "Li-Ming",
        "butcher": "The Butcher",
        "faeriedragon": "Brightwing",
        "necromancer": "Xul",
        "wanderer": "Chen",
        "dryad": "Lunara",
        "siegebreaker": "Azmodan",
        "firebat": "Blaze",
        "cryptlord": "Anub'arak",
        "lichlord": "Kel'Thuzad",
        "nexuslord": "Deathwing",
        "nexushunter": "Qhira",
        "lostvikings": "The Lost Vikings",
        "sgthammer": "Sgt. Hammer",
        "l90etc": "E.T.C."
    }
    clean = clean_text(internal_name)
    return m.get(clean, internal_name)
import json; sys.modules['imp'] = setup_imp_shim(); import types; import mpyq; from heroprotocol.versions import latest; from api.services.replay_parser.tracker import process_tracker_events; 

archive = mpyq.MPQArchive('/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-21 00.52.33 Dragon Shire.StormReplay')
protocol = latest()
contents = archive.read_file('replay.details')
details = protocol.decode_replay_details(contents)

# Get Player IDs
players = {}
for i, p in enumerate(details['m_playerList']):
    name = p['m_name'].decode('utf-8')
    pid = i + 1
    players[pid] = {'name': name, 'team': p['m_teamId']}
    print(f"Player {pid}: {name} (Team {p['m_teamId']})")

print('-' * 20)

user_pid = next(pid for pid, p in players.items() if p['name'] == 'Discerning')
print(f"User PID: {user_pid}")

tracker_events = protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events'))

unit_tags = {}
hero_units = {}

print(f"
Scanning for Hero Deaths (Victims on opposite team of User)...")

for e in tracker_events:
    if e['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent':
        tag = e['m_unitTagIndex']
        pid = e.get('m_controlPlayerId')
        # Map unit tags
        if tag not in unit_tags:
             unit_tags[tag] = {'type': e['m_unitTypeName'].decode('utf-8'), 'pid': pid}
        
    elif e['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent':
        victim_tag = e['m_unitTagIndex']
        if victim_tag in unit_tags:
            victim = unit_tags[victim_tag]
            # Check if victim is a hero
            if victim.get('pid'):
                v_pid = victim['pid']
                # If victim is enemy (User is Team 0? Need to check team logic from DB dump earlier.
                # Earlier dump said Discerning Team 0. Enemy is Team 1.
                # Details m_teamId might be 0 and 1.
                # Let's just print ALL hero deaths and their killer.
                
                killer_pid = e.get('m_killerPlayerId')
                killer_tag = e.get('m_killerUnitTagIndex')
                
                k_info = "Unknown"
                if killer_pid:
                    k_info = f"Player {killer_pid}"
                elif killer_tag and killer_tag in unit_tags:
                    k_unit = unit_tags[killer_tag]
                    k_info = f"Unit {k_unit['type']} (Owner: {k_unit.get('pid')})"
                
                print(f"CreateEvent Gameloop {e['_gameloop']}: Hero {victim['type']} (P{v_pid}) killed by {k_info}")

