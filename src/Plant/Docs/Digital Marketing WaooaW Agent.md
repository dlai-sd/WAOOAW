# Digital Marketing WAOOAW Agent (Healthcare)

## Purpose
Deliver a production-ready “Digital Marketing Agent for Healthcare” that doctors can hire.

The agent must support:
- **Configurable platforms** (count + names + constraints)
- **Platform-suited content** (tone/format per channel)
- **Scheduled posting** (date/time + timezone)
- **Mandatory customer review** before any post is published

Execution priority is **Plant + PP first**, with **CP epics/stories groomed separately** so they can be scheduled later.

---

## Scope

### Phase 1 (execute first): Plant + PP (ops + in-house enablement)
- Create/seed a Healthcare Marketing agent template (AgentSpec) and make it runnable from PP.
- Allow configuring platforms + credentials **after hire** (stored server-side; browser never sends raw credentials to Plant).
- Generate a “posting batch” that includes:
  - canonical message
  - per-platform drafts for a configurable platform list
  - per-platform scheduled time(s)
- Enforce: **no publish without customer approval** (approval gate) and **audit every decision**.

### Phase 2 (groomed, separate): CP (customer self-serve)
- Customer can connect platforms, review drafts, approve, and schedule without ops involvement.

## Out of scope (explicit)
- Payments/subscriptions UX in CP.
- Fully autonomous autopublish without customer review.

---

## Non-bypassable safety rules (must hold in all phases)
| Rule | Enforcement point | Expected behavior |
|---|---|---|
| Deny-by-default for external actions | Plant hook bus | Any “publish/post/send” attempt without approval is denied |
| Customer review required | Approval token/record | Every individual post must have an approval record before execution |
| Credentials never flow browser → Plant | PP/CP backend boundary | Plant receives only credential references/IDs |
| Auditability | Policy denial + usage events | Every deny/allow has correlation_id + persisted audit signal |
| Scheduling is deterministic | Plant scheduler + DB | Scheduled posts run exactly once or retry with idempotency |

---

## Architecture mapping (Plant)
- **Base Agent intent** (shared runtime design): [main/Foundation/template/base_agent_anatomy.yml](../../main/Foundation/template/base_agent_anatomy.yml)
- **Manufacturing mechanism** (implemented today): Agent Mold
  - Agent blueprint: AgentSpec + dimensions: [src/Plant/BackEnd/agent_mold/spec.py](../BackEnd/agent_mold/spec.py)
  - Dimensions compile/materialize: [src/Plant/BackEnd/agent_mold/registry.py](../BackEnd/agent_mold/registry.py)
  - Enforcement plane (hooks + approvals + budgets): [src/Plant/BackEnd/api/v1/agent_mold.py](../BackEnd/api/v1/agent_mold.py)
- **Marketing skill pipeline** (implemented today): playbook + deterministic executor + adapters
  - Adapters: [src/Plant/BackEnd/agent_mold/skills/adapters.py](../BackEnd/agent_mold/skills/adapters.py)
  - Executor: [src/Plant/BackEnd/agent_mold/skills/executor.py](../BackEnd/agent_mold/skills/executor.py)

## Exposure mapping (PP)
- PP page (already exists): [src/PP/FrontEnd/src/pages/ReferenceAgents.tsx](../../PP/FrontEnd/src/pages/ReferenceAgents.tsx)
- PP gateway client (already exists): [src/PP/FrontEnd/src/services/gatewayApiClient.ts](../../PP/FrontEnd/src/services/gatewayApiClient.ts)

---

## Product definition
### Target customer
- Doctors / clinics who want a consistent theme across multiple platforms with platform-native formatting.

### Core job-to-be-done
- “Given a theme, generate platform-specific drafts, have the customer review them, and then publish at the requested date/time.”

### Inputs
- Content inputs (per batch): `theme`, `brand_name`, optional `offer/location/audience/tone/language`
- Configuration inputs (post-hire, per customer+agent): platform list + credential references + constraints + timezone defaults

### Outputs
- **Draft batch**: canonical + variants for the configured platform list
- **Review status** per platform post: `pending_review | approved | changes_requested | rejected`
- **Execution status** per platform post: `scheduled | running | posted | failed`

---

## Post-hire configuration (Agent Setup)

### Config object (logical contract)
This is the minimum configuration needed after an agent is hired by a customer.

**AgentSetup** (per `customer_id` + `agent_id`):
- `timezone`: IANA timezone (e.g., `Asia/Kolkata`)
- `platforms`: list of enabled platforms
  - `platform`: `youtube | instagram | facebook | linkedin | whatsapp`
  - `credential_ref`: opaque ID stored in PP/CP backend (never the secret)
  - `posting_identity`: page/channel/account identifier
  - `constraints`: optional max lengths/hashtag rules per platform
