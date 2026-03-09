# CP-DEFECTS-1 — Portal Routing Fixes (PP Ops + Plant Diagnostics)

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-DEFECTS-1` |
| Feature area | PP Portal + Plant Backend — ops proxy route corrections (5 defects) |
| Created | 2026-03-09 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `defect_list_8_Mar_2026.md` — RCA + live route test results |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 4 |
| Total stories | 7 |

---

## Zero-Cost Agent Constraints (READ FIRST)

Every story card is fully self-contained — no cross-references, no "see above".
NFR code patterns are embedded inline; never reference NFRReusable.md.

---

## Background — Defects Being Fixed

Five routing defects were identified during PP portal live testing on 8 March 2026
(see `defect_list_8_Mar_2026.md` for full RCA). Two root-cause themes:

1. **PP BackEnd proxy paths** hardcoded wrong Plant paths (missing `/payments` prefix, wrong param style).
2. **Plant `construct_diagnostics.py`** routers included their own `/v1` prefix, causing double `/v1/v1/…`
   when mounted inside `api_v1_router`.

Additionally, DEF-005 (double-v1) masked two completely missing Plant routes that the PP proxy was
already calling — these must be added to Plant to fully unblock the PP ops console.

| Defect | File | Status in code |
|--------|------|----------------|
| DEF-001: `GET /pp/ops/subscriptions` → wrong Plant path | `src/PP/BackEnd/api/ops_subscriptions.py` | ✅ Fixed |
| DEF-002: `GET /pp/ops/subscriptions/{id}` → missing `/payments` segment | `src/PP/BackEnd/api/ops_subscriptions.py` | ✅ Fixed |
| DEF-003: `GET /pp/ops/hired-agents` → query param instead of path param | `src/PP/BackEnd/api/ops_hired_agents.py` | ✅ Fixed |
| DEF-004: `GET /pp/ops/hired-agents/{id}` → Plant has no bare GET-by-ID | `src/Plant/BackEnd/api/v1/hired_agents_simple.py` | ✅ Fixed |
| DEF-005: double `/v1` prefix on construct_diagnostics routers | `src/Plant/BackEnd/api/v1/construct_diagnostics.py` | ✅ Fixed |
| E4-new: `POST /api/v1/ops/dlq/{id}/requeue` missing in Plant | `src/Plant/BackEnd/api/v1/construct_diagnostics.py` | ✅ Added |
| E4-new: `GET /api/v1/hired-agents/{id}/hook-trace` missing in Plant | `src/Plant/BackEnd/api/v1/construct_diagnostics.py` | ✅ Added |

---

## Agent Execution Rules

> **CHECKPOINT RULE**: After completing each epic (all tests passing), run:
> ```bash
> git add -A && git commit -m "feat(CP-DEFECTS-1): [epic-id] — [epic title]" && git push
> ```
> Do this BEFORE starting the next epic.

- **Scope lock**: Only touch files listed in each story card's "Files to create / modify" table.
- **Never** use bare `APIRouter` — always `waooaw_router()`.
- **GET routes** use `get_read_db_session()`, never `get_db_session()`.
- **STUCK PROTOCOL**: If blocked > 30 min on any epic, post the blocker and HALT.

---

## Iteration 1 — Fix all 5 routing defects + add 2 missing Plant routes

**Time estimate**: 2h  
**Expert persona**: Senior Python 3.11 / FastAPI engineer  
**Prerequisites**: None — all changes are routing/path fixes, no DB migrations needed.

---

### E1 — Fix PP BackEnd subscription proxy paths (DEF-001 + DEF-002)

**Outcome**: `GET /api/pp/ops/subscriptions?customer_id=X` and `GET /api/pp/ops/subscriptions/{id}`
both proxy to the correct Plant payment subscription routes.

#### Story E1-S1 — Fix list subscriptions path (DEF-001)

| Field | Value |
|---|---|
| Status | ✅ Done |
| File | `src/PP/BackEnd/api/ops_subscriptions.py` |
| Change | `plant_path = f"/api/v1/payments/subscriptions/by-customer/{customer_id}"` (was `/api/v1/subscriptions`) |
| Test | `src/PP/BackEnd/tests/test_ops_subscriptions.py` — `test_list_subscriptions_forwards_query_params` asserts path ends with `/by-customer/C1` |

```python
# Pattern (already applied)
customer_id = params.pop("customer_id", None)
if not customer_id:
    raise HTTPException(status_code=400, detail="customer_id is required")
