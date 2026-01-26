"""
Cursed Hollow Map Expert
Specializes in Tribute timing, Curse value extraction, and Boss control
"""

from .base_map_expert import BaseMapExpert
import json

class CursedHollowExpert(BaseMapExpert):
    """Expert agent for Cursed Hollow map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Cursed Hollow",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Cursed Hollow specific analysis prompt
        
        Focus Areas:
        - "Tribute Efficiency" (1/3 of a Curse)
        - "Boss Timing"
        - "Curse Value" (Structures destroyed during Curse)
        - "Golden Throws" (Dying before Tribute spawn)
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
        
        # Cursed Hollow specific logic involves "Curse Damage" or "Tribute Participation"
        # Since standard replays don't always track "Tributes Collected" perfectly in stats block,
        # we infer participation from teamfight presence during objective windows or specific event logs.
        # But for this expert, we'll focus on the 'mechanics' we can convert to prompt logic.
        
        # We can look for "TeamfightDamageTaken" or high "HeroDamage" relative to game time to infer combat participation.
        # But more specifically, let's look at "MercenaryCampCaptures" for Boss control.
        merc_captures = stats.get('MercenaryCampCaptures', 0)
        
        # Tribute Participation (Proxy): In most parsed replays, we rely on 'events' or 'objective' keys.
        # If not available, we use general engagement stats.
        
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
        
        prompt = f"""You are a Cursed Hollow tactical expert {mode_instruction}.

**MAP CONTEXT:**
Cursed Hollow is defined by TRIBUTE CADENCE and CURSE VALUE.
- **Tribute Efficiency**: Tributes spawn every ~2-3 minutes. Participation is non-negotiable (33% of a win condition).
- **Curse Value**: A Curse is useless if you don't push structures.
- **Boss Control**: The Boss is a "False Win Condition" unless taken *during* a Curse or to end the game. Taking it randomly is a "Throw Pit".

**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}  # Truncated for token efficiency

{gold_standard_prompt}

**YOUR ANALYSIS MUST:**
1. **Focus on Tribute Rotation**: Did the player rotate early? (Look at deaths/positioning if available in summary).
2. **Analyze Boss Calls**: (If MercCaptures > 0). Was it a "Throw Pit"?
3. **Calculate "Golden Throws"**: Dying 10-20 seconds before a Tribute spawn is a critical error.
4. **Lane Soak vs. Tribute**: You must soak *between* tributes, but never *during* them (unless giving 1/3 is strategic).

**OUTPUT FORMAT (JSON):**
{{
    "map_specific_metrics": {{
        "tribute_participation_grade": "A/B/C/D/F",
        "boss_control_grade": "A/B/C/D/F",
        "curse_value_assessment": "Did the team capitalize on curses?"
    }},
    "critical_mistake": "Single most impactful map-specific error (e.g. 'Late rotation to bottom Tribute at 12:04')",
    "win_condition": "How Tribute control determined the match outcome",
    "tactical_advice": [
        "Specific advice for Cursed Hollow rotations",
        "Boss timing rules",
        "Positioning for narrow Tribute choke points"
    ],
    "summary": "2-3 sentence summary focusing on Tribute/Curse dynamics"
}}
"""
        return prompt
