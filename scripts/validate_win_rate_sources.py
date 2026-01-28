#!/usr/bin/env python3
"""
Validate Win Rate Source Attribution
Checks for discrepancies between Blizzard Verified stats and Parsed match data.
Flags heroes where data sources don't match (potential data integrity issues).
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.services.database import DatabaseManager

def validate_win_rate_sources():
    """Validate win rate sources across all heroes"""
    db = DatabaseManager()
    
    # Get profile and verified stats
    profile = db.get_kv('player_profile') or {}
    audit = profile.get('storm_league_audit', {})
    hero_audit = audit.get('heroes', {})
    hero_profile_stats = profile.get('hero_stats', {})
    
    # Get all matches
    matches = db.get_matches(limit=10000)
    
    if not matches:
        print("❌ No matches found in database")
        return 1
    
    print("🔍 Validating Win Rate Source Attribution...\n")
    print(f"📊 Analyzing {len(matches)} matches across all heroes\n")
    
    # Group matches by hero
    hero_match_stats = {}
    for match in matches:
        hero = match.get('hero')
        if not hero:
            continue
        
        if hero not in hero_match_stats:
            hero_match_stats[hero] = {'wins': 0, 'games': 0}
        
        hero_match_stats[hero]['games'] += 1
        if match.get('result') == 'WIN':
            hero_match_stats[hero]['wins'] += 1
    
    # Compare with verified stats
    discrepancies = []
    verified_only = []
    parsed_only = []
    matching = []
    
    all_heroes = set(list(hero_audit.keys()) + list(hero_match_stats.keys()) + list(hero_profile_stats.keys()))
    
    for hero in sorted(all_heroes):
        # Get verified stats
        verified_wr = hero_audit.get(hero, {}).get('win_rate')
        verified_games = hero_audit.get(hero, {}).get('games_played')
        
        # Fallback to profile stats
        if verified_wr is None:
            verified_wr = hero_profile_stats.get(hero, {}).get('lifetime', {}).get('win_rate')
            verified_games = hero_profile_stats.get(hero, {}).get('lifetime', {}).get('games')
        
        # Get parsed stats
        parsed_stats = hero_match_stats.get(hero, {})
        parsed_games = parsed_stats.get('games', 0)
        parsed_wr = (parsed_stats.get('wins', 0) / parsed_games * 100) if parsed_games > 0 else None
        
        # Categorize
        if verified_wr is not None and verified_games and verified_games > 0:
            if parsed_games == 0:
                verified_only.append({
                    'hero': hero,
                    'verified_wr': verified_wr,
                    'verified_games': verified_games,
                    'source': 'verified_only'
                })
            elif parsed_games > 0:
                diff = abs(parsed_wr - float(verified_wr))
                if diff > 5.0:  # More than 5% difference
                    discrepancies.append({
                        'hero': hero,
                        'verified_wr': float(verified_wr),
                        'verified_games': int(verified_games),
                        'parsed_wr': parsed_wr,
                        'parsed_games': parsed_games,
                        'difference': diff
                    })
                else:
                    matching.append({
                        'hero': hero,
                        'wr': float(verified_wr),
                        'verified_games': int(verified_games),
                        'parsed_games': parsed_games,
                        'difference': diff
                    })
        elif parsed_games > 0:
            parsed_only.append({
                'hero': hero,
                'parsed_wr': parsed_wr,
                'parsed_games': parsed_games,
                'source': 'parsed_only'
            })
    
    # Report results
    print("=" * 80)
    print("📊 VALIDATION RESULTS")
    print("=" * 80)
    
    print(f"\n✅ Matching Sources: {len(matching)}")
    if matching:
        print("   Heroes where verified and parsed stats align (±5%):")
        for item in matching[:10]:  # Show first 10
            print(f"   - {item['hero']}: {item['wr']:.1f}% WR "
                  f"(Verified: {item['verified_games']}g, Parsed: {item['parsed_games']}g, "
                  f"Diff: {item['difference']:.1f}%)")
        if len(matching) > 10:
            print(f"   ... and {len(matching) - 10} more")
    
    print(f"\n⚠️  Discrepancies Found: {len(discrepancies)}")
    if discrepancies:
        print("   Heroes where verified and parsed stats differ significantly (>5%):")
        for item in sorted(discrepancies, key=lambda x: x['difference'], reverse=True):
            print(f"   ❌ {item['hero']}:")
            print(f"      Verified: {item['verified_wr']:.1f}% ({item['verified_games']} games)")
            print(f"      Parsed:   {item['parsed_wr']:.1f}% ({item['parsed_games']} games)")
            print(f"      Difference: {item['difference']:.1f}% ⚠️")
    
    print(f"\n📋 Verified Only (No Parsed Matches): {len(verified_only)}")
    if verified_only:
        for item in verified_only[:5]:
            print(f"   - {item['hero']}: {item['verified_wr']:.1f}% WR ({item['verified_games']} games) [Verified]")
        if len(verified_only) > 5:
            print(f"   ... and {len(verified_only) - 5} more")
    
    print(f"\n📋 Parsed Only (No Verified Stats): {len(parsed_only)}")
    if parsed_only:
        for item in sorted(parsed_only, key=lambda x: x['parsed_games'], reverse=True)[:10]:
            print(f"   - {item['hero']}: {item['parsed_wr']:.1f}% WR ({item['parsed_games']} games) [Parsed]")
        if len(parsed_only) > 10:
            print(f"   ... and {len(parsed_only) - 10} more")
    
    # Calculate health score
    total_heroes = len(all_heroes)
    health_score = 0
    
    if total_heroes > 0:
        # Matching sources = 100% health
        # Discrepancies = -10% per discrepancy (capped at -50%)
        # Verified only = neutral (expected for heroes you haven't played recently)
        # Parsed only = neutral (expected for new heroes)
        
        discrepancy_penalty = min(len(discrepancies) * 10, 50)
        health_score = max(0, 100 - discrepancy_penalty)
    
    print("\n" + "=" * 80)
    print(f"🏥 HEALTH SCORE: {health_score:.0f}/100")
    
    if health_score >= 95:
        print("✅ Excellent - Data integrity is solid")
    elif health_score >= 90:
        print("✅ Good - Minor discrepancies detected")
    elif health_score >= 80:
        print("⚠️  Fair - Some discrepancies need investigation")
    else:
        print("❌ Poor - Significant discrepancies detected")
    
    if discrepancies:
        print(f"\n⚠️  ACTION REQUIRED: {len(discrepancies)} heroes have data discrepancies >5%")
        print("   These may indicate:")
        print("   - Sample bias in parsed matches")
        print("   - Outdated verified stats")
        print("   - Data entry errors")
        print("\n   Recommendation: Review these heroes and reconcile the data sources.")
    
    print("=" * 80)
    
    # Exit code based on health
    if health_score < 90:
        return 1  # Indicates issues found
    return 0  # Healthy

if __name__ == "__main__":
    sys.exit(validate_win_rate_sources())
