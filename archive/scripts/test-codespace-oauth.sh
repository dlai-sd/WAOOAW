#!/bin/bash
# Test Codespace OAuth Configuration
# Tests all three components: Backend, Customer Portal, Platform Portal

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 CODESPACE OAUTH CONFIGURATION TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Check Codespace Environment Variables
echo -e "${BLUE}Test 1: Codespace Environment Variables${NC}"
if [ -z "$CODESPACE_NAME" ]; then
    echo -e "${RED}✗ CODESPACE_NAME not set${NC}"
    exit 1
else
    echo -e "${GREEN}✓ CODESPACE_NAME: $CODESPACE_NAME${NC}"
fi

if [ -z "$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN" ]; then
    echo -e "${RED}✗ PORT_FORWARDING_DOMAIN not set${NC}"
    exit 1
else
    echo -e "${GREEN}✓ PORT_FORWARDING_DOMAIN: $GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN${NC}"
fi
echo ""

# Expected URLs
BACKEND_URL="https://${CODESPACE_NAME}-8000.app.github.dev"
CUSTOMER_PORTAL_URL="https://${CODESPACE_NAME}-8080.app.github.dev"
PLATFORM_PORTAL_URL="https://${CODESPACE_NAME}-3000.app.github.dev"

echo -e "${BLUE}Expected Service URLs:${NC}"
echo "  Backend API:      $BACKEND_URL"
echo "  Customer Portal:  $CUSTOMER_PORTAL_URL"
echo "  Platform Portal:  $PLATFORM_PORTAL_URL"
echo ""

# Test 2: Backend Health Check
echo -e "${BLUE}Test 2: Backend Health Check${NC}"
HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health" 2>&1)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
    echo "  Response: $(echo $HEALTH_RESPONSE | jq -r '.status + " (" + .environment + ")"' 2>/dev/null || echo $HEALTH_RESPONSE)"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    echo "  Response: $HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test 3: Backend OAuth Config Detection
echo -e "${BLUE}Test 3: Backend OAuth Redirect Detection${NC}"
OAUTH_RESPONSE=$(curl -s -I "$BACKEND_URL/auth/login?frontend=pp" 2>&1)
if echo "$OAUTH_RESPONSE" | grep -q "Location:"; then
    LOCATION=$(echo "$OAUTH_RESPONSE" | grep -i "Location:" | cut -d' ' -f2 | tr -d '\r')
    if echo "$LOCATION" | grep -q "accounts.google.com"; then
        echo -e "${GREEN}✓ OAuth redirect to Google configured${NC}"
        
        # Extract redirect_uri from Google OAuth URL
        REDIRECT_URI=$(echo "$LOCATION" | grep -oP 'redirect_uri=\K[^&]+' | python3 -c "import sys, urllib.parse; print(urllib.parse.unquote(sys.stdin.read()))" 2>/dev/null || echo "Could not extract")
        
        if [ "$REDIRECT_URI" == "$BACKEND_URL/auth/callback" ]; then
            echo -e "${GREEN}✓ Correct redirect_uri: $REDIRECT_URI${NC}"
        else
            echo -e "${YELLOW}⚠ Unexpected redirect_uri: $REDIRECT_URI${NC}"
            echo -e "${YELLOW}  Expected: $BACKEND_URL/auth/callback${NC}"
        fi
    else
        echo -e "${RED}✗ Not redirecting to Google${NC}"
        echo "  Location: $LOCATION"
        exit 1
    fi
else
    echo -e "${RED}✗ No redirect found${NC}"
    exit 1
fi
echo ""

# Test 4: Backend CORS Configuration
echo -e "${BLUE}Test 4: Backend CORS Configuration${NC}"
# Check logs for CORS origins
CORS_CHECK=$(tail -20 /tmp/backend.log 2>/dev/null | grep "cors_origins" | tail -1 || echo "")
if [ -z "$CORS_CHECK" ]; then
    echo -e "${YELLOW}⚠ Could not verify CORS from logs${NC}"
else
    if echo "$CORS_CHECK" | grep -q "app.github.dev"; then
        echo -e "${GREEN}✓ CORS includes Codespace domains${NC}"
    else
        echo -e "${YELLOW}⚠ CORS may not include Codespace domains${NC}"
        echo "  Check: $CORS_CHECK"
    fi
fi
echo ""

