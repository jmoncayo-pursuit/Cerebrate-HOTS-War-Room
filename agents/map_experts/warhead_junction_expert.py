"""
Warhead Junction Map Expert
Specializes in Nuke Economy, Global Rotation, and Boss Pit Control
"""

from .base_map_expert import BaseMapExpert
import json

class WarheadJunctionExpert(BaseMapExpert):
    """Expert agent for Warhead Junction map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Warhead Junction",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Warhead Junction specific analysis prompt
        
        Focus Areas:
        - "Nuke Economy": Collecting vs. Using vs. Losing (Dying with Nukes).
        - "Global Pressure": This is a large map; global heroes (Falstad, Dehaka) and movement speed matter.
        - "Boss Control": There are two bosses. Taking them safely is a win condition.
        - "Split Push": The map size encourages split pushing.
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
        
        # Warhead Specific Metrics
        # Nuke damage to structures is a key metric if trackable.
        # Otherwise, "TimeAlive" with "HeroDamage" allows inferring skirmish effectiveness.
        
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
        
        prompt = f"""You are a Warhead Junction tactical expert {mode_instruction}.

**MAP CONTEXT:**
Warhead Junction is a MACRO and GLOBAL map.
- **Nukes**: Tactical weapons. Do not hoard them. Use them to break forts or zone objectives.
- **Map Size**: It is huge. Rotations take forever. "Global" heroes (Falstad, Dehaka, Brightwing) are S-Tier.
- **The Bosses**: The "Swarm Hosts" bosses are strong but risky. Throw pits are common.
- **The Golden Rule**: Never die with a Nuke. It passes to the enemy.

**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}  # Truncated for token efficiency

{gold_standard_prompt}

**YOUR ANALYSIS MUST:**
1. **Analyze Nuke Usage**: (If discernible). Did the team use nukes effectively or die with them?
2. **Evaluate Global Presence**: Did the team draft/use global mobility?
3. **Boss Control**: Were bosses taken to end the game or pressure lanes?
4. **Lane Pressure**: Was the map pushed evenly?

**OUTPUT FORMAT (JSON):**
{{
    "map_specific_metrics": {{
        "nuke_efficiency_grade": "A/B/C/D/F",
        "global_pressure_rating": "How well did they use the map size?",
        "boss_control_grade": "Throw pit or Win condition?"
    }},
    "critical_mistake": "Single most impactful macro error (e.g. 'Dying with a Nuke at Bot Boss')",
    "win_condition": "How Nuke/Boss pressure determined the match outcome",
    "tactical_advice": [
        "Specific advice for Nuke targeting",
        "Rotation paths for large maps",
        "When to force Boss vs. Split Push"
    ],
    "summary": "2-3 sentence summary focusing on Nuke economy and Macro pressure"
}}
"""
        return prompt
