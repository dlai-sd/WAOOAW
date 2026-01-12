# WAOOAW Unified Architecture (Cost-Optimized, Terraform-Driven)

**Last Updated**: January 12, 2026

## What we want
- **One static IP + one HTTPS load balancer** (cost constraint).
- **Terraform-driven provisioning** (pipeline creates CP demo infra cleanly).
- **Code-only deploys most days** (CP frontend/backend image updates only).
- Later: deploy **PP/Plant independently** without accidentally changing CP.

## Core approach

### Single entrypoint (cost-friendly)
- One global IP
- One HTTPS LB
- Host-based routing:
  - `cp.<env>.waooaw.com` → CP
  - `pp.<env>.waooaw.com` → PP
  - `plant.<env>.waooaw.com` → Plant

### Terraform “stacks” with separate remote state (isolation)
We isolate deployments by splitting state, even though the LB/IP is shared.

- `foundation` stack (changes rarely)
  - LB, proxies, forwarding rules, URL maps, managed cert resources
- `cp` stack (changes often)
  - CP Cloud Run services + minimal IAM
- `pp` stack (future)
  - PP Cloud Run services + minimal IAM
- `plant` stack (future)
  - Plant Cloud Run services + minimal IAM

Remote state prefixes (GCS) example:
- `env/demo/foundation/default.tfstate`
- `env/demo/cp/default.tfstate`
- `env/demo/pp/default.tfstate`
- `env/demo/plant/default.tfstate`

Why this works:
- Deploying PP does not touch CP *state*.
- Deploying CP day-to-day does not touch foundation (LB/certs).

## Deployment modes

### 1) Clean start / Bootstrap (now)
- Pipeline runs Terraform apply to create:
  - foundation (LB + cert objects)
  - CP services
- DNS points to the single static IP.
- Wait for managed SSL to become ACTIVE.

### 2) Code-only CP deploy (default)
- Build/push CP images.
- Terraform apply updates only CP Cloud Run services (new revision).
- No LB changes.

### 3) Add PP/Plant later
- Deploy PP/Plant Cloud Run via their stack.
- Update foundation routing/certs once.
- CP remains untouched.

## Guardrails (non-negotiable)
- No `terraform -target` in CI.
- CI must be reproducible (do not edit committed `*.tfvars` files).
- Lock concurrency per `env + stack`.
- Always: plan → apply(planfile).

## Current focus (CP only)
- Keep PP/Plant disabled by default until code exists.
- Make CP demo fully functional (infra + deploy + smoke checks).
  enable_plant: true
  environment: demo

Pipeline Actions:
  ✅ Test & build: CP (3 services) + Plant (2 services)
  ✅ Terraform deploys: 5 services total
  ✅ IAM: CP backend granted invoker role on Plant backend

GCP Services Created:
  ├─ waooaw-cp-frontend-demo
  ├─ waooaw-cp-backend-demo    → calls Plant
  ├─ waooaw-cp-health-demo
  ├─ waooaw-plant-backend-demo (Core API)
  └─ waooaw-plant-health-demo

Service Communication:
  CP Backend → Plant Backend (internal, authenticated)
```

### Scenario 3: All Components (Future)
```yaml
Workflow Inputs:
  enable_cp: true
  enable_pp: true
  enable_plant: true
  environment: uat

Pipeline Actions:
  ✅ Test & build: All 8 services
  ✅ Terraform deploys: 8 services total
  ✅ IAM: CP/PP backends can invoke Plant

GCP Services Created:
  CP:    waooaw-cp-frontend-uat, waooaw-cp-backend-uat, waooaw-cp-health-uat
  PP:    waooaw-pp-frontend-uat, waooaw-pp-backend-uat, waooaw-pp-health-uat
  Plant: waooaw-plant-backend-uat, waooaw-plant-health-uat

Load Balancer Routes:
  cp.uat.waooaw.com/    → CP services
  pp.uat.waooaw.com/    → PP services
  plant.uat.waooaw.com/ → Plant services

Service Communication:
  CP Backend → Plant Backend
  PP Backend → Plant Backend
```

---

## Service Naming Convention

### Pattern
```
waooaw-{component}-{service-type}-{environment}
```

### Examples by Environment
  target_components = "all"
  deploy_to_gcp = true
  target_environment = "demo"
  terraform_action = "apply"

Pipeline Actions (when all paths exist):
  ✅ Tests: All component tests
  ✅ Builds: cp-backend + cp + pp-backend + pp + plant images
  ✅ Terraform: All enable_* flags = true

GCP State After Apply:
  ├─ api-demo (CP backend) - CREATED
  ├─ portal-demo (CP frontend) - CREATED
  ├─ platform-api-demo (PP backend) - CREATED
  ├─ platform-portal-demo (PP frontend) - CREATED
  └─ plant-api-demo (Plant core) - CREATED

URLs Available:
  ├─ api.waooaw.com (CP backend)
  ├─ waooaw.com (CP portal)
  ├─ platform-api.waooaw.com (PP backend)
  ├─ platform.waooaw.com (PP portal)
  └─ plant-api.waooaw.com (Plant API)
```

