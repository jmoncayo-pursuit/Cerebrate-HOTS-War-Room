#!/bin/bash

# Wait for services to start
sleep 2

# ANSI color codes
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
RESET='\033[0m'

# Display startup banner
echo ""
echo -e "${CYAN}${BOLD}🧊 ═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}${BOLD}   CEREBRATE WAR ROOM - ONLINE${RESET}"
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "   ${MAGENTA}🌐 Frontend:${RESET}  ${GREEN}http://localhost:5173${RESET}"
echo -e "   ${YELLOW}⚡ API:${RESET}       ${GREEN}http://localhost:5001${RESET}"
echo -e "   ${CYAN}👁️  Watcher:${RESET}  ${GREEN}Active${RESET}"
echo ""
echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
echo ""
