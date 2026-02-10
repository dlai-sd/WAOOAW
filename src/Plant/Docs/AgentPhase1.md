# Agent Phase 1 — CP “My Agents” (Configure + Goal Setting)

**Date**: 2026-02-09

## Purpose
Phase 1 delivers a real customer-operable **My Agents** experience in CP with:
- A **top dropdown** to select among multiple hired agents (agent instances/subscriptions).
- Two management dimensions (Phase 1 only):
  1) **Configure** (mandatory) — customer customizes the agent’s appearance + behavior + required setup.
  2) **Goal Setting** — customer sets 1..n goals, each with a frequency and task settings; deliverables are produced as drafts and require customer approval before any external side-effect.

This must work for:
- **Digital Marketing Agent** (multichannel posting).
- **Share Trading Agent** (Delta Exchange India futures) — **deterministic** in Phase 1.

## Phase 1 constraints (non-negotiable)
- **Self-serve credentials in CP** (customer connects platforms/exchange keys in CP).
- **Deterministic trading** (no AI-driven trading recommendations in Phase 1).
- **Single door**: CP FrontEnd calls CP BackEnd `/api/*` only; CP BackEnd proxies to Plant Gateway where needed.
- **Non-bypassable enforcement**: publish/post/send/place_order/close_position always goes through Plant enforcement (hooks, approval gates, trial + budget rules).
- **No browser → Plant secrets**: credentials are encrypted at rest in CP BackEnd; Plant receives only `credential_ref` / `exchange_account_id`.
- **Testing is Docker-based only** (no virtualenv usage). Run tests after each epic (not each story), and enforce coverage at epic boundaries.

## How to run tests (Docker-only)

**Rule**: do not run local venv/poetry/pip installs for testing; use Docker Compose services.

Common commands:
- Plant BackEnd: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- Plant Gateway: `docker compose -f docker-compose.local.yml exec -T plant-gateway pytest -q --cov --cov-report=term-missing`
- CP BackEnd: `docker compose -f docker-compose.local.yml exec -T cp-backend pytest -q --cov --cov-report=term-missing`
- PP BackEnd: `docker compose -f docker-compose.local.yml exec -T pp-backend pytest -q --cov --cov-report=term-missing`
- CP FrontEnd: `docker compose -f docker-compose.local.yml run --rm cp-frontend-test npm run test -- --run`
- PP FrontEnd: `docker compose -f docker-compose.local.yml run --rm pp-frontend-test npm run test -- --run`

**Note (Plant BackEnd tests)**: the suite resets schema and will refuse to run against `waooaw_db`; ensure `waooaw_test_db` exists in Postgres before running.

---

## Product-owner gap scan (Phase 1)

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| CP has a “My Agents” list but not a **top agent selector** nor instance-level management UX | Customer can’t quickly switch between hired agents or manage an agent instance holistically | Convert My Agents to a **selector + tabs** model and keep the list as secondary (or replace list with selector + summary card) |
| Configuration is currently “Hire wizard-only” and not a durable, schema-driven contract | New agent types will force CP rewrites; “configured=true” won’t match actual operational readiness | Introduce an **AgentTypeDefinition** contract: config schema + goal templates + validation rules authored in PP and stored in Plant |
| CP already stores credentials (platform/exchange), but agent instance config doesn’t standardize how refs attach | Drift between credential stores and hired agent config; support burden | Standardize config fields to store **only refs** in Plant (e.g., `credential_ref`, `exchange_credential_ref`) and validate them |
| Goal setting is not implemented as a first-class entity | Customers can’t define deliverables; Plant can’t schedule/run consistent work | Add goal entities: `GoalTemplate` (by agent type) and `GoalInstance` (per hired agent instance), plus draft/review lifecycle |
| Approval UX is not anchored to goals/deliverables | Customer approval requirement becomes ad-hoc and bypassable | Every deliverable item must have a stable id and state machine: `draft → pending_review → approved/rejected → scheduled/executed` |
| Deterministic trading needs “value” without recommendations | Without value, trading agent feels like a UI wrapper over “place order” | Make Phase 1 deliverables explicit: **trade intent drafts**, **guardrail-validated action plans**, **approval-gated execution** |

