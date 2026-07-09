#!/usr/bin/env bash
# =====================================================================
# Quantigen AI — Universal One-Click Production Launcher (Linux/macOS)
# =====================================================================

set -e

echo -e "\033[0;36m=====================================================================\033[0m"
echo -e "\033[1;37m         Quantigen AI — Universal Production Launcher\033[0m"
echo -e "\033[0;36m=====================================================================\033[0m\n"

# 1. Build Production Single Page Application
echo -e "\033[1;33m[1/2] Compiling Production Frontend (React 18 + Vite)...\033[0m"
cd "$(dirname "$0")/frontend"
npm run build
cd ..

# 2. Detect Local Network IPv4 Address
LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")

# 3. Launch Unified Production Server
echo -e "\n\033[1;32m[2/2] Launching Quantigen AI Unified Server on port 8000...\033[0m"
echo -e "\033[1;30m---------------------------------------------------------------------\033[0m"
echo -e "  -> Local Access:   \033[1;36mhttp://localhost:8000\033[0m"
echo -e "  -> Network Access: \033[1;36mhttp://${LAN_IP}:8000\033[0m"
echo -e "\033[1;30m---------------------------------------------------------------------\033[0m"
echo -e "\033[1;33mQuantigen AI is now running universally! Press Ctrl+C to stop.\033[0m\n"

# Open browser if available
if command -v xdg-open &> /dev/null; then
    (sleep 2 && xdg-open "http://localhost:8000") &
elif command -v open &> /dev/null; then
    (sleep 2 && open "http://localhost:8000") &
fi

# Start FastAPI/Uvicorn server
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
