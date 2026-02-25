import logging
import time
from flask import request

class ColoredLogger:
    # ANSI Colors
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def get_status_color(code):
        if code < 300: return ColoredLogger.GREEN
        if code < 400: return ColoredLogger.CYAN
        if code < 500: return ColoredLogger.YELLOW
        return ColoredLogger.RED

    @staticmethod
    def setup_flask_logging(app, service_name="API"):
        # Disable default werkzeug logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        @app.before_request
        def start_timer():
            request.start_time = time.time()

        @app.after_request
        def log_request(response):
            # 1. Silencing Polling Noise
            # We skip repetitive GET requests that are successful or cached to keep the terminal clean.
            # We still log them if they FAIL (4xx, 5xx) or are significant mutations (POST, DELETE).
            
            # Paths to silence if success/cached
            SILENT_PATHS = [
                '/health', 
                '/api/health', 
                '/api/usage',  # Polled every 5s by AgentDashboard
                '/api/nexus/agents',  # Polled by AgentDashboard
                '/api/strategies', 
                '/api/roster-constraints', 
                '/api/watcher/status', 
                '/api/match_history', 
                '/api/player_profile',
                '/api/refresh_context',
                '/api/analyze_replay',  # Silent during batch scanning
                '/api/player_interactions',  # Silent polling
                '/api/rejected_replays',  # Frequent polling
                '/api/nexus_config',  # Frequent polling
                '/api/healer/status',  # Healer disabled; silence if still polled
                '/api/data_sources/status',  # Frequent polling
                '/api/data_sources/conflicts'  # Frequent polling
            ]
            
            # Silence successful polling or data fetching
            if request.method in ['GET', 'POST'] and response.status_code in [200, 304]:
                if request.path in SILENT_PATHS or request.path.startswith('/api/data/'):
                    return response
            
            duration = (time.time() - request.start_time) * 1000
            status_code = response.status_code
            color = ColoredLogger.get_status_color(status_code)
            
            # Icon based on status
            # 2xx/3xx ✅, 404 ❓, Others ❌
            if status_code < 400:
                icon = "✅"
            elif status_code == 404:
                icon = "❓"
            else:
                icon = "❌"

            # 2. Removing Redundant Tags
            # We remove the [API] prefix because 'concurrently' already adds it.
            print(f"{icon} {ColoredLogger.BOLD}{request.method:4}{ColoredLogger.RESET} {request.path:30} "
                  f"-> {color}{status_code}{ColoredLogger.RESET} ({duration:4.1f}ms)")
            
            return response

    @staticmethod
    def success(message, service="API"):
        print(f"{ColoredLogger.GREEN}✔ {ColoredLogger.RESET}{message}")

    @staticmethod
    def info(message, service="API"):
        print(f"{ColoredLogger.CYAN}ℹ {ColoredLogger.RESET}{message}")

    @staticmethod
    def warn(message, service="API"):
        print(f"{ColoredLogger.YELLOW}⚠ {ColoredLogger.RESET}{message}")

    @staticmethod
    def error(message, service="API"):
        print(f"{ColoredLogger.RED}✖ {ColoredLogger.RESET}{message}")

    @staticmethod
    def processing(message, service="API"):
        # Premium DX: Moving star for processing
        print(f"{ColoredLogger.MAGENTA}✧ {ColoredLogger.RESET}{message}")

    @staticmethod
    def tier_shift(old_tier, new_tier, reason="Quota Hit"):
        # Elite Fallback Visualization
        print(f"{ColoredLogger.YELLOW}⚡ {ColoredLogger.BOLD}TACTICAL FALLBACK:{ColoredLogger.RESET} {reason} on {old_tier} {ColoredLogger.CYAN}→{ColoredLogger.RESET} Shifting to {ColoredLogger.BOLD}{new_tier}{ColoredLogger.RESET}")

    @staticmethod
    def signal(source, message):
        # Precise Mission Feedback
        print(f"{ColoredLogger.CYAN}📡 {ColoredLogger.BOLD}{source.upper()}:{ColoredLogger.RESET} {message}")
