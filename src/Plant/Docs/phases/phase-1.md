# Phase 1 — Stabilize the Core Journey (Register → Hire)

This Phase 1 document is intentionally **gap-only**: it describes *only* what is missing or mismatched relative to the current implementation.

Target outcome for Phase 1 (kept constant):
- Customer registration is durable and becomes the starting point of all subsequent actions.
- Hiring becomes durable (DB-backed) and produces a customer-owned hired agent instance tied to a subscription.
- The customer journey exposes **exactly 2 agent types**.
- **No skill enforcement** blocks Register → Hire in Phase 1.

Status values used below: `todo` | `in_progress` | `done`.

---

## Current implementation snapshot (what already exists)

**Registration durability (CP → Plant)**
- CP FrontEnd collects full registration payload + Turnstile + OTP.
- CP BackEnd persists registration in a file store, then on OTP verify upserts the customer into Plant via `POST /api/v1/customers`.

**Agent types (Plant)**
- Plant already exposes `GET /api/v1/agent-types` (in-memory) with exactly 2 definitions:
  - `marketing.digital_marketing.v1` (“Digital Marketing”)
  - `trading.share_trader.v1` (“Share Trader”)
- Plant already exposes `GET /api/v1/agent-types-db` (DB-backed) guarded by `USE_AGENT_TYPE_DB` (default `false`).

**Payments + subscriptions (Plant)**
- Plant already exposes `POST /api/v1/payments/...` (in-memory) and maintains in-memory subscription state.

**Hire journey (Plant)**
- Plant already exposes `PUT /api/v1/hired-agents/draft`, `GET /by-subscription/...`, goal CRUD, and `POST /{id}/finalize`.
- Hired agent state is stored **in-memory** (`_by_id`, `_by_subscription`, `_goals_by_hired_instance`) and uses `payments_simple` to decide read/write status.
- When `PERSISTENCE_MODE=db`, SK-3.1 Agent→JobRole→Skill enforcement is **opt-in** via `HIRE_ENFORCE_SKILL_CHAIN` (default off); default remains `PERSISTENCE_MODE=memory`.
- Plant already enforces **refs-only config** at the API boundary (raw secrets rejected) for the hired agent config.

---

## Gaps to close (from current implementation only)

| Root cause | Impact | Best possible solution/fix |
|---|---|---|
| Hire still infers type via `_agent_type_id_for_agent_id()` based on `agent_id` prefix | CP/Plant can drift on what “two agents” means; the journey isn’t strictly catalog-driven | Require `agent_type_id` explicitly in hire and validate against the catalog (stop inferring from `agent_id`) |
| Core subscription + hired-instance persistence is in-memory (`payments_simple`, `hired_agents_simple`) | Register→Hire breaks on restart; cannot scale beyond single process | Introduce DB-backed persistence for subscriptions + hired instances (keep in-memory only for unit tests) |
| Two “agent types” surfaces exist (`/agent-types` and `/agent-types-db`) with separate feature gating | CP can’t reliably know which endpoint is authoritative | Make CP use a single endpoint and make Plant route that endpoint to DB when enabled (or alias `/agent-types` → DB) |
| Phase 1 durability is not proven by docker integration tests in DB mode | Regressions are likely as flags change | Add docker-first integration tests covering register→hire→finalize for both agent types in DB mode |

---

## Gap-driven epics & stories

### PH1-EP1: “Exactly 2 agent types” is catalog-driven (not inferred)

| Story | Status | Gap being closed |
|---|---|---|
| PH1-1.1: Canonicalize the two agent types (IDs + naming) | done | Canonical IDs + display names are enforced (legacy IDs are accepted as aliases) |
| PH1-1.2: Remove `_agent_type_id_for_agent_id()` from hire path by requiring `agent_type_id` in hire requests | done | Hire currently infers type from `agent_id` prefix |
| PH1-1.3: Ensure CP listing is sourced from the catalog endpoint and contains exactly 2 rows | done | CP could list something else or drift if it uses legacy sources |

**PH1-1.1 — Canonicalize the two agent types (IDs + naming)**
- Current: Plant catalog is canonicalized to `marketing.digital_marketing.v1` (“Digital Marketing”) and `trading.share_trader.v1` (“Share Trader”).
- Fix (implemented): `GET /api/v1/agent-types` returns only the canonical IDs, and legacy IDs (`marketing.healthcare.v1`, `trading.delta_futures.v1`) resolve as aliases.

**PH1-1.2 — Require `agent_type_id` in hire requests; stop inferring from `agent_id`**
- Current: `src/Plant/BackEnd/api/v1/hired_agents_simple.py` infers agent type via `_agent_type_id_for_agent_id()`.
- Gap: inference prevents strict “2 agent types” enforcement and couples behavior to `agent_id` prefixes.
- Fix: extend the hire draft/finalize requests to include `agent_type_id`, validate it against the catalog, and store it on the hired instance.

**PH1-1.3 — CP must list only the two types**
- Current: Plant serves exactly two types in-memory; CP listing source-of-truth still needs to be enforced.
- Fix: CP should render the marketplace/hire entry point strictly from the catalog endpoint, and nothing else.

---

