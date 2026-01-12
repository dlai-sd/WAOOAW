#!/bin/bash
# Quick Infrastructure Status Check

echo "🔍 WAOOAW Demo Infrastructure Status"
echo "====================================="
echo ""

# Cloud Run Services
echo "☁️  Cloud Run Services:"
gcloud run services list --region=asia-south1 | grep demo | awk '{print "   ✅", $1, "-", $4}'
echo ""

# Network Endpoint Groups
echo "🌐 Network Endpoint Groups:"
gcloud compute network-endpoint-groups list --regions=asia-south1 | grep demo | awk '{print "   ✅", $1}'
echo ""

# Backend Services
echo "🔧 Backend Services:"
gcloud compute backend-services list --global | grep demo | awk '{print "   ✅", $1, "-", $NF}'
echo ""

# URL Maps
echo "🗺️  URL Maps:"
gcloud compute url-maps list --global | grep demo | awk '{print "   ✅", $1}'
echo ""

# SSL Certificates
echo "🔒 SSL Certificates:"
echo "   Customer Portal:"
gcloud compute ssl-certificates describe demo-customer-ssl --global --format="value(managed.domains[0],managed.status)" 2>/dev/null | xargs echo "      "
echo "   Platform Portal:"
gcloud compute ssl-certificates describe demo-platform-ssl --global --format="value(managed.domains[0],managed.status)" 2>/dev/null | xargs echo "      "
echo ""

# Forwarding Rules
echo "📡 Forwarding Rules (Single IP Architecture):"
gcloud compute forwarding-rules list --global | grep demo | awk '{print "   ✅", $1, "→", $2, "(port", $3")"}'
echo ""

# Test Direct Cloud Run Access
echo "🧪 Testing Direct Cloud Run URLs:"
# CP Backend
BACKEND_URL=$(gcloud run services describe waooaw-cp_api-demo --region=asia-south1 --format="value(status.url)" 2>/dev/null)
if [ -n "$BACKEND_URL" ]; then
  echo "   CP Backend API: $BACKEND_URL/health"
  curl -s "$BACKEND_URL/health" -m 5 > /tmp/health.txt 2>&1 && echo "      ✅ Responding" || echo "      ❌ Not responding"
fi

# CP Portal
CUSTOMER_URL=$(gcloud run services describe waooaw-cp-demo --region=asia-south1 --format="value(status.url)" 2>/dev/null)
if [ -n "$CUSTOMER_URL" ]; then
  echo "   CP Portal: $CUSTOMER_URL"
  curl -s "$CUSTOMER_URL" -m 5 -o /dev/null && echo "      ✅ Responding" || echo "      ❌ Not responding"
fi

# PP Platform Portal
PLATFORM_URL=$(gcloud run services describe waooaw-platform-portal-demo --region=asia-south1 --format="value(status.url)" 2>/dev/null)
if [ -n "$PLATFORM_URL" ]; then
  echo "   PP Platform Portal: $PLATFORM_URL"
  curl -s "$PLATFORM_URL" -m 5 -o /dev/null && echo "      ✅ Responding" || echo "      ❌ Not responding"
fi
echo ""

# Terraform State
echo "📦 Terraform State:"
cd /workspaces/WAOOAW/cloud/terraform 2>/dev/null || cd terraform
RESOURCE_COUNT=$(terraform state list 2>/dev/null | wc -l)
echo "   ✅ Managing $RESOURCE_COUNT resources"
echo ""

echo "====================================="
echo ""
echo "📋 MANUAL STEPS REQUIRED:"
echo ""
echo "1. Configure DNS (GoDaddy):"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   | Record | Type | Value       | TTL |"
echo "   |━━━━━━━━|━━━━━━|━━━━━━━━━━━━━|━━━━━|"
echo "   | cp.demo| A    | 35.190.6.91 | 600 |"
echo "   | pp.demo| A    | 35.190.6.91 | 600 |"
echo "   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "2. Update OAuth Console:"
echo "   https://console.cloud.google.com/apis/credentials"
echo ""
echo "   Authorized JavaScript origins:"
echo "   • https://cp.demo.waooaw.com"
echo "   • https://pp.demo.waooaw.com"
echo ""
echo "   Authorized redirect URIs:"
echo "   • https://cp.demo.waooaw.com/api/auth/callback"
echo "   • https://pp.demo.waooaw.com/api/auth/callback"
echo ""
echo "3. Wait for SSL (10-15 min after DNS):"
echo "   Watch: gcloud compute ssl-certificates list --global"
echo ""
echo "4. Test OAuth Flow:"
echo "   Open: https://pp.demo.waooaw.com"
echo "   Click: Sign in with Google"
echo "   Verify: No 2-minute timeout!"
echo ""
echo "🎯 KEY IMPROVEMENT:"
echo "   OAuth now works on SAME domain (pp.demo.waooaw.com)"
echo "   • Request: pp.demo.waooaw.com/api/auth/google"
echo "   • Callback: pp.demo.waooaw.com/api/auth/callback"
echo "   • No cross-origin redirect = No browser blocking! ✅"
