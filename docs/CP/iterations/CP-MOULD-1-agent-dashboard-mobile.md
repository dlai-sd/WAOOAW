# CP-MOULD-1 — Agent-Centric Dashboard (Mobile + BackEnd Proxy)

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-MOULD-1` |
| Feature area | CP BackEnd (proxy routes) + Mobile (React Native / Expo) |
| Created | 2026-03-07 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/plant/AGENT-CONSTRUCT-DESIGN.md` §13 (esp. §13.4, §13.7) |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 3 |
| Total epics | 6 |
| Total stories | 10 |

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

- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
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
| 1 | Lane B — New CP BackEnd proxy routes: scheduler-summary, trial-budget, pause/resume, approval-queue | 2 | 4 | 3.5h | +4h after launch |
| 2 | Lane A — Mobile screens: AgentCard enhancements, MyAgentsScreen, HireWizardScreen (4-step) | 2 | 3 | 4h | +5h after launch |
| 3 | Lane A — New mobile screens: AgentOperationsScreen (hub), TrialDashboardScreen approval queue, NotificationsScreen deep-links | 2 | 3 | 4.5h | +5h after launch |

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

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer comfortable with thin proxy patterns.
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11/FastAPI proxy engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-MOULD-1-agent-dashboard-mobile.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2. Do not touch Iteration 2 or 3.
TIME BUDGET: 3.5h. If you reach 4h without finishing, follow STUCK PROTOCOL.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(PLANT-MOULD-1) iteration 2 merged.
  If not, post: "Blocked: PLANT-MOULD-1 not fully merged to main." and HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" section.
2. Read "Iteration 1" section.
3. Execute Epics: E1 → E2
4. Docker-test all new routes.
5. Open iteration PR. Post URL. HALT.
```

Come back at: **+4h after launch**

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge:**
```bash
git fetch origin && git log --oneline origin/main | head -5
# Must show: feat(CP-MOULD-1): iteration 1
```

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer experienced with mobile UI/UX.
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React Native/TypeScript engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-MOULD-1-agent-dashboard-mobile.md
YOUR SCOPE: Iteration 2 only — Epics E3, E4. Do not touch Iteration 1 or 3.
TIME BUDGET: 4h.

PREREQUISITE CHECK:
  git log --oneline origin/main | head -5
  Must show: feat(CP-MOULD-1): iteration 1 merged.
  If not: post "Blocked: Iteration 1 not merged." HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
2. Execute Epics: E3 → E4
3. Run Jest tests: cd src/mobile && npm test -- --forceExit
4. Open iteration PR. Post URL. HALT.
```

Come back at: **+5h after launch**

---

### Iteration 3

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Verify merge:**
```bash
git fetch origin && git log --oneline origin/main | head -5
# Must show: feat(CP-MOULD-1): iteration 2
```

**Iteration 3 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer experienced with complex mobile navigation and real-time data.
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React Native/TypeScript engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-MOULD-1-agent-dashboard-mobile.md
YOUR SCOPE: Iteration 3 only — Epics E5, E6. Do not touch previous or future content.
TIME BUDGET: 4.5h.

PREREQUISITE CHECK:
  git log --oneline origin/main | head -5
  Must show: feat(CP-MOULD-1): iteration 2 merged.
  If not: HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 3" sections.
2. Execute Epics: E5 → E6
3. Run Jest: cd src/mobile && npm test -- --forceExit
4. Open iteration PR. Post URL. HALT.
```

Come back at: **+5h after launch**

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas
Open every epic with the persona stated in the task block.

### Rule 0 — Open tracking draft PR first
```bash
git checkout main && git pull
git checkout -b feat/CP-MOULD-1-itN-eN
git commit --allow-empty -m "chore(CP-MOULD-1): start iteration N"
git push origin feat/CP-MOULD-1-itN-eN
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/CP-MOULD-1-itN-eN`.

### Rule 2 — Scope lock
Implement only the acceptance criteria. Do not add features or refactor unrelated code.

### Rule 3 — Tests before the next story

### Rule 4 — Commit + push after every story
```bash
git add -A
git commit -m "feat(CP-MOULD-1): [story title]"
git push origin feat/CP-MOULD-1-itN-eN
```

### Rule 5 — Integration test after every epic
**Backend (Iteration 1):**
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```
**Mobile (Iterations 2, 3):**
```bash
cd src/mobile && npm test -- --forceExit
```

