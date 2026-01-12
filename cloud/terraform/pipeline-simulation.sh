#!/bin/bash
# Pipeline Simulation Script for Architecture v2.0
# Simulates GitHub Actions pipeline execution to identify issues

# Don't exit on error - we want to collect all issues
set +e

echo "======================================================================"
echo "🔍 WAOOAW Pipeline Simulation - Architecture v2.0"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ISSUES_FOUND=0
WARNINGS_FOUND=0

# Function to report issue
report_issue() {
    echo -e "${RED}❌ ISSUE: $1${NC}"
    ((ISSUES_FOUND++))
}

# Function to report warning
report_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNINGS_FOUND++))
}

# Function to report success
report_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to report info
report_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "======================================================================"
echo "Phase 1: Component Path Validation"
echo "======================================================================"
echo ""

# Check CP component
report_info "Checking CP component paths..."
if [ -d "/workspaces/WAOOAW/src/CP" ]; then
    report_success "CP source directory exists"
    
    # Check for backend
    if [ -d "/workspaces/WAOOAW/src/CP/BackEnd" ] || [ -d "/workspaces/WAOOAW/src/CP/backend" ]; then
        report_success "CP backend directory exists"
    else
        report_warning "CP backend directory not found"
    fi
    
    # Check for frontend
    if [ -d "/workspaces/WAOOAW/src/CP/FrontEnd" ] || [ -d "/workspaces/WAOOAW/src/CP/frontend" ] || [ -d "/workspaces/WAOOAW/src/CP/app" ]; then
        report_success "CP frontend directory exists"
    else
        report_warning "CP frontend directory not found"
    fi
else
    report_issue "CP source directory not found at src/CP"
fi

# Check PP component
report_info "Checking PP component paths..."
if [ -d "/workspaces/WAOOAW/src/PP" ]; then
    report_success "PP source directory exists"
    
    # Check for backend
    if [ -d "/workspaces/WAOOAW/src/PP/BackEnd" ] || [ -d "/workspaces/WAOOAW/src/PP/backend" ]; then
        report_success "PP backend directory exists"
    else
        report_warning "PP backend directory not found"
    fi
    
    # Check for frontend
    if [ -d "/workspaces/WAOOAW/src/PP/FrontEnd" ] || [ -d "/workspaces/WAOOAW/src/PP/frontend" ] || [ -d "/workspaces/WAOOAW/src/PP/app" ]; then
        report_success "PP frontend directory exists"
    else
        report_warning "PP frontend directory not found"
    fi
else
    report_warning "PP source directory not found at src/PP"
fi

# Check Plant component
report_info "Checking Plant component paths..."
if [ -d "/workspaces/WAOOAW/src/Plant" ]; then
    report_success "Plant source directory exists"
    
    # Check for backend
    if [ -d "/workspaces/WAOOAW/src/Plant/BackEnd" ] || [ -d "/workspaces/WAOOAW/src/Plant/backend" ]; then
        report_success "Plant backend directory exists"
    else
        report_warning "Plant backend directory not found"
    fi
else
    report_warning "Plant source directory not found at src/Plant"
fi

echo ""
echo "======================================================================"
echo "Phase 2: Dockerfile Validation"
echo "======================================================================"
echo ""

# Check for Dockerfiles
report_info "Checking for Dockerfiles..."

# CP Dockerfiles
if [ -f "/workspaces/WAOOAW/infrastructure/docker/Dockerfile.cp-frontend" ]; then
    report_success "CP frontend Dockerfile exists"
else
    report_warning "CP frontend Dockerfile not found (infrastructure/docker/Dockerfile.cp-frontend)"
fi

if [ -f "/workspaces/WAOOAW/infrastructure/docker/Dockerfile.cp-backend" ]; then
    report_success "CP backend Dockerfile exists"
else
    report_warning "CP backend Dockerfile not found (infrastructure/docker/Dockerfile.cp-backend)"
fi

# PP Dockerfiles
if [ -f "/workspaces/WAOOAW/infrastructure/docker/Dockerfile.pp-frontend" ]; then
    report_success "PP frontend Dockerfile exists"
else
    report_warning "PP frontend Dockerfile not found (infrastructure/docker/Dockerfile.pp-frontend)"
fi

if [ -f "/workspaces/WAOOAW/infrastructure/docker/Dockerfile.pp-backend" ]; then
    report_success "PP backend Dockerfile exists"
