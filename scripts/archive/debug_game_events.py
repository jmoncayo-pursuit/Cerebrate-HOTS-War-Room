
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

def debug_game_events(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    
    stitches_uid = 0 # Based on PID 1
    
    print(f"Scanning game events for Stitches (User {stitches_uid})...")
    
    for event in game_events:
        if event.get('_userid', {}).get('m_userId') == stitches_uid:
            etype = event['_event']
            if etype == 'NNet.Game.SCmdEvent':
                # CMD event usually has abilLink
                abil = event.get('m_abil')
                if abil:
                    link = abil.get('m_abilLink')
                    # Stitches Hook Link ID? I don't know it, so I'll print them all initially
                    # but filtered to common ones or just range
                    ts = round(event['_gameloop'] / 16.0, 1)
                    # print(f"[{ts}s] CMD: {link} {event.get('m_data')}")
                    pass

    # We need to find which abilLink is Hook.
    # Usually it's in the metadata? No.
    # Let's check SStatGameEvent 'TalentChosen' to see if we can find ability names.
    
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SStatGameEvent':
            ename = event.get('m_eventName', b'').decode('utf-8')
            if ename == 'TalentChosen':
                str_map = {d.get('m_key', b'').decode('utf-8'): d.get('m_value', b'').decode('utf-8') for d in (event.get('m_stringData') or [])}
                if str_map.get('Hero') == 'HeroStitches':
                    print(f"Talent: {str_map}")

if __name__ == "__main__":
    replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-19 21.57.59 Garden of Terror.StormReplay"
    debug_game_events(replay_path)
