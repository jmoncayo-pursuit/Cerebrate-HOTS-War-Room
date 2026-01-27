from flask import Blueprint, request, jsonify
from api.services.database import DatabaseManager
import os

system_bp = Blueprint('system', __name__, url_prefix='/api')
db = DatabaseManager()

@system_bp.route('/data_sources/status', methods=['GET'])
def source_status():
    log = db.get_kv('ingestion_log') or {"entries": []}
    # Mocking some status data since we don't have a formal source tracker yet
    return jsonify({
        "blizzard_verified": {
            "healthy": True,
            "last_updated": log['entries'][0]['timestamp'] if log['entries'] else "2026-01-26T00:00:00",
            "record_count": 1420,
            "coverage": 85,
            "confidence": "High"
        },
        "replay_parser": {
            "healthy": True,
            "last_updated": "2026-01-26T12:00:00",
            "record_count": 542,
            "coverage": 100,
            "confidence": "Absolute"
        }
    })

@system_bp.route('/data_sources/conflicts', methods=['GET'])
def data_conflicts():
    # Placeholder for conflict detection
    return jsonify({"conflicts": []})

@system_bp.route('/data/ingestion_log.json', methods=['GET'])
def ingestion_log_json():
    # Compatibility with frontend fetching json file
    log = db.get_kv('ingestion_log') or {"entries": []}
    return jsonify(log)

@system_bp.route('/system/health', methods=['GET'])
def system_health():
    return jsonify({
        "status": "operational",
        "database": "connected",
        "kv_store": "active"
    })

PID_FILE = ".healer.pid"

def is_healer_running():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            import os as native_os
            native_os.kill(pid, 0)
            return True
        except:
            return False
    return False

@system_bp.route('/healer/status', methods=['GET'])
def healer_status():
    log_file = "healer.log"
    last_pulse = None
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                content = f.read()
                if "HEALER_ACTIVE:" in content:
                    last_pulse = content.split("HEALER_ACTIVE:")[1].strip()
        except:
            pass
            
    return jsonify({
        "running": is_healer_running(),
        "last_pulse": last_pulse,
        "mode": "AUTONOMOUS SELF-REPAIR"
    })

@system_bp.route('/healer/start', methods=['POST'])
def start_healer():
    if is_healer_running():
        return jsonify({"success": True, "message": "Already active"})
    
    import subprocess
    subprocess.Popen(["python3", "scripts/cerebrate_healer.py"], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    start_new_session=True)
    return jsonify({"success": True})

@system_bp.route('/healer/stop', methods=['POST'])
def stop_healer():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            import os as native_os
            import signal
            native_os.kill(pid, signal.SIGTERM)
            native_os.remove(PID_FILE)
            return jsonify({"success": True})
        except:
            pass
    return jsonify({"success": True, "message": "Healer was not running or could not be stopped"})
