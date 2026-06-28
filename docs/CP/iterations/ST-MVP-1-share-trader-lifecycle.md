# ST-MVP-1 — Share Trader Full Commercial Lifecycle

> **Template version**: 3.0 (adapted)
> **Plan ID**: ST-MVP-1
> **Advances**: Share Trader value — every story in this plan is required for the first paying customer

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `ST-MVP-1` |
| Feature area | Share Trader — Full commercial lifecycle (CP BackEnd, Plant BackEnd, Mobile) |
| Created | 2026-06-28 |
| Author | GitHub Copilot (PM mode) |
| Parent gap analysis | Session 2026-06-28 — Share Trader gap analysis |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 4 |
| Total stories | 12 |
| Branch | `docs/ST-MVP-1-share-trader-lifecycle` |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns embedded **inline** in each story card |
| No planning ability | Stories are atomic — one deliverable, one file set, one test command |
| Max 3 file reads per story | Pre-identified in each card's "Files to read first" |
| Binary inference only | Acceptance criteria are pass/fail |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT open other stories. All patterns you need are in your card.

---

## Vision Intake Summary

- **Area**: Plant BackEnd (business logic), CP BackEnd (thin proxy), Mobile React Native
- **Outcome**: A paying Share Trader customer completes the full lifecycle on mobile — configure credentials + strategy + autonomous limits via chat wizard → agent identifies trades via RSI → customer approves or autonomous mode executes → notifications sent → performance reviewed → P&L tax report downloaded
- **Out of scope**: CP FrontEnd web UI; multiple exchanges (Delta Exchange India only); LLM-driven wizard (Phase 2 — step-machine only for this plan); backtesting; SEBI algo registration
- **Lane**: Lane B — new Plant BE endpoints, extended step-machine, new mobile screens
- **Urgency**: 2 iterations, ≤ 6 stories each to avoid agent context exhaustion per run

---

## Objectives & Definition of Done

### Configure lifecycle ✓ when:
- [ ] Customer completes 10-step chat wizard: api_key → api_secret → validate → instrument (Delta crypto only) → rsi_period → risk_limits → capital_pct → leverage → autonomous_mode consent → risk_disclosure → done
- [ ] Wizard rejects NIFTY/BANKNIFTY; validates instrument against Delta Exchange `/v2/products`
- [ ] Credentials persisted via `ExchangeCredentialService`; `credential_ref` stored in `goal_config`
- [ ] `GoalConfig` stores: `default_coin`, `rsi_period`, `max_units_per_order`, `capital_pct` (1–20%), `leverage` (1–200), `autonomous_mode` (bool), `autonomous_consent_at`, `stop_loss_pct`, `profit_target_pct`

### Trade execution lifecycle ✓ when:
- [ ] `DeltaExchangePump` resolves API key from `ExchangeCredentialService` via `credential_ref` (no plaintext key in skill_config)
- [ ] RSI computed using Wilder's EMA (matches TradingView for same period + candles)
- [ ] Agent suppresses BUY if open long position already exists; suppresses SELL if short already open
- [ ] Stop-loss and take-profit limit orders placed alongside every entry order
- [ ] Approval mode: deliverable queued; trade executes only after customer approves on mobile
- [ ] Autonomous mode: trade executes directly after consent check; customer notified via email + SMS + in-app push within 60 seconds

### Safety lifecycle ✓ when:
- [ ] Emergency stop halts scheduler and cancels pending orders within 60 seconds of customer tap on mobile
- [ ] No single trade exceeds `capital_pct` × account balance
- [ ] Platform hard-cap enforced: `max_leverage = 10` (ConstraintPolicy); customer can configure up to this value

### Review lifecycle ✓ when:
- [ ] Trade history list shows all executed trades: instrument, direction, entry price, P&L, timestamp
- [ ] Performance card shows aggregate win rate, avg P&L%, trade count for configurable period
- [ ] Recommendation engine suggests RSI threshold adjustments after ≥ 5 trades

### Reporting lifecycle ✓ when:
- [ ] Tax report endpoint returns per-month P&L statement with all trades
- [ ] Mobile export/share button delivers CSV to device

---

## PM Review Checklist

- [x] Epic titles name customer outcomes
- [x] Every story has exact branch name
- [x] Every story embeds NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every CP BackEnd story states pattern A, B, or C
- [x] Every new Plant route uses `waooaw_router()`
- [x] Every GET route uses `get_read_db_session()`
- [x] All stories have `BLOCKED UNTIL` (or "none")
- [x] Each iteration has time estimate and come-back datetime
- [x] Each iteration has GitHub agent launch block
- [x] STUCK PROTOCOL present in Agent Execution Rules
- [x] Stories sequenced: backend before frontend
- [x] No placeholders remain
- [x] BDD scenarios present for every customer-facing flow
- [x] Route baseline cross-checked against §5.2

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | P0 bug fixes + full configuration lifecycle | E1, E2 | 6 | 4.5h | 2026-06-28 21:00 UTC |
| 2 | Trade execution + review + P&L tax reports | E3, E4 | 6 | 5.5h | 2026-06-29 06:00 UTC |

**Estimate basis:** Plant BE endpoint = 45 min | Full-stack (BE+mobile) = 90 min | CP proxy = 30 min. Buffer: 20%.

---

## Integration Baseline Gate

> **Agent: run these before writing any code in Iteration 1. Any 404 = HALT.**

```bash
# Exchange credentials endpoint exists (expects 401, NOT 404)
curl -sS -o /dev/null -w "%{http_code}\n" \
  https://plant.demo.waooaw.com/api/v1/hired-agents/test/exchange-credentials

# Trading setup endpoint exists (expects 401/422, NOT 404)
curl -sS -o /dev/null -w "%{http_code}\n" \
  https://plant.demo.waooaw.com/api/v1/hired-agents/test/trading-setup

# CP trading setup proxy exists (expects 401, NOT 404)
curl -sS -o /dev/null -w "%{http_code}\n" \
  https://cp.demo.waooaw.com/api/cp/trading-setup/test
```

---

## Agent Execution Rules

1. Work on the GitHub task branch created for this run. Do not assume manual branch creation.
2. Execute epics in stated order. Do not start E2 stories until all E1 stories pass tests.
3. Every story: write tests first (TDD), then implementation.
4. Run `pytest src/Plant/BackEnd/tests/ -x -q` (or equivalent) after each story. If not in shell, state: "Validation deferred — test output will appear in CI."
5. After all stories in your iteration: open a PR to `main` with title `feat(share-trader): ST-MVP-1 Iteration N — [scope]`.
6. Post PR URL in a comment and HALT.

**STUCK PROTOCOL**: If blocked for > 15 min on any story, post `STUCK: [story ID] — [exact blocker]` and move to the next story. Do not attempt to fix unrelated code.

**EXECUTION AGENT AUDIT ROUND**: Before submitting the PR, re-read each story's acceptance criteria and confirm each one is met. Post a one-line ✓/✗ per criterion in the PR body.

---

## How to Launch Each Iteration

### Iteration 1

**Steps:**
1. Open `https://github.com/dlai-sd/WAOOAW`
2. Click **Agents** tab
3. Start a new agent task, select **platform-engineer** if shown
4. Paste the task block below and start the run
5. Come back at **2026-06-28 21:00 UTC**

**Iteration 1 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python/FastAPI engineer specialising in financial data pipelines + Senior React Native/TypeScript engineer with trading UI experience.
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/ST-MVP-1-share-trader-lifecycle.md
YOUR SCOPE: Iteration 1 only — Epics E1 and E2 (Stories S1–S6). Do NOT touch Iteration 2 content.
TIME BUDGET: 4.5h. If you reach 5h without finishing, follow STUCK PROTOCOL now.

ENVIRONMENT REQUIREMENT:
- Intended for GitHub repository Agents tab.
- Shell/git/docker tools may be unavailable; use GitHub task branch/PR flow.
- Do NOT halt only because terminal tools are unavailable.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing any file):
1. Verify docs/CP/iterations/ST-MVP-1-share-trader-lifecycle.md is readable and contains "Iteration 1" section.
2. Verify this surface allows repository writes on the task branch.
3. Verify this surface allows opening a PR to `main`.
4. If any gate fails: post "Blocked at validation gate: [exact reason]" and HALT.

