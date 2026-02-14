import logging
import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from api.logger import ColoredLogger

# Load environment variables
load_dotenv()

# Silence Flask/Werkzeug logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
from api.routes.consultation_routes import consultation_bp, init_consultation_routes
from api.routes.management_routes import management_bp
from api.routes.replay_routes import replay_bp
from api.routes.agent_routes import agent_bp
from api.routes.social_routes import social_bp
from api.routes.system_routes import system_bp
from api.routes.watcher_routes import watcher_bp
from api.routes.verification_routes import verification_bp
from api.services.database import DatabaseManager
from api.services.mcp_bridge_service import mcp_bridge

def create_app():
    app = Flask(__name__)
    db = DatabaseManager()
    
    # Initialize Dependencies
    init_consultation_routes(db, os.environ.get('GEMINI_API_KEY'))
    
    # Start Neural Link (MCP Bridge)
    mcp_bridge.start_background()
    
    # Register Consolidated Blueprints
    # Unified prefix management: Blueprints handle their own /api prefixes
    app.register_blueprint(consultation_bp)
    app.register_blueprint(management_bp)
    app.register_blueprint(replay_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(system_bp)
    app.register_blueprint(watcher_bp)
    app.register_blueprint(verification_bp)
    
    @app.route('/api/health')
    def health():
        return jsonify({"status": "healthy", "version": "elite-dx-v3"})

    return app

if __name__ == '__main__':
    try:
        app = create_app()
        port = int(os.environ.get('API_PORT', 5001))
        ColoredLogger.success(f"Cerebrate API Online | Port: {port}", "API")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        ColoredLogger.error(f"Server Startup Error: {e}", "API")
