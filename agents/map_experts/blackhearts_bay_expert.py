"""
Blackheart's Bay Map Expert
Specializes in coin economy analysis and turn-in timing
"""

from .base_map_expert import BaseMapExpert
import json

class BlackheartsBayExpert(BaseMapExpert):
    """Expert agent for Blackheart's Bay map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Blackheart's Bay",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Blackheart's Bay specific analysis prompt
        
        Focus Areas:
        - Coin collection efficiency
        - Turn-in timing
        - Coin economy battle
        - Deaths while holding coins
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
        kv_stats = user_player.get('kv_stats', {})
        all_stats = {**kv_stats, **stats}
        
        # Coin economy metrics
        coins_collected = all_stats.get('BlackheartDoubloonsCollected', 0)
        coins_turned_in = all_stats.get('BlackheartDoubloonsTurnedIn', 0)
        coins_likely_dropped = max(0, coins_collected - coins_turned_in)
        
        # Calculate enemy coin totals (approximate)
        enemy_coins = 0
        user_team = user_player.get('team', 0)
        for p in players:
            if p.get('team') != user_team:
                p_stats = {**p.get('kv_stats', {}), **p.get('stats', {})}
                enemy_coins += p_stats.get('BlackheartDoubloonsCollected', 0)
        
        # Get gold standards
        gold_standards = self._get_map_gold_standards(limit=2)
        gold_standard_prompt = ""
        if gold_standards:
            gold_standard_prompt = "\n**FEW-SHOT GOLD STANDARD EXAMPLES (CRITICAL - MATCH THIS QUALITY):**\n"
            for i, gs in enumerate(gold_standards):
                gold_standard_prompt += f"### Example {i+1} ({gs['map']} {gs['result']})\n"
                gold_standard_prompt += f"Verdict: {gs['gold_verdict']}\n"
                gold_standard_prompt += f"Summary: {gs['gold_summary']}\n\n"
        
        # Role-based coin targets
        hero_role = self._infer_hero_role(user_hero)
        coin_target = 3 if hero_role in ['healer', 'tank'] else 5
        
        is_general_query = result == "STRATEGIC_PLANNING"
        mode_instruction = "providing a comprehensive map strategy and win condition breakdown" if is_general_query else f"analyzing a {result} match"
        
        prompt = f"""You are a Blackheart's Bay tactical expert {mode_instruction}.

**MAP CONTEXT:**
Blackheart's Bay is a COIN ECONOMY map. The win condition is controlling coin collection and turn-in timing, NOT just teamfights or lane soak.

**COIN ECONOMY METRICS:**
- Player ({user_hero}): {coins_collected} coins collected, {coins_turned_in} coins turned in
- Likely Dropped: {coins_likely_dropped} coins (died while holding)
- Enemy Team Total: ~{enemy_coins} coins collected
- Coin Target for {hero_role}: {coin_target}+ coins (you collected {coins_collected})
- Coin Efficiency: {(coins_turned_in / coins_collected * 100) if coins_collected > 0 else 0:.1f}%

**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}  # Truncated for token efficiency

{gold_standard_prompt}

**YOUR ANALYSIS MUST:**
1. **PRIORITIZE COIN ECONOMY** over lane soak or teamfight stats
2. **Identify coin collection failures**: If player collected < {coin_target} coins, this IS the primary win condition failure
3. **Analyze turn-in timing**: Did player turn in before objective spawns? Did they hold coins too long?
4. **Death analysis**: If coins_likely_dropped > 0, analyze deaths while holding coins as critical mistakes
5. **Coin economy battle**: Compare player's coin collection vs enemy team's total

**OUTPUT FORMAT (JSON):**
{{
    "coin_analysis": {{
        "collected": {coins_collected},
        "turned_in": {coins_turned_in},
        "dropped": {coins_likely_dropped},
        "efficiency": {(coins_turned_in / coins_collected * 100) if coins_collected > 0 else 0:.1f},
        "target_met": {coins_collected >= coin_target},
        "assessment": "Detailed assessment of coin collection performance"
    }},
    "critical_mistake": "Single most impactful coin economy mistake with timestamp",
    "win_condition": "How coin economy determined the match outcome",
    "tactical_advice": [
        "Specific advice for improving coin collection",
        "Turn-in timing recommendations",
        "Positioning advice for coin collection safety"
    ],
    "summary": "2-3 sentence summary focusing on coin economy as primary win condition"
}}

**CRITICAL RULES:**
- If coins_collected < {coin_target}, the summary MUST state this as the PRIMARY failure
- Do NOT prioritize lane soak analysis if coin collection was insufficient
- Use technical jargon: "coin economy deficit", "turn-in timing", "coin collection efficiency"
- Match the quality and style of the gold standard examples above
"""
        
        return prompt
    
    def _infer_hero_role(self, hero_name):
        """Infer hero role for coin target calculation"""
        # Healers
        healers = ['Kharazim', 'Uther', 'Rehgar', 'Brightwing', 'Tyrande', 'Li Li', 'Malfurion', 'Ana', 'Anduin', 'Deckard', 'Whitemane', 'Auriel', 'Stukov', 'Alexstrasza']
        # Tanks
        tanks = ['Muradin', 'Diablo', 'Tyrael', 'Arthas', 'Johanna', 'Anub\'arak', 'E.T.C.', 'Stitches', 'Garrosh', 'Blaze', 'Mal\'Ganis', 'Yrel', 'Imperius']
        
        if hero_name in healers:
            return 'healer'
        elif hero_name in tanks:
            return 'tank'
        else:
            return 'dps'  # DPS or Bruiser
