
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

def debug_enemy_deaths(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    
    # We need to find hero names for PIDs
    hero_names = {}
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent':
            u_type = event.get('m_unitTypeName', b'').decode('utf-8')
            if u_type.startswith('Hero'):
                hero_names[event.get('m_controlPlayerId')] = u_type

    print("Enemy Deaths (PIDs 6-10):")
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SStatGameEvent':
            ename = event.get('m_eventName', b'').decode('utf-8')
            if ename == 'PlayerDeath':
                data = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or []) + (event.get('m_fixedData') or [])}
                pid = data.get('PlayerID')
                if pid and pid >= 6:
                    ts = round(event['_gameloop'] / 16.0, 1)
                    hero = hero_names.get(pid, f"PID {pid}")
                    killer = data.get('KillingPlayer')
                    print(f"  [{ts}s] {hero} (PID {pid}) killed by PID {killer} at ({data.get('PositionX')}, {data.get('PositionY')})")

if __name__ == "__main__":
    replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-19 21.57.59 Garden of Terror.StormReplay"
    debug_enemy_deaths(replay_path)
