#!/bin/bash

# Cerebrate HOTS War Room - Stop All Services

echo "🛑 Stopping Cerebrate HOTS War Room..."
echo ""

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

stopped_count=0

# Stop API Server
if [ -f .api_server.pid ]; then
    PID=$(cat .api_server.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✅ Stopped API Server (PID: $PID)${NC}"
        stopped_count=$((stopped_count + 1))
    fi
    rm .api_server.pid
fi

# Stop Frontend
if [ -f .frontend.pid ]; then
    PID=$(cat .frontend.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✅ Stopped Frontend (PID: $PID)${NC}"
        stopped_count=$((stopped_count + 1))
    fi
    rm .frontend.pid
fi

# Stop Replay Watcher
if [ -f .replay_watcher.pid ]; then
    PID=$(cat .replay_watcher.pid)
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✅ Stopped Replay Watcher (PID: $PID)${NC}"
        stopped_count=$((stopped_count + 1))
    fi
    rm .replay_watcher.pid
fi

# Kill any remaining processes on ports
for port in 5001 8000 5173; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        echo -e "${YELLOW}⚠️  Killed process on port $port${NC}"
        stopped_count=$((stopped_count + 1))
    fi
done

# Kill Watcher and Healer if not caught by PID
pkill -f replay_watcher.py 2>/dev/null && echo -e "${GREEN}✅ Stopped Replay Watcher${NC}"
pkill -f cerebrate_healer.py 2>/dev/null && echo -e "${GREEN}✅ Stopped Healer Protocol${NC}"

echo ""
if [ $stopped_count -eq 0 ]; then
    echo "ℹ️  No services were running"
else
    echo -e "${GREEN}✅ Stopped $stopped_count service(s)${NC}"
fi
