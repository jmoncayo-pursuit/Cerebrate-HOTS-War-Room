
import sqlite3
import requests
import time
import json
import os
from datetime import datetime

API_URL = "http://localhost:5001/api/reparse_match"
DB_PATH = "src/data/nexus_core.db"
PIPELINE_VERSION = "2.1.0"

def get_outdated_matches():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Find matches that are not on the latest pipeline version
    query = "SELECT id, map, hero, pipeline_version FROM matches WHERE pipeline_version != ? OR pipeline_version IS NULL OR pipeline_version = ''"
    matches = conn.execute(query, (PIPELINE_VERSION,)).fetchall()
    conn.close()
    return matches

def main():
    print("🚀 NEXUS RE-BASELINE INITIALIZED")
    print(f"Target Version: {PIPELINE_VERSION}")
    
    matches = get_outdated_matches()
    total = len(matches)
    
    if total == 0:
        print("✅ All matches are already on the latest pipeline version.")
        return

    print(f"Found {total} matches requiring re-analysis.")
    print("---------------------------------------------------------------")
    
    success_count = 0
    fail_count = 0
    
    for i, match in enumerate(matches, 1):
        match_id = match['id']
        current_v = match['pipeline_version'] or "Legacy/None"
        
        print(f"[{i}/{total}] Re-analyzing {match['hero']} on {match['map']} (Current V: {current_v})...")
        
        try:
            start_time = time.time()
            res = requests.post(API_URL, json={"match_id": match_id}, timeout=120)
            duration = time.time() - start_time
            
            if res.status_code == 200:
                data = res.json()
                print(f"   ✅ Success ({duration:.1f}s) | Pipeline Updated to {PIPELINE_VERSION}")
                success_count += 1
            else:
                print(f"   ❌ Failed: {res.status_code} - {res.text}")
                fail_count += 1
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            fail_count += 1
            
        # Pacing to avoid overloading the API or hitting rate limits
        time.sleep(1)
        
    print("\n---------------------------------------------------------------")
    print(f"🎉 Re-Baselining Complete.")
    print(f"Total: {total} | Success: {success_count} | Failed: {fail_count}")

if __name__ == "__main__":
    main()
