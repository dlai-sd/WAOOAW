# Skills Implementation (Living Plan)

**Owner surfaces:** CP (Customer Portal) + PP (Platform Portal) + Plant (BackEnd + Gateway).  
**Terminology:** PP = Platform Portal, CP = Customer Portal.
This is a living execution plan for Skills: define → certify → compose → configure per customer → enforce usage → measure outcomes. Update this file after each completed story.

---

## Introduction — our vision on skills management
A **Skill** is a versioned, testable, certifiable capability that can be composed into job roles and then expressed through an agent type at runtime. Skills are not “tags”; they are enforceable contracts: they constrain inputs, tools, side effects, approvals, and telemetry.

The most important property of a Skill is **safe, measurable usage**. Definition matters, but the value is created when a skill is configured per customer, executed through Plant’s enforcement plane, and produces outcomes that can be compared to explicit goals.

We treat Skills as “small units of delivery”: independently certifiable, independently measurable, and independently revocable.

---

## Three-surface contract (Customer config → PP setup → Plant implementation)

**Customer config (CP surface).** The customer expresses goals, constraints, and preferences (what success means; budgets; tone; allowed channels; markets; risk profile). This is business intent and must remain auditable, customer-owned, and editable without redeploying Plant.

**Platform Portal setup (PP surface).** PP operators translate customer intent into safe, enforceable configuration artifacts: credential references, allowlists, rate limits, approval gates, and run templates. PP stores secrets encrypted at rest and only passes references to Plant.

**Plant implementation (Plant surface).** Plant owns deterministic execution, policy enforcement, approvals, and telemetry emission. Plant must be able to execute a skill safely given only: the skill implementation, the runtime bundle (refs), and the request input; it must never require direct browser secrets.

---

## Outcome (who uses skills, and how)

This plan is considered successful only when these three personas can use skills end-to-end:

- **PP operators** can create/certify skills + job roles (Genesis), publish agent types referencing certified skills, and review/approve side effects.
- **CP customers** can (a) discover agents by job role/skills, (b) hire an agent, (c) configure customer-owned intent/settings per skill (e.g., marketing platforms, trading constraints), and (d) see outcomes at a basic “is it working?” level.
- **Plant developers** can implement skills as runtime playbooks with deterministic inputs/outputs, enforce certified-only usage, and emit usage/outcome telemetry attributable to a canonical skill identifier.

Practical implication: each story below explicitly lists **UI**, **API**, and **DB** tasks per surface.

---

## Product MVP framing (so we ship value early)

**MVP definition:** a CP customer can hire an agent with a certified job role/skills, configure required skill blocks (via existing onboarding flows), run safely through Plant enforcement, and see basic per-skill usage/outcome proof. PP operators can manage the catalog and approvals without new pages.

| Release increment | Customer-visible outcome | Included stories | Explicit non-included scope |
|---|---|---|---|
| R1: Governance + safety | Only certified skills can be composed/executed; fail-closed enforcement | SK-1.1–SK-1.4, SK-3.2–SK-3.3 | Advanced scoring, new analytics UI, multi-stage certification workflow |
| R2: Operator catalog usability | PP can create/certify skills + job roles in one place | SK-2.1–SK-2.3, SK-2.5 | New PP pages, complex search/filter UX |
| R3: Customer setup consistency | Existing CP onboarding writes/reads per-skill config blocks; secrets never hit Plant | SK-4.1–SK-4.2 | New customer setup wizard steps beyond mapping existing inputs |
| R4: Proof of value | Per-skill attribution + basic rollups visible in PP/CP | SK-5.1–SK-5.4 | Full BI suite, custom dashboards, predictive KPIs |

**Non-goals (Phase 1):**
- Building a new “Skills Analytics” page or a full reporting suite.
- Multi-step certification workflows (peer review, attestations, expiry) beyond a single certify action.
- Customer-editable skill-by-skill configuration UIs if the same data can be captured via existing wizard/setup screens.

