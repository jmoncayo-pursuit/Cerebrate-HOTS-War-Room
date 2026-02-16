import os
import sys
import json
from pathlib import Path
sys.path.append(os.getcwd())
from api.services.database.manager import DatabaseManager
from api.services.replay_service import ReplayService
from api.services.replay_parser.header import get_match_id

def main():
    db = DatabaseManager()
    replay_service = ReplayService()
    
    # Target only matches with "Unknown" in analysis
    with db._get_connection() as conn:
        rows = conn.execute("SELECT id, map, hero FROM matches WHERE hero = 'Stitches' AND analysis LIKE '%Unknown%'").fetchall()
    
    if not rows:
        print("No matches with 'Unknown' found.")
        return

    print(f"Targeting {len(rows)} matches for corruption cleanup...")
    
    # Replay discovery
    home = Path.home()
    search_paths = [home / "Library/Application Support/Blizzard/Heroes of the Storm", home / "Documents/Heroes of the Storm", Path(os.getcwd()) / "replays"]
    replay_map = {}
    for base_path in search_paths:
        if not base_path.exists(): continue
        for r, d, f in os.walk(base_path):
            for file in f:
                if file.endswith(".StormReplay"):
                    try:
                        p = str(Path(r) / file)
                        mid = get_match_id(p)
                        replay_map[mid] = p
                    except: pass

    for row in rows:
        mid = row['id']
        path = replay_map.get(mid)
        if path:
            print(f"Repairing {mid}...")
            replay_service.analyze_match(mid, force=True, replay_path=path)
        else:
            print(f"Could not find replay for {mid}")

if __name__ == "__main__":
    main()