else
    report_warning "PP backend Dockerfile not found (infrastructure/docker/Dockerfile.pp-backend)"
fi

# Plant Dockerfile
if [ -f "/workspaces/WAOOAW/infrastructure/docker/Dockerfile.plant-backend" ]; then
    report_success "Plant backend Dockerfile exists"
else
    report_warning "Plant backend Dockerfile not found (infrastructure/docker/Dockerfile.plant-backend)"
fi

# Health service Dockerfile
if [ -f "/workspaces/WAOOAW/infrastructure/docker/Dockerfile.health" ]; then
    report_success "Health service Dockerfile exists"
else
    report_warning "Health service Dockerfile not found (infrastructure/docker/Dockerfile.health)"
fi

echo ""
echo "======================================================================"
echo "Phase 3: Terraform Configuration Validation"
echo "======================================================================"
echo ""

cd /workspaces/WAOOAW/cloud/terraform

report_info "Running terraform fmt check..."
if terraform fmt -check -recursive > /dev/null 2>&1; then
    report_success "Terraform files are properly formatted"
else
    report_warning "Some Terraform files need formatting (run: terraform fmt -recursive)"
fi

report_info "Running terraform validate..."
if terraform validate > /dev/null 2>&1; then
    report_success "Terraform configuration is valid"
else
    report_issue "Terraform validation failed"
    terraform validate
fi

echo ""
echo "======================================================================"
echo "Phase 4: GitHub Actions Workflow Validation"
echo "======================================================================"
echo ""

WORKFLOW_FILE="/workspaces/WAOOAW/.github/workflows/cp-pipeline.yml"

report_info "Checking workflow file..."
if [ -f "$WORKFLOW_FILE" ]; then
    report_success "Workflow file exists"
    
    # Check for old variable names
    report_info "Checking for deprecated variables..."
    
    if grep -q "enable_backend_api" "$WORKFLOW_FILE"; then
        report_issue "Workflow still uses deprecated 'enable_backend_api' (should use 'enable_cp')"
    fi
    
    if grep -q "enable_customer_portal" "$WORKFLOW_FILE"; then
        report_issue "Workflow still uses deprecated 'enable_customer_portal' (should use 'enable_cp')"
    fi
    
    if grep -q "enable_platform_portal" "$WORKFLOW_FILE"; then
        report_issue "Workflow still uses deprecated 'enable_platform_portal' (should use 'enable_pp')"
    fi
    
    # Check for new variables
    if grep -q "enable_cp" "$WORKFLOW_FILE"; then
        report_success "Workflow uses new 'enable_cp' variable"
    else
        report_warning "Workflow doesn't reference 'enable_cp' variable"
    fi
    
    if grep -q "enable_pp" "$WORKFLOW_FILE"; then
        report_success "Workflow uses new 'enable_pp' variable"
    else
        report_warning "Workflow doesn't reference 'enable_pp' variable"
    fi
    
    if grep -q "enable_plant" "$WORKFLOW_FILE"; then
        report_success "Workflow uses new 'enable_plant' variable"
    else
        report_warning "Workflow doesn't reference 'enable_plant' variable"
    fi
    
else
    report_issue "Workflow file not found"
fi

echo ""
echo "======================================================================"
echo "Phase 4.5: GCP Naming Convention Check"
echo "======================================================================"
echo ""

report_info "Checking for GCP-incompatible naming patterns..."

# Check main.tf for underscores in module names
if grep -E 'module "[a-zA-Z0-9]*_[a-zA-Z0-9]*"' /workspaces/WAOOAW/cloud/terraform/main.tf > /dev/null; then
    report_warning "Module names contain underscores (may cause issues in NEG naming)"
    report_info "Note: Underscores in module names are converted to hyphens in NEG resources"
else
    report_success "No underscores in module names"
fi

# Check for uppercase in resource names (should be lowercase)
if grep -E '(name.*=.*"[^"]*[A-Z][^"]*")' /workspaces/WAOOAW/cloud/terraform/main.tf > /dev/null; then
    report_warning "Found uppercase letters in resource names (GCP prefers lowercase)"
else
    report_success "All resource names use lowercase"
fi

# Verify NEG naming in networking module uses replace function
if grep -q 'replace(each.key, "_", "-")' /workspaces/WAOOAW/cloud/terraform/modules/networking/main.tf; then
    report_success "NEG module correctly converts underscores to hyphens"
else
    report_issue "NEG module missing underscore-to-hyphen conversion"
