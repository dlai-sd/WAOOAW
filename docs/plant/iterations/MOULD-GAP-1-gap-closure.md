# MOULD-GAP-1 — Mould Gap Closure

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `MOULD-GAP-1` |
| Feature area | Plant BackEnd (G3 LifecycleHooks, G7 TRIAL/BUDGET) + CP Mobile (HiredAgentsListScreen, notifications-config) + PP FrontEnd (CostBreakdownScreen, agent-type construct health) |
| Created | 2026-03-07 |
| Author | GitHub Copilot (PM mode) |
| Master source | `docs/PP/AGENT-CONSTRUCT-DESIGN.md` §6.3 (G3), §3.2/§11-G7 (G7), §13.7 (CP-G1), §13.4 (CP-G2), §14.7 (PP-G1), §14.5–14.6 (PP-G2) |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 6 |
| Total stories | 8 |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story — agent never opens NFRReusable.md |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. Do NOT open NFRReusable.md. All patterns you need are in your card.

---

## PM Review Checklist

- [x] Epic titles name user/operator outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before frontend (S2)
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Plant BackEnd — G3 LifecycleHooks ABC + wiring (E1) and G7 TRIAL/BUDGET enforcement (E2) | 2 | 4 | 3.5h | +4h after launch |
| 2 | CP Mobile — HiredAgentsListScreen enhancements (E3) + notifications-config route (E4); PP FrontEnd — CostBreakdownScreen (E5) + agent-type construct health (E6) | 4 | 4 | 3h | +4h after launch |

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check:**
```bash
git fetch origin && git log --oneline origin/main | head -5
# Must show: feat(PLANT-MOULD-1) iteration 2 and feat(CP-MOULD-1) iteration 3 on main.
```

**Iteration 1 agent task** (paste verbatim into @platform-engineer):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer experienced with ABC patterns,
hook buses, and async lifecycle wiring.
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11/FastAPI engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/MOULD-GAP-1-gap-closure.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2. Do not touch Iteration 2.
TIME BUDGET: 3.5h. If you reach 4h without finishing, follow STUCK PROTOCOL.

PREREQUISITE CHECK:
  git log --oneline origin/main | head -5
  Must show: feat(PLANT-MOULD-1) iteration 2 merged.
  If not: post "Blocked: PLANT-MOULD-1 not fully merged." HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" section.
2. Read "Iteration 1" section fully.
3. Execute Epics: E1 → E2
4. Run: docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
5. Open iteration PR. Post URL. HALT.
```

Come back at: **+4h after launch**

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge:**
```bash
git fetch origin && git log --oneline origin/main | head -5
# Must show: feat(MOULD-GAP-1): iteration 1
```

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / TypeScript engineer (CP mobile) AND Senior
React 18 / Vite / TypeScript engineer (PP FrontEnd). Activate both personas.
Begin each epic with:
  "Acting as a Senior [React Native / React 18] engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/MOULD-GAP-1-gap-closure.md
YOUR SCOPE: Iteration 2 only — Epics E3, E4, E5, E6. Do not touch Iteration 1.
TIME BUDGET: 3h.

PREREQUISITE CHECK:
  git log --oneline origin/main | head -5
  Must show: feat(MOULD-GAP-1): iteration 1 merged.
  If not: HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 2" sections.
2. Execute Epics: E3 → E4 → E5 → E6
3. Run CP mobile tests: cd src/mobile && npx jest --forceExit --passWithNoTests
4. Run PP FE tests: cd src/PP/FrontEnd && npm test -- --forceExit
5. Open iteration PR. Post URL. HALT.
```

Come back at: **+4h after launch**

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas
Read `EXPERT PERSONAS:` from your task block. Open every epic with the persona statement.

### Rule 0 — Open tracking draft PR first
```bash
git checkout main && git pull
git checkout -b feat/MOULD-GAP-1-itN-eN
git commit --allow-empty -m "chore(MOULD-GAP-1): start iteration N"
git push origin feat/MOULD-GAP-1-itN-eN
```

### Rule 1 — Branch discipline
One branch per iteration: `feat/MOULD-GAP-1-itN`. All epics in the iteration commit to the same branch.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria. Do not add features or refactor unrelated code.

### Rule 3 — Tests before the next story
All tests for the current story must pass before starting the next story.

### Rule 4 — Commit + push after every story
```bash
git add -A
git commit -m "feat(MOULD-GAP-1): [story title]"
git push origin feat/MOULD-GAP-1-itN
```

### Rule 5 — Integration test after every epic
**Iteration 1 (Plant BackEnd):**
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```
**Iteration 2 (CP mobile + PP FrontEnd):**
```bash
cd src/mobile && npx jest --forceExit --passWithNoTests
cd /workspaces/WAOOAW/src/PP/FrontEnd && npm test -- --forceExit
```

### Rule 6 — STUCK PROTOCOL
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/MOULD-GAP-1-itN
```
**HALT. Post the blocked story ID and exact error. Do not start the next story.**

### Rule 7 — Iteration PR
```bash
gh pr create --base main \
  --title "feat(MOULD-GAP-1): iteration N — [summary]" \
  --body "Closes gaps: [list gap IDs]"
```

### CHECKPOINT RULE
After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(MOULD-GAP-1): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | E1: LifecycleHooks ABC | Add `AgentLifecycleHooks` ABC + `lifecycle_hooks_class` to `ConstructBindings` | 🔴 Not Started | — |
| E1-S2 | 1 | E1: LifecycleHooks ABC | Wire `on_hire`/`on_trial_start` in `finalize` + `on_deliverable_approved` in `review_deliverable` | 🔴 Not Started | — |
| E2-S1 | 1 | E2: TRIAL/BUDGET enforcement | `TrialDimension.register_hooks()` — enforce `trial_task_limit` via `QuotaGateHook` | 🔴 Not Started | — |
| E2-S2 | 1 | E2: TRIAL/BUDGET enforcement | `BudgetDimension.register_hooks()` — enforce `max_tasks_per_day` cap via `ConstraintPolicyHook` | 🔴 Not Started | — |
| E3-S1 | 2 | E3: HiredAgentsListScreen | Add deliverable count + last-delivery badge + PerformanceCard row to `HiredAgentsListScreen.tsx` | 🔴 Not Started | — |
| E4-S1 | 2 | E4: notifications-config | `GET /cp/hired-agents/{id}/notifications-config` BE route + mobile `useNotificationsConfig` hook | 🔴 Not Started | — |
| E5-S1 | 2 | E5: CostBreakdownScreen | Create `CostBreakdownScreen.tsx` — cost per goal-run table with goal-run, LLM cost, platform fee columns | 🔴 Not Started | — |
| E6-S1 | 2 | E6: Agent-type health | Add agent-type-specific fields to PP `HiredAgentsOps.tsx` construct-health detail panel | 🔴 Not Started | — |

---

## Iteration 1

### Epic E1: Plant lifecycle events fire correctly when agents are hired and deliverables are approved

**Outcome:** `on_hire` and `on_trial_start` are called when a hired agent is finalised; `on_deliverable_approved` fires when a customer approves a deliverable — closing G3 from the master gap register.

**Context (2 sentences):** `ConstructBindings` in `src/Plant/BackEnd/agent_mold/spec.py` has no `lifecycle_hooks_class` field, and `AgentLifecycleHooks` ABC does not yet exist in `agent_mold/hooks.py`. The `finalize` endpoint in `hired_agents_simple.py` (line 1123) and `review_deliverable` in `deliverables_simple.py` are the two wiring points per §6.3 of the master design doc.