**Open questions (resolve before implementation begins):**
- Which exact PP page has (or should own) a stable `customer_id` context for outcome views (GenesisConsole vs AgentSetup)?
- For outcomes: should we treat usage-event counts as “good enough” MVP value proof where deliverables aren’t created?

---

## High level design and flow

1. **Define skill catalog (Genesis)** in Plant via PP proxy.
2. **Certify** skills and job roles (Genesis gates; initially best-effort, later multi-gate workflow).
3. **Compose** skills into job roles; attach job roles/skills into agent definitions.
4. **Customer hire + setup** stores per-customer configuration (channels + credential refs + allowlists).
5. **Execution** runs through Plant enforcement endpoints (approval-gated side effects).
6. **Usage + outcomes** emitted as usage events and compared to goals/deliverables.

**Existing code/UI anchors used by this plan**
- Plant Genesis skills/job-roles API: [src/Plant/BackEnd/api/v1/genesis.py](../BackEnd/api/v1/genesis.py)
- Plant skill model/service: [src/Plant/BackEnd/models/skill.py](../BackEnd/models/skill.py), [src/Plant/BackEnd/services/skill_service.py](../BackEnd/services/skill_service.py)
- Plant skill execution enforcement: [src/Plant/BackEnd/api/v1/agent_mold.py](../BackEnd/api/v1/agent_mold.py)
- PP Genesis proxy routes: [src/PP/BackEnd/api/genesis.py](../../PP/BackEnd/api/genesis.py)
- PP seed defaults (skills/job roles/agents): [src/PP/BackEnd/api/agents.py](../../PP/BackEnd/api/agents.py)
- PP control surfaces:
  - Agent type defs JSON editor: [src/PP/FrontEnd/src/pages/AgentManagement.tsx](../../PP/FrontEnd/src/pages/AgentManagement.tsx)
  - Seed catalog: [src/PP/FrontEnd/src/pages/AgentData.tsx](../../PP/FrontEnd/src/pages/AgentData.tsx)
  - Agent setup (channels + credential refs): [src/PP/FrontEnd/src/pages/AgentSetup.tsx](../../PP/FrontEnd/src/pages/AgentSetup.tsx)
  - Approval/review queue (marketing drafts): [src/PP/FrontEnd/src/pages/ReviewQueue.tsx](../../PP/FrontEnd/src/pages/ReviewQueue.tsx)
  - Reference agent runner: [src/PP/FrontEnd/src/pages/ReferenceAgents.tsx](../../PP/FrontEnd/src/pages/ReferenceAgents.tsx)

---

## Current gaps (grounded in current implementation)

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| `SkillService.list_skills()` filters `Skill.status == "active"` but creation/certification status semantics are unclear | PP list skills may appear empty or inconsistent | Align BaseEntity status defaults + explicitly set status transitions in Genesis create/certify |
| `certify_skill()` sets `custom_attributes.genesis_certification` but does not clearly set a certified status | “Certified” is ambiguous; downstream gating can’t rely on status | Add explicit `status="certified"` (or `certified_at`) and enforce it in composition + execution |
| Skills exist in two conceptual layers (Genesis skill catalog vs Agent Mold “skill playbooks”) | Confusing mental model for operators and developers | Treat Genesis skills as **catalog + governance**, and playbooks as **runtime executors**; map via stable `skill_key` |

---

## Epic summary (update status after each story)

Status values: `todo` | `in_progress` | `done`.

| Epic | Stories (IDs) | Status | Comments |
|---|---|---|---|
| SK-EP1: Canonical Skill Contract | SK-1.1 → SK-1.4 | done | Canonical skill_key/external_id + explicit lifecycle + certified-only composition + single-door boundary |
| SK-EP2: PP Skill Catalog Control Surface | SK-2.1 → SK-2.5 | in_progress | SK-2.2 complete; next: certify idempotency test alignment + job role parity |
| SK-EP3: Composition (Skill → JobRole → Agent Type) | SK-3.1 → SK-3.4 | todo | Make “required skills” enforceable at runtime |
| SK-EP4: Customer Setup → Runtime Bundle | SK-4.1 → SK-4.4 | todo | Generalize current AgentSetup to per-skill config |
| SK-EP5: Usage, Goals, Outcomes | SK-5.1 → SK-5.4 | todo | Outcome reporting per customer + per skill |

