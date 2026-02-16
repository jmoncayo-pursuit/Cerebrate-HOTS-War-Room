"""
Summary Validator Hook
AfterAnalysis hook that validates summary quality
"""

import re
from typing import Dict, Any
from agents.hooks_manager import HookResponse


def summary_validator_hook(data: Dict[str, Any]) -> HookResponse:
    """
    Validate summary quality after analysis
    
    Checks for:
    - Hero-specific distances (not abstract units)
    - Critical mistake present
    - Win condition is player-focused
    
    Args:
        data: Contains summary, match_data
    
    Returns:
        HookResponse: deny if quality standards not met
    """
    summary = data.get('summary', {})
    match_data = data.get('match_data', {})
    hero = match_data.get('hero', 'Unknown')
    
    if not summary:
        return HookResponse.deny(
            "No summary generated",
            "Summary generation failed - empty response"
        )
    
    # Extract summary text and critical mistake
    summary_text = summary.get('summary', '')
    critical_mistake = summary.get('critical_mistake', '')
    win_condition = summary.get('win_condition', '')
    
    issues = []
    
    # Check 1: Ensure critical mistake exists
    if not critical_mistake or len(critical_mistake.strip()) < 20:
        issues.append("Missing or too short critical_mistake field")
    
    # Check 2: Look for abstract distance units (bad)
    abstract_units_pattern = r'\b\d+\s*units?\b'
    if re.search(abstract_units_pattern, summary_text + critical_mistake, re.IGNORECASE):
        issues.append("Found abstract 'units' - use hero-specific distances (e.g., '3x Blizzard cast range')")
    
    # Check 3: Ensure win condition is player-focused
    enemy_focused_keywords = ['enemy team', 'they won', 'their strategy', 'opponents']
    player_focused_keywords = ['you could have', 'your positioning', 'stay within', 'don\'t engage']
    
    if win_condition:
        enemy_count = sum(1 for kw in enemy_focused_keywords if kw.lower() in win_condition.lower())
        player_count = sum(1 for kw in player_focused_keywords if kw.lower() in win_condition.lower())
        
        if enemy_count > player_count:
            issues.append("Win condition is enemy-focused - should be player-actionable advice")
    
    # Check 4: Ensure hero name is mentioned (context awareness)
    if hero != 'Unknown' and hero.lower() not in (summary_text + critical_mistake).lower():
        issues.append(f"Hero name '{hero}' not mentioned - summary lacks context")

    # Check 5: Anti-Hallucination - Hero mismatch
    all_players = match_data.get('players', [])
    valid_heroes = [p.get('hero', '').lower() for p in all_players]
    
    # Check victims in kills
    for kill in summary.get('areas_for_improvement', []):
        if kill.get('title') == "Your Kills":
            for item in kill.get('items', []):
                victim = item.get('victim', '').lower()
                if victim not in valid_heroes and victim not in ['stats', 'assisted', 'unknown']:
                    issues.append(f"Hallucination detected: Hero '{victim}' was not in this match.")
    
    # Check killers in deaths
    for death in summary.get('areas_for_improvement', []):
        if death.get('title') == "Deaths":
            for item in death.get('items', []):
                killer = item.get('killer', '').lower()
                if killer not in valid_heroes and killer not in ['unknown', 'environment', 'structure']:
                    issues.append(f"Hallucination detected: Hero '{killer}' was not in this match.")

    # Check 6: Map Hallucinations
    map_name = match_data.get('map', '').lower()
    if 'dragon shire' in map_name and 'boss pit' in (summary_text + critical_mistake).lower():
        issues.append("Hallucination detected: Dragon Shire has no 'Boss Pit'.")
    if 'hanamura' in map_name and 'tribute' in (summary_text + critical_mistake).lower():
        issues.append("Hallucination detected: Hanamura has no Tributes.")
    
    # Check 7: Stitches Hook Integrity
    if 'stitches' in hero.lower():
        analysis_text = (summary_text + critical_mistake).lower()
        if "0 hooks thrown" in analysis_text or "complete absence of tactical application" in analysis_text:
            issues.append("Invalid Data: Stitches analysis claims 0 Hooks. Check parser integrity.")
    
    if issues:
        feedback = "Summary quality issues:\n" + "\n".join(f"- {issue}" for issue in issues)
        return HookResponse.deny(
            feedback,
            "Quality validation failed - regenerate with corrections"
        )
    
    return HookResponse.allow("All quality checks passed")
