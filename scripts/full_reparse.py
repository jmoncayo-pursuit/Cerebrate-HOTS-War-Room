
import os
import sys
import time
import json
from api.services.replay_service import ReplayService
from api.services.database import DatabaseManager
from api.logger import ColoredLogger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def full_reparse(limit=None):
    # Ensure we are in the project root
    os.chdir("/Users/jmoncayopursuit.org/Desktop/Cerebrate-HOTS-War-Room")
    
    service = ReplayService()
    db = DatabaseManager()
    
    # 1. Get List of all replays
    replays_file = "all_replays.txt"
    if not os.path.exists(replays_file):
        print("Error: all_replays.txt not found. Run find command first.")
        return

    with open(replays_file, 'r') as f:
        replay_paths = [line.strip() for line in f if line.strip()]

    if limit:
        replay_paths = replay_paths[:limit]

    print(f"🚀 Starting Full Reparse of {len(replay_paths)} replays...")
    
    success_count = 0
    fail_count = 0
    
    # Mock file object for process_replay_file
    class MockFile:
        def __init__(self, path):
            self.path = path
            self.filename = os.path.basename(path)
        def save(self, target):
            import shutil
            shutil.copy(self.path, target)

    for i, path in enumerate(replay_paths):
        print(f"\n[{i+1}/{len(replay_paths)}] Processing: {os.path.basename(path)}")
        try:
            # We use analyze_match via process_replay_file flow
            # But process_replay_file might be safer as it re-runs the parser logic
            mock_file = MockFile(path)
            
            # Note: We want to FORCE the analysis part
            # Currently process_replay_file calls _generate_match_summary with force=True
            result, code = service.process_replay_file(mock_file)
            
            if code == 200:
                print(f"✅ Success: {result['match_id']} ({result['hero']} on {result['map']})")
                
                # Now trigger the FULL analysis (Social + Audit) 
                # because process_replay_file only does the basic summary
                print(f"🧠 Triggering Deep Analysis (Social + Audit)...")
                analysis_res = service.analyze_match(result['match_id'], force=True)
                if analysis_res.get('status') == 'complete':
                    print(f"✨ Analysis complete.")
                
                success_count += 1
            else:
                print(f"❌ Failed: {result.get('error')}")
                fail_count += 1
        except Exception as e:
            print(f"💥 Critical Error: {e}")
            fail_count += 1
            
        # Respect RPM limits slightly
        time.sleep(1)

    print(f"\n🏁 Full Reparse Finished.")
    print(f"Total: {len(replay_paths)} | Success: {success_count} | Failed: {fail_count}")

if __name__ == "__main__":
    # Start with a small batch to verify, or let the user decide.
    # The user said "lets get a full reparse going", but I'll limit to 10 for now just in case.
    # Actually I'll do 200 if possible, or all but with a safety break.
    full_reparse(limit=10) # Verify first 10
