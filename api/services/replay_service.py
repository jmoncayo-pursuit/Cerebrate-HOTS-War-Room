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

            # DEBUG
            # print(f"DEBUG: parser result keys {result.keys()}")

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
            
            os.remove(temp_path)
            return {'success': success, 'match_id': result['match_id'], 'hero': result['hero'], 'map': result['map']}, 200

        except Exception as e:
            if os.path.exists(temp_path): os.remove(temp_path)
            ColoredLogger.error(f"Replay Service Error: {e}", "REPLAY")
            return {'error': str(e)}, 500

    def get_match_history(self, limit=50, include_details=False):
        return self.db.get_matches(limit=limit, include_details=include_details)

    def analyze_match(self, match_id):
        """Run AI analysis on an existing match."""
        # This will be implemented with LLM logic later
        return {"status": "analysis_pending", "match_id": match_id}