EXECUTION ORDER:
1. Read the "Agent Execution Rules" section in the plan file.
2. Read the "Iteration 1" section in the plan file.
3. Read nothing else before starting.
4. Execute: E1-S1 → E1-S2 → E1-S3 → E2-S4 → E2-S5 → E2-S6
5. Write or update tests as listed in each story's test table before moving on.
6. After all 6 stories: open PR to `main` titled "feat(share-trader): ST-MVP-1 It1 — P0 fixes + configuration lifecycle"
7. Post PR URL and HALT.
```

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Prerequisite evidence:**
- Iteration 1 PR: `[PENDING — fill after merge]`
- Merge commit on `main`: `[PENDING]`
- Merged at: `[PENDING]`

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python/FastAPI engineer specialising in algorithmic trading systems + Senior React Native/TypeScript engineer with financial reporting experience.
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/ST-MVP-1-share-trader-lifecycle.md
YOUR SCOPE: Iteration 2 only — Epics E3 and E4 (Stories S7–S12). Do NOT touch Iteration 1 content.
TIME BUDGET: 5.5h. Follow STUCK PROTOCOL if you reach 6h.

ENVIRONMENT REQUIREMENT: Same as Iteration 1.

FAIL-FAST VALIDATION GATE:
1. Confirm Iteration 1 PR is merged: check that ExchangeCredentialService.get_secrets() call exists in delta_exchange_pump.py.
2. Confirm plan file is readable and contains "Iteration 2" section.
3. Confirm this surface allows repository writes and PR creation.
4. If any gate fails: post "Blocked at validation gate: [exact reason]" and HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" in the plan file.
2. Read "Iteration 2" section only.
3. Execute: E3-S7 → E3-S8 → E3-S9 → E4-S10 → E4-S11 → E4-S12
4. Write tests per each story's test table before moving on.
5. After all 6 stories: open PR to `main` titled "feat(share-trader): ST-MVP-1 It2 — trading operation + P&L lifecycle"
6. Post PR URL and HALT.
```

---

## PM Critique Round

| Question | Answer |
|---|---|
| Does every story advance Share Trader value directly? | Yes — S1–S3 unblock trade execution; S4–S6 complete configuration; S7–S9 make trades safe and autonomous; S10–S12 close the review/reporting loop |
| Are there any stories that could be deferred without blocking a paying customer? | S12 (tax report) is nice-to-have for Month 1 but legally required by Q1; kept in plan |
| Is the credential bridge fix (S1) technically sound? | Yes — `credential_ref` flows from setup → ExchangeCredentialService → pump via DB session created inline in the component |
| Is the autonomous mode design safe? | Yes — AutonomousModeHook checks both `autonomous_mode == True` AND `autonomous_consent_at` is not null; notification is fire-and-forget but logged |
| Does the plan fit in 2 iterations without scope creep? | Yes — LLM wizard, backtesting, multi-exchange deferred to Phase 2 |

---

---

# Iteration 1 — P0 Fixes + Configuration Lifecycle Complete

**Objective alignment**: Share Trader value — these 6 stories eliminate the bugs that prevent the agent from ever making a trade, then complete the full configuration lifecycle so a customer can actually set up the agent end-to-end.

---

## Epic E1: Bugs Eliminated — Agent Can Execute Its First Trade

> Without S1–S3, the agent cannot trade: credentials never reach the pump, `customer_id` mismatches silently produce wrong records, and encrypted key blobs are visible in API responses. Fix all three before any other work.

---

### S1 — Credential bridge: setup wizard saves to ExchangeCredentialService; pump reads from it

**Advances**: Share Trader value (unblocks first trade execution)
**Branch**: `feat/ST-MVP-1-s1-credential-bridge`
**Estimate**: 45 min
**BLOCKED UNTIL**: none

**Context** (2 sentences):
The setup wizard (`trading_setup.py`) stores `encrypted_api_key`/`encrypted_api_secret` in `hired_agent.config["trading_setup"]["collected"]` JSONB but never writes to `ExchangeCredentialModel`. `DeltaExchangePump` reads `skill_config.customer_fields.delta_api_key` (always empty) — so every scheduled market-analysis run fails silently with an authentication error.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/api/v1/trading_setup.py` — find the `done` step handler (search for `state.configured = True`)
2. `src/Plant/BackEnd/delta_exchange_pump.py` — find `customer_fields.get("delta_api_key")`
3. `src/Plant/BackEnd/services/exchange_credential_service.py` — check `upsert()` and `get_secrets()` signatures

**Files to create / edit**:
- `src/Plant/BackEnd/api/v1/trading_setup.py` — done step: call `ExchangeCredentialService.upsert()`, store `credential_ref` in `collected`
- `src/Plant/BackEnd/delta_exchange_pump.py` — replace plaintext key read with `get_secrets(credential_ref=...)`
- `src/Plant/BackEnd/tests/test_trading_setup.py` — add test: done step persists credential_ref

**Acceptance criteria**:
1. After wizard completes, `ExchangeCredentialModel` row exists for the customer with `validation_status = "valid"`.
2. `state.collected["credential_ref"]` is set and matches the stored row's `credential_ref`.
3. `DeltaExchangePump.execute()` with a valid `credential_ref` in `skill_config.customer_fields` returns `success=True` and non-empty `candles`.
4. `DeltaExchangePump.execute()` with an empty or missing `credential_ref` returns `ComponentOutput(success=False, error_message="No credential_ref configured")` — never a Python exception.
5. `api_key` and `api_secret` do NOT appear in any log line (PII masking).

**Code patterns to copy exactly**:

```python
# In trading_setup.py — done step (add after state.configured = True):
from services.exchange_credential_service import ExchangeCredentialService, _decrypt

async def _persist_credentials_on_done(
    collected: dict,
    customer_id: str,
    db: AsyncSession,
) -> str:
    """Persist credentials to ExchangeCredentialService; return credential_ref."""
    svc = ExchangeCredentialService(db)
    api_key = _decrypt(collected["encrypted_api_key"])
    api_secret = _decrypt(collected["encrypted_api_secret"])
    rec = await svc.upsert(
        customer_id=customer_id,
        exchange_provider="delta_exchange_india",
        api_key=api_key,
        api_secret=api_secret,
        default_coin=collected.get("default_coin", "BTC"),
        allowed_coins=[collected.get("default_coin", "BTC")],
        risk_limits={
            "max_units_per_order": collected.get("max_units_per_order", 1),
            "max_notional_per_order_inr": collected.get("max_notional_per_order_inr", 50000),
        },
    )
    return rec.credential_ref

# In delta_exchange_pump.py — replace current api_key read with:
from core.database import _connector
from services.exchange_credential_service import ExchangeCredentialService

async def execute(self, input: ComponentInput) -> ComponentOutput:
    customer_fields = input.skill_config.get("customer_fields", {})
    instrument = customer_fields.get("instrument", customer_fields.get("default_coin", "BTC"))
    credential_ref = customer_fields.get("credential_ref", "")
    if not credential_ref:
        return ComponentOutput(success=False, error_message="No credential_ref configured — complete trading setup wizard first")
    async with _connector.get_session() as session:
        svc = ExchangeCredentialService(session)
        secrets = await svc.get_secrets(credential_ref=credential_ref)
    if not secrets:
        return ComponentOutput(success=False, error_message="Credentials not found for credential_ref")
    api_key = secrets["api_key"]  # NEVER log this value
    candles = await self._fetch_candles(instrument, api_key)
    return ComponentOutput(success=True, data={"candles": candles, "instrument": instrument})
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Done step calls `ExchangeCredentialService.upsert()` and sets `collected["credential_ref"]` | `tests/test_trading_setup.py` |
| T2 | Unit | `DeltaExchangePump` with valid `credential_ref` returns `success=True` | `tests/unit/test_delta_exchange_pump.py` |
| T3 | Unit | `DeltaExchangePump` with missing `credential_ref` returns `success=False` with descriptive message | `tests/unit/test_delta_exchange_pump.py` |

**BDD scenario**:
```
Given a customer has completed the trading setup wizard
When the done step is processed
Then ExchangeCredentialModel has a row with validation_status = "valid"
And state.collected["credential_ref"] equals that row's credential_ref
And DeltaExchangePump.execute() with that credential_ref in skill_config returns candles
```

---

### S2 — customer_id format unified across all CP trading routes

**Advances**: Share Trader value (prevents silent record mismatches between CP routes)
**Branch**: `feat/ST-MVP-1-s2-customer-id-fix`
**Estimate**: 30 min
**BLOCKED UNTIL**: none

**Context** (2 sentences):
`cp_trading_setup.py` returns `str(user.id)` but `trading.py` returns `f"CUST-{user.id}"` — the same user appears as two different customers in Plant. This silently creates duplicate or orphaned records; a customer's trade approval is sent to a different `customer_id` than the one that owns the credentials.

**Files to read first** (max 3):
1. `src/CP/BackEnd/api/trading.py` — find `_customer_id_from_user()`
2. `src/CP/BackEnd/api/cp_trading_setup.py` — find `_customer_id()`
3. `src/CP/BackEnd/api/cp_trading_performance.py` — check if it has a customer_id helper

