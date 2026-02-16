
import os
import sys
import types
import importlib.util
import importlib.machinery
import mpyq

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
        imp.PY_SOURCE = 1
        return imp

setup_imp_shim()
from heroprotocol.versions import latest as protocol

def debug_tags(path):
    archive = mpyq.MPQArchive(path)
    contents = archive.read_file('replay.tracker.events')
    events = protocol().decode_replay_tracker_events(contents)
    
    tags_by_pid = {}
    
    for event in events:
        etype = event['_event']
        if '.' in etype: etype = etype.split('.')[-1]
        
        if etype == 'SUnitBornEvent':
            tag = event.get('m_unitTagIndex')
            u_type = event.get('m_unitTypeName', b'').decode('utf-8')
            u_pid = event.get('m_controlPlayerId', event.get('m_upkeepPlayerId'))
            if u_pid and 1 <= u_pid <= 10:
                if u_pid not in tags_by_pid: tags_by_pid[u_pid] = []
                tags_by_pid[u_pid].append({'tag': tag, 'type': u_type})
                
    for pid, tags in tags_by_pid.items():
        print(f"PID {pid}: {tags}")

if __name__ == "__main__":
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-12 18.08.01 Hanamura Temple.StormReplay"
    debug_tags(path)
