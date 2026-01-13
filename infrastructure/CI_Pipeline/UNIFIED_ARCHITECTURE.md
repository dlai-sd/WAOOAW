# WAOOAW Unified Architecture (Cost-Optimized, Terraform-Driven)

**Last Updated**: January 13, 2026

## What we want
- **One static IP + one HTTPS load balancer** (cost constraint).
- **Terraform-driven provisioning** (pipeline creates CP demo infra cleanly).
- **Code-only deploys most days** (CP frontend/backend image updates only).
- Later: deploy **PP/Plant independently** without accidentally changing CP.

## Core approach

### Single entrypoint (cost-friendly)
- One global IP
- One HTTPS LB
- SSL: **grouped SAN managed cert** for all hostnames initially; keep the option to move to **one managed cert per hostname** later as environments grow.
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
- `foundation/default.tfstate`
- `env/demo/cp/default.tfstate`
- `env/demo/pp/default.tfstate`
- `env/demo/plant/default.tfstate`

Why this works:
- Deploying PP does not touch CP *state*.
- Deploying CP day-to-day does not touch foundation (LB/certs).

## Deployment modes

### 1) Foundation bootstrap (rare)
**CRITICAL ORDER (Chicken-and-Egg Prevention):**
1. **Deploy app stack FIRST** (e.g., `waooaw-deploy.yml` for PP)
   - Creates Cloud Run services + NEGs
   - Writes `backend_negs` output to remote state at `env/demo/pp/default.tfstate`
2. **Enable in foundation SECOND** (set `enable_pp = true` in `default.tfvars`)
3. **Apply foundation THIRD** (`waooaw-foundation-deploy.yml`)
   - Reads NEG names from app stack remote state
   - Adds host rules to LB + extends SSL cert
4. **DNS** points to the single static IP
5. **SSL** becomes ACTIVE asynchronously (15-60 min)

**Why this order:** Foundation reads `data.terraform_remote_state.<stack>.outputs.backend_negs`. If you enable before the app stack exists, foundation plan fails with "object has no attribute backend_negs".

### 2) App deploy (common)
- CI runs all tests/scans.
- CD builds & pushes images (always auto-tagged).
- Terraform plan → apply updates only the app stack (no LB changes).

### 3) Routing expansion (occasional)
- When PP/Plant are introduced, update foundation routing/certs once.
- App stacks remain isolated.

## Guardrails (non-negotiable)
- No `terraform -target` in CI.
- CI must be reproducible (do not edit committed `*.tfvars` files).
- Lock concurrency per `env + stack`.
- No Terraform planfile artifacts between jobs (avoid brittle artifact wiring).
- Apply runs `terraform plan` (visibility) then `terraform apply` against remote state.
- **Frontend container images must match the CP pattern**: static `listen 8080` nginx, no runtime `envsubst`, no dynamic PORT templating. Cloud Run sets `PORT=8080` by default and the CP image pattern is proven. Reuse the same Dockerfile/nginx.conf for PP and Plant to avoid startup failures.
- **Cloud Run module must explicitly set PORT environment variable** (critical for startup probe): The `cloud-run` Terraform module sets `PORT=<port>` as an environment variable on all services. This is required because Cloud Run startup probes check if the container listens on the PORT env var; if PORT is not set, startup probes fail with "HEALTH_CHECK_CONTAINER_ERROR".

---

## CI/CD Pipeline Design (Best Practice, Minimal Inputs)

### Goals
- Reusable for **CP**, **PP**, and **Plant** across **demo/uat/prod**.
- **No user toggles** to skip tests, skip builds, or override tags.
- The only operator choice is **plan vs apply**.
- Keep workflow logic readable (avoid condition mazes).

### Recommended Structure (clean separation)

1) **CI workflow (always)**
- Triggers: PRs + pushes to `main`.
- Runs: lint/typecheck/unit/integration/security + UI tests where applicable.
- Builds: Docker images (always) to validate Dockerfiles.
- Does **not** deploy.

2) **CD workflow (deploy)**
- Triggers: manual dispatch, or automatic on successful CI for `main`.
- Inputs (only):
  - `environment`: `demo | uat | prod`
  - `terraform_action`: `plan | apply`
- Runs: build & push images (always), then terraform plan → apply (if requested).

