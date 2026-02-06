# Agent Ecosystem Implementation Plan (Plant)

**Purpose**: This document is an executable implementation plan to evolve WAOOAW’s existing Base Agent design into a manufacturable “Agent Mold” that can produce real-world agents (e.g., Marketing agents across industries, Tutor agent with whiteboard UI) while enforcing trials, budgets, and token limits.

**Scope constraints**
- We improve and extend the **existing** Base Agent architecture (organs, DNA/EEPROM, constitutional posture). We do not invent a new architecture per agent.
- Dimensions can be **present** or **null/void** (explicit, safe defaults). No “half-implemented” dimensions.
- Enforcement must be **non-bypassable**: LLM calls and external tool calls must pass through policy/budget hooks.

**Key references in this repo**
- Base Agent anatomy (organs, DNA, guardian, metabolic tracking): `main/Foundation/template/base_agent_anatomy.yml`
- AI Explorer (LLM front-door, token tracking, budget enforcement): `main/Foundation/template/component_ai_explorer.yml`
- Trial Mode PEP enforcement: `main/Foundation/template/component_trial_mode_pep_enforcement.yml`
- Subscription plan limits incl. query budget: `main/Foundation/template/financials.yml`
- Plant blueprint (golden source): `docs/plant/PLANT_BLUEPRINT.yaml`

---

## North Star

**Outcome**: “Manufacture” agents by assembling certified components:
- **AgentSpec** (declarative blueprint)
- Certified **Skill playbooks** (marketingskills-style)
- **IndustryProfile** (tuning)
- **Customer setup** profiles
- Non-bypassable **Hooks** + **Policy** + **Budget** enforcement
- Usage **Ledger** tied to subscription plans + trials

---

## Vocabulary (must be consistent)

- **Base Agent**: the runtime motherboard (organs) + DNA persistence + self-healing.
- **Dimension**: a pluggable module that adds capability/constraints (Skill, Industry, Team, Integrations, UI, Localization, Trial, Budget).
- **Null dimension**: explicit no-op implementation with safe defaults (never implicitly missing).
- **AgentSpec**: declarative object that selects dimensions and their configs.
- **Hook bus**: runtime interception points (`SessionStart`, `PreSkill`, `PreToolUse`, `PostToolUse`, `PostSkill`, `SessionEnd`).
- **Policy gate**: decision engine that can allow/deny with an auditable decision record.
- **Usage ledger**: append-only events for tokens/cost/usage.

---

## 5 Goals → Epics → Stories

### Goal 1 — Define AgentSpec + dimension contracts

**Goal statement**: Every agent is created from an `AgentSpec`. Dimensions are modular, versioned, and may be null.

**Epic 1.1: AgentSpec schema + validation**
 - Story 1.1.1: Define `AgentSpec` schema (Pydantic model + JSON schema export)
   - Required: `agent_id`, `agent_type`, `version`, `dimensions{}`
   - Required dimensions list is agent-type dependent; null is allowed if declared.
 - Story 1.1.2: Add validation rules
   - Reject unknown dimensions.
   - Reject partially configured dimensions.
   - Enforce version compatibility.

**Epic 1.2: DimensionContract interface + NullDimension implementations**
- Story 1.2.1: Define `DimensionContract`
  - Methods: `validate(spec)`, `materialize(context)`, `register_hooks(hook_bus)`, `observe(event)`
- Story 1.2.2: Implement `NullDimension` baseline
  - Safe no-op behavior; explicit `present=false`.

**Acceptance criteria**
- You can load a valid AgentSpec and get a compiled “runtime config bundle”.
- Any missing/void dimension is explicit, predictable, and safe.

**Tests**
- Unit tests for schema validation and null-dimension behavior.

**Reviews**
- Solution Architect: schema composability and versioning.
- Business Analyst: fields cover onboarding + goals + deliverables.
- Vision Guardian: defaults are deny-by-default where relevant.

---

### Goal 2 — Implement hook bus + non-bypassable enforcement plane

**Goal statement**: No LLM/tool/integration call can occur without passing through hooks that enforce trial, approvals, and budgets.

**Epic 2.1: Hook bus (runtime interception points)**
- Story 2.1.1: Implement hook bus with standardized events
  - Events include: correlation_id, agent_id, customer_id, purpose, timestamps
- Story 2.1.2: Wire hooks into the execution path used by agents
  - At minimum, before/after any external tool call and LLM call

**Epic 2.2: Policy & approval gates**
- Story 2.2.1: Approval gating for external actions
  - Policy: publish/send requires `approval_id` (unless agent is explicitly configured for autopublish)
- Story 2.2.2: Uniform error responses + audit logging

**Acceptance criteria**
- Attempted publish without approval is denied consistently.
- All denied decisions are logged with a decision_id.

**Tests**
- Unit tests for hooks ordering.
- Integration tests: “publish without approval → 403”.

**Reviews**
- Vision Guardian: safety posture and deny behavior.
- Solution Architect: enforcement plane placement (non-bypassable).

---

### Goal 3 — Ship Skills v1 playbook pipeline (marketingskills adoption)

**Goal statement**: Skills are certified playbooks with deterministic output contracts.

