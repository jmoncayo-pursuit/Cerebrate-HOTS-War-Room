"""
Battlefield of Eternity Map Expert
Specializes in Immortal Racing, Damage Optimization, and Shield Management
"""

from .base_map_expert import BaseMapExpert
import json

class BattlefieldOfEternityExpert(BaseMapExpert):
    """Expert agent for Battlefield of Eternity map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Battlefield of Eternity",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Battlefield of Eternity specific analysis prompt
        
        Focus Areas:
        - "Immortal Racing": Damage output during objective phases
        - "Shield Value": Converting Immortal shield into structure damage
        - "Defensive Positioning": Defending against enemy Immortal
        - "Sustain vs Burst": Team composition for prolonged fights
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
        hero_dmg = stats.get('HeroDamage', 0)
        
        # Sanitize match data
        clean_match_data = match_data.copy()
        if 'analysis' in clean_match_data:
            del clean_match_data['analysis']

        is_general_query = result == "STRATEGIC_PLANNING"
        mode_instruction = "providing a comprehensive map strategy and win condition breakdown" if is_general_query else f"analyzing a {result} match"
        
        prompt = f"""You are a Battlefield of Eternity tactical expert {mode_instruction}.

**MAP CONTEXT:**
Battlefield of Eternity is a RACE map with two-lane structure.
- **The Objective**: Two Immortals spawn. The team that kills their Immortal first gets it as a pushing unit.
- **The Shield**: The Immortal's shield value = damage dealt to enemy Immortal. Higher shield = more structure damage.
- **The Pitfall**: Fighting the enemy team instead of racing the Immortal. Sustained damage > burst kills here.
- **Defensive Strategy**: Kiting the enemy Immortal, not face-tanking it.

**MATCH DATA:**
{json.dumps(clean_match_data, indent=2)[:2000]}  # Truncated for token efficiency


**YOUR ANALYSIS MUST:**
1. **Evaluate Immortal Damage**: Did the hero contribute enough damage? (Hero Damage: {hero_dmg}).
2. **Shield Conversion**: Did the team's Immortal get value, or was it defended well?
3. **Race vs Fight**: Did the team prioritize racing or fighting the enemy?
4. **Sustain Composition**: Did the team have enough sustain for prolonged objective fights?

**OUTPUT FORMAT (JSON):**
{{
    "map_specific_metrics": {{
        "immortal_damage_contribution": "High/Medium/Low",
        "shield_value_rating": "Excellent/Good/Poor",
        "race_vs_fight_decision": "Correct/Greedy"
    }},
    "critical_mistake": "Single most impactful map-specific error",
    "win_condition": "How Immortal racing determined the outcome",
    "tactical_advice": [
        "Advice for Immortal damage optimization",
        "Defensive positioning tips",
        "Team composition recommendations"
    ],
    "summary": "2-3 sentence summary focusing on Immortal racing and shield value"
}}

IMPORTANT: Return raw JSON only. No markdown formatting, no code blocks. Just the JSON object.
"""
        return prompt
