
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

def debug_abil_timeline(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    
    links = {
        26: 'Mount/Z',
        111: 'Ability_?',
        185: 'Ability_?',
        574: 'Ability_?',
        575: 'Ability_?',
        568: 'Pills/Active?'
    }
    
    print("Timeline of Casts for Stitches (User 0):")
    for event in game_events:
        if event.get('_userid', {}).get('m_userId') == 0:
            if event['_event'] == 'NNet.Game.SCmdEvent':
                abil = event.get('m_abil')
                if abil:
                    link = abil.get('m_abilLink')
                    ts = round(event['_gameloop'] / 16.0, 1)
                    if link in [574, 575, 111, 185]:
                         print(f"  [{ts}s] Link {link}")

if __name__ == "__main__":
    replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-19 21.57.59 Garden of Terror.StormReplay"
    debug_abil_timeline(replay_path)
