#!/bin/bash

# Clean shutdown handler
cleanup() {
    echo ""
    echo "🛑 Shutting down War Room..."
    # Kill all child processes
    pkill -P $$ 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Kill existing processes
export API_PORT=5001
lsof -i :${API_PORT},5173 -t | xargs kill -9 2>/dev/null || true
pkill -9 -f replay_watcher.py 2>/dev/null || true
pkill -9 -f cerebrate_healer.py 2>/dev/null || true

# Start services with concurrently (suppress Python tracebacks on exit)
npx concurrently --raw --kill-others false \
  "vite" \
  "python3 -u api_server.py" \
  "python3 -u replay_watcher.py" \
  "python3 -u scripts/cerebrate_healer.py" \
  "./scripts/startup_banner.sh" \
  -c "magenta,yellow,blue,cyan,green,red" \
  --names "FRONT,API,WATCH,HEAL,INFO"
