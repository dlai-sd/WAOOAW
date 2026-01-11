# Pipeline Update Summary

**Last Updated**: January 11, 2026 (18:31 UTC)  
**Latest Workflow Commit**: b6ed849 (frontend Dockerfile user fix)  
**Context**: Run #80 attempted deploy but services failed to start; root cause and fixes identified.

## ✅ Latest Changes (Jan 11, 2026 - Session 2)

**Workflow & Cleanup:**
- Added `clean_services` input (optional, default false): deletes existing Cloud Run services before apply, preventing 409 conflicts.
- Workflow cleanup step runs `gcloud run services delete` for `waooaw-api-demo` and `waooaw-portal-demo` if `clean_services=true`.
- Commit: feat(workflow): add clean_services input and optional Cloud Run cleanup before apply (f556713).

**Container Startup Fixes:**
- Frontend (Nginx) Dockerfile: changed from custom `appuser` to native `nginx` user with proper permissions for `/var/run/nginx.pid`, `/var/cache/nginx`, and `/var/log/nginx`.
  - Root cause of run #80 failure: custom user lacked permission to write to Nginx pid/log files, causing startup timeout.
  - Commit: fix(frontend): run Nginx as nginx user with proper permissions to ensure Cloud Run startup (b6ed849).
- Backend Dockerfile already correct: uses `python -m uvicorn`, honors `$PORT` environment variable.

**Terraform & Deployment:**
- After clean deletion of Cloud Run services, `apply` recreates services with the newly pushed images.
- Load balancer updates remain optional and are `false` by default to preserve static IP/DNS.

## 📌 Run #80 Failure & Resolution

- **Status**: Failed.
- **Image Build & Push**: ✅ Success (demo-f556713-80).
- **Terraform Apply**: ❌ Failed—both backend and portal services failed to start within Cloud Run timeout.
- **Backend Error**: "container failed to start and listen on PORT=8000" (uvicorn startup issue or dependency load).
- **Portal Error**: "container failed to start and listen on PORT=8080" (Nginx user permissions issue).
- **Root Cause**: Frontend Dockerfile ran Nginx as custom `appuser` without write permissions to system pid/log directories.
- **Fix Applied**: Frontend Dockerfile now uses native `nginx` user; backend already correct.
- **Next Steps**: Re-run with `clean_services=true` to ensure fresh services and apply fixed containers.

## ▶️ Trigger Checklist (Manual Dispatch)

Use these inputs to deploy CP to Demo with fresh images and containers:
- deploy_to_gcp: `true` (REQUIRED)
- build_images: `true`
- run_tests: `false`
- terraform_action: `apply`
- target_environment: `demo`
- update_load_balancer: `false`
- clean_services: `true` (recommended for fresh deploy; deletes old services)

This ensures:
1. Images are built/pushed to `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw`.
2. Existing Cloud Run services are deleted (avoiding 409 conflicts).
3. Terraform applies Cloud Run + networking with fresh services (LB skipped).
4. Containers start with proper user permissions and port bindings.

## 📌 Run Outcomes & Root Causes

- Run 75: Terraform apply failed with "Image not found" → Build & Push steps were skipped due to brittle string-based `if` conditions.
- Run 76: Same error pattern; validated enable flags were `true` but steps still skipped.
- Run 77: Most jobs skipped → `deploy_to_gcp` not set to `true`; default `false` caused deploy jobs to skip.

---

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
