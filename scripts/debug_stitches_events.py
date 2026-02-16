import mpyq
import sys
import os

sys.path.append(os.getcwd())

from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol
from api.services.replay_parser.header import get_match_id

def main():
    target_id = "d5ff347587e7844c"
    root_dir = os.path.expanduser("~/Library/Application Support/Blizzard/Heroes of the Storm")
    
    print(f"Searching for {target_id}...")
    replay_path = None
    for r, d, f in os.walk(root_dir):
        for file in f:
            if file.endswith(".StormReplay"):
                p = os.path.join(r, file)
                try:
                    if get_match_id(p) == target_id:
                        replay_path = p
                        break
                except: pass
        if replay_path: break
        
    print(f"Analyzing {replay_path}")
    archive = mpyq.MPQArchive(replay_path)
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    
    # Cast was at 937
    start = 937
    end = 980
    
    print(f"\n--- ALL TRACKER EVENTS {start}-{end} ---")
    for e in tracker_events:
        gl = e['_gameloop']
        if start <= gl <= end:
            evt_short = e['_event'].replace('NNet.Replay.Tracker.', '')
            print(f"[{gl}] {evt_short}")
            
            if 'SUnitBornEvent' in e['_event']:
                print(f"    Type: {e.get('m_unitTypeName', b'').decode('utf-8')}")
            
            if 'SStatGameEvent' in e['_event']:
                 # Check what stats are logged
                 name = e.get('m_eventName', b'').decode('utf-8')
                 print(f"    Name: {name}")

if __name__ == "__main__":
    main()