---

## Detailed epics & stories (aligned to code + UI)

**Story template used below (so implementation stays unambiguous):**
- **UI (PP/CP):** concrete files/pages and interactions
- **API (Plant/PP/CP):** endpoints + payload shape + error semantics
- **DB (Plant/CP):** tables/columns/indexes touched (or explicitly “no DB change”)
- **Tests:** where to add tests and what they should assert
- **DoD:** definition of done for the story

### SK-EP1: Canonical Skill Contract

**SK-1.1 — Define the canonical identifiers (`skill_id` vs `skill_key`).** ✅ DONE
- Scope: define a stable “human-meaningful” skill identifier (`skill_key`) for runtime and reporting, and map it to Genesis `skill_id`.
- Primary code anchors: [src/Plant/BackEnd/models/base_entity.py](../BackEnd/models/base_entity.py), [src/Plant/BackEnd/api/v1/genesis.py](../BackEnd/api/v1/genesis.py)

Implementation notes:
- Branch: `feat/skills-sk-1-1-skill-key`

UI (PP/CP):
- PP: in [src/PP/FrontEnd/src/pages/GenesisConsole.tsx](../../PP/FrontEnd/src/pages/GenesisConsole.tsx), display `external_id` (as “Key”) when present.
- CP: no new UI; keep showing `Skill.name`, but keep `skill_key` available in API payloads for support/debug.

API (Plant/PP/CP):
- Plant: treat `Skill.external_id` (BaseEntity) as `skill_key`.
- Plant: on create, accept an optional `skill_key` (mapped to `external_id`); if omitted, derive a deterministic slug from `name`.
- Plant: include `external_id` in `SkillResponse` so PP/CP can display and persist it.

DB (Plant/CP):
- Plant: no migration required (uses `base_entity.external_id`).
- CP: no DB change.

Tests:
- Plant: creating two skills with the same `skill_key` returns 409; creating without `skill_key` derives a stable slug.

DoD:
- Every skill has a stable `skill_key` that can be used in runtime enforcement and usage/outcome attribution.

**SK-1.2 — Make certification status explicit and testable.** ✅ DONE
- Scope: make certification visible and enforceable via explicit lifecycle values, so PP/CP don’t “lose” skills due to mismatched filters.
- Primary code anchors: [src/Plant/BackEnd/services/skill_service.py](../BackEnd/services/skill_service.py)

Implementation notes:
- Branch: `feat/skills-sk-1-2-skill-cert-status`

UI (PP/CP):
- PP: Genesis Console already displays `status` and has a “Certify” action; ensure UI refresh shows the certified state.
- CP: no direct certification UI.

API (Plant/PP/CP):
- Plant: on create, set `status="pending_certification"` instead of default `active`.
- Plant: on certify, set `status="certified"` and populate `custom_attributes.genesis_certification`.
- Plant: fix listing semantics: `GET /genesis/skills` should not hard-filter to `status == "active"` (currently it does in `list_skills()`).
  - Minimal approach: add optional query param `status` and default to returning all skills except `deleted`.

DB (Plant/CP):
- No migration required (uses existing `base_entity.status` and `base_entity.custom_attributes`).

Tests:
- Plant: create returns pending; certify returns certified; list returns both unless status-filtered.

DoD:
- PP can list skills consistently and see a skill transition to certified.

**SK-1.3 — Lock down composition rules (certified-only).** ✅ DONE
- Scope: job roles and agent types can reference only certified skills.
- Primary code anchors: [src/Plant/BackEnd/models/job_role.py](../BackEnd/models/job_role.py), [src/Plant/BackEnd/api/v1/genesis.py](../BackEnd/api/v1/genesis.py)

