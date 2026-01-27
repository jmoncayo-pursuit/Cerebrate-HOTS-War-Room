from flask import Blueprint, request, jsonify
import os
import json
import signal
import subprocess
import time

watcher_bp = Blueprint('watcher', __name__, url_prefix='/api')

STATUS_FILE = ".watcher_status.json"
ACTIVITY_LOG_FILE = ".watcher_activity.json"
PID_FILE = ".watcher.pid"

def get_watcher_pid():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            pass
    return None

def is_watcher_running():
    pid = get_watcher_pid()
    if pid:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
    return False

@watcher_bp.route('/watcher/status', methods=['GET'])
def get_status():
    status = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                status = json.load(f)
        except:
            pass
            
    activities = []
    if os.path.exists(ACTIVITY_LOG_FILE):
        try:
            with open(ACTIVITY_LOG_FILE, 'r') as f:
                activities = json.load(f)
        except:
            pass
            
    return jsonify({
        "running": is_watcher_running(),
        "processing": status,
        "activities": activities[:50],
        "replay_count": status.get('total', 0)
    })

@watcher_bp.route('/watcher/start', methods=['POST'])
def start_watcher():
    if is_watcher_running():
        return jsonify({"success": True, "running": True, "message": "Already running"})
        
    # Start in background
    process = subprocess.Popen(["python3", "replay_watcher.py"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL,
                             start_new_session=True)
                             
    return jsonify({"success": True, "running": True})

@watcher_bp.route('/watcher/stop', methods=['POST'])
def stop_watcher():
    pid = get_watcher_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            return jsonify({"success": True, "running": False})
        except:
            pass
            
    return jsonify({"success": True, "running": False})
