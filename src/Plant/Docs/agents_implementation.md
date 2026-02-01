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