Implementation notes:
- Branch: `feat/skills-sk-1-3-certified-only-job-roles`

UI (PP/CP):
- PP: on job role creation/edit (Genesis Console enhancements), surface validation errors when required skills aren’t certified.
- CP: only certified skills should appear when showing job role requirements.

API (Plant/PP/CP):
- Plant: validate `JobRoleCreate.required_skills` by loading each Skill and requiring `status == "certified"`.
- Plant: return 422 listing which skill IDs are not eligible.

DB (Plant/CP):
- No migration required (uses `job_role_entity.required_skills` UUID array).

Tests:
- Plant: job role create fails when a required skill is not certified; succeeds when all are certified.

DoD:
- Composition is fail-closed: uncertified skills cannot be composed into job roles.

**SK-1.4 — Document the governance boundary (“single door”).** ✅ DONE
- Scope: enforce “single door” boundaries for privileged actions (PP/CP backends), and ensure Plant remains behind gateways.

Implementation notes:
- Branch: `feat/skills-sk-1-4-governance-boundary`

UI (PP/CP):
- PP: Genesis Console calls PP backend proxies via [src/PP/FrontEnd/src/services/gatewayApiClient.ts](../../PP/FrontEnd/src/services/gatewayApiClient.ts).
- CP: hire wizard writes drafts via CP backend ([src/CP/BackEnd/api/hire_wizard.py](../../CP/BackEnd/api/hire_wizard.py)) which can proxy to Plant when enabled.

API (Plant/PP/CP):
- PP BackEnd: ensure all PP skill catalog operations go through `/api/pp/genesis/*`.
- CP BackEnd: ensure CP FrontEnd never needs Plant base URLs; CP always proxies to Plant.

DB:
- No DB change.

Tests:
- PP BackEnd: auth tests for genesis endpoints (admin-only).
- CP BackEnd: forwarding tests preserve `Authorization` and `X-Correlation-ID`.

DoD:
- Browsers only talk to PP/CP; Plant is never called directly for privileged mutations.

---

### SK-EP2: PP Skill Catalog Control Surface

**SK-2.1 — Minimal PP UI to list skills (no new pages).** ✅ DONE
- Scope: standardize on the existing Genesis Console page for skills/job roles rather than creating new pages.

Implementation notes:
- Branch: `feat/skills-sk-2-1-pp-skill-key-ui`

UI (PP):
- Use and extend [src/PP/FrontEnd/src/pages/GenesisConsole.tsx](../../PP/FrontEnd/src/pages/GenesisConsole.tsx): display `name`, `category`, `status`, and `skill_key` (external_id).

API (PP/Plant):
- Ensure PP gateway client calls the PP backend proxy routes (not Plant directly) for listing.

DB:
- No DB change.

Tests:
- PP FrontEnd: renders empty state, renders list state, and shows ApiErrorPanel on fetch errors.

DoD:
- PP operator can reliably see the skill catalog and statuses.

**SK-2.2 — PP UI create skill (admin-only).** ✅ DONE
- Scope: add a minimal create form to Genesis Console (no new route).

Implementation notes:
- Branch: `feat/skills-sk-2-2-pp-create-skill-ui`

UI (PP):
- Add fields: `name`, `description`, `category`, optional `skill_key`.
- On submit: call create, then refresh list.
- On 409/422: show ApiErrorPanel with the RFC7807 payload.

API (PP/Plant):
- PP BackEnd proxy must forward create payload to Plant `/genesis/skills`.
- Plant create must support `skill_key` (mapped to `external_id`) per SK-1.1.

DB:
- No DB change.

Tests:
- PP FrontEnd: required field validation; displays error panel for 409.

DoD:
- PP operator can create a skill and see it in the list.

**SK-2.3 — PP UI certify skill (explicit action).** ✅ DONE
- Scope: keep the existing “Certify” action but align it to `status=="certified"` semantics from SK-1.2.

Implementation notes:
- Branch: `feat/skills-sk-2-3-pp-certify-tests`

