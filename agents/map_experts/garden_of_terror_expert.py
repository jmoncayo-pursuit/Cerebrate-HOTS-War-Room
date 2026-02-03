"""
Garden of Terror Map Expert
Specializes in Seed Collection, Terror Deployment, and Multi-Lane Pressure
"""

from .base_map_expert import BaseMapExpert
import json

class GardenOfTerrorExpert(BaseMapExpert):
    """Expert agent for Garden of Terror map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Garden of Terror",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Garden of Terror specific analysis prompt
        """
        return f"""You are a Garden of Terror tactical expert.
**MAP CONTEXT:**
Garden is a MACRO map.
- **Seeds**: Collect 3 for the Terror wave.
- **Terrors**: Push all three lanes. Split defense is hard.
- **Shamblers**: Good source of early XP and seeds.
**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}
"""