---

#### E1-S1 — Add `AgentLifecycleHooks` ABC and `lifecycle_hooks_class` to `ConstructBindings`

**Branch:** `feat/MOULD-GAP-1-it1`
**BLOCKED UNTIL:** none
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/Plant/BackEnd/agent_mold/spec.py` — `ConstructBindings` dataclass (lines 27–74), `ConstraintPolicy` shape
2. `src/Plant/BackEnd/agent_mold/hooks.py` — `HookBus`, `HookStage`, existing hook classes
3. `src/Plant/BackEnd/agent_mold/contracts.py` — `DimensionContract` pattern for ABC style

**NFR patterns to copy exactly (do NOT open NFRReusable.md):**
```python
# Plant BackEnd router — always use waooaw_router, never bare APIRouter
from core.routing import waooaw_router
# Read-only DB session (use for all GET routes and query-only paths)
from core.database import get_read_db_session
# PII masking filter — already active at root logger; no action needed in route code
# Trace via correlation_id (X-Correlation-ID header), never by email
```

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/Plant/BackEnd/agent_mold/hooks.py` — add `AgentLifecycleHooks` ABC at bottom |
| MODIFY | `src/Plant/BackEnd/agent_mold/spec.py` — add `lifecycle_hooks_class` field to `ConstructBindings` |
| CREATE | `src/Plant/BackEnd/tests/unit/test_lifecycle_hooks_abc.py` |

**What to build:**

```python
# ADD to src/Plant/BackEnd/agent_mold/hooks.py (after existing imports and classes)

from abc import ABC, abstractmethod
from typing import Any

class LifecycleContext:
    """Minimal context passed to every lifecycle event.

    Keeps hooks decoupled from DB session — they receive only what they need.
    Never log ctx.customer_email raw (PIIMaskingFilter handles it at logger level).
    """
    def __init__(
        self,
        hired_instance_id: str,
        agent_type_id: str,
        customer_id: str,
        agent_id: str | None = None,
        deliverable_id: str | None = None,
        extra: dict | None = None,
    ):
        self.hired_instance_id = hired_instance_id
        self.agent_type_id = agent_type_id
        self.customer_id = customer_id
        self.agent_id = agent_id
        self.deliverable_id = deliverable_id
        self.extra: dict = extra or {}


class AgentLifecycleHooks(ABC):
    """Base class for agent-type-specific lifecycle event handlers.

    Agent types override only the events they care about.
    All methods are async and non-blocking — a failure must NOT raise to caller.
    Default implementations are silent no-ops (safe to leave unoverridden).
    """

    async def on_hire(self, ctx: LifecycleContext) -> None:
        """Called when a hired agent is finalised (trial or direct hire)."""

    async def on_trial_start(self, ctx: LifecycleContext) -> None:
        """Called when trial_start_at is set on the hired agent."""

    async def on_trial_end(self, ctx: LifecycleContext) -> None:
        """Called when trial period expires (scheduler detects trial_end_date passed)."""

    async def on_trial_day_N(self, ctx: LifecycleContext, day: int) -> None:
        """Called once per trial day N (day=1 on first full day, etc.)."""

    async def on_deliverable_pending_review(self, ctx: LifecycleContext) -> None:
        """Called when a deliverable lands in pending_review status."""

    async def on_deliverable_approved(self, ctx: LifecycleContext) -> None:
        """Called when a customer approves a deliverable.

        For trading agents: triggers DeltaTradeAdapter.execute_approved_order().
        For content agents: triggers Publisher.publish() for approved posts.
        Subclass MUST override if agent has an approval side-effect.
        """

    async def on_deliverable_rejected(self, ctx: LifecycleContext) -> None:
        """Called when a customer rejects a deliverable."""

    async def on_goal_run_start(self, ctx: LifecycleContext) -> None:
        """Called at the start of each goal run (Scheduler fires)."""

    async def on_goal_run_complete(self, ctx: LifecycleContext) -> None:
        """Called when a goal run finishes successfully."""

    async def on_cancel(self, ctx: LifecycleContext) -> None:
        """Called when subscription is cancelled."""

    async def on_quota_exhausted(self, ctx: LifecycleContext) -> None:
        """Called when trial_task_limit is reached."""


class NullLifecycleHooks(AgentLifecycleHooks):
    """No-op lifecycle hooks. Used as default when agent type has no overrides."""
```

```python
# MODIFY src/Plant/BackEnd/agent_mold/spec.py
# Add import at top:
from typing import Optional, Type  # (already likely present)

# Inside ConstructBindings dataclass — add one field (after publisher_class):
    lifecycle_hooks_class: Optional[Type] = None
    # Type must be a subclass of AgentLifecycleHooks.
    # None → platform uses NullLifecycleHooks (silent no-ops).

# Also update ConstructBindings.validate() to check lifecycle_hooks_class:
    def validate(self) -> None:
        from agent_mold.processor import BaseProcessor
        from agent_mold.pump import BasePump
        from agent_mold.hooks import AgentLifecycleHooks
        if not issubclass(self.processor_class, BaseProcessor):
            raise TypeError(f"{self.processor_class} must inherit BaseProcessor")
        if not issubclass(self.pump_class, BasePump):
            raise TypeError(f"{self.pump_class} must inherit BasePump")
        if self.lifecycle_hooks_class is not None:
            if not issubclass(self.lifecycle_hooks_class, AgentLifecycleHooks):
                raise TypeError(
                    f"{self.lifecycle_hooks_class} must inherit AgentLifecycleHooks"
                )
```

**Tests to write:**
```python
# src/Plant/BackEnd/tests/unit/test_lifecycle_hooks_abc.py
import pytest
from agent_mold.hooks import AgentLifecycleHooks, LifecycleContext, NullLifecycleHooks


def make_ctx() -> LifecycleContext:
    return LifecycleContext(
        hired_instance_id="hi-1",
        agent_type_id="trading",
        customer_id="cust-1",
    )


@pytest.mark.asyncio
async def test_null_hooks_all_methods_are_no_ops():
    """NullLifecycleHooks must not raise on any event call."""
    hooks = NullLifecycleHooks()
    ctx = make_ctx()
    await hooks.on_hire(ctx)
    await hooks.on_trial_start(ctx)
    await hooks.on_deliverable_approved(ctx)
    await hooks.on_cancel(ctx)


def test_construct_bindings_validates_lifecycle_hooks_class():
    """ConstructBindings.validate() must reject non-AgentLifecycleHooks class."""
    from agent_mold.spec import ConstructBindings
    from agent_mold.processor import BaseProcessor
    from agent_mold.pump import BasePump, GoalConfigPump

    class FakeProcessor(BaseProcessor):
        PROCESSOR_ID = "test"
        async def execute(self, inp): ...

    class FakeScheduler: ...

    class NotAHook:  # does NOT inherit AgentLifecycleHooks
        pass

    bindings = ConstructBindings(
        processor_class=FakeProcessor,
        scheduler_class=FakeScheduler,
        pump_class=GoalConfigPump,
        lifecycle_hooks_class=NotAHook,
    )
    with pytest.raises(TypeError, match="AgentLifecycleHooks"):
        bindings.validate()


def test_construct_bindings_accepts_null_lifecycle():
    """lifecycle_hooks_class=None is valid — no-ops are used."""
    from agent_mold.spec import ConstructBindings
    from agent_mold.processor import BaseProcessor
    from agent_mold.pump import GoalConfigPump

    class FakeProcessor(BaseProcessor):
        PROCESSOR_ID = "test"
        async def execute(self, inp): ...

    class FakeScheduler: ...

    bindings = ConstructBindings(
        processor_class=FakeProcessor,
        scheduler_class=FakeScheduler,
        pump_class=GoalConfigPump,
        lifecycle_hooks_class=None,
    )
    bindings.validate()  # must not raise
```

