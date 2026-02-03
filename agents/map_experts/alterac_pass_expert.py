"""
Alterac Pass Map Expert
Specializes in Cavalry Momentum, Objective Mud Pits, and Gnoll Camp Timing
"""

from .base_map_expert import BaseMapExpert
import json

class AlteracPassExpert(BaseMapExpert):
    """Expert agent for Alterac Pass map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Alterac Pass",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Alterac Pass specific analysis prompt
        """
        return f"""You are an Alterac Pass tactical expert.
**MAP CONTEXT:**
Alterac Pass is a MOMENTUM map.
- **Cavalry**: Capture them simultaneously if possible; they provide a massive aura.
- **Mud Pits**: Essential zones for control.
- **Gnoll Camps**: High XP and high damage.
**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}
"""