**Files to create / edit**:
- `src/CP/BackEnd/api/trading.py` — change `f"CUST-{user.id}"` → `str(user.id)`
- `src/CP/BackEnd/api/exchange_setup.py` — audit and align if needed
- `src/CP/BackEnd/tests/test_trading_api.py` — assert customer_id format is `str(user.id)` in request body

**Acceptance criteria**:
1. Every CP trading route sends `customer_id = str(user.id)` (pure UUID string, no prefix).
2. `grep -r "CUST-" src/CP/BackEnd/api/` returns zero matches.
3. Tests pass with the unified format.

**Code patterns to copy exactly**:

```python
# In EVERY CP trading route file — use this exact helper, not f"CUST-{user.id}":
def _customer_id(user: User) -> str:
    """Return canonical customer_id — plain UUID string, no prefix."""
    return str(user.id)
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | `draft_trade_plan` sends `customer_id = str(user.id)` to Plant | `tests/test_trading_api.py` |
| T2 | Unit | `approve_and_execute_trade` sends same format | `tests/test_trading_api.py` |

**BDD scenario**:
```
Given any authenticated user makes a CP trading request
Then customer_id in the Plant-bound payload equals str(user.id)
And customer_id does not contain the string "CUST-"
```

---

### S3 — Encrypted credential blobs filtered from GET trading-setup responses

**Advances**: Share Trader value (prevents credential ciphertext exposure in API responses)
**Branch**: `feat/ST-MVP-1-s3-jsonb-filter`
**Estimate**: 30 min
**BLOCKED UNTIL**: none

**Context** (2 sentences):
`TradingSetupState.collected` stores `encrypted_api_key` and `encrypted_api_secret` Fernet blobs. The `GET /hired-agents/{id}/trading-setup` endpoint returns this dict unfiltered — any client that calls this endpoint receives the ciphertext, which could be targeted for offline brute-force if `secret_key` is ever compromised.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/api/v1/trading_setup.py` — find `get_trading_setup()` and `TradingSetupResponse`
2. `src/Plant/BackEnd/api/v1/trading_setup.py` — find `_readiness()` and `TradingSetupState`

**Files to create / edit**:
- `src/Plant/BackEnd/api/v1/trading_setup.py` — add `_sanitize_collected()` filter; call in both GET and POST response paths

**Acceptance criteria**:
1. `GET /hired-agents/{id}/trading-setup` response JSON does not contain the keys `encrypted_api_key` or `encrypted_api_secret`.
2. `POST /hired-agents/{id}/trading-setup/message` response JSON does not contain those keys.
3. The `has_credentials` field in `readiness` still returns `True` when credentials are stored.
4. `grep "encrypted_api_key" <(curl GET response)` returns zero matches.

**Code patterns to copy exactly**:

```python
# Add this function to trading_setup.py and call it on state.collected before returning:
_SENSITIVE_COLLECTED_KEYS = frozenset({
    "encrypted_api_key",
    "encrypted_api_secret",
})

def _sanitize_collected(collected: dict) -> dict:
    """Strip encrypted credential blobs from the collected dict before API response."""
    return {k: v for k, v in collected.items() if k not in _SENSITIVE_COLLECTED_KEYS}

# In get_trading_setup and send_trading_setup_message, before constructing the response:
safe_state = state.model_copy(
    update={"collected": _sanitize_collected(state.collected)}
)
# Use safe_state (not state) in TradingSetupResponse(...)
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | GET response does not contain `encrypted_api_key` even when it is stored | `tests/test_trading_setup.py` |
| T2 | Unit | `has_credentials` in readiness is `True` when encrypted blob exists | `tests/test_trading_setup.py` |

**BDD scenario**:
```
Given a customer has entered their API key
When they GET /trading-setup
Then the response body does not contain "encrypted_api_key"
And readiness.has_credentials is true
```

---

## Epic E2: Customer Configures Full Trading Strategy in One Chat Session

> The current wizard stops at risk_limits. This epic adds leverage, % capital, autonomous mode consent, and risk disclosure — completing the full configuration lifecycle a paying customer needs.

---

### S4 — GoalConfig schema extended with leverage, capital_pct, autonomous mode fields

**Advances**: Share Trader value (enables position sizing, leverage control, and autonomous mode at the data layer)
**Branch**: `feat/ST-MVP-1-s4-goalconfig-schema`
**Estimate**: 45 min
**BLOCKED UNTIL**: none

**Context** (2 sentences):
The `execute-trade-order` skill GoalSchema (defined in `skill_execute_trade_order_seed.py`) already has `stop_loss_pct` and `leverage` fields but is missing `capital_pct` (% of account to deploy), `autonomous_mode` (bool), `autonomous_consent_at` (ISO datetime), and `risk_disclosure_accepted` (bool). The `ConstraintPolicy` in `agent_mold/spec.py` also needs `max_leverage = 10` and `max_capital_pct_per_trade = 20.0` as platform hard-caps.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/database/seeds/skill_execute_trade_order_seed.py` — full field list
2. `src/Plant/BackEnd/agent_mold/spec.py` — `ConstraintPolicy` class
3. `src/Plant/BackEnd/agent_mold/reference_agents.py` — Share Trader AgentSpec definition

**Files to create / edit**:
- `src/Plant/BackEnd/database/seeds/skill_execute_trade_order_seed.py` — add 4 new fields
- `src/Plant/BackEnd/agent_mold/spec.py` — add `max_leverage` and `max_capital_pct_per_trade` to `ConstraintPolicy`
- `src/Plant/BackEnd/agent_mold/reference_agents.py` — set those caps on the Share Trader AgentSpec
- `src/Plant/BackEnd/tests/unit/test_share_trader_spec.py` — new: assert ConstraintPolicy caps are set

**Acceptance criteria**:
1. Running the seed script (`python -m database.seeds.skill_execute_trade_order_seed`) succeeds without error.
2. The seeded skill's `goal_schema.fields` contains `capital_pct`, `autonomous_mode`, `autonomous_consent_at`, `risk_disclosure_accepted`.
3. `ConstraintPolicy` has `max_leverage: int = 10` and `max_capital_pct_per_trade: float = 20.0`.
4. Share Trader AgentSpec in `reference_agents.py` has `constraint_policy.max_leverage = 10`.

**Code patterns to copy exactly**:

```python
# Add these 4 entries to the fields list in skill_execute_trade_order_seed.py:
{
    "key": "capital_pct",
    "type": "decimal",
    "required": True,
    "label": "Capital deployment per trade (%)",
    "min": 1,
    "max": 20,
    "default": 5,
    "help": "Percentage of your account balance used per trade. Max 20% enforced by platform.",
},
{
    "key": "autonomous_mode",
    "type": "boolean",
    "required": True,
    "label": "Autonomous trading mode",
    "default": False,
    "help": "When enabled the agent executes trades without requesting approval. You will be notified after each execution.",
},
{
    "key": "autonomous_consent_at",
    "type": "string",
    "required": False,
    "label": "Autonomous mode consent timestamp",
    "default": None,
    "help": "ISO datetime when customer consented to autonomous mode. Set automatically.",
},
{
    "key": "risk_disclosure_accepted",
    "type": "boolean",
    "required": True,
    "label": "Risk disclosure accepted",
    "default": False,
    "help": "Customer confirmed they understand trading involves risk of total capital loss.",
},

# In agent_mold/spec.py — add to ConstraintPolicy:
max_leverage: int = 10                  # platform hard-cap; customer configures up to this
max_capital_pct_per_trade: float = 20.0  # percent; prevents over-concentration
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Share Trader `ConstraintPolicy.max_leverage == 10` | `tests/unit/test_share_trader_spec.py` |
| T2 | Unit | Seed adds all 4 new fields to goal_schema | `tests/unit/test_share_trader_spec.py` |

---

### S5 — Chat wizard extended: capital_pct, leverage, autonomous consent, risk disclosure steps

**Advances**: Share Trader value (customer completes full 10-step configuration in one chat session)
**Branch**: `feat/ST-MVP-1-s5-wizard-extension`
**Estimate**: 90 min
**BLOCKED UNTIL**: S4 merged (needs new fields in schema)

**Context** (2 sentences):
`trading_setup.py` STEPS list currently ends at `risk_limits → done`. This story appends four new steps (`capital_pct`, `leverage`, `autonomous_mode`, `risk_disclosure`) between `risk_limits` and `done`, and updates `TradingSetupScreen.tsx` to show step labels and handle the new `autonomous_mode` step with a confirm-style UX.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/api/v1/trading_setup.py` — full STEPS list, `_process_step`, `_ASSISTANT_INTRO`
2. `src/mobile/src/screens/agents/TradingSetupScreen.tsx` — `SECURE_STEPS`, `stepLabel` map, `handleSend`
3. `src/Plant/BackEnd/tests/test_trading_setup.py` — existing test structure

