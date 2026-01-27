"""
Infernal Shrines Map Expert
Specializes in Shrine Control, Waveclear Efficiency, and Punisher Capitalization
"""

from .base_map_expert import BaseMapExpert
import json

class InfernalShrinesExpert(BaseMapExpert):
    """Expert agent for Infernal Shrines map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Infernal Shrines",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Infernal Shrines specific analysis prompt
        
        Focus Areas:
        - "Shrine Cadence": Rotating to Shrines on time.
        - "Waveclear Efficiency": This map demands high waveclear for the objective (40 minions).
        - "Punisher Value": Structures taken with the Punisher vs. Defending against it.
        - "Greed vs. Soak": Fighting over a lost shrine vs soaking to catch up in XP.
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
        
        # Infernal Shrines Metrics
        # "SiegeDamage" is often a proxy for Waveclear on the objective if high during objective phases.
        siege_dmg = stats.get('SiegeDamage', 0)
        hero_dmg = stats.get('HeroDamage', 0)
        
        # Check for specific "Shrine" related stats if available in KV, otherwise infer from Siege
        # Note: Some replay parsers map "DamageDoneToShrineMinions"
        
        # Get gold standards (DISABLED temporarily to prevent Markdown hallucinations from legacy data)
        # gold_standards = self._get_map_gold_standards(limit=2)
        gold_standard_prompt = ""
        # if gold_standards:
        #     gold_standard_prompt = "\n**FEW-SHOT GOLD STANDARD EXAMPLES (CRITICAL - MATCH THIS QUALITY):**\n"
        #     for i, gs in enumerate(gold_standards):
        #         gold_standard_prompt += f"### Example {i+1} ({gs['map_name']} {gs['result']})\n"
        #         gold_standard_prompt += f"Verdict: {gs['verdict']}\n"
        #         gold_standard_prompt += f"Summary: {gs['summary']}\n\n"
        
        # Sanitize match data to remove previous failed analysis (which triggers model fallback)
        clean_match_data = match_data.copy()
        if 'analysis' in clean_match_data:
            del clean_match_data['analysis']

        is_general_query = result == "STRATEGIC_PLANNING"
        mode_instruction = "providing a comprehensive map strategy and win condition breakdown" if is_general_query else f"analyzing a {result} match"
        
        prompt = f"""You are an Infernal Shrines tactical expert {mode_instruction}.

**MAP CONTEXT:**
Infernal Shrines is a WAVECLEAR and CONTROL map.
- **The Objective**: Killing 40 Guardians is a race. High AoE damage is critical.
- **The Punisher**: Focuses heroes first. Defense requires "baiting" it over the gate. Offense requires pushing *with* it.
- **The Pitfall**: Committing 5 heroes to a shrine for 2 minutes while losing all 3 lanes of XP. Sometimes giving the first Punisher to soak Level 10 is the winning play.

**MATCH DATA:**
{json.dumps(clean_match_data, indent=2)[:2000]}  # Truncated for token efficiency

{gold_standard_prompt}

**YOUR ANALYSIS MUST:**
1. **Evaluate Waveclear**: Did the hero contribute enough Siege/AoE damage? (Siege Damage: {siege_dmg}).
2. **Punisher Defense**: If lost, did the team defend inside gates or get caught out?
3. **Analyze "Shrine Greed"**: Identify if the team fought for a lost shrine instead of soaking.
4. **Win Condition**: Punisher pushes are the primary win condition, but XP soak is the fuel.

**OUTPUT FORMAT (JSON):**
{{
    "map_specific_metrics": {{
        "shrine_control_grade": "A/B/C/D/F",
        "punisher_capitalization": "Did the team get fort value?",
        "waveclear_efficiency": "Assessment of clear speed"
    }},
    "critical_mistake": "Single most impactful map-specific error (e.g. 'Fighting 3v5 at North Shrine at 4:30')",
    "win_condition": "How Shrine control determined the match outcome",
    "tactical_advice": [
        "Specific advice for Infernal Shrines rotation",
        "How to defend against the specific Punisher type (Arcane/Mortar/Frozen)",
        "Soak prioritization vs Objective"
    ],
    "summary": "2-3 sentence summary focusing on Shrine dynamics and Punisher value"
}}

IMPORTANT: Return raw JSON only. No markdown formatting, no code blocks. Just the JSON object.
"""
        return prompt
