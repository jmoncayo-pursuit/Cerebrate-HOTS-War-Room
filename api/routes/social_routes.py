from flask import Blueprint, request, jsonify
from api.services.database import DatabaseManager
import uuid
from datetime import datetime

social_bp = Blueprint('social', __name__, url_prefix='/api')
db = DatabaseManager()

@social_bp.route('/player_interactions', methods=['GET'])
def get_interactions():
    interactions = db.get_kv('player_interactions') or {}
    return jsonify(interactions)

@social_bp.route('/player_interactions/<player_id>/neural_brief', methods=['POST'])
def save_brief(player_id):
    data = request.json or {}
    brief = data.get('brief')
    
    interactions = db.get_kv('player_interactions') or {}
    
    # Find player by ID or Name
    player_data = None
    if player_id in interactions:
        player_data = interactions[player_id]
    else:
        # Search by name in values
        for pid, pdata in interactions.items():
            if pdata.get('name') == player_id:
                player_data = pdata
                break
                
    if not player_data:
        return jsonify({"success": False, "error": "Player not found"}), 404
        
    player_data['aiStrategy'] = brief
    player_data['brief_updated'] = datetime.now().isoformat()
    
    db.set_kv('player_interactions', interactions)
    return jsonify({"success": True})

@social_bp.route('/player_network', methods=['GET'])
def player_network():
    # Helper to return consolidated network data
    interactions = db.get_kv('player_interactions') or {}
    return jsonify({
        "players": list(interactions.values()),
        "total_nodes": len(interactions)
    })