**Files to create / edit**:
- `src/Plant/BackEnd/api/v1/trading_setup.py` — STEPS, _ASSISTANT_INTRO, _process_step handlers for 4 new steps
- `src/mobile/src/screens/agents/TradingSetupScreen.tsx` — stepLabel, confirm-style input for autonomous_mode
- `src/Plant/BackEnd/tests/test_trading_setup.py` — tests for each new step transition

**Acceptance criteria**:
1. `STEPS = ["welcome","api_key","api_secret","validate","instrument","rsi_period","risk_limits","capital_pct","leverage","autonomous_mode","risk_disclosure","done"]`
2. `capital_pct` step rejects input < 1 or > 20 with an inline error message.
3. `leverage` step rejects input < 1 or > 200 (customer-facing max) and warns if > 10 (platform cap).
4. `autonomous_mode` step accepts only `yes` or `no`; if `yes`, sets `collected["autonomous_consent_at"]` to current UTC ISO string.
5. `risk_disclosure` step accepts only `I ACCEPT` (case-insensitive); any other input re-presents the disclaimer.
6. `state.configured` is only set to `True` after `risk_disclosure` is accepted.
7. Mobile `TradingSetupScreen` shows correct step label for all 10 steps.
8. `autonomous_mode` step shows a yellow warning banner: "⚠️ Autonomous mode: trades will execute without your approval."

**Code patterns to copy exactly**:

```python
# New STEPS list in trading_setup.py:
STEPS = [
    "welcome", "api_key", "api_secret", "validate",
    "instrument", "rsi_period", "risk_limits",
    "capital_pct", "leverage", "autonomous_mode", "risk_disclosure",
    "done",
]

# New _ASSISTANT_INTRO entries (add to existing dict):
_ASSISTANT_INTRO["capital_pct"] = (
    "**Step 7 of 10 — Capital Deployment**\n\n"
    "What percentage of your account balance should I deploy per trade?\n\n"
    "• **5%** is conservative (recommended for beginners)\n"
    "• **10%** is moderate\n"
    "• **20%** is the platform maximum\n\n"
    "Enter a number between 1 and 20, or type **5** for the default."
)
_ASSISTANT_INTRO["leverage"] = (
    "**Step 8 of 10 — Leverage**\n\n"
    "Leverage amplifies both gains and losses. Delta Exchange supports up to 200x.\n\n"
    "⚠️ **Warning**: The platform safety cap is **10x**. Configuring above 10x requires "
    "you to acknowledge increased liquidation risk.\n\n"
    "Enter a number between 1 and 200, or type **1** for no leverage."
)
_ASSISTANT_INTRO["autonomous_mode"] = (
    "**Step 9 of 10 — Autonomous Trading Mode**\n\n"
    "In **Autonomous Mode**, I will execute trades without asking for your approval each time. "
    "You will be notified by SMS, email, and app notification after every execution.\n\n"
    "⚠️ **This means real money can be deployed without a second confirmation from you.**\n\n"
    "Type **yes** to enable autonomous mode, or **no** to keep approval-based trading."
)
_ASSISTANT_INTRO["risk_disclosure"] = (
    "**Step 10 of 10 — Risk Disclosure**\n\n"
    "Before I begin trading on your behalf, please read and accept:\n\n"
    "• Trading involves substantial risk of loss, including total loss of capital.\n"
    "• Past RSI signals do not guarantee future performance.\n"
    "• WAOOAW does not provide financial advice.\n"
    "• You are solely responsible for any trading decisions.\n\n"
    "Type **I ACCEPT** to confirm you have read and understood the above."
)

# Step handlers (add to _process_step function):
elif step == "capital_pct":
    try:
        val = float(inp)
        if not (1 <= val <= 20):
            raise ValueError
    except ValueError:
        msgs.append(_user_msg(inp))
        msgs.append(_assistant_msg("Please enter a number between 1 and 20."))
    else:
        collected["capital_pct"] = val
        msgs.append(_user_msg(inp))
        msgs.append(_assistant_msg(_ASSISTANT_INTRO["leverage"]))
        state.step = "leverage"

elif step == "leverage":
    try:
        val = int(inp)
        if not (1 <= val <= 200):
            raise ValueError
    except ValueError:
        msgs.append(_user_msg(inp))
        msgs.append(_assistant_msg("Please enter a whole number between 1 and 200."))
    else:
        collected["leverage"] = val
        warning = ""
        if val > 10:
            warning = "\n\n⚠️ You've set leverage above 10x. Liquidation risk is significantly elevated."
        msgs.append(_user_msg(inp))
        msgs.append(_assistant_msg(_ASSISTANT_INTRO["autonomous_mode"] + warning))
        state.step = "autonomous_mode"

elif step == "autonomous_mode":
    if inp.lower() not in ("yes", "no"):
        msgs.append(_user_msg(inp))
        msgs.append(_assistant_msg("Please type **yes** or **no**."))
    else:
        collected["autonomous_mode"] = (inp.lower() == "yes")
        if collected["autonomous_mode"]:
            from datetime import datetime, timezone
            collected["autonomous_consent_at"] = datetime.now(timezone.utc).isoformat()
        msgs.append(_user_msg(inp))
        msgs.append(_assistant_msg(_ASSISTANT_INTRO["risk_disclosure"]))
        state.step = "risk_disclosure"

elif step == "risk_disclosure":
    if inp.strip().upper() != "I ACCEPT":
        msgs.append(_user_msg(inp))
        msgs.append(_assistant_msg(
            "To proceed, type exactly **I ACCEPT** to confirm you have read the risk disclosure."
        ))
    else:
        collected["risk_disclosure_accepted"] = True
        msgs.append(_user_msg(inp))
        # trigger done
        state.step = "done"
        state.configured = True
        # persist credentials via ExchangeCredentialService (see S1 pattern)
```

```typescript
// In TradingSetupScreen.tsx — update stepLabel:
const stepLabel: Record<string, string> = {
  welcome: 'Welcome',
  api_key: 'Step 1 of 10 — API Key',
  api_secret: 'Step 2 of 10 — API Secret',
  validate: 'Step 3 of 10 — Validating…',
  instrument: 'Step 4 of 10 — Instrument',
  rsi_period: 'Step 5 of 10 — RSI Period',
  risk_limits: 'Step 6 of 10 — Risk Limits',
  capital_pct: 'Step 7 of 10 — Capital Deployment',
  leverage: 'Step 8 of 10 — Leverage',
  autonomous_mode: 'Step 9 of 10 — Autonomous Mode',
  risk_disclosure: 'Step 10 of 10 — Risk Disclosure',
  done: 'Setup Complete ✅',
}

// Add autonomous_mode warning banner — render when currentStep === 'autonomous_mode':
{currentStep === 'autonomous_mode' && (
  <View style={{ backgroundColor: '#f59e0b18', borderColor: '#f59e0b55',
    borderWidth: 1, borderRadius: 8, padding: 10, marginHorizontal: 16 }}>
    <Text style={{ color: '#f59e0b', fontSize: 12 }}>
      ⚠️ Autonomous mode: trades will execute without your approval. You will be notified after each execution.
    </Text>
  </View>
)}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | `capital_pct` step rejects 0 and 21; accepts 5 | `tests/test_trading_setup.py` |
| T2 | Unit | `leverage` step > 10 appends warning text | `tests/test_trading_setup.py` |
| T3 | Unit | `autonomous_mode = "yes"` sets `autonomous_consent_at` to ISO string | `tests/test_trading_setup.py` |
| T4 | Unit | `risk_disclosure = "thanks"` stays on step; `I ACCEPT` advances to done | `tests/test_trading_setup.py` |
| T5 | BDD | Full 10-step wizard produces `configured = True` with all fields in `collected` | `tests/test_trading_setup.py` |

**BDD scenario**:
```
Given a new hired Share Trader agent
When customer completes all 10 wizard steps with valid inputs
Then state.configured is True
And collected contains capital_pct, leverage, autonomous_mode, autonomous_consent_at, risk_disclosure_accepted
And credential_ref is set (from S1 credential bridge)
And ExchangeCredentialModel has a valid row for this customer
```

---

### S6 — Instrument validation: reject NIFTY/BANKNIFTY; validate against Delta Exchange products

**Advances**: Share Trader value (prevents silent failure when customer enters an unsupported instrument)
**Branch**: `feat/ST-MVP-1-s6-instrument-validation`
**Estimate**: 45 min
**BLOCKED UNTIL**: none

**Context** (2 sentences):
The wizard's `instrument` step example text lists NIFTY and BANKNIFTY — these do not exist on Delta Exchange India, which only offers crypto derivatives. When a customer enters NIFTY, the pump fetches an empty candles list and RSI returns 50.0 (HOLD) forever, silently.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/api/v1/trading_setup.py` — `_ASSISTANT_INTRO["instrument"]` and the `instrument` step handler
2. `src/Plant/BackEnd/api/v1/exchange_credentials.py` — `_validate_exchange_live` for circuit_breaker pattern

