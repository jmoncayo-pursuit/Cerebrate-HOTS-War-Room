#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import json
import requests
from datetime import datetime

# Setup paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from database_manager import DatabaseManager
from api.logger import ColoredLogger

class CerebrateHealer:
    def __init__(self):
        self.db = DatabaseManager()
        self.api_url = "http://localhost:5001"
        self.last_integrity_check = 0
        self.check_interval = 60 # Check every minute
        
    def check_api_health(self):
        """Check if the API is responding."""
        try:
            res = requests.get(f"{self.api_url}/api/player_profile", timeout=5)
            if res.status_code == 200:
                return True
        except:
            pass
        return False

    def repair_data_integrity(self):
        """Fix mathematical inconsistencies in player profile."""
        profile = self.db.get_kv('player_profile')
        if not profile: return
        
        hero_stats = profile.get('hero_stats', {})
        repaired = False
        
        for hero, data in hero_stats.items():
            for key in ['verified_season_2025_3', 'verified_lifetime']:
                stats = data.get(key)
                if stats:
                    try:
                        wr = float(stats.get('wr') or stats.get('win_rate') or 0)
                        games = int(stats.get('games') or 0)
                        curr_wins = int(stats.get('wins', 0))
                        expected_wins = round(games * (wr / 100))
                    except ValueError:
                        continue
                    
                    if abs(curr_wins - expected_wins) > 1:
                        ColoredLogger.warn(f"🔧 [HEALER] Repairing {hero} {key}: {curr_wins}->{expected_wins} wins", "HEAL")
                        stats['wins'] = expected_wins
                        stats['losses'] = games - expected_wins
                        repaired = True
        
        if repaired:
            self.db.set_kv('player_profile', profile)
            # Notify API to refresh if up
            try: requests.post(f"{self.api_url}/api/refresh_context", timeout=2)
            except: pass

    def recover_failed_analyses(self):
        """Detect 'ANALYSIS FAILED' matches and trigger re-analysis."""
        matches = self.db.get_matches(limit=50) # Check recent
        for match in matches:
            analysis = match.get('analysis', {})
            if isinstance(analysis, dict) and analysis.get('verdict') == "ANALYSIS FAILED":
                match_id = match.get('id')
                ColoredLogger.processing(f"🧠 [HEALER] Triggering re-analysis for Match {match_id}...", "HEAL")
                try:
                    # Use internal script to re-process
                    subprocess.run([sys.executable, f"{PROJECT_ROOT}/scripts/trigger_reanalysis.py", "--match_id", str(match_id)], capture_output=True)
                except Exception as e:
                    ColoredLogger.error(f"Failed to trigger re-analysis: {e}", "HEAL")

    def get_latest_version(self):
        """Fetch current PIPELINE_VERSION from api_server."""
        try:
            # Dynamic import to avoid circular dependencies if any
            import api_server
            return getattr(api_server, 'PIPELINE_VERSION', '1.0.0')
        except:
            return "1.0.0"

    def heal_outdated_pipelines(self):
        """Detect and re-analyze matches from older pipeline versions."""
        latest = self.get_latest_version()
        matches = self.db.get_matches(limit=50)
        
        for match in matches:
            m_id = match.get('id')
            m_version = match.get('pipeline_version') or '1.0.0'
            m_map = match.get('map', '')
            
            # Logic Upgrade: BoE matches with version < 2.1.0 are inherently broken (missing participation)
            should_heal = False
            
            if m_version < "2.1.0" and m_map == "Battlefield of Eternity":
                ColoredLogger.warn(f"🎯 [HEALER] BoE Match {m_id} uses legacy version {m_version}. Scheduling re-analysis...", "HEAL")
                should_heal = True
            elif m_version < latest:
                # Optional: Gradually update all matches to latest version
                # For now, let's just stick to critical ones like BoE to save tokens/time
                pass
                
            if should_heal:
                try:
                    subprocess.run([sys.executable, f"{PROJECT_ROOT}/scripts/trigger_reanalysis.py", "--match_id", str(m_id)], capture_output=True)
                except Exception as e:
                    ColoredLogger.error(f"Failed to heal BoE match: {e}", "HEAL")

    def run(self):
        # PID Lock to prevent recursive healers
        my_pid = os.getpid()
        healer_pid_file = os.path.join(PROJECT_ROOT, ".healer.pid")
        
        if os.path.exists(healer_pid_file):
            try:
                with open(healer_pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                os.kill(old_pid, 0)
                # If we reach here, process exists. Exit to avoid duplicates.
                return
            except (ProcessLookupError, ValueError, OSError):
                pass # Stale PID
        
        with open(healer_pid_file, 'w') as f:
            f.write(str(my_pid))

        ColoredLogger.success("🧊 Cerebrate Healer Protocol: ACTIVE", "HEAL")
        ColoredLogger.info("⏳ Healer observing initialization (30s delay)...", "HEAL")
        time.sleep(30) # Delay start to avoid race conditions with start_server.sh
        while True:
            try:
                # 1. API Health Check
                if not self.check_api_health():
                    ColoredLogger.error("🚨 API DOWN. Attempting emergency restart...", "HEAL")
                    # Use a lock-file to ensure only one process triggers restart
                    restart_lock = os.path.join(PROJECT_ROOT, ".restart.lock")
                    if not os.path.exists(restart_lock):
                        with open(restart_lock, 'w') as f: f.write(str(time.time()))
                        subprocess.run(["./stop_server.sh"], cwd=PROJECT_ROOT)
                        # Don't use start_server.sh which starts the healer again
                        # Use a separate background starter or just wait for the user
                        ColoredLogger.warn("📡 Server stopped. Please run ./start_server.sh manually if services don't recover.", "HEAL")
                        os.remove(restart_lock)
                    time.sleep(60)
                
                # 2. Daily/Hourly Integrity Check
                curr_time = time.time()
                if curr_time - self.last_integrity_check > 3600: # Every hour
                    self.repair_data_integrity()
                    self.heal_outdated_pipelines() # Check for version drifts
                    self.last_integrity_check = curr_time
                
                # 3. Pipeline Heartbeat (Watch for crashed sub-processes)
                self.monitor_watcher()
                
                # 4. Ongoing Analysis Recovery (Failed Verdicts)
                self.recover_failed_analyses()
                
                # 5. Heartbeat Log (for API transparency)
                with open(os.path.join(PROJECT_ROOT, "healer.log"), "w") as f:
                    f.write(f"HEALER_ACTIVE: {datetime.now().isoformat()}\n")
                
            except Exception as e:
                ColoredLogger.error(f"Healer Loop Error: {e}", "HEAL")
                
            time.sleep(self.check_interval)

if __name__ == "__main__":
    healer = CerebrateHealer()
    healer.run()
