import os
import sys
import mpyq

# Setup environment
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from api.services.replay_parser.utils import setup_imp_shim
setup_imp_shim()
from heroprotocol.versions import latest
from api.services.replay_parser import parse_replay

def verify_dc_timing():
    replays_dir = '/Users/jmoncayopursuit.org/Library/Application Support/Blizzard/Heroes of the Storm/Accounts'
    count = 0
    found = 0
    for root, dirs, files in os.walk(replays_dir):
        for f in files:
            if f.endswith('.StormReplay'):
                path = os.path.join(root, f)
                try:
                    result = parse_replay(path)
                    if result.get('status') == 'success':
                        game_length = result['game_length']
                        dcs = []
                        for p in result['players']:
                            if p.get('disconnected'):
                                ts = p.get('dc_timestamp', 0)
                                # Filter out end-of-game departures (last 20s)
                                if ts < game_length - 20:
                                    dcs.append(f"{p['name']} ({p['hero']}) @ {int(ts//60)}:{int(ts%60):02d}")
                        
                        if dcs:
                            print(f"\nREAL DC DETECTED in: {f}")
                            print(f"Match length: {int(game_length//60)}:{int(game_length%60):02d}")
                            for dc in dcs:
                                print(f"  - {dc}")
                            found += 1
                            if found >= 3: return
                except:
                    pass
                count += 1
                if count % 20 == 0: print(f"Scanned {count}...")
                if count > 200: break
        if count > 200: break
    if found == 0:
        print("No mid-game DCs found in sample.")

if __name__ == "__main__":
    verify_dc_timing()
