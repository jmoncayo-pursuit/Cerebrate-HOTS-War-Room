#!/usr/bin/env python3
"""
Quick Summary Fixes - Batch Update
Removes common bad patterns from summaries
"""

import sqlite3
import json

def main():
    db = sqlite3.connect('war_room.db')
    cursor = db.cursor()
    
    fixes_applied = []
    
    # Fix 1: Remove "DC Status: Stable Uplink" noise
    cursor.execute("""
        SELECT id, analysis FROM matches 
        WHERE analysis LIKE '%DC Status%Stable Uplink%'
    """)
    
    for match_id, analysis_str in cursor.fetchall():
        analysis = json.loads(analysis_str)
        old_summary = analysis.get('summary', '')
        
        # Remove DC noise
        new_summary = old_summary.replace('. The DC Status was Stable Uplink.', '.')
        new_summary = new_summary.replace(' The DC Status was Stable Uplink.', '')
        
        if new_summary != old_summary:
            analysis['summary'] = new_summary
            cursor.execute("UPDATE matches SET analysis = ? WHERE id = ?", 
                         (json.dumps(analysis), match_id))
            fixes_applied.append(('DC_NOISE', match_id, old_summary[:80]))
    
    db.commit()
    
    print(f"=== BATCH FIX REPORT ===")
    print(f"Total fixes applied: {len(fixes_applied)}")
    
    for fix_type, match_id, old_text in fixes_applied:
        print(f"\n[{fix_type}] {match_id}")
        print(f"  Old: {old_text}...")

if __name__ == '__main__':
    main()