fi

echo ""
echo "======================================================================"
echo "Phase 5: Environment Variables Check"
echo "======================================================================"
echo ""

# Check demo.tfvars
report_info "Checking demo.tfvars..."
TFVARS_FILE="/workspaces/WAOOAW/cloud/terraform/environments/demo.tfvars"

if [ -f "$TFVARS_FILE" ]; then
    report_success "demo.tfvars exists"
    
    # Check for new variables
    if grep -q "enable_cp" "$TFVARS_FILE"; then
        report_success "demo.tfvars uses enable_cp"
    else
        report_warning "demo.tfvars missing enable_cp"
    fi
    
    if grep -q "enable_pp" "$TFVARS_FILE"; then
        report_success "demo.tfvars uses enable_pp"
    else
        report_warning "demo.tfvars missing enable_pp"
    fi
    
    if grep -q "enable_plant" "$TFVARS_FILE"; then
        report_success "demo.tfvars uses enable_plant"
    else
        report_warning "demo.tfvars missing enable_plant"
    fi
    
    # Check for image variables
    if grep -q "cp_frontend_image" "$TFVARS_FILE"; then
        report_success "demo.tfvars has cp_frontend_image"
    else
        report_warning "demo.tfvars missing cp_frontend_image"
    fi
    
    if grep -q "health_service_image" "$TFVARS_FILE"; then
        report_success "demo.tfvars has health_service_image"
    else
        report_warning "demo.tfvars missing health_service_image"
    fi
else
    report_issue "demo.tfvars not found"
fi

echo ""
echo "======================================================================"
echo "Phase 6: Module Validation"
echo "======================================================================"
echo ""

report_info "Checking Terraform modules..."

# Check cloud-run module
if [ -f "/workspaces/WAOOAW/cloud/terraform/modules/cloud-run/main.tf" ]; then
    report_success "cloud-run module exists"
    
    # Check for service_account output
    if grep -q "service_account" "/workspaces/WAOOAW/cloud/terraform/modules/cloud-run/outputs.tf"; then
        report_success "cloud-run module has service_account output"
    else
        report_warning "cloud-run module missing service_account output"
    fi
else
    report_issue "cloud-run module not found"
fi

# Check load-balancer module
if [ -f "/workspaces/WAOOAW/cloud/terraform/modules/load-balancer/main.tf" ]; then
    report_success "load-balancer module exists"
    
    # Check for new enable flags
    if grep -q "enable_cp" "/workspaces/WAOOAW/cloud/terraform/modules/load-balancer/variables.tf"; then
        report_success "load-balancer module uses enable_cp"
    else
        report_warning "load-balancer module missing enable_cp"
    fi
else
    report_issue "load-balancer module not found"
fi

# Check networking module
if [ -f "/workspaces/WAOOAW/cloud/terraform/modules/networking/main.tf" ]; then
    report_success "networking module exists"
else
    report_issue "networking module not found"
fi

echo ""
echo "======================================================================"
echo "Phase 7: Docker Build Context Check"
echo "======================================================================"
echo ""

report_info "Checking Docker build contexts..."

# Check if we can access source directories for Docker builds
if [ -d "/workspaces/WAOOAW/src" ]; then
    report_success "Source directory accessible for Docker builds"
else
    report_issue "Source directory not found - Docker builds will fail"
fi

if [ -d "/workspaces/WAOOAW/infrastructure/docker" ]; then
    report_success "Docker infrastructure directory exists"
else
    report_warning "Docker infrastructure directory not found"
fi

echo ""
echo "======================================================================"
echo "Phase 8: IAM and Service Account Check"
echo "======================================================================"
echo ""

report_info "Checking IAM configurations..."

# Check main.tf for IAM bindings
if grep -q "google_cloud_run_service_iam_member" "/workspaces/WAOOAW/cloud/terraform/main.tf"; then
    report_success "IAM bindings defined in main.tf"
    
    # Check for CP to Plant binding
    if grep -q "cp_to_plant" "/workspaces/WAOOAW/cloud/terraform/main.tf"; then
        report_success "CP to Plant IAM binding exists"
    else
        report_warning "CP to Plant IAM binding not found"
    fi
    
    # Check for PP to Plant binding
    if grep -q "pp_to_plant" "/workspaces/WAOOAW/cloud/terraform/main.tf"; then
        report_success "PP to Plant IAM binding exists"
    else
        report_warning "PP to Plant IAM binding not found"
    fi
