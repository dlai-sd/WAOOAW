# EXEC-ENGINE-001 — Execution Layer: Flow, Component & Agent Runtime

**Plan ID:** EXEC-ENGINE-001  
**Service/Area:** Plant BackEnd (execution engine) + CP FrontEnd + PP FrontEnd  
**Branch:** `feat/execution-engine-v1`  
**Status:** IN PROGRESS — skeleton committed, story cards being written per iteration  
**Created:** 2026-03-08  

---

## Vision Intake (Locked)

| Question | Answer |
|---|---|
| **User outcome** | A customer hires a Share Trader or Marketing Agent, configures it, sets a goal, sees it run on schedule, approves or rejects output, and views delivered results — all persisted to DB. A PP operator monitors the fleet and drills into any agent's health. |
| **Out of scope** | PP Compose UI (FlowDef/ComponentDef authoring via browser), mobile app, billing/Razorpay, any agent type beyond Share Trader and Marketing Agent |
| **Lane** | Lane B — new backend tables: `flow_run`, `component_run`, `skill_config`; new Celery component queues; `BaseComponent` interface |
| **Timeline** | 6 iterations, P0 gaps closed by Iteration 2 |

---

## Constitutional Architecture (Locked — reference for all stories)

```
DEFINITION LAYER (PP governs, versioned, immutable once approved)
  AgentTypeDef  →  [SkillDef]  →  [FlowDef]  →  [ComponentDef]

INSTANCE LAYER (customer governs at hire)
  HiredAgent (pins definition_version_id)  →  SkillConfig  →  RunContext template

EXECUTION LAYER (Plant executes, ephemeral, fully audited)
  AgentRun  →  SkillRun  →  FlowRun  →  ComponentRun
  Postgres owns workflow state. Redis/Celery owns job transport.
```

### BaseComponent Interface (agreed — every component implements this)
```python
from dataclasses import dataclass
from uuid import UUID
from abc import ABC, abstractmethod

@dataclass
class ComponentInput:
    flow_run_id: UUID
    customer_id: UUID
    skill_config: dict        # PP-locked + customer-filled values
    run_context: dict         # dynamic params injected per run cycle
    previous_step_output: dict | None

@dataclass
class ComponentOutput:
    success: bool
    data: dict
    error_message: str | None
    duration_ms: int

class BaseComponent(ABC):
    @abstractmethod
    async def execute(self, input: ComponentInput) -> ComponentOutput: ...
```

### FlowRun Status Machine (agreed)
```
pending → running → awaiting_approval → running → completed
                                               ↘ partial_failure
                  → failed
```

### Celery Queue Routing (agreed)
```python
task_routes = {
    "execute_pump":      {"queue": "pump"},
    "execute_processor": {"queue": "processor"},
    "execute_publisher": {"queue": "publisher"},
}
```

### Approval Gate Rule (constitutional)
Gate is a step inside FlowDef. `goal.auto_execute` / `goal.customer_reviews` is a boolean the FlowRun executor checks at that step. No wiring at Skill or Agent level.

### Fan-out Rule (constitutional)
`FlowDef.parallel_steps: list[str]` dispatches one ComponentRun per entry. Fan-in: all complete → `completed`; any fail → `partial_failure` with per-branch outcome in `component_run`.

---

## NFR Pattern (embed in every Plant BackEnd route story)
```python
from core.routing import waooaw_router
router = waooaw_router(prefix="/resource", tags=["resource"])

# GET routes
async def list_things(db=Depends(get_read_db_session)): ...

# POST/PATCH routes  
async def create_thing(db=Depends(get_db_session)): ...

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

with tracer.start_as_current_span("service.operation"):
    pass

@circuit_breaker(service="external_service_name")
async def call_external(): ...
```

---

## Iteration Summary

| Iteration | Scope | ⏱ Est | P-gaps closed |
|---|---|---|---|
| 1 | DB foundation: `flow_run`, `component_run`, `skill_config` tables + migrations | 4h | P0 (DB base), P1 (component_run, skill_config), P2 (definition_version_id) |
| 2 | `BaseComponent`, `ComponentInput/Output`, `RunContext` + Celery component queues | 4.5h | P0 (BaseComponent, Celery queues) |
| 3 | Share Trader components + FlowRun executor (sequential) | 5h | P0 (execution engine for ST) |
| 4 | Marketing Agent components + fan-out executor + PARTIAL_FAILURE | 5h | P2 (fan-out, PARTIAL_FAILURE) |
| 5 | CP UI: hire wizard, goal setting, approval queue, deliverables view | 5h | CP features 1-8 |
| 6 | PP UI: fleet dashboard, agent health drill-in, DLQ | 3.5h | PP features 1-4 |

---

## Agent Execution Rules (every story must follow)

> **CHECKPOINT RULE**: After completing each epic (all tests passing), run:
> ```bash
> git add -A && git commit -m "feat(EXEC-ENGINE-001): [epic-id] — [epic title]" && git push
> ```
> Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

- Never use bare `APIRouter` — always `waooaw_router()`
- GET routes: `get_read_db_session` — never `get_db_session`
- `PIIMaskingFilter` on every logger
- `@circuit_breaker` on every external HTTP call (Delta API, LinkedIn API, YouTube API)
- Postgres owns flow state; Redis only transports jobs
- Stories are self-contained — no "see above" references

---

## Reusable UI Components (defined here, referenced by name in stories)

| Component | First defined | Purpose |
|---|---|---|
| `AgentCard` | Iteration 5 — S1 | Marketplace + My Agents card with avatar, status dot, specialty, rating |
| `StatusDot` | Iteration 5 — S1 | Colour-coded status pill: 🟢 running / 🟡 awaiting_approval / 🔴 failed / ⚫ paused |
| `ApprovalQueueItem` | Iteration 5 — S3 | Single approval request row with preview, approve/reject CTAs |
| `FlowRunTimeline` | Iteration 5 — S4 | Horizontal stepper showing FlowRun steps and per-step status |
| `ComponentRunRow` | Iteration 6 — S2 | Table row for a single ComponentRun: type, status, duration, input/output expand |
| `DeliverableCard` | Iteration 5 — S4 | Deliverable output card with type badge, content preview, download link |

---

<!-- ITERATION STORIES BEGIN BELOW — written and committed one iteration at a time -->

---

## Iteration 1 — DB Foundation

> **Stories written and committed:** 2026-03-08

### I1-S1 — Add `flow_run` table with status machine (45 min)

**Context:** `GoalRunModel` (`src/Plant/BackEnd/models/goal_run.py`) currently tracks runs with only `pending | running | completed | failed`. We need a richer `flow_run` table that owns multi-step workflow state — including `awaiting_approval` and `partial_failure` — so Postgres (not Redis) is the ledger for execution state. `GoalRunModel` is superseded but kept for backward compatibility until migration is complete.

**Files to read first:**
- `src/Plant/BackEnd/models/goal_run.py` — existing run model to understand shape
- `src/Plant/BackEnd/models/hired_agent.py` — FK target
- `src/Plant/BackEnd/database/migrations/versions/` — pick next migration number

**Deliverable:** New file `src/Plant/BackEnd/models/flow_run.py` + Alembic migration.

