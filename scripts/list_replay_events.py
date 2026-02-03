import os
import sys
import types
import importlib.util
import importlib.machinery
import mpyq

# Shim for 'imp' module (removed in Python 3.12)
# heroprotocol relies on it.
try:
    import imp
except ImportError:
    # Create a mock imp module
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
    imp.load_source = load_module # Alias just in case

from heroprotocol.versions import build, latest
import json

def list_events(path):
    archive = mpyq.MPQArchive(path)
    
    # Get protocol
    header_content = archive.header['user_data_header']['content']
    header = latest().decode_replay_header(header_content)
    base_build = header['m_version']['m_baseBuild']
    protocol = build(base_build)
    
    # Read game events
    contents = archive.read_file('replay.game.events')
    game_events = protocol.decode_replay_game_events(contents)
    
    event_names = set()
    for event in game_events:
        event_names.add(event['_event'])
        
    print("Unique Game Events:")
    for name in sorted(list(event_names)):
        print(f"  {name}")
        
    # Read tracker events
    contents = archive.read_file('replay.tracker.events')
    tracker_events = protocol.decode_replay_tracker_events(contents)
    
    tracker_names = set()
    for event in tracker_events:
        tracker_names.add(event['_event'])
        
    print("\nUnique Tracker Events:")
    for name in sorted(list(tracker_names)):
        print(f"  {name}")

if __name__ == "__main__":
    list_events(sys.argv[1])
