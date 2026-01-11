# Pipeline Component Selection Guide

## Overview

The unified CI/CD pipeline now supports selective building and deployment of individual components: **CP** (Customer Portal), **PP** (Platform Portal), and **Plant** (Agent Core).

## New Workflow Input: `target_components`

When manually triggering the workflow, select which components to build and deploy:

### Options

| Value | Description | Status |
|-------|-------------|--------|
| `cp` (default) | Customer Portal only | ✅ Ready |
| `pp` | Platform Portal only | ⏳ Paths not yet created |
| `plant` | Agent Core only | ⏳ Paths not yet created |
| `cp,pp` | CP + PP | ⏳ PP pending |
| `cp,plant` | CP + Plant | ⏳ Plant pending |
| `pp,plant` | PP + Plant | ⏳ Both pending |
| `all` | All available components | ⏳ PP/Plant pending |

## New Workflow Input: `target_environment`

Select the GCP environment to deploy to when `deploy_to_gcp=true`:

- `demo` (default)
- `uat`
- `prod`

## Pipeline Flow

```
1. [validate-components]
   ├─ Parse target_components input
   ├─ Check if component paths exist (src/CP/*, src/PP/*, src/Plant/*)
   ├─ Skip non-existent components with warning
   ├─ Set Terraform enable_* flags based on what WILL be built
   └─ Output: build_cp, build_pp, build_plant, enable_backend_api, enable_customer_portal, enable_platform_portal

2. [backend-test] (if build_cp=true)
   ├─ Test & lint src/CP/BackEnd
   └─ Generate coverage reports

3. [frontend-test] (if build_cp=true)
   ├─ Test & lint src/CP/FrontEnd
   └─ Generate coverage reports

4. [backend-security] (if build_cp=true)
   ├─ Bandit, pip-audit, safety scans
   └─ Upload security reports

5. [frontend-security] (if build_cp=true)
   ├─ Trivy container scan
   └─ Upload reports

6. [build-images] (if build_images=true AND tests pass)
   ├─ Build Docker images for: cp-backend, cp
   └─ Push to GCP Artifact Registry

7. [build-and-push-gcp] (if build_images=true)
   ├─ Build additional GCP-specific images
   └─ Push to asia-south1-docker.pkg.dev

8. [terraform-deploy] (if deploy_to_gcp=true)
   ├─ Authenticate to GCP
   ├─ Initialize Terraform
   ├─ **NEW**: Update tfvars with component enable flags from validate-components
   ├─ Terraform plan/apply using target_environment
   ├─ Only deploy services where enable_* = true
   ├─ Smoke test deployed services
   └─ Output deployment URLs
```

## Key Changes

### Before
- ✅ Pipeline hardcoded to CP only
- ❌ No component selection
- ❌ Terraform always deplyed all 3 services (backend_api, customer_portal, platform_portal)
- ❌ Mismatch: Pipeline built images but Terraform tried to deploy services for images not built

### After
- ✅ Pipeline supports CP/PP/Plant component selection
- ✅ Validates component paths exist before building
- ✅ Gracefully skips non-existent components with warnings
- ✅ Sets Terraform enable_* flags based on what was actually built
- ✅ Terraform only deploys services matching built images
- ✅ No more "image not found" errors

## Terraform Integration

The pipeline now **dynamically updates tfvars** during deployment:

```bash
# Example: User selects target_components="cp"
enable_backend_api = true           # CP depends on backend
enable_customer_portal = true       # CP selected
enable_platform_portal = false      # PP not selected → not built → don't deploy

# Result: Terraform deploys ONLY backend_api + customer_portal
# platform_portal services are NOT created in Cloud Run
```

## Expected Paths (When Components Ready)

```
src/
├── CP/                     # ✅ Exists
│   ├── BackEnd/
│   │   └── Dockerfile
│   └── FrontEnd/
│       └── Dockerfile
├── PP/                     # ⏳ To be created
│   ├── BackEnd/
│   │   └── Dockerfile
│   └── FrontEnd/
│       └── Dockerfile
└── Plant/                  # ⏳ To be created
    ├── ...
    └── Dockerfile
```

## Example Workflows

### 1. Deploy CP Only (Default)

```
Inputs:
  target_components: cp
  build_images: true
  deploy_to_gcp: true
  target_environment: demo

Result:
  ✅ Tests src/CP/BackEnd + src/CP/FrontEnd
  ✅ Builds cp-backend, cp Docker images
  ✅ Deploys with enable_backend_api=true, enable_customer_portal=true, enable_platform_portal=false
```

### 2. Test PP When Ready (PP paths must exist)

```
Inputs:
  target_components: pp
  build_images: true
  deploy_to_gcp: false

Result:
  ✅ Tests src/PP/BackEnd + src/PP/FrontEnd
  ✅ Builds pp-backend, pp Docker images
  ⏭️  Skips deployment (deploy_to_gcp=false)
```

### 3. Deploy CP + PP Together (When ready)

```
Inputs:
  target_components: cp,pp
  build_images: true
  deploy_to_gcp: true
  target_environment: uat

Result:
  ✅ Tests both CP and PP
  ✅ Builds all 4 images: cp-backend, cp, pp-backend, pp
  ✅ Deploys to UAT with all 3 services enabled
```

### 4. Staged Deployment (CP to Prod, Test PP in Demo)

Run pipeline twice:
```
# Run 1: CP to Prod
target_components: cp
target_environment: prod
deploy_to_gcp: true

# Run 2: PP to Demo (just test, don't deploy yet)
target_components: pp
target_environment: demo
deploy_to_gcp: false
build_images: true
```

## Troubleshooting

### ⚠️ "PP selected but src/PP/BackEnd not found - skipping PP build"

**Cause**: User selected `target_components=pp` but path doesn't exist yet.

**Solution**: 
- Create `src/PP/BackEnd/` and `src/PP/FrontEnd/` with Dockerfile
- Or select only available components (e.g., `target_components=cp`)

### ❌ "ERROR: CP selected but src/CP/BackEnd not found!"

**Cause**: Critical error - CP is the default component but its path is missing.

**Solution**: This shouldn't happen in normal operation. Check git clone or file structure.

### ❌ "Image 'asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp:demo' not found"

**Cause**: Old issue - Terraform tried to deploy `platform_portal` but pipeline didn't build `pp` image.

**Solution**: Already fixed! Pipeline now sets enable flags dynamically based on what was built.

## Future Work

- [ ] Create separate pp-pipeline.yml when PP development starts (or extend this one)
- [ ] Create separate plant-pipeline.yml when Plant development starts (or extend this one)
- [ ] Add matrix strategy for building multiple components in parallel
- [ ] Add multi-select UI for `target_components` in GitHub UI (requires GitHub Enterprise)
- [ ] Add post-deploy smoke tests for each component type
- [ ] Add rollback workflow to revert to previous image tags
