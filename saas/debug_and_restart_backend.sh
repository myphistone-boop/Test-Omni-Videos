#!/bin/bash
#
# Debug and Restart Backend Script
# Diagnoses crash issues and cleanly restarts the backend
#

set -e

echo "=========================================="
echo "🔍 BACKEND DIAGNOSTICS & RESTART"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
BACKEND_DIR="/home/shorts/Test-Omni-Videos/saas/backend"
LOG_FILE="/var/log/shorts-backend.log"

echo -e "${BLUE}[STEP 1]${NC} Checking crash logs..."
echo "=========================================="
if [ -f "$LOG_FILE" ]; then
    echo "Last 50 lines of backend log:"
    tail -50 "$LOG_FILE"
    echo ""
    echo "Errors found:"
    grep -i "error\|exception\|traceback" "$LOG_FILE" | tail -20 || echo "No obvious errors in log"
else
    echo -e "${YELLOW}⚠️  Log file not found: $LOG_FILE${NC}"
fi
echo ""

echo -e "${BLUE}[STEP 2]${NC} Finding all running backend processes..."
echo "=========================================="
echo "Processes matching 'python.*main' or 'uvicorn':"
ps aux | grep -E 'python.*main|uvicorn' | grep -v grep || echo "No backend processes found"
echo ""

echo -e "${BLUE}[STEP 3]${NC} Checking what's listening on port 8000..."
echo "=========================================="
lsof -i :8000 2>/dev/null || echo "Nothing listening on port 8000"
echo ""

echo -e "${BLUE}[STEP 4]${NC} Killing ALL backend processes..."
echo "=========================================="
pkill -9 -f "main.py" 2>/dev/null && echo -e "${GREEN}✅ Killed main.py processes${NC}" || echo "No main.py processes to kill"
pkill -9 -f "uvicorn" 2>/dev/null && echo -e "${GREEN}✅ Killed uvicorn processes${NC}" || echo "No uvicorn processes to kill"
sleep 2
echo ""

echo -e "${BLUE}[STEP 5]${NC} Verifying all processes are gone..."
echo "=========================================="
REMAINING=$(ps aux | grep -E 'python.*main|uvicorn' | grep -v grep | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo -e "${RED}❌ WARNING: $REMAINING processes still running!${NC}"
    ps aux | grep -E 'python.*main|uvicorn' | grep -v grep
    echo ""
    echo "Trying harder with kill -9..."
    ps aux | grep -E 'python.*main|uvicorn' | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true
    sleep 2
else
    echo -e "${GREEN}✅ All processes cleaned up${NC}"
fi
echo ""

echo -e "${BLUE}[STEP 6]${NC} Checking Python dependencies..."
echo "=========================================="
cd "$BACKEND_DIR"
python3 -c "import fastapi; print('✅ FastAPI:', fastapi.__version__)" 2>&1
python3 -c "import yt_dlp; print('✅ yt-dlp installed')" 2>&1
python3 -c "import youtube_downloader; print('✅ youtube_downloader module OK')" 2>&1
echo ""

echo -e "${BLUE}[STEP 7]${NC} Testing main.py syntax..."
echo "=========================================="
python3 -m py_compile main.py && echo -e "${GREEN}✅ Syntax OK${NC}" || echo -e "${RED}❌ Syntax error!${NC}"
echo ""

echo -e "${BLUE}[STEP 8]${NC} Starting backend (foreground test)..."
echo "=========================================="
echo "Testing startup for 5 seconds..."
timeout 5 python3 main.py 2>&1 | head -20 || true
echo ""

echo -e "${BLUE}[STEP 9]${NC} Starting backend in background..."
echo "=========================================="
# Clear old log
> "$LOG_FILE"

# Start in background
cd "$BACKEND_DIR"
nohup python3 main.py > "$LOG_FILE" 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✅ Backend started with PID: $BACKEND_PID${NC}"
echo "Waiting 3 seconds for startup..."
sleep 3
echo ""

echo -e "${BLUE}[STEP 10]${NC} Verifying backend is running..."
echo "=========================================="
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✅ Backend process is running (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}❌ Backend crashed immediately!${NC}"
    echo "Last 30 lines of log:"
    tail -30 "$LOG_FILE"
    exit 1
fi
echo ""

echo -e "${BLUE}[STEP 11]${NC} Testing API endpoint..."
echo "=========================================="
sleep 2  # Give it a bit more time
curl -s http://localhost:8000/ | python3 -m json.tool || echo "Failed to connect"
echo ""

echo -e "${BLUE}[STEP 12]${NC} Testing /api/process endpoint..."
echo "=========================================="
echo "Creating test job..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/process \
  -F "video_url=https://www.youtube.com/watch?v=dQw4w9WgXcQ" \
  -F "language=fr" \
  -F "transcription_mode=youtube_subs")

echo "$RESPONSE" | python3 -m json.tool

# Check if message contains "mode public" (correct) or "Cookie Pool" (wrong)
if echo "$RESPONSE" | grep -q "mode public"; then
    echo ""
    echo -e "${GREEN}✅✅✅ SUCCESS! Backend is running NEW code (mode public)${NC}"
elif echo "$RESPONSE" | grep -q "Cookie Pool"; then
    echo ""
    echo -e "${RED}❌❌❌ ERROR! Backend is still running OLD code (Cookie Pool)${NC}"
    echo "This suggests the code wasn't properly updated or the wrong directory is being used"
else
    echo ""
    echo -e "${YELLOW}⚠️  Unexpected response - check output above${NC}"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ DIAGNOSTICS COMPLETE${NC}"
echo "=========================================="
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Log file: $LOG_FILE"
echo "Backend dir: $BACKEND_DIR"
echo ""
echo "To monitor logs:"
echo "  tail -f $LOG_FILE"
echo ""
echo "To stop backend:"
echo "  kill $BACKEND_PID"
echo ""
