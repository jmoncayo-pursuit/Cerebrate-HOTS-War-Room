#!/bin/bash

# Clean shutdown handler
cleanup() {
    echo ""
    echo "🛑 Shutting down Nexus Command Lab..."
    # Kill all child processes
    pkill -P $$ 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Kill existing processes
export API_PORT=8000
lsof -i :${API_PORT},5173 -t | xargs kill -9 2>/dev/null || true
pkill -9 -f replay_watcher.py 2>/dev/null || true
pkill -9 -f nexus_healer.py 2>/dev/null || true

# Start services with concurrently
npx concurrently --raw --kill-others false \
  "vite" \
  "./venv/bin/python3 -u api_server.py" \
  "./venv/bin/python3 -u replay_watcher.py" \
  "./venv/bin/python3 -u scripts/nexus_healer.py" \
  "./scripts/startup_banner.sh" \
  -c "magenta,blue,cyan,green,yellow" \
  --names "FRONT,API,WATCH,HEAL,INFO"
