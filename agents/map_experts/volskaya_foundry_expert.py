"""
Volskaya Foundry Map Expert
Specializes in Protector Control, Gunner/Driver Synergy, and Conveyor Belt Plays
"""

from .base_map_expert import BaseMapExpert
import json

class VolskayaFoundryExpert(BaseMapExpert):
    """Expert agent for Volskaya Foundry map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Volskaya Foundry",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=None
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Volskaya Foundry specific analysis prompt
        
        Focus Areas:
        - "Protector Control": Capturing the objective
        - "Pilot Synergy": Gunner/Driver coordination
        - "Conveyor Belt": Using the map mechanic for rotations
        - "Protector Value": Structure damage vs team fight usage
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
        
        prompt = f"""You are a Volskaya Foundry tactical expert {mode_instruction}.

**MAP CONTEXT:**
Volskaya Foundry is a CONTROL map with a two-person vehicle objective.
- **The Protector**: Requires a Gunner and Driver. Coordination is critical.
- **Conveyor Belt**: Provides fast rotations between lanes.
- **The Pitfall**: Using the Protector for team fights instead of structure damage.
- **Optimal Play**: Get the Protector, push a lane hard, then rotate using conveyor.

**MATCH DATA:**
{json.dumps(clean_match_data, indent=2)[:2000]}  # Truncated for token efficiency


**YOUR ANALYSIS MUST:**
1. **Protector Control**: Did the team secure the objective?
2. **Pilot Coordination**: Did Gunner/Driver work together effectively?
3. **Protector Value**: Was it used for structures or wasted on fights?
4. **Conveyor Usage**: Did the team use the belt for rotations?

**OUTPUT FORMAT (JSON):**
{{
    "map_specific_metrics": {{
        "protector_control_grade": "A/B/C/D/F",
        "pilot_synergy_rating": "Excellent/Good/Poor",
        "protector_value": "Structure Focus/Fight Focus/Wasted"
    }},
    "critical_mistake": "Single most impactful map-specific error",
    "win_condition": "How Protector usage determined the outcome",
    "tactical_advice": [
        "Protector capture strategy",
        "Gunner/Driver coordination tips",
        "Conveyor belt rotation advice"
    ],
    "summary": "2-3 sentence summary focusing on Protector control and value"
}}

IMPORTANT: Return raw JSON only. No markdown formatting, no code blocks. Just the JSON object.
"""
        return prompt
