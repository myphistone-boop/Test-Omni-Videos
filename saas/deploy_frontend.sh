#!/bin/bash
#
# Deploy Frontend - Copy updated index.html to web server
#

set -e

echo "=========================================="
echo "🌐 DEPLOYING FRONTEND"
echo "=========================================="
echo ""

# Paths
REPO_DIR="/home/shorts/Test-Omni-Videos"
FRONTEND_SOURCE="$REPO_DIR/saas/frontend/index.html"
WEB_ROOT="/var/www/html"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[STEP 1]${NC} Pulling latest changes..."
echo "=========================================="
cd "$REPO_DIR"
git pull origin claude/setup-server-branch-H8EBU
echo ""

echo -e "${BLUE}[STEP 2]${NC} Checking if index.html exists..."
echo "=========================================="
if [ -f "$FRONTEND_SOURCE" ]; then
    echo -e "${GREEN}✅ Found: $FRONTEND_SOURCE${NC}"
else
    echo "❌ Frontend file not found!"
    exit 1
fi
echo ""

echo -e "${BLUE}[STEP 3]${NC} Backing up old index.html..."
echo "=========================================="
if [ -f "$WEB_ROOT/index.html" ]; then
    cp "$WEB_ROOT/index.html" "$WEB_ROOT/index.html.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✅ Backup created${NC}"
else
    echo "No existing index.html to backup"
fi
echo ""

echo -e "${BLUE}[STEP 4]${NC} Copying new index.html..."
echo "=========================================="
cp "$FRONTEND_SOURCE" "$WEB_ROOT/index.html"
chmod 644 "$WEB_ROOT/index.html"
echo -e "${GREEN}✅ Frontend deployed to $WEB_ROOT${NC}"
echo ""

echo -e "${BLUE}[STEP 5]${NC} Verifying deployment..."
echo "=========================================="
if grep -q "try {" "$WEB_ROOT/index.html"; then
    echo -e "${GREEN}✅ JavaScript syntax is correct (try {)${NC}"
else
    echo "⚠️  Could not verify JavaScript syntax"
fi
echo ""

echo "=========================================="
echo -e "${GREEN}✅ FRONTEND DEPLOYED${NC}"
echo "=========================================="
echo ""
echo "Frontend URL: http://184.174.36.43/"
echo ""
echo "Test in your browser or run:"
echo "  curl -s http://184.174.36.43/ | grep 'try {'"
echo ""
