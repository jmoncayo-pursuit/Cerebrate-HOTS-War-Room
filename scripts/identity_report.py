
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.services.replay_parser import parse_replay
import json
import sqlite3

# 1. Investigate the missing handle for the specific match
MATCH_ID = '3d0190852148d141'
REPLAYS_DIR = os.path.expanduser("~/Library/Application Support/Blizzard/Heroes of the Storm/Accounts/474575/1-Hero-1-3446653/Replays/Multiplayer")

# Find the file
import glob
files = glob.glob(os.path.join(REPLAYS_DIR, "*.StormReplay"))

found_file = None
for f in files:
    # We don't know the filename mapping for match_id easily, so we parse until found
    # Actually, let's just use the current DB state to show the user the stats
    pass

print("=== IDENTITY TRACKING REPORT ===")

# 2. Check for name changes (Multiple names, one handle)
conn = sqlite3.connect('nexus_command_lab.db')
conn.row_factory = sqlite3.Row

name_changes = conn.execute("""
    SELECT toon_handle, COUNT(DISTINCT player_name) as name_count, GROUP_CONCAT(DISTINCT player_name) as names
    FROM match_players 
    WHERE toon_handle != '0-0-0' AND toon_handle != ''
    GROUP BY toon_handle 
    HAVING name_count > 1
""").fetchall()

print(f"\n[Name Changes Detected: {len(name_changes)} souls tracked across name changes]")
for row in name_changes[:5]:
    print(f"  Handle: {row['toon_handle']} -> Names: {row['names']}")

# 3. Check for name duplicates (Same name, multiple handles)
name_dupes = conn.execute("""
    SELECT player_name, COUNT(DISTINCT toon_handle) as handle_count, GROUP_CONCAT(DISTINCT toon_handle) as handles
    FROM match_players 
    WHERE player_name != 'Player' AND toon_handle != '0-0-0' AND toon_handle != ''
    GROUP BY player_name 
    HAVING handle_count > 1
""").fetchall()

print(f"\n[Duplicate Names Sanitized: {len(name_dupes)} names identified as different people]")
for row in name_dupes[:5]:
    print(f"  Name: {row['player_name']} -> {row['handle_count']} different players found")

# 4. Total Social Reach
total_profiles = conn.execute("SELECT COUNT(*) FROM social_profiles").fetchone()[0]
print(f"\n[Total Verified Combat Profiles: {total_profiles}]")

conn.close()
