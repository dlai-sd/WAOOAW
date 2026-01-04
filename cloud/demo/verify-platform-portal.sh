#!/bin/bash
# Platform Portal - Post-Deployment Verification Script
# Run this after GitHub Actions completes

echo "=== PLATFORM PORTAL VERIFICATION ==="
echo ""

PORTAL_URL="https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app"

echo "Testing Platform Portal at: $PORTAL_URL"
echo ""

# Test 1: Root Path (/)
echo "1️⃣ Testing Root Path (/)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PORTAL_URL/")
CONTENT_TYPE=$(curl -s -I "$PORTAL_URL/" | grep -i "content-type" | cut -d' ' -f2-)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ HTTP 200 OK"
    echo "   ✅ Content-Type: $CONTENT_TYPE"
    if echo "$CONTENT_TYPE" | grep -q "text/html"; then
        echo "   ✅ Serving HTML (Frontend working!)"
    else
        echo "   ⚠️  Not HTML - got: $CONTENT_TYPE"
    fi
else
    echo "   ❌ HTTP $HTTP_CODE (Expected 200)"
fi
echo ""

# Test 2: Backend API (/ping)
echo "2️⃣ Testing Backend API (/ping)..."
PING_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PORTAL_URL/ping")
if [ "$PING_CODE" = "200" ]; then
    echo "   ✅ Backend API responding"
else
    echo "   ❌ Backend API failed: HTTP $PING_CODE"
fi
echo ""

# Test 3: Dashboard Route
echo "3️⃣ Testing Dashboard Route (/dashboard)..."
DASHBOARD_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PORTAL_URL/dashboard")
if [ "$DASHBOARD_CODE" = "200" ]; then
    echo "   ✅ Dashboard route working"
else
    echo "   ℹ️  Dashboard: HTTP $DASHBOARD_CODE (may redirect to /)"
fi
echo ""

# Test 4: Login Page
echo "4️⃣ Testing Login Page (/login)..."
LOGIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PORTAL_URL/login")
if [ "$LOGIN_CODE" = "200" ]; then
    echo "   ✅ Login page accessible"
else
    echo "   ℹ️  Login: HTTP $LOGIN_CODE"
fi
echo ""

# Test 5: Check for Frontend Assets
echo "5️⃣ Checking Frontend Assets..."
curl -s "$PORTAL_URL/" | grep -q "WAOOAW" && echo "   ✅ WAOOAW branding found in HTML" || echo "   ⚠️  Branding not found"
curl -s "$PORTAL_URL/" | grep -q "script" && echo "   ✅ JavaScript loaded" || echo "   ⚠️  No JavaScript found"
echo ""

# Summary
echo "==================================="
echo "SUMMARY"
echo "==================================="
if [ "$HTTP_CODE" = "200" ] && [ "$PING_CODE" = "200" ]; then
    echo "✅ Platform Portal is OPERATIONAL"
    echo ""
    echo "Dashboard URL: $PORTAL_URL"
    echo "Login URL: $PORTAL_URL/login"
    echo ""
    echo "Features:"
    echo "  • Dark theme with cyan accents"
    echo "  • Metrics: Active Agents, Trials, Customers, Revenue"
    echo "  • OAuth login integration"
    echo "  • Real-time operations monitoring"
else
    echo "❌ Platform Portal has issues"
    echo "   Root: HTTP $HTTP_CODE"
    echo "   Backend: HTTP $PING_CODE"
    echo ""
    echo "Check logs with:"
    echo "  gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=waooaw-platform-portal-demo' --limit=50 --project=waooaw-oauth"
fi
echo ""
