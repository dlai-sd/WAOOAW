# PP-MOULD-1 — Platform IT Diagnostic Toolkit

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PP-MOULD-1` |
| Feature area | PP BackEnd (diagnostic routes) + PP FrontEnd (React 18 / Vite web panels) |
| Created | 2026-03-07 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/plant/AGENT-CONSTRUCT-DESIGN.md` §14 (esp. §14.3, §14.4, §14.7) |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 3 |
| Total epics | 6 |
| Total stories | 12 |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story — agent never opens NFRReusable.md |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. Do NOT open NFRReusable.md. All patterns you need are in your card.

---

## PM Review Checklist

- [x] Epic titles name operator/IT outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] PP RBAC role requirements specified in every backend route story (7-role OPA hierarchy)
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before frontend (S2)
- [x] No placeholders remain

---

## PP RBAC Reference (embed in every route story — do NOT open NFRReusable.md)

PP enforces a 7-role OPA hierarchy. Minimum role required per route type:

| Role | Level | Can access |
|---|---|---|
| `admin` | highest | All routes including destructive mutations |
| `developer` | 2nd | All read routes + non-destructive writes |
| `manager` | 3rd | Cost/billing reads, approvals |
| `agent_ops` | 4th | Hired-agent state reads |
| `support` | 5th | Customer-facing reads only |
| `readonly` | 6th | Audit log reads |
| `viewer` | lowest | Public metrics only |

**Route RBAC assignments for this plan:**
- `GET .../construct-health` → `developer`
- `GET .../scheduler-diagnostics` → `developer`
- `POST .../scheduler/pause` + `/resume` → `admin`
- `GET /ops/dlq` → `developer`
- `POST /ops/dlq/{id}/requeue` → `admin`
- `GET .../hook-trace` → `developer`
- `PATCH .../constraint-policy` → `admin` (with mandatory audit log)

**OPA enforcement pattern (copy exactly — do NOT reference NFRReusable.md):**
```python
from core.authorization import require_role
from core.routing import waooaw_router

router = waooaw_router(prefix="/pp/your-resource", tags=["pp-your-resource"])

@router.get("/{id}/your-endpoint")
async def your_handler(
    id: str,
    _auth = Depends(require_role("developer")),   # ← OPA enforcement
    db: AsyncSession = Depends(get_read_db_session),
):
    ...
```

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — New PP BackEnd diagnostic routes: construct-health, scheduler-diagnostics, pause/resume, DLQ, hook-trace, constraint-policy PATCH | 3 | 6 | 4.5h | +5h after launch |
| 2 | Lane A — PP React FrontEnd: ConstructHealthPanel drawer (6-card grid), SchedulerDiagnosticsPanel tab, HookTracePanel tab | 2 | 3 | 4h | +5h after launch |
| 3 | Lane A — PP React FrontEnd: AgentTypeSetupScreen form, ConstraintPolicyLiveTuneDrawer, ApprovalsQueueScreen overhaul | 1 | 3 | 3.5h | +4h after launch |

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check:**
```bash
git status && git log --oneline -3
# Must show: clean tree on main.
```

**Iteration 1 agent task** (paste verbatim into @platform-engineer):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer experienced with operator tooling, RBAC, and thin proxy patterns.
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11/FastAPI/RBAC engineer, I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-MOULD-1-diagnostic-toolkit.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2 or 3.
TIME BUDGET: 4.5h. If you reach 5h without finishing, follow STUCK PROTOCOL.

PREREQUISITE CHECK:
  git log --oneline origin/main | head -5
  Must show: feat(PLANT-MOULD-1) iteration 2 merged.
  If not: post "Blocked: PLANT-MOULD-1 not fully merged." HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" section.
2. Read "Iteration 1" section, including "PP RBAC Reference".
3. Execute Epics: E1 → E2 → E3
4. Docker-test all routes.
5. Open iteration PR. Post URL. HALT.
```

Come back at: **+5h after launch**

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge:**
```bash
git fetch origin && git log --oneline origin/main | head -5
# Must show: feat(PP-MOULD-1): iteration 1
```

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Vite engineer experienced with operator dashboards, data tables, and real-time status UIs.
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React 18/TypeScript/Vite engineer, I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-MOULD-1-diagnostic-toolkit.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5. Do not touch Iteration 1 or 3.
TIME BUDGET: 4h.

PREREQUISITE CHECK:
  git log --oneline origin/main | head -5
  Must show: feat(PP-MOULD-1): iteration 1 merged.
  If not: HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 2" sections.
2. Execute Epics: E4 → E5
3. Run: cd src/PP/FrontEnd && npm test -- --forceExit
4. Open iteration PR. Post URL. HALT.
```

Come back at: **+5h after launch**

---

### Iteration 3

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Verify merge:**
```bash
git fetch origin && git log --oneline origin/main | head -5
# Must show: feat(PP-MOULD-1): iteration 2
```

**Iteration 3 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Vite engineer experienced with complex forms, live-tune drawers, and approval workflows.
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React 18/TypeScript engineer, I will [what] by [approach]."

PLAN FILE: docs/PP/iterations/PP-MOULD-1-diagnostic-toolkit.md
YOUR SCOPE: Iteration 3 only — Epic E6. Do not touch previous content.
TIME BUDGET: 3.5h.

PREREQUISITE CHECK:
  git log --oneline origin/main | head -5
  Must show: feat(PP-MOULD-1): iteration 2 merged.
  If not: HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 3" sections.
