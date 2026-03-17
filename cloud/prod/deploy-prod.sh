#!/bin/bash
# Deploy WAOOAW Platform Portal v2 to Production Environment
# GCP Cloud Run - Multi-region
# Load Balancer with custom domains (*.waooaw.com)
# High availability with min instances

set -e

PROJECT_ID="waooaw-oauth"
REGION="us-central1"
ENV="production"

# Service names
BACKEND_SERVICE="waooaw-backend-prod"
PLATFORM_PORTAL_SERVICE="waooaw-platform-portal-prod"
CUSTOMER_PORTAL_SERVICE="waooaw-portal-prod"

# Custom domains
BACKEND_DOMAIN="api.waooaw.com"
PLATFORM_PORTAL_DOMAIN="pp.waooaw.com"
CUSTOMER_PORTAL_DOMAIN="www.waooaw.com"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}⚠️  PRODUCTION DEPLOYMENT${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Env:      $ENV"
echo ""
echo -e "${YELLOW}This will deploy to PRODUCTION with live customer traffic!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not logged in to gcloud. Run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Verify secrets exist
echo ""
echo "🔐 Verifying secrets..."
REQUIRED_SECRETS=("GOOGLE_CLIENT_ID" "GOOGLE_CLIENT_SECRET" "YOUTUBE_CLIENT_ID" "YOUTUBE_CLIENT_SECRET" "JWT_SECRET" "DATABASE_URL_PROD" "REDIS_URL_PROD")
for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! gcloud secrets describe $secret &>/dev/null; then
        echo "❌ Secret $secret not found!"
        exit 1
    fi
    echo "✅ $secret"
done

echo ""
echo "📦 Step 1: Deploy Backend API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ../../WaooawPortal/backend

gcloud run deploy $BACKEND_SERVICE \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 100 \
  --min-instances 2 \
  --max-instances 50 \
  --cpu-throttling \
  --set-env-vars "ENV=$ENV" \
    --set-secrets "GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,YOUTUBE_CLIENT_ID=YOUTUBE_CLIENT_ID:latest,YOUTUBE_CLIENT_SECRET=YOUTUBE_CLIENT_SECRET:latest,JWT_SECRET=JWT_SECRET:latest,DATABASE_URL=DATABASE_URL_PROD:latest,REDIS_URL=REDIS_URL_PROD:latest" \
  --no-traffic

BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)')
echo "✅ Backend deployed (no traffic): $BACKEND_URL"

# Smoke test new revision
echo "🧪 Running smoke tests..."
REVISION=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.latestCreatedRevisionName)')
REVISION_URL=$(gcloud run revisions describe $REVISION --region $REGION --format 'value(status.url)')

if curl -sf "${REVISION_URL}/health" > /dev/null; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed!"
    exit 1
fi

# Gradual rollout
echo "🚀 Starting gradual rollout..."
gcloud run services update-traffic $BACKEND_SERVICE --region $REGION --to-revisions $REVISION=10
echo "✅ 10% traffic to new revision"

read -p "Continue to 50%? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud run services update-traffic $BACKEND_SERVICE --region $REGION --to-revisions $REVISION=50
    echo "✅ 50% traffic to new revision"
    
    read -p "Continue to 100%? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud run services update-traffic $BACKEND_SERVICE --region $REGION --to-revisions $REVISION=100
        echo "✅ 100% traffic to new revision"
    fi
fi

echo ""
echo "📦 Step 2: Deploy Platform Portal"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ../PlatformPortal

gcloud run deploy $PLATFORM_PORTAL_SERVICE \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 100 \
  --min-instances 2 \
  --max-instances 50 \
  --cpu-throttling \
  --set-env-vars "ENV=$ENV,PORT=8080" \
  --no-traffic

PORTAL_URL=$(gcloud run services describe $PLATFORM_PORTAL_SERVICE --region $REGION --format 'value(status.url)')
echo "✅ Platform Portal deployed (no traffic): $PORTAL_URL"

# Smoke test
REVISION=$(gcloud run services describe $PLATFORM_PORTAL_SERVICE --region $REGION --format 'value(status.latestCreatedRevisionName)')
REVISION_URL=$(gcloud run revisions describe $REVISION --region $REGION --format 'value(status.url)')

if curl -sf "${REVISION_URL}/" > /dev/null; then
    echo "✅ Smoke test passed"
else
    echo "❌ Smoke test failed!"
    exit 1
fi

# Gradual rollout
echo "🚀 Starting gradual rollout..."
gcloud run services update-traffic $PLATFORM_PORTAL_SERVICE --region $REGION --to-revisions $REVISION=10
echo "✅ 10% traffic to new revision"

read -p "Continue to 100%? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud run services update-traffic $PLATFORM_PORTAL_SERVICE --region $REGION --to-revisions $REVISION=100
    echo "✅ 100% traffic to new revision"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ PRODUCTION DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "🌐 Live URLs:"
echo "   Platform Portal:   https://$PLATFORM_PORTAL_DOMAIN"
echo "   Backend API:       https://$BACKEND_DOMAIN"
echo "   Customer Portal:   https://$CUSTOMER_PORTAL_DOMAIN"
echo ""
echo "📊 Monitoring:"
echo "   1. Check uptime: https://console.cloud.google.com/monitoring"
echo "   2. View logs: gcloud logging read 'severity>=ERROR' --limit=50"
echo "   3. Check metrics: gcloud monitoring dashboards list"
echo ""
echo "🔄 Rollback (if needed):"
echo "   gcloud run revisions list --service $BACKEND_SERVICE --region $REGION"
echo "   gcloud run services update-traffic $BACKEND_SERVICE --to-revisions REVISION_NAME=100"
echo ""