### Rule 6 — STUCK PROTOCOL
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/CP-MOULD-1-itN-eN
```
**HALT. Post the error and blocked story ID. Do not start the next story.**

### Rule 7 — Iteration PR
```bash
git checkout -b feat/CP-MOULD-1-itN-rollup
git merge --no-ff feat/CP-MOULD-1-itN-e1 feat/CP-MOULD-1-itN-e2
git push origin feat/CP-MOULD-1-itN-rollup
gh pr create --base main --title "feat(CP-MOULD-1): iteration N — [summary]" --body "..."
```

### CHECKPOINT RULE
After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(CP-MOULD-1): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic.

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | E1: Scheduler + budget proxy routes | `GET /cp/hired-agents/{id}/scheduler-summary` + `GET /cp/hired-agents/{id}/trial-budget` | 🔴 Not Started | — |
| E1-S2 | 1 | E1: Scheduler + budget proxy routes | `POST /cp/hired-agents/{id}/pause` + `POST /cp/hired-agents/{id}/resume` | 🔴 Not Started | — |
| E2-S1 | 1 | E2: Approval queue proxy | `GET /cp/hired-agents/{id}/approval-queue` | 🔴 Not Started | — |
| E2-S2 | 1 | E2: Approval queue proxy | `POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/approve` + `/reject` | 🔴 Not Started | — |
| E3-S1 | 2 | E3: AgentCard + MyAgentsScreen | Enhance `AgentCard.tsx` — health dot, cadence label, trial gauge, approval badge | 🔴 Not Started | — |
| E3-S2 | 2 | E3: AgentCard + MyAgentsScreen | Update `MyAgentsScreen.tsx` — sort-by-attention, empty-state | 🔴 Not Started | — |
| E4-S1 | 2 | E4: HireWizardScreen 4-step | Refactor `HireWizardScreen.tsx` — 4 named steps + `ConnectorSetupCard` | 🔴 Not Started | — |
| E5-S1 | 3 | E5: AgentOperationsScreen | Create new `AgentOperationsScreen.tsx` — 8-section hub | 🔴 Not Started | — |
| E5-S2 | 3 | E5: AgentOperationsScreen | Add approval queue section to `TrialDashboardScreen.tsx` | 🔴 Not Started | — |
| E6-S1 | 3 | E6: Notification deep-links | Update `NotificationsScreen.tsx` — agent-aware deep-links | 🔴 Not Started | — |

---

## Iteration 1

### Epic E1: Customers can see scheduler health and trial budget from the CP mobile app

**Outcome:** CP BackEnd exposes four new thin proxy routes that the mobile app calls to render scheduler status and trial budget. All data comes from Plant BackEnd — CP BackEnd is a pass-through with auth forwarding.

**Context (2 sentences):** `src/CP/BackEnd/api/hired_agents_proxy.py` already has the helper functions `_plant_get_json`, `_plant_post_json` — use them. These are Pattern B proxy routes (new `api/cp_scheduler.py` file with `waooaw_router`) forwarded to the Plant diagnostic endpoints added in PLANT-MOULD-1.

---

#### E1-S1 — `GET /cp/hired-agents/{id}/scheduler-summary` + `GET /cp/hired-agents/{id}/trial-budget`

**Branch:** `feat/CP-MOULD-1-it1-e1`
**BLOCKED UNTIL:** `PLANT-MOULD-1` Iteration 2 merged to main (Plant diagnostic endpoints must exist)
**Estimate:** 45 min

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/hired_agents_proxy.py` — `waooaw_router` usage, `_plant_get_json` helper, auth forwarding pattern
2. `src/CP/BackEnd/services/plant_gateway_client.py` — `PlantGatewayClient.request_json` method signature
3. `src/CP/BackEnd/main.py` — to find where to register the new router

**CP BackEnd architecture pattern (Pattern B — this story):**
> Pattern B = missing `/cp/*` route → new `api/cp_<resource>.py` file with `waooaw_router` + `PlantGatewayClient`.
> CP BackEnd is a thin proxy. Zero business logic. Zero data storage.
> All data lives in Plant BackEnd. CP: authenticate → forward → return.

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/CP/BackEnd/api/cp_scheduler.py` |
| MODIFY | `src/CP/BackEnd/main.py` — register `cp_scheduler_router` |
| CREATE | `src/CP/BackEnd/tests/test_cp_scheduler.py` |

**What to build — NFR patterns to copy exactly:**
```python
# src/CP/BackEnd/api/cp_scheduler.py
from __future__ import annotations
from fastapi import Header, HTTPException
from core.routing import waooaw_router                 # ← MANDATORY: never bare APIRouter
from services.plant_gateway_client import PlantGatewayClient
import logging

logger = logging.getLogger(__name__)

router = waooaw_router(
    prefix="/cp/hired-agents",
    tags=["cp-scheduler"],
)


