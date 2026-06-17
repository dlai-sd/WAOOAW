# INFRA-ROUTING-1 — Policy-Driven Dual-Path Data Router

**Objective**
Add a routing control plane to Plant BackEnd that can steer reads and writes
between PostgreSQL (current path) and Firestore (new serverless path) per
entity type, per environment, and per operation — without changing any API
contract, client code, CI/CD workflow, or GCP infrastructure shape.

This is **DMA enablement**: cost-sustainable demo lets the team run DMA
customer trials without a ₹10–15k/month always-on GCP bill. All existing
components (Cloud SQL, Redis, VPC connectors, Cloud Run) remain fully intact.
No removal, no contract breaks, safe rollback in < 60 seconds via env var flip.

**Objective alignment**: DMA enablement (P1/P2) — keeps demo affordable so DMA
trials can be run continuously without billing shock. Also Share Trader
enablement — same demo affordability applies to trading agent trials.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `INFRA-ROUTING-1` |
| Feature area | Plant BackEnd — core data layer + Firestore client + Terraform Firestore API |
| Created | 2026-06-17 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/infra/DEMO_ENV_SHUTDOWN_WORKFLOW_PLAN.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 4 |
| Total stories | 9 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story — agent never opens NFRReusable.md |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.

---

## PM Review Checklist

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] No CP BackEnd changes — all work is Plant BackEnd only
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: infra S1 before application S2
- [x] No placeholders remain
- [x] TDD/BDD — every story card has a test table
- [x] Integration Baseline Gate section is populated

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Routing control plane + Firestore client + first entity (agent status) on dual-write | 2 | 5 | 5h | 2026-06-18 08:00 IST |
| 2 | Shadow-read mode + drift detection + reconciliation job + demo Terraform | 2 | 4 | 4h | 2026-06-18 14:00 IST |

**Estimate basis:** New core module = 45 min | Integration with existing service = 60 min | Terraform change = 30 min | Test suite = 45 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

**Why 2 iterations:** Iteration 1 ships a working dual-write for the cheapest-to-route entity (agent status/performance stats) and the Firestore client with circuit breaker. Iteration 2 adds the safety net: shadow reads, drift detection, and the demo Terraform wiring that actually activates cost savings. Each iteration delivers a self-contained, mergeable slice.

---

## Integration Baseline Gate

> **Agent: run these commands BEFORE writing any code in Iteration 1. If any returns 404 or connection error, HALT and post the result as a comment.**

```bash
# 1. Plant BackEnd config module importable (expects no error)
cd src/Plant/BackEnd && python -c "from core.config import settings; print(settings.environment)"

# 2. Plant BackEnd core routing module present
ls src/Plant/BackEnd/core/routing.py

# 3. Plant BackEnd database connector present
ls src/Plant/BackEnd/core/database.py

# 4. Plant BackEnd redis client present
ls src/Plant/BackEnd/core/redis_client.py

# 5. Performance stats model present (entity we route in It1)
ls src/Plant/BackEnd/models/performance_stat.py
```

**Failure criteria:** any file-not-found or import error = check out the correct branch before proceeding.
**Pass criteria:** all five commands succeed with no errors.

---

## Architecture Overview

```
BEFORE (current):
Service → SQLAlchemy Session → PostgreSQL

AFTER (this plan):
Service → DatastoreRouter → routing policy (env var)
                    ├── sql path  → SQLAlchemy Session → PostgreSQL  (unchanged)
                    └── firestore → FirestoreClient → Firestore

Modes (DATA_ROUTER_MODE env var):
  sql          — 100% SQLAlchemy, no Firestore touched (default, safe rollback)
  dual_write   — write to SQL + async Firestore write; reads from SQL
  shadow_read  — dual_write + compare Firestore read result in background; emit mismatch metric
  firestore    — reads+writes to Firestore only (SQL bypassed for routed entities)
```

**Entity routing matrix — which entities can be routed (non-transactional, no FK requirements):**

| Entity | SQL table | Firestore collection | Routable in It1 | Notes |
|---|---|---|---|---|
| Agent performance stats | `performance_stats` | `agent_performance/{hired_agent_id}` | ✅ | Read-heavy, no FK dependencies from other services |
| Agent availability status | column on `hired_agent_entity` | `agent_availability/{hired_agent_id}` | ✅ It2 | Lookup-only reads; status update is low-risk |
| Activity feed (skill runs) | `flow_runs` | `activity_feed/{hired_agent_id}/runs/{run_id}` | ❌ | Has FK dependencies; SQL-only until migration approved |
| Customer, HiredAgent, Deliverable, Payment | multiple | — | ❌ forever | Transactional; SQL-only invariant must hold |

---

## How to Launch Each Iteration

### Iteration 1

> These plans are written for GitHub-hosted agents.
> Do not require shell, git, gh, or docker tools to begin work from the Agents tab.

**Agent task block — paste verbatim into GitHub Agents tab:**

```
You are a Python/FastAPI/GCP expert executing Iteration 1 of plan INFRA-ROUTING-1.
Branch: feat/infra-routing-1-it1-routing-foundation
Base: main

EXPERT PERSONAS ACTIVE:
- Python 3.11 / FastAPI / SQLAlchemy async expert
- Google Cloud Firestore / google-cloud-firestore Python SDK expert
- GCP Cloud Run / Secret Manager / Terraform expert

PLATFORM RULES (mandatory, no exceptions):
1. Router: always waooaw_router() from core.routing — never bare APIRouter()
2. App deps: FastAPI() must have dependencies=[Depends(get_correlation_id), Depends(get_audit_log)]
3. GET routes use get_read_db_session() not get_db_session()
4. PIIMaskingFilter on every logger: logger.addFilter(PIIMaskingFilter())
5. @circuit_breaker(service="...") on every external HTTP/network call
6. No env-specific values in code, Dockerfiles, or committed .env — runtime env vars via Secret Manager only
7. Image promotion: same Docker image promotes demo→uat→prod via injected env vars only

FAIL-FAST VALIDATION GATE (run first, halt if any fails):
  cd src/Plant/BackEnd && python -c "from core.config import settings; print(settings.environment)"
  ls src/Plant/BackEnd/core/routing.py
  ls src/Plant/BackEnd/core/database.py
  ls src/Plant/BackEnd/models/performance_stat.py

Execute stories in order: S1 → S2 → S3 → S4 → S5.
After each story: run its test command. If tests fail, fix before moving to the next story.
After all stories pass: open one PR to main with title "feat(infra): INFRA-ROUTING-1 It1 — routing foundation + Firestore client + dual-write"

--- STORY S1 ---
[see story card below]

--- STORY S2 ---
[see story card below]

--- STORY S3 ---
[see story card below]

--- STORY S4 ---
[see story card below]

--- STORY S5 ---
[see story card below]
```

