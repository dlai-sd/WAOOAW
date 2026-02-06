# Share Trading WAOOAW Agent (Delta Exchange India – Futures)

## Purpose
Deliver a production-ready “Trading Agent” that a customer can hire to place and close **futures trades on Delta Exchange India**.

The agent must support post-hire configuration of:
- exchange credentials/keys (stored server-side)
- coin(s) (BTC/ETH/etc.)
- quantity/units
- entry/exit instructions
- optional run interval/time window settings (for later strategy automation)

Execution priority is **Plant + PP first**, with **CP epics/stories groomed separately** so they can be prioritized later.

---

## Scope

### Phase 1 (execute first): Plant + PP (ops + in-house enablement)
- Create/seed a Delta futures trading agent template (AgentSpec) and make it runnable from PP.
- Support **manual trade intents** (enter/exit) with strict validation and idempotent execution.
- Enforce: **no order placement without explicit customer approval**.
- Store credentials/config after hire (PP backend), send only references to Plant.

### Phase 2 (groomed, separate): CP (customer self-serve)
- Customer can connect exchange keys, set parameters, and approve each trade execution.

## Out of scope (explicit)
- Fully autonomous strategy execution without a customer approval gate.
- CP billing/hire/payments UX.

---

## Non-bypassable safety rules
| Rule | Enforcement point | Expected behavior |
|---|---|---|
| Deny-by-default for external actions | Plant hook bus | Any `place_order/close_position` attempt without approval is denied |
| Customer approval required | Approval record | Every executed trade action must have an approval record |
| Credentials never flow browser → Plant | PP/CP backend boundary | Plant receives only credential references/IDs |
| Allowlist exchange actions | Integration layer | Only supported actions/endpoints are callable |
| Auditability | Policy denial + usage events | Every deny/allow is persisted with correlation_id |

---

## Architecture mapping (Plant)
- **Base Agent safety posture:** [main/Foundation/template/base_agent_anatomy.yml](../../main/Foundation/template/base_agent_anatomy.yml)
- **LLM front door concept:** [main/Foundation/template/component_ai_explorer.yml](../../main/Foundation/template/component_ai_explorer.yml) (note: MVP trading does not require LLM; may be deterministic).
- **Agent manufacturing:** [src/Plant/BackEnd/agent_mold/spec.py](../BackEnd/agent_mold/spec.py)
- **Enforcement hooks:** [src/Plant/BackEnd/agent_mold/hooks.py](../BackEnd/agent_mold/hooks.py), [src/Plant/BackEnd/api/v1/agent_mold.py](../BackEnd/api/v1/agent_mold.py)

## Exposure mapping (PP)
- PP page: [src/PP/FrontEnd/src/pages/ReferenceAgents.tsx](../../PP/FrontEnd/src/pages/ReferenceAgents.tsx)

---

# EPICS & STORIES

## Post-hire configuration (Agent Setup)

### Config object (logical contract)
**AgentSetup** (per `customer_id` + `agent_id`):
- `exchange_provider`: `delta_exchange_india`
- `credential_ref`: opaque ID stored in PP/CP backend (never the secret)
- `default_coin`: `BTC | ETH | ...`
- `allowed_coins`: list
- `risk_limits`:
  - `max_units_per_order`
  - `max_notional_inr` (optional)
- `execution_policy`:
  - `require_customer_approval`: always `true` (MVP)
  - `approval_scope`: `per_trade_action`
- Optional (later strategies):
  - `interval_seconds`
  - `active_window` (start/end times)

### Credential storage boundary
- **PP/CP backends** store encrypted API keys and return a `credential_ref`.
- **Plant** uses the ref to request a short-lived signed credential bundle at execution time.

## Epic TR-PLANT-1: Define the Trading AgentSpec + reference agent entry
**Goal:** Create an AgentSpec-backed reference agent for trading.

### Story TR-PLANT-1.1: Add reference agent definition
- **Description:** Add `AGT-TRD-DELTA-001` as `agent_type="trading"`.
- **Dimensions (MVP proposal):**
  - `skill` present with `primary_playbook_id="TRADING.DELTA.FUTURES.MANUAL.V1"` and `category="trading"`
  - `integrations` present with `providers=["delta_exchange_india"]`
  - `industry` present with `industry="trading"` (or platform domain)
  - `trial` and `budget` present
- **Landing spot:** [src/Plant/BackEnd/agent_mold/reference_agents.py](../BackEnd/agent_mold/reference_agents.py)
- **DoD:** Agent appears in `GET /api/v1/reference-agents` and AgentSpec validates.
- **Docker test:** `docker compose -f docker-compose.local.yml exec plant-backend pytest -q src/Plant/BackEnd/tests/unit/test_reference_agents_api.py`

### Story TR-PLANT-1.2: Define request/response contract for trade intents
- **Description:** Extend the reference-agent run request body to accept trading fields for `agent_type="trading"`.
- **Fields (MVP):**
  - `exchange_account_id` (reference to stored credentials)
  - `coin` (e.g., BTC, ETH)
  - `units`
  - `side` (long/short)
  - `action` (enter/exit)
  - optional: `limit_price`, `market` boolean
