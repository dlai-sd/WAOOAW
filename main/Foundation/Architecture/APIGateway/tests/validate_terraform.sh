#!/bin/bash
# Terraform Validation Script
# Version: 1.0
# Owner: Platform Team

set -e

echo "========================================"
echo "TERRAFORM MODULE VALIDATION"
echo "========================================"
echo ""

MODULE_DIR="/workspaces/WAOOAW/infrastructure/terraform/modules/gateway"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Change to module directory
cd "$MODULE_DIR"

echo "1. Terraform Format Check"
echo "--------------------------"
if terraform fmt -check -recursive; then
    echo -e "${GREEN}✅ PASS${NC}: All Terraform files are properly formatted"
else
    echo -e "${YELLOW}⚠️  WARN${NC}: Some files need formatting (running fmt...)"
    terraform fmt -recursive
fi
echo ""

echo "2. Terraform Initialization"
echo "---------------------------"
if terraform init -backend=false; then
    echo -e "${GREEN}✅ PASS${NC}: Terraform initialized successfully"
else
    echo -e "${RED}❌ FAIL${NC}: Terraform initialization failed"
    exit 1
fi
echo ""

echo "3. Terraform Validation"
echo "-----------------------"
if terraform validate; then
    echo -e "${GREEN}✅ PASS${NC}: Terraform configuration is valid"
else
    echo -e "${RED}❌ FAIL${NC}: Terraform validation failed"
    exit 1
fi
echo ""

echo "4. Required Files Check"
echo "-----------------------"
REQUIRED_FILES=(
    "main.tf"
    "variables.tf"
    "secrets.tf"
    "iam.tf"
    "monitoring.tf"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ PASS${NC}: $file exists"
    else
        echo -e "${RED}❌ FAIL${NC}: $file is missing"
        exit 1
    fi
done
echo ""

echo "5. Variable Definitions Check"
echo "------------------------------"
REQUIRED_VARS=(
    "project_id"
    "region"
    "environment"
    "cloud_sql_instance_name"
    "redis_instance_name"
)

for var in "${REQUIRED_VARS[@]}"; do
    if grep -q "variable \"$var\"" variables.tf; then
        echo -e "${GREEN}✅ PASS${NC}: Variable $var is defined"
    else
        echo -e "${RED}❌ FAIL${NC}: Variable $var is missing"
        exit 1
    fi
done
echo ""

echo "6. Resource Definitions Check"
echo "------------------------------"
REQUIRED_RESOURCES=(
    "google_service_account.gateway_cp"
    "google_service_account.gateway_pp"
    "google_service_account.opa_service"
    "google_cloud_run_service.gateway_cp"
    "google_cloud_run_service.gateway_pp"
    "google_cloud_run_service.opa_service"
    "google_secret_manager_secret.jwt_secret_cp"
    "google_secret_manager_secret.jwt_secret_pp"
    "google_storage_bucket.opa_bundles"
)

for resource in "${REQUIRED_RESOURCES[@]}"; do
    if grep -q "resource \"${resource%%.*}\" \"${resource##*.}\"" *.tf; then
        echo -e "${GREEN}✅ PASS${NC}: Resource $resource is defined"
    else
        echo -e "${RED}❌ FAIL${NC}: Resource $resource is missing"
        exit 1
    fi
done
echo ""

echo "7. Output Definitions Check"
echo "---------------------------"
REQUIRED_OUTPUTS=(
    "gateway_cp_url"
    "gateway_pp_url"
    "opa_service_url"
)

for output in "${REQUIRED_OUTPUTS[@]}"; do
    if grep -q "output \"$output\"" main.tf; then
        echo -e "${GREEN}✅ PASS${NC}: Output $output is defined"
    else
        echo -e "${RED}❌ FAIL${NC}: Output $output is missing"
        exit 1
    fi
done
echo ""

echo "8. Syntax Check (All Files)"
echo "----------------------------"
FILES=$(find . -name "*.tf")
for file in $FILES; do
    if terraform fmt -check "$file" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}: $file syntax valid"
    else
        echo -e "${YELLOW}⚠️  WARN${NC}: $file has formatting issues"
    fi
done
echo ""

echo "========================================"
echo "VALIDATION COMPLETE"
echo "========================================"
echo -e "${GREEN}All Terraform validation checks passed!${NC}"
echo ""
echo "Next steps:"
echo "1. Set required variables in terraform.tfvars"
echo "2. Run: terraform plan"
echo "3. Review changes carefully"
echo "4. Run: terraform apply"