- `review_policy`:
  - `require_customer_approval`: always `true` for this agent
  - `approval_scope`: `per_post` (MVP)

### Credential storage boundary
- **PP/CP backends** store encrypted credentials and return a `credential_ref`.
- **Plant** can request a short-lived signed credential bundle at execution time (internal call) or use a vault integration.

---

## Workflow (end-to-end)
1. Hire agent (PP Phase 1, CP Phase 2)
2. Configure platforms + credentials (post-hire AgentSetup)
3. Create draft batch for a theme
4. Customer reviews each platform draft
5. Approved drafts are scheduled
6. Scheduler executes posts at requested times
7. Audit + usage events are recorded; failures are retryable with idempotency

---

# EPICS & STORIES

## Plant epics (execute first)

### Epic DM-PLANT-1: Agent template + configurable platform variants
**Goal:** Manufacture a Healthcare marketing agent and generate content for a configurable platform list.

#### Story DM-PLANT-1.1: Add Healthcare marketing reference agent template ✅ COMPLETED
- **Landing spot:** [src/Plant/BackEnd/agent_mold/reference_agents.py](../BackEnd/agent_mold/reference_agents.py)
- **DoD:** `GET /api/v1/reference-agents` includes `AGT-MKT-HEALTH-001` with `industry=healthcare`.
- **Docker test:** `docker compose -f docker-compose.local.yml exec -T plant-backend pytest -q --no-cov tests/unit/test_reference_agents_api.py`

#### Story DM-PLANT-1.2: Make executor emit variants for the configured platforms
- **Landing spot:** [src/Plant/BackEnd/agent_mold/skills/executor.py](../BackEnd/agent_mold/skills/executor.py), [src/Plant/BackEnd/agent_mold/skills/adapters.py](../BackEnd/agent_mold/skills/adapters.py)
- **DoD:** Returned output includes variants for all requested platforms (default set: YouTube/Instagram/Facebook/LinkedIn/WhatsApp).
- **Docker test:** `docker compose -f docker-compose.local.yml exec -T plant-backend pytest -q --no-cov tests/unit/test_skill_playbook_pipeline.py`

✅ **COMPLETED**

### Epic DM-PLANT-2: Draft batch + review gate + scheduled posting
**Goal:** Create a reviewable batch, require approval per post, and schedule posting.

#### Story DM-PLANT-2.1: Add “draft batch” API contract (no execution)
- **Description:** Endpoint creates a batch of drafts and stores it with `pending_review` state.
- **Landing spot:** New routes under `src/Plant/BackEnd/api/v1/` (marketing posting module) + file-backed persistence under `src/Plant/BackEnd/services/`.
- **DoD:** Batch contains N platform drafts, each with a stable `post_id`.
- **Docker test:** `docker compose -f docker-compose.local.yml exec -T plant-backend pytest -q --no-cov -k draft_batch`

✅ **COMPLETED**

#### Story DM-PLANT-2.2: Enforce “no post without approval_id” per post
- **Description:** Execution endpoint requires `approval_id` and denies otherwise.
- **Landing spot:** [src/Plant/BackEnd/agent_mold/hooks.py](../BackEnd/agent_mold/hooks.py) (ensure `post/publish/send` actions are covered) + execution endpoint.
- **DoD:** Denied requests return 403 with `reason=approval_required` and correlation_id.
- **Docker test:** `docker compose -f docker-compose.local.yml exec -T plant-backend pytest -q --no-cov tests/unit/test_agent_mold_enforcement_api.py`

✅ **COMPLETED**

#### Story DM-PLANT-2.3: Add scheduler to execute due approved posts
- **Description:** Use APScheduler (already in Plant) to poll for `scheduled` posts whose `scheduled_at <= now` and execute idempotently.
- **Landing spot:** Plant scheduler module (similar to embedding quality job patterns) + posting execution service.
- **DoD:** A post runs once, retries on transient failures, and records `posted|failed` with details.
- **Docker test:** `docker compose -f docker-compose.local.yml exec -T plant-backend pytest -q --no-cov -k scheduled_posting`

### Epic DM-PLANT-3: Social platform integrations (real posting)
**Goal:** Post via provider APIs using credential references resolved server-side.

#### Story DM-PLANT-3.1: Add integration abstraction + provider allowlist
- **Description:** Define a provider interface and allowlist only the configured platforms.
- **DoD:** Unknown providers are denied before any network call.
- **Docker test:** `docker compose -f docker-compose.local.yml exec -T plant-backend pytest -q --no-cov -k provider_allowlist`

