import requests
import json
import sys
import os

# Ensure we can import from the root directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.services.database import DatabaseManager

def reanalyze_all():
    db = DatabaseManager()
    matches = db.get_matches(limit=1000)
    print(f"✧ 🧠 [HEALER] Found {len(matches)} matches to re-analyze...")
    
    for match in matches:
        match_id = match.get('id')
        if not match_id: continue
        
        print(f"✧ 🧠 [HEALER] Triggering RE-ANALYSIS for {match_id} ({match.get('hero')} on {match.get('map')})...")
        try:
            # We use the internal reparse_match endpoint
            response = requests.post(
                "http://localhost:5001/api/reparse_match",
                json={"match_id": match_id},
                timeout=120
            )
            if response.status_code == 200:
                print(f"  ✅ SUCCESS")
            else:
                print(f"  ❌ FAILED: {response.text}")
        except Exception as e:
            print(f"  ❌ ERROR: {e}")

if __name__ == "__main__":
    reanalyze_all()
