# Pipeline Component Selection Guide

## Overview

The unified CI/CD pipeline supports selective building and deployment of **CP** (Customer Portal), **PP** (Platform Portal), and **Plant** (Agent Core). Currently focused on **demo environment + CP** deployment with workflow gating to prevent Load Balancer churn during app-only updates.

## Current Deployment Strategy (January 2026)

### Phase 1: Demo + CP (Current - Days 1-3)
- **Environment**: demo only (uat/prod deferred)
- **Component**: CP (Customer Portal Backend + Frontend)
- **State**: Local terraform.tfstate (GCS migration deferred)
- **LB Strategy**: Workflow gating with `update_load_balancer=false` default

### Phase 2: Demo + PP (Days 4-5)
- **Enable**: Platform Portal in demo.tfvars
- **Component**: PP (Platform Portal Backend + Frontend)
- **LB Behavior**: Automatically adds PP health check, backend service, URL map rules

### Phase 3: Demo + Plant (Days 6-7)
- **Component**: Plant (Agent Core Backend only)
- **LB Behavior**: No LB changes (backend-only service)

### Phase 4: Multi-Environment (Month 2+)
- **Environments**: demo → uat → prod promotion
- **State Management**: Separate states per environment or workspaces
- **Approval Gates**: Human review required for production

## Workflow Inputs

### `target_components`

When manually triggering the workflow, select which components to build and deploy:

### Options

| Value | Description | Status | Timeline |
|-------|-------------|--------|----------|
| `cp` (default) | Customer Portal (Backend + Frontend) | ✅ Ready | Days 1-3 |
| `pp` | Platform Portal (Backend + Frontend) | ⏳ Ready Days 4-5 | Days 4-5 |
| `plant` | Agent Core (Backend only) | ⏳ Ready Days 6-7 | Days 6-7 |
| `cp,pp` | CP + PP combined | ⏳ After Day 5 | Week 2+ |
| `cp,plant` | CP + Plant combined | ⏳ After Day 7 | Week 2+ |
| `pp,plant` | PP + Plant combined | ⏳ After Day 7 | Week 2+ |
| `all` | All available components | ⏳ After Day 7 | Week 2+ |

### `target_environment`

Select the GCP environment to deploy to when `deploy_to_gcp=true`:

- `demo` (default) - **Active development target (Month 1)**
- `uat` - **Deferred (Month 2+)**
- `prod` - **Deferred (Month 2+)**

### `update_load_balancer`

Controls whether Load Balancer resources are included in Terraform operations:

- `false` (default) - **App-only deploy**: Targeted refresh/plan skips LB module, zero LB churn
- `true` - **Full deploy**: Includes LB resources (use when enabling/disabling services or changing LB config)

**When to use `update_load_balancer=true`:**
- Enabling Platform Portal for first time (`enable_platform_portal=true`)
- Disabling services (`enable_platform_portal=false`)
- Changing domains, SSL certs, URL routing rules
- Initial environment setup

**Default behavior (`update_load_balancer=false`):**
- Only Cloud Run services updated with new images
- Health checks, backend services, URL maps untouched
- Faster deploys (2-3 min vs 5-10 min)
- Production-safe for app updates

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

## Key Architectural Decisions

### Load Balancer Decoupling Strategy

**Problem**: LB + App in single Terraform state caused LB resource churn during app-only updates.

**Solutions Evaluated**:
1. ❌ **State split** - Separate LB state from app state (complex migration, overkill for demo)
2. ❌ **Lifecycle guards (`prevent_destroy`)** - Blocked legitimate topology changes (e.g., disabling Platform Portal)
3. ✅ **Workflow gating** - `update_load_balancer` input controls targeted operations

**Implementation**:
- `update_load_balancer=false` (default): Terraform uses `-target` flags to skip LB module in refresh/plan/apply
- `update_load_balancer=true`: Full Terraform operations include LB resources
- Sanity checks run full plans (no `-target` flags) with exit code 2 accepted (changes detected = valid)
- No `prevent_destroy` on LB resources (allows service enable/disable)

**Benefits**:
- App updates don't touch LB (zero churn, faster deploys)
- Service topology changes work correctly (enable/disable PP, Plant)
- Simple to understand and operate
- Migration path to state split when scaling to uat/prod

### State Management

**Current (Demo-Only)**:
- Local `terraform.tfstate` file in repo
- Single state contains demo/uat/prod configs (only demo active)
- Acceptable for single-developer, demo-only scope
- No state locking needed (no parallel deploys)

**Future (Multi-Environment)**:
- GCS backend with state locking (`gs://waooaw-terraform-state/`)
- Separate states per environment (demo.tfstate, uat.tfstate, prod.tfstate)
- Workload Identity Federation (keyless auth, no SA keys)
- State encryption at rest