2. Execute Epic E6 (3 stories).
3. Run: cd src/PP/FrontEnd && npm test -- --forceExit
4. Open iteration PR. Post URL. HALT.
```

Come back at: **+4h after launch**

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas
Read `EXPERT PERSONAS:` from your task block. Open every epic with the persona.

### Rule 0 — Open tracking draft PR first
```bash
git checkout main && git pull
git checkout -b feat/PP-MOULD-1-itN-eN
git commit --allow-empty -m "chore(PP-MOULD-1): start iteration N"
git push origin feat/PP-MOULD-1-itN-eN
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/PP-MOULD-1-itN-eN`.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria. Do not add features or refactor unrelated code.

### Rule 3 — Tests before the next story

### Rule 4 — Commit + push after every story
```bash
git add -A
git commit -m "feat(PP-MOULD-1): [story title]"
git push origin feat/PP-MOULD-1-itN-eN
```

### Rule 5 — Integration test after every epic
**Backend (Iteration 1):**
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```
**FrontEnd (Iterations 2, 3):**
```bash
cd src/PP/FrontEnd && npm test -- --forceExit
```

### Rule 6 — STUCK PROTOCOL
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/PP-MOULD-1-itN-eN
```
**HALT. Post the blocked story ID and exact error. Do not start the next story.**

### Rule 7 — Iteration PR
```bash
git checkout -b feat/PP-MOULD-1-itN-rollup
git merge --no-ff [all epic branches for this iteration]
git push origin feat/PP-MOULD-1-itN-rollup
gh pr create --base main --title "feat(PP-MOULD-1): iteration N — [summary]" --body "..."
```

### CHECKPOINT RULE
After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(PP-MOULD-1): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic.

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | E1: Construct health + scheduler endpoints | `GET /pp/ops/hired-agents/{id}/construct-health` + `GET .../scheduler-diagnostics` | 🔴 Not Started | — |
| E1-S2 | 1 | E1: Construct health + scheduler endpoints | `POST .../scheduler/pause` + `POST .../scheduler/resume` | 🔴 Not Started | — |
| E2-S1 | 1 | E2: DLQ endpoints | `GET /pp/ops/dlq` + `POST /pp/ops/dlq/{id}/requeue` | 🔴 Not Started | — |
| E2-S2 | 1 | E2: DLQ endpoints | `GET /pp/ops/hired-agents/{id}/hook-trace` | 🔴 Not Started | — |
| E3-S1 | 1 | E3: Constraint policy PATCH | `PATCH /pp/agent-setups/{id}/constraint-policy` | 🔴 Not Started | — |
| E3-S2 | 1 | E3: Constraint policy PATCH | `GET /pp/agent-setups/{id}/constraint-policy` (read route) | 🔴 Not Started | — |
| E4-S1 | 2 | E4: ConstructHealthPanel | `ConstructHealthPanel.tsx` drawer with 6-card construct grid | 🔴 Not Started | — |
| E4-S2 | 2 | E4: ConstructHealthPanel | Wire `ConstructHealthPanel` into `OpsHiredAgentsList` row action | 🔴 Not Started | — |
| E5-S1 | 2 | E5: Scheduler + Hook panels | `SchedulerDiagnosticsPanel.tsx` tab | 🔴 Not Started | — |
| E5-S2 | 2 | E5: Scheduler + Hook panels | `HookTracePanel.tsx` tab with 50-row event table + filters | 🔴 Not Started | — |
| E6-S1 | 3 | E6: Setup + policy + approvals | `AgentTypeSetupScreen.tsx` form (new) | 🔴 Not Started | — |
| E6-S2 | 3 | E6: Setup + policy + approvals | `ConstraintPolicyLiveTuneDrawer.tsx` + `ApprovalsQueueScreen.tsx` overhaul | 🔴 Not Started | — |

---

## Iteration 1

### Epic E1: PP operators can read and control scheduler health for any hired agent

**Outcome:** PP IT operators can call four new PP BackEnd endpoints to read construct health, get scheduler diagnostics, and pause/resume any hired agent's scheduler from the ops console.

**Context (2 sentences):** `src/PP/BackEnd/api/ops_hired_agents.py` already uses `waooaw_router(prefix="/ops/hired-agents")` — add the new routes there. All read routes proxy to Plant's `construct_diagnostics` endpoints added in PLANT-MOULD-1; pause/resume routes proxy to Plant's scheduler control endpoints.

---

#### E1-S1 — `GET /pp/ops/hired-agents/{id}/construct-health` + `GET .../scheduler-diagnostics`

**Branch:** `feat/PP-MOULD-1-it1-e1`
**BLOCKED UNTIL:** `PLANT-MOULD-1` Iteration 2 merged to `main` (Plant diagnostic endpoints must exist)
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/PP/BackEnd/api/ops_hired_agents.py` — existing routes, `waooaw_router` usage
2. `src/PP/BackEnd/clients/plant_client.py` — `PlantGatewayClient` for PP (circuit breaker already present)
3. `src/PP/BackEnd/api/approvals.py` — `require_role` import pattern in PP

**NFR patterns to copy exactly (inline — do NOT open NFRReusable.md):**
```python
# PP BackEnd: MANDATORY patterns for every new route
from core.routing import waooaw_router                 # ← never bare APIRouter
from core.database import get_read_db_session          # ← GET routes only
from core.authorization import require_role            # ← OPA RBAC enforcement
from services.audit_dependency import AuditLogger, get_audit_logger  # ← mutations only
import logging

logger = logging.getLogger(__name__)

# Read route pattern (developer+ required)
@router.get("/{hired_agent_id}/construct-health")
async def get_construct_health(
    hired_agent_id: str,
    _auth = Depends(require_role("developer")),         # ← RBAC: developer+
    db: AsyncSession = Depends(get_read_db_session),   # ← read replica
):
    ...
```

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/PP/BackEnd/api/ops_hired_agents.py` — add 2 GET routes |
| CREATE | `src/PP/BackEnd/tests/test_ops_diagnostics.py` |

**What to build:**
```python
# Add to src/PP/BackEnd/api/ops_hired_agents.py