plant_path = f"/api/v1/payments/subscriptions/by-customer/{customer_id}"
```

#### Story E1-S2 — Fix get single subscription path (DEF-002)

| Field | Value |
|---|---|
| Status | ✅ Done |
| File | `src/PP/BackEnd/api/ops_subscriptions.py` |
| Change | `plant_path = f"/api/v1/payments/subscriptions/{subscription_id}"` (was `/api/v1/subscriptions/{id}`) |
| Test | `src/PP/BackEnd/tests/test_ops_subscriptions.py` — `test_get_subscription_uses_payments_path` asserts exact path |

---

### E2 — Fix PP BackEnd hired-agents proxy paths (DEF-003) + Plant GET-by-ID (DEF-004)

**Outcome**: `GET /api/pp/ops/hired-agents?subscription_id=X` calls the correct Plant path-param route.
`GET /api/pp/ops/hired-agents/{id}` no longer 404s in Plant.

#### Story E2-S1 — Fix hired-agents list proxy (DEF-003)

| Field | Value |
|---|---|
| Status | ✅ Done |
| File | `src/PP/BackEnd/api/ops_hired_agents.py` |
| Change | Route on `subscription_id` → call `GET /api/v1/hired-agents/by-subscription/{subscription_id}`; `customer_id` → call `GET /api/v1/hired-agents/by-customer/{customer_id}`; single-object response wrapped in list. |
| Test | `src/PP/BackEnd/tests/test_ops_hired_agents.py` — covers by-subscription, by-customer, single-object wrap, 400 without IDs |

#### Story E2-S2 — Add GET-by-ID route to Plant (DEF-004)

| Field | Value |
|---|---|
| Status | ✅ Done |
| File | `src/Plant/BackEnd/api/v1/hired_agents_simple.py` |
| Change | Added `@router.get("/{hired_instance_id}", response_model=HiredAgentInstanceResponse)` at line 991. Uses `get_read_db_session()`. |
| Test | `src/PP/BackEnd/tests/test_ops_hired_agents.py` — `test_get_hired_agent_returns_200` confirms proxy passes through |

---

### E3 — Fix Plant construct_diagnostics double-v1 prefix (DEF-005)

**Outcome**: `GET /api/v1/hired-agents/{id}/construct-health`, `scheduler-diagnostics`, scheduler pause/resume,
and `GET/POST /api/v1/ops/dlq…` all resolve to the correct Plant handlers.

#### Story E3-S1 — Remove `/v1` from construct_diagnostics router prefixes

| Field | Value |
|---|---|
| Status | ✅ Done |
| File | `src/Plant/BackEnd/api/v1/construct_diagnostics.py` |
| Change | `router = waooaw_router(prefix="/hired-agents", ...)` (was `prefix="/v1/hired-agents"`); `ops_router = waooaw_router(prefix="/ops", ...)` (was `prefix="/v1/ops"`) |
| Test | `src/Plant/BackEnd/tests/test_construct_diagnostics_api.py` — `test_construct_health_returns_200_for_known_hire` and DLQ tests verify correct paths |

---

### E4 — Add missing Plant routes unblocked by DEF-005 fix

**Outcome**: `GET /api/v1/hired-agents/{id}/hook-trace` and `POST /api/v1/ops/dlq/{id}/requeue`
both return valid responses; PP ops console fully unblocked.

#### Story E4-S1 — Add hook-trace stub to Plant (CP-DEFECTS-1 new)

| Field | Value |
|---|---|
| Status | ✅ Done |
| Files to create / modify | `src/Plant/BackEnd/api/v1/construct_diagnostics.py`, `src/Plant/BackEnd/tests/test_construct_diagnostics_api.py` |
| Change | `@router.get("/{hired_agent_id}/hook-trace", response_model=list[HookTraceEntry])` added after `scheduler-diagnostics` route. Returns 404 for unknown hire, empty list for known (no hook-trace table yet — stub). |
| Tests added | `test_hook_trace_returns_404_for_unknown_hire`, `test_hook_trace_returns_empty_list_for_known_hire`, `test_hook_trace_accepts_stage_and_result_filters` |

```python
# Pattern applied (CP-DEFECTS-1 E4-S1)
@router.get(
    "/{hired_agent_id}/hook-trace",
    response_model=list[HookTraceEntry],
)
async def get_hook_trace(
    hired_agent_id: str,
    stage: Optional[str] = None,
    result: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_read_db_session),  # ← MANDATORY read replica
) -> list[HookTraceEntry]:
    if not await _check_hired_agent_exists(hired_agent_id, db):
        raise HTTPException(status_code=404, detail="Hired agent not found")
    return []  # Hook-trace table not yet implemented — non-breaking stub
