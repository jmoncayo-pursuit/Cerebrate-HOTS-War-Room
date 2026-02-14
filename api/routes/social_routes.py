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
    audit = data.get('audit') # Frontend might pass audit if it triggered it, but we'll re-audit or store it
    
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
        
    # INTEGRATE NEURAL AUDIT if not provided
    if not audit:
        try:
            from agents.cerebrate_orchestrator import CerebrateOrchestrator
            from api.services.intelligence_service import IntelligenceService
            import os
            api_key = os.environ.get('GEMINI_API_KEY')
            intel = IntelligenceService(db, api_key)
            orchestrator = CerebrateOrchestrator(call_gemini_api_fn=intel.generate_chat_response, db_manager=db)
            
            audit_context = {
                'target_query': player_data.get('name', 'Unknown Player'),
                'target_context': f"Player Data: {json.dumps(player_data)}",
                'target_response': brief,
                'audit_type': 'SOCIAL'
            }
            auditor_result = orchestrator.agents['auditor'].analyze(player_data.get('name'), audit_context)
            if auditor_result.get('success'):
                audit = auditor_result.get('audit')
        except Exception as e:
            print(f"Social Audit Error: {e}")

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