@router.get("/{hired_agent_id}/construct-health")
async def get_construct_health(
    hired_agent_id: str,
    _auth = Depends(require_role("developer")),
    db: AsyncSession = Depends(get_read_db_session),
):
    """Returns 6-construct health snapshot for ConstructHealthPanel drawer.

    Proxies to Plant GET /v1/hired-agents/{id}/construct-health.
    PP adds RBAC gate (developer+) — no business logic, no data storage.
    """
    from clients.plant_client import PlantGatewayClient
    client = PlantGatewayClient()
    return await client.request_json(
        "GET", f"/v1/hired-agents/{hired_agent_id}/construct-health"
    )


@router.get("/{hired_agent_id}/scheduler-diagnostics")
async def get_scheduler_diagnostics(
    hired_agent_id: str,
    _auth = Depends(require_role("developer")),
    db: AsyncSession = Depends(get_read_db_session),
):
    """Returns full scheduler diagnostic state for SchedulerDiagnosticsPanel tab.

    Proxies to Plant GET /v1/hired-agents/{id}/scheduler-diagnostics.
    """
    from clients.plant_client import PlantGatewayClient
    client = PlantGatewayClient()
    return await client.request_json(
        "GET", f"/v1/hired-agents/{hired_agent_id}/scheduler-diagnostics"
    )
```

**Acceptance criteria:**
- [ ] `GET /ops/hired-agents/{id}/construct-health` returns 200 for valid hire; 403 without `developer` role
- [ ] `GET /ops/hired-agents/{id}/scheduler-diagnostics` returns 200; 403 without `developer` role
- [ ] Both routes use `get_read_db_session` (confirm in dependency graph)
- [ ] `waooaw_router` in use — no bare `APIRouter`
- [ ] `pytest src/PP/BackEnd/tests/test_ops_diagnostics.py` exits 0

**Tests to write:**
```python
# src/PP/BackEnd/tests/test_ops_diagnostics.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

def test_construct_health_requires_developer_role(client):
    # Call with viewer role token — expect 403
    resp = client.get("/ops/hired-agents/ha-1/construct-health",
                      headers={"Authorization": "Bearer viewer_token"})
    assert resp.status_code == 403

def test_construct_health_ok_for_developer(client, mock_plant_client):
    mock_plant_client.request_json = AsyncMock(return_value={"scheduler": "ok"})
    resp = client.get("/ops/hired-agents/ha-1/construct-health",
                      headers={"Authorization": "Bearer developer_token"})
    assert resp.status_code == 200

def test_scheduler_diagnostics_requires_developer_role(client):
    resp = client.get("/ops/hired-agents/ha-1/scheduler-diagnostics",
                      headers={"Authorization": "Bearer viewer_token"})
    assert resp.status_code == 403

def test_scheduler_diagnostics_ok(client, mock_plant_client):
    mock_plant_client.request_json = AsyncMock(return_value={"cron": "ok"})
    resp = client.get("/ops/hired-agents/ha-1/scheduler-diagnostics",
                      headers={"Authorization": "Bearer developer_token"})
    assert resp.status_code == 200
```

---

#### E1-S2 — `POST /ops/hired-agents/{id}/scheduler/pause` + `POST .../scheduler/resume`

**Branch:** `feat/PP-MOULD-1-it1-e1`
**BLOCKED UNTIL:** E1-S1 merged
**Estimate:** 45 min

**Files to read first (max 3):**
1. `src/PP/BackEnd/api/ops_hired_agents.py` — updated in E1-S1
2. `src/PP/BackEnd/clients/plant_client.py`

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/PP/BackEnd/api/ops_hired_agents.py` — add pause + resume routes |
| MODIFY | `src/PP/BackEnd/tests/test_ops_diagnostics.py` — add tests |

**PP mutation pattern with audit log (copy exactly — never from NFRReusable.md):**
```python
from services.audit_dependency import AuditLogger, get_audit_logger

@router.post("/{hired_agent_id}/scheduler/pause")
async def pause_scheduler(
    hired_agent_id: str,
    _auth = Depends(require_role("admin")),             # ← RBAC: admin ONLY
    audit: AuditLogger = Depends(get_audit_logger),    # ← mandatory on mutations
    db: AsyncSession = Depends(get_db_session),        # ← write session for mutations
):
    from clients.plant_client import PlantGatewayClient
    client = PlantGatewayClient()
    result = await client.request_json("POST", f"/v1/hired-agents/{hired_agent_id}/pause")
    await audit.log(
        screen="ops_hired_agents",
        action="scheduler_pause",
        outcome="success",
        hired_agent_id=hired_agent_id,
        # Note: PIIMaskingFilter active — do NOT log customer email here
    )
    return result
```

**Acceptance criteria:**
- [ ] `POST .../scheduler/pause` returns 200; 403 for non-admin roles
- [ ] `POST .../scheduler/resume` returns 200; 403 for non-admin roles
- [ ] Both routes write an audit log entry
- [ ] Tests pass (including 403 check for `developer` role on pause/resume)

---

### Epic E2: PP operators can inspect the DLQ and trace hook execution

**Outcome:** PP developers can view all entries in the dead-letter queue across all agents, requeue failed hook events, and view a timeline of all hook executions for a specific hired agent.

**Context (2 sentences):** DLQ entries land in `scheduler_dlq` table when a hook `HookDecision.proceed=False` and the run cannot be retried — today there is no API to surface these. `hook-trace` endpoint returns the last 50 `HookEvent` records for a hired agent stored in `goal_run_audit` or equivalent hook log table.

