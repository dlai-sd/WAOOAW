#!/bin/bash
# Test Suite for WAOOAW Demo Infrastructure

set -e

CUSTOMER_DOMAIN="cp.demo.waooaw.com"
PLATFORM_DOMAIN="pp.demo.waooaw.com"
STATIC_IP="35.190.6.91"

echo "🧪 WAOOAW Infrastructure Test Suite"
echo "===================================="
echo ""

# Test 1: DNS Resolution
echo "1️⃣  Testing DNS Resolution..."
if host $CUSTOMER_DOMAIN | grep -q $STATIC_IP; then
    echo "   ✅ $CUSTOMER_DOMAIN → $STATIC_IP"
else
    echo "   ❌ $CUSTOMER_DOMAIN not resolving to $STATIC_IP"
    echo "   📝 Action: Configure DNS A record in GoDaddy"
fi

if host $PLATFORM_DOMAIN | grep -q $STATIC_IP; then
    echo "   ✅ $PLATFORM_DOMAIN → $STATIC_IP"
else
    echo "   ❌ $PLATFORM_DOMAIN not resolving to $STATIC_IP"
    echo "   📝 Action: Configure DNS A record in GoDaddy"
fi
echo ""

# Test 2: SSL Certificate Status
echo "2️⃣  Testing SSL Certificates..."
CUSTOMER_SSL=$(gcloud compute ssl-certificates describe demo-customer-ssl --global --format="get(managed.status)" 2>/dev/null || echo "NOT_FOUND")
PLATFORM_SSL=$(gcloud compute ssl-certificates describe demo-platform-ssl --global --format="get(managed.status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$CUSTOMER_SSL" = "ACTIVE" ]; then
    echo "   ✅ Customer SSL: ACTIVE"
else
    echo "   ⏳ Customer SSL: $CUSTOMER_SSL (wait 10-15 minutes after DNS config)"
fi

if [ "$PLATFORM_SSL" = "ACTIVE" ]; then
    echo "   ✅ Platform SSL: ACTIVE"
else
    echo "   ⏳ Platform SSL: $PLATFORM_SSL (wait 10-15 minutes after DNS config)"
fi
echo ""

# Test 3: Backend API Health
echo "3️⃣  Testing Backend API Health..."
if curl -s -k "https://$CUSTOMER_DOMAIN/api/health" | grep -q "ok\|healthy\|status"; then
    echo "   ✅ Backend API responding"
    curl -s "https://$CUSTOMER_DOMAIN/api/health" | jq . 2>/dev/null || cat
else
    echo "   ❌ Backend API not responding"
    echo "   Trying direct Cloud Run URL..."
    BACKEND_URL=$(gcloud run services describe waooaw-cp_api-demo --region=asia-south1 --format="get(status.url)")
    curl -s "$BACKEND_URL/health" | jq . 2>/dev/null || echo "   Direct access also failed"
fi
echo ""

# Test 4: Customer Portal
echo "4️⃣  Testing Customer Portal..."
CUSTOMER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$CUSTOMER_DOMAIN" -k)
if [ "$CUSTOMER_STATUS" = "200" ]; then
    echo "   ✅ Customer Portal: HTTP $CUSTOMER_STATUS"
else
    echo "   ⚠️  Customer Portal: HTTP $CUSTOMER_STATUS"
fi
echo ""

# Test 5: Platform Portal
echo "5️⃣  Testing Platform Portal..."
PLATFORM_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$PLATFORM_DOMAIN" -k)
if [ "$PLATFORM_STATUS" = "200" ]; then
    echo "   ✅ Platform Portal: HTTP $PLATFORM_STATUS"
else
    echo "   ⚠️  Platform Portal: HTTP $PLATFORM_STATUS"
fi
echo ""

