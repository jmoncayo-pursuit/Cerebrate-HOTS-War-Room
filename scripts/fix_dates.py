#!/usr/bin/env python3
"""
Fix Replay Dates - Lightweight Script
Extracts correct dates from replay filenames and updates the database directly.
NO API calls, NO reparsing - just SQL updates.

Usage:
    python3 scripts/fix_dates.py
"""

import os
import re
import sqlite3
from datetime import datetime, timezone

# Find replays directory
REPLAYS_DIRS = [
    os.path.expanduser("~/Library/Application Support/Blizzard/Heroes of the Storm/Accounts"),
]

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "war_room.db")

def extract_date_from_filename(filename):
    """Extract ISO timestamp from filename like '2025-12-25 05.45.56 Map.StormReplay'"""
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2})\.(\d{2})\.(\d{2})', filename)
    if match:
        year, month, day, hour, minute, second = match.groups()
        dt = datetime(int(year), int(month), int(day), 
                     int(hour), int(minute), int(second), 
                     tzinfo=timezone.utc)
        return dt.isoformat()
    return None

def get_match_id_fast(replay_path):
    """Get match_id from replay header without full parsing."""
    import mpyq
    import hashlib
    
    try:
        archive = mpyq.MPQArchive(replay_path)
        # Use raw header bytes for speed
        header_content = archive.header['user_data_header']['content']
        
        # Import heroprotocol with shim
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from api.services.replay_parser.utils import setup_imp_shim
        setup_imp_shim()
        from heroprotocol.versions import latest
        
        protocol = latest()
        header = protocol.decode_replay_header(header_content)
        
        id_components = [
            str(header.get('m_randomValue', '')),
            str(header.get('m_signature', '')),
            str(header.get('m_timeUTC', 0)),
            str(header.get('m_elapsedGameLoops', 0)),
            str(header.get('m_version', {}).get('m_baseBuild', 0))
        ]
        return hashlib.md5('_'.join(id_components).encode()).hexdigest()[:16]
    except Exception as e:
        return None

def find_all_replays():
    """Find all .StormReplay files in known directories."""
    replays = []
    for base_dir in REPLAYS_DIRS:
        if not os.path.exists(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            for f in files:
                if f.endswith('.StormReplay'):
                    replays.append(os.path.join(root, f))
    return replays

def fix_dates():
    """Main function to fix dates in database."""
    print("🔧 Fixing replay dates (no API calls)...")
    
    # 1. Get all replays on disk
    replays = find_all_replays()
    print(f"📁 Found {len(replays)} replay files on disk")
    
    if not replays:
        print("❌ No replay files found!")
        return
    
    # 2. Connect to database
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 3. Get all match IDs from database with wrong dates (2026 is clearly wrong - real games are from 2025)
    cursor = conn.execute("SELECT id, date FROM matches WHERE date LIKE '2026-%'")
    wrong_dates = {row['id']: row['date'] for row in cursor.fetchall()}
    
    print(f"📊 Found {len(wrong_dates)} matches with wrong dates (2026)")

    
    if not wrong_dates:
        print("✅ No dates need fixing!")
        conn.close()
        return
    
    # 4. Build match_id -> filename mapping for affected matches
    fixed = 0
    errors = 0
    
    for replay_path in replays:
        filename = os.path.basename(replay_path)
        
        # Extract date from filename
        correct_date = extract_date_from_filename(filename)
        if not correct_date:
            continue
        
        # Get match_id
        match_id = get_match_id_fast(replay_path)
        if not match_id:
            continue
        
        # Check if this match needs fixing
        if match_id in wrong_dates:
            # Update database
            conn.execute("UPDATE matches SET date = ? WHERE id = ?", (correct_date, match_id))
            print(f"  ✓ {filename[:40]}... → {correct_date[:10]}")
            fixed += 1
            del wrong_dates[match_id]  # Remove from pending
            
            if not wrong_dates:  # All fixed
                break
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Fixed {fixed} dates, {len(wrong_dates)} remaining (files not found on disk)")

if __name__ == "__main__":
    fix_dates()
