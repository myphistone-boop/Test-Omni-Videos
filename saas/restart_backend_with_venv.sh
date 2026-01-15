#!/bin/bash
#
# Restart Backend with Virtualenv
# Properly restarts the backend using the existing virtualenv
#

set -e

echo "=========================================="
echo "🚀 BACKEND RESTART (with virtualenv)"
echo "=========================================="
echo ""

# Paths
BACKEND_DIR="/home/shorts/Test-Omni-Videos/saas/backend"
VENV_DIR="$BACKEND_DIR/venv"
LOG_FILE="/home/shorts/api.log"
ERROR_LOG="/home/shorts/api-error.log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[STEP 1]${NC} Killing old backend processes..."
echo "=========================================="
pkill -9 -f "gunicorn.*main:app" 2>/dev/null && echo -e "${GREEN}✅ Killed gunicorn${NC}" || echo "No gunicorn to kill"
pkill -9 -f "uvicorn" 2>/dev/null && echo -e "${GREEN}✅ Killed uvicorn${NC}" || echo "No uvicorn to kill"
sleep 2
echo ""

echo -e "${BLUE}[STEP 2]${NC} Verifying virtualenv exists..."
echo "=========================================="
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✅ Virtualenv found: $VENV_DIR${NC}"
else
    echo -e "${RED}❌ Virtualenv not found!${NC}"
    echo "Creating new virtualenv..."
    python3 -m venv "$VENV_DIR"
    echo "Installing dependencies..."
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/../../requirements.txt"
fi
echo ""

echo -e "${BLUE}[STEP 3]${NC} Checking FastAPI is installed in venv..."
echo "=========================================="
"$VENV_DIR/bin/python3" -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)" 2>&1
"$VENV_DIR/bin/python3" -c "import yt_dlp; print('✅ yt-dlp installed')" 2>&1
"$VENV_DIR/bin/python3" -c "import gunicorn; print('✅ Gunicorn installed')" 2>&1
echo ""

echo -e "${BLUE}[STEP 4]${NC} Testing main.py syntax with venv python..."
echo "=========================================="
cd "$BACKEND_DIR"
"$VENV_DIR/bin/python3" -m py_compile main.py && echo -e "${GREEN}✅ Syntax OK${NC}" || echo -e "${RED}❌ Syntax error!${NC}"
echo ""

echo -e "${BLUE}[STEP 5]${NC} Clearing old logs..."
echo "=========================================="
> "$LOG_FILE"
> "$ERROR_LOG"
echo -e "${GREEN}✅ Logs cleared${NC}"
echo ""

echo -e "${BLUE}[STEP 6]${NC} Starting backend with gunicorn (using venv)..."
echo "=========================================="
cd "$BACKEND_DIR"

# Start gunicorn in background
# TOUT va dans un seul fichier : /home/shorts/shorts-backend-full.log
FULL_LOG="/home/shorts/shorts-backend-full.log"
> "$FULL_LOG"  # Clear log

nohup "$VENV_DIR/bin/gunicorn" main:app \
    -w 1 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --log-level debug \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    > "$FULL_LOG" 2>&1 &

BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started with PID: $BACKEND_PID${NC}"
echo "Waiting 5 seconds for startup..."
sleep 5
echo ""

echo -e "${BLUE}[STEP 7]${NC} Verifying backend is running..."
echo "=========================================="
if pgrep -f "gunicorn.*main:app" > /dev/null; then
    ACTUAL_PID=$(pgrep -f "gunicorn.*main:app" | head -1)
    echo -e "${GREEN}✅ Backend process running (PID: $ACTUAL_PID)${NC}"
else
    echo -e "${RED}❌ Backend not running!${NC}"
    echo "Error log:"
    cat "$ERROR_LOG"
    exit 1
fi
echo ""

echo -e "${BLUE}[STEP 8]${NC} Testing API endpoint..."
echo "=========================================="
sleep 2
curl -s http://localhost:8000/ | python3 -m json.tool || echo "Failed to connect"
echo ""

echo -e "${BLUE}[STEP 9]${NC} Testing /api/process with mode public..."
echo "=========================================="
RESPONSE=$(curl -s -X POST http://localhost:8000/api/process \
  -F "video_url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  -F "language=fr" \
  -F "transcription_mode=youtube_subs")

echo "$RESPONSE" | python3 -m json.tool

# Check message
if echo "$RESPONSE" | grep -q "mode public"; then
    echo ""
    echo -e "${GREEN}✅✅✅ SUCCESS! Backend running NEW code (mode public)${NC}"
elif echo "$RESPONSE" | grep -q "Cookie Pool"; then
    echo ""
    echo -e "${RED}❌ Backend still showing OLD code (Cookie Pool)${NC}"
    echo "The venv might have cached .pyc files. Clearing..."
    find "$BACKEND_DIR" -name "*.pyc" -delete
    find "$BACKEND_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    echo "Please restart the backend again"
else
    echo ""
    echo -e "${YELLOW}⚠️  Unexpected response${NC}"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ BACKEND RESTARTED${NC}"
echo "=========================================="
echo ""
echo "Backend PID: $ACTUAL_PID"
echo "Full log: $FULL_LOG"
echo "Virtualenv: $VENV_DIR"
echo ""
echo "🔍 VOIR TOUS LES LOGS EN TEMPS RÉEL:"
echo "  tail -f $FULL_LOG"
echo ""
echo "Stop backend:"
echo "  pkill -f 'gunicorn.*main:app'"
echo ""
