#!/bin/bash
# WAOOAW Infrastructure Deployment using gcloud commands
# Single IP (35.190.6.91) routes to ALL environments

set -e

ENVIRONMENT=${1:-demo}
PROJECT="waooaw-oauth"
STATIC_IP="35.190.6.91"
STATIC_IP_NAME="waooaw-lb-ip"
REGION="asia-south1"

# Domain configuration
declare -A CUSTOMER_DOMAINS=(
    ["demo"]="cp.demo.waooaw.com"
    ["uat"]="cp.uat.waooaw.com"
    ["prod"]="www.waooaw.com"
)

declare -A PLATFORM_DOMAINS=(
    ["demo"]="pp.demo.waooaw.com"
    ["uat"]="pp.uat.waooaw.com"
    ["prod"]="pp.waooaw.com"
)

CUSTOMER_DOMAIN="${CUSTOMER_DOMAINS[$ENVIRONMENT]}"
PLATFORM_DOMAIN="${PLATFORM_DOMAINS[$ENVIRONMENT]}"

echo "🚀 Deploying $ENVIRONMENT environment"
echo "   Project: $PROJECT"
echo "   Customer Portal: $CUSTOMER_DOMAIN"
echo "   Platform Portal: $PLATFORM_DOMAIN"
echo "   Static IP: $STATIC_IP"
echo "================================"

# 1. Deploy Cloud Run Services
echo "📦 Deploying Cloud Run services..."

# Backend API
echo "  ├─ Backend API (waooaw-api-$ENVIRONMENT)..."
gcloud run deploy "waooaw-api-$ENVIRONMENT" \
  --image="gcr.io/$PROJECT/waooaw-api:latest" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8000 \
  --cpu=1 \
  --memory=512Mi \
  --min-instances=0 \
  --max-instances=5 \
  --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
  --set-secrets="GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,JWT_SECRET=JWT_SECRET:latest" \
  --quiet || echo "Warning: Backend API deployment failed or already exists"

# Customer Portal
echo "  ├─ Customer Portal (waooaw-portal-$ENVIRONMENT)..."
gcloud run deploy "waooaw-portal-$ENVIRONMENT" \
  --image="gcr.io/$PROJECT/waooaw-portal:latest" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --cpu=1 \
  --memory=512Mi \
  --min-instances=0 \
  --max-instances=5 \
  --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
  --quiet || echo "Warning: Customer Portal deployment failed or already exists"

# Platform Portal  
echo "  └─ Platform Portal (waooaw-platform-portal-$ENVIRONMENT)..."
gcloud run deploy "waooaw-platform-portal-$ENVIRONMENT" \
  --image="gcr.io/$PROJECT/waooaw-platform-portal:latest" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --cpu=1 \
  --memory=1Gi \
  --min-instances=0 \
  --max-instances=5 \
  --set-env-vars="ENVIRONMENT=$ENVIRONMENT" \
  --set-secrets="GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,JWT_SECRET=JWT_SECRET:latest" \
  --quiet || echo "Warning: Platform Portal deployment failed or already exists"

# 2. Create Network Endpoint Groups
echo ""
echo "🌐 Creating Network Endpoint Groups..."

echo "  ├─ API NEG..."
gcloud compute network-endpoint-groups create "waooaw-$ENVIRONMENT-api-neg" \
  --region="$REGION" \
  --network-endpoint-type=SERVERLESS \
  --cloud-run-service="waooaw-api-$ENVIRONMENT" \
  --quiet 2>/dev/null || echo "  │  (already exists)"

echo "  ├─ Customer NEG..."
gcloud compute network-endpoint-groups create "waooaw-$ENVIRONMENT-customer-neg" \
  --region="$REGION" \
  --network-endpoint-type=SERVERLESS \
  --cloud-run-service="waooaw-portal-$ENVIRONMENT" \
  --quiet 2>/dev/null || echo "  │  (already exists)"

echo "  └─ Platform NEG..."
gcloud compute network-endpoint-groups create "waooaw-$ENVIRONMENT-platform-neg" \
  --region="$REGION" \
  --network-endpoint-type=SERVERLESS \
  --cloud-run-service="waooaw-platform-portal-$ENVIRONMENT" \
  --quiet 2>/dev/null || echo "  │  (already exists)"

# 3. Create Health Checks
echo ""
echo "🏥 Creating health checks..."

echo "  ├─ API health check..."
gcloud compute health-checks create https "$ENVIRONMENT-api-health-check" \
  --port=443 \
  --request-path=/health \
  --check-interval=10s \
  --timeout=5s \
  --unhealthy-threshold=3 \
  --healthy-threshold=2 \
  --quiet 2>/dev/null || echo "  │  (already exists)"

