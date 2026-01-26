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
    from database_manager import DatabaseManager
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
        # Build context
        player_profile = context.get('profile', {})
        # Deeply truncate profile to save tokens
        if 'hero_stats' in player_profile:
            player_profile['hero_stats'] = {k: v for i, (k, v) in enumerate(player_profile['hero_stats'].items()) if i < 10}
            
        recent_matches = context.get('matches', [])[:5]
        global_meta = context.get('global_meta', [])[:10]

        prompt = f"""
{protocol}

**TACTICAL SCAN INPUT:**
- Query: {query}
- Combat Zone (Map): {map_name}

**DATA SOURCES:**
- Player Profile: {json.dumps(player_profile, indent=2)}
- Recent Matches: {json.dumps(recent_matches, indent=2)}
- Global Meta: {json.dumps(global_meta, indent=2)}

**MISSION OBJECTIVE:**
Activate Mode A: DEPLOYMENT.
Provide a complete tactical foundation for the combat zone. 
Include mandatory 🚫 TARGETED BANS.
Use Granular Excellence formatting.
Cite win rates formatted as [XX.X]% WR [[Source]].
"""
        
        try:
            if self.call_gemini_fn:
                response = self.call_gemini_fn(prompt, raw_mode=True, silent=True)
                response_text = str(response).strip()
                
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'map_strategy',
                    'map': map_name,
                    'response': response_text
                }
            else:
                # Fallback
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'map_strategy',
                    'map': map_name,
                    'response': f"Programmatic Fallback: Strategy for {map_name} is to focus on objective control."
                }
        except Exception as e:
            return {
                'agent': self.name,
                'success': False,
                'error': str(e),
                'response': f"Failed to generate tactical intelligence. Error: {str(e)}"
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
        
        # Use ResponseCache for fast, filtered recommendations
        # This reuses the same logic that filters by hero_preferences and owned heroes
        try:
            # Lazy import to avoid circular dependency - import inside function
            import sys
            api_server_module = sys.modules.get('api_server')
            if not api_server_module:
                # If api_server not loaded, try importing it
                import api_server
                api_server_module = api_server
            
            response_cache = getattr(api_server_module, 'RESPONSE_CACHE', None)
            if not response_cache:
                # Fallback: create ResponseCache instance
                from api_server import ResponseCache
                response_cache = ResponseCache()
            
            # Generate formatted response using same filtering logic as API endpoint
            # This filters by hero_preferences, excludes dislike/rarely_play, and only shows heroes you actually play
            formatted_response = response_cache._generate_map_response(map_name)
            
            return {
                'success': True,
                'agent': self.name,
                'analysis_type': 'map_strategy',
                'map': map_name,
                'response': formatted_response,  # Formatted text in Cerebrate protocol format
                'format': 'cerebrate_protocol'
            }
        except Exception as e:
            # Fallback to basic strategy if ResponseCache unavailable
            import traceback
            return {
                'success': False,
                'error': f'Failed to generate map response: {e}',
                'message': f'TACTICIAN error: {str(e)}',
                'traceback': traceback.format_exc()
            }
    
    def _load_map_strategy(self, map_name: str) -> Dict[str, Any]:
        """Load map strategy from database or config"""
        # Try database first
        strategy = self.db.get_kv('cerebrate_config') or {}
        strategies = strategy.get('strategies', {})
        
        if map_name in strategies:
            return strategies[map_name]
        
        # Fallback: check strategies table
        with self.db._get_connection() as conn:
            row = conn.execute(
                'SELECT content_json FROM strategies WHERE key = ? AND category = ?',
                (map_name, 'map_strategy')
            ).fetchone()
            if row:
                import json
                return json.loads(row['content_json'])
        
        # Default strategy
        return {
            'name': map_name,
            'desc': 'Control objectives and maintain map pressure',
            'primary': None,
            'backups': []
        }
    
    def _get_map_performance(self, map_name: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get player's performance on this map"""
        map_records = profile.get('map_records_verified', {})
        map_data = map_records.get(map_name, {})
        
        wins = map_data.get('wins', 0)
        losses = map_data.get('losses', 0)
        total = wins + losses
        
        return {
            'wins': wins,
            'losses': losses,
            'total': total,
            'win_rate': (wins / total * 100) if total > 0 else 0,
            'games_played': total
        }
    
    def _generate_rotations(self, map_name: str, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate rotation timings for the map"""
        # Map-specific rotation timings (in seconds)
        rotation_templates = {
            'Dragon Shire': [
                {'time': '0:00', 'action': 'Split lanes - Top/Mid/Bot', 'priority': 'high'},
                {'time': '2:00', 'action': 'Shrine spawns - Rotate to control', 'priority': 'critical'},
                {'time': '5:00', 'action': 'Dragon Knight spawns - Group for objective', 'priority': 'critical'},
            ],
            'Infernal Shrines': [
                {'time': '0:00', 'action': 'Split lanes - Soak all 3', 'priority': 'high'},
                {'time': '2:00', 'action': 'Shrine activates - Rotate to shrine', 'priority': 'critical'},
                {'time': '5:00', 'action': 'Punisher spawns - Group for teamfight', 'priority': 'critical'},
            ],
            'Cursed Hollow': [
                {'time': '0:00', 'action': 'Split lanes - Soak all 3', 'priority': 'high'},
                {'time': '2:30', 'action': 'First tribute spawns - Rotate early', 'priority': 'critical'},
                {'time': '5:00', 'action': 'Second tribute - Control vision', 'priority': 'high'},
            ],
            'Battlefield of Eternity': [
                {'time': '0:00', 'action': 'Split lanes - Immortal lanes', 'priority': 'high'},
                {'time': '2:00', 'action': 'Immortal spawns - Group for objective', 'priority': 'critical'},
            ],
            'Tomb of the Spider Queen': [
                {'time': '0:00', 'action': 'Split lanes - Collect gems', 'priority': 'high'},
                {'time': '3:00', 'action': 'Turn in gems - Group for protection', 'priority': 'critical'},
            ],
        }
        
        # Get map-specific rotations or use default
        rotations = rotation_templates.get(map_name, [
            {'time': '0:00', 'action': 'Split lanes and soak', 'priority': 'high'},
            {'time': '2:00', 'action': 'First objective spawns - Rotate', 'priority': 'critical'},
        ])
        
        # Add strategy-specific notes
        if strategy.get('desc'):
            rotations.insert(0, {
                'time': 'Strategy',
                'action': strategy['desc'],
                'priority': 'info'
            })
        
        return rotations
    
    def _generate_objective_priorities(self, map_name: str, strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate objective priority list for the map"""
        objective_templates = {
            'Dragon Shire': [
                {'objective': 'Shrine Control', 'priority': 1, 'timing': '2:00', 'notes': 'Control both shrines to activate Dragon Knight'},
                {'objective': 'Dragon Knight', 'priority': 1, 'timing': '5:00', 'notes': 'Use to push structures'},
            ],
            'Infernal Shrines': [
                {'objective': 'Shrine Minions', 'priority': 1, 'timing': '2:00', 'notes': 'Kill 40 minions to spawn Punisher'},
                {'objective': 'Punisher', 'priority': 1, 'timing': '5:00', 'notes': 'Use to push structures'},
            ],
            'Cursed Hollow': [
                {'objective': 'Tributes', 'priority': 1, 'timing': '2:30', 'notes': 'Need 3 to curse enemy team'},
                {'objective': 'Boss', 'priority': 2, 'timing': '10:00', 'notes': 'Take after curse or when ahead'},
            ],
        }
        
        objectives = objective_templates.get(map_name, [
            {'objective': 'Primary Objective', 'priority': 1, 'timing': '2:00', 'notes': 'Control to gain advantage'},
        ])
        
        return objectives
    
    def _get_hero_map_strategy(self, hero: str, map_name: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Get hero-specific strategy for this map"""
        # Check if hero is in strategy
        primary = strategy.get('primary', {})
        if primary and primary.get('name') == hero:
            return {
                'role': 'Primary Pick',
                'build': primary.get('code', ''),
                'notes': primary.get('notes', ''),
                'rationale': f'{hero} is the primary pick for {map_name}'
            }
        
        # Check backups
        backups = strategy.get('backups', [])
        for backup in backups:
            if backup.get('name') == hero:
                return {
                    'role': 'Backup Pick',
                    'build': backup.get('code', ''),
                    'notes': backup.get('notes', ''),
                    'rationale': f'{hero} is a viable backup for {map_name}'
                }
        
        return {
            'role': 'Not Recommended',
            'notes': f'{hero} is not in the recommended strategy for {map_name}',
            'rationale': 'Consider using a hero from the primary/backup list'
        }
    
    def _generate_recommendations(self, strategy: Dict[str, Any], map_stats: Dict[str, Any], hero: Optional[str]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Performance-based recommendations
        if map_stats['win_rate'] < 40 and map_stats['games_played'] >= 5:
            recommendations.append(f"Your win rate on this map is {map_stats['win_rate']:.1f}% - Consider reviewing your strategy")
        
        # Strategy-based recommendations
        if strategy.get('primary'):
            primary_name = strategy['primary'].get('name')
            if hero and hero != primary_name:
                recommendations.append(f"Consider {primary_name} as your primary pick for this map")
        
        # Rotation recommendations
        recommendations.append("Focus on early lane soak before first objective")
        recommendations.append("Group for objectives 10-15 seconds before they spawn")
        
        return recommendations
    
    def get_prompt(self, context: Dict[str, Any]) -> str:
        """Generate prompt for map strategy"""
        map_name = context.get('map', 'Unknown Map')
        hero = context.get('hero', 'Any Hero')
        
        return f"""
        TACTICIAN Agent Map Strategy Request
        
        Map: {map_name}
        Hero: {hero}
        
        Generate map-specific strategy including rotations, objectives, and positioning.
        """
    
    def can_handle(self, query: str, context: Dict[str, Any]) -> bool:
        """TACTICIAN handles map strategy queries - prioritize map name detection"""
        query_lower = query.lower()
        
        # First check if query contains a map name (highest priority)
        # Use orchestrator's map list for consistency
        maps = [
            'tomb of the spider queen', 'infernal shrines', 'dragon shire',
            'blackheart\'s bay', 'cursed hollow', 'sky temple',
            'battlefield of eternity', 'towers of doom', 'garden of terror',
            'volskaya foundry', 'braxis holdout', 'warhead junction',
            'alterac pass', 'hanamura temple', 'haunted mines'
        ]
        
        # Check for exact map name matches first
        for map_name in maps:
            if map_name in query_lower:
                # Also check for partial matches (e.g., "cursed hollow" -> "cursed", "hollow")
                map_words = map_name.split()
                if len(map_words) > 1 and all(word in query_lower for word in map_words):
                    return True
                elif map_name in query_lower:
                    return True
        
        # Fallback: check for strategy keywords (but only if no explicit draft/hero query)
        draft_keywords = ['pick', 'draft', 'ban', 'recommend', 'what should i', 'hero', 'healer', 'tank', 'bruiser', 'assassin']
        has_draft_keyword = any(keyword in query_lower for keyword in draft_keywords)
        
        if has_draft_keyword:
            return False  # Let SCOUT handle explicit draft queries
        
        # Strategy keywords
        strategy_keywords = [
            'strategy', 'rotation', 'timing', 'objective', 'how to play',
            'positioning', 'soak', 'lane', 'directives'
        ]
        return any(keyword in query_lower for keyword in strategy_keywords)
