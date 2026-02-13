#!/bin/bash
# Diagnose DB Updates Auth Issue
# Checks JWT_SECRET consistency, token flow, and endpoint reachability

set -e

ENVIRONMENT="${1:-demo}"
echo "🔍 Diagnosing DB Updates Auth for environment: $ENVIRONMENT"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_env_var() {
    local service=$1
    local var_name=$2
    local region=${3:-us-central1}
    
    echo -n "Checking $service.$var_name... "
    value=$(gcloud run services describe "$service" --region "$region" --format="value(spec.template.spec.containers[0].env[?(@.name=='$var_name')].value)" 2>/dev/null || echo "")
    
    if [ -z "$value" ]; then
        # Check secrets
        secret=$(gcloud run services describe "$service" --region "$region" --format="value(spec.template.spec.containers[0].env[?(@.name=='$var_name')].valueFrom.secretKeyRef.name)" 2>/dev/null || echo "")
        if [ -n "$secret" ]; then
            echo -e "${YELLOW}SECRET:$secret${NC}"
            echo "$secret"
        else
            echo -e "${RED}NOT SET${NC}"
            echo "NOT_SET"
        fi
    else
        echo -e "${GREEN}${value:0:20}...${NC}"
        echo "$value"
    fi
}

echo "═══════════════════════════════════════════════════════"
echo " 1. JWT_SECRET Consistency Check"
echo "═══════════════════════════════════════════════════════"

PP_SERVICE="waooaw-pp-backend-$ENVIRONMENT"
GATEWAY_SERVICE="waooaw-plant-gateway-$ENVIRONMENT"
PLANT_SERVICE="waooaw-plant-backend-$ENVIRONMENT"

PP_SECRET=$(check_env_var "$PP_SERVICE" "JWT_SECRET")
GATEWAY_SECRET=$(check_env_var "$GATEWAY_SERVICE" "JWT_SECRET")
PLANT_SECRET=$(check_env_var "$PLANT_SERVICE" "JWT_SECRET")

echo ""
if [ "$PP_SECRET" = "$GATEWAY_SECRET" ] && [ "$PP_SECRET" = "$PLANT_SECRET" ] && [ "$PP_SECRET" != "NOT_SET" ]; then
    echo -e "${GREEN}✓ JWT_SECRET is consistent across all services${NC}"
else
    echo -e "${RED}✗ JWT_SECRET MISMATCH OR NOT SET!${NC}"
    echo "  PP Backend: $PP_SECRET"
    echo "  Gateway:    $GATEWAY_SECRET"
    echo "  Plant:      $PLANT_SECRET"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo " 2. ENABLE_DB_UPDATES Check"
echo "═══════════════════════════════════════════════════════"

PP_DB_ENABLED=$(check_env_var "$PP_SERVICE" "ENABLE_DB_UPDATES")
PLANT_DB_ENABLED=$(check_env_var "$PLANT_SERVICE" "ENABLE_DB_UPDATES")

echo ""
if [ "$PP_DB_ENABLED" = "true" ]; then
    echo -e "${GREEN}✓ PP Backend ENABLE_DB_UPDATES=true${NC}"
else
    echo -e "${RED}✗ PP Backend ENABLE_DB_UPDATES=$PP_DB_ENABLED (should be true for $ENVIRONMENT)${NC}"
fi

if [ "$PLANT_DB_ENABLED" = "true" ]; then
    echo -e "${GREEN}✓ Plant Backend ENABLE_DB_UPDATES=true${NC}"
else
    echo -e "${YELLOW}⚠ Plant Backend ENABLE_DB_UPDATES=$PLANT_DB_ENABLED${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo " 3. Endpoint Reachability Test"
echo "═══════════════════════════════════════════════════════"

PP_DOMAIN="pp.$ENVIRONMENT.waooaw.com"
if [ "$ENVIRONMENT" = "prod" ]; then
    PP_DOMAIN="platform.waooaw.com"
