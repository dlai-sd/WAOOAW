#!/bin/bash
# Deploy WAOOAW Platform Portal v2 to UAT Environment
# GCP Cloud Run - us-central1
# Load Balancer with custom domains (uat-*.waooaw.com)
# Minimum 1 instance for faster response

set -e

PROJECT_ID="waooaw-oauth"
REGION="us-central1"
ENV="uat"

# Service names
BACKEND_SERVICE="waooaw-backend-uat"
PLATFORM_PORTAL_SERVICE="waooaw-platform-portal-uat"
CUSTOMER_PORTAL_SERVICE="waooaw-portal-uat"

# Custom domains
BACKEND_DOMAIN="uat-api.waooaw.com"
PLATFORM_PORTAL_DOMAIN="uat-pp.waooaw.com"
CUSTOMER_PORTAL_DOMAIN="uat-www.waooaw.com"

echo "🚀 Deploying WAOOAW Platform v2 to UAT Environment"
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

cd ../../backend-v2

gcloud run deploy $BACKEND_SERVICE \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --platform managed \
  --memory 1Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 100 \
  --min-instances 1 \
  --max-instances 20 \
  --set-env-vars "ENV=$ENV" \
  --set-secrets "GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,JWT_SECRET=JWT_SECRET:latest,DATABASE_URL=DATABASE_URL_UAT:latest,REDIS_URL=REDIS_URL_UAT:latest"

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
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 100 \
  --min-instances 1 \
  --max-instances 20 \
  --set-env-vars "ENV=$ENV,PORT=8080"

PORTAL_URL=$(gcloud run services describe $PLATFORM_PORTAL_SERVICE --region $REGION --format 'value(status.url)')
echo "✅ Platform Portal deployed: $PORTAL_URL"

echo ""
echo "📦 Step 3: Deploy Customer Portal (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
read -p "Deploy Customer Portal? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd ../WaooawPortal
    
    gcloud run deploy $CUSTOMER_PORTAL_SERVICE \
      --source . \
      --region $REGION \
      --allow-unauthenticated \
      --platform managed \
      --memory 512Mi \
      --cpu 1 \
      --timeout 300 \
      --concurrency 100 \
      --min-instances 1 \
      --max-instances 10 \
      --set-env-vars "ENV=$ENV"
    
    CUSTOMER_PORTAL_URL=$(gcloud run services describe $CUSTOMER_PORTAL_SERVICE --region $REGION --format 'value(status.url)')
    echo "✅ Customer Portal deployed: $CUSTOMER_PORTAL_URL"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ UAT DEPLOYMENT COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔗 Cloud Run URLs:"
echo "   Backend API:       $BACKEND_URL"
echo "   Platform Portal:   $PORTAL_URL"
echo ""
echo "🌐 Custom Domains (requires Load Balancer setup):"
echo "   Backend API:       https://$BACKEND_DOMAIN"
echo "   Platform Portal:   https://$PLATFORM_PORTAL_DOMAIN"
echo "   Customer Portal:   https://$CUSTOMER_PORTAL_DOMAIN"
echo ""
echo "🔐 OAuth Redirect URIs (add to Google Console):"
echo "   https://$BACKEND_DOMAIN/auth/callback"
echo "   https://$PLATFORM_PORTAL_DOMAIN/auth/callback"
echo ""
echo "📊 Next Steps:"
echo "   1. Configure Load Balancer for custom domains"
echo "   2. Update DNS records (A/AAAA) to point to Load Balancer IP"
echo "   3. Add redirect URIs to Google OAuth Console"
echo "   4. Test: https://$PLATFORM_PORTAL_DOMAIN"
echo ""
