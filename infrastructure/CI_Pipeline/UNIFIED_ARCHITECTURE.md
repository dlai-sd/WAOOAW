# Unified Multi-Component Platform Architecture

**Last Updated**: January 12, 2026  
**Architecture Version**: 2.0 (3-Component Model)

## System Overview

WAOOAW is a **unified multi-component platform** with:
1. **Three core components** (CP, PP, Plant)
2. **Conditional deployment** via enable flags (deploy only what's needed)
3. **Service-to-service communication** (CP/PP backends call Plant backend)
4. **No Portal component** (removed from architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                 GitHub Actions Workflow                    │
│                  cp-pipeline.yml                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: enable_cp (bool), enable_pp (bool),                │
│         enable_plant (bool), environment (demo/uat/prod)   │
│         ⬇️                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  validate-components                                │  │
│  │  ✓ Check enabled component paths exist             │  │
│  │  ✓ Set build flags based on enable_* inputs        │  │
│  │  ✓ Pass enable_cp, enable_pp, enable_plant to TF   │  │
│  └──────────────────────────────────────────────────────┘  │
│         ⬇️                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Conditional Test & Build Jobs                     │  │
│  │  (Only run for enabled components)                 │  │
│  │  ├─ CP: test + build frontend/backend/health       │  │
│  │  ├─ PP: test + build frontend/backend/health       │  │
│  │  └─ Plant: test + build backend/health             │  │
│  └──────────────────────────────────────────────────────┘  │
│         ⬇️                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  terraform-deploy (if deploy_to_gcp=true)          │  │
│  │  ├─ Auth to GCP                                     │  │
│  │  ├─ terraform plan with enable_* variables         │  │
│  │  ├─ terraform apply (creates only enabled services)│  │
│  │  ├─ Verifies: CP (3), PP (3), Plant (2) if enabled │  │
│  │  └─ Smoke tests on deployed services               │  │
│  └──────────────────────────────────────────────────────┘  │
│         ⬇️                                                   │
│  GCP Cloud Run: 3-8 services per environment               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Overview: 3 Components, 8 Services Total

```
CP (Customer Portal) - 3 services
├─ Frontend  → User interface
├─ Backend   → Orchestration layer → calls Plant backend
└─ Health    → Monitoring endpoint

PP (Platform Portal) - 3 services  
├─ Frontend  → User interface
├─ Backend   → Orchestration layer → calls Plant backend
└─ Health    → Monitoring endpoint

Plant (Core API) - 2 services
├─ Backend   → Shared business logic (no frontend)
└─ Health    → Monitoring endpoint
```

### Service Communication Flow

```
User → CP Frontend → CP Backend → Plant Backend (Core API)
User → PP Frontend → PP Backend → Plant Backend (Core API)
```

**Key Points:**
- CP and PP backends are thin orchestration layers
- Plant backend contains all shared business logic
- Plant has no frontend (backend-only component)
- All inter-service calls use service account authentication

---

## Component Details

### 1. Customer Portal (CP) - ✅ Active (Demo)

**Source Code**: `src/CP/`
```
src/CP/
├── BackEnd/
│   ├── api/          (FastAPI routes)
│   ├── core/         (orchestration logic)
│   ├── models/       (data models)
│   ├── Dockerfile
│   └── requirements.txt
└── FrontEnd/
    ├── src/          (React components)
    ├── Dockerfile
    └── package.json
```

**Cloud Run Services** (Demo environment):
```
waooaw-cp-frontend-demo  → React app on :8080
waooaw-cp-backend-demo   → FastAPI on :8000 → calls Plant
waooaw-cp-health-demo    → Monitoring on :8080
```

**Docker Images**:
```
asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-frontend:{env}-{sha}-{run}
asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend:{env}-{sha}-{run}
asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-health:{env}-{sha}-{run}
```

**Load Balancer Routing**:
```
cp.demo.waooaw.com/          → waooaw-cp-frontend-demo
cp.demo.waooaw.com/api/*     → waooaw-cp-backend-demo
cp.demo.waooaw.com/health    → waooaw-cp-health-demo
```

**Terraform Variables**:
```hcl
enable_cp = true  # Deploys all 3 CP services
```

---

### 2. Platform Portal (PP) - ⏳ Future

**Source Code**: `src/PP/` (to be created)
```
src/PP/
├── BackEnd/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── Dockerfile
│   └── requirements.txt
└── FrontEnd/
    ├── src/
    ├── Dockerfile
    └── package.json
```

**Cloud Run Services** (when enabled):
```
waooaw-pp-frontend-demo  → React app on :8080
waooaw-pp-backend-demo   → FastAPI on :8000 → calls Plant
waooaw-pp-health-demo    → Monitoring on :8080
```

**Docker Images**:
```
asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp-frontend:{env}-{sha}-{run}
asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp-backend:{env}-{sha}-{run}
asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp-health:{env}-{sha}-{run}
```

**Load Balancer Routing**:
```
pp.demo.waooaw.com/          → waooaw-pp-frontend-demo
pp.demo.waooaw.com/api/*     → waooaw-pp-backend-demo
pp.demo.waooaw.com/health    → waooaw-pp-health-demo
```

**Terraform Variables**:
```hcl
enable_pp = false  # When true, deploys all 3 PP services
```

---

### 3. Plant (Core API) - ⏳ Future

**Source Code**: `src/Plant/` (to be created)
```
src/Plant/
└── BackEnd/
    ├── api/          (Core business logic APIs)
    ├── core/         (Shared services)
    ├── models/       (Data models)
    ├── Dockerfile
    └── requirements.txt

Note: Plant has NO frontend (backend-only component)
```

**Cloud Run Services** (when enabled):
```
waooaw-plant-backend-demo  → FastAPI on :8000 (Core API)
waooaw-plant-health-demo   → Monitoring on :8080
```

**Docker Images**:
```
asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-backend:{env}-{sha}-{run}
asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant-health:{env}-{sha}-{run}
```

**Load Balancer Routing**:
```
plant.demo.waooaw.com/api/*  → waooaw-plant-backend-demo
plant.demo.waooaw.com/health → waooaw-plant-health-demo
```

**Terraform Variables**:
```hcl
enable_plant = false  # When true, deploys 2 Plant services
```

**IAM Configuration**:
```hcl
# CP backend can call Plant backend
google_cloud_run_service_iam_member.cp_to_plant

# PP backend can call Plant backend
google_cloud_run_service_iam_member.pp_to_plant
```

---

## Deployment Scenarios

### Scenario 1: CP Only (Current - Demo)
```yaml
Workflow Inputs:
  enable_cp: true
  enable_pp: false
  enable_plant: false
  environment: demo
  deploy_to_gcp: true
  terraform_action: apply

Pipeline Actions:
  ✅ Test & build: CP frontend, CP backend, CP health
  ✅ Terraform deploys: 3 services

GCP Services Created:
  ├─ waooaw-cp-frontend-demo  (:8080)
  ├─ waooaw-cp-backend-demo   (:8000)
  └─ waooaw-cp-health-demo    (:8080)

Load Balancer Routes:
  cp.demo.waooaw.com/       → frontend
  cp.demo.waooaw.com/api/*  → backend
  cp.demo.waooaw.com/health → health
```

### Scenario 2: CP + Plant (Future)
```yaml
Workflow Inputs:
  enable_cp: true
  enable_pp: false
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

### To Deploy CP (Current)
```bash
# Use GitHub Actions UI or CLI:
gh workflow run .github/workflows/cp-pipeline.yml \
  --ref main \
  -f target_components=cp \
  -f build_images=true \
  -f deploy_to_gcp=true \
  -f target_environment=demo \
  -f terraform_action=apply \
  -f run_tests=true
```

### To Prepare for PP (Future)
1. Create `src/PP/BackEnd/` with Dockerfile
2. Create `src/PP/FrontEnd/` with Dockerfile
3. Pipeline will auto-detect and include in builds
4. Deploy with: `target_components=pp` or `target_components=all`

### To Prepare for Plant (Future)
1. Create `src/Plant/` with Dockerfile
2. Pipeline will auto-detect and include in builds
3. Deploy with: `target_components=plant` or `target_components=all`

---

## Implementation Roadmap

### Code Files Requiring Changes

#### Terraform Core Files (3 files)

1. **`cloud/terraform/main.tf`**
   - Replace 3 old modules (backend_api, customer_portal, platform_portal) with 8 new modules (cp_frontend, cp_backend, cp_health, pp_frontend, pp_backend, pp_health, plant_backend, plant_health) using enable_cp/pp/plant flags

2. **`cloud/terraform/variables.tf`**
   - Remove enable_backend_api/customer_portal/platform_portal variables, add enable_cp/enable_pp/enable_plant boolean flags, update domains variable to include cp/pp/plant keys, remove portal domain references

3. **`cloud/terraform/outputs.tf`**
   - Update outputs from old service names to new naming convention (cp-frontend/backend/health, pp-frontend/backend/health, plant-backend/health)

#### Terraform Modules (2 files)

4. **`cloud/terraform/modules/networking/main.tf`**
   - Update NEG creation to handle 8 services with new naming pattern (waooaw-{component}-{type}-neg-{env})

5. **`cloud/terraform/modules/load-balancer/main.tf`**
   - Replace 3-component routing (api/customer/platform) with new routing (cp/pp/plant domains), add /health path rules for health services, update SSL certificate resources to use new domain structure, add IAM bindings for CP/PP backends to invoke Plant backend

6. **`cloud/terraform/modules/load-balancer/variables.tf`**
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