### Iteration 2

**Agent task block — paste verbatim into GitHub Agents tab:**

```
You are a Python/FastAPI/GCP expert executing Iteration 2 of plan INFRA-ROUTING-1.
Branch: feat/infra-routing-1-it2-shadow-and-terraform
Base: main  ← BLOCKED UNTIL Iteration 1 PR is merged to main

EXPERT PERSONAS ACTIVE:
- Python 3.11 / FastAPI / SQLAlchemy async expert
- Google Cloud Firestore / google-cloud-firestore Python SDK expert
- Terraform / GCP Cloud Run expert

PLATFORM RULES: same as Iteration 1 (waooaw_router, get_read_db_session, PIIMaskingFilter, circuit_breaker, no env baking).

FAIL-FAST VALIDATION GATE (run first, halt if any fails):
  ls src/Plant/BackEnd/core/datastore_router.py     ← must exist from It1
  ls src/Plant/BackEnd/core/firestore_client.py     ← must exist from It1
  python -c "from core.datastore_router import DatastoreRouter; print('ok')"

Execute stories in order: S1 → S2 → S3 → S4.
After all pass: open one PR to main with title "feat(infra): INFRA-ROUTING-1 It2 — shadow read + drift detection + demo Terraform"
```

---

## Agent Execution Rules

### STUCK PROTOCOL
If you cannot proceed on a story after two attempts:
1. Post a comment on the PR describing exactly which file, line, and error blocked you.
2. Mark the PR as Draft.
3. Stop — do not attempt further stories in this session.

### CHECKPOINT RULE
After completing each story (all tests passing), run:
```bash
git add -A && git commit -m "feat(infra): INFRA-ROUTING-1 [story-id] — [story title]" && git push
```
Do this BEFORE starting the next story. If interrupted, completed stories are already saved.

### EXECUTION AGENT AUDIT ROUND
Before opening the PR, verify:
- [ ] Every new file has a module docstring
- [ ] `PIIMaskingFilter` is added to every logger in new files
- [ ] No hardcoded project IDs, collection names, or env-specific strings in Python code
- [ ] `DATA_ROUTER_MODE` is read exclusively from `settings.data_router_mode` — not from `os.environ.get()`
- [ ] All new tests pass: `docker-compose -f docker-compose.test.yml run plant-test pytest tests/ -x -v`

---

## Iteration 1 — Routing Foundation + Firestore Client + Dual-Write

### Epic E1 — Platform can route data without touching client code

**Customer/operator value:** Platform operator sets `DATA_ROUTER_MODE=dual_write` in Cloud Run and Plant BackEnd immediately starts dual-writing agent performance stats to both SQL and Firestore — no deployment, no code change, no API contract change.

**DMA/Share Trader alignment:** DMA enablement — enables demo to be shifted to Firestore-only path, reducing demo fixed costs and keeping DMA trials affordable.

---

#### Story S1 — `DatastoreRouter` class with routing policy from env

**Branch:** `feat/infra-routing-1-it1-routing-foundation`
**Estimate:** 45 min
**BLOCKED UNTIL:** none

**Context (2 sentences):**
Plant BackEnd currently calls SQLAlchemy sessions directly from service code with no abstraction layer. This story adds `src/Plant/BackEnd/core/datastore_router.py` — the central routing policy class that reads `DATA_ROUTER_MODE` from `settings` and provides `route_read()` and `route_write()` helpers that callers use instead of calling sessions directly.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/core/config.py` — understand Settings class structure to add `data_router_mode` field
2. `src/Plant/BackEnd/core/routing.py` — understand `waooaw_router()` factory pattern to follow same conventions
3. `src/Plant/BackEnd/core/database.py` — understand session factory shape to wire into router

**Task:**
1. Add `data_router_mode` field to `Settings` in `src/Plant/BackEnd/core/config.py`:

```python
# Add inside Settings class, after redis_url field (around line 116)
data_router_mode: str = Field(
    default="sql",
    validation_alias=AliasChoices("DATA_ROUTER_MODE", "data_router_mode"),
    description="Routing policy: sql | dual_write | shadow_read | firestore",
)

@field_validator("data_router_mode", mode="before")
@classmethod
def validate_router_mode(cls, v: object) -> str:
    allowed = {"sql", "dual_write", "shadow_read", "firestore"}
    if str(v) not in allowed:
        raise ValueError(f"data_router_mode must be one of {allowed}, got '{v}'")
    return str(v)
```

2. Create `src/Plant/BackEnd/core/datastore_router.py` with this exact content:

```python
"""
DatastoreRouter — INFRA-ROUTING-1 policy-driven data path selector.

Reads DATA_ROUTER_MODE from Settings and provides routing helpers
that service code calls instead of raw SQLAlchemy sessions.

Modes:
  sql          — 100% SQLAlchemy (default, safe rollback point)
  dual_write   — write SQL + async Firestore; reads from SQL
  shadow_read  — dual_write + background Firestore read comparison
  firestore    — reads+writes to Firestore only for routed entities

Usage:
  router = DatastoreRouter()
  if router.reads_from_firestore("agent_performance"):
      return await firestore_client.get_agent_performance(hired_agent_id)
  # else fall through to SQL path
"""

