import mpyq
import sys
import os
sys.path.append(os.getcwd())
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def debug_deaths():
    replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2025-12-14 20.34.39 Tomb of the Spider Queen.StormReplay"
    
    archive = mpyq.MPQArchive(replay_path)
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    
    print("--- PLAYER DEATH EVENTS ---")
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SStatGameEvent' and event.get('m_eventName', b'').decode('utf-8') == 'PlayerDeath':
            print("\nDeath Event:")
            # Flatten data
            data = {}
            if 'm_intData' in event:
                for d in event['m_intData']:
                    k = d['m_key'].decode('utf-8')
                    v = d['m_value']
                    data[k] = v
            if 'm_fixedData' in event:
                for d in event['m_fixedData']:
                    k = d['m_key'].decode('utf-8')
                    v = d['m_value']
                    data[k] = v
            
            print(json.dumps(data, indent=2))

import json
if __name__ == "__main__":
    debug_deaths()
