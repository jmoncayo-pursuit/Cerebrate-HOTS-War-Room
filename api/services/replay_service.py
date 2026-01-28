import os
import time
import json
from datetime import datetime
from api.logger import ColoredLogger
from api.services.replay_parser import parse_replay
from api.services.database import DatabaseManager
from api.services.quota_manager import QuotaManager

class ReplayService:
    def __init__(self):
        self.db = DatabaseManager()
        self.quota = QuotaManager()
        self._intel_service = None  # Lazy-loaded

    def _get_intel_service(self):
        """Lazy-load IntelligenceService to avoid circular imports."""
        if self._intel_service is None:
            from api.services.intelligence_service import IntelligenceService
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key:
                self._intel_service = IntelligenceService(self.db, api_key)
        return self._intel_service

    def process_replay_file(self, replay_file):
        """Handle file upload, validation, parsing, and database storage."""
        filename = replay_file.filename
        
        # 1. Validation Filters
        if not filename.endswith('.StormReplay'):
             return {'error': 'Invalid file type'}, 400

        fname_low = filename.lower().replace(' ', '')
        # Blacklist check
        non_sl_maps = [
            'lostcavern', 'silvercity', 'industrialdistrict', 'braxisoutpost',
            'checkpoint', 'pullparty', 'poolparty', 'escapefrombraxis', 
            'deadmansstand', 'sandbox', 'tryme', 'blackheartsrevenge', 
            'hauntedmines', 'tutorial', 'hallowsend', 'snowbrawl'
        ]
        if any(m in fname_low for m in non_sl_maps):
            return {'error': 'Non-competitive map ignored'}, 400
        
        if 'hanamura' in fname_low and 'temple' not in fname_low:
             return {'error': 'Non-standard Hanamura maps are blacklisted'}, 400

        # 2. Quota Check
        if not self.quota.can_process_replay():
            return {'error': 'Daily quota exceeded', 'status': 'quota_exceeded'}, 429

        # 3. Temp Save & Parse
        temp_path = os.path.join("/tmp", filename)
        try:
            replay_file.save(temp_path)
            
            # Parse
            result = parse_replay(temp_path)
            if not result or result.get('status') == 'error':
                 os.remove(temp_path)
                 return {'error': result.get('message', 'Parsing failed'), 'traceback': result.get('traceback')}, 500
            
            if result.get('status') == 'rejected':
                 os.remove(temp_path)
                 return {'error': result.get('message')}, 400

            # 4. Database Ingestion
            db_data = {
                'id': result['match_id'],
                'map': result['map'],
                'hero': result['hero'],
                'result': result['result'].upper(), # WIN/LOSS
                'date': result['timestamp_iso'],
                'duration': result['game_length'],
                'players': result['players'],
                'advanced_stats': result.get('advanced_stats', {})
            }
            
            # Upsert
            success = self.db.upsert_match(db_data)
            
            # 5. IMMEDIATE ANALYSIS (within quota)
            analysis_result = None
            if success and self.quota.can_make_request():
                try:
                    analysis_result = self._generate_match_summary(db_data)
                    if analysis_result and analysis_result.get('success'):
                        self.db.update_match_analysis(result['match_id'], analysis_result['analysis'])
                        self.quota.record_request()
                except Exception as e:
                    ColoredLogger.warn(f"Analysis generation failed: {e}", "REPLAY")
            
            os.remove(temp_path)
            return {
                'success': success, 
                'match_id': result['match_id'], 
                'hero': result['hero'], 
                'map': result['map'],
                'analysis_status': 'complete' if analysis_result else 'pending'
            }, 200

        except Exception as e:
            if os.path.exists(temp_path): os.remove(temp_path)
            ColoredLogger.error(f"Replay Service Error: {e}", "REPLAY")
            return {'error': str(e)}, 500

    def _generate_match_summary(self, match_data):
        """Generate a concise AI summary for a match."""
        intel_service = self._get_intel_service()
        if not intel_service:
            return None
        
        map_name = match_data.get('map', 'Unknown')
        hero = match_data.get('hero', 'Unknown')
        result = match_data.get('result', 'UNKNOWN')
        duration = match_data.get('duration', 'Unknown')
        
        # Extract player stats
        players = match_data.get('players', [])
        user_stats = {}
        for p in players:
            if p.get('hero') == hero:
                user_stats = p.get('stats', {})
                break
        
        prompt = f"""You are analyzing a Heroes of the Storm match. Generate a concise tactical summary.

**MATCH DATA (VERIFIED):**
- Map: {map_name}
- Hero: {hero}
- Result: {result}
- Duration: {duration}

**USER STATS:**
{json.dumps(user_stats, indent=2)[:1500]}

**OUTPUT REQUIREMENTS:**
Return ONLY a JSON object with these fields:
{{
    "verdict": "WIN" or "LOSS",
    "summary": "2-3 sentence tactical summary focusing on objective contribution and key moments",
    "key_insight": "Single most important tactical takeaway"
}}

CRITICAL: Base your analysis ONLY on the provided stats. Do not invent data. Keep summary under 100 words.
"""
        
        try:
            response = intel_service.model.generate_content([prompt])
            res_text = response.text.strip()
            
            # Parse JSON
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(res_text)
            return {'success': True, 'analysis': analysis}
        except Exception as e:
            ColoredLogger.warn(f"Summary parse error: {e}", "REPLAY")
            return None

    def get_match_history(self, limit=50, include_details=False):
        return self.db.get_matches(limit=limit, include_details=include_details)

    def analyze_match(self, match_id):
        """Run AI analysis on an existing match."""
        # Get match data
        matches = self.db.get_matches(match_id=match_id, include_details=True)
        if not matches:
            return {"status": "error", "message": "Match not found"}
        
        match_data = matches[0]
        
        # Check if already analyzed
        if match_data.get('analysis') and match_data['analysis'] != {}:
            return {"status": "complete", "match_id": match_id, "analysis": match_data['analysis']}
        
        # Generate analysis
        if not self.quota.can_make_request():
            return {"status": "quota_exceeded", "match_id": match_id}
        
        result = self._generate_match_summary(match_data)
        if result and result.get('success'):
            self.db.update_match_analysis(match_id, result['analysis'])
            self.quota.record_request()
            return {"status": "complete", "match_id": match_id, "analysis": result['analysis']}
        
        return {"status": "error", "match_id": match_id, "message": "Analysis generation failed"}