**Epic 3.1: Skill playbook format + loader/compiler**
- Story 3.1.1: Define `SkillPlaybook` format
  - inputs schema, steps, output schema, QA rubric, boundary constraints
- Story 3.1.2: Loader + validation
  - Playbooks must pass schema and QA checks to be “Genesis certifiable”

**Epic 3.2: Channel adapters (for Marketing)**
- Story 3.2.1: Canonical message output schema
- Story 3.2.2: Adapter transforms for LinkedIn/YouTube/Instagram/Facebook/WhatsApp

**Acceptance criteria**
- A marketing skill produces a canonical output + per-channel variants.

**Tests**
- Contract tests for playbook output schema.

**Reviews**
- Business Analyst: deliverable output matches customer value.
- Vision Guardian: claims/compliance constraints are in playbook.

---

### Goal 4 — Trials + subscription metering (token/cost/usage)

**Goal statement**: Trials and paid plans enforce limits (tasks/day, tokens/day, budget/month) with auditability.

**Status**: In-progress (ledger + budget checks + usage events landed)
- In-process usage ledger: `src/Plant/BackEnd/services/usage_ledger.py`
- Usage ledger persistence option (JSON file store): set `USAGE_LEDGER_STORE_PATH`
- Plan budget lookup (template-backed): `src/Plant/BackEnd/services/plan_limits.py`
- Skill execution enforces trial tasks/day cap (10/day) when `trial_mode=true`: `src/Plant/BackEnd/api/v1/agent_mold.py`
- Trial restrictions enforced in skill execution (PEP-aligned):
  - blocks production writes in trial mode
  - blocks high-cost calls when `estimated_cost_usd > 1.0`
- Skill execution enforces monthly budget when `plan_id` + `estimated_cost_usd` are provided
- Skill execution can also estimate cost from tokens/model when `estimated_cost_usd` is omitted (via `MODEL_PRICING_JSON`)
- Usage events schema + append-only (in-memory) store: `src/Plant/BackEnd/services/usage_events.py`
- Usage events persistence option (JSONL file store): set `USAGE_EVENTS_STORE_PATH` for Plant BackEnd
- Usage events aggregation helpers (day/month buckets): `aggregate_usage_events(...)` in `src/Plant/BackEnd/services/usage_events.py`
- API emits usage events:
  - `budget_precheck` when a budget check is performed
  - `skill_execution` after successful execution
  - `skill_execution` records tokens/model/cache_hit when provided by caller (AI Explorer ready)
- Tests: `src/Plant/BackEnd/tests/unit/test_usage_ledger.py`, `src/Plant/BackEnd/tests/unit/test_usage_events.py`, `src/Plant/BackEnd/tests/unit/test_agent_mold_enforcement_api.py`

**Epic 4.1: Usage ledger (append-only)**
- Story 4.1.1: Define usage_event schema
  - tokens_in/out, model, cost_usd, cache_hit, purpose
- Story 4.1.2: Persist + aggregate
  - File-backed append-only store now exists (JSONL) to avoid DB migrations
  - Aggregation helpers available for day/month buckets

**Epic 4.2: Budget enforcement**
- Story 4.2.1: Pre-call estimated cost check
- Story 4.2.2: Trial caps (tasks/day + tokens/day + no production writes)

**Acceptance criteria**
- Over-budget requests are denied before incurring cost.
- Trial agents cannot burn tokens beyond configured caps.

**Tests**
- Unit tests for budget math.
- Integration tests for trial caps.

**Reviews**
- Solution Architect: service boundaries for ledger.
- Vision Guardian: safety + trial restrictions.

---

### Goal 5 — Deliver 3 reference agents end-to-end

**Goal statement**: Prove the mold by manufacturing three agents.

**Status**: Implemented (API + tests)
- Reference agents registry (AgentSpecs): `src/Plant/BackEnd/agent_mold/reference_agents.py`
- Reference agents API: `src/Plant/BackEnd/api/v1/reference_agents.py`
- Unit tests: `src/Plant/BackEnd/tests/unit/test_reference_agents_api.py`
- All executions run through the same hooks + trial/budget enforcement + usage events.

**Status**: Implemented (minimal end-to-end proof via API)
- Reference agent definitions (AgentSpecs): `src/Plant/BackEnd/agent_mold/reference_agents.py`
- Reference agents API:
  - `GET /api/v1/reference-agents`
  - `POST /api/v1/reference-agents/{agent_id}/run`
  - File: `src/Plant/BackEnd/api/v1/reference_agents.py`
- Tests: `src/Plant/BackEnd/tests/unit/test_reference_agents_api.py`

**Epic 5.1: Marketing Agent (Beauty Artist)**
- Setup: brand + locality + offerings
- Goals: 5 posts/week
- Execution: draft → review → publish

**Epic 5.2: Marketing Agent (Cake Shop)**
- Same skills as 5.1, different IndustryProfile

**Epic 5.3: Tutor Agent (Whiteboard)**
- Setup: syllabus + voice/language preferences
- Goals: chapter plan negotiation
- Execution: teach sessions + quizzes

**Acceptance criteria**
- These three agents run through the same hooks/ledger/policy plane.

---

## “Small chunks” to start (first 3 increments)

These are designed to be commit-friendly and to reduce request/CI limits.

