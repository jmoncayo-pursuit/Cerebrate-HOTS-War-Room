
import sqlite3
import requests
import time
import json
import sys

API_URL = "http://localhost:5001/api/reparse_match"
USAGE_URL = "http://localhost:5001/api/usage"
DB_PATH = "src/data/cerebrate.db"

def get_recent_matches(limit=5):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Get recent matches, newest first
    matches = conn.execute("SELECT id, map, result FROM matches ORDER BY timestamp_iso DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return matches

def get_usage():
    try:
        res = requests.get(USAGE_URL)
        if res.status_code == 200:
            return res.json().get('usage', {})
    except:
        pass
    return {}

def main():
    try:
        match_id_to_process = None
        limit = 5
        
        # Simple arg parsing
        if len(sys.argv) > 1:
            if sys.argv[1] == "--match_id" and len(sys.argv) > 2:
                match_id_to_process = sys.argv[2]
            else:
                try: limit = int(sys.argv[1])
                except: pass
        
        if match_id_to_process:
            # Fetch specific match
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            match = conn.execute("SELECT id, map, result FROM matches WHERE id = ?", (match_id_to_process,)).fetchone()
            conn.close()
            matches = [match] if match else []
        else:
            matches = get_recent_matches(limit)
        
        print(f"🔄 Starting Batch Re-Analysis for {len(matches)} matches...")
        print("---------------------------------------------------------------")
        
        start_usage = get_usage()
        print(f"Initial Usage: {start_usage.get('total_tokens', 0):,} tokens")
        
        for i, match in enumerate(matches, 1):
            match_id = match['id']
            print(f"\n[{i}/{len(matches)}] Analyzing {match['map']} ({match['result']})...")
            
            try:
                # Get pre-call usage
                pre_usage = get_usage().get('total_tokens', 0)
                
                # Trigger Analysis
                start_time = time.time()
                res = requests.post(API_URL, json={"match_id": match_id}, timeout=120)
                duration = time.time() - start_time
                
                # Get post-call usage
                params_usage = get_usage()
                post_usage = params_usage.get('total_tokens', 0)
                delta = post_usage - pre_usage
                
                if res.status_code == 200:
                    data = res.json()
                    verdict = data.get('analysis', {}).get('verdict', 'N/A')
                    print(f"✅ Success ({duration:.1f}s) | Cost: {delta} tokens")
                    print(f"   Verdict: {verdict}")
                else:
                    print(f"❌ Failed: {res.status_code} - {res.text}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                
            # Rate limit politeness
            time.sleep(2)
            
        print("\n---------------------------------------------------------------")
        end_usage = get_usage()
        total_delta = end_usage.get('total_tokens', 0) - start_usage.get('total_tokens', 0)
        print(f"🎉 Batch Complete.")
        print(f"Total Session Consumption: {total_delta:,} tokens")
        
    except KeyboardInterrupt:
        print("\n🛑 Aborted by user.")
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")

if __name__ == "__main__":
    main()
