"""
Context Injector Hook
BeforeAnalysis hook that injects recent match history and player stats
"""

from typing import Dict, Any
from agents.hooks_manager import HookResponse


def context_injector_hook(data: Dict[str, Any]) -> HookResponse:
    """
    Inject recent match context before analysis
    
    Args:
        data: Contains match_data, db_manager
    
    Returns:
        HookResponse with modified data including recent_matches
    """
    db_manager = data.get('db_manager')
    match_data = data.get('match_data', {})
    
    if not db_manager:
        return HookResponse.allow("No database manager available")
    
    hero = match_data.get('hero')
    if not hero:
        return HookResponse.allow("No hero specified")
    
    try:
        # Get last 5 matches
        recent_matches = db_manager.get_matches(limit=5, include_details=True)
        
        if not recent_matches:
            return HookResponse.allow("No recent matches found")
        
        # Calculate stats
        total_matches = len(recent_matches)
        wins = sum(1 for m in recent_matches if m.get('result') == 'WIN')
        win_rate = round((wins / total_matches) * 100, 1) if total_matches > 0 else 0
        
        # Find hero-specific stats
        hero_matches = [m for m in recent_matches if m.get('hero') == hero]
        hero_wins = sum(1 for m in hero_matches if m.get('result') == 'WIN')
        hero_win_rate = round((hero_wins / len(hero_matches)) * 100, 1) if hero_matches else 0
        
        # Build context string
        context = f"""
RECENT PERFORMANCE CONTEXT:
- Last {total_matches} matches: {wins}W-{total_matches - wins}L ({win_rate}% WR)
- {hero} performance: {len(hero_matches)} games, {hero_win_rate}% WR
"""
        
        # Add to match data
        modified_data = data.copy()
        modified_data['match_data'] = match_data.copy()
        modified_data['match_data']['recent_context'] = context
        modified_data['match_data']['recent_matches_count'] = total_matches
        modified_data['match_data']['overall_win_rate'] = win_rate
        
        return HookResponse.modify(
            modified_data, 
            f"Injected {total_matches} recent matches context"
        )
    
    except Exception as e:
        return HookResponse.allow(f"Context injection failed: {str(e)}")