---

## Shared definitions (Phase 1)

### Core entities
- **Agent Type**: a versioned definition (what fields/goals exist). Authored in PP.
- **Hired Agent Instance**: customer-specific agent instance tied to a subscription.
- **Config**: customer-entered configuration for that hired instance.
- **Goal Template**: a goal definition available for an agent type (name, settings schema, skill binding).
- **Goal Instance**: a customer-selected goal with `frequency` and `settings`.
- **Deliverable**: a generated draft/output for a goal run, requiring customer approval when it can cause external actions.

### Non-bypassable enforcement rules (Phase 1)
| Rule | Where enforced | Expected behavior |
|---|---|---|
| Secrets never sent browser → Plant | CP BackEnd + Plant validation | Plant receives only refs/IDs; denies if raw secrets are present |
| Approval required for external side effects | Plant hook bus | Any `publish/post/send/place_order/close_position` without `approval_id` is denied |
| Trial/budget cannot be bypassed | Plant enforcement + metering | Over-limit calls are denied before cost; denials are auditable |

---

## Agent-specific configuration (Phase 1)

### Digital Marketing Agent — customer configuration fields
These fields must reflect on CP when customer logs in and selects the Marketing agent.

| Field | Type | Required | Where stored | Notes |
|---|---:|:---:|---|---|
| Agent nickname | string | ✅ | Plant (hired agent config) | Display name for dropdown |
| Avatar/theme | enum | ✅ | Plant | Cosmetic |
| Primary language | enum | ✅ | Plant | Used for drafts |
| Timezone | IANA string | ✅ | Plant | Used for scheduling |
| Brand name | string | ✅ | Plant | Used in deliverables |
| Offerings/services | list<string> | ✅ | Plant | Used in deliverables |
| Location | string | ✅ | Plant | Used in deliverables |
| Platforms enabled | list<platform> | ✅ | Plant | Platform allowlist per customer |
| Per-platform credential ref | object | ✅ | Plant (refs only), CP stores secret | `credential_ref` minted by CP via `/api/cp/platform-credentials` |
| Posting identity | string | ⛔ | Plant | e.g., page/channel handle |
| Constraints | object | ⛔ | Plant | max length, hashtag rules |
| Review policy | fixed | ✅ | Plant | Always require approval per post |

**Existing CP credential API to reuse**:
- CP BackEnd route: `PUT /api/cp/platform-credentials` (stores encrypted secrets; returns `credential_ref`). Implementation: [src/CP/BackEnd/api/platform_credentials.py](src/CP/BackEnd/api/platform_credentials.py)

### Share Trading Agent — customer configuration fields
These fields must reflect on CP when customer logs in and selects the Trading agent.

| Field | Type | Required | Where stored | Notes |
|---|---:|:---:|---|---|
| Agent nickname | string | ✅ | Plant | Display name for dropdown |
| Avatar/theme | enum | ✅ | Plant | Cosmetic |
| Timezone | IANA string | ✅ | Plant | Used for windows/reminders |
| Exchange provider | enum | ✅ | Plant | Phase 1 fixed: `delta_exchange_india` |
| Exchange credential ref | string (ref) | ✅ | Plant (ref), CP stores secret | Minted by CP via `/api/cp/exchange-setup` |
| Allowed coins | list<string> | ✅ | Plant | Allowlist enforced |
| Default coin | string | ✅ | Plant | Prefill goal settings |
| Risk limits | object | ✅ | Plant | `max_units_per_order`, optional `max_notional_inr` |
| Execution policy | fixed | ✅ | Plant | Approval required per trade action |