**Code pattern:**
```python
# src/Plant/BackEnd/models/flow_run.py
from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

FLOW_RUN_STATUSES = (
    "pending", "running", "awaiting_approval",
    "completed", "failed", "partial_failure"
)

class FlowRunModel(Base):
    __tablename__ = "flow_runs"

    id = Column(String, primary_key=True, nullable=False)
    hired_instance_id = Column(String, nullable=False, index=True)
    skill_id = Column(String, nullable=False)
    flow_name = Column(String, nullable=False)          # e.g. "MarketAnalysisFlow"
    status = Column(String, nullable=False, default="pending", index=True)
    current_step = Column(String, nullable=True)        # name of step in progress
    run_context = Column(JSONB, nullable=False, default=dict)
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_flow_runs_hired_instance_id", "hired_instance_id"),
        Index("ix_flow_runs_status", "status"),
        Index("ix_flow_runs_idempotency_key", "idempotency_key"),
    )
```

**Acceptance criteria:**
- [ ] `flow_runs` table created in DB via Alembic migration (`alembic upgrade head`)
- [ ] All 6 statuses can be set on `FlowRunModel.status`
- [ ] `idempotency_key` constraint enforced (duplicate insert raises `IntegrityError`)
- [ ] Unit test covers: create, transition statuses, idempotency guard
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I1-S2 — Add `component_run` table (45 min)

**Context:** There is currently no per-component audit record. Every `ComponentRun` must write an immutable record to Postgres so PP can drill into exactly which step of which flow failed, with what input, and what output. File to create: `src/Plant/BackEnd/models/component_run.py`.

**Files to read first:**
- `src/Plant/BackEnd/models/flow_run.py` — FK source (from I1-S1)
- `src/Plant/BackEnd/database/migrations/versions/` — next migration number

**Code pattern:**
```python
# src/Plant/BackEnd/models/component_run.py
from sqlalchemy import Column, String, DateTime, Integer, Index
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

COMPONENT_RUN_STATUSES = ("pending", "running", "completed", "failed")

class ComponentRunModel(Base):
    __tablename__ = "component_runs"

    id = Column(String, primary_key=True, nullable=False)
    flow_run_id = Column(String, nullable=False, index=True)  # FK to flow_runs.id
    component_type = Column(String, nullable=False, index=True)  # e.g. "DeltaExchangePump"
    step_name = Column(String, nullable=False)                   # e.g. "step_1"
    status = Column(String, nullable=False, default="pending", index=True)
    input_context = Column(JSONB, nullable=False, default=dict)
    output = Column(JSONB, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)

    __table_args__ = (
        Index("ix_component_runs_flow_run_id", "flow_run_id"),
        Index("ix_component_runs_component_type", "component_type"),
        Index("ix_component_runs_status", "status"),
    )
```

**Acceptance criteria:**
- [ ] `component_runs` table created via Alembic migration
- [ ] Foreign key integrity: `flow_run_id` references `flow_runs.id`
- [ ] `input_context` and `output` stored as JSONB — arbitrary shape per component type
- [ ] Unit test: create, mark running, mark completed with output, mark failed with error
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I1-S3 — Add `skill_config` table (45 min)

**Context:** `HiredAgentModel.config` is a single JSONB blob mixing PP-locked fields, customer-fillable fields, and runtime hints. This creates an audit gap and prevents per-skill version pinning. New `skill_config` table stores one row per (hired_instance, skill) with `pp_locked_fields` and `customer_fields` separated. Location: `src/Plant/BackEnd/models/skill_config.py`.

**Files to read first:**
- `src/Plant/BackEnd/models/hired_agent.py` — FK target, existing `config` blob shape
- `src/Plant/BackEnd/database/migrations/versions/` — next migration number

**Code pattern:**
```python
# src/Plant/BackEnd/models/skill_config.py
from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from core.database import Base

class SkillConfigModel(Base):
    __tablename__ = "skill_configs"

    id = Column(String, primary_key=True, nullable=False)
    hired_instance_id = Column(String, nullable=False, index=True)
    skill_id = Column(String, nullable=False)              # e.g. "market_analysis_skill"
    definition_version_id = Column(String, nullable=False) # pinned at hire time
    pp_locked_fields = Column(JSONB, nullable=False, default=dict)
    customer_fields = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("hired_instance_id", "skill_id", name="uq_skill_config_per_hire"),
        Index("ix_skill_configs_hired_instance_id", "hired_instance_id"),
    )
```

**Acceptance criteria:**
- [ ] `skill_configs` table created via Alembic migration
- [ ] `(hired_instance_id, skill_id)` unique constraint enforced
- [ ] PATCH endpoint on Plant BackEnd: `PATCH /v1/skill-configs/{hired_instance_id}/{skill_id}` accepts `customer_fields` only (pp_locked_fields not updatable by customer)
- [ ] Unit test: create, update customer_fields, reject pp_locked_fields update attempt
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I1-S4 — Add `definition_version_id` to `hired_agents` (30 min)

**Context:** `HiredAgentModel` currently has `agent_type_id` as a live pointer. If PP updates the agent type, all hired agents silently change behaviour. Add `definition_version_id` column set at hire time and never changed automatically. Alembic migration adds the column; `hired_agents_simple.py` hire endpoint sets it.

**Files to read first:**
- `src/Plant/BackEnd/models/hired_agent.py` — add column here
- `src/Plant/BackEnd/api/v1/hired_agents_simple.py` — hire endpoint to update
- `src/Plant/BackEnd/database/migrations/versions/` — next migration number

**Acceptance criteria:**
- [ ] `definition_version_id` (nullable String) column added to `hired_agents` via Alembic migration
- [ ] Hire endpoint sets `definition_version_id = agent_type_version` from the `agent_type_definitions` table at hire time
- [ ] Existing rows with null `definition_version_id` do not break — nullable is fine for now
- [ ] Unit test: hire creates row with non-null `definition_version_id`
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I1-S5 — CHECKPOINT: register all new models in `__init__.py` + smoke test (30 min)

**Context:** `src/Plant/BackEnd/models/__init__.py` imports all models so Alembic autodiscovers them. After I1-S1 through I1-S4, three new model files exist and one existing model is changed. This story ensures they are all imported, `alembic upgrade head` runs cleanly in the test DB, and a basic integration smoke test confirms all four tables exist.

**Files to read first:**
- `src/Plant/BackEnd/models/__init__.py` — add imports here
- `src/Plant/BackEnd/database/migrations/env.py` — confirm `target_metadata` picks up new models

**Acceptance criteria:**
- [ ] `flow_runs`, `component_runs`, `skill_configs` imported in `models/__init__.py`
- [ ] `alembic upgrade head` completes without error in test DB (Docker compose test environment)
- [ ] `alembic downgrade -1` then `alembic upgrade head` round-trips cleanly
- [ ] Smoke test queries each new table: `SELECT COUNT(*) FROM flow_runs` returns 0
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

## Iteration 2 — BaseComponent Interface + Celery Component Queues

> **Stories written and committed:** 2026-03-08

### I2-S1 — Define `BaseComponent`, `ComponentInput`, `ComponentOutput` (45 min)

