#!/bin/bash
set -e

PROJECT="waooaw-oauth"
REGION="asia-south1"

echo "=========================================="
echo "WAOOAW Infrastructure Cleanup"
echo "=========================================="
echo ""
echo "This will DELETE manually-created resources:"
echo "  ✗ Cloud Run services (demo/staging/prod)"
echo "  ✗ Network Endpoint Groups (NEGs)"
echo "  ✗ Backend Services"
echo "  ✗ URL Maps"
echo "  ✗ Target Proxies (HTTP/HTTPS)"
echo "  ✗ Forwarding Rules"
echo "  ✗ SSL Certificates"
echo "  ✗ Health Checks"
echo ""
echo "This will PRESERVE:"
echo "  ✓ Static IP: waooaw-lb-ip (35.190.6.91)"
echo "  ✓ Secrets: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET"
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Function to safely delete resource
safe_delete() {
    local resource_type=$1
    local resource_name=$2
    local extra_args=${3:-}
    
    echo "Checking $resource_type: $resource_name..."
    if gcloud $resource_type describe $resource_name $extra_args --project=$PROJECT &>/dev/null; then
        echo "  → Deleting $resource_name..."
        gcloud $resource_type delete $resource_name $extra_args --project=$PROJECT --quiet 2>/dev/null || echo "  ⚠ Failed to delete (may not exist or already deleted)"
    else
        echo "  ✓ Already deleted or doesn't exist"
    fi
}

# 1. Delete Global Forwarding Rules (must be first - blocks other deletions)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Deleting Forwarding Rules..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
safe_delete "compute forwarding-rules" "demo-https-forwarding-rule" "--global"
safe_delete "compute forwarding-rules" "demo-http-forwarding-rule" "--global"
safe_delete "compute forwarding-rules" "staging-https-forwarding-rule" "--global"
safe_delete "compute forwarding-rules" "staging-http-forwarding-rule" "--global"
safe_delete "compute forwarding-rules" "prod-https-forwarding-rule" "--global"
safe_delete "compute forwarding-rules" "prod-http-forwarding-rule" "--global"
safe_delete "compute forwarding-rules" "waooaw-https-forwarding-rule" "--global"
safe_delete "compute forwarding-rules" "waooaw-http-forwarding-rule" "--global"

# 2. Delete Target Proxies
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Deleting Target Proxies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
safe_delete "compute target-https-proxies" "demo-https-proxy"
safe_delete "compute target-http-proxies" "demo-http-proxy"
safe_delete "compute target-https-proxies" "staging-https-proxy"
safe_delete "compute target-http-proxies" "staging-http-proxy"
safe_delete "compute target-https-proxies" "prod-https-proxy"
safe_delete "compute target-http-proxies" "prod-http-proxy"
safe_delete "compute target-https-proxies" "waooaw-https-proxy"
safe_delete "compute target-http-proxies" "waooaw-http-proxy"

# 3. Delete URL Maps
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Deleting URL Maps..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
safe_delete "compute url-maps" "demo-url-map"
safe_delete "compute url-maps" "demo-http-redirect-map"
safe_delete "compute url-maps" "staging-url-map"
safe_delete "compute url-maps" "staging-http-redirect-map"
safe_delete "compute url-maps" "prod-url-map"
safe_delete "compute url-maps" "prod-http-redirect-map"
safe_delete "compute url-maps" "waooaw-url-map"
safe_delete "compute url-maps" "waooaw-http-redirect"

# 4. Delete SSL Certificates
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Deleting SSL Certificates..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
safe_delete "compute ssl-certificates" "waooaw-demo-ssl-cert"
safe_delete "compute ssl-certificates" "demo-ssl-cert"
safe_delete "compute ssl-certificates" "staging-ssl-cert"
safe_delete "compute ssl-certificates" "prod-ssl-cert"
safe_delete "compute ssl-certificates" "waooaw-ssl-cert"

# 5. Delete Backend Services
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Deleting Backend Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
safe_delete "compute backend-services" "demo-api-backend-service"
safe_delete "compute backend-services" "demo-platform-backend-service"
safe_delete "compute backend-services" "demo-customer-backend-service"
safe_delete "compute backend-services" "staging-api-backend"
safe_delete "compute backend-services" "staging-platform-backend"
safe_delete "compute backend-services" "staging-customer-backend"
safe_delete "compute backend-services" "prod-api-backend"
safe_delete "compute backend-services" "prod-platform-backend"
safe_delete "compute backend-services" "prod-customer-backend"
safe_delete "compute backend-services" "waooaw-demo-api-backend"
safe_delete "compute backend-services" "waooaw-demo-platform-backend"

