#!/usr/bin/env python3
"""
Quick validation script to check if match summaries use accountability language.
Scans recent matches for external-blame patterns that violate locus of control principles.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import DatabaseManager

def check_accountability():
    """Check match summaries for external-blame patterns"""
    db = DatabaseManager()
    
    # Get recent matches
    matches = db.get_matches(limit=50)
    
    if not matches:
        print("❌ No matches found in database")
        return
    
    print(f"🔍 Checking {len(matches)} matches for accountability violations...\n")
    
    # Patterns that indicate external blame (violations)
    bad_patterns = [
        'teammates to', 'team failed', 'allies to peel', 'forcing a 4v5',
        'enabling enemy', 'allowing enemy', 'permits teammates',
        'team suffered', 'team achieved', 'your team underperformed'
    ]
    
    violations_found = 0
    clean_count = 0
    
    for match in matches:
        match_id = match.get('id', 'unknown')[:8]
        summary = match.get('analysis', {}).get('summary', '')
        
        if not summary:
            continue
        
        summary_lower = summary.lower()
        found_violations = [p for p in bad_patterns if p in summary_lower]
        
        if found_violations:
            print(f"❌ Match {match_id}: Found external blame: {found_violations}")
            print(f"   Preview: {summary[:150]}...")
            violations_found += 1
        else:
            clean_count += 1
            # Only show first few clean ones to avoid spam
            if clean_count <= 3:
                print(f"✅ Match {match_id}: Clean accountability")
    
    print(f"\n📊 Summary:")
    print(f"   ✅ Clean: {clean_count}")
    print(f"   ❌ Violations: {violations_found}")
    print(f"   📈 Compliance Rate: {(clean_count / len(matches) * 100):.1f}%")
    
    if violations_found > 0:
        print(f"\n⚠️  {violations_found} matches need re-analysis with the new locus of control prompt.")
        print("   These should be automatically flagged with [ACCOUNTABILITY VIOLATION] prefix.")

if __name__ == "__main__":
    check_accountability()