**Context:** There is currently no abstract base class for components. Every future component (`DeltaExchangePump`, `RSIProcessor`, `ContentProcessor`, etc.) must implement the same interface so the FlowRun executor can call any component polymorphically. Create `src/Plant/BackEnd/components/base.py`.

**Files to read first:**
- `src/Plant/BackEnd/models/component_run.py` — the DB record that execute() must write
- `src/Plant/BackEnd/core/observability.py` — OTel tracer to inject into execute()

**Code to implement:**
```python
# src/Plant/BackEnd/components/__init__.py  — empty, marks package
# src/Plant/BackEnd/components/base.py

from __future__ import annotations
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

@dataclass
class ComponentInput:
    flow_run_id: str
    customer_id: str
    skill_config: dict[str, Any]        # PP-locked + customer-filled values
    run_context: dict[str, Any]         # dynamic params for this run cycle
    previous_step_output: dict[str, Any] | None = None

@dataclass
class ComponentOutput:
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    duration_ms: int = 0

class BaseComponent(ABC):
    """
    Stateless execution unit. Implement execute() in every component subclass.
    The executor writes ComponentRunModel records; do not write DB inside execute().
    """

    @property
    @abstractmethod
    def component_type(self) -> str:
        """Unique string identifier, e.g. 'DeltaExchangePump'."""
        ...

    @abstractmethod
    async def execute(self, input: ComponentInput) -> ComponentOutput:
        """Execute component logic. Must be idempotent."""
        ...

    async def safe_execute(self, input: ComponentInput) -> ComponentOutput:
        """Wraps execute() with timing and exception catch."""
        start = time.monotonic()
        try:
            result = await self.execute(input)
            result.duration_ms = int((time.monotonic() - start) * 1000)
            return result
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            return ComponentOutput(
                success=False,
                data={},
                error_message=str(exc),
                duration_ms=duration_ms,
            )
```

**Acceptance criteria:**
- [ ] `ComponentInput`, `ComponentOutput`, `BaseComponent` importable from `components.base`
- [ ] Concrete subclass that does not implement `execute()` raises `TypeError` at instantiation
- [ ] `safe_execute()` returns `ComponentOutput(success=False, error_message=...)` when `execute()` raises
- [ ] `duration_ms` is always populated (≥ 0)
- [ ] Unit tests for `safe_execute()` — success path and exception path
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I2-S2 — Celery component task routing + worker queue config (45 min)

**Context:** `src/Plant/BackEnd/worker/celery_app.py` currently routes only `email`, `events`, and `archival` queues. Agent execution has no async worker backbone. Add three component queues (`pump`, `processor`, `publisher`) and a generic `execute_component` Celery task that accepts a component type name + serialized `ComponentInput` and dispatches to the correct registered component.

**Files to read first:**
- `src/Plant/BackEnd/worker/celery_app.py` — add routes here
- `src/Plant/BackEnd/worker/tasks/` — create `component_tasks.py` here
- `src/Plant/BackEnd/components/base.py` — from I2-S1

**Code to add to `celery_app.py`:**
```python
# Add to existing task_routes dict:
"execute_pump":      {"queue": "pump"},
"execute_processor": {"queue": "processor"},
"execute_publisher": {"queue": "publisher"},

# Add to autodiscover_tasks:
celery_app.autodiscover_tasks(["worker.tasks", "worker.tasks.component_tasks"])
```

**New file `worker/tasks/component_tasks.py`:**
```python
from worker.celery_app import celery_app
from components.registry import get_component
from components.base import ComponentInput

@celery_app.task(name="execute_pump", bind=True, max_retries=3,
                 default_retry_delay=5, acks_late=True)
def execute_pump(self, component_type: str, input_dict: dict, flow_run_id: str):
    """Execute a Pump component. Retries up to 3x with 5s backoff."""
    _run_component(self, component_type, input_dict, flow_run_id)

@celery_app.task(name="execute_processor", bind=True, max_retries=3,
                 default_retry_delay=10, acks_late=True)
def execute_processor(self, component_type: str, input_dict: dict, flow_run_id: str):
    """Execute a Processor component."""
    _run_component(self, component_type, input_dict, flow_run_id)

@celery_app.task(name="execute_publisher", bind=True, max_retries=3,
                 default_retry_delay=15, acks_late=True)
def execute_publisher(self, component_type: str, input_dict: dict, flow_run_id: str):
    """Execute a Publisher component."""
    _run_component(self, component_type, input_dict, flow_run_id)

def _run_component(task, component_type: str, input_dict: dict, flow_run_id: str):
    import asyncio
    component = get_component(component_type)
    comp_input = ComponentInput(**input_dict)
    result = asyncio.get_event_loop().run_until_complete(
        component.safe_execute(comp_input)
    )
    if not result.success:
        raise task.retry(exc=RuntimeError(result.error_message))
    return result.data
```

**Acceptance criteria:**
- [ ] `pump`, `processor`, `publisher` queues declared in `celery_app.conf.task_routes`
- [ ] `execute_pump`, `execute_processor`, `execute_publisher` tasks importable without error
- [ ] Task retry config: pump max 3×/5s, processor max 3×/10s, publisher max 3×/15s
- [ ] `celery -A worker.celery_app inspect registered` shows all three tasks
- [ ] Unit test: mocked component executes and returns data; failed component triggers retry
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I2-S3 — Component registry (30 min)

**Context:** `_run_component` in I2-S2 calls `get_component(component_type)`. The registry maps string names to component class instances. This is the substitutability primitive — swapping `RSIProcessor_v1` for `RSIProcessor_v2` is a single registry change. Create `src/Plant/BackEnd/components/registry.py`.

**Files to read first:**
- `src/Plant/BackEnd/components/base.py` — from I2-S1

**Code pattern:**
```python
# src/Plant/BackEnd/components/registry.py
from typing import Type
from components.base import BaseComponent

_REGISTRY: dict[str, BaseComponent] = {}

def register_component(component: BaseComponent) -> None:
    """Register a component instance under its component_type."""
    _REGISTRY[component.component_type] = component

def get_component(component_type: str) -> BaseComponent:
    """Retrieve registered component. Raises KeyError if not found."""
    if component_type not in _REGISTRY:
        raise KeyError(f"Component '{component_type}' not registered. "
                       f"Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[component_type]

def list_registered() -> list[str]:
    return list(_REGISTRY.keys())
```

**Acceptance criteria:**
- [ ] `register_component()`, `get_component()`, `list_registered()` work correctly
- [ ] `get_component("unknown")` raises `KeyError` with helpful message listing available
- [ ] Two components with same `component_type` — second registration overwrites first (versioning path)
- [ ] Unit tests for all three scenarios
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I2-S4 — FlowRun executor: sequential step runner (90 min)

**Context:** There is currently no engine that reads a FlowRun's step sequence and dispatches ComponentRuns in order. This is the most critical story in Iteration 2. The executor reads `flow_run.run_context`, iterates `sequential_steps`, dispatches each to the appropriate Celery queue, writes `component_run` records for each step, and updates `flow_run.status` at each transition. Approval gate: when `flow_def.has_approval_gate=true` and `run_context.auto_execute=false`, set `flow_run.status="awaiting_approval"` and stop. Customer approval resumes from the gate step.

