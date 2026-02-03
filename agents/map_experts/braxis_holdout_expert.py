"""
Braxis Holdout Map Expert
Specializes in Beacon Control, Zerg Wave Management, and Solo Lane Durability
"""

from .base_map_expert import BaseMapExpert
import json

class BraxisHoldoutExpert(BaseMapExpert):
    """Expert agent for Braxis Holdout map analysis"""
    
    def __init__(self, call_gemini_api_fn=None, db_manager=None):
        super().__init__(
            map_name="Braxis Holdout",
            call_gemini_api_fn=call_gemini_api_fn,
            db_manager=db_manager
        )
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build Braxis Holdout specific analysis prompt
        """
        return f"""You are a Braxis Holdout tactical expert.
**MAP CONTEXT:**
Braxis is a SNOWBALL map.
- **Beacons**: Constant contest. 100% zerg wave is often game-ending.
- **Solo Lane**: Top lane is the most critical 1v1 in the game.
- **Zerg Wave**: Defense is as important as offense.
**MATCH DATA:**
{json.dumps(match_data, indent=2)[:2000]}
"""