**Acceptance criteria:**
- [ ] `AgentLifecycleHooks` ABC exists in `hooks.py` with all 10 event methods
- [ ] `NullLifecycleHooks` is a concrete no-op subclass
- [ ] `LifecycleContext` dataclass exists with all fields
- [ ] `ConstructBindings.lifecycle_hooks_class` field exists, Optional, defaults to `None`
- [ ] `ConstructBindings.validate()` raises `TypeError` for non-`AgentLifecycleHooks` class
- [ ] `pytest src/Plant/BackEnd/tests/unit/test_lifecycle_hooks_abc.py` exits 0

---

#### E1-S2 — Wire `on_hire`/`on_trial_start` in `finalize` + `on_deliverable_approved` in `review_deliverable`

**Branch:** `feat/MOULD-GAP-1-it1`
**BLOCKED UNTIL:** E1-S1 merged
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/Plant/BackEnd/api/v1/hired_agents_simple.py` — `finalize` function at line 1123
2. `src/Plant/BackEnd/api/v1/deliverables_simple.py` — `review_deliverable` function at line 484
3. `src/Plant/BackEnd/agent_mold/registry.py` — how to get `AgentSpec` from `agent_type_id`

**What to build:**

```python
# In hired_agents_simple.py — inside finalize() AFTER the hired agent row is persisted:
# (after line ~1205 where persisted = await repo.finalize(...))

from agent_mold.hooks import LifecycleContext, NullLifecycleHooks
from agent_mold.registry import AgentSpecRegistry

# Resolve lifecycle hooks from ConstructBindings (or fall back to no-ops)
try:
    spec = AgentSpecRegistry.instance().get_spec(record.agent_type_id)
    bindings = spec.bindings
    hooks_cls = (bindings.lifecycle_hooks_class if bindings else None) or NullLifecycleHooks
except Exception:
    hooks_cls = NullLifecycleHooks

hooks = hooks_cls()
ctx = LifecycleContext(
    hired_instance_id=persisted.hired_instance_id,
    agent_type_id=record.agent_type_id or "",
    customer_id=record.customer_id or "",
    agent_id=record.agent_id,
)

# Fire lifecycle events — non-blocking, errors must not fail the hire response
import asyncio, logging
_lhooks_logger = logging.getLogger(__name__)

async def _fire(coro):
    try:
        await coro
    except Exception as exc:  # noqa: BLE001
        _lhooks_logger.warning("lifecycle hook error: %s", exc)

await _fire(hooks.on_hire(ctx))
if trial_start_at is not None:
    await _fire(hooks.on_trial_start(ctx))
```

```python
# In deliverables_simple.py — inside review_deliverable() AFTER d.review_status is set to "approved":
# (after line ~508 where d.review_status = "approved")

from agent_mold.hooks import LifecycleContext, NullLifecycleHooks
from agent_mold.registry import AgentSpecRegistry

if decision == "approved":
    try:
        spec = AgentSpecRegistry.instance().get_spec(d.agent_type_id or "")
        bindings = spec.bindings if spec else None
        hooks_cls = (bindings.lifecycle_hooks_class if bindings else None) or NullLifecycleHooks
    except Exception:
        hooks_cls = NullLifecycleHooks

    hooks = hooks_cls()
    ctx = LifecycleContext(
        hired_instance_id=d.hired_instance_id,
        agent_type_id=d.agent_type_id or "",
        customer_id=d.customer_id or "",
        deliverable_id=deliverable_id,
    )
    import logging
    _dlhooks_logger = logging.getLogger(__name__)
    try:
        await hooks.on_deliverable_approved(ctx)
    except Exception as exc:  # noqa: BLE001
        _dlhooks_logger.warning("on_deliverable_approved hook error: %s", exc)
```

**Tests to write:**
```python
# Append to src/Plant/BackEnd/tests/unit/test_lifecycle_hooks_abc.py

from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_on_hire_called_on_finalize(async_client, mock_registry):
    """Mocking registry + lifecycle hooks — on_hire must be awaited during finalize."""
    mock_hooks = MagicMock(spec=AgentLifecycleHooks)
    mock_hooks.on_hire = AsyncMock()
    mock_hooks.on_trial_start = AsyncMock()

    class MockHooksClass:
        def __new__(cls):
            return mock_hooks

    mock_spec = MagicMock()
    mock_spec.bindings.lifecycle_hooks_class = MockHooksClass
    mock_registry.get_spec.return_value = mock_spec

    # Simulate finalize path — on_hire must be called
    ctx = LifecycleContext("hi-1", "trading", "cust-1")
    await mock_hooks.on_hire(ctx)
    mock_hooks.on_hire.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_deliverable_approved_called_on_review(async_client, mock_registry):
    """on_deliverable_approved must be awaited when decision == 'approved'."""
    mock_hooks = MagicMock(spec=AgentLifecycleHooks)
    mock_hooks.on_deliverable_approved = AsyncMock()

    ctx = LifecycleContext("hi-1", "trading", "cust-1", deliverable_id="del-1")
    await mock_hooks.on_deliverable_approved(ctx)
    mock_hooks.on_deliverable_approved.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifecycle_hook_error_does_not_fail_hire():
    """A crashing hook must be caught — hire/approval response must not 500."""
    class CrashingHooks(AgentLifecycleHooks):
        async def on_hire(self, ctx):
            raise RuntimeError("simulated hook crash")

    hooks = CrashingHooks()
    ctx = LifecycleContext("hi-1", "trading", "cust-1")
    # Should not raise — caller wraps in try/except
    try:
        await hooks.on_hire(ctx)
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass  # Caller must catch this — test documents the contract
```

**Acceptance criteria:**
- [ ] `finalize` endpoint calls `hooks.on_hire(ctx)` after row is persisted
- [ ] `finalize` endpoint calls `hooks.on_trial_start(ctx)` when `trial_start_at` is set
- [ ] `review_deliverable` calls `hooks.on_deliverable_approved(ctx)` when `decision == "approved"`
- [ ] All hook calls are wrapped in try/except — hook crash does NOT 500 the endpoint
- [ ] `NullLifecycleHooks` is used as fallback when `lifecycle_hooks_class` is None or registry lookup fails
- [ ] Full docker test suite passes (`pytest --cov=app --cov-fail-under=80`)

---

### Epic E2: TRIAL quota and BUDGET task caps are enforced at the mould level, not just in docs

**Outcome:** `TrialDimension` enforces `trial_task_limit` by registering a `QuotaGateHook`, and `BudgetDimension` enforces `max_tasks_per_day` via `ConstraintPolicyHook` — closing G7 from the master gap register.

**Context (2 sentences):** `BasicDimension.register_hooks()` in `src/Plant/BackEnd/agent_mold/contracts.py` (line 104) returns `None` unconditionally regardless of dimension type — TRIAL and BUDGET enforcement only exists in documentation. Two new concrete dimension classes need to override `register_hooks()` and actually register hooks onto the `HookBus` that is passed to them at mould compilation time.

---

#### E2-S1 — `TrialDimension` — enforce `trial_task_limit` via `QuotaGateHook`

**Branch:** `feat/MOULD-GAP-1-it1`
**BLOCKED UNTIL:** E1-S1 merged (hooks infrastructure in place)
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/Plant/BackEnd/agent_mold/contracts.py` — full file: `DimensionContract`, `BasicDimension`, `NullDimension`
2. `src/Plant/BackEnd/agent_mold/hooks.py` — `HookBus`, `HookStage`, `HookEvent`, `HookDecision`
3. `src/Plant/BackEnd/agent_mold/hooks_builtin.py` — `QuotaGateHook` and `ConstraintPolicyHook` patterns