### PH1-EP2: Make subscription lifecycle durable (replace in-memory `payments_simple` in core path)

| Story | Status | Gap being closed |
|---|---|---|
| PH1-2.1: DB-backed subscription record with idempotency | done | Subscriptions are currently in-memory (`payments_simple`) |
| PH1-2.2: Preserve existing “writable vs read-only” gating but source status from DB | done | Hire gating now uses DB subscription status when `PERSISTENCE_MODE=db` |

**PH1-2.1 — DB-backed subscription record with idempotency**
- Current: `src/Plant/BackEnd/api/v1/payments_simple.py` stores subscriptions in `_subscriptions` dict.
- Gap: restart loses subscription state; not safe for scaling.
- Fix: persist subscription (and trial timestamps/status) in DB; preserve idempotency semantics.

**PH1-2.2 — Gate hire writes based on DB subscription status**
- Current: `hired_agents_simple` blocks draft/finalize if `payments_simple` says subscription not active.
- Gap: gating must remain but use DB as source-of-truth.
- Fix: replace `payments_simple.get_subscription_status(...)` calls with a DB-backed lookup.

---

### PH1-EP3: Make hired agent instances durable (replace in-memory `_by_id`/`_by_subscription`)

| Story | Status | Gap being closed |
|---|---|---|
| PH1-3.1: DB-backed hired agent instance + lookup by subscription | done | Instances persist and lookup-by-subscription uses DB when `PERSISTENCE_MODE=db` |
| PH1-3.2: DB-backed goals persistence (if goals remain part of Phase 1 UX) | done | Goals persist in DB when `PERSISTENCE_MODE=db` (memory remains default) |
| PH1-3.3: Preserve refs-only config enforcement in DB mode | done | Raw-secret rejection is enforced in both memory and DB mode |
| PH1-3.4: Preserve customer ownership semantics (404-on-mismatch) in DB mode | done | DB-mode endpoints return 404 on customer mismatch to avoid leaking existence |

**PH1-3.1 — DB-backed hired agent instance + lookup by subscription**
- Current: `src/Plant/BackEnd/api/v1/hired_agents_simple.py` stores hired instances in `_by_id` and `_by_subscription`.
- Gap: restart loses hired instances; cannot scale.
- Fix: persist hired instances in DB and implement `GET /by-subscription/...` as a DB lookup.

**PH1-3.2 — DB-backed goals persistence (only if Phase 1 keeps goals)**
- Current: goal CRUD stores records in `_goals_by_hired_instance`.
- Gap: goals vanish on restart.
- Fix (implemented): when `PERSISTENCE_MODE=db`, goal CRUD uses `goal_instances` via `GoalInstanceRepository`; in-memory remains the default for Phase-1 compatibility.

---

### PH1-EP4: Disable skill enforcement for Phase 1 DB mode (no skills required)

| Story | Status | Gap being closed |
|---|---|---|
| PH1-4.1: Gate SK-3.1 Agent→JobRole→Skill enforcement behind a flag/capability defaulting OFF | done | DB mode previously enforced skills and could block hiring |

**PH1-4.1 — Gate SK-3.1 enforcement behind a Phase 1-compatible switch**
- Current: `hired_agents_simple` calls `_validate_agent_job_role_skill_chain(...)` when `PERSISTENCE_MODE=db` for both draft and finalize.
- Gap: Phase 1 explicitly requires “no skills enforced”, but DB mode previously made skills a hard requirement.
- Fix (implemented): `HIRE_ENFORCE_SKILL_CHAIN` (default off) gates SK-3.1 enforcement in [src/Plant/BackEnd/api/v1/hired_agents_simple.py](src/Plant/BackEnd/api/v1/hired_agents_simple.py), with unit coverage in [src/Plant/BackEnd/tests/unit/test_hired_agents_skill_chain_validation.py](src/Plant/BackEnd/tests/unit/test_hired_agents_skill_chain_validation.py).

---

### PH1-EP5: Prove the journey in DB mode (docker-first integration tests)

| Story | Status | Gap being closed |
|---|---|---|
| PH1-5.1: Integration test for register→hire→finalize in DB mode for both agent types | done | DB-mode journey is proven with integration coverage for both agent types |
| PH1-5.2: Regression test that defaults don’t silently fall back to in-memory in docker environments | done | DB-mode reads ignore in-memory maps even when seeded with misleading state |

**PH1-5.1 — Docker integration test (DB mode)**
- Current: DB-backed mode exists as a partial feature flag (and agent types DB has its own flag), but hire/payout persistence is still in-memory.
- Gap: Phase 1 needs an executable proof that “restart-safe” Register→Hire works.
- Fix: add an integration test that runs with DB mode enabled and asserts durable fetch works after writes.

**PH1-5.2 — Regression tests for “no silent fallback to memory” in docker**
- Current: multiple feature flags default to Phase-1 compatibility behavior (e.g., `PERSISTENCE_MODE=memory`, `USE_AGENT_TYPE_DB=false`).
- Gap: it’s easy to unintentionally run “Phase 1” environments without DB durability.
- Fix: add a docker integration assertion suite that fails fast if DB durability is not enabled in the environment under test.

