import sys
import types
import importlib.util
import importlib.machinery
import os

# --- FULL IMP SHIM START ---
if 'imp' not in sys.modules:
    imp = types.ModuleType('imp')
    sys.modules['imp'] = imp

    def find_module(name, path=None):
        if path is None:
            path = sys.path
        spec = importlib.machinery.PathFinder.find_spec(name, path)
        if spec is None:
            raise ImportError(f"No module named {name}")
        return None, spec.origin, ('', '', 0)

    def load_module(name, file, pathname, description):
        spec = importlib.util.spec_from_file_location(name, pathname)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module

    imp.find_module = find_module
    imp.load_module = load_module
    imp.PY_SOURCE = 1
    imp.PKG_DIRECTORY = 5
# --- FULL IMP SHIM END ---

from heroprotocol.versions import latest
import mpyq

replay_path = '/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-01-21 00.52.33 Dragon Shire.StormReplay'

archive = mpyq.MPQArchive(replay_path)
tracker_events = latest().decode_replay_tracker_events(archive.read_file('replay.tracker.events'))

# Get User PID (known from prev steps: Discerning)
# We need to find the specific PID for score tracking.
# In ScoreResultEvent, stats are usually a list of lists.
# We need to know which index corresponds to which player.

print("Scanning Score Results for Kill Jumps...")
last_kills = 0
current_kills = 0

for e in tracker_events:
    event = e['_event']
    gameloop = e['_gameloop']
    timestamp = f"{int(gameloop / 16 / 60):02d}:{int((gameloop / 16) % 60):02d}"
    
    if event == 'NNet.Replay.Tracker.SScoreResultEvent':
        # Structure is usually m_instanceList containing stat names/values
        # e['m_instanceList'] -> list of dicts
        # Each dict has m_values -> list of lists?
        
        # Let's dump the structure of the first one to be sure
        # But generally: m_instanceList [{'m_name': 'SoloKill', 'm_values': [[PID1_Val], [PID2_Val]...]}]
        
        for entry in e['m_instanceList']:
            if entry['m_name'].decode('utf-8') == 'SoloKill':
                # Iterate through values to find Player 5 (Discerning, usually index 4 if 0-based or 5?)
                # Player indices in m_values match the player list order (0-9 or 1-10)
                # Discerning was Player 5 in previous script (Team 0).
                # Score indexes are usually 0-based. So Player 5 is index 4.
                
                # Check all players to be safe
                # Discerning PID was 5 so index 4
                
                vals = entry['m_values']
                # vals is list of lists, e.g. [[0], [0], [0], [1], [5], ...]
                
                # Assuming index 4 is Discerning
                if len(vals) > 4:
                    my_kills = vals[4][0]['m_value']
                    
                    if my_kills > last_kills:
                        print(f"[{timestamp}] Kill Count Bump: {last_kills} -> {my_kills}")
                        last_kills = my_kills
