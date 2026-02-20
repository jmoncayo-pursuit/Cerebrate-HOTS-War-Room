"""
Scout Agent
Specializes in draft intelligence, hero recommendations, and meta predictions
"""

from .base_agent import BaseAgent

class ScoutAgent(BaseAgent):
    """Agent specialized in draft intelligence and hero recommendations"""
    
    def __init__(self, call_gemini_fn=None, db_manager=None):
        super().__init__(
            name="SCOUT",
            role="Draft Intelligence Specialist",
            expertise=[
                "Hero recommendations",
                "Draft strategy",
                "Ban priorities",
                "Meta predictions",
                "Map-specific picks",
                "Role selection"
            ],
            call_gemini_fn=call_gemini_fn
        )
        self.db = db_manager
    
    def can_handle(self, query, context):
        """Check if query is about draft/hero selection - exclude pure map name queries"""
        query_lower = query.lower()
        
        # Explicit draft keywords that indicate hero selection intent
        explicit_draft_keywords = [
            'what should i pick', 'what should i draft', 'who should i play',
            'best hero', 'recommend', 'suggestion', 'pick for',
            'what hero', 'which hero', 'hero for', 'pick', 'draft',
            'predict', 'prediction', 'outcome'
        ]
        
        # Role keywords (indicates draft query)
        role_keywords = ['healer', 'tank', 'bruiser', 'ranged assassin', 'melee assassin']
        
        # Only match if query has explicit draft intent or role specification
        # Pure map names (e.g., "cursed hollow", "infernal shrines") should go to TACTICIAN
        has_explicit_draft = any(keyword in query_lower for keyword in explicit_draft_keywords)
        has_role_spec = any(keyword in query_lower for keyword in role_keywords)
        has_draft_context = 'ban' in query_lower or 'counter' in query_lower or 'synergy' in query_lower
        
        # Don't match if it's just a map name without draft keywords
        # Check if query is ONLY a map name (no other keywords)
        if not (has_explicit_draft or has_role_spec or has_draft_context):
            return False
        
        return has_explicit_draft or has_role_spec or has_draft_context
    
    def analyze(self, query, context):
        """
        Produce a high-quality draft recommendation based on the Draft Recommendation Protocol.
        """
        import json
        map_name = context.get('map') or self._extract_map(query)
        role = context.get('role') or self._extract_role(query)
        
        # Load Protocol
        import os
        protocol_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.agent/brain/DRAFT_RECOMMENDATION_PROTOCOL.md')
        protocol = ""
        if os.path.exists(protocol_path):
            try:
                with open(protocol_path, 'r') as f:
                    protocol = f.read()
            except:
                pass

        # Build context message
        player_profile = context.get('profile', {})
        # Deeply truncate profile to save tokens
        if 'hero_stats' in player_profile:
            player_profile['hero_stats'] = {k: v for i, (k, v) in enumerate(player_profile['hero_stats'].items()) if i < 10}
            
        recent_matches = context.get('matches', [])[:5]
        global_meta = context.get('global_meta', [])[:15]

        prompt = f"""
{protocol}

**TACTICAL INPUT:**
- Query: {query}
- Map: {map_name or 'Unknown'}
- Requested Role: {role or 'Any'}

**DATA SOURCES (YOUR DATALINK—USE THIS DATA):**
- Player Profile: {json.dumps(player_profile, indent=2)}
- Recent Match History: {json.dumps(recent_matches, indent=2)}
- Global Meta Stats: {json.dumps(global_meta, indent=2)}

**CRITICAL:** You have been given Player Profile and Match History above. Do NOT output "USER DATALINK SEVERED", "Map context not provided", or similar disclaimers—use the data you have. For hero counter/ban questions without a map, use match history (who eliminated you) and profile.

**MISSION OBJECTIVE:**
Generate a draft recommendation that follows the MANDATORY RECOMMENDATION STRUCTURE in the protocol.
Be specific, technical, and data-driven. Use the player's personal win rates if available.
If names are available in the profile/recent matches, incorporate Social Intelligence (Apex Threats, Stable Links).
"""
        
        # Visual Context Handling
        image_data = context.get('image')
        vision_prompt = ""
        if image_data:
            vision_prompt = """
**VISUAL INTELLIGENCE ACTIVE:**
An image of the draft/loading screen has been provided.
1. OCR the hero names and player names.
2. Identify the map from the background/text.
3. Predict the match outcome based on composition synergy and counters.
4. If this is a loading screen, identify the user (likely 'Discerning') and analyze their matchup.
"""
            prompt += vision_prompt

        try:
            # Call Gemini with Image support
            response = self.call_gemini_fn(prompt, raw_mode=True, silent=True, image_data=image_data)
            response_text = str(response).strip()
            
            return {
                'agent': self.name,
                'success': True,
                'analysis_type': 'draft_recommendation',
                'query': query,
                'map': map_name,
                'role': role,
                'response': response_text,
                'context': f"Map: {map_name or 'Any'}, Role: {role or 'Any'}"
            }
        except Exception as e:
            # Fallback
            return {
                'agent': self.name,
                'success': False,
                'error': str(e),
                'analysis_type': 'draft_recommendation',
                'query': query,
                'response': f"Failed to generate draft intelligence. API quota may be exceeded. Error: {str(e)}"
            }

    def _extract_map(self, query):
        """Extract map name from query"""
        query_lower = query.lower()
        maps = [
            'Tomb of the Spider Queen', 'Infernal Shrines', 'Dragon Shire',
            'Blackheart\'s Bay', 'Cursed Hollow', 'Sky Temple',
            'Battlefield of Eternity', 'Towers of Doom', 'Garden of Terror',
            'Volskaya Foundry', 'Braxis Holdout', 'Warhead Junction',
            'Alterac Pass', 'Hanamura Temple', 'Haunted Mines'
        ]
        
        for map_name in maps:
            if map_name.lower().replace("'", "") in query_lower.replace("'", ""):
                return map_name
        return None

    def _extract_role(self, query):
        """Extract role from query"""
        query_lower = query.lower()
        roles = {
            'tank': ['tank', 'warrior', 'frontline'],
            'healer': ['healer', 'support', 'sustain'],
            'assassin': ['assassin', 'damage', 'dps', 'carry'],
            'bruiser': ['bruiser', 'solo lane', 'offlane']
        }
        
        for role_name, keywords in roles.items():
            if any(keyword in query_lower for keyword in keywords):
                return role_name.capitalize()
        return None

    def get_example_queries(self):
        return [
            "What should I pick for Tomb of the Spider Queen?",
            "Best healer for Dragon Shire?",
            "Recommend a bruiser",
            "Who should I ban on Infernal Shrines?",
            "What's my best tank?"
        ]
