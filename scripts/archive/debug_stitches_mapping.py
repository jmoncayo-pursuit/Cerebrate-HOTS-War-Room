
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def debug_stitches_mapping(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    details = protocol().decode_replay_details(archive.read_file('replay.details'))
    
    uid_hero_map = {}
    for i, p in enumerate(details['m_playerList']):
        name = p.get('m_name', b'').decode('utf-8')
        hero = p.get('m_hero', b'').decode('utf-8')
        uid_hero_map[i] = {'name': name, 'hero': hero}

    link_counts = {}
    for event in game_events:
        if event['_event'] == 'NNet.Game.SSelectionDeltaEvent':
            uid = event['_userid']['m_userId']
            delta = event.get('m_delta', {})
            subgroups = delta.get('m_addSubgroups', [])
            if subgroups:
                link = subgroups[0]['m_unitLink']
                if uid not in link_counts: link_counts[uid] = {}
                link_counts[uid][link] = link_counts[uid].get(link, 0) + 1

    print("--- Link to Hero Mapping ---")
    for uid, counts in link_counts.items():
        if uid in uid_hero_map:
            best_link = max(counts.items(), key=lambda x: x[1])[0]
            print(f"UID {uid} ({uid_hero_map[uid]['hero']}) -> Link {best_link}")

if __name__ == '__main__':
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-15 10.12.43 Volskaya Foundry.StormReplay"
    debug_stitches_mapping(path)