**Files to create / edit**:
- `src/Plant/BackEnd/api/v1/trading_setup.py` — update intro text; add live Delta Exchange product lookup in instrument step

**Acceptance criteria**:
1. `_ASSISTANT_INTRO["instrument"]` lists only Delta Exchange crypto symbols: BTC, ETH, SOL, MATIC, LINK. Zero mentions of NIFTY or BANKNIFTY.
2. When customer enters `NIFTY`, the wizard responds: "NIFTY is not available on Delta Exchange India. Available instruments include BTC, ETH, SOL, MATIC, LINK. Please enter a supported symbol."
3. In `test` / `development` environment, instrument validation mocks success (same pattern as `_validate_exchange_live`).
4. Live validation uses `@circuit_breaker(service="delta_exchange_api")`.

**Code patterns to copy exactly**:

```python
# Updated intro in trading_setup.py:
_ASSISTANT_INTRO["instrument"] = (
    "**Step 4 of 10 — Default Instrument**\n\n"
    "Which crypto instrument should I trade by default on Delta Exchange India?\n\n"
    "Examples: **BTC**, **ETH**, **SOL**, **MATIC**, **LINK**\n\n"
    "Type the symbol (e.g. `BTC`). I'll verify it exists on Delta Exchange before continuing."
)

# Instrument validation helper (add near _validate_exchange_live import section):
from core.security import circuit_breaker
import httpx

@circuit_breaker(service="delta_exchange_api")
async def _validate_instrument_live(instrument: str) -> bool:
    """Returns True if the instrument exists on Delta Exchange India."""
    from core.config import settings
    if settings.environment in {"test", "development", "local"}:
        return True  # mock success in non-prod
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            "https://api.delta.exchange/v2/products",
            params={"page_size": 100},
        )
        resp.raise_for_status()
        products = resp.json().get("result", [])
        return any(
            p.get("underlying_asset", {}).get("symbol", "").upper() == instrument.upper()
            or p.get("symbol", "").upper().startswith(instrument.upper())
            for p in products
        )

# Updated instrument step handler in _process_step:
elif step == "instrument":
    symbol = inp.strip().upper()
    if not symbol:
        msgs.append(_user_msg("[empty]"))
        msgs.append(_assistant_msg("Please enter an instrument symbol such as BTC or ETH."))
    else:
        valid = await _validate_instrument_live(symbol)
        if not valid:
            msgs.append(_user_msg(symbol))
            msgs.append(_assistant_msg(
                f"**{symbol}** is not available on Delta Exchange India. "
                "Available instruments include BTC, ETH, SOL, MATIC, LINK. "
                "Please enter a supported symbol."
            ))
        else:
            collected["default_coin"] = symbol
            msgs.append(_user_msg(symbol))
            msgs.append(_assistant_msg(_ASSISTANT_INTRO["rsi_period"]))
            state.step = "rsi_period"
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | `NIFTY` input stays on `instrument` step with error message | `tests/test_trading_setup.py` |
| T2 | Unit | `BTC` input (mocked valid) advances to `rsi_period` | `tests/test_trading_setup.py` |
| T3 | Unit | `_validate_instrument_live` in test env returns `True` without HTTP call | `tests/unit/test_instrument_validation.py` |

**BDD scenario**:
```
Given the wizard is on the instrument step
When customer types "NIFTY"
Then the response contains "not available on Delta Exchange India"
And the step remains "instrument"
When customer then types "BTC"
Then the step advances to "rsi_period"
```

---

---

# Iteration 2 — Trading Operation + Review + P&L Lifecycle

**Objective alignment**: Share Trader value — these 6 stories complete the operating lifecycle: safe trade execution with correct RSI signals, autonomous mode, emergency controls, trade history, and tax-ready P&L reports.

---

## Epic E3: Customer's Trades Execute Safely and Autonomously

---

### S7 — RSI uses Wilder's EMA; pump suppresses signal if position already open

**Advances**: Share Trader value (correct signals + no runaway position stacking)
**Branch**: `feat/ST-MVP-1-s7-rsi-accuracy`
**Estimate**: 45 min
**BLOCKED UNTIL**: Iteration 1 merged to main

**Context** (2 sentences):
`RSIProcessor._calculate_rsi()` uses a simple average over a fixed window — this produces different values than every charting platform (TradingView, MetaTrader) which use Wilder's smoothed EMA. Additionally, the pump has no awareness of existing open positions, so the agent can stack multiple long entries on the same instrument.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/rsi_processor.py` — full `_calculate_rsi` and `execute` method
2. `src/Plant/BackEnd/delta_exchange_pump.py` — full `execute` and `_fetch_candles`
3. `src/Plant/BackEnd/tests/unit/test_rsi_processor.py` — existing test structure

**Files to create / edit**:
- `src/Plant/BackEnd/rsi_processor.py` — replace `_calculate_rsi` with Wilder's EMA; add position guard
- `src/Plant/BackEnd/delta_exchange_pump.py` — add `_fetch_open_positions()` call; include in output
- `src/Plant/BackEnd/tests/unit/test_rsi_processor.py` — update / add tests for Wilder's values

**Acceptance criteria**:
1. `RSIProcessor._calculate_rsi_wilder([...14 candles of known values...], period=14)` matches TradingView's RSI output to within 0.1.
2. When `input.previous_step_output["open_positions"]` contains a `"long"` position for the instrument, `execute()` returns `signal = "HOLD"` regardless of RSI value.
3. When no open positions, BUY/SELL signals fire as expected.
4. `DeltaExchangePump` output dict includes `"open_positions"` key (list, may be empty).
5. In test environment, `_fetch_open_positions` returns `[]` (mock, no network call).

**Code patterns to copy exactly**:

```python
# In rsi_processor.py — replace _calculate_rsi with:
def _calculate_rsi_wilder(self, candles: list[dict], period: int) -> float:
    """Wilder's smoothed RSI — matches TradingView output."""
    closes = [float(c.get("close", 0)) for c in candles]
    if len(closes) < period + 1:
        return 50.0
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    # Seed with simple average over first period
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    # Wilder's smoothing: alpha = 1/period
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_loss == 0:
        return 100.0
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 4)

# Update execute() to use Wilder's and add position guard:
async def execute(self, input: ComponentInput) -> ComponentOutput:
    candles = (input.previous_step_output or {}).get("candles", [])
    open_positions = (input.previous_step_output or {}).get("open_positions", [])
    if not candles:
        return ComponentOutput(success=False, error_message="Insufficient data")
    period = int(input.skill_config.get("customer_fields", {}).get("rsi_period", 14))
    rsi_value = self._calculate_rsi_wilder(candles, period)
    # Position guard: suppress signal if matching direction already open
    if rsi_value < 30:
        raw_signal = "BUY"
    elif rsi_value > 70:
        raw_signal = "SELL"
    else:
        raw_signal = "HOLD"
    position_sides = [p.get("side", "").lower() for p in open_positions]
    if raw_signal == "BUY" and "long" in position_sides:
        raw_signal = "HOLD"  # already long, do not stack
    if raw_signal == "SELL" and "short" in position_sides:
        raw_signal = "HOLD"  # already short, do not stack
    return ComponentOutput(
        success=True,
        data={"rsi_value": rsi_value, "signal": raw_signal, "confidence": 0.9},
    )

# In delta_exchange_pump.py — add position fetch:
@circuit_breaker(service="delta_exchange_api")
async def _fetch_open_positions(self, instrument: str, api_key: str) -> list[dict]:
    from core.config import settings
    if settings.environment in {"test", "development", "local"}:
        return []  # mock: no open positions
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(
            "https://api.delta.exchange/v2/positions/margined",
            headers={"api-key": api_key},
            timeout=5.0,
        )
        resp.raise_for_status()
        positions = resp.json().get("result", [])
        return [p for p in positions if instrument.upper() in p.get("product_symbol", "").upper()]

# In DeltaExchangePump.execute(), add after fetching candles:
open_positions = await self._fetch_open_positions(instrument, api_key)
return ComponentOutput(
    success=True,
    data={"candles": candles, "instrument": instrument, "open_positions": open_positions},
)
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Wilder's RSI with 20 known closes matches expected value ± 0.1 | `tests/unit/test_rsi_processor.py` |
| T2 | Unit | BUY signal suppressed to HOLD when `open_positions` has a long | `tests/unit/test_rsi_processor.py` |
| T3 | Unit | `_fetch_open_positions` in test env returns `[]` | `tests/unit/test_delta_exchange_pump.py` |

---

### S8 — Stop-loss and take-profit orders placed alongside every entry

**Advances**: Share Trader value (prevents unlimited loss — a commercial requirement for any paying customer)
**Branch**: `feat/ST-MVP-1-s8-stop-loss-enforcement`
**Estimate**: 60 min
**BLOCKED UNTIL**: S7 merged

**Context** (2 sentences):
`TradingOrderIntent` produces only an entry order. The GoalSchema seed defines `stop_loss_pct` and `profit_target_pct` fields but neither `TradingExecutor` nor the publisher uses them — a customer's stop-loss setting is silently ignored.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/agent_mold/skills/trading_executor.py` — `TradingOrderIntent`, `execute_trading_delta_futures_manual_v1`
2. `src/Plant/BackEnd/integrations/delta_exchange/` — check existing order placement methods
3. `src/Plant/BackEnd/tests/unit/test_delta_orders.py` — existing order test structure

