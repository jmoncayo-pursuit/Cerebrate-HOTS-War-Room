#!/bin/bash

# Nexus Command Lab - Stop All Services

echo "🛑 Stopping Nexus Command Lab..."
echo ""

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

stopped_count=0

# Stop Processes by PID (if exists)
for service in "server" "watcher" "healer"; do
    PID_FILE="logs/pids/${service}.pid"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            kill $PID 2>/dev/null
            echo -e "${GREEN}✅ Stopped ${service} (PID: $PID)${NC}"
            stopped_count=$((stopped_count + 1))
        fi
        rm "$PID_FILE"
    fi
done

# Kill any remaining processes on relevant ports
for port in 5001 8000 5173; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        echo -e "${YELLOW}⚠️  Killed stray process on port $port${NC}"
        stopped_count=$((stopped_count + 1))
    fi
done

# Force kill any remaining python workers
pkill -f replay_watcher.py 2>/dev/null && echo -e "${GREEN}✅ Stopped Replay Watcher${NC}"
pkill -f nexus_healer.py 2>/dev/null && echo -e "${GREEN}✅ Stopped Healer Protocol${NC}"

echo ""
if [ $stopped_count -eq 0 ]; then
    echo "ℹ️  No core services were running"
else
    echo -e "${GREEN}✅ Stopped $stopped_count service(s)${NC}"
fi