@router.get("/{hired_agent_id}/scheduler-summary")
async def get_scheduler_summary(
    hired_agent_id: str,
    authorization: str | None = Header(None),
):
    """Proxy to Plant GET /v1/hired-agents/{id}/scheduler-diagnostics.

    Returns scheduler health snapshot for the mobile SchedulerSummaryCard component.
    CP BackEnd adds no data — it forwards auth and returns Plant's response verbatim.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    client = PlantGatewayClient()
    # Circuit breaker is inside PlantGatewayClient — no extra handling here
    return await client.request_json(
        "GET",
        f"/v1/hired-agents/{hired_agent_id}/scheduler-diagnostics",
        headers={"Authorization": authorization},
    )


@router.get("/{hired_agent_id}/trial-budget")
async def get_trial_budget(
    hired_agent_id: str,
    authorization: str | None = Header(None),
):
    """Proxy to Plant GET /v1/hired-agents/{id}/trial-budget.

    Returns trial_task_limit, tasks_used, trial_ends_at for the mobile TrialGauge.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    client = PlantGatewayClient()
    return await client.request_json(
        "GET",
        f"/v1/hired-agents/{hired_agent_id}/trial-budget",
        headers={"Authorization": authorization},
    )
```

Register in `main.py`:
```python
from api.cp_scheduler import router as cp_scheduler_router
app.include_router(cp_scheduler_router)
```

**Acceptance criteria:**
- [ ] `GET /cp/hired-agents/{id}/scheduler-summary` returns HTTP 200 proxying to Plant
- [ ] `GET /cp/hired-agents/{id}/trial-budget` returns HTTP 200 proxying to Plant
- [ ] Both routes return HTTP 401 when `Authorization` header is missing
- [ ] `waooaw_router` used — no bare `APIRouter`
- [ ] `pytest src/CP/BackEnd/tests/test_cp_scheduler.py` exits 0

**Tests to write:**
```python
# src/CP/BackEnd/tests/test_cp_scheduler.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

def test_scheduler_summary_requires_auth(client):
    resp = client.get("/cp/hired-agents/ha-1/scheduler-summary")
    assert resp.status_code == 401

def test_scheduler_summary_proxies_to_plant(client, mock_plant_client):
    mock_plant_client.request_json = AsyncMock(return_value={"scheduler": "ok"})
    resp = client.get("/cp/hired-agents/ha-1/scheduler-summary",
                      headers={"Authorization": "Bearer test"})
    assert resp.status_code == 200

def test_trial_budget_requires_auth(client):
    resp = client.get("/cp/hired-agents/ha-1/trial-budget")
    assert resp.status_code == 401

def test_trial_budget_proxies_to_plant(client, mock_plant_client):
    mock_plant_client.request_json = AsyncMock(return_value={"tasks_used": 3})
    resp = client.get("/cp/hired-agents/ha-1/trial-budget",
                      headers={"Authorization": "Bearer test"})
    assert resp.status_code == 200
```

---

#### E1-S2 — `POST /cp/hired-agents/{id}/pause` + `POST /cp/hired-agents/{id}/resume`

**Branch:** `feat/CP-MOULD-1-it1-e1`
**BLOCKED UNTIL:** E1-S1 merged
**Estimate:** 30 min

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/cp_scheduler.py` — just created in E1-S1
2. `src/CP/BackEnd/services/plant_gateway_client.py` — `request_json` signature

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/CP/BackEnd/api/cp_scheduler.py` — add `/pause` and `/resume` routes |
| MODIFY | `src/CP/BackEnd/tests/test_cp_scheduler.py` — add tests |

**What to build:**
```python
# Append to src/CP/BackEnd/api/cp_scheduler.py
@router.post("/{hired_agent_id}/pause")
async def pause_agent(
    hired_agent_id: str,
    authorization: str | None = Header(None),
):
    """Pause scheduled execution for a hired agent.

    Proxies to Plant POST /v1/hired-agents/{id}/pause.
    Customer can pause their agent from the mobile app — no PP involvement needed.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    client = PlantGatewayClient()
    return await client.request_json(
        "POST",
        f"/v1/hired-agents/{hired_agent_id}/pause",
        headers={"Authorization": authorization},
    )


@router.post("/{hired_agent_id}/resume")
async def resume_agent(
    hired_agent_id: str,
    authorization: str | None = Header(None),
):
    """Resume scheduled execution for a previously paused agent."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    client = PlantGatewayClient()
    return await client.request_json(
        "POST",
        f"/v1/hired-agents/{hired_agent_id}/resume",
        headers={"Authorization": authorization},
    )
```

**Acceptance criteria:**
- [ ] `POST /cp/hired-agents/{id}/pause` returns 200 when Plant confirms
- [ ] `POST /cp/hired-agents/{id}/resume` returns 200 when Plant confirms
- [ ] Both return 401 without `Authorization` header
- [ ] Tests pass

---

### Epic E2: Customers approve or reject agent deliverables from the mobile app

**Outcome:** CP BackEnd exposes an approval-queue endpoint so the mobile `TrialDashboardScreen` can show pending deliverables and let customers approve/reject without opening a web browser.

**Context (2 sentences):** Plant BackEnd stores deliverables with `pending_review` status when `approval_mode=MANUAL` — CP BackEnd needs a proxy route to surface these and accept decisions. `POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/approve` calls Plant's existing deliverables state PATCH endpoint.

---

#### E2-S1 — `GET /cp/hired-agents/{id}/approval-queue`

**Branch:** `feat/CP-MOULD-1-it1-e2`
**BLOCKED UNTIL:** E1-S2 merged
**Estimate:** 30 min

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/hired_agents_proxy.py` — existing deliverables GET route pattern
2. `src/CP/BackEnd/services/plant_gateway_client.py`

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/CP/BackEnd/api/cp_approvals.py` |
| MODIFY | `src/CP/BackEnd/main.py` — register router |
| CREATE | `src/CP/BackEnd/tests/test_cp_approvals.py` |

**What to build — NFR patterns to copy exactly:**
```python
# src/CP/BackEnd/api/cp_approvals.py
from __future__ import annotations
from fastapi import Header, HTTPException
from core.routing import waooaw_router                 # ← MANDATORY
from services.plant_gateway_client import PlantGatewayClient
import logging

