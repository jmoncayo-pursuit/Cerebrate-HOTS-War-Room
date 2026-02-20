import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def dump_azmo_events(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    
    # Identify Azmodan PID
    details = protocol().decode_replay_details(archive.read_file('replay.details'))
    azmo_pid = None
    for i, p in enumerate(details['m_playerList']):
        if p.get('m_hero', b'').decode('utf-8') == 'Azmodan':
            azmo_pid = i + 1
            break
            
    if not azmo_pid:
        print("Azmodan not found")
        return

    print(f"Azmodan PID: {azmo_pid}")
    
    for e in tracker_events:
        if e['_event'] == 'NNet.Replay.Tracker.SScoreResultEvent':
            for instance in e.get('m_instanceList', []):
                name = instance.get('m_name', b'').decode('utf-8')
                if 'annihilation' in name.lower() or 'azmo' in name.lower() or 'stack' in name.lower():
                    print(f"Matched: {name}")
            break















if __name__ == "__main__":
    replay_path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-14 00.37.31 Sky Temple.StormReplay"
    if os.path.exists(replay_path):
        dump_azmo_events(replay_path)
    else:
        print("Replay not found")
