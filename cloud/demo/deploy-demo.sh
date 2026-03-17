#!/bin/bash
# Deploy WAOOAW Platform Portal v2 to Demo Environment
# GCP Cloud Run - asia-south1 (Mumbai)
# Scale-to-zero configuration

set -e

PROJECT_ID="waooaw-oauth"
REGION="asia-south1"
ENV="demo"

# Service names
BACKEND_SERVICE="waooaw-api-demo"
PLATFORM_PORTAL_SERVICE="waooaw-platform-portal-demo"

echo "🚀 Deploying WAOOAW Platform v2 to DEMO Environment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Env:      $ENV"
echo ""

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not logged in to gcloud. Run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

echo ""
echo "📦 Step 1: Deploy Backend API"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ../../WaooawPortal/backend

gcloud run deploy $BACKEND_SERVICE \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --platform managed \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "ENV=$ENV" \
  --set-secrets "GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,YOUTUBE_CLIENT_ID=YOUTUBE_CLIENT_ID:latest,YOUTUBE_CLIENT_SECRET=YOUTUBE_CLIENT_SECRET:latest,JWT_SECRET=JWT_SECRET:latest"

BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region $REGION --format 'value(status.url)')
echo "✅ Backend deployed: $BACKEND_URL"

echo ""
echo "📦 Step 2: Deploy Platform Portal"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ../PlatformPortal

gcloud run deploy $PLATFORM_PORTAL_SERVICE \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --platform managed \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "ENV=$ENV"

PORTAL_URL=$(gcloud run services describe $PLATFORM_PORTAL_SERVICE --region $REGION --format 'value(status.url)')
echo "✅ Platform Portal deployed: $PORTAL_URL"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEMO DEPLOYMENT COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔗 URLs:"
echo "   Backend API:       $BACKEND_URL"
echo "   Platform Portal:   $PORTAL_URL"
echo ""
echo "🔐 OAuth Redirect URI (add to Google Console if not present):"
echo "   $BACKEND_URL/auth/callback"
echo ""
echo "📊 Next Steps:"
echo "   1. Verify deployment: ./verify-platform-portal.sh"
echo "   2. Test OAuth flow: $PORTAL_URL"
echo "   3. Check logs: gcloud logging read 'resource.type=cloud_run_revision' --limit=50"
echo ""