### Chunk A (Foundations): AgentSpec + DimensionContract skeleton
- Deliverables
  - `AgentSpec` Pydantic model
  - `DimensionContract` interface
  - `NullDimension` implementations for: Industry, Team, UI, Localization
- Acceptance
  - Load spec; compile into runtime config; null dimensions are explicit.
- Tests
  - Schema validation unit tests

**Status**: Implemented in `src/Plant/BackEnd/agent_mold/`.

### Chunk B (Non-bypassable enforcement skeleton): Hook bus + one enforcement rule
- Deliverables
  - Hook bus with event types
  - Enforce one universal rule: “external publish requires approval_id”
  - Audit log event emitted on deny
- Acceptance
  - Integration test that proves deny happens.

**Status**: Hook bus + approval gate implemented and wired into an API endpoint:
- Skill execution endpoint (enforced): `POST /api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute`
- Test: `src/Plant/BackEnd/tests/unit/test_agent_mold_enforcement_api.py`

### Chunk C (Skills v1 seed): One marketing playbook + 2 channel adapters
- Deliverables
  - Marketing playbook format + loader
  - Canonical output schema + LinkedIn + Instagram adapters
- Acceptance
  - Given brand + industry + theme, produce two platform-appropriate outputs.

**Status**: Implemented minimal pipeline:
- Playbook file: `src/Plant/BackEnd/agent_mold/playbooks/marketing/multichannel_post_v1.md`
- Loader: `src/Plant/BackEnd/agent_mold/skills/loader.py`
- Adapters: `src/Plant/BackEnd/agent_mold/skills/adapters.py`
- Deterministic executor (no AI Explorer yet): `src/Plant/BackEnd/agent_mold/skills/executor.py`

---

## Review gates (Vision Guardian / Solution Architect / Business Analyst)

We implement “reviews” as explicit checkpoints before moving from chunk to chunk.

- **Vision Guardian gate**
  - Confirms deny-by-default for external actions
  - Confirms trial restrictions cover token burn
  - Confirms safety constraints in skill playbooks

- **Solution Architect gate**
  - Confirms enforcement plane is non-bypassable
  - Confirms clean service boundaries (AI Explorer vs Plant)
  - Confirms versioning and rollout strategy

- **Business Analyst gate**
  - Confirms onboarding captures right business facts
  - Confirms deliverables are valuable and measurable
  - Confirms customer review flows fit real UX

---

## Execution notes

- Commit strategy: keep each chunk within small diffs; ensure tests run per chunk.
- Avoid broad refactors; ship minimal scaffolding first.
- Prefer adding new code in Plant execution layer rather than touching PP/CP unless needed.

---

## Open questions (answer before implementation begins)

### Resolved

1. **Plant implementation location**: `src/Plant/BackEnd` only.
2. **API exposure**: Plant APIs are exposed via Gateway (enforcement proxy).
3. **AI Explorer**: separate service (agents/services do not call LLM providers directly).
4. **Message bus**: defer to a later phase (start with synchronous HTTP flows; add queues later).

### Still open

1. For “publish requires approval”: do we allow an opt-in `autopublish=true` per customer/agent with extra policy guardrails?
2. For Tutor whiteboard: which UI stack do we target first (web canvas, WebRTC, or simplest event stream)?
---

## Local Build & Test Setup

### Docker Images

| Component | Images | Ports | Description |
|-----------|--------|-------|-------------|
| **PP (Platform Portal)** | 2 | 8015 (backend), 3001 (frontend) | Admin interface for platform management |
| **Plant + Gateway** | 2 | 8001 (backend), 8000 (gateway) | Agent execution engine + enforcement proxy |
| **CP (Customer Portal)** | 2 | 8020 (backend), 3002 (frontend) | Customer-facing interface |
| **Infrastructure** | 3 | 5432 (postgres), 6379 (redis), 8081 (adminer) | Shared services |

### Quick Start

```bash
# Build all images
docker-compose -f docker-compose.local.yml build

# Start all services
docker-compose -f docker-compose.local.yml up -d

# Check status
docker-compose -f docker-compose.local.yml ps

# View logs
docker-compose -f docker-compose.local.yml logs -f plant-backend plant-gateway pp-backend
```

### Testing

**Unit Tests:**
```bash
# Plant Backend tests
docker-compose -f docker-compose.local.yml exec plant-backend pytest

# PP Backend tests
docker-compose -f docker-compose.local.yml exec pp-backend pytest
```

**Integration Tests:**
```bash
# Test reference agent execution
curl -X POST http://localhost:8000/api/v1/reference-agents/beauty-artist-marketing/run \
  -H "Content-Type: application/json" \
  -d '{"context": {"brand_name": "Test Brand", "industry": "beauty", "theme": "Launch"}, "trial_mode": true}'

# Check usage events
curl http://localhost:8001/api/v1/usage/events
```

**Smoke Tests:**
```bash
curl http://localhost:8001/health  # Plant Backend
curl http://localhost:8000/health  # Plant Gateway
curl http://localhost:8015/health  # PP Backend
curl http://localhost:3001/        # PP Frontend
```

### Service URLs