UI (PP):
- Disable “Certify” when status is `certified` (already implemented).
- Refresh list after certify.

API (PP/Plant):
- Ensure certify returns the updated status + certification metadata.

DB:
- No DB change.

Tests:
- PP FrontEnd: certify triggers refresh; button disables after certified.

DoD:
- Certify is idempotent and UI reflects certified state.

**SK-2.4 — Seed defaults remains the fast path.** ✅ DONE
- Scope: keep [src/PP/FrontEnd/src/pages/AgentData.tsx](../../PP/FrontEnd/src/pages/AgentData.tsx) as the dev bootstrap path; ensure it stays safe to re-run.
- DoD: seed endpoint remains gated in prod-like environments.

Implementation notes:
- Branch: `feat/skills-sk-2-4-seed-gating`

**SK-2.5 — PP job role management parity (create/certify/edit).**
- Scope: PP operators must be able to create/certify job roles referencing certified skills, without leaving Genesis Console.

UI (PP):
- Extend [src/PP/FrontEnd/src/pages/GenesisConsole.tsx](../../PP/FrontEnd/src/pages/GenesisConsole.tsx) job role section to support:
  - create job role (name/description + required skill selection)
  - certify job role (idempotent)
  - clear validation errors when required skills are not certified

API (Plant/PP):
- Ensure Plant job-role create/certify aligns with the same lifecycle semantics as skills (at minimum: a role is not “publishable” until certified).

Tests:
- Plant: job role create fails when referencing non-certified skills (SK-1.3);
- PP FrontEnd: certify job role refreshes list and disables action.

DoD:
- PP operator can create and certify a job role composed only of certified skills.

---

### SK-EP3: Composition (Skill → JobRole → Agent Type)

**SK-3.1 — Enforce job role required skills at hire/setup time.**
- Scope: when a customer hires/configures an agent, the resulting hired instance must be consistent with a certified job role and its certified skills.

UI (CP):
- CP agent detail already loads job role + skills in [src/CP/FrontEnd/src/pages/AgentDetail.tsx](../../CP/FrontEnd/src/pages/AgentDetail.tsx); keep this as the customer-facing view of “what skills this agent requires”.
- CP hire wizard should only allow proceeding when the required skills’ setup blocks are complete (see SK-4.1).

API (Plant/CP):
- Plant: on hired-agent draft upsert/finalize, validate that:
  - the agent’s job role exists and is eligible for hire, and
  - each `required_skills` entry resolves to a `Skill` with `status == "certified"`.
- CP BackEnd: already proxies drafts/finalize to Plant in [src/CP/BackEnd/api/hire_wizard.py](../../CP/BackEnd/api/hire_wizard.py); ensure Plant validation errors bubble to the UI.

DB (Plant):
- Reads: `job_role_entity.required_skills`, `skill_entity` rows.
- Writes: `hired_agents` row via [src/Plant/BackEnd/models/hired_agent.py](../BackEnd/models/hired_agent.py) and repository/service.

Tests:
- Plant: hired-agent finalize fails (422) if any required skill is not certified.

DoD:
- A customer cannot end up with an “active” hired instance whose skill chain is uncertified.

**SK-3.2 — Connect agent type definitions to skill composition.**
- Scope: agent type definitions must declare the required skills so enforcement and setup can be deterministic.

UI (PP):
- In [src/PP/FrontEnd/src/pages/AgentManagement.tsx](../../PP/FrontEnd/src/pages/AgentManagement.tsx), validate and document a `required_skill_keys: string[]` field in the JSON definition.

API (Plant/PP):
- Plant: on agent type publish, validate `required_skill_keys`:
  - each key maps to an existing skill (via `external_id`), and
  - each mapped skill is certified.
- Return 422 RFC7807 with details listing missing/uncertified keys.

DB (Plant):
- Uses existing agent type persistence (likely JSON-based); no new tables required.

Tests:
- Plant: publish fails for unknown key; fails for uncertified key; succeeds for certified keys.

