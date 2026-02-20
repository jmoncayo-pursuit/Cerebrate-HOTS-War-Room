from flask import Blueprint, request, jsonify
import json
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
    audit = None  # Auditor removed to reduce token usage
    
    interactions = db.get_kv('player_interactions') or {}
    
    # Find player by ID or Name
    player_data = None
    target_pid = None
    if player_id in interactions:
        player_data = interactions[player_id]
        target_pid = player_id
    else:
        # Search by name in values
        for pid, pdata in interactions.items():
            if pdata.get('name') == player_id:
                player_data = pdata
                target_pid = pid
                break
                
    if not player_data:
        return jsonify({"success": False, "error": "Player not found"}), 404

    player_data['aiStrategy'] = brief
    player_data['audit'] = audit
    player_data['brief_updated'] = datetime.now().isoformat()
    
    db.set_kv('player_interactions', interactions)
    
    # Also sync to social_profiles if possible
    try:
        with db._get_connection() as conn:
            conn.execute("""
                UPDATE social_profiles 
                SET neural_brief = ?, neural_brief_audit = ? 
                WHERE player_name = ? OR toon_handle = ?
            """, (brief, json.dumps(audit) if audit else None, player_data.get('name'), target_pid))
    except Exception as sync_e:
        print(f"Sync to social_profiles failed: {sync_e}")

    return jsonify({"success": True, "audit": audit})

@social_bp.route('/player_network', methods=['GET'])
def player_network():
    # Helper to return consolidated network data
    interactions = db.get_kv('player_interactions') or {}
    return jsonify({
        "players": list(interactions.values()),
        "total_nodes": len(interactions)
    })
