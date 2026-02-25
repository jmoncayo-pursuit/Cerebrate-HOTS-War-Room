from flask import Blueprint, request, jsonify, current_app
import os
import json
import time
from agents.nexus_orchestrator import NexusOrchestrator
from api.services.database import DatabaseManager
from api.services.quota_manager import QuotaManager
from api.logger import ColoredLogger

agent_bp = Blueprint('agent', __name__, url_prefix='/api')
db = DatabaseManager()
quota_manager = QuotaManager()

from api.services.mcp_bridge_service import mcp_bridge
from api.routes.watcher_routes import is_watcher_running
from api.routes.system_routes import is_healer_running

# We need the call_gemini_api function. In this architecture, it's usually 
# handled by IntelligenceService or passed down.
from api.services.intelligence_service import IntelligenceService

# Global orchestrator instance (lazy loaded)
_orchestrator = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        # Get API Key
        api_key = os.environ.get('GEMINI_API_KEY')
        intel_service = IntelligenceService(db, api_key)
        
        def call_gemini(prompt, raw_mode=False, silent=False, image_data=None, **kwargs):
             # Wrapper for orchestrator
             try:
                 contents = [prompt]
                 response = intel_service.model.generate_content(contents)
                 return response.text
             except Exception as e:
                 ColoredLogger.error(f"Agent API Call Error: {e}")
                 return f"Error: {e}"

        _orchestrator = NexusOrchestrator(call_gemini_api_fn=call_gemini, db_manager=db)
    return _orchestrator

@agent_bp.route('/nexus/agents', methods=['GET'])
def get_agents():
    orchestrator = get_orchestrator()
    return jsonify({"agents": orchestrator.get_available_agents()})

@agent_bp.route('/nexus/ask', methods=['POST'])
def ask_agent():
    data = request.json or {}
    query = data.get('query')
    context = data.get('context', {})
    
    # Inject profile and matches into context if not provided
    if 'profile' not in context:
        context['profile'] = db.get_kv('player_profile')
    if 'matches' not in context:
        context['matches'] = db.get_matches(limit=50)

    orchestrator = get_orchestrator()
    result = orchestrator.route_query(query, context)
    responder = result.get('orchestrator', {}).get('selected_agent', 'UNKNOWN')

    # 🕵️ TELEMETRY: Identify which agent handled the query
    provenance = result.get('data_provenance', 'AI_GENERATED')
    
    # Record usage if successful and NOT a programmatic/cached response
    is_programmatic = provenance in ['SWARM_PROTOCOL_CACHE', 'STATIC_VERIFIED', 'LOCAL_COGNITION']
    
    if result.get('success') and not is_programmatic:
        # Use the default model for telemetry
        quota_manager.record_request(model="gemini-3-flash-preview")
    
    # Add responder info to result for frontend transparency
    result['responder_id'] = responder

    # Sanitize response
    if result.get('response') and isinstance(result['response'], str):
        from api.services.replay_service import ReplayService
        result['response'] = ReplayService().clean_text(result['response'])
        # Collapse duplicate hero name artifacts
        import re
        result['response'] = re.sub(r'\b([A-Z][a-z]+)(\s+\1)+\b', r'\1', result['response'])
        
    return jsonify(result)

@agent_bp.route('/usage', methods=['GET'])
def get_usage():
    # Return extended usage info for AgentDashboard
    status = quota_manager.get_status()
    
    # Check for token telemetry in database
    telemetry = db.get_kv('token_telemetry') or {
        "total_tokens": 0,
        "prompt_tokens": 0,
        "response_tokens": 0,
        "total_calls": 0,
        "history": []
    }
    
    # Determine model health based on quota
    remaining = sum(s['remaining'] for s in status.values())
    quality = "Nexus Link Stable" if remaining > 500 else "Neural Degradation Detected" if remaining > 100 else "Emergency Link Active"
    
    return jsonify({
        "status": "active",
        "quota": status,
        "total_tokens": telemetry.get('total_tokens', 0),
        "prompt_tokens": telemetry.get('prompt_tokens', 0),
        "response_tokens": telemetry.get('response_tokens', 0),
        "total_calls": telemetry.get('total_calls', 0),
        "history": telemetry.get('history', []),
        "link_quality": quality,
        "current_model": "Gemini 3.1 Pro",
        "pipeline_version": "3.2.0",
        "services": {
            "mcp_bridge": "ACTIVE" if mcp_bridge.is_healthy() else "DISCONNECTED",
            "healer": "ACTIVE" if is_healer_running() else "OFFLINE",
            "watcher": "ACTIVE" if is_watcher_running() else "OFFLINE"
        }
    })

