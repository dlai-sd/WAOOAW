#!/bin/bash
# Master Test Runner for Phase 0
# Version: 1.0
# Owner: Platform Team

set -e

echo "========================================"
echo "PHASE 0 INTEGRATION TEST SUITE"
echo "GW-00P: Prerequisites & Contracts"
echo "========================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TOTAL_PASSED=0
TOTAL_FAILED=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test 1: JWT Contract Validation
echo -e "${BLUE}═══ Test 1: JWT Contract Validation ═══${NC}"
echo ""

if command -v python3 &> /dev/null; then
    # Install dependencies if needed
    if ! python3 -c "import jwt" 2>/dev/null; then
        echo "Installing PyJWT..."
        pip3 install --quiet PyJWT pytest
    fi
    
    if python3 "$SCRIPT_DIR/test_jwt_contract.py"; then
        echo -e "${GREEN}✅ JWT Contract tests PASSED${NC}"
        ((TOTAL_PASSED++))
    else
        echo -e "${RED}❌ JWT Contract tests FAILED${NC}"
        ((TOTAL_FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️  Python3 not found, skipping JWT tests${NC}"
fi
echo ""

# Test 2: Environment Variables Validation
echo -e "${BLUE}═══ Test 2: Environment Variables Validation ═══${NC}"
echo ""

# Create temporary .env file with test values
TEST_ENV_FILE="/tmp/test_gateway.env"
cat > "$TEST_ENV_FILE" << 'EOF'
# Test environment variables
JWT_SECRET_CP="test-secret-cp-12345"
JWT_ALGORITHM="HS256"
JWT_ISSUER="cp.waooaw.com"
JWT_MAX_LIFETIME_SECONDS=86400

OPA_SERVICE_URL="http://localhost:8181"
PLANT_API_URL="http://localhost:8000"
PLANT_API_TIMEOUT_SECONDS=30

DATABASE_URL="postgresql://gateway:gateway@localhost:5432/gateway_audit"
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_PASSWORD=""

RATE_LIMIT_TRIAL=100
RATE_LIMIT_PAID=1000
RATE_LIMIT_ENTERPRISE=10000

AGENT_BUDGET_CAP_USD=1.00
PLATFORM_BUDGET_CAP_USD=100.00
COST_GUARD_THRESHOLD_80=80.00
COST_GUARD_THRESHOLD_95=95.00

TRIAL_TASK_LIMIT_PER_DAY=10
TRIAL_DURATION_DAYS=7

FEATURE_FLAG_OPA_POLICY=true
FEATURE_FLAG_BUDGET_GUARD=true
FEATURE_FLAG_RATE_LIMITING=true

LOG_LEVEL="INFO"
GCP_PROJECT_ID="waooaw-oauth"
ENVIRONMENT="local"
EOF

# Source test environment
set -a
source "$TEST_ENV_FILE"
set +a

if "$SCRIPT_DIR/validate_env_vars.sh"; then
    echo -e "${GREEN}✅ Environment Variables validation PASSED${NC}"
    ((TOTAL_PASSED++))
else
    echo -e "${RED}❌ Environment Variables validation FAILED${NC}"
    ((TOTAL_FAILED++))
fi

# Cleanup
rm -f "$TEST_ENV_FILE"
echo ""

# Test 3: Terraform Module Validation
echo -e "${BLUE}═══ Test 3: Terraform Module Validation ═══${NC}"
echo ""

if command -v terraform &> /dev/null; then
    if "$SCRIPT_DIR/validate_terraform.sh"; then
        echo -e "${GREEN}✅ Terraform validation PASSED${NC}"
        ((TOTAL_PASSED++))
    else
        echo -e "${RED}❌ Terraform validation FAILED${NC}"
        ((TOTAL_FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️  Terraform not found, skipping Terraform tests${NC}"
fi
echo ""

# Test 4: Contract Documents Exist
echo -e "${BLUE}═══ Test 4: Contract Documents Validation ═══${NC}"
echo ""

CONTRACTS_DIR="/workspaces/WAOOAW/main/Foundation/Architecture/APIGateway/contracts"
REQUIRED_CONTRACTS=(
    "JWT_CONTRACT.md"
    "PLANT_API_CONTRACT.md"
    "ENVIRONMENT_VARIABLES.md"
)

CONTRACT_PASSED=0
for contract in "${REQUIRED_CONTRACTS[@]}"; do
    if [ -f "$CONTRACTS_DIR/$contract" ]; then
        # Check file size (should be > 1KB) - Linux stat format
        FILE_SIZE=$(stat -c%s "$CONTRACTS_DIR/$contract" 2>/dev/null || echo "0")
        if [ "$FILE_SIZE" -gt 1024 ]; then
            echo -e "${GREEN}✅ $contract exists and is substantial ($FILE_SIZE bytes)${NC}"
            ((CONTRACT_PASSED++))
        else
            echo -e "${YELLOW}⚠️  $contract exists but seems incomplete ($FILE_SIZE bytes)${NC}"
        fi
    else
        echo -e "${RED}❌ $contract is missing${NC}"
    fi
done

if [ "$CONTRACT_PASSED" -eq "${#REQUIRED_CONTRACTS[@]}" ]; then
    echo -e "${GREEN}✅ All contract documents present${NC}"
    ((TOTAL_PASSED++))
else
    echo -e "${RED}❌ Some contract documents missing or incomplete${NC}"
    ((TOTAL_FAILED++))
fi
echo ""

# Test 5: Terraform Files Structure
echo -e "${BLUE}═══ Test 5: Terraform Files Structure ═══${NC}"
echo ""

TERRAFORM_DIR="/workspaces/WAOOAW/infrastructure/terraform/modules/gateway"
REQUIRED_TF_FILES=(
    "main.tf"
    "variables.tf"
    "secrets.tf"
    "iam.tf"
    "monitoring.tf"
)

TF_FILES_PASSED=0
for tf_file in "${REQUIRED_TF_FILES[@]}"; do
    if [ -f "$TERRAFORM_DIR/$tf_file" ]; then
        FILE_SIZE=$(stat -c%s "$TERRAFORM_DIR/$tf_file" 2>/dev/null || echo "0")
        echo -e "${GREEN}✅ $tf_file exists ($FILE_SIZE bytes)${NC}"
        ((TF_FILES_PASSED++))
    else
        echo -e "${RED}❌ $tf_file is missing${NC}"
    fi
done

if [ "$TF_FILES_PASSED" -eq "${#REQUIRED_TF_FILES[@]}" ]; then
    echo -e "${GREEN}✅ All Terraform files present${NC}"
    ((TOTAL_PASSED++))
else
    echo -e "${RED}❌ Some Terraform files missing${NC}"
    ((TOTAL_FAILED++))
fi
echo ""

# Summary
echo "========================================"
echo "PHASE 0 TEST SUMMARY"
echo "========================================"
echo -e "${GREEN}✅ Test Suites Passed: $TOTAL_PASSED${NC}"
echo -e "${RED}❌ Test Suites Failed: $TOTAL_FAILED${NC}"
echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Phase 0 Prerequisites are COMPLETE!${NC}"
    echo ""
    echo "✅ JWT Contract specification created"
    echo "✅ Plant API Contract specification created"
    echo "✅ Environment Variables template created"
    echo "✅ Terraform modules created (5 files)"
    echo "✅ All validation tests passed"
    echo ""
    echo "Next Steps:"
    echo "1. Review contracts in: $CONTRACTS_DIR"
    echo "2. Review Terraform in: $TERRAFORM_DIR"
    echo "3. Proceed to Phase 1: OPA Deployment (GW-000)"
    exit 0
else
    echo -e "${RED}⚠️  Phase 0 has issues that need to be resolved${NC}"
    echo ""
    echo "Please fix the failing tests before proceeding to Phase 1."
    exit 1
fi
