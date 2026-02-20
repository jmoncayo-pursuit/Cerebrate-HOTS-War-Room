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

from heroprotocol.versions import latest
import mpyq

replay_path = '/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-21 00.52.33 Dragon Shire.StormReplay'

archive = mpyq.MPQArchive(replay_path)
tracker_events = latest().decode_replay_tracker_events(archive.read_file('replay.tracker.events'))
contents = archive.read_file('replay.details')
details = latest().decode_replay_details(contents)

# map PIDs
players = {}
for i, p in enumerate(details['m_playerList']):
    name = p['m_name'].decode('utf-8')
    pid = i + 1 
    hero = p['m_hero'].decode('utf-8')
    players[pid] = {'name': name, 'hero': hero}

print("Scanning deaths for Discerning...")

unit_tags = {}

for e in tracker_events:
    event = e['_event']
    gameloop = e['_gameloop']
    
    if event == 'NNet.Replay.Tracker.SUnitBornEvent':
        tag = e['m_unitTagIndex']
        u_type = e['m_unitTypeName'].decode('utf-8')
        c_pid = e.get('m_controlPlayerId')
        unit_tags[tag] = {'type': u_type, 'c_pid': c_pid}
        
    elif event == 'NNet.Replay.Tracker.SUnitDiedEvent':
        victim_tag = e['m_unitTagIndex']
        if victim_tag in unit_tags:
            victim = unit_tags[victim_tag]
            c_pid = victim.get('c_pid')
            
            # Check if it is Discerning (we know Discerning is usually PID 5 based on prev turns, let's look it up dynamically)
            # Actually just look for name 'Discerning' in players
            if c_pid and c_pid in players and players[c_pid]['name'] == 'Discerning':
                timestamp = f"{int(gameloop / 16 / 60):02d}:{int((gameloop / 16) % 60):02d}"
                print(f"[{timestamp}] Unit Died: {victim['type']} (Player: Discerning)")
