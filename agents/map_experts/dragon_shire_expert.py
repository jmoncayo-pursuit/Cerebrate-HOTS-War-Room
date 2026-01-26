"""
Dragon Shire Map Expert
Specializes in Shrine Control, Dragon Knight Rotation, and Triangle Control
"""

from .base_map_expert import BaseMapExpert
import json

class DragonShireExpert(BaseMapExpert):
    """Expert agent for Dragon Shire map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Dragon Shire",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Dragon Shire specific analysis prompt
        
        Focus Areas:
        - "Triangle Control": Top/Mid bridge rotation.
        - "Anchor Plays": Bot lane 1v1 matchup importance.
        - "Dragon Knight Value": Structure damage vs. wasted time.
        - "Shrine Uptime": Duration of shrine control.
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
        
        # Dragon Shire Metrics
        # Objective time is critical
        game_time = stats.get('TimeAlive', 600) + stats.get('TimeSpentDead', 0)
        
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
        
        prompt = f"""You are a Dragon Shire tactical expert {mode_instruction}.

**MAP CONTEXT:**
Dragon Shire is a ROTATION map defined by the "Triangle" (Top/Mid) and the "Island" (Bot).
- **The Triangle**: 4-man rotation between Top and Mid to clear waves and control the Moon Shrine.
- **The Island**: The Bot Laner must win the duel or safely soak. 
- **The Dragon Knight**: A siege engine. Chasing heroes with the DK is a critical failure.
- **Stall Tactics**: Controlling one shrine indefinitely can starve the enemy of the objective.

**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}  # Truncated for token efficiency

{gold_standard_prompt}

**YOUR ANALYSIS MUST:**
1. **Analyze Rotation**: Did the team control the Top/Mid bridge or get split?
2. **Bot Lane Duel**: Who won the bottom shrine control?
3. **Dragon Knight Usage**: If taken, was it used for structure damage?
4. **Win Condition**: Map control > Kills on this map.

**OUTPUT FORMAT (JSON):**
{{
    "map_specific_metrics": {{
        "rotation_control_grade": "A/B/C/D/F",
        "bot_lane_dominance": "Who won the island?",
        "dk_value_assessment": "Structure damage efficiency"
    }},
    "critical_mistake": "Single most impactful rotation error (e.g. 'Leaving Top Shrine unguarded at 6:30')",
    "win_condition": "How shrine control determined the match outcome",
    "tactical_advice": [
        "Specific advice for Triangle rotation",
        "Bot lane matchup tips",
        "Dragon Knight piloting instructions"
    ],
    "summary": "2-3 sentence summary focusing on Triangle control and DK usage"
}}
"""
        return prompt