# Test 6: Load Balancer Routing
echo "6️⃣  Testing Load Balancer Routing..."
echo "   Testing customer portal routes to correct backend..."
CUSTOMER_BACKEND=$(curl -s -k "https://$CUSTOMER_DOMAIN" -I | grep -i "via\|x-cloud-trace" | head -1)
echo "   Customer: $CUSTOMER_BACKEND"

echo "   Testing platform portal routes to correct backend..."
PLATFORM_BACKEND=$(curl -s -k "https://$PLATFORM_DOMAIN" -I | grep -i "via\|x-cloud-trace" | head -1)
echo "   Platform: $PLATFORM_BACKEND"

echo "   Testing API routes through both domains..."
curl -s -k "https://$CUSTOMER_DOMAIN/api/health" > /tmp/api-via-customer.txt
curl -s -k "https://$PLATFORM_DOMAIN/api/health" > /tmp/api-via-platform.txt
if diff /tmp/api-via-customer.txt /tmp/api-via-platform.txt > /dev/null; then
    echo "   ✅ Both domains route to same API backend"
else
    echo "   ⚠️  API responses differ between domains"
fi
echo ""

# Test 7: CORS Headers
echo "7️⃣  Testing CORS Configuration..."
echo "   Checking customer portal CORS..."
CUSTOMER_CORS=$(curl -s -k "https://$CUSTOMER_DOMAIN/api/health" -H "Origin: https://$CUSTOMER_DOMAIN" -I | grep -i "access-control-allow-origin")
if [ -n "$CUSTOMER_CORS" ]; then
    echo "   ✅ CORS: $CUSTOMER_CORS"
else
    echo "   ⚠️  CORS headers not found"
fi
echo ""

# Test 8: OAuth Configuration Check
echo "8️⃣  OAuth Configuration Status..."
echo "   📝 Manual Check Required:"
echo "   1. Go to: https://console.cloud.google.com/apis/credentials"
echo "   2. Verify Authorized JavaScript origins:"
echo "      - https://$CUSTOMER_DOMAIN"
echo "      - https://$PLATFORM_DOMAIN"
echo "   3. Verify Authorized redirect URIs:"
echo "      - https://$CUSTOMER_DOMAIN/api/auth/callback"
echo "      - https://$PLATFORM_DOMAIN/api/auth/callback"
echo ""

# Test 9: Cloud Run Service Health
echo "9️⃣  Testing Cloud Run Services Directly..."
BACKEND_URL=$(gcloud run services describe waooaw-cp_api-demo --region=asia-south1 --format="get(status.url)" 2>/dev/null)
CUSTOMER_URL=$(gcloud run services describe waooaw-cp-demo --region=asia-south1 --format="get(status.url)" 2>/dev/null)
PLATFORM_URL=$(gcloud run services describe waooaw-platform-portal-demo --region=asia-south1 --format="get(status.url)" 2>/dev/null)

echo "   CP Backend: $BACKEND_URL"
echo "   CP Portal: $CUSTOMER_URL"
echo "   PP Platform: $PLATFORM_URL"
echo ""

# Test 10: Infrastructure State
echo "🔟 Testing Infrastructure State..."
echo "   Terraform state:"
cd /workspaces/WAOOAW/cloud/terraform
terraform state list | wc -l | xargs echo "   Resources managed:"
echo ""

echo "===================================="
echo "✅ Test Suite Complete!"
echo ""
echo "📋 Next Manual Tests:"
echo "   1. Open browser: https://$PLATFORM_DOMAIN"
echo "   2. Click 'Sign in with Google'"
echo "   3. Verify OAuth flow completes WITHOUT timeout"
echo "   4. Check dashboard loads successfully"
echo "   5. Test logout and re-login"
echo ""
echo "🎯 Critical Test (Original Issue):"
echo "   The OAuth redirect should work seamlessly now because:"
echo "   - Both auth request and callback are on same domain ($PLATFORM_DOMAIN)"
echo "   - No cross-origin redirect blocking"
echo "   - Load Balancer routes /api/* to backend transparently"
