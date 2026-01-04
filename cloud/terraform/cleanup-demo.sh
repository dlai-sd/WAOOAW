#!/bin/bash
# Cleanup script for demo environment

set -e

ENVIRONMENT="demo"
PROJECT="waooaw-oauth"
REGION="asia-south1"

echo "🧹 Cleaning up $ENVIRONMENT environment"
echo "   Project: $PROJECT"
echo "================================"

# Delete forwarding rules first
echo "📡 Deleting forwarding rules..."
gcloud compute forwarding-rules delete "${ENVIRONMENT}-https-forwarding-rule" --global --quiet 2>/dev/null || echo "  (not found)"
gcloud compute forwarding-rules delete "${ENVIRONMENT}-http-forwarding-rule" --global --quiet 2>/dev/null || echo "  (not found)"

# Delete proxies
echo "🔐 Deleting proxies..."
gcloud compute target-https-proxies delete "${ENVIRONMENT}-https-proxy" --quiet 2>/dev/null || echo "  (not found)"
gcloud compute target-http-proxies delete "${ENVIRONMENT}-http-proxy" --quiet 2>/dev/null || echo "  (not found)"

# Delete SSL certificates
echo "🔒 Deleting SSL certificates..."
gcloud compute ssl-certificates delete "${ENVIRONMENT}-customer-ssl" --quiet 2>/dev/null || echo "  (not found)"
gcloud compute ssl-certificates delete "${ENVIRONMENT}-platform-ssl" --quiet 2>/dev/null || echo "  (not found)"

# Delete URL maps
echo "🗺️  Deleting URL maps..."
gcloud compute url-maps delete "${ENVIRONMENT}-url-map" --quiet 2>/dev/null || echo "  (not found)"
gcloud compute url-maps delete "${ENVIRONMENT}-http-redirect-map" --quiet 2>/dev/null || echo "  (not found)"

# Delete backend services
echo "🔧 Deleting backend services..."
gcloud compute backend-services delete "${ENVIRONMENT}-api-backend" --global --quiet 2>/dev/null || echo "  (not found)"
gcloud compute backend-services delete "${ENVIRONMENT}-customer-backend" --global --quiet 2>/dev/null || echo "  (not found)"
gcloud compute backend-services delete "${ENVIRONMENT}-platform-backend" --global --quiet 2>/dev/null || echo "  (not found)"

# Delete health checks
echo "🏥 Deleting health checks..."
gcloud compute health-checks delete "${ENVIRONMENT}-api-health-check" --quiet 2>/dev/null || echo "  (not found)"
gcloud compute health-checks delete "${ENVIRONMENT}-customer-health-check" --quiet 2>/dev/null || echo "  (not found)"
gcloud compute health-checks delete "${ENVIRONMENT}-platform-health-check" --quiet 2>/dev/null || echo "  (not found)"

# Delete NEGs
echo "🌐 Deleting Network Endpoint Groups..."
gcloud compute network-endpoint-groups delete "waooaw-${ENVIRONMENT}-api-neg" --region="$REGION" --quiet 2>/dev/null || echo "  (not found)"
gcloud compute network-endpoint-groups delete "waooaw-${ENVIRONMENT}-customer-neg" --region="$REGION" --quiet 2>/dev/null || echo "  (not found)"
gcloud compute network-endpoint-groups delete "waooaw-${ENVIRONMENT}-platform-neg" --region="$REGION" --quiet 2>/dev/null || echo "  (not found)"

# Delete Cloud Run services
echo "📦 Deleting Cloud Run services..."
gcloud run services delete "waooaw-api-${ENVIRONMENT}" --region="$REGION" --quiet 2>/dev/null || echo "  (not found)"
gcloud run services delete "waooaw-portal-${ENVIRONMENT}" --region="$REGION" --quiet 2>/dev/null || echo "  (not found)"
gcloud run services delete "waooaw-platform-portal-${ENVIRONMENT}" --region="$REGION" --quiet 2>/dev/null || echo "  (not found)"

echo ""
echo "================================"
echo "✅ Cleanup complete!"
echo ""
echo "Note: Static IP (35.190.6.91) preserved for reuse"
