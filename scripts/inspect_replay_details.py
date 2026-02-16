
import os
import mpyq
import sys
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
                        return (open(file_path, 'r'), file_path, (".py", "r", 1))
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
from heroprotocol.versions import latest

def inspect_replay(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    protocol = latest()
    details = protocol.decode_replay_details(archive.read_file('replay.details'))
    
    for i, p in enumerate(details['m_playerList']):
        print(f"Player {i}:")
        for key, value in p.items():
            if isinstance(value, bytes):
                print(f"  {key}: {value.decode('utf-8')}")
            else:
                print(f"  {key}: {value}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        replay_path = sys.argv[1]
        inspect_replay(replay_path)
    else:
        REPLAYS_DIR = os.path.expanduser("~/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer")
        import glob
        replays = sorted(glob.glob(os.path.join(REPLAYS_DIR, "*.StormReplay")), reverse=True)
        if replays:
            inspect_replay(replays[0])
        else:
            print("No replays found.")
