
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def debug_stitches_events(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    
    print("--- SScoreResultEvent Keys ---")
    score_keys = set()
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SScoreResultEvent':
            for instance in event.get('m_instanceList', []):
                score_keys.add(instance.get('m_name', b'').decode('utf-8'))
    
    for k in sorted(list(score_keys)):
        print(f"  {k}")

    print("\n--- SStatGameEvent Names ---")
    stat_names = set()
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SStatGameEvent':
            stat_names.add(event.get('m_eventName', b'').decode('utf-8'))
    
    for n in sorted(list(stat_names)):
        print(f"  {n}")

if __name__ == '__main__':
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-15 10.12.43 Volskaya Foundry.StormReplay"
    debug_stitches_events(path)