logger = logging.getLogger(__name__)

router = waooaw_router(prefix="/cp/hired-agents", tags=["cp-approvals"])


@router.get("/{hired_agent_id}/approval-queue")
async def get_approval_queue(
    hired_agent_id: str,
    authorization: str | None = Header(None),
):
    """Returns deliverables with status=pending_review for this hired agent.

    Proxies to Plant GET /v1/hired-agents/{id}/deliverables?status=pending_review
    Mobile TrialDashboardScreen calls this to render the approval queue section.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    client = PlantGatewayClient()
    return await client.request_json(
        "GET",
        f"/v1/hired-agents/{hired_agent_id}/deliverables",
        headers={"Authorization": authorization},
        params={"status": "pending_review"},
    )
```

**Acceptance criteria:**
- [ ] `GET /cp/hired-agents/{id}/approval-queue` returns 200 with pending deliverables list
- [ ] Proxies to Plant with `?status=pending_review` query param
- [ ] Returns 401 without `Authorization` header
- [ ] Tests pass

---

#### E2-S2 — `POST /cp/hired-agents/{id}/approval-queue/{deliverable_id}/approve` + `/reject`

**Branch:** `feat/CP-MOULD-1-it1-e2`
**BLOCKED UNTIL:** E2-S1 merged
**Estimate:** 30 min

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/cp_approvals.py` — just created
2. `src/CP/BackEnd/services/plant_gateway_client.py`

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/CP/BackEnd/api/cp_approvals.py` — add approve + reject routes |
| MODIFY | `src/CP/BackEnd/tests/test_cp_approvals.py` |

**What to build:**
```python
# Append to src/CP/BackEnd/api/cp_approvals.py

@router.post("/{hired_agent_id}/approval-queue/{deliverable_id}/approve")
async def approve_deliverable(
    hired_agent_id: str,
    deliverable_id: str,
    authorization: str | None = Header(None),
):
    """Customer approves a pending deliverable — triggers publish to the channel.

    Proxies to Plant PATCH /v1/deliverables/{deliverable_id}/status
    with body {"status": "approved"}.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    client = PlantGatewayClient()
    return await client.request_json(
        "PATCH",
        f"/v1/deliverables/{deliverable_id}/status",
        headers={"Authorization": authorization},
        json={"status": "approved", "hired_agent_id": hired_agent_id},
    )


