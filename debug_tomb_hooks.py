
import os
import mpyq
import math
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def debug_tomb_match(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    details = protocol().decode_replay_details(archive.read_file('replay.details'))
    
    target_uid = None
    for i, p in enumerate(details['m_playerList']):
        name = p['m_name'].decode('utf-8')
        if name == 'Discerning':
            target_uid = i
            break
    
    if target_uid is None:
        print("Stitches player Discerning not found")
        return

    print(f"Target UserID: {target_uid}")
    
    # Range around 9:05 (545s, 8720 loops)
    start_loop = 8600
    end_loop = 8900
    
    print("\n--- Game Events around 9:05 ---")
    for event in game_events:
        loop = event['_gameloop']
        if start_loop <= loop <= end_loop:
            uid = event.get('_userid', {}).get('m_userId')
            if uid == target_uid:
                if event['_event'] == 'NNet.Game.SCmdEvent':
                    abil = event.get('m_abil')
                    if abil:
                        print(f"Loop {loop} (TS {loop/16.0}): CmdEvent AbilLink={abil.get('m_abilLink')}")
                elif event['_event'] == 'NNet.Game.SSelectionDeltaEvent':
                    pass

    print("\n--- Tracker Events around 9:05 ---")
    for event in tracker_events:
        loop = event['_gameloop']
        if start_loop <= loop <= end_loop:
            if event['_event'] == 'NNet.Replay.Tracker.SStatGameEvent':
                name = event.get('m_eventName', b'').decode('utf-8')
                if name == 'PlayerDeath':
                    data = {d.get('m_key', b'').decode('utf-8'): d.get('m_value') for d in (event.get('m_intData') or []) + (event.get('m_fixedData') or [])}
                    print(f"Loop {loop} (TS {loop/16.0}): Death! Data={data}")

if __name__ == "__main__":
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2025-12-14 20.34.39 Tomb of the Spider Queen.StormReplay"
    debug_tomb_match(path)