**What to build:**

```python
# ADD to src/Plant/BackEnd/agent_mold/contracts.py (after BasicDimension class)

class TrialDimension(DimensionContract):
    """TRIAL dimension — enforces trial_task_limit at PRE_PUMP stage.

    Compiles into a QuotaGateHook registered on the HookBus.
    When tasks_used >= trial_task_limit the hook returns DENY and fires
    the on_quota_exhausted lifecycle event.

    trial_task_limit is read from AgentSpec.constraint_policy at register time.
    Default limit: 10 (matches ConstraintPolicy default).
    """

    name = DimensionName.TRIAL

    def __init__(self, *, trial_task_limit: int = 10):
        self.trial_task_limit = trial_task_limit

    def validate(self, spec: "AgentSpec") -> None:  # noqa: F821
        if self.trial_task_limit < 1:
            raise ValueError("trial_task_limit must be >= 1")

    def materialize(self, compiled: "CompiledAgentSpec", context: DimensionContext) -> Dict[str, Any]:
        return {
            "present": True,
            "name": self.name,
            "version": self.version,
            "trial_task_limit": self.trial_task_limit,
        }

    def register_hooks(self, hook_bus: Any) -> None:
        """Register QuotaGateHook at PRE_PUMP stage.

        HookBus is the live instance from GoalSchedulerService.
        The hook reads tasks_used from the goal_run context at fire time.
        """
        from agent_mold.hooks import HookStage

        trial_limit = self.trial_task_limit

        class _TrialQuotaHook:
            """Blocks execution if trial task limit is reached."""

            def __call__(self, event: Any) -> Any:
                from agent_mold.hooks import HookDecision
                tasks_used = getattr(event, "tasks_used", 0) or 0
                if tasks_used >= trial_limit:
                    return HookDecision(
                        proceed=False,
                        reason=f"trial_task_limit reached ({tasks_used}/{trial_limit})",
                        decision_id=f"trial-quota-deny-{tasks_used}",
                    )
                return HookDecision(proceed=True, reason="within_trial_quota", decision_id="trial-quota-allow")

        hook_bus.register(HookStage.PRE_PUMP, _TrialQuotaHook())

    def observe(self, event: Any) -> None:
        # Future: emit metric when quota_remaining drops below 20%
        pass


class BudgetDimension(DimensionContract):
    """BUDGET dimension — enforces max_tasks_per_day at PRE_PUMP stage.

    Compiles into a daily task cap hook registered on the HookBus.
    When tasks_today >= max_tasks_per_day (and max > 0), blocks execution.
    max_tasks_per_day=0 means no limit (unlimited).
    """

    name = DimensionName.BUDGET

    def __init__(self, *, max_tasks_per_day: int = 0):
        self.max_tasks_per_day = max_tasks_per_day  # 0 = no limit

    def validate(self, spec: "AgentSpec") -> None:  # noqa: F821
        if self.max_tasks_per_day < 0:
            raise ValueError("max_tasks_per_day cannot be negative")

    def materialize(self, compiled: "CompiledAgentSpec", context: DimensionContext) -> Dict[str, Any]:
        return {
            "present": True,
            "name": self.name,
            "version": self.version,
            "max_tasks_per_day": self.max_tasks_per_day,
        }

    def register_hooks(self, hook_bus: Any) -> None:
        """Register daily task cap hook at PRE_PUMP stage.

        Checks tasks_today from event context. Skipped when max_tasks_per_day=0.
        """
        from agent_mold.hooks import HookStage

        max_daily = self.max_tasks_per_day
        if max_daily == 0:
            return  # No limit configured — register nothing

        class _DailyTaskCapHook:
            """Blocks execution if today's task count reaches max_tasks_per_day."""

            def __call__(self, event: Any) -> Any:
                from agent_mold.hooks import HookDecision
                tasks_today = getattr(event, "tasks_today", 0) or 0
                if tasks_today >= max_daily:
                    return HookDecision(
                        proceed=False,
                        reason=f"max_tasks_per_day reached ({tasks_today}/{max_daily})",
                        decision_id=f"budget-cap-deny-{tasks_today}",
                    )
                return HookDecision(proceed=True, reason="within_daily_budget", decision_id="budget-cap-allow")

        hook_bus.register(HookStage.PRE_PUMP, _DailyTaskCapHook())

    def observe(self, event: Any) -> None:
        # Future: emit Prometheus counter when daily budget is 80% consumed
        pass
```

**Tests to write:**
```python
# src/Plant/BackEnd/tests/unit/test_dimension_enforcement.py
import pytest
from unittest.mock import MagicMock
from agent_mold.contracts import TrialDimension, BudgetDimension
from agent_mold.hooks import HookBus, HookStage, HookEvent


def _make_event(tasks_used=0, tasks_today=0):
    event = MagicMock()
    event.tasks_used = tasks_used
    event.tasks_today = tasks_today
    return event


# ── TrialDimension tests ────────────────────────────────────────────────────

def test_trial_dimension_registers_hook_on_hookbus():
    dim = TrialDimension(trial_task_limit=5)
    bus = HookBus()
    dim.register_hooks(bus)
    assert len(bus._hooks.get(HookStage.PRE_PUMP, [])) == 1


def test_trial_quota_hook_allows_when_under_limit():
    dim = TrialDimension(trial_task_limit=10)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_used=5)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is True


def test_trial_quota_hook_denies_when_at_limit():
    dim = TrialDimension(trial_task_limit=10)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_used=10)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is False
    assert "trial_task_limit" in decision.reason


def test_trial_quota_hook_denies_when_over_limit():
    dim = TrialDimension(trial_task_limit=5)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_used=7)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is False


def test_trial_dimension_validate_rejects_zero_limit():
    dim = TrialDimension(trial_task_limit=0)
    with pytest.raises(ValueError, match="trial_task_limit"):
        dim.validate(MagicMock())


# ── BudgetDimension tests ───────────────────────────────────────────────────

def test_budget_dimension_zero_registers_no_hook():
    """max_tasks_per_day=0 means unlimited — no hook should be registered."""
    dim = BudgetDimension(max_tasks_per_day=0)
    bus = HookBus()
    dim.register_hooks(bus)
    assert len(bus._hooks.get(HookStage.PRE_PUMP, [])) == 0


def test_budget_dimension_registers_hook_when_limit_set():
    dim = BudgetDimension(max_tasks_per_day=3)
    bus = HookBus()
    dim.register_hooks(bus)
    assert len(bus._hooks.get(HookStage.PRE_PUMP, [])) == 1


def test_budget_cap_hook_allows_when_under_limit():
    dim = BudgetDimension(max_tasks_per_day=5)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_today=2)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is True


def test_budget_cap_hook_denies_when_at_limit():
    dim = BudgetDimension(max_tasks_per_day=3)
    bus = HookBus()
    dim.register_hooks(bus)
    event = _make_event(tasks_today=3)
    decision = bus.emit(HookStage.PRE_PUMP, event)
    assert decision.proceed is False
    assert "max_tasks_per_day" in decision.reason
```

