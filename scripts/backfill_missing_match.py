
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import glob
from api.services.replay_parser import parse_replay
from api.services.replay_parser.header import get_match_id
from api.services.database import DatabaseManager

# The one stubborn match
MATCH_ID = '3d0190852148d141'
REPLAYS_DIR = os.path.expanduser("~/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer")

db = DatabaseManager()

def backfill():
    print(f"Searching for match {MATCH_ID}...")
    files = glob.glob(os.path.join(REPLAYS_DIR, "*.StormReplay"))
    for fpath in files:
        try:
            # FAST CHECK FIRST
            mid = get_match_id(fpath)
            if mid == MATCH_ID:
                print(f"Found it! Parsing: {os.path.basename(fpath)}")
                result = parse_replay(fpath)
                db_data = {
                    'id': result['match_id'],
                    'map': result['map'],
                    'hero': result['hero'],
                    'result': result['result'].upper(),
                    'date': result['timestamp_iso'],
                    'duration': result['game_length'],
                    'players': result['players'],
                    'advanced_stats': result.get('advanced_stats', {})
                }
                db.upsert_match(db_data)
                print(f"Successfully backfilled match {MATCH_ID}")
                return True
        except Exception as e:
            continue
    print("Match not found in replay directory.")
    return False

if __name__ == "__main__":
    backfill()