DoD:
- A published agent type always references a certified skill set.

**SK-3.3 — Runtime enforcement checks skill availability.**
- Scope: Plant enforcement plane must fail-closed when a requested execution does not match the hired instance’s allowed skills.

API (Plant):
- Agent Mold endpoints accept `skill_key` (preferred) and/or `skill_id` (compat), resolve to the canonical key, and validate against:
  - the agent type’s `required_skill_keys`, and
  - the hired instance’s configured `skill_configs` (where relevant).
- Denial response (make consistent across skills):
  - 422 for malformed/invalid requests (missing required fields, invalid IDs)
  - 403 for policy denials (skill not allowed for this hired instance / not certified)

DB (Plant):
- Reads `hired_agents.config` (JSONB) and agent type definition; writes audit trail (existing logging/audit patterns).

Tests:
- Plant: execution returns denial when `skill_key` is not allowed; acceptance when it is allowed.

DoD:
- It is impossible to execute a skill that is not allowed for that hired instance.

**SK-3.4 — Reference agents become “golden fixtures”.**
- Scope: ensure reference agent runs can be used as end-to-end fixtures proving skill attribution and enforcement.

UI (PP):
- In [src/PP/FrontEnd/src/pages/ReferenceAgents.tsx](../../PP/FrontEnd/src/pages/ReferenceAgents.tsx), display the `skill_key` used for the run and the returned attribution fields.

API (Plant/PP):
- Plant: reference agent execution returns a payload that includes `skill_key`.

DB (Plant):
- Writes deliverables and/or run outputs; include `skill_key` in deliverable payload if no dedicated usage-events table exists.

Tests:
- Plant: reference agent execution response includes `skill_key`.

DoD:
- A reference agent run always yields an auditable `skill_key`.

---

### SK-EP4: Customer Setup → Runtime Bundle

**SK-4.1 — Generalize AgentSetup into per-skill setup blocks.**
- Scope: unify PP setup (operator-owned) and CP setup (customer-owned) into predictable “skill config blocks”, without breaking the existing marketing/trading onboarding.

UI (CP):
- Extend [src/CP/FrontEnd/src/pages/HireSetupWizard.tsx](../../CP/FrontEnd/src/pages/HireSetupWizard.tsx):
  - Continue collecting trading + marketing configs as it does today.
  - Also write a namespaced structure into the draft payload:
    - `config.skill_configs.{skill_key} = { ... }`
  - Backwards compatibility: still read legacy keys (`exchange_provider`, `platforms`, etc.) so existing trials are not broken.

UI (PP):
- Keep PP operator setup in [src/PP/FrontEnd/src/pages/AgentSetup.tsx](../../PP/FrontEnd/src/pages/AgentSetup.tsx) as the place where platform-owned credential refs and allowlists are stored.

API (Plant/CP/PP):
- CP BackEnd: continues to upsert wizard drafts to Plant via `/api/v1/hired-agents/draft` when enabled.
- Plant: validate config structure:
  - accept both legacy and namespaced config for the same skill,
  - compute `configured` based on required skills present + required fields in each skill block.

DB (Plant):
- Persist into `hired_agents.config` (JSONB) in [src/Plant/BackEnd/models/hired_agent.py](../BackEnd/models/hired_agent.py); no migration required.

Tests:
- Plant: draft upsert accepts legacy-only config and namespaced config; configured computation behaves as expected.

DoD:
- A hired instance draft can safely store per-skill configuration blocks while remaining backwards compatible.

**SK-4.2 — Credential refs remain refs; secrets never hit Plant.**
- Scope: enforce that PP/CP store secrets and Plant only receives references.

UI (PP/CP):
- PP: credential and exchange setup flows already mint credential refs; keep UI patterns.
- CP: in hire wizard, never send raw secrets to Plant; only send `credential_ref` values.

API (Plant/PP/CP):
- Plant: validate that config payload does not contain raw secrets (simple denylist for keys like `api_secret`, `access_token`, etc.) and require `*_credential_ref` fields.