# 6. Delete Health Checks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Deleting Health Checks..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
safe_delete "compute health-checks" "demo-api-health-check"
safe_delete "compute health-checks" "demo-platform-health-check"
safe_delete "compute health-checks" "demo-customer-health-check"
safe_delete "compute health-checks" "staging-api-health-check"
safe_delete "compute health-checks" "staging-platform-health-check"
safe_delete "compute health-checks" "staging-customer-health-check"
safe_delete "compute health-checks" "prod-api-health-check"
safe_delete "compute health-checks" "prod-platform-health-check"
safe_delete "compute health-checks" "prod-customer-health-check"
safe_delete "compute health-checks" "waooaw-demo-api-health-check"
safe_delete "compute health-checks" "waooaw-demo-platform-health-check"

# 7. Delete Network Endpoint Groups (NEGs)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. Deleting Network Endpoint Groups..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
safe_delete "compute network-endpoint-groups" "waooaw-demo-api-neg" "--region=$REGION"
safe_delete "compute network-endpoint-groups" "waooaw-demo-platform-neg" "--region=$REGION"
safe_delete "compute network-endpoint-groups" "waooaw-demo-customer-neg" "--region=$REGION"
safe_delete "compute network-endpoint-groups" "demo-api-neg" "--region=$REGION"
safe_delete "compute network-endpoint-groups" "demo-platform-neg" "--region=$REGION"
safe_delete "compute network-endpoint-groups" "demo-customer-neg" "--region=$REGION"
safe_delete "compute network-endpoint-groups" "staging-api-neg" "--region=$REGION"
safe_delete "compute network-endpoint-groups" "staging-platform-neg" "--region=$REGION"
safe_delete "compute network-endpoint-groups" "staging-customer-neg" "--region=$REGION"

# Check for NEGs in us-central1 (if any remain)
echo "Checking us-central1 for remaining NEGs..."
safe_delete "compute network-endpoint-groups" "waooaw-api-neg" "--region=us-central1"
safe_delete "compute network-endpoint-groups" "waooaw-platform-neg" "--region=us-central1"

# 8. Delete Cloud Run Services
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8. Deleting Cloud Run Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Demo services
echo "Demo environment:"
safe_delete "run services" "waooaw-api-demo" "--region=$REGION"
safe_delete "run services" "waooaw-platform-portal-demo" "--region=$REGION"
safe_delete "run services" "waooaw-portal-demo" "--region=$REGION"

# Staging services (if any)
echo "Staging environment:"
safe_delete "run services" "waooaw-api-staging" "--region=$REGION"
safe_delete "run services" "waooaw-platform-portal-staging" "--region=$REGION"
safe_delete "run services" "waooaw-portal-staging" "--region=$REGION"

# Production services (if any)
echo "Production environment:"
safe_delete "run services" "waooaw-api-prod" "--region=$REGION"
safe_delete "run services" "waooaw-platform-portal-prod" "--region=$REGION"
safe_delete "run services" "waooaw-portal-prod" "--region=$REGION"

# Check us-central1 for any remaining services
echo "Checking us-central1 for remaining services..."
safe_delete "run services" "waooaw-api" "--region=us-central1"
safe_delete "run services" "waooaw-platform-portal" "--region=us-central1"

# 9. Verify Static IP and Secrets are PRESERVED
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9. Verifying Preserved Resources..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Static IP (should exist):"
if gcloud compute addresses describe waooaw-lb-ip --global --project=$PROJECT &>/dev/null; then
    IP=$(gcloud compute addresses describe waooaw-lb-ip --global --project=$PROJECT --format="value(address)")
    echo "  ✓ waooaw-lb-ip: $IP (PRESERVED)"
else
    echo "  ⚠ WARNING: Static IP not found! May need to recreate."
fi

echo ""
echo "Secrets (should exist):"
for secret in GOOGLE_CLIENT_ID GOOGLE_CLIENT_SECRET JWT_SECRET; do
    if gcloud secrets describe $secret --project=$PROJECT &>/dev/null; then
        echo "  ✓ $secret (PRESERVED)"
    else
        echo "  ⚠ WARNING: $secret not found!"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Cleanup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Review cleanup results above"
echo "  2. Deploy demo: ./deploy.py --environment demo --action create"
echo "  3. Configure DNS in GoDaddy (one-time)"
echo "  4. Update Google OAuth Console"
echo ""
