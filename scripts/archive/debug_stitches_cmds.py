
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def debug_stitches_cmds(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    
    target_uid = 5 # Stitches in that match
    
    print("--- SCmdEvent with TargetUnit (UID 5) ---")
    count = 0
    for event in game_events:
        if event['_event'] == 'NNet.Game.SCmdEvent':
            uid = event.get('_userid', {}).get('m_userId')
            if uid == target_uid:
                data = event.get('m_data', {})
                if 'TargetUnit' in data:
                    tu = data['TargetUnit']
                    print(f"TS {event['_gameloop']/16.0}: {tu}")
                    count += 1
                    if count > 20: break

if __name__ == '__main__':
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-15 10.12.43 Volskaya Foundry.StormReplay"
    debug_stitches_cmds(path)
