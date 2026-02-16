

from api.services.database.manager import DatabaseManager
from api.services.mechanical_analysis_service import MechanicalAnalysisService
from api.services.replay_parser.parser import parse_replay
import os
import json
import sqlite3

# 1. Initialize
# Need to hack the path resolution because script is running from root
import sys
sys.path.append(os.getcwd())
db = DatabaseManager()
print("Starting Mechanic Refinement for Stitches...")

# 2. Get Stitches Matches
# The 'matches' table does NOT have replay_file. It's constructed or might not be stored.
# We need to find the replay file from the file system by matching the ID or just re-scanning all replays.
# Actually, the 'matches' table has 'id'. The replay filename is usually lost unless stored.
# BUT, we can iterate through the replays directory, get the match ID, check if it's in the list of Stitches matches, and then re-process.

# Let's get the list of Stitches match IDs
with db._get_connection() as conn:
    rows = conn.execute("SELECT id, analysis FROM matches WHERE hero = 'Stitches'").fetchall()

matches_to_refine = {row[0]: row[1] for row in rows}
print(f"Found {len(matches_to_refine)} Stitches matches to refine.")

# 3. Find Replays
from pathlib import Path
home = Path.home()
replay_dirs = [
    home / "Library/Application Support/Blizzard/Heroes of the Storm",
    home / "Documents/Heroes of the Storm",
    # Also check local directories just in case
    Path(os.getcwd()) / "replays",
    Path(os.getcwd()) / "replays" / "uploaded",
    Path(os.getcwd()) / "downloaded_replays"
]

print(f"Searching for replays in: {[str(p) for p in replay_dirs]}")

found_count = 0
matches_processed = set()

from api.services.replay_parser.header import get_match_id

for base_dir in replay_dirs:
    if not base_dir.exists(): continue
    
    print(f"Scanning {base_dir}...")
    # Walk strictly
    for r, d, f in os.walk(base_dir):
        for file in f:
            if file.endswith(".StormReplay"):
                full_path = os.path.join(r, file)
                try:
                    # Optimization: Check if file modification time is recent? No, we need specific IDs.
                    # We have to parse the header to get the ID. This is slow but necessary.
                    m_id = get_match_id(full_path)
                    
                    if m_id in matches_to_refine:
                        if m_id in matches_processed: continue
                        
                        print(f"Refining forensics for {m_id} from {full_path}...")
                        
                        # Generate new forensics
                        forensics = MechanicalAnalysisService.analyze_replay(full_path, 'Stitches')
                        
                        if forensics:
                            # Merge into analysis
                            current_analysis_json = matches_to_refine[m_id]
                            analysis = {}
                            if current_analysis_json:
                                try:
                                    analysis = json.loads(current_analysis_json)
                                except: pass
                                
                            analysis['forensics'] = forensics
                            
                            # Save back to DB
                            with db._get_connection() as conn:
                                conn.execute("UPDATE matches SET analysis = ? WHERE id = ?", (json.dumps(analysis), m_id))
                            print(f"Updated forensics for match {m_id}")
                            found_count += 1
                            matches_processed.add(m_id)
                except Exception as e:
                    # print(f"Error checking {file}: {e}")
                    pass

print(f"Refined {found_count} matches.")

# 4. Invalidate Cache
with db._get_connection() as conn:
    conn.execute("DELETE FROM hero_dossiers WHERE hero_name = 'Stitches'")
    
print("Forensic refinement complete. Cache invalidated.")
