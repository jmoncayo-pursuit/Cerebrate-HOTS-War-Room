from flask import Blueprint, request, jsonify
from api.services.replay_service import ReplayService

replay_bp = Blueprint('replay', __name__)
replay_service = ReplayService()

@replay_bp.route('/api/upload_replay', methods=['POST'])
def upload_replay():
    """Endpoint for uploading and parsing a replay file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    result, status_code = replay_service.process_replay_file(request.files['file'])
    return jsonify(result), status_code

@replay_bp.route('/api/analyze_replay', methods=['POST'])
def analyze_replay():
    """
    Combined endpoint (Compatibility): 
    1. If file provided: Process and then analyze.
    2. If match_id provided: Analyze existing.
    """
    # 1. File Upload Case (Legacy Watcher Support)
    if 'file' in request.files:
        result, status_code = replay_service.process_replay_file(request.files['file'])
        if status_code != 200:
            return jsonify(result), status_code
        return jsonify(result), 200

    # 2. JSON Request Case
    if request.is_json:
        data = request.get_json() or {}
        match_id = data.get('match_id')
        if not match_id:
            return jsonify({'error': 'No match_id or file provided'}), 400
        result = replay_service.analyze_match(match_id)
        return jsonify(result)
    
    return jsonify({'error': 'Expected JSON or File'}), 415

@replay_bp.route('/api/match_history', methods=['GET'])
def match_history():
    """Serve match history for frontend"""
    limit = request.args.get('limit', 500)
    include_details = request.args.get('details', 'false').lower() == 'true'
    try:
        limit = int(limit)
    except:
        limit = 500
        
    matches = replay_service.get_match_history(limit=limit, include_details=include_details)
    return jsonify(matches)