---

#### E2-S1 — `GET /pp/ops/dlq` + `POST /pp/ops/dlq/{id}/requeue`

**Branch:** `feat/PP-MOULD-1-it1-e2`
**BLOCKED UNTIL:** E1-S2 merged
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/PP/BackEnd/api/ops_hired_agents.py`
2. `src/PP/BackEnd/clients/plant_client.py`
3. `src/Plant/BackEnd/models/` — look for `scheduler_dlq.py` to understand DLQ table fields

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/PP/BackEnd/api/ops_dlq.py` — new router |
| MODIFY | `src/PP/BackEnd/main.py` — register `ops_dlq_router` |
| CREATE | `src/PP/BackEnd/tests/test_ops_dlq.py` |

**What to build — NFR patterns to copy exactly:**
```python
# src/PP/BackEnd/api/ops_dlq.py
from __future__ import annotations
from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.routing import waooaw_router                 # ← MANDATORY
from core.database import get_read_db_session          # ← GET routes
from core.database import get_db_session               # ← POST/mutation routes
from core.authorization import require_role
from services.audit_dependency import AuditLogger, get_audit_logger
import logging

logger = logging.getLogger(__name__)

router = waooaw_router(prefix="/pp/ops/dlq", tags=["pp-ops-dlq"])


@router.get("/", response_model=list[dict])
async def list_dlq_entries(
    agent_type: str | None = Query(None),
    hired_agent_id: str | None = Query(None),
    limit: int = Query(50, le=200),
    _auth = Depends(require_role("developer")),          # RBAC: developer+
    db: AsyncSession = Depends(get_read_db_session),    # GET — read replica
):
    """List DLQ entries. Filterable by agent_type and/or hired_agent_id.

    Returns: list of {dlq_id, hired_agent_id, failed_at, hook_stage,
                       error_message (first 200 chars), retry_count}
    Proxies to Plant GET /v1/ops/dlq with query params forwarded.
    """
    from clients.plant_client import PlantGatewayClient
    client = PlantGatewayClient()
    params: dict = {"limit": limit}
    if agent_type:
        params["agent_type"] = agent_type
    if hired_agent_id:
        params["hired_agent_id"] = hired_agent_id
    return await client.request_json("GET", "/v1/ops/dlq", params=params)


@router.post("/{dlq_id}/requeue")
async def requeue_dlq_entry(
    dlq_id: str,
    _auth = Depends(require_role("admin")),              # RBAC: admin ONLY
    audit: AuditLogger = Depends(get_audit_logger),     # mandatory audit
    db: AsyncSession = Depends(get_db_session),         # write session
):
    """Requeue a DLQ entry for retry execution.

    Only admin role can requeue — retries trigger a goal run on Plant.
    Action is audit-logged with dlq_id.
    """
    from clients.plant_client import PlantGatewayClient
    client = PlantGatewayClient()
    result = await client.request_json("POST", f"/v1/ops/dlq/{dlq_id}/requeue")
    await audit.log(
        screen="ops_dlq",
        action="dlq_requeue",
        outcome="success",
        dlq_id=dlq_id,
    )
    return result
```

Register in `main.py`:
```python
from api.ops_dlq import router as ops_dlq_router
app.include_router(ops_dlq_router)
```

**Acceptance criteria:**
- [ ] `GET /pp/ops/dlq` returns 200 list; 403 for `viewer` role
- [ ] `POST /pp/ops/dlq/{id}/requeue` returns 200; 403 for `developer` role (admin only)
- [ ] Requeue writes an audit log entry with `dlq_id`
- [ ] `pytest src/PP/BackEnd/tests/test_ops_dlq.py` exits 0

---

#### E2-S2 — `GET /pp/ops/hired-agents/{id}/hook-trace`

**Branch:** `feat/PP-MOULD-1-it1-e2`
**BLOCKED UNTIL:** E2-S1 merged
**Estimate:** 45 min

**Files to read first (max 3):**
1. `src/PP/BackEnd/api/ops_hired_agents.py`
2. `src/PP/BackEnd/clients/plant_client.py`

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/PP/BackEnd/api/ops_hired_agents.py` — add hook-trace route |
| MODIFY | `src/PP/BackEnd/tests/test_ops_diagnostics.py` |

**What to build:**
```python
# Append to ops_hired_agents.py

class HookTraceEntry(BaseModel):
    event_id: str
    stage: str           # HookStage enum value
    hired_agent_id: str
    agent_type: str
    result: str          # "proceed" or "halt"
    reason: str
    emitted_at: str      # ISO-8601
    payload_summary: str # first 100 chars of payload JSON — no PII

@router.get("/{hired_agent_id}/hook-trace", response_model=list[HookTraceEntry])
async def get_hook_trace(
    hired_agent_id: str,
    stage: str | None = Query(None),
    result: str | None = Query(None),
    limit: int = Query(50, le=200),
    _auth = Depends(require_role("developer")),         # RBAC: developer+
    db: AsyncSession = Depends(get_read_db_session),   # GET — read replica
):
    """Returns last N hook events for this hired agent.

    Filterable by stage (e.g. "pre_pump") and result ("proceed"/"halt").
    Proxies to Plant GET /v1/hired-agents/{id}/hook-trace.
    payload_summary is truncated at 100 chars by Plant — no PII exposure.
    """
    from clients.plant_client import PlantGatewayClient
    client = PlantGatewayClient()
    params: dict = {"limit": limit}
    if stage:
        params["stage"] = stage
    if result:
        params["result"] = result
    return await client.request_json(
        "GET", f"/v1/hired-agents/{hired_agent_id}/hook-trace", params=params
    )
