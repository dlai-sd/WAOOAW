#!/bin/bash
# Deploy all 5 Cloud Run services to asia-south1 (Mumbai)
# Phase 1: Single zone (a), scale-to-zero
# Usage: ./deploy-phase1.sh

set -e

PROJECT_ID="waooaw-oauth"
REGION="asia-south1"
REGISTRY="asia-south1-docker.pkg.dev"

echo "🚀 Deploying WAOOAW Platform - Phase 1 (Mumbai, Single Zone)"
echo "=============================================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Zone Strategy: Single zone (a), scale-to-zero"
echo ""

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not logged in to gcloud. Run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

echo ""
echo "📦 Step 1: Deploy Backend API (api.waooaw.com)"
echo "================================================"
gcloud run deploy waooaw-api \
    --image=$REGISTRY/$PROJECT_ID/waooaw-containers/waooaw-backend:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --port=8000 \
    --set-env-vars=ENV=production,FRONTEND_URL=https://www.waooaw.com,GOOGLE_REDIRECT_URI=https://api.waooaw.com/auth/callback,CORS_ORIGINS="https://www.waooaw.com,https://pp.waooaw.com,https://dp.waooaw.com,https://yk.waooaw.com" \
    --set-secrets=GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest \
    --execution-environment=gen2

echo ""
echo "📦 Step 2: Deploy Platform Portal (pp.waooaw.com)"
echo "==================================================="
# Note: Rename from waooaw-frontend-staging if it exists
gcloud run deploy waooaw-platform-portal \
    --image=$REGISTRY/$PROJECT_ID/waooaw-containers/waooaw-frontend:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --min-instances=0 \
    --max-instances=5 \
    --port=3000 \
    --set-env-vars=ENV=production,BACKEND_URL=https://api.waooaw.com \
    --set-secrets=OAUTH_CLIENT_ID=google-client-id:latest \
    --execution-environment=gen2

echo ""
echo "📦 Step 3: Deploy Development Portal (dp.waooaw.com)"
echo "======================================================"
# Note: Build dev portal image separately, or reuse platform portal for now
echo "⚠️  Dev Portal deployment skipped - build image first"
echo "   To deploy: Build DevPortal/ and push to registry, then run:"
echo "   gcloud run deploy waooaw-dev-portal --image=... --region=$REGION"

echo ""
echo "📦 Step 4: Deploy Customer Marketplace (www.waooaw.com)"
echo "========================================================"
echo "⚠️  Marketplace deployment skipped - build React app first"
echo "   To deploy: Build frontend/ React app and push to registry, then run:"
echo "   gcloud run deploy waooaw-marketplace --image=... --region=$REGION"

echo ""
echo "📦 Step 5: Deploy Customer Portal (yk.waooaw.com)"
echo "==================================================="
echo "⚠️  Customer portal deployment skipped - build template first"
echo "   To deploy: Build customer portal and push to registry, then run:"
echo "   gcloud run deploy waooaw-customer-yk --image=... --region=$REGION"

echo ""
echo "✅ Phase 1 Deployment Complete!"
echo "================================"
echo ""
echo "Deployed Services:"
echo "  - waooaw-api (Backend API)"
echo "  - waooaw-platform-portal (Platform Portal)"
echo ""
echo "Pending (build images first):"
echo "  - waooaw-marketplace (www.waooaw.com)"
echo "  - waooaw-dev-portal (dp.waooaw.com)"
echo "  - waooaw-customer-yk (yk.waooaw.com)"
echo ""
echo "Next Steps:"
echo "1. Build React marketplace app → push to registry"
echo "2. Clone & build dev portal → push to registry"
echo "3. Build customer portal template → push to registry"
echo "4. Run this script again (or deploy manually)"
echo "5. Configure load balancer URL map (see cloud/gcp/runbooks/)"
echo "6. Add DNS A records for pp, dp, yk subdomains"
echo "7. Create multi-domain SSL certificate"
echo ""
echo "Cost Estimate: $86-127/month (Phase 1)"
