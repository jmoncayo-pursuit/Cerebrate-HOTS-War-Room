#!/usr/bin/env python3
"""
Forensic Counter-Intelligence Script.
Analyzes the match history to build a persistent Counter-Selection Matrix.
Identifies which enemy heroes cause the most losses specifically per user hero.
"""

import sys
import os
import json
from collections import Counter
from datetime import datetime

# Handle paths relative to script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.insert(0, PROJECT_ROOT)
from api.services.database import DatabaseManager

FORENSICS_FILE = os.path.join(PROJECT_ROOT, 'src/data/nemesis_forensics.json')

def update_forensics(verbose=False):
    db = DatabaseManager()
    # Get matches from DB instead of JSON
    history = db.get_matches(limit=200, include_players=True)
    
    if not history:
        if verbose: print("No match history found in DB.")
        return
        
    # Matrix: { my_hero: Counter({ enemy_hero: loss_count }) }
    counter_matrix = {}
    universal_trauma = Counter() # Overall biggest threats
    
    # We scan the last 200 games for better statistical significance
    for m in history[:200]:
        if m.get('result') == 'LOSS' and 'players' in m:
            my_hero = m.get('hero')
            if not my_hero: continue
            
            if my_hero not in counter_matrix:
                counter_matrix[my_hero] = Counter()
            
            for p in m['players']:
                if p.get('win') is True:
                    en_hero = p.get('hero')
                    if en_hero and en_hero != 'Unknown':
                        counter_matrix[my_hero][en_hero] += 1
                        universal_trauma[en_hero] += 1
                        
    # Convert Counters to plain dicts for JSON
    formatted_matrix = {hero: dict(counts.most_common(10)) for hero, counts in counter_matrix.items()}
    
    forensics = {
        "generated_at": datetime.now().isoformat(),
        "universal_nemeses": [h for h, c in universal_trauma.most_common(15)],
        "counter_matrix": formatted_matrix
    }
    
    # Save to SQL
    db.set_kv('nemesis_forensics', forensics)
    
    # Optional legacy file write
    try:
        with open(FORENSICS_FILE, 'w') as f:
            json.dump(forensics, f, indent=2)
    except:
        pass
    
    if verbose:
        print(f"✅ Nemesis Forensics updated: {len(formatted_matrix)} hero counters indexed.")

if __name__ == "__main__":
    verbose = "--verbose" in sys.argv
    update_forensics(verbose=verbose)
