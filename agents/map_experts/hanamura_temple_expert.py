"""
Hanamura Temple Map Expert
Specializes in Payload Escort, Samurai Camp Control, and Vision Dominance
"""

from .base_map_expert import BaseMapExpert
import json

class HanamuraTempleExpert(BaseMapExpert):
    """Expert agent for Hanamura Temple map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Hanamura Temple",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Hanamura Temple specific analysis prompt
        """
        return f"""You are a Hanamura Temple tactical expert.
**MAP CONTEXT:**
Hanamura is a BRAWL map.
- **Payloads**: The primary objective. Escorting 2 at once is a major win.
- **Samurai Camp**: Most impactful merc in the game. Do not let enemy take it for free.
- **Vision**: Essential for payload safety.
**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}
"""