**Existing CP credential API to reuse**:
- CP BackEnd route: `PUT /api/cp/exchange-setup` (stores encrypted secrets + risk limits; returns `credential_ref`). Implementation: [src/CP/BackEnd/api/exchange_setup.py](src/CP/BackEnd/api/exchange_setup.py)

---

## Goal Setting (Phase 1)

### Goal design rules
- Each goal has:
  - `goal_template_id`
  - `frequency` (Phase 1: `daily | weekly | monthly | on_demand`)
  - `settings` (goal-specific JSON)
- Every deliverable produced by a goal run must be:
  - Stored with a stable `deliverable_id`
  - Reviewable in CP
  - Approval-gated before any external side effect

### Digital Marketing — 3 major goals (Phase 1)
| Goal | Frequency | Value (customer outcome) | Deliverables | Approval scope |
|---|---|---|---|---|
| Weekly multichannel posting batch | weekly | Consistent presence across channels | Draft batch: canonical + per-platform drafts + suggested schedule | Per post |
| Daily patient-education micro-post | daily | Trust-building content cadence | 1 draft/day per enabled platform | Per post |
| Monthly campaign pack | monthly | Higher leverage “theme month” marketing | Calendar + N drafts grouped by week | Per post (batch approve can be UI convenience but Plant still enforces per action) |

### Share Trading (deterministic) — 3 major goals (Phase 1)
| Goal | Frequency | Value (customer outcome) | Deliverables | Approval scope |
|---|---|---|---|---|
| Trade intent draft (enter/exit) | on_demand | Customer can create validated trade intents quickly | Draft action plan payload + risk checks (no execution) | Approval required only when executing |
| Scheduled close-position reminder | daily/weekly | Reduce “forgot to close” operational risk | Draft close action proposal at a chosen time window | Approval required to execute close |
| Guardrail report | daily | Visibility into whether configured limits allow requested actions | Deterministic report (limits, allowed coins, last N attempted actions) | Acknowledge in UI; execution still approval-gated |

---

## Generic architecture (Phase 1)

### Agent Type Definition (schema-driven)
**Goal**: keep CP generic while allowing new agent types/goals without rewriting CP.

Minimum fields for an `AgentTypeDefinition`:
- `agent_type_id` (e.g., `marketing.healthcare.v1`, `trading.delta_futures.v1`)
- `version`
- `config_schema` (field definitions + required + constraints)
- `goal_templates[]` (each with `settings_schema`, `default_frequency`, and `skill_binding`)
- `enforcement_defaults` (approval required, trial caps behavior)

### Where authored / stored
- **PP**: author/edit AgentTypeDefinition and publish a new version.
- **Plant**: stores the authoritative versions and serves them to CP.
- **CP**: fetches definitions to render Configure/Goal Setting forms.

### Minimum API contracts (Phase 1)
These are the API surfaces needed so development and tests are unblocked.

| Capability | Endpoint (single door) | Owner | Notes |
|---|---|---|---|
| List hired agent instances/subscriptions | `GET /api/cp/subscriptions` + `GET /api/v1/hired-agents/by-subscription/{subscription_id}` | CP BackEnd + Plant | CP aggregates into one summary for UI |
| Agent instance summary (selected agent hub) | `GET /api/cp/my-agents/summary` | CP BackEnd | Returns list of instances + current selected + per-instance flags (`configured`, `trial_status`) |
| Agent type definitions | `GET /api/v1/agent-types` and `GET /api/v1/agent-types/{agent_type_id}` | Plant | Versioned schema payload (config + goal templates) |
| Save instance config | `PUT /api/v1/hired-agents/draft` + `POST /api/v1/hired-agents/{hired_instance_id}/finalize` | Plant | Plant computes `configured=true` based on agent type requirements |
| Marketing credential store | `PUT /api/cp/platform-credentials` / `GET /api/cp/platform-credentials` | CP BackEnd | Stores encrypted tokens, returns `credential_ref` |
| Trading credential store | `PUT /api/cp/exchange-setup` / `GET /api/cp/exchange-setup` | CP BackEnd | Stores encrypted keys, returns `credential_ref` |
| Goals CRUD | `GET/PUT/DELETE /api/v1/hired-agents/{hired_instance_id}/goals` | Plant | Uses goal templates from agent type definitions |
| Drafts list/review | `GET /api/v1/hired-agents/{hired_instance_id}/deliverables` + `POST /api/v1/deliverables/{deliverable_id}/review` | Plant | Stores approve/reject + mints `approval_id` |
| Execute side-effects (approval-gated) | `POST /api/v1/deliverables/{deliverable_id}/execute` | Plant | Requires `approval_id` for publish/order actions |