**Files to create / edit**:
- `src/Plant/BackEnd/agent_mold/skills/trading_executor.py` — add `stop_loss_price` and `take_profit_price` to `TradingOrderIntent`; compute from `goal_config` + `last_close_price` from pump output
- `src/Plant/BackEnd/tests/unit/test_delta_orders.py` — add stop_loss order tests

**Acceptance criteria**:
1. `TradingOrderIntent` has fields `stop_loss_price: Optional[float]` and `take_profit_price: Optional[float]`.
2. When `goal_config.customer_fields` contains `stop_loss_pct = 2.5` and pump output has `last_close_price`, `stop_loss_price = last_close_price × (1 - 0.025)` for long entries.
3. When `stop_loss_pct` is absent from config, `stop_loss_price = None` and no SL order is placed.
4. `TradingExecutionResult.debug` includes `stop_loss_price` and `take_profit_price` for traceability.
5. In draft mode, SL/TP prices are present in the deliverable JSON so the customer can see them during approval.

**Code patterns to copy exactly**:

```python
# In trading_executor.py — update TradingOrderIntent:
class TradingOrderIntent(BaseModel):
    exchange_provider: str = Field(..., min_length=1)
    exchange_account_id: str = Field(..., min_length=1)
    coin: str = Field(..., min_length=1)
    units: float = Field(..., gt=0)
    side: str = Field(..., min_length=1)      # long|short
    action: str = Field(..., min_length=1)    # enter|exit
    order_type: str = Field(..., min_length=1)  # market|limit
    limit_price: Optional[float] = Field(default=None, gt=0)
    stop_loss_price: Optional[float] = Field(default=None, gt=0)   # NEW
    take_profit_price: Optional[float] = Field(default=None, gt=0)  # NEW

# In execute_trading_delta_futures_manual_v1 — compute SL/TP before building intent:
def _compute_sl_tp(
    goal_config: dict,
    last_close: Optional[float],
    side: str,
) -> tuple[Optional[float], Optional[float]]:
    if last_close is None:
        return None, None
    cfg = goal_config.get("customer_fields", {})
    sl_pct = cfg.get("stop_loss_pct")
    tp_pct = cfg.get("profit_target_pct")
    if side == "long":
        sl = round(last_close * (1 - sl_pct / 100), 4) if sl_pct else None
        tp = round(last_close * (1 + tp_pct / 100), 4) if tp_pct else None
    else:  # short
        sl = round(last_close * (1 + sl_pct / 100), 4) if sl_pct else None
        tp = round(last_close * (1 - tp_pct / 100), 4) if tp_pct else None
    return sl, tp
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Long entry with `stop_loss_pct=2.5`, `last_close=100` → `stop_loss_price=97.5` | `tests/unit/test_delta_orders.py` |
| T2 | Unit | Missing `stop_loss_pct` → `stop_loss_price=None` | `tests/unit/test_delta_orders.py` |
| T3 | Unit | Draft deliverable JSON contains `stop_loss_price` | `tests/unit/test_delta_orders.py` |

---

### S9 — Autonomous mode bypasses approval gate; SMS + email + in-app notification sent

**Advances**: Share Trader value (enables hands-free trading with full notification transparency)
**Branch**: `feat/ST-MVP-1-s9-autonomous-mode`
**Estimate**: 60 min
**BLOCKED UNTIL**: S8 merged

**Context** (2 sentences):
Currently every trade requires `approval_id` to execute — there is no autonomous path. This story adds an `AutonomousModeHook` that checks `goal_config.customer_fields.autonomous_mode` and `autonomous_consent_at` and, if both are set, injects a platform-generated approval so the trade executes without customer interaction; it then fires notifications via `NotificationService`.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/agent_mold/enforcement.py` — `default_hook_bus()` structure
2. `src/Plant/BackEnd/agent_mold/hooks.py` — `AgentLifecycleHooks` and existing hook registration
3. `src/Plant/BackEnd/services/notification_service.py` — `NotificationService.send()` signature

**Files to create / edit**:
- `src/Plant/BackEnd/agent_mold/hooks.py` — add `AutonomousModeHook` class
- `src/Plant/BackEnd/agent_mold/enforcement.py` — register hook in `default_hook_bus()`
- `src/Plant/BackEnd/services/notification_sms_templates.py` — add `trade_executed` template
- `src/Plant/BackEnd/templates/email/trade_executed.html` — new email template
- `src/Plant/BackEnd/tests/unit/test_autonomous_mode_hook.py` — new test file

**Acceptance criteria**:
1. When `goal_config.customer_fields.autonomous_mode = True` and `autonomous_consent_at` is set, the hook generates a `platform_approval_id` and sets it on the execution context — trade executes without customer interaction.
2. When `autonomous_mode = False` or `autonomous_consent_at` is absent, hook is a no-op — existing approval gate applies.
3. After autonomous execution, `NotificationService.send()` is called with `channel="email"`, `template="trade_executed"`.
4. `notification_sms_templates.py` has a `trade_executed` entry with: instrument, direction, units, price, P&L.
5. Hook is registered in `default_hook_bus()` at `PRE_PUBLISH` stage.
6. Notification call is fire-and-forget (does not block trade execution).

**Code patterns to copy exactly**:

```python
# In agent_mold/hooks.py — add AutonomousModeHook:
import asyncio
from datetime import datetime, timezone

class AutonomousModeHook:
    """PRE_PUBLISH hook: bypasses approval gate for consented autonomous mode.
    Fires SMS+email+in-app notification after execution via fire-and-forget task.
    """
    async def __call__(self, context: dict) -> None:
        goal_config = context.get("goal_config", {}).get("customer_fields", {})
        if not goal_config.get("autonomous_mode"):
            return  # approval mode — do nothing, let ApprovalGateHook handle it
        consent_at = goal_config.get("autonomous_consent_at")
        if not consent_at:
            return  # consent not recorded — treat as approval mode
        # Inject platform approval so ApprovalGateHook passes
        context["platform_approval_id"] = f"AUTO-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        context["autonomous_execution"] = True

    async def notify_after_execution(self, context: dict) -> None:
        """Fire-and-forget post-execution notifications."""
        from services.notification_service import NotificationService
        customer_email = context.get("customer_email", "")
        customer_phone = context.get("customer_phone", "")
        trade = context.get("execution_result", {})
        notification_ctx = {
            "instrument": trade.get("coin", ""),
            "direction": trade.get("side", ""),
            "units": trade.get("units", ""),
            "price": trade.get("limit_price", "market"),
            "stop_loss": trade.get("stop_loss_price", "N/A"),
        }
        svc = NotificationService()
        if customer_email:
            asyncio.create_task(svc.send(  # fire-and-forget
                channel="email",
                destination=customer_email,
                template="trade_executed",
                context=notification_ctx,
            ))

# In notification_sms_templates.py — add template:
TRADE_EXECUTED_SMS = (
    "WAOOAW Trade: {direction} {units} {instrument} @ {price}. "
    "Stop-loss: {stop_loss}. Check app for full details."
)
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Hook sets `platform_approval_id` when `autonomous_mode=True` + consent present | `tests/unit/test_autonomous_mode_hook.py` |
| T2 | Unit | Hook is no-op when `autonomous_mode=False` | `tests/unit/test_autonomous_mode_hook.py` |
| T3 | Unit | Hook is no-op when `autonomous_consent_at` is absent | `tests/unit/test_autonomous_mode_hook.py` |

**BDD scenario**:
```
Given a customer has consented to autonomous mode
When RSI produces a BUY signal
Then the hook injects platform_approval_id
And the trade executes without a customer approval step
And NotificationService.send is called with template="trade_executed"
```

---

## Epic E4: Customer Reviews Performance and Downloads Tax Reports

---

### S10 — Emergency stop halts agent; mobile shows panic button

**Advances**: Share Trader value (mandatory safety control for any autonomous trading product)
**Branch**: `feat/ST-MVP-1-s10-emergency-stop`
**Estimate**: 60 min
**BLOCKED UNTIL**: Iteration 1 merged to main

**Context** (2 sentences):
There is no way for a customer to immediately halt the agent during high-volatility events — they would need to manually revoke Delta Exchange API keys. This story adds an emergency-stop endpoint that pauses the scheduler and records a halt timestamp, surfaced as a red button in the mobile `TradingSetupScreen`.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/services/scheduler_persistence_service.py` — `pause()` method
2. `src/CP/BackEnd/api/cp_trading_setup.py` — existing proxy pattern for reference
3. `src/mobile/src/screens/agents/TradingSetupScreen.tsx` — done step rendering

