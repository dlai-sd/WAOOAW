# WAOOAW — Context & Indexing Reference

**Version**: 2.4  
**Date**: 2026-03-09  
**Purpose**: Single-source context document for any AI agent (including lower-cost models) to efficiently navigate, understand, and modify the WAOOAW codebase.  
**Update cadence**: Section 12 ("Latest Changes") should be refreshed daily.  
**Key design doc**: [`docs/PP/AGENT-CONSTRUCT-DESIGN.md`](PP/AGENT-CONSTRUCT-DESIGN.md) — full low-level design of the Agent Construct system (v2, 2179 lines). Read §§1–8 before touching `agent_mold/` or any construct pipeline.

---

## Table of Contents

0. [How To Use This Document](#0-how-to-use-this-document)
1. [Problem Statement & Vision](#1-problem-statement--vision)
2. [Solution Hypothesis](#2-solution-hypothesis)
3. [Constitutional Design Pattern](#3-constitutional-design-pattern)
4. [Four Major Components](#4-four-major-components)
  - [4.6 Agent Construct Architecture](#46-agent-construct-architecture)
  - [4.7 Canonical Runtime Vocabulary](#47-canonical-runtime-vocabulary)
5. [Architecture & Technical Stack](#5-architecture--technical-stack)
  - [5.1 Platform Runtime Layout](#51-platform-runtime-layout)
  - [5.2 Route Ownership And Debug Order](#52-route-ownership-and-debug-order)
  - [5.3 Service Ownership Map](#53-service-ownership-map)
  - [5.4 Ops, Infra, And Deployment Control Plane](#54-ops-infra-and-deployment-control-plane)
  - [5.5 Logging, Metrics, And Debugging Spine](#55-logging-metrics-and-debugging-spine)
  - [5.6 Platform NFR Standards — Mandatory Patterns for Every New Route](#56-platform-nfr-standards--mandatory-patterns-for-every-new-route)
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
22. [Troubleshooting FAQ — Agent Self-Service Reference](#22-troubleshooting-faq--agent-self-service-reference)
23. [Mobile Application — CP Mobile](#23-mobile-application--cp-mobile)
24. [Skills & Capabilities for World-Class Platform](#24-skills--capabilities-for-world-class-platform)
25. [Session Commentary Protocol — Context Recovery](#25-session-commentary-protocol--context-recovery)
26. [Agent Construct Design — Quick Reference](#26-agent-construct-design--quick-reference)

---

## 0. How To Use This Document

Treat this file as the platform operating manual, not as a changelog dump. It should answer three questions fast: what WAOOAW is, where each responsibility lives, and which files are the canonical edit points for a task.

### Reading order by task

| If you are doing... | Read first | Then read | Outcome |
|---|---|---|---|
| First-time repo orientation | §1, §4, §5.1 | §13, §15, §16 | You understand product shape, service layout, ports, and start commands |
| CP or PP route bug | §5.2 | §13 CP/PP + Plant sections | You trace FE/BE/Gateway/Plant ownership without guessing |
| Plant runtime or hired-agent work | §4.6, §4.7 | §5.1, §13 Plant section | You use the correct Agent/Skill/Component/SkillRun vocabulary and files |
| Mobile work | §6, §23 | §13 mobile section, §15 | You know when mobile talks directly to Gateway vs through CP Backend |
| Docker, Terraform, deploy, or image-promotion work | §8, §8.1, §9 | §13 infra sections, §21 | You avoid baking environment logic into images or templates |
| Database, migration, or seed work | §10 | §13 Plant models/core sections | You know the DB entrypoints, migration path, and local/demo access pattern |
| Logging, tracing, or production debugging | §5.5, §9, §21, §22 | §13 Plant/Gateway/PP core sections | You start from the actual logging/metrics/observability files |

### Source-of-truth rules

| Content type | Canonical home in this document | What should stay out |
|---|---|---|
| Stable product and constitutional truths | §§1–4 | PR-by-PR storytelling |
| Current service ownership and runtime layout | §5 | Deep historical implementation notes |
| Deployment, Terraform, image promotion, secrets | §§8–9 | Environment-specific hacks or temporary overrides |
| Database, testing, ports, common commands | §§10–16 | Repeated command snippets copied into many other sections |
| Rapid code navigation | §13 | Narrative explanations better suited for architecture sections |
| Time-sensitive history | §12 | Permanent design guidance |

### Maintenance rules for keeping this document authoritative

| Rule | Why |
|---|---|
| Update the section that owns the truth instead of adding a new disconnected note | Prevents contradictions and duplicated guidance |
| Prefer stable entrypoints and central files over leaf implementation details | Makes the document usable for new engineers and small-context agents |
| Add temporary findings to §12 or §17, not to core architecture sections, unless the architecture actually changed | Keeps the bible durable instead of noisy |
| When a route or workflow changes, update both the ownership map and the file index in the same PR | Prevents navigation drift |
| If a concept has one canonical term, use it everywhere here even if code still carries a legacy name | Keeps public/runtime language converged |

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
| **Agent mold** | `src/Plant/BackEnd/agent_mold/` — in-memory BlueprintRegistry for all agent types (`AgentSpec` + `ConstructBindings` + `ConstraintPolicy` + `LifecycleHooks`); Pump/Processor/Publisher ABCs; `DimensionContract` enforcement; `HookBus` at construct pipeline boundaries. Full design: `docs/PP/AGENT-CONSTRUCT-DESIGN.md` |

### 4.2 Plant Gateway

| Aspect | Detail |
|--------|--------|
| **Role** | API gateway — auth, RBAC, policy, budget, audit middleware; proxies to Plant Backend |
| **Backend** | FastAPI on port 8000 (public-facing) |
| **Key paths** | `src/Plant/Gateway/` |
| **Entry point** | `src/Plant/Gateway/main.py` (787 lines) |
| **Middleware stack** | auth.py → rbac.py → policy.py → budget.py → audit.py → error_handler.py |
| **OPA policies** | `src/Plant/Gateway/opa/` — 5 Rego policy files + unit tests; OPA called over HTTPS from `rbac.py`, `policy.py`, `budget.py` middleware |
| **Infrastructure** | `src/Plant/Gateway/infrastructure/` — feature_flags/ |
| **Pattern** | Receives requests from CP/PP → validates JWT → queries OPA for RBAC/policy/budget decisions → proxies to Plant Backend at port 8001 |

### 4.6 Agent Construct Architecture

> **Full spec**: [`docs/PP/AGENT-CONSTRUCT-DESIGN.md`](PP/AGENT-CONSTRUCT-DESIGN.md) (v2, 2179 lines). This section is the quick-reference summary — read the full doc before editing any construct pipeline code.

#### Platform Hierarchy

```
Customer
  └── HiredAgent          (one runtime Agent hired by one customer)
    └── Skill         (smallest customer-visible value-producing capability)
      └── SkillRun (one execution record of one Skill)
        └── Deliverable / Approval outcome
```

**Canonical runtime rule:** external docs, route contracts, and new APIs should use `Agent`, `Skill`, `Component`, `SkillRun`, and `Goal` as the default runtime language.

**Legacy compatibility note:** the codebase still contains `GoalRun` and `flow_runs` storage names. Treat those as internal compatibility and persistence terms, not the preferred public vocabulary.

**Constructs** are internal building blocks. Customers never interact with them — only with the Skill API surface (configure → run → approve → receive deliverable).

**The mould is in-memory.** `AgentSpec` objects are created at process startup from `agent_mold/reference_agents.py` and held in `DimensionRegistry` + `SkillRegistry` in RAM. No DB persistence of the mould — only hired instances and runtime artefacts are persisted.

#### Construct Hierarchy

```
AgentSpec (blueprint — in-memory)
  ├── Dimensions          (Skill, Industry, Team, Integrations, Budget, Trial, UI, L10n)
  ├── ConstructBindings   (which Pump / Processor / Publisher / Connector to use)
  ├── ConstraintPolicy    (risk limits, rate limits, cost gates)
  └── LifecycleHooks      (on_hire, on_trial_end, on_cancel … — all defined, agents override)
        └── Skill
              ├── CONSTRUCT: Scheduler  ← PLATFORM CORE — when to run
              ├── CONSTRUCT: Pump       ← PLATFORM CORE — what data flows in
              ├── CONSTRUCT: Processor  ← AGENT-SPECIFIC — the AI brain
              ├── CONSTRUCT: Connector  ← PLATFORM CORE — credentials + protocol
              └── CONSTRUCT: Publisher  ← PLATFORM CORE — where results go out
```

#### Platform Core vs Agent-Specific

| Construct | Owner | Rationale |
|---|---|---|
| Scheduler | **Platform Core** | Cadence, retry, DLQ identical across all agents |
| Pump | **Platform Core** | Data assembly from DB + config is identical; schema only differs |
| Connector | **Platform Core** | Credential lifecycle, Secret Manager — never agent-specific |
| Publisher | **Platform Core** | Destination adapter registry is common |
| **Processor** | **Agent-Specific** | The AI reasoning, LLM calls, domain logic — only this varies |

**Invariant:** Constructs are stateless. State lives in the database. A construct reads from DB on entry, writes on exit.

### 4.7 Canonical Runtime Vocabulary

Use this vocabulary in plans, route reviews, API design, and code comments to prevent future drift.

| Term | Canonical meaning | Avoid drifting to |
|---|---|---|
| **Agent** | The customer-hired runtime worker that owns lifecycle state, schedule defaults, budget, payment linkage, and enabled Skills | Treating Agent as a single Skill or a one-off workflow |
| **Skill** | The smallest customer-visible, value-producing capability inside an Agent | Using generic `workflow` or `tool` for customer-facing capability |
| **Component** | A stateless execution unit inside a Skill | Stateful mini-agents or ad hoc plugin terminology |
| **Connector** | External integration boundary: credentials, auth, protocol, transport | Data-source synonym or publisher substitute |
| **Pump** | Reads or assembles input data for execution | Hidden business logic processor |
| **Processor** | Performs domain logic, AI reasoning, or transformation | Scheduler, connector, or publisher work |
| **Validator** | Evaluates quality, policy, constraints, and goal attainment | An invisible post-step buried inside Processor |
| **Publisher** | Writes, posts, or submits outputs to external systems | Generic connector or processor logic |
| **Platform Configuration** | PP-managed certified structure, bindings, limits, and governance fields | Customer-editable business inputs |
| **Customer Configuration** | Customer-managed runtime inputs within certified limits | PP-owned structural configuration |
| **Skill Run** | One execution record of one Skill, including run context, component history, status, approval state, outputs, and metrics | Publicly naming it a Flow when the business unit is a Skill |
| **Goal** | Expected business result measured at Skill or Agent level | Component-owned business outcome |

#### Anti-drift rules

| Rule | Why it matters |
|---|---|
| Prefer `SkillRun` in new public APIs and portal contracts | Keeps product language aligned with the customer-facing unit of value |
| Keep `flow_runs` and `GoalRun` as compatibility/storage names until a deliberate migration is approved | Avoids breaking persistence while converging public contracts |
| Every customer-facing business capability should fit `Agent -> Skill -> Component -> Skill Run -> Goal` | Makes architecture review and story planning consistent |
| Components remain stateless; state belongs in Agent, Skill configuration, SkillRun, and persisted records | Prevents hidden runtime state and easier debugging failures |

#### Key Agent Mold Files

| File | Purpose |
|---|---|
| `agent_mold/spec.py` | `AgentSpec`, `CompiledAgentSpec`, `ConstructBindings`, `ConstraintPolicy`, `DimensionSpec`, `DimensionName` |
| `agent_mold/contracts.py` | `DimensionContract` ABC — `validate()` / `materialize()` / `register_hooks()` / `observe()` |
| `agent_mold/hooks.py` | `AgentLifecycleHooks` ABC — all platform lifecycle events (on_hire, on_trial_start, on_deliverable_approved, on_cancel …) |
| `agent_mold/enforcement.py` | `default_hook_bus()` singleton — builds the platform `HookBus` with platform-default hooks registered |
| `agent_mold/registry.py` | `DimensionRegistry`, `SkillRegistry` — startup wiring; `register("content.creator.v1", …)` |
| `agent_mold/reference_agents.py` | Marketing, tutor, trading reference `AgentSpec` definitions |
| `agent_mold/skills/content_creator.py` | `ContentCreatorProcessor` — generates `DailyThemeList` + `ContentPost` objects |
| `agent_mold/skills/trading_executor.py` | `TradingProcessor` — produces `TradingOrderIntent` in draft mode; never places real orders |
| `agent_mold/skills/publisher_engine.py` | `DestinationAdapter` ABC + `DestinationRegistry` + `PublisherEngine` |
| `agent_mold/skills/adapters_publish.py` | `SimulatedAdapter` (Phase 1 publisher) |
| `integrations/delta_exchange/` | Delta Exchange client, order placement, risk engine |
| `integrations/social/` | LinkedIn / social credential resolver |

#### Construct Execution Flow (v2)

```
Scheduler → HookBus(PRE_PUMP) → Pump.pull() → HookBus(PRE_PROCESSOR)
  → Processor.execute() → HookBus(PRE_PUBLISH) → [ApprovalGate]
  → Connector.resolve() → Publisher.publish() → HookBus(POST_PUBLISH)
  → Deliverable persisted → LifecycleHook: on_goal_run_complete
```

#### ConstraintPolicy — mould-level guardrails

```python
class ConstraintPolicy(BaseModel):
    max_goal_runs_per_day:      Optional[int]   = None
    max_cost_per_run_usd:       Optional[float] = None
    max_position_size_usd:      Optional[float] = None   # trading
    max_concurrent_positions:   Optional[int]   = None   # trading
    allowed_exchanges:          List[str]       = []     # ["delta_exchange_india"]
    max_posts_per_day:          Optional[int]   = None   # content
    allowed_channels:           List[str]       = []     # ["linkedin", "instagram"]
    approval_required_before_publish: bool      = True
    max_cost_per_month_usd:     Optional[float] = None
    budget_alert_threshold_pct: float           = 0.8
```

#### HookBus stages

| Stage | Hook registered | Enforces |
|---|---|---|
| `PRE_PUMP` | `QuotaGateHook` | `quota_remaining > 0` |
| `PRE_PUMP` | `SchedulerPauseHook` | `scheduler_state.is_paused = false` |
| `PRE_PROCESSOR` | `ConstraintPolicyHook` | `max_goal_runs_per_day` not exceeded |
| `PRE_TOOL_USE` | `ApprovalRequiredHook` | External actions need approval_id |
| `PRE_PUBLISH` | `ApprovalGateHook` | `approval_mode != auto` requires approval |
| `POST_PUBLISH` | `CostAuditHook` | Log cost to metering service |

#### Agent profiles quick reference

| | Share Trader (`AGT-TRADING-001`) | Content Creator (`AGT-MKT-*`) |
|---|---|---|
| `processor_class` | `TradingProcessor` | `ContentCreatorProcessor` |
| `pump_class` | `TradingPump` (custom — live positions) | `GoalConfigPump` (platform default) |
| `publisher_class` | `DestinationPublisher` (→ `DeltaTradeAdapter`) | `DestinationPublisher` (→ `LinkedInAdapter`) |
| `max_goal_runs_per_day` | 10 | 3 |
| `approval_required` | Yes | Yes |
| Key hook override | `on_deliverable_approved` → place real order | `on_deliverable_approved` → trigger Publisher |

---

### 4.5 Plant OPA (Policy Engine)

| Aspect | Detail |
|--------|--------|
| **Role** | Stateless Open Policy Agent service — evaluates RBAC, trial mode, governor role, agent budget, and sandbox routing policies |
| **Runtime** | Official OPA server (`openpolicyagent/opa:0.68.0`) on port 8181 |
| **Key paths** | `src/Plant/Gateway/opa/` |
| **Dockerfile** | `src/Plant/Gateway/opa/Dockerfile` — policies baked in at build time (code, not config) |
| **Policies** | `policies/rbac_pp.rego`, `policies/trial_mode.rego`, `policies/governor_role.rego`, `policies/agent_budget.rego`, `policies/sandbox_routing.rego` |
| **Tests** | `tests/` — 24 unit tests across 5 policy files; run via `opa test src/Plant/Gateway/opa -v` |
| **Access** | Service-to-service only (`allow_unauthenticated = false`); Plant Gateway authenticates using GCP Identity token |
| **Cloud Run** | `waooaw-plant-opa-{env}` — stateless, 0.5 CPU, 256 Mi, no DB, no VPC connector needed |
| **IAM** | `plant_gateway_sa` granted `roles/run.invoker` on the OPA service |
| **Two-gate design** | OPA is Gate 1 (role-level RBAC). Plant Backend `/api/v1/admin/db/*` is Gate 2 (hard admin-role check via `_require_admin_via_gateway`). Non-admin roles may pass Gate 1 for `resource="admin"` but are rejected at Gate 2. |

### 4.3 CP (Customer Portal)

| Aspect | Detail |
|--------|--------|
| **Role** | Customer-facing — browse agents, sign up, trial, hire, pay, manage subscriptions |
| **Backend** | FastAPI thin proxy on port 8020; routes auth/registration locally, proxies most API calls to Plant Gateway |
| **Frontend** | React 18 + TypeScript + Vite on port 3002→8080; dark-themed marketplace UI |
| **Key paths** | `src/CP/BackEnd/`, `src/CP/FrontEnd/` |
| **BE entry** | `src/CP/BackEnd/main.py` (245 lines) — thin proxy to Plant Gateway |
| **BE routes** | `src/CP/BackEnd/api/` — auth/, cp_registration.py, cp_otp.py, hire_wizard.py, payments_razorpay.py, trading.py, exchange_setup.py, subscriptions.py, invoices.py, receipts.py, `cp_skills.py`, `cp_flow_runs.py`, `cp_approvals_proxy.py`, `cp_scheduler.py` |
| **Runtime-facing routes** | `GET /cp/hired-agents/{id}/skills`, `PATCH /cp/hired-agents/{id}/skills/{skill_id}/goal-config`, `GET /cp/flow-runs`, `GET /cp/component-runs`, `GET /cp/hired-agents/{id}/approval-queue`, `POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/approve|reject` |
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
| **BE routes** | `src/PP/BackEnd/api/` — genesis.py, agents.py, agent_types.py, agent_setups.py, approvals.py, audit.py, auth.py, db_updates.py, exchange_credentials.py, metering_debug.py, security.py, ops_hired_agents.py, ops_dlq.py |
| **Diagnostic routes** | `GET /pp/ops/hired-agents/{id}/construct-health`, `GET /pp/ops/hired-agents/{id}/scheduler-diagnostics`, `GET /pp/ops/hired-agents/{id}/hook-trace`, `GET /pp/ops/dlq`, `POST /pp/ops/dlq/{id}/requeue`, `PATCH /pp/agent-setups/{id}/constraint-policy` — PP service-centre diagnostic toolkit (§14 of AGENT-CONSTRUCT-DESIGN.md) |
| **RBAC** | 7-role hierarchy (`admin > customer_admin > developer > manager > analyst > support > viewer`) enforced via OPA. Diagnostic routes require `admin` or `developer`. DLQ requeue requires `admin`. |
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
                 ┌────────▼─────────┐        ┌──────────────────┐
                 │  Plant Gateway   │◄──────►│  Plant OPA       │
                 │  FastAPI:8000    │        │  OPA:8181        │
                 │  Auth/RBAC/      │        │  Policy engine   │
                 │  Policy/Budget   │        │  (stateless)     │
                 └────────┬─────────┘        └──────────────────┘
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

### 5.1 Platform Runtime Layout

| Layer | Primary responsibility | Entry files | Notes |
|---|---|---|---|
| **CP FrontEnd** | Customer UI, service selection, request shaping | `src/CP/FrontEnd/src/pages/`, `src/CP/FrontEnd/src/services/` | First place to inspect when the portal calls the wrong CP route |
| **CP BackEnd** | Thin proxy only: auth/registration local, runtime requests forwarded to Plant Gateway | `src/CP/BackEnd/main.py`, `src/CP/BackEnd/api/` | Must not own business logic or data storage |
| **Plant Gateway** | Public API ingress, JWT validation, RBAC, policy, budget, audit, proxy to Plant | `src/Plant/Gateway/main.py`, `src/Plant/Gateway/middleware/` | Customer-facing public routes live under `/api/v1/...` |
| **Plant BackEnd** | Runtime business logic, persistence, scheduling, approvals, hired-agent state, skill execution | `src/Plant/BackEnd/main.py`, `src/Plant/BackEnd/api/v1/`, `src/Plant/BackEnd/services/` | Source of truth for hired agents, skills, deliverables, approvals, and execution history |
| **PostgreSQL** | Durable system state | `src/Plant/BackEnd/models/`, Alembic migrations | Holds hired agents, skills, skill configs, deliverables, and current run backing tables |
| **Redis** | Caching, throttling, scheduler/support state | service-level integrations | Not the source of truth for runtime business records |
| **External systems** | OAuth, payments, exchanges, social publish targets | adapters and integrations | Should be reached via Connector/Publisher boundaries, not portal business logic |

### 5.2 Route Ownership And Debug Order

When a CP customer flow fails, trace it in this order so route drift is classified correctly.

| Step | Layer | Start here | What you are confirming |
|---|---|---|---|
| 1 | CP FrontEnd | `src/CP/FrontEnd/src/services/` | The frontend is calling the intended CP route |
| 2 | CP BackEnd | `src/CP/BackEnd/api/` | The thin proxy points to the canonical Plant path |
| 3 | Plant Gateway | mounted `/api/v1/...` route inventory | The public route is actually exposed |
| 4 | Plant BackEnd | `src/Plant/BackEnd/api/v1/` + `services/` | The handler implements the expected runtime semantics |
| 5 | Persistence | `models/` + live DB row shape | The identifiers and stored fields match the contract being probed |

#### Runtime route ownership map

| Customer capability | CP FrontEnd service | CP BackEnd proxy | Plant public route | Plant implementation file |
|---|---|---|---|---|
| Hired-agent skills list | `src/CP/FrontEnd/src/services/agentSkills.service.ts` | `src/CP/BackEnd/api/cp_skills.py` | `GET /api/v1/hired-agents/{hired_instance_id}/skills` | `src/Plant/BackEnd/api/v1/agent_skills.py` |
| Save customer skill config | `src/CP/FrontEnd/src/services/agentSkills.service.ts` | `src/CP/BackEnd/api/cp_skills.py` | `PATCH /api/v1/hired-agents/{hired_instance_id}/skills/{skill_id}/customer-config` | `src/Plant/BackEnd/api/v1/skill_configs.py` |
| Skill run history | CP consumer of `/api/cp/flow-runs` | `src/CP/BackEnd/api/cp_flow_runs.py` | `GET /api/v1/skill-runs`, `GET /api/v1/skill-runs/{skill_run_id}` | `src/Plant/BackEnd/api/v1/flow_runs.py` |
| Component run history | CP consumer of `/api/cp/component-runs` | `src/CP/BackEnd/api/cp_flow_runs.py` | `GET /api/v1/component-runs?flow_run_id=...` | `src/Plant/BackEnd/api/v1/flow_runs.py` |
| Approval queue | CP approvals panel | `src/CP/BackEnd/api/cp_approvals_proxy.py` | `GET /api/v1/hired-agents/{hired_agent_id}/deliverables?...` | `src/Plant/BackEnd/api/v1/deliverables_simple.py` |
| Approve/reject deliverable | CP approvals panel | `src/CP/BackEnd/api/cp_approvals_proxy.py` | `POST /api/v1/deliverables/{deliverable_id}/review` | `src/Plant/BackEnd/api/v1/deliverables_simple.py` |

### 5.3 Service Ownership Map

Use this table when deciding where a change belongs before you open any file.

| Domain | Primary responsibility | Edit here first | Route/API entrypoint | Test home |
|---|---|---|---|---|
| CP FrontEnd | Customer-facing web UX and request shaping | `src/CP/FrontEnd/src/pages/`, `src/CP/FrontEnd/src/services/` | Browser calls `/api/cp/...` or Gateway-backed endpoints | `src/CP/FrontEnd/src/__tests__/`, Playwright in `tests/` |
| CP BackEnd | Thin proxy and customer-auth support flows | `src/CP/BackEnd/api/`, `src/CP/BackEnd/services/plant_gateway_client.py` | `/api/cp/...` | `src/CP/BackEnd/tests/` |
| PP FrontEnd | Internal operator UX, governor/admin tools | `src/PP/FrontEnd/src/pages/`, `src/PP/FrontEnd/src/components/` | Browser calls `/pp/...` or PP proxy routes | `src/PP/FrontEnd/src/` tests |
| PP BackEnd | Operator thin proxy, admin workflows, observability hooks | `src/PP/BackEnd/api/`, `src/PP/BackEnd/clients/plant_client.py` | `/pp/...` | `src/PP/BackEnd/tests/` |
| Plant Gateway | Auth, RBAC, policy, audit, public ingress | `src/Plant/Gateway/main.py`, `src/Plant/Gateway/middleware/` | `/api/v1/...` public surface | `src/Plant/Gateway/tests/`, root `tests/` |
| Plant BackEnd | Runtime business logic, persistence, scheduling, approvals | `src/Plant/BackEnd/api/v1/`, `src/Plant/BackEnd/services/`, `src/Plant/BackEnd/models/` | Handlers behind Gateway `/api/v1/...` | `src/Plant/BackEnd/tests/` |
| Mobile | Customer mobile UX, direct Gateway consumption, device integrations | `src/mobile/src/` | Mostly Plant Gateway `/api/v1/...`, not CP BackEnd, unless a CP-only capability is required | `src/mobile/__tests__/`, `src/mobile/e2e/` |
| Terraform/Cloud Run | Environment wiring, service deployment, secrets injection, scaling | `cloud/terraform/`, `.github/workflows/waooaw-deploy.yml` | Cloud Run services + LB | Manual validation + targeted infra tests |

### 5.4 Ops, Infra, And Deployment Control Plane

These are the canonical files for delivery, environments, and operational behavior. If a task touches deployment or runtime wiring, start here before making service-level edits.

| Concern | Primary source files | Why these files matter | Edit rule |
|---|---|---|---|
| Local full-stack startup | `docker-compose.local.yml`, `start-local-no-docker.sh` | Defines local service topology and fallback non-Docker startup | Keep Docker as the default development path |
| Regression test topology | `docker-compose.test.yml`, `tests/` | Defines isolated test containers and cross-service checks | Never replace with venv-only commands |
| Mobile local/dev flow | `src/mobile/CODESPACE_DEV.md`, `src/mobile/start-codespace.sh`, `src/mobile/Dockerfile.test` | Owns mobile dev/test startup and Codespace behavior | Keep mobile instructions aligned with actual Expo/EAS files |
| CI validation | `.github/workflows/waooaw-ci.yml`, `.github/workflows/cp-pipeline.yml` | Gate lint, tests, and branch quality | CI edits must preserve Docker-first validation |
| Deploy + image promotion | `.github/workflows/waooaw-deploy.yml`, `cloud/terraform/`, §8.1 | Owns build once, promote unchanged flow | Never bake env-specific values into image or Dockerfile |
| Environment tfvars and scaling | `cloud/terraform/environments/`, `cloud/terraform/variables.tf` | Own safe defaults and per-env overrides | Defaults in `variables.tf`, overrides in tfvars |
| Service stacks | `cloud/terraform/stacks/` | Service-specific Cloud Run, secrets, env vars, IAM wiring | Avoid duplicating logic already present in modules/root |
| Monitoring assets | `infrastructure/monitoring/`, `cloud/monitoring/` | Prometheus, Grafana, alert rules, dashboards | Keep monitoring changes traceable to a service need |
| Supplemental Docker/K8s assets | `infrastructure/docker/`, `infrastructure/kubernetes/` | Secondary deployment/support assets outside the Cloud Run path | Treat as infra support, not the primary promotion path |

### 5.5 Logging, Metrics, And Debugging Spine

Start with these files when the problem is observability, production diagnosis, or request tracing.

| Capability | Primary files | What they own |
|---|---|---|
| Plant structured logging + PII masking | `src/Plant/BackEnd/core/logging.py` | Global logger setup and `PIIMaskingFilter` |
| Plant metrics and observability wiring | `src/Plant/BackEnd/core/metrics.py`, `src/Plant/BackEnd/core/observability.py` | Metrics export and observability bootstrap |
| Gateway operational middleware | `src/Plant/Gateway/middleware/audit.py`, `src/Plant/Gateway/middleware/error_handler.py`, `src/Plant/Gateway/middleware/circuit_breaker.py` | Audit trail, RFC 7807 errors, upstream protection |
| CP request correlation and audit | `src/CP/BackEnd/core/dependencies.py`, `src/CP/BackEnd/services/audit_dependency.py`, `src/CP/BackEnd/services/plant_gateway_client.py` | Correlation IDs, audit emission, gateway client resilience |
| PP tracing and metrics | `src/PP/BackEnd/core/observability.py`, `src/PP/BackEnd/core/metrics.py`, `src/PP/BackEnd/services/audit_dependency.py` | OTel spans, Prometheus metrics, PP audit integration |
| Infra monitoring and dashboards | `infrastructure/monitoring/`, `cloud/monitoring/` | Alert rules, dashboards, Prometheus/Grafana assets |
| Cloud Run / GCP diagnosis | §9, §21, §22 | Logs, service-account access, and standard recovery commands |

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

## 5.6 Platform NFR Standards — Mandatory Patterns for Every New Route

> **Full source of truth**: [`docs/CP/iterations/NFRReusable.md`](CP/iterations/NFRReusable.md)  
> This section is the quick-reference summary every agent needs before writing any API route.

### What is implemented (as of PRs #809, #810, #811 — 2026-02-27)

All NFR corrective (C1–C7) and preventive (P1–P4) gaps are closed. PP Backend baseline (P5) is in progress (PR #811). C8 (PII field-level DB encryption) is **permanently parked** — see rationale below.

### Mandatory: `waooaw_router()` — never bare `APIRouter()`

Every `api/` file in CP, Plant, and PP **must** use `waooaw_router()` instead of bare `APIRouter()`. Bare `APIRouter()` in `api/` directories is banned by `ruff` (TID251) in each service's `pyproject.toml` — it will fail CI.

```python
# ❌ FORBIDDEN in api/ directories
from fastapi import APIRouter
router = APIRouter(prefix="/agents", tags=["agents"])

# ✅ CORRECT
from core.routing import waooaw_router
router = waooaw_router(prefix="/agents", tags=["agents"])
```

`waooaw_router()` automatically injects `Depends(require_correlation_id)` on every route. Future platform-wide gates added to `core/routing.py` apply to every route with zero per-file changes.

| Service | Router factory file | Dependencies file |
|---------|--------------------|-----------------|
| CP BackEnd | `src/CP/BackEnd/core/routing.py` | `src/CP/BackEnd/core/dependencies.py` |
| Plant BackEnd | `src/Plant/BackEnd/core/routing.py` | `src/Plant/BackEnd/core/dependencies.py` |
| Plant Gateway | — (middleware-based) | `src/Plant/Gateway/core/dependencies.py` |
| PP BackEnd | `src/PP/BackEnd/core/routing.py` | `src/PP/BackEnd/core/dependencies.py` |

### Mandatory: Global `dependencies=[]` on FastAPI app

All four `FastAPI(...)` app instantiations have `dependencies=[Depends(require_correlation_id)]` wired at the app level. This runs on every request. Do not remove it.

### Mandatory: Correlation ID

`require_correlation_id` reads `X-Correlation-ID` from the incoming request (or generates a UUID4 if absent) and stores it in a `ContextVar`. All log records and outbound calls must carry the same ID.

```python
# Read the current correlation ID anywhere in a request lifecycle:
from core.dependencies import _correlation_id
cid = _correlation_id.get()  # returns str — never empty during a request
```

### Mandatory: Audit logging pattern (CP, PP)

Use `get_audit_logger` FastAPI dependency. Never call `AuditClient` directly from a route — always go through the dependency. All calls are fire-and-forget (never blocks response).

```python
from services.audit_dependency import AuditLogger, get_audit_logger

@router.post("/my-endpoint")
async def my_endpoint(
    body: MyRequest,
    audit: AuditLogger = Depends(get_audit_logger),  # add this
):
    result = await do_work(body)
    await audit.log("screen_name", "action_name", "success", user_id=..., email=...)
    return result
```

| Service | Audit dependency file |
|---------|---------------------|
| CP BackEnd | `src/CP/BackEnd/services/audit_dependency.py` |
| PP BackEnd | `src/PP/BackEnd/services/audit_dependency.py` |

### Mandatory: Read replica for read-only routes

Any endpoint that only reads data **must** use `get_read_db_session()`. Only write endpoints (INSERT/UPDATE/DELETE) use `get_db_session()`.

```python
# ❌ WRONG — hits primary for a read-only list
@router.get("/agents")
async def list_agents(db: AsyncSession = Depends(get_db_session)):
    ...

# ✅ CORRECT
@router.get("/agents")
async def list_agents(db: AsyncSession = Depends(get_read_db_session)):
    ...
```

### Mandatory: Circuit breaker on all upstream HTTP clients

All `httpx` calls to upstream services must go through a circuit breaker. The pattern:
- Class-level `CircuitBreaker` instance (shared across all requests, not per-request)
- 3 failures → OPEN; 30s recovery → HALF_OPEN; 1 success → CLOSED
- `ServiceUnavailableError` on OPEN → HTTP 503

| Client | Location | CB implemented? |
|--------|----------|:--------------:|
| CP `PlantGatewayClient` | `src/CP/BackEnd/services/plant_gateway_client.py` | ✅ |
| CP `PlantClient` | `src/CP/BackEnd/services/plant_client.py` | ✅ |
| PP `PlantAPIClient` | `src/PP/BackEnd/clients/plant_client.py` | ✅ (PP-N1) |
| Plant Gateway middleware | `src/Plant/Gateway/middleware/circuit_breaker.py` | ✅ (shared CB) |

### Mandatory: Feature flag dependency (do not route-check flags inline)

```python
# src/CP/BackEnd/api/feature_flag_dependency.py
# src/Plant/BackEnd/api/v1/feature_flag_dependency.py

from api.feature_flag_dependency import require_flag  # CP path

@router.post("/new-hire-wizard")
async def hire(
    _: bool = Depends(require_flag("new_hire_wizard")),  # 404 if flag off
):
    ...
```

### PII masking in logs — already active

`PIIMaskingFilter` is wired at the root logger in both CP and Plant backends. Emails appear as `j***@domain.com`, phones as `+91******4567`, IPs as `1.2.3.XXX`. Route code does not need to do anything — masking is automatic.

Debug tip: trace by `user_id` or `X-Correlation-ID` (never by email in logs — masked). DB still has plaintext email for lookups.

### C8 — PII field-level DB encryption: PERMANENTLY PARKED

**Decision**: Application-layer encrypt-on-write for `email`/`phone`/`full_name` is deferred indefinitely.

**Rationale**:
- Cloud SQL CMEK covers the disk/backup threat model (the only threat that field encryption would add protection against)
- PII masking in logs removes the Cloud Logging exposure risk
- `email_hash` index allows blind lookups without plaintext scanning
- GDPR erasure wipes all PII columns on demand
- Field encryption would break `WHERE email = ?` queries, admin tooling, and make incident debugging significantly harder

**Do not implement C8.** If a compliance audit specifically requires application-layer field encryption, re-open the discussion with the engineering team.

---

## 6. Service Communication & Data Flow

### Request flow (CP example)

```
User browser → CP Frontend (React)
  → CP Backend (FastAPI :8020)
    → Plant Gateway (FastAPI :8000)  [JWT validation, RBAC, policy, budget check]
      → Plant OPA (:8181)  [rbac_pp / trial_mode / governor_role / agent_budget / sandbox_routing]
      → Plant Backend (FastAPI :8001) [business logic, DB access]
        → PostgreSQL / Redis / External APIs
```

### CP Gateway → Plant Route Architecture (Construct-facing)

```
Customer App (mobile)
        │  JWT
        ▼
CP BackEnd ──── PlantGatewayClient ────► Plant Gateway
                                                │
                              ┌─────────────────┤
                              │  OPA checks:    │
                              │  trial_mode     │ → caps tasks_used ≤ 10
                              │  governor_role  │ → 5 sensitive actions need approval token
                              │  sandbox_routing│ → trial hires → Plant sandbox
                              └─────────────────┤
                                                │
                                                ▼
                                      Plant BackEnd
```

**Governor-gated CP routes** (require an approval token from `POST /pp/approvals`):

| CP Route | Governor reason |
|---|---|
| `POST /cp/trading/approve-execute` | Financial action — irreversible |
| `POST /cp/hired-agents/{id}/platform-connections` | OAuth credential storage |
| `DELETE /cp/hired-agents/{id}/platform-connections/{conn_id}` | Credential removal |
| `POST /cp/hire/wizard/finalize` | Subscription commitment |
| `PATCH /cp/hired-agents/{id}/skills/{skill_id}/goal-config` | Goal override in production |

### Key communication patterns

| Pattern | Detail |
|---------|--------|
| CP/PP → Gateway | HTTP proxy; CP/PP backends forward requests using `httpx` to `PLANT_GATEWAY_URL` |
| Gateway → Plant | HTTP proxy with identity token (GCP metadata server in Cloud Run, shared JWT in dev) |
| Gateway middleware order | Error handler → Auth → RBAC → Policy → Budget → Audit → Proxy |
| Gateway → OPA | `rbac.py`, `policy.py`, `budget.py` each make a `POST /v1/data/gateway/<policy>/allow` HTTP call to `OPA_URL`. OPA returns `{"result": {"allow": bool, ...}}`. Circuit breaker wraps every call. |
| Auth flow | Google OAuth2 → JWT issued by CP/PP → validated at Gateway → forwarded to Plant |
| Registration flow (web/CP) | CP Backend `/api/register` → creates customer in local DB → calls Plant Gateway `/api/v1/customers` to create in Plant DB |
| Registration flow (mobile) | Mobile app → Plant Gateway **directly** (no CP Backend). Three steps: `POST /auth/register` (upsert customer) → `POST /auth/otp/start` (issue OTP challenge) → `POST /auth/otp/verify` (verify code, receive JWT). All three paths are in `PUBLIC_ENDPOINTS` — no prior JWT needed. |
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
3. Build Docker images (parallel: CP-BE, CP-FE, PP-BE, PP-FE, Plant-BE, Plant-GW, Plant-OPA)
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
| Plant OPA | `src/Plant/Gateway/opa/Dockerfile` | `plant-opa` |
| CP Combined | `src/CP/Dockerfile.combined` | (BE+FE in one) |
| PP Combined | `src/PP/Dockerfile.combined` | (BE+FE in one) |

### Environments

| Environment | Domain (CP) | Domain (PP) | Scaling |
|-------------|-------------|-------------|---------|
| demo | cp.demo.waooaw.com | pp.demo.waooaw.com | min 0, max 2 (scale to zero) |
| uat | cp.uat.waooaw.com | pp.uat.waooaw.com | min 0, max 3 |
| prod | cp.waooaw.com | pp.waooaw.com | min 1, max 10 |

### 8.1 — Image Promotion & Secrets Mandate ⚠️ MANDATORY FOR ALL AGENTS

> **Read this before touching any Dockerfile, terraform file, Python config, or environment variable.**

**Rule**: ONE Docker image is built once and promoted **unchanged** through `demo → uat → prod`. The same binary runs in every environment. Environment-specific behaviour is controlled **entirely** by externally injected values — never by logic baked in at build time.

#### Where each type of value belongs

| Value type | Where it lives | Example |
|---|---|---|
| Sensitive credentials | **GCP Secret Manager** — `secrets {}` block in Cloud Run terraform | `JWT_SECRET`, `RAZORPAY_KEY_ID`, `CP_REGISTRATION_KEY`, SMTP username/password |
| Non-sensitive env-specific flags | **`environments/{env}.tfvars`** → wired as `env_vars` in `main.tf` | `PAYMENTS_MODE`, `OTP_DELIVERY_MODE`, `ENVIRONMENT`, `PLANT_GATEWAY_URL` |
| Python/JS code defaults | **`variables.tf` `default =`** for the fallback when a tfvar is omitted | `default = "razorpay"`, `default = "provider"` |
| Docker image contents | **Never** anything environment-specific | ❌ No env names, no URLs, no secrets, no feature flags |

#### Terraform template rules (violations will be reverted)

```hcl
# ✅ CORRECT — clean passthrough, no logic baked in
env_vars = {
  PAYMENTS_MODE   = var.payments_mode        # value comes from tfvars
  OTP_DELIVERY_MODE = var.otp_delivery_mode  # value comes from tfvars
}

# ❌ WRONG — baking environment-conditional logic into the template
env_vars = {
  PAYMENTS_MODE     = var.payments_mode != "" ? var.payments_mode : "razorpay"  # ternary = baked logic
  OTP_DELIVERY_MODE = var.mode != "" ? var.mode : (var.environment == "demo" ? "disabled" : "provider")  # worst case: env name in template
}
```

Defaults belong in `variables.tf` (`default = "razorpay"`), not in `main.tf` ternary expressions. The template must be brainless — it only passes `var.*` through.

#### Checklist before opening a PR that touches terraform or config

- [ ] No hardcoded `"demo"`, `"uat"`, `"prod"` strings in `main.tf` env_vars block
- [ ] No ternary expressions whose fallback encodes an environment name or a sensitive value
- [ ] All secrets are in `secrets {}` block (sourced from Secret Manager), not `env_vars {}`
- [ ] Every new env var has a corresponding `variable` entry in `variables.tf` with a safe `default`
- [ ] Every `environments/{env}.tfvars` explicitly sets the new variable (no silent reliance on `default`)
- [ ] The same image tag can be deployed to all three environments by changing only tfvars

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

- **Cloud Run** — 7 services (CP-BE, CP-FE, PP-BE, PP-FE, Plant-BE, Plant-GW, **Plant-OPA** `waooaw-plant-opa-{env}`)
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

### Codespace Service Account — `waooaw-codespace-reader`

> **AI agents in Codespace have permanent GCP access via this SA.** `gcloud auth list` should show it ACTIVE. If not, re-run `bash .devcontainer/gcp-auth.sh`.

| Property | Value |
|----------|-------|
| SA email | `waooaw-codespace-reader@waooaw-oauth.iam.gserviceaccount.com` |
| Key stored as | Codespace secret `GCP_SA_KEY` (personal, repo-scoped to `dlai-sd/WAOOAW`) |
| Key persisted at | `/root/.gcp/waooaw-sa.json` (written by `gcp-auth.sh` on boot) |
| Auto-activation | `.devcontainer/gcp-auth.sh` runs as `postCreateCommand` on every Codespace start |

#### SA granted roles

| Role | What it enables |
|------|-----------------|
| `roles/logging.viewer` | Read Cloud Logging — pull service logs for any log command |
| `roles/secretmanager.viewer` | List secrets in Secret Manager |
| `roles/secretmanager.secretAccessor` | **Read secret values** — `DB_URL`, `JWT_SECRET`, etc. |
| `roles/run.viewer` | Describe Cloud Run services, revisions, traffic |
| `roles/cloudsql.viewer` | List and describe Cloud SQL instances |
| `roles/cloudsql.client` | Connect to Cloud SQL via Cloud SQL Auth Proxy |
| `roles/cloudsql.admin` | Patch Cloud SQL instance settings (e.g. enable/disable public IP) |

#### Cloud SQL Proxy — permanent DB tunnel

- **Binary**: `/usr/local/bin/cloud-sql-proxy` (v2.14.2, auto-downloaded by `gcp-auth.sh` if missing)
- **Instance**: `waooaw-oauth:asia-south1:plant-sql-demo`
- **Port**: `127.0.0.1:15432`
- **Auth**: `--gcloud-auth` (uses active gcloud SA credentials)
- **Starts automatically** via `gcp-auth.sh` on Codespace boot
- **Log**: `/tmp/cloud-sql-proxy.log`
- **pgpass**: `/root/.pgpass` — enables passwordless `psql` (written by `gcp-auth.sh` from Secret Manager `demo-plant-database-url`)
- **DB env file**: `/root/.env.db` — `source /root/.env.db && psql` is all you need

**Quick connect:**
```bash
# Step 0 — if gcloud is missing (run ONCE per Codespace; takes ~60s)
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list
apt-get update -qq && apt-get install -y -qq google-cloud-cli

# Step 1 — run auth script (activates SA, downloads proxy binary, writes /root/.env.db)
bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh

# Step 2 — if proxy says "instance does not have IP of type PUBLIC":
#   The Cloud SQL instance needs public IP enabled (SA has cloudsql.admin):
gcloud sql instances patch plant-sql-demo --project=waooaw-oauth --assign-ip
#   Then re-run the auth script:
bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh

# Step 3 — connect
source /root/.env.db && psql          # recommended
psql -h 127.0.0.1 -p 15432 -U plant_app plant  # direct

# Verify
psql -h 127.0.0.1 -p 15432 -U plant_app plant -c "SELECT version_num FROM alembic_version;"
```

> **Public IP**: `plant-sql-demo` has public IP enabled (patched 8 Mar 2026 — SA has `cloudsql.admin`).
> If the proxy log ever shows `instance does not have IP of type "PUBLIC"` (e.g. after a Terraform refresh),
> re-run: `gcloud sql instances patch plant-sql-demo --assign-ip --project=waooaw-oauth`, wait ~30s, then restart the auth script.

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

### How to connect to demo DB from Codespace

Cloud SQL `plant-sql-demo` has **public IP enabled** (patched 8 Mar 2026). Access still goes through the
Cloud SQL Auth Proxy for IAM-based authentication — do not connect directly on port 5432.

| Property | Value |
|----------|-------|
| Instance | `waooaw-oauth:asia-south1:plant-sql-demo` |
| DB name | `plant` |
| DB user | `plant_app` |
| Local port | `15432` (via proxy) |
| Password | Stored in Secret Manager: `demo-plant-database-url` (special chars — handled by `gcp-auth.sh`) |
| pgpass | `/root/.pgpass` (auto-written by `gcp-auth.sh`) |
| env file | `/root/.env.db` — `source /root/.env.db && psql` is all you need |

> **demo@waooaw.com test customer** (inserted 8 Mar 2026): `id = ce8cf044-b378-4d3d-b11d-4817074b08f6`.
> Required for dev-token auth — Plant `/api/v1/auth/validate` looks up this email on every request.

#### Precise steps (follow in order, every step matters)

> **gcloud is pre-installed** in every Codespace via `setup-slim.sh` (added 8 Mar 2026).
> Step 1 below is only needed if you rebuilt the container without running `postCreateCommand`.

```bash
# 1. Install gcloud if missing (verify first: which gcloud)
#    Skip if 'gcloud version' already prints SDK 559+
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" > /etc/apt/sources.list.d/google-cloud-sdk.list
apt-get update -qq && apt-get install -y -qq google-cloud-cli
gcloud version   # should print SDK 559+

# 2. Run auth script — activates SA, starts proxy, writes /root/.env.db + /root/.pgpass
bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh
# Expected last line: "✅ DB ready — connect: source /root/.env.db && psql"

# 3. Connect and verify
source /root/.env.db && psql -c "SELECT version_num FROM alembic_version;"

# 4. Check number of customers (quick sanity check)
psql -c "SELECT COUNT(*) AS customers FROM customer_entity;"
# Expected: 4 (yogeshkhandge@gmail.com, rupalikhandge@gmail.com, yogeshk7377@gmail.com, demo@waooaw.com)

# --- Recovery steps (only needed if step 2 fails) ---

# If proxy log says "instance does not have IP of type PUBLIC" (public IP was disabled)
cat /tmp/cloud-sql-proxy.log   # check exact error
gcloud sql instances patch plant-sql-demo --assign-ip --project=waooaw-oauth
# Wait ~30s for the patch, then re-run step 2

# If proxy died between sessions, restart it:
kill $(pgrep cloud-sql-proxy) 2>/dev/null; bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh

# Proxy diagnostics
cat /tmp/cloud-sql-proxy.log        # full proxy log
pgrep -fa cloud-sql-proxy           # check PID — empty means proxy not running
```

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

- **Preferred (CI)**: Trigger `plant-db-migrations-job.yml` workflow (dispatches a Cloud Run job for `demo`/`uat`/`prod`)
- **Emergency / dev (Codespace)**: Run migration DDL directly via psql through the proxy

#### Running migrations via psql directly (when alembic unavailable)

> `alembic` is not installed in the Codespace venv — use psql with the migration DDL directly.
> All migration files are in `src/Plant/BackEnd/database/migrations/versions/`.

```bash
# 1. Ensure proxy is running + env loaded
source /root/.env.db

# 2. Check current migration level
psql -c "SELECT version_num FROM alembic_version;"

# 3. Write migrations to a .sql file, then execute
# Use IF NOT EXISTS / DO $$ guards (idempotent) — see examples in migrations/versions/*.py
# Pattern for each migration:
#   CREATE TABLE IF NOT EXISTS ...
#   DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='...') THEN ALTER TABLE ... ADD CONSTRAINT ...; END IF; END $$;
#   CREATE INDEX IF NOT EXISTS ...

# 4. Always update alembic_version at the end:
#   UPDATE alembic_version SET version_num = '023_performance_stats';

# 5. Run:
psql -f /tmp/my_migration.sql
```

#### Seeding `skill_entity` — CRITICAL: base_entity NOT NULL columns

`skill_entity` uses joined-table inheritance from `base_entity`. Both rows must be inserted.
`base_entity` has **18 NOT NULL columns** — use this exact template:

```sql
-- Idempotent pattern: upsert base_entity → upsert skill_entity in one CTE
WITH upserted_base AS (
    INSERT INTO base_entity (
        id, entity_type, external_id, governance_agent_id, status, version_hash,
        amendment_history, evolution_markers, l0_compliance_status, amendment_alignment,
        drift_detector, append_only, hash_chain_sha256, tamper_proof,
        tags, custom_attributes, child_ids, created_at, updated_at
    ) VALUES (
        gen_random_uuid(), 'Skill', 'my-skill-external-id', 'genesis', 'active', 'initial',
        '[]'::json, '{}'::json, '{}'::json, 'aligned',
        '{}'::json, true, '{}', true,
        '{domain_expertise}', '{}'::json, '{}', now(), now()
    )
    ON CONFLICT (external_id) DO UPDATE SET updated_at = now()
    RETURNING id
)
INSERT INTO skill_entity (id, name, description, category, goal_schema)
SELECT id, 'Skill Name', 'Description.', 'domain_expertise', '{...}'::jsonb
FROM upserted_base
ON CONFLICT (id) DO UPDATE SET goal_schema = EXCLUDED.goal_schema;
```

> **Do NOT** use `INSERT INTO base_entity ... INSERT INTO skill_entity ...` as two separate statements
> without the CTE — the skill row will fail with `null value in column "version_hash"` (or similar).

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

### DB changes — PP Portal management screen (stop-gap)

As a stop-gap arrangement, the platform has provisioned a fast way to make DB changes via the PP portal's **DB Management screen**. This screen has a text box that executes one SQL statement at a time.

**Use this screen for any DB-related changes — DDL (CREATE TABLE, ALTER TABLE, CREATE INDEX) or data (INSERT, UPDATE, DELETE) — on Demo, UAT, or Prod databases.**

Steps:
1. Open the PP portal → DB Management screen
2. Paste one SQL statement at a time into the text box
3. Execute and verify the response before running the next statement
4. Always run statements in migration order (lowest number first)

#### Current demo DB schema — all tables & indexes

| Table | Index name | Type | Columns |
|-------|-----------|------|---------|
| `agent_entity` | `agent_entity_pkey` | UNIQUE | `id` |
| `agent_entity` | `agent_entity_name_key` | UNIQUE | `name` |
| `agent_entity` | `ix_agent_industry_id` | INDEX | `industry_id` |
| `agent_entity` | `ix_agent_name` | INDEX | `name` |
| `agent_type_definitions` | `agent_type_definitions_pkey` | UNIQUE | `id` |
| `agent_type_definitions` | `uq_agent_type_id_version` | UNIQUE | `agent_type_id, version` |
| `agent_type_definitions` | `ix_agent_type_definitions_agent_type_id` | INDEX | `agent_type_id` |
| `alembic_version` | `alembic_version_pkc` | UNIQUE | `version_num` |
| `approvals` | `approvals_pkey` | UNIQUE | `approval_id` |
| `approvals` | `ix_approvals_customer` | INDEX | `customer_id` |
| `approvals` | `ix_approvals_deliverable` | INDEX | `deliverable_id` |
| `audit_logs` | `pk_audit_logs` | UNIQUE | `id` |
| `audit_logs` | `idx_audit_logs_action` | INDEX | `action` |
| `audit_logs` | `idx_audit_logs_correlation_id` | INDEX | `correlation_id` |
| `audit_logs` | `idx_audit_logs_email` | INDEX | `email` |
| `audit_logs` | `idx_audit_logs_screen` | INDEX | `screen` |
| `audit_logs` | `idx_audit_logs_timestamp` | INDEX | `timestamp DESC` |
| `audit_logs` | `idx_audit_logs_user_id` | INDEX | `user_id` |
| `base_entity` | `base_entity_pkey` | UNIQUE | `id` |
| `base_entity` | `base_entity_external_id_key` | UNIQUE | `external_id` |
| `base_entity` | `ix_base_entity_created_at` | INDEX | `created_at` |
| `base_entity` | `ix_base_entity_entity_type` | INDEX | `entity_type` |
| `base_entity` | `ix_base_entity_governance_agent_id` | INDEX | `governance_agent_id` |
| `base_entity` | `ix_base_entity_status` | INDEX | `status` |
| `customer_entity` | `customer_entity_pkey` | UNIQUE | `id` |
| `customer_entity` | `customer_entity_email_key` | UNIQUE | `email` |
| `customer_entity` | `uq_customer_phone` | UNIQUE | `phone` |
| `customer_entity` | `ix_customer_email` | INDEX | `email` |
| `customer_entity` | `ix_customer_phone` | INDEX | `phone` |
| `customer_entity` | `ix_customer_email_hash` | INDEX | `email_hash` |
| `deliverables` | `deliverables_pkey` | UNIQUE | `deliverable_id` |
| `deliverables` | `ix_deliverables_goal_instance` | INDEX | `goal_instance_id` |
| `deliverables` | `ix_deliverables_hired_instance_created` | INDEX | `hired_instance_id, created_at` |
| `deliverables` | `ix_deliverables_hired_instance_id` | INDEX | `hired_instance_id` |
| `deliverables` | `ix_deliverables_review_status` | INDEX | `review_status` |
| `feature_flags` | `pk_feature_flags` | UNIQUE | `key` |
| `feature_flags` | `ix_feature_flags_scope` | INDEX | `scope` |
| `gateway_audit_logs` | `gateway_audit_logs_pkey` | UNIQUE | `id` |
| `gateway_audit_logs` | `idx_audit_action_resource` | INDEX | `action, resource` |
| `gateway_audit_logs` | `idx_audit_causation_id` | INDEX | `causation_id` (partial: NOT NULL) |
| `gateway_audit_logs` | `idx_audit_correlation_id` | INDEX | `correlation_id` |
| `gateway_audit_logs` | `idx_audit_customer_id` | INDEX | `customer_id` (partial: NOT NULL) |
| `gateway_audit_logs` | `idx_audit_customer_timestamp` | INDEX | `customer_id, timestamp DESC` (partial: NOT NULL) |
| `gateway_audit_logs` | `idx_audit_errors` | INDEX | `status_code, error_type` (partial: status_code >= 400) |
| `gateway_audit_logs` | `idx_audit_gateway_type` | INDEX | `gateway_type` |
| `gateway_audit_logs` | `idx_audit_opa_decisions` | GIN | `opa_decisions` |
| `gateway_audit_logs` | `idx_audit_timestamp` | INDEX | `timestamp DESC` |
| `gateway_audit_logs` | `idx_audit_user_id` | INDEX | `user_id` |
| `gateway_audit_logs` | `idx_audit_user_timestamp` | INDEX | `user_id, timestamp DESC` |
| `goal_instances` | `uq_goal_instance_id` | UNIQUE | `goal_instance_id` |
| `goal_instances` | `ix_goal_instances_hired_instance_id` | INDEX | `hired_instance_id` |
| `hired_agents` | `hired_agents_pkey` | UNIQUE | `hired_instance_id` |
| `hired_agents` | `ix_hired_agents_subscription_id` | UNIQUE | `subscription_id` |
| `hired_agents` | `ix_hired_agents_agent_id` | INDEX | `agent_id` |
| `hired_agents` | `ix_hired_agents_customer_id` | INDEX | `customer_id` |
| `hired_agents` | `ix_hired_agents_trial_status` | INDEX | `trial_status` |
| `industry_entity` | `industry_entity_pkey` | UNIQUE | `id` |
| `industry_entity` | `industry_entity_name_key` | UNIQUE | `name` |
| `industry_entity` | `industry_embedding_ivfflat_idx` | IVFFLAT | `embedding_384 vector_cosine_ops` (lists=100) |
| `industry_entity` | `ix_industry_embedding` | IVFFLAT | `embedding_384 vector_cosine_ops` |
| `industry_entity` | `ix_industry_name` | INDEX | `name` |
| `job_role_entity` | `job_role_entity_pkey` | UNIQUE | `id` |
| `job_role_entity` | `job_role_entity_name_key` | UNIQUE | `name` |
| `job_role_entity` | `ix_job_role_industry_id` | INDEX | `industry_id` |
| `job_role_entity` | `ix_job_role_name` | INDEX | `name` |
| `job_role_entity` | `ix_job_role_seniority_level` | INDEX | `seniority_level` |
| `otp_sessions` | `pk_otp_sessions` | UNIQUE | `otp_id` |
| `otp_sessions` | `ix_otp_sessions_destination` | INDEX | `destination` |
| `otp_sessions` | `ix_otp_sessions_expires_at` | INDEX | `expires_at` |
| `otp_sessions` | `ix_otp_sessions_registration_id` | INDEX | `registration_id` |
| `otp_sessions` | `ix_otp_sessions_verified_at` | INDEX | `verified_at` |
| `skill_entity` | `skill_entity_pkey` | UNIQUE | `id` |
| `skill_entity` | `skill_entity_name_key` | UNIQUE | `name` |
| `skill_entity` | `skill_embedding_ivfflat_idx` | IVFFLAT | `embedding_384 vector_cosine_ops` (lists=100) |
| `skill_entity` | `ix_skill_embedding` | IVFFLAT | `embedding_384 vector_cosine_ops` |
| `skill_entity` | `ix_skill_category` | INDEX | `category` |
| `skill_entity` | `ix_skill_name` | INDEX | `name` |
| `subscriptions` | `subscriptions_pkey` | UNIQUE | `subscription_id` |
| `subscriptions` | `ix_subscriptions_agent_id` | INDEX | `agent_id` |
| `subscriptions` | `ix_subscriptions_customer_id` | INDEX | `customer_id` |
| `subscriptions` | `ix_subscriptions_status` | INDEX | `status` |
| `team_entity` | `team_entity_pkey` | UNIQUE | `id` |
| `team_entity` | `team_entity_name_key` | UNIQUE | `name` |
| `team_entity` | `ix_team_job_role_id` | INDEX | `job_role_id` |
| `team_entity` | `ix_team_name` | INDEX | `name` |
| `trial_deliverables` | `trial_deliverables_pkey` | UNIQUE | `id` |
| `trial_deliverables` | `idx_trial_deliverables_created_at` | INDEX | `created_at` |
| `trial_deliverables` | `idx_trial_deliverables_trial_id` | INDEX | `trial_id` |
| `trials` | `trials_pkey` | UNIQUE | `id` |
| `trials` | `idx_trials_agent_id` | INDEX | `agent_id` |
| `trials` | `idx_trials_customer_email` | INDEX | `customer_email` |
| `trials` | `idx_trials_start_date` | INDEX | `start_date` |
| `trials` | `idx_trials_status` | INDEX | `status` |

> Last verified: 2026-02-26 against demo DB. Re-run the query in section "DB changes" to refresh this table after any DDL change.

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
| **Property-based** | Plant Backend | `src/Plant/BackEnd/tests/property/` | pytest + Hypothesis | `plant-backend-test` | Invariant proofs: usage ledger, trial billing, hash chain |
| **BDD** | Plant BackEnd, CP BackEnd | `src/Plant/BackEnd/tests/bdd/`, `src/CP/BackEnd/tests/bdd/` | pytest-bdd | `plant-backend-test`, `cp-backend-test` | Gherkin feature specs (trial lifecycle, hire wizard) |
| **Contract (Pact)** | CP→Gateway, PP→Gateway, Mobile→Gateway | `src/CP/BackEnd/tests/pact/consumer/`, `src/Plant/Gateway/tests/pact/provider/` | pact-python | `cp-backend-test`, `plant-gateway-test` | Consumer/provider contract tests |
| **Web E2E** | CP+PP+Plant stack | `tests/e2e/web/auth/`, `tests/e2e/web/hire/`, `tests/e2e/web/admin/` | Playwright | `playwright` | OTP auth, hire wizard, PP agent approval journeys |
| **Mobile E2E** | Mobile | `tests/e2e/mobile/` | Maestro | `maestro` | OTP auth, hire agent, browse agents (YAML-driven) |
| **Performance** | Plant Gateway | `tests/performance/` | Locust | `locust` | p95 < 500 ms @ 50 rps, trial concurrency |
| **Security SAST** | All Python | via `scripts/security-scan.sh` | Bandit + Safety + Semgrep | Any | High-severity findings block CI |

### Docker-based test infrastructure

| File | Purpose |
|------|--------|
| `tests/docker-compose.test.yml` | Isolated test stack (postgres-test on :5433, redis-test on :6380) |
| `tests/Dockerfile.test` | Test runner image (Python 3.11 + git + test deps) |
| `tests/requirements.txt` | Test-specific Python dependencies |
| `docker-compose.local.yml` → `cp-frontend-test` | CP frontend test container (Vitest) |
| `docker-compose.local.yml` → `pp-frontend-test` | PP frontend test container (Vitest) |
| `docker-compose.test.yml` | **Dedicated regression test stack** — includes plant-backend-test, cp-backend-test, pp-backend-test, playwright, maestro, locust, zap services |
| `scripts/test-web.sh` | Convenience wrapper — runs full or `--quick` web regression via docker-compose.test.yml |
| `scripts/test-mobile.sh` | Convenience wrapper — runs mobile regression (Jest + Maestro) |
| `.github/workflows/waooaw-regression.yml` | Manual `workflow_dispatch` regression — 9 stages, `scope=full\|quick` |
| `.github/workflows/mobile-regression.yml` | Manual `workflow_dispatch` mobile regression — 6 stages |

### Running tests (Docker-only)

```bash
# --- Quick per-PR smoke (run BEFORE pushing) ---
docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest src/Plant/BackEnd/tests/ -x -q
docker compose -f docker-compose.test.yml run --rm cp-backend-test pytest src/CP/BackEnd/tests/ -x -q

# --- Backend unit + API (full) ---
docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest src/Plant/BackEnd/tests/unit/ -m "unit or api" -v
docker compose -f docker-compose.test.yml run --rm cp-backend-test pytest src/CP/BackEnd/tests/ -m "unit or api" -v
docker compose -f docker-compose.test.yml run --rm pp-backend-test pytest src/PP/BackEnd/tests/ -m "unit or api" -v

# --- Property-based tests ---
docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest -m property -v

# --- BDD feature specs ---
docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest -m bdd
docker compose -f docker-compose.test.yml run --rm cp-backend-test pytest -m bdd

# --- Integration tests (needs postgres+redis) ---
docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest -m integration -v

# --- Contract / Pact tests ---
docker compose -f docker-compose.test.yml run --rm cp-backend-test pytest src/CP/BackEnd/tests/pact/consumer/
docker compose -f docker-compose.test.yml run --rm plant-gateway-test pytest src/Plant/Gateway/tests/pact/provider/

# --- Web E2E (Playwright) ---
docker compose -f docker-compose.test.yml run playwright npx playwright test

# --- Mobile E2E (Maestro) ---
docker compose -f docker-compose.test.yml run maestro maestro test tests/e2e/mobile/auth_otp.yaml

# --- Performance (Locust) ---
docker compose -f docker-compose.test.yml run locust --headless -u 50 -r 5 --run-time 60s

# --- Security scan (SAST) ---
bash scripts/security-scan.sh

# --- Full regression (local, all stages) ---
bash scripts/test-web.sh
bash scripts/test-mobile.sh

# --- Quick regression (skip perf + mutation) ---
bash scripts/test-web.sh --quick

# --- Legacy Codespace shortcuts (still work) ---
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

### Regression testing per iteration — MANDATORY

> **Every iteration PR that merges to `main` requires the steps below.** Run the smoke + unit check *before* opening a PR, and the doc update *immediately after* merging. Do NOT wait for an epic or story to complete — update after each iteration.

#### Before merging (developer gate — run in Codespace)

```bash
# 1. Smoke: all services pass, no regression introduced
docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest src/Plant/BackEnd/tests/ -x -q
docker compose -f docker-compose.test.yml run --rm cp-backend-test pytest src/CP/BackEnd/tests/ -x -q

# 2. If the iteration touches Plant BE models/migration:
docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest -m integration -v

# 3. If the iteration touches CP FrontEnd components:
docker compose -f docker-compose.test.yml run --rm cp-frontend-test npx vitest run --reporter verbose
```

#### After merging (PM/developer — update docs)

1. **Open `docs/testing/ExistingTestAssets.md`** and update the service row(s) affected:
   - Increment the test file count
   - List the new test file path and what it covers
   - Update the `Last updated` field to the merged PR number

2. **Add a row to §12 "Latest Changes & Recent PRs"** in this file (the normal process).

3. **If a new test type was introduced** (BDD spec, property test, Pact consumer, Playwright spec):
   - Update the relevant Epic story status in `docs/testing/TestingEpics.md` to ✅ Done

#### What to check per change type

| Change in the iteration | Required test check | Doc to update |
|------------------------|---------------------|---------------|
| New Plant BE model/migration | `pytest -m integration` — verify migration columns exist | `ExistingTestAssets.md` Plant BE row |
| New Plant BE endpoint | Unit test file in `tests/unit/` + Plant Gateway policy test | `ExistingTestAssets.md` Plant BE + Gateway rows |
| New CP BE proxy route | Unit test in `src/CP/BackEnd/tests/` | `ExistingTestAssets.md` CP BE row |
| New CP FE component | React component test in `src/CP/FrontEnd/src/__tests__/` | `ExistingTestAssets.md` CP FE row |
| New service/env flag (Terraform) | No test required — document in §12 as config change | §12 table |
| Alembic migration | Assert new columns present in `test_alembic_migrations.py` | `ExistingTestAssets.md` Plant BE row |
| Gateway RBAC policy change | Update `src/Plant/Gateway/middleware/tests/test_proxy.py` allowed paths | `ExistingTestAssets.md` Gateway row |

---

## 12. Latest Changes & Recent PRs

> **⚠️ UPDATE THIS SECTION DAILY**

### Current branch: `main` (PP-MOULD-1 construct diagnostic toolkit + MOULD-GAP-1 docs merged — 2026-03-07)

### Recently merged — 2026-03-07

| PR | Branch | Summary | Key files |
|----|--------|---------|----------|
| **#885** | `docs/mould-gap-1-plan` | **MOULD-GAP-1 iteration plan** — `docs/PP/iterations/MOULD-GAP-1-construct-hardening.md`; covers E1 (LifecycleHooks), E2 (ConstraintPolicy enforcement), E3 (HiredAgentsListScreen discriminator), E4 (mobile notifications per agent), E5 (DeltaTradeAdapter), E6 (PP HiredAgentsOps deep-links); skeleton + all 6 epics committed incrementally. | `docs/PP/iterations/MOULD-GAP-1-construct-hardening.md` |
| **#884** | `copilot/execute-iteration-2-epics-e4-e5` | **PP-MOULD-1 Iteration 2: ConstructHealthPanel, SchedulerDiagnosticsPanel, HookTracePanel** — PP FrontEnd diagnostic trio: 6-card construct health drawer, scheduler detail tab (cron + lag + DLQ), hook trace table (last 50 events); PP Backend `ops_hired_agents.py` with `GET /pp/ops/hired-agents/{id}/construct-health`, `.../scheduler-diagnostics`, `.../hook-trace`; ConstraintPolicyLiveTuneDrawer + `PATCH .../constraint-policy`; React Query hooks for all 3 endpoints. | `src/PP/BackEnd/api/ops_hired_agents.py`, `src/PP/FrontEnd/src/components/ConstructHealthPanel.tsx`, `src/PP/FrontEnd/src/components/SchedulerDiagnosticsPanel.tsx`, `src/PP/FrontEnd/src/components/HookTracePanel.tsx`, `src/PP/FrontEnd/src/components/ConstraintPolicyLiveTuneDrawer.tsx` |
| **#883** | `copilot/execute-iteration-1-epics-pp-mould` | **PP-MOULD-1 Iteration 1: DLQ console + RBAC** — `ops_dlq.py` routes (`GET /pp/ops/dlq`, `POST .../requeue`); `core/authorization.py` with 7-role hierarchy + `require_role(min_role)` FastAPI dependency. | `src/PP/BackEnd/api/ops_dlq.py`, `src/PP/BackEnd/core/authorization.py` |

### Recently merged — 2026-03-06

| PR | Branch | Summary | Key files |
|----|--------|---------|----------|
| **#872** | `copilot/execute-iteration-4-epics-e7-e8` | **PLANT-CONTENT-1 Iteration 4: skill registration + CP campaign proxy** — Registers `content.creator.v1` and `content.publisher.v1` in `agent_mold/registry.py`; CP BackEnd thin proxy `api/campaigns.py` exposes 8 campaign endpoints to the CP FrontEnd; router registered in `main_proxy.py`. | `src/Plant/BackEnd/agent_mold/registry.py`, `src/CP/BackEnd/api/campaigns.py`, `src/CP/BackEnd/main_proxy.py`, `src/CP/BackEnd/tests/test_campaigns_proxy.py` |
| **#871** | `copilot/execute-iteration-3-epics` | **PLANT-CONTENT-1 Iteration 3: publisher engine + publish API** — Plug-and-play `DestinationAdapter` ABC + `DestinationRegistry` + `PublisherEngine`; `SimulatedAdapter` for Phase 1; `POST /api/v1/campaigns/{id}/posts/{post_id}/publish` route; campaign status advances to `published`. | `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py`, `src/Plant/BackEnd/agent_mold/skills/adapters_publish.py`, `src/Plant/BackEnd/api/v1/campaigns.py` (extended), `src/Plant/BackEnd/tests/test_publisher_engine.py` |
| **#870** | `copilot/execute-iteration-2-epics-e3-e4` | **PLANT-CONTENT-1 Iteration 2: campaign orchestration API** — 8-endpoint campaign REST API (`POST /campaigns`, `GET /campaigns`, `GET /campaigns/{id}`, `POST .../approve-themes`, `POST .../posts/generate`, `POST .../posts/{id}/approve`, `GET /posts`) backed by in-memory dicts; auth via `Authorization` header passthrough. | `src/Plant/BackEnd/api/v1/campaigns.py` (created), `src/Plant/BackEnd/main.py` (router registered), `src/Plant/BackEnd/tests/test_campaigns_api.py` |
| **#869** | `copilot/execute-iteration-1-epics-e1-e2` | **PLANT-CONTENT-1 Iteration 1: content campaign models + cost estimator + ContentCreatorSkill** — `content_models.py` with 9 Pydantic models (`Campaign`, `DailyThemeItem`, `ContentPost`, `CampaignBrief`, `CostEstimate`, enums) + pure-function `estimate_cost()`; `ContentCreatorSkill` using deterministic templates (or Grok when `EXECUTOR_BACKEND=grok`); `grok_client.py` thin OpenAI-SDK-compatible Grok client. | `src/Plant/BackEnd/agent_mold/skills/content_models.py`, `src/Plant/BackEnd/agent_mold/skills/content_creator.py`, `src/Plant/BackEnd/agent_mold/skills/grok_client.py`, `src/Plant/BackEnd/tests/test_content_models.py`, `src/Plant/BackEnd/tests/test_content_creator.py` |
| **#868** | `feat/mobile-nfr-1-hardening` | **MOBILE-NFR-1 both iterations: Sentry + resilience retries + auth throttle + Apple Sign-In** — Sentry real `@sentry/react-native` import wired per-environment (env-gated DSN); React Query hooks in `useHiredAgents`, `useAgents`, `useAgentDetail`, `useAgentTypes` now use exponential back-off `retryDelay`; `cpApiClient.ts` response interceptor retries 429/5xx ≤ 3 times; submit throttle (2s cooldown) on Sign-Up + 60s OTP resend timer; iOS EAS build profile + `expo-apple-authentication` Apple Sign-In button. | `src/mobile/src/config/sentry.config.ts`, `src/mobile/src/lib/cpApiClient.ts`, `src/mobile/src/hooks/useHiredAgents.ts`, `src/mobile/src/hooks/useAgents.ts`, `src/mobile/src/hooks/useAgentDetail.ts`, `src/mobile/src/hooks/useAgentTypes.ts`, `src/mobile/src/screens/auth/SignUpScreen.tsx`, `src/mobile/src/screens/auth/OTPVerificationScreen.tsx`, `src/mobile/eas.json` |
| **#867** | `feat/mobile-func-1-iteration-3` | **MOBILE-FUNC-1 Iteration 3: payment screens + push notifications** — `useRazorpay.ts` hook with real `RazorpayCheckout` SDK (not stub); `PaymentMethodsScreen.tsx` wired with Razorpay; `NotificationsScreen.tsx` shows notification preferences; mobile app calls `POST /api/v1/customers/fcm-token` (Plant Backend, S8b) after sign-in to store FCM token for push delivery. | `src/mobile/src/hooks/useRazorpay.ts`, `src/mobile/src/screens/profile/PaymentMethodsScreen.tsx`, `src/mobile/src/screens/profile/NotificationsScreen.tsx`, `src/mobile/src/services/notifications/pushNotifications.service.ts`, `src/mobile/src/stores/authStore.ts` |
| **#866** | `feat/plant-backend-fcm-token` | **MOBILE-FUNC-1 S8a: FCM token storage endpoint (Plant BackEnd)** — `POST /api/v1/customers/fcm-token` authenticated route stores device FCM token against the customer record; required for push notification delivery. | `src/Plant/BackEnd/api/v1/customers.py` (extended), `src/Plant/BackEnd/tests/unit/test_fcm_token.py` |
| **#865** | `feat/mobile-func-1-iteration-2` | **MOBILE-FUNC-1 Iteration 2: MyAgents screens + Razorpay enabled** — `MyAgentsScreen.tsx`, `HiredAgentsListScreen.tsx`, `ActiveTrialsListScreen.tsx` fully wired to Plant Gateway; `razorpay.service.ts` real SDK import restored (was commented out); `SubscriptionManagementScreen.tsx` + `HelpCenterScreen.tsx` created. | `src/mobile/src/screens/agents/MyAgentsScreen.tsx`, `src/mobile/src/screens/agents/HiredAgentsListScreen.tsx`, `src/mobile/src/screens/agents/ActiveTrialsListScreen.tsx`, `src/mobile/src/services/payment/razorpay.service.ts`, `src/mobile/src/screens/profile/SubscriptionManagementScreen.tsx`, `src/mobile/src/screens/profile/HelpCenterScreen.tsx` |
| **#864** | `copilot/execute-iteration-1-epics-again` | **MOBILE-FUNC-1 Iteration 1: real deliverables + profile fix + discover screens** — `TrialDashboardScreen.tsx` uses real `GET /api/v1/deliverables` via React Query (replaces mock); `EditProfileScreen.tsx` calls Plant Gateway `PATCH /api/v1/customers/profile` (not CP Backend); `SearchResultsScreen.tsx`, `FilterAgentsScreen.tsx`, `SettingsScreen.tsx`, `ProfileScreen.tsx` created and registered in `MainNavigator`; index barrel exports added. | `src/mobile/src/screens/agents/TrialDashboardScreen.tsx`, `src/mobile/src/screens/profile/EditProfileScreen.tsx`, `src/mobile/src/screens/discover/SearchResultsScreen.tsx`, `src/mobile/src/screens/discover/FilterAgentsScreen.tsx`, `src/mobile/src/screens/profile/SettingsScreen.tsx`, `src/mobile/src/navigation/MainNavigator.tsx`, `src/mobile/src/navigation/types.ts` |

### Recently merged — 2026-03-04/05

| PR | Branch | Summary | Key files |
|----|--------|---------|----------|
| **#863** | `copilot/execute-iteration-2-epics-again` | **PP-NFR-1 Iteration 2: config dedup + OTel spans + Prometheus metrics + deep health probe** — PP Backend settings deduplication; per-route OTel spans; Prometheus counter/histogram in `core/metrics.py`; deep health endpoint checks DB + Redis + Plant Gateway reachability. | `src/PP/BackEnd/core/config.py`, `src/PP/BackEnd/core/observability.py`, `src/PP/BackEnd/core/metrics.py`, `src/PP/BackEnd/api/health.py` |
| **#862** | `copilot/execute-iteration-1-epics-again` | **PP-NFR-1 Iteration 1: secrets safety + Terraform alignment + PII masking + audit wiring + env gates** — PP Backend `PIIMaskingFilter` on all loggers; `AuditLogger` dependency wired into remaining routes; `ENVIRONMENT` env var propagated through PP Terraform; PAYMENTS_MODE env gate added. | `src/PP/BackEnd/core/logging.py`, `src/PP/BackEnd/api/*.py`, `cloud/terraform/stacks/pp/main.tf` |
| **#860** | `copilot/execute-iteration-2-epics` | **PP-FUNC-1 Iteration 2: Redis response caching for ops proxy routes** — `POST /pp/agents` and related ops routes now cache responses in Redis (TTL 60s); reduces Plant Gateway load for list endpoints. | `src/PP/BackEnd/api/agents.py`, `src/PP/BackEnd/core/redis_cache.py` |
| **#859** | `copilot/execute-iteration-1-epics` | **PP-FUNC-1 Iteration 1: PP ops screens live data** — subscriptions and hired-agents proxy routes in PP Backend, wired to PP FrontEnd `HiredAgentsOps` and `Billing` pages. | `src/PP/BackEnd/api/subscriptions.py`, `src/PP/BackEnd/api/hired_agents.py`, `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx`, `src/PP/FrontEnd/src/pages/Billing.tsx` |
| **#858** | `fix/cp-frontend-form-pattern-a` | **CP FrontEnd form field standardisation** — all form inputs normalised to Pattern A (consistent label + input layout). | `src/CP/FrontEnd/src/pages/*.tsx` |
| **#856–857** | `perf/deploy-pipeline-parallel` | **Deploy pipeline parallelisation** — split build-plant; fix Dockerfile AS casing; parallel scans + builds + health checks; ~14 min → ~5-6 min total. | `.github/workflows/waooaw-deploy.yml` |
| **#855** | `fix/ui-coupon-signout-signin` | **Coupon checkout fix + signout redirect + 6-digit OTP** — coupon validation 403 fixed; signout now redirects to `/signin`; OTP input widened to 6 digits. | `src/CP/FrontEnd/src/components/BookingModal.tsx`, `src/CP/FrontEnd/src/pages/SignIn.tsx`, `src/CP/FrontEnd/src/pages/SignUp.tsx` |
| **#854** | `fix/razorpay-receipt-length-plant` | **Razorpay receipt length fix** — Plant payments truncates `receipt` to 40 chars max (Razorpay limit). | `src/Plant/BackEnd/api/v1/payments_simple.py` |
| **#853** | `docs/session-commentary-agent-protocol` | **Session commentary protocol** — §25 added to CONTEXT_AND_INDEX.md; `session_commentary.md` format defined; recovery procedure for reconnecting agents. | `docs/CONTEXT_AND_INDEX.md` |
| **#852** | `fix/portal-nav-and-payments-mode-cp` | **Portal nav + Razorpay payment methods + Terraform** — Sidebar nav visible on `/discover` and `/agent/*`; Razorpay methods picker enabled; PAYMENTS_MODE Terraform fix. | `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx`, `src/CP/FrontEnd/src/components/BookingModal.tsx` |
| **#851** | `fix/portal-nav-and-payments-mode-cp` | **CP Backend PAYMENTS_MODE Terraform fix** — removed ternary env-baking anti-pattern (§17 violation) from CP stack's `main.tf`. | `cloud/terraform/stacks/cp/main.tf` |
| **#848–850** | `fix/cp-auth-*` | **CP auth stability** — stable Plant UUID as JWT `sub`; Google login loop fixed; agent detail infinite spinner; coupon 403 + OTP UUID fix. | `src/CP/BackEnd/api/auth/`, `src/CP/FrontEnd/src/pages/AgentDetail.tsx` |

### Recently merged — 2026-03-03

| PR | Branch | Summary | Key files |
|----|--------|---------|----------|
| **#843** | `feat/PLANT-OPA-1-it1-e1` | **PLANT-OPA-1 Iteration 1: OPA Rego bundle + Dockerfile + CI gate** — 5 Rego policy files (`rbac_pp`, `trial_mode`, `governor_role`, `agent_budget`, `sandbox_routing`) + 24 unit tests; OPA Dockerfile (build-once, policies baked in, port 8181); `opa-policy-test` CI job using static OPA binary download (replaces fragile Docker bind-mount pattern). | `src/Plant/Gateway/opa/policies/` (5 files), `src/Plant/Gateway/opa/tests/` (5 files), `src/Plant/Gateway/opa/Dockerfile`, `src/Plant/Gateway/opa/.dockerignore`, `.github/workflows/waooaw-ci.yml` |
| **#845** | `fix/PLANT-OPA-1-it2-to-main` | **PLANT-OPA-1 Iteration 2: Terraform Cloud Run + deploy pipeline** — `module "plant_opa"` Cloud Run service (stateless, port 8181, 0.5 CPU, 256 Mi, `allow_unauthenticated=false`); `google_cloud_run_v2_service_iam_member.plant_opa_invoker` grants plant_gateway_sa `roles/run.invoker`; OPA_URL wired to `module.plant_opa.service_url` (removes TODO placeholder); `plant_opa_image` Terraform variable; all 3 env tfvars updated; `plant-opa` build/push step in `waooaw-deploy.yml`; `-var="plant_opa_image=..."` added to all 4 Terraform plan/apply calls. Note: PR #844 (same content) accidentally merged into stacked branch rather than `main` — #845 is the correct cherry-pick. | `cloud/terraform/stacks/plant/main.tf`, `cloud/terraform/stacks/plant/variables.tf`, `cloud/terraform/stacks/plant/environments/{demo,uat,prod}.tfvars`, `.github/workflows/waooaw-deploy.yml` |
| **#847** | `feat/PLANT-SKILLS-1-it3-part2` | **PLANT-SKILLS-1 Iteration 3 (Part 2): OPA identity token + Secret Manager credentials** — GoalConfigForm wired to real Secret Manager credentials endpoint; OPA gateway identity token propagated through Plant Gateway → OPA sidecar; integration tests confirming end-to-end skill execution with real credentials. | `src/Plant/Gateway/middleware/opa_middleware.py`, `src/Plant/BackEnd/api/v1/credentials.py`, `src/CP/FrontEnd/src/components/GoalConfigForm.tsx` |
| **#842** | `feat/CP-HIRE-1` | **CP-HIRE-1: hire journey full DB persistence** — fixes GET `/cp/hired-agents/by-subscription/{id}` proxy (was using wrong Plant path); adds `CP_HIRE_USE_PLANT` Terraform flag to switch between in-memory and Plant-backed hired-agent creation; Razorpay secrets wired through Terraform Secret Manager references. | `src/CP/BackEnd/api/cp_hire.py`, `cloud/terraform/stacks/cp/main.tf`, `cloud/terraform/stacks/cp/variables.tf` |
| **#841** | `fix/cp-backend-my-agents-terraform` | **My Agents (0) Terraform env flags fix** — CP Backend Terraform env flags were missing `MY_AGENTS_USE_PLANT` and related feature flags, causing My Agents page to always return 0. Regression tests added to catch env flag gaps. | `cloud/terraform/stacks/cp/main.tf`, `src/CP/BackEnd/tests/test_env_flags.py` |
| **#840** | `feat/CP-SKILLS-2-it2` | **CP-SKILLS-2 Iteration 2: goal-config persistence** — Alembic `025_agent_skill_goal_config.py` migration adds `goal_config JSONB` column to `agent_skills`; Plant PATCH endpoint persists per-instance goal config; CP proxy `PATCH /cp/hired-agents/{id}/skills/{skill_id}/goal-config`; CP FE `GoalConfigForm` seeds from DB with Saving…/Saved ✓/error states. | `src/Plant/BackEnd/database/migrations/versions/025_agent_skill_goal_config.py`, `src/Plant/BackEnd/api/v1/agent_skills.py`, `src/CP/BackEnd/api/cp_skills.py`, `src/CP/FrontEnd/src/components/GoalConfigForm.tsx` |
| **#839** | `feat/CP-MY-AGENTS-1` | **CP My Agents listing fallback + portal UX fixes** — My Agents page falls back gracefully when Plant Gateway returns empty; portal sidebar active-item highlight fix; loading skeleton added to AgentCard. | `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx`, `src/CP/FrontEnd/src/components/Sidebar.tsx`, `src/CP/FrontEnd/src/components/AgentCard.tsx` |

### Recently merged — 2026-03-02

| PR | Branch | Summary | Key files |
|----|--------|---------|----------|
| **#836** | `feat/CP-SKILLS-2-it1-e1` | **CP-SKILLS-2 Iteration 1: goal_config persistence** — Alembic migration 025 adds `goal_config JSONB` to `agent_skills`; Plant PATCH endpoint persists per-instance goal config; GET list response extended with `goal_config` + `goal_schema`; CP proxy `PATCH /cp/hired-agents/{id}/skills/{skill_id}/goal-config` (two-hop); CP FE `GoalConfigForm` seeds from DB and calls real async Save with Saving…/Saved ✓/error states; 8 new tests across Plant BE + CP BE. | `src/Plant/BackEnd/database/migrations/versions/025_agent_skill_goal_config.py`, `src/Plant/BackEnd/models/agent_skill.py`, `src/Plant/BackEnd/api/v1/agent_skills.py`, `src/Plant/BackEnd/tests/test_agent_skills_api.py`, `src/Plant/BackEnd/tests/unit/test_agent_skills_api.py`, `src/CP/BackEnd/api/cp_skills.py`, `src/CP/BackEnd/tests/test_cp_skills_routes.py`, `src/CP/FrontEnd/src/components/GoalConfigForm.tsx` |
| **#835** | `feat/CP-SKILLS-1-it2` | **CP-SKILLS-1 Iteration 2: CP FrontEnd SkillsPanel + performance** — `SkillsPanel.tsx` component renders agent skills list; `PerformanceStats` section in agent detail; `platformConnections.service.ts` + `performanceStats.service.ts` service layer; all wired into `MyAgents.tsx` hired-agent detail view. | `src/CP/FrontEnd/src/services/agentSkills.service.ts`, `src/CP/FrontEnd/src/services/performanceStats.service.ts`, `src/CP/FrontEnd/src/services/platformConnections.service.ts`, `src/CP/FrontEnd/src/components/SkillsPanel.tsx`, `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` |
| **#834** | `feat/CP-SKILLS-1-it1` | **CP-SKILLS-1 Iteration 1: CP BackEnd proxy — 6 skills routes** — `cp_skills.py` implements 6 thin proxy routes (`GET /cp/hired-agents/{id}/skills`, `GET .../skills/{skill_id}`, `GET .../platform-connections`, `GET .../platform-connections/{conn_id}`, `GET .../performance-stats`, `PATCH .../skills/{skill_id}/goal-config`) forwarding to Plant Backend; registered in `main_proxy.py`. | `src/CP/BackEnd/api/cp_skills.py`, `src/CP/BackEnd/main_proxy.py`, `src/CP/BackEnd/tests/test_cp_skills_routes.py` |

### Recently merged — 2026-03-01

| PR | Branch | Summary | Key files |
|----|--------|---------|----------|
| **#830** | `feat/PLANT-SKILLS-1-it2` | **PLANT-SKILLS-1 Iteration 2: platform-connections + performance-stats APIs + skill seeds** — `platform_connections` REST API with CRUD; `performance_stats` read/write endpoints under hired agent context; seed data for demo agents' platform connections; Plant Gateway pass-through routes for both resources. | `src/Plant/BackEnd/api/v1/platform_connections.py`, `src/Plant/BackEnd/api/v1/performance_stats.py`, `src/Plant/BackEnd/database/seeds/platform_connections_seed.py`, `src/Plant/Gateway/api/v1/platform_connections.py`, `src/Plant/Gateway/api/v1/performance_stats.py` |
| **#829** | `feat/CP-NAV-1-it2` | **CP-NAV-1 Iteration 2: Edit Profile BE + CP FE modal + mobile nav** — `cp_profile.py` adds `GET /cp/profile` and `PATCH /cp/profile` (two-hop via Plant Gateway); `ProfileSettingsModal` in CP FrontEnd wires to real API; mobile `EditProfileScreen.tsx` calls Plant Gateway `PATCH /api/v1/customers/profile` directly; `profile.service.ts` created for CP FE service layer. | `src/CP/BackEnd/api/cp_profile.py`, `src/CP/BackEnd/main_proxy.py`, `src/CP/FrontEnd/src/pages/authenticated/ProfileSettings.tsx`, `src/CP/FrontEnd/src/services/profile.service.ts`, `src/mobile/src/screens/profile/EditProfileScreen.tsx` |
| **#828** | `feat/PLANT-SKILLS-1-it1` | **PLANT-SKILLS-1 Iteration 1: agent_skills + platform_connections + performance_stats models** — SQLAlchemy models + Alembic migrations for all three tables; Plant Backend APIs for agent skill listing and detail; unit tests; seeds for demo agent skills. | `src/Plant/BackEnd/models/agent_skill.py`, `src/Plant/BackEnd/models/platform_connection.py`, `src/Plant/BackEnd/models/performance_stat.py`, `src/Plant/BackEnd/database/migrations/versions/024_agent_skills.py`, `src/Plant/BackEnd/api/v1/agent_skills.py`, `src/Plant/BackEnd/tests/test_agent_skills_api.py` |
| **#827** | `feat/CP-NAV-1-it1` | **CP-NAV-1 Iteration 1: authenticated portal sidebar redesign + page stubs** — `AuthenticatedPortal.tsx` sidebar redesigned to match UX navigation spec (My Agents, Command Centre, Deliverables, Inbox, Profile Settings); stub pages `CommandCentre.tsx`, `Deliverables.tsx`, `Inbox.tsx`, `ProfileSettings.tsx` created; React Router routes wired up. | `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx`, `src/CP/FrontEnd/src/pages/authenticated/CommandCentre.tsx`, `src/CP/FrontEnd/src/pages/authenticated/Deliverables.tsx`, `src/CP/FrontEnd/src/pages/authenticated/Inbox.tsx`, `src/CP/FrontEnd/src/pages/authenticated/ProfileSettings.tsx` |
| **#822** | `fix/registration-otp-email-delivery` | **Registration OTP email delivery** — CP backend now sends OTP email directly instead of relying on Plant Celery; Plant backend extended to send OTP in demo env with Celery fallback; Terraform SMTP config made env-specific via variables; 23 unit tests for OTP sessions covering env detection, email dispatch, Celery fallback, DB writes, and response contract. | `src/CP/BackEnd/api/cp_registration_otp.py`, `src/CP/BackEnd/services/cp_otp_delivery.py`, `src/Plant/BackEnd/api/v1/otp.py`, `src/Plant/BackEnd/tests/unit/test_otp_sessions.py`, `cloud/terraform/stacks/plant/variables.tf`, `cloud/terraform/stacks/plant/environments/demo.tfvars` |
| **#821** | `feat/cp-landing-brand-fonts` | **CP landing page brand system + 3-step registration wizard** — Hero carousel, Space Grotesk/Outfit/Inter single-source CSS font vars, OTP email verification on Step 1 before registration, Turnstile widget reset fix, full (unmasked) email in OTP hint, SMTP host corrected to `smtp.gmail.com`, dev OTP code leak removed from hints. | `src/CP/FrontEnd/src/components/HeroCarousel.tsx`, `src/CP/FrontEnd/src/pages/SignUp.tsx`, `src/CP/FrontEnd/src/services/otp.service.ts`, `src/CP/FrontEnd/src/components/auth/CaptchaWidget.tsx` |
| **#820** | `feat/cp-landing-brand-fonts` | Earlier iteration of CP landing brand fonts (superseded by #821). | — |
| **#815** | `feat/nfr-mobile-compliance` | **Mobile NFR compliance + 3-step signup wizard** — Mobile `SignUpScreen` rewritten as 3-step wizard (progress dots, industry cards, no static header pane); `fast-check` property-based tests added; CP frontend industry selector replaced emoji-cards with dropdown matching mobile; dynamic left panel on signup page with equal columns. | `src/mobile/`, `src/CP/FrontEnd/src/pages/SignUp.tsx` |

### Recently merged — 2026-02-27

| PR | Branch | Summary | Key files |
|----|--------|---------|----------|
| **#809** | `fix/cp-5xx-hardening-all-plant-routes` | **NFR corrective work C1–C7** — closed all NFR gaps across CP and Plant: `audit_dependency.py` (C1), audit wired into 5 CP flows (C2), circuit breaker on `PlantGatewayClient` (C3), `PIIMaskingFilter` in CP + Plant logging (C4+C5), catalog GET routes → read replica (C6), `feature_flag_dependency.py` in CP + Plant (C7). Ghost account + 503 registration fix also included. | `src/CP/BackEnd/services/audit_dependency.py`, `src/CP/BackEnd/services/plant_gateway_client.py`, `src/CP/BackEnd/core/logging.py`, `src/Plant/BackEnd/core/logging.py`, `src/Plant/BackEnd/api/v1/feature_flag_dependency.py`, `src/CP/BackEnd/api/feature_flag_dependency.py` |
| **#810** | `feat/nfr-preventive-gates-p1-p4` | **NFR preventive gates P1–P4** — circuit breaker on all Gateway middleware (P1), `dependencies=[Depends(require_correlation_id)]` on all 4 FastAPI apps (P2), `waooaw_router()` factory + ruff ban on bare `APIRouter()` migrated across all 58+ router files in CP/Plant/PP (P3), genesis + audit GET routes → read replica (P4). | `src/CP/BackEnd/core/routing.py`, `src/CP/BackEnd/core/dependencies.py`, `src/Plant/BackEnd/core/routing.py`, `src/Plant/BackEnd/core/dependencies.py`, `src/Plant/Gateway/core/dependencies.py`, `src/Plant/Gateway/middleware/circuit_breaker.py`, `src/gateway/middleware/circuit_breaker.py`, `src/CP/BackEnd/pyproject.toml`, `src/Plant/BackEnd/pyproject.toml`, `scripts/migrate_p3_routers.py` |
| **#811** | `feat/nfr-pp-baseline-p5` | **PP Backend NFR baseline P5** — circuit breaker on `PlantAPIClient` (PP-N1), OTel tracing via `core/observability.py` (PP-N2), `waooaw_router()` migration + ruff ban (PP-N3b), `AuditLogger` dependency wired into agents/approvals/genesis (PP-N4), `require_correlation_id` already wired via P2. | `src/PP/BackEnd/clients/plant_client.py`, `src/PP/BackEnd/core/observability.py`, `src/PP/BackEnd/core/routing.py`, `src/PP/BackEnd/core/dependencies.py`, `src/PP/BackEnd/services/audit_dependency.py`, `src/PP/BackEnd/services/audit_client.py`, `src/PP/BackEnd/pyproject.toml` |

### Completed (previously pending) — 2026-02-27

| Area | Summary | Key files |
|---|---|---|
| Ghost account + registration 503 fix | **PR #808** — included in PR #809 above. | `src/Plant/BackEnd/api/v1/customers.py` |
| Permanent GCP + DB access from Codespace | `.devcontainer/gcp-auth.sh` now: (1) persists SA key to `/root/.gcp/waooaw-sa.json`, (2) activates gcloud with SA `waooaw-codespace-reader`, (3) starts Cloud SQL Auth Proxy v2.14.2 on port 15432, (4) reads `demo-plant-database-url` from Secret Manager → writes `/root/.pgpass` + `/root/.env.db` for passwordless psql. `devcontainer.json` updated with `google-cloud-cli` feature + `postCreateCommand`. | `.devcontainer/gcp-auth.sh`, `.devcontainer/devcontainer.json` |

### Pending (unmerged) work — 2026-02-24

| Area | Summary | Key files |
|---|---|---|
| Mobile Google Sign-In fix | **PR #755** — Added Play App Signing SHA-1 (`8fd589b1…`) as a second type-1 Android OAuth client entry in `google-services.json`. Resolves `DEVELOPER_ERROR` (error code 10) on Google Sign-In for Play Store builds. Root cause: Google Play re-signs AABs with its own key; the device-installed APK's certificate SHA-1 did not match the EAS upload keystore SHA-1 that was previously the only registered entry. Manual steps also completed: SHA-1 added to Firebase Console (waooaw-oauth → `com.waooaw.app`) and GCP OAuth Android client (`270293855600-2shlgots…`). | `src/mobile/google-services.json` |

### Pending (unmerged) work — 2026-02-22

| Area | Summary | Key files |
|---|---|---|
| Mobile auth (web preview) | Web Google sign-in now requests an **ID token** (not access token) so the app can exchange it at the Plant Gateway (`POST /auth/google/verify`) and receive WAOOAW JWTs; token persistence on **web preview** is resilient (browser storage fallback) so login completes. | `src/mobile/src/hooks/useGoogleAuth.ts`, `src/mobile/src/services/auth.service.ts`, `src/mobile/src/lib/secureStorage.ts`, `src/mobile/src/lib/apiClient.ts` |
| Mobile CI/CD | Added GitHub Actions workflows and Play Store deployment pipeline (used for internal testing → production). | `.github/workflows/mobile-*.yml` |
| Infrastructure | Terraform modules/support for mobile deployment prerequisites. | `cloud/terraform/mobile/`, `cloud/terraform/modules/mobile-support/` |

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

- Registration OTP email delivered directly from CP backend (not via Plant Celery)
- CP landing page: hero carousel, brand fonts (Space Grotesk, Outfit, Inter), 3-step signup wizard
- OTP email verification on Step 1 of registration (pre-registration email confirm)
- Mobile: 3-step signup wizard + NFR compliance (property-based tests)
- Terraform SMTP config made env-specific (no baked-in values)
- CP frontend: industry dropdown replaces emoji-cards, dynamic left panel on signup
- CP registration robustness (duplicate detection, OTP, 2FA, Turnstile CAPTCHA)
- Plant gateway hardening; mobile Play Store CI/CD pipeline

### Active feature branches

| Branch | Area |
|--------|------|
| feat/skills-sk-* (series) | Skills certification lifecycle (SK-1.1 through SK-3.1) |

---

## 13. Code File Index

### Fast-path index for runtime routing and vocabulary

Use this shortlist first when the task is about Agent/Skill/Component runtime behaviour or CP route drift.

| Need | First file | Then inspect | Why |
|---|---|---|---|
| Canonical runtime vocabulary | `main/Foundation/genesis_foundational_governance_agent.md` §3a–3c | `docs/CONTEXT_AND_INDEX.md` §4.7 | Source of truth for Agent, Skill, Component, Skill Run, and Goal vocabulary |
| CP hired-agent skills flow | `src/CP/FrontEnd/src/services/agentSkills.service.ts` | `src/CP/BackEnd/api/cp_skills.py` → `src/Plant/BackEnd/api/v1/agent_skills.py` | Full FE → proxy → Plant chain |
| Customer skill config save | `src/CP/BackEnd/api/cp_skills.py` | `src/Plant/BackEnd/api/v1/skill_configs.py` | Canonical hired-agent skill config write path |
| Skill/component run history | `src/CP/BackEnd/api/cp_flow_runs.py` | `src/Plant/BackEnd/api/v1/flow_runs.py` | CP proxy and Plant route registration meet here |
| Approval queue and review actions | `src/CP/BackEnd/api/cp_approvals_proxy.py` | `src/Plant/BackEnd/api/v1/deliverables_simple.py` | Prevents drift back to nonexistent deliverable status patch paths |
| Hired-agent identity lookup | `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | `src/Plant/BackEnd/tests/unit/test_hired_agents_api.py` | Canonical by-id surface and validation entry point |

### Fast-path index for platform ownership and operations

Use this shortlist when the task is broader than runtime routes.

| Need | First file | Then inspect | Why |
|---|---|---|---|
| CP page bug or wrong API call | `src/CP/FrontEnd/src/services/` | `src/CP/BackEnd/api/` | Most CP breakage starts with the FE service calling the wrong proxy |
| PP operator workflow issue | `src/PP/FrontEnd/src/pages/` | `src/PP/BackEnd/api/` | PP remains a UI + thin-proxy/admin stack |
| Gateway auth/RBAC/policy issue | `src/Plant/Gateway/main.py` | `src/Plant/Gateway/middleware/` | Gateway owns ingress enforcement, not Plant BackEnd |
| Plant business-logic bug | `src/Plant/BackEnd/api/v1/router.py` | `src/Plant/BackEnd/services/`, `src/Plant/BackEnd/models/` | Confirms mounted route, service path, and persistence layer |
| Mobile feature or auth issue | `src/mobile/src/` | §23 + Plant Gateway auth endpoints | Mobile often talks to Gateway directly |
| Docker/local stack issue | `docker-compose.local.yml` | `docker-compose.test.yml`, `infrastructure/docker/` | Distinguishes dev stack from regression stack and support assets |
| Deploy, Cloud Run, or Terraform issue | `.github/workflows/waooaw-deploy.yml` | `cloud/terraform/`, `cloud/terraform/stacks/`, `cloud/terraform/environments/` | Build/push/apply ownership lives here |
| Logging/metrics/debug work | `src/Plant/BackEnd/core/logging.py` | `src/Plant/BackEnd/core/metrics.py`, `src/PP/BackEnd/core/observability.py`, `infrastructure/monitoring/` | Fastest path into observability ownership |
| Database or migration issue | `src/Plant/BackEnd/core/database.py` | `src/Plant/BackEnd/models/`, `src/Plant/BackEnd/database/migrations/`, §10 | DB truth belongs to Plant, not to portal services |

### Root directory

| File | Purpose |
|------|---------|
| `README.md` | Project overview, quick start, architecture |
| `docker-compose.local.yml` | Full local dev stack (Postgres, Redis, Plant, PP, CP, Gateway) |
| `docker-compose.test.yml` | Dedicated regression stack — backend, frontend, E2E, perf, security test containers |
| `docker-compose.mobile.yml` | Mobile-specific local/test stack support |
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

#### Non-versioned API routes (`api/`)
| File | Endpoints |
|------|-----------|
| `factorial.py` | Factorial test/validation endpoint (smoke test) |
| `trials.py` | Trial lifecycle endpoints (non-versioned path) |

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
| `hired_agents_simple.py` | Hired agent management — includes direct lookup `GET /hired-agents/by-id/{hired_instance_id}` and hired-agent lifecycle/config endpoints |
| `trial_status_simple.py` | Trial status endpoints |
| `audit.py` | Audit log endpoints |
| `auth.py` | Authentication endpoints — `POST /auth/google/verify`, `POST /auth/validate`, `POST /auth/register` (mobile registration), `POST /auth/otp/start` (mobile OTP challenge), `POST /auth/otp/verify` (mobile OTP → JWT) |
| `otp.py` | OTP session lifecycle — create session, deliver email/SMS, verify code, revoke (added PR #822) |
| `agent_skills.py` | Agent and hired-agent skill surfaces — legacy `GET /agents/{id}/skills` plus canonical `GET /hired-agents/{hired_instance_id}/skills`; includes normalized runtime Skill response helpers |
| `feature_flags.py` | Feature flag CRUD — create, enable/disable, query flags |
| `invoices_simple.py` | Invoice generation |
| `payments_simple.py` | Payment processing |
| `receipts_simple.py` | Receipt management |
| `deliverables_simple.py` | Deliverable tracking |
| `skill_configs.py` | Customer-editable hired-agent skill config routes — legacy `/skill-configs/{hired_instance_id}/{skill_id}` plus canonical `/hired-agents/{hired_instance_id}/skills/{skill_id}/customer-config` |
| `flow_runs.py` | Flow-run backing store plus public runtime aliases — `/flow-runs`, `/skill-runs`, `/component-runs` |
| `campaigns.py` | Campaign management — 12 endpoints: `POST /campaigns` (create with ContentCreatorSkill theme generation), `GET /campaigns`, `GET /campaigns/{id}`, `POST .../themes/approve`, `POST .../posts/generate`, `POST .../posts`, `GET .../posts`, `POST .../posts/{post_id}/approve`, `POST .../posts/{post_id}/publish`; in-memory stores `_campaigns`, `_theme_items`, `_posts` (Phase 1 — PLANT-CONTENT-2 will persist to PostgreSQL). |
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
| `flow_run.py` | FlowRunModel — current backing store for public SkillRun aliases |
| `component_run.py` | ComponentRunModel — per-step execution trace backing `/api/v1/component-runs` |
| `scheduled_goal_run.py` | ScheduledGoalRun model |
| `scheduler_dlq.py` | DeadLetterQueue model |
| `scheduler_state.py` | SchedulerState model |
| `industry.py` | Industry model |
| `job_role.py` | JobRole model |
| `skill.py` | Skill model |
| `agent_skill.py` | AgentSkillModel — join table `agent_skills` (agent_id, skill_id, is_primary, ordinal, `goal_config` JSONB nullable — migration 025) |
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
| `otp_service.py` | In-memory OTP store for mobile auth — SHA-256 hashed codes, 5-min TTL, 5-attempt cap, 3-per-10min rate limit per destination |
| `audit_log_service.py` | Audit log querying and filtering service |
| `feature_flag_service.py` | Feature flag business logic — create, toggle, evaluate flags |
| `idempotency.py` | Low-level idempotency utilities (key generation, TTL check) |
| `notification_service.py` | Unified notification dispatch orchestrator (email + SMS) |

#### Core (`core/`)
| File | Purpose |
|------|---------|
| `config.py` | Pydantic settings (174 lines) |
| `database.py` | Async DB connector (306 lines) |
| `exceptions.py` | Custom exception hierarchy |
| `logging.py` | Structured logging setup — includes `PIIMaskingFilter` (E1-S2) that masks email/phone/IP in all log records automatically |
| `metrics.py` | Prometheus-style metrics |
| `observability.py` | Observability setup |
| `security.py` | Security utilities |
| `routing.py` | `waooaw_router()` factory — enforces correlation ID on all routes |
| `dependencies.py` | `require_correlation_id` — global FastAPI dependency wired in `main.py` |

#### Platform additions (`api/v1/`)
| File | Purpose |
|------|---------|
| `feature_flag_dependency.py` | `require_flag("flag_name")` dependency factory — 404 if flag off |

#### Agent Mold Core (`agent_mold/`)
| File | Purpose |
|------|---------|
| `spec.py` | `AgentSpec`, `CompiledAgentSpec`, `ConstructBindings`, `ConstraintPolicy`, `DimensionSpec`, `DimensionName` — the full v2 mould blueprint |
| `contracts.py` | `DimensionContract` ABC — `validate()` / `materialize()` / `register_hooks()` / `observe()`; `TrialDimension`, `BudgetDimension` (MOULD-GAP-1) |
| `hooks.py` | `AgentLifecycleHooks` ABC — all lifecycle events: `on_hire`, `on_trial_start`, `on_trial_day_N`, `on_trial_end`, `on_cancel`, `on_deliverable_approved`, `on_quota_exhausted` etc. Default = no-op. (MOULD-GAP-1) |
| `enforcement.py` | `default_hook_bus()` singleton — registers platform default hooks (`QuotaGateHook`, `SchedulerPauseHook`, `ConstraintPolicyHook`, `ApprovalGateHook`, `CostAuditHook`) |
| `registry.py` | `DimensionRegistry`, `SkillRegistry` — startup wiring; `register("content.creator.v1", …)` |
| `reference_agents.py` | Marketing, tutor, trading reference `AgentSpec` definitions with `ConstructBindings` + `ConstraintPolicy` |

#### Agent Mold Skills (`agent_mold/skills/`)
| File | Purpose |
|------|---------|
| `content_models.py` | All Pydantic models for the content pipeline: `Campaign`, `DailyThemeItem`, `ContentPost`, `CampaignBrief`, `CostEstimate`, `DestinationRef`, `ReviewStatus` enum, `CampaignStatus` enum, `PublishStatus` enum, `PublishInput`, `PublishReceipt`; also pure-function `estimate_cost(brief) → CostEstimate` (PLANT-CONTENT-1 It1 #869). |
| `content_creator.py` | `ContentCreatorProcessor` (was `ContentCreatorSkill`) — reads `EXECUTOR_BACKEND` env var; if `"grok"` calls Grok API via `grok_client.py`; otherwise uses deterministic templates. Implements `BaseProcessor.execute()`. Registered as `content.creator.v1`. (PLANT-CONTENT-1 #869, MOULD-GAP-1) |
| `trading_executor.py` | `TradingProcessor` — given `TradingProcessorInput` (with live position state from `TradingPump`), produces `TradingProcessorOutput(draft_only=True)`. **Never places a real order** — that only happens in `on_deliverable_approved`. |
| `grok_client.py` | Thin Grok API client — OpenAI-SDK-compatible interface; reads `XAI_API_KEY` from env; used by `ContentCreatorProcessor` when `EXECUTOR_BACKEND=grok` (PLANT-CONTENT-1 It1 #869). |
| `publisher_engine.py` | `DestinationAdapter` ABC (abstract `publish(PublishInput) → PublishReceipt`); `DestinationRegistry` plug-and-play dict; `PublisherEngine`; `build_default_registry()` with `SimulatedAdapter`. Registered as `content.publisher.v1` (PLANT-CONTENT-1 It3+It4 #871, #872). |
| `adapters_publish.py` | `SimulatedAdapter(DestinationAdapter)` — Phase 1 publisher. **Extension point**: add `DeltaTradeAdapter`, `LinkedInAdapter` etc. and register in `build_default_registry()` (PLANT-CONTENT-1 #871). |
| `adapters.py` | Channel adapters for social posting: LinkedIn, Instagram, YouTube, Facebook, WhatsApp |

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
| `middleware/auth.py` | JWT validation middleware — `PUBLIC_ENDPOINTS` list controls unauthenticated access. Currently public: `/auth/google/verify`, `/auth/validate`, `/auth/register`, `/auth/otp/start`, `/auth/otp/verify` (and their `/api/v1/` prefixed equivalents) |
| `middleware/rbac.py` | Role-based access control |
| `middleware/policy.py` | OPA policy enforcement |
| `middleware/budget.py` | Budget guard middleware |
| `middleware/audit.py` | Audit logging middleware |
| `middleware/error_handler.py` | RFC 7807 error responses (active version) |
| `middleware/error_handler_new.py` | Updated RFC 7807 error handler (candidate replacement) |
| `middleware/error_handler_old.py` | Preserved original error handler for rollback reference |
| `middleware/circuit_breaker.py` | Shared `CircuitBreaker` class used by all middleware — prevents upstream hangs platform-wide |
| `core/dependencies.py` | `require_correlation_id` for gateway-level correlation ID propagation |

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
| `api/auth/` | Auth routes (Google OAuth) — `google_oauth.py`, `routes.py`, `dependencies.py`, `user_store.py` |
| `api/cp_registration.py` | Customer registration endpoint |
| `api/cp_registration_otp.py` | Pre-registration OTP: verify email ownership before full registration (added PR #822) |
| `api/cp_otp.py` | OTP verification (post-registration 2FA) |
| `api/hire_wizard.py` | Agent hiring flow |
| `api/payments_razorpay.py` | Razorpay payment integration |
| `api/payments_config.py` | Payment gateway config endpoint (key, currency, mode) |
| `api/payments_coupon.py` | Coupon/discount code validation and application |
| `api/exchange_setup.py` | Exchange configuration |
| `api/trading.py` | Trading endpoints |
| `api/trading_strategy.py` | Trading strategy configuration endpoints |
| `api/subscriptions.py` | Subscription management |
| `api/invoices.py` | Invoice endpoints |
| `api/receipts.py` | Receipt endpoints |
| `api/hired_agents_proxy.py` | Proxy hired-agent queries to Plant Gateway |
| `api/my_agents_summary.py` | Customer "my agents" summary (active agents, status, metrics) |
| `api/marketing_review.py` | Marketing content review/approval endpoints |
| `api/platform_credentials.py` | Platform credential management (social, exchange) |
| `api/feature_flags_proxy.py` | Proxy feature flag queries to Plant Backend |
| `api/internal_plant_credential_resolver.py` | Internal credential resolution for Plant → CP calls |
| `api/cp_skills.py` | CP skills thin proxy — hired-agent skills list, hired-agent customer-config save, skill lookup, platform connections, and performance stats. Canonical Plant targets are `/api/v1/hired-agents/{hired_instance_id}/skills` and `/api/v1/hired-agents/{hired_instance_id}/skills/{skill_id}/customer-config`. `POST` platform connection writes raw credentials to GCP Secret Manager via `SecretManagerAdapter`, forwards only opaque `secret_ref` to Plant — credentials never touch the Plant DB directly. |
| `api/cp_flow_runs.py` | CP thin proxy for SkillRun and ComponentRun history — `/api/cp/flow-runs`, `/api/cp/component-runs`, `/api/cp/approvals/{flow_run_id}/approve|reject`; Plant targets must use `/api/v1/skill-runs`, `/api/v1/component-runs`, `/api/v1/approvals/...` |
| `api/cp_approvals_proxy.py` | CP approval queue thin proxy — `/api/cp/hired-agents/{id}/approval-queue` and approve/reject actions; canonical Plant write target is `POST /api/v1/deliverables/{deliverable_id}/review` |
| `api/cp_scheduler.py` | CP thin proxy for trial budget, scheduler summary, and pause/resume actions on hired agents |
| `api/campaigns.py` | CP BackEnd thin proxy for campaign endpoints — 8 routes (`POST /cp/campaigns`, `GET /cp/campaigns`, `GET /cp/campaigns/{id}`, `POST .../themes/approve`, `POST .../posts/generate`, `GET .../posts`, `POST .../posts/{post_id}/approve`, `POST .../posts/{post_id}/publish`) forwarding to Plant Backend campaign API; registered in `main_proxy.py` (PLANT-CONTENT-1 It4 #872). |
| `api/cp_profile.py` | `GET /cp/profile` and `PATCH /cp/profile` — two-hop via Plant Gateway; reads/updates customer profile data; registered in `main_proxy.py` (CP-NAV-1 It2 #829). |
| `api/feature_flag_dependency.py` | `require_flag("flag_name")` dependency factory — returns 404 if flag is off |
| `services/auth_service.py` | Auth business logic |
| `services/cp_registrations.py` | Registration service |
| `services/cp_2fa.py` | Two-factor auth service |
| `services/cp_otp.py` | OTP service |
| `services/cp_otp_delivery.py` | OTP delivery orchestration — dispatches email/SMS directly from CP backend (PR #822) |
| `services/cp_approvals.py` | CP-side approval request forwarding to gateway |
| `services/cp_refresh_revocations.py` | Token refresh revocation management |
| `services/cp_subscriptions_simple.py` | Simplified subscription read queries |
| `services/secret_manager.py` | Cloud-portable credential storage — `SecretManagerAdapter` ABC with two implementations: `GcpSecretManagerAdapter` (ADC, no key file; used in demo/uat/prod) and `LocalSecretManagerAdapter` (in-memory dict; used locally and in CI). Toggled by `SECRET_MANAGER_BACKEND` env var. Secret naming convention: `hired-{hired_instance_id}-{platform_key}`. (PLANT-SKILLS-1 It3 #846) |
| `services/exchange_setup.py` | Exchange credential setup and validation service |
| `services/plant_client.py` | Direct Plant Backend HTTP client (for internal CP→Plant calls bypassing Gateway) |
| `services/plant_gateway_client.py` | HTTP client to Plant Gateway — has class-level `_circuit_breaker` (3 failures→OPEN, 30s recovery) |
| `services/platform_credentials.py` | Platform credential storage and retrieval service |
| `services/audit_dependency.py` | `AuditLogger` class + `get_audit_logger` FastAPI dependency — fire-and-forget audit events |
| `services/audit_client.py` | Low-level HTTP client to audit service — never call directly from routes, use `audit_dependency` |
| `core/routing.py` | `waooaw_router()` factory — use instead of bare `APIRouter()` in all `api/` files |
| `core/dependencies.py` | `require_correlation_id` — reads/generates `X-Correlation-ID`; wired globally in `main.py` |
| `pyproject.toml` | ruff TID251 ban on bare `from fastapi import APIRouter` in `api/` directories |

### src/CP/FrontEnd/src/ — Customer Portal Frontend

| File | Purpose |
|------|---------|
| `App.tsx` | Root React component |
| `main.tsx` | Entry point |
| `theme.ts` | Design system tokens |
| `pages/LandingPage.tsx` | Marketplace landing page — hero carousel, brand fonts, rotating tagline |
| `pages/AgentDiscovery.tsx` | Agent browsing/search |
| `pages/AgentDetail.tsx` | Individual agent view |
| `pages/SignIn.tsx` | Sign-in page |
| `pages/SignUp.tsx` | 3-step registration wizard — Step 1 email+OTP verify, Step 2 profile, Step 3 industry |
| `pages/AuthCallback.tsx` | OAuth/OIDC redirect callback handler |
| `pages/HireSetupWizard.tsx` | Agent hiring wizard |
| `pages/TrialDashboard.tsx` | Trial management |
| `pages/AuthenticatedPortal.tsx` | Post-login portal |
| `pages/HireReceipt.tsx` | Hire confirmation |
| `pages/authenticated/Dashboard.tsx` | Customer authenticated home dashboard |
| `pages/authenticated/MyAgents.tsx` | Active agents management view |
| `pages/authenticated/GoalsSetup.tsx` | Configure goals for hired agents |
| `pages/authenticated/Performance.tsx` | Agent performance metrics view |
| `pages/authenticated/UsageBilling.tsx` | Usage and billing history |
| `pages/authenticated/Approvals.tsx` | Customer approval requests |
| `pages/authenticated/CommandCentre.tsx` | Command Centre page stub (CP-NAV-1 #827) |
| `pages/authenticated/Deliverables.tsx` | Deliverables page stub (CP-NAV-1 #827) |
| `pages/authenticated/Inbox.tsx` | Inbox page stub (CP-NAV-1 #827) |
| `pages/authenticated/ProfileSettings.tsx` | Profile settings page — modal with edit-profile form; calls `PATCH /cp/profile` via `profile.service.ts`; stub wired in sidebar nav (CP-NAV-1 #827, It2 #829) |
| `components/AgentCard.tsx` | Agent card component |
| `components/AgentSelector.tsx` | Multi-agent selection UI |
| `components/Header.tsx` | Navigation header |
| `components/Footer.tsx` | Page footer |
| `components/BookingModal.tsx` | Booking modal |
| `components/HeroCarousel.tsx` | Landing page rotating hero carousel (PR #821) |
| `components/SkeletonLoaders.tsx` | Skeleton loading placeholders |
| `components/FeedbackIndicators.tsx` | Loading/success/error feedback indicators |
| `components/HelpTooltip.tsx` | Contextual help tooltips |
| `components/TrialStatusBanner.tsx` | Trial status banner |
| `components/auth/AuthModal.tsx` | Auth modal (sign-in/sign-up overlay) |
| `components/auth/AuthPanel.tsx` | Auth form container panel |
| `components/auth/CaptchaWidget.tsx` | Cloudflare Turnstile CAPTCHA integration |
| `components/auth/GoogleLoginButton.tsx` | Google OAuth login button |
| `components/SkillsPanel.tsx` | Skills tab — skill cards with expand/collapse, `GoalConfigForm` seeded from `skill.goal_config`, async Save (Saving…/Saved ✓/error), `PlatformConnectionsPanel` (CP-SKILLS-1 #835, CP-SKILLS-2 #836). Updated to use `conn.id` + `conn.platform_key` matching Plant BE field names (PLANT-SKILLS-1 It3 #846) |
| `services/agentSkills.service.ts` | Skills API — `listHiredAgentSkills()`, `getSkill()`, `saveGoalConfig()` via `PATCH /api/cp/hired-agents/{id}/skills/{skill_id}/goal-config`; first FE file to inspect for hired-agent skill drift |
| `services/performanceStats.service.ts` | Performance stats API — `listPerformanceStats()` (CP-SKILLS-1 #835) |
| `services/platformConnections.service.ts` | Platform connections API — `listPlatformConnections()`, `createPlatformConnection()`, `deletePlatformConnection()`; inspect this immediately after `agentSkills.service.ts` when a hired-agent configuration flow fails |
| `services/profile.service.ts` | Profile read/update API calls — `getProfile()` and `updateProfile()` via `GET|PATCH /cp/profile` (CP-NAV-1 It2 #829) |
| `services/auth.service.ts` | Auth API calls |
| `services/registration.service.ts` | Registration API calls |
| `services/otp.service.ts` | OTP initiation and verification (pre-registration email verify) |
| `services/hireWizard.service.ts` | Hire flow API calls |
| `services/plant.service.ts` | Plant API client |
| `services/gatewayApiClient.ts` | Base Axios/fetch client for Plant Gateway (auth headers, interceptors) |
| `services/agentTypes.service.ts` | Agent types API |
| `services/trading.service.ts` | Trading API calls |
| `services/tradingStrategy.service.ts` | Trading strategy configuration API calls |
| `services/hiredAgents.service.ts` | Hired agents list/management API calls |
| `services/hiredAgentGoals.service.ts` | Goal management for hired agents |
| `services/hiredAgentDeliverables.service.ts` | Deliverables for hired agents |
| `services/invoices.service.ts` | Invoice API calls |
| `services/receipts.service.ts` | Receipt API calls |
| `services/subscriptions.service.ts` | Subscription management API calls |
| `services/trialStatus.service.ts` | Trial status polling |
| `services/marketingReview.service.ts` | Marketing content review API calls |
| `services/myAgentsSummary.service.ts` | My agents summary API calls |
| `services/paymentsConfig.service.ts` | Payment gateway config API calls |
| `services/couponCheckout.service.ts` | Coupon/discount checkout flow |
| `services/razorpayCheckout.service.ts` | Razorpay checkout integration |
| `services/exchangeSetup.service.ts` | Exchange setup API calls |
| `services/platformCredentials.service.ts` | Platform credentials API calls |
| `config/` | App configuration |
| `context/` | React context providers |
| `hooks/` | Custom React hooks |
| `styles/` | CSS styles |
| `types/` | TypeScript type definitions |

### src/PP/ — Platform Portal

| File | Purpose |
|------|---------|
| `BackEnd/main.py` → `main_proxy.py` | PP app entry (thin proxy) — has OTel instrumentation + global `require_correlation_id` |
| `BackEnd/api/genesis.py` | Genesis certification endpoints — audit wired |
| `BackEnd/api/agents.py` | Agent management — audit wired |
| `BackEnd/api/agent_types.py` | Agent type management endpoints |
| `BackEnd/api/agent_setups.py` | Agent setup/configuration endpoints — `PUT /pp/agent-setups` defines ConstructBindings + ConstraintPolicy defaults |
| `BackEnd/api/approvals.py` | Approval workflows — audit wired |
| `BackEnd/api/audit.py` | Audit log access |
| `BackEnd/api/auth.py` | PP authentication |
| `BackEnd/api/db_updates.py` | Database update/migration management endpoints |
| `BackEnd/api/deps.py` | Shared PP API dependencies (auth, role checks) |
| `BackEnd/api/exchange_credentials.py` | Exchange credential management |
| `BackEnd/api/metering_debug.py` | Metering debug/inspection endpoints |
| `BackEnd/api/security.py` | Security audit and management endpoints |
| `BackEnd/api/ops_hired_agents.py` | Construct health + scheduler diagnostics + hook trace per hired agent — `GET /pp/ops/hired-agents/{id}/construct-health`, `GET .../scheduler-diagnostics`, `GET .../hook-trace` (PP-MOULD-1 It2 #884) |
| `BackEnd/api/ops_dlq.py` | DLQ console — `GET /pp/ops/dlq`, `POST /pp/ops/dlq/{id}/requeue` (PP-MOULD-1 It1 #883) |
| `BackEnd/core/authorization.py` | RBAC enforcement — `require_role(min_role)` dependency; 7-role hierarchy (PP-MOULD-1 It1 #883) |
| `BackEnd/clients/plant_client.py` | `PlantAPIClient` — httpx client to Plant Gateway with class-level `_PlantCircuitBreaker` (PP-N1) |
| `BackEnd/core/routing.py` | `waooaw_router()` factory for PP — same pattern as CP/Plant |
| `BackEnd/core/dependencies.py` | `require_correlation_id` |
| `BackEnd/core/observability.py` | OTel tracing wrapper (PP-N2) — try/except guarded; GCP Cloud Trace exporter when `OTEL_EXPORTER=gcp` |
| `BackEnd/services/audit_client.py` | PP audit HTTP client — gracefully no-ops if `AUDIT_SERVICE_KEY` not set |
| `BackEnd/services/audit_dependency.py` | `AuditLogger` + `get_audit_logger` FastAPI dependency |
| `BackEnd/pyproject.toml` | ruff TID251 ban on bare `APIRouter()` |
| `FrontEnd/src/pages/LandingPage.tsx` | PP login/landing page |
| `FrontEnd/src/pages/Dashboard.tsx` | Admin dashboard |
| `FrontEnd/src/pages/GovernorConsole.tsx` | Governor control panel |
| `FrontEnd/src/pages/GenesisConsole.tsx` | Genesis certification UI |
| `FrontEnd/src/pages/AgentManagement.tsx` | Agent management UI |
| `FrontEnd/src/pages/AgentSetup.tsx` | Agent configuration/setup UI |
| `FrontEnd/src/pages/AgentData.tsx` | Agent raw data inspection view |
| `FrontEnd/src/pages/AgentSpecTools.tsx` | Agent specification tooling UI |
| `FrontEnd/src/pages/CustomerManagement.tsx` | Customer management UI |
| `FrontEnd/src/pages/ReviewQueue.tsx` | Review/approval queue |
| `FrontEnd/src/pages/AuditConsole.tsx` | Audit log viewer |
| `FrontEnd/src/pages/PolicyDenials.tsx` | Policy denial viewer |
| `FrontEnd/src/pages/HiredAgentsOps.tsx` | Hired agent operations view — includes agent-type-specific construct diagnostic panels (trader + content) (PP-MOULD-1 It2 MOULD-GAP-1 E6) |
| `FrontEnd/src/pages/ReferenceAgents.tsx` | Reference agent catalog management |
| `FrontEnd/src/pages/Billing.tsx` | Platform billing view |
| `FrontEnd/src/pages/DbUpdates.tsx` | Database update management UI |
| `FrontEnd/src/pages/AgentTypeSetupScreen.tsx` | Agent type setup form — ConstructBindings + ConstraintPolicy defaults + lifecycle hook checklist (PP-MOULD-1 It2 #884) |
| `FrontEnd/src/pages/ApprovalsQueueScreen.tsx` | Approvals queue with type badge + expiry countdown (PP-MOULD-1 It2 #884) |
| `FrontEnd/src/components/ConstructHealthPanel.tsx` | 6-card construct health drawer — Scheduler / Pump / Processor / Connector / Publisher / Policy; per-card inline actions (PP-MOULD-1 It2 #884) |
| `FrontEnd/src/components/SchedulerDiagnosticsPanel.tsx` | Scheduler detail tab — cron, lag, DLQ inline table, pause/resume (PP-MOULD-1 It2 #884) |
| `FrontEnd/src/components/HookTracePanel.tsx` | Hook trace log — last 50 events, stage + result + hook class (PP-MOULD-1 It2 #884) |
| `FrontEnd/src/components/ConstraintPolicyLiveTuneDrawer.tsx` | Live-tune approval_mode + max_tasks_per_day with audit acknowledgement (PP-MOULD-1 It2 #884) |
| `FrontEnd/src/services/useConstructHealth.ts` | React hook for `/pp/ops/hired-agents/{id}/construct-health` |
| `FrontEnd/src/services/useSchedulerDiagnostics.ts` | React hook for scheduler diagnostics endpoint |
| `FrontEnd/src/services/useHookTrace.ts` | React hook for hook trace endpoint |
| `FrontEnd/src/services/useAgentTypeSetup.ts` | React hook for agent setup CRUD |

### src/mobile/ — CP Mobile

| File | Purpose |
|------|---------|
| `App.tsx` | Mobile app root |
| `index.ts` | Expo/React Native entrypoint |
| `src/navigation/` | Main navigation graph and screen registration |
| `src/screens/` | Customer-facing mobile screens |
| `src/hooks/` | React Query and screen-level hooks |
| `src/lib/cpApiClient.ts` | Mobile HTTP client — correlation ID propagation, retries, auth headers |
| `src/stores/authStore.ts` | Auth/session state |
| `src/config/sentry.config.ts` | Sentry and environment-aware mobile observability wiring |
| `eas.json` | EAS build profiles |
| `app.config.js` | Expo app config per environment/build |
| `__tests__/`, `e2e/` | Unit and device/e2e tests |
| `CODESPACE_DEV.md`, `QUICKSTART.md`, `BUILD_INSTRUCTIONS.md`, `DEPLOYMENT_GUIDE.md` | Mobile developer/operator docs |

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

### infrastructure/ — Supplemental Ops Assets

| File | Purpose |
|------|---------|
| `monitoring/README.md` | Monitoring stack overview |
| `monitoring/prometheus.yml` | Prometheus scrape configuration |
| `monitoring/prometheus-alerts-orchestration.yml` | Alert rules for orchestration/runtime health |
| `monitoring/grafana/` | Grafana dashboards and provisioning assets |
| `docker/docker-compose.yml` | Supplemental Docker stack outside the primary local/test compose files |
| `docker/*.Dockerfile` | Support Docker images for gateway/event-bus/orchestration assets |
| `kubernetes/` | K8s manifests/support files for non-Cloud-Run deployment paths |
| `gcp/`, `nginx/`, `opa/`, `ssl/` | Infra support assets for platform networking, policy, and certificates |

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
| `OPA_URL` | Plant Gateway | HTTPS URL to Plant OPA Cloud Run service — set by Terraform `module.plant_opa.service_url`; use `http://localhost:8181` locally |
| `OPA_SERVICE_URL` | Plant Gateway | Back-compat alias for `OPA_URL` — kept in sync |
| `ENVIRONMENT` | All | development / demo / uat / prod |
| `ENABLE_DB_UPDATES` | Plant | Enable DB update endpoints |
| `GCP_PROJECT_ID` | Terraform, Plant, CP BackEnd | GCP project identifier — required when `SECRET_MANAGER_BACKEND=gcp` |
| `SECRET_MANAGER_BACKEND` | CP BackEnd | `gcp` (demo/uat/prod via Terraform) or `local` (default for CI and local dev) — switches between `GcpSecretManagerAdapter` and `LocalSecretManagerAdapter` |
| `XAI_API_KEY` | Plant BackEnd | Grok API key (from [console.x.ai](https://console.x.ai)) — enables live AI content generation in `ContentCreatorSkill` and `ContentPublisherSkill`; absent (or `EXECUTOR_BACKEND` not `"grok"`) means deterministic template mode (zero API cost, zero dependency) (PLANT-CONTENT-1 #869). |
| `EXECUTOR_BACKEND` | Plant BackEnd | `"grok"` → use Grok API for content generation; any other value (or absent) → deterministic templates. Per-agent default — can be overridden via `ConstructBindings.processor_config` in future phases. (PLANT-CONTENT-1 #869). |
| `CAMPAIGN_PERSISTENCE_MODE` | Plant BackEnd | `"memory"` (default) → in-memory campaign dict; `"db"` → Processor writes to PostgreSQL. |
| `SCHEDULER_ENABLED` | Plant BackEnd | `"true"` (default) → all Scheduler firing is active; `"false"` → disable firing (test only). |
| `APPROVAL_GATE_ENABLED` | Plant BackEnd | `"true"` (default) → `ApprovalGateHook` active at `PRE_PUBLISH`; `"false"` → bypass gate in dev/demo. |
| `CIRCUIT_BREAKER_ENABLED` | Plant BackEnd | `"true"` (default); set `"false"` in unit tests only to avoid CB interference. |

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
| 8181 | Plant OPA | Internal — OPA policy engine (Cloud Run service-to-service only) |
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
| Agent mold playbooks | Agent behavior templates in `src/Plant/BackEnd/agent_mold/playbooks/`. Currently: `marketing/multichannel_post_v1.md`, `trading/delta_futures_manual_v1.md`. Skills library: `agent_mold/skills/` — see §4.6 for full index. |
| AgentSpec is in-memory only | `AgentSpec` / `ConstructBindings` / `ConstraintPolicy` / `LifecycleHooks` are created at startup from `reference_agents.py` and held in RAM. **There is no DB table for AgentSpec.** Only `agent_type_entity` (reference data) and `hired_agents` (customer instance) are persisted. |
| Processor constitutional rule | `BaseProcessor.execute()` **must NOT** access the database, manage credentials, or call the Publisher. It is purely computational. This makes every Processor unit-testable without mocking external APIs. |
| secret_ref is write-only | `platform_connections.secret_ref` is stored but **never returned in any GET response**. Only `CredentialResolver` can resolve it at runtime. Any GET of `/platform-connections` deliberately omits `secret_ref`. |
| TradingProcessor is always draft-only | `TradingProcessorOutput(draft_only=True)` always. Real order placement only happens inside `on_deliverable_approved` hook → `DeltaTradeAdapter.publish()`. Never short-circuit this. |
| ConstructBindings.processor_class is required | Every `AgentSpec` must declare its `processor_class`. An agent with no Processor cannot fire — Scheduler will raise `PermanentError` on the first attempt and DLQ it. |
| DimensionContract.register_hooks() | Each dimension's `register_hooks()` is called at mould compilation. Currently `BasicDimension` is a no-op — `TrialDimension` and `BudgetDimension` are being wired in MOULD-GAP-1. Do not add quota / budget enforcement inside service code — it belongs in the mould. |
| GitHub Actions concurrency | ALM workflow uses concurrency groups (vg-$issue, ba-sa-$issue, testing-$epic, deploy-$epic) to prevent duplicates. |
| go-coding label | Governor must manually apply `go-coding` label to an epic before Code Agent can run — this is a deliberate human gate. |
| Docker compose profiles | Use `docker-compose.local.yml` for full local dev. No separate test/prod compose currently. |
| Redis DB assignments | Each service uses a different Redis DB (0-3). Don't share DB indices. |
| Codespace browser URLs | Use `https://${CODESPACE_NAME}-{PORT}.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/` format. |
| No docs without asking | AI agents must NOT auto-create documentation files — always ask user first. |
| **`waooaw_router()` is mandatory everywhere** | Never use bare `APIRouter()` in any `api/` directory across CP, Plant, or PP. Ruff TID251 bans it in CI. Use `from core.routing import waooaw_router`. Core routing files: `src/CP/BackEnd/core/routing.py`, `src/Plant/BackEnd/core/routing.py`, `src/PP/BackEnd/core/routing.py`. |
| **OPA is Gate 1; Plant Backend is Gate 2** | Plant Gateway middleware queries OPA for RBAC/policy decisions (Gate 1 — role-level). Plant Backend `/api/v1/admin/db/*` has its own hard admin-role check `_require_admin_via_gateway` (Gate 2). A non-admin role may pass OPA Gate 1 for `resource="admin"` (level-based) but will be rejected at Gate 2. Never remove either gate. |
| **OPA Dockerfile — never add env-specific values** | `src/Plant/Gateway/opa/Dockerfile` must not contain env names, GCP URLs, secrets, or environment labels. Runtime config (log level only) is passed as Cloud Run env vars at deploy time. Image is built once and promoted demo → uat → prod. |
| **OPA CI test — use static binary, not Docker bind-mount** | GitHub Actions overlay filesystem rejects bind-mounts (`-v` flag on `docker run`). CI downloads `opa_linux_amd64_static` from GitHub releases and runs `opa test src/Plant/Gateway/opa -v` natively. Do NOT revert to `docker run -v`. |
| **Stacked PRs — always verify base branch after first PR merges** | When PR A and PR B are stacked (B based on A), merging A to main does NOT automatically rebase B to main. GitHub keeps B's base pointing at A's old branch. B's merge will land on the stale branch, not main. Always verify with `gh pr view <N> --json baseRefName` after merging the parent. Cherry-pick to main if needed (see PR #845 — #844 merged into `feat/PLANT-OPA-1-it1-e1` instead of `main`). |
| **OPA cold start on Cloud Run** | OPA service (`waooaw-plant-opa-{env}`) scales to zero on demo/uat (min_instances=0). First request after idle will hit an OPA cold start (~3s). Plant Gateway middleware has a circuit breaker — fails open on timeout rather than 500ing. For prod, set `min_instances=1` on the OPA module to eliminate cold-start latency. |
| **Correlation ID via ContextVar** | `require_correlation_id` is wired globally on all 4 apps. To read the current correlation ID anywhere in a request (e.g. in a service): `from core.dependencies import _correlation_id; cid = _correlation_id.get()`. Never pass correlation ID as a function argument — read from context. |
| **Audit = fire-and-forget only** | Always use `get_audit_logger` dependency in routes. Never call `AuditClient` directly from route handlers. All `audit.log()` calls schedule the HTTP call as an asyncio task — they never block the response. |
| **Read replica = GET/query operations ONLY** | `get_read_db_session()` for any endpoint that only reads. `get_db_session()` only for INSERT/UPDATE/DELETE. Rule enforced by code review — not a lint check. |
| **Circuit breakers are class-level, not per-request** | `_circuit_breaker` is a `ClassVar` (or module-level singleton). Do NOT create a new `CircuitBreaker()` instance inside `__init__` or per-request — state would be lost between requests. |
| **PII masking is automatic** | `PIIMaskingFilter` is wired at the root logger. Don't try to mask fields manually in route code. Debug by correlation ID or user_id — not by email (masked in logs). |
| **C8 (PII DB encryption) is PARKED** | Decision: never implement application-layer field encryption for `email`/`phone`/`full_name`. CMEK + masking + email_hash + GDPR erasure cover the compliance requirement. See Section 5.6. |
| **GCP auth is permanent in Codespace** | `waooaw-codespace-reader` SA activates automatically via `gcp-auth.sh` on every Codespace start. Run `gcloud auth list` to verify. Cloud SQL Proxy starts on port 15432 automatically. No user action needed. |
| **Cloud SQL Auth Proxy required** | `plant-sql-demo` has public IP enabled (8 Mar 2026) but always connect via Cloud SQL Auth Proxy on `127.0.0.1:15432` for IAM auth. Never connect directly on port 5432. If you get `connection refused` on 15432, proxy is not running — restart with `bash .devcontainer/gcp-auth.sh`. gcloud is pre-installed via `setup-slim.sh`; `source /root/.env.db && psql` is all you need after the proxy starts. |
| **SA role scope** | `waooaw-codespace-reader` has `cloudsql.admin` — can patch Cloud SQL settings (e.g. `gcloud sql instances patch plant-sql-demo --assign-ip`). Has `secretmanager.secretAccessor` — can read all secret values. |
| **Image promotion — no env baking** | **ONE image built once, promoted unchanged through demo → uat → prod.** All env-specific config MUST come from env vars (non-sensitive) or GCP Secret Manager (sensitive) — injected by terraform at deploy time. See §8.1 for the full checklist and §19 for code examples. **Terraform template anti-pattern that is BANNED**: `SOME_VAR = var.x != "" ? var.x : (var.environment == "demo" ? "value_a" : "value_b")` — this bakes environment-conditional logic into the template. Defaults belong in `variables.tf default =`, not in `main.tf` ternaries. Violations are reverted on review. This was found and fixed in PR #851 for CP Backend `PAYMENTS_MODE` and `OTP_DELIVERY_MODE`. |
| **`SecretManagerAdapter` — never call GCP SDK directly in routes** | CP BackEnd `services/secret_manager.py` provides the ABC. Routes call `get_secret_manager_adapter()` which reads `SECRET_MANAGER_BACKEND`. For `local`/CI: in-memory `LocalSecretManagerAdapter`. For `gcp`: `GcpSecretManagerAdapter` using Application Default Credentials on Cloud Run — no key file needed. Never instantiate `secretmanager.SecretManagerServiceClient` directly in a route or service other than `GcpSecretManagerAdapter`. |
| **Platform credential secrets — naming convention** | Platform connection credentials are stored as GCP Secret Manager secrets named `hired-{hired_instance_id}-{platform_key}`. The returned `secret_ref` is the full GCP resource path (e.g., `projects/waooaw-oauth/secrets/hired-abc123-instagram/versions/latest`). Only the `secret_ref` is forwarded to Plant BE and persisted in `platform_connections.secret_ref`. Raw credentials never leave CP BackEnd. |
| **CP BackEnd SA needs `secretmanager.secretVersionAdder`** | On first deploy of PLANT-SKILLS-1 It3 (#846), verify CP BackEnd's Cloud Run SA has `roles/secretmanager.secretVersionAdder` (or `roles/secretmanager.admin`). Without it, `POST /cp/hired-agents/{id}/platform-connections` will return 500. Check: `gcloud projects get-iam-policy waooaw-oauth --flatten="bindings[].members" --filter="bindings.members:serviceAccount:waooaw-cp-backend@waooaw-oauth.iam.gserviceaccount.com" --format="table(bindings.role)"` |
| **OPA `delete_agent` mis-classification (fixed PR #846)** | Before #846, `DELETE /api/v1/agents/{id}/skills/{skill_id}` was classified as `action=delete_agent` in `policy.py`, triggering the `SENSITIVE_ACTIONS` governor_role check. Fixed: `delete_agent` now only fires when `len(parts) <= 2`; deeper paths (sub-resources like `skills`) use `resource=parts[2]`, `action=delete`. |
| **Google Sign-In — never use `tokeninfo`** | The `tokeninfo` HTTP endpoint is banned by Google for production (debug-only). All three backends (CP, PP, Plant) use `google.oauth2.id_token.verify_oauth2_token()` from `google-auth[requests]>=2.25.0`. This validates RSA signature locally via cached JWKs and enforces `aud`, `iss`, `exp`. |
| **Google Sign-In — `aud` = Web client ID** | `GOOGLE_CLIENT_ID` in GCP Secret Manager (project `waooaw-oauth`) must be the **Web client ID** (`270293855600-uoag582a…`), NOT the Android client ID. Plant backend reads this via `settings.google_client_id`. Already verified correct. |
| **Google Sign-In — Play App Signing SHA-1** | When distributing via Play Store (even internal testing), Google re-signs the AAB. The device presents Play App Signing SHA-1 to GCP OAuth, not the EAS keystore SHA-1. **FIXED (PR #755, 2026-02-24)**: Play App Signing SHA-1 `8F:D5:89:B1:20:14:85:E3:73:E8:0C:C0:B0:1B:56:74:E5:2F:5F:FA` is now registered in: (1) `google-services.json` (type-1 Android OAuth client), (2) Firebase Console → waooaw-oauth → `com.waooaw.app` → SHA certificate fingerprints, (3) GCP Console → Credentials → Android OAuth client `270293855600-2shlgots…`. Access: Play Console → Your app → Setup → App integrity → App signing → App signing key certificate. |
| **`eas build:view` has no `--non-interactive` flag** | The flag is invalid and causes a hard failure. CI uses `eas build:view "$BUILD_ID" --json` (no flag). EAS CLI emits spinner text before the JSON; always strip with `awk '/^[{\[]/{found=1} found{print}'` before piping to `jq`. |
| **EAS `test-apk` profile** | Direct APK install that bypasses Play Store re-signing. Uses EAS keystore SHA-1 (`14f7ccef…`) which is already registered in GCP. Use this for testing Google Sign-In without Play Store. Download from Expo dashboard, install with "unknown sources" enabled. |

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
| **Image promotion path** | **ONE Docker image per service, promoted unchanged demo → uat → prod.** Never bake env-specific values (DB URL, timeouts, tracing, log levels, feature flags) into images. All config comes from env vars, Secret Manager, or tfvars. See "Environment Configuration Rules" below. |

### Environment Configuration Rules (Image Promotion Path)

> **CRITICAL**: We follow the **12-factor app** principle. A single Docker image is built once and promoted unchanged through all environments. Environment-specific behavior is controlled EXTERNALLY.

#### What MUST be external (env vars / Secret Manager / tfvars)

| Category | Examples | Where it's injected |
|----------|----------|--------------------|
| **Database** | `DATABASE_URL`, connection pool size, SSL mode | Cloud Run env vars / Secret Manager |
| **Timeouts** | Request timeout, DB query timeout, retry intervals | Cloud Run env vars |
| **Tracing / Observability** | `OTEL_EXPORTER_ENDPOINT`, trace sample rate, `ENABLE_TRACING` | Cloud Run env vars |
| **Logging** | `LOG_LEVEL` (DEBUG/INFO/WARNING), `LOG_FORMAT` (json/text), verbose mode | Cloud Run env vars |
| **Feature flags** | `ENABLE_2FA`, `ENABLE_AUDIT_LOG`, `MAINTENANCE_MODE` | Cloud Run env vars |
| **Secrets** | `JWT_SECRET`, `CP_REGISTRATION_KEY`, API keys, OAuth credentials | GCP Secret Manager |
| **Service URLs** | `PLANT_GATEWAY_URL`, `REDIS_URL`, inter-service endpoints | Cloud Run env vars / tfvars |
| **Scaling** | Min/max instances, CPU, memory | Terraform tfvars (`cloud/terraform/environments/{env}.tfvars`) |
| **Domain / CORS** | `ALLOWED_ORIGINS`, domain mappings | Terraform tfvars |

#### What is ALLOWED in the Docker image

| Allowed | Example |
|---------|--------|
| Application code | Python source, compiled frontend assets |
| Default config values | Sensible defaults that get overridden by env vars |
| Static assets | CSS, JS bundles, images |
| Dependencies | `requirements.txt`, `node_modules` |

#### Terraform Template Anti-Patterns (BANNED)

These patterns bake environment knowledge into the terraform template, violating the image promotion rule. They are rejected on code review.

```hcl
# ❌ BANNED: ternary with hardcoded fallback value
PAYMENTS_MODE = var.payments_mode != "" ? var.payments_mode : "razorpay"

# ❌ BANNED: env-conditional logic in template (found in CP terraform, fixed PR #851)
OTP_DELIVERY_MODE = var.otp_delivery_mode != "" ? var.otp_delivery_mode : (var.environment == "demo" ? "disabled" : "provider")

# ✅ CORRECT: clean passthrough — defaults live in variables.tf
PAYMENTS_MODE     = var.payments_mode     # variables.tf: default = "razorpay"
OTP_DELIVERY_MODE = var.otp_delivery_mode # variables.tf: default = "provider"
```

The template is a passthrough. `variables.tf` holds safe defaults. `environments/{env}.tfvars` overrides per environment. Sensitive values (API keys, JWT secrets, DB URLs) go in `secrets {}` sourced from GCP Secret Manager — never in `env_vars {}`.

**Quick rule**: if you write `var.environment` anywhere inside `env_vars = {}`, stop — you are baking environment logic into the template.
| Health check endpoints | `/health`, `/ready` |

#### ❌ NEVER do this

```dockerfile
# ❌ WRONG — hardcoding env-specific values in Dockerfile
ENV DATABASE_URL=postgresql://waooaw:pass@demo-db:5432/waooaw_db
ENV LOG_LEVEL=DEBUG
ENV PLANT_GATEWAY_URL=https://gateway-demo.waooaw.com
```

```python
# ❌ WRONG — hardcoding env-specific values in source code
DATABASE_URL = "postgresql://waooaw:pass@demo-db:5432/waooaw_db"
TIMEOUT = 30 if environment == "prod" else 5  # Don't branch on env name
```

#### ✅ DO this instead

```python
# ✅ CORRECT — read from environment with sensible defaults
import os

DATABASE_URL = os.environ["DATABASE_URL"]  # Required — fail fast if missing
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")  # Optional with default
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))  # Default 30s
ENABLE_TRACING = os.environ.get("ENABLE_TRACING", "false").lower() == "true"
```

```hcl
# ✅ CORRECT — environment-specific values in tfvars
# cloud/terraform/environments/demo.tfvars
log_level       = "DEBUG"
request_timeout = 5
enable_tracing  = true
min_instances   = 0

# cloud/terraform/environments/prod.tfvars
log_level       = "WARNING"
request_timeout = 30
enable_tracing  = true
min_instances   = 2
```

#### Image promotion flow

```
Build (CI)          Deploy (CD)
─────────           ──────────────────────────────────────
                    ┌─────────────────────────────────────┐
code ──► image:v1 ──┤  demo  (env vars from demo.tfvars)  │
     (one build)    │  uat   (env vars from uat.tfvars)   │
                    │  prod  (env vars from prod.tfvars)  │
                    └─────────────────────────────────────┘
```

> **Agent checkpoint**: Before committing any change, verify: *"Would this change behave differently if the same Docker image were deployed to demo vs prod?"* If yes → the config MUST be externalized.

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
| Platform connection credentials | (runtime-written) | `hired-{hired_instance_id}-{platform_key}` | CP Backend (write), Plant Backend (read via `secret_ref`) | NO — different secret per connection; written at POST time by `GcpSecretManagerAdapter` |

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

#### GCP authentication in Codespace — ALREADY CONFIGURED

> **GCP auth is permanent.** The `waooaw-codespace-reader` SA activates automatically on every Codespace start via `.devcontainer/gcp-auth.sh`.

```bash
# --- Verify auth (run first, should always show ACTIVE) ---
gcloud auth list
# Expected: waooaw-codespace-reader@waooaw-oauth.iam.gserviceaccount.com  ACTIVE

# --- If not active (e.g. after manual gcloud logout) ---
bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh

# --- What the script does on each boot ---
# 1. Reads GCP_SA_KEY Codespace secret → /root/.gcp/waooaw-sa.json
# 2. gcloud auth activate-service-account --key-file=/root/.gcp/waooaw-sa.json
# 3. gcloud config set project waooaw-oauth
# 4. Starts cloud-sql-proxy on 127.0.0.1:15432 (→ plant-sql-demo)
# 5. Reads demo-plant-database-url from Secret Manager
# 6. Writes /root/.pgpass + /root/.env.db for passwordless psql
```

> **SA**: `waooaw-codespace-reader@waooaw-oauth.iam.gserviceaccount.com`  
> **Roles**: `logging.viewer`, `run.viewer`, `cloudsql.admin`, `cloudsql.client`, `secretmanager.viewer`, `secretmanager.secretAccessor`  
> **Scope**: read-only on logs/services, full read on secrets, admin on Cloud SQL

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
gcloud sql instances describe plant-sql-demo --format="value(ipAddresses)"  # Check IPs
gcloud sql instances patch plant-sql-demo --assign-ip --quiet  # Enable public IP (SA has cloudsql.admin)
gcloud sql operations list --instance=plant-sql-demo --filter="status!=DONE"  # Check running ops

# --- Connect to demo DB (proxy auto-started, just run psql) ---
source /root/.env.db && psql                               # Recommended
psql -h 127.0.0.1 -p 15432 -U plant_app plant             # Direct

# --- Proxy management ---
cat /tmp/cloud-sql-proxy.log                               # Check proxy status
pgrep -fa cloud-sql-proxy                                  # Confirm proxy PID
bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh          # Restart if needed

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

### Runtime Validation Playbook — verified on demo (9 Mar 2026)

Use this when validating `PLANT-RUNTIME-1` or any CP FrontEnd -> CP BackEnd -> Plant runtime contract.

#### 1. Validate in this order

| Step | Root cause avoided | Impact if skipped | Best possible solution/fix |
|------|--------------------|-------------------|----------------------------|
| 1. Plant Gateway public route | CP proxy can hide upstream route drift behind nested 404s | You misclassify a Plant defect as a CP defect | Probe `waooaw-plant-gateway-{env}` first for the canonical Plant path |
| 2. CP Backend proxy route | CP proxy may still target stale upstream paths | You miss thin-proxy breakage even when Plant is healthy | Probe `waooaw-cp-backend-{env}` second with the same business identifier |
| 3. CP FrontEnd service file | Frontend may still call an outdated CP route | You blame backend only and miss the actual caller | Confirm the exact frontend service path before classifying the defect |
| 4. Live DB row shape | Demo data mixes UUID-backed and external-id-backed records | False negatives from invalid identifiers | Pull one real row from Cloud SQL before testing non-list endpoints |

#### 2. Use the correct public surface

| Surface | Use for | Notes |
|---------|---------|-------|
| `waooaw-plant-gateway-{env}` | Public validation of Plant customer-facing runtime routes | Preferred first hop for deployed runtime validation |
| `waooaw-cp-backend-{env}` | CP proxy validation (`/api/cp/*`, `/api/auth/*`) | Use after Plant Gateway so you can separate proxy drift from upstream drift |
| `waooaw-plant-backend-{env}` | Logs, revision inspection, service metadata | Direct HTTP access is Cloud Run IAM-protected; do not expect anonymous curl from Codespace to work |

#### 3. Cloud SQL proxy gotchas that were verified live

| Root cause | Impact | Best possible solution/fix |
|------------|--------|----------------------------|
| `gcp-auth.sh` completed but Cloud SQL proxy could not attach because the instance had no `PUBLIC` IP | `psql` hangs or fails even though auth setup appears complete | Check `/tmp/cloud-sql-proxy.log`; if it says `instance does not have IP of type PUBLIC`, run `gcloud sql instances patch plant-sql-demo --assign-ip --project=waooaw-oauth --quiet`, wait for the operation to finish, then rerun `bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh` |
| Proxy process exists but tunnel is stale | Ad hoc SQL checks return misleading connection failures | `pgrep -fa cloud-sql-proxy`, `cat /tmp/cloud-sql-proxy.log`, then restart the auth script |
| Assuming docs imply direct DB connectivity on `5432` | Wasted time debugging the wrong socket | Always use `source /root/.env.db && psql` or `psql -h 127.0.0.1 -p 15432 -U plant_app plant` |

#### 4. Schema assumptions that caused false starts

Inspect `information_schema.columns` before writing ad hoc queries. Demo schema contains these verified shapes:

| Table | Verified column(s) to use | Do not assume |
|-------|---------------------------|---------------|
| `customer_entity` | `id`, `email`, `full_name`, `business_name` | `customer_id` does not exist in this table |
| `hired_agents` | `hired_instance_id`, `agent_id`, `customer_id`, `active`, `configured`, `goals_completed` | A generic `status` column |
| `agent_skills` | `agent_id`, `skill_id`, `goal_config` | Skill config lives only in a separate logical surface |
| `skill_configs` | `hired_instance_id`, `skill_id`, `customer_fields`, `pp_locked_fields` | Free-form names without checking the table first |

#### 5. Identifier discipline for live probes

| Root cause | Impact | Best possible solution/fix |
|------------|--------|----------------------------|
| Mixing external ids like `AGT-MKT-001` with UUID-backed routes | `422 Invalid UUID` can look like a route defect | Query the live row first and probe with the exact identifier type stored in the route contract |
| Demo hired agents are mixed: some point to UUID `agent_id`, others to external ids | One sample works, another fails for unrelated reasons | Treat every probe id as data-dependent until confirmed in SQL |
| Assuming a hired-agent route is equivalent to an agent route | False confidence because legacy `/api/v1/agents/{agent_id}/skills` still exists | Test the canonical hired-agent route separately; legacy agent routes do not prove Iteration 1 is deployed |

#### 6. CP request-chain tracing entry points

Start here when a CP UI flow fails and you need the exact hop sequence.

| Surface | First file to inspect | What it controls |
|---------|-----------------------|------------------|
| CP FrontEnd hired-agent skills | `src/CP/FrontEnd/src/services/agentSkills.service.ts` | `/api/cp/hired-agents/{id}/skills` and goal-config save calls |
| CP FrontEnd platform connections | `src/CP/FrontEnd/src/services/platformConnections.service.ts` | Hired-agent platform-connection calls |
| CP BackEnd hired-agent skills proxy | `src/CP/BackEnd/api/cp_skills.py` | CP -> Plant translation for hired-agent skills and goal-config |
| CP BackEnd flow/component runs proxy | `src/CP/BackEnd/api/cp_flow_runs.py` | CP -> Plant flow-runs and component-runs targets |
| CP BackEnd scheduler proxy | `src/CP/BackEnd/api/cp_scheduler.py` | Trial budget, scheduler summary, pause/resume |
| CP BackEnd approvals proxy | `src/CP/BackEnd/api/cp_approvals_proxy.py` | Approval queue, approve, reject |

#### 7. Known runtime drift patterns observed on demo

These are environment findings, not normative architecture. Re-check before acting on them.

| Root cause | Impact | Best possible solution/fix |
|------------|--------|----------------------------|
| Plant Gateway exposes legacy `/api/v1/agents/{agent_id}/skills` but not canonical hired-agent skills route | Iteration 1 hired-agent skill surface fails even though a nearby legacy route still works | Deploy the hired-agent route from `PLANT-RUNTIME-1` and do not treat the legacy agent route as equivalent |
| Plant Gateway does not expose `/api/v1/hired-agents/by-id/{id}`, `/api/v1/skill-runs`, or `/api/v1/component-runs` on demo | Iteration 2 CP proxy routes fail with nested upstream 404s | Deploy the normalized Plant runtime surface before debugging CP behavior |
| Some route inventories still include malformed paths like `/api/v1/v1/...` | Proxy construction bugs are harder to spot during manual validation | Inspect OpenAPI and route inventories for duplicated version prefixes whenever route-not-found responses look inconsistent |

#### 8. Auth guidance for runtime validation

| Use case | Recommended method |
|----------|--------------------|
| Plant Gateway customer-route validation | Mint a short-lived customer access JWT from `JWT_SECRET` and call the gateway directly |
| CP proxy validation | Prefer a real CP session or a known-good refresh token captured from the deployed flow; do not assume an ad hoc signed refresh token will always satisfy CP refresh semantics |
| Direct Plant Backend validation | Use logs/OpenAPI/service metadata unless you also have Cloud Run IAM invocation rights |

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

**Answer**: GCP auth is **permanently configured** in this Codespace via the `waooaw-codespace-reader` SA. You should be able to run `gcloud` commands immediately.

| Situation | Action |
|-----------|--------|
| Normal case | `gcloud auth list` shows `waooaw-codespace-reader@waooaw-oauth.iam.gserviceaccount.com ACTIVE` — proceed directly |
| Auth missing (e.g. after container rebuild before `GCP_SA_KEY` secret propagates) | Run `bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh` |
| SA not authorized for an action | Check SA roles in Section 9. If missing a role, ask user to grant it from Cloud Shell. |
| Need DB access | Cloud SQL Proxy auto-starts on port 15432. Run `source /root/.env.db && psql` — no further setup needed. |

**Quick auth check script:**
```bash
# Run this FIRST before any gcloud command
if gcloud auth list 2>/dev/null | grep -q ACTIVE; then
  echo "✅ GCP auth active — $(gcloud config get-value account 2>/dev/null)"
else
  echo "⚠️ Re-running auth setup..."
  bash /workspaces/WAOOAW/.devcontainer/gcp-auth.sh
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

## 23. Mobile Application — CP Mobile

> **Full reference**: `docs/mobile/mobile_approach.md`  
> **Current status**: Active — Android (Play Store internal testing) + iOS (EAS profile added, Apple Sign-In wired — MOBILE-NFR-1 #868).  
> **Current focus**: `demo` environment. Use `uat`/`prod` only when those environments are needed.  
> **Last updated**: 2026-03-07

---

### Overview

| Aspect | Detail |
|--------|--------|
| **App** | WAOOAW CP Mobile — customer-facing marketplace for browsing, hiring, and managing AI agents |
| **Platform** | React Native (Expo Managed Workflow) |
| **Targets** | Android (API 31+, Android 12+); iOS (iOS 15+) — iOS build pending |
| **Package** | `com.waooaw.app` |
| **EAS account** | `waooaw` (https://expo.dev/accounts/waooaw) |
| **EAS project ID** | `fdb3bbde-a0e0-43f9-bf55-e780ecc563e7` |
| **Source path** | `src/mobile/` |
| **Full docs** | `docs/mobile/mobile_approach.md` |

---

### Mobile Iterations (Living Log)

Mobile work is tracked in `docs/mobile/iterations/`.

| Doc | What it’s for | Key takeaways for implementers/testers |
|---|---|---|
| `docs/mobile/iterations/it_1.md` | Iteration 1 delivery log (branch: `feat/mobile-it1-safe-area-logo-signup`, status: complete) | Safe-area handling is mandatory on Android edge-to-edge; logo assets were standardized; SignUp form is now web-CP parity; Plant auth OTP endpoints must exist and be public in Gateway. |
| `docs/mobile/iterations/registration.md` | Registration issues from real Firebase Test Lab / CI evidence | Mobile registration is Plant-Gateway-direct and has **no CAPTCHA**; historical failures were caused by (1) React version mismatch crash and (2) Plant Gateway PolicyMiddleware treating unauth auth routes as JWT-required; watch for API base URL misconfiguration pointing at CP instead of Plant. |
| `docs/mobile/iterations/MOBILE-FUNC-1-functional-completeness.md` | All 3 iterations merged — real deliverables API, 9 missing screens created and registered, Razorpay SDK un-stubbed, FCM push notification registration (PRs #864, #865, #866, #867 — 2026-03-06) | `TrialDashboardScreen.tsx` now uses React Query against real `GET /api/v1/deliverables` (replaces static mock). `EditProfileScreen.tsx` calls Plant Gateway `PATCH /api/v1/customers/profile` directly (not CP Backend). `pushNotifications.service.ts` registers FCM token after sign-in via Plant Backend `POST /api/v1/customers/fcm-token` (PR #866). New screens live in `src/mobile/src/screens/{discover,agents,profile}/` and are registered in `MainNavigator`. Razorpay SDK is fully un-stubbed — `razorpay.service.ts` imports real `RazorpayCheckout`. |
| `docs/mobile/iterations/MOBILE-NFR-1-nfr-hardening.md` | Both iterations merged — Sentry active, React Query retry + interceptor retry, sign-up throttle, OTP cooldown, iOS EAS profile, Apple Sign-In (PR #868 — 2026-03-06) | `@sentry/react-native` real import; DSN injected per-environment (env-gated). React Query hooks have `retryDelay` exponential back-off. `cpApiClient.ts` response interceptor retries 429/5xx up to 3 times. Sign-Up submit throttle (2s cooldown) + 60s OTP resend timer added. iOS EAS build profile added to `eas.json`; `expo-apple-authentication` added and Apple Sign-In button wired. |

> **Testing rule (mobile)**: All tests are executed in Docker/Codespace (no local venv/virtualenv assumption for backend parity). Mobile unit tests run via `cd src/mobile && npm test` in the devcontainer environment.

---

### Architecture Role

The mobile app is a **CP-equivalent client** — it talks directly to the **Plant Gateway** (port 8000), the same as CP Backend does. It does **not** go through CP Backend.

```
Mobile App
  → Plant Gateway (/:8000) [JWT auth, RBAC, policy]
    → Plant Backend (:8001) [business logic, DB]
```

This means the mobile API base URL is the Plant Gateway URL, not the CP backend URL (`cp.*.waooaw.com`).

---

### Registration & OTP (Mobile vs CP Web)

**Mobile registration (actual, current design)** — all calls go to **Plant Gateway directly** (no CP backend involvement):

1. `POST /auth/register` — submits full sign-up form (business + contact fields)
2. `POST /auth/otp/start` — sends `{ "registration_id": "<uuid>" }` (NOT email)
3. User enters OTP on `OTPVerificationScreen`
4. `POST /auth/otp/verify` — sends `{ "otp_id": "...", "code": "..." }` → returns JWT tokens

**CP web registration (separate flow)** — uses CP backend endpoints (namespaced under `/api/cp/...`) and includes CAPTCHA/Plant duplicate checks:

- `POST /api/cp/auth/register/otp/start` (CP backend) → CAPTCHA + Plant duplicate lookup + OTP session create (via Plant Gateway)
- `POST /api/cp/auth/register` (CP backend) → OTP verify + customer creation (via Plant Gateway)

**Gotcha**: If a mobile build points its API base URL at `https://cp.<env>.waooaw.com` instead of `https://plant.<env>.waooaw.com`, auth endpoints like `/auth/register` will not exist (CP backend exposes `/api/cp/auth/...`), producing misleading failures.

**Plant Gateway requirement**: `/auth/register`, `/auth/otp/start`, and `/auth/otp/verify` must be treated as **public endpoints** (no JWT) consistently across Auth/RBAC/Policy middleware.

**Verification quick checks (demo)**:

```bash
# Plant Gateway should return 422 (validation), NOT 500 (JWT required)
curl -sS -o /dev/null -w "%{http_code}\n" -X POST https://plant.demo.waooaw.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com"}'

# If this returns 404, your mobile build is probably hitting CP Backend (wrong base URL)
curl -sS -o /dev/null -w "%{http_code}\n" -I https://cp.demo.waooaw.com/auth/register
```

---

### Environments

Aligns with platform-wide standard. `EXPO_PUBLIC_ENVIRONMENT` (set inline in `eas.json` per profile) drives runtime behaviour.

| Environment | `EXPO_PUBLIC_ENVIRONMENT` | Plant API Base URL | Build type | Play Store track |
|---|---|---|---|---|
| `development` | `development` | `https://${CODESPACE_NAME}-8000.app.github.dev` (runtime) | APK (debug) | — |
| `demo` | `demo` | `https://plant.demo.waooaw.com` | AAB (store) | internal |
| `uat` | `uat` | `https://plant.uat.waooaw.com` | APK (release) | alpha |
| `prod` | `prod` | `https://plant.waooaw.com` | AAB (store) | production |

---

### EAS Build Profiles (`src/mobile/eas.json`)

| Profile | `distribution` | `channel` | EAS `environment` | Output |
|---|---|---|---|---|
| `development` | `internal` | `development` | `development` | APK (debug, Expo dev client) |
| `test-apk` | `internal` | — | `production` | APK (release) — **use this to test without Play Store re-signing** |
| `demo` | `store` | `demo` | `production` | AAB (release) |
| `uat` | `internal` | `uat` | `production` | APK (release) |
| `prod` | `store` | `production` | `production` | AAB (release) |

> **EAS constraint**: Custom environment names (`demo`, `uat`, `prod`) require a paid EAS plan. Free plan only supports `development`, `preview`, `production`. All three store profiles map to EAS `"environment": "production"` to get secrets injected. Runtime environment is differentiated via `EXPO_PUBLIC_ENVIRONMENT`.

---

### EAS Secrets (in EAS `production` environment)

> **Note**: These are pushed by CI from GitHub Secrets before each build (`eas secret:push`). See "Secrets — GitHub Secrets vs EAS Secrets" subsection below for full details.

| Variable | Value | Purpose |
|---|---|---|
| `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO` | `270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com` | Android OAuth (type=1 client; package `com.waooaw.app`) |
| `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_DEMO` | `270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com` | Backend token exchange only |
| `EXPO_PUBLIC_API_URL_DEMO` | `https://plant.demo.waooaw.com` | Plant Gateway base URL |
| `EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_DEMO` | `com.googleusercontent.apps.270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu` | Custom URI scheme for OAuth redirect |

---

### Technology Stack

| Layer | Technology |
|---|---|
| Framework | React Native + Expo Managed Workflow |
| Language | TypeScript |
| Navigation | `@react-navigation/native` (stack + bottom tabs) |
| State | Zustand (auth, UI) + React Query (server state) |
| HTTP | axios (same as web CP) |
| Auth | `@react-native-google-signin/google-signin` v16 (native SDK); JWTs minted by Plant via `POST /auth/google/verify`. Configure with `webClientId` so `aud` claim = Web client ID. |
| Storage | `secureStorage` wrapper: SecureStore (native) + web fallback (localStorage/sessionStorage/in-memory); AsyncStorage used for cache/backfill |
| UI | `react-native-paper`, `react-native-linear-gradient` |
| Lists | `@shopify/flash-list` ^1.8.3 (NOT v2 — requires new architecture) |
| Build | EAS CLI v18 (`eas-cli`) |
| OTA updates | Expo Updates (`expo-updates`) via EAS channels |
| Error tracking | `@sentry/react-native` (disabled in demo; enabled in uat/prod) |
| Testing | Jest + `@testing-library/react-native` + Detox (E2E) |

---

### Source Directory (`src/mobile/src/`)

| Directory | Contents |
|---|---|
| `config/` | `environment.config.ts`, `api.config.ts`, `oauth.config.ts`, `sentry.config.ts`, `razorpay.config.ts` |
| `screens/` | All app screens (auth/, agents/, home/, profile/, etc.) |
| `navigation/` | `RootNavigator`, `AuthNavigator`, `MainNavigator` — `AuthNavigator` uses render-prop pattern (not `component=` shorthand) for all three auth screens so custom props are forwarded. Sign In → Sign Up → OTP Verification stack. |
| `store/` | Zustand stores (`authStore.ts`, `uiStore.ts`) |
| `hooks/` | Custom hooks (`useGoogleAuth.ts`, `useAuthState.ts`, etc.) |
| `services/` | API service layer (mirrors CP web services) |
| `components/` | Shared UI components |
| `lib/` | `apiClient.ts` (axios instance) |
| `theme/` | Colors, typography, spacing tokens (dark theme) |
| `types/` | TypeScript type definitions |

### Key Root Files (`src/mobile/`)

| File | Purpose |
|---|---|
| `eas.json` | EAS build profiles (development / demo / uat / prod) |
| `app.json` | Expo config — package name, version, plugins, scheme. Icon assets: `icon` = `./assets/WAOOAW Logo.png` (iOS, full-bleed OK); `android.adaptiveIcon.foregroundImage` = `./assets/adaptive-icon.png` (padded — logo at 682×682 centred on 1024×1024 transparent canvas, 17% gutter each side); `splash.image` = `./assets/WAOOAW Logo.png`. |
| `package.json` | Dependencies + npm scripts |
| `App.tsx` | App entry — Expo root + navigation shell. Wraps tree with `<SafeAreaProvider>` (required for `useSafeAreaInsets()` to return non-zero insets on Android edge-to-edge). |
| `secrets/google-play-service-account.json` | Play Store service account (gitignored; also in GCP Secret Manager) |

---

### Authentication (Google OAuth2 — Android)

### Codespaces Web Preview (Expo `--web`)

When running the mobile app as a **web preview** in Codespaces, two things matter:

1. **Env var injection happens at dev-server start** — ensure the Expo process is started with `EXPO_PUBLIC_API_URL` and `EXPO_PUBLIC_GOOGLE_*` variables set, otherwise Google sign-in fails with `Missing required parameter: client_id`.

2. **Web needs an ID token** — the web provider flow must request an `id_token` so the app can exchange it at the Plant Gateway (`POST /auth/google/verify`).

3. **Token persistence on web** — `expo-secure-store` can be unavailable/blocked on web; token persistence uses the `secureStorage` web fallback so successful backend exchange does not fail at the “save tokens” step.

Critical implementation rules for Android with `@react-native-google-signin/google-signin` v16 (PR #751 — replaces deprecated `expo-auth-session`):

1. **Configure with `webClientId`** — the native SDK signs in silently via Google Play Services. The `webClientId` (GCP Web OAuth client, type=3) is passed to `GoogleSignin.configure()`. This is what sets the `aud` claim in the returned ID token so backends can validate it with `verify_oauth2_token()`. Do NOT pass the Android client ID here.

2. **ID token is returned directly** — `GoogleSignin.signIn()` returns `{ data: { idToken, user } }` — no redirect URI, no Chrome Custom Tab, no intent filter needed. The `idToken` is sent to `POST /auth/google/verify`.

3. **`DEVELOPER_ERROR` means SHA-1 mismatch** — the SHA-1 of the signing certificate on the device must match an entry in the GCP Android OAuth client (`270293855600-2shlgots…`). Two relevant SHA-1s:
   - **EAS keystore**: `14:F7:CC:EF:B7:D5:1C:1B:2F:FE:01:97:A5:D2:F6:9B:4F:B6:74:95` — registered, used for direct APK/AAB installs
   - **Play App Signing**: not yet registered — only obtainable after first AAB upload to Play Console → Setup → App integrity

4. **`DEVELOPER_ERROR` is now fixed for Play Store builds (PR #755)** — Play App Signing SHA-1 (`8F:D5:89:B1:20:14:85:E3:73:E8:0C:C0:B0:1B:56:74:E5:2F:5F:FA`) has been added to `google-services.json`, Firebase Console, and GCP OAuth Android client. Both EAS keystore and Play signing key are now registered. The fix takes effect from the next Play Store build. The registered SHA-1s are:
   - **EAS keystore** (upload key): `14:F7:CC:EF:B7:D5:1C:1B:2F:FE:01:97:A5:D2:F6:9B:4F:B6:74:95`
   - **Play App Signing key**: `8F:D5:89:B1:20:14:85:E3:73:E8:0C:C0:B0:1B:56:74:E5:2F:5F:FA` ← this was missing, now added

4b. **`test-apk` EAS profile bypasses Play Store re-signing** — for direct APK testing (`distribution: internal`). Builds are signed with the EAS keystore (SHA-1 above), no Play Store re-signing → no `DEVELOPER_ERROR`. Use `eas build --profile test-apk`.

5. **After OAuth success** — must call `login(authUser)` from `authStore` AND `userDataService.saveUserData(authUser)`. Without this, `isAuthenticated` stays false and navigation never switches to `MainNavigator`.

6. **On app restart** — `authStore.initialize()` has SecureStore fallback: if AsyncStorage is empty (Google auth writes to SecureStore, not AsyncStorage), reads from SecureStore and backfills AsyncStorage.

```typescript
// src/mobile/src/hooks/useGoogleAuth.ts — current implementation (v16 native SDK)
import { GoogleSignin, isSuccessResponse, isCancelledResponse } from '@react-native-google-signin/google-signin';

GoogleSignin.configure({ webClientId: process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID });

// Hook returns: { promptAsync, loading, error, userInfo, idToken, isConfigured }
// Call promptAsync() — NOT signIn() directly — to trigger the sign-in flow.

const promptAsync = async () => {
  await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });

  // CRITICAL: signOut() FIRST — clears Play Services credential cache.
  // Without this, signIn() silently reuses the last account and bypasses
  // the account chooser. signOut() does NOT revoke the user's Google grant.
  try { await GoogleSignin.signOut(); } catch { /* not signed in — OK */ }

  const response = await GoogleSignin.signIn();
  if (isCancelledResponse(response)) return;  // user dismissed picker
  if (!isSuccessResponse(response)) return;

  const { idToken } = response.data;
  // POST idToken to Plant Gateway /auth/google/verify
  // → { access_token, refresh_token, token_type, expires_in }
  // Then: authStore.login(user) + userDataService.saveUserData(user)
};
```

---

### Certificate Fingerprints & SHA-1 Keys

**Critical for Google OAuth Android Client Configuration**

When using EAS Build + Play Store App Signing, there are **two separate certificates**:

1. **Upload Certificate** (EAS-managed)
   - Used by EAS to sign the AAB before uploading to Play Store
   - ❌ **DO NOT use this SHA-1 for OAuth configuration**
   - Managed internally by Expo, not accessible to developers

2. **App Signing Certificate** (Play Store-managed)
   - Play Store re-signs the app with this certificate before distribution
   - ✅ **THIS is the correct SHA-1 for Google OAuth Android client**
   - Users' devices verify against this certificate

#### Current Production SHA-1 (App Signing Certificate)

| Algorithm | Fingerprint | Source | Last Verified |
|-----------|-------------|--------|---------------|
| **SHA-1** | `3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07` | Play Console → App Integrity | 2026-02-23 |

**Where this SHA-1 is used**:
- GCP OAuth 2.0 Android Client: `270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com`
- Package name: `com.waooaw.app`
- Redirect URI: `com.googleusercontent.apps.270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu:/oauth2redirect`

#### How to Extract SHA-1 from Play Console

**Method 1: Direct from Play Console UI**
```bash
# 1. Go to: Play Console → Your App → Setup → App integrity
# 2. Find "App signing key certificate" section (NOT "Upload certificate")
# 3. Copy the SHA-1 fingerprint displayed
```

**Method 2: Download and Extract Locally**
```bash
# 1. In Play Console → App integrity → Download app signing certificate as PEM
# 2. Extract SHA-1:
openssl x509 -in app-signing-cert.pem -noout -fingerprint -sha1

# Output format:
# SHA1 Fingerprint=3A:E5:69:D6:03:65:C3:FF:26:56:55:66:24:F6:DB:5C:C4:37:64:07
```

**⚠️ IMPORTANT: Do NOT use local keystore SHA-1**

The following commands extract fingerprints from **local keystores** which are **NOT valid** for EAS-managed builds:

```bash
# ❌ WRONG for production - this is the debug keystore
keytool -list -v -keystore ~/.android/debug.keystore \
  -alias androiddebugkey -storepass android -keypass android

# ❌ WRONG for EAS builds - EAS manages signing keys in the cloud
keytool -list -v -keystore /path/to/release.keystore -alias YOUR_ALIAS
```

#### Verification Before Each Release

Before promoting builds to production:

```bash
# 1. Get SHA-1 from Play Console (Method 1 above)
PLAY_SHA1="[paste from Play Console]"

# 2. Get SHA-1 from GCP OAuth client:
# https://console.cloud.google.com/apis/credentials
GCP_SHA1="[paste from GCP Console]"

# 3. Compare
if [ "$PLAY_SHA1" = "$GCP_SHA1" ]; then
  echo "✅ SHA-1 matches - OAuth will work"
else
  echo "❌ MISMATCH - Update GCP OAuth client immediately"
  echo "   Play Store: $PLAY_SHA1"
  echo "   GCP Config:  $GCP_SHA1"
fi
```

#### Emergency: OAuth Fails After Deployment

If Google sign-in suddenly fails with `Error 401: invalid_client` or `Error 400: invalid_request` after a Play Store release:

1. **Check for SHA-1 mismatch** - Play Store may have rotated the app signing key
2. **Extract current SHA-1** from Play Console (see methods above)
3. **Update GCP OAuth client** with new SHA-1
4. **Wait 5-10 minutes** for Google to propagate changes
5. **Test again** - OAuth should work with updated SHA-1

---

### CI/CD — GitHub Actions Workflow

**File**: `.github/workflows/mobile-playstore-deploy.yml`

| Input | Options | Default |
|---|---|---|
| `environment` | `demo`, `uat`, `prod` | `demo` |
| `track` | `internal`, `alpha`, `beta`, `production` | `internal` |
| `build_method` | `expo`, `local-eas`, `existing` | `expo` |
| `build_id` | (EAS build UUID) | — |

Profile mapping is now **1:1** — `environment` = `build-profile` (no more `demo → demo-store` translation).

**Version naming**: The workflow reads `expo.version` from `app.json` as-is and does NOT overwrite it. The `versionCode` is auto-incremented remotely by EAS (`appVersionSource: remote` + `autoIncrement: versionCode`). To bump the user-facing version, update `expo.version` in `src/mobile/app.json` and commit before triggering the workflow.

**Quick trigger (demo → Play Store internal)**:
```bash
gh workflow run mobile-playstore-deploy.yml \
  -f environment=demo -f track=internal -f build_method=expo
```

**Manual build + submit from Codespaces**:
```bash
export EXPO_TOKEN=<token>   # from https://expo.dev/accounts/waooaw/settings/access-tokens
cd src/mobile
eas build --platform android --profile demo --non-interactive
eas submit --platform android --profile demo --id <BUILD_ID> --non-interactive
```

---

### Testing

| Type | Command | Framework |
|---|---|---|
| Unit | `cd src/mobile && npm test` | Jest + React Native Testing Library |
| Unit (coverage) | `cd src/mobile && npm run test:coverage` | Jest coverage |
| E2E (Android) | `cd src/mobile && npm run test:e2e:android` | Detox |
| Firebase Test Lab | See `docs/mobile/mobile_approach.md` §13 | gcloud FTL (Robo test) |

**Verified FTL device matrix** (2026-02-21):
- `oriole` (Pixel 6), version `33` (Android 13) ✅
- `redfin` (Pixel 5), version `30` (Android 11) ✅
- ❌ Do NOT use `oriole+34` or `redfin+33` — incompatible, silently skipped

---

### Play Store Service Account

| Property | Value |
|---|---|
| Email | `waooaw-mobile-deployment@waooaw-mobile.iam.gserviceaccount.com` |
| Key file | `src/mobile/secrets/google-play-service-account.json` (gitignored) |
| GCP Secret Manager | `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` |
| GitHub Actions secret | `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` |
| Key path in eas.json | `./secrets/google-play-service-account.json` |

> **⚠️ Required one-time setup — Play Console permissions (NOT GCP IAM)**
>
> The service account needs **Release Manager** permission granted inside Google Play Console. This is separate from GCP IAM and must be done by whoever owns the Play Console developer account.
>
> 1. Open [play.google.com/console](https://play.google.com/console)
> 2. **Users and permissions** (left sidebar, account-level)
> 3. Find or invite: `waooaw-mobile-deployment@waooaw-mobile.iam.gserviceaccount.com`
> 4. Set role → **Release Manager**
> 5. Save — no acceptance/confirmation needed from the service account (it is not a real user)
>
> Without this, `eas submit` will fail with: *"The service account is missing the necessary permissions to submit the app to Google Play Store."*

---

### Mobile-Specific Gotchas

| Gotcha | Detail |
|---|---|
| `@shopify/flash-list` version | Must be `^1.8.3` — v2 requires `newArchEnabled: true` which is `false` in this app. App crashes on launch if v2 is used. |
| EAS secrets not injecting | Profile must have `"environment": "production"` in `eas.json`. Without it, `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID` is empty → falls back to web client ID → Google OAuth returns `Error 400`. |
| `eas token:create` does not exist | EAS CLI v18 removed this command. Create tokens at https://expo.dev/accounts/waooaw/settings/access-tokens |
| `eas download` rejects non-simulator builds | For AABs: use `curl -H "expo-session: $SESSION"` with the artifact URL from `eas build:view <ID> --json` |
| Play Store ignores re-uploads | If versionCode is the same as a previous upload, Play Console silently ignores it. `autoIncrement: versionCode` in `eas.json` handles this automatically. |
| `@react-native-google-signin` needs `webClientId` | Pass the **Web** OAuth client ID (not the Android one) to `GoogleSignin.configure({ webClientId })`. This sets the `aud` claim so backends can validate with `verify_oauth2_token()`. Using the Android client ID here causes `DEVELOPER_ERROR`. |
| `DEVELOPER_ERROR` = SHA-1 mismatch | Both SHA-1s are now registered: EAS keystore `14:F7:CC:EF…` and Play App Signing `8F:D5:89:B1…`. If error reappears after a Play Store release, re-check Play Console → App integrity for a rotated signing key. |
| OTP screen stuck after verification | `login()` must be called after `verifyOTP()` — AuthNavigator only switches to `MainNavigator` when `isAuthenticated === true` in Zustand store. |
| Re-auth on restart | `authStore.initialize()` must check SecureStore when AsyncStorage is empty (Google OAuth writes only to SecureStore, not AsyncStorage). |
| Google Sign-In skips account picker | `GoogleSignin.signIn()` silently reuses Play Services cached credentials. Always call `await GoogleSignin.signOut()` before `signIn()` in `promptAsync` to force the account chooser on every tap. `signOut()` clears cache only — it does NOT revoke the user's Google OAuth grant. |
| Adaptive icon clipped on Android | `android.adaptiveIcon.foregroundImage` must have a 17% transparent gutter on each side — Android's circular mask covers only the centre 66% of the canvas. Use a 1024×1024 canvas with the logo at ≤682×682 centred. Full-bleed images (no padding) will be clipped. Current file: `assets/adaptive-icon.png` (correct). Root `icon` for iOS can remain full-bleed. |
| React Navigation custom prop not received | Using `component={MyScreen}` shorthand passes only `navigation` and `route` props. To forward custom props (e.g. `onSignUpPress`), use the render-prop pattern: `<Stack.Screen name="X">{(props) => <MyScreen {...props} onSignUpPress={...} />}</Stack.Screen>`. AuthNavigator uses render-prop for all three auth screens. |
| `SafeAreaProvider` required at root | `react-native-safe-area-context` returns zero insets everywhere until `<SafeAreaProvider>` is mounted at the app root (`App.tsx`). Without it, `SafeAreaView edges` and `useSafeAreaInsets()` have no effect regardless of which edges are declared. |

---

### Secrets — GitHub Secrets vs EAS Secrets

**These are two separate systems.** Confusing them is the #1 source of "env var not injected" bugs.

| System | Where stored | Available where | Format in eas.json |
|---|---|---|---|
| **GitHub Secrets** | `github.com/repo → Settings → Secrets → Actions` | GitHub Actions runner only (`${{ secrets.VAR }}`) | N/A directly |
| **EAS Secrets** | `expo.dev/accounts/waooaw → Project → Secrets` | Expo cloud build servers (resolves `$VAR` in eas.json `env` blocks) | `"$VAR_NAME"` |

**The bridge**: The workflow runs `eas secret:push` before each build to copy GitHub Secrets → EAS Secrets. Defined in the "Sync EAS Secrets from GitHub Secrets" step in `.github/workflows/mobile-playstore-deploy.yml`.

#### Required GitHub Secrets (Demo — must exist in repo settings)

| GitHub Secret Name | Value | Purpose |
|---|---|---|
| `EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO` | `270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com` | Android OAuth client ID (type=1) |
| `EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID_DEMO` | `270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com` | Web OAuth client (backend token exchange) |
| `EXPO_PUBLIC_API_URL_DEMO` | `https://plant.demo.waooaw.com` | Plant Gateway URL for demo |
| `EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME_DEMO` | `com.googleusercontent.apps.270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu` | Custom URI scheme for OAuth redirect |
| `EXPO_TOKEN` | (from expo.dev access tokens) | Authenticates EAS CLI in CI |
| `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` | (JSON key from GCP) | Uploads AAB to Play Store |

#### How EAS secret substitution works

```
eas.json: "EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID": "$EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO"
                                                      ↑
                         EAS resolves this at build time from EAS project secrets
                         (NOT from GitHub Secrets or shell environment)
```

The workflow "Sync EAS Secrets" step runs `eas secret:push --scope project --env-file /tmp/eas-secrets.env --force` to populate EAS secrets from GitHub Secrets before triggering the EAS cloud build.

#### Diagnosing secret injection failures

If a build results in `client_id=$EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID_DEMO` (literal, not substituted):
1. The GitHub Secret exists but was never pushed to EAS
2. The build ran before the "Sync EAS Secrets" step completed
3. The EAS profile `"environment"` key is missing or wrong (`"production"` required for non-development secrets)

---

### Design System

All design tokens are in `src/mobile/src/theme/`. The theme is **dark-first**, matching the web CP Frontend exactly.

#### Colors (`src/mobile/src/theme/colors.ts`)

| Token | Hex / Value | Usage |
|---|---|---|
| `colors.black` | `#0a0a0a` | Primary background |
| `colors.grayDark` / `colors.card` | `#18181b` | Card / secondary background |
| `colors.backgroundTertiary` / `colors.cardHover` | `#27272a` | Hover state, borders |
| `colors.neonCyan` | `#00f2fe` | Primary accent (focus, CTA, neon glow) |
| `colors.neonPurple` | `#667eea` | Secondary accent |
| `colors.neonPink` | `#f093fb` | Tertiary accent / gradient |
| `colors.statusOnline` | `#10b981` | Agent available (green) |
| `colors.statusWorking` | `#f59e0b` | Agent working (yellow) |
| `colors.statusOffline` | `#ef4444` | Agent offline (red) |
| `colors.textPrimary` | `#ffffff` | Primary text |
| `colors.textSecondary` | `#a1a1aa` | Supporting text |
| `colors.textMuted` | `#71717a` | Hints, placeholders |
| `colors.border` | `#27272a` | Default border |
| `colors.borderFocus` | `#00f2fe` | Focus ring (neon cyan) |

Use `ColorUtils.getStatusColor(status)` and `ColorUtils.getSemanticColor(type)` for programmatic access.

#### Typography (`src/mobile/src/theme/typography.ts`)

| Font | Usage |
|---|---|
| **Space Grotesk** 700 Bold | Display / screen headings |
| **Outfit** | Section headings |
| **Inter** | Body, labels, inputs |

All three fonts are loaded via `@expo-google-fonts/space-grotesk`, `@expo-google-fonts/outfit`, `@expo-google-fonts/inter` in `App.tsx` using `useFonts()`.

#### Spacing (`src/mobile/src/theme/spacing.ts`)

4pt base grid: `xs=4, sm=8, md=16, lg=24, xl=32, xxl=48`. Use `spacing.md` not raw `16`.

#### Theme Provider

`src/mobile/src/theme/ThemeProvider.tsx` wraps the app. Access via `useTheme()` hook (`src/mobile/src/hooks/useTheme.ts`).

---

### Screens & Navigation

#### Navigation Tree

```
RootNavigator (NativeStack)
├── Auth (NativeStack) — shown when isAuthenticated === false
│   ├── SignIn
│   ├── SignUp
│   └── OTPVerification  { registrationId, otpId, channel?, destinationMasked }
└── Main (BottomTabs) — shown when isAuthenticated === true
    ├── HomeTab (NativeStack)
    │   ├── Home
    │   ├── AgentDetail  { agentId }
    │   └── TrialDashboard  { trialId }
    ├── DiscoverTab (NativeStack)
    │   ├── Discover
    │   ├── AgentDetail  { agentId }
    │   ├── HireWizard  { agentId, step? }
    │   ├── SearchResults  { query }
    │   └── FilterAgents  { industry?, minRating?, maxPrice? }
    ├── MyAgentsTab (NativeStack)
    │   ├── MyAgents
    │   ├── AgentDetail  { agentId }
    │   ├── TrialDashboard  { trialId }
    │   ├── ActiveTrialsList
    │   └── HiredAgentsList
    └── ProfileTab (NativeStack)
        ├── Profile
        ├── EditProfile
        ├── Settings
        ├── Notifications
        ├── PaymentMethods
        ├── SubscriptionManagement
        ├── HelpCenter
        ├── PrivacyPolicy
        └── TermsOfService
```

#### Screen Files

| Screen | File | Auth? |
|---|---|---|
| Sign In | `src/screens/auth/SignInScreen.tsx` | No |
| Sign Up | `src/screens/auth/SignUpScreen.tsx` | No |
| OTP Verification | `src/screens/auth/OTPVerificationScreen.tsx` | No |
| Home | `src/screens/home/HomeScreen.tsx` | Yes |
| Discover | `src/screens/discover/DiscoverScreen.tsx` | Yes |
| Search Results | `src/screens/discover/SearchResultsScreen.tsx` | Yes |
| Filter Agents | `src/screens/discover/FilterAgentsScreen.tsx` | Yes |
| Agent Detail | `src/screens/discover/AgentDetailScreen.tsx` | Yes |
| Hire Wizard | `src/screens/hire/HireWizardScreen.tsx` | Yes |
| Hire Confirmation | `src/screens/hire/HireConfirmationScreen.tsx` | Yes |
| My Agents | `src/screens/agents/MyAgentsScreen.tsx` | Yes |
| Active Trials | `src/screens/agents/ActiveTrialsListScreen.tsx` | Yes |
| Hired Agents List | `src/screens/agents/HiredAgentsListScreen.tsx` | Yes |
| Trial Dashboard | `src/screens/agents/TrialDashboardScreen.tsx` | Yes |
| Profile | `src/screens/profile/ProfileScreen.tsx` | Yes |
| Settings | `src/screens/profile/SettingsScreen.tsx` | Yes |
| Notifications | `src/screens/profile/NotificationsScreen.tsx` | Yes |
| Payment Methods | `src/screens/profile/PaymentMethodsScreen.tsx` | Yes |
| Subscription Mgmt | `src/screens/profile/SubscriptionManagementScreen.tsx` | Yes |
| Help Center | `src/screens/profile/HelpCenterScreen.tsx` | Yes |
| Privacy Policy | `src/screens/legal/PrivacyPolicyScreen.tsx` | No |
| Terms of Service | `src/screens/legal/TermsOfServiceScreen.tsx` | No |

Navigation guard: `RootNavigator.tsx` reads `isAuthenticated` from `useAuthStore()` and renders `Auth` or `Main` accordingly. **Never** use `navigation.navigate('Main')` directly — change `isAuthenticated` in the store instead.

---

### Components Catalogue

| Component | File | Purpose |
|---|---|---|
| `AgentCard` | `components/AgentCard.tsx` | Marketplace card with avatar, status badge, rating, specialty. Used in Discover + Home feeds. |
| `GoogleSignInButton` | `components/GoogleSignInButton.tsx` | Brand-compliant Google sign-in button. Calls `useGoogleAuth()` internally. |
| `OTPInput` | `components/OTPInput.tsx` | 6-digit OTP entry with auto-advance |
| `LoadingSpinner` | `components/LoadingSpinner.tsx` | Full-screen or inline loading indicator |
| `ErrorBoundary` | `components/ErrorBoundary.tsx` | React error boundary; logs to Sentry in uat/prod |
| `ErrorView` | `components/ErrorView.tsx` | In-screen error display with retry action |
| `EmptyState` | `components/EmptyState.tsx` | No-data placeholder with icon + message |
| `NetworkStatusBanner` | `components/NetworkStatusBanner.tsx` | Offline indicator ribbon; uses `useNetworkStatus()` |
| `AnalyticsConsentModal` | `components/analytics/AnalyticsConsentModal.tsx` | GDPR consent prompt for Firebase Analytics |
| `AppRatingPrompt` | `components/feedback/AppRatingPrompt.tsx` | Play Store rating prompt |
| `VoiceControl` | `components/voice/VoiceControl.tsx` | Voice command trigger UI |
| `VoiceFAB` | `components/voice/VoiceFAB.tsx` | Floating action button for voice input |
| `VoiceHelpModal` | `components/voice/VoiceHelpModal.tsx` | Help overlay listing available voice commands |

---

### Services & API Endpoints

All services use the `apiClient` singleton (`src/mobile/src/lib/apiClient.ts`) — an Axios instance pointing at `EXPO_PUBLIC_API_URL` (Plant Gateway). The gateway requires `Authorization: Bearer <JWT>` on all protected endpoints.

#### Auth endpoints (`src/mobile/src/services/auth.service.ts`)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/google/verify` | Exchange Google `id_token` for WAOOAW JWT. Body: `{ id_token, source: "mobile" }`. Response: `{ access_token, refresh_token, token_type, expires_in }` |
| `POST` | `/auth/refresh` | Refresh access token. Body: `{ refresh_token }` |
| `POST` | `/auth/logout` | Invalidate tokens |

#### Agent endpoints (`src/mobile/src/services/agents/agent.service.ts`)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v1/agents` | List agents (query params: `industry`, `min_rating`, `page`, `limit`) |
| `GET` | `/v1/agents/:agentId` | Agent detail |

#### Hired Agents (`src/mobile/src/services/hiredAgents/hiredAgents.service.ts`)

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v1/hired_agents` | Active hired agents for current customer |
| `GET` | `/v1/hired_agents/:id` | Hired agent detail + trial status |

#### Payments (`src/mobile/src/services/payment/razorpay.service.ts`)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/v1/payments/create-order` | Create Razorpay order |
| `POST` | `/v1/payments/verify` | Verify payment signature |
| `POST` | `/v1/payments/refund` | Initiate refund |
| `GET` | `/v1/payments/:paymentId/status` | Payment status |

#### Registration (`src/mobile/src/services/registration.service.ts`)

Handles mobile customer registration and OTP-based auth. All three steps call Plant Gateway directly (no CP Backend involvement). The `registration_id` returned by `/auth/register` is the customer UUID and must be passed to `/auth/otp/start`.

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/auth/register` | Create customer account. Body: `CustomerCreate` (camelCase fields). Response: `{ registration_id, email, phone, created }` |
| `POST` | `/auth/otp/start` | Start OTP challenge. Body: `{ registration_id, channel? }`. Response: `{ otp_id, channel, destination_masked, expires_in_seconds, otp_code? }` (`otp_code` echoed only in dev/demo env) |
| `POST` | `/auth/otp/verify` | Verify OTP, receive JWT tokens. Body: `{ otp_id, code }`. Response: `{ access_token, refresh_token, token_type, expires_in }` |

All three paths are in `PUBLIC_ENDPOINTS` in `src/Plant/Gateway/middleware/auth.py` — no JWT required.

#### Token Management (`src/mobile/src/services/tokenManager.service.ts`)

Manages access/refresh token lifecycle: reads from `secureStorage`, handles auto-refresh via Axios interceptor (retry queue pattern for concurrent requests during refresh).

#### Push Notifications (`src/mobile/src/services/notifications/pushNotifications.service.ts`)

Registers device FCM token with Plant Backend after sign-in. On sign-in success, calls `POST /api/v1/customers/fcm-token` (authenticated) to store the token against the customer record. Required for agent status + deliverable ready push notifications (MOBILE-FUNC-1 #866, #867).

---

### State Management

#### Auth Store (`src/mobile/src/store/authStore.ts`)

Zustand store — single source of truth for authentication state.

| State field | Type | Description |
|---|---|---|
| `isAuthenticated` | `boolean` | Gate for `RootNavigator`; only true after `login()` called |
| `user` | `AuthUser \| null` | `{ customer_id, email, full_name?, phone?, business_name? }` |
| `isLoading` | `boolean` | True during `initialize()` — show splash until resolved |

| Action | Effect |
|---|---|
| `login(user)` | Sets `isAuthenticated = true`, stores user — triggers nav switch to `Main` |
| `logout()` | Clears tokens (SecureStore) + user data + resets state |
| `updateUser(partial)` | Merge updates into `user` |
| `initialize()` | Called on app start — reads SecureStore, restores session if valid, sets `isLoading = false` |

**Critical**: After Google OAuth + backend JWT exchange, call **both** `authStore.login(user)` **and** `userDataService.saveUserData(user)`. Missing either keeps the user stuck on the auth screen.

#### SecureStore Keys (`src/mobile/src/lib/secureStorage.ts`)

| Key constant | SecureStore key | Contents |
|---|---|---|
| `ACCESS_TOKEN` | `cp_access_token` | JWT access token |
| `REFRESH_TOKEN` | `cp_refresh_token` | JWT refresh token |
| `TOKEN_EXPIRES_AT` | `token_expires_at` | Unix timestamp (seconds) |
| `USER_ID` | `user_id` | WAOOAW customer ID |
| `USER_EMAIL` | `user_email` | User email |
| `USER_NAME` | `user_name` | Display name |
| `USER_PICTURE` | `user_picture` | Avatar URL |
| `BIOMETRIC_ENABLED` | `biometric_enabled` | Biometric auth flag |

---

### Key Dependencies

| Package | Version | Notes |
|---|---|---|
| `expo` | `~54.0.33` | Managed workflow |
| `react-native` | `0.81.5` | New Architecture disabled (`newArchEnabled: false`) |
| `react` | `19.1.0` | |
| `typescript` | `~5.9.2` | Strict mode |
| `@react-navigation/native` | `^7.1.28` | |
| `@react-navigation/native-stack` | `^7.13.0` | |
| `@react-navigation/bottom-tabs` | `^7.14.0` | |
| `zustand` | `^5.0.11` | Auth + UI state |
| `@tanstack/react-query` | `^5.90.21` | Server state / data fetching |
| `axios` | `^1.13.5` | HTTP client |
| `@react-native-google-signin/google-signin` | `^16.1.1` | Google OAuth — native Android SDK, replaces `expo-auth-session` |
| `expo-secure-store` | `^15.0.8` | Token storage (iOS Keychain / Android KeyStore) |
| `@shopify/flash-list` | `^1.8.3` | **Must be 1.x** — v2 requires new architecture |
| `@react-native-async-storage/async-storage` | `^2.1.0` | Cache / AsyncStorage backfill |
| `@react-native-community/netinfo` | `^11.4.1` | Network status |
| `expo-speech` | `~14.0.8` | Text-to-speech (voice features) |
| `expo-image` | `~3.0.11` | Optimised image component |
| `@sentry/react-native` | (in package) | Error tracking (disabled in demo, enabled uat/prod) |
| `detox` | `^20.47.0` | E2E testing |
| `jest` | `~29.7.0` | Unit testing |
| `@testing-library/react-native` | `^13.3.3` | Component testing |

---

### Testing Reference

#### npm Scripts

| Script | Command | Description |
|---|---|---|
| `npm test` | `jest` | Run active unit tests |
| `npm run test:full` | `jest --config jest.full.config.js` | Run all tests including skipped |
| `npm run test:watch` | `jest --watch` | Watch mode |
| `npm run test:coverage` | `jest --coverage` | Coverage report (min 80% on services + apiClient) |
| `npm run test:e2e:android` | `detox test --configuration android.emu.debug` | E2E on Android emulator |
| `npm run lint` | `ESLINT_USE_FLAT_CONFIG=false eslint . --ext .ts,.tsx` | Lint |
| `npm run typecheck` | `tsc --noEmit` | Type check |
| `npm run validate` | `typecheck + test` | Full CI-equivalent check |

#### Active Test Files (`__tests__/`)

The following tests run in standard `npm test`:

`App.test.tsx`, `GoogleSignInButton.test.tsx`, `MyAgentsScreen.test.tsx`, `OTPVerificationScreen.test.tsx`, `RootNavigator.test.tsx`, `SignInScreen.test.tsx`, `SignUpScreen.test.tsx`, `ThemeProvider.test.tsx`, `agentCard.test.tsx`, `agentDetailScreen.test.tsx`, `agentService.test.ts`, `apiClient.test.ts`, `auth.service.test.ts`, `authStore.test.ts`, `errorHandler.test.ts`, `googleAuth.service.test.ts`, `hireConfirmationScreen.test.tsx`, `hiredAgentsService.test.ts`, `oauth.config.test.ts`, `offlineCache.test.ts`, `performanceMonitoring.test.ts`, `registration.service.test.ts`, `tokenManager.service.test.ts`, `voiceCommandParser.test.ts`

#### Skipped Tests (in `jest.config.js` `testPathIgnorePatterns`)

| File | Reason skipped |
|---|---|
| `hireWizardScreen.test.tsx` | Complex multi-step UI — mock setup incomplete |
| `hiredAgentsHooks.test.tsx` | Hooks use React Query; needs full provider wrapper |
| `useRazorpay.test.ts` | Razorpay native module mock not stable |
| `discoverScreen.test.tsx` | FlashList mock + filter interactions — WIP |
| `useGoogleAuth.test.ts` | `@react-native-google-signin` jest mock in `__mocks__/` — verify mock covers `hasPlayServices` + `signIn` response shape |
| `coreScreens.test.tsx` | Covers multiple screens; needs navigation mock upgrade |
| `agentHooks.test.tsx` | React Query provider setup incomplete |
| `OTPInput.test.tsx` | Custom input component mock instability |
| `secureStorage.test.ts` | Native module (SecureStore) requires device |
| `accessibility.test.ts` | Platform-specific assertions fail in Node env |
| `navigation.test.ts` | Full navigation tree mocking — WIP |
| `theme.test.ts` | Font loading async behavior — WIP |
| `integration/auth.test.ts` | Requires live backend; skip in unit CI |
| `integration/api.test.ts` | Requires live backend |
| `integration/fontLoading.test.ts` | Expo font loading async |
| `api.config.test.ts` | Environment-specific URL assertions |
| `razorpay.service.test.ts` | Native module dependency |
| `e2e/app-launch.test.js` | Detox only — run via `test:e2e:android` |

#### Coverage Scope

Coverage is collected from `src/services/**/*.{ts,tsx}` and `src/lib/apiClient.ts`. Threshold: **80% statements/branches/functions/lines**. Voice, analytics, monitoring, payment, and hiredAgents service sub-trees are excluded from coverage enforcement.

---

### Hooks Reference

| Hook | File | Returns |
|---|---|---|
| `useGoogleAuth()` | `hooks/useGoogleAuth.ts` | `{ promptAsync, loading, error, userInfo, idToken, isConfigured }` — call `promptAsync()` to trigger sign-in; internally does `signOut()` then `signIn()` to always show account picker |
| `useAuthState()` | aliased from authStore | `{ isAuthenticated, user, isLoading }` |
| `useAgents(filters)` | `hooks/useAgents.ts` | React Query result for agent list |
| `useAgentDetail(agentId)` | `hooks/useAgentDetail.ts` | React Query result for single agent |
| `useHiredAgents()` | `hooks/useHiredAgents.ts` | Active hired agents + trials |
| `useNetworkStatus()` | `hooks/useNetworkStatus.ts` | `{ isConnected, isInternetReachable }` |
| `useTheme()` | `hooks/useTheme.ts` | Full theme object (colors, typography, spacing) |
| `useVoiceCommands()` | `hooks/useVoiceCommands.ts` | Voice command recognition + parsed intent |
| `useSpeechToText()` | `hooks/useSpeechToText.ts` | STT recording state + transcript |
| `useTextToSpeech()` | `hooks/useTextToSpeech.ts` | TTS playback |
| `useRazorpay()` | `hooks/useRazorpay.ts` | Payment initiation + result |
| `usePerformanceMonitoring()` | `hooks/usePerformanceMonitoring.ts` | Screen trace start/stop |

---

### Lib Utilities

| File | Purpose |
|---|---|
| `lib/apiClient.ts` | Axios instance with auth interceptor + token refresh queue |
| `lib/secureStorage.ts` | Typed wrapper for `expo-secure-store` (iOS Keychain / Android KeyStore) |
| `lib/errorHandler.ts` | Normalises API, network, and auth errors to `AppError` type |
| `lib/networkStatus.ts` | `netinfo` wrapper with observable status |
| `lib/offlineCache.ts` | AsyncStorage-backed cache for offline-first reads |
| `lib/performanceMonitoring.ts` | Firebase Performance trace helpers |
| `lib/accessibility.ts` | WCAG helpers, `accessibilityLabel` generators |

---

### Voice Features

Voice is a progressive feature — it degrades gracefully if permissions are denied.

| Service | File | Notes |
|---|---|---|
| Speech-to-text | `services/voice/speechToText.service.ts` | Uses `expo-speech` (STT) |
| Text-to-speech | `services/voice/textToSpeech.service.ts` | Uses `expo-speech` (TTS) |
| Command parser | `services/voice/voiceCommandParser.service.ts` | Maps transcript → app intents |
| Components | `components/voice/` | `VoiceFAB`, `VoiceControl`, `VoiceHelpModal` |

Disable completely: remove `VoiceFAB` from `MainNavigator`. No other code changes needed.

---

### Analytics & Monitoring

| Service | Enabled in demo | File |
|---|---|---|
| Firebase Analytics | ✅ (with consent) | `services/analytics/firebase.analytics.ts` |
| Firebase Crashlytics | ✅ | `services/monitoring/crashlytics.service.ts` |
| Firebase Performance | ✅ | `services/monitoring/performance.service.ts` |
| Sentry | ❌ (enabled uat/prod) | `src/config/sentry.config.ts` |

Consent gate: `AnalyticsConsentModal` shown on first launch. Decision persisted in SecureStore.

---

### Local Development

```bash
# In Codespaces — uses tunnel to expose 8081
cd src/mobile && npm run start:codespace

# Requires in .env.local (copy from .env.local.example):
EXPO_PUBLIC_ENVIRONMENT=development
EXPO_PUBLIC_API_URL=https://${CODESPACE_NAME}-8000.app.github.dev
EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID=270293855600-2shlgotsrqhv8doda15kr8noh74jjpcu.apps.googleusercontent.com
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=270293855600-uoag582a6r5eqq4ho43l3mrvob6gpdmq.apps.googleusercontent.com
EXPO_PUBLIC_OAUTH_REDIRECT_SCHEME=com.waooaw.dev
```

Scan the QR code in Expo Go (Android) or use the dev APK build for Google sign-in (Expo Go does not support custom URI scheme redirects).

---

## 24. Skills & Capabilities for World-Class Platform

> This section defines the depth of expertise required to build and operate WAOOAW at world-class quality across every dimension. It serves as a hiring bar, agent-tuning reference, and skill-gap radar. Updated with the document cadence (bi-weekly or on demand).

### 24.1 Backend Engineering

| Domain | Required Capability |
|--------|---------------------|
| **Python** | 3.11+ async-first code; `asyncio`, `anyio`, context-vars; deep knowledge of CPython memory model |
| **FastAPI** | Dependency injection chains, lifespan events, background tasks, custom middleware ordering, OpenAPI customisation |
| **SQLAlchemy (async)** | Async session management, hybrid properties, complex join strategies, bulk-upsert patterns, session-scoped vs request-scoped |
| **Alembic** | Multi-branch migrations, data migrations, zero-downtime column changes, autogenerate pitfalls |
| **Pydantic v2** | Custom validators, discriminated unions, model serialisation performance, settings management |
| **Security** | RSA-4096 sign/verify, SHA-256 hash chains, TOTP 2FA, CAPTCHA integration, JWT HS256/RS256 lifecycle, credential encryption at rest |
| **Constitutional patterns** | `BaseEntity` 7-section design, `validate_self()` hooks, append-only audit, `ConstitutionalAlignmentError` propagation |

### 24.2 Frontend Engineering

| Domain | Required Capability |
|--------|---------------------|
| **React 18** | Concurrent rendering, `Suspense`, `useTransition`, server components awareness, render optimisation |
| **TypeScript** | Strict mode, advanced generics, discriminated unions, mapped/conditional types, module augmentation |
| **Vite** | Plugin authoring, SSR config, env variable handling, code-split strategies |
| **State management** | Zustand (mobile), Context API, optimistic updates, cache invalidation patterns |
| **UI/UX — Marketplace DNA** | Talent-marketplace patterns (card grids, filter/sort, real-time activity feeds, status badges); dark theme design system with CSS variables |
| **Accessibility** | WCAG 2.1 AA compliance, keyboard navigation, ARIA roles |
| **Testing** | Vitest component tests, Playwright E2E, MSW for API mocking |

### 24.3 Mobile Engineering (React Native / Expo)

| Domain | Required Capability |
|--------|---------------------|
| **React Native** | New Architecture awareness (Fabric, JSI), bridgeless mode trade-offs, platform-specific code splitting |
| **Expo / EAS** | EAS Build profiles, OTA update channels, `app.json` config plugin authoring, version-code auto-increment |
| **Auth on mobile** | `@react-native-google-signin` v16 native SDK, `webClientId` = Web OAuth client for `aud` claim, SHA-1 certificate fingerprint registration in GCP, `expo-secure-store` vs AsyncStorage session persistence |
| **Navigation** | `react-navigation` v7, deep linking, protected route guards, navigator nesting |
| **CI/CD** | EAS Submit, Google Play internal track, Play Store service account IAM, GitHub Actions for automated submissions |

### 24.4 Cloud & Infrastructure (GCP)

| Domain | Required Capability |
|--------|---------------------|
| **GCP Cloud Run** | Concurrency tuning, min-instance cold-start mitigation, VPC connector, IAM ingress controls |
| **Terraform** | Module composition, remote state (GCS backend), `terraform plan` in CI, destroy-protection, workspace strategy (demo/UAT/prod) |
| **Secret Manager** | Secret rotation, version pinning, IAM binding to service accounts, injecting into Cloud Run env |
| **Cloud SQL (Postgres)** | Private IP, connection pooling via Cloud SQL Proxy / pgBouncer, point-in-time recovery |
| **Artifact Registry** | Docker image tagging strategy (SHA + semver), vulnerability scanning |
| **IAM & Security** | Principle of least privilege, Workload Identity Federation for GitHub Actions (keyless auth) |
| **Networking** | Load balancer health checks, HTTPS redirect, custom domains, Cloud Armor WAF basics |

### 24.5 Database & Persistence

| Domain | Required Capability |
|--------|---------------------|
| **PostgreSQL 15** | pgvector extension for embeddings, JSONB indexing (GIN), partial indexes, `EXPLAIN ANALYZE` query tuning |
| **Redis 7** | Pub/Sub, sorted sets for leaderboards/rate-limits, TTL strategy, cluster vs sentinel |
| **Schema design** | Constitutional 7-section schema pattern, append-only audit tables, hash-chain integrity columns |
| **asyncpg** | Connection pool sizing, prepared statements, `COPY` for bulk loads |

### 24.6 Testing & Quality

| Domain | Required Capability |
|--------|---------------------|
| **pytest** | Async fixtures, Factory Boy, parametrize, markers (unit/integration/e2e), coverage ≥ 80% overall / 90%+ critical paths |
| **Mocking & isolation** | `pytest-mock`, `respx` for HTTP, `fakeredis`, dependency-override patterns in FastAPI |
| **E2E** | Playwright multi-browser, page object model, trace viewer, screenshots on failure |
| **Contract testing** | OpenAPI schema validation, Schemathesis property-based API tests |
| **Performance** | `locust` load tests, `pytest-benchmark`, p95 latency goals, DB query budgets |
| **Security testing** | OWASP ZAP baseline, `bandit` static analysis, `safety` dependency CVE checks |

### 24.7 DevOps & Automation

| Domain | Required Capability |
|--------|---------------------|
| **Docker / Compose** | Multi-stage builds, layer caching, `docker compose` service dependency ordering, health-check patterns |
| **GitHub Actions** | Reusable workflows, matrix builds, OIDC keyless GCP auth, concurrency groups, manual-trigger `workflow_dispatch` |
| **Conventional Commits** | Enforce via `commitlint`, auto-generate CHANGELOG, semantic-release versioning |
| **Code quality gates** | Black, ESLint, Prettier, yamllint, `actionlint` for workflow validation, pre-commit hooks |
| **Observability** | Structured JSON logging, correlation IDs, custom metrics middleware, GCP Cloud Monitoring dashboards |

### 24.8 AI / ML Integration

| Domain | Required Capability |
|--------|---------------------|
| **LLM integration** | GitHub Models API, prompt engineering for agent personas, streaming responses |
| **Embeddings** | pgvector similarity search, embedding cache design, quality evaluation |
| **Constitutional AI** | Policy-layer enforcement (OPA), drift detection, governance agent orchestration |
| **Agent architecture** | Playbook design (marketing/trading molds), multi-agent coordination, Governor single-point-of-authority pattern |

### 24.9 Domain & Product Knowledge

| Domain | Required Capability |
|--------|---------------------|
| **Marketplace mechanics** | Trial-to-paid funnels, subscription billing (Razorpay), proration, dunning |
| **Trading / FinTech** | Delta Exchange API, order lifecycle, P&L metering, credential encryption for exchange keys |
| **Regulatory awareness** | Data residency (India), GDPR basics, SOC 2 readiness, audit-log immutability requirements |
| **UX writing** | Talent-marketplace copy patterns; agent personality as a product differentiator |

### 24.10 Soft Skills & Ways of Working

| Skill | Standard |
|-------|----------|
| **Constitutional thinking** | Every change must respect L0/L1 principles — no shortcuts on audit trail or governance |
| **Minimal interaction discipline** | Agent responses ≤ 5 lines unless detail explicitly requested; respect the user's cognitive bandwidth |
| **Bi-weekly doc hygiene** | Refresh Section 12 (Latest Changes) every sprint; update Section 24 after significant technology additions |
| **Conventional Commits** | Every commit is typed, scoped, and describes impact — not implementation |
| **Test-first mindset** | New features ship with unit + integration tests hitting coverage thresholds before PR merge |

---

## 25. Session Commentary Protocol — Context Recovery

> **MANDATORY for all agents**: After completing each logical task, append a timestamped entry to `session_commentary.md` at the repo root. This file is the primary recovery mechanism when connections drop or sessions reset mid-task.

### 25.1 Purpose

Long-running tasks (multi-PR refactors, multi-step debugging) frequently span multiple agent sessions. Without an explicit log, a reconnecting agent must re-read all files from scratch, wasting tokens and often missing critical in-flight state (e.g. "PR #852 is CI-green, waiting for merge", "test is failing because of X not Y").

`session_commentary.md` solves this: it is an append-only journal at the repo root that any agent can read in seconds to reconstruct working context.

### 25.2 File location

```
/session_commentary.md      ← repo root, always
```

### 25.3 On session start — read first

Before doing anything else in a new session, run:

```bash
tail -120 session_commentary.md
```

Read the last 3–5 entries. They tell you:
- What branch/PR is active
- What was last completed
- What the next step is
- Any blocking conditions

### 25.4 When to append

Append **immediately after** completing each of these logical task boundaries:

| Boundary | Examples |
|----------|----------|
| Analysis complete | Root cause identified, architecture decision made |
| Code change complete | Bug fixed, feature implemented, refactor done |
| Tests run | All pass, or specific failures noted |
| Commit + push | Branch pushed to remote |
| PR created or updated | PR number and URL known |
| CI result known | All checks green / specific checks failing |
| Blocked / waiting | Waiting for merge, waiting for user input |
| Session end | Agent about to hand off or go idle |

**Do not** batch entries. Write each boundary as it happens. Append even for partial progress — a partial log is infinitely better than silence.

### 25.5 Entry format

Append this block verbatim, filling in the fields:

```markdown
## [YYYY-MM-DD HH:MM UTC] <Short task title (8 words max)>

**Branch**: `<branch-name>`
**PR**: #<number> (<url>) | None yet
**Status**: Completed | In Progress | Blocked

### What was done
<2–5 sentences. What problem, what decision, what action.>

### Outcome
- <concrete result — e.g. "5/5 tests pass", "PR #N created", "CI green">
- <second bullet if needed>

### Key files changed
| File | Change |
|------|--------|
| `path/to/file` | what changed |

### Next step
<One sentence: what should be done next if resuming from here.>

### Recovery hint
<Non-obvious state that would be lost otherwise: pending merges, blocked-by, env quirks, secret names, test isolation issues, etc.>
```

### 25.6 Format rules

- Timestamp in **UTC**, ISO-8601 format: `YYYY-MM-DD HH:MM UTC`
- Title ≤ 8 words — enough to skim the file like a git log
- **Never edit or delete past entries** — append only
- Keep each entry under 30 lines; link to PRs/commits for detail
- If the session produces only one entry, that is fine — write it at session end

### 25.7 Bootstrap (first time in a repo session)

If `session_commentary.md` does not exist yet, create it:

```bash
cat > session_commentary.md << 'EOF'
# Session Commentary — WAOOAW

> Append-only log for context recovery. Read last 3–5 entries on session start.

---
EOF
```

Then immediately append the first entry for the current task.

### 25.8 Recovery procedure for a reconnecting agent

1. `tail -120 session_commentary.md` — scan last entries
2. Check **Branch** and **PR** fields — verify branch is still checked out (`git status`)
3. Check **Next step** field — start there
4. Check **Recovery hint** — resolve any blockers before coding
5. Confirm CI state if a PR exists: `gh pr checks <N> --repo dlai-sd/WAOOAW`
6. Resume and append a new entry: "Resumed session — continuing from <previous title>"

### 25.9 Example entry

```markdown
## [2026-03-04 14:20 UTC] Applied Razorpay amount + prefill fix

**Branch**: `fix/portal-nav-and-payments-mode-cp`
**PR**: #852 — https://github.com/dlai-sd/WAOOAW/pull/852
**Status**: Completed

### What was done
Added missing `amount` and `prefill` fields to the Razorpay constructor options
in BookingModal.tsx. Without `amount`, Razorpay checkout.js cannot render the
payment method selection screen (UPI, card, netbanking).

### Outcome
- All 5 BookingModal tests pass (3/5 before fix)
- CI: 12/12 checks green on PR #852

### Key files changed
| File | Change |
|------|--------|
| `src/CP/FrontEnd/src/components/BookingModal.tsx` | `amount` + `prefill` added |
| `src/CP/FrontEnd/src/test/BookingModal.test.tsx` | Button name assertions + regression guard |

### Next step
Merge PR #852, then open docs PR for session commentary protocol.

### Recovery hint
PR #852 was all CI-green. User confirmed intent to merge.
```

---

*End of Context & Indexing Document (updated)*

---

## 26. Agent Construct Design — Quick Reference

> **Full document**: [`docs/PP/AGENT-CONSTRUCT-DESIGN.md`](PP/AGENT-CONSTRUCT-DESIGN.md) — v2, 2179 lines, 2026-03-07.

This document is the **single source of truth** for all construct-pipeline design decisions. Read it in full before modifying `agent_mold/`, any Scheduler/Pump/Processor/Connector/Publisher code, or the HookBus.

| § | Topic | Quick pointer |
|---|---|---|
| §1 | Platform hierarchy — Customer→HiredAgent→Skill→GoalRun→Deliverable | `src/Plant/BackEnd/models/` |
| §2 | Construct hierarchy + ownership diagram | `agent_mold/spec.py` (ConstructBindings) |
| §3 | Full mould interface: `AgentSpec`, `ConstructBindings`, `LifecycleHooks` ABC, `ConstraintPolicy` | `agent_mold/spec.py`, `agent_mold/hooks.py` |
| §4 | Platform Core: Scheduler, Pump/GoalConfigPump/TradingPump, Connector, Publisher | `agent_mold/skills/`, Scheduler in `core/scheduler.py` |
| §5 | Agent-Specific Processor: `BaseProcessor`, `ContentCreatorProcessor`, `TradingProcessor` | `agent_mold/skills/content_creator.py`, `trading_executor.py` |
| §6 | HookBus stage wiring — PRE_PUMP through POST_PUBLISH | `agent_mold/enforcement.py` |
| §7 | Agent profile validation (Share Trader + Content Creator sample `AgentSpec` definitions) | `agent_mold/reference_agents.py` |
| §8 | End-to-end execution flow diagram | — |
| §9 | NFR requirements per construct | See §17 (Gotchas) |
| §10 | Environment flags: `CAMPAIGN_PERSISTENCE_MODE`, `CIRCUIT_BREAKER_ENABLED`, `SCHEDULER_ENABLED`, `APPROVAL_GATE_ENABLED` | See §14 |
| §11 | Gap register (G1–G13) | `docs/PP/iterations/MOULD-GAP-1-construct-hardening.md` |
| §13 | CP UX — construct surfaces in Customer Portal; 5 missing CP routes; screen-by-screen changes | See §4.3 |
| §14 | PP Service-Centre vision; 7-role RBAC; 10 missing PP routes; 7 new PP screens | See §4.4 |
| §15 | Key DB tables quick reference (12 tables) | See §10 |
| §16 | Suggested improvements requiring user sign-off (WebSocket, swipe-to-approve, OAuth expiry UI) | — |

**When to read this doc:**
- Before implementing any new GoalRun, Deliverable, or approval flow
- Before adding a new agent type to `reference_agents.py`
- Before modifying `ConstraintPolicy` fields or `LifecycleHooks` signatures
- Before adding PP diagnostic routes or PP FrontEnd construct-health screens
- Before changing how TradingProcessor produces output (always `draft_only=True`)

**Parent context in this file:** §4.6 (construct architecture quick-reference), §4.3 (CP), §4.4 (PP), §13 (code file index), §14 (env vars), §17 (gotchas).
