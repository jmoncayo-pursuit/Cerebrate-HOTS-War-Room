import sys
import os
import types
import importlib.util
import importlib.machinery

def setup_imp_shim():
    try:
        import imp
        return imp
    except ImportError:
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
        return imp

setup_imp_shim()
import mpyq
from heroprotocol.versions import latest
import json

def debug_replay(path):
    archive = mpyq.MPQArchive(path)
    protocol = latest()
    details = protocol.decode_replay_details(archive.read_file('replay.details'))
    
    player_data = []
    for p in details['m_playerList']:
        player_data.append({
            'name': p['m_name'].decode('utf-8'),
            'hero': p['m_hero'].decode('utf-8'),
            'team': p['m_teamId'],
            'keys': list(p.keys())
        })
    
    print(json.dumps(player_data, indent=2))

debug_replay('/Users/jmoncayopursuit.org/Desktop/Cerebrate-HOTS-War-Room/replays/2026-01-20 03.18.23 Dragon Shire.StormReplay')
