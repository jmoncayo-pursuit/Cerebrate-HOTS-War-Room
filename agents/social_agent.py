"""
SOCIAL Agent
Specialized in player synergy and nemesis tracking
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional

try:
    from database_manager import DatabaseManager
except ImportError:
    DatabaseManager = None


class SocialAgent(BaseAgent):
    """
    SOCIAL Agent - Player Synergy Specialist
    
    Expertise:
    - Player synergy analysis
    - Nemesis tracking
    - Duo queue recommendations
    - Team composition analysis
    - Social network insights
    """
    
    def __init__(self, db=None, call_gemini_fn=None):
        super().__init__(
            name="SOCIAL",
            role="Player Synergy Specialist",
            expertise="Player synergy, nemesis tracking, duo queue recommendations, team composition",
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
        Analyze player interactions and generate social intelligence using Gemini.
        """
        # Load Protocol
        import os
        protocol_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.agent/brain/SOCIAL_INTELLIGENCE_PROTOCOL.md')
        protocol = ""
        if os.path.exists(protocol_path):
            try:
                with open(protocol_path, 'r') as f:
                    protocol = f.read()
            except:
                pass

        # Load player interactions
        interactions = self.db.get_kv('player_interactions') or {}
        # Truncate to top 20 players to save tokens
        if len(interactions) > 20:
            sorted_players = sorted(interactions.items(), key=lambda x: x[1].get('total_with', 0) + x[1].get('total_against', 0), reverse=True)
            interactions = dict(sorted_players[:20])

        player_name = context.get('player_name') or self._extract_player(query)
        
        prompt = f"""
{protocol}

**SOCIAL SCAN INPUT:**
- Query: {query}
- Focus Player: {player_name or 'Network Overview'}

**RAW INTERACTION DATA:**
{json.dumps(interactions, indent=2)}

**MISSION OBJECTIVE:**
Generate a social intelligence report. If a specific player is targeted, provide their combat profile (relationship, WR with/against, tactical counter).
If it's a general query, provide a Social Network Analytics report with High-Synergy Assets and High-Threat Identifications.
Follow the formatting standards in the protocol.
"""
        

        # Visual Context Handling
        image_data = context.get('image')
        if image_data:
            prompt += """
\n**VISUAL INTELLIGENCE ACTIVE:**
An image of the scoreboard/lobby has been provided. 
1. Perform OCR to extract ALL player names from the image.
2. Cross-reference these names with your internal knowledge of known allies/nemeses.
3. If you identify known players, prioritize them in the report.
4. "The Discerning" is the user. Identify teammates vs enemies.
"""

        try:
            if self.call_gemini_fn:
                response = self.call_gemini_fn(prompt, raw_mode=True, silent=True, image_data=image_data)
                response_text = str(response).strip()
                
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'social_analysis',
                    'query': query,
                    'response': response_text,
                    'player_name': player_name
                }
            else:
                # Fallback to programmatic analysis if Gemini not available
                if player_name:
                    return self._analyze_specific_player(player_name, interactions, context)
                else:
                    return self._analyze_social_network(interactions, context)
        except Exception as e:
            return {
                'agent': self.name,
                'success': False,
                'error': str(e),
                'response': f"Failed to generate social intelligence. Error: {str(e)}"
            }

    def _extract_player(self, query):
        """Extract player name from query"""
        query_lower = query.lower()
        player_keywords = ['player', 'teammate', 'ally', 'opponent', 'enemy']
        for keyword in player_keywords:
            if keyword in query_lower:
                parts = query_lower.split(keyword)
                if len(parts) > 1:
                    next_part = parts[1].strip().split()[0] if parts[1].strip() else None
                    if next_part and len(next_part) > 2:
                        return next_part.capitalize()
        return None

    def _analyze_specific_player(self, player_name: str, interactions: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze relationship with a specific player (Programmatic Fallback)"""
        player_data = interactions.get(player_name, {})
        if not player_data:
            return {'error': 'Player not found', 'message': f'No data found for player: {player_name}'}
        
        wins_with = player_data.get('wins_with', 0)
        total_with = player_data.get('total_with', 0)
        wins_against = player_data.get('wins_against', 0)
        total_against = player_data.get('total_against', 0)
        
        wr_with = (wins_with / total_with * 100) if total_with > 0 else 0
        wr_against = (wins_against / total_against * 100) if total_against > 0 else 0
        
        relationship = 'neutral'
        if total_with >= 3 and wr_with >= 60: relationship = 'strong_ally'
        elif total_against >= 3 and wr_against < 40: relationship = 'nemesis'
        
        return {
            'agent': self.name,
            'analysis_type': 'player_analysis',
            'player_name': player_name,
            'relationship': relationship,
            'stats': {
                'with': {'wins': wins_with, 'total': total_with, 'win_rate': wr_with},
                'against': {'wins': wins_against, 'total': total_against, 'win_rate': wr_against}
            },
            'response': f"Programmatic Scan: {player_name} is currently flagged as {relationship.upper()}."
        }

    def _analyze_social_network(self, interactions: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # (Simplified programmatic fallback)
        return {
            'agent': self.name,
            'analysis_type': 'social_network',
            'message': "Programmatic Overview: Network contains " + str(len(interactions)) + " identified entities."
        }

    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """SOCIAL handles player and network queries"""
        query_lower = query.lower()
        social_keywords = [
            'player', 'teammate', 'ally', 'allies', 'nemesis', 'nemeses', 'duo', 'queue',
            'synergy', 'network', 'social', 'who should i play with',
            'best partner', 'partners', 'friends', 'worst matchup', 'threat', 'rival'
        ]
        return any(keyword in query_lower for keyword in social_keywords)
