"""
Towers of Doom Map Expert
Specializes in Altar Control, Bell Tower Management, and Sapper Pressure
"""

from .base_map_expert import BaseMapExpert
import json

class TowersOfDoomExpert(BaseMapExpert):
    """Expert agent for Towers of Doom map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Towers of Doom",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Towers of Doom specific analysis prompt
        
        Focus Areas:
        - "Protected Core": The core cannot be attacked directly. Strategic objective control is mandatory.
        - "The Kill Box": Controlling the bottom lane Bell Towers creates a kill zone.
        - "Sapper Pressure": Mercenaries (Sappers) deal direct core damage. 
        - "Altar Trading": Giving up one altar to secure two (or structure advantage) is a key macro decision.
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
        
        stats = user_player.get('stats', {})
        
        # Towers Metrics
        # "Structure Damage" is huge because taking Bell Towers increases Altar damage.
        siege_dmg = stats.get('SiegeDamage', 0)
        
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
        
        prompt = f"""You are a Towers of Doom tactical expert {mode_instruction}.

**MAP CONTEXT:**
Towers of Doom is a CONTROL map where the Core is protected.
- **Altars**: Spawn periodically. Channeling them damages the enemy core.
- **Bell Towers**: Capturing enemy towers increases Altar damage. 
- **The "Kill Box"**: Controlling enemy bottom towers creates a choke point.
- **Sappers (Mercs)**: They are "Walking Core Damage". Escorting them is a win condition.
- **Boss**: The Headless Horseman deals massive core damage (4 shots).

**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}  # Truncated for token efficiency

{gold_standard_prompt}

**YOUR ANALYSIS MUST:**
1. **Analyze Altar Control**: Did the team trade effectively (give 1 to get 2)?
2. **Bell Tower Aggression**: Did they take enemy structures to increase shot count?
3. **Sapper Usage**: Were Sappers escorted to the death zone?
4. **Boss Calls**: Was the Headless Horseman taken at the right time?

**OUTPUT FORMAT (JSON):**
{{
    "map_specific_metrics": {{
        "altar_control_grade": "A/B/C/D/F",
        "tower_aggression_rating": "Defensive vs Offensive",
        "sapper_pressure_grade": "Did Sappers hit the core?"
    }},
    "critical_mistake": "Single most impactful macro error (e.g. 'Fighting 4v5 for a bottom altar while losing Top Fort')",
    "win_condition": "How Altar/Tower control determined the match outcome",
    "tactical_advice": [
        "Specific advice for Altar trading",
        "Sapper escort timing",
        "When to take the Boss"
    ],
    "summary": "2-3 sentence summary focusing on Altar economy and Structure control"
}}
"""
        return prompt
