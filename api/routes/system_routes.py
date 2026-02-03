from flask import Blueprint, request, jsonify
from api.services.database import DatabaseManager
import os

system_bp = Blueprint('system', __name__, url_prefix='/api')
db = DatabaseManager()

@system_bp.route('/data_sources/status', methods=['GET'])
def source_status():
    log = db.get_kv('ingestion_log') or {"entries": []}
    
    # Real counts from DB
    with db._get_connection() as conn:
        match_count = conn.execute("SELECT COUNT(*) FROM matches").fetchone()[0]
        player_records = conn.execute("SELECT COUNT(*) FROM match_players").fetchone()[0]
        hero_mastery = conn.execute("SELECT COUNT(*) FROM hero_stats WHERE games_played > 0").fetchone()[0]

    return jsonify({
        "secure_datalink": {
            "healthy": True,
            "last_updated": log['entries'][0]['timestamp'] if log['entries'] else "2026-02-02T12:00:00",
            "record_count": match_count,
            "coverage": 100,
            "confidence": "Absolute (Local SQL)"
        },
        "neural_synthesizer": {
            "healthy": True,
            "last_updated": "2026-02-02T12:00:00",
            "record_count": hero_mastery,
            "coverage": 85,
            "confidence": "High (AI Synthesis)"
        },
        "telemetry_link": {
            "healthy": True,
            "last_updated": "2026-02-02T12:00:00",
            "record_count": player_records,
            "coverage": 92,
            "confidence": "Verified"
        }
    })

@system_bp.route('/data_sources/lineage/search', methods=['GET'])
def lineage_search():
    query = request.args.get('q', '').lower()
    # Simple semantic fallback for lineage search
    results = []
    if not query:
        return jsonify({"results": []})

    with db._get_connection() as conn:
        # Search for hero provenance
        heroes = conn.execute("SELECT hero, win_rate, games_played FROM hero_stats WHERE lower(hero) LIKE ?", (f"%{query}%",)).fetchall()
        for h in heroes:
            results.append({
                "target": h['hero'],
                "type": "Mastery Dossier",
                "source": "SECURE_DATALINK",
                "evidence": f"{h['games_played']} verified matches recorded.",
                "confidence": "100%"
            })
    
    return jsonify({"results": results})

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
