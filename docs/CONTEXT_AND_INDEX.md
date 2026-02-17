# WAOOAW — Context & Indexing Reference

**Version**: 1.0  
**Date**: 2026-02-17  
**Purpose**: Single-source context document for any AI agent (including lower-cost models) to efficiently navigate, understand, and modify the WAOOAW codebase.  
**Update cadence**: Section 12 ("Latest Changes") should be refreshed daily.

---

## Table of Contents

1. [Problem Statement & Vision](#1-problem-statement--vision)
2. [Solution Hypothesis](#2-solution-hypothesis)
3. [Constitutional Design Pattern](#3-constitutional-design-pattern)
4. [Four Major Components](#4-four-major-components)
5. [Architecture & Technical Stack](#5-architecture--technical-stack)
6. [Service Communication & Data Flow](#6-service-communication--data-flow)
7. [Development ALM — Workflows & PRs](#7-development-alm--workflows--prs)
8. [Deployment Pipeline](#8-deployment-pipeline)
9. [GCP, Secrets & Terraform](#9-gcp-secrets--terraform)
10. [Database — Local, Demo, UAT, Prod](#10-database--local-demo-uat-prod)
11. [Testing Strategy](#11-testing-strategy)
12. [Latest Changes & Recent PRs](#12-latest-changes--recent-prs)
13. [Code File Index](#13-code-file-index)
14. [Environment Variables Quick Reference](#14-environment-variables-quick-reference)
15. [Port Map](#15-port-map)
16. [Common Tasks Cheat Sheet](#16-common-tasks-cheat-sheet)
17. [Gotchas & Tribal Knowledge](#17-gotchas--tribal-knowledge)
18. [Free Model Selection Guide](#18-free-model-selection-guide)
19. [Agent Working Instructions — Epic & Story Execution](#19-agent-working-instructions--epic--story-execution)
20. [Secrets Lifecycle & Flow](#20-secrets-lifecycle--flow)
21. [CLI Reference — Git, GCP, Debugging](#21-cli-reference--git-gcp-debugging)

---

## 1. Problem Statement & Vision

| Dimension | Detail |
|-----------|--------|
| **Problem** | Businesses want to use AI agents but face high risk — they pay upfront with no proof of value, can't compare options, and have no governance guardrails. |
| **Market gap** | No marketplace exists where AI agents *earn* business by delivering real work before payment; all current solutions are SaaS-first, tool-first, not talent-first. |
| **Vision** | WAOOAW ("WAH-oo-ah", a palindrome = quality from any angle) is the first AI agent marketplace where specialized agents demonstrate value in a 7-day free trial. Customers keep all deliverables even if they cancel. |
| **Tagline** | "Agents Earn Your Business" |
| **Business model** | 7-day free trial → monthly subscription (₹8K–18K/month). Agents across Marketing, Education, Sales. |
| **Differentiator** | Constitutional governance (single Governor, L0/L1 compliance), agent personality/status, marketplace DNA (browse, compare, hire like Upwork — not a SaaS landing page). |

---

## 2. Solution Hypothesis

> **If** we build a marketplace where AI agents deliver real, measurable work during a free trial with zero risk to the customer,  
> **and** every agent operates under constitutional governance with immutable audit trails,  
> **then** customers will convert at higher rates than traditional SaaS because they've already seen value,  
> **and** the platform will maintain trust through transparent, verifiable agent behavior.

### Key bets:

| Bet | Validation signal |
|-----|-------------------|
| Try-before-hire drives conversion | Trial-to-paid conversion rate > 30% |
| Constitutional governance builds trust | Zero policy violations in production |
| Marketplace UX beats SaaS landing pages | Higher engagement than feature-list pages |
| Single Governor model scales | One human can govern 19+ agents via automation |

---

## 3. Constitutional Design Pattern

WAOOAW uses a **two-layer constitutional framework** enforced at the data model level.

### L0 — Foundational Governance (applies to ALL entities)

| Code | Principle | Enforcement |
|------|-----------|-------------|
| L0-01 | Single Governor | `governance_agent_id` required on every entity |
| L0-02 | Amendment History | Append-only `amendment_history` JSON column |
| L0-03 | Immutable Audit | `hash_chain_sha256` links; no UPDATE to past |
| L0-04 | Supersession Chain | Entity evolution tracked via `evolution_markers` |
| L0-05 | Compliance Gate | `validate_self()` must pass before persistence |
| L0-06 | Version Control | Hash-based `version_hash` on every change |
| L0-07 | Signature Verification | RSA signature on amendments |

### L1 — Entity-Specific Rules

| Entity | Key rules |
|--------|-----------|
| Skill | Name + description required; category ∈ {technical, soft_skill, domain_expertise, certification} |
| JobRole | ≥1 required skill; seniority ∈ {junior, mid, senior} |
| Team | ≥1 agent; job_role_id set |
| Agent | skill_id + job_role_id + industry_id all required |
| Industry | Name required |

### Implementation files

| Purpose | File |
|---------|------|
| BaseEntity (7-section ORM) | `src/Plant/BackEnd/models/base_entity.py` |
| Constitutional validator | `src/Plant/BackEnd/validators/constitutional_validator.py` |
| Entity validator | `src/Plant/BackEnd/validators/entity_validator.py` |
| Hash chain | `src/Plant/BackEnd/security/hash_chain.py` |
| Cryptographic signatures | `src/Plant/BackEnd/security/cryptography.py` |
| Credential encryption | `src/Plant/BackEnd/security/credential_encryption.py` |

### BaseEntity 7 Sections

```
Section 1 — IDENTITY:                 id (UUID), entity_type, external_id
Section 2 — LIFECYCLE:                created_at, updated_at, deleted_at, status
Section 3 — VERSIONING:               version_hash, amendment_history, evolution_markers
Section 4 — CONSTITUTIONAL_ALIGNMENT: l0_compliance_status, amendment_alignment, drift_detector
Section 5 — AUDIT_TRAIL:              append_only, hash_chain_sha256, tamper_proof
Section 6 — METADATA:                 tags, custom_attributes, governance_notes
Section 7 — RELATIONSHIPS:            parent_id, child_ids, governance_agent_id
```

---

## 4. Four Major Components

### 4.1 Plant (Core Agent Platform)

| Aspect | Detail |
|--------|--------|
| **Role** | Central brain — agent factory, constitutional governance, data persistence, scheduling, metering |
| **Backend** | FastAPI on port 8001 (internal); Python 3.11+ |
| **Database** | PostgreSQL (asyncpg) — owns the single shared DB |
| **Key paths** | `src/Plant/BackEnd/` |
| **Entry point** | `src/Plant/BackEnd/main.py` (711 lines) |
| **API routes** | `src/Plant/BackEnd/api/v1/` — agents, customers, genesis, audit, hired_agents, invoices, payments, trials, marketing, notifications, scheduler, etc. |
| **Models** | `src/Plant/BackEnd/models/` — agent.py, customer.py, hired_agent.py, subscription.py, deliverable.py, trial.py, etc. |
| **Services** | `src/Plant/BackEnd/services/` — 30+ service files covering agent, customer, trial, notification, scheduler, metering, marketing, security |
| **Validators** | `src/Plant/BackEnd/validators/` — constitutional_validator.py, entity_validator.py |
| **Security** | `src/Plant/BackEnd/security/` — hash_chain.py, cryptography.py, credential_encryption.py |
| **Middleware** | `src/Plant/BackEnd/middleware/` — rate_limit, security_headers, input_validation, audit, correlation_id, error_handler |
| **Integrations** | `src/Plant/BackEnd/integrations/` — delta_exchange/ (trading), social/ (marketing) |
| **ML** | `src/Plant/BackEnd/ml/` — inference_client.py, embedding_cache/quality |
| **DB migrations** | `src/Plant/BackEnd/database/migrations/` (Alembic) |
| **Seeds** | `src/Plant/BackEnd/database/seeds/` — agent_type_definitions_seed.py |
| **Agent mold** | `src/Plant/BackEnd/agent_mold/` — playbooks for marketing/trading |

### 4.2 Plant Gateway

| Aspect | Detail |
|--------|--------|
| **Role** | API gateway — auth, RBAC, policy, budget, audit middleware; proxies to Plant Backend |
| **Backend** | FastAPI on port 8000 (public-facing) |
| **Key paths** | `src/Plant/Gateway/` |
| **Entry point** | `src/Plant/Gateway/main.py` (787 lines) |
| **Middleware stack** | auth.py → rbac.py → policy.py → budget.py → audit.py → error_handler.py |
| **Infrastructure** | `src/Plant/Gateway/infrastructure/` — feature_flags/ |
| **Pattern** | Receives requests from CP/PP → validates JWT → applies RBAC/policy → proxies to Plant Backend at port 8001 |

### 4.3 CP (Customer Portal)

| Aspect | Detail |
|--------|--------|
| **Role** | Customer-facing — browse agents, sign up, trial, hire, pay, manage subscriptions |
| **Backend** | FastAPI thin proxy on port 8020; routes auth/registration locally, proxies most API calls to Plant Gateway |
| **Frontend** | React 18 + TypeScript + Vite on port 3002→8080; dark-themed marketplace UI |
| **Key paths** | `src/CP/BackEnd/`, `src/CP/FrontEnd/` |
| **BE entry** | `src/CP/BackEnd/main.py` (245 lines) — thin proxy to Plant Gateway |
| **BE routes** | `src/CP/BackEnd/api/` — auth/, cp_registration.py, cp_otp.py, hire_wizard.py, payments_razorpay.py, trading.py, exchange_setup.py, subscriptions.py, invoices.py, receipts.py |
| **BE services** | `src/CP/BackEnd/services/` — auth_service.py, cp_registrations.py, cp_2fa.py, cp_otp.py, plant_gateway_client.py, trading_strategy.py |
| **FE pages** | `src/CP/FrontEnd/src/pages/` — LandingPage, AgentDiscovery, AgentDetail, SignIn, SignUp, HireSetupWizard, TrialDashboard, AuthenticatedPortal, HireReceipt |
| **FE services** | `src/CP/FrontEnd/src/services/` — 23 service files (auth, agents, trading, payments, subscriptions, etc.) |
| **FE components** | `src/CP/FrontEnd/src/components/` — AgentCard, Header, Footer, BookingModal, TrialStatusBanner, etc. |

### 4.4 PP (Platform Portal)

| Aspect | Detail |
|--------|--------|
| **Role** | Internal admin — governor console, genesis certification, agent management, customer management, audit, approvals |
| **Backend** | FastAPI thin proxy on port 8015; proxies to Plant Gateway |
| **Frontend** | React/Vite on port 3001→8080 |
| **Key paths** | `src/PP/BackEnd/`, `src/PP/FrontEnd/` |
| **BE entry** | `src/PP/BackEnd/main.py` → `main_proxy.py` |
| **BE routes** | `src/PP/BackEnd/api/` — genesis.py, agents.py, agent_types.py, agent_setups.py, approvals.py, audit.py, auth.py, db_updates.py, exchange_credentials.py, metering_debug.py, security.py |
| **FE pages** | `src/PP/FrontEnd/src/pages/` — Dashboard, GovernorConsole, GenesisConsole, AgentManagement, CustomerManagement, ReviewQueue, AuditConsole, PolicyDenials, HiredAgentsOps, AgentSetup, ReferenceAgents, etc. |

---

## 5. Architecture & Technical Stack

### High-level architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERNET                             │
│         cp.demo.waooaw.com    pp.demo.waooaw.com            │
└────────────────┬───────────────────┬────────────────────────┘
                 │                   │
         ┌───────▼───────┐   ┌──────▼────────┐
         │  CP Frontend  │   │  PP Frontend   │
         │  React/Vite   │   │  React/Vite    │
         │  :3002→8080   │   │  :3001→8080    │
         └───────┬───────┘   └──────┬─────────┘
                 │                   │
         ┌───────▼───────┐   ┌──────▼─────────┐
         │  CP Backend   │   │  PP Backend     │
         │  FastAPI:8020 │   │  FastAPI:8015   │
         │ (thin proxy)  │   │  (thin proxy)   │
         └───────┬───────┘   └──────┬──────────┘
                 │                   │
                 └────────┬──────────┘
                          │
                 ┌────────▼─────────┐
                 │  Plant Gateway   │
                 │  FastAPI:8000    │
                 │  Auth/RBAC/      │
                 │  Policy/Budget   │
                 └────────┬─────────┘
                          │
                 ┌────────▼─────────┐
                 │  Plant Backend   │
                 │  FastAPI:8001    │
                 │  Core business   │
                 │  logic + DB      │
                 └────────┬─────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
         ┌────▼───┐  ┌───▼────┐  ┌──▼───┐
         │Postgres│  │ Redis  │  │ GCP  │
         │ :5432  │  │ :6379  │  │ APIs │
         └────────┘  └────────┘  └──────┘
```

### Technology stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy (async), Alembic |
| Frontend | React 18, TypeScript, Vite, Vitest, Playwright |
| Database | PostgreSQL 15 (pgvector), asyncpg driver |
| Cache/Queue | Redis 7 |
| Auth | JWT (HS256 shared secret), Google OAuth2, OTP, 2FA (TOTP), Cloudflare Turnstile CAPTCHA |
| Payments | Razorpay |
| Trading | Delta Exchange integration |
| Infrastructure | Docker, Docker Compose, GCP Cloud Run, Terraform |
| CI/CD | GitHub Actions (8 workflow files) |
| Testing | pytest, Vitest, Playwright (E2E) |
| Monitoring | Structured logging, metrics middleware, observability module |
| Code quality | Black, ESLint, Prettier, yamllint |

---

## 6. Service Communication & Data Flow

### Request flow (CP example)

```
User browser → CP Frontend (React)
  → CP Backend (FastAPI :8020)
    → Plant Gateway (FastAPI :8000)  [JWT validation, RBAC, policy, budget check]
      → Plant Backend (FastAPI :8001) [business logic, DB access]
        → PostgreSQL / Redis / External APIs
```

### Key communication patterns

| Pattern | Detail |
|---------|--------|
| CP/PP → Gateway | HTTP proxy; CP/PP backends forward requests using `httpx` to `PLANT_GATEWAY_URL` |
| Gateway → Plant | HTTP proxy with identity token (GCP metadata server in Cloud Run, shared JWT in dev) |
| Gateway middleware order | Error handler → Auth → RBAC → Policy → Budget → Audit → Proxy |
| Auth flow | Google OAuth2 → JWT issued by CP/PP → validated at Gateway → forwarded to Plant |
| Registration flow | CP Backend `/api/register` → creates customer in local DB → calls Plant Gateway `/api/v1/customers` to create in Plant DB |
| CP registration key | Shared secret (`CP_REGISTRATION_KEY`) used between CP → Gateway to authorize customer upsert calls |

### Database ownership

- **Plant Backend** owns the single PostgreSQL database (`waooaw_db`)
- CP Backend has its own `user` table for auth (SQLite-like local or PostgreSQL)
- PP Backend proxies all data operations to Plant via Gateway
- All entity tables inherit from `BaseEntity` (7-section schema)

---

## 7. Development ALM — Workflows & PRs

### ALM lifecycle (autonomous agents)

The ALM is orchestrated by `.github/workflows/project-automation.yml` using GitHub Issues and Actions.

```
Epic created → Auto-Triage → Vision Guardian (7-part analysis)
  → BA Agent (5 user stories) + SA Agent (architecture)
    → Governor applies "go-coding" label (manual gate)
      → Code Agent (scripts/code_agent.py via GitHub Models API)
        → Test Agent (scripts/test_agent.py)
          → Deploy Agent (scripts/deploy_agent.py)
            → PR review & merge
```

### Key files

| File | Purpose |
|------|---------|
| `.github/workflows/project-automation.yml` | Main ALM orchestrator (2200+ lines) |
| `.github/ALM_FLOW.md` | Master reference document for ALM |
| `scripts/vision_guardian_agent.py` | VG analysis script |
| `scripts/business_analyst_agent.py` | BA story decomposition |
| `scripts/systems_architect_agent.py` | SA architecture analysis |
| `scripts/code_agent_aider.py` | Code generation agent |
| `scripts/test_agent.py` | Test generation agent |
| `scripts/deploy_agent.py` | Deployment manifest generation |

### PR workflow (manual development)

1. Create feature branch from `main` (e.g., `feat/skills-sk-1-1-skill-key`)
2. Implement changes, push branch
3. CI runs automatically on PR (`waooaw-ci.yml`)
4. Review, approve, merge to `main`
5. Deploy via `waooaw-deploy.yml` (manual dispatch)

### CI workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `waooaw-ci.yml` | PR + push to main | YAML validation, package-lock sync, lint, unit tests |
| `cp-pipeline.yml` | Manual dispatch | Full CP/PP/Plant build + test + optional GCP deploy |
| `cp-pipeline-advanced.yml` | Manual dispatch | Advanced pipeline variant |
| `waooaw-deploy.yml` | Manual dispatch | Deploy to demo/uat/prod (build images → Terraform plan/apply) |
| `waooaw-foundation-deploy.yml` | Manual dispatch | Foundation infra deployment |
| `plant-db-migrations-job.yml` | Manual dispatch | Run DB migrations on Cloud SQL |
| `plant-db-infra-reconcile.yml` | Manual dispatch | DB infrastructure reconciliation |
| `waooaw-drift.yml` | Scheduled/dispatch | Terraform drift detection |
| `project-automation.yml` | Issues/PRs/comments | ALM agent orchestration |

### Branch naming convention

```
feat/<scope>-<feature>        # New features
fix/<scope>-<description>     # Bug fixes
chore/<scope>-<description>   # Maintenance
debug/<description>           # Investigation branches
```

---

## 8. Deployment Pipeline

### GCP deployment flow (`waooaw-deploy.yml`)

```
1. Resolve image tag (SHA-short + run number)
2. Detect which components have Dockerfiles
3. Build Docker images (parallel: CP-BE, CP-FE, PP-BE, PP-FE, Plant-BE, Plant-GW)
4. Push to Artifact Registry (asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/)
5. Terraform plan (per environment)
6. Terraform apply (creates/updates Cloud Run services + LB)
```

### Component → Docker image mapping

| Component | Dockerfile | Image name |
|-----------|-----------|-----------|
| CP Backend | `src/CP/BackEnd/Dockerfile` | `cp-backend` |
| CP Frontend | `src/CP/FrontEnd/Dockerfile` | `cp` |
| PP Backend | `src/PP/BackEnd/Dockerfile` | `pp-backend` |
| PP Frontend | `src/PP/FrontEnd/Dockerfile` | `pp` |
| Plant Backend | `src/Plant/BackEnd/Dockerfile` | `plant-backend` |
| Plant Gateway | `src/Plant/Gateway/Dockerfile` | `plant-gateway` |
| CP Combined | `src/CP/Dockerfile.combined` | (BE+FE in one) |
| PP Combined | `src/PP/Dockerfile.combined` | (BE+FE in one) |

### Environments

| Environment | Domain (CP) | Domain (PP) | Scaling |
|-------------|-------------|-------------|---------|
| demo | cp.demo.waooaw.com | pp.demo.waooaw.com | min 0, max 2 (scale to zero) |
| uat | cp.uat.waooaw.com | pp.uat.waooaw.com | min 0, max 3 |
| prod | cp.waooaw.com | pp.waooaw.com | min 1, max 10 |

---

## 9. GCP, Secrets & Terraform

### GCP project

| Setting | Value |
|---------|-------|
| Project ID | `waooaw-oauth` |
| Region | `asia-south1` (Mumbai) |
| Artifact Registry | `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/` |
| Static IP | `waooaw-lb-ip` (shared across environments) |

### GCP services used

- **Cloud Run** — all 6 services (CP-BE, CP-FE, PP-BE, PP-FE, Plant-BE, Plant-GW)
- **Cloud SQL** — PostgreSQL 15 (connected via Cloud SQL Proxy / unix socket)
- **Cloud Load Balancer** — single IP, multi-domain routing (cp.*.waooaw.com, pp.*.waooaw.com)
- **Artifact Registry** — Docker image storage
- **Secret Manager** — GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET, CP_REGISTRATION_KEY, TURNSTILE_SECRET_KEY, etc.
- **VPC Connector** — private networking for Cloud Run → Cloud SQL
- **SSL managed certificates** — for custom domains

### Terraform structure

```
cloud/terraform/
├── main.tf              # Root module — Cloud Run services, networking, LB
├── variables.tf         # All input variables (project, region, images, domains, scaling)
├── outputs.tf           # Output values
├── environments/        # Per-env tfvars
├── modules/
│   ├── cloud-run/       # Cloud Run service module
│   ├── cloud-run-job/   # Cloud Run job (migrations)
│   ├── cloud-sql/       # Cloud SQL instance
│   ├── load-balancer/   # Global LB with URL map + SSL
│   ├── networking/      # NEGs for Cloud Run
│   └── vpc-connector/   # Serverless VPC connector
└── stacks/              # Modular stacks

cloud/terraform-lb/
├── main.tf              # Standalone LB configuration
└── variables.tf
```

### Single IP + Load Balancer architecture

```
Static IP (waooaw-lb-ip)
  → Global HTTPS Load Balancer
    → URL Map (host-based routing):
        cp.demo.waooaw.com  → CP Frontend NEG (Cloud Run)
        pp.demo.waooaw.com  → PP Frontend NEG (Cloud Run)
        /api/*              → Backend NEGs
    → SSL Certificate (managed)
```

### Secrets in GitHub

- Stored as GitHub repository secrets
- Used in workflows via `${{ secrets.GOOGLE_CLIENT_ID }}` etc.
- Key secrets: `GCP_SA_KEY` (service account JSON), `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_SECRET`, `CP_REGISTRATION_KEY`, `TURNSTILE_SECRET_KEY`

### Secrets in GCP

- Stored in GCP Secret Manager
- Referenced in Terraform as `secrets = { KEY = "SECRET_NAME:latest" }`
- Cloud Run services access them as environment variables
- Script to set: `scripts/set_gcp_secrets_cp_turnstile.sh`

> For full secrets lifecycle & flow diagram, see [Section 20 — Secrets Lifecycle & Flow](#20-secrets-lifecycle--flow).

---

## 10. Database — Local, Demo, UAT, Prod

### Connection strings by environment

| Environment | Connection | Driver |
|-------------|-----------|--------|
| Local (Docker) | `postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_db` | asyncpg |
| Local (no Docker) | `postgresql+asyncpg://waooaw:waooaw_dev_password@localhost:5432/waooaw_db` | asyncpg |
| Demo/UAT/Prod | Cloud SQL via unix socket or private IP (set via `DATABASE_URL` env) | asyncpg |

### Key database files

| File | Purpose |
|------|---------|
| `src/Plant/BackEnd/core/database.py` | Global async DB connector (engine, sessions, pooling) |
| `src/Plant/BackEnd/core/config.py` | Settings with DB URL validation |
| `src/Plant/BackEnd/database/init_db.py` | Table creation script |
| `src/Plant/BackEnd/database/seed_data.py` | Seed data loader |
| `src/Plant/BackEnd/database/seeds/` | Seed definitions (agent types) |
| `src/Plant/BackEnd/database/migrations/` | Alembic migrations |
| `src/Plant/BackEnd/alembic.ini` | Alembic config |
| `src/Plant/BackEnd/create_tables.py` | Direct table creation |
| `src/Plant/BackEnd/Dockerfile.migrations` | Migration runner Docker image |
| `infrastructure/database/` | DB infrastructure (migration SQL, tests) |
| `docker-compose.local.yml` | Local Postgres + pgvector container |

### How to test database locally

```bash
# 1. Start Postgres via Docker Compose
docker-compose -f docker-compose.local.yml up postgres -d

# 2. Run migrations
cd src/Plant/BackEnd
alembic upgrade head

# 3. Seed data
python -m database.seed_data

# 4. Run Plant backend (will auto-initialize DB)
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### How to run migrations on GCP

- Use workflow: `plant-db-migrations-job.yml` (dispatches a Cloud Run job)
- Or manually: build `Dockerfile.migrations`, push, run as Cloud Run job

### Database image

- Uses `pgvector/pgvector:pg15` (PostgreSQL 15 with pgvector extension)
- Extensions auto-loaded: `pgvector`, `uuid-ossp`

### Redis usage

| Service | Redis DB | Purpose |
|---------|----------|---------|
| Plant Backend | 0 | Cache, sessions |
| Plant Gateway | 1 | Rate limiting, policy cache |
| PP Backend | 2 | Cache |
| CP Backend | 3 | Sessions, OTP storage |

---

## 11. Testing Strategy

### ⚠️ MANDATORY RULE: Docker-only testing — NO venv

> **All tests MUST run inside Docker containers or Codespace (devcontainer).** Virtual environments (`venv`, `virtualenv`, `conda`) are **strictly prohibited**. This ensures parity with CI/CD and GCP Cloud Run.

### Test suite locations (detailed)

| Suite type | Component | Path | Framework | Docker service | What to add here |
|-----------|-----------|------|-----------|----------------|------------------|
| **Unit** | Plant Backend | `src/Plant/BackEnd/tests/unit/` (70+ files) | pytest | `plant-backend` | Model changes, service logic, validators |
| **Integration** | Plant Backend | `src/Plant/BackEnd/tests/integration/` | pytest | `plant-backend` + `postgres` | DB queries, cross-service calls |
| **E2E** | Plant Backend | `src/Plant/BackEnd/tests/e2e/` | pytest | Full stack | End-to-end API flows |
| **Security** | Plant Backend | `src/Plant/BackEnd/tests/security/` | pytest | `plant-backend` | Auth bypass, injection, secrets exposure |
| **Performance** | Plant Backend | `src/Plant/BackEnd/tests/performance/` | pytest | Full stack | Load, latency, throughput |
| **Middleware** | Plant Gateway | `src/Plant/Gateway/middleware/tests/` | pytest | `plant-gateway` | Auth, RBAC, policy, budget middleware |
| **Unit** | CP Backend | `src/CP/BackEnd/tests/` (35+ files) | pytest | `cp-backend` | Registration, OTP, auth, proxy routes |
| **Unit (UI)** | CP Frontend | `src/CP/FrontEnd/src/__tests__/` | Vitest | `cp-frontend-test` | Component rendering, hooks |
| **E2E (UI)** | CP Frontend | `src/CP/FrontEnd/e2e/` | Playwright | `cp-frontend-test` | Browser-based user journeys |
| **Unit (UI)** | PP Frontend | `src/PP/FrontEnd/src/pages/*.test.tsx` | Vitest | `pp-frontend-test` | Admin UI components |
| **Parity** | Gateway | `tests/test_gateway_middleware_parity.py` | pytest | Any | Gateway vs Plant middleware alignment |
| **Config** | Cross-service | `tests/test_local_compose_auth_config.py` | pytest | Any | Docker Compose auth config |
| **OpenAPI** | Cross-service | `tests/test_plant_gateway_openapi.py` | pytest | `plant-gateway` | OpenAPI spec validation |
| **Shared fixtures** | All | `tests/conftest.py` | pytest | — | Common test utilities |

### Docker-based test infrastructure

| File | Purpose |
|------|--------|
| `tests/docker-compose.test.yml` | Isolated test stack (postgres-test on :5433, redis-test on :6380) |
| `tests/Dockerfile.test` | Test runner image (Python 3.11 + git + test deps) |
| `tests/requirements.txt` | Test-specific Python dependencies |
| `docker-compose.local.yml` → `cp-frontend-test` | CP frontend test container (Vitest) |
| `docker-compose.local.yml` → `pp-frontend-test` | PP frontend test container (Vitest) |

### Running tests (Docker-only)

```bash
# --- Backend tests via Docker Compose ---
# Plant Backend unit tests
docker-compose -f docker-compose.local.yml exec plant-backend pytest tests/unit/ -v

# Plant Backend integration tests (needs postgres)
docker-compose -f docker-compose.local.yml exec plant-backend pytest tests/integration/ -v

# CP Backend tests
docker-compose -f docker-compose.local.yml exec cp-backend pytest tests/ -v

# Gateway middleware tests
docker-compose -f docker-compose.local.yml exec plant-gateway pytest middleware/tests/ -v

# --- Frontend tests via Docker ---
# CP Frontend (Vitest)
docker-compose -f docker-compose.local.yml run cp-frontend-test npx vitest run

# PP Frontend (Vitest)
docker-compose -f docker-compose.local.yml run pp-frontend-test npx vitest run

# CP E2E (Playwright)
docker-compose -f docker-compose.local.yml run cp-frontend-test npx playwright test

# --- Cross-service tests ---
docker-compose -f tests/docker-compose.test.yml up -d
docker-compose -f tests/docker-compose.test.yml run --rm test-runner pytest tests/ -v

# --- Or run directly in Codespace terminal (already Docker-based) ---
cd src/Plant/BackEnd && pytest tests/unit/ -v
cd src/CP/BackEnd && pytest tests/ -v
```

> **Note**: Codespaces run inside a devcontainer (Docker). Running `pytest` directly in a Codespace terminal is acceptable — it's already containerized. The prohibition is on creating local `venv`/`virtualenv`.

### Test requirement by change type

| What you changed | Required test suite | Path |
|-----------------|--------------------|----- |
| Plant model/service | Unit | `src/Plant/BackEnd/tests/unit/` |
| Plant API endpoint | Unit + Integration | `src/Plant/BackEnd/tests/unit/` + `tests/integration/` |
| Plant validator | Unit | `src/Plant/BackEnd/tests/unit/` |
| Gateway middleware | Unit | `src/Plant/Gateway/middleware/tests/` |
| CP Backend route | Unit | `src/CP/BackEnd/tests/` |
| CP Frontend component | UI Unit | `src/CP/FrontEnd/src/__tests__/` |
| CP Frontend page | UI Unit + E2E | `src/CP/FrontEnd/src/__tests__/` + `e2e/` |
| PP Frontend page | UI Unit | `src/PP/FrontEnd/src/pages/<Page>.test.tsx` |
| Cross-service behavior | Integration | `tests/` (root) |
| Terraform/infra | Manual verification | Document in story |
| Docker/compose | Config test | `tests/test_local_compose_auth_config.py` |

### Coverage

- Target: 80% overall, 90% critical paths
- Coverage reports: `htmlcov/` directories in each component
- Root coverage: `coverage.xml`, `htmlcov/`

---

## 12. Latest Changes & Recent PRs

> **⚠️ UPDATE THIS SECTION DAILY**

### Current branch: `fix/cp-registration-robustness-v2`

### Recent merged PRs (as of 2026-02-17)

| PR | Branch | Summary |
|----|--------|---------|
| #677 | fix/cp-registration-robustness-v2 | CP registration robustness improvements (latest merge to main) |
| #676 | fix/cp-registration-robustness-v2 | CP registration robustness (earlier iteration) |
| #675 | fix/cp-registration-robustness-v2 | CP registration robustness (earlier iteration) |
| #674 | fix/cp-registration-unique-identifiers | Reject duplicate email/phone registrations |
| #673 | fix/cp-frontend-marketplace-visuals-restore | Restore AgentCard visuals for marketplace |
| #672 | fix/cp-otp-delivery-mode-flags | Harden Plant gateway + CP upsert errors |
| #671 | fix/cp-otp-delivery-mode-flags | OTP delivery mode flag |
| #670 | fix/cp-turnstile-and-otp | Wire Turnstile env + retry widget |
| #669 | fix/cp-turnstile-and-otp | Turnstile + OTP fixes |
| #668 | fix/cp-turnstile-and-otp | Turnstile + OTP fixes |
| #667 | fix/cp-auth-captcha-nonblocking | Auth CAPTCHA non-blocking fix |
| #666 | feat/skills-sk-3-1-hire-skill-validation | Hire skill validation feature |

### Recent commit themes

- CP registration robustness (duplicate detection, OTP, 2FA, Turnstile CAPTCHA)
- CP frontend marketplace visual polish (hero banner, theme, agent cards)
- Terraform fixes (CP_REGISTRATION_KEY wiring, formatting)
- Country-based phone + GSTIN validation
- Plant gateway hardening

### Active feature branches

| Branch | Area |
|--------|------|
| fix/cp-registration-robustness-v2 | CP registration pipeline |
| feat/skills-sk-* (series) | Skills certification lifecycle (SK-1.1 through SK-3.1) |

---

## 13. Code File Index

### Root directory

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quick start, architecture |
| `docker-compose.local.yml` | Full local dev stack (Postgres, Redis, Plant, PP, CP, Gateway) |
| `pytest.ini` | Root pytest configuration |
| `.env.example` | Template for environment variables |
| `.env.docker` | Docker-specific env vars |
| `.env.gateway` | Gateway-specific env vars |
| `start-local-no-docker.sh` | Run services without Docker |
| `coverage.xml` | Test coverage report |

### src/Plant/BackEnd/ — Core Platform

#### Entry points
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app with all routes, middleware, exception handlers (711 lines) |
| `main_simple.py` | Simplified main for testing |

#### API routes (`api/v1/`)
| File | Endpoints |
|------|-----------|
| `router.py` | Central router aggregating all v1 routes |
| `agents.py` | Agent CRUD, catalog, search |
| `agents_simple.py` | Simplified agent endpoints |
| `agent_types_simple.py` | Agent type listing |
| `agent_types_db.py` | Agent types from database |
| `agent_mold.py` | Agent mold/template endpoints |
| `customers.py` | Customer registration, profile |
| `genesis.py` | Skill/JobRole certification (genesis flow) |
| `hired_agents_simple.py` | Hired agent management |
| `trial_status_simple.py` | Trial status endpoints |
| `audit.py` | Audit log endpoints |
| `auth.py` | Authentication endpoints |
| `invoices_simple.py` | Invoice generation |
| `payments_simple.py` | Payment processing |
| `receipts_simple.py` | Receipt management |
| `deliverables_simple.py` | Deliverable tracking |
| `marketing_drafts.py` | Marketing content drafts |
| `notifications.py` | Notification endpoints |
| `usage_events.py` | Usage event tracking |
| `reference_agents.py` | Reference agent catalog |
| `scheduler_admin.py` | Scheduler admin controls |
| `scheduler_health.py` | Scheduler health checks |
| `db_updates.py` | DB update endpoints |

#### Models (`models/`)
| File | Entity |
|------|--------|
| `base_entity.py` | BaseEntity (7-section, 543 lines) — parent of all entities |
| `agent.py` | Agent model |
| `agent_type.py` | AgentType model |
| `customer.py` | Customer model |
| `hired_agent.py` | HiredAgent model |
| `subscription.py` | Subscription model |
| `deliverable.py` | Deliverable model |
| `trial.py` | Trial model |
| `goal_run.py` | GoalRun model |
| `scheduled_goal_run.py` | ScheduledGoalRun model |
| `scheduler_dlq.py` | DeadLetterQueue model |
| `scheduler_state.py` | SchedulerState model |
| `industry.py` | Industry model |
| `job_role.py` | JobRole model |
| `skill.py` | Skill model |
| `team.py` | Team model |
| `schemas.py` | Pydantic schemas |

#### Services (`services/`)
| File | Purpose |
|------|---------|
| `agent_service.py` | Agent business logic |
| `agent_type_service.py` | Agent type management |
| `customer_service.py` | Customer operations |
| `trial_service.py` | Trial lifecycle management |
| `skill_service.py` | Skill certification logic |
| `job_role_service.py` | JobRole management |
| `audit_service.py` | Audit log service |
| `goal_scheduler_service.py` | Goal scheduling engine |
| `scheduler_admin_service.py` | Scheduler administration |
| `scheduler_dlq_service.py` | Dead letter queue handling |
| `scheduler_health_service.py` | Health monitoring |
| `scheduler_persistence_service.py` | State persistence |
| `idempotency_service.py` | Idempotency key management |
| `metering.py` | Usage metering |
| `plan_limits.py` | Subscription plan limits |
| `usage_events.py` | Usage event processing |
| `usage_ledger.py` | Usage ledger tracking |
| `notification_events.py` | Notification event processing |
| `notification_delivery_store.py` | Delivery tracking |
| `notification_email_templates.py` | Email templates |
| `notification_sms_templates.py` | SMS templates |
| `email_providers.py` | Email provider abstraction |
| `sms_providers.py` | SMS provider abstraction |
| `marketing_providers.py` | Social media providers |
| `marketing_scheduler.py` | Marketing post scheduling |
| `draft_batches.py` | Draft batch management |
| `credential_resolver.py` | Credential resolution |
| `social_credential_resolver.py` | Social media credentials |
| `security_audit.py` | Security audit logging |
| `security_throttle.py` | Rate throttling |
| `policy_denial_audit.py` | Policy denial tracking |

#### Core (`core/`)
| File | Purpose |
|------|---------|
| `config.py` | Pydantic settings (174 lines) |
| `database.py` | Async DB connector (306 lines) |
| `exceptions.py` | Custom exception hierarchy |
| `logging.py` | Structured logging setup |
| `metrics.py` | Prometheus-style metrics |
| `observability.py` | Observability setup |
| `security.py` | Security utilities |

#### Repositories (`repositories/`)
| File | Purpose |
|------|---------|
| `agent_type_repository.py` | AgentType data access |
| `deliverable_repository.py` | Deliverable data access |
| `hired_agent_repository.py` | HiredAgent data access |
| `subscription_repository.py` | Subscription data access |

### src/Plant/Gateway/ — API Gateway

| File | Purpose |
|------|---------|
| `main.py` | Gateway app with middleware stack + proxy (787 lines) |
| `middleware/auth.py` | JWT validation middleware |
| `middleware/rbac.py` | Role-based access control |
| `middleware/policy.py` | OPA policy enforcement |
| `middleware/budget.py` | Budget guard middleware |
| `middleware/audit.py` | Audit logging middleware |
| `middleware/error_handler.py` | RFC 7807 error responses |

### src/CP/BackEnd/ — Customer Portal Backend

| File | Purpose |
|------|---------|
| `main.py` | CP app — thin proxy to Plant Gateway (245 lines) |
| `core/config.py` | CP configuration |
| `core/database.py` | CP local database |
| `core/jwt_handler.py` | JWT token handling |
| `core/security.py` | Security utilities |
| `models/user.py` | User model |
| `models/user_db.py` | User DB operations |
| `api/auth/` | Auth routes (Google OAuth) |
| `api/cp_registration.py` | Customer registration endpoint |
| `api/cp_otp.py` | OTP verification |
| `api/hire_wizard.py` | Agent hiring flow |
| `api/payments_razorpay.py` | Razorpay payment integration |
| `api/exchange_setup.py` | Exchange configuration |
| `api/trading.py` | Trading endpoints |
| `api/subscriptions.py` | Subscription management |
| `api/invoices.py` | Invoice endpoints |
| `api/receipts.py` | Receipt endpoints |
| `services/auth_service.py` | Auth business logic |
| `services/cp_registrations.py` | Registration service |
| `services/cp_2fa.py` | Two-factor auth service |
| `services/cp_otp.py` | OTP service |
| `services/plant_gateway_client.py` | HTTP client to Plant Gateway |

### src/CP/FrontEnd/src/ — Customer Portal Frontend

| File | Purpose |
|------|---------|
| `App.tsx` | Root React component |
| `main.tsx` | Entry point |
| `theme.ts` | Design system tokens |
| `pages/LandingPage.tsx` | Marketplace landing page |
| `pages/AgentDiscovery.tsx` | Agent browsing/search |
| `pages/AgentDetail.tsx` | Individual agent view |
| `pages/SignIn.tsx` | Sign-in page |
| `pages/SignUp.tsx` | Registration page |
| `pages/HireSetupWizard.tsx` | Agent hiring wizard |
| `pages/TrialDashboard.tsx` | Trial management |
| `pages/AuthenticatedPortal.tsx` | Post-login portal |
| `pages/HireReceipt.tsx` | Hire confirmation |
| `components/AgentCard.tsx` | Agent card component |
| `components/Header.tsx` | Navigation header |
| `components/Footer.tsx` | Page footer |
| `components/BookingModal.tsx` | Booking modal |
| `services/auth.service.ts` | Auth API calls |
| `services/registration.service.ts` | Registration API calls |
| `services/hireWizard.service.ts` | Hire flow API calls |
| `services/plant.service.ts` | Plant API client |
| `services/agentTypes.service.ts` | Agent types API |
| `services/trading.service.ts` | Trading API calls |
| `config/` | App configuration |
| `context/` | React context providers |
| `hooks/` | Custom React hooks |
| `styles/` | CSS styles |
| `types/` | TypeScript type definitions |

### src/PP/ — Platform Portal

| File | Purpose |
|------|---------|
| `BackEnd/main.py` → `main_proxy.py` | PP app entry (thin proxy) |
| `BackEnd/api/genesis.py` | Genesis certification endpoints |
| `BackEnd/api/agents.py` | Agent management |
| `BackEnd/api/approvals.py` | Approval workflows |
| `BackEnd/api/audit.py` | Audit log access |
| `BackEnd/api/auth.py` | PP authentication |
| `FrontEnd/src/pages/Dashboard.tsx` | Admin dashboard |
| `FrontEnd/src/pages/GovernorConsole.tsx` | Governor control panel |
| `FrontEnd/src/pages/GenesisConsole.tsx` | Genesis certification UI |
| `FrontEnd/src/pages/AgentManagement.tsx` | Agent management UI |
| `FrontEnd/src/pages/CustomerManagement.tsx` | Customer management UI |
| `FrontEnd/src/pages/ReviewQueue.tsx` | Review/approval queue |
| `FrontEnd/src/pages/AuditConsole.tsx` | Audit log viewer |
| `FrontEnd/src/pages/PolicyDenials.tsx` | Policy denial viewer |

### .github/ — CI/CD & ALM

| File | Purpose |
|------|---------|
| `workflows/waooaw-ci.yml` | CI pipeline (lint, test, validate) |
| `workflows/waooaw-deploy.yml` | Deploy to GCP (build, push, terraform) |
| `workflows/cp-pipeline.yml` | Full CP/PP/Plant pipeline (1096 lines) |
| `workflows/cp-pipeline-advanced.yml` | Advanced pipeline variant |
| `workflows/project-automation.yml` | ALM agent orchestration |
| `workflows/plant-db-migrations-job.yml` | DB migration runner |
| `workflows/plant-db-infra-reconcile.yml` | DB infra reconciliation |
| `workflows/waooaw-drift.yml` | Terraform drift detection |
| `workflows/waooaw-foundation-deploy.yml` | Foundation infra |
| `ALM_FLOW.md` | ALM workflow documentation |
| `PROJECT_MANAGEMENT.md` | Project management guide |
| `copilot-instructions.md` | AI copilot instructions |

### scripts/ — Automation & Agent Scripts

| File | Purpose |
|------|---------|
| `vision_guardian_agent.py` | VG analysis (GitHub Models API) |
| `business_analyst_agent.py` | BA story decomposition |
| `systems_architect_agent.py` | SA architecture analysis |
| `code_agent_aider.py` | Code generation |
| `test_agent.py` | Test generation + pytest |
| `deploy_agent.py` | K8s/Terraform generation |
| `preflight_check.py` | Pre-deployment validation |
| `generate_test_report.py` | Test report generator |
| `validate_github_script_blocks.py` | Script validation |
| `deploy-gateway.sh` | Gateway deployment script |

### cloud/terraform/ — Infrastructure as Code

| File | Purpose |
|------|---------|
| `main.tf` | Root: Cloud Run + networking + LB (168 lines) |
| `variables.tf` | All input vars (144 lines) |
| `outputs.tf` | Output definitions |
| `modules/cloud-run/` | Cloud Run service module |
| `modules/cloud-run-job/` | Cloud Run job module (migrations) |
| `modules/cloud-sql/` | Cloud SQL module |
| `modules/load-balancer/` | Global LB module |
| `modules/networking/` | NEG module |
| `modules/vpc-connector/` | VPC connector module |
| `environments/` | Per-environment tfvars |

### tests/ — Cross-service tests

| File | Purpose |
|------|---------|
| `test_gateway_middleware_parity.py` | Gateway vs Plant middleware parity |
| `test_local_compose_auth_config.py` | Docker Compose auth config validation |
| `test_plant_gateway_openapi.py` | Plant Gateway OpenAPI spec tests |
| `conftest.py` | Shared test fixtures |

---

## 14. Environment Variables Quick Reference

| Variable | Used by | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | Plant, CP, PP | PostgreSQL connection string |
| `REDIS_URL` | All services | Redis connection |
| `JWT_SECRET` | All services | **MUST be identical** across CP, PP, Plant, Gateway |
| `GOOGLE_CLIENT_ID` | CP, PP, Gateway | Google OAuth2 client ID |
| `GOOGLE_CLIENT_SECRET` | Gateway, GCP | Google OAuth2 secret |
| `CP_REGISTRATION_KEY` | CP, Gateway | Shared secret for customer upsert authorization |
| `TURNSTILE_SITE_KEY` | CP Frontend | Cloudflare Turnstile CAPTCHA (public) |
| `TURNSTILE_SECRET_KEY` | CP Backend | Cloudflare Turnstile CAPTCHA (server) |
| `PLANT_GATEWAY_URL` | CP, PP | URL to Plant Gateway (default: http://localhost:8000) |
| `ENVIRONMENT` | All | development / demo / uat / prod |
| `ENABLE_DB_UPDATES` | Plant | Enable DB update endpoints |
| `GCP_PROJECT_ID` | Terraform, Plant | GCP project identifier |

---

## 15. Port Map

| Port | Service | Notes |
|------|---------|-------|
| 3001 | PP Frontend (dev) | Maps to 8080 internal |
| 3002 | CP Frontend (dev) | Maps to 8080 internal |
| 5432 | PostgreSQL | Shared database |
| 6379 | Redis | Shared cache/queue |
| 8000 | Plant Gateway | Public-facing API gateway |
| 8001 | Plant Backend | Internal only |
| 8015 | PP Backend | Internal |
| 8020 | CP Backend | Internal |
| 8081 | Adminer | DB admin UI |

---

## 16. Common Tasks Cheat Sheet

### Start full local stack
```bash
docker-compose -f docker-compose.local.yml up --build -d
```

### Start individual services
```bash
# Plant backend only
cd src/Plant/BackEnd && uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Gateway only
cd src/Plant/Gateway && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# CP backend only
cd src/CP/BackEnd && uvicorn main:app --host 0.0.0.0 --port 8020 --reload
```

### Run tests
```bash
# Plant backend tests
cd src/Plant/BackEnd && pytest tests/unit/ -v

# CP backend tests
cd src/CP/BackEnd && pytest tests/ -v

# CP frontend tests
cd src/CP/FrontEnd && npx vitest run

# All root-level cross-service tests
pytest tests/ -v
```

### Deploy to GCP
1. Go to GitHub Actions → "WAOOAW Deploy" → Run workflow
2. Select environment (demo/uat/prod)
3. Select terraform_action (plan first, then apply)

### Check service health
```bash
curl http://localhost:8001/health   # Plant Backend
curl http://localhost:8000/health   # Gateway
curl http://localhost:8020/health   # CP Backend
curl http://localhost:8015/health   # PP Backend
```

### Access API docs
```
http://localhost:8001/docs   # Plant Backend Swagger
http://localhost:8020/docs   # CP Backend Swagger
```

---

## 17. Gotchas & Tribal Knowledge

| Topic | Detail |
|-------|--------|
| JWT_SECRET sync | ALL services (CP, PP, Plant, Gateway) **must** use the exact same JWT_SECRET value. Mismatches cause silent 401 errors. |
| CP_REGISTRATION_KEY | Shared secret between CP Backend and Plant Gateway to authorize customer creation. Must be set in both services. |
| Database ownership | Only Plant Backend writes to the main DB. CP and PP proxy through Gateway. |
| CP is a thin proxy | CP Backend routes most requests to Plant Gateway via `httpx`. Only auth/registration/OTP is handled locally. |
| PP is a thin proxy | PP Backend delegates to `main_proxy.py` which proxies to Plant Gateway. |
| Gateway middleware order matters | Error handler → Auth → RBAC → Policy → Budget → Audit → Proxy. Changing order breaks security. |
| Alembic migrations | Run from `src/Plant/BackEnd/`. The `alembic.ini` file lives there. |
| pgvector | Database uses `pgvector/pgvector:pg15` image. Extensions auto-load on first connection. |
| Scale to zero | Demo/UAT Cloud Run services scale to 0 instances. First request has cold start (~5s). |
| Constitutional validators | Every entity MUST pass `validate_self()` before persistence. Violations raise `ConstitutionalAlignmentError`. |
| Agent mold playbooks | Agent behavior templates in `src/Plant/BackEnd/agent_mold/playbooks/`. Currently: marketing/multichannel_post_v1.md, trading/delta_futures_manual_v1.md. |
| GitHub Actions concurrency | ALM workflow uses concurrency groups (vg-$issue, ba-sa-$issue, testing-$epic, deploy-$epic) to prevent duplicates. |
| go-coding label | Governor must manually apply `go-coding` label to an epic before Code Agent can run — this is a deliberate human gate. |
| Docker compose profiles | Use `docker-compose.local.yml` for full local dev. No separate test/prod compose currently. |
| Redis DB assignments | Each service uses a different Redis DB (0-3). Don't share DB indices. |
| Codespace browser URLs | Use `https://${CODESPACE_NAME}-{PORT}.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/` format. |
| No docs without asking | AI agents must NOT auto-create documentation files — always ask user first. |

---

## 18. Free Model Selection Guide

> **INSTRUCTION TO AI AGENT**: When a user describes a task, you MUST consult this section and recommend the best free model BEFORE starting work. State the model name, why it's the best fit, and which sections of this document to include in context.

### Available free models

| Model | Access | Context window | Strengths | Monthly free limit |
|-------|--------|----------------|-----------|-------------------|
| **GPT-4o-mini** | GitHub Copilot Free tier (default) | 128K tokens | Fast, good at single-file edits, tests, small refactors, Q&A | 2,000 completions/month |
| **Claude 3.5 Sonnet** | GitHub Copilot Free tier (premium) | 200K tokens | Complex reasoning, multi-file changes, large context analysis, architecture decisions | 50 requests/month |
| **GitHub Models API** | `GITHUB_TOKEN` in Codespaces/Actions | Varies | Script-based automation, ALM agent tasks | Rate-limited (free) |

### Task → Model decision matrix

| Task type | Best model | Reason | Context sections to include |
|-----------|-----------|--------|----------------------------|
| Single file bug fix | GPT-4o-mini | Fast, low cost, sufficient for focused edits | 13 (relevant file only) + 17 |
| Add a new API endpoint | GPT-4o-mini | Follows existing patterns, one component at a time | 4 (relevant component) + 13 (relevant subsection) |
| Write unit tests | GPT-4o-mini | Pattern-based, reference existing tests | 11 + 13 (test files) |
| CSS/UI styling changes | GPT-4o-mini | Localized changes, theme tokens known | 4.3 or 4.4 (frontend section) |
| Fix environment/config issues | GPT-4o-mini | Lookup-based, reference env vars | 14 + 15 + 17 |
| Docker/compose changes | GPT-4o-mini | Focused, pattern-following | 5 + 15 |
| Multi-file refactor (2-5 files, same component) | GPT-4o-mini | If files are in the same component, mini handles it | 4 (component) + 13 (all affected files) |
| **Multi-component change** (CP + Gateway + Plant) | **Claude 3.5 Sonnet** | Needs to reason across service boundaries and communication flow | 4 + 5 + 6 + 13 (all affected) |
| **Architecture decision** | **Claude 3.5 Sonnet** | Requires deep understanding of trade-offs, constitutional compliance | 1-6 + 17 |
| **New feature spanning multiple services** | **Claude 3.5 Sonnet** | Cross-cutting concerns, needs full context | Full doc (fits in 200K) |
| **Debugging cross-service auth/JWT issues** | **Claude 3.5 Sonnet** | Must understand Gateway middleware stack, JWT flow, secret sync | 6 + 9 + 14 + 17 |
| **Terraform/GCP infrastructure changes** | **Claude 3.5 Sonnet** | Complex module dependencies, secret wiring, LB routing | 8 + 9 + 13 (terraform) |
| **Database migration + model change** | **Claude 3.5 Sonnet** | Must understand BaseEntity, constitutional validators, Alembic | 3 + 10 + 13 (models + DB) |
| **ALM workflow changes** | **Claude 3.5 Sonnet** | 2200+ line workflow, complex job chaining, concurrency | 7 + 13 (scripts + workflows) |
| **Constitutional validator changes** | **Claude 3.5 Sonnet** | Core design pattern, affects all entities | 3 + 13 (validators + models) |
| CI/CD pipeline tweaks | GPT-4o-mini | Usually single-file YAML edits | 7 + 8 |
| README/docs updates | GPT-4o-mini | Text editing, low complexity | Relevant section |
| Script automation | GitHub Models API | For ALM-triggered agent scripts | 7 + 13 (scripts) |

### Cost optimization rules

1. **Default to GPT-4o-mini** — it handles 85% of tasks at zero marginal cost
2. **Use Claude 3.5 Sonnet only when**: task touches 3+ files across 2+ components, OR requires architectural reasoning, OR involves the constitutional design pattern
3. **Never paste the full document into GPT-4o-mini** — only paste the sections listed in the "Context sections" column above
4. **Paste the full document into Claude 3.5 Sonnet** when doing cross-component work — it fits easily in 200K context
5. **Budget your 50 Claude requests/month**: ~2 per working day. Save them for complex tasks, use mini for everything else
6. **For repetitive similar tasks** (e.g., adding 5 similar endpoints): use Claude for the first one to establish the pattern, then GPT-4o-mini for the remaining 4

### How to use this guide (agent instruction)

When a user describes a task:

```
1. Classify the task using the decision matrix above
2. State: "Recommended model: [MODEL] because [REASON]"
3. State: "Include these context sections: [NUMBERS]"
4. If the task is ambiguous, default to GPT-4o-mini
5. If the user explicitly requests a different model, respect that
6. Track Claude usage — warn if approaching monthly limit
```

---

## 19. Agent Working Instructions — Epic & Story Execution

> **MANDATORY**: Every AI agent working on this codebase MUST follow these instructions when the user describes a feature, fix, or improvement.

### Step 1: Create Epic & Story Document

Before writing any code, **ask the user** to confirm the feature scope, then create a planning document.

**Document location**: `docs/epics/EPIC_<NUMBER>_<SHORT_NAME>.md`

**Document structure**:

```markdown
# Epic: <Title>

**Created**: <date>
**Branch**: <branch-name>
**Status**: In Progress

## Tracking Table

| # | Story | Status | Branch commit | Notes |
|---|-------|--------|---------------|-------|
| 1 | <story title> | 🔴 Not Started | — | — |
| 2 | <story title> | 🔴 Not Started | — | — |
| 3 | <story title> | 🔴 Not Started | — | — |

Status legend: 🔴 Not Started | 🟡 In Progress | 🔵 Dev Complete, Pending Testing | 🟢 Complete (tests pass)

## Story 1: <Title>
### Objective
<what this story achieves>
### Acceptance criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
### Files to modify
- `<path>` — <what changes>
### Files to create
- `<path>` — <purpose>
### Test requirements
- **Unit**: Add to `<test suite path>` — test <what>
- **Integration**: Add to `<test suite path>` — test <what>
- **UI**: Add to `<test suite path>` — test <what>
### Dependencies
- Depends on: Story <N> (if any)
- Blocked by: <nothing / description>

## Story 2: <Title>
...
```

### Step 2: Execute stories sequentially

1. **Mark story as 🟡 In Progress** in the tracking table
2. Implement the code changes described in the story
3. Add test cases to the **correct test suite** (see Section 11 for locations)
4. After code + tests written (but before running tests): **mark as 🔵 Dev Complete, Pending Testing**
5. Run tests via Docker (see Section 11 — Docker-only, NO venv)
6. When all tests pass: **mark as 🟢 Complete**
7. Commit and push to branch
8. Move to next story

### Step 3: Status updates & git

After each story completion:
```bash
# Update the tracking table in the epic doc
# Stage, commit, push
git add .
git commit -m "<type>(<scope>): <story summary>"
git push origin <branch>
```

### Rules (non-negotiable)

| Rule | Detail |
|------|--------|
| **Ask first** | Always ask the user to confirm epic scope and stories before creating the doc |
| **Sequential execution** | Stories execute in order unless explicitly marked as independent |
| **Docker-only testing** | All tests run inside Docker containers or Codespace (devcontainer). **NO venv, virtualenv, or conda.** |
| **No auth changes** | Do NOT modify authentication architecture (JWT flow, OAuth, Gateway auth middleware, RBAC). If a story requires auth changes, flag it and ask user. |
| **No constitutional changes** | Do NOT modify BaseEntity 7-section schema or L0 constitutional rules without explicit user approval |
| **Test suite placement** | Tests go in the correct suite per Section 11. Do not create ad-hoc test files outside established paths. |
| **Status accuracy** | 🔵 = code done + tests written but not executed. 🟢 = tests pass. Never mark 🟢 without passing tests. |
| **Commit messages** | Follow conventional commits: `<type>(<scope>): <subject>` (see Section 7) |
| **Branch discipline** | Work on the feature branch, never commit directly to `main` |

### Test requirement by change type

| What you changed | Required test suite | Path |
|-----------------|--------------------|----- |
| Plant model/service | Unit | `src/Plant/BackEnd/tests/unit/` |
| Plant API endpoint | Unit + Integration | `src/Plant/BackEnd/tests/unit/` + `tests/integration/` |
| Plant validator | Unit | `src/Plant/BackEnd/tests/unit/` |
| Gateway middleware | Unit | `src/Plant/Gateway/middleware/tests/` |
| CP Backend route | Unit | `src/CP/BackEnd/tests/` |
| CP Frontend component | UI Unit | `src/CP/FrontEnd/src/__tests__/` |
| CP Frontend page | UI Unit + E2E | `src/CP/FrontEnd/src/__tests__/` + `e2e/` |
| PP Frontend page | UI Unit | `src/PP/FrontEnd/src/pages/<Page>.test.tsx` |
| Cross-service behavior | Integration | `tests/` (root) |
| Terraform/infra | Manual verification | Document in story |
| Docker/compose | Config test | `tests/test_local_compose_auth_config.py` |

---

## 20. Secrets Lifecycle & Flow

### How secrets flow from source to running service

```
┌─────────────────────────────────────────────────────────────┐
│                    SECRET SOURCES                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Developer creates secret value                          │
│     ↓                                                       │
│  2. Stored in TWO places (must stay in sync):               │
│     ┌──────────────────┐    ┌──────────────────────┐        │
│     │  GitHub Secrets   │    │  GCP Secret Manager  │        │
│     │  (for CI/CD)      │    │  (for Cloud Run)     │        │
│     └────────┬─────────┘    └──────────┬───────────┘        │
│              │                          │                    │
│  3. GitHub Actions                 4. Terraform              │
│     reads secrets via              references secrets as     │
│     ${{ secrets.KEY }}             "SECRET_NAME:latest"      │
│              │                          │                    │
│  5. Workflow builds Docker         6. Cloud Run service      │
│     image, passes secrets as          mounts secret as       │
│     build args or env vars            env variable           │
│              │                          │                    │
│  7. Container runs with           8. Container runs with    │
│     secret in ENV                     secret in ENV          │
│     (Codespace/CI)                    (GCP production)       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Secret inventory

| Secret | GitHub Secret name | GCP Secret name | Used by | Sync critical? |
|--------|-------------------|-----------------|---------|----------------|
| JWT signing key | `JWT_SECRET` | `JWT_SECRET` | CP, PP, Plant, Gateway | **YES** — mismatch = silent 401s |
| Google OAuth ID | `GOOGLE_CLIENT_ID` | `GOOGLE_CLIENT_ID` | CP, PP, Gateway | YES |
| Google OAuth secret | `GOOGLE_CLIENT_SECRET` | `GOOGLE_CLIENT_SECRET` | Gateway | YES |
| GCP Service Account | `GCP_SA_KEY` | (IAM, not SM) | CI/CD workflows | — |
| CP ↔ Gateway shared key | `CP_REGISTRATION_KEY` | `CP_REGISTRATION_KEY` | CP Backend, Gateway | YES |
| Turnstile public key | `TURNSTILE_SITE_KEY` | (frontend build arg) | CP Frontend | NO (public) |
| Turnstile server key | `TURNSTILE_SECRET_KEY` | `TURNSTILE_SECRET_KEY` | CP Backend | YES |

### How to update a secret

```bash
# 1. Update in GitHub (via UI or CLI)
gh secret set JWT_SECRET --body "new-value-here"

# 2. Update in GCP Secret Manager
gcloud secrets versions add JWT_SECRET --data-file=- <<< "new-value-here"

# 3. Redeploy affected services (secret change requires new revision)
# Via workflow: GitHub Actions → WAOOAW Deploy → select environment → apply
# Or manually:
gcloud run services update waooaw-api-demo --region asia-south1 --update-secrets=JWT_SECRET=JWT_SECRET:latest
```

### Local development secrets

| File | Purpose | Git-tracked? |
|------|---------|--------------|
| `.env` | Local overrides (developer-specific) | **NO** (in .gitignore) |
| `.env.example` | Template with placeholder values | YES |
| `.env.docker` | Docker Compose specific | **NO** |
| `.env.gateway` | Gateway specific | **NO** |
| `docker-compose.local.yml` | Has default dev values (non-sensitive) | YES |

---

## 21. CLI Reference — Git, GCP, Debugging

### Git CLI commands

```bash
# --- Branch management ---
git checkout -b feat/new-feature          # Create feature branch
git push origin feat/new-feature           # Push branch
git checkout main && git pull              # Update main

# --- Status & history ---
git --no-pager log --oneline -20           # Recent commits
git --no-pager log --oneline --merges -10  # Recent merged PRs
git --no-pager diff --stat main            # Changes vs main
git --no-pager diff --name-only main       # Changed files only

# --- Commit (conventional) ---
git add .
git commit -m "feat(cp): add phone validation"
git push origin $(git branch --show-current)

# --- Stash & recover ---
git stash                                  # Save uncommitted work
git stash pop                              # Restore stashed work

# --- PR-related ---
gh pr create --title "feat(cp): ..." --body "..."  # Create PR
gh pr list                                          # List open PRs
gh pr view 678                                      # View specific PR
gh pr checks 678                                    # Check CI status
```

### GCP CLI commands

#### ⚠️ Prerequisites — GCP authentication in Codespace

> **GCP CLI commands require authentication.** They do NOT work out-of-the-box in Codespaces. You must complete ONE of these auth methods first:

```bash
# --- Option 1: Interactive login (for developer sessions) ---
gcloud auth login                                           # Opens browser for OAuth
gcloud config set project waooaw-oauth                      # Set project
gcloud config set compute/region asia-south1                # Set region

# --- Option 2: Service account key (for scripted/CI access) ---
# Ask the repo owner for the service account key JSON file
gcloud auth activate-service-account --key-file=key.json
gcloud config set project waooaw-oauth

# --- Verify auth works ---
gcloud auth list                                            # Should show active account
gcloud run services list --region=asia-south1               # Should list services (if any deployed)
```

> **If you get "permission denied" or "not authenticated"**: you need the repo owner to share GCP access. The `GCP_SA_KEY` secret in GitHub Actions is for CI/CD only and is not available in Codespaces.

#### Cloud Run service names (exact lookup table)

| Component | Service name pattern | demo | uat | prod |
|-----------|---------------------|------|-----|------|
| CP Frontend | `waooaw-cp-frontend-{env}` | `waooaw-cp-frontend-demo` | `waooaw-cp-frontend-uat` | `waooaw-cp-frontend-prod` |
| CP Backend | `waooaw-cp-backend-{env}` | `waooaw-cp-backend-demo` | `waooaw-cp-backend-uat` | `waooaw-cp-backend-prod` |
| PP Frontend | `waooaw-pp-frontend-{env}` | `waooaw-pp-frontend-demo` | `waooaw-pp-frontend-uat` | `waooaw-pp-frontend-prod` |
| PP Backend | `waooaw-pp-backend-{env}` | `waooaw-pp-backend-demo` | `waooaw-pp-backend-uat` | `waooaw-pp-backend-prod` |
| Plant Backend | `waooaw-plant-backend-{env}` | `waooaw-plant-backend-demo` | `waooaw-plant-backend-uat` | `waooaw-plant-backend-prod` |
| Plant Gateway | `waooaw-plant-gateway-{env}` | `waooaw-plant-gateway-demo` | `waooaw-plant-gateway-uat` | `waooaw-plant-gateway-prod` |
| Gateway (CP) | `waooaw-gateway-cp-{env}` | `waooaw-gateway-cp-demo` | `waooaw-gateway-cp-uat` | `waooaw-gateway-cp-prod` |
| Gateway (PP) | `waooaw-gateway-pp-{env}` | `waooaw-gateway-pp-demo` | `waooaw-gateway-pp-uat` | `waooaw-gateway-pp-prod` |

> **Currently deployed**: Only CP services (`enable_cp=true`) are active in all environments. PP and Plant are `enable_pp=false`, `enable_plant=false`.

#### GCP project & region constants

| Setting | Value |
|---------|-------|
| Project ID | `waooaw-oauth` |
| Region | `asia-south1` |
| Artifact Registry | `asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/` |

#### Ready-to-use log commands

Replace `{SERVICE}` with a service name from the table above (e.g., `waooaw-cp-backend-demo`):

```bash
# --- Authentication (must do first) ---
gcloud auth login
gcloud config set project waooaw-oauth

# --- Secrets ---
gcloud secrets list                                         # List all secrets
gcloud secrets versions access latest --secret=JWT_SECRET   # Read a secret value
gcloud secrets versions add JWT_SECRET --data-file=- <<< "new-value"  # Update secret

# --- List all Cloud Run services ---
gcloud run services list --region=asia-south1

# --- Describe a specific service ---
gcloud run services describe {SERVICE} --region=asia-south1

# --- Live logs (last 10 minutes, 50 entries) ---
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="{SERVICE}"' \
  --limit=50 --format=json --freshness=10m

# --- Error logs only ---
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=ERROR AND resource.labels.service_name="{SERVICE}"' \
  --limit=20 --format="table(timestamp,textPayload)"

# --- Example: CP Backend demo errors ---
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=ERROR AND resource.labels.service_name="waooaw-cp-backend-demo"' \
  --limit=20 --format="table(timestamp,textPayload)"

# --- Example: Plant Gateway demo logs ---
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant-gateway-demo"' \
  --limit=50 --format=json --freshness=10m

# --- Cloud SQL ---
gcloud sql instances list                                   # List DB instances
gcloud sql connect waooaw-db --user=waooaw                  # Connect to DB

# --- Artifact Registry ---
gcloud artifacts docker images list asia-south1-docker.pkg.dev/waooaw-oauth/waooaw  # List images
gcloud artifacts docker tags list asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend  # Image tags

# --- Terraform state ---
cd cloud/terraform
terraform state list                                        # List managed resources
terraform state show module.customer_portal[0]               # Inspect a resource
terraform plan -var-file=environments/demo.tfvars            # Plan changes
```

### Debugging cheat sheet

| Scenario | Command |
|----------|---------|
| App won't start locally | `docker-compose -f docker-compose.local.yml logs plant-backend --tail=50` |
| 401 errors across services | Check JWT_SECRET matches: `echo $JWT_SECRET` in each container |
| CP can't reach Gateway | `docker-compose -f docker-compose.local.yml exec cp-backend curl http://plant-gateway:8000/health` |
| DB connection failing | `docker-compose -f docker-compose.local.yml exec postgres pg_isready -U waooaw` |
| Check running containers | `docker-compose -f docker-compose.local.yml ps` |
| GCP service unhealthy | `gcloud run services describe <service> --region=asia-south1 --format='get(status.conditions)'` |
| GCP deployment failed | `gcloud logging read 'resource.type="cloud_run_revision" AND severity>=ERROR' --limit=10 --freshness=30m` |
| Secret not reaching container | `gcloud run services describe <service> --region=asia-south1 --format='yaml(spec.template.spec.containers[0].env)'` |
| Port already in use | `lsof -i :<port>` or `docker ps --filter publish=<port>` |
| Redis connectivity | `docker-compose -f docker-compose.local.yml exec redis redis-cli ping` |

### GitHub CLI (gh) commands

```bash
# --- Secrets ---
gh secret list                             # List repo secrets
gh secret set MY_SECRET                    # Set (interactive prompt)
gh secret set MY_SECRET --body "value"     # Set (inline)

# --- Actions ---
gh run list --limit 10                     # Recent workflow runs
gh run view <run-id>                       # View specific run
gh run view <run-id> --log                 # Full logs
gh workflow run waooaw-deploy.yml -f environment=demo -f terraform_action=plan  # Trigger deploy

# --- Issues ---
gh issue list --label epic                 # List epics
gh issue view 191                          # View issue
```

---

## 22. Troubleshooting FAQ — Agent Self-Service Reference

> **INSTRUCTION TO AI AGENT**: Before asking the user ANY question about credentials, service names, environments, or debugging — **read this section first**. Every common question is pre-answered below.

---

### Q1: "I need GCP credentials to run log commands"

**Answer**: You do NOT have GCP credentials by default in Codespaces. Here's what to do:

| Situation | Action |
|-----------|--------|
| You were asked to fetch GCP logs | Tell the user: *"I need GCP auth. Please run `gcloud auth login` in the terminal first, or provide a service account key file."* |
| You want to check if auth already exists | Run `gcloud auth list` — if it shows an active account, you're good. If empty/errors, auth is missing. |
| User says "here's the key" | Run `gcloud auth activate-service-account --key-file=<path>` then `gcloud config set project waooaw-oauth` |
| User says "just use what's available" | GCP auth is NOT stored in Codespace environment variables. The `GCP_SA_KEY` GitHub secret is for CI/CD only. You must ask the user to authenticate. |

**Quick auth check script:**
```bash
# Run this FIRST before any gcloud command
if gcloud auth list 2>/dev/null | grep -q ACTIVE; then
  echo "✅ GCP auth active"
  gcloud config set project waooaw-oauth 2>/dev/null
else
  echo "❌ No GCP auth. Run: gcloud auth login"
fi
```

---

### Q2: "I need the exact Cloud Run service name"

**Answer**: Use this lookup table. The naming pattern is `waooaw-{component}-{role}-{environment}`.

| Component | Role | demo | uat | prod |
|-----------|------|------|-----|------|
| CP | frontend | `waooaw-cp-frontend-demo` | `waooaw-cp-frontend-uat` | `waooaw-cp-frontend-prod` |
| CP | backend | `waooaw-cp-backend-demo` | `waooaw-cp-backend-uat` | `waooaw-cp-backend-prod` |
| PP | frontend | `waooaw-pp-frontend-demo` | `waooaw-pp-frontend-uat` | `waooaw-pp-frontend-prod` |
| PP | backend | `waooaw-pp-backend-demo` | `waooaw-pp-backend-uat` | `waooaw-pp-backend-prod` |
| Plant | backend | `waooaw-plant-backend-demo` | `waooaw-plant-backend-uat` | `waooaw-plant-backend-prod` |
| Plant | gateway | `waooaw-plant-gateway-demo` | `waooaw-plant-gateway-uat` | `waooaw-plant-gateway-prod` |
| Gateway | cp | `waooaw-gateway-cp-demo` | `waooaw-gateway-cp-uat` | `waooaw-gateway-cp-prod` |
| Gateway | pp | `waooaw-gateway-pp-demo` | `waooaw-gateway-pp-uat` | `waooaw-gateway-pp-prod` |

> **Currently deployed (as of Feb 2026)**: Only **CP** services are active (`enable_cp=true`). PP and Plant have `enable_pp=false`, `enable_plant=false` in all environments.

**How to pick the right service:**

| You're debugging… | Service to query |
|-------------------|-----------------|
| Customer registration / login / OTP | `waooaw-cp-backend-{env}` |
| Customer portal UI not loading | `waooaw-cp-frontend-{env}` |
| API proxy / auth / JWT errors | `waooaw-gateway-cp-{env}` or `waooaw-plant-gateway-{env}` |
| Agent CRUD / industry / skill data | `waooaw-plant-backend-{env}` |
| Platform portal (admin) UI | `waooaw-pp-frontend-{env}` |
| Platform portal API | `waooaw-pp-backend-{env}` |

---

### Q3: "Which environment and region should I use?"

**Answer**:

| Setting | Value | Notes |
|---------|-------|-------|
| **GCP Project** | `waooaw-oauth` | Always this — single project for all envs |
| **Region** | `asia-south1` | All Cloud Run, Cloud SQL, and Artifact Registry resources |
| **Default environment** | `demo` | Unless user specifies otherwise, assume `demo` |
| **Environments available** | `demo`, `uat`, `prod` | Terraform tfvars: `cloud/terraform/environments/{env}.tfvars` |

**Rule of thumb**: If the user says "check logs" without specifying environment → use **demo**. If they say "production issue" → use **prod**.

---

### Q4: "What time window should I search for logs?"

**Answer**: Use these defaults if the user doesn't specify:

| User says | `--freshness` value | Command snippet |
|-----------|-------------------|----------------|
| "just happened" / "right now" | `5m` | `--freshness=5m` |
| "recent" / "just tried" | `30m` | `--freshness=30m` |
| "today" / "this morning" | `6h` | `--freshness=6h` |
| "yesterday" | `24h` | `--freshness=24h` |
| Specific time given | Use timestamp filter | `timestamp>="2026-02-17T10:00:00Z"` |
| No time mentioned at all | `1h` | `--freshness=1h` (safe default) |

**Complete log command template (copy-paste ready):**
```bash
# Replace {SERVICE} and {FRESHNESS} — defaults: waooaw-cp-backend-demo, 1h
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="{SERVICE}"' \
  --project=waooaw-oauth \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)" \
  --freshness={FRESHNESS}
```

---

### Q5: "Registration failed — how do I debug it?"

**Answer**: CP registration flows through 3 services. Check in this order:

| Step | Service | What to look for |
|------|---------|-----------------|
| 1. Frontend | `waooaw-cp-frontend-{env}` | JS console errors, failed API calls (open browser DevTools → Network tab) |
| 2. CP Backend | `waooaw-cp-backend-{env}` | `/register` endpoint errors, OTP validation failures, GSTIN/phone validation |
| 3. Plant Gateway | `waooaw-plant-gateway-{env}` | Customer creation via CP_REGISTRATION_KEY auth, DB write errors |

**Quick debug commands (demo env):**
```bash
# Step 1: Check CP Backend for registration errors
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-cp-backend-demo" AND severity>=ERROR' \
  --project=waooaw-oauth --limit=20 --freshness=1h \
  --format="table(timestamp,textPayload)"

# Step 2: Check Plant Gateway for downstream errors
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant-gateway-demo" AND severity>=ERROR' \
  --project=waooaw-oauth --limit=20 --freshness=1h \
  --format="table(timestamp,textPayload)"

# Step 3: Check if it's a secret mismatch
# CP_REGISTRATION_KEY must match in both CP Backend AND Plant Gateway
gcloud secrets versions access latest --secret=CP_REGISTRATION_KEY
```

---

### Q6: "JWT / 401 Unauthorized errors across services"

**Answer**: Almost always a **JWT_SECRET mismatch**.

| Check | Command |
|-------|---------|
| Verify JWT_SECRET is set | `gcloud secrets versions access latest --secret=JWT_SECRET` |
| Verify all services use same secret | All 4 components (CP, PP, Plant, Gateway) must reference the same `JWT_SECRET` in Secret Manager |
| Check Gateway middleware logs | Query `waooaw-gateway-cp-{env}` or `waooaw-plant-gateway-{env}` for auth errors |
| Local Docker JWT issue | Ensure `JWT_SECRET` in `docker-compose.local.yml` matches across all services |

**Local Docker fix:**
```bash
# Check if JWT_SECRET is consistent across services in docker-compose
grep -n "JWT_SECRET" docker-compose.local.yml
```

---

### Q7: "Docker containers won't start / database connection errors"

**Answer**:

```bash
# Check which containers are running
docker compose -f docker-compose.local.yml ps

# Check container logs for errors
docker compose -f docker-compose.local.yml logs --tail=50 plant-backend
docker compose -f docker-compose.local.yml logs --tail=50 cp-backend

# Restart everything cleanly
docker compose -f docker-compose.local.yml down -v
docker compose -f docker-compose.local.yml up --build -d

# Check if DB is accepting connections
docker compose -f docker-compose.local.yml exec db pg_isready -U waooaw

# Check if Redis is up
docker compose -f docker-compose.local.yml exec redis redis-cli ping
```

| Common error | Root cause | Fix |
|-------------|------------|-----|
| `connection refused port 5432` | DB not ready yet | Wait 10s or restart compose |
| `role "waooaw" does not exist` | DB not initialized | `docker compose down -v && docker compose up --build -d` |
| `FATAL: password authentication failed` | Wrong POSTGRES_PASSWORD | Check `docker-compose.local.yml` env vars |
| `redis.exceptions.ConnectionError` | Redis not started | `docker compose up -d redis` |

---

### Q8: "How do I run tests?"

**Answer**: **Docker only. Never use venv.**

```bash
# Run all tests for a component
docker compose -f docker-compose.local.yml run --rm plant-backend pytest -x -v

# Run specific test file
docker compose -f docker-compose.local.yml run --rm cp-backend pytest tests/test_registration.py -v

# Run with coverage
docker compose -f docker-compose.local.yml run --rm plant-backend pytest --cov=app --cov-report=html

# Run frontend tests
docker compose -f docker-compose.local.yml run --rm cp-frontend npm test
```

> See **Section 11** for full test strategy and file locations.

---

### Q9: "How do I check what's deployed vs what's in code?"

**Answer**:

```bash
# What's deployed to Cloud Run (requires GCP auth)
gcloud run services describe waooaw-cp-backend-demo --region=asia-south1 \
  --format="value(status.latestReadyRevisionName)"

# What's the latest image in Artifact Registry
gcloud artifacts docker tags list \
  asia-south1-docker.pkg.dev/waooaw-oauth/waooaw/cp-backend --limit=5

# What's merged to main
git --no-pager log --oneline origin/main -10

# What's different between your branch and main
git --no-pager diff --stat origin/main

# Last GitHub Actions deploy
gh run list --workflow=waooaw-deploy.yml --limit=5
```

---

### Q10: "I need to check/update a database table"

**Answer**:

| Method | How |
|--------|-----|
| **Local (Docker)** | `docker compose -f docker-compose.local.yml exec db psql -U waooaw -d waooaw_db` |
| **GCP Cloud SQL** | `gcloud sql connect waooaw-db --user=waooaw` (requires GCP auth + Cloud SQL Admin API) |
| **Adminer UI (local)** | `http://localhost:8081` — server: `db`, user: `waooaw`, db: `waooaw_db` |

**Common queries:**
```sql
-- Check recent customers
SELECT id, email, company_name, created_at FROM customers ORDER BY created_at DESC LIMIT 10;

-- Check migration status
SELECT version_num FROM alembic_version;

-- Check agent data
SELECT id, name, industry, status FROM agents LIMIT 20;
```

> See **Section 10** for full schema reference.

---

### Q11: "How do I find the right file to edit?"

**Answer**: Use this decision tree:

| You need to change… | Look in | Key files |
|---------------------|---------|-----------|
| CP registration logic | `src/CP/BackEnd/app/` | `routes/auth.py`, `services/registration.py` |
| CP frontend UI | `src/CP/FrontEnd/src/` | `pages/`, `components/`, `App.tsx` |
| API routing / auth middleware | `src/Plant/Gateway/app/` | `middleware/`, `routes/proxy.py` |
| Database models | `src/Plant/BackEnd/app/models/` | `agent.py`, `industry.py`, `base_entity.py` |
| Constitutional validators | `src/Plant/BackEnd/app/validators/` | `constitutional_validator.py`, `entity_validator.py` |
| Terraform / infra | `cloud/terraform/` | `main.tf`, `stacks/{component}/main.tf` |
| CI/CD workflows | `.github/workflows/` | `waooaw-alm.yml`, `waooaw-deploy.yml` |
| Docker setup | project root | `docker-compose.local.yml` |
| Environment variables | See **Section 14** | `.env` files per component |

> See **Section 13** for the complete code index.

---

### Quick decision flowchart for agents

```
START: User reports an issue
  │
  ├─ Is it a LOCAL dev issue?
  │   ├─ Docker not running → Q7
  │   ├─ Tests failing → Q8
  │   ├─ DB issue → Q10
  │   └─ Can't find file → Q11
  │
  ├─ Is it a DEPLOYED (GCP) issue?
  │   ├─ Do you have GCP auth? → Q1
  │   │   └─ No → Ask user to authenticate first
  │   ├─ Which service? → Q2
  │   ├─ Which environment? → Q3
  │   ├─ What time window? → Q4
  │   ├─ Registration failure → Q5
  │   └─ Auth/JWT errors → Q6
  │
  └─ Need to check deploy status? → Q9
```

---

*End of Context & Indexing Document*