@agent_bp.route('/temporal_analysis', methods=['GET'])
def temporal_analysis():
    # Check if IntelligenceService is available
    api_key = os.environ.get('GEMINI_API_KEY')
    intel_service = IntelligenceService(db, api_key)
    stats = intel_service.get_temporal_patterns()
    
    # Format for frontend
    formatted = {}
    for k, v in stats.items():
        formatted[k] = {
            "wins": v['wins'],
            "games": v['games'],
            "wr": round(v['wins'] / v['games'] * 100, 1) if v['games'] > 0 else 0
        }
        
    return jsonify({"success": True, "stats": formatted})
@agent_bp.route('/audit/gaps', methods=['GET'])
def get_intelligence_gaps():
    from api.agentic_brain import AgenticBrain
    brain = AgenticBrain()
    gaps = brain.get_all_intelligence_gaps()
    return jsonify({"success": True, "gaps": gaps})
@agent_bp.route('/global_account_stats', methods=['GET'])
def get_global_account_stats():
    # Fetch from global_account_stats table
    try:
        with db._get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM global_account_stats")
            rows = cursor.fetchall()
            stats_map = {row[0]: row[1] for row in rows}
            
            # Format into structured response
            formatted = {
                "lifetime_games_played": int(stats_map.get('lifetime_games_played', 0)),
                "lifetime_win_rate": stats_map.get('lifetime_win_rate', 0),
                "kda_ratio": str(stats_map.get('lifetime_kda_ratio', "0.0")),
                "roles": {
                    "Tank": {"win_rate": stats_map.get('lifetime_role_tank', 0), "games": 0},
                    "Healer": {"win_rate": stats_map.get('lifetime_role_healer', 0), "games": 0},
                    "Bruiser": {"win_rate": stats_map.get('lifetime_role_bruiser', 0), "games": 0},
                    "Ranged Assassin": {"win_rate": stats_map.get('lifetime_role_ranged_assassin', 0), "games": 0},
                    "Melee Assassin": {"win_rate": stats_map.get('lifetime_role_melee_assassin', 0), "games": 0},
                    "Support": {"win_rate": stats_map.get('lifetime_role_support', 0), "games": 0}
                },
                "seasonal": {
                    "games": int(stats_map.get('season_games_played', 0)),
                    "win_rate": stats_map.get('season_win_rate', 0),
                    "most_played": "N/A" # Need another query for this if wanted
                }
            }
            return jsonify(formatted)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@agent_bp.route('/map_stats', methods=['GET'])
def get_map_stats():
    # Fetch map performance distribution from global_map_stats
    try:
        with db._get_connection() as conn:
            cursor = conn.execute("SELECT map_name, games_played, wins, losses, win_rate FROM global_map_stats ORDER BY win_rate DESC")
            rows = cursor.fetchall()
            return jsonify([{
                "map_name": r[0],
                "games": r[1],
                "wins": r[2],
                "losses": r[3],
                "win_rate": r[4]
            } for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


from api.services.dossier_service import DossierService

@agent_bp.route('/hero_dossier/manifest', methods=['GET'])
def get_dossier_manifest():
    try:
        service = DossierService(db)
        manifest = service.get_manifest()
        return jsonify({"manifest": manifest})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/hero_dossier', methods=['GET'])
def get_hero_dossier():
    hero = request.args.get('hero')
    if not hero:
        return jsonify({"error": "Hero name required"}), 400
        
    try:
        service = DossierService(db)
        dossier = service.generate_dossier(hero)
        
        if not dossier:
            return jsonify({"error": "Insufficient data"}), 404
            
        return jsonify(dossier)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agent_bp.route('/mcp/inspect', methods=['GET'])
def inspect_mcp():
    from api.services.mcp_bridge_service import mcp_bridge
    
    action = request.args.get('action')
    
    if action == 'logs':
        result = mcp_bridge.run_command(mcp_bridge.get_console_logs())
        return jsonify(result)
        
    if action == 'dom':
        result = mcp_bridge.run_command(mcp_bridge.get_dom_snapshot())
        return jsonify(result)

    status = {
        "connected": mcp_bridge.is_healthy(),
        "bridge_type": "Chrome DevTools Protocol",
        "capabilities": ["evaluate_script", "list_console_messages"],
        "link_status": "NEURAL_LINK_ESTABLISHED" if mcp_bridge.is_healthy() else "SEARCHING_FOR_SIGNAL"
    }
    return jsonify(status)

@agent_bp.route('/vision/analyze', methods=['GET'])
def vision_analyze():
    map_name = request.args.get('map', 'Infernal Shrines')
    from api.agentic_brain import AgenticBrain
    brain = AgenticBrain()
    recommendations = brain.get_draft_recommendations(map_name)
    return jsonify(recommendations)