- **Landing spot:** [src/Plant/BackEnd/api/v1/reference_agents.py](../BackEnd/api/v1/reference_agents.py)
- **DoD:** Request validation returns 422 on missing/invalid fields.
- **Docker test:** `docker compose -f docker-compose.local.yml exec plant-backend pytest -q -k trade_intent_contract`

---

## Epic TR-PLANT-2: Implement Delta Exchange integration layer (deterministic)
**Goal:** Provide a tool/service that can place and close orders with strict safety constraints.

### Story TR-PLANT-2.1: Create Delta client wrapper
- **Description:** Implement a minimal HTTP client wrapper with:
  - request signing (as required by Delta)
  - retry/backoff
  - strict endpoint allowlist
  - redaction for logs
- **Landing spot:** new module under `src/Plant/BackEnd/integrations/delta_exchange/`
- **DoD:**
  - Client can call “place order” and “close position” in a sandbox/dev mode (or mocked tests if sandbox not available).
  - No secret is ever returned in errors/logs.
- **Docker test:** `docker compose -f docker-compose.local.yml exec plant-backend pytest -q -k delta_client`

### Story TR-PLANT-2.2: Credential storage interface (PP-only)
- **Description:** Define a storage boundary so Plant never receives raw keys from the browser.
- **MVP approach:**
  - PP stores credentials server-side (PP BackEnd) and exchanges an `exchange_account_id` with Plant.
  - Plant calls PP (or a secure internal vault service) to fetch short-lived signed credentials at runtime.
- **Landing spot:**
  - PP BackEnd: new admin-only endpoints under `src/PP/BackEnd/api/` (implementation in later sprint)
  - Plant BackEnd: `services/credential_resolver.py` (or similar) (implementation in later sprint)
- **DoD:** Documented contract and enforcement that browser-originated requests cannot pass keys directly.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec pp-backend pytest -q -k exchange_credentials`
  - `docker compose -f docker-compose.local.yml exec plant-backend pytest -q -k credential_resolver`

---

## Epic TR-PLANT-3: Enforce approvals for trading side effects
**Goal:** Order placement and position closing are always approval-gated.

### Story TR-PLANT-3.1: Extend ApprovalRequiredHook to cover trading actions
- **Description:** Treat trading side effects as external actions requiring `approval_id`.
- **Actions to gate (MVP):** `place_order`, `close_position`
- **Landing spot:** [src/Plant/BackEnd/agent_mold/hooks.py](../BackEnd/agent_mold/hooks.py)
- **DoD:** Any attempt without approval yields 403 with `reason="approval_required"` and includes correlation_id.
- **Docker test:** `docker compose -f docker-compose.local.yml exec plant-backend pytest -q src/Plant/BackEnd/tests/unit/test_agent_mold_enforcement_api.py`

### Story TR-PLANT-3.2: Require explicit intent_action on trading runs
- **Description:** Mirror the marketing enforcement model: any external side effect must declare intent.
- **Landing spot:** [src/Plant/BackEnd/api/v1/reference_agents.py](../BackEnd/api/v1/reference_agents.py)
- **DoD:** If trading run tries to place/close without explicit intent, fail closed.
- **Docker test:** `docker compose -f docker-compose.local.yml exec plant-backend pytest -q -k trading_intent_action`

---

## Epic TR-PLANT-4: Implement “manual trading skill” playbook and executor
**Goal:** Produce a deterministic, auditable action plan and optionally execute (when approval present).

### Story TR-PLANT-4.1: Add trading playbook definition
- **Description:** Create a playbook stub for `TRADING.DELTA.FUTURES.MANUAL.V1` with:
  - inputs schema
  - output schema (proposed order request + risk checks)
  - QA rubric and boundary constraints
- **Landing spot:** `src/Plant/BackEnd/agent_mold/playbooks/trading/delta_futures_manual_v1.md`
- **DoD:** Loader validates playbook metadata; tests cover pass/fail.
- **Docker test:** `docker compose -f docker-compose.local.yml exec plant-backend pytest -q -k trading_playbook`

### Story TR-PLANT-4.2: Add trading executor (deterministic)
- **Description:** Implement an executor that:
  - validates coin/units bounds
  - creates an “order intent” payload
  - if `intent_action` is present and approved, calls Delta client
  - otherwise returns a draft plan (no external calls)
- **Landing spot:** `src/Plant/BackEnd/agent_mold/skills/trading_executor.py` (or a folder `skills/trading/`)
- **DoD:** Unit tests prove draft-only output and approved execution path.
- **Docker test:** `docker compose -f docker-compose.local.yml exec plant-backend pytest -q -k trading_executor`

---

## Epic TR-PLANT-5: Audit, usage, and error hygiene
**Goal:** Trading actions are fully auditable and safe to operate.

### Story TR-PLANT-5.1: Emit usage events on every run
- **Description:** Append usage events for draft planning and execution, including correlation_id and action.
- **Landing spot:** [src/Plant/BackEnd/services/usage_events.py](../BackEnd/services/usage_events.py)
- **DoD:** PP can inspect usage records and correlate to requests.
- **Docker test:** `docker compose -f docker-compose.local.yml exec plant-backend pytest -q src/Plant/BackEnd/tests/unit/test_usage_events_api.py`

### Story TR-PLANT-5.2: Persist denial audit records
- **Description:** On any policy deny (missing approval/invalid intent), append to policy denial audit store.
- **Landing spot:** [src/Plant/BackEnd/services/policy_denial_audit.py](../BackEnd/services/policy_denial_audit.py)
- **DoD:** Deny responses always include correlation_id and can be listed.
- **Docker test:** `docker compose -f docker-compose.local.yml exec plant-backend pytest -q -k policy_denial`

---

## PP epics (execute with Plant)

### Epic TR-PP-1: Hire + configure Trading agent (admin)
#### Story TR-PP-1.1: Add AgentSetup screens/endpoints for exchange credentials
- **DoD:** PP stores encrypted keys and exposes `exchange_account_id/credential_ref` for Plant to use.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec pp-backend pytest -q -k exchange_credentials`
  - `docker compose -f docker-compose.local.yml exec pp-frontend npm run test -- --run`

