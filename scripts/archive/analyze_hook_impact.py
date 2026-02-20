
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

def analyze_hook_stats(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    
    # 1. Map PIDs to Hero Names
    hero_names = {}
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent':
            u_type = event.get('m_unitTypeName', b'').decode('utf-8')
            if u_type.startswith('Hero'):
                hero_names[event.get('m_controlPlayerId')] = u_type

    # 2. Extract Casts
    casts = []
    hooks = []
    devours = []
    for event in game_events:
        if event.get('_userid', {}).get('m_userId') == 0:
            if event['_event'] == 'NNet.Game.SCmdEvent':
                abil = event.get('m_abil')
                if abil:
                    link = abil.get('m_abilLink')
                    ts = round(event['_gameloop'] / 16.0, 1)
                    if link == 575: hooks.append(ts)
                    elif link == 185: devours.append(ts)

    # 3. Extract Deaths
    deaths = []
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SStatGameEvent':
            if event.get('m_eventName', b'').decode('utf-8') == 'PlayerDeath':
                data = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or []) + (event.get('m_fixedData') or [])}
                pid = data.get('PlayerID')
                if pid and pid >= 6:
                    deaths.append({
                        'ts': round(event['_gameloop'] / 16.0, 1),
                        'hero': hero_names.get(pid, f"PID {pid}"),
                        'pid': pid
                    })

    # 4. Correlation
    landed_hooks = []
    for h_ts in hooks:
        impact = []
        
        # Check for Devour (E) within 2s of Hook
        for e_ts in devours:
            if 0 < (e_ts - h_ts) <= 2.2:
                impact.append("Hooked & Devoured (confirmed hit)")
                break
        
        # Check for Death within 5s
        for d in deaths:
            if 0 < (d['ts'] - h_ts) <= 5.0:
                impact.append(f"LETHAL: {d['hero']} killed {round(d['ts'] - h_ts, 1)}s later")
                break
        
        if impact:
            landed_hooks.append({'ts': h_ts, 'result': impact})

    print(f"Stitches Hook Performance (Match 84cbd66dcdcda2f8):")
    print(f"Total Hooks Thrown: {len(hooks)}")
    print(f"Hooks Landed (Heuristic Hits): {len(landed_hooks)}")
    print(f"Landing Accuracy: {round((len(landed_hooks)/len(hooks))*100, 1)}%")
    
    print(f"\nBreakdown of Landed Hooks:")
    for h in landed_hooks:
        print(f"  [{h['ts']}s]: {' | '.join(h['result'])}")

if __name__ == "__main__":
    replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-19 21.57.59 Garden of Terror.StormReplay"
    analyze_hook_stats(replay_path)