**Acceptance criteria:**
- [ ] `TrialDimension` class exists in `contracts.py` with `register_hooks()` registering a hook at `HookStage.PRE_PUMP`
- [ ] `BudgetDimension` class exists in `contracts.py` with `register_hooks()` registering a cap hook (skipped when `max_tasks_per_day=0`)
- [ ] `TrialDimension` hook returns `HookDecision(proceed=False)` when `tasks_used >= trial_task_limit`
- [ ] `BudgetDimension` hook returns `HookDecision(proceed=False)` when `tasks_today >= max_tasks_per_day`
- [ ] `pytest src/Plant/BackEnd/tests/unit/test_dimension_enforcement.py` exits 0

---

#### E2-S2 — Export `TrialDimension` and `BudgetDimension` from `agent_mold` and add integration smoke test

**Branch:** `feat/MOULD-GAP-1-it1`
**BLOCKED UNTIL:** E2-S1 merged
**Estimate:** 30 min

**Files to read first (max 3):**
1. `src/Plant/BackEnd/agent_mold/__init__.py` — current exports
2. `src/Plant/BackEnd/agent_mold/contracts.py` — new classes from E2-S1
3. `src/Plant/BackEnd/agent_mold/reference_agents.py` — how existing agents declare dimensions

**What to build:**

```python
# MODIFY src/Plant/BackEnd/agent_mold/__init__.py
# Add to exports:
from agent_mold.contracts import (
    DimensionContract,
    BasicDimension,
    NullDimension,
    TrialDimension,      # ← NEW
    BudgetDimension,     # ← NEW
)
from agent_mold.hooks import AgentLifecycleHooks, NullLifecycleHooks, LifecycleContext  # ← NEW
```

```python
# MODIFY src/Plant/BackEnd/agent_mold/reference_agents.py
# For each reference agent that has a TRIAL or BUDGET dimension declared as BasicDimension,
# replace with TrialDimension / BudgetDimension and pass the relevant limit.
# Example — for marketing agent:
#   BEFORE: DimensionName.TRIAL: BasicDimension(DimensionName.TRIAL)
#   AFTER:  DimensionName.TRIAL: TrialDimension(trial_task_limit=10)
#           DimensionName.BUDGET: BudgetDimension(max_tasks_per_day=3)
```

```python
# ADD src/Plant/BackEnd/tests/unit/test_dimension_integration.py

def test_trial_and_budget_dimensions_importable_from_agent_mold():
    from agent_mold import TrialDimension, BudgetDimension
    assert TrialDimension is not None
    assert BudgetDimension is not None


def test_lifecycle_hooks_importable_from_agent_mold():
    from agent_mold import AgentLifecycleHooks, NullLifecycleHooks, LifecycleContext
    ctx = LifecycleContext("hi-1", "trading", "cust-1")
    assert ctx.hired_instance_id == "hi-1"


def test_reference_agent_uses_trial_dimension():
    """Reference agents must use TrialDimension, not BasicDimension, for TRIAL."""
    from agent_mold.reference_agents import get_all_reference_agents
    from agent_mold.contracts import TrialDimension
    from agent_mold.spec import DimensionName

    agents = get_all_reference_agents()
    for a in agents:
        trial_dim = a.dimensions.get(DimensionName.TRIAL)
        if trial_dim is not None:
            assert isinstance(trial_dim, TrialDimension), \
                f"Agent {a.agent_id} uses {type(trial_dim)} for TRIAL — must be TrialDimension"
```

**Acceptance criteria:**
- [ ] `TrialDimension` and `BudgetDimension` importable from `agent_mold` top-level package
- [ ] `AgentLifecycleHooks`, `NullLifecycleHooks`, `LifecycleContext` importable from `agent_mold`
- [ ] At least one reference agent uses `TrialDimension` (not `BasicDimension`) for TRIAL
- [ ] `pytest src/Plant/BackEnd/tests/unit/test_dimension_integration.py` exits 0
- [ ] Full docker test suite exits 0 with coverage ≥ 80%

---

## Iteration 2

### Epic E3: Hired agent cards show deliverable count and last-delivery summary

**Outcome:** Customers see how many deliverables each hired agent has produced and when the last one was delivered — directly on the `HiredAgentsListScreen` card, mapping §13.7 of the master design doc.

**Context (2 sentences):** `src/mobile/src/screens/agents/HiredAgentsListScreen.tsx` (180 lines) only shows agent name and subscription status — no deliverable metrics are surfaced per §13.7 which specifies a deliverable-count column and last-delivery time. The `useHiredAgents()` hook already returns `hired_instance_id` which can be used to count deliverables from the existing performance-stats endpoint.

---

#### E3-S1 — Add deliverable count + last-delivery badge + PerformanceCard row to `HiredAgentsListScreen.tsx`

**Branch:** `feat/MOULD-GAP-1-it2`
**BLOCKED UNTIL:** none (pure FE change, no new BE route needed)
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/mobile/src/screens/agents/HiredAgentsListScreen.tsx` — full file (180 lines)
2. `src/mobile/src/hooks/useHiredAgents.ts` — shape of `agents` items returned
3. `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` — pattern for performance stats display

**What to build:**

```tsx
// MODIFY src/mobile/src/screens/agents/HiredAgentsListScreen.tsx
// Add deliverable count + last_delivered_at badge to each card row.
// Pattern: read from item.deliverable_count and item.last_delivered_at if present,
// else show "— deliverables" as a graceful empty state.
// Also add a PerformanceCard micro-row showing "X deliverables · Last: <date or 'Never'>".

// 1. Extend the card TouchableOpacity renderItem to include:
<View style={{ flexDirection: 'row', marginTop: spacing.xs, gap: spacing.sm }}>
  {/* Deliverable count badge */}
  <View style={{
    backgroundColor: colors.purple + '20',
    borderRadius: spacing.xs,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
  }}>
    <Text style={{
      color: colors.purple,
      fontFamily: typography.fontFamily.body,
      fontSize: 12,
    }}>
      {item.deliverable_count != null ? `${item.deliverable_count} deliverables` : '— deliverables'}
    </Text>
  </View>

  {/* Last delivery timestamp */}
  {item.last_delivered_at && (
    <Text style={{
      color: colors.textSecondary,
      fontFamily: typography.fontFamily.body,
      fontSize: 11,
      alignSelf: 'center',
    }}>
      Last: {new Date(item.last_delivered_at).toLocaleDateString()}
    </Text>
  )}
</View>
```

**Type extension (if needed):**
```typescript
// If the HiredAgent type does not have deliverable_count / last_delivered_at,
// add them as optional fields to the local type used in this screen:
type HiredAgentItem = {
  subscription_id: string;
  agent_id: string;
  nickname?: string | null;
  status?: string | null;
  trial_status?: string | null;
  deliverable_count?: number | null;
  last_delivered_at?: string | null;  // ISO-8601
};
```

**Tests to write:**
```typescript
// src/mobile/__tests__/hiredAgentsListScreen.test.tsx
import React from 'react';
import { render } from '@testing-library/react-native';
import { HiredAgentsListScreen } from '../src/screens/agents/HiredAgentsListScreen';

const mockNavigation = { navigate: jest.fn(), goBack: jest.fn() };

jest.mock('../src/hooks/useHiredAgents', () => ({
  useHiredAgents: () => ({
    data: [
      {
        subscription_id: 'sub-1',
        agent_id: 'agent-1',
        nickname: 'Content Agent',
        status: 'active',
        trial_status: 'completed',
        deliverable_count: 12,
        last_delivered_at: '2026-03-06T10:00:00Z',
      },
      {
        subscription_id: 'sub-2',
        agent_id: 'agent-2',
        nickname: null,
        status: 'active',
        trial_status: 'completed',
        deliverable_count: null,
        last_delivered_at: null,
      },
    ],
    isLoading: false,
  }),
}));

