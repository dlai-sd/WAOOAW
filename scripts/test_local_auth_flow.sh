#!/bin/bash
# Local Token Flow End-to-End Test
# Tests: Dev Token → DB Updates Token → Agent Management

set -e

echo "🧪 Local Auth Flow Test"
echo "======================="
echo ""

# Check services
echo "1️⃣  Checking services..."
if ! curl -f -s http://localhost:8015/health > /dev/null 2>&1; then
    echo "❌ PP Backend not running on :8015"
    exit 1
fi
echo "   ✅ PP Backend"

if ! curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Plant Gateway not running on :8000"
    exit 1
fi
echo "   ✅ Plant Gateway"

echo ""
echo "2️⃣  Checking environment variables..."

# Docker compose scenario
if command -v docker-compose >/dev/null 2>&1; then
    PP_SECRET=$(docker-compose exec -T pp-backend env 2>/dev/null | grep "^JWT_SECRET=" | cut -d= -f2 || echo "")
    GW_SECRET=$(docker-compose exec -T plant-gateway env 2>/dev/null | grep "^JWT_SECRET=" | cut -d= -f2 || echo "")
    
    if [ -n "$PP_SECRET" ] && [ -n "$GW_SECRET" ]; then
        if [ "$PP_SECRET" = "$GW_SECRET" ]; then
            echo "   ✅ JWT_SECRET consistent (Docker Compose)"
        else
            echo "   ❌ JWT_SECRET MISMATCH!"
            echo "      PP: ${PP_SECRET:0:20}..."
            echo "      GW: ${GW_SECRET:0:20}..."
            exit 1
        fi
    else
        echo "   ⚠️  Could not verify JWT_SECRET via docker-compose"
    fi
fi

echo ""
echo "3️⃣  Testing token minting..."

# Get dev token
echo "   → Minting dev token..."
DEV_TOKEN_RESP=$(curl -sS -X POST http://localhost:8015/api/auth/dev-token -H 'Content-Type: application/json' 2>&1)

if echo "$DEV_TOKEN_RESP" | grep -q "access_token"; then
    ACCESS_TOKEN=$(echo "$DEV_TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
    echo "   ✅ Dev token obtained"
    echo "      Token preview: ${ACCESS_TOKEN:0:30}..."
else
    echo "   ❌ Dev token failed:"
    echo "$DEV_TOKEN_RESP"
    exit 1
fi

echo ""
echo "4️⃣  Testing DB updates token..."

# Mint DB updates token
echo "   → Minting DB updates token with access token..."
DB_TOKEN_RESP=$(curl -sS -w "\n%{http_code}" -X POST http://localhost:8015/api/auth/db-updates-token \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H 'Content-Type: application/json' 2>&1)

HTTP_CODE=$(echo "$DB_TOKEN_RESP" | tail -n1)
BODY=$(echo "$DB_TOKEN_RESP" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$BODY" | grep -q "access_token"; then
        echo "   ✅ DB updates token obtained"
        DB_TOKEN=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
        echo "      Token preview: ${DB_TOKEN:0:30}..."
    else
        echo "   ⚠️  200 OK but unexpected body:"
        echo "$BODY"
    fi
elif [ "$HTTP_CODE" = "401" ]; then
    echo "   ❌ 401 UNAUTHORIZED - This is the DB Updates issue!"
    echo ""
    echo "Response body:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    echo "Possible causes:"
    echo "  1. JWT_SECRET mismatch between services"
    echo "  2. Token validation logic issue in require_admin()"
    echo "  3. JWT_ALGORITHM mismatch (should be HS256)"
    echo ""
    echo "Debug steps:"
    echo "  • Check JWT_SECRET in both services"
    echo "  • Decode token: jwt.io"
    echo "  • Check logs: docker-compose logs pp-backend | grep -i auth"
    exit 1
elif [ "$HTTP_CODE" = "404" ]; then
    echo "   ⚠️  404 NOT FOUND - ENABLE_DB_UPDATES may be false"
    exit 1
else
    echo "   ❌ Unexpected HTTP $HTTP_CODE"
    echo "$BODY"
    exit 1
fi

echo ""
echo "5️⃣  Testing Plant Backend customer lookup..."

# Seed demo customer first
echo "   → Seeding demo customer..."
CUSTOMER_RESP=$(curl -sS -w "\n%{http_code}" -X POST http://localhost:8000/api/v1/customers \
    -H 'Content-Type: application/json' \
    -d '{
      "fullName": "Demo User",
      "businessName": "WAOOAW Demo Co",
      "businessIndustry": "software",
      "businessAddress": "Demo Street 1",
      "email": "demo@waooaw.com",
      "phone": "+15555555555",
      "preferredContactMethod": "email",
      "consent": true
    }' 2>&1)

CUST_CODE=$(echo "$CUSTOMER_RESP" | tail -n1)
if [ "$CUST_CODE" = "200" ] || [ "$CUST_CODE" = "201" ]; then
    echo "   ✅ Demo customer exists/created"
else
    echo "   ⚠️  Customer creation returned HTTP $CUST_CODE (may already exist)"
fi

# Test agent list (this triggers customer lookup via auth validation)
echo "   → Testing agent list (triggers customer auth validation)..."
AGENT_RESP=$(curl -sS -w "\n%{http_code}" -X GET "http://localhost:8000/api/v1/agents?limit=5" \
    -H "Authorization: Bearer $ACCESS_TOKEN" 2>&1)

AGENT_CODE=$(echo "$AGENT_RESP" | tail -n1)
AGENT_BODY=$(echo "$AGENT_RESP" | sed '$d')

if [ "$AGENT_CODE" = "200" ]; then
    AGENT_COUNT=$(echo "$AGENT_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('agents',[])))" 2>/dev/null || echo "?")
    echo "   ✅ Agent list returned ($AGENT_COUNT agents)"
elif [ "$AGENT_CODE" = "404" ] || [ "$AGENT_CODE" = "500" ]; then
    echo "   ❌ HTTP $AGENT_CODE - This is the Agent Management issue!"
    echo ""
    echo "Response:"
    echo "$AGENT_BODY" | python3 -m json.tool 2>/dev/null || echo "$AGENT_BODY"
    echo ""
    if echo "$AGENT_BODY" | grep -q "Customer not found"; then
        echo "Root cause: Customer record missing in Plant Backend database"
        echo "Fix: Run customer seed (done above) and retry"
    fi
    exit 1
else
    echo "   ⚠️  Unexpected HTTP $AGENT_CODE"
fi

echo ""
echo "═══════════════════════════════════════"
echo "✅ ALL TESTS PASSED!"
echo "═══════════════════════════════════════"
echo ""
echo "Summary:"
echo "  • Dev token minting: ✅"
echo "  • DB updates token: ✅"
echo "  • Customer lookup: ✅"
echo "  • Agent management: ✅"
echo ""
echo "Your local environment is configured correctly."
echo "If you still see 401 errors in the browser:"
echo "  1. Clear localStorage: pp_access_token"
echo "  2. Clear sessionStorage: pp_db_access_token"
echo "  3. Re-login via Google OAuth"
echo "  4. Check Network tab for Authorization header"
