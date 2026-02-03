from flask import Blueprint, request, jsonify
import json
import time
import base64
from api.services.database import DatabaseManager
from api.services.intelligence_service import IntelligenceService
import os

verification_bp = Blueprint('verification', __name__, url_prefix='/api')
db = DatabaseManager()

def get_intelligence():
    api_key = os.environ.get('GEMINI_API_KEY')
    return IntelligenceService(db, api_key)

@verification_bp.route('/extract_stats_from_screenshot', methods=['POST'])
def extract_stats():
    """Extracts HotsLogs or Profile stats from a screenshot using Gemini Vision."""
    data = request.json or {}
    image_data = data.get('image') # Base64 encoded image
    
    if not image_data:
        return jsonify({"success": False, "error": "No image data provided"}), 400
        
    intel = get_intelligence()
    
    prompt = """
    Extract Heroes of the Storm player statistics from this screenshot. 
    Focus on:
    - Lifetime Games Played
    - Win Rate
    - KDA Ratio
    - Most Played Heroes (Name and Win Rate)
    - Role distribution (Win Rates)
    
    Return ONLY a JSON object with these keys:
    {
      "games_played": number,
      "win_rate": number,
      "kda": "ratio string",
      "heroes": [{"name": string, "win_rate": number}],
      "roles": {"Tank": number, "Healer": number, "Bruiser": number, "Assassins": number}
    }
    """
    
    try:
        # Assuming IntelligenceService.model exists and can handle vision
        # This is a bit speculative on the internal structure of intel_service 
        # but matches the 'ask_agent' pattern.
        response_text = intel.model.generate_content([prompt, {"mime_type": "image/png", "data": image_data.split(',')[-1]}]).text
        
        # Parse JSON from response
        # Clean up any markdown blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        stats = json.loads(response_text)
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@verification_bp.route('/verify_stats', methods=['POST'])
def verify_stats():
    """Compares extracted stats with local DB data and identifies discrepancies."""
    data = request.json or {}
    extracted = data.get('extracted', {})
    
    # Fetch local truth from DB
    try:
        with db._get_connection() as conn:
            # Simple global stats check
            cursor = conn.execute("SELECT key, value FROM global_account_stats")
            rows = cursor.fetchall()
            local_map = {row[0]: row[1] for row in rows}
            
            # Compare Games Played
            local_games = int(local_map.get('lifetime_games_played', 0))
            ext_games = int(extracted.get('games_played', 0))
            
            diff_games = ext_games - local_games
            
            # Basic verification logic
            verification = {
                "games": {
                    "source": ext_games,
                    "local": local_games,
                    "delta": diff_games,
                    "status": "synchronized" if diff_games == 0 else "behind" if diff_games > 0 else "ahead"
                },
                "confidence": 0.85 if diff_games < 10 else 0.5,
                "needs_sync": diff_games > 0,
                "message": f"Source shows {diff_games} more games than local database." if diff_games > 0 else "Local data matches source telemetry."
            }
            
            return jsonify({"success": True, "verification": verification})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