@router.post("/{hired_agent_id}/approval-queue/{deliverable_id}/reject")
async def reject_deliverable(
    hired_agent_id: str,
    deliverable_id: str,
    authorization: str | None = Header(None),
):
    """Customer rejects a deliverable — marks it as rejected, no publish."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    client = PlantGatewayClient()
    return await client.request_json(
        "PATCH",
        f"/v1/deliverables/{deliverable_id}/status",
        headers={"Authorization": authorization},
        json={"status": "rejected", "hired_agent_id": hired_agent_id},
    )
```

**Acceptance criteria:**
- [ ] `POST .../approve` returns 200, proxies with `{"status": "approved"}` to Plant
- [ ] `POST .../reject` returns 200, proxies with `{"status": "rejected"}` to Plant
- [ ] Both return 401 without auth header
- [ ] Tests pass

---

## Iteration 2

### Epic E3: AgentCard and MyAgentsScreen surface construct health at a glance

**Outcome:** A customer opening the app immediately sees which agents need their attention — health dot, cadence label, trial gauge, and approval badge are visible on the AgentCard in the agents list.

**Context (2 sentences):** `AgentCard.tsx` currently shows name, status, and a ratings chip — it needs four new data-driven UI elements. `MyAgentsScreen.tsx` lists agents in insertion order — add a sort-by-attention option that puts agents with pending approvals or degraded health at the top.

---

#### E3-S1 — Enhance `AgentCard.tsx` — health dot, cadence, trial gauge, approval badge

**Branch:** `feat/CP-MOULD-1-it2-e3`
**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimate:** 75 min

**Files to read first (max 3):**
1. `src/mobile/src/components/AgentCard.tsx` — full file
2. `src/mobile/src/screens/agents/MyAgentsScreen.tsx` — how AgentCard is called / what props it receives
3. `src/mobile/src/hooks/useHiredAgents.ts` (or `useAgentsInTrial.ts`) — current data shape

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/mobile/src/components/AgentCard.tsx` |
| MODIFY | `src/mobile/src/hooks/useHiredAgents.ts` — add `schedulerSummary`, `approvalQueueCount`, `trialBudget` to data shape (fetch from new CP endpoints: `GET /cp/hired-agents/{id}/scheduler-summary` and `GET /cp/hired-agents/{id}/trial-budget`) |
| CREATE | `src/mobile/src/__tests__/AgentCard.test.tsx` |

**What to build:**

Add these props to `AgentCard` (without breaking existing callers — all new props optional):

```typescript
// New optional props added to AgentCard
interface AgentCardProps {
  // ... existing props
  healthStatus?: "healthy" | "degraded" | "offline"; // new
  cadenceLabel?: string;       // e.g. "Posts 3x daily" or "Checks market hourly"
  trialTasksUsed?: number;     // new
  trialTaskLimit?: number;     // new
  approvalQueueCount?: number; // new — badge count on card
}
```

Add to JSX (existing card content unchanged — append new section):
```typescript
// Health dot row (add below the existing status badge)
{healthStatus && (
  <View style={styles.healthRow}>
    <View style={[styles.healthDot,
      healthStatus === "healthy" ? styles.dotGreen
      : healthStatus === "degraded" ? styles.dotYellow
      : styles.dotRed
    ]} />
    <Text style={styles.healthLabel}>{healthStatus}</Text>
    {cadenceLabel && <Text style={styles.cadenceLabel}>{cadenceLabel}</Text>}
  </View>
)}

// Trial gauge (only when trialTaskLimit is set)
{trialTaskLimit != null && trialTaskLimit > 0 && (
  <View style={styles.trialGaugeRow}>
    <View style={styles.trialGaugeBar}>
      <View style={[styles.trialGaugeFill, {
        width: `${Math.min(100, ((trialTasksUsed ?? 0) / trialTaskLimit) * 100)}%`
      }]} />
    </View>
    <Text style={styles.trialGaugeLabel}>
      {trialTasksUsed ?? 0}/{trialTaskLimit} trial tasks used
    </Text>
  </View>
)}

// Approval badge (right side chip)
{(approvalQueueCount ?? 0) > 0 && (
  <View style={styles.approvalBadge}>
    <Text style={styles.approvalBadgeText}>
      {approvalQueueCount} pending
    </Text>
  </View>
)}
```

Add corresponding `StyleSheet` entries (dark theme — consistent with WAOOAW design system):
```typescript
healthRow: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4 },
healthDot: { width: 8, height: 8, borderRadius: 4 },
dotGreen: { backgroundColor: "#10b981" },
dotYellow: { backgroundColor: "#f59e0b" },
dotRed: { backgroundColor: "#ef4444" },
trialGaugeBar: { height: 4, backgroundColor: "#27272a", borderRadius: 2, flex: 1 },
trialGaugeFill: { height: 4, backgroundColor: "#00f2fe", borderRadius: 2 },
approvalBadge: { backgroundColor: "#f59e0b22", borderRadius: 12, paddingHorizontal: 8,
                  paddingVertical: 2, alignSelf: "flex-start", marginTop: 4 },
```

**Acceptance criteria:**
- [ ] `AgentCard` renders without changes when new props are absent (backward-compat)
- [ ] Health dot renders green/yellow/red based on `healthStatus`
- [ ] Trial gauge fills proportionally to `trialTasksUsed / trialTaskLimit`
- [ ] Approval badge hidden when `approvalQueueCount` is 0 or undefined
- [ ] Jest tests pass: `cd src/mobile && npm test -- --testPathPattern AgentCard`

---

#### E3-S2 — Upgrade `MyAgentsScreen.tsx` — sort-by-attention, empty-state copy

**Branch:** `feat/CP-MOULD-1-it2-e3`
**BLOCKED UNTIL:** E3-S1 merged
**Estimate:** 45 min

**Files to read first (max 3):**
1. `src/mobile/src/screens/agents/MyAgentsScreen.tsx` — full file
2. `src/mobile/src/components/AgentCard.tsx` — updated in E3-S1

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/mobile/src/screens/agents/MyAgentsScreen.tsx` |
| CREATE | `src/mobile/src/__tests__/MyAgentsScreen.test.tsx` |

**What to build:**

Add sort options at the top of the agents list (add a horizontal chip bar):
```typescript
// Sort options for the agents list
type SortOption = "attention" | "alphabetical" | "recent";

const SORT_OPTIONS: { key: SortOption; label: string }[] = [
  { key: "attention", label: "Needs attention" },
  { key: "alphabetical", label: "A–Z" },
  { key: "recent", label: "Recently active" },
];

// Sort logic — "attention" puts agents with pendingApprovals > 0 or
// healthStatus === "degraded" first
function sortAgents(agents: HiredAgent[], sort: SortOption): HiredAgent[] {
  if (sort === "attention") {
    return [...agents].sort((a, b) => {
      const aScore = (a.approvalQueueCount ?? 0) + (a.healthStatus === "degraded" ? 10 : 0);
      const bScore = (b.approvalQueueCount ?? 0) + (b.healthStatus === "degraded" ? 10 : 0);
      return bScore - aScore;
    });
  }
  if (sort === "alphabetical") return [...agents].sort((a, b) => a.name.localeCompare(b.name));
  return agents; // "recent" = existing order
}
```

Update empty-state copy for the `hired` tab:
```typescript
// When no hired agents:
<EmptyState
  icon="🤖"
  title="No agents hired yet"
  subtitle="Your agents will appear here once you hire one. Try a 7-day free trial — keep everything they build."
  action={{ label: "Browse agents", onPress: () => navigate("Marketplace") }}
/>
```

**Acceptance criteria:**
- [ ] Chip bar shows three sort options
- [ ] Selecting "Needs attention" re-orders the list with agents that have pending approvals or degraded health first
- [ ] Empty-state shows correct copy and "Browse agents" action
- [ ] Jest tests pass

---

### Epic E4: HireWizardScreen guides customers through setup in four named steps

**Outcome:** The hire wizard has four clearly named steps with a progress indicator: (1) Choose Agent, (2) Connect Platform, (3) Set Goals, (4) Start Trial.

**Context (2 sentences):** `HireWizardScreen.tsx` currently uses a step counter without labels — customers don't know how many steps remain. Adding a `ConnectorSetupCard` component for step 2 makes it clear what platform credentials are needed and allows the customer to complete setup without leaving the wizard.

---

#### E4-S1 — Refactor `HireWizardScreen.tsx` — 4 named steps + `ConnectorSetupCard`

**Branch:** `feat/CP-MOULD-1-it2-e4`
**BLOCKED UNTIL:** E3-S2 merged
**Estimate:** 90 min

**Files to read first (max 3):**
1. `src/mobile/src/screens/hire/HireWizardScreen.tsx` — full file, current wizard logic
2. `src/mobile/src/navigation/types.ts` — navigation param types
3. `src/mobile/src/components/` — check for any existing component patterns to follow

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/mobile/src/screens/hire/HireWizardScreen.tsx` |
| CREATE | `src/mobile/src/components/ConnectorSetupCard.tsx` — new component |
| CREATE | `src/mobile/src/__tests__/HireWizardScreen.test.tsx` |

**What to build — `ConnectorSetupCard.tsx`:**
```typescript
// src/mobile/src/components/ConnectorSetupCard.tsx
import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";

interface ConnectorSetupCardProps {
  platformName: string;       // e.g. "Twitter / X", "LinkedIn", "Zerodha Kite"
  requiredCredentials: string[]; // e.g. ["API Key", "API Secret"]
  isConnected: boolean;
  onConnect: () => void;
  onDisconnect: () => void;
}

export function ConnectorSetupCard({
  platformName, requiredCredentials, isConnected, onConnect, onDisconnect
}: ConnectorSetupCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.platformName}>{platformName}</Text>
        <View style={[styles.statusChip,
          isConnected ? styles.statusConnected : styles.statusDisconnected]}>
          <Text style={styles.statusText}>{isConnected ? "Connected" : "Not connected"}</Text>
        </View>
      </View>
      {!isConnected && (
        <>
          <Text style={styles.credentialsLabel}>You'll need:</Text>
          {requiredCredentials.map((cred) => (
            <Text key={cred} style={styles.credentialItem}>• {cred}</Text>
          ))}
          <TouchableOpacity style={styles.connectButton} onPress={onConnect}>
            <Text style={styles.connectButtonText}>Connect {platformName}</Text>
          </TouchableOpacity>
        </>
      )}
      {isConnected && (
        <TouchableOpacity style={styles.disconnectButton} onPress={onDisconnect}>
          <Text style={styles.disconnectButtonText}>Disconnect</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: "#18181b", borderRadius: 16, padding: 16,
          borderWidth: 1, borderColor: "#27272a" },
  statusConnected: { backgroundColor: "#10b98122" },
  statusDisconnected: { backgroundColor: "#ef444422" },
  connectButton: { backgroundColor: "#00f2fe22", borderRadius: 8, padding: 12,
                   alignItems: "center", marginTop: 12 },
  // ... add all remaining style entries
});
```

**Four-step wizard update in `HireWizardScreen.tsx`:**
```typescript
const STEPS = [
  { key: "choose", label: "Choose Agent", description: "Pick the agent type" },
  { key: "connect", label: "Connect Platform", description: "Link your account" },
  { key: "goals", label: "Set Goals", description: "Configure what the agent does" },
  { key: "trial", label: "Start Trial", description: "Begin your 7-day free trial" },
] as const;

// Progress indicator — add at top of wizard
<View style={styles.progressBar}>
  {STEPS.map((step, idx) => (
    <View key={step.key} style={styles.progressStep}>
      <View style={[styles.stepDot,
        currentStep > idx ? styles.stepDone
        : currentStep === idx ? styles.stepActive
        : styles.stepPending
      ]}>
        <Text style={styles.stepDotText}>{idx + 1}</Text>
      </View>
      <Text style={styles.stepLabel}>{step.label}</Text>
    </View>
  ))}
</View>
```

**Acceptance criteria:**
- [ ] Wizard shows 4 named steps with progress indicator
- [ ] Progress indicator shows correct done/active/pending state
- [ ] `ConnectorSetupCard` renders required credentials list when `isConnected=false`
- [ ] `ConnectorSetupCard` shows Disconnect when `isConnected=true`
- [ ] Jest tests pass: `cd src/mobile && npm test -- --testPathPattern HireWizard`

---

## Iteration 3

### Epic E5: Customers manage their agents from a single operations hub

**Outcome:** Customers can access a new `AgentOperationsScreen` from any hired agent card — a single screen with 8 sections covering activity, approvals, scheduler controls, credential health, goal configuration, spend, publications, and performance history.

**Context (2 sentences):** The screen is new — it does not exist in the codebase. It is the CP-side counterpart of the PP `ConstructHealthPanel` — same data, customer-appropriate framing (no developer jargon).

---

#### E5-S1 — Create new `AgentOperationsScreen.tsx` — 8-section hub

**Branch:** `feat/CP-MOULD-1-it3-e5`
**BLOCKED UNTIL:** Iteration 2 merged to `main`
**Estimate:** 90 min

**Files to read first (max 3):**
1. `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` — scroll + section structure to follow
2. `src/mobile/src/navigation/types.ts` — add new screen to param types
3. `src/mobile/src/hooks/useHiredAgents.ts` — data available

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` |
| MODIFY | `src/mobile/src/navigation/types.ts` — add `AgentOperations: { hiredAgentId: string }` param |
| MODIFY | `src/mobile/src/navigation/AgentsNavigator.tsx` (or equivalent) — register new screen |
| CREATE | `src/mobile/src/__tests__/AgentOperationsScreen.test.tsx` |

**What to build — 8 sections:**
```typescript
// Section map for AgentOperationsScreen
const SECTIONS = [
  { id: "activity",    title: "Today's Activity",      icon: "⚡" },
  { id: "approvals",  title: "Pending Approvals",      icon: "✋" },
  { id: "scheduler",  title: "Schedule Controls",       icon: "🕐" },
  { id: "health",     title: "Connection Health",       icon: "🔗" },
  { id: "goals",      title: "Goal Configuration",      icon: "🎯" },
  { id: "spend",      title: "Trial Usage & Spend",     icon: "💰" },
  { id: "recent",     title: "Recent Publications",     icon: "📤" },
  { id: "history",    title: "Performance History",     icon: "📈" },
] as const;
```

Each section is a collapsible card. Sections `approvals` and `scheduler` have action buttons:
- Approvals section: pulls from `useApprovalQueue(hiredAgentId)` hook → shows `TradePlanApprovalCard` or `ContentDraftApprovalCard` based on `deliverable.type`
- Scheduler section: shows `cron_expression` in human-readable text + Pause / Resume buttons that call `POST /cp/hired-agents/{id}/pause|resume`

Top of screen: agent name, avatar, `healthDot`, `cadenceLabel` — same props as `AgentCard` uses.

Hook to create:
```typescript
// src/mobile/src/hooks/useApprovalQueue.ts
export function useApprovalQueue(hiredAgentId: string) {
  // Call: GET /cp/hired-agents/{id}/approval-queue
  // Returns: { deliverables: DeliverableItem[], isLoading, error }
  // Mutation: approve(deliverableId), reject(deliverableId)
}
```

**Acceptance criteria:**
- [ ] `AgentOperationsScreen` exists at `src/mobile/src/screens/agents/AgentOperationsScreen.tsx`
- [ ] Screen is registered in navigation with `hiredAgentId` param
- [ ] All 8 section cards render (collapsed by default, expand on tap)
- [ ] Scheduler section shows Pause/Resume buttons
- [ ] Approvals section shows `approvalQueueCount` badge in the section header
- [ ] Jest snapshot test passes

---

#### E5-S2 — Add approval queue section to `TrialDashboardScreen.tsx`

**Branch:** `feat/CP-MOULD-1-it3-e5`
**BLOCKED UNTIL:** E5-S1 merged
**Estimate:** 45 min

**Files to read first (max 3):**
1. `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` — current structure
2. `src/mobile/src/hooks/useApprovalQueue.ts` — just created in E5-S1

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` |
| CREATE | `src/mobile/src/components/TradePlanApprovalCard.tsx` |
| CREATE | `src/mobile/src/components/ContentDraftApprovalCard.tsx` |

**What to build:**

Add a new section between "Trial Progress" and "Recent Deliverables":

```typescript
// In TrialDashboardScreen, add using useApprovalQueue hook:
const { deliverables: pendingApprovals } = useApprovalQueue(hiredAgentId);
// ...
{pendingApprovals.length > 0 && (
  <View style={styles.approvalSection}>
    <Text style={styles.sectionTitle}>Needs Your Approval ({pendingApprovals.length})</Text>
    {pendingApprovals.map((item) =>
      item.type === "trade_plan"
        ? <TradePlanApprovalCard key={item.id} deliverable={item} onApprove={approve} onReject={reject} />
        : <ContentDraftApprovalCard key={item.id} deliverable={item} onApprove={approve} onReject={reject} />
    )}
  </View>
)}
```

`TradePlanApprovalCard`: shows symbol, action (BUY/SELL), price, quantity, risk rating, Approve/Reject buttons.
`ContentDraftApprovalCard`: shows content preview (first 200 chars), target platform icon, Approve/Reject buttons.

**Acceptance criteria:**
- [ ] Approval queue section renders only when `pendingApprovals.length > 0`
- [ ] `TradePlanApprovalCard` shows trade details
- [ ] `ContentDraftApprovalCard` shows content preview
- [ ] Approve/reject calls update the list optimistically
- [ ] Jest tests pass

---

### Epic E6: Notifications deep-link to the relevant agent operation

**Outcome:** Tapping a notification about a pending approval, paused agent, or expiring credential navigates directly to the correct section of `AgentOperationsScreen` — no extra taps required.

**Context (2 sentences):** `NotificationsScreen.tsx` currently lists notification text with no deep-link navigation. Adding agent-aware routing reduces time-to-action for approval and credential alerts by 2+ taps.

---

#### E6-S1 — Update `NotificationsScreen.tsx` — agent-aware notification deep-links

**Branch:** `feat/CP-MOULD-1-it3-e6`
**BLOCKED UNTIL:** E5-S2 merged
**Estimate:** 60 min

**Files to read first (max 3):**
1. `src/mobile/src/screens/profile/NotificationsScreen.tsx` — full file
2. `src/mobile/src/navigation/types.ts` — navigation params (after E5-S1 additions)
3. `src/mobile/src/hooks/useNotifications.ts` — notification data shape

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/mobile/src/screens/profile/NotificationsScreen.tsx` |
| CREATE | `src/mobile/src/__tests__/NotificationsScreen.test.tsx` |

**What to build:**

Add a `notificationTarget` resolver function:
```typescript
type NotificationType =
  | "approval_required"       // → AgentOperationsScreen, section: "approvals"
  | "credential_expiring"     // → AgentOperationsScreen, section: "health"
  | "agent_paused"            // → AgentOperationsScreen, section: "scheduler"
  | "trial_ending"            // → AgentOperationsScreen, section: "spend"
  | "goal_run_failed"         // → AgentOperationsScreen, section: "activity"
  | "generic";                // → NotificationsScreen (no deep link)

function resolveNavigationTarget(
  notification: Notification
): { screen: string; params: object } | null {
  switch (notification.type) {
    case "approval_required":
      return { screen: "AgentOperations",
               params: { hiredAgentId: notification.hired_agent_id,
                         focusSection: "approvals" } };
    case "credential_expiring":
      return { screen: "AgentOperations",
               params: { hiredAgentId: notification.hired_agent_id,
                         focusSection: "health" } };
    case "agent_paused":
      return { screen: "AgentOperations",
               params: { hiredAgentId: notification.hired_agent_id,
                         focusSection: "scheduler" } };
    case "trial_ending":
      return { screen: "AgentOperations",
               params: { hiredAgentId: notification.hired_agent_id,
                         focusSection: "spend" } };
    case "goal_run_failed":
      return { screen: "AgentOperations",
               params: { hiredAgentId: notification.hired_agent_id,
                         focusSection: "activity" } };
    default:
      return null;
  }
}

// In the notification list item's onPress:
onPress={notification.hired_agent_id
  ? () => { const target = resolveNavigationTarget(notification);
             if (target) navigation.navigate(target.screen as any, target.params); }
  : undefined}
```

`AgentOperationsScreen` must accept an optional `focusSection` param and auto-expand that card on mount (scroll into view using a `ScrollView.scrollTo` ref).

**Acceptance criteria:**
- [ ] Tapping an `approval_required` notification navigates to `AgentOperationsScreen` with `focusSection: "approvals"`
- [ ] Tapping a `generic` notification does not navigate (no crash)
- [ ] Notifications without `hired_agent_id` are not tappable (or open a details modal — no navigation)
- [ ] `AgentOperationsScreen` scrolls to and expands `focusSection` on mount
- [ ] Jest tests pass for `resolveNavigationTarget` logic