else
    report_warning "No IAM bindings found in main.tf"
fi

echo ""
echo "======================================================================"
echo "Phase 9: Health Service Check"
echo "======================================================================"
echo ""

report_info "Checking health service configurations..."

# Check if health modules are defined
if grep -q "cp_health" "/workspaces/WAOOAW/cloud/terraform/main.tf"; then
    report_success "CP health service defined"
else
    report_warning "CP health service not defined in main.tf"
fi

if grep -q "pp_health" "/workspaces/WAOOAW/cloud/terraform/main.tf"; then
    report_success "PP health service defined"
else
    report_warning "PP health service not defined in main.tf"
fi

if grep -q "plant_health" "/workspaces/WAOOAW/cloud/terraform/main.tf"; then
    report_success "Plant health service defined"
else
    report_warning "Plant health service not defined in main.tf"
fi

echo ""
echo "======================================================================"
echo "Phase 10: Pipeline Job Structure Analysis"
echo "======================================================================"
echo ""

report_info "Analyzing pipeline job structure..."

# Check for validate-components job
if grep -q "validate-components:" "$WORKFLOW_FILE"; then
    report_success "validate-components job exists"
else
    report_warning "validate-components job not found in workflow"
fi

# Check for build jobs
if grep -q "build-cp:" "$WORKFLOW_FILE" || grep -q "build-cp-" "$WORKFLOW_FILE"; then
    report_success "CP build job exists"
else
    report_warning "CP build job not found in workflow"
fi

if grep -q "build-pp:" "$WORKFLOW_FILE" || grep -q "build-pp-" "$WORKFLOW_FILE"; then
    report_success "PP build job exists"
else
    report_warning "PP build job not found - will need to add for PP deployment"
fi

if grep -q "build-plant:" "$WORKFLOW_FILE" || grep -q "build-plant-" "$WORKFLOW_FILE"; then
    report_success "Plant build job exists"
else
    report_warning "Plant build job not found - will need to add for Plant deployment"
fi

echo ""
echo "======================================================================"
echo "Summary Report"
echo "======================================================================"
echo ""

if [ $ISSUES_FOUND -eq 0 ]; then
    report_success "No critical issues found!"
else
    report_issue "Found $ISSUES_FOUND critical issue(s) that must be fixed"
fi

if [ $WARNINGS_FOUND -eq 0 ]; then
    report_success "No warnings!"
else
    report_warning "Found $WARNINGS_FOUND warning(s) to review"
fi

echo ""
echo "======================================================================"
echo "Recommendations"
echo "======================================================================"
echo ""

if [ $ISSUES_FOUND -gt 0 ] || [ $WARNINGS_FOUND -gt 0 ]; then
    echo "📋 Action Items:"
    echo ""
    
    if grep -q "enable_backend_api" "$WORKFLOW_FILE" 2>/dev/null; then
        echo "1. Update .github/workflows/cp-pipeline.yml:"
        echo "   - Replace enable_backend_api/enable_customer_portal/enable_platform_portal"
        echo "   - Add enable_cp, enable_pp, enable_plant workflow inputs"
        echo "   - Update Terraform step to pass new variables"
        echo ""
    fi
    
    if [ ! -d "/workspaces/WAOOAW/src/PP" ]; then
        echo "2. Create PP component structure:"
        echo "   - Create src/PP/frontend and src/PP/backend directories"
        echo "   - Add placeholder files or actual PP implementation"
        echo ""
    fi
    
    if [ ! -d "/workspaces/WAOOAW/src/Plant" ]; then
        echo "3. Create Plant component structure:"
        echo "   - Create src/Plant/backend directory"
        echo "   - Add placeholder files or actual Plant implementation"
        echo ""
    fi
    
    if [ ! -f "/workspaces/WAOOAW/infrastructure/docker/Dockerfile.health" ]; then
        echo "4. Create health service Dockerfile:"
        echo "   - Create infrastructure/docker/Dockerfile.health"
        echo "   - Implement simple health check service"
        echo ""
    fi
    
    echo "5. Add build jobs to workflow for PP and Plant components"
    echo ""
    echo "6. Test pipeline with CP-only deployment first (enable_cp=true)"
    echo ""
fi

echo "======================================================================"
echo "Simulation Complete!"
echo "======================================================================"
echo ""

# Exit with error if critical issues found
if [ $ISSUES_FOUND -gt 0 ]; then
    exit 1
else
    exit 0
fi