## Terraform State Management

### Environment-Specific Configurations
```
cloud/terraform/environments/
├── demo.tfvars
│   ├── environment = "demo"
│   ├── domain_name = "waooaw.com"
│   ├── enable_backend_api = true
│   ├── enable_customer_portal = true
│   └── enable_platform_portal = false (updated by pipeline)
│
├── uat.tfvars
│   ├── environment = "uat"
│   ├── domain_name = "uat.waooaw.com"
│   ├── enable_backend_api = true
│   ├── enable_customer_portal = true
│   └── enable_platform_portal = false (updated by pipeline)
│
└── prod.tfvars
    ├── environment = "prod"
    ├── domain_name = "api.waooaw.com" / "waooaw.com"
    ├── enable_backend_api = true
    ├── enable_customer_portal = true
    └── enable_platform_portal = false (updated by pipeline)
```

### How Terraform Enable Flags Work

```hcl
# cloud/terraform/variables.tf
variable "enable_backend_api" {
  type = bool
  default = true
}

variable "enable_customer_portal" {
  type = bool
  default = true
}

variable "enable_platform_portal" {
  type = bool
  default = false
}

# cloud/terraform/main.tf
module "backend_api" {
  count = var.enable_backend_api ? 1 : 0
  # ... backend configuration
}

module "customer_portal" {
  count = var.enable_customer_portal ? 1 : 0
  # ... customer portal configuration
}

module "platform_portal" {
  count = var.enable_platform_portal ? 1 : 0
  # ... platform portal configuration
}

# Only modules with count > 0 are created/updated in GCP
```

## Network & Load Balancer

```
Load Balancer (GCP HTTP(S) Load Balancer)
  ├─ Public IP: 35.xxx.xxx.xxx
  └─ SSL Certificate: *.waooaw.com, waooaw.com
     ├─ Host Rule: api.waooaw.com → Backend Service (api-demo)
     ├─ Host Rule: waooaw.com → Backend Service (portal-demo)
     ├─ Host Rule: platform-api.waooaw.com → Backend Service (platform-api-demo) [conditional]
     └─ Host Rule: platform.waooaw.com → Backend Service (platform-portal-demo) [conditional]

Backend Services (Cloud Run NEGs):
  ├─ backend-api-neg (Network Endpoint Group, Cloud Run)
  ├─ customer-portal-neg (Network Endpoint Group, Cloud Run)
  ├─ platform-api-neg [conditional]
  └─ plant-api-neg [conditional]

Cloud Run Services (Actual Application Instances):
  ├─ api-demo (runs cp-backend Docker image)
  ├─ portal-demo (runs cp Docker image)
  ├─ platform-api-demo [conditional] (runs pp-backend Docker image)
  ├─ platform-portal-demo [conditional] (runs pp Docker image)
  └─ plant-api-demo [conditional] (runs plant Docker image)
```

## Summary: The Unified Architecture

| Aspect | Before | After |
|--------|--------|-------|
| **Component Support** | CP only | CP + PP + Plant (selectable) |
| **Pipeline** | Hardcoded paths | Dynamic component selection |
| **Terraform** | Always deploy all 3 | Deploy only enabled services |
| **Enable Flags** | Static in tfvars | Dynamic from pipeline |
| **Mismatch Risk** | ❌ High (image not found errors) | ✅ Zero (pipeline controls deployment) |
| **Dev Workflow** | Build CP, deploy CP | Select what to build/deploy |
| **Future Ready** | Need rewrite for PP/Plant | Auto-detects new components |

## Getting Started

### Deployment Instructions (Architecture v2.0)

**Pipeline Status**: ✅ All critical issues resolved (Commit: 31279e4)

#### Deploy CP-Only to Demo (Recommended First Deployment)
```bash
# Trigger via GitHub Actions UI:
# Navigate to: Actions → CP Pipeline → Run workflow
# Set inputs:
enable_cp: true
enable_pp: false
enable_plant: false
environment: demo
dep# Deploy CP + Plant (Phase 2)
```bash
gh workflow run .github/workflows/cp-pipeline.yml \
  --ref main \
  -f enable_cp=true \
  -f enable_pp=false \
  -f enable_plant=true \
  -f environment=demo \
  -f deploy_to_gcp=true \
  -f terraform_action=apply
```

**Expected Outcome**:
- 5 Cloud Run services: CP (3) + Plant (2)
- CP backend can call Plant backend via IAM authentication

#### Deploy Full Platform (Phase 3)
```bash
gh workflow run .github/workflows/cp-pipeline.yml \
  --ref main \
  -f enable_cp=true \
  -f enable_pp=true \
  -f enable_plant=true \
  -f environment=demo \
  -f deploy_to_gcp=true \
  -f terraform_action=apply