DB:
- No schema change.

Tests:
- Plant: sending raw secrets returns 422 with a clear error.

DoD:
- Plant never persists raw secrets; only refs exist in `hired_agents.config`.

**SK-4.3 — Approval minting becomes reusable across skills.**
- Scope: standardize approval semantics so any skill with side effects uses the same “draft → approve → execute” contract.

UI (PP/CP):
- PP: ReviewQueue remains the operator surface for approving deliverables.
- CP: customers should be able to request actions and then see their deliverables pending approval (existing CP hired agents views).

API (Plant/PP/CP):
- Plant: require `approval_id` for any execute endpoint that causes side effects.
- Plant: approvals are persisted via [src/Plant/BackEnd/models/deliverable.py](../BackEnd/models/deliverable.py) `approvals` table.

DB (Plant):
- Uses `deliverables` + `approvals` tables (no migration required).

Tests:
- Plant: executing without approval_id returns 422; executing with approval_id succeeds and marks deliverable executed.

DoD:
- Any side-effectful skill is approval-gated with a consistent contract.

**SK-4.4 — Add a “dry-run” mode per skill.**
- Scope: enable customers/operators to preview output for each skill without side effects.

UI (PP/CP):
- PP: ReferenceAgents already supports draft runs; extend to show dry-run outputs per `skill_key`.
- CP: hire wizard and/or portal can show “preview” runs where applicable.

API (Plant):
- Add/standardize `dry_run=true` behavior: produce deliverable drafts but do not execute side effects and do not require approvals.

DB (Plant):
- Writes deliverable drafts to `deliverables` with `execution_status=not_executed`.

Tests:
- Plant: dry-run creates deliverable with pending_review/not_executed; no external actions invoked.

DoD:
- Dry-run is safe and produces auditable drafts.

---

### SK-EP5: Usage, Goals, Outcomes

**SK-5.1 — Emit `skill_key` on usage events.**
- Scope: every unit of execution is attributable to a canonical `skill_key` (Skill.external_id).
- Primary anchors: [src/Plant/BackEnd/services/usage_events.py](../BackEnd/services/usage_events.py), [src/Plant/BackEnd/api/v1/usage_events.py](../BackEnd/api/v1/usage_events.py)

UI (PP/CP):
- PP: when running reference agents or reviewing drafts, show returned `skill_key` and correlation IDs.
- CP: no new UI required initially.

API (Plant):
- Extend `UsageEvent` with optional `skill_key`.
- Ensure Agent Mold appends usage events with `skill_key` whenever a skill executes.
- Add `skill_key` as an optional filter to `/usage-events` and `/usage-events/aggregate`.

DB (Plant):
- No DB migration (usage events are in-memory/JSONL behind a store interface).

Tests:
- Plant: list usage events filtered by `skill_key` returns only matching events.

DoD:
- Usage events are queryable and attributable by `skill_key`.

**SK-5.2 — Goals link to skills.**
- Scope: each goal instance records which skill(s) it is meant to exercise, so outcomes and usage can roll up per skill.

UI (CP/PP):
- CP: when creating/updating goals for a hired agent, include `skill_keys` in goal settings (derived from the agent type/job role). This can be hidden (not user-editable) in phase 1.
- PP: optionally display associated skill keys when listing goals/deliverables for support.

API (Plant/CP/PP):
- Plant: treat `goal_instances.settings.skill_keys: string[]` as the source of truth for goal→skill attribution.
- CP/PP: pass through `skill_keys` in goal upserts, even if UI does not expose it.

DB (Plant):
- Persist in `goal_instances.settings` JSONB in [src/Plant/BackEnd/models/hired_agent.py](../BackEnd/models/hired_agent.py) (`GoalInstanceModel.settings`).

Tests:
- Plant: goal upsert with `settings.skill_keys=[...]` round-trips unchanged.

DoD:
- Goal instances are attributable to one or more `skill_key` values without schema changes.