### Reuse Across 3 Apps (no “component selection” input)
Use **one unified deploy workflow** plus a separate foundation workflow:

- `waooaw-deploy.yml` (apps)
  - Detects which components are deployable by checking for Dockerfiles.
  - Builds/pushes images + plans/applies only the stacks that exist.
  - Inputs remain minimal: `environment` + `terraform_action`.
- `waooaw-foundation-deploy.yml` (shared LB)
  - Plans/applies the shared LB + cert + routing.
  - Changes should be rare and controlled (single shared entrypoint).
  - Apply path includes `terraform fmt -check` and `terraform validate` gates (same as plan).
  - HTTPS proxy is managed by Terraform without ignoring `ssl_certificates` changes (safer cert rotation / domain expansion).

Additive workflows (do not deploy):
- `waooaw-ci.yml`
  - Runs on PRs and pushes to `main`.
  - Terraform `fmt -check` + `validate` and Docker build smoke checks (no push).
- `waooaw-drift.yml`
  - Scheduled + manual drift checks using `terraform plan -detailed-exitcode`.
  - Currently plans `foundation` + `cp` for the selected environment.

CP-focused entrypoints (manual, optional):
- `cp-pipeline.yml`
  - CP-only safe update: build/push CP images, terraform plan/apply for one env, quick LB smoke.
- `cp-pipeline-advanced.yml`
  - Advanced/preset-driven CP/PP/Plant deployer with toggles for tests/scans, LB updates, and optional cleanup.

**Demo deploy quick pick:** Use `waooaw-deploy.yml` with `environment: demo` and `terraform_action: apply` to push code to the demo stack (builds/pushes images, applies app stacks). If you only need a CP-only fast path without LB changes, run `cp-pipeline.yml` with `target_environment: demo` and `image_tag: auto`.

### Tagging (always auto)
- Use a deterministic tag per deploy: `\<env\>-\<short_sha\>-\<run_number\>`.
- Optionally also push `\<env\>-latest` for convenience.

### Environment Configuration (GitHub Environments)
- Environment name maps 1:1: `demo`, `uat`, `prod`.
- Store app config as Environment vars/secrets.
  - CP/PP frontend requires `GOOGLE_OAUTH_CLIENT_ID` to set `VITE_GOOGLE_CLIENT_ID` at build-time.
  - Plant does not require OAuth build args.

### Terraform
- Remote state lives in a GCS bucket with prefixes: `env/<env>/<stack>/default.tfstate`.
- Deploy workflows do not pass planfiles/artifacts; apply runs against the remote backend state.
- Concurrency lock by: `env + stack`.

Foundation bootstrap note:
- The foundation stack reads app stack outputs via `terraform_remote_state`.
- To support demo-first bootstrapping, foundation routing is gated by `enabled_environments` (default: `demo`).

### Sanity Checks
- Remove “terraform sanity plan all envs” from the deploy workflow.
- Keep any terraform formatting/validate steps as part of CI.

---

## Recommended Add-Ons (Low/No Infra Cost)

### 1) OIDC to GCP (replace service account JSON keys)
- Use GitHub OIDC → GCP Workload Identity Federation for auth.
- Outcome: no long-lived `GCP_SA_KEY` secrets; lower breach risk.
- Cost: no meaningful GCP cost; minimal setup effort.

Current status:
- The foundation workflow supports WIF when repo variables are configured:
  - `GCP_WORKLOAD_IDENTITY_PROVIDER`
  - `GCP_SERVICE_ACCOUNT_EMAIL`
- If those are not set, it safely falls back to `secrets.GCP_SA_KEY` (existing behavior).

- The app deploy workflow (`waooaw-deploy.yml`) supports the same optional WIF auth with the same JSON fallback.

### 2) Terraform Drift Detection (separate from deploy)
- Scheduled workflow runs `terraform plan` for `demo/uat/prod` and alerts on drift.
- Keeps the deploy workflow clean and deterministic.
- Cost: small CI minutes; no additional GCP infra.

### 3) SBOM + Image Signing (supply chain hardening)
- Generate SBOM per image and sign images/provenance (e.g., cosign/SLSA).
- Cost: small CI time; no additional infra.

