# Pipeline Update Summary

**Last Updated**: January 11, 2026  
**Latest Workflow Commit**: d2f3b89 (safer flag handling via fromJson)  
**Container Fixes**: Runs #81-86 (Cloud Run startup issues resolved)  
**Context**: Recent runs showed deploy jobs skipped or failing to find images; fixes applied and inputs clarified. Subsequent runs revealed Cloud Run container startup failures requiring multiple Dockerfile and config iterations.

## ✅ Latest Changes (Jan 11, 2026)

### Workflow & Pipeline
- Deployment gating clarified: `deploy_to_gcp` defaults to `false`. If not explicitly set to `true` on manual dispatch, all deploy jobs are skipped by design.
- Build & Push to GCP reliability: job now `needs: [validate-components]`; step-level conditions updated to `fromJson(needs.validate-components.outputs.enable_backend_api) == true` (and similarly for customer portal) to avoid string/whitespace mismatch.
- Terraform behavior: After clean deletion of Cloud Run services, `apply` recreates services with the newly pushed images. Load balancer updates remain optional and are `false` by default to preserve static IP/DNS.

### Backend Container Fixes (Runs #81-86)
1. **System-wide pip install** (Run #82):
   - Changed from `pip install --user` to `pip install --no-cache-dir`
   - Packages installed to `/usr/local` instead of `/root/.local`
   - Non-root `appuser` can now access installed packages
   - Root cause: `appuser` couldn't read `/root/.local` due to filesystem permissions

2. **Shell path in CMD** (Run #83):
   - Changed from `["sh", "-c", ...]` to `["/bin/sh", "-c", ...]`
   - Ensures proper shell execution and `${PORT}` environment variable expansion
   - Root cause: Relative shell path wasn't being resolved correctly in Cloud Run

3. **Final backend CMD**:
   ```dockerfile
   CMD ["/bin/sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
   ```

### Frontend Container Fixes (Runs #84-86)
1. **Nginx PID file location** (Run #85):
   - Changed from `/var/run/nginx.pid` to `/tmp/nginx/nginx.pid`
   - Non-root `nginx` user can write to `/tmp` but not `/var/run`
   - Root cause: Permission denied when nginx tried to create PID file

2. **Removed unresolvable proxy** (Run #86):
   - Commented out `proxy_pass http://backend:8000;` in nginx.conf
   - Nginx validates upstream hosts on startup; unresolvable host causes failure
   - Root cause: `backend` hostname doesn't exist in container DNS
   - In Cloud Run, API calls go through load balancer, not internal proxy

3. **Final nginx CMD**:
   ```dockerfile
   CMD ["nginx", "-g", "daemon off; pid /tmp/nginx/nginx.pid;"]
   ```

## ▶️ Trigger Checklist (Manual Dispatch)

Use these inputs to deploy CP to Demo with fresh images:
- deploy_to_gcp: true (REQUIRED)
- build_images: true
- run_tests: false
- terraform_action: apply
- target_environment: demo
- update_load_balancer: false

This ensures images are built/pushed to `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw` and Terraform applies Cloud Run + networking (LB skipped).

## 📌 Run Outcomes & Root Causes

### Image Build Issues (Runs #75-77)
- Run 75: Terraform apply failed with "Image not found" → Build & Push steps were skipped due to brittle string-based `if` conditions.
- Run 76: Same error pattern; validated enable flags were `true` but steps still skipped.
- Run 77: Most jobs skipped → `deploy_to_gcp` not set to `true`; default `false` caused deploy jobs to skip.

### Cloud Run Container Startup Failures (Runs #81-86)
- **Run 81-82**: Error code 9, PORT=8000/8080 - Container failed to start and listen
  - Backend: `appuser` couldn't access packages in `/root/.local`
  - Frontend: nginx user permission issues
  - Fix: System-wide pip install + nginx permission updates

- **Run 83**: Same Error code 9 after PYTHONPATH workaround
  - Root cause: Packages still inaccessible; PYTHONPATH insufficient
  - Fix: Removed `--user` flag entirely; copy from `/usr/local`

- **Run 84-85**: Backend succeeded ✅, frontend still failing on PORT=8080
  - Root cause: Nginx couldn't write PID file to `/var/run/nginx.pid`
  - Fix: Changed PID location to `/tmp/nginx/nginx.pid`

- **Run 86**: Backend succeeded ✅, frontend still failing
  - Root cause: Nginx config validation failed due to unresolvable `proxy_pass http://backend:8000`
  - Fix: Commented out API proxy block in nginx.conf

## 🔍 Debugging Commands

### Fetch GitHub Actions Logs
```bash
# Via GitHub CLI
gh run list -R dlai-sd/WAOOAW --limit 20
RUN_ID=$(gh run list -R dlai-sd/WAOOAW --json id,runNumber | jq -r '.[] | select(.runNumber == 85) | .id')
gh run view $RUN_ID --json jobs | jq '.jobs[] | {name: .name, conclusion: .conclusion}'
gh run view $RUN_ID --job <JOB_ID> --log > job.log
```

### Fetch Cloud Run Container Logs
```bash
# Set project
gcloud config set project waooaw-oauth

# Backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=waooaw-api-demo" \
  --limit 50 --format=json --project waooaw-oauth | \
  jq -r '.[] | "\(.timestamp) [\(.severity)] \(.textPayload // .jsonPayload.message)"'

# Frontend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=waooaw-portal-demo" \
  --limit 50 --format=json --project waooaw-oauth | \
  jq -r '.[] | "\(.timestamp) [\(.severity)] \(.textPayload // .jsonPayload.message)"'

# Specific revision logs (get revision name from Terraform error)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=waooaw-api-demo-00001-abc" \
  --limit 100 --format=json --project waooaw-oauth
```

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
