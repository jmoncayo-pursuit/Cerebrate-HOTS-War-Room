
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def inspect_event(replay_path, loop_target):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    
    for event in game_events:
        if abs(event['_gameloop'] - loop_target) < 15:
            if event['_event'] == 'NNet.Game.SCmdEvent' and event.get('_userid', {}).get('m_userId') == 8:
                print(f"Loop {event['_gameloop']}: {event}")

if __name__ == "__main__":
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2025-12-14 20.34.39 Tomb of the Spider Queen.StormReplay"
    print("Inspecting 185 at 8710:")
    inspect_event(path, 8710)
    print("\nInspecting 575 at 8737:")
    inspect_event(path, 8737)
