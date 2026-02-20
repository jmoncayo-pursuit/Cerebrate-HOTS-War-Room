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
import json; import sqlite3; from api.services.database import DatabaseManager; db = DatabaseManager(); match_id = '2ba9403cd33f83ff'; with open('raw_analysis.txt', 'r') as f: analysis_json = json.load(f); db.conn.execute('UPDATE matches SET analysis = ? WHERE id = ?', (json.dumps(analysis_json), match_id)); db.conn.commit(); print(f'Successfully force-updated analysis for {match_id} with Blood Monk version.')