### 4) Promotion Flow (demo → uat → prod)
- Promote the same built image tag across environments with approvals.
- Cost: no infra; reduces production risk.

### 5) Rollback (one-click)
- Keep a “last-known-good” tag per env and allow apply to pin services back.
- Cost: no infra; faster recovery.

---

---

## Critical Debugging Notes (Jan 13, 2026)

### PP Frontend Deployment Failures (Root Causes & Fixes)

**Symptom**: Cloud Run startup probe fails with `HEALTH_CHECK_CONTAINER_ERROR` for PP frontend service. Terraform apply shows "module.pp_frontend...Creation complete" but Cloud Run status shows "RoutesReady=False, ConfigurationsReady=False, Ready=False" with message "The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable within the allocated timeout."

**Root Cause #1: Incomplete nginx.conf**
- **Finding**: PP's nginx.conf was truncated, missing closing braces (`}`) and the `/health` endpoint.
- **Effect**: nginx failed config validation at startup, never bound to port 8080.
- **Fix**: Ensured PP nginx.conf matches CP nginx.conf exactly (static `listen 8080;`, health endpoint, proper closing braces).
- **Validation**: `diff -u src/CP/FrontEnd/nginx.conf src/PP/FrontEnd/nginx.conf` → no diff.
- **Commit**: `7c5f09d` "fix(pp): complete nginx.conf with closing braces and health check endpoint"

**Root Cause #2: Missing PORT Environment Variable in Terraform Module**
- **Finding**: The `cloud-run` Terraform module (used by all app stacks) was NOT setting the `PORT` environment variable on Cloud Run services. It set `container_port = var.port` in the container spec but did not add `PORT=<port>` as an environment variable.
- **Effect**: Cloud Run startup probe checks if container listens on `${PORT}` env var. If PORT is undefined, the probe defaults to checking port 8080 directly, but without the environment variable explicitly set, nginx and other services lack clear port binding instruction.
- **Fix**: Added static `env { name = "PORT"; value = tostring(var.port) }` block to the `cloud-run` module's template.containers before the dynamic env_vars loop. This ensures every Cloud Run service receives `PORT=<configured-port>` (e.g., `PORT=8080` for frontend, `PORT=8000` for backend).
- **Impact**: Applied to ALL app stacks (CP, PP, Plant) immediately.
- **Commit**: `ea20f48` "fix(terraform): explicitly set PORT env var in cloud-run module"

**Validation Steps**
1. Verify nginx.conf syntax: `nginx -t -c <path>` (local Docker test).
2. Check Terraform module: grep for `PORT.*=` in cloud-run/main.tf (must have explicit env block).
3. Cloud Run logs: Look for "tcpSocket on port 8080" in startup conditions (healthy).

---

---

### Pattern
`waooaw-<app>-<role>-<env>`

### Examples
- CP frontend: `waooaw-cp-frontend-demo`
- CP backend: `waooaw-cp-backend-demo`
- PP frontend: `waooaw-pp-frontend-uat`
- Plant API: `waooaw-plant-backend-prod`

## Terraform State Management (GCS)

- One bucket, multiple prefixes.
- Prefix scheme: `env/<env>/<stack>/default.tfstate`.

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

## Summary

This architecture stays cost-optimized (single LB/IP) while keeping deployments safe and maintainable:
- Isolation: state split by `env + stack`.
- Reuse: one reusable CI/CD pattern, three thin app entrypoints.
- Reliability: mandatory tests and mandatory builds; deploy is only plan/apply.

---

## PP Demo Deployment - Complete Process (Jan 13, 2026)

### Overview
Successfully deployed Platform Portal (PP) to demo environment following the documented bootstrap sequence. This section captures the actual steps taken, issues encountered, and resolutions applied.

### Prerequisites Completed
- ✅ PP frontend scaffolding (React + Fluent UI + OAuth shell)
- ✅ PP backend scaffolding (FastAPI on port 8015)
- ✅ PP Dockerfiles (FrontEnd: Node→Nginx, BackEnd: Python→Uvicorn)
- ✅ PP Terraform stack (`cloud/terraform/stacks/pp/`)
- ✅ PP environment tfvars (demo/uat/prod)

### Step-by-Step Deployment Process

#### Phase 1: Deploy PP App Stack
**Workflow**: `waooaw-deploy.yml` with `environment=demo`, `terraform_action=apply`