---

## EPICS & STORIES (Phase 1)

### Tracking convention
- Every story below is designed to be **small** (request-limit friendly).
- Use the `Status` checkbox to track progress; this file is the single resumption point after any break.
- Run Docker test suites **after each epic**.

---

## Epic AGP1-CP-1 — My Agents selector + instance hub
**Outcome**: CP shows a top dropdown for hired agents and a selected-agent hub with Configure + Goal Setting entry points.

| Story ID | Status | Component(s) | Summary | DoD | Docker tests (after epic) |
|---|---|---|---|---|---|
| AGP1-CP-1.1 | - [x] | CP FE | Replace list-first UI with **top agent selector** (dropdown), showing agent nickname/agent_id/subscription status | Dropdown selects a subscription/instance; selection is persisted in URL query or local state; zero hard-coded assumptions about agent type | See epic tests |
| AGP1-CP-1.2 | - [x] | CP FE | Add 2 tabs/sections for the selected agent: **Configure** and **Goal Setting** (3rd dimension later) | Tabs render and route correctly; disabled states shown when subscription is ended beyond retention | See epic tests |
| AGP1-CP-1.3 | - [x] | CP FE + CP BE | Add CP single-door endpoint to load “agent instance summary” (subscription + hired instance + trial status) | CP FE loads all hub data from one endpoint; summary response includes `configured`, `goals_completed`, and trial fields | See epic tests |

**Epic tests (Docker)**
- CP FrontEnd: `docker compose -f docker-compose.local.yml run --rm cp-frontend-test npm run test -- --run`

---

## Epic AGP1-PLANT-1 — Agent Type Definitions (schema + goal templates)
**Outcome**: Plant serves versioned AgentTypeDefinitions for Marketing and Trading; PP can manage them.

| Story ID | Status | Component(s) | Summary | DoD | Docker tests (after epic) |
|---|---|---|---|---|---|
| AGP1-PLANT-1.1 | - [x] | Plant BE | Create `AgentTypeDefinition` model + in-memory/file store (Phase 1 simple) | Can list/get definitions; includes 2 definitions: Marketing + Trading; versioned | See epic tests |
| AGP1-PLANT-1.2 | - [x] | Plant BE | Add API: `GET /api/v1/agent-types` and `GET /api/v1/agent-types/{id}` | Returns stable JSON contract; unit tests cover | See epic tests |
| AGP1-PP-1.1 | - [x] | PP FE + PP BE | Add PP “Agent Management” page to edit/publish AgentTypeDefinitions | PP can update definition fields and publish a version; guardrails prevent invalid schema | See epic tests |

**Dependency note**: Epic AGP1-CP-2 and AGP1-CP-3 must read definitions from this epic; avoid hard-coding fields/goals in CP.

**Epic tests (Docker)**
- Plant: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- PP BackEnd: `docker compose -f docker-compose.local.yml exec -T pp-backend pytest -q --cov --cov-report=term-missing`
- PP FrontEnd: `docker compose -f docker-compose.local.yml run --rm pp-frontend-test npm run test -- --run`

---

