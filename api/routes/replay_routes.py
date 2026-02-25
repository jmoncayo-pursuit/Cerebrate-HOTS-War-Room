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
        force = data.get('force', False)
        
        if not match_id:
            return jsonify({"status": "error", "message": "match_id required"}), 400
            
        result = replay_service.analyze_match(match_id, force=force)
        return jsonify(result)
    
    return jsonify({'error': 'Expected JSON or File'}), 415

@replay_bp.route('/api/reparse_match', methods=['POST'])
def reparse_match():
    """Re-parse a match's replay file to refresh draft picks, banner, and DC data. Preserves analysis."""
    if not request.is_json:
        return jsonify({"success": False, "error": "JSON body required"}), 400
    data = request.get_json() or {}
    match_id = data.get("match_id")
    if not match_id:
        return jsonify({"success": False, "error": "match_id required"}), 400
    result = replay_service.reparse_match(match_id)
    if result.get("success"):
        return jsonify(result), 200
    return jsonify(result), 404 if result.get("error") == "Match not found" else 400

@replay_bp.route('/api/match_history', methods=['GET'])
def match_history():
    """Serve match history for frontend. Optional: id (single match), hero, since (YYYY-MM-DD) for this-season coverage."""
    limit = request.args.get('limit', 500)
    include_details = request.args.get('details', 'false').lower() == 'true'
    match_id = request.args.get('id') or request.args.get('match_id')
    search = request.args.get('search')
    hero = request.args.get('hero') or None
    since = request.args.get('since') or None
    try:
        limit = int(limit)
    except ValueError:
        limit = 2000
    limit = min(limit, 2000)  # cap list size for memory
    matches = replay_service.get_match_history(
        limit=limit, include_details=include_details, search=search, hero=hero, since=since, match_id=match_id
    )
    return jsonify(matches)
