"""
Tomb of the Spider Queen Map Expert
Specializes in Gem Collection, Turn-In Timing, and Webweaver Pressure
"""

from .base_map_expert import BaseMapExpert
import json

class TombOfTheSpiderQueenExpert(BaseMapExpert):
    """Expert agent for Tomb of the Spider Queen map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Tomb of the Spider Queen",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Tomb of the Spider Queen specific analysis prompt
        
        Focus Areas:
        - "Gem Collection": Waveclear and jungle camp efficiency
        - "Turn-In Safety": Not dying with gems
        - "Webweaver Timing": When to turn in for maximum pressure
        - "Altar Denial": Preventing enemy turn-ins
        """
        # Get player stats
        players = match_data.get('players', [])
        user_hero = match_data.get('hero', 'Unknown')
        result = match_data.get('result', 'UNKNOWN')
        
        # Find user player
        user_player = None
        for p in players:
            if p.get('hero') == user_hero or p.get('name') == context.get('player_name'):
                user_player = p
                break
        
        if not user_player:
            user_player = players[0] if players else {}
        
        # Sanitize match data
        clean_match_data = match_data.copy()
        if 'analysis' in clean_match_data:
            del clean_match_data['analysis']

        is_general_query = result == "STRATEGIC_PLANNING"
        mode_instruction = "providing a comprehensive map strategy and win condition breakdown" if is_general_query else f"analyzing a {result} match"
        
        prompt = f"""You are a Tomb of the Spider Queen tactical expert {mode_instruction}.

**MAP CONTEXT:**
Tomb of the Spider Queen is a GEM COLLECTION map with tight lanes.
- **The Objective**: Collect 50 gems to summon Webweavers that push all lanes.
- **The Pitfall**: Dying with gems. Each death drops gems for the enemy.
- **Turn-In Strategy**: Turn in when safe, not when greedy. 40+ gems is a target on your back.
- **Altar Denial**: Blocking enemy turn-ins is as valuable as collecting gems.

**MATCH DATA:**
{json.dumps(clean_match_data, indent=2)[:2000]}  # Truncated for token efficiency


**YOUR ANALYSIS MUST:**
1. **Gem Economy**: Did the team collect efficiently without dying?
2. **Turn-In Safety**: Were turn-ins made at safe times?
3. **Webweaver Value**: Did the Webweavers get structure damage?
4. **Altar Control**: Did the team deny enemy turn-ins?

**OUTPUT FORMAT (JSON):**
{{
    "map_specific_metrics": {{
        "gem_collection_efficiency": "Excellent/Good/Poor",
        "turn_in_safety_rating": "Safe/Risky/Reckless",
        "webweaver_value": "High/Medium/Low"
    }},
    "critical_mistake": "Single most impactful map-specific error (e.g. 'Died with 45 gems at 8:30')",
    "win_condition": "How gem economy determined the outcome",
    "tactical_advice": [
        "Gem collection optimization",
        "Turn-in timing recommendations",
        "Altar denial strategies"
    ],
    "summary": "2-3 sentence summary focusing on gem economy and turn-in discipline"
}}

IMPORTANT: Return raw JSON only. No markdown formatting, no code blocks. Just the JSON object.
"""
        return prompt