## Epic AGP1-CP-2 — Configure dimension (schema-driven + self-serve credentials)
**Outcome**: For the selected agent instance, CP renders a Configure form from Plant schema and stores refs in Plant while secrets stay in CP.

| Story ID | Status | Component(s) | Summary | DoD | Docker tests (after epic) |
|---|---|---|---|---|---|
| AGP1-CP-2.1 | - [x] | CP FE | Render Configure form dynamically from Plant `config_schema` | Field types: text, enum, list; required validation; save button disabled when invalid | See epic tests |
| AGP1-CP-2.2 | - [x] | CP FE + CP BE | Implement “connect platform” flow for marketing using existing CP credential store | CP stores platform secrets via `/api/cp/platform-credentials`; saved config uses `credential_ref` only | See epic tests |
| AGP1-CP-2.3 | - [x] | CP FE + CP BE | Implement “connect exchange” flow for trading using existing CP exchange setup | CP stores exchange keys via `/api/cp/exchange-setup`; Plant config stores `exchange_credential_ref` only | See epic tests |
| AGP1-CP-2.4 | - [x] | CP BE + Plant Gateway | Ensure CP proxy strips any browser-supplied server-only headers (e.g., `X-Metering-*`) when forwarding | Regression tests prove spoofed headers are removed | See epic tests |

**Dependency note**: Plant-side config completeness rules live in Epic AGP1-PLANT-2.

**Epic tests (Docker)**
- CP BackEnd: `docker compose -f docker-compose.local.yml exec -T cp-backend pytest -q --cov --cov-report=term-missing`
- CP FrontEnd: `docker compose -f docker-compose.local.yml run --rm cp-frontend-test npm run test -- --run`
- Plant: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- Plant Gateway: `docker compose -f docker-compose.local.yml exec -T plant-gateway pytest -q --cov --cov-report=term-missing`

---

## Epic AGP1-PLANT-2 — Plant config completeness + validation (agent-specific)
**Outcome**: Plant determines `configured=true` using agent-specific requirements (Marketing vs Trading) and enforces “refs only” (no secrets) so the agent instance is operationally safe.

| Story ID | Status | Component(s) | Summary | DoD | Docker tests (after epic) |
|---|---|---|---|---|---|
| AGP1-PLANT-2.1 | - [x] | Plant BE | Expand hired agent config validation to include Phase-1 required fields (timezone, language, brand, limits, etc.) | `configured=true` reflects real readiness per agent type definition; invalid configs return actionable errors | See epic tests |
| AGP1-PLANT-2.2 | - [x] | Plant BE | Enforce “refs only” contract for config fields that represent credentials | Requests that attempt to embed secrets in hired-agent config are rejected/ignored; only `credential_ref` values are stored | See epic tests |

**Landing spot (current Phase-1 baseline)**: [src/Plant/BackEnd/api/v1/hired_agents_simple.py](src/Plant/BackEnd/api/v1/hired_agents_simple.py)

**Epic tests (Docker)**
- Plant: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- Plant Gateway: `docker compose -f docker-compose.local.yml exec -T plant-gateway pytest -q --cov --cov-report=term-missing`

---

## Epic AGP1-CP-3 — Goal Setting dimension (templates + drafts + approvals)
**Outcome**: Customer selects goals for the agent instance; Plant generates deliverables as drafts; CP shows review and captures approvals.

