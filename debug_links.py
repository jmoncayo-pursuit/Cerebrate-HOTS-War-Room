
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol

def debug_links(replay_path):
    archive = mpyq.MPQArchive(replay_path)
    game_events = list(protocol().decode_replay_game_events(archive.read_file('replay.game.events')))
    details = protocol().decode_replay_details(archive.read_file('replay.details'))
    
    target_uid = None
    for i, p in enumerate(details['m_playerList']):
        if p['m_name'].decode('utf-8') == 'Discerning':
            target_uid = i
            break
            
    links = {}
    for event in game_events:
        if event['_event'] == 'NNet.Game.SCmdEvent' and event.get('_userid', {}).get('m_userId') == target_uid:
            abil = event.get('m_abil')
            if abil:
                link = abil.get('m_abilLink')
                if link is not None:
                    links[link] = links.get(link, 0) + 1
                
    print(f"AbilLinks for Discerning: {links}")

if __name__ == "__main__":
    path = "/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer/2026-02-12 18.40.25 Volskaya Foundry.StormReplay"
    debug_links(path)