- **Plant Gateway**: http://localhost:8000 (main entry point)
- **Plant Backend**: http://localhost:8001 (internal)
- **PP Backend**: http://localhost:8015/docs (Swagger UI)
- **PP Frontend**: http://localhost:3001
- **CP Backend**: http://localhost:8020/docs
- **CP Frontend**: http://localhost:3002
- **Adminer (DB UI)**: http://localhost:8081

### Troubleshooting

**Clean restart:**
```bash
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up --build
```

**Check logs:**
```bash
docker-compose -f docker-compose.local.yml logs --tail=50 plant-backend
```

---

## Codespace Deployment (Current)

### Status: ✅ RUNNING

All services are deployed and tested in GitHub Codespace.

### Tested URLs

| Service | URL | Status |
|---------|-----|--------|
| **Plant Backend API** | https://automatic-space-garbanzo-wrp959gxp7qrh96j7-8001.app.github.dev/docs | ✅ TESTED |
| **Plant Gateway API** | https://automatic-space-garbanzo-wrp959gxp7qrh96j7-8000.app.github.dev/docs | ✅ TESTED |
| **PP Backend API** | https://automatic-space-garbanzo-wrp959gxp7qrh96j7-8015.app.github.dev/docs | ✅ TESTED |

**Note**: Ports are forwarded via GitHub Codespaces. Make sure ports 8000, 8001, and 8015 have "Public" visibility in VS Code Ports panel.

### Quick Health Check

```bash
curl https://automatic-space-garbanzo-wrp959gxp7qrh96j7-8001.app.github.dev/health
curl https://automatic-space-garbanzo-wrp959gxp7qrh96j7-8000.app.github.dev/health
curl https://automatic-space-garbanzo-wrp959gxp7qrh96j7-8015.app.github.dev/health
```


---

## Execution Checklist (What’s Left)

This checklist is mapped 1:1 to the Goals/Epics/Stories above. Each row is designed to be implemented as a small, reviewable chunk.