| Story ID | Status | Component(s) | Summary | DoD | Docker tests (after epic) |
|---|---|---|---|---|---|
| AGP1-PLANT-3.1 | - [x] | Plant BE | Add goal template + goal instance storage keyed by `hired_instance_id` | CRUD goals; validate against agent type templates | See epic tests |
| AGP1-CP-3.1 | - [x] | CP FE | Goal Setting UI renders available goal templates and allows adding/editing goal instances | Frequency + settings form rendered from schema; save persists | See epic tests |
| AGP1-PLANT-3.2 | - [x] | Plant BE | Implement goal-run to produce drafts (marketing: draft batch; trading: draft intent plan) | Drafts stored with stable ids; deterministic output for trading | See epic tests |
| AGP1-CP-3.2 | - [x] | CP FE | Review UI: list drafts, open detail, approve/reject with notes | Approvals create an `approval_id` record and update draft state | See epic tests |
| AGP1-PLANT-3.3 | - [x] | Plant BE | Enforce approval id on execution endpoints (publish/order actions) via hooks | Any execution attempt without approval is denied (403) with correlation_id | See epic tests |
| AGP1-PLANT-3.4 | - [x] | Plant BE | Scheduler wiring for recurring goals (daily/weekly/monthly) | Goal runs happen at due times; idempotent; retries safe | See epic tests |

**Phase-1 implementation note (deterministic trading)**: trading goal runs must not call any LLM; the deliverable is a validated plan payload and (when approved) an execution request.

**Epic tests (Docker)**
- Plant: `docker compose -f docker-compose.local.yml exec -T -e DATABASE_URL=postgresql+asyncpg://waooaw:waooaw_dev_password@postgres:5432/waooaw_test_db plant-backend pytest -q`
- Plant Gateway: `docker compose -f docker-compose.local.yml exec -T plant-gateway pytest -q --cov --cov-report=term-missing`
- CP BackEnd: `docker compose -f docker-compose.local.yml exec -T cp-backend pytest -q --cov --cov-report=term-missing`
- CP FrontEnd: `docker compose -f docker-compose.local.yml run --rm cp-frontend-test npm run test -- --run`

---

## Epic AGP1-PP-2 — Internal ops visibility + override controls (minimal)
**Outcome**: PP can view agent instances, configs, goals, and approvals for support/debug in Phase 1.

| Story ID | Status | Component(s) | Summary | DoD | Docker tests (after epic) |
|---|---|---|---|---|---|
| AGP1-PP-2.1 | - [x] | PP FE + PP BE | PP page to list customers’ hired agents and show config + goals summary | Support can see configured state and goal list per instance | See epic tests |
| AGP1-PP-2.2 | - [x] | PP FE + PP BE | PP read-only view of drafts + approvals + denials (correlation_id drilldown) | Operators can debug why something was denied | See epic tests |

**Epic tests (Docker)**
- PP BackEnd: `docker compose -f docker-compose.local.yml exec -T pp-backend pytest -q --cov --cov-report=term-missing`
- PP FrontEnd: `docker compose -f docker-compose.local.yml run --rm pp-frontend-test npm run test -- --run`

---

## Notes on “small chunks” (request-limit friendly)
- Keep each story within 1–3 files per app where possible.
- Prefer adding new endpoints in Plant/CP/PP as small, scoped modules (like existing `*_simple.py` modules).
- Add tests alongside each story, but **run full Docker test suites only at epic completion**.

---

## Resumption checklist (copy/paste)
- Current epic in progress: `AGP1-___`
- Last completed story: `AGP1-___.___`
- Next story to start: `AGP1-___.___`

---

## Appendix — Current relevant code anchors (already in repo)
- CP My Agents page: [src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx](src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx)
- Plant hired agent instance API (Phase-1): [src/Plant/BackEnd/api/v1/hired_agents_simple.py](src/Plant/BackEnd/api/v1/hired_agents_simple.py)
- CP hire wizard proxy: [src/CP/BackEnd/api/hire_wizard.py](src/CP/BackEnd/api/hire_wizard.py)
- CP self-serve marketing credentials: [src/CP/BackEnd/api/platform_credentials.py](src/CP/BackEnd/api/platform_credentials.py)
- CP self-serve exchange setup: [src/CP/BackEnd/api/exchange_setup.py](src/CP/BackEnd/api/exchange_setup.py)
- Trading strategy config store (future): [src/CP/BackEnd/api/trading_strategy.py](src/CP/BackEnd/api/trading_strategy.py)
