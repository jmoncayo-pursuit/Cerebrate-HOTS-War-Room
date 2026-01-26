"""
Sky Temple Map Expert
Specializes in Temple Rotation, Boss Control, and Split Push Timing
"""

from .base_map_expert import BaseMapExpert
import json

class SkyTempleExpert(BaseMapExpert):
    """Expert agent for Sky Temple map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Sky Temple",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Sky Temple specific analysis prompt
        
        Focus Areas:
        - "Temple Rotation": Spawn order is predictable (Top/Mid -> Bot -> etc.).
        - "Boss Control": The boss is a throw pit. Taking it safely is rare.
        - "Structure Trading": Trading a fort for shots is often worth it.
        - "Split Push": Pushing during temple phases is high value.
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
        
        # Get gold standards
        gold_standards = self._get_map_gold_standards(limit=2)
        gold_standard_prompt = ""
        if gold_standards:
            gold_standard_prompt = "\n**FEW-SHOT GOLD STANDARD EXAMPLES (CRITICAL - MATCH THIS QUALITY):**\n"
            for i, gs in enumerate(gold_standards):
                gold_standard_prompt += f"### Example {i+1} ({gs['map']} {gs['result']})\n"
                gold_standard_prompt += f"Verdict: {gs['gold_verdict']}\n"
                gold_standard_prompt += f"Summary: {gs['gold_summary']}\n\n"
        
        is_general_query = result == "STRATEGIC_PLANNING"
        mode_instruction = "providing a comprehensive map strategy and win condition breakdown" if is_general_query else f"analyzing a {result} match"
        
        prompt = f"""You are a Sky Temple tactical expert {mode_instruction}.

**MAP CONTEXT:**
Sky Temple is a CONTROL map with predictable objectives.
- **Cycle 1**: Top + Mid Temples (Most important for XP lead).
- **Cycle 2**: Bot Temple alone.
- **The Boss**: A common throw pit. Only take when 2+ enemies are dead.
- **Strategy**: Holding 1 temple + soaking 2 lanes > Fighting 5v5 for both temples.

**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}  # Truncated for token efficiency

{gold_standard_prompt}

**YOUR ANALYSIS MUST:**
1. **Analyze Temple Control**: Did the team prioritize the right temples?
2. **Soak vs Fight**: Did they soak lanes during temple phases?
3. **Boss Calls**: Was the boss a throw or a win condition?
4. **Structure Trading**: Did they trade forts effectively?

**OUTPUT FORMAT (JSON):**
{{
    "map_specific_metrics": {{
        "temple_rotation_grade": "A/B/C/D/F",
        "boss_decision_rating": "Safe / Risky / Throw",
        "soak_during_objective": "Yes / No"
    }},
    "critical_mistake": "Single most impactful macro error",
    "win_condition": "How temple mechanics determined the outcome",
    "tactical_advice": [
        "Advice for temple rotation",
        "Boss timing tips",
        "Split push recommendations"
    ],
    "summary": "2-3 sentence summary focusing on Temple control and Soak efficiency"
}}
"""
        return prompt