**SK-5.3 — Outcome scoring (simple first).**
- Scope: define a minimal, auditable outcome schema per skill and make it aggregatable by month and `skill_key` without adding a new analytics datastore.

UI (CP):
- Surface a basic “is it working?” table on an existing CP page (prefer TrialDashboard or hired-agent detail): last 7/30 days outcome counts/metrics per `skill_key`.

API (Plant):
- Standardize an **Outcome Envelope** emitted by skill executions when they create deliverables.
- Persist outcomes inside `deliverables.payload.outcomes[]` (list of metrics) with at least:
  - `skill_key`, `metric_key`, `metric_value`, `unit`, `observed_at`
  - optional: `goal_instance_id`, `correlation_id`
- Add an aggregation endpoint (new if none exists) to roll up outcomes by month:
  - `GET /api/v1/outcomes/aggregate?customer_id=...&skill_key=...&from=...&to=...&bucket=month`

DB (Plant):
- No schema change: outcomes live inside existing `deliverables.payload` JSON.

MVP note:
- If a skill does not produce deliverables yet, use usage-event rollups as the default “value proof” until outcome envelopes exist for that skill.

Tests:
- Plant: aggregation returns correct bucketed totals when seeded with a few deliverables containing outcomes.
- Plant: empty outcomes does not error and returns empty results.

DoD:
- A monthly rollup exists per `customer_id` per `skill_key` using persisted Plant deliverables.

**SK-5.4 — Surface outcomes in PP without building a new analytics suite.**
- Scope: reuse existing PP patterns (tables + list views) and the Plant aggregation endpoint so an operator can answer: “is this skill delivering value for this customer?”

UI (PP):
- Add an “Outcomes” table to an existing PP page (do not create a new analytics page):
  - Preferred: [src/PP/FrontEnd/src/pages/GenesisConsole.tsx](../../PP/FrontEnd/src/pages/GenesisConsole.tsx) (operators already use it for skills/job roles).
  - Table shows: `period`, `skill_key`, `metric_key`, `value`, `unit`.
- Inputs: `customer_id` selector (or reuse existing context selection if present) and optional `skill_key` dropdown.

UI (CP):
- Read-only: show the same aggregated outcomes on an existing CP page (TrialDashboard or hired-agent detail), scoped to the logged-in customer.

API (PP/CP):
- PP/CP BackEnds proxy the Plant outcomes aggregation endpoint through the same gateway boundary used for Genesis/hired-agent calls.

API (Plant):
- Aggregation endpoint supports filters: `customer_id` (required), `skill_key` (optional), `from/to` (optional defaults), `bucket=month`.

Tests:
- PP FrontEnd: render outcomes table from mocked API response.
- Plant: tenant scoping mirrors existing deliverables access rules.

DoD:
- A PP operator can view per-skill outcome rollups for a customer using Plant data.

---

## Docker-only testing strategy (coverage after each epic)

**Baseline (bring up stack):**
- `docker compose -f docker-compose.local.yml up -d --build`

**After each epic, run coverage for impacted services:**
- Plant BackEnd: `docker compose -f docker-compose.local.yml run --rm plant-backend pytest -q --cov --cov-report=term-missing`
- PP BackEnd: `docker compose -f docker-compose.local.yml run --rm pp-backend pytest -q --cov --cov-report=term-missing`
- PP FrontEnd: `docker compose -f docker-compose.local.yml run --rm pp-frontend-test npm run test -- --run`

**Rule:** do not chase coverage per story; do it after each epic, but keep each story small enough that failures are attributable.

---

## Working process (push after each story)

For each story (SK-x.y):
1. Implement in a short-lived branch.
2. Run Docker tests for the touched service(s).
3. Push the branch.
4. Update this doc:
   - mark the story status `done`
   - add a link to PR/branch name
   - note any follow-up work discovered

Branch naming suggestion:
- `feat/skills-sk-1-1-skill-key` (or `fix/skills-...` for pure bugfixes)
