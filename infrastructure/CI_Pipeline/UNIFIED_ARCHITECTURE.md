# Unified Multi-Component Platform Architecture

## System Overview

WAOOAW is now configured as a **unified multi-component platform** with:
1. **Flexible component selection** (CP, PP, Plant)
2. **Conditional Terraform deployment** (only deploy selected components)
3. **Automatic enable flag management** (pipeline tells Terraform what to deploy)

```
┌─────────────────────────────────────────────────────────────┐
│                 GitHub Actions Workflow                    │
│                  cp-pipeline.yml                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: target_components (cp|pp|plant|all)                │
│         target_environment (demo|uat|prod)                 │
│         ⬇️                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  validate-components                                │  │
│  │  ✓ Check component paths exist                      │  │
│  │  ✓ Set build_cp, build_pp, build_plant flags       │  │
│  │  ✓ Set enable_backend_api/customer_portal/platform │  │
│  │    portal Terraform flags                           │  │
│  └──────────────────────────────────────────────────────┘  │
│         ⬇️ (outputs: build_*, enable_*)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Conditional Test Jobs (if build_cp=true)          │  │
│  │  ├─ backend-test (src/CP/BackEnd)                   │  │
│  │  ├─ frontend-test (src/CP/FrontEnd)                │  │
│  │  ├─ backend-security                               │  │
│  │  └─ frontend-security                              │  │
│  └──────────────────────────────────────────────────────┘  │
│         ⬇️                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  build-images (if build_images=true)               │  │
│  │  └─ Docker build & push: cp-backend, cp            │  │
│  │     (Only builds what's needed)                     │  │
│  └──────────────────────────────────────────────────────┘  │
│         ⬇️                                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  terraform-deploy (if deploy_to_gcp=true)          │  │
│  │  ├─ Auth to GCP                                     │  │
│  │  ├─ Update tfvars with enable_* flags              │  │
│  │  ├─ terraform plan (show what will deploy)         │  │
│  │  ├─ terraform apply (deploy only enabled services) │  │
│  │  └─ Smoke tests on deployed services               │  │
│  └──────────────────────────────────────────────────────┘  │
│         ⬇️                                                   │
│  GCP Cloud Run (only enabled services deployed)            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Customer Portal (CP) - ✅ Ready
```
Source Code:
  src/CP/
  ├── BackEnd/
  │   ├── api/          (FastAPI routes)
  │   ├── core/         (business logic)
  │   ├── models/       (data models)
  │   ├── Dockerfile
  │   └── requirements.txt
  └── FrontEnd/
      ├── src/          (React components)
      ├── Dockerfile
      └── package.json

Pipeline Artifacts:
  Docker Images:
    ├── asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend:demo
    └── asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp:demo

Cloud Run Services:
  ├── api-demo (backend, runs cp-backend image)
  └── portal-demo (frontend, runs cp image)

Infrastructure (Terraform):
  ├── enable_backend_api = true     (if CP selected)
  ├── enable_customer_portal = true (if CP selected)
  └── enable_platform_portal = false (unless PP selected)

DNS/Load Balancer:
  ├── api.waooaw.com → api-demo (Cloud Run)
  └── waooaw.com → portal-demo (Cloud Run)
```

### Platform Portal (PP) - ⏳ To Be Implemented
```
Expected Structure (when created):
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

When Pipeline Detects (target_components=pp):
  Docker Images:
    ├── asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp-backend:demo
    └── asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/pp:demo

Cloud Run Services:
  ├── platform-api-demo (backend, runs pp-backend image)
  └── platform-portal-demo (frontend, runs pp image)

Infrastructure (Terraform):
  ├── enable_backend_api = false            (PP uses separate backend)
  ├── enable_customer_portal = false        (unless CP also selected)
  └── enable_platform_portal = true         (if PP selected)

DNS/Load Balancer:
  ├── platform-api.waooaw.com → platform-api-demo (Cloud Run)
  └── platform.waooaw.com → platform-portal-demo (Cloud Run)
```

### Plant (Agent Core) - ⏳ To Be Implemented
```
Expected Structure (when created):
  src/Plant/
  ├── api/
  ├── agents/
  ├── core/
  ├── Dockerfile
  └── requirements.txt

When Pipeline Detects (target_components=plant):
  Docker Images:
    └── asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/plant:demo

Cloud Run Services:
  └── plant-api-demo (runs plant image)

Infrastructure (Terraform):
  ├── enable_backend_api = false (unless CP also selected)
  ├── enable_customer_portal = false (unless CP also selected)
  └── enable_platform_portal = false (unless PP also selected)

DNS/Load Balancer:
  └── plant-api.waooaw.com → plant-api-demo (Cloud Run)
```

## Deployment Scenarios

### Scenario 1: Deploy CP Only (Current Default)
```
Workflow Input:
  target_components = "cp"
  deploy_to_gcp = true
  target_environment = "demo"
  terraform_action = "apply"

Pipeline Actions:
  ✅ Tests: backend-test + frontend-test
  ✅ Builds: cp-backend + cp Docker images
  ✅ Terraform: enable_backend_api=true, enable_customer_portal=true, enable_platform_portal=false

GCP State After Apply:
  ├─ api-demo (backend) - CREATED
  ├─ portal-demo (frontend) - CREATED
  └─ platform-portal-demo - NOT CREATED (enable=false)

URLs Available:
  ├─ api.waooaw.com (backend API)
  └─ waooaw.com (customer portal)
```

### Scenario 2: Deploy CP to Prod, PP to UAT Demo
```
Run 1: CP to Production
  target_components = "cp"
  deploy_to_gcp = true
  target_environment = "prod"
  terraform_action = "apply"

Run 2: PP to UAT (Plan Only, No Apply)
  target_components = "pp"
  deploy_to_gcp = true
  target_environment = "uat"
  terraform_action = "plan"  # Just see what would deploy

Result:
  ├─ Production: CP deployed (2 services)
  ├─ UAT: Terraform plan shows 2 services for PP
  └─ PP not actually deployed (plan only)
```

### Scenario 3: Deploy CP + Plant Together
```
Workflow Input:
  target_components = "cp,plant"
  deploy_to_gcp = true
  target_environment = "demo"
  terraform_action = "apply"

Pipeline Actions:
  ✅ Tests: CP backend + frontend tests (Plant tests if it has them)
  ✅ Builds: cp-backend + cp + plant Docker images
  ✅ Terraform: enable_backend_api=true, enable_customer_portal=true, enable_platform_portal=false

GCP State After Apply:
  ├─ api-demo (CP backend) - CREATED
  ├─ portal-demo (CP frontend) - CREATED
  ├─ plant-api-demo (Plant core) - CREATED
  └─ platform-portal-demo - NOT CREATED (enable=false)

URLs Available:
  ├─ api.waooaw.com (CP backend)
  ├─ waooaw.com (CP portal)
  └─ plant-api.waooaw.com (Plant API)
```

### Scenario 4: Deploy All Components
```
Workflow Input:
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
