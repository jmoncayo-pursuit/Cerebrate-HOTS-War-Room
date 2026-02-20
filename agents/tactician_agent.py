"""
TACTICIAN Agent
Specialized in map strategy and rotation timings
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional

try:
    from api.services.database import DatabaseManager
except ImportError:
    DatabaseManager = None


class TacticianAgent(BaseAgent):
    """
    TACTICIAN Agent - Map Strategy Specialist
    
    Expertise:
    - Map-specific strategies
    - Rotation timings
    - Objective priorities
    - Hero positioning
    - Win condition analysis per map
    """
    
    def __init__(self, db=None, call_gemini_fn=None):
        super().__init__(
            name="TACTICIAN",
            role="Map Strategy Specialist",
            expertise="Map strategies, rotation timings, objective priorities, positioning",
            call_gemini_fn=call_gemini_fn
        )
        self._db = db
    
    @property
    def db(self):
        """Lazy initialization of database manager"""
        if self._db is None:
            if DatabaseManager is None:
                raise RuntimeError("DatabaseManager not available")
            self._db = DatabaseManager()
        return self._db
    
    def analyze(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate map strategy recommendations using Gemini and Protocol.
        """
        import json
        import os
        map_name = context.get('map') or self._extract_map(query)
        
        if not map_name:
            return {
                'success': False,
                'error': 'Missing map name',
                'message': 'TACTICIAN requires a map name to provide strategy'
            }

        # Load Protocol
        protocol_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.agent/brain/AI_CHAT_PROTOCOL.md')
        protocol = ""
        if os.path.exists(protocol_path):
            try:
                with open(protocol_path, 'r') as f:
                    protocol = f.read()
            except:
                pass

        # Build context
        player_profile = context.get('profile', {})
        if 'hero_stats' in player_profile:
            player_profile['hero_stats'] = {k: v for i, (k, v) in enumerate(player_profile['hero_stats'].items()) if i < 10}
            
        recent_matches = context.get('matches', [])[:5]
        global_meta = context.get('global_meta', [])[:10]

        prompt = f"""
{protocol}

**TACTICAL SCAN INPUT:**
- Query: {query}
- Combat Zone (Map): {map_name}

**DATA SOURCES (YOUR DATALINK—USE THIS DATA):**
- Player Profile: {json.dumps(player_profile, indent=2)}
- Recent Matches: {json.dumps(recent_matches, indent=2)}
- Global Meta: {json.dumps(global_meta, indent=2)}

**CRITICAL:** You have been given Player Profile and Match Data above. Do NOT output "USER DATALINK SEVERED" or similar disclaimers—use the data.

**MISSION OBJECTIVE:**
Activate Mode A: DEPLOYMENT.
Provide a complete tactical foundation for the combat zone. 
Include mandatory 🚫 TARGETED BANS.
Use Granular Excellence formatting.
Cite win rates formatted as [XX.X]% WR [[Source]].
"""
        
        # MODE SELECTION: Programmatic (Cache) vs Forensic (Gemini)
        query_lower = query.lower()
        audit_keywords = ['why', 'lost', 'mistake', 'review', 'audit', 'breakdown', 'what happened']
        analysis_requested = any(kw in query_lower for kw in audit_keywords)
        
        if not analysis_requested:
            # SWARM PROTOCOL: Check for programmatic cache first to save tokens
            try:
                db = self.db
                cache_data = db.get_kv('map_recommendations_cache') or {}
                recs = cache_data.get('recommendations', {}).get(map_name)

                if recs:
                    # Header
                    human_response = f"## {map_name} (Tactical Relay)\n"
                    human_response += f"*{recs.get('desc', 'Strategic priority required.')}*\n\n"

                    # Bans
                    human_response += "### 🚫 Priority Bans\n"
                    for i, ban in enumerate(recs.get('bans', []), 1):
                        human_response += f"{i}. **{ban['hero']}** — [{ban['priority']}]\n"

                    # Recommendations
                    human_response += "\n### Role-Specific Recommendations\n"
                    role_recs = recs.get('role_recs', {})
                    for role, heroes in role_recs.items():
                        human_response += f"**{role}:** "
                        human_response += ", ".join([f"{h['hero']} ({h['wr']:.1f}%)" for h in heroes])
                        human_response += "\n"

                    return {
                        'agent': self.name,
                        'success': True,
                        'analysis_type': 'map_strategy_cache',
                        'data_provenance': 'SWARM_PROTOCOL_CACHE',
                        'map': map_name,
                        'response': human_response
                    }
            except Exception as e:
                # Fallback to standard logic if cache fails
                pass

        if self.call_gemini_fn:
            try:
                response = self.call_gemini_fn(prompt, raw_mode=True, silent=True)
                response_text = str(response).strip()
                
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'map_strategy',
                    'map': map_name,
                    'response': response_text
                }
            except Exception as e:
                return {
                    'agent': self.name,
                    'success': False,
                    'error': str(e),
                    'response': f"Failed to generate tactical intelligence. Error: {str(e)}"
                }
        
        # Fallback
        return {
            'agent': self.name,
            'success': True,
            'analysis_type': 'map_strategy_fallback',
            'map': map_name,
            'response': f"Programmatic Fallback: Strategy for {map_name} is to focus on objective control and lane soak."
        }

    def _extract_map(self, query):
        """Extract map name from query"""
        query_lower = query.lower()
        maps = [
            'Tomb of the Spider Queen', 'Infernal Shrines', 'Dragon Shire',
            'Blackhearts Bay', 'Cursed Hollow', 'Sky Temple',
            'Battlefield of Eternity', 'Towers of Doom', 'Garden of Terror',
            'Volskaya Foundry', 'Braxis Holdout', 'Warhead Junction',
            'Alterac Pass', 'Hanamura Temple', 'Haunted Mines'
        ]
        
        for map_name in maps:
            if map_name.lower().replace("'", "") in query_lower.replace("'", ""):
                return map_name
        return None
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """TACTICIAN handles map strategy queries - prioritize map name detection"""
        query_lower = query.lower()
        
        # First check if query contains a map name (highest priority)
        maps = [
            'tomb of the spider queen', 'infernal shrines', 'dragon shire',
            'blackheart\'s bay', 'cursed hollow', 'sky temple',
            'battlefield of eternity', 'towers of doom', 'garden of terror',
            'volskaya foundry', 'braxis holdout', 'warhead junction',
            'alterac pass', 'hanamura temple', 'haunted mines'
        ]
        
        for map_name in maps:
            if map_name in query_lower:
                return True
        
        # Strategy keywords
        strategy_keywords = [
            'strategy', 'rotation', 'timing', 'objective', 'how to play',
            'positioning', 'soak', 'lane', 'directives'
        ]
        return any(keyword in query_lower for keyword in strategy_keywords)