#### Story DM-PLANT-3.2: Implement provider adapters (YouTube/Instagram/Facebook/LinkedIn/WhatsApp)
- **Description:** MVP can use mocked provider calls in tests; real posting is enabled only with configured secrets.
- **DoD:** Each provider adapter supports “publish text” (and optionally media later) and returns provider post URL/ID.
- **Docker test:** `docker compose -f docker-compose.local.yml exec -T plant-backend pytest -q --no-cov -k social_provider`

### Epic DM-PLANT-4: Audit + usage events for draft/review/post lifecycle
**Goal:** Every important transition is auditable.

#### Story DM-PLANT-4.1: Persist policy denials and execution events
- **Landing spot:** [src/Plant/BackEnd/services/policy_denial_audit.py](../BackEnd/services/policy_denial_audit.py), [src/Plant/BackEnd/services/usage_events.py](../BackEnd/services/usage_events.py)
- **DoD:** Denials and executions have correlation_id; PP can list them.
- **Docker test:** `docker compose -f docker-compose.local.yml exec -T plant-backend pytest -q --no-cov tests/unit/test_usage_events_api.py`

---

## PP epics (execute with Plant)

### Epic DM-PP-1: Hire + configure Healthcare marketing agent (admin)
**Goal:** PP can attach the agent to a customer and store post-hire setup (platforms + credential refs).

#### Story DM-PP-1.1: Add admin screens/endpoints for AgentSetup
- **Description:** Create/update AgentSetup for a customer+agent and store encrypted credential refs.
- **Landing spot:** PP BackEnd `src/PP/BackEnd/api/` + PP FrontEnd pages under `src/PP/FrontEnd/src/pages/`.
- **DoD:** PP can save AgentSetup; Plant receives only refs.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec pp-backend pytest -q -k agent_setup`
  - `docker compose -f docker-compose.local.yml exec pp-frontend npm run test -- --run`

### Epic DM-PP-2: Ops-assisted customer review + approvals (Phase 1)
**Goal:** Until CP is prioritized, PP supports the review gate workflow.

#### Story DM-PP-2.1: Review queue UI for draft batches
- **DoD:** Ops can view each platform post draft, mark it “approved”, and capture an `approval_id`.
- **Docker test:** `docker compose -f docker-compose.local.yml exec pp-frontend npm run test -- --run`

#### Story DM-PP-2.2: Schedule approved posts
- **DoD:** Ops can set `scheduled_at` per platform post (timezone-aware) and submit schedule to Plant.
- **Docker test:** `docker compose -f docker-compose.local.yml exec pp-backend pytest -q -k schedule_post`

---

## CP epics (groomed separately; execute later)

### Epic DM-CP-1: Customer connects platforms after hiring
#### Story DM-CP-1.1: Platform connection UI + backend credential storage
- **DoD:** Customer connects YouTube/Instagram/Facebook/LinkedIn/WhatsApp; CP stores encrypted credentials and issues `credential_ref` values.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec cp-backend pytest -q -k platform_credentials`
  - `docker compose -f docker-compose.local.yml exec cp-frontend npm run test -- --run`

### Epic DM-CP-2: Customer review & approval UX (mandatory gate)
#### Story DM-CP-2.1: Review drafts per platform and approve/reject
- **DoD:** Customer approves each post; CP produces an `approval_id` usable by Plant for execution.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec cp-backend pytest -q -k approval`
  - `docker compose -f docker-compose.local.yml exec cp-frontend npm run test -- --run`

### Epic DM-CP-3: Customer scheduling UX
#### Story DM-CP-3.1: Schedule approved posts with timezone support
- **DoD:** Customer chooses date/time per platform post; CP submits schedule to Plant.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec cp-backend pytest -q -k schedule`
  - `docker compose -f docker-compose.local.yml exec cp-frontend npm run test -- --run`

---

## Runbook (Phase 1)
1. Start stack: `docker compose -f docker-compose.local.yml up -d --build`
2. In PP: configure AgentSetup for the customer (platform list + credential refs).
3. Create a draft batch (theme + brand inputs) and verify all configured platforms got drafts.
4. Approve each platform post (create approval_id records).
5. Schedule posts.
6. Confirm scheduler executes at scheduled time and provider adapters post successfully.

## Full test suites (after all stories land)
- Plant: `docker compose -f docker-compose.local.yml exec plant-backend pytest`
- Plant Gateway: `docker compose -f docker-compose.local.yml exec plant-gateway pytest`
- PP BackEnd: `docker compose -f docker-compose.local.yml exec pp-backend pytest`
- PP FrontEnd: `docker compose -f docker-compose.local.yml exec pp-frontend npm run test -- --run`
- CP BackEnd: `docker compose -f docker-compose.local.yml exec cp-backend pytest`
- CP FrontEnd: `docker compose -f docker-compose.local.yml exec cp-frontend npm run test -- --run`