echo "  ├─ Customer health check..."
gcloud compute health-checks create https "$ENVIRONMENT-customer-health-check" \
  --port=443 \
  --request-path=/ \
  --check-interval=10s \
  --timeout=5s \
  --unhealthy-threshold=3 \
  --healthy-threshold=2 \
  --quiet 2>/dev/null || echo "  │  (already exists)"

echo "  └─ Platform health check..."
gcloud compute health-checks create https "$ENVIRONMENT-platform-health-check" \
  --port=443 \
  --request-path=/ \
  --check-interval=10s \
  --timeout=5s \
  --unhealthy-threshold=3 \
  --healthy-threshold=2 \
  --quiet 2>/dev/null || echo "  │  (already exists)"

# 4. Create Backend Services
echo ""
echo "🔧 Creating backend services..."

echo "  ├─ API backend..."
gcloud compute backend-services create "$ENVIRONMENT-api-backend" \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --protocol=HTTPS \
  --port-name=http \
  --timeout=30s \
  --health-checks="$ENVIRONMENT-api-health-check" \
  --enable-logging \
  --logging-sample-rate=1.0 \
  --quiet 2>/dev/null || echo "  │  (already exists)"

gcloud compute backend-services add-backend "$ENVIRONMENT-api-backend" \
  --global \
  --network-endpoint-group="waooaw-$ENVIRONMENT-api-neg" \
  --network-endpoint-group-region="$REGION" \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8 \
  --quiet 2>/dev/null || echo "  │  (backend already added)"

echo "  ├─ Customer backend..."
gcloud compute backend-services create "$ENVIRONMENT-customer-backend" \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --protocol=HTTPS \
  --port-name=http \
  --timeout=30s \
  --health-checks="$ENVIRONMENT-customer-health-check" \
  --enable-logging \
  --logging-sample-rate=1.0 \
  --quiet 2>/dev/null || echo "  │  (already exists)"

gcloud compute backend-services add-backend "$ENVIRONMENT-customer-backend" \
  --global \
  --network-endpoint-group="waooaw-$ENVIRONMENT-customer-neg" \
  --network-endpoint-group-region="$REGION" \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8 \
  --quiet 2>/dev/null || echo "  │  (backend already added)"

echo "  └─ Platform backend..."
gcloud compute backend-services create "$ENVIRONMENT-platform-backend" \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --protocol=HTTPS \
  --port-name=http \
  --timeout=30s \
  --health-checks="$ENVIRONMENT-platform-health-check" \
  --enable-logging \
  --logging-sample-rate=1.0 \
  --quiet 2>/dev/null || echo "  │  (already exists)"

gcloud compute backend-services add-backend "$ENVIRONMENT-platform-backend" \
  --global \
  --network-endpoint-group="waooaw-$ENVIRONMENT-platform-neg" \
  --network-endpoint-group-region="$REGION" \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8 \
  --quiet 2>/dev/null || echo "  │  (backend already added)"

# 5. Create URL Map with host-based routing
echo ""
echo "🗺️  Creating URL map..."

# Create a temporary URL map config
cat > /tmp/urlmap-$ENVIRONMENT.yaml <<EOF
name: $ENVIRONMENT-url-map
defaultService: https://www.googleapis.com/compute/v1/projects/$PROJECT/global/backendServices/$ENVIRONMENT-customer-backend
hostRules:
- hosts:
  - $CUSTOMER_DOMAIN
  pathMatcher: customer-matcher
- hosts:
  - $PLATFORM_DOMAIN
  pathMatcher: platform-matcher
