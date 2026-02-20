import os
import sys
import mpyq

# Setup environment
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest

def discover_event_signatures():
    replays_dir = '/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts'
    count = 0
    all_tracker_event_names = set()
    all_game_event_names = set()
    stat_event_names = set()
    
    for root, dirs, files in os.walk(replays_dir):
        for f in files:
            if f.endswith('.StormReplay'):
                path = os.path.join(root, f)
                try:
                    archive = mpyq.MPQArchive(path)
                    protocol = latest()
                    
                    # Tracker Events
                    tracker_events = protocol.decode_replay_tracker_events(archive.read_file('replay.tracker.events'))
                    for event in tracker_events:
                        all_tracker_event_names.add(event.get('_event'))
                        if event.get('_event') == 'SStatGameEvent':
                            ename = event.get('m_eventName', b'').decode('utf-8')
                            stat_event_names.add(ename)
                    
                    # Game Events
                    game_events = protocol.decode_replay_game_events(archive.read_file('replay.game.events'))
                    for event in game_events:
                        all_game_event_names.add(event.get('_event'))
                        
                except Exception as e:
                    pass
                
                count += 1
                if count >= 10: # Just check 10 to see common ones
                    break
        if count >= 10:
            break
            
    print("TRACKER EVENTS:")
    for name in sorted(list(all_tracker_event_names)):
        print(f"  - {name}")
        
    print("\nSTAT GAME EVENTS (m_eventName):")
    for name in sorted(list(stat_event_names)):
        print(f"  - {name}")
        
    print("\nGAME EVENTS:")
    for name in sorted(list(all_game_event_names)):
        print(f"  - {name}")

if __name__ == "__main__":
    discover_event_signatures()
