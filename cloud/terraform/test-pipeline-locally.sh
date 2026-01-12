#!/bin/bash

#############################################################################
# WAOOAW Local Pipeline Test Script
# Tests the complete pipeline workflow locally without deploying to GCP
#############################################################################

# Don't exit on error - we want to collect all test results
# set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=0

print_header() {
    echo ""
    echo -e "${CYAN}======================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}======================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((TESTS_PASSED++))
}

print_failure() {
    echo -e "${RED}❌ FAIL: $1${NC}"
    ((TESTS_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header "🧪 WAOOAW Local Pipeline Test - Architecture v2.0"

# Get workspace root
WORKSPACE_ROOT="/workspaces/WAOOAW"
cd "$WORKSPACE_ROOT"

#############################################################################
# Test 1: Component Path Validation
#############################################################################

print_header "Test 1: Component Path Validation"

# CP Component
if [ -d "src/CP/BackEnd" ] && [ -d "src/CP/FrontEnd" ]; then
    print_success "CP component paths exist"
else
    print_failure "CP component paths missing"
fi

# PP Component
if [ -d "src/PP/BackEnd" ] && [ -d "src/PP/FrontEnd" ]; then
    print_success "PP component paths exist"
else
    print_warning "PP component paths missing (expected for demo-only deployment)"
fi

# Plant Component
if [ -d "src/Plant/BackEnd" ]; then
    print_success "Plant component path exists"
else
    print_warning "Plant component path missing (expected for demo-only deployment)"
fi

#############################################################################
# Test 2: Terraform Configuration Validation
#############################################################################

print_header "Test 2: Terraform Configuration Validation"

cd cloud/terraform

# Check terraform is available
if command -v terraform &> /dev/null; then
    print_success "Terraform CLI installed"
else
    print_failure "Terraform CLI not found"
fi

# Terraform format check
print_info "Running terraform fmt check..."
if terraform fmt -check -recursive . > /dev/null 2>&1; then
    print_success "Terraform files are properly formatted"
else
    print_warning "Terraform files need formatting (run: terraform fmt -recursive)"
fi

# Terraform init
print_info "Running terraform init..."
if terraform init -backend=false > /tmp/tf-init.log 2>&1; then
    print_success "Terraform init successful"
else
    print_failure "Terraform init failed (check /tmp/tf-init.log)"
    cat /tmp/tf-init.log
fi

# Terraform validate
print_info "Running terraform validate..."
if terraform validate > /tmp/tf-validate.log 2>&1; then
    print_success "Terraform configuration is valid"
else
    print_failure "Terraform validation failed (check /tmp/tf-validate.log)"
    cat /tmp/tf-validate.log
fi

#############################################################################
# Test 2.5: GCP Naming Convention Check
#############################################################################

print_header "Test 2.5: GCP Naming Convention Check"

# Check for underscores in module names
if grep -E 'module "[a-zA-Z0-9]*_[a-zA-Z0-9]*"' main.tf > /dev/null; then
    print_warning "Module names contain underscores (converted to hyphens in NEG resources)"
else
    print_success "No underscores in module names"
fi

# Check for uppercase in resource names
if grep -E '(name.*=.*"[^"]*[A-Z][^"]*")' main.tf > /dev/null 2>&1; then
    print_failure "Found uppercase letters in resource names (GCP requires lowercase)"
else
    print_success "All resource names use lowercase"
fi

# Verify NEG naming uses replace function
if grep -q 'replace(each.key, "_", "-")' modules/networking/main.tf; then
    print_success "NEG module converts underscores to hyphens"
else
    print_failure "NEG module missing underscore-to-hyphen conversion"
fi

#############################################################################
# Test 3: Variable Definitions Check
#############################################################################

print_header "Test 3: Variable Definitions Check"

# Check variables.tf has new enable flags
if grep -q "enable_cp" variables.tf && \
   grep -q "enable_pp" variables.tf && \
   grep -q "enable_plant" variables.tf; then
    print_success "New enable flags defined in variables.tf"
else
    print_failure "Missing enable_cp/pp/plant variables"
fi

# Check for deprecated variables
if grep -q "enable_backend_api" variables.tf || \
   grep -q "enable_customer_portal" variables.tf || \
   grep -q "enable_platform_portal" variables.tf; then
    print_failure "Deprecated variables still present in variables.tf"
else
    print_success "No deprecated variables in variables.tf"
fi

# Check demo.tfvars
if [ -f "demo.tfvars" ] || [ -f "environments/demo.tfvars" ]; then
    DEMO_TFVARS=$([ -f "demo.tfvars" ] && echo "demo.tfvars" || echo "environments/demo.tfvars")
    print_success "demo.tfvars exists ($DEMO_TFVARS)"
    
    if grep -q "enable_cp.*=.*true" "$DEMO_TFVARS"; then
        print_success "demo.tfvars enables CP component"
    else
        print_failure "demo.tfvars missing enable_cp = true"
    fi
    
    if grep -q "cp_frontend_image" "$DEMO_TFVARS" && \
       grep -q "cp_backend_image" "$DEMO_TFVARS"; then
        print_success "demo.tfvars has new image variables"
    else
        print_failure "demo.tfvars missing new image variables"
    fi
else
    print_failure "demo.tfvars not found"
fi

#############################################################################
# Test 4: Module Validation
#############################################################################

print_header "Test 4: Module Validation"

# Check cloud-run module
if [ -f "modules/cloud-run/main.tf" ]; then
    print_success "cloud-run module exists"
    
    if grep -q "service_account" modules/cloud-run/outputs.tf; then
        print_success "cloud-run module has service_account output"
    else
        print_failure "cloud-run module missing service_account output"
    fi
else
    print_failure "cloud-run module not found"
fi

# Check load-balancer module
if [ -f "modules/load-balancer/main.tf" ]; then
    print_success "load-balancer module exists"
    
    if grep -q "enable_cp" modules/load-balancer/main.tf; then
        print_success "load-balancer module uses new enable flags"
    else
        print_failure "load-balancer module missing enable_cp references"
    fi
else
    print_failure "load-balancer module not found"
fi

# Check networking module
if [ -f "modules/networking/main.tf" ]; then
    print_success "networking module exists"
else
    print_failure "networking module not found"
fi

#############################################################################
# Test 5: main.tf Service Definitions
#############################################################################

print_header "Test 5: main.tf Service Definitions"

# Check for 8 service modules (count distinct module definitions)
cp_frontend=$(grep "module \"cp_frontend\"" main.tf | wc -l)
cp_backend=$(grep "module \"cp_backend\"" main.tf | wc -l)
cp_health=$(grep "module \"cp_health\"" main.tf | wc -l)
pp_frontend=$(grep "module \"pp_frontend\"" main.tf | wc -l)
pp_backend=$(grep "module \"pp_backend\"" main.tf | wc -l)
pp_health=$(grep "module \"pp_health\"" main.tf | wc -l)
plant_backend=$(grep "module \"plant_backend\"" main.tf | wc -l)
plant_health=$(grep "module \"plant_health\"" main.tf | wc -l)

total_services=$((cp_frontend + cp_backend + cp_health + pp_frontend + pp_backend + pp_health + plant_backend + plant_health))

if [ "$total_services" -eq 8 ]; then
    print_success "All 8 service modules defined in main.tf"
else
    print_warning "Found $total_services module definitions (expected 8 unique modules)"
fi

# Check IAM bindings (look for resource definitions)
if grep -q "resource \"google_cloud_run_service_iam_member\" \"cp_to_plant\"" main.tf && \
   grep -q "resource \"google_cloud_run_service_iam_member\" \"pp_to_plant\"" main.tf; then
    print_success "IAM bindings configured (CP→Plant, PP→Plant)"
else
    print_warning "IAM bindings may need verification in main.tf"
fi

#############################################################################
# Test 6: GitHub Actions Workflow Validation
#############################################################################

print_header "Test 6: GitHub Actions Workflow Validation"

cd "$WORKSPACE_ROOT"
WORKFLOW_FILE=".github/workflows/cp-pipeline.yml"

if [ -f "$WORKFLOW_FILE" ]; then
    print_success "Workflow file exists"
else
    print_failure "Workflow file not found"
    exit 1
fi

# Check for new enable flags in workflow inputs
if grep -q "enable_cp:" "$WORKFLOW_FILE" && \
   grep -q "enable_pp:" "$WORKFLOW_FILE" && \
   grep -q "enable_plant:" "$WORKFLOW_FILE"; then
    print_success "Workflow has new enable flags in inputs"
else
    print_failure "Workflow missing enable_cp/pp/plant inputs"
fi

# Check for deprecated variables
if grep -q "enable_backend_api" "$WORKFLOW_FILE" || \
   grep -q "enable_customer_portal" "$WORKFLOW_FILE" || \
   grep -q "enable_platform_portal" "$WORKFLOW_FILE"; then
    print_failure "Workflow still contains deprecated variables"
else
    print_success "No deprecated variables in workflow"
fi

# Check for validate-components job
if grep -q "validate-components:" "$WORKFLOW_FILE"; then
    print_success "validate-components job exists"
else
    print_failure "validate-components job not found"
fi

# Check for backend-test job
if grep -q "backend-test:" "$WORKFLOW_FILE"; then
    print_success "backend-test job exists"
else
    print_failure "backend-test job not found"
fi

# Check for terraform-deploy job
if grep -q "terraform-deploy:" "$WORKFLOW_FILE"; then
    print_success "terraform-deploy job exists"
else
    print_failure "terraform-deploy job not found"
fi

#############################################################################
# Test 7: Smoke Test Configuration
#############################################################################

print_header "Test 7: Smoke Test Configuration"

# Check for component-level smoke tests
if grep -q "Smoke Test - CP Component" "$WORKFLOW_FILE" && \
   grep -q "Smoke Test - PP Component" "$WORKFLOW_FILE" && \
   grep -q "Smoke Test - Plant Component" "$WORKFLOW_FILE"; then
    print_success "Component-level smoke tests defined"
else
    print_failure "Missing component-level smoke tests"
fi

# Check URL retrieval logic
if grep -q "cp_url" "$WORKFLOW_FILE" && \
   grep -q "pp_url" "$WORKFLOW_FILE" && \
   grep -q "plant_url" "$WORKFLOW_FILE"; then
    print_success "URL retrieval uses new output names"
else
    print_failure "URL retrieval still uses old output names"
fi

#############################################################################
# Test 8: Terraform Plan Simulation (CP-only)
#############################################################################

print_header "Test 8: Terraform Plan Simulation (CP-only)"

cd "$WORKSPACE_ROOT/cloud/terraform"

print_info "Running terraform plan for CP-only deployment..."

# Create temporary tfvars for testing
cat > /tmp/test-cp-only.tfvars <<EOF
project_id           = "waooaw-oauth"
region              = "asia-south1"
environment         = "demo"
enable_cp           = true
enable_pp           = false
enable_plant        = false
cp_frontend_image   = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-frontend:demo-test-1"
cp_backend_image    = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend:demo-test-1"
health_service_image = "asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-health:demo-test-1"
domains = {
  cp = {
    frontend = "cp.demo.waooaw.com"
    backend  = "cp.demo.waooaw.com"
  }
  pp = {
    frontend = "pp.demo.waooaw.com"
    backend  = "pp.demo.waooaw.com"
  }
  plant = {
    backend = "plant.demo.waooaw.com"
  }
}
EOF

# Skip actual terraform plan if no GCP credentials (expected in local testing)
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ] || gcloud auth application-default print-access-token &>/dev/null; then
    if terraform plan -var-file=/tmp/test-cp-only.tfvars -out=/tmp/test-plan.tfplan > /tmp/tf-plan.log 2>&1; then
        print_success "Terraform plan succeeded for CP-only configuration"
        
        # Check plan shows resources will be created
        if grep -q "Plan:" /tmp/tf-plan.log; then
            plan_summary=$(grep "Plan:" /tmp/tf-plan.log | tail -1)
            print_info "Plan summary: $plan_summary"
        fi
    else
        print_failure "Terraform plan failed (check /tmp/tf-plan.log)"
        echo ""
        echo "Last 30 lines of plan output:"
        tail -30 /tmp/tf-plan.log
    fi
else
    print_warning "GCP credentials not configured - skipping terraform plan execution"
    print_info "To enable: run 'gcloud auth application-default login'"
fi

# Cleanup
rm -f /tmp/test-cp-only.tfvars /tmp/test-plan.tfplan

#############################################################################
# Test 9: Documentation Validation
#############################################################################

print_header "Test 9: Documentation Validation"

cd "$WORKSPACE_ROOT"

# Check for key documentation files
if [ -f "infrastructure/CI_Pipeline/UNIFIED_ARCHITECTURE.md" ]; then
    print_success "UNIFIED_ARCHITECTURE.md exists"
else
    print_failure "UNIFIED_ARCHITECTURE.md not found"
fi

if [ -f "cloud/terraform/PIPELINE_SIMULATION_RESULTS.md" ]; then
    print_success "PIPELINE_SIMULATION_RESULTS.md exists"
else
    print_failure "PIPELINE_SIMULATION_RESULTS.md not found"
fi

if [ -f "cloud/terraform/pipeline-simulation.sh" ]; then
    print_success "pipeline-simulation.sh exists"
    
    if [ -x "cloud/terraform/pipeline-simulation.sh" ]; then
        print_success "pipeline-simulation.sh is executable"
    else
        print_warning "pipeline-simulation.sh is not executable (run: chmod +x)"
    fi
else
    print_failure "pipeline-simulation.sh not found"
fi

#############################################################################
# Test 10: Git Status Check
#############################################################################

print_header "Test 10: Git Status Check"

# Check current branch
current_branch=$(git branch --show-current)
print_info "Current branch: $current_branch"

# Check for uncommitted changes
if git diff --quiet && git diff --cached --quiet; then
    print_success "No uncommitted changes"
else
    print_warning "Uncommitted changes detected"
    echo ""
    git status --short
fi

# Check recent commits
print_info "Recent commits:"
git log --oneline -n 5 | while read line; do
    echo "  $line"
done

#############################################################################
# Summary Report
#############################################################################

print_header "📊 Test Summary"

echo ""
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}======================================================================${NC}"
    echo -e "${GREEN}🎉 ALL CRITICAL TESTS PASSED!${NC}"
    echo -e "${GREEN}======================================================================${NC}"
    echo ""
    echo -e "${CYAN}✨ Pipeline is ready for deployment!${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. Review warnings (if any) - they may not block deployment"
    echo "2. Deploy CP-only to demo:"
    echo "   gh workflow run .github/workflows/cp-pipeline.yml \\"
    echo "     --ref main \\"
    echo "     -f enable_cp=true \\"
    echo "     -f enable_pp=false \\"
    echo "     -f enable_plant=false \\"
    echo "     -f environment=demo \\"
    echo "     -f deploy_to_gcp=true \\"
    echo "     -f terraform_action=apply"
    echo ""
    exit 0
else
    echo -e "${RED}======================================================================${NC}"
    echo -e "${RED}❌ TESTS FAILED - PIPELINE NOT READY${NC}"
    echo -e "${RED}======================================================================${NC}"
    echo ""
    echo "Please fix the failures above before deploying."
    echo ""
    exit 1
fi
