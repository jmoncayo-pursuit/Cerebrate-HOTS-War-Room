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
    
    # Extract summary text and critical mistake (Safe-load to handle None values)
    from api.logger import ColoredLogger
    
    summary_text = summary.get('summary') or ''
    critical_mistake = summary.get('critical_mistake') or ''
    win_condition = summary.get('win_condition') or ''
    
    ColoredLogger.info(f"DEBUG: Validating summary for {hero}. Length: {len(summary_text)}", "HOOKS")
    
    issues = []
    
    # Check 1: Ensure critical mistake exists and is meaningful
    if not critical_mistake or len(critical_mistake.strip()) < 20:
        issues.append("Missing or too short critical_mistake field")
    
    # Check 1b: Reject "None detected" or "No mistakes" responses
    critical_mistake_lower = critical_mistake.lower().strip()
    none_patterns = [
        "none detected", "no mistakes", "no mistake", "none found",
        "no critical mistake", "no errors", "no error", "perfect game"
    ]
    if any(pattern in critical_mistake_lower for pattern in none_patterns):
        issues.append("Critical mistake cannot be 'None detected'. Even in dominant wins, identify what prevented carrying harder (opportunity costs, missed rotations, suboptimal positioning windows).")
    
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
    
    # Whitelist for legitimate non-hero kills/deaths
    allowed_non_heroes = [
        'stats', 'assisted', 'unknown', 'n/a', 'multiple unknown', 
        'enemy hero', 'enemy', 'minions', 'minion', 'mercenary', 
        'mercenaries', 'mercs', 'structure', 'structures', 
        'environment', 'boss', 'objective', 'undetermined', 'various',
        'unrecorded', 'unknown terminal', 'none'
    ]

    # Check victims in kills
    for kill in summary.get('areas_for_improvement', []):
        if not isinstance(kill, dict): continue
        if kill.get('title') == "Your Kills":
            for item in kill.get('items', []):
                if not isinstance(item, dict): continue
                victim = (item.get('victim') or '').lower()
                if not victim: continue
                if victim not in valid_heroes and victim not in allowed_non_heroes:
                    issues.append(f"Hallucination detected: Hero '{victim}' was not in this match.")
    
    # Check killers in deaths
    for death in summary.get('areas_for_improvement', []):
        if not isinstance(death, dict): continue
        if death.get('title') == "Deaths":
            for item in death.get('items', []):
                if not isinstance(item, dict): continue
                killer = (item.get('killer') or '').lower()
                if not killer: continue
                if killer not in valid_heroes and killer not in allowed_non_heroes:
                    issues.append(f"Hallucination detected: Hero '{killer}' was not in this match.")

    # Check 6: Map Hallucinations (Expanded)
    map_name = match_data.get('map', '').lower()
    analysis_lowered = (summary_text + " " + critical_mistake).lower()
    
    map_hallucinations = {
        'dragon shire': ['boss pit', 'payload', 'punisher', 'immortal'],
        'hanamura': ['tribute', 'boss pit', 'punisher', 'immortal', 'cavalry'],
        'tomb of the spider queen': ['tribute', 'payload', 'cavalry', 'immortal', 'punisher'],
        'infernal shrines': ['tribute', 'payload', 'cavalry', 'boss pit'],
        'battlefield of eternity': ['tribute', 'payload', 'cavalry', 'boss pit', 'punisher'],
        'alterac pass': ['tribute', 'payload', 'punisher', 'immortal'],
        'cursed hollow': ['payload', 'cavalry', 'punisher', 'immortal'],
        'towers of doom': ['tribute', 'payload', 'cavalry', 'punisher', 'immortal']
    }
    
    for check_map, terms in map_hallucinations.items():
        if check_map in map_name:
            for term in terms:
                if term in analysis_lowered:
                    issues.append(f"Hallucination detected: {map_name.title()} has no '{term}'.")

    # Check 7: Stitches Hook Integrity
    if 'stitches' in hero.lower():
        if "0 hooks thrown" in analysis_lowered or "complete absence of tactical application" in analysis_lowered:
            issues.append("Invalid Data: Stitches analysis claims 0 Hooks. Check parser integrity.")

    # Check 8: Ban vague, generic root-cause language
    banned_phrases = [
        "critical breakdown in positional awareness",
        "critical breakdown in either positional awareness",
        "in either positional awareness, target prioritization, or an inability to disengage",
        "in positional awareness, target prioritization, or an inability to disengage",
        "breakdown in positional awareness",
        "inability to disengage from sustained damage",
        "multiplicative failure",
        "multiplicative effect on the loss",
        "room for improvement",
        "failed to capitalize",
        "needs to improve"
    ]
    for phrase in banned_phrases:
        if phrase in analysis_lowered:
            issues.append(f"Vague root-cause language detected ('{phrase}'). Use concrete, data-backed patterns instead (e.g., 4/5 deaths outnumbered).")

    # Check 9: Ban technical jargon — use plain language instead
    jargon_terms = [
        'theoretical value delta', 'unified throughput', 'pure soak',
        'force multiplier', 'additive link', 'macro anchor', 'attrition scaling',
        'resource supremacy', 'macroeconomic masterclass', 'synergistic value',
        'tactical delta', 'value differential'
    ]
    found_jargon = [term for term in jargon_terms if term in analysis_lowered]
    if found_jargon:
        issues.append(f"Jargon detected ({found_jargon}). Use plain language: 'the main problem', 'healing/damage output', 'lane XP', 'your impact', etc.")

    # Check 10: GOLD STANDARD - Specific Numbers in summary
    numbers_pattern = r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b'
    found_numbers = re.findall(numbers_pattern, summary_text)
    if len(found_numbers) < 2:
        issues.append("Summary lacks specific numerical data. Cite exact XP, Healing, or Siege numbers from the stats.")

    # Check 11: GOLD STANDARD - Verbosity (Sentences)
    sentences = [s for s in re.split(r'[.!?]+', summary_text) if len(s.strip()) > 10]
    if len(sentences) < 3:
        issues.append(f"Summary too brief ({len(sentences)} sentences). Must be a detail-heavy 3-5 sentence audit.")
        
    # Check 12: Anti-AI Pleasantries
    pleasantries = [
        "here is the analysis",
        "in conclusion",
        "to summarize",
        "overall,",
        "as an ai",
        "as a tactical analyst",
        "let's break down",
        "delving into the data",
        "it is clear that"
    ]
    for p in pleasantries:
        if p in analysis_lowered:
            issues.append(f"AI filler detected ('{p}'). Start directly with the tactical audit, no intros or outros.")
    
    if issues:
        feedback = "Summary quality issues:\n" + "\n".join(f"- {issue}" for issue in issues)
        return HookResponse.deny(
            feedback,
            "Quality validation failed - regenerate with corrections"
        )
    
    return HookResponse.allow("All quality checks passed")
