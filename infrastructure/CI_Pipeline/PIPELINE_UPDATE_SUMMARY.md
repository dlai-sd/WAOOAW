# Pipeline Update Summary

## ✅ Changes Completed

### 1. Added Component Selection Input
- **New workflow input**: `target_components` (choice)
  - Options: `cp`, `pp`, `plant`, `cp,pp`, `cp,plant`, `pp,plant`, `all`
  - Default: `cp` (Customer Portal)
  - Used to control which components are built and tested

### 2. Added Environment Selection Input  
- **New workflow input**: `target_environment` (choice)
  - Options: `demo`, `uat`, `prod`
  - Default: `demo`
  - Used to select which GCP environment to deploy to

### 3. Created `validate-components` Job
This is the **gatekeeper job** that runs first:

**What it does:**
- Parses `target_components` input
- Checks if each component path exists:
  - `src/CP/BackEnd` - ✅ Exists (CP is required)
  - `src/PP/BackEnd` - ⏳ Not yet created (warns, skips if selected)
  - `src/Plant` - ⏳ Not yet created (warns, skips if selected)
- Sets Terraform enable flags based on what will be built:
  - `enable_backend_api`: true if CP selected
  - `enable_customer_portal`: true if CP selected
  - `enable_platform_portal`: true if PP selected
- Outputs build flags to downstream jobs

**Why it matters:**
- Prevents trying to build paths that don't exist
- Prevents Terraform from deploying services for images that weren't built
- Solves the original problem: "Image not found" errors

### 4. Updated Test Jobs to Be Conditional
- `backend-test`: Only runs if `validate-components.build_cp == true`
- `frontend-test`: Only runs if `validate-components.build_cp == true`
- Other jobs respect conditional flags similarly

### 5. Updated `terraform-deploy` Job
Now dynamically updates tfvars with component enable flags:

```bash
# Before (hardcoded, always deployed all 3 services):
terraform plan -var-file=environments/demo.tfvars -out=demo.tfplan

# After (conditional based on what was built):
cat >> environments/demo.tfvars <<EOF
enable_backend_api = true          # From validate-components.outputs
enable_customer_portal = true      # From validate-components.outputs
enable_platform_portal = false     # From validate-components.outputs
EOF
terraform plan -var-file=environments/demo.tfvars -out=demo.tfplan
```

### 6. Created Pipeline Documentation
- **File**: `infrastructure/CI_Pipeline/PIPELINE_COMPONENT_SELECTION.md`
- **Contains**:
  - Component selection options and expected paths
  - Pipeline flow diagram
  - Before/after comparison
  - Terraform integration details
  - Example workflows for different scenarios
  - Troubleshooting guide

## 🔗 How It All Works Together

```
User Triggers Pipeline
  ↓
validate-components (checks paths, sets flags)
  ↓
  ├─→ build_cp=true/false
  ├─→ build_pp=true/false
  ├─→ build_plant=true/false
  ├─→ enable_backend_api=true/false
  ├─→ enable_customer_portal=true/false
  └─→ enable_platform_portal=true/false
      ↓
      [Conditional test jobs based on build_* flags]
      ↓
      [Docker build & push]
      ↓
      [Terraform Deploy] uses enable_* flags
      ↓
      Only deploys services that were built ✅
```

## 🎯 Solving the Original Problem

**Before:**
- Pipeline: Hardcoded to build CP only
- Terraform: Always tried to deploy backend_api + customer_portal + platform_portal
- Result: ❌ `platform_portal` service deployed but image not built → "Image not found" error

**After:**
- Pipeline: Dynamically builds selected components
- Pipeline: Passes `enable_*` flags to Terraform
- Terraform: Only deploys services matching `enable_* = true`
- Result: ✅ No mismatch, services only deploy if images exist

## 📋 Paths That Need to Be Created (When Development Starts)

Currently, only CP exists:
- ✅ `src/CP/BackEnd/` (Python FastAPI + Dockerfile)
- ✅ `src/CP/FrontEnd/` (React + Dockerfile)

To enable PP and Plant builds in the future, create:
- ⏳ `src/PP/BackEnd/` (with Dockerfile)
- ⏳ `src/PP/FrontEnd/` (with Dockerfile)
- ⏳ `src/Plant/` (with Dockerfile)

Once these exist, the pipeline will automatically:
1. Detect them in `validate-components`
2. Include them in build matrix
3. Set appropriate Terraform flags
4. Deploy them with `terraform apply`

## 🧪 Testing the Pipeline

### Test 1: CP Only (Default)
```
target_components: cp
build_images: true
deploy_to_gcp: false  # Skip deploy, just test build
run_tests: true
```
Expected: ✅ Tests pass, images built, terraform plan shows 2 services

### Test 2: CP to UAT
```
target_components: cp
build_images: true
deploy_to_gcp: true
target_environment: uat
terraform_action: plan  # Plan only, don't apply
run_tests: true
```
Expected: ✅ Terraform plan shows enable flags in tfvars, only 2 services in plan

### Test 3: PP Selection (Will Warn)
```
target_components: pp
build_images: true
deploy_to_gcp: false
```
Expected: ⚠️ Workflow shows warning "PP selected but src/PP/BackEnd not found - skipping PP build"

## 📊 Files Modified

| File | Changes |
|------|---------|
| `.github/workflows/cp-pipeline.yml` | +200 lines: component selection, validate-components job, conditional test jobs, dynamic tfvars update |
| `cloud/terraform/` | 12 files: Added enable_* variables, conditional module counts, dynamic resource creation |
| `infrastructure/CI_Pipeline/PIPELINE_COMPONENT_SELECTION.md` | New: Component selection guide |

## 🚀 Next Steps

The pipeline is now **component-aware** but:
1. Only CP actually exists in code
2. PP paths need to be created: `src/PP/BackEnd/`, `src/PP/FrontEnd/`
3. Plant paths need to be created: `src/Plant/`

When those are created, immediately:
- ✅ Pipeline will auto-detect them
- ✅ Jobs will conditionally include them
- ✅ Terraform will conditionally deploy them
- ✅ No further pipeline changes needed
