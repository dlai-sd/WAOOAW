#!/bin/bash

#############################################################################
# WAOOAW Local Pipeline Test Script
# Validates the new stack-based Terraform layout + unified GitHub workflows
# WITHOUT deploying to GCP.
#############################################################################

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

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

print_success() { echo -e "${GREEN}✅ $1${NC}"; ((TESTS_PASSED++)) || true; }
print_failure() { echo -e "${RED}❌ FAIL: $1${NC}"; ((TESTS_FAILED++)) || true; }
print_warning() { echo -e "${YELLOW}⚠️  WARNING: $1${NC}"; ((WARNINGS++)) || true; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$WORKSPACE_ROOT"

print_header "🧪 WAOOAW Local Pipeline Test - Stacks + Unified Workflow"

#############################################################################
# Test 1: Component Path Validation
#############################################################################

print_header "Test 1: Component Dockerfile Detection (matches deploy workflow)"

if [ -f "src/CP/BackEnd/Dockerfile" ] && [ -f "src/CP/FrontEnd/Dockerfile" ]; then
    print_success "CP Dockerfiles present"
else
    print_warning "CP Dockerfiles missing (CP will not be deployable)"
fi

if [ -f "src/PP/BackEnd/Dockerfile" ] && [ -f "src/PP/FrontEnd/Dockerfile" ]; then
    print_success "PP Dockerfiles present"
else
    print_warning "PP Dockerfiles missing (PP will not be deployable)"
fi

if [ -f "src/Plant/BackEnd/Dockerfile" ]; then
    print_success "Plant Dockerfile present"
else
    print_warning "Plant Dockerfile missing (Plant will not be deployable)"
fi

#############################################################################
# Test 2: Terraform Configuration Validation
#############################################################################

print_header "Test 2: Terraform Stacks Validation (no backend, no credentials)"

if command -v terraform &> /dev/null; then
    print_success "Terraform CLI installed"
else
    print_failure "Terraform CLI not found"
fi

print_info "Running terraform fmt check (stacks + modules)..."
if terraform fmt -check -recursive cloud/terraform/stacks cloud/terraform/modules > /dev/null 2>&1; then
    print_success "Terraform files are properly formatted"
else
    print_warning "Terraform files need formatting (run: terraform fmt -recursive cloud/terraform/stacks cloud/terraform/modules)"
fi

STACKS=(cp pp plant foundation)
for s in "${STACKS[@]}"; do
    dir="cloud/terraform/stacks/${s}"
    if [ -d "${dir}" ]; then
        print_info "Validating stack: ${s}"
        if (cd "${dir}" && terraform init -backend=false -input=false > /tmp/tf-init-${s}.log 2>&1 && terraform validate > /tmp/tf-validate-${s}.log 2>&1); then
            print_success "Stack '${s}' is valid"
        else
            print_failure "Stack '${s}' validation failed"
            tail -80 "/tmp/tf-init-${s}.log" || true
            tail -80 "/tmp/tf-validate-${s}.log" || true
        fi
    else
        print_failure "Missing stack directory: ${dir}"
    fi
done

#############################################################################
# Test 2.5: GCP Naming Convention Check
#############################################################################

print_header "Test 3: Workflow Files (Unified)"

if [ -f ".github/workflows/waooaw-deploy.yml" ]; then
    print_success "Unified deploy workflow exists (waooaw-deploy.yml)"
else
    print_failure "Missing .github/workflows/waooaw-deploy.yml"
fi

if [ -f ".github/workflows/waooaw-foundation-deploy.yml" ]; then
    print_success "Foundation workflow exists (waooaw-foundation-deploy.yml)"
else
    print_failure "Missing .github/workflows/waooaw-foundation-deploy.yml"
fi

if ls .github/workflows/wahooaw-*.yml > /dev/null 2>&1; then
    print_failure "Found legacy incorrectly named wahooaw-*.yml workflows"
else
    print_success "No legacy wahooaw-*.yml workflows present"
fi

#############################################################################
# Test 3: Variable Definitions Check
#############################################################################

print_header "Test 4: Documentation Presence"

if [ -f "infrastructure/CI_Pipeline/UNIFIED_ARCHITECTURE.md" ]; then
    print_success "UNIFIED_ARCHITECTURE.md exists"
else
    print_failure "Missing UNIFIED_ARCHITECTURE.md"
fi

#############################################################################
# Test 4: Module Validation
#############################################################################

print_header "Test 5: Git Status Check"

branch="$(git rev-parse --abbrev-ref HEAD)"
print_info "Current branch: ${branch}"

if git status --porcelain | grep -q .; then
    print_warning "Uncommitted changes detected"
else
    print_success "Working tree clean"
fi

print_header "📊 Test Summary"

echo ""
echo -e "${GREEN}✅ Tests Passed: ${TESTS_PASSED}${NC}"
echo -e "${RED}❌ Tests Failed: ${TESTS_FAILED}${NC}"
echo -e "${YELLOW}⚠️  Warnings: ${WARNINGS}${NC}"

if [ "${TESTS_FAILED}" -eq 0 ]; then
    print_header "✅ LOCAL VALIDATION PASSED"
    exit 0
else
    print_header "❌ LOCAL VALIDATION FAILED"
    exit 1
fi
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