pathMatchers:
- name: customer-matcher
  defaultService: https://www.googleapis.com/compute/v1/projects/$PROJECT/global/backendServices/$ENVIRONMENT-customer-backend
  pathRules:
  - paths:
    - /api/*
    - /auth/*
    - /health
    service: https://www.googleapis.com/compute/v1/projects/$PROJECT/global/backendServices/$ENVIRONMENT-api-backend
- name: platform-matcher
  defaultService: https://www.googleapis.com/compute/v1/projects/$PROJECT/global/backendServices/$ENVIRONMENT-platform-backend
  pathRules:
  - paths:
    - /api/*
    - /auth/*
    - /health
    service: https://www.googleapis.com/compute/v1/projects/$PROJECT/global/backendServices/$ENVIRONMENT-api-backend
EOF

gcloud compute url-maps import "$ENVIRONMENT-url-map" \
  --source=/tmp/urlmap-$ENVIRONMENT.yaml \
  --quiet 2>/dev/null || echo "  (already exists, updating...)" && \
gcloud compute url-maps import "$ENVIRONMENT-url-map" \
  --source=/tmp/urlmap-$ENVIRONMENT.yaml \
  --quiet

# 6. Create SSL Certificates
echo ""
echo "🔒 Creating SSL certificates..."

echo "  ├─ Customer SSL cert..."
gcloud compute ssl-certificates create "$ENVIRONMENT-customer-ssl" \
  --domains="$CUSTOMER_DOMAIN" \
  --global \
  --quiet 2>/dev/null || echo "  │  (already exists)"

echo "  └─ Platform SSL cert..."
gcloud compute ssl-certificates create "$ENVIRONMENT-platform-ssl" \
  --domains="$PLATFORM_DOMAIN" \
  --global \
  --quiet 2>/dev/null || echo "  │  (already exists)"

# 7. Create HTTPS Proxy
echo ""
echo "🔐 Creating HTTPS proxy..."

gcloud compute target-https-proxies create "$ENVIRONMENT-https-proxy" \
  --url-map="$ENVIRONMENT-url-map" \
  --ssl-certificates="$ENVIRONMENT-customer-ssl,$ENVIRONMENT-platform-ssl" \
  --global \
  --quiet 2>/dev/null || echo "  (already exists, updating...)" && \
gcloud compute target-https-proxies update "$ENVIRONMENT-https-proxy" \
  --url-map="$ENVIRONMENT-url-map" \
  --ssl-certificates="$ENVIRONMENT-customer-ssl,$ENVIRONMENT-platform-ssl" \
  --quiet

# 8. Create HTTP to HTTPS Redirect
echo ""
echo "🔀 Creating HTTP redirect..."

# Create redirect URL map
cat > /tmp/redirect-urlmap.yaml <<EOF
name: $ENVIRONMENT-http-redirect-map
defaultUrlRedirect:
  httpsRedirect: true
  redirectResponseCode: MOVED_PERMANENTLY_DEFAULT
EOF

gcloud compute url-maps import "$ENVIRONMENT-http-redirect-map" \
  --source=/tmp/redirect-urlmap.yaml \
  --quiet 2>/dev/null || \
gcloud compute url-maps import "$ENVIRONMENT-http-redirect-map" \
  --source=/tmp/redirect-urlmap.yaml \
  --quiet

gcloud compute target-http-proxies create "$ENVIRONMENT-http-proxy" \
  --url-map="$ENVIRONMENT-http-redirect-map" \
  --global \
  --quiet 2>/dev/null || echo "  (already exists)"

# 9. Create Forwarding Rules (uses existing static IP)
echo ""
echo "📡 Creating forwarding rules..."

echo "  ├─ HTTPS forwarding rule..."
gcloud compute forwarding-rules create "$ENVIRONMENT-https-forwarding-rule" \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --address="$STATIC_IP_NAME" \
  --target-https-proxy="$ENVIRONMENT-https-proxy" \
  --ports=443 \
  --quiet 2>/dev/null || echo "  │  (already exists)"

echo "  └─ HTTP forwarding rule..."
gcloud compute forwarding-rules create "$ENVIRONMENT-http-forwarding-rule" \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --address="$STATIC_IP_NAME" \
  --target-http-proxy="$ENVIRONMENT-http-proxy" \
  --ports=80 \
  --quiet 2>/dev/null || echo "  │  (already exists)"

echo ""
echo "================================"
echo "✅ Deployment complete!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Configure DNS (if not done):"
echo "   Add A records in GoDaddy pointing to $STATIC_IP:"
echo "   - $CUSTOMER_DOMAIN → $STATIC_IP"
echo "   - $PLATFORM_DOMAIN → $STATIC_IP"
echo ""
echo "2. Update OAuth Console:"
echo "   https://console.cloud.google.com/apis/credentials"
echo "   Add authorized origins:"
echo "   - https://$CUSTOMER_DOMAIN"
echo "   - https://$PLATFORM_DOMAIN"
echo "   Add redirect URIs:"
echo "   - https://$CUSTOMER_DOMAIN/api/auth/callback"
echo "   - https://$PLATFORM_DOMAIN/api/auth/callback"
echo ""
echo "3. Check SSL certificate status (takes 10-15 minutes):"
echo "   gcloud compute ssl-certificates list --global"
echo ""
echo "4. Test the deployment:"
echo "   Customer Portal: https://$CUSTOMER_DOMAIN"
echo "   Platform Portal: https://$PLATFORM_DOMAIN"
echo "   Backend API: https://$CUSTOMER_DOMAIN/api/health"
echo ""