### Epic TR-PP-2: Ops-assisted approvals for executed trades (Phase 1)
#### Story TR-PP-2.1: Approval UI for trade actions
- **DoD:** PP can capture customer approval (manual in Phase 1) and mint an `approval_id` used in Plant execution.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec pp-backend pytest -q -k approval`
  - `docker compose -f docker-compose.local.yml exec pp-frontend npm run test -- --run`

### Epic TR-PP-3: Extend PP ReferenceAgents runner for trading inputs
#### Story TR-PP-3.1: Add trading input fields + approval_id field
- **Landing spot:** [src/PP/FrontEnd/src/pages/ReferenceAgents.tsx](../../PP/FrontEnd/src/pages/ReferenceAgents.tsx)
- **DoD:** Ops can run a draft plan and (with approval) execute.
- **Docker test:** `docker compose -f docker-compose.local.yml exec pp-frontend npm run test -- --run`

---

## CP epics (groomed separately; execute later)

### Epic TR-CP-1: Customer self-serve exchange setup
#### Story TR-CP-1.1: Connect exchange API keys and set parameters
- **DoD:** Customer stores keys; sets default coin, allowed coins, and limits; CP issues `credential_ref`.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec cp-backend pytest -q -k exchange_setup`
  - `docker compose -f docker-compose.local.yml exec cp-frontend npm run test -- --run`

### Epic TR-CP-2: Customer approvals for trade execution (mandatory gate)
#### Story TR-CP-2.1: Approve trade actions and generate approval_id
- **DoD:** Customer sees proposed trade, approves, CP generates approval_id, Plant executes.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec cp-backend pytest -q -k approval`
  - `docker compose -f docker-compose.local.yml exec cp-frontend npm run test -- --run`

### Epic TR-CP-3: Interval/strategy configuration (future)
#### Story TR-CP-3.1: Configure time interval + strategy parameters
- **DoD:** Customer configures interval and strategy inputs; execution remains approval-gated.
- **Docker tests:**
  - `docker compose -f docker-compose.local.yml exec cp-backend pytest -q -k strategy_config`
  - `docker compose -f docker-compose.local.yml exec cp-frontend npm run test -- --run`

---

# Runbook (MVP)
1. In PP: open “Reference Agents”.
2. Select “Delta Futures Trading Agent” (AGT-TRD-DELTA-001).
3. Enter `exchange_account_id`, `coin`, `units`, `side`, `action=enter`.
4. Run without approval (expect deny if intent is execution) OR run draft-only (no intent_action) based on final contract.
5. Provide `approval_id` and rerun to execute order (in prod-enabled environment).

# Acceptance criteria (MVP)
- Trading reference agent is listed in Plant and visible in PP.
- Manual trade intent produces a deterministic plan; execution is approval-gated.
- Credentials are never passed from browser to Plant in plaintext; only IDs/short-lived tokens.
- All actions are auditable (policy denial + usage events) and correlation_id is preserved.

---

## Full test suites (after all stories land)
- Plant: `docker compose -f docker-compose.local.yml exec plant-backend pytest`
- Plant Gateway: `docker compose -f docker-compose.local.yml exec plant-gateway pytest`
- PP BackEnd: `docker compose -f docker-compose.local.yml exec pp-backend pytest`
- PP FrontEnd: `docker compose -f docker-compose.local.yml exec pp-frontend npm run test -- --run`
- CP BackEnd: `docker compose -f docker-compose.local.yml exec cp-backend pytest`
- CP FrontEnd: `docker compose -f docker-compose.local.yml exec cp-frontend npm run test -- --run`