```

**Acceptance criteria:**
- [ ] `GET .../hook-trace` returns 200 list; 403 for `viewer` role
- [ ] `stage` and `result` query params are forwarded to Plant
- [ ] `payload_summary` in response never exceeds 100 chars
- [ ] Tests pass

---

### Epic E3: PP admins can tune agent behaviour without a deploy

**Outcome:** PP admins can read and update the `ConstraintPolicy` for any agent type (approval mode, task caps, position limits) via REST — changes take effect on the next goal run without any code deployment.

**Context (2 sentences):** `src/PP/BackEnd/api/agent_setups.py` manages `AgentType` configuration — add two routes there for reading and patching `ConstraintPolicy` fields. The PATCH route requires `admin` role and writes a mandatory audit log entry because changing `approval_mode` or `max_position_size_inr` is a high-impact action.

---

#### E3-S1 — `PATCH /pp/agent-setups/{id}/constraint-policy`

**Branch:** `feat/PP-MOULD-1-it1-e3`
**BLOCKED UNTIL:** E1-S2 merged (audit log pattern confirmed)
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/PP/BackEnd/api/agent_setups.py` — existing routes, `waooaw_router` usage
2. `src/PP/BackEnd/models/agent_setup.py` — or `agent_type.py` — to find where `constraint_policy` JSONB is stored
3. `src/PP/BackEnd/services/audit_dependency.py` — `AuditLogger` interface

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/PP/BackEnd/api/agent_setups.py` — add PATCH route |
| CREATE | `src/PP/BackEnd/tests/test_agent_setup_constraint_policy.py` |

**What to build — NFR patterns to copy exactly:**
```python
# Append to src/PP/BackEnd/api/agent_setups.py

from pydantic import BaseModel
from typing import Optional

class ConstraintPolicyPatch(BaseModel):
    """Partial update — all fields optional. Only provided fields are changed."""
    approval_mode: Optional[str] = None        # "manual" or "auto"
    max_tasks_per_day: Optional[int] = None    # 0 = no limit
    max_position_size_inr: Optional[float] = None   # 0.0 = no limit
    trial_task_limit: Optional[int] = None


@router.patch("/{agent_setup_id}/constraint-policy")
async def update_constraint_policy(
    agent_setup_id: str,
    patch: ConstraintPolicyPatch,
    _auth = Depends(require_role("admin")),             # ← RBAC: admin ONLY
    audit: AuditLogger = Depends(get_audit_logger),    # ← MANDATORY on mutation
    db: AsyncSession = Depends(get_db_session),        # ← write session for mutations
):
    """Update ConstraintPolicy fields for an agent type.

    Uses partial update (PATCH semantics) — only provided fields are changed.
    Writes mandatory audit record including: admin user_id, changed fields, old/new values.
    Does NOT log approval_mode raw value to avoid PII (mode is not PII, but good habit).
    """
    # 1. Load existing agent_setup row
    # 2. Merge patch into existing constraint_policy JSONB
    # 3. Save updated row
    # 4. Write audit log
    patch_data = patch.model_dump(exclude_none=True)
    if not patch_data:
        raise HTTPException(status_code=422, detail="No fields provided to update")

    # Load agent_setup from DB
    stmt = select(AgentSetup).where(AgentSetup.id == agent_setup_id)
    result = await db.execute(stmt)
    agent_setup = result.scalar_one_or_none()
    if not agent_setup:
        raise HTTPException(status_code=404, detail="AgentSetup not found")

    # Merge into existing policy
    existing_policy: dict = agent_setup.constraint_policy or {}
    updated_policy = {**existing_policy, **patch_data}
    agent_setup.constraint_policy = updated_policy
    await db.commit()
    await db.refresh(agent_setup)

    # Audit — record changed fields (not values to keep audit log clean of operational data)
    await audit.log(
        screen="agent_setups",
        action="constraint_policy_patch",
        outcome="success",
        agent_setup_id=agent_setup_id,
        changed_fields=list(patch_data.keys()),
    )
    return {"agent_setup_id": agent_setup_id, "constraint_policy": updated_policy}
```

**Acceptance criteria:**
- [ ] `PATCH .../constraint-policy` returns 200 with updated policy; 403 for `developer` role
- [ ] Returns 404 for unknown `agent_setup_id`
- [ ] Returns 422 when request body has no fields
- [ ] Audit log entry is written with `changed_fields` list
- [ ] Partial update: only provided fields change; other fields remain unchanged
- [ ] `pytest src/PP/BackEnd/tests/test_agent_setup_constraint_policy.py` exits 0

---

#### E3-S2 — `GET /pp/agent-setups/{id}/constraint-policy`

**Branch:** `feat/PP-MOULD-1-it1-e3`
**BLOCKED UNTIL:** E3-S1 merged
**Estimate:** 30 min

**Files to read first (max 3):**
1. `src/PP/BackEnd/api/agent_setups.py` — updated in E3-S1

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/PP/BackEnd/api/agent_setups.py` — add GET route |
| MODIFY | `src/PP/BackEnd/tests/test_agent_setup_constraint_policy.py` |

**What to build:**
```python
# Append to agent_setups.py

@router.get("/{agent_setup_id}/constraint-policy")
async def get_constraint_policy(
    agent_setup_id: str,
    _auth = Depends(require_role("developer")),         # RBAC: developer+
    db: AsyncSession = Depends(get_read_db_session),   # ← GET — read replica
):
    """Returns current ConstraintPolicy for the given agent type setup.

    developer+ can READ; admin required to PATCH (see E3-S1).
    """
    stmt = select(AgentSetup).where(AgentSetup.id == agent_setup_id)
    result = await db.execute(stmt)
    agent_setup = result.scalar_one_or_none()
    if not agent_setup:
        raise HTTPException(status_code=404, detail="AgentSetup not found")
    return {
        "agent_setup_id": agent_setup_id,
        "constraint_policy": agent_setup.constraint_policy or {},
    }
```