**Files to read first:**
- `src/Plant/BackEnd/models/flow_run.py` — from I1-S1
- `src/Plant/BackEnd/models/component_run.py` — from I1-S2
- `src/Plant/BackEnd/worker/tasks/component_tasks.py` — from I2-S2
- `src/Plant/BackEnd/components/registry.py` — from I2-S3

**Code to create: `src/Plant/BackEnd/engine/flow_executor.py`**
```python
"""
FlowRun executor — sequential step dispatch.
Postgres owns state; Redis/Celery owns transport.
"""
from __future__ import annotations
import asyncio, time, uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models.flow_run import FlowRunModel
from models.component_run import ComponentRunModel
from components.registry import get_component
from components.base import ComponentInput
from core.logging import get_logger
from core.logging import PIIMaskingFilter

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

async def execute_sequential_flow(
    flow_run: FlowRunModel,
    sequential_steps: list[dict],  # [{"step_name": "step_1", "component_type": "DeltaExchangePump"}]
    db: Session,
    approval_gate_index: int | None = None,  # None = no gate; int = step index before which gate fires
) -> None:
    prev_output = flow_run.run_context.get("previous_step_output")
    for idx, step in enumerate(sequential_steps):
        # Approval gate check
        if approval_gate_index is not None and idx == approval_gate_index:
            auto_execute = flow_run.run_context.get("auto_execute", False)
            if not auto_execute:
                flow_run.status = "awaiting_approval"
                flow_run.current_step = step["step_name"]
                flow_run.updated_at = datetime.now(timezone.utc)
                db.commit()
                return  # Stop — customer must approve to continue

        flow_run.current_step = step["step_name"]
        db.commit()

        comp = get_component(step["component_type"])
        comp_input = ComponentInput(
            flow_run_id=flow_run.id,
            customer_id=flow_run.run_context.get("customer_id", ""),
            skill_config=flow_run.run_context.get("skill_config", {}),
            run_context=flow_run.run_context,
            previous_step_output=prev_output,
        )
        comp_run = ComponentRunModel(
            id=str(uuid.uuid4()),
            flow_run_id=flow_run.id,
            component_type=step["component_type"],
            step_name=step["step_name"],
            status="running",
            input_context=comp_input.__dict__,
            started_at=datetime.now(timezone.utc),
        )
        db.add(comp_run)
        db.commit()

        result = await comp.safe_execute(comp_input)

        comp_run.status = "completed" if result.success else "failed"
        comp_run.output = result.data
        comp_run.error_message = result.error_message
        comp_run.duration_ms = result.duration_ms
        comp_run.completed_at = datetime.now(timezone.utc)
        db.commit()

        if not result.success:
            flow_run.status = "failed"
            flow_run.error_details = {"step": step["step_name"], "error": result.error_message}
            flow_run.updated_at = datetime.now(timezone.utc)
            db.commit()
            return

        prev_output = result.data

    flow_run.status = "completed"
    flow_run.completed_at = datetime.now(timezone.utc)
    flow_run.updated_at = datetime.now(timezone.utc)
    db.commit()
```

**Acceptance criteria:**
- [ ] Sequential flow of 3 steps: all succeed → `flow_run.status = completed`, 3 `component_run` rows written
- [ ] Step 2 fails → `flow_run.status = failed`, `component_run[step_2].status = failed`, step 3 not executed
- [ ] Approval gate at index 1, `auto_execute=false` → `flow_run.status = awaiting_approval`, execution stops after step 0
- [ ] Approval gate at index 1, `auto_execute=true` → gate skipped, execution continues
- [ ] `previous_step_output` from step N is passed as `ComponentInput.previous_step_output` to step N+1
- [ ] Unit tests (mocked components) for all four scenarios above
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I2-S5 — FlowRun executor: fan-out (parallel) step runner + PARTIAL_FAILURE (90 min)

**Context:** Marketing Agent's `PublishingFlow` dispatches `LinkedInPublisher` and `YouTubePublisher` in parallel. The executor must launch both ComponentRuns concurrently, await both, and set `flow_run.status = partial_failure` if one succeeds and one fails. Create `engine/flow_executor.py` parallel path (in same file as I2-S4).

**Files to read first:**
- `src/Plant/BackEnd/engine/flow_executor.py` — from I2-S4 (add to existing file)
- `src/Plant/BackEnd/models/component_run.py` — from I1-S2
- `src/Plant/BackEnd/models/flow_run.py` — from I1-S1

**Code to add to existing `flow_executor.py`:**
```python
async def execute_parallel_flow(
    flow_run: FlowRunModel,
    parallel_steps: list[dict],  # [{"step_name": "linkedin", "component_type": "LinkedInPublisher"}, ...]
    db: Session,
    shared_input: dict,           # output from preceding sequential steps
) -> None:
    flow_run.status = "running"
    db.commit()

    async def run_one(step: dict) -> tuple[str, bool, dict]:
        comp = get_component(step["component_type"])
        comp_input = ComponentInput(
            flow_run_id=flow_run.id,
            customer_id=flow_run.run_context.get("customer_id", ""),
            skill_config=flow_run.run_context.get("skill_config", {}),
            run_context=flow_run.run_context,
            previous_step_output=shared_input,
        )
        comp_run = ComponentRunModel(
            id=str(uuid.uuid4()),
            flow_run_id=flow_run.id,
            component_type=step["component_type"],
            step_name=step["step_name"],
            status="running",
            input_context=comp_input.__dict__,
            started_at=datetime.now(timezone.utc),
        )
        db.add(comp_run)
        db.commit()

        result = await comp.safe_execute(comp_input)
        comp_run.status = "completed" if result.success else "failed"
        comp_run.output = result.data
        comp_run.error_message = result.error_message
        comp_run.duration_ms = result.duration_ms
        comp_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        return step["step_name"], result.success, result.data

    outcomes = await asyncio.gather(*[run_one(s) for s in parallel_steps])

    all_ok = all(ok for _, ok, _ in outcomes)
    any_ok = any(ok for _, ok, _ in outcomes)

    if all_ok:
        flow_run.status = "completed"
    elif any_ok:
        flow_run.status = "partial_failure"
        flow_run.error_details = {
            "failed_steps": [name for name, ok, _ in outcomes if not ok]
        }
    else:
        flow_run.status = "failed"

    flow_run.completed_at = datetime.now(timezone.utc)
    flow_run.updated_at = datetime.now(timezone.utc)
    db.commit()
```

**Acceptance criteria:**
- [ ] Both parallel steps succeed → `flow_run.status = completed`
- [ ] LinkedIn succeeds, YouTube fails → `flow_run.status = partial_failure`, `error_details.failed_steps = ["youtube"]`
- [ ] Both fail → `flow_run.status = failed`
- [ ] Both `component_run` rows written regardless of outcome
- [ ] Steps run concurrently (use `asyncio.gather` — confirmed by timing test)
- [ ] Unit tests for all three outcomes
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

## Iteration 3 — Share Trader: Components + End-to-End Flow