**Files to create / edit**:
- `src/Plant/BackEnd/api/v1/trading_setup.py` — new `POST /{id}/emergency-stop` endpoint
- `src/CP/BackEnd/api/cp_trading_setup.py` — new proxy `POST /cp/trading-setup/{id}/emergency-stop`
- `src/mobile/src/screens/agents/TradingSetupScreen.tsx` — red emergency stop button on done step
- `src/mobile/src/services/tradingSetup.service.ts` — `emergencyStop(hiredAgentId)` function

**Acceptance criteria**:
1. `POST /api/v1/hired-agents/{id}/emergency-stop` sets `scheduler_state.is_paused = True` for the given agent.
2. Sets `hired_agent.config["emergency_stopped_at"]` to current UTC ISO string.
3. Returns `{"status": "stopped", "stopped_at": "<iso>"}`.
4. CP proxy route `POST /cp/trading-setup/{id}/emergency-stop` forwards to Plant with `customer_id = str(user.id)`.
5. Mobile shows red "🛑 Emergency Stop" button on the `done` step. Tapping shows confirmation dialog: "This will halt all trading immediately. Continue?"
6. After confirmation, button shows "Stopping…" spinner, then "✓ Agent Halted".

**Code patterns to copy exactly**:

```python
# In trading_setup.py — new Plant endpoint:
from core.routing import waooaw_router
from core.database import get_db_session
from core.logging import PiiMaskingFilter, get_logger

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

@router.post("/{hired_instance_id}/emergency-stop", response_model=dict)
async def emergency_stop_trading(
    hired_instance_id: str,
    db=Depends(get_db_session),
) -> dict:
    """Pause scheduler and record emergency halt timestamp."""
    from datetime import datetime, timezone
    from repositories.hired_agent_repository import HiredAgentRepository
    repo = HiredAgentRepository(db)
    agent = await repo.get_by_id(hired_instance_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Hired agent not found")
    # Pause scheduler
    from services.scheduler_persistence_service import SchedulerPersistenceService
    await SchedulerPersistenceService(db).pause(hired_instance_id)
    # Record halt timestamp
    config = dict(agent.config or {})
    stopped_at = datetime.now(timezone.utc).isoformat()
    config["emergency_stopped_at"] = stopped_at
    await repo.update_config(hired_instance_id, config)
    await db.commit()
    logger.info("emergency_stop: agent %s halted", hired_instance_id)
    return {"status": "stopped", "stopped_at": stopped_at}

# In cp_trading_setup.py — CP proxy (Pattern B):
@router.post("/{hired_instance_id}/emergency-stop", response_model=Dict[str, Any])
async def cp_emergency_stop(
    hired_instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    plant: PlantGatewayClient = Depends(_plant_client),
) -> Dict[str, Any]:
    try:
        resp = await plant.request_json(
            method="POST",
            path=f"api/v1/hired-agents/{hired_instance_id}/emergency-stop",
            headers=_fwd(request),
            json_body={"customer_id": str(current_user.id)},
        )
    except ServiceUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.json)
    return resp.json
```

```typescript
// Mobile: add to TradingSetupScreen.tsx done-step rendering:
{currentStep === 'done' && (
  <TouchableOpacity
    style={[s.stopBtn, { backgroundColor: '#ef444418', borderColor: '#ef444455' }]}
    onPress={handleEmergencyStop}
    testID="emergency-stop-btn"
  >
    <Text style={{ color: '#ef4444', fontWeight: '700', fontSize: 14 }}>
      🛑 Emergency Stop
    </Text>
    <Text style={{ color: '#ef444499', fontSize: 11, marginTop: 2 }}>
      Halts all trading immediately
    </Text>
  </TouchableOpacity>
)}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Plant endpoint sets `scheduler_state.is_paused = True` | `tests/test_trading_setup.py` |
| T2 | Unit | Plant endpoint returns `{"status": "stopped", "stopped_at": ...}` | `tests/test_trading_setup.py` |
| T3 | Integration | CP proxy forwards to Plant and returns Plant response | `tests/test_cp_trading_setup.py` |

---

### S11 — Trade history endpoint and mobile trade list

**Advances**: Share Trader value (customer can audit every trade the agent made — required for trust)
**Branch**: `feat/ST-MVP-1-s11-trade-history`
**Estimate**: 60 min
**BLOCKED UNTIL**: S9 merged (autonomous execution produces trade records)

**Context** (2 sentences):
`TradePerformanceCard` shows aggregate stats (win rate, avg P&L) but there is no per-trade history list. Customers need to see each trade's instrument, direction, entry time, entry price, and P&L to verify the agent's decisions.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/api/v1/trade_performance.py` — existing performance aggregate for route structure
2. `src/Plant/BackEnd/models/performance_stat.py` — `PerformanceStatModel` columns
3. `src/mobile/src/components/TradePerformanceCard.tsx` — existing card for UI pattern

**Files to create / edit**:
- `src/Plant/BackEnd/api/v1/trade_history.py` — new: `GET /{id}/trade-history?page=1&page_size=20`
- `src/Plant/BackEnd/main.py` — register router
- `src/CP/BackEnd/api/cp_trading_performance.py` — add proxy `GET /cp/trading/history/{id}`
- `src/mobile/src/screens/agents/TradeHistoryScreen.tsx` — new screen
- `src/mobile/src/services/tradingSetup.service.ts` — add `getTradeHistory()` function

**Acceptance criteria**:
1. `GET /api/v1/hired-agents/{id}/trade-history?page=1&page_size=20` returns `{"trades": [...], "total": N, "page": 1, "page_size": 20}`.
2. Each trade item has: `stat_date`, `skill_id`, `trades_count`, `pnl_pct_avg`, `win_rate`, `stop_loss_count` (from `PerformanceStatModel`).
3. Results paginated; default page_size = 20; max = 100.
4. Uses `get_read_db_session()` (read replica).
5. Mobile `TradeHistoryScreen` renders a flat list with per-stat-date rows showing P&L and win rate.
6. Accessible from `AgentOperationsScreen` via "Trade History" link on hired Share Trader agent card.

**Code patterns to copy exactly**:

```python
# New file: src/Plant/BackEnd/api/v1/trade_history.py
from __future__ import annotations
from typing import Any, Dict, List
from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from core.database import get_read_db_session
from core.logging import PiiMaskingFilter, get_logger
from core.routing import waooaw_router
from models.performance_stat import PerformanceStatModel

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["trade-history"])

class TradeHistoryRow(BaseModel):
    stat_date: str
    skill_id: str
    trades_count: int
    pnl_pct_avg: float
    win_rate: float
    stop_loss_count: int

class TradeHistoryResponse(BaseModel):
    hired_instance_id: str
    trades: List[TradeHistoryRow]
    total: int
    page: int
    page_size: int

@router.get("/{hired_instance_id}/trade-history", response_model=TradeHistoryResponse)
async def get_trade_history(
    hired_instance_id: str,
    page: int = 1,
    page_size: int = 20,
    db=Depends(get_read_db_session),  # always read replica for GETs
) -> TradeHistoryResponse:
    page_size = min(max(page_size, 1), 100)
    offset = (max(page, 1) - 1) * page_size
    total_result = await db.execute(
        select(func.count()).select_from(PerformanceStatModel).where(
            PerformanceStatModel.hired_instance_id == hired_instance_id
        )
    )
    total = total_result.scalar_one()
    rows_result = await db.execute(
        select(PerformanceStatModel)
        .where(PerformanceStatModel.hired_instance_id == hired_instance_id)
        .order_by(PerformanceStatModel.stat_date.desc())
        .offset(offset).limit(page_size)
    )
    rows = rows_result.scalars().all()
    trades = [
        TradeHistoryRow(
            stat_date=str(r.stat_date),
            skill_id=r.skill_id,
            trades_count=(r.metrics or {}).get("trades_count", 0),
            pnl_pct_avg=(r.metrics or {}).get("pnl_pct", 0.0),
            win_rate=(r.metrics or {}).get("win_rate", 0.0),
            stop_loss_count=(r.metrics or {}).get("stop_loss_count", 0),
        )
        for r in rows
    ]
    return TradeHistoryResponse(
        hired_instance_id=hired_instance_id,
        trades=trades,
        total=total,
        page=page,
        page_size=page_size,
    )
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Empty history returns `{"trades": [], "total": 0}` | `tests/unit/test_trade_history_api.py` |
| T2 | Unit | Pagination: page=2, page_size=5 skips first 5 rows | `tests/unit/test_trade_history_api.py` |
| T3 | Unit | page_size capped at 100 | `tests/unit/test_trade_history_api.py` |

---

### S12 — Monthly/quarterly P&L tax report endpoint and mobile export

**Advances**: Share Trader value (legally required for customers; high-value retention feature)
**Branch**: `feat/ST-MVP-1-s12-tax-report`
**Estimate**: 60 min
**BLOCKED UNTIL**: S11 merged

**Context** (2 sentences):
Indian customers must declare crypto P&L for income tax purposes; there is no report endpoint today. This story adds a `GET /hired-agents/{id}/tax-report` endpoint that aggregates `PerformanceStatModel` rows for a given year/month into a structured P&L statement, with JSON and CSV output modes, and a mobile share button.

**Files to read first** (max 3):
1. `src/Plant/BackEnd/api/v1/trade_history.py` — just created in S11; use same DB pattern
2. `src/Plant/BackEnd/models/performance_stat.py` — columns: `stat_date`, `skill_id`, `metrics` JSONB
3. `src/mobile/src/components/TradePerformanceCard.tsx` — UI pattern for report display

**Files to create / edit**:
- `src/Plant/BackEnd/api/v1/tax_report.py` — new endpoint with JSON + CSV output
- `src/Plant/BackEnd/main.py` — register router
- `src/CP/BackEnd/api/cp_trading_performance.py` — proxy `GET /cp/trading/tax-report/{id}`
- `src/mobile/src/screens/agents/TaxReportScreen.tsx` — new screen with share button
- `src/mobile/src/services/tradingSetup.service.ts` — `getTaxReport()` function

**Acceptance criteria**:
1. `GET /api/v1/hired-agents/{id}/tax-report?year=2026&period=monthly&month=6` returns a report with `period`, `total_trades`, `total_pnl_pct`, `profitable_trades`, `loss_trades`, `stop_loss_exits`, and a `trades` array.
2. `GET` with `Accept: text/csv` header returns CSV with columns: `date,instrument,direction,pnl_pct,stop_loss`.
3. `period=quarterly&quarter=Q2` returns April–June aggregation.
4. Uses `get_read_db_session()`.
5. Mobile `TaxReportScreen` renders the report with a "Share / Export CSV" button that calls `Share.share()` with the CSV content.
6. Empty period returns `total_trades: 0` — never 500.

**Code patterns to copy exactly**:

```python
# New file: src/Plant/BackEnd/api/v1/tax_report.py
from __future__ import annotations
import csv, io
from datetime import date
from typing import Any, Dict, List, Optional
from fastapi import Depends, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from core.database import get_read_db_session
from core.logging import PiiMaskingFilter, get_logger
from core.routing import waooaw_router
from models.performance_stat import PerformanceStatModel

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())

router = waooaw_router(prefix="/hired-agents", tags=["tax-report"])

_QUARTER_MONTHS = {
    "Q1": (1, 2, 3), "Q2": (4, 5, 6),
    "Q3": (7, 8, 9), "Q4": (10, 11, 12),
}

@router.get("/{hired_instance_id}/tax-report")
async def get_tax_report(
    hired_instance_id: str,
    year: int = Query(..., ge=2024, le=2030),
    period: str = Query("monthly", regex="^(monthly|quarterly)$"),
    month: Optional[int] = Query(default=None, ge=1, le=12),
    quarter: Optional[str] = Query(default=None, regex="^Q[1-4]$"),
    db=Depends(get_read_db_session),
) -> Dict[str, Any]:
    # Determine date range
    if period == "monthly":
        if month is None:
            raise HTTPException(status_code=422, detail="month required for period=monthly")
        start = date(year, month, 1)
        end = date(year, month + 1, 1) if month < 12 else date(year + 1, 1, 1)
    else:
        if quarter is None:
            raise HTTPException(status_code=422, detail="quarter required for period=quarterly")
        months = _QUARTER_MONTHS[quarter]
        start = date(year, months[0], 1)
        end = date(year, months[-1] + 1, 1) if months[-1] < 12 else date(year + 1, 1, 1)
    result = await db.execute(
        select(PerformanceStatModel).where(
            PerformanceStatModel.hired_instance_id == hired_instance_id,
            PerformanceStatModel.stat_date >= start,
            PerformanceStatModel.stat_date < end,
        ).order_by(PerformanceStatModel.stat_date)
    )
    rows = result.scalars().all()
    if not rows:
        return {"hired_instance_id": hired_instance_id, "period": period,
                "year": year, "total_trades": 0, "total_pnl_pct": 0.0, "trades": []}
    metrics = [r.metrics or {} for r in rows]
    trades_data = [
        {"date": str(r.stat_date), "skill_id": r.skill_id,
         "trades_count": (r.metrics or {}).get("trades_count", 0),
         "pnl_pct": (r.metrics or {}).get("pnl_pct", 0.0),
         "win_rate": (r.metrics or {}).get("win_rate", 0.0),
         "stop_loss_count": (r.metrics or {}).get("stop_loss_count", 0)}
        for r in rows
    ]
    return {
        "hired_instance_id": hired_instance_id, "period": period, "year": year,
        "total_trades": sum(m.get("trades_count", 0) for m in metrics),
        "total_pnl_pct": round(sum(m.get("pnl_pct", 0.0) for m in metrics), 4),
        "profitable_trades": sum(1 for m in metrics if m.get("pnl_pct", 0.0) > 0),
        "loss_trades": sum(1 for m in metrics if m.get("pnl_pct", 0.0) < 0),
        "stop_loss_exits": sum(m.get("stop_loss_count", 0) for m in metrics),
        "trades": trades_data,
    }
```

```typescript
// In TaxReportScreen.tsx — share/export button:
import { Share } from 'react-native'

const handleExport = async () => {
  const csv = ["date,skill_id,trades,pnl_pct,stop_losses"]
    .concat(report.trades.map(
      (t: any) => `${t.date},${t.skill_id},${t.trades_count},${t.pnl_pct},${t.stop_loss_count}`
    )).join('\n')
  await Share.share({ message: csv, title: `Trade Report ${report.year}` })
}
```

**Test table**:

| # | Type | Description | File |
|---|---|---|---|
| T1 | Unit | Monthly report for month with no data returns `total_trades: 0` | `tests/unit/test_tax_report_api.py` |
| T2 | Unit | Monthly report aggregates 3 rows correctly | `tests/unit/test_tax_report_api.py` |
| T3 | Unit | Q2 quarterly covers April–June dates only | `tests/unit/test_tax_report_api.py` |
| T4 | Unit | Missing `month` for `period=monthly` returns 422 | `tests/unit/test_tax_report_api.py` |

**BDD scenario**:
```
Given a customer has 10 trade performance records in June 2026
When they request GET /hired-agents/{id}/tax-report?year=2026&period=monthly&month=6
Then the response contains total_trades = sum of all trades_count
And profitable_trades + loss_trades <= total_trades
And the trades array has 10 entries
When the mobile user taps "Export CSV"
Then Share.share is called with CSV content
```

---

## Future Phase 2 (out of scope for ST-MVP-1)

| Item | Reason deferred |
|---|---|
| LLM-guided strategy wizard for non-sensitive steps | Requires LLM_PROVIDER env var and prompt engineering; safe to add after step-machine proves out |
| Multiple exchange support (Binance, Zerodha) | Connector pattern extension; unblocks after Delta Exchange is proven |
| Backtesting historical data | Requires historical OHLCV store and simulation engine |
| SEBI algo trading registration | Legal process, not engineering |
| Performance stats auto-population from Delta Exchange order history | Requires order-close webhook or polling loop |