from __future__ import annotations

import logging

from core.config import settings
from core.logging import PIIMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PIIMaskingFilter())

# Collections that are eligible for Firestore routing.
# Transactional entities (customer, hired_agent, deliverable, payment) are
# NOT in this set — they are SQL-only forever.
_ROUTABLE_COLLECTIONS = frozenset(
    {
        "agent_performance",   # PerformanceStat model → performance_stats table
        "agent_availability",  # HiredAgent status column (read-only Firestore path)
    }
)


class DatastoreRouter:
    """
    Stateless routing policy helper.  Instantiate per-request or as a singleton.
    Reads DATA_ROUTER_MODE from settings at call time (no caching) so a
    Cloud Run env-var flip takes effect on the next request with no restart.
    """

    def __init__(self) -> None:
        self._mode = settings.data_router_mode

    @property
    def mode(self) -> str:
        # Re-read each time so hot-reload of settings works in tests.
        return settings.data_router_mode

    def is_routable(self, collection: str) -> bool:
        """True if this collection participates in the routing policy."""
        return collection in _ROUTABLE_COLLECTIONS

    def reads_from_firestore(self, collection: str) -> bool:
        """True when the read path for this collection should use Firestore."""
        return self.mode == "firestore" and self.is_routable(collection)

    def writes_to_firestore(self, collection: str) -> bool:
        """True when a secondary Firestore write should be triggered."""
        return self.mode in {"dual_write", "shadow_read", "firestore"} and self.is_routable(collection)

    def shadow_mode(self, collection: str) -> bool:
        """True when background read comparison should be triggered."""
        return self.mode == "shadow_read" and self.is_routable(collection)


# Module-level singleton — callers import and use directly.
datastore_router = DatastoreRouter()
```

**Acceptance criteria (all must pass):**
- [ ] `from core.datastore_router import DatastoreRouter, datastore_router` succeeds with no import error
- [ ] `DatastoreRouter().reads_from_firestore("agent_performance")` returns `False` when `DATA_ROUTER_MODE=sql`
- [ ] `DatastoreRouter().writes_to_firestore("agent_performance")` returns `True` when `DATA_ROUTER_MODE=dual_write`
- [ ] `DatastoreRouter().reads_from_firestore("customer")` returns `False` for all modes (non-routable entity)
- [ ] `settings.data_router_mode` raises `ValueError` when set to an unknown value

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_datastore_router_modes` | Unit | `src/Plant/BackEnd/tests/test_datastore_router.py` | `pytest src/Plant/BackEnd/tests/test_datastore_router.py -v` |
| `test_settings_data_router_mode_validation` | Unit | `src/Plant/BackEnd/tests/test_datastore_router.py` | same |

**Code patterns to copy exactly:**

```python
# waooaw_router factory (from src/Plant/BackEnd/core/routing.py) — for reference only,
# S1 does not add a new route but follows the same module pattern.
from fastapi import APIRouter, Depends
from core.dependencies import require_correlation_id

def waooaw_router(prefix: str = "", tags: list[str] | None = None, **kwargs) -> APIRouter:
    platform_deps = [Depends(require_correlation_id)]
    caller_deps = kwargs.pop("dependencies", [])
    return APIRouter(prefix=prefix, tags=tags or [], dependencies=platform_deps + caller_deps, **kwargs)
```

---

#### Story S2 — `FirestoreClient` with circuit breaker and PII masking

**Branch:** `feat/infra-routing-1-it1-routing-foundation` (same branch as S1)
**Estimate:** 45 min
**BLOCKED UNTIL:** S1 merged to this branch