**Acceptance criteria:**
- [ ] `GET .../constraint-policy` returns 200 with `constraint_policy` dict; 403 for `viewer` role
- [ ] Returns 404 for unknown `agent_setup_id`
- [ ] Uses `get_read_db_session` (not write session)
- [ ] Tests pass

---

## Iteration 2

### Epic E4: PP operators see a 6-card construct health grid for any hired agent

**Outcome:** Any PP developer/admin can click a "Health" button on the hired-agents list row and see a drawer panel with 6 cards — one per construct — showing live status indicators without leaving the page.

**Context (2 sentences):** `OpsHiredAgentsList` (the existing PP web table of all hired agents) needs a new row action that opens a `ConstructHealthPanel` drawer. The drawer calls `GET /pp/ops/hired-agents/{id}/construct-health` added in Iteration 1 and renders 6 cards (Scheduler, Pump, Processor, Connector, Publisher, Policy) each with a traffic-light status and key metrics.

---

#### E4-S1 — `ConstructHealthPanel.tsx` drawer with 6-card construct grid

**Branch:** `feat/PP-MOULD-1-it2-e4`
**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimate:** 75 min

**Files to read first (max 3):**
1. `src/PP/FrontEnd/src/pages/OpsHiredAgentsList.tsx` (or equivalent list page) — row structure and existing drawer patterns
2. `src/PP/FrontEnd/src/components/` — check for existing Drawer/Panel component to reuse
3. `src/PP/FrontEnd/src/hooks/` — check for fetch hook pattern (`useFetch`, `useQuery`, etc.)

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/PP/FrontEnd/src/components/ConstructHealthPanel.tsx` |
| CREATE | `src/PP/FrontEnd/src/hooks/useConstructHealth.ts` |
| CREATE | `src/PP/FrontEnd/src/__tests__/ConstructHealthPanel.test.tsx` |

**What to build — `ConstructHealthPanel.tsx`:**

The panel is a slide-in drawer. It receives `hiredAgentId` as a prop and fetches from the PP BackEnd:

```typescript
// src/PP/FrontEnd/src/components/ConstructHealthPanel.tsx
interface ConstructHealthPanelProps {
  hiredAgentId: string;
  isOpen: boolean;
  onClose: () => void;
}

// 6 construct cards to render
const CONSTRUCT_CARDS = [
  { key: "scheduler",  label: "Scheduler",  icon: "⏱" },
  { key: "pump",       label: "Pump",        icon: "⬆" },
  { key: "processor",  label: "Processor",   icon: "⚙" },
  { key: "connector",  label: "Connector",   icon: "🔗" },
  { key: "publisher",  label: "Publisher",   icon: "📤" },
  { key: "policy",     label: "Policy",      icon: "🛡" },
] as const;

// Traffic-light status helper
function statusColor(status: string): string {
  if (status === "healthy") return "#10b981";
  if (status === "degraded") return "#f59e0b";
  return "#ef4444"; // "offline" or unknown
}
```

Each card renders:
- Construct name + icon
- Status dot (green/yellow/red)
- 2–3 key metrics from the corresponding section of `ConstructHealthResponse`
- For `connector`: `secret_ref` shown as `****{last4}` — never full value

Hook:
```typescript
// src/PP/FrontEnd/src/hooks/useConstructHealth.ts
export function useConstructHealth(hiredAgentId: string) {
  // GET /pp/ops/hired-agents/{id}/construct-health
  // Returns: { data: ConstructHealthResponse | null, isLoading, error, refetch }
}
```

**Acceptance criteria:**
- [ ] `ConstructHealthPanel` renders 6 cards with names from `CONSTRUCT_CARDS`
- [ ] Status dots use correct colors (green/yellow/red)
- [ ] `connector.secret_ref` is displayed as `****{last4}` — assertion in test
- [ ] Panel closes on `onClose` callback
- [ ] `useConstructHealth` returns `isLoading=true` while fetching
- [ ] Jest tests pass

---

#### E4-S2 — Wire `ConstructHealthPanel` into `OpsHiredAgentsList` row action

**Branch:** `feat/PP-MOULD-1-it2-e4`
**BLOCKED UNTIL:** E4-S1 merged
**Estimate:** 30 min

**Files to read first (max 3):**
1. `src/PP/FrontEnd/src/pages/OpsHiredAgentsList.tsx`
2. `src/PP/FrontEnd/src/components/ConstructHealthPanel.tsx` — just created

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/PP/FrontEnd/src/pages/OpsHiredAgentsList.tsx` |

**What to build:**

Add a "Health" icon/button to each table row's action column. On click, open `ConstructHealthPanel` with the row's `hiredAgentId`:

```typescript
// In OpsHiredAgentsList — add state:
const [healthPanelAgentId, setHealthPanelAgentId] = useState<string | null>(null);

// In the actions cell for each row, add:
<button
  onClick={() => setHealthPanelAgentId(row.hired_agent_id)}
  title="View construct health"
  aria-label="Construct health"
>
  🩺 Health
</button>

// After the table, add:
{healthPanelAgentId && (
  <ConstructHealthPanel
    hiredAgentId={healthPanelAgentId}
    isOpen={true}
    onClose={() => setHealthPanelAgentId(null)}
  />
)}
```

**Acceptance criteria:**
- [ ] Each row in `OpsHiredAgentsList` has a "Health" action button
- [ ] Clicking a row's Health button opens `ConstructHealthPanel` for that agent
- [ ] Closing the panel sets `healthPanelAgentId` to `null`
- [ ] No other rows are affected (only one drawer open at a time)
- [ ] Existing table snapshot tests still pass