**Actions:**
1. CI detects PP Dockerfiles → builds both FrontEnd and BackEnd images
2. Pushes images to GCP Artifact Registry with tag `demo-<commit>-<run>`
3. Terraform init with remote state: `env/demo/pp/default.tfstate`
4. Terraform apply creates:
   - `waooaw-pp-frontend-demo` (Cloud Run service)
   - `waooaw-pp-backend-demo` (Cloud Run service)
   - NEGs (Network Endpoint Groups) for both services
5. Outputs `backend_negs` to remote state for foundation consumption

**Issue Encountered**: PP frontend container failed startup with `HEALTH_CHECK_CONTAINER_ERROR`

**Root Cause**: PP's `nginx.conf` was incomplete - missing closing braces and `/health` endpoint

**Resolution**: 
- Fixed nginx.conf to match CP exactly (commit `7c5f09d`)
- Cloud Run automatically provides `PORT=8080` env var (no manual setting needed)
- **Critical learning**: Cloud Run reserves `PORT` env var - do NOT set it explicitly in Terraform

**Result**: ✅ PP app stack deployed successfully (Run #14, Jan 13 15:24:48 UTC)

#### Phase 2: Enable PP in Foundation
**File**: `cloud/terraform/stacks/foundation/environments/default.tfvars`

**Change**: Set `enable_pp = true` (commit `0e8fb84`)

**Purpose**: Signals foundation to include PP in routing configuration

#### Phase 3: Deploy Foundation with PP Routing
**Workflow**: `waooaw-foundation-deploy.yml` with `environment=demo`, `terraform_action=apply`

**Issue Encountered**: SSL certificate creation failed with error 409 "resource already exists"

**Root Cause**: 
- SSL cert has static name `"waooaw-shared-ssl"`
- When domains change (adding PP), Terraform marks cert for replacement
- `lifecycle { create_before_destroy = true }` tries to create new cert with same name → collision

**Resolution**: Dynamic SSL cert naming with domain hash (commit `0f61f41`)
```hcl
locals {
  domain_hash = substr(md5(join(",", sort(local.all_domains))), 0, 8)
}

resource "google_compute_managed_ssl_certificate" "shared" {
  name = "waooaw-shared-ssl-${local.domain_hash}"
  # ...
}
```

**What Changed**:
- Old cert: `waooaw-shared-ssl` (CP domains only)
- New cert: `waooaw-shared-ssl-779b788b` (CP + PP domains)
- Zero downtime: New cert created → HTTPS proxy swapped → old cert deleted

**Result**: ✅ Foundation deployed successfully (Run #5, Jan 13 15:57:06 UTC)
- Added PP backend services to LB
- Created new SSL cert with `cp.demo.waooaw.com` + `pp.demo.waooaw.com`
- URL map now routes `pp.demo.waooaw.com` to PP frontend/backend

### Final State
- **PP Frontend**: `https://waooaw-pp-frontend-demo-<id>.a.run.app` (direct Cloud Run URL)
- **PP Backend**: `https://waooaw-pp-backend-demo-<id>.a.run.app` (direct Cloud Run URL)
- **PP via LB**: `https://pp.demo.waooaw.com` (routes through shared LB on 35.190.6.91)
- **SSL Certificate**: `waooaw-shared-ssl-779b788b` (provisioning 15-60 min for ACTIVE status)
- **Infrastructure**: 1 added, 1 changed, 1 destroyed (cert replacement)

### Key Learnings
1. **nginx.conf completeness is critical** - missing closing braces causes silent startup failure
2. **Cloud Run PORT env var is reserved** - do not set it manually; Cloud Run provides it automatically
3. **SSL cert replacement requires dynamic naming** - static names cause 409 conflicts with `create_before_destroy`
4. **Bootstrap sequence must be followed** - app stack first, then foundation enable/apply
5. **Workflow detects all components automatically** - no manual toggles needed if Dockerfiles exist

### Time to Deploy
- PP app stack: ~6 minutes (image build + terraform apply)
- Foundation update: ~3 minutes (terraform apply with cert replacement)
- SSL provisioning: 15-60 minutes (asynchronous, no downtime)
- **Total active deployment time**: ~10 minutes