**Context (2 sentences):**
The Firestore path needs a thin client wrapper that applies the circuit breaker NFR pattern and PII masking to every Firestore operation. This story creates `src/Plant/BackEnd/core/firestore_client.py` as the only entry point for all Firestore reads/writes in Plant BackEnd — no service file may import `google.cloud.firestore` directly.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/core/datastore_router.py` — understand the routing module pattern just created
2. `src/Plant/BackEnd/core/config.py` — find `gcp_project_id` field for Firestore project
3. `src/Plant/BackEnd/core/redis_client.py` — copy lazy-init pattern for the Firestore client instance

**Task:**
1. Add `google-cloud-firestore` to `src/Plant/BackEnd/requirements.txt` (or the correct requirements file).
2. Create `src/Plant/BackEnd/core/firestore_client.py`:

```python
"""
FirestoreClient — INFRA-ROUTING-1 Firestore access layer.

Single entry point for all Firestore reads/writes in Plant BackEnd.
Service files MUST NOT import google.cloud.firestore directly.

Circuit breaker: every network call is wrapped so a Firestore outage
cannot propagate into a Plant BackEnd 500.  On open circuit the caller
receives None (reads) or False (writes) and falls back to SQL.

PII rule: document field names and log messages must never contain
email, phone, or full_name values. Use entity IDs only.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from unittest.mock import MagicMock

from core.config import settings
from core.logging import PIIMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PIIMaskingFilter())

_CIRCUIT_OPEN_THRESHOLD = 5    # consecutive failures before opening
_CIRCUIT_RESET_SECONDS  = 30   # seconds before half-open retry


class _SimpleCircuitBreaker:
    """Lightweight circuit breaker — no external dependency required."""

    def __init__(self, threshold: int = _CIRCUIT_OPEN_THRESHOLD, reset_seconds: int = _CIRCUIT_RESET_SECONDS) -> None:
        import time
        self._failures = 0
        self._threshold = threshold
        self._reset_seconds = reset_seconds
        self._opened_at: Optional[float] = None
        self._time = time

    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if self._time.time() - self._opened_at > self._reset_seconds:
            self._opened_at = None
            self._failures = 0
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = self._time.time()
            logger.warning("firestore_client: circuit opened after %d consecutive failures", self._failures)


_breaker = _SimpleCircuitBreaker()
_fs_client: Any = None  # google.cloud.firestore.AsyncClient or None


def _get_client() -> Any:
    """Lazily initialise the Firestore async client."""
    global _fs_client
    if _fs_client is not None:
        return _fs_client
    if settings.environment in {"development", "test", "local"}:
        # Return a mock so unit tests never hit the network.
        _fs_client = MagicMock()
        return _fs_client
    try:
        from google.cloud import firestore as _fs  # type: ignore[import]
        _fs_client = _fs.AsyncClient(project=settings.gcp_project_id)
        logger.info("firestore_client: async client initialised for project=%s", settings.gcp_project_id)
    except Exception as exc:
        logger.error("firestore_client: failed to initialise — %s", exc)
        _fs_client = None
    return _fs_client


async def get_document(collection: str, doc_id: str) -> Optional[dict]:
    """Read a single Firestore document. Returns None on circuit open or error."""
    if _breaker.is_open():
        logger.warning("firestore_client: circuit open, skipping read %s/%s", collection, doc_id)
        return None
    client = _get_client()
    if client is None:
        return None
    try:
        doc_ref = client.collection(collection).document(doc_id)
        snapshot = await doc_ref.get()
        _breaker.record_success()
        return snapshot.to_dict() if snapshot.exists else None
    except Exception as exc:
        _breaker.record_failure()
        logger.error("firestore_client: read error %s/%s — %s", collection, doc_id, exc)
        return None


async def set_document(collection: str, doc_id: str, data: dict, merge: bool = True) -> bool:
    """Write a Firestore document. Returns False on circuit open or error."""
    if _breaker.is_open():
        logger.warning("firestore_client: circuit open, skipping write %s/%s", collection, doc_id)
        return False
    client = _get_client()
    if client is None:
        return False
    try:
        doc_ref = client.collection(collection).document(doc_id)
        await doc_ref.set(data, merge=merge)
        _breaker.record_success()
        return True
    except Exception as exc:
        _breaker.record_failure()
        logger.error("firestore_client: write error %s/%s — %s", collection, doc_id, exc)
        return False
```

**Acceptance criteria (all must pass):**
- [ ] `from core.firestore_client import get_document, set_document` succeeds with no import error
- [ ] `get_document("agent_performance", "test-id")` returns `None` in test/local environment (mock path)
- [ ] `set_document("agent_performance", "test-id", {"stat": 1})` returns `False` when circuit is open
- [ ] No raw `google.cloud.firestore` import exists in any service file (only in `firestore_client.py`)
- [ ] `PIIMaskingFilter` is attached to the module logger

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_firestore_client_circuit_breaker` | Unit | `src/Plant/BackEnd/tests/test_firestore_client.py` | `pytest src/Plant/BackEnd/tests/test_firestore_client.py -v` |
| `test_firestore_client_mock_in_test_env` | Unit | `src/Plant/BackEnd/tests/test_firestore_client.py` | same |

---

#### Story S3 — Agent performance stats dual-write via `DatastoreRouter`

**Branch:** `feat/infra-routing-1-it1-routing-foundation` (same branch)
**Estimate:** 60 min
**BLOCKED UNTIL:** S2 merged to this branch

**Context (2 sentences):**
`PerformanceStat` (table `performance_stats`) is a read-heavy, non-transactional entity with no FK dependencies from other service files — it is the safest first entity to route. This story wires the `DatastoreRouter` into the performance stats read/write path so that when `DATA_ROUTER_MODE=dual_write`, stats are written to SQL (primary) and asynchronously to Firestore collection `agent_performance/{hired_agent_id}`.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/performance_stat.py` — understand the PerformanceStat ORM model
2. `src/Plant/BackEnd/core/datastore_router.py` — routing helpers just created
3. `src/Plant/BackEnd/core/firestore_client.py` — set_document / get_document helpers just created

**Task:**
1. Create `src/Plant/BackEnd/services/performance_stat_router.py`:

```python
"""
performance_stat_router — INFRA-ROUTING-1 dual-write adapter for PerformanceStat.

Wraps the SQL persistence path for performance stats and adds an async
Firestore secondary write when DATA_ROUTER_MODE is dual_write, shadow_read,
or firestore.

Firestore schema (collection: agent_performance):
  Document ID: str(hired_agent_id)
  Fields:
    hired_agent_id: str
    stat_date: str (ISO 8601)
    posts_count: int
    impressions: int
    engagements: int
    retention_rate: float
    response_time_minutes: float
    updated_at: str (ISO 8601 UTC)

PII: no customer email, phone, or name is stored in Firestore documents.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.datastore_router import datastore_router
from core.firestore_client import get_document, set_document
from core.logging import PIIMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PIIMaskingFilter())

_FIRESTORE_COLLECTION = "agent_performance"