```

**Expected Outcome**:
- 8 Cloud Run services: CP (3) + PP (3) + Plant (2)
- All inter-service IAM bindings configured

### Prerequisites for PP/Plant Deployment
**PP Component** (Currently: enable_pp=false):
1. ✅ Implementation Status (Architecture v2.0)

### Completed Tasks

#### ✅ Phase 1: Terraform State Cleanup
- **Status**: Complete (Commit: 06bfed7)
- **Actions**:
  - Removed 19 ghost resources from terraform.tfstate
  - Cleaned up old load-balancer, networking, and platform_portal modules
  - Verified GCP matches cleaned state

#### ✅ Phase 2: Terraform Configuration Updates
- **Status**: Complete (Commit: 06bfed7)
- **Files Updated**:
  - ✅ `cloud/terraform/main.tf` - 8 new service modules with enable_cp/pp/plant flags
  - ✅ `cloud/terraform/variables.tf` - New enable flags and image variables
  - ✅ `cloud/terraform/outputs.tf` - New output structure (cp_url, pp_url, plant_url)
  - ✅ `cloud/terraform/modules/load-balancer/main.tf` - 8-service routing, health checks
  - ✅ `cloud/terraform/modules/networking/main.tf` - Updated for new architecture
  - ✅ `cloud/terraform/demo.tfvars` - Updated with Architecture v2.0 variables
- **Validation**: terraform fmt ✅, terraform init ✅, terraform validate ✅

#### ✅ Phase 3: Pipeline Updates
- **Status**: Complete (Commit: 31279e4)
- **Files Updated**:
  - ✅ `.github/workflows/cp-pipeline.yml` - Complete overhaul for Architecture v2.0
    - New workflow inputs: enable_cp, enable_pp, enable_plant
    - Updated validate-components job with correct path checks
    - Fixed all job conditions (frontend-test, backend-test, build, push)
    - Dynamic Terraform module targeting based on enabled components
    - New URL retrieval logic (cp_url, pp_url, plant_url)
    - Component-level smoke tests (CP, PP, Plant)
- **Validation**: Pipeline simulation ✅ (0 critical issues)

#### ✅ Phase 4: Pipeline Validation
- **Status**: Complete
- **Tool**: `cloud/terraform/pipeline-simulation.sh`
- **Results**:
  - ✅ 0 Critical Issues
  - ⚠️ 9 Warnings (non-blocking):
    - 6 Dockerfiles missing (can use existing images)
    - 3 build jobs for PP/Plant (not needed for CP-only deployment)
- **Documentation**: `cloud/terraform/PIPELINE_SIMULATION_RESULTS.md`

### Pending Tasks

#### ⏳ Phase 5: First Deployment Test
- **Action**: Deploy CP-only to demo environment
- **Command**: Use GitHub Actions workflow with enable_cp=true
- **Expected**: 3 services deploy successfully
- **Status**: Ready to execute

#### ⏳ Phase 6: Docker Build Infrastructure (Optional)
- **Requirements**: Create 6 Dockerfiles for PP and Plant components
- **Priority**: MEDIUM (not blocking CP deployment)
- **Status**: Documented as warnings

#### ⏳ Phase 7: Environment Propagation
- **Action**: Update uat.tfvars and prod.tfvars with Architecture v2.0 variables
- **Priority**: MEDIUM (required before deploying to other environments)
- **Status**: demo.tfvars complete, uat/prod pending

### Git Commits History

```
31279e4 - fix(pipeline): remove all deprecated variable references (Latest)
          - Removed enable_backend_api/customer_portal/platform_portal
          - Updated all job conditions to use enable_cp/pp/plant
          - Pipeline simulation: 0 critical issues

8fdbbe7 - fix(pipeline): update workflow for architecture v2.0
          - Updated workflow inputs, validation logic
          - Terraform targeting, URL retrieval, smoke tests
          - Fixed 3 critical issues from simulation

06bfed7 - feat(architecture): implement architecture v2.0 with 8-service model
          - Updated main.tf, variables.tf, outputs.tf
          - Updated load-balancer and networking modules
          - Cleaned terraform.tfstate (19 ghost resources)
```es/load-balancer/variables.tf`**
   - Update enable flags from enable_api/customer/platform to enable_cp/pp/plant, update domain variables structure

#### CI/CD Pipeline (1 file)

7. **`.github/workflows/cp-pipeline.yml`**
   - Add enable_cp/enable_pp/enable_plant workflow inputs, update validate-components job to check all 3 component paths, add conditional build jobs for PP and Plant, pass enable flags to Terraform step

#### State Cleanup (manual)

8. **`cloud/terraform/terraform.tfstate`**
   - Remove ghost resources via `terraform state rm` commands (19 resources: load_balancer module, networking module, platform_portal module resources)

### Implementation Phases

**Phase 1: State Cleanup (Manual)**
- Clean Terraform state of ghost resources
- Verify GCP matches state

**Phase 2: Terraform Updates**
- Update variables, main.tf, outputs
- Update networking and load-balancer modules
- Test with `terraform plan`

**Phase 3: Pipeline Updates**
- Add enable_cp/pp/plant inputs to workflow
- Add PP and Plant build jobs (conditional)
- Update Terraform step to pass new flags

**Phase 4: Deployment**
- Deploy CP with new structure (enable_cp=true)
- Verify load balancer recreation
- Test custom domain access
