import requests
import json
import time

def reanalyze_missing():
    API_URL = "http://localhost:5001/api/match_history?limit=100&details=true"
    REANALYZE_URL = "http://localhost:5001/api/analyze_replay"
    
    try:
        res = requests.get(API_URL)
        matches = res.json()
        
        missing = [m for m in matches if not m.get('analysis') or m.get('analysis') == {}]
        print(f"Found {len(missing)} matches missing analysis.")
        
        for m in missing:
            match_id = m['id']
            print(f"Analyzing {match_id} ({m['hero']} on {m['map']})...")
            # This triggers analyze_match in replay_service
            res = requests.post(REANALYZE_URL, json={'match_id': match_id})
            if res.status_code == 200:
                print(f"  Success: {res.json().get('status')}")
            else:
                print(f"  Failed: {res.status_code}")
            time.sleep(1) # Be gentle
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reanalyze_missing()
