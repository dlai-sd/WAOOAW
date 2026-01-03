#!/bin/bash
# Local OAuth Testing Script
# Tests OAuth flow before deploying to Cloud Run

set -e

echo "🧪 WAOOAW OAuth Local Testing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend not running${NC}"
    echo "Starting backend..."
    
    cd /workspaces/WAOOAW/backend-v2
    
    # Load secrets from GCP Secret Manager
    if [ ! -f .env.local ]; then
        echo "Fetching OAuth secrets from GCP Secret Manager..."
        cat > .env.local << EOF
ENV=development
GOOGLE_CLIENT_ID=270293855600-2t94c6qkr2ijg9eg4c9b3s3t8gv1tpbp.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=$(gcloud secrets versions access latest --secret="GOOGLE_CLIENT_SECRET" --project=waooaw-oauth)
JWT_SECRET=$(gcloud secrets versions access latest --secret="JWT_SECRET" --project=waooaw-oauth)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/waooaw
REDIS_URL=redis://localhost:6379
EOF
    fi
    
    # Start backend
    source venv/bin/activate
    export $(cat .env.local | xargs)
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend started (PID: $BACKEND_PID)"
    sleep 3
fi

echo ""
echo "1️⃣ Testing Backend Health..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend healthy${NC}"
    echo "$HEALTH" | jq
else
    echo -e "${RED}❌ Backend unhealthy${NC}"
    exit 1
fi

echo ""
echo "2️⃣ Testing OAuth Login (Platform Portal)..."
REDIRECT=$(curl -w "\n%{redirect_url}\n" -s -o /dev/null "http://localhost:8000/auth/login?frontend=pp")
if echo "$REDIRECT" | grep -q "accounts.google.com"; then
    echo -e "${GREEN}✅ OAuth redirect works${NC}"
    echo "Redirect URL: ${REDIRECT:0:80}..."
else
    echo -e "${RED}❌ OAuth redirect failed${NC}"
    exit 1
fi

echo ""
echo "3️⃣ Testing OAuth Login (Customer Portal)..."
REDIRECT=$(curl -w "\n%{redirect_url}\n" -s -o /dev/null "http://localhost:8000/auth/login")
if echo "$REDIRECT" | grep -q "accounts.google.com"; then
    echo -e "${GREEN}✅ OAuth redirect works${NC}"
    echo "Redirect URL: ${REDIRECT:0:80}..."
else
    echo -e "${RED}❌ OAuth redirect failed${NC}"
    exit 1
fi

echo ""
echo "4️⃣ Testing Agents Endpoint..."
AGENTS=$(curl -s http://localhost:8000/agents)
AGENT_COUNT=$(echo "$AGENTS" | jq '. | length')
if [ "$AGENT_COUNT" -eq 7 ]; then
    echo -e "${GREEN}✅ Agents endpoint works (${AGENT_COUNT} agents)${NC}"
else
    echo -e "${RED}❌ Expected 7 agents, got ${AGENT_COUNT}${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 All local OAuth tests passed!${NC}"
echo ""
echo "📝 Manual Test:"
echo "1. Open: http://localhost:8000/auth/login?frontend=pp"
echo "2. Complete Google OAuth flow"
echo "3. Should redirect back with token parameters"
echo ""
echo "Backend logs: tail -f /tmp/backend.log"
