
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def debug_hero_names(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    tracker_events = list(protocol().decode_replay_tracker_events(archive.read_file('replay.tracker.events')))
    details = protocol().decode_replay_details(archive.read_file('replay.details'))
    
    player_heroes = [p['m_hero'].decode('utf-8') for p in details['m_playerList']]
    print(f"Player Heroes: {player_heroes}")
    
    born_heroes = []
    for event in tracker_events:
        if event['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent':
            name = event['m_unitTypeName'].decode('utf-8')
            if 'Hero' in name and event['m_controlPlayerId'] > 0:
                born_heroes.append(name)
    
    print(f"Born Heroes: {list(set(born_heroes))}")

if __name__ == "__main__":
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-15 10.12.43 Volskaya Foundry.StormReplay"
    debug_hero_names(path)