---

### Epic E5: PP developers can diagnose scheduler lag and trace every hook execution

**Outcome:** Two new detail tabs appear in the hired-agent detail view: `Scheduler Diagnostics` with cron, lag gauge, and DLQ inline table; and `Hook Trace` with a 50-row filterable event table.

**Context (2 sentences):** Both tabs are part of the hired-agent detail page/drawer that exists in PP FrontEnd — add them as new tab options. They are powered by the two PP BackEnd endpoints added in Iteration 1 (`scheduler-diagnostics` and `hook-trace`).

---

#### E5-S1 — `SchedulerDiagnosticsPanel.tsx` tab

**Branch:** `feat/PP-MOULD-1-it2-e5`
**BLOCKED UNTIL:** E4-S2 merged
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/PP/FrontEnd/src/pages/` — look for hired agent detail page/drawer that has tabs
2. `src/PP/FrontEnd/src/hooks/` — fetch hook pattern

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/PP/FrontEnd/src/components/SchedulerDiagnosticsPanel.tsx` |
| CREATE | `src/PP/FrontEnd/src/hooks/useSchedulerDiagnostics.ts` |
| MODIFY | Hired agent detail page/drawer — add "Scheduler" tab |
| CREATE | `src/PP/FrontEnd/src/__tests__/SchedulerDiagnosticsPanel.test.tsx` |

**What to build:**

```typescript
// SchedulerDiagnosticsPanel shows:
// 1. Cron expression + human-readable translation
//    e.g. "0 9 * * 1-5" → "Every weekday at 9:00 AM"
// 2. Next run, last run, lag gauge
// 3. Pause/Resume controls (admin role only — hide for non-admin)
// 4. DLQ inline table when dlq_depth > 0 (columns: failed_at, hook_stage, error_message)
// 5. Trial usage: tasks_used_today / trial_task_limit progress bar

interface SchedulerDiagnosticsPanelProps {
  hiredAgentId: string;
  isAdmin: boolean;   // show pause/resume buttons only for admin users
}

// Human-readable cron helper (no external lib — simple cases only):
function describeCron(expr: string): string {
  // For complex crons, return expr unchanged with a note "custom schedule"
  const parts = expr.split(" ");
  if (parts.length !== 5) return `Custom: ${expr}`;
  const [min, hour, dom, month, dow] = parts;
  if (dom === "*" && month === "*" && dow === "1-5" && min === "0")
    return `Every weekday at ${hour}:00`;
  if (dom === "*" && month === "*" && dow === "*")
    return `Daily at ${hour}:${min.padStart(2, "0")}`;
  return `Custom: ${expr}`;
}
```

**Acceptance criteria:**
- [ ] Panel displays `cron_expression` and its human-readable description
- [ ] Lag gauge renders as a bar (red if lag_seconds > 3600)
- [ ] DLQ section renders only when `dlq_depth > 0`
- [ ] Pause/Resume buttons hidden when `isAdmin=false`
- [ ] Jest tests pass

---

#### E5-S2 — `HookTracePanel.tsx` tab with 50-row event table + filters

**Branch:** `feat/PP-MOULD-1-it2-e5`
**BLOCKED UNTIL:** E5-S1 merged
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/PP/FrontEnd/src/components/SchedulerDiagnosticsPanel.tsx` — just created, for structural pattern
2. `src/PP/FrontEnd/src/hooks/` — existing hook patterns

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/PP/FrontEnd/src/components/HookTracePanel.tsx` |
| CREATE | `src/PP/FrontEnd/src/hooks/useHookTrace.ts` |
| MODIFY | Hired agent detail page — add "Hook Trace" tab |
| CREATE | `src/PP/FrontEnd/src/__tests__/HookTracePanel.test.tsx` |

**What to build:**

```typescript
// HookTracePanel — 50-row event table with filter controls
// Columns: emitted_at | stage | result (proceed/halt) | reason | payload_summary

// Filter UI: two dropdowns above the table
// [Stage dropdown]: All / pre_pump / post_pump / pre_processor / post_processor /
//                  pre_tool_use / post_tool_use / pre_publish / post_publish
// [Result dropdown]: All / proceed / halt

// Table rows have result color coding:
// result="halt" → row background #ef444415 (red tint)
// result="proceed" → no special background

// Stage chip color coding:
// pre_pump / post_pump → cyan (#00f2fe)
// pre_processor / post_processor → purple (#667eea)
// pre_publish / post_publish → pink (#f093fb)
// tool_use → yellow (#f59e0b)

interface HookTracePanelProps {
  hiredAgentId: string;
}
```

**Acceptance criteria:**
- [ ] Table renders up to 50 rows from `useHookTrace` hook
- [ ] Stage dropdown filters table by stage value
- [ ] Result dropdown filters by "proceed"/"halt"
- [ ] Halt rows have red tint background
- [ ] Stage chips have correct color per hook category
- [ ] `payload_summary` column shows truncated text (max 100 chars — guaranteed by backend)
- [ ] Jest tests pass

---

## Iteration 3

### Epic E6: PP admins can set up new agent types and tune policies live

**Outcome:** PP admins can create/edit an agent type's full configuration (identity, ConstructBindings, ConstraintPolicy, hook checklist) from a single form; and live-tune any hired agent's approval mode from a lightweight drawer without opening the full setup form.

**Context (2 sentences):** `AgentTypeSetupScreen` is a new full-page form replacing a basic create form — it adds `ConstructBindings` selector (processor/pump/connector classes) and the `ConstraintPolicy` form group. `ConstraintPolicyLiveTuneDrawer` is a focused 2-field drawer for high-urgency changes (approval_mode toggle; max_tasks_per_day) with an audit acknowledgement checkbox.