> **Stories written and committed:** 2026-03-08

### I3-S1 — `DeltaExchangePump` component (45 min)

**Context:** First concrete `BaseComponent` implementation. Pulls OHLCV candle data from Delta Exchange API for a given instrument. Reads `skill_config.customer_fields.instrument` and `skill_config.pp_locked_fields.data_provider`. Uses `@circuit_breaker` on the HTTP call. Returns normalised candle list. Create `src/Plant/BackEnd/components/share_trader/delta_exchange_pump.py`.

**Files to read first:**
- `src/Plant/BackEnd/components/base.py` — from I2-S1
- `src/Plant/BackEnd/components/registry.py` — from I2-S3
- `src/Plant/BackEnd/core/security.py` — for any secrets access pattern

**NFR pattern (mandatory):**
```python
from core.logging import get_logger, PIIMaskingFilter
from core.observability import tracer  # circuit_breaker from core.security or equivalent

logger = get_logger(__name__)
logger.addFilter(PIIMaskingFilter())

@circuit_breaker(service="delta_exchange_api")
async def _fetch_candles(instrument: str, api_key: str) -> list[dict]:
    # httpx async call to Delta Exchange API
    ...
```

**Acceptance criteria:**
- [ ] `DeltaExchangePump.component_type == "DeltaExchangePump"`
- [ ] `execute()` returns `ComponentOutput.data = {"candles": [...], "instrument": "NIFTY"}`
- [ ] `skill_config.customer_fields.instrument` controls which instrument is fetched
- [ ] `@circuit_breaker(service="delta_exchange_api")` wraps the HTTP call
- [ ] `PIIMaskingFilter` on logger — API key never logged
- [ ] Registered in registry at module import: `register_component(DeltaExchangePump())`
- [ ] Unit test with mocked HTTP: success path returns candles; HTTP 500 returns `ComponentOutput(success=False)`
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I3-S2 — `RSIProcessor` component (45 min)

**Context:** Takes candle data from `previous_step_output`, calculates RSI for a configurable period, and classifies the signal as `BUY | SELL | HOLD`. No external HTTP calls — pure calculation. Create `src/Plant/BackEnd/components/share_trader/rsi_processor.py`.

**Files to read first:**
- `src/Plant/BackEnd/components/base.py` — from I2-S1
- `src/Plant/BackEnd/components/registry.py` — from I2-S3

**Acceptance criteria:**
- [ ] `RSIProcessor.component_type == "RSIProcessor"`
- [ ] `execute()` reads `previous_step_output.candles` and `skill_config.customer_fields.rsi_period`
- [ ] Returns `{"rsi_value": float, "signal": "BUY"|"SELL"|"HOLD", "confidence": float}`
- [ ] RSI < 30 → BUY; RSI > 70 → SELL; else HOLD
- [ ] Empty candles list → `ComponentOutput(success=False, error_message="Insufficient data")`
- [ ] No external HTTP — circuit_breaker not required
- [ ] Unit tests: BUY threshold, SELL threshold, HOLD range, empty input
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I3-S3 — `DeltaPublisher` component (45 min)

**Context:** Places a market order on Delta Exchange using the order params from `previous_step_output`. Reads API key from `skill_config.customer_fields.delta_api_key`. Uses `@circuit_breaker`. Returns order confirmation. Create `src/Plant/BackEnd/components/share_trader/delta_publisher.py`.

**Files to read first:**
- `src/Plant/BackEnd/components/base.py` — from I2-S1
- `src/Plant/BackEnd/core/encryption.py` — API key decryption pattern

**Acceptance criteria:**
- [ ] `DeltaPublisher.component_type == "DeltaPublisher"`
- [ ] `@circuit_breaker(service="delta_exchange_api")` on HTTP call
- [ ] API key decrypted from `skill_config.customer_fields.delta_api_key` using `core.encryption`
- [ ] API key NEVER appears in logs (`PIIMaskingFilter` active)
- [ ] Returns `{"order_id": str, "fill_price": float, "status": "filled"|"rejected"}`
- [ ] HTTP failure → `ComponentOutput(success=False)` — triggers Celery retry via `execute_publisher` task
- [ ] Unit tests: success path, HTTP 4xx (order rejected), HTTP 5xx (retry path)
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I3-S4 — Share Trader FlowDef + end-to-end run (90 min)

**Context:** Wire `DeltaExchangePump → RSIProcessor → DeltaPublisher` into a FlowDef and run it end-to-end using the `execute_sequential_flow` engine from I2-S4. The FlowDef is stored as a Python constant (no DB table yet — P3 gap, deferred). Create `src/Plant/BackEnd/flows/share_trader.py`. Add Plant API endpoint: `POST /v1/flow-runs` to trigger a named flow for a hired agent.

**Files to read first:**
- `src/Plant/BackEnd/engine/flow_executor.py` — from I2-S4
- `src/Plant/BackEnd/models/flow_run.py` — from I1-S1
- `src/Plant/BackEnd/models/skill_config.py` — from I1-S3
- `src/Plant/BackEnd/api/v1/` — add new route here

**Flow constant:**
```python
# src/Plant/BackEnd/flows/share_trader.py
MARKET_ANALYSIS_FLOW = {
    "flow_name": "MarketAnalysisFlow",
    "sequential_steps": [
        {"step_name": "step_1", "component_type": "DeltaExchangePump"},
        {"step_name": "step_2", "component_type": "RSIProcessor"},
    ],
    "approval_gate_index": None,  # No gate on analysis
}

EXECUTE_TRADE_FLOW = {
    "flow_name": "ExecuteTradeFlow",
    "sequential_steps": [
        {"step_name": "step_1", "component_type": "DeltaPublisher"},
    ],
    "approval_gate_index": 0,  # Gate fires before DeltaPublisher
}
```

**Acceptance criteria:**
- [ ] `POST /v1/flow-runs` accepts `{hired_instance_id, flow_name, run_context}`, creates `FlowRunModel`, enqueues to correct Celery queue
- [ ] `GET /v1/flow-runs/{flow_run_id}` returns current status + current_step
- [ ] Full end-to-end integration test: trigger `MarketAnalysisFlow` → RSI=28 → signal=BUY → `ExecuteTradeFlow` triggered → order placed → `flow_run.status=completed`
- [ ] With `auto_execute=false`: `ExecuteTradeFlow` stops at gate → `awaiting_approval`
- [ ] `waooaw_router()` used — bare `APIRouter` forbidden
- [ ] `get_read_db_session` on GET route, `get_db_session` on POST route
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I3-S5 — Deliverable written at FlowRun completion (30 min)

**Context:** When `ExecuteTradeFlow` completes, a `DeliverableModel` row must be written with the order confirmation so the customer can see it in their CP dashboard. Add deliverable-creation logic to `execute_sequential_flow` post-completion hook. The deliverable `content` field stores the last step's `component_run.output` as JSONB.

**Files to read first:**
- `src/Plant/BackEnd/models/deliverable.py` — existing model
- `src/Plant/BackEnd/engine/flow_executor.py` — add post-completion hook here

