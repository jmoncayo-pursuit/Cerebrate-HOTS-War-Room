import sqlite3
import json
import os
from datetime import datetime

# ==============================================================================
# Cerebrate Privacy Sync - Example File Generator (SQLite Version)
# ==============================================================================

DB_PATH = "src/data/cerebrate.db"
OUTPUT_DIR = "src/data"

def anonymize_profile(profile_data):
    """Deep anonymization of personal profile data"""
    if not profile_data: return {}
    
    # Clone to avoid modifying original
    clean = dict(profile_data)
    
    # Generic Identity
    if 'battle_tag' in clean: clean['battle_tag'] = "Commander#1234"
    if 'battletag' in clean: clean['battletag'] = "Commander#1234"
    if 'name' in clean: clean['name'] = "Cerebrate"
    
    # Wipe specific telemetry that might be too personal
    if 'last_updated' in clean: clean['last_updated'] = datetime.now().isoformat()
    
    return clean

def main():
    print("🔒 Cerebrate Privacy Sync: Extracting templates from SQLite...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. PLAYER PROFILE
    try:
        row = conn.execute("SELECT value FROM kv_store WHERE key='player_profile'").fetchone()
        if row:
            profile = json.loads(row['value'])
            clean_profile = anonymize_profile(profile)
            with open(os.path.join(OUTPUT_DIR, "player_profile.json.example"), "w") as f:
                json.dump(clean_profile, f, indent=4)
            print("  ✅ Created player_profile.json.example")
    except Exception as e:
        print(f"  ⚠️  Failed to sync profile: {e}")

    # 2. MATCH HISTORY (Sample)
    try:
        rows = conn.execute("SELECT * FROM matches LIMIT 3").fetchall()
        matches = [dict(r) for r in rows]
        # Anonymize match IDs and sensitive metadata if needed
        for m in matches:
            m['pipeline_version'] = "2.1.0"
            # Optional: Wipe specific player names in the match if desired
            
        with open(os.path.join(OUTPUT_DIR, "match_history.json.example"), "w") as f:
            json.dump(matches, f, indent=4)
        print(f"  ✅ Created match_history.json.example ({len(matches)} samples)")
    except Exception as e:
        print(f"  ⚠️  Failed to sync match history: {e}")

    # 3. GLOBAL META STATS (Public so just a dump)
    try:
        rows = conn.execute("SELECT * FROM global_meta_stats LIMIT 5").fetchall()
        meta = [dict(r) for r in rows]
        with open(os.path.join(OUTPUT_DIR, "global_stats_dump.json.example"), "w") as f:
            json.dump(meta, f, indent=4)
        print("  ✅ Created global_stats_dump.json.example")
    except Exception as e:
        print(f"  ⚠️  Failed to sync global stats: {e}")

    conn.close()
    print("\n✨ Privacy Synchronization Complete.")

if __name__ == "__main__":
    main()