---

#### E6-S1 — `AgentTypeSetupScreen.tsx` (new full-page form)

**Branch:** `feat/PP-MOULD-1-it3-e6`
**BLOCKED UNTIL:** Iteration 2 merged to `main`
**Estimate:** 90 min

**Files to read first (max 3):**
1. `src/PP/FrontEnd/src/pages/` — check for existing agent type setup/create page to replace or extend
2. `src/PP/FrontEnd/src/components/` — check for existing form components, Select, etc.
3. `src/PP/BackEnd/api/agent_setups.py` — to confirm field names and endpoint paths

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/PP/FrontEnd/src/pages/AgentTypeSetupScreen.tsx` |
| CREATE | `src/PP/FrontEnd/src/hooks/useAgentTypeSetup.ts` |
| CREATE | `src/PP/FrontEnd/src/__tests__/AgentTypeSetupScreen.test.tsx` |

**Form sections:**

```typescript
// AgentTypeSetupScreen — 4 sections

// Section 1: Identity
// - agent_type (text, required)
// - display_name (text, required)
// - description (textarea)
// - industry (select: marketing | education | sales)

// Section 2: ConstructBindings
// - processor_class (select — populated from Plant GET /v1/agent-mold/processors)
// - pump_class (select — populated from Plant GET /v1/agent-mold/pumps)
// - connector_class (select, optional — "None" option available)
// - publisher_class (select, optional — "None" option available)

// Section 3: ConstraintPolicy
// - approval_mode (toggle: Manual / Auto)
// - max_tasks_per_day (number input — 0 = no limit, helper text: "0 = unlimited")
// - max_position_size_inr (number input — 0 = no limit; visible when connector_class includes "trading")
// - trial_task_limit (number input — default 10)

// Section 4: Hook Checklist
// - List of hooks with enable/disable checkboxes
// - AuditHook checkbox is locked (always enabled, cannot disable)
// - helper text per hook explaining what it does
```

Submit calls `POST /pp/agent-setups` (create) or `PATCH /pp/agent-setups/{id}` (edit).

**Acceptance criteria:**
- [ ] All 4 form sections render
- [ ] `approval_mode` toggle shows "Manual / Auto" labels
- [ ] `max_position_size_inr` field is hidden when `connector_class` does not include "trading"
- [ ] AuditHook checkbox is locked as checked (cannot be unchecked — set `disabled={true}`)
- [ ] Valid form submission calls the correct endpoint
- [ ] Required field validation shows inline errors before submission
- [ ] Jest tests pass

---

#### E6-S2 — `ConstraintPolicyLiveTuneDrawer.tsx` + `ApprovalsQueueScreen.tsx` overhaul

**Branch:** `feat/PP-MOULD-1-it3-e6`
**BLOCKED UNTIL:** E6-S1 merged
**Estimate:** 90 min

**Files to read first (max 3):**
1. `src/PP/FrontEnd/src/components/ConstructHealthPanel.tsx` — drawer pattern to follow
2. `src/PP/FrontEnd/src/pages/ApprovalsQueueScreen.tsx` (or equivalent) — current approvals UI
3. `src/PP/BackEnd/api/agent_setups.py` — `PATCH /constraint-policy` endpoint

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/PP/FrontEnd/src/components/ConstraintPolicyLiveTuneDrawer.tsx` |
| MODIFY | `src/PP/FrontEnd/src/pages/ApprovalsQueueScreen.tsx` — add type badges + expiry countdown |
| CREATE | `src/PP/FrontEnd/src/__tests__/ConstraintPolicyLiveTuneDrawer.test.tsx` |

**`ConstraintPolicyLiveTuneDrawer`:**
```typescript
// Lightweight 2-field drawer for urgent policy changes
// Field 1: approval_mode toggle (Manual / Auto)
// Field 2: max_tasks_per_day number input
// Mandatory: Audit acknowledgement checkbox
//   "I understand this change takes effect on the next goal run and is audit-logged."
//   Submit button disabled until checkbox is checked.

interface ConstraintPolicyLiveTuneDrawerProps {
  agentSetupId: string;
  currentPolicy: ConstraintPolicy;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (updatedPolicy: ConstraintPolicy) => void;
}

// Submit → PATCH /pp/agent-setups/{agentSetupId}/constraint-policy
```

**`ApprovalsQueueScreen` overhaul:**
```typescript
// Three changes to existing ApprovalsQueueScreen:

// 1. Type badges — show delivery type chip on each row:
//    "Trade Plan" → yellow badge (#f59e0b)
//    "Content Draft" → cyan badge (#00f2fe)
//    "Report" → purple badge (#667eea)

// 2. Context preview — 2-line text preview under the approval title
//    For trade plans: "BUY RELIANCE · 10 shares · ₹2,450"
//    For content drafts: first 80 chars of draft text

// 3. Expiry countdown — show "Expires in Xh Ym" for pending items
//    Red text if < 2h remaining
//    Yellow text if 2–12h remaining
//    Gray text if > 12h remaining
```

**Acceptance criteria:**
- [ ] `ConstraintPolicyLiveTuneDrawer` renders approval_mode toggle and max_tasks_per_day input
- [ ] Submit button is disabled until audit acknowledgement checkbox is checked
- [ ] Submitting calls `PATCH /pp/agent-setups/{id}/constraint-policy` and calls `onSuccess`
- [ ] `ApprovalsQueueScreen` shows type badges on all rows
- [ ] Context preview renders under the approval title
- [ ] Expiry countdown shows correct color: red (<2h), yellow (2–12h), gray (>12h)
- [ ] Jest tests pass for both components
