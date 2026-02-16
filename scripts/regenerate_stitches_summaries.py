import os
import sys
import json
import sqlite3
from pathlib import Path
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add project root to path
sys.path.append(os.getcwd())

from api.services.database.manager import DatabaseManager
from api.services.replay_service import ReplayService
from api.services.replay_parser.header import get_match_id

def main():
    print("🧊 CEREBRATE: Stitches Summary Regeneration Protocol 🧊")
    try:
        db = DatabaseManager()
        replay_service = ReplayService()
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 1. Fetch Target Matches
    with db._get_connection() as conn:
        rows = conn.execute("SELECT id, map, date, hero, analysis FROM matches WHERE hero = 'Stitches' ORDER BY date DESC").fetchall()
        
    target_ids = {row['id'] for row in rows}
    print(f"🎯 Target: {len(target_ids)} Stitches matches identified.")
    
    # 2. Discover Replay Files (Optimized O(N) Scan)
    print("🔍 Scanning local replays...")
    home = Path.home()
    search_paths = [
        home / "Library/Application Support/Blizzard/Heroes of the Storm",
        home / "Documents/Heroes of the Storm",
        Path(os.getcwd()) / "replays",
        Path(os.getcwd()) / "downloaded_replays"
    ]
    
    replay_map = {} # mid -> path
    scanned_files = 0
    
    for base_path in search_paths:
        if not base_path.exists(): continue
        print(f"  - Scanning {base_path}...")
        for r, d, f in os.walk(base_path):
            for file in f:
                if file.endswith(".StormReplay"):
                    scanned_files += 1
                    full_path = str(Path(r) / file)
                    try:
                        mid = get_match_id(full_path)
                        if mid in target_ids:
                            replay_map[mid] = full_path
                    except Exception as e:
                        pass
                        
    print(f"✅ Replay Discovery Complete. Found {len(replay_map)}/{len(target_ids)} source files.")
    
    # 3. Process Valid Matches
    print("\n🚀 Initiating Gold Standard Analysis Sequence...")
    
    success_count = 0
    
    for row in rows:
        mid = row['id']
        map_name = row['map']
        
        # Check current status
        current_analysis = {}
        try:
            if row['analysis']:
                current_analysis = json.loads(row['analysis'])
        except: pass
        
        has_summary = 'summary' in current_analysis and current_analysis['summary']
        status_label = "REFINING" if has_summary else "RECOVERING"
        
        path = replay_map.get(mid)
        if not path:
            print(f"⚠️  [SKIP] {mid} ({map_name}): No replay file found.")
            continue
            
        print(f"⚡ [{status_label}] {mid} on {map_name}...")
        
        try:
            # 1. PARSE & UPSERT (CRITICAL: Get new HooksThrown data)
            from api.services.replay_parser import parse_replay
            parse_result = parse_replay(path)
            
            if parse_result.get('status') == 'success':
                db_data = {
                    'id': parse_result['match_id'],
                    'map': parse_result['map'],
                    'hero': parse_result['hero'],
                    'result': parse_result['result'].upper(),
                    'date': parse_result['timestamp_iso'],
                    'duration': parse_result['game_length'],
                    'players': parse_result['players'],
                    'advanced_stats': parse_result.get('advanced_stats', {})
                }
                db.upsert_match(db_data)
                print(f"   -> Database Updated (Hooks Captured)")
            
            # 2. FORCE RE-ANALYSIS
            result = replay_service.analyze_match(mid, force=True, replay_path=path)
            
            if result.get('status') == 'complete':
                new_analysis = result.get('analysis', {})
                verdict = new_analysis.get('verdict', 'UNKNOWN')
                
                # Check specifics
                hooks = "Unknown"
                if 'social_insights' in new_analysis:
                     pass 
                
                print(f"   -> Verdict: {verdict}")
                success_count += 1
            elif result.get('status') == 'quota_exceeded':
                 print("   -> ⚠️ QUOTA EXCEEDED (Wait 24h)")
                 break
            else:
                print(f"   -> FAILED: {result.get('message')}")
            
            # Short sleep to prevent rate limit spikes
            time.sleep(1)

        except Exception as e:
             print(f"   -> ERROR: {e}")
             
    print(f"\n🏁 OPERATION COMPLETE. {success_count} Matches Updated to Gold Standard.")

if __name__ == "__main__":
    main()
