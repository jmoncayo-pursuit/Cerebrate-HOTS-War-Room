
import os
import mpyq
from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest as protocol
from pathlib import Path

def find_recent_kharazim():
    home = Path.home()
    search = home / "Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer"
    
    files = sorted(search.glob("*.StormReplay"), key=os.path.getmtime, reverse=True)
    
    for f in files[:30]:
        try:
            archive = mpyq.MPQArchive(str(f))
            details = protocol().decode_replay_header(archive.header['user_data_header']['content']) # Actually need details
            # Decode details
            details = protocol().decode_replay_details(archive.read_file('replay.details'))
            for p in details['m_playerList']:
                name = p.get('m_name', b'').decode('utf-8')
                hero = p.get('m_hero', b'').decode('utf-8')
                if name == 'Discerning' and hero == 'Monk': # Monk is Kharazim
                    print(f"FOUND: {f}")
                    return
        except: continue

if __name__ == '__main__':
    find_recent_kharazim()