| Goal/Epic/Story | Work item (Definition of Done) | Landing spot (exact files) |
|---|---|---|
| ✅ **Goal 1 — Epic 1.1 / Story 1.1.1 (AgentSpec schema)** | Export JSON schema for `AgentSpec` (and related models) and expose it via a small API endpoint or CLI so specs can be validated outside runtime; DoD: schema output is stable and covered by a unit test snapshot. | `src/Plant/BackEnd/agent_mold/spec.py`, `src/Plant/BackEnd/api/v1/agent_mold.py` (new endpoint), `src/Plant/BackEnd/tests/unit/test_agent_mold_spec.py` |
| ✅ **Goal 1 — Epic 1.1 / Story 1.1.2 (validation rules)** | Enforce: reject unknown dimensions (already), reject “partially configured” dimensions (define what “partial” means per dimension), enforce version compatibility (dimension `version` must be supported); DoD: invalid specs return 422 with violations. | `src/Plant/BackEnd/agent_mold/spec.py`, `src/Plant/BackEnd/agent_mold/contracts.py`, `src/Plant/BackEnd/tests/unit/test_agent_mold_spec.py` |
| ✅ **Goal 1 — Epic 1.2 / Story 1.2.1 (DimensionContract usage)** | Add a compile/materialize step: `AgentSpec` → `CompiledAgentSpec` → “runtime bundle” created from registered dimensions; DoD: reference agents compile successfully and null dimensions are explicit. | `src/Plant/BackEnd/agent_mold/contracts.py`, `src/Plant/BackEnd/agent_mold/registry.py`, `src/Plant/BackEnd/agent_mold/reference_agents.py`, `src/Plant/BackEnd/tests/unit/test_agent_mold_spec.py` |
| ✅ **Goal 1 — Epic 1.2 / Story 1.2.2 (NullDimensions completeness)** | Ensure all optional dimensions used by current AgentSpecs have an explicit null default (including `integrations`, and any new dims added later); DoD: `CompiledAgentSpec.from_agent_spec()` produces a complete dimension set for every agent type. | `src/Plant/BackEnd/agent_mold/spec.py`, `src/Plant/BackEnd/agent_mold/contracts.py` |
| ✅ **Goal 2 — Epic 2.1 / Story 2.1.1 (hook bus events)** | Standardize hook event payload to always include: correlation_id, agent_id, customer_id, purpose, timestamps; add consistent decision_id generation on deny/allow; DoD: every deny returns a decision_id and is auditable. | `src/Plant/BackEnd/agent_mold/hooks.py`, `src/Plant/BackEnd/agent_mold/enforcement.py` |
| ✅ **Goal 2 — Epic 2.1 / Story 2.1.2 (wire hooks into execution path)** | Make hook enforcement non-bypassable for “external actions”: require callers to declare `intent_action` for any side-effecting operation and deny-by-default when missing; DoD: tests prove publish/send/post cannot execute without passing hooks. | `src/Plant/BackEnd/api/v1/agent_mold.py`, `src/Plant/BackEnd/api/v1/reference_agents.py`, `src/Plant/BackEnd/tests/unit/test_agent_mold_enforcement_api.py` |
| ✅ **Goal 2 — Epic 2.2 / Story 2.2.1 (approval gating policy)** | Add explicit policy for optional `autopublish=true` (if allowed): must be set in AgentSpec dimension config and must still pass budget/trial checks; DoD: autopublish off by default and covered by unit tests. | `src/Plant/BackEnd/agent_mold/spec.py`, `src/Plant/BackEnd/api/v1/agent_mold.py`, `src/Plant/BackEnd/agent_mold/hooks.py`, `src/Plant/BackEnd/tests/unit/test_agent_mold_enforcement_api.py` |
| ✅ **Goal 2 — Epic 2.2 / Story 2.2.2 (uniform errors + audit)** | Persist policy denials as append-only audit records (not only logs) and expose a read endpoint; DoD: denial creates an audit record with decision_id and correlation_id. | `src/Plant/BackEnd/services/audit_service.py`, `src/Plant/BackEnd/api/v1/audit.py`, `src/Plant/BackEnd/api/v1/agent_mold.py` |
| ✅ **Goal 3 — Epic 3.1 / Story 3.1.1 (SkillPlaybook format)** | Tighten playbook schema: validate required metadata, inputs, output schema, QA rubric fields; DoD: invalid playbooks fail loader validation with actionable errors. | `src/Plant/BackEnd/agent_mold/skills/playbook.py`, `src/Plant/BackEnd/agent_mold/skills/loader.py` |
| ✅ **Goal 3 — Epic 3.1 / Story 3.1.2 (loader + certification checks)** | Add “certifiable” checks: playbook must pass schema + QA rubric presence; DoD: loader returns a cert status and tests cover pass/fail. | `src/Plant/BackEnd/agent_mold/skills/loader.py`, `src/Plant/BackEnd/agent_mold/skills/playbook.py`, `src/Plant/BackEnd/tests/unit/` (new tests) |
| ✅ **Goal 3 — Epic 3.2 / Story 3.2.1 (canonical output schema)** | Ensure canonical schema is stable and versioned; DoD: adapter contract tests ensure channel variants preserve required fields. | `src/Plant/BackEnd/agent_mold/skills/playbook.py`, `src/Plant/BackEnd/agent_mold/skills/adapters.py` |
| ✅ **Goal 3 — Epic 3.2 / Story 3.2.2 (channel adapters)** | Implement remaining adapters listed in the doc (YouTube/Facebook/WhatsApp) or explicitly mark them out-of-scope for v1; DoD: each adapter has a deterministic transformation and contract tests. | `src/Plant/BackEnd/agent_mold/skills/adapters.py`, `src/Plant/BackEnd/tests/unit/` (new tests) |
| ✅ **Goal 4 — Epic 4.1 / Story 4.1.1 (usage event schema)** | Expand usage schema to include `tokens_in/out`, `model`, `cost_usd`, `cache_hit`, and a normalized `purpose`; DoD: schema is validated and listing endpoint returns consistent fields. (Most fields exist; finalize contract + tests.) | `src/Plant/BackEnd/services/usage_events.py`, `src/Plant/BackEnd/api/v1/usage_events.py`, `src/Plant/BackEnd/tests/unit/test_usage_events.py`, `src/Plant/BackEnd/tests/unit/test_usage_events_api.py` |
| ✅ **Goal 4 — Epic 4.1 / Story 4.1.2 (persist + aggregate)** | Add API endpoints for listing + aggregation (day/month) so PP/CP can display usage; DoD: aggregation endpoint returns deterministic buckets and is covered by unit tests. | `src/Plant/BackEnd/api/v1/usage_events.py`, `src/Plant/BackEnd/api/v1/router.py`, `src/Plant/BackEnd/services/usage_events.py`, `src/Plant/BackEnd/tests/unit/test_usage_events_api.py` |
| ✅ **Goal 4 — Epic 4.2 / Story 4.2.1 (pre-call cost check)** | Fail closed when `plan_id` is provided but metering data is missing/untrusted; DoD: monthly budget cannot be bypassed by omitting `estimated_cost_usd`/meter fields. | `src/Plant/BackEnd/services/metering.py`, `src/Plant/BackEnd/api/v1/agent_mold.py`, `src/Plant/BackEnd/tests/unit/test_agent_mold_enforcement_api.py` |
| ✅ **Goal 4 — Epic 4.2 / Story 4.2.2 (trial caps)** | Clarify semantics: rolling window vs calendar day/month; implement chosen semantics consistently across ledger + aggregation; DoD: counters reset predictably and tests cover boundary conditions. (Chosen semantics: UTC calendar day for trial caps, UTC calendar month for plan budgets.) | `src/Plant/BackEnd/services/metering.py`, `src/Plant/BackEnd/tests/unit/test_metering_trial_caps.py`, `src/Plant/BackEnd/tests/unit/test_agent_mold_enforcement_api.py` |
| ✅ **Goal 5 — Epic 5.1/5.2 (marketing reference agents)** | Add a “draft → review → publish” state machine stub (even if publish is mocked) with explicit approval flow; DoD: `do_publish=true` without approval is denied, with approval is allowed and recorded. | `src/Plant/BackEnd/api/v1/reference_agents.py`, `src/Plant/BackEnd/tests/unit/test_reference_agents_api.py`, `src/Plant/BackEnd/services/usage_events.py` |
| ✅ **Goal 5 — Epic 5.3 (tutor reference agent)** | Add minimal UI event stream contract (even if not implemented): whiteboard step events + quiz delivery; DoD: API returns a deterministic structure that frontends can render without additional inference. | `src/Plant/BackEnd/api/v1/reference_agents.py`, `src/Plant/BackEnd/tests/unit/test_reference_agents_api.py` |
| ✅ **Gateway alignment (Doc “API exposure via Gateway”)** | Remove drift risk by making Plant Gateway middleware import from the shared gateway middleware package (or enforce exact parity via tests); DoD: a single source of truth for Auth/RBAC/Policy/Budget behavior. | `src/Plant/Gateway/middleware/*`, `src/gateway/middleware/*`, `tests/test_gateway_middleware_parity.py` |
| ✅ **AI Explorer integration (Doc “LLM front-door”)** | Add a “trusted metering envelope” contract from AI Explorer → Plant (signed headers) so cost/tokens/model can’t be spoofed; DoD: when `METERING_ENVELOPE_SECRET` is set and the plan has a budget, Plant rejects requests unless a valid `X-Metering-*` signature envelope is present. | `src/Plant/BackEnd/services/metering.py`, `src/Plant/BackEnd/api/v1/agent_mold.py`, `src/Plant/Gateway/main.py`, `src/Plant/BackEnd/tests/unit/test_trusted_metering_envelope.py` |

