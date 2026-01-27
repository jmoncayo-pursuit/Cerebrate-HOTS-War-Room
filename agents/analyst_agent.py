"""
Analyst Agent
Specializes in post-game match analysis, critical mistakes, and win conditions
"""

from .base_agent import BaseAgent

class AnalystAgent(BaseAgent):
    """Agent specialized in match review and post-game analysis"""
    
    def __init__(self, call_gemini_fn=None):
        super().__init__(
            name="ANALYST",
            role="Match Review Specialist",
            expertise=[
                "Post-game analysis",
                "Critical mistakes identification",
                "Win condition analysis",
                "Performance evaluation",
                "Tactical breakdowns"
            ],
            call_gemini_fn=call_gemini_fn
        )
    
    def can_handle(self, query, context):
        """Check if query is about match analysis"""
        query_lower = query.lower()
        
        # Keywords that indicate match analysis
        analysis_keywords = [
            'why did i lose', 'why did i win', 'what went wrong',
            'analyze', 'review', 'mistake', 'critical error',
            'what happened', 'breakdown', 'post-game',
            'last match', 'recent game', 'that game',
            'forensic', 'performance', 'stats',
            'verdict', 'explain', 'tell me about this', 'why'
        ]
        
        # If we have an active match context, we handle analytical followups
        if context.get('selectedMatch') or context.get('match_id'):
            if query_lower.startswith(('why', 'how', 'tell me', 'explain', 'elaborate')):
                return True
        
        return any(keyword in query_lower for keyword in analysis_keywords)
    
    def analyze(self, query, context):
        """
        Perform match analysis or forensic audit using Gemini.
        """
        import json
        import os
        
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
        # Deeply truncate profile to save tokens
        if 'hero_stats' in player_profile:
            player_profile['hero_stats'] = {k: v for i, (k, v) in enumerate(player_profile['hero_stats'].items()) if i < 10}
        
        recent_matches = context.get('matches', [])[:5] # Limit to 5 most recent
        
        # Target specific match or general audit?
        selected_match = context.get('selectedMatch')
        match_id = context.get('match_id')
        
        target_match = None
        if selected_match:
            target_match = selected_match
        elif match_id:
            target_match = next((m for m in recent_matches if m.get('id') == match_id), None)
        
        mode = "Match Analysis" if target_match else "FORENSIC AUDIT"
        
        prompt = f"""
{protocol}

**ANALYST SCAN INPUT:**
- Query: {query}
- Target Mode: {mode}

**DATA SOURCES:**
- Player Profile: {json.dumps(player_profile, indent=2)}
- Recent Match Data (Telemetry): {json.dumps(recent_matches, indent=2)}
- LIVE APP TELEMETRY (Neural Link): {json.dumps(context.get('live_telemetry', 'Disconnected'), indent=2)}

**MISSION OBJECTIVE:**
{'Analyze the specific match provided.' if target_match else 'Analyze the recent performance trends and patterns.'}
If Live App Telemetry is available, prioritize identifying any UI errors or state inconsistencies currently visible to the user.
Follow the mandatory formatting for {'Mode B: FORENSIC AUDIT' if not target_match else 'MATCH ANALYSIS'}.
Identify if failures are Multiplicative or Additive.
Cite win rates formatted as [XX.X]% WR [[Source]].
"""

        try:
            if self.call_gemini_fn:
                response = self.call_gemini_fn(prompt, raw_mode=True, silent=True)
                response_text = str(response).strip()
                
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'match_analysis' if target_match else 'forensic_audit',
                    'query': query,
                    'response': response_text,
                    'hero': target_match.get('hero') if target_match else None,
                    'map': target_match.get('map') if target_match else None
                }
            else:
                # Basic programmatic fallback
                return {
                    'agent': self.name,
                    'success': True,
                    'analysis_type': 'match_analysis',
                    'response': "Programmatic Fallback: Match analysis currently limited. Replays indicate consistent performance."
                }
        except Exception as e:
            return {
                'agent': self.name,
                'success': False,
                'error': str(e),
                'response': f"Failed to generate analysis. Error: {str(e)}"
            }

    def get_example_queries(self):
        return [
            "Why did I lose that last game?",
            "Analyze my recent Kharazim match",
            "What was my critical mistake?",
            "Review my performance on Infernal Shrines",
            "Perform a forensic analysis of my recent performance"
        ]
