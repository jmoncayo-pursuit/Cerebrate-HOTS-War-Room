from flask import Blueprint, request, jsonify, send_from_directory
import json
import os
from api.services.data_management_service import DataManagementService

management_bp = Blueprint('management', __name__, url_prefix='/api')
mgmt_service = DataManagementService()

@management_bp.route('/roster-constraints', methods=['GET'])
def get_constraints():
    return jsonify(mgmt_service.get_constraints())

@management_bp.route('/roster-constraints', methods=['POST'])
def update_constraints():
    data = request.json or {}
    hero = data.get('hero')
    action = data.get('action')
    config = mgmt_service.update_hero_status(hero, action)
    return jsonify({"success": True, "config": config})

@management_bp.route('/data-sources/status', methods=['GET'])
def data_status():
    return jsonify(mgmt_service.get_source_status())

@management_bp.route('/player_profile', methods=['GET'])
def get_profile():
    profile = mgmt_service.db.get_kv('player_profile') or {}
    config = mgmt_service.get_constraints()
    
    # Season Flow Fix: Ensure profile always reflects current active season from config
    active_season = config.get('active_season')
    if active_season:
        profile['active_season'] = active_season
    
    return jsonify(profile)

@management_bp.route('/cerebrate_config', methods=['GET'])
def cerebrate_config():
    """Returns the master configuration including strategies and constraints."""
    return jsonify(mgmt_service.get_constraints())

@management_bp.route('/strategies', methods=['GET'])
def strategies():
    """Legacy endpoint for strategies, maps to config."""
    config = mgmt_service.get_constraints()
    return jsonify(config.get('strategies', {}))

@management_bp.route('/data/<path:filename>')
def serve_data_files(filename):
    return send_from_directory('src/data', filename)

@management_bp.route('/data/global_hero_stats_stormleague_plus_talents.json', methods=['GET'])
def get_global_hero_stats():
    # Legacy compatibility endpoint
    return jsonify(mgmt_service.get_global_meta())

@management_bp.route('/refresh_context', methods=['POST'])
def refresh_context():
    """Trigger a refresh of in-memory data (currently a stub for refactored system)."""
    return jsonify({"success": True, "message": "Context refresh synchronized"})
