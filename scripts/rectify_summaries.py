
import os
import sys
import json
import sqlite3
import requests
import time

# Setup paths (Assume running from project root)
PROJECT_ROOT = os.path.abspath(os.curdir)
sys.path.insert(0, PROJECT_ROOT)

from agents.hooks_manager import HookResponse, HooksManager
from agents.hooks.summary_validator import summary_validator_hook
from api.services.database import DatabaseManager

# --- CONFIGURATION ---
TARGET_VERSION = "GOLD_2026_V1"
API_URL = "http://localhost:8000/api/analyze_replay"

def rectify():
    db = DatabaseManager()
    
    print("🔍 [RECTIFIER] Starting Audit of Match History...")
    
    # 1. Fetch matches with analysis
    with db._get_connection() as conn:
        rows = conn.execute("""
            SELECT m.id, m.hero, m.map, m.analysis, m.pipeline_version, m.date
            FROM matches m
            WHERE m.analysis IS NOT NULL AND m.analysis != '' AND m.analysis != '{}'
        """).fetchall()
        
    total_audited = len(rows)
    to_repair = []
    
    # 2. Audit each summary
    for row in rows:
        match_id = row['id']
        hero = row['hero']
        map_name = row['map']
        analysis = json.loads(row['analysis'])
        version = row['pipeline_version'] or "Legacy"
        
        # Build shallow match_data for validator (hero names are needed for hallucination check)
        # Fetch players for this match
        with db._get_connection() as conn:
            p_rows = conn.execute("SELECT hero, player_name FROM match_players WHERE match_id = ?", (match_id,)).fetchall()
            players = [{"hero": pr['hero'], "name": pr['player_name']} for pr in p_rows]
            
        validator_data = {
            "summary": analysis,
            "match_data": {
                "hero": hero,
                "map": map_name,
                "players": players
            }
        }
        
        # Quality Check
        hook_resp = summary_validator_hook(validator_data)
        
        reason = None
        if hook_resp.decision == HookResponse.DENY:
            reason = f"Quality Failure: {hook_resp.reason}"
        elif version != TARGET_VERSION:
            reason = f"Legacy Version: {version} -> {TARGET_VERSION}"
            
        if reason:
            print(f"⚠️  [FAIL] Match {match_id[:8]} ({hero} on {map_name}): {reason[:60]}...")
            to_repair.append({"id": match_id, "reason": reason})
        else:
            # print(f"✅ [PASS] Match {match_id[:8]} ({hero})")
            pass

    print(f"\n📊 Audit Complete. {len(to_repair)}/{total_audited} matches require rectification.")
    
    if not to_repair:
        print("🎉 All summaries meet current quality standards.")
        return

    # 3. Perform Rectification
    print(f"🚀 Initializing Autonomous Rectification for {len(to_repair)} matches...")
    print("----------------------------------------------------------------------")
    
    for i, item in enumerate(to_repair, 1):
        mid = item['id']
        print(f"[{i}/{len(to_repair)}] Rectifying Match {mid}...")
        
        try:
            # Trigger full re-analysis
            # Note: This will hit the Gemini API and run through full forensic pipeline
            res = requests.post(API_URL, json={"match_id": mid, "force": True}, timeout=150)
            
            if res.status_code == 200:
                data = res.json()
                verdict = data.get('analysis', {}).get('verdict', 'N/A')
                print(f"   ✅ SUCCESS | Verdict: {verdict}")
            else:
                print(f"   ❌ FAILED | HTTP {res.status_code}: {res.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ ERROR | {e}")
            
        # Rate-limit safety
        time.sleep(1)

    print("\n✨ Mission Accomplished: Match summaries have been rectified to Gold Standard.")

if __name__ == "__main__":
    rectify()