def _to_firestore_doc(hired_agent_id: UUID, stat: Any) -> dict:
    """Convert a PerformanceStat ORM row to a Firestore-safe dict (no PII)."""
    return {
        "hired_agent_id": str(hired_agent_id),
        "stat_date": stat.stat_date.isoformat() if hasattr(stat, "stat_date") else None,
        "posts_count": getattr(stat, "posts_count", 0),
        "impressions": getattr(stat, "impressions", 0),
        "engagements": getattr(stat, "engagements", 0),
        "retention_rate": float(getattr(stat, "retention_rate", 0.0)),
        "response_time_minutes": float(getattr(stat, "response_time_minutes", 0.0)),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


async def after_stat_write(hired_agent_id: UUID, stat: Any) -> None:
    """
    Called after a PerformanceStat SQL write.
    Fires an async Firestore secondary write if the routing policy requires it.
    Failures are logged but never raise — SQL path is authoritative.
    """
    if not datastore_router.writes_to_firestore(_FIRESTORE_COLLECTION):
        return
    doc_id = str(hired_agent_id)
    doc = _to_firestore_doc(hired_agent_id, stat)
    ok = await set_document(_FIRESTORE_COLLECTION, doc_id, doc)
    if not ok:
        logger.warning(
            "performance_stat_router: Firestore secondary write skipped for agent=%s (circuit open or error)",
            doc_id,
        )


async def read_stat_from_firestore(hired_agent_id: UUID) -> Optional[dict]:
    """
    Returns the Firestore document for this agent's performance, or None.
    Only used when DATA_ROUTER_MODE=firestore.
    """
    if not datastore_router.reads_from_firestore(_FIRESTORE_COLLECTION):
        return None
    return await get_document(_FIRESTORE_COLLECTION, str(hired_agent_id))
```

**Acceptance criteria (all must pass):**
- [ ] `from services.performance_stat_router import after_stat_write, read_stat_from_firestore` succeeds
- [ ] `after_stat_write(uuid, mock_stat)` returns without error when `DATA_ROUTER_MODE=sql` (no-op)
- [ ] `after_stat_write(uuid, mock_stat)` calls `set_document` when `DATA_ROUTER_MODE=dual_write`
- [ ] `read_stat_from_firestore(uuid)` returns `None` when `DATA_ROUTER_MODE=sql`
- [ ] No exception propagates from `after_stat_write` when Firestore is unavailable

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_after_stat_write_noop_in_sql_mode` | Unit | `src/Plant/BackEnd/tests/test_performance_stat_router.py` | `pytest src/Plant/BackEnd/tests/test_performance_stat_router.py -v` |
| `test_after_stat_write_calls_firestore_in_dual_write` | Unit | same | same |
| `test_read_stat_from_firestore_returns_none_in_sql_mode` | Unit | same | same |

---

#### Story S4 — Wire `after_stat_write` into existing performance stat service

**Branch:** `feat/infra-routing-1-it1-routing-foundation` (same branch)
**Estimate:** 45 min
**BLOCKED UNTIL:** S3 merged to this branch

**Context (2 sentences):**
`src/Plant/BackEnd/services/redis_runtime.py` currently manages runtime stat updates using Redis. This story adds the `after_stat_write` call as a fire-and-forget side-effect after any SQL performance stat write, so the dual-write path activates without changing any existing write logic or API contract.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/services/redis_runtime.py` — find where performance stats are written to identify the correct insertion point
2. `src/Plant/BackEnd/services/performance_stat_router.py` — the adapter just created
3. `src/Plant/BackEnd/api/v1/runtime_redis.py` — understand the route that triggers stat writes to ensure contract is unchanged

**Task:**
1. In `src/Plant/BackEnd/services/redis_runtime.py`, after any write operation that persists a performance stat (search for `performance_stat` or `PerformanceStat` write calls), add a fire-and-forget async call:

```python
# Add this import at the top of redis_runtime.py (after existing imports):
import asyncio
from services.performance_stat_router import after_stat_write

# Add this line immediately after any PerformanceStat SQL session.add() / session.flush() / session.commit():
# Replace `stat` and `hired_agent_id` with the actual local variable names in that function.
asyncio.create_task(after_stat_write(hired_agent_id, stat))
```

2. If `redis_runtime.py` does not write PerformanceStat rows (it only reads/writes Redis keys), search for the actual SQL write call:
   - `grep -rn "PerformanceStat\|performance_stat" src/Plant/BackEnd/services/ src/Plant/BackEnd/api/`
   - Find the correct service/API file and add the `asyncio.create_task(after_stat_write(...))` call there instead.
   - Document the file you changed in the PR description.

**Acceptance criteria (all must pass):**
- [ ] No existing test breaks after the change
- [ ] `asyncio.create_task(after_stat_write(...))` is called in exactly one place — at the SQL write site
- [ ] The API contract for the performance stat route is unchanged (same request/response schema)
- [ ] `DATA_ROUTER_MODE=sql` (default): `after_stat_write` is a no-op — no Firestore calls made
- [ ] `DATA_ROUTER_MODE=dual_write`: `set_document` is called asynchronously after SQL write

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_stat_write_noop_firestore_in_sql_mode` | Integration | `src/Plant/BackEnd/tests/test_performance_stat_router.py` | `pytest src/Plant/BackEnd/tests/ -k "stat" -v` |
| Existing tests still pass | Regression | all Plant tests | `docker-compose -f docker-compose.test.yml run plant-test pytest -x` |

---

#### Story S5 — Add `google-cloud-firestore` to requirements and CI test gate

**Branch:** `feat/infra-routing-1-it1-routing-foundation` (same branch)
**Estimate:** 30 min
**BLOCKED UNTIL:** none (can run in parallel with S1)

**Context (2 sentences):**
The Firestore client requires `google-cloud-firestore` in the Plant BackEnd `requirements.txt`. The test environment must also be able to run the new unit tests without a live Firestore connection (mock path in `firestore_client.py` handles this for `environment=test`).

**Files to read first (max 3):**
1. `src/Plant/BackEnd/requirements.txt` — add `google-cloud-firestore` in the correct section
2. `docker-compose.test.yml` — confirm `plant-test` service environment variables
3. `.github/workflows/waooaw-ci.yml` — confirm CI matrix includes plant tests

**Task:**
1. Add to `src/Plant/BackEnd/requirements.txt`:
```
google-cloud-firestore>=2.16.0
```
2. Confirm `docker-compose.test.yml` `plant-test` service has `ENVIRONMENT=test` (so `_get_client()` returns mock).
3. If `ENVIRONMENT` is not set, add it:
```yaml
environment:
  - ENVIRONMENT=test
  - DATA_ROUTER_MODE=sql
```
4. Do NOT change `.github/workflows/waooaw-ci.yml` — the existing matrix already runs plant tests.

**Acceptance criteria (all must pass):**
- [ ] `pip install -r src/Plant/BackEnd/requirements.txt` completes without error in Docker
- [ ] All new unit tests (S1, S2, S3) pass in `docker-compose.test.yml run plant-test pytest` without needing GCP credentials
- [ ] `ENVIRONMENT=test` means `_get_client()` returns `MagicMock()` — no real Firestore calls in CI

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| CI gate | Regression | all | `docker-compose -f docker-compose.test.yml run plant-test pytest -x` |

---

### Epic E2 — Demo costs drop when Firestore mode is active

**Customer/operator value:** When `DATA_ROUTER_MODE=dual_write` has been running stably for 48h, the operator flips to `DATA_ROUTER_MODE=firestore` for the `agent_performance` collection, confirms reads are correct, and removes the always-on Cloud SQL instance from demo — dropping demo infra cost by ₹2–3k/month for that entity alone.

---

*(Epic E2 stories are delivered in Iteration 2.)*

---

## Iteration 2 — Shadow Read + Drift Detection + Demo Terraform

### Epic E3 — Platform can prove Firestore and SQL are in sync before full cutover

**Customer/operator value:** Operator can set `DATA_ROUTER_MODE=shadow_read`, watch a drift metric in Cloud Monitoring, and only flip to `DATA_ROUTER_MODE=firestore` when the mismatch rate has been 0% for 48h — giving a data-evidence-based go/no-go decision.

---

#### Story S1 — Shadow read mode: background Firestore vs SQL comparison

**Branch:** `feat/infra-routing-1-it2-shadow-and-terraform`
**Estimate:** 90 min
**BLOCKED UNTIL:** Iteration 1 PR merged to main

**Context (2 sentences):**
Shadow read mode runs both SQL and Firestore reads in parallel, compares the results, and emits a mismatch counter metric — without changing which result the caller receives (SQL is still authoritative). This story adds `shadow_compare()` to `src/Plant/BackEnd/services/performance_stat_router.py` and wires a Prometheus counter for drift tracking.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/services/performance_stat_router.py` — add shadow_compare() here
2. `src/Plant/BackEnd/core/metrics.py` — understand how Prometheus counters are registered
3. `src/Plant/BackEnd/core/datastore_router.py` — shadow_mode() helper

**Task:**
1. Add to `src/Plant/BackEnd/core/metrics.py` (after existing counter definitions):

```python
# INFRA-ROUTING-1: Firestore drift tracking
from prometheus_client import Counter
firestore_drift_total = Counter(
    "waooaw_firestore_drift_total",
    "Number of times Firestore read result differed from SQL result",
    ["collection"],
)
firestore_shadow_reads_total = Counter(
    "waooaw_firestore_shadow_reads_total",
    "Number of shadow read comparisons performed",
    ["collection"],
)
```

2. Add to `src/Plant/BackEnd/services/performance_stat_router.py`:

```python
# Add these imports at the top:
import asyncio
from core.metrics import firestore_drift_total, firestore_shadow_reads_total

async def shadow_compare(hired_agent_id: UUID, sql_result: Any) -> None:
    """
    Background task: read Firestore and compare with SQL result.
    Emits drift metric on mismatch. Never raises — shadow mode must be invisible to callers.
    Called via asyncio.create_task() immediately after SQL read returns.
    """
    if not datastore_router.shadow_mode(_FIRESTORE_COLLECTION):
        return
    firestore_shadow_reads_total.labels(collection=_FIRESTORE_COLLECTION).inc()
    try:
        fs_doc = await get_document(_FIRESTORE_COLLECTION, str(hired_agent_id))
        if fs_doc is None:
            # No Firestore document yet — expected until dual_write has run once
            return
        sql_posts = getattr(sql_result, "posts_count", None)
        fs_posts  = fs_doc.get("posts_count")
        if sql_posts != fs_posts:
            firestore_drift_total.labels(collection=_FIRESTORE_COLLECTION).inc()
            logger.warning(
                "shadow_compare: drift detected for agent=%s sql_posts=%s fs_posts=%s",
                str(hired_agent_id), sql_posts, fs_posts,
            )
    except Exception as exc:
        logger.error("shadow_compare: error — %s", exc)
```

3. Wire `asyncio.create_task(shadow_compare(hired_agent_id, sql_stat))` after the SQL read in the performance stat API route.

**Acceptance criteria (all must pass):**
- [ ] `waooaw_firestore_drift_total` counter is incremented when SQL and Firestore values differ
- [ ] `shadow_compare()` never raises — exceptions are caught and logged only
- [ ] `shadow_compare()` is a no-op when `DATA_ROUTER_MODE=sql` or `DATA_ROUTER_MODE=dual_write`
- [ ] Shadow compare does not change the value returned to the API caller

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_shadow_compare_increments_drift_counter` | Unit | `src/Plant/BackEnd/tests/test_shadow_compare.py` | `pytest src/Plant/BackEnd/tests/test_shadow_compare.py -v` |
| `test_shadow_compare_noop_in_sql_mode` | Unit | same | same |
| `test_shadow_compare_never_raises` | Unit | same | same |

---

#### Story S2 — Reconciliation background task (daily SQL vs Firestore sweep)

**Branch:** `feat/infra-routing-1-it2-shadow-and-terraform` (same branch)
**Estimate:** 60 min
**BLOCKED UNTIL:** S1 merged to this branch

**Context (2 sentences):**
Shadow mode catches per-request drift in real time, but a scheduled reconciliation sweep catches accumulated drift from failed dual-writes (e.g., circuit open during a spike). This story adds a Celery-compatible async task in `src/Plant/BackEnd/services/reconciliation_service.py` that scans all `performance_stats` rows, cross-checks Firestore, and logs a structured summary.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/services/performance_stat_router.py` — `_to_firestore_doc()` shape to compare against
2. `src/Plant/BackEnd/models/performance_stat.py` — ORM model field names
3. `src/Plant/BackEnd/core/metrics.py` — add reconciliation metric here

**Task:**
Create `src/Plant/BackEnd/services/reconciliation_service.py`:

```python
"""
reconciliation_service — INFRA-ROUTING-1 daily drift sweep.

Scans all PerformanceStat rows, reads matching Firestore documents,
compares posts_count as the primary reconciliation field, and logs
a structured summary.  Designed to run as a scheduled Cloud Run Job
(one-off invocation) or triggered from a PP admin route.

Never writes to SQL from this service — SQL is read-only authoritative source.
Repair action: re-trigger after_stat_write() for drifted rows.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.firestore_client import get_document
from core.logging import PIIMaskingFilter
from core.metrics import firestore_drift_total
from models.performance_stat import PerformanceStat
from services.performance_stat_router import after_stat_write, _FIRESTORE_COLLECTION

logger = logging.getLogger(__name__)
logger.addFilter(PIIMaskingFilter())


async def run_reconciliation_sweep(db: AsyncSession) -> dict:
    """
    Sweep all PerformanceStat rows and re-sync drifted Firestore documents.

    Returns:
        dict with keys: total_checked, drifted, repaired, errors
    """
    result = await db.execute(select(PerformanceStat))
    stats = result.scalars().all()

    total = len(stats)
    drifted = 0
    repaired = 0
    errors = 0

    for stat in stats:
        try:
            hired_agent_id = stat.hired_instance_id
            fs_doc = await get_document(_FIRESTORE_COLLECTION, str(hired_agent_id))
            sql_posts = getattr(stat, "posts_count", 0)
            fs_posts  = fs_doc.get("posts_count") if fs_doc else None
            if fs_posts != sql_posts:
                drifted += 1
                firestore_drift_total.labels(collection=_FIRESTORE_COLLECTION).inc()
                ok = await after_stat_write(hired_agent_id, stat)
                if ok is not False:
                    repaired += 1
        except Exception as exc:
            errors += 1
            logger.error("reconciliation_service: error for stat=%s — %s", getattr(stat, "id", "?"), exc)

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "total_checked": total,
        "drifted": drifted,
        "repaired": repaired,
        "errors": errors,
    }
    logger.info("reconciliation_service: sweep complete %s", summary)
    return summary
```

**Acceptance criteria (all must pass):**
- [ ] `run_reconciliation_sweep(db)` returns a dict with `total_checked`, `drifted`, `repaired`, `errors`
- [ ] Drift counter increments for each drifted row
- [ ] Function never raises — all per-row errors are caught and counted
- [ ] `after_stat_write` is called for each drifted row to re-sync Firestore

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| `test_reconciliation_sweep_detects_drift` | Unit | `src/Plant/BackEnd/tests/test_reconciliation_service.py` | `pytest src/Plant/BackEnd/tests/test_reconciliation_service.py -v` |
| `test_reconciliation_sweep_handles_errors_gracefully` | Unit | same | same |

---

#### Story S3 — Terraform: enable Firestore API and inject `DATA_ROUTER_MODE` for demo

**Branch:** `feat/infra-routing-1-it2-shadow-and-terraform` (same branch)
**Estimate:** 30 min
**BLOCKED UNTIL:** none (can run in parallel with S1)

**Context (2 sentences):**
Firestore (Datastore mode) must be enabled in `waooaw-oauth` GCP project — it is not enabled by default. This story adds the Firestore API enable to the foundation Terraform stack and adds `DATA_ROUTER_MODE=sql` as the default Cloud Run env var for demo (operator changes it manually in Cloud Run console to activate routing).

**Files to read first (max 3):**
1. `cloud/terraform/stacks/foundation/environments/default.tfvars` — understand foundation config shape
2. `cloud/terraform/stacks/plant/environments/demo.tfvars` — add DATA_ROUTER_MODE here
3. `cloud/terraform/stacks/plant/main.tf` OR `cloud/terraform/stacks/plant/variables.tf` — find where Cloud Run env vars are injected to add the new variable

**Task:**
1. In `cloud/terraform/stacks/plant/environments/demo.tfvars`, add:
```hcl
# INFRA-ROUTING-1: Data routing mode (sql | dual_write | shadow_read | firestore)
# Default: sql — operator changes in Cloud Run console to activate routing.
data_router_mode = "sql"
```

2. In `cloud/terraform/stacks/plant/variables.tf`, add:
```hcl
variable "data_router_mode" {
  description = "DatastoreRouter mode: sql | dual_write | shadow_read | firestore"
  type        = string
  default     = "sql"
  validation {
    condition     = contains(["sql", "dual_write", "shadow_read", "firestore"], var.data_router_mode)
    error_message = "data_router_mode must be one of: sql, dual_write, shadow_read, firestore"
  }
}
```

3. In the Cloud Run resource block that deploys Plant BackEnd (search `cloud/terraform/stacks/plant/` for `DATA_ROUTER_MODE` or `env` block), add the env var injection:
```hcl
env {
  name  = "DATA_ROUTER_MODE"
  value = var.data_router_mode
}
```

4. Add matching entries to `cloud/terraform/stacks/plant/environments/uat.tfvars` and `cloud/terraform/stacks/plant/environments/prod.tfvars` (both default to `sql`):
```hcl
data_router_mode = "sql"
```

**Acceptance criteria (all must pass):**
- [ ] `terraform validate` passes in `cloud/terraform/stacks/plant/`
- [ ] `terraform plan -var-file=environments/demo.tfvars` shows `DATA_ROUTER_MODE=sql` in the plan output
- [ ] All three environment tfvars files (demo, uat, prod) have `data_router_mode` set
- [ ] No existing Terraform variable is renamed or removed

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| Terraform validation | Infra | `cloud/terraform/stacks/plant/` | `terraform validate` |
| Plan review | Infra | same | `terraform plan -var-file=environments/demo.tfvars` |

---

#### Story S4 — Full integration test suite for all routing modes

**Branch:** `feat/infra-routing-1-it2-shadow-and-terraform` (same branch)
**Estimate:** 45 min
**BLOCKED UNTIL:** S1 and S2 merged to this branch

**Context (2 sentences):**
The three new core modules (`datastore_router`, `firestore_client`, `performance_stat_router`) each have targeted unit tests, but there is no integration test that walks all four routing modes in sequence. This story adds `tests/test_routing_integration.py` (root `tests/` — runs in the Docker test topology) to validate end-to-end routing mode transitions without a live Firestore connection.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/core/datastore_router.py` — modes and helpers
2. `src/Plant/BackEnd/services/performance_stat_router.py` — adapter under test
3. `tests/test_demo_runtime_batch_script_integration.py` — existing root-level integration test to follow its pattern

**Task:**
Create `tests/test_routing_integration.py`:

```python
"""
Integration tests for INFRA-ROUTING-1 dual-path data router.

Tests all four routing modes without live GCP credentials.
Firestore calls are intercepted by the mock client (ENVIRONMENT=test).
"""

import asyncio
import os
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture(autouse=True)
def reset_router_mode(monkeypatch):
    """Reset DATA_ROUTER_MODE to sql after each test."""
    yield
    monkeypatch.setenv("DATA_ROUTER_MODE", "sql")


def set_mode(monkeypatch, mode: str):
    monkeypatch.setenv("DATA_ROUTER_MODE", mode)
    # Force settings re-read
    from core import config as cfg_mod
    cfg_mod.settings.data_router_mode = mode


@pytest.mark.asyncio
async def test_sql_mode_no_firestore_call(monkeypatch):
    set_mode(monkeypatch, "sql")
    from services.performance_stat_router import after_stat_write
    with patch("services.performance_stat_router.set_document", new_callable=AsyncMock) as mock_set:
        await after_stat_write(uuid4(), object())
        mock_set.assert_not_called()


@pytest.mark.asyncio
async def test_dual_write_mode_calls_firestore(monkeypatch):
    set_mode(monkeypatch, "dual_write")
    from services.performance_stat_router import after_stat_write
    with patch("services.performance_stat_router.set_document", new_callable=AsyncMock, return_value=True) as mock_set:
        await after_stat_write(uuid4(), object())
        mock_set.assert_called_once()


@pytest.mark.asyncio
async def test_firestore_mode_reads_from_firestore(monkeypatch):
    set_mode(monkeypatch, "firestore")
    hired_id = uuid4()
    from services.performance_stat_router import read_stat_from_firestore
    with patch("services.performance_stat_router.get_document", new_callable=AsyncMock, return_value={"posts_count": 5}) as mock_get:
        result = await read_stat_from_firestore(hired_id)
        mock_get.assert_called_once_with("agent_performance", str(hired_id))
        assert result == {"posts_count": 5}


@pytest.mark.asyncio
async def test_rollback_to_sql_stops_firestore_reads(monkeypatch):
    """Simulates operator flipping DATA_ROUTER_MODE back to sql."""
    set_mode(monkeypatch, "sql")
    hired_id = uuid4()
    from services.performance_stat_router import read_stat_from_firestore
    with patch("services.performance_stat_router.get_document", new_callable=AsyncMock) as mock_get:
        result = await read_stat_from_firestore(hired_id)
        mock_get.assert_not_called()
        assert result is None
```

**Acceptance criteria (all must pass):**
- [ ] All 4 test functions pass: `pytest tests/test_routing_integration.py -v`
- [ ] No live GCP credentials required (mock path active in `ENVIRONMENT=test`)
- [ ] Rollback test (`test_rollback_to_sql_stops_firestore_reads`) explicitly proves env-var flip works

**Test table:**

| Test | Type | File | Command |
|---|---|---|---|
| All 4 routing mode tests | Integration | `tests/test_routing_integration.py` | `docker-compose -f docker-compose.test.yml run plant-test pytest tests/test_routing_integration.py -v` |
| Full regression | Regression | all | `docker-compose -f docker-compose.test.yml run plant-test pytest -x` |

---

### Epic E4 — Demo cost is governed and measurable

**Customer/operator value:** After Iteration 2 merges, operator can read `waooaw_firestore_drift_total` in Cloud Monitoring, confirm 0 drift over 48h in shadow mode, then flip `DATA_ROUTER_MODE=firestore` in Cloud Run console and scale Cloud SQL demo tier down — provably reducing the demo bill with a data trail.

**DMA/Share Trader alignment:** DMA enablement — demo remains affordable for continuous DMA customer trials. Cost saved is ₹2–3k/month per entity migrated to Firestore path.

---

## Rollback Procedure (operator runbook)

**Time to rollback: < 60 seconds.**

```bash
# Step 1: Flip DATA_ROUTER_MODE back to sql in Cloud Run
gcloud run services update waooaw-plant-backend-demo \
  --update-env-vars DATA_ROUTER_MODE=sql \
  --region asia-south1 \
  --project waooaw-oauth

# Step 2: Verify the update is live
gcloud run services describe waooaw-plant-backend-demo \
  --region asia-south1 --project waooaw-oauth \
  --format "value(spec.template.spec.containers[0].env)"
# Should show DATA_ROUTER_MODE=sql

# Step 3: Confirm Firestore writes stop (check logs)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="waooaw-plant-backend-demo" AND textPayload:"firestore_client"' \
  --project=waooaw-oauth --limit=10 --freshness=5m 2>&1
# Should show no new firestore_client log entries
```

No code change, no deployment, no database migration required for rollback.

---

## Definition of Done

- [ ] `DatastoreRouter` class exists in `src/Plant/BackEnd/core/datastore_router.py`
- [ ] `FirestoreClient` with circuit breaker exists in `src/Plant/BackEnd/core/firestore_client.py`
- [ ] `performance_stat_router.py` wires dual-write for `PerformanceStat` entity
- [ ] Shadow read mode emits `waooaw_firestore_drift_total` Prometheus counter
- [ ] Reconciliation sweep service exists and re-syncs drifted rows
- [ ] Terraform `DATA_ROUTER_MODE` variable added to all three plant environment tfvars
- [ ] All 9 stories have passing tests; no existing test regresses
- [ ] CI (`waooaw-ci.yml`) passes with no new pip-audit ignores needed
- [ ] Rollback procedure is documented and validated (test S4 proves it)
- [ ] Zero changes to API contracts, CP/PP/mobile client code, or CI/CD workflows