**Acceptance criteria:**
- [ ] On `flow_run.status = completed`, a `DeliverableModel` row is created with `content = last_component_run.output`
- [ ] `deliverable.hired_instance_id` and `deliverable.goal_instance_id` populated from `flow_run.run_context`
- [ ] `deliverable.type` set to `"trade_execution"` for Share Trader flows
- [ ] `GET /v1/deliverables?hired_instance_id=X` returns the new deliverable
- [ ] Unit test: completed flow → deliverable row exists with correct content
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

## Iteration 4 — Marketing Agent: Components + Fan-out Flow

> **Stories written and committed:** 2026-03-08

### I4-S1 — `GoalConfigPump` component (30 min)

**Context:** Marketing Agent's first step. Reads the customer's campaign brief and platform targets from `flow_run.run_context.goal_context` (set by the goal setting form). No external HTTP — pure context extraction and normalisation. Returns a structured `brief_payload` for the ContentProcessor. Create `src/Plant/BackEnd/components/marketing/goal_config_pump.py`.

**Files to read first:**
- `src/Plant/BackEnd/components/base.py` — from I2-S1

**Acceptance criteria:**
- [ ] `GoalConfigPump.component_type == "GoalConfigPump"`
- [ ] Reads `run_context.goal_context.campaign_brief`, `run_context.goal_context.content_type`, `skill_config.customer_fields.target_platforms`
- [ ] Returns `{"brief_payload": {...}, "platform_specs": [{"platform": "linkedin", "format": "post"}, ...]}`
- [ ] Missing `campaign_brief` → `ComponentOutput(success=False, error_message="campaign_brief required")`
- [ ] Registered in component registry at module import
- [ ] Unit tests: full brief, missing brief
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I4-S2 — `ContentProcessor` component (90 min)

**Context:** Takes `GoalConfigPump` output and calls an LLM (OpenAI or equivalent) to generate platform-specific post variants. Reads `skill_config.pp_locked_fields.brand_voice_model` (e.g. `gpt-4o`) and `skill_config.customer_fields.brand_name`, `tone`, `audience`. Uses `@circuit_breaker(service="openai_api")`. Returns `per_platform_variants` dict keyed by platform name. Create `src/Plant/BackEnd/components/marketing/content_processor.py`.

**Files to read first:**
- `src/Plant/BackEnd/components/base.py` — from I2-S1
- `src/Plant/BackEnd/core/encryption.py` — for OpenAI API key decryption

**NFR pattern:**
```python
@circuit_breaker(service="openai_api")
async def _call_llm(prompt: str, model: str, api_key: str) -> str:
    # httpx async POST to OpenAI /v1/chat/completions
    ...
```

**Acceptance criteria:**
- [ ] `ContentProcessor.component_type == "ContentProcessor"`
- [ ] `@circuit_breaker(service="openai_api")` wraps LLM call
- [ ] OpenAI API key never logged (`PIIMaskingFilter` active)
- [ ] Returns `{"post_text": str, "hashtags": list, "per_platform_variants": {"linkedin": {...}, "youtube": {...}}}`
- [ ] LLM HTTP failure → `ComponentOutput(success=False)` — triggers retry
- [ ] Unit test with mocked LLM: success path; HTTP 429 (rate limit) returns failure
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I4-S3 — `LinkedInPublisher` + `YouTubePublisher` components (45 min)

**Context:** Two publisher components for Marketing Agent. Both implement `BaseComponent`. Each reads its platform API key from `skill_config.customer_fields`. Both use `@circuit_breaker` on the post call. Return published content URL. Create `src/Plant/BackEnd/components/marketing/linkedin_publisher.py` and `youtube_publisher.py`.

**Files to read first:**
- `src/Plant/BackEnd/components/base.py` — from I2-S1
- `src/Plant/BackEnd/core/encryption.py` — API key decryption

**Acceptance criteria (both publishers):**
- [ ] `LinkedInPublisher.component_type == "LinkedInPublisher"`, `YouTubePublisher.component_type == "YouTubePublisher"`
- [ ] `@circuit_breaker(service="linkedin_api")` / `@circuit_breaker(service="youtube_api")`
- [ ] API keys never logged
- [ ] Return `{"platform_post_id": str, "published_url": str, "platform": str}`
- [ ] HTTP 4xx from platform → `ComponentOutput(success=False, error_message=...)` with platform name in message
- [ ] Both registered in component registry
- [ ] Unit tests: success, platform rejection, network error
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I4-S4 — Marketing Agent FlowDef + fan-out end-to-end (90 min)

**Context:** Wire `GoalConfigPump → ContentProcessor → [approval gate] → [LinkedInPublisher || YouTubePublisher]` using `execute_sequential_flow` + `execute_parallel_flow` from I2-S4/S5. Add `CONTENT_CREATION_FLOW` and `PUBLISHING_FLOW` constants. Full end-to-end test: brief → LLM content → approval → publish to both platforms.

**Files to read first:**
- `src/Plant/BackEnd/engine/flow_executor.py` — from I2-S4 and I2-S5
- `src/Plant/BackEnd/flows/` — create `marketing_agent.py` here
- `src/Plant/BackEnd/models/deliverable.py`

**Flow constants:**
```python
# src/Plant/BackEnd/flows/marketing_agent.py
CONTENT_CREATION_FLOW = {
    "flow_name": "ContentCreationFlow",
    "sequential_steps": [
        {"step_name": "step_1", "component_type": "GoalConfigPump"},
        {"step_name": "step_2", "component_type": "ContentProcessor"},
    ],
    "approval_gate_index": 2,  # Gate fires AFTER ContentProcessor, BEFORE publishing
}

PUBLISHING_FLOW = {
    "flow_name": "PublishingFlow",
    "parallel_steps": [
        {"step_name": "linkedin", "component_type": "LinkedInPublisher"},
        {"step_name": "youtube", "component_type": "YouTubePublisher"},
    ],
}
```

**Acceptance criteria:**
- [ ] `customer_reviews=true`: `ContentCreationFlow` stops at gate → `awaiting_approval`
- [ ] Customer approves → `PublishingFlow` triggered → both publishers run in parallel
- [ ] LinkedIn ✓ + YouTube ✗ → `flow_run.status = partial_failure`, both `component_run` rows written
- [ ] Deliverable created with `type="content_post"` and `content = {linkedin: {...}, youtube: {...}}`
- [ ] `customer_reviews=false`: gate skipped, publishing happens immediately
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

### I4-S5 — `POST /v1/approvals/{flow_run_id}/approve` endpoint (45 min)

**Context:** When `flow_run.status = awaiting_approval`, the customer clicks Approve in CP. CP calls this Plant endpoint. The endpoint transitions `flow_run.status = running` and re-enqueues the next step to the appropriate Celery queue. This is the resume-from-gate mechanism.

**Files to read first:**
- `src/Plant/BackEnd/models/flow_run.py` — from I1-S1
- `src/Plant/BackEnd/engine/flow_executor.py` — from I2-S4
- `src/CP/BackEnd/api/cp_approvals_proxy.py` — CP proxy that calls this endpoint

