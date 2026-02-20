import os
import sys
import types
import importlib.util
import importlib.machinery
import mpyq

# Shim for 'imp' module (removed in Python 3.12)
try:
    import imp
except ImportError:
    imp = types.ModuleType('imp')
    sys.modules['imp'] = imp
    def find_module(name, path=None):
        if path:
            for p in path:
                target = os.path.join(p, name + ".py")
                if os.path.exists(target):
                    return open(target, 'r'), target, ('.py', 'r', 1)
        raise ImportError(f"No module named {name}")
    def load_module(name, file, filename, description):
        loader = importlib.machinery.SourceFileLoader(name, filename)
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        return module
    imp.find_module = find_module
    imp.load_module = load_module
    imp.load_source = load_module

from heroprotocol.versions import build, latest

def debug_replay(path):
    archive = mpyq.MPQArchive(path)
    header = latest().decode_replay_header(archive.header['user_data_header']['content'])
    protocol = build(header['m_version']['m_baseBuild'])
    
    # Check Game Events for anything suspicious
    game_events = protocol.decode_replay_game_events(archive.read_file('replay.game.events'))
    
    print("--- Searching Game Events for 'Leave', 'Quit', 'DC', 'Player' ---")
    for event in game_events:
        ename = event['_event']
        if any(kw in ename for kw in ['Leave', 'Quit', 'Disconnect', 'Control']):
            print(f"[{round(event['_gameloop']/16.0, 1)}s] {ename}: {event}")

    # Check Tracker Events
    tracker_events = protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events'))
    print("\n--- Searching Tracker Events ---")
    for event in tracker_events:
        ename = event['_event']
        if 'Leave' in ename or 'Disconnect' in ename:
            print(f"[{round(event['_gameloop']/16.0, 1)}s] {ename}: {event}")

if __name__ == "__main__":
    debug_replay(sys.argv[1])