---

## PP Portal Adoption (Make Plant Visible in PP)

This section maps the **new Plant capabilities** (Agent Mold, usage events, policy denial audit, reference agents, trusted metering envelope) into concrete PP Portal (admin) workflows.

### Epics & Stories

| Epic | Story | PP landing spot (exact files) | Plant capability used | Definition of Done |
|---|---|---|---|---|
| **PP-PLANT-1: Reference agents demo & publish flow** | ✅ **1.1 List reference agents**: show available reference agents in PP so ops can demo “Try Before Hire”. | PP FE page: `src/PP/FrontEnd/src/pages/ReferenceAgents.tsx`; routes: `src/PP/FrontEnd/src/App.tsx`; nav: `src/PP/FrontEnd/src/components/Layout.tsx`; PP FE client: `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | Plant: `GET /api/v1/reference-agents` | PP page lists agents with name/type/spec, handles loading/errors, and is reachable via router + nav. |
|  | ✅ **1.2 Run reference agent (draft)**: run an agent with `customer_id`, `plan_id`, and show draft output. | PP FE page (runner UI): `src/PP/FrontEnd/src/pages/ReferenceAgents.tsx`; PP FE client: `src/PP/FrontEnd/src/services/gatewayApiClient.ts`; uses existing `/api/*` proxy in `src/PP/BackEnd/main_proxy.py` | Plant: `POST /api/v1/reference-agents/{agent_id}/run` | PP can run a reference agent, display returned `draft`, and surface correlation_id on errors. |
|  | ✅ **1.3 Approval-assisted publish**: support `approval_id` entry and `do_publish=true` to simulate the publish gate. | PP FE: `src/PP/FrontEnd/src/pages/GovernorConsole.tsx`; PP FE error surface: `src/PP/FrontEnd/src/components/ApiErrorPanel.tsx`; PP FE client: `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | Plant: publish gating via hooks in reference agent run endpoint | Attempt without `approval_id` shows deny reason; attempt with `approval_id` shows `published=true` and records a `publish_action` usage event. |
| **PP-PLANT-2: Usage & budget visibility in PP** | ✅ **2.1 Usage events list**: display usage events by `customer_id` and optional `agent_id` so PP can explain billing/budgets. | PP FE: `src/PP/FrontEnd/src/pages/CustomerManagement.tsx`; PP FE test: `src/PP/FrontEnd/src/pages/CustomerManagement.test.tsx`; PP FE client: `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | Plant: `GET /api/v1/usage-events` | PP shows a table of events (type/model/tokens/cost/correlation_id) and can filter by customer/agent. |
|  | ✅ **2.2 Usage aggregation**: chart/bucket usage per UTC day/month for budget reporting. | PP FE: `src/PP/FrontEnd/src/pages/CustomerManagement.tsx`; PP FE test: `src/PP/FrontEnd/src/pages/CustomerManagement.test.tsx`; PP FE client: `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | Plant: `GET /api/v1/usage-events/aggregate` | PP renders deterministic buckets and matches Plant’s UTC window semantics (day/month). |
|  | ✅ **2.3 Budget explainability**: when a call is denied due to budgets, show plan/month window reset time from error details. | PP FE: error UI `src/PP/FrontEnd/src/components/ApiErrorPanel.tsx`; PP FE test `src/PP/FrontEnd/src/components/ApiErrorPanel.test.tsx` | Plant: `UsageLimitError` reasons `monthly_budget_exceeded`, `metering_required_for_budget`, `metering_envelope_*` | PP error panel renders `reason`, `details.window_resets_at`, and `correlation_id` consistently. |
| **PP-PLANT-3: Policy denial audit visibility** | ✅ **3.1 List policy denials**: expose the denial audit log so ops can debug “why denied”. | PP FE page: `src/PP/FrontEnd/src/pages/PolicyDenials.tsx`; PP FE test: `src/PP/FrontEnd/src/pages/PolicyDenials.test.tsx`; routes: `src/PP/FrontEnd/src/App.tsx`; nav: `src/PP/FrontEnd/src/components/Layout.tsx`; PP FE client: `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | Plant: `GET /api/v1/audit/policy-denials` | PP lists denial records with correlation_id/decision_id/action/reason/path and supports `limit`. |
|  | ✅ **3.2 Drilldown**: click a denial → show details JSON + recommended operator next action. | PP FE: `src/PP/FrontEnd/src/pages/PolicyDenials.tsx`; PP FE test: `src/PP/FrontEnd/src/pages/PolicyDenials.test.tsx` | Plant: denial record `details` payload | PP supports a simple drilldown that surfaces full `details` and correlation_id. |
| **PP-PLANT-4: AgentSpec tooling in PP (spec validation & schema)** | ✅ **4.1 Fetch AgentSpec JSON schema**: allow PP to download/display schema for external validation. | PP FE page: `src/PP/FrontEnd/src/pages/AgentSpecTools.tsx`; PP FE test: `src/PP/FrontEnd/src/pages/AgentSpecTools.test.tsx`; routes: `src/PP/FrontEnd/src/App.tsx`; nav: `src/PP/FrontEnd/src/components/Layout.tsx`; PP FE client: `src/PP/FrontEnd/src/services/gatewayApiClient.ts` | Plant: `GET /api/v1/agent-mold/schema/agent-spec` | PP renders schema JSON and supports download/copy; schema fetch is cached client-side (in-memory per session). |
|  | **4.2 Validate AgentSpec preflight**: add a form to paste an AgentSpec and call Plant validation endpoint(s) to get 422 violations. | PP FE + PP FE client; PP BE optional proxy | Plant: AgentSpec validation surface (current schema + runtime validation behavior) | Invalid specs show violations in UI; valid spec confirms “OK” without executing a run. |
| **PP-PLANT-5: Trusted metering envelope operationalization** | **5.1 Gateway/header hygiene**: ensure PP cannot be used to spoof `X-Metering-*` headers when proxying to Plant. | PP BE: `src/PP/BackEnd/main_proxy.py` (strip inbound `X-Metering-*` from requests) | Plant: trusted metering enforcement (budgeted plans) | Any inbound `X-Metering-*` from browsers is removed at PP; only server-side trusted callers can add it. |
|  | **5.2 Debug-only envelope signer (optional)**: add a dev-only endpoint to mint a valid envelope for manual testing in PP (never enabled in prod-like envs). | PP BE: new module `src/PP/BackEnd/api/metering_debug.py`; PP FE: optional debug UI | Plant: envelope contract in `services/metering.py` | When `ENABLE_METERING_DEBUG=true` and non-prod-like, PP can mint an envelope; otherwise endpoint 404. |

### Notes (integration choices)

- **Direct proxy vs PP-specific endpoints**: PP already proxies `/api/*` to the Plant Gateway in `src/PP/BackEnd/main_proxy.py`. For PP UX that needs stable admin contracts, prefer adding `/api/pp/*` endpoints that call Plant via `clients/plant_client.py` (type-safe, consistent error mapping).
- **Where “end-user” lives**: the current PP frontend is an admin console; if PP is also intended to be the customer-facing “Plant Portal”, create a dedicated customer UI surface (separate routes/pages) that consumes the same Plant endpoints but enforces stricter RBAC and hides admin-only actions.

### Plant API details (copy/paste for PP implementation)

#### Common conventions

- **Base path**: all Plant endpoints below are under `/api/v1/*`.
- **Tracing header**: send `X-Correlation-ID` on every request; Plant echoes it in error responses and stores it in usage/audit data.
- **Auth**: PP must forward the incoming `Authorization: Bearer <token>` to the Plant Gateway (PP already does this today).
- **Error format**: Plant returns RFC 7807-ish JSON on error.
  - Policy denies: `403` with `{ title: "Policy Enforcement Denied", reason, details, correlation_id }`
  - Usage/metering denies: `429` with `{ title: "Usage Limit Denied", reason, details, correlation_id }`
  - Validation errors: `422` with `{ title: "Request Validation Error", violations, correlation_id }`

#### Epic PP-PLANT-1: Reference agents demo & publish flow

**1.1 List reference agents**

- **Endpoint**: `GET /api/v1/reference-agents`
- **Request**: no body
- **Response**: array of
  - `agent_id: string`
  - `display_name: string`
  - `agent_type: string` (e.g., `marketing`, `tutor`)
  - `spec: object` (AgentSpec-ish payload)

**1.2 Run reference agent (draft)**

- **Endpoint**: `POST /api/v1/reference-agents/{agent_id}/run`
- **Request body (JSON)** (all optional unless noted):
  - `customer_id?: string`
  - `trial_mode?: boolean` (default `false`)
  - `plan_id?: string`
  - Publish:
    - `do_publish?: boolean` (default `false`)
    - `autopublish?: boolean` (default `false`)
    - `approval_id?: string`
  - Metering fields (accepted, but may be overridden by trusted envelope):
    - `estimated_cost_usd?: number` (default `0`)
    - `meter_tokens_in?: number` (default `0`)
    - `meter_tokens_out?: number` (default `0`)
    - `meter_model?: string`
    - `meter_cache_hit?: boolean` (default `false`)
  - Agent-specific inputs:
    - Marketing: `theme?: string`, `language?: string`
    - Tutor: `topic?: string`, `language?: string`
  - Tracing:
    - `purpose?: string`
    - `correlation_id?: string` (if omitted, uses `X-Correlation-ID`)
- **Response (JSON)**:
  - `agent_id: string`
  - `agent_type: string`
  - `status: "draft" | "in_review" | "published"`
  - `review?: { approval_id?: string }`
  - `draft: object` (marketing has `draft.output.*`; tutor has a lesson plan + `ui_event_stream`)
  - `published: boolean`
- **Key error reasons to handle**:
  - `403 Policy Enforcement Denied`
    - `approval_required` (publish attempted without `approval_id`)
    - `autopublish_not_allowed`
    - `unknown_reference_agent`
  - `429 Usage Limit Denied`
    - `trial_production_write_blocked` (trial + publish)
    - `trial_daily_cap` / `trial_daily_token_cap` / `trial_high_cost_call`
    - `metering_required_for_budget` / `monthly_budget_exceeded`
    - `metering_envelope_required` / `metering_envelope_invalid` / `metering_envelope_expired` (when trusted envelope is enabled)

#### Epic PP-PLANT-2: Usage & budget visibility in PP

**2.1 Usage events list**

- **Endpoint**: `GET /api/v1/usage-events`
- **Query params**:
  - `customer_id?: string`
  - `agent_id?: string`
  - `correlation_id?: string`
  - `event_type?: string` (enum, e.g., `skill_execution`, `publish_action`, `budget_precheck`)
  - `since?: datetime` (ISO8601)
  - `until?: datetime` (ISO8601)
  - `limit?: int` (default `100`)
- **Response**: `{ count: number, events: UsageEvent[] }`
  - Each event includes: `event_type`, `correlation_id`, `customer_id`, `agent_id`, `purpose`, `model?`, `cache_hit?`, `tokens_in`, `tokens_out`, `cost_usd`, `timestamp`.

**2.2 Usage aggregation**

- **Endpoint**: `GET /api/v1/usage-events/aggregate`
- **Query params**: same filters as list, plus
  - `bucket?: "day" | "month"` (defaults to `day`)
- **Response**: `{ count: number, rows: UsageAggregateRow[] }`
  - Rows are deterministic UTC buckets with token/cost totals.

#### Epic PP-PLANT-3: Policy denial audit visibility

**3.1 List policy denials**

- **Endpoint**: `GET /api/v1/audit/policy-denials`
- **Query params**:
  - `correlation_id?: string`
  - `customer_id?: string`
  - `agent_id?: string`
  - `limit?: int` (default `100`)
- **Response**: `{ count: number, records: PolicyDenialAuditRecord[] }`
  - Record includes: `correlation_id`, `decision_id?`, `agent_id`, `customer_id?`, `stage`, `action`, `reason`, `path`, `details`.

#### Epic PP-PLANT-4: AgentSpec tooling

**4.1 Fetch AgentSpec schema**

- **Endpoint**: `GET /api/v1/agent-mold/schema/agent-spec`
- **Response**: JSON Schema for `AgentSpec`.

#### Epic PP-PLANT-5: Trusted metering envelope (budget spoof protection)

**When enforced**

- The trusted envelope is **disabled by default**.
- If `METERING_ENVELOPE_SECRET` is set in the Plant backend, then **budgeted-plan calls** require a valid envelope; otherwise Plant returns `429` with `reason` one of:
  - `metering_envelope_required` (no envelope provided)
  - `metering_envelope_invalid` (bad signature/format)
  - `metering_envelope_expired` (timestamp outside TTL)

**Header contract (signed metering envelope)**

- Required headers:
  - `X-Metering-Timestamp`: unix seconds
  - `X-Metering-Tokens-In`: int
  - `X-Metering-Tokens-Out`: int
  - `X-Metering-Model`: string (can be empty)
  - `X-Metering-Cache-Hit`: `0/1` (optional; defaults false)
  - `X-Metering-Cost-USD`: float (optional; defaults 0)
  - `X-Metering-Signature`: base64url(HMAC-SHA256)
- Signature payload (canonical string):
  - `ts|correlation_id|tokens_in|tokens_out|model|cache_hit|cost_usd`
  - `cost_usd` is canonicalized to 6 decimal places.
- TTL:
  - `METERING_ENVELOPE_TTL_SECONDS` (default 300s) controls allowable clock skew.

**Related execution endpoint (budget enforcement happens here too)**

- **Endpoint**: `POST /api/v1/agent-mold/skills/marketing/multichannel-post-v1/execute`
- **Request body (JSON)** includes (key fields):
  - `agent_id` (required), `theme` (required), `brand_name` (required)
  - Optional: `customer_id`, `trial_mode`, `plan_id`, `intent_action`, `autopublish`, `approval_id`
  - Metering fields: `estimated_cost_usd`, `meter_tokens_in/out`, `meter_model`, `meter_cache_hit`
- **Notes for PP**:
  - If a trusted envelope is present, Plant will use envelope metering values (not the JSON body) for budget enforcement and usage event recording.
  - PP should strip inbound `X-Metering-*` headers in its proxy so browsers can’t spoof them.