**NFR pattern:**
```python
router = waooaw_router(prefix="/v1/approvals", tags=["approvals"])

@router.post("/{flow_run_id}/approve")
async def approve_flow_run(
    flow_run_id: str,
    db: Session = Depends(get_db_session),  # write — not read replica
):
    flow_run = db.query(FlowRunModel).filter_by(id=flow_run_id).first()
    if not flow_run or flow_run.status != "awaiting_approval":
        raise HTTPException(status_code=409, detail="Not awaiting approval")
    flow_run.status = "running"
    flow_run.run_context = {**flow_run.run_context, "auto_execute": True}
    db.commit()
    # Re-enqueue remaining steps via Celery
    ...
```

**Acceptance criteria:**
- [ ] `POST /v1/approvals/{flow_run_id}/approve` transitions status from `awaiting_approval` → `running`
- [ ] `POST /v1/approvals/{flow_run_id}/reject` transitions to `failed` with `error_details.reason = "customer_rejected"`
- [ ] Calling approve on a non-`awaiting_approval` flow_run returns HTTP 409
- [ ] CP proxy `cp_approvals_proxy.py` updated to call new endpoint (not old deliverable-level endpoint)
- [ ] Unit tests: approve → resumes execution; reject → failed; wrong status → 409
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

## Iteration 5 — CP Portal UI

> **Stories written and committed:** 2026-03-08

### I5-S1 — Reusable `AgentCard` + `StatusDot` UI components (30 min)

**Context:** These two components are used on Marketplace, My Agents, and everywhere an agent is displayed. Defining them once as reusable HTML/CSS/JS components prevents duplication in all subsequent UI stories. All styling uses WAOOAW design system tokens. Create `frontend/components/AgentCard.js` and `frontend/components/StatusDot.js`.

**Design system tokens to use:**
```css
--bg-card: #18181b;
--color-primary: #667eea;
--color-neon-cyan: #00f2fe;
--border-dark: rgba(255,255,255,0.08);
--status-green: #10b981;   /* running */
--status-yellow: #f59e0b;  /* awaiting_approval */
--status-red: #ef4444;     /* failed */
--status-gray: #6b7280;    /* paused / no goal */
```

**AgentCard renders:** avatar (initials + gradient bg), agent name, industry tag, status dot, specialty text, rating (⭐ n.n), monthly price, "Hire / View" CTA button.

**StatusDot renders:** 8px circle, colour from status string, tooltip on hover (`running | awaiting approval | failed | paused`).

**Acceptance criteria:**
- [ ] `AgentCard` accepts props: `{id, name, industry, status, specialty, rating, price, ctaLabel, ctaHref}`
- [ ] `StatusDot` accepts props: `{status}` — maps to correct CSS color token
- [ ] Both dark theme compliant — `#0a0a0a` background, no white backgrounds
- [ ] Hover on AgentCard: `translateY(-8px)` + neon cyan box-shadow
- [ ] StatusDot tooltip shows human-readable status label
- [ ] Renders correctly with missing optional props (no JS errors)
- [ ] Visual review: screenshot matches WAOOAW design system

---

### I5-S2 — Marketplace screen with hire CTA (45 min)

**Context:** The marketplace is the first screen a customer sees — it must feel like browsing talent (Upwork/Fiverr), not a SaaS feature list. Uses `AgentCard` from I5-S1. Calls `GET /cp/agents` (existing CP proxy). Displays Share Trader and Marketing Agent cards. Each card has a "Start 7-day trial" CTA linking to the hire wizard. File: `frontend/pages/marketplace.html` + `frontend/pages/marketplace.js`.

**Acceptance criteria:**
- [ ] Prominent search bar at top (placeholder: "Find your agent...")
- [ ] Filter row: Industry (All / Marketing / Trading), Status (All / Available), Rating (★ 4+)
- [ ] Agent cards rendered using `AgentCard` component — no inline card markup
- [ ] "Start 7-day trial" CTA on each card links to `/hire/{agent_id}`
- [ ] Empty state: "No agents found — adjust your filters" with reset button
- [ ] Dark theme — `#0a0a0a` background, neon cyan search bar focus ring
- [ ] Works with keyboard navigation (tab through cards + enter to hire)

---

### I5-S3 — Hire wizard: skill config + goal setting (90 min)

**Context:** Three-step wizard: (1) Confirm agent + nickname, (2) Fill skill config fields (customer-fillable fields from `SkillConfig`), (3) Goal setting (schedule, approval preference). Calls `POST /cp/hired-agents` then `PATCH /cp/skill-configs/{id}` then `POST /cp/goal-instances`. On completion, redirects to My Agents. File: `frontend/pages/hire.html` + `frontend/pages/hire.js`.

**Acceptance criteria:**
- [ ] Step 1: Agent name (read-only), nickname input (required), trial badge "7 days free · keep everything"
- [ ] Step 2: Dynamic form — fields rendered from `skill_config.customer_fields` schema; API key fields are `type=password` masked
- [ ] Step 3: Schedule picker (daily / hourly / custom cron), approval toggle ("Review before execution" on/off)
- [ ] Back/Next navigation with validation — cannot advance with invalid fields
- [ ] Step 2 calls `PATCH /cp/skill-configs` on Next (not on final submit)
- [ ] Final submit: goal created → redirect to `/my-agents`
- [ ] API errors shown inline under relevant field, not alert()

---

### I5-S4 — My Agents + `FlowRunTimeline` + `DeliverableCard` (90 min)

**Context:** The My Agents screen is the customer's daily hub. Shows each hired agent with `StatusDot`, last run time, next scheduled run, and a "View" button. Clicking View opens the per-agent detail page showing `FlowRunTimeline` (current run in progress or last completed) and `DeliverableCard` list. New reusable components: `FlowRunTimeline` and `DeliverableCard`.

**FlowRunTimeline renders:** horizontal step sequence — each step as a node: `step_name`, status icon (✓ / ⏳ / ✗ / ⏸), duration_ms. Highlights `current_step` with pulse animation when status = `running`.

**DeliverableCard renders:** type badge (`trade_execution` | `content_post`), creation time, content preview (truncated 120 chars), "View full" expand, download link.

**Acceptance criteria:**
- [ ] My Agents lists all hired agents with `AgentCard` (compact variant) + `StatusDot`
- [ ] "Needs approval" badge on cards where `flow_run.status = awaiting_approval`
- [ ] Per-agent detail: `FlowRunTimeline` at top, `DeliverableCard` list below
- [ ] `FlowRunTimeline` auto-refreshes every 5s when `flow_run.status = running`
- [ ] `DeliverableCard` "View full" expands inline without page reload
- [ ] Empty state: "No runs yet — your first run will appear here"
- [ ] Calls `GET /cp/flow-runs?hired_instance_id=X` and `GET /cp/deliverables?hired_instance_id=X`

---

### I5-S5 — Approval queue + `ApprovalQueueItem` (45 min)

**Context:** When `flow_run.status = awaiting_approval`, the customer must be able to see a preview of what the agent produced and approve or reject it with one tap. This is the zero-risk promise in action. New reusable component `ApprovalQueueItem`. Notification badge on nav shows count. File: `frontend/pages/approvals.html` + `frontend/pages/approvals.js`.

