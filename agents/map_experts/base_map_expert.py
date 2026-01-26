"""
Base Map Expert Agent
Foundation for map-specific analysis agents
"""

from ..base_agent import BaseAgent

class BaseMapExpert(BaseAgent):
    """Base class for map-specific expert agents"""
    
    def __init__(self, map_name, call_gemini_api_fn=None, db_manager=None):
        """
        Initialize a map expert
        
        Args:
            map_name: Name of the map this expert specializes in
            call_gemini_api_fn: Gemini API function
            db_manager: Database manager for data access
        """
        super().__init__(
            name=f"{map_name} Expert",
            role=f"Tactical Specialist",
            expertise=[
                f"{map_name} objective control",
                f"{map_name} win conditions",
                f"Map-specific macro decisions",
                f"Timing and rotation strategies"
            ],
            call_gemini_fn=call_gemini_api_fn
        )
        self.map_name = map_name
        self.db = db_manager
    
    def can_handle(self, query, context):
        """Check if this map expert should handle the query"""
        # Check if map is mentioned in query or context
        query_lower = query.lower()
        map_lower = self.map_name.lower()
        
        # Direct map mention
        if map_lower in query_lower:
            return True
        
        # Check context for map
        context_map = context.get('map', '')
        if context_map and context_map.lower() == map_lower:
            return True
        
        # Check if this is a match analysis for this map
        matches = context.get('matches', [])
        if matches:
            latest_match = matches[0] if isinstance(matches, list) else matches
            match_map = latest_match.get('map', '') if isinstance(latest_match, dict) else ''
            if match_map and match_map.lower() == map_lower:
                return True
        
        return False
    
    def analyze(self, query, context):
        """
        Perform map-specific analysis
        
        Args:
            query: User's question
            context: Additional context (profile, matches, etc.)
        
        Returns:
            dict: Map-specific analysis response
        """
        # Get match data from context
        match_id = context.get('match_id')
        matches = context.get('matches', [])
        
        if not match_id and matches:
            match_id = matches[0].get('id') if isinstance(matches, list) else matches.get('id')
        
        if not match_id:
            # Fallback to general map strategy if no match is provided
            # This allows the expert to still provide tactical value for general queries
            target_match = {
                'map': self.map_name,
                'hero': 'Generic',
                'result': 'STRATEGIC_PLANNING',
                'players': []
            }
        else:
            # Get match data
            target_match = None
            if isinstance(matches, list):
                target_match = next((m for m in matches if m.get('id') == match_id), None)
            elif isinstance(matches, dict):
                target_match = matches if matches.get('id') == match_id else None
            
            if not target_match:
                # Try to load from database
                if self.db:
                    all_matches = self.db.get_matches(limit=10)
                    target_match = next((m for m in all_matches if m.get('id') == match_id), None)
            
            if not target_match:
                return {
                    'agent': self.name,
                    'success': False,
                    'error': f'Match {match_id} not found'
                }
        
        # Build map-specific prompt
        prompt = self._build_map_specific_prompt(target_match, context)
        
        # Visual Context Handling
        image_data = context.get('image')
        if image_data:
            prompt += """
\n**VISUAL INTELLIGENCE ACTIVE:**
An image has been provided. 
1. If this is a draft screen, analyze the composition relative to this map's win conditions.
2. If this is a scoreboard, analyze the stats relative to this map's objectives.
3. Use the visual data to augment your strategic advice.
"""
        
        # Call Gemini with map-specific prompt
        if not self.call_gemini_fn:
            return {
                'agent': self.name,
                'success': False,
                'error': 'Gemini API function not available'
            }
        
        response = self.call_gemini_fn(prompt, context=context, raw_mode=False, silent=True, image_data=image_data)
        
        # Parse response
        try:
            import json
            res_text = str(response).strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(res_text)
        except Exception as e:
            return {
                'agent': self.name,
                'success': False,
                'error': f'Failed to parse analysis: {e}',
                'raw_response': str(response)[:500]
            }
        
        return {
            'agent': self.name,
            'success': True,
            'analysis_type': 'map_specific_analysis',
            'map': self.map_name,
            'match_id': match_id,
            'analysis': analysis
        }
    
    def _build_map_specific_prompt(self, match_data, context):
        """
        Build map-specific analysis prompt
        
        Args:
            match_data: Match data dictionary
            context: Additional context
        
        Returns:
            str: Formatted prompt for Gemini
        """
        raise NotImplementedError(f"{self.name} must implement _build_map_specific_prompt()")
    
    def _get_map_gold_standards(self, limit=2):
        """Get map-specific gold standard examples"""
        if not self.db:
            return []
        return self.db.get_gold_standards(map_name=self.map_name, limit=limit)
    
    def get_example_queries(self):
        """Return example queries for this map"""
        return [
            f"How should I play {self.map_name}?",
            f"What are the win conditions on {self.map_name}?",
            f"Analyze my {self.map_name} match",
            f"What mistakes did I make on {self.map_name}?"
        ]
