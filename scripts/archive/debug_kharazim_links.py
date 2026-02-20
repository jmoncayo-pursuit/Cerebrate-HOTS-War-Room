
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def find_kharazim_abils(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    details = protocol().decode_replay_details(archive.read_file('replay.details'))
    
    target_uid = None
    for i, p in enumerate(details['m_playerList']):
        name = p.get('m_name', b'').decode('utf-8')
        if name == 'Discerning':
            target_uid = i
            hero = p.get('m_hero', b'').decode('utf-8')
            print(f"Discerning is playing {hero} (UID {i})")
            break
            
    if target_uid is None: return

    links = {}
    for event in game_events:
        if event['_event'] == 'NNet.Game.SCmdEvent':
            uid = event.get('_userid', {}).get('m_userId')
            if uid == target_uid:
                abil = event.get('m_abil')
                if abil:
                    link = abil.get('m_abilLink')
                    links[link] = links.get(link, 0) + 1
    
    print("--- Ability Links ---")
    for link, count in sorted(links.items(), key=lambda x: x[1], reverse=True):
        print(f"Link {link}: {count} casts")

if __name__ == '__main__':
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-12 18.08.01 Hanamura Temple.StormReplay"
    find_kharazim_abils(path)
