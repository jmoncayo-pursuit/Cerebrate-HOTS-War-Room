#!/usr/bin/env python3
"""
Seed Gold Standard Examples into Database
Extracts examples from docs and migrates them to gold_standard_examples table
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import DatabaseManager

def seed_gold_standards():
    """Seed initial gold standard examples from documentation"""
    DB = DatabaseManager()
    
    examples = [
        {
            'id': 'gold_dragon_shire_kharazim_loss',
            'map': "Dragon Shire",
            'hero': 'Kharazim',
            'result': 'LOSS',
            'summary': "RESOURCE SUPREMACY. Despite the loss, your performance was a macroeconomic masterclass. Your 27,439 Experience Contribution contained **22,040 Minion XP** (Isolated Minion XP), proving you were the team's primary engine for level progression. However, a critical **Vehicle Allocation** error occurred: piloting the Dragon Knight (10:04 capture) as a solo-healer. This choice traded ~5,200 Healing Per Minute (HPM) for siege damage—equivalent to removing 1.5x of a Valla's health pool from the team's sustain capacity.",
            'verdict': 'Macro Anchor',
            'quality_score': 5
        },
        {
            'id': 'gold_towers_doom_kharazim_win',
            'map': "Towers of Doom",
            'hero': 'Kharazim',
            'result': 'WIN',
            'summary': "MACRO ENGINE ENGAGED. On Towers of Doom, you and **Jaina** demonstrated elite **Throughput Distribution**. By allowing a High-Efficiency Camper (**Jaina**) to manage 8 Sapper captures (**24 Core Damage**), you were freed to generate **16,834 Experience** and anchor the lane-states with **9,144 Minion XP**. This synergy secured 36 total Core Shots from mercenaries alone, turning the map into a structured ammunition factory while you maintained the team's level advantage.",
            'verdict': 'Macro Anchor',
            'quality_score': 5
        },
        {
            'id': 'gold_dragon_shire_timing_failure',
            'map': "Dragon Shire",
            'hero': 'Kharazim',
            'result': 'LOSS',
            'summary': "TIMING FAILURE. **Kharazim** died at 19:16 (isolated) near the Boss Pit, 10 seconds before the objective spawned. This forced a 4v5 defense which collapsed. Earlier deaths at 05:46 and 07:32 fed critical XP during the rotation phase, putting the team down a Talent Tier at the 12:00 mark.",
            'verdict': 'Solid',
            'quality_score': 5
        },
        {
            'id': 'gold_blackhearts_bay_coin_economy',
            'map': "Blackheart's Bay",
            'hero': 'Stitches',
            'result': 'LOSS',
            'summary': "COIN ECONOMY DEFICIT. Your 2 coins collected (Target: 3+ for tanks) enabled enemy team to secure 3 more turn-ins, creating structural deficit. Despite generating 8,234 Minion XP (lane anchor), your failure to contest coin spawns at 3:15, 6:42, and 9:18 allowed enemy Greymane to accumulate 12 coins total. The coin economy battle determined the outcome—your lane soak was insufficient compensation.",
            'verdict': 'Feeder',
            'quality_score': 5
        },
    ]
    
    print(f"Seeding {len(examples)} gold standard examples...")
    
    for ex in examples:
        DB.save_gold_standard(
            example_id=ex['id'],
            map_name=ex['map'],
            hero=ex['hero'],
            result=ex['result'],
            summary=ex['summary'],
            verdict=ex['verdict'],
            quality_score=ex['quality_score']
        )
        print(f"  ✓ Saved: {ex['id']} ({ex['map']} - {ex['hero']} - {ex['result']})")
    
    print(f"\n✅ Successfully seeded {len(examples)} gold standard examples!")
    print("\nTo verify, run:")
    print("  python3 -c \"from database_manager import DatabaseManager; DB = DatabaseManager(); print(DB.get_gold_standards())\"")

if __name__ == '__main__':
    seed_gold_standards()