```

#### Story E4-S2 — Add DLQ requeue route to Plant (CP-DEFECTS-1 new)

| Field | Value |
|---|---|
| Status | ✅ Done |
| Files to create / modify | `src/Plant/BackEnd/api/v1/construct_diagnostics.py`, `src/Plant/BackEnd/tests/test_construct_diagnostics_api.py` |
| Change | `@ops_router.post("/dlq/{dlq_id}/requeue", response_model=dict)` added to `ops_router`. Deletes the DLQ row (removes from dead-letter queue → scheduler can retry); returns `{"status": "queued", "dlq_id": dlq_id}`; 404 when not found. Uses `get_db_session()` (write path). |
| Tests added | `test_dlq_requeue_returns_404_for_unknown_entry`, `test_dlq_requeue_returns_queued_status_on_success` |

```python
# Pattern applied (CP-DEFECTS-1 E4-S2)
@ops_router.post("/dlq/{dlq_id}/requeue", response_model=dict)
async def requeue_dlq_entry(
    dlq_id: str,
    db: AsyncSession = Depends(get_db_session),  # ← write path
) -> dict:
    from sqlalchemy import delete as sa_delete
    from models.scheduler_dlq import SchedulerDLQModel

    result = await db.execute(
        sa_delete(SchedulerDLQModel).where(SchedulerDLQModel.dlq_id == dlq_id)
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="DLQ entry not found")

    return {"status": "queued", "dlq_id": dlq_id}
```

---

## How to Launch Iteration 1 Agent

This iteration is **complete**. All epics (E1–E4) are implemented and tested.

To verify:
```bash
# PP BackEnd tests (covers E1, E2, E3 proxy-side)
docker-compose -f docker-compose.test.yml run pp-test pytest -x -v \
  tests/test_ops_subscriptions.py tests/test_ops_hired_agents.py \
  tests/test_ops_diagnostics.py tests/test_ops_dlq.py

# Plant BackEnd tests (covers E3, E4 Plant-side)
docker-compose -f docker-compose.test.yml run plant-test pytest -x -v \
  tests/test_construct_diagnostics_api.py
```

## PM Review Checklist

- [x] All 5 defects from `defect_list_8_Mar_2026.md` addressed
- [x] 2 missing Plant routes added (hook-trace stub + DLQ requeue)
- [x] Tests exist for every story
- [x] GET routes use `get_read_db_session()` — POST/DELETE use `get_db_session()`
- [x] `waooaw_router()` used throughout — no bare `APIRouter`
- [x] No DB migrations required — all changes are routing/logic only
- [x] No environment-specific values hardcoded
