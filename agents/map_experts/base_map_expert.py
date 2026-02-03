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
        """
        from .map_summaries import get_quick_summary
        
        query_lower = query.lower()
        explicit_match_id = context.get('match_id')

        # MODE SELECTION: Programmatic (Cache) vs Forensic (Gemini)
        # Forensic is only for "Why did I lose" or specific match review
        audit_keywords = ['why', 'lost', 'mistake', 'review', 'audit', 'breakdown', 'what happened']
        is_forensic_request = any(kw in query_lower for kw in audit_keywords)
        
        # If no explicit match ID and not a specific audit request, ALWAYS use programmatic cache
        if not explicit_match_id and not is_forensic_request:
            # GOLD STANDARD: Pull from programmatic Swarm Protocol cache
            from api.services.database import DatabaseManager
            db = DatabaseManager()
            cache_data = db.get_kv('map_recommendations_cache') or {}
            recs = cache_data.get('recommendations', {}).get(self.map_name)

            if recs:
                # 1. Header & Priority
                human_response = f"## {self.map_name}\n"
                human_response += f"*{recs.get('desc', 'Strategic priority required.')}*\n\n"

                # 1.5. Carry Hover (Auto-Hover Ideal 1st Pick)
                carry = recs.get('carry_hover')
                if carry and carry.get('hero') != "None":
                    human_response += f"### ✨ Carry Suggestion (Auto-Hover)\n"
                    human_response += f"**{carry['hero']}**: {carry['justification']}\n\n"

                # 2. Targeted Bans
                human_response += "### 🚫 Priority Bans\n"
                for i, ban in enumerate(recs.get('bans', []), 1):
                    human_response += f"- **{ban['hero']}** ({ban['priority']}): {ban['why']} — *{ban['counter']}*\n"
                human_response += "\n"

                # 3. Role-Specific Recommendations
                human_response += "### ⚔️ Role-Specific Recommendations\n\n"
                role_recs = recs.get('role_recs', {})
                for role, heroes in role_recs.items():
                    human_response += f"**If you must play {role}:**\n"
                    for h in heroes:
                        # Clean fallback display
                        h_name = h['hero'] if h['hero'] != "[Meta Fallback]" else "Meta Backup"
                        human_response += f"- **{h_name}**: {h['wr']:.1f}% WR ({h['games']}g) — {h['source']}\n"
                        if h.get('talent_code'):
                            human_response += f"  - [{h['talent_code']},{h['hero']}]\n"
                    human_response += "\n"

                # 4. Strategic Directives (General Map Advice)
                human_response += "### 📜 Strategic Directives\n"
                for directive in recs.get('directives', []):
                    human_response += f"- {directive}\n"

                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'quick_strategy_summary',
                    'data_provenance': 'SWARM_PROTOCOL_CACHE',
                    'map': self.map_name,
                    'analysis': recs,
                    'response': human_response
                }
            
            # Legacy fallback if cache missing
            quick_summary = get_quick_summary(self.map_name)
            if quick_summary:
                human_response = f"## {self.map_name} Tactical Overview\n"
                human_response += f"**Win Condition:** {quick_summary.get('win_condition')}\n\n"
                human_response += f"**Critical Objective:** {quick_summary.get('critical_objective')}\n"
                human_response += f"**Key Timings:** {quick_summary.get('key_timings')}\n"
                human_response += f"**Draft Focus:** {quick_summary.get('draft_focus')}\n"
                human_response += f"\n**Macro Priority:** {quick_summary.get('macro_priority')}\n"
                
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'quick_strategy_summary',
                    'data_provenance': 'STATIC_VERIFIED',
                    'map': self.map_name,
                    'analysis': quick_summary,
                    'response': human_response
                }
            else:
                return {
                    'agent': self.name,
                    'success': False,
                    'error': f'No strategy data available for {self.map_name}',
                    'data_provenance': 'INSUFFICIENT'
                }

        # ELSE: Proceed to Gemini Analysis (Only for Forensic audits with match context)
        matches = context.get('matches', [])
        match_id = explicit_match_id
        
        # Auto-pick latest match for this map if doing a forensic audit without explicit ID
        if not match_id and matches:
            for m in (matches if isinstance(matches, list) else [matches]):
                if m.get('map', '').lower() == self.map_name.lower():
                    match_id = m.get('id')
                    break
            if not match_id: # Fallback to most recent if no map-specific match found
                match_id = matches[0].get('id') if isinstance(matches, list) else matches.get('id')
        
        target_match = None
        if match_id:
            from api.services.database import DatabaseManager
            db = DatabaseManager()
            match_data = db.get_matches(match_id=match_id)
            if match_data:
                target_match = match_data[0]
        
        if not target_match and not is_forensic_request:
             return {
                'agent': self.name,
                'success': False,
                'error': f'Strategic data for {self.map_name} is currently offline.',
                'response': "⚠️ Tactical Datalink Failure. Re-synchronize using @cerebrate."
             }

        # FINAL STEP: Call Gemini for Forensic Analysis
        if not self.call_gemini_fn:
            return {
                'agent': self.name,
                'success': False,
                'error': 'Gemini API function not available'
            }

        prompt = self._build_map_specific_prompt(target_match or {}, context)
        
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
            'analysis': analysis,
            'response': analysis.get('summary', 'Analysis complete. Review tactical data below.')
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
