#!/bin/bash
# OPA Service Build and Deploy Script
# Version: 1.0
# Owner: Platform Team

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-waooaw-oauth}"
REGION="${GCP_REGION:-us-central1}"
IMAGE_NAME="opa-service"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE="gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  OPA Service Build & Deploy            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Validate Rego policies
echo -e "${YELLOW}Step 1: Validating Rego policies...${NC}"
cd "$(dirname "$0")"

if command -v opa &> /dev/null; then
    for policy in policies/*.rego; do
        echo "  Checking $policy..."
        if opa check "$policy"; then
            echo -e "  ${GREEN}✅ $policy valid${NC}"
        else
            echo -e "  ${RED}❌ $policy has errors${NC}"
            exit 1
        fi
    done
else
    echo -e "${YELLOW}⚠️  OPA CLI not found, skipping validation${NC}"
fi
echo ""

# Step 2: Run tests
echo -e "${YELLOW}Step 2: Running OPA tests...${NC}"
if command -v opa &> /dev/null; then
    if [ -d "tests" ]; then
        opa test policies/ tests/ -v
        echo -e "${GREEN}✅ All tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️  No tests found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Skipping tests${NC}"
fi
echo ""

# Step 3: Build Docker image
echo -e "${YELLOW}Step 3: Building Docker image...${NC}"
docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" -t "${FULL_IMAGE}" .
echo -e "${GREEN}✅ Docker image built: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
echo ""

# Step 4: Push to GCR
echo -e "${YELLOW}Step 4: Pushing to Google Container Registry...${NC}"
docker push "${FULL_IMAGE}"
echo -e "${GREEN}✅ Image pushed: ${FULL_IMAGE}${NC}"
echo ""

# Step 5: Deploy to Cloud Run
echo -e "${YELLOW}Step 5: Deploying to Cloud Run...${NC}"
gcloud run deploy opa-service \
  --image="${FULL_IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --memory=128Mi \
  --cpu=0.1 \
  --min-instances=1 \
  --max-instances=3 \
  --port=8181 \
  --set-env-vars="REDIS_HOST=${REDIS_HOST},REDIS_PORT=${REDIS_PORT}" \
  --set-secrets="REDIS_PASSWORD=gateway-redis-password:latest" \
  --no-allow-unauthenticated

echo -e "${GREEN}✅ OPA service deployed successfully!${NC}"
echo ""

# Step 6: Get service URL
SERVICE_URL=$(gcloud run services describe opa-service --region="${REGION}" --format='value(status.url)')
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
echo ""

# Step 7: Test health check
echo -e "${YELLOW}Step 7: Testing health check...${NC}"
TOKEN=$(gcloud auth print-identity-token)
HEALTH_RESPONSE=$(curl -s -H "Authorization: Bearer ${TOKEN}" "${SERVICE_URL}/health")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "$HEALTH_RESPONSE"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "$HEALTH_RESPONSE"
fi
echo ""

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  OPA Service Deployment Complete!      ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "1. Update API Gateway environment variables with OPA_SERVICE_URL=${SERVICE_URL}"
echo "2. Grant API Gateway service accounts run.invoker role"
echo "3. Test policy evaluation"