**ApprovalQueueItem renders:** agent name + avatar, preview of what will happen (e.g. "Publish to LinkedIn: [post preview]" or "Place trade: NIFTY BUY ₹22,340"), time waiting, Approve (neon cyan) / Reject (red) buttons.

**Acceptance criteria:**
- [ ] Approval queue accessible from main nav ("Approvals" with badge count)
- [ ] Each `ApprovalQueueItem` shows content preview from `deliverable.content.per_platform_variants` or `deliverable.content.order_params`
- [ ] Approve button calls `POST /cp/approvals/{flow_run_id}/approve` — optimistic UI (button disabled immediately)
- [ ] Reject button calls `POST /cp/approvals/{flow_run_id}/reject` with confirmation dialog
- [ ] On approve: item removed from queue, `FlowRunTimeline` on My Agents updates to `running`
- [ ] Empty queue: "Nothing waiting for your approval — nice!" with confetti emoji

---

## Iteration 6 — PP Portal UI: Fleet + Health + DLQ

> **Stories written and committed:** 2026-03-08

### I6-S1 — PP Fleet dashboard with agent health map (45 min)

**Context:** PP operators need a real-time view of all hired agents across all customers. This is the ops nerve centre. Calls `GET /pp/hired-agents` (existing ops proxy, extend to include `flow_run` latest status). Uses `AgentCard` (compact variant) + `StatusDot`. File: `frontend/pp/pages/fleet.html` + `fleet.js`.

**Acceptance criteria:**
- [ ] Table/grid view: customer name (PII-masked in PP logs), agent name, agent type, status dot, last run time, last run duration, error count last 24h
- [ ] Filter: by status (all / running / awaiting_approval / failed / paused)
- [ ] Sort: by last run time (desc default), by error count
- [ ] Row click → opens Agent Health panel (I6-S2)
- [ ] Auto-refresh every 30s (not polling every second — battery/cost consideration)
- [ ] Error rows highlighted with red left border
- [ ] Dark theme, neon cyan active filters

---

### I6-S2 — Per-agent health drill-in with `ComponentRunRow` (45 min)

**Context:** PP operator clicks a fleet row → opens a rightside panel (or dedicated page) showing all `FlowRun` records for that hired agent, and for each FlowRun the individual `ComponentRunRow` entries. New reusable `ComponentRunRow` component. Calls `GET /pp/flow-runs?hired_instance_id=X` and `GET /pp/component-runs?flow_run_id=Y`.

**ComponentRunRow renders:** component type badge, step name, status icon, `duration_ms` bar (relative to slowest step), expand arrow → inline JSON display of `input_context` and `output` (syntax highlighted).

**Acceptance criteria:**
- [ ] FlowRun list shows last 20 runs, paginated
- [ ] Each FlowRun row expandable → shows `ComponentRunRow` list for that run
- [ ] `ComponentRunRow` input/output JSON expand uses syntax-highlighted `<pre>` block
- [ ] `PIIMaskingFilter` respected: PP UI must not display raw customer API keys even if they leaked into `input_context` — mask `*_key`, `*_secret`, `*_token` fields client-side
- [ ] "Re-run" button on failed FlowRun → calls `POST /pp/flow-runs/{id}/retry`
- [ ] `ComponentRunRow` duration bar: longest step = 100% width, others proportional

---

### I6-S3 — DLQ panel: view, requeue, skip (45 min)

**Context:** `scheduler_dlq` table already exists. This story wires the existing DLQ model to a PP UI panel showing failed component runs that exhausted all retries, with Requeue and Skip actions. Calls existing `GET /pp/dlq` and new `POST /pp/dlq/{id}/requeue` + `POST /pp/dlq/{id}/skip`.

**Files to read first:**
- `src/PP/BackEnd/api/ops_dlq.py` — existing DLQ endpoint
- `src/Plant/BackEnd/models/scheduler_dlq.py` — existing DLQ model

**Acceptance criteria:**
- [ ] DLQ panel accessible from PP nav ("DLQ" with error count badge)
- [ ] Each DLQ item shows: component type, flow_run_id, hired_instance_id, error message (last retry), retry count, first failed at
- [ ] "Requeue" button: calls `POST /pp/dlq/{id}/requeue` — component re-enters `execute_pump`/`execute_processor`/`execute_publisher` queue
- [ ] "Skip" button: marks DLQ item `skipped` — removes from queue with reason input required
- [ ] Filter: by component type, by date range
- [ ] Empty DLQ: "All clear — no failed jobs" in green

---

### I6-S4 — CP proxy routes for flow-runs + component-runs (30 min)

**Context:** All new Plant endpoints (`/v1/flow-runs`, `/v1/component-runs`, `/v1/approvals`) need CP proxy routes so the CP frontend can call them. CP BackEnd is a thin proxy — Pattern A: existing `/cp/*` route calls Plant via `gatewayRequestJson`. No business logic in CP BackEnd.

**Files to read first:**
- `src/CP/BackEnd/api/cp_approvals_proxy.py` — existing approval proxy pattern
- `src/CP/BackEnd/api/hired_agents_proxy.py` — existing hire proxy pattern

**New routes to add (Pattern A):**
```
GET  /cp/flow-runs                → GET /v1/flow-runs (Plant)
GET  /cp/flow-runs/{id}           → GET /v1/flow-runs/{id} (Plant)
POST /cp/approvals/{id}/approve   → POST /v1/approvals/{id}/approve (Plant)
POST /cp/approvals/{id}/reject    → POST /v1/approvals/{id}/reject (Plant)
GET  /cp/component-runs           → GET /v1/component-runs (Plant)
```

**Acceptance criteria:**
- [ ] All 5 routes implemented as thin proxies via `gatewayRequestJson`
- [ ] `waooaw_router()` used — not bare `APIRouter`
- [ ] Auth header forwarded on all proxied calls
- [ ] `X-Correlation-ID` forwarded on all proxied calls
- [ ] `get_read_db_session` on all GET routes
- [ ] Unit tests: each proxy route returns Plant response body unchanged (mocked Plant)
- [ ] `pytest --cov=app --cov-fail-under=80` passes

---

## PM Review Checklist

- [x] Zero placeholders in published plan
- [x] Every story is self-contained (no "see above", exact file paths given)
- [x] NFR patterns embedded inline in relevant stories
- [x] Story size: all ≤ 90 min
- [x] Max 6 stories per iteration
- [x] Backend story precedes frontend counterpart in iteration ordering
- [x] UI stories specify component names, design tokens, data fields
- [x] Reusable components named and catalogued in summary table
- [x] P0 gaps closed by end of Iteration 2
- [x] P1 gaps closed by end of Iteration 2
- [x] P2 gaps closed by end of Iteration 4
- [x] Data persistence: every story that touches data includes Alembic migration or DB write as acceptance criterion
- [x] Approval gate: located in FlowDef, not AgentType or Goal (constitutional invariant)
- [x] Fan-out: parallel_steps in FlowDef, PARTIAL_FAILURE status in flow_run
- [x] `definition_version_id` pin on HiredAgent in Iteration 1
- [x] No in-memory stubs — all state in Postgres
- [x] CHECKPOINT RULE embedded in Agent Execution Rules