### IAM & Security

**Current**:
- Service account key (`GCP_SA_KEY` secret) for authentication
- Roles: `roles/run.admin`, `roles/compute.loadBalancerAdmin`, `roles/iam.serviceAccountUser`
- Key committed to repo (demo-only, acceptable risk)

**Future Improvements**:
- Workload Identity Federation (no keys)
- SOPS/sealed-secrets for encrypted secrets in repo
- Separate service accounts per environment (least privilege)
- Audit logging for all infrastructure changes

## Terraform Integration

The pipeline **dynamically updates tfvars** during deployment based on component selection:

```bash
# Example: User selects target_components="cp"
enable_backend_api = true           # CP depends on backend API
enable_customer_portal = true       # CP frontend selected
enable_platform_portal = false      # PP not selected → skip deployment

# Terraform behavior with update_load_balancer=false (default):
# 1. Refresh: terraform apply -refresh-only -target=module.backend_api -target=module.customer_portal -target=module.networking
# 2. Plan: terraform plan -target=module.backend_api -target=module.customer_portal -target=module.networking
# 3. Apply: terraform apply (using targeted plan, LB unchanged)

# Result: Only backend_api + customer_portal images updated, LB untouched
```

### Terraform Module Structure

```
cloud/terraform/
├── main.tf                          # Root config, orchestrates modules
├── variables.tf                     # Input variables
├── outputs.tf                       # Service URLs, IPs
├── environments/
│   ├── demo.tfvars                  # enable_platform_portal=false (current)
│   ├── uat.tfvars                   # All services enabled (future)
│   └── prod.tfvars                  # All services enabled (future)
└── modules/
    ├── cloud-run/                   # Cloud Run service module
    ├── load-balancer/               # Global LB (health checks, backends, URL maps)
    └── networking/                  # NEGs (Network Endpoint Groups)
```

### Service Enable Logic

| Component | `enable_backend_api` | `enable_customer_portal` | `enable_platform_portal` |
|-----------|---------------------|-------------------------|-------------------------|
| CP        | ✅ true              | ✅ true                  | ❌ false                 |
| PP        | ✅ true              | ❌ false                 | ✅ true                  |
| Plant     | ✅ true              | ❌ false                 | ❌ false                 |
| CP+PP     | ✅ true              | ✅ true                  | ✅ true                  |

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

### 1. Deploy CP to Demo (Current Default)

```yaml
Inputs:
  target_components: cp
  build_images: true
  deploy_to_gcp: true
  target_environment: demo
  terraform_action: plan
  update_load_balancer: false        # Default - app-only deploy

Result:
  ✅ Sanity checks pass (exit code 2 accepted)
  ✅ Tests src/CP/BackEnd + src/CP/FrontEnd
  ✅ Builds cp-backend:demo-{sha}-{run}, cp:demo-{sha}-{run}
  ✅ Pushes to asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/
  ✅ Terraform plan shows only Cloud Run image updates (LB skipped)
  ⏸️  Manual approval: Re-run with terraform_action=apply
```

### 2. Enable Platform Portal (First Time)

```yaml
Step 1 - Build PP Images:
  target_components: pp
  build_images: true
  deploy_to_gcp: false               # Build only, don't deploy yet

Step 2 - Update demo.tfvars locally:
  enable_platform_portal = true      # Edit file

Step 3 - Deploy PP with LB Update:
  target_components: pp
  deploy_to_gcp: true
  terraform_action: apply
  update_load_balancer: true         # ⚠️ Required for first-time enable

Result:
  ✅ PP images deployed to Cloud Run
  ✅ LB adds PP health check, backend service, URL map rules
  ✅ pp.demo.waooaw.com accessible
```

### 3. Hotfix CP Frontend (Common Workflow)

```yaml
Inputs:
  target_components: cp
  build_images: true
  deploy_to_gcp: true
  terraform_action: apply            # Direct apply for hotfix
  update_load_balancer: false        # App-only, no LB changes

Result:
  ✅ New CP frontend image built and deployed
  ✅ LB untouched (zero downtime)
  ✅ cp.demo.waooaw.com serves updated frontend
  ⏱️  Total time: ~3 minutes
```

### 4. Combined CP+PP Update (Week 2+)

```yaml
Inputs:
  target_components: cp,pp
  build_images: true
  deploy_to_gcp: true
  terraform_action: plan
  update_load_balancer: false        # Both services already enabled

Result:
  ✅ Builds all 4 images: cp-backend, cp, pp-backend, pp
  ✅ Terraform plan shows Cloud Run updates for both services
  ✅ LB skipped (no topology change)
  ✅ Apply updates both CP and PP simultaneously
```

