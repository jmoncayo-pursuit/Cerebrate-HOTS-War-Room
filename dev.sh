#!/bin/bash

# Configuration
CHROME_CANARY="/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"
DEBUG_PORT=56991
PROFILE_DIR="/tmp/chrome-canary-debug"
FRONTEND_URL="http://localhost:5173"
API_URL="http://localhost:8000/api/health"

echo "=================================================="
echo "🚀 INITIATING NEXUS COMMAND LAB ENVIRONMENT 🚀"
echo "=================================================="

# 1. Neural Link Check
echo "[1/3] Establish Neural Link (Chrome Remote Debugging)..."
if lsof -i :$DEBUG_PORT > /dev/null; then
    echo "✅ Neural Link is already active on port $DEBUG_PORT."
else
    echo "⚡ Neural Link inactive. Launching Chrome Canary..."
    
    if [ -f "$CHROME_CANARY" ]; then
        # Launch Canary with remote debugging enabled
        "$CHROME_CANARY" \
            --remote-debugging-port=$DEBUG_PORT \
            --user-data-dir="$PROFILE_DIR" \
            --no-first-run \
            --no-default-browser-check \
            --window-size=1600,1200 \
            --window-position=0,0 \
            "$FRONTEND_URL" \
            "$API_URL" &
            
        # Wait for port to open
        echo "⏳ Waiting for Neural Link to stabilize..."
        TRIES=0
        until lsof -i :$DEBUG_PORT > /dev/null || [ $TRIES -eq 30 ]; do
            sleep 0.5
            ((TRIES++))
            printf "."
        done
        echo ""
        
        if [ $TRIES -eq 30 ]; then
             echo "❌ Failed to establish Neural Link (Chrome didn't start on port $DEBUG_PORT)."
             exit 1
        fi
        echo "✅ Neural Link established on port $DEBUG_PORT."
    else
        echo "❌ Chrome Canary not found."
        echo "   Please install Google Chrome Canary or update the path in this script."
        exit 1
    fi
fi

# 2. Environment Validation
echo "[2/3] Validating Core Systems..."
if [ ! -f "start_server.sh" ]; then
    echo "❌ Critical Error: start_server.sh not found!"
    exit 1
fi

# 3. Hand off to Core Startup
echo "[3/3] Interfacing with Nexus Command Lab..."
echo "🔌 Passing control to Core Startup Script..."
./start_server.sh