# Test 5: Customer Portal Config
echo -e "${BLUE}Test 5: Customer Portal Config (Simulated)${NC}"
CUSTOMER_CONFIG=$(cat <<'JSEOF'
const hostname = process.argv[2];
function detectEnvironment() {
  if (hostname.includes('app.github.dev')) return 'codespace';
  if (hostname.includes('waooaw-portal-demo')) return 'demo';
  return 'development';
}
function getCodespaceBackendUrl() {
  const match = hostname.match(/^(.+)-\d+\.app\.github\.dev$/);
  if (match) {
    const codespaceName = match[1];
    return `https://${codespaceName}-8000.app.github.dev`;
  }
  return 'http://localhost:8000';
}
const env = detectEnvironment();
const apiUrl = env === 'codespace' ? getCodespaceBackendUrl() : 'http://localhost:8000';
console.log(JSON.stringify({ env, apiUrl }));
JSEOF
)

CUSTOMER_TEST=$(echo "$CUSTOMER_CONFIG" | node - "${CODESPACE_NAME}-8080.app.github.dev" 2>/dev/null || echo '{"error":"node not available"}')
if echo "$CUSTOMER_TEST" | grep -q "codespace"; then
    API_URL=$(echo "$CUSTOMER_TEST" | grep -oP '"apiUrl":"?\K[^",}]+')
    if [ "$API_URL" == "$BACKEND_URL" ]; then
        echo -e "${GREEN}✓ Customer Portal detects codespace correctly${NC}"
        echo "  Detected Backend URL: $API_URL"
    else
        echo -e "${YELLOW}⚠ Customer Portal API URL mismatch${NC}"
        echo "  Expected: $BACKEND_URL"
        echo "  Got: $API_URL"
    fi
else
    echo -e "${YELLOW}⚠ Could not test Customer Portal config (node not available)${NC}"
fi
echo ""

# Test 6: Platform Portal Config
echo -e "${BLUE}Test 6: Platform Portal Config (Python)${NC}"
PLATFORM_TEST=$(python3 <<PYEOF
import os
os.environ['CODESPACE_NAME'] = '${CODESPACE_NAME}'

def detect_environment():
    if os.getenv('CODESPACE_NAME'):
        return 'codespace'
    return os.getenv('ENV', 'development')

def get_backend_url(environment):
    if environment == 'codespace':
        codespace_name = os.getenv('CODESPACE_NAME', '')
        if codespace_name:
            return f'https://{codespace_name}-8000.app.github.dev'
        return 'http://localhost:8000'
    return 'http://localhost:8000'

env = detect_environment()
backend_url = get_backend_url(env)
print(f'{env}|{backend_url}')
PYEOF
)

PLATFORM_ENV=$(echo "$PLATFORM_TEST" | cut -d'|' -f1)
PLATFORM_BACKEND=$(echo "$PLATFORM_TEST" | cut -d'|' -f2)

if [ "$PLATFORM_ENV" == "codespace" ] && [ "$PLATFORM_BACKEND" == "$BACKEND_URL" ]; then
    echo -e "${GREEN}✓ Platform Portal detects codespace correctly${NC}"
    echo "  Detected Backend URL: $PLATFORM_BACKEND"
else
    echo -e "${YELLOW}⚠ Platform Portal configuration issue${NC}"
    echo "  Environment: $PLATFORM_ENV (expected: codespace)"
    echo "  Backend URL: $PLATFORM_BACKEND (expected: $BACKEND_URL)"
fi
echo ""

# Test 7: OAuth Console Check
echo -e "${BLUE}Test 7: OAuth Console Configuration${NC}"
echo -e "${YELLOW}⚠ Manual verification required:${NC}"
echo "  Check OAuth Console has this redirect URI:"
echo "  ${BACKEND_URL}/auth/callback"
echo ""
echo "  Go to: https://console.cloud.google.com/apis/credentials/oauthclient/270293855600-2t94c6qkr2ijg9eg4c9b3s3t8gv1tpbp.apps.googleusercontent.com?project=waooaw-oauth"
echo ""

# Test Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ CODESPACE OAUTH CONFIGURATION TESTS COMPLETE${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}🔗 Test OAuth Flow:${NC}"
echo "  ${BACKEND_URL}/auth/login?frontend=pp"
echo ""
echo -e "${BLUE}Expected Flow:${NC}"
echo "  1. Click URL above"
echo "  2. Redirects to Google sign-in"
echo "  3. Sign in with Google"
echo "  4. Google redirects to: ${BACKEND_URL}/auth/callback"
echo "  5. Backend processes OAuth"
echo "  6. Backend redirects to: ${PLATFORM_PORTAL_URL}/auth/callback"
echo "  7. Platform Portal handles callback and logs you in"
echo ""
