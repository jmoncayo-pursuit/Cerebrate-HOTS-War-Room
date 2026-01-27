from flask import Blueprint, request, jsonify
from api.services.intelligence_service import IntelligenceService

consultation_bp = Blueprint('consultation', __name__, url_prefix='/api')
intel_service = None

def init_consultation_routes(db, api_key):
    global intel_service
    intel_service = IntelligenceService(db, api_key)

@consultation_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    msg = data.get('message')
    history = data.get('history', [])
    response = intel_service.generate_chat_response(msg, history)
    return jsonify({"response": response})

@consultation_bp.route('/advice/stats', methods=['GET'])
def advice_stats():
    return jsonify(intel_service.get_advice_stats())

@consultation_bp.route('/telemetry/temporal', methods=['GET'])
def temporal_stats():
    return jsonify(intel_service.get_temporal_patterns())
