#!/bin/bash
set -e

# Gateway Deployment Script for GCP Cloud Run
# Deploys CP and PP Gateways with all dependencies

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-waooaw-production}"
REGION="${GCP_REGION:-us-central1}"
ARTIFACT_REGISTRY="${ARTIFACT_REGISTRY:-us-central1-docker.pkg.dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}WAOOAW Gateway Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Image Tag: $IMAGE_TAG"
echo ""

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}ERROR: gcloud CLI not found. Install from https://cloud.google.com/sdk${NC}"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}ERROR: Docker not found. Install from https://www.docker.com${NC}"
        exit 1
    fi
    
    # Check terraform
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}ERROR: Terraform not found. Install from https://www.terraform.io${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Prerequisites OK${NC}"
}

# Build Docker images
build_images() {
    echo ""
    echo -e "${YELLOW}Building Docker images...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Build CP Gateway
    echo "Building CP Gateway..."
    docker build \
        -f infrastructure/docker/cp_gateway.Dockerfile \
        -t "$ARTIFACT_REGISTRY/$PROJECT_ID/waooaw/cp-gateway:$IMAGE_TAG" \
        .
    
    # Build PP Gateway
    echo "Building PP Gateway..."
    docker build \
        -f infrastructure/docker/pp_gateway.Dockerfile \
        -t "$ARTIFACT_REGISTRY/$PROJECT_ID/waooaw/pp-gateway:$IMAGE_TAG" \
        .
    
    echo -e "${GREEN}✓ Images built successfully${NC}"
}

# Push images to Artifact Registry
push_images() {
    echo ""
    echo -e "${YELLOW}Pushing images to Artifact Registry...${NC}"
    
    # Authenticate Docker with Artifact Registry
    gcloud auth configure-docker "$ARTIFACT_REGISTRY" --quiet
    
    # Push CP Gateway
    echo "Pushing CP Gateway..."
    docker push "$ARTIFACT_REGISTRY/$PROJECT_ID/waooaw/cp-gateway:$IMAGE_TAG"
    
    # Push PP Gateway
    echo "Pushing PP Gateway..."
    docker push "$ARTIFACT_REGISTRY/$PROJECT_ID/waooaw/pp-gateway:$IMAGE_TAG"
    
    echo -e "${GREEN}✓ Images pushed successfully${NC}"
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    echo ""
    echo -e "${YELLOW}Deploying infrastructure with Terraform...${NC}"
    
    cd "$PROJECT_ROOT/infrastructure/terraform"
    
    # Initialize Terraform
    terraform init
    
    # Plan
    terraform plan \
        -var="project_id=$PROJECT_ID" \
        -var="region=$REGION" \
        -var="image_tag=$IMAGE_TAG" \
        -out=tfplan
    
    # Apply
    terraform apply tfplan
    
    echo -e "${GREEN}✓ Infrastructure deployed${NC}"
}

# Run database migrations
run_migrations() {
    echo ""
    echo -e "${YELLOW}Running database migrations...${NC}"
    
    # Get Cloud SQL connection info
    INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe waooaw-postgres \
        --project="$PROJECT_ID" \
        --format="value(connectionName)")
    
    # Run migrations via Cloud SQL Proxy
    cd "$PROJECT_ROOT"
    
    # Start Cloud SQL Proxy in background
    ./cloud_sql_proxy -instances="$INSTANCE_CONNECTION_NAME"=tcp:5432 &
    PROXY_PID=$!
    
    sleep 5
    
    # Run migrations
    psql "postgresql://postgres@localhost:5432/waooaw" \
        < infrastructure/database/migrations/gateway_audit_logs.sql
    
    # Stop proxy
    kill $PROXY_PID
    
    echo -e "${GREEN}✓ Migrations completed${NC}"
}

# Deploy OPA policies
deploy_opa_policies() {
    echo ""
    echo -e "${YELLOW}Deploying OPA policies...${NC}"
    
    cd "$PROJECT_ROOT/infrastructure/opa"
    
    # Run OPA deployment script
    ./build-and-deploy.sh
    
    echo -e "${GREEN}✓ OPA policies deployed${NC}"
}

# Deploy Cost Guard Cloud Function
deploy_cost_guard() {
    echo ""
    echo -e "${YELLOW}Deploying Cost Guard Cloud Function...${NC}"
    
    cd "$PROJECT_ROOT/infrastructure/functions/cost_guard"
    
    # Run deployment script
    ./deploy.sh
    
    echo -e "${GREEN}✓ Cost Guard deployed${NC}"
}

# Verify deployment
verify_deployment() {
    echo ""
    echo -e "${YELLOW}Verifying deployment...${NC}"
    
    # Get service URLs
    CP_GATEWAY_URL=$(gcloud run services describe cp-gateway \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --format="value(status.url)")
    
    PP_GATEWAY_URL=$(gcloud run services describe pp-gateway \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --format="value(status.url)")
    
    # Health check CP Gateway
    echo "Checking CP Gateway..."
    if curl -f "$CP_GATEWAY_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ CP Gateway is healthy${NC}"
    else
        echo -e "${RED}✗ CP Gateway health check failed${NC}"
    fi
    
    # Health check PP Gateway
    echo "Checking PP Gateway..."
    if curl -f "$PP_GATEWAY_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PP Gateway is healthy${NC}"
    else
        echo -e "${RED}✗ PP Gateway health check failed${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "CP Gateway URL: $CP_GATEWAY_URL"
    echo "PP Gateway URL: $PP_GATEWAY_URL"
    echo ""
    echo "Next steps:"
    echo "1. Configure DNS: cp.waooaw.com → $CP_GATEWAY_URL"
    echo "2. Configure DNS: pp.waooaw.com → $PP_GATEWAY_URL"
    echo "3. Set up monitoring alerts"
    echo "4. Run integration tests"
}

# Main execution
main() {
    check_prerequisites
    build_images
    push_images
    deploy_infrastructure
    run_migrations
    deploy_opa_policies
    deploy_cost_guard
    verify_deployment
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