## Troubleshooting

### ✅ Sanity Check: "Plan shows changes (exit code 2)"

**Behavior**: Sanity check passes with exit code 2 (changes detected).

**Explanation**: 
- Exit code 2 = Terraform plan succeeded but detected changes (valid state)
- Exit code 1 = Terraform plan failed with errors (pipeline fails)
- Exit code 0 = No changes detected (ideal but rare in active development)

**Action**: No action needed - this is expected behavior during active development.

---

### ⚠️ Run Fails: "Instance cannot be destroyed - lifecycle.prevent_destroy"

**Cause**: You re-introduced `prevent_destroy` on LB resources or trying to destroy protected static IP.

**Solution**: 
- LB resources should NOT have `prevent_destroy` (blocks service enable/disable)
- Only static IP should have protection (permanent infrastructure)
- Check commit history: `git log --grep="prevent_destroy" --oneline`

---

### ⚠️ Terraform Plan: "LB resources showing changes despite update_load_balancer=false"

**Cause**: `-target` flags not working correctly in workflow.

**Diagnosis**:
- Check workflow logs for "Targeted refresh" vs "Full refresh"
- Verify `update_load_balancer` input is exactly `false` (not empty string)
- Review terraform plan output for unexpected LB changes

**Solution**:
- Ensure workflow uses: `if [ "$UPDATE_LB" != "true" ]; then` (string comparison)
- Check commit 2de11f0 has correct `-target` flag logic

---

### ❌ Deploy Fails: "Error creating Backend Service: Health check not found"

**Cause**: Platform Portal disabled but LB module expects health check.

**Solution**:
- LB module uses `count = var.enable_platform ? 1 : 0` (conditional creation)
- Verify demo.tfvars has `enable_platform_portal = false`
- Check Terraform state: `terraform state list | grep platform`
- If stale resources exist: `terraform state rm module.load_balancer.google_compute_health_check.platform[0]`

---

### ⚠️ "image not found in Artifact Registry"

**Cause**: Terraform trying to deploy service but image not built.

**Diagnosis**:
- Check pipeline logs: "Building images for components: cp" should match deployment
- Verify image tag: `gcloud artifacts docker images list asia-south1-docker.pkg.dev/waooaw-oauth/waooaw`
- Check tfvars update step: "Updated demo.tfvars keys" should show correct image tags

**Solution**:
- Ensure `build_images=true` when `deploy_to_gcp=true`
- Match `target_components` between build and deploy
- Use `image_tag=auto` for automatic version tagging

---

### 🔴 State Conflict: "Error acquiring state lock"

**Cause**: Two pipeline runs executing Terraform simultaneously.

**Solution (Current - Local State)**:
- Wait for first run to complete
- Cancel duplicate runs via GitHub Actions UI
- This shouldn't happen with local state (no locking mechanism)

**Solution (Future - GCS Backend)**:
- State lock timeout: `terraform apply -lock-timeout=5m`
- Force unlock (dangerous): `terraform force-unlock <LOCK_ID>`
- Check Cloud Console: Storage > waooaw-terraform-state > Locks

---

### ✅ Deployment Success but Service Unhealthy

**Symptoms**:
- Terraform apply succeeds
- Cloud Run service shows "Unhealthy" or "HEALTH_CHECK_CONTAINER_ERROR"
- cp.demo.waooaw.com returns 502 Bad Gateway

**Diagnosis**:
- Check Cloud Run logs: `gcloud run services logs read waooaw-portal-demo --region=asia-south1`
- Verify port: Container MUST listen on port 8080 (Nginx, not 80)
- Check health endpoint: `curl -H "Host: cp.demo.waooaw.com" http://[CLOUD_RUN_URL]/`

**Common Issues**:
- Container running as root (use non-root user, port 8080+)
- ENV vars missing (GOOGLE_CLIENT_ID, JWT_SECRET)
- Backend API not responding to /health endpoint
- SSL cert provisioning in progress (wait 10-15 min)

---

### 📋 Known Issues & Limitations

**Current State (January 2026)**:
- ⚠️ Local Terraform state (not suitable for team collaboration or production)
- ⚠️ Service account key in repo (security risk, acceptable for demo)
- ⚠️ No rollback automation (manual image revert required)
- ⚠️ No approval gates (anyone with repo access can deploy)
- ⚠️ Single GCP project for all environments (cost visibility difficult)

**Planned Improvements**:
- 🔄 GCS backend with state locking (Month 2)
- 🔄 Workload Identity Federation (Month 2)
- 🔄 Separate GCP projects per environment (Month 3)
- 🔄 Blue-green deployment strategy (Month 4)
- 🔄 Automated rollback on health check failures (Month 4)

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
