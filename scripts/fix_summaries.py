#!/usr/bin/env python3
"""
Summary Fixer Script
Manually rewrites bad AI summaries using actual match data.
NO API CALLS - all fixes are rule-based using raw stats.
"""

import sqlite3
import json
import re
from datetime import datetime

def fmt_time(seconds):
    """Format seconds to MM:SS"""
    if seconds is None:
        return "0:00"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"

def generate_fixed_summary(match_data, stats_data):
    """Generate a gold-standard summary from raw data"""
    
    hero = match_data['hero']
    map_name = match_data['map']
    result = match_data['result']
    duration = match_data['duration']
    
    players = stats_data.get('players', [])
    user_player = next((p for p in players if p.get('hero') == hero), None)
    
    if not user_player:
        return None
    
    user_team = user_player.get('team')
    user_stats = user_player.get('stats', {})
    
    # Team aggregates
    team_players = [p for p in players if p.get('team') == user_team]
    enemy_players = [p for p in players if p.get('team') != user_team]
    
    team_deaths = sum(p.get('stats', {}).get('Deaths', 0) for p in team_players)
    enemy_deaths = sum(p.get('stats', {}).get('Deaths', 0) for p in enemy_players)
    
    team_kills = sum(p.get('stats', {}).get('SoloKill', 0) for p in team_players)
    enemy_kills = sum(p.get('stats', {}).get('SoloKill', 0) for p in enemy_players)
    
    # Merc caps
    merc_events = stats_data.get('merc_captures', [])
    team_mercs = len([m for m in merc_events if m.get('captured_by_team') == user_team])
    enemy_mercs = len([m for m in merc_events if m.get('captured_by_team') != user_team])
    
    # User contribution
    user_deaths = user_stats.get('Deaths', 0)
    user_kills = user_stats.get('SoloKill', 0)
    user_hero_dmg = user_stats.get('HeroDamage', 0)
    user_siege_dmg = user_stats.get('SiegeDamage', 0)
    user_xp = user_stats.get('ExperienceContribution', 0)
    
    # Build summary
    verdict = result.upper()
    
    # Determine primary issue
    if team_deaths > enemy_deaths * 1.3:
        issue = f"team fight losses ({team_deaths} deaths vs enemy's {enemy_deaths})"
    elif team_mercs < enemy_mercs * 0.5:
        issue = f"macro disadvantage ({team_mercs} merc caps vs enemy's {enemy_mercs})"
    elif team_kills < enemy_kills * 0.7:
        issue = f"kill deficit ({team_kills} kills vs enemy's {enemy_kills})"
    else:
        issue = "close match decided by late-game execution"
    
    summary = f"{verdict} on {map_name} ({duration}). "
    
    if result == 'LOSS':
        summary += f"Your team lost due to {issue}. "
    else:
        summary += f"Your team won despite {issue}. "
    
    summary += f"As {hero}, you contributed {user_hero_dmg:,} hero damage and {user_siege_dmg:,} siege damage. "
    
    # Add merc context if significant
    if team_mercs > 0 or enemy_mercs > 0:
        summary += f"Merc control: your team {team_mercs}, enemy {enemy_mercs}. "
    
    # Win condition
    if result == 'WIN':
        win_condition = f"Your team secured victory through superior {_get_win_factor(team_stats=team_players, enemy_stats=enemy_players, merc_diff=team_mercs-enemy_mercs)}."
    else:
        win_condition = f"Enemy team won through {_get_win_factor(team_stats=enemy_players, enemy_stats=team_players, merc_diff=enemy_mercs-team_mercs)}."
    
    return {
        'summary': summary.strip(),
        'win_condition': win_condition,
        'verdict': verdict,
        'key_insights': {
            'commander_kills': user_kills,
            'team_global_merc_caps': team_mercs,
            'enemy_global_merc_caps': enemy_mercs,
            'contribution_index': f"{user_hero_dmg:,} Hero Dmg / {user_xp:,} XP"
        }
    }

def _get_win_factor(team_stats, enemy_stats, merc_diff):
    """Determine primary win factor"""
    team_deaths = sum(p.get('stats', {}).get('Deaths', 0) for p in team_stats)
    enemy_deaths = sum(p.get('stats', {}).get('Deaths', 0) for p in enemy_stats)
    
    if team_deaths < enemy_deaths * 0.7:
        return "dominant team fighting"
    elif merc_diff > 5:
        return "superior macro play and merc control"
    else:
        return "consistent objective control"

def main():
    """Fix all bad summaries in database"""
    db = sqlite3.connect('war_room.db')
    cursor = db.cursor()
    
    # Get all matches with analysis
    cursor.execute("""
        SELECT id, map, hero, result, duration, analysis, raw_stats 
        FROM matches 
        WHERE analysis IS NOT NULL AND analysis != '{}'
    """)
    
    matches = cursor.fetchall()
    print(f"Found {len(matches)} matches with analysis")
    
    fixed_count = 0
    skipped_count = 0
    
    for match_id, map_name, hero, result, duration, analysis_str, raw_stats_str in matches:
        analysis = json.loads(analysis_str) if analysis_str else {}
        stats = json.loads(raw_stats_str) if raw_stats_str else {}
        
        current_summary = analysis.get('summary', '')
        current_win_cond = analysis.get('win_condition', '')
        
        # Check if needs fixing - be more aggressive
        needs_fix = (
            'DC Status' in current_summary or
            'Stable Uplink' in current_summary or
            'severe' in current_summary.lower() or
            'decisive' in current_summary.lower() or
            'significant' in current_summary.lower() or
            'characterized by' in current_summary.lower() or
            'complete failure' in current_summary.lower() or
            'won by winning' in current_win_cond.lower() or
            'achieved victory by' in current_win_cond.lower() or
            len(current_summary) < 100  # Too short
        )
        
        if not needs_fix:
            skipped_count += 1
            continue
        
        # Generate fixed summary
        match_data = {
            'hero': hero,
            'map': map_name,
            'result': result,
            'duration': duration
        }
        
        fixed_analysis = generate_fixed_summary(match_data, stats)
        
        if fixed_analysis:
            # Merge with existing analysis (preserve other fields)
            analysis.update(fixed_analysis)
            
            # Update database
            cursor.execute(
                "UPDATE matches SET analysis = ? WHERE id = ?",
                (json.dumps(analysis), match_id)
            )
            
            fixed_count += 1
            
            if fixed_count <= 10:  # Show first 10 fixes
                print(f"\n=== FIXED #{fixed_count}: {hero} on {map_name} ({result}) ===")
                print(f"BEFORE: {current_summary[:120]}...")
                print(f"AFTER:  {fixed_analysis['summary'][:120]}...")
    
    db.commit()
    print(f"\n=== SUMMARY ===")
    print(f"Fixed: {fixed_count}")
    print(f"Skipped (already good): {skipped_count}")
    print(f"Total: {len(matches)}")

if __name__ == '__main__':
    main()
