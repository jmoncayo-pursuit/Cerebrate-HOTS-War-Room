"""
Referee Agent
Grades match summaries for quality and triggers retries if needed
"""

import json
from api.logger import ColoredLogger
# from api_server import call_gemini_api # Removed to fix circular import

class RefereeAgent:
    """
    Referee Agent - Quality Control Specialist
    
    Grades match summaries on:
    - Strategic Accuracy (1-5): Does the analysis correctly identify what happened?
    - Persona Consistency (1-5): Does it match the Nexus authoritative tone?
    - Map-Specific Insight (1-5): Does it provide map-relevant tactical advice?
    """
    
    def __init__(self, db_manager=None):
        self.db = db_manager
    
    def grade_summary(self, summary, match_data, attempt_number=1):
        """
        Grade a match summary using Gemini.
        
        Args:
            summary: The generated summary dict (verdict, summary, key_insights, etc.)
            match_data: Full parsed match data for context
            attempt_number: Which attempt this is (for tracking)
        
        Returns:
            dict: {
                'strategic_accuracy': int (1-5),
                'persona_consistency': int (1-5),
                'map_specific_insight': int (1-5),
                'overall': float,
                'feedback': str
            }
        """
        map_name = match_data.get('map', 'Unknown')
        hero = match_data.get('hero', 'Unknown')
        result = match_data.get('result', 'Unknown')
        
        # Build grading prompt
        prompt = f"""You are the Referee Agent, a quality control specialist for match analysis summaries.

**MATCH CONTEXT:**
- Map: {map_name}
- Hero: {hero}
- Result: {result}
- Attempt: {attempt_number}

**SUMMARY TO GRADE:**
```json
{json.dumps(summary, indent=2)}
```

**GRADING CRITERIA (1-5 scale):**

1. **Strategic Accuracy** (1-5):
   - 5: Correctly identifies key plays, mistakes, and win conditions with specific evidence
   - 4: Mostly accurate but missing some nuance or context
   - 3: Generally correct but has minor inaccuracies
   - 2: Significant gaps or errors in analysis
   - 1: Fundamentally wrong or missing critical information

2. **Persona Consistency** (1-5):
   - 5: Perfect authoritative, clinical, data-centric tone with tactical jargon
   - 4: Good tone but occasional fluff or casual language
   - 3: Inconsistent tone, mixes authoritative with casual
   - 2: Mostly casual or unclear tone
   - 1: Completely wrong tone or style

3. **Map-Specific Insight** (1-5):
   - 5: Provides map-specific tactical advice (objective timing, rotations, etc.)
   - 4: Some map context but could be more specific
   - 3: Generic advice that applies to any map
   - 2: Minimal map awareness
   - 1: No map-specific insight

{f"**MAP-SPECIFIC CRITERIA FOR {map_name}:**" if map_name == "Blackheart's Bay" else ""}
{f"""
- **MANDATORY**: Summary MUST include coin collection analysis with specific numbers
- **MANDATORY**: Win condition analysis MUST prioritize coin economy over level milestones
- **MANDATORY**: If coins_collected < target (3+ healer/tank, 5+ dps/bruiser), this MUST be identified as PRIMARY win condition failure
- **MANDATORY**: Coin efficiency calculation (turned_in / collected) must be included
- **REDUCE SCORE TO 2 OR BELOW** if summary prioritizes lane soak over coin collection
- **REDUCE SCORE TO 1** if coin collection is not mentioned at all
""" if map_name == "Blackheart's Bay" else ""}

**YOUR TASK:**
Grade this summary and provide constructive feedback.

Return ONLY a JSON object:
{{
    "strategic_accuracy": <1-5>,
    "persona_consistency": <1-5>,
    "map_specific_insight": <1-5>,
    "overall": <average of three scores>,
    "feedback": "<Specific, actionable feedback on what to improve>"
}}"""

        from api_server import call_gemini_api
        try:
            response = call_gemini_api(prompt, raw_mode=True, silent=True)
            response_text = str(response).strip()
            
            # Extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                grades = json.loads(json_str)
                
                # Ensure scores are in valid range
                for key in ['strategic_accuracy', 'persona_consistency', 'map_specific_insight']:
                    if key in grades:
                        grades[key] = max(1, min(5, int(grades[key])))
                
                # Calculate overall if not provided
                if 'overall' not in grades:
                    grades['overall'] = (
                        grades.get('strategic_accuracy', 3) +
                        grades.get('persona_consistency', 3) +
                        grades.get('map_specific_insight', 3)
                    ) / 3.0
                
                return grades
            else:
                # Fallback if JSON parsing fails
                ColoredLogger.warn("Referee response not in JSON format, using default scores", "REFEREE")
                return {
                    'strategic_accuracy': 3,
                    'persona_consistency': 3,
                    'map_specific_insight': 3,
                    'overall': 3.0,
                    'feedback': 'Could not parse referee response - defaulting to neutral score'
                }
        except Exception as e:
            ColoredLogger.error(f"Referee grading error: {e}", "REFEREE")
            return {
                'strategic_accuracy': 3,
                'persona_consistency': 3,
                'map_specific_insight': 3,
                'overall': 3.0,
                'feedback': f'Error during grading: {str(e)}'
            }
    
    def needs_rewrite(self, grades, threshold=4.0):
        """
        Determine if summary needs to be rewritten based on grades.
        
        Args:
            grades: Dict with 'overall' score
            threshold: Minimum overall score to pass (default 4.0)
        
        Returns:
            bool: True if rewrite needed, False if summary passes
        """
        overall = grades.get('overall', 0)
        return overall < threshold
    
    def save_grade(self, match_id, attempt_number, grades, feedback):
        """Save grade to database if db_manager is available."""
        if self.db:
            try:
                self.db.save_summary_grade(match_id, attempt_number, grades, feedback)
            except Exception as e:
                ColoredLogger.error(f"Failed to save grade: {e}", "REFEREE")
