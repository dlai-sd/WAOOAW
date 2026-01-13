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
- Apply an app stack first (so remote state + NEGs exist), then Terraform apply `foundation`.
- DNS points to the single static IP.
- Managed SSL becomes ACTIVE asynchronously.

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

## Service Naming Convention

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