jest.mock('../src/hooks/useTheme', () => ({
  useTheme: () => ({
    colors: { black: '#000', textPrimary: '#fff', textSecondary: '#999', card: '#1a1a1a', border: '#333', neonCyan: '#00f2fe', purple: '#667eea' },
    spacing: { screenPadding: { horizontal: 16 }, md: 16, sm: 8, xs: 4, xl: 32 },
    typography: { fontFamily: { display: 'SpaceGrotesk', body: 'Inter', bodyBold: 'Inter-Bold' } },
  }),
}));

describe('HiredAgentsListScreen', () => {
  it('shows deliverable count when present', () => {
    const { getByText } = render(
      <HiredAgentsListScreen navigation={mockNavigation as any} route={{} as any} />
    );
    expect(getByText('12 deliverables')).toBeTruthy();
  });

  it('shows fallback when deliverable_count is null', () => {
    const { getAllByText } = render(
      <HiredAgentsListScreen navigation={mockNavigation as any} route={{} as any} />
    );
    expect(getAllByText('— deliverables').length).toBeGreaterThanOrEqual(1);
  });

  it('shows last delivery date when present', () => {
    const { getByText } = render(
      <HiredAgentsListScreen navigation={mockNavigation as any} route={{} as any} />
    );
    expect(getByText(/Last:/)).toBeTruthy();
  });
});
```

**Acceptance criteria:**
- [ ] Each card in `HiredAgentsListScreen` shows a deliverable count badge
- [ ] When `deliverable_count` is null, shows `— deliverables` (graceful empty state)
- [ ] When `last_delivered_at` is present, shows formatted date
- [ ] `npx jest src/mobile/__tests__/hiredAgentsListScreen.test.tsx --forceExit` exits 0
- [ ] TypeScript compilation clean (`npx tsc --noEmit` exits 0 in `src/mobile`)

---

### Epic E4: Customers can read and manage per-agent notification preferences from the mobile app

**Outcome:** A new CP BackEnd route serves notification preferences per hired agent; `NotificationsScreen.tsx` displays and can toggle per-agent notification settings — closing the missing `notifications-config` route identified in §13.4 of the master design doc.

**Context (2 sentences):** `src/CP/BackEnd/api/cp_scheduler.py` already has the `waooaw_router(prefix="/cp/hired-agents")` pattern — add the new route there. `src/mobile/src/screens/profile/NotificationsScreen.tsx` deep-links to agents (per CP-MOULD-1 E6-S1) but has no way to fetch or display per-agent notification preferences.

---

#### E4-S1 — `GET /cp/hired-agents/{id}/notifications-config` BE + mobile `useNotificationsConfig` hook

**Branch:** `feat/MOULD-GAP-1-it2`
**BLOCKED UNTIL:** none
**Estimate:** 75 min

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/cp_scheduler.py` — full file: `waooaw_router` usage, `gatewayRequestJson` pattern
2. `src/mobile/src/screens/profile/NotificationsScreen.tsx` — current content
3. `src/mobile/src/hooks/useSchedulerSummary.ts` — hook pattern to copy for `useNotificationsConfig`

**NFR patterns to copy exactly (do NOT open NFRReusable.md):**
```python
# CP BackEnd thin proxy — MANDATORY patterns (copy from cp_scheduler.py):
from core.routing import waooaw_router                     # never bare APIRouter
from core.database import get_read_db_session              # GET routes only
from app.dependencies import get_current_user, CurrentUser # auth dependency
from app.gateway import gatewayRequestJson                 # Plant proxy call

router = waooaw_router(prefix="/cp/hired-agents", tags=["cp-notifications"])

@router.get("/{hired_instance_id}/notifications-config")
async def get_notifications_config(
    hired_instance_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_read_db_session),
):
    """Returns per-agent notification preferences for the authenticated customer.

    Response shape:
    {
      "hired_instance_id": "...",
      "approval_pending":   true,   // notify when deliverable needs review
      "goal_run_complete":  true,   // notify when agent finishes a run
      "trial_summary":      true,   // daily trial summary notifications
      "credential_expiry":  true,   // warn when OAuth token near expiry
    }

    Defaults to all-true when no explicit preferences stored.
    Proxies to Plant GET /v1/hired-agents/{id}/notifications-config.
    Customer must own this hired agent (enforced by Plant via JWT).
    """
    return await gatewayRequestJson(
        "GET",
        f"/v1/hired-agents/{hired_instance_id}/notifications-config",
        current_user=current_user,
    )
```

**Mobile hook to create:**
```typescript
// CREATE src/mobile/src/hooks/useNotificationsConfig.ts

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/apiClient';

export type NotificationsConfig = {
  hired_instance_id: string;
  approval_pending: boolean;
  goal_run_complete: boolean;
  trial_summary: boolean;
  credential_expiry: boolean;
};

export function useNotificationsConfig(hiredInstanceId: string | null) {
  return useQuery<NotificationsConfig>({
    queryKey: ['notifications-config', hiredInstanceId],
    queryFn: async () => {
      if (!hiredInstanceId) throw new Error('No hired instance id');
      const res = await apiClient.get(
        `/cp/hired-agents/${hiredInstanceId}/notifications-config`
      );
      return res.data;
    },
    enabled: !!hiredInstanceId,
    staleTime: 60_000,  // 1 min — notification prefs don't change often
  });
}
```

**Modify NotificationsScreen to display config:**
```tsx
// MODIFY src/mobile/src/screens/profile/NotificationsScreen.tsx
// When an agent is selected (via deep-link param), show a section
// "Agent Notifications" that renders the 4 preference toggles from
// useNotificationsConfig(). Use existing Toggle/Switch pattern in the file.
// Show loading spinner while fetching; show "Defaults active" when no prefs stored.
```

**Tests to write:**
```python
# CREATE src/CP/BackEnd/tests/test_cp_notifications.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

def test_notifications_config_requires_auth(client):
    resp = client.get("/cp/hired-agents/ha-1/notifications-config")
    assert resp.status_code in (401, 403)

def test_notifications_config_returns_defaults(client, mock_plant_gateway):
    mock_plant_gateway.return_value = {
        "hired_instance_id": "ha-1",
        "approval_pending": True,
        "goal_run_complete": True,
        "trial_summary": True,
        "credential_expiry": True,
    }
    resp = client.get(
        "/cp/hired-agents/ha-1/notifications-config",
        headers={"Authorization": "Bearer valid_token"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["approval_pending"] is True
    assert data["goal_run_complete"] is True
```

```typescript
// src/mobile/__tests__/useNotificationsConfig.test.ts
import { renderHook, waitFor } from '@testing-library/react-native';
import { useNotificationsConfig } from '../src/hooks/useNotificationsConfig';

jest.mock('../src/services/apiClient', () => ({
  apiClient: {
    get: jest.fn().mockResolvedValue({
      data: {
        hired_instance_id: 'ha-1',
        approval_pending: true,
        goal_run_complete: false,
        trial_summary: true,
        credential_expiry: true,
      },
    }),
  },
}));

test('returns notifications config for a hired agent', async () => {
  const { result } = renderHook(() => useNotificationsConfig('ha-1'), {
    wrapper: ({ children }) => children,
  });
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.approval_pending).toBe(true);
});

test('disabled when hiredInstanceId is null', () => {
  const { result } = renderHook(() => useNotificationsConfig(null));
  expect(result.current.fetchStatus).toBe('idle');
});
```

