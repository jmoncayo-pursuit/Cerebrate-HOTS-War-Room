
import os
import sys
import types
import importlib.util
import importlib.machinery
import mpyq

# Full Shim for 'imp' module (removed in Python 3.12)
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
        imp.PKG_DIRECTORY = 5
        return imp

setup_imp_shim()
from heroprotocol.versions import latest as protocol

def search_init_data(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    init_data = archive.read_file('replay.initData')
    # Just search for strings in raw bytes
    if b'Hook' in init_data:
        print("FOUND 'Hook' in initData")
    if b'Stitches' in init_data:
        print("FOUND 'Stitches' in initData")
        
    # Search in game events for ability links
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    for event in game_events:
        if event.get('_userid', {}).get('m_userId') == 0:
            if event['_event'] == 'NNet.Game.SCmdEvent':
                # Sometimes the m_data has the ability name if it's a specific type? No.
                pass

if __name__ == "__main__":
    replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-19 21.57.59 Garden of Terror.StormReplay"
    search_init_data(replay_path)