fi

echo "Testing https://$PP_DOMAIN/api/health"
HEALTH_STATUS=$(curl -sS -o /dev/null -w "%{http_code}" "https://$PP_DOMAIN/api/health" || echo "000")
if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ PP Backend reachable (HTTP $HEALTH_STATUS)${NC}"
else
    echo -e "${RED}✗ PP Backend not reachable (HTTP $HEALTH_STATUS)${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo " 4. Auth Token Flow Test"
echo "═══════════════════════════════════════════════════════"

if [ "$ENVIRONMENT" = "demo" ]; then
    echo "Testing dev-token endpoint..."
    DEV_TOKEN_RESP=$(curl -sS -X POST "https://$PP_DOMAIN/api/auth/dev-token" -H 'Content-Type: application/json' 2>&1 || echo "ERROR")
    
    if echo "$DEV_TOKEN_RESP" | grep -q "access_token"; then
        echo -e "${GREEN}✓ Dev token minting works${NC}"
        ACCESS_TOKEN=$(echo "$DEV_TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
        
        if [ -n "$ACCESS_TOKEN" ]; then
            echo ""
            echo "Testing db-updates-token endpoint with minted token..."
            DB_TOKEN_RESP=$(curl -sS -X POST "https://$PP_DOMAIN/api/auth/db-updates-token" \
                -H 'Content-Type: application/json' \
                -H "Authorization: Bearer $ACCESS_TOKEN" 2>&1 || echo "ERROR")
            
            if echo "$DB_TOKEN_RESP" | grep -q "access_token"; then
                echo -e "${GREEN}✓ DB updates token minting works!${NC}"
                echo ""
                echo "Auth flow is working correctly. Issue may be in frontend token storage/transmission."
            elif echo "$DB_TOKEN_RESP" | grep -q "401"; then
                echo -e "${RED}✗ DB updates token returned 401${NC}"
                echo "Response: $DB_TOKEN_RESP"
                echo ""
                echo "Possible causes:"
                echo "  - JWT_SECRET mismatch (but check #1 passed)"
                echo "  - Token validation logic issue"
                echo "  - require_admin dependency failing"
            else
                echo -e "${RED}✗ Unexpected response${NC}"
                echo "$DB_TOKEN_RESP"
            fi
        fi
    elif echo "$DEV_TOKEN_RESP" | grep -q "404"; then
        echo -e "${YELLOW}⚠ Dev token endpoint disabled (expected for non-local)${NC}"
        echo "Manual test required with real Google OAuth token"
    else
        echo -e "${RED}✗ Dev token failed${NC}"
        echo "$DEV_TOKEN_RESP"
    fi
else
    echo -e "${YELLOW}⚠ Skipping automated token test for $ENVIRONMENT (requires real auth)${NC}"
    echo ""
    echo "Manual test commands:"
    echo "  1. Login via Google OAuth in browser"
    echo "  2. Open DevTools → Application → Local Storage"
    echo "  3. Copy value of 'pp_access_token'"
    echo "  4. Run:"
    echo ""
    echo "     curl -X POST https://$PP_DOMAIN/api/auth/db-updates-token \\"
    echo "       -H 'Authorization: Bearer <YOUR_TOKEN>' \\"
    echo "       -H 'Content-Type: application/json'"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo " 5. Summary & Recommendations"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "If auth flow test passed:"
echo "  → Issue is in frontend (token not being sent or stored)"
echo "  → Check browser DevTools → Network → request headers"
echo "  → Verify localStorage has 'pp_access_token'"
echo ""
echo "If auth flow test failed with 401:"
echo "  → Check JWT_SECRET is actually matching (secrets may differ)"
echo "  → Verify require_admin dependency logic"
echo "  → Check JWT_ALGORITHM consistency (should be HS256)"
echo ""
echo "If ENABLE_DB_UPDATES=false:"
echo "  → Update Terraform and redeploy"
echo ""