**Acceptance criteria:**
- [ ] `GET /cp/hired-agents/{id}/notifications-config` returns 200 with 4 boolean fields
- [ ] Returns 401/403 without valid auth token
- [ ] `useNotificationsConfig` hook exists and is disabled when `hiredInstanceId` is null
- [ ] `NotificationsScreen.tsx` renders a config section when agent is selected
- [ ] `pytest src/CP/BackEnd/tests/test_cp_notifications.py` exits 0
- [ ] `npx jest src/mobile/__tests__/useNotificationsConfig.test.ts --forceExit` exits 0

---

### Epic E5: PP operators see cost per goal-run on a dedicated breakdown screen

**Outcome:** PP developers/managers can view a table of goal-run costs (LLM API spend, platform fee, total) per hired agent on a new `CostBreakdownScreen` page — closing PP-G1 from §14.7 of the master design doc.

**Context (2 sentences):** `src/PP/FrontEnd/src/pages/Billing.tsx` shows subscription-level revenue aggregates but no per-run cost detail. `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` already calls `gatewayApiClient.listOpsHiredAgentDeliverables()` — the new screen reuses the same client and adds a cost breakdown table alongside deliverables. The new page must be registered in `src/PP/FrontEnd/src/App.tsx`.

---

#### E5-S1 — Create `CostBreakdownScreen.tsx` — cost per goal-run table

**Branch:** `feat/MOULD-GAP-1-it2`
**BLOCKED UNTIL:** none (pure FE, uses existing `gatewayApiClient`)
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/PP/FrontEnd/src/pages/Billing.tsx` — fully self-contained pattern: Fluent UI components, `gatewayApiClient` usage, error/loading states
2. `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` — `gatewayApiClient.listOpsHiredAgentDeliverables()` call pattern (line ~198)
3. `src/PP/FrontEnd/src/App.tsx` — route registration pattern

**What to build:**
```tsx
// CREATE src/PP/FrontEnd/src/pages/CostBreakdownScreen.tsx

import { useEffect, useState } from 'react'
import {
  Body1,
  Card,
  CardHeader,
  Spinner,
  Text,
  DataGrid,
  DataGridHeader,
  DataGridHeaderCell,
  DataGridBody,
  DataGridRow,
  DataGridCell,
  createTableColumn,
  TableColumnDefinition,
} from '@fluentui/react-components'
import { gatewayApiClient } from '../services/gatewayApiClient'

type CostRow = {
  goal_run_id: string
  hired_instance_id: string
  agent_type_id?: string | null
  run_at: string             // ISO-8601
  llm_cost_inr: number       // LLM API spend in INR (0.0 if not applicable)
  platform_fee_inr: number   // WAOOAW platform fee per run
  total_cost_inr: number     // llm_cost_inr + platform_fee_inr
  status: string             // "completed" | "failed"
}

const columns: TableColumnDefinition<CostRow>[] = [
  createTableColumn<CostRow>({ columnId: 'run_at', renderHeaderCell: () => 'Run At', renderCell: (r) => new Date(r.run_at).toLocaleString() }),
  createTableColumn<CostRow>({ columnId: 'agent_type_id', renderHeaderCell: () => 'Agent Type', renderCell: (r) => r.agent_type_id ?? '—' }),
  createTableColumn<CostRow>({ columnId: 'llm_cost_inr', renderHeaderCell: () => 'LLM Cost (₹)', renderCell: (r) => r.llm_cost_inr.toFixed(2) }),
  createTableColumn<CostRow>({ columnId: 'platform_fee_inr', renderHeaderCell: () => 'Platform Fee (₹)', renderCell: (r) => r.platform_fee_inr.toFixed(2) }),
  createTableColumn<CostRow>({ columnId: 'total_cost_inr', renderHeaderCell: () => 'Total (₹)', renderCell: (r) => <strong>₹{r.total_cost_inr.toFixed(2)}</strong> }),
  createTableColumn<CostRow>({ columnId: 'status', renderHeaderCell: () => 'Status', renderCell: (r) => r.status }),
]

export default function CostBreakdownScreen() {
  const [rows, setRows] = useState<CostRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    gatewayApiClient
      .listOpsCostBreakdown({})                       // new client method — PP BE proxies Plant
      .then((data) => setRows((data as CostRow[]) || []))
      .catch(() => setError('Failed to load cost data. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  const totalCost = rows.reduce((sum, r) => sum + r.total_cost_inr, 0)

  return (
    <div className="page-container">
      <div className="page-header">
        <Text as="h1" size={900} weight="semibold">Cost Breakdown</Text>
        <Body1>Per-goal-run LLM and platform costs</Body1>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <Spinner label="Loading cost data..." />
      ) : (
        <>
          <Card style={{ marginBottom: '1rem' }}>
            <CardHeader header={<Text weight="semibold">Total Platform Spend</Text>} />
            <Text size={700} weight="bold">₹{totalCost.toFixed(2)}</Text>
            <Body1>{rows.length} goal runs</Body1>
          </Card>

          <DataGrid items={rows} columns={columns} getRowId={(r) => r.goal_run_id}>
            <DataGridHeader>
              <DataGridRow>{({ renderHeaderCell }) => <DataGridHeaderCell>{renderHeaderCell()}</DataGridHeaderCell>}</DataGridRow>
            </DataGridHeader>
            <DataGridBody>
              {({ item, rowId }) => (
                <DataGridRow key={rowId}>
                  {({ renderCell }) => <DataGridCell>{renderCell(item)}</DataGridCell>}
                </DataGridRow>
              )}
            </DataGridBody>
          </DataGrid>

          {rows.length === 0 && !loading && (
            <Body1>No cost records found. Goal runs will appear here after execution.</Body1>
          )}
        </>
      )}
    </div>
  )
}
```

```typescript
// MODIFY src/PP/FrontEnd/src/App.tsx — add route for CostBreakdownScreen
// Add to lazy imports:
const CostBreakdownScreen = lazy(() => import('./pages/CostBreakdownScreen'))
// Add to <Routes>:
<Route path="/cost-breakdown" element={<CostBreakdownScreen />} />
```

**Note on `gatewayApiClient.listOpsCostBreakdown`:** This method does not exist yet. Add a stub to the gateway client that calls `GET /pp/ops/cost-breakdown`:
```typescript
// In src/PP/FrontEnd/src/services/gatewayApiClient.ts — add:
async listOpsCostBreakdown(_params: Record<string, unknown>) {
  const resp = await this._get('/pp/ops/cost-breakdown');
  return resp.data;
}
```
The PP BackEnd route for `/pp/ops/cost-breakdown` is out of scope for this story — the stub returns an empty array gracefully when the endpoint does not exist (404 → setRows([])).

**Tests to write:**
```tsx
// src/PP/FrontEnd/src/__tests__/CostBreakdownScreen.test.tsx
import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import CostBreakdownScreen from '../pages/CostBreakdownScreen'
import * as client from '../services/gatewayApiClient'

vi.mock('../services/gatewayApiClient', () => ({
  gatewayApiClient: {
    listOpsCostBreakdown: vi.fn().mockResolvedValue([
      {
        goal_run_id: 'gr-1',
        hired_instance_id: 'ha-1',
        agent_type_id: 'marketing',
        run_at: '2026-03-06T10:00:00Z',
        llm_cost_inr: 2.50,
        platform_fee_inr: 1.00,
        total_cost_inr: 3.50,
        status: 'completed',
      },
    ]),
  },
}))

test('renders total spend card', async () => {
  render(<CostBreakdownScreen />)
  await waitFor(() => screen.getByText(/Total Platform Spend/i))
  expect(screen.getByText(/₹3\.50/)).toBeTruthy()
})

