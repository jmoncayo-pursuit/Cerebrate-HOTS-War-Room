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

from api.services.database import DatabaseManager
from api.logger import ColoredLogger
from api.summary_schema import SUMMARY_SCHEMA_VERSION
from api.services.quota_manager import QuotaManager

class CerebrateHealer:
    def __init__(self):
        self.db = DatabaseManager()
        self.api_url = "http://localhost:8000"
        self.last_integrity_check = 0
        self.last_reflection_check = 0
        self.last_evolution_check = 0
        self.last_summary_audit = 0
        self.check_interval = 60 # Check every minute
        # Consumption safety: reuse global quota limits and keep a buffer
        self.quota = QuotaManager()
        # Max number of healer-initiated summary re-audits per day
        self.max_daily_reaudits = int(os.environ.get("HEALER_MAX_DAILY_REAUDITS", "20"))
        # Leave a safety buffer of requests so user actions are never starved
        self.min_quota_buffer = int(os.environ.get("HEALER_QUOTA_BUFFER", "100"))
        self.api_log_path = os.path.join(PROJECT_ROOT, "api_server.log")
        self.diagnostics_dir = os.path.join(PROJECT_ROOT, ".diagnostics")
        os.makedirs(self.diagnostics_dir, exist_ok=True)
        
    def check_api_health(self):
        """Check if the API is responding."""
        try:
            res = requests.get(f"{self.api_url}/api/health", timeout=5)
            if res.status_code == 200:
                data = res.json()
                return data.get("status") == "healthy"
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
        # Use limit=10 to reduce scan impact
        matches = self.db.get_matches(limit=10)
        
        for match in matches:
            # Table uses 'id' but dictionary might have 'match_id' depending on get_matches
            m_id = match.get('id') or match.get('match_id')
            m_version = match.get('pipeline_version') or '1.0.0'
            m_map = match.get('map', '')
            
            should_heal = False
            
            # Logic Upgrade: BoE matches with version < 2.1.0 are inherently broken
            if m_version < "2.1.0" and m_map == "Battlefield of Eternity":
                # Only log if specifically healing (simulated for now since trigger_reanalysis is a stub)
                # ColoredLogger.warn(f"🎯 [HEALER] BoE Match {m_id} uses legacy version. Ready for heal.", "HEAL")
                should_heal = False # Disabled for now to prevent spam until tool is verified
            
            if should_heal and os.path.exists(f"{PROJECT_ROOT}/scripts/trigger_reanalysis.py"):
                try:
                    subprocess.run([sys.executable, f"{PROJECT_ROOT}/scripts/trigger_reanalysis.py", "--match_id", str(m_id)], capture_output=True)
                except:
                    pass

    def heal_invalid_dates(self):
        """
        Compare DB dates to replay filenames. Fix any mismatches.
        """
        fix_script = os.path.join(PROJECT_ROOT, "scripts", "fix_dates.py")
        if os.path.exists(fix_script):
            # Just run fix_dates.py - it handles the comparison logic
            result = subprocess.run([sys.executable, fix_script], capture_output=True, text=True)
            if "Fixed" in result.stdout and "Fixed 0" not in result.stdout:
                ColoredLogger.warn(f"🔧 [HEALER] Date corrections applied", "HEAL")

    def backfill_banner_stats(self):
        """Backfill user_was_banner and enemy_banner_name for existing Storm League matches (carry vs carry)."""
        backfill_script = os.path.join(PROJECT_ROOT, "scripts", "backfill_banner_stats.py")
        if not os.path.exists(backfill_script):
            return
        try:
            result = subprocess.run(
                [sys.executable, backfill_script, "--limit", "100"],
                capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=120
            )
            if result.returncode == 0 and result.stdout and "updated" in result.stdout:
                parts = result.stdout.strip().split()
                n = parts[1] if len(parts) >= 3 and parts[2] == "matches" else "0"
                if n != "0":
                    ColoredLogger.warn(f"🔧 [HEALER] Banner stats backfilled for {n} matches", "HEAL")
        except Exception as e:
            ColoredLogger.error(f"Banner backfill error: {e}", "HEAL")



    def monitor_watcher(self):
        """Ensure the replay watcher process is running."""
        watcher_pid_file = os.path.join(PROJECT_ROOT, ".watcher.pid")
        if os.path.exists(watcher_pid_file):
            try:
                with open(watcher_pid_file, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0) # Check if process exists
                return True
            except (ProcessLookupError, ValueError, OSError):
                pass # Process dead or PID file corrupted
        
        # If we are here, watcher is likely down
        ColoredLogger.warn("👁️ [HEALER] Replay Watcher seems offline. Protocol requires it to be active.", "HEAL")
        return False

    def perform_neural_reflection(self):
        """Monitor logs for exceptions and propose fragments of self-correction."""
        if not os.path.exists(self.api_log_path): return
        
        ColoredLogger.processing("🧠 [HEALER] Initiating Neural Reflection pass...", "HEAL")
        
        try:
            with open(self.api_log_path, 'r') as f:
                # Read last 100 lines
                lines = f.readlines()[-100:]
            
            traceback_lines = []
            capturing = False
            for line in lines:
                if "Traceback" in line:
                    capturing = True
                    traceback_lines = [line]
                elif capturing:
                    traceback_lines.append(line)
                    if not line.startswith(" ") and len(line.strip()) > 0 and "Traceback" not in line:
                        # End of traceback usually
                        if "Error" in line:
                            # We got the error message
                            error_summary = line.strip()
                            self._trigger_diagnostic_reflection(traceback_lines, error_summary)
                            capturing = False
        except Exception as e:
            ColoredLogger.error(f"Reflection Error: {e}", "HEAL")

    def _trigger_diagnostic_reflection(self, traceback, error_msg):
        """Generate a diagnostic report for the detected error."""
        diag_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        diag_file = os.path.join(self.diagnostics_dir, f"error_{diag_id}.json")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "error": error_msg,
            "traceback": "".join(traceback),
            "status": "PROPOSED_PATCH",
            "proposed_remedy": "Recalibrate None-safety in affected module or investigate data drift."
        }
        
        with open(diag_file, 'w') as f:
            json.dump(report, f, indent=4)
        
        ColoredLogger.warn(f"☣️ [HEALER] Critical Exception Detected! Diagnostic Report: {diag_file}", "HEAL")

    def observe_data_centric_evolution(self):
        """Detect Data Drift between Scoreboard and Forensics."""
        ColoredLogger.processing("🧬 [HEALER] Observing Data-Centric Evolution patterns...", "HEAL")
        
        matches = self.db.get_matches(limit=5, include_players=True)
        drift_count = 0
        checked = 0

        for m in matches:
            analysis = m.get('analysis')
            if not isinstance(analysis, dict):
                continue
            forensics = analysis.get('forensics', {})
            highlights = forensics.get('tactical_highlights', [])
            forensic_kills = len([h for h in highlights if h.get('type') == 'KILL'])
            if forensic_kills == 0:
                continue
            checked += 1

            scoreboard_kills = 0
            user_hero = m.get('hero')
            for p in m.get('players') or []:
                if p.get('hero') == user_hero:
                    stats = p.get('stats') or {}
                    if isinstance(stats, str):
                        try:
                            stats = json.loads(stats)
                        except Exception:
                            stats = {}
                    scoreboard_kills = int(stats.get('SoloKill', 0) or 0)
                    break

            if abs(forensic_kills - scoreboard_kills) > 0:
                drift_count += 1

        if checked >= 2 and drift_count >= min(3, checked):
            ColoredLogger.warn(f"📈 [HEALER] Significant Data Drift detected ({drift_count}/{checked} matches). Proposing Heuristic Recalibration.", "HEAL")
            self.db.set_kv('heuristic_recalibration_required', True)

    def audit_summaries(self):
        """
        Identify matches whose summaries were generated under an older schema
        or contain quality issues (e.g. "None detected" critical mistakes)
        so they can be re-audited with the latest detectors and validators.
        """
        try:
            queue = self.db.get_kv('summary_reaudit_queue') or []
            if not isinstance(queue, list):
                queue = []

            matches = self.db.get_matches(limit=25)
            for m in matches:
                m_id = m.get('id') or m.get('match_id')
                if not m_id:
                    continue
                analysis = m.get('analysis') or {}
                if isinstance(analysis, str):
                    try:
                        analysis = json.loads(analysis)
                    except Exception:
                        analysis = {}
                if not isinstance(analysis, dict):
                    continue

                # Check 1: Schema version (legacy summaries)
                version = int(analysis.get('summary_version') or 0)
                needs_reaudit = False
                reason = None
                
                if version < SUMMARY_SCHEMA_VERSION:
                    needs_reaudit = True
                    reason = f"schema v{version} -> v{SUMMARY_SCHEMA_VERSION}"
                
                # Check 2: "None detected" critical mistake (quality violation)
                critical_mistake = analysis.get('critical_mistake', '') or ''
                critical_mistake_lower = critical_mistake.lower().strip()
                none_patterns = [
                    "none detected", "no mistakes", "no mistake", "none found",
                    "no critical mistake", "no errors", "no error", "perfect game"
                ]
                if any(pattern in critical_mistake_lower for pattern in none_patterns):
                    needs_reaudit = True
                    reason = "critical_mistake contains 'None detected' (quality violation)"
                
                if needs_reaudit and m_id not in queue:
                    ColoredLogger.processing(
                        f"🧠 [HEALER] Queuing match {m_id} for summary re-audit ({reason})",
                        "HEAL"
                    )
                    queue.append(m_id)

            self.db.set_kv('summary_reaudit_queue', queue)
        except Exception as e:
            ColoredLogger.error(f"Summary Audit Error: {e}", "HEAL")

    def populate_reparse_queue(self):
        """
        Queue matches lacking draft sequences (picks) or social/draft data (banner).
        Banner can be backfilled from raw_stats.bans; if no bans we need a reparse.
        """
        try:
            queue = self.db.get_kv('reparse_queue') or []
            if not isinstance(queue, list):
                queue = []
            seen = set(queue)
            matches = self.db.get_matches(limit=200, include_details=True)
            for m in matches:
                m_id = m.get('id') or m.get('match_id')
                if not m_id or m_id in seen:
                    continue
                raw = m.get('raw_stats') or {}
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except Exception:
                        raw = {}
                picks = raw.get('picks') if isinstance(raw, dict) else []
                has_picks = bool(picks and len(picks) > 0)
                has_milestones = isinstance(raw, dict) and isinstance(raw.get('level_milestones'), dict) and bool(raw.get('level_milestones'))
                has_banner = m.get('user_was_banner') in (1, True) or (m.get('enemy_banner_name') or "").strip()
                bans = (raw or {}).get('bans') if isinstance(raw, dict) else []
                has_bans = bool(bans)
                need_reparse = (not has_picks) or (not has_milestones) or (not has_banner and not has_bans)
                if need_reparse:
                    ColoredLogger.processing(
                        f"🔄 [HEALER] Queuing match {m_id} for reparse (missing picks or banner data)",
                        "HEAL"
                    )
                    queue.append(m_id)
                    seen.add(m_id)
            self.db.set_kv('reparse_queue', queue)
        except Exception as e:
            ColoredLogger.error(f"Reparse queue populate error: {e}", "HEAL")

    def process_reparse_queue(self, batch_size=1):
        """Pop up to batch_size match IDs from reparse_queue and trigger reparse via API."""
        try:
            queue = self.db.get_kv('reparse_queue') or []
            if not isinstance(queue, list) or not queue:
                return
            to_process = queue[:batch_size]
            removed = set()
            for m_id in to_process:
                try:
                    ColoredLogger.processing(f"🔄 [HEALER] Reparsing match {m_id} (draft/banner refresh).", "HEAL")
                    r = requests.post(
                        f"{self.api_url}/api/reparse_match",
                        json={"match_id": str(m_id)},
                        timeout=60
                    )
                    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                    removed.add(m_id)
                    if not data.get("success"):
                        ColoredLogger.warn(f"Reparse failed for {m_id}: {data.get('error', r.text)}", "HEAL")
                except Exception as api_err:
                    ColoredLogger.error(f"Reparse API error for {m_id}: {api_err}", "HEAL")
                    removed.add(m_id)
            remaining = [q for q in queue if q not in removed]
            self.db.set_kv('reparse_queue', remaining)
        except Exception as e:
            ColoredLogger.error(f"Process reparse queue error: {e}", "HEAL")

    def process_summary_reaudit_queue(self, batch_size=2):
        """
        Pop a small batch of matches from the summary re-audit queue and
        trigger fresh analysis via the API.
        """
        try:
            # 0. Hard daily cap for healer-initiated re-audits (separate from global quota)
            today = datetime.now().strftime("%Y-%m-%d")
            healer_stats = self.db.get_kv('healer_reaudit_stats') or {
                "date": today,
                "count": 0
            }
            if healer_stats.get("date") != today:
                healer_stats = {"date": today, "count": 0}

            if healer_stats["count"] >= self.max_daily_reaudits:
                ColoredLogger.warn(
                    f"🛑 [HEALER] Daily re-audit cap reached "
                    f"({healer_stats['count']}/{self.max_daily_reaudits}). "
                    "Deferring remaining items to preserve quota.",
                    "HEAL"
                )
                self.db.set_kv('healer_reaudit_stats', healer_stats)
                return

            # 1. Respect global quota buffer before spending any remaining calls
            remaining_global = self.quota.get_remaining()
            if remaining_global <= self.min_quota_buffer:
                ColoredLogger.warn(
                    f"🛑 [HEALER] Global quota low "
                    f"({remaining_global} remaining; buffer={self.min_quota_buffer}). "
                    "Pausing summary re-audits so War Room and user actions stay priority.",
                    "HEAL"
                )
                return

            queue = self.db.get_kv('summary_reaudit_queue') or []
            if not isinstance(queue, list) or not queue:
                return

            to_process = queue[:batch_size]
            remaining = queue[batch_size:]

            for m_id in to_process:
                try:
                    ColoredLogger.processing(f"🧠 [HEALER] Re-analyzing match {m_id} for updated summary.", "HEAL")
                    requests.post(
                        f"{self.api_url}/api/analyze_replay",
                        json={"match_id": str(m_id), "force": True},
                        timeout=60
                    )
                    # Record healer-initiated cost against the daily cap
                    healer_stats["count"] += 1
                    # If we hit the cap mid-batch, stop early and keep remaining IDs queued
                    if healer_stats["count"] >= self.max_daily_reaudits:
                        ColoredLogger.warn(
                            f"🛑 [HEALER] Reached daily re-audit cap mid-batch "
                            f"({healer_stats['count']}/{self.max_daily_reaudits}). "
                            "Leaving remaining matches in queue.",
                            "HEAL"
                        )
                        # Put unprocessed IDs back at the front of the queue
                        remaining = to_process[to_process.index(m_id)+1:] + remaining
                        break
                except Exception as api_err:
                    ColoredLogger.error(f"Summary Re-analysis Error for {m_id}: {api_err}", "HEAL")
                    # If API fails, put it back for later
                    remaining.append(m_id)

            # Persist healer consumption stats
            self.db.set_kv('healer_reaudit_stats', healer_stats)
            self.db.set_kv('summary_reaudit_queue', remaining)
        except Exception as e:
            ColoredLogger.error(f"Summary Queue Error: {e}", "HEAL")

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

        # ColoredLogger.success("🧊 Cerebrate Healer Protocol: ACTIVE", "HEAL")
        # ColoredLogger.info("⏳ Healer observing initialization (30s delay)...", "HEAL")
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
                    self.heal_invalid_dates()  # Auto-fix wrong dates
                    self.backfill_banner_stats()  # Backfill banner columns (carry vs carry)
                    self.populate_reparse_queue()  # Queue matches lacking draft picks or banner data
                    # self.heal_outdated_pipelines() # DISABLED - Prevents token usage
                    self.last_integrity_check = curr_time
                
                # 3. Pipeline Heartbeat (Watch for crashed sub-processes)
                self.monitor_watcher()
                
                # 4. Neural Reflection (Every 10 minutes)
                if curr_time - self.last_reflection_check > 600:
                    self.perform_neural_reflection()
                    self.last_reflection_check = curr_time
                
                # 5. Data-Centric Evolution (Every 30 minutes)
                if curr_time - self.last_evolution_check > 1800:
                    self.observe_data_centric_evolution()
                    self.last_evolution_check = curr_time

                # 6. Summary Schema Audit (Every 30 minutes)
                if curr_time - self.last_summary_audit > 1800:
                    self.audit_summaries()
                    self.last_summary_audit = curr_time

                # 7. Process Summary Re-Audit Queue (small batch each cycle)
                self.process_summary_reaudit_queue()

                # 8. Process Reparse Queue (1 match per cycle: draft picks / banner refresh)
                self.process_reparse_queue(batch_size=1)

                # 9. Heartbeat Log (for API transparency)
                with open(os.path.join(PROJECT_ROOT, "healer.log"), "w") as f:
                    f.write(f"HEALER_ACTIVE: {datetime.now().isoformat()}\n")
                
            except Exception as e:
                ColoredLogger.error(f"Healer Loop Error: {e}", "HEAL")
                
            time.sleep(self.check_interval)

if __name__ == "__main__":
    healer = CerebrateHealer()
    healer_pid_file = os.path.join(PROJECT_ROOT, ".healer.pid")
    try:
        healer.run()
    except KeyboardInterrupt:
        from api.logger import ColoredLogger
        ColoredLogger.info("🛑 Healer Protocol stopped by user", "HEAL")
    finally:
        # Cleanup PID file on exit
        if os.path.exists(healer_pid_file):
            try:
                os.remove(healer_pid_file)
            except:
                pass