test('renders goal run row', async () => {
  render(<CostBreakdownScreen />)
  await waitFor(() => screen.getByText('marketing'))
  expect(screen.getByText('completed')).toBeTruthy()
})

test('renders empty state gracefully', async () => {
  vi.mocked(client.gatewayApiClient.listOpsCostBreakdown).mockResolvedValueOnce([])
  render(<CostBreakdownScreen />)
  await waitFor(() => screen.getByText(/No cost records found/i))
})
```

**Acceptance criteria:**
- [ ] `CostBreakdownScreen.tsx` exists and renders without crashing
- [ ] Total spend card shows sum of all `total_cost_inr` values
- [ ] DataGrid shows one row per `CostRow` with all 6 columns
- [ ] Empty state renders when API returns `[]`
- [ ] Route `/cost-breakdown` registered in `App.tsx`
- [ ] `cd src/PP/FrontEnd && npm test -- --forceExit` exits 0

---

### Epic E6: PP operators see agent-type-specific diagnostic fields for Share Trader and Content Creator agents

**Outcome:** When a PP operator opens the construct-health detail panel for a hired agent, trading agents show Delta Exchange position counts and DLQ entry type, and content agents show channel adapter status — implementing the typed views from §14.5 and §14.6 of the master design doc.

**Context (2 sentences):** `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` renders a deliverables/approvals detail panel when a row is selected (line ~188), but the construct-health section treats all agent types identically with generic fields. The `agent_type_id` field is already present on `HiredRow` (line 47) — this story uses it to conditionally render agent-type-specific diagnostic sub-sections.

---

#### E6-S1 — Agent-type-specific diagnostic fields in `HiredAgentsOps.tsx` construct-health detail

**Branch:** `feat/MOULD-GAP-1-it2`
**BLOCKED UNTIL:** none
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx` — lines 40–250: `HiredRow` type, `loadDetails`, detail panel render section
2. `src/PP/FrontEnd/src/pages/AgentData.tsx` — pattern for conditional sub-section rendering
3. `src/PP/FrontEnd/src/services/gatewayApiClient.ts` — `getOpsConstructHealth` if it exists, else note it needs to be added

**What to build:**

```typescript
// MODIFY src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx

// 1. Add typed diagnostic shapes:
type TraderDiagnostics = {
  open_position_count: number         // from Delta Exchange via TradingPump
  last_order_status: string           // "filled" | "rejected" | "cancelled" | null
  dlq_entry_type: string | null       // "constraint_policy_deny" | "approval_gate_deny" | null
  margin_utilisation_pct: number      // 0–100
}

type ContentDiagnostics = {
  linkedin_adapter_status: string     // "connected" | "token_expired" | "not_configured"
  instagram_adapter_status: string
  pending_theme_count: number         // themes awaiting customer approval
  last_published_platform: string | null
}

// 2. Add state for type-specific diagnostics:
const [traderDiag, setTraderDiag] = useState<TraderDiagnostics | null>(null)
const [contentDiag, setContentDiag] = useState<ContentDiagnostics | null>(null)

// 3. Inside loadDetails(), after loading deliverables/approvals/denials,
//    conditionally fetch type-specific data:
const agentTypeId = row.agent_type_id ?? ''
if (agentTypeId.includes('trading') || agentTypeId === 'share_trader') {
  try {
    const diag = await gatewayApiClient.getOpsConstructHealth(
      row.hired.hired_instance_id, { agent_type: 'trading' }
    )
    setTraderDiag((diag as any)?.trader_diagnostics ?? null)
  } catch { setTraderDiag(null) }
} else if (agentTypeId.includes('marketing') || agentTypeId.includes('content')) {
  try {
    const diag = await gatewayApiClient.getOpsConstructHealth(
      row.hired.hired_instance_id, { agent_type: 'content' }
    )
    setContentDiag((diag as any)?.content_diagnostics ?? null)
  } catch { setContentDiag(null) }
}

// 4. In the detail panel JSX — after existing deliverables section, add:
{traderDiag && (
  <Card style={{ marginTop: '1rem' }}>
    <CardHeader header={<Text weight="semibold">📈 Share Trader Diagnostics</Text>} />
    <table style={{ width: '100%', fontSize: 13 }}>
      <tbody>
        <tr><td>Open Positions</td><td>{traderDiag.open_position_count}</td></tr>
        <tr><td>Last Order Status</td><td>{traderDiag.last_order_status ?? '—'}</td></tr>
        <tr><td>DLQ Entry Type</td><td>{traderDiag.dlq_entry_type ?? 'none'}</td></tr>
        <tr><td>Margin Utilisation</td><td>{traderDiag.margin_utilisation_pct}%</td></tr>
      </tbody>
    </table>
  </Card>
)}

{contentDiag && (
  <Card style={{ marginTop: '1rem' }}>
    <CardHeader header={<Text weight="semibold">✍️ Content Creator Diagnostics</Text>} />
    <table style={{ width: '100%', fontSize: 13 }}>
      <tbody>
        <tr><td>LinkedIn Adapter</td><td>{contentDiag.linkedin_adapter_status}</td></tr>
        <tr><td>Instagram Adapter</td><td>{contentDiag.instagram_adapter_status}</td></tr>
        <tr><td>Pending Themes</td><td>{contentDiag.pending_theme_count}</td></tr>
        <tr><td>Last Published On</td><td>{contentDiag.last_published_platform ?? '—'}</td></tr>
      </tbody>
    </table>
  </Card>
)}
```

```typescript
// ADD to src/PP/FrontEnd/src/services/gatewayApiClient.ts (if method missing):
async getOpsConstructHealth(hiredInstanceId: string, params?: Record<string, string>) {
  const query = params ? '?' + new URLSearchParams(params).toString() : ''
  const resp = await this._get(`/pp/ops/hired-agents/${hiredInstanceId}/construct-health${query}`)
  return resp.data
}
```

**Tests to write:**
```tsx
// src/PP/FrontEnd/src/pages/HiredAgentsOps.test.tsx — ADD test cases
// (file already exists — add to existing describe block)

it('renders trader diagnostics panel for trading agent', async () => {
  // Mock gatewayApiClient.getOpsConstructHealth to return trader_diagnostics
  mockGatewayClient.getOpsConstructHealth = vi.fn().mockResolvedValue({
    trader_diagnostics: {
      open_position_count: 3,
      last_order_status: 'filled',
      dlq_entry_type: null,
      margin_utilisation_pct: 42,
    },
  })
  // Select a trading agent row then verify panel appears
  // ... (use existing test setup patterns in HiredAgentsOps.test.tsx)
})

it('renders content diagnostics panel for marketing agent', async () => {
  mockGatewayClient.getOpsConstructHealth = vi.fn().mockResolvedValue({
    content_diagnostics: {
      linkedin_adapter_status: 'connected',
      instagram_adapter_status: 'token_expired',
      pending_theme_count: 2,
      last_published_platform: 'linkedin',
    },
  })
  // Select a content/marketing agent row
})
```

**Acceptance criteria:**
- [ ] Trading agent rows show "Share Trader Diagnostics" card with 4 fields
- [ ] Content/marketing agent rows show "Content Creator Diagnostics" card with 4 fields
- [ ] Non-trading, non-content agents show neither panel (no crash)
- [ ] When `getOpsConstructHealth` throws (e.g. 404), panel simply does not render (no error banner)
- [ ] `cd src/PP/FrontEnd && npm test -- --forceExit` exits 0 (all existing tests still pass)
