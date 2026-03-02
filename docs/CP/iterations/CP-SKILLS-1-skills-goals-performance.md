# CP-SKILLS-1 — Customer Portal: Skills Goals & Platform Performance

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-SKILLS-1` |
| Feature area | Customer Portal — Skills Goals, Platform Connections & Performance Stats |
| Created | 2026-03-01 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/plant/iterations/PLANT-SKILLS-1-generic-skills-architecture.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 3 |
| Total stories | 5 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story — agent never opens NFRReusable.md |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. Do NOT open NFRReusable.md. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.

---

## PM Review Checklist

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` / no DB in proxies
- [x] Every story that adds env vars lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (E1) before frontend (E2, E3)
- [x] No placeholders remain

---

## Background — What PLANT-SKILLS-1 Built (Already Merged)

The Plant BackEnd Iterations 1–2 are complete. The following is live in the demo DB and
Plant BackEnd API, confirmed by `alembic_version = 023_performance_stats` and `ls src/Plant/BackEnd/api/v1/`.

| Plant asset | Status | Key endpoint(s) |
|---|---|---|
| Migration 021 `agent_skills` | ✅ Live | n/a |
| Migration 022 `platform_connections` | ✅ Live | n/a |
| Migration 023 `performance_stats` | ✅ Live | n/a |
| Skill seeds: `social-content-publisher`, `execute-trade-order` with full `goal_schema` | ✅ Live | `GET /api/v1/skills/{skill_id}` |
| `api/v1/agent_skills.py` | ✅ Live | `GET /api/v1/agents/{agent_id}/skills` · `POST` · `DELETE` |
| `api/v1/platform_connections.py` | ✅ Live | `GET /api/v1/hired-agents/{id}/platform-connections` · `POST` · `DELETE` · `PATCH …/verify` |
| `api/v1/performance_stats.py` | ✅ Live | `GET /api/v1/hired-agents/{id}/performance-stats` · `POST` |

**What CP cannot do today:** The Customer Portal has no proxy routes for skills, platform connections, or performance stats. `MyAgents.tsx` shows only "Configure" and "Goal Setting" tabs — no skills discovery, no platform connection management, no performance view.

---

## User Outcome (Vision Intake Answer)

> After this plan is complete, a customer can open **My Agents**, select a hired agent, and:
> 1. See the list of skills assigned to their agent, with a goal-configuration form driven by each skill's `goal_schema`
> 2. Connect or disconnect external platform accounts (e.g. LinkedIn OAuth token for the content-publishing skill)
> 3. View a daily performance stats panel showing the agent's output metrics

Nothing in this plan requires Plant BackEnd changes. All work is CP BackEnd (proxy) + CP FrontEnd (UI).

**Out of scope:** Celery stats collector job · `max_plan_gate` enforcement layer · billing plan enforcement · PP/Plant changes · new Plant migrations.

---

## Proxy Architecture — Pattern B

CP BackEnd is a **thin proxy** — no business logic or data storage.
This plan creates one new file (`api/cp_skills.py`) and zero DB access.

```
Browser → CP BackEnd /cp/hired-agents/{id}/skills          → Plant Gateway /api/v1/agents/{agent_id}/skills
Browser → CP BackEnd /cp/skills/{skill_id}                 → Plant Gateway /api/v1/skills/{skill_id}
Browser → CP BackEnd /cp/hired-agents/{id}/platform-connections → Plant Gateway /api/v1/hired-agents/{id}/platform-connections
Browser → CP BackEnd /cp/hired-agents/{id}/performance-stats   → Plant Gateway /api/v1/hired-agents/{id}/performance-stats
```

The `/cp/hired-agents/{id}/skills` endpoint requires a two-hop: first resolve `agent_id` from the hired agent record, then fetch skills for that `agent_id`. This two-hop is done inside the CP BackEnd proxy (same pattern as `hired_agents_proxy.py`'s `get_by_subscription`).

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — CP BackEnd proxy: new `api/cp_skills.py` (6 routes + tests) | 1 | 2 | ~1h 30m | Start + 2h |
| 2 | Lane A — CP FrontEnd: 3 services + SkillsPanel + Performance tab | 2 | 3 | ~3h 30m | Start + 4h |

**Estimate basis:** New BE endpoint group = 45 min | FE service layer = 45 min | FE component = 90 min | FE wiring = 45 min | Docker test = 15 min | PR = 10 min. Add 20% buffer.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: clean main branch. If not, resolve before launching.
git status
# Must show: nothing to commit, working tree clean
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown at the top of the chat panel → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` in the message box → select **platform-engineer** from the dropdown
6. Copy the block below and paste into the message box → press **Enter**
7. Go away. Come back in 2h.

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / httpx engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11/FastAPI/httpx engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-SKILLS-1-skills-goals-performance.md
YOUR SCOPE: Iteration 1 only — Epic E1. Do not touch Iteration 2 content.
TIME BUDGET: 1h 30m. If you reach 2h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epic E1 in order: E1-S1 → E1-S2
6. When all stories are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(CP-SKILLS-1): iteration 1 — cp BackEnd skills proxy
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React/TypeScript/Fluent UI engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React/TypeScript/Fluent UI engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-SKILLS-1-skills-goals-performance.md
YOUR SCOPE: Iteration 2 only — Epics E2, E3. Do not touch Iteration 1 content.
TIME BUDGET: 3h 30m. If you reach 4h without finishing, follow STUCK PROTOCOL now.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(CP-SKILLS-1): iteration 1 — cp BackEnd skills proxy
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Execute in order: E2-S1 → E3-S1 → E3-S2
4. Respect BLOCKED UNTIL on E3-S1 and E3-S2.
5. When all epics are docker-tested, open the iteration PR. Post URL. HALT.
```

**Come back at:** Start + 4h

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `src/CP/BackEnd/` | Senior Python 3.11 / FastAPI / httpx engineer |
| `src/CP/FrontEnd/` | Senior React / TypeScript / Fluent UI engineer |

---

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
# 1. Create the first epic branch from main
git checkout main && git pull
git checkout -b feat/CP-SKILLS-1-it1-e1

# 2. Push an empty init commit so the branch exists on remote
git commit --allow-empty -m "chore(CP-SKILLS-1): start iteration 1"
git push origin feat/CP-SKILLS-1-it1-e1

# 3. Open draft PR — this is the progress tracker, not the final iteration PR
gh pr create \
  --base main \
  --head feat/CP-SKILLS-1-it1-e1 \
  --draft \
  --title "tracking: CP-SKILLS-1 Iteration 1 — in progress" \
  --body "## tracking: CP-SKILLS-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Create api/cp_skills.py (6 proxy routes)
- [ ] [E1-S2] Tests for cp_skills routes ≥80% coverage

_Live updates posted as comments below ↓_"
```

---

### Rule 1 — Branch discipline
One epic = one branch: `feat/CP-SKILLS-1-itN-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside your scope: add a TODO comment and move on.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing.
Run the test command listed in the story card — not a generic command.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat(CP-SKILLS-1): [story title]"
git push origin feat/CP-SKILLS-1-itN-eN

# Update this file's Tracking Table: change story status to Done
git add docs/CP/iterations/CP-SKILLS-1-skills-goals-performance.md
git commit -m "docs(CP-SKILLS-1): mark [story-id] done"
git push origin feat/CP-SKILLS-1-itN-eN

# Post progress comment to tracking draft PR
gh pr comment \
  $(gh pr list --head feat/CP-SKILLS-1-it1-e1 --json number -q '.[0].number') \
  --body "✅ **[story-id] done** — $(git rev-parse --short HEAD)
Files changed: [list]
Tests: [T1 ✅ T2 ✅ ...]
Next: [next-story-id]"
```

### Rule 5 — Docker integration test after every epic
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit cp-backend-test
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```
Exit 0 → add `**Epic complete ✅**` under the epic heading, commit, push.
Non-zero → fix on same branch, retry. Max 3 attempts. Then: STUCK PROTOCOL.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/CP-SKILLS-1-itN-eN
gh pr create \
  --base main \
  --head feat/CP-SKILLS-1-itN-eN \
  --title "WIP: [story-id] — blocked" \
  --draft \
  --body "Blocked on: [test name]
Error: [exact error message — paste in full]
Attempted fixes:
1. [what I tried]
2. [what I tried]"
```
Post the draft PR URL. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
```bash
git checkout main && git pull
git checkout -b feat/CP-SKILLS-1-itN
# Merge all epic branches for this iteration:
git merge --no-ff feat/CP-SKILLS-1-itN-e1
# For iteration 2: git merge --no-ff feat/CP-SKILLS-1-it2-e2 feat/CP-SKILLS-1-it2-e3
git push origin feat/CP-SKILLS-1-itN

gh pr create \
  --base main \
  --head feat/CP-SKILLS-1-itN \
  --title "feat(CP-SKILLS-1): iteration N — [one-line summary]" \
  --body "## CP-SKILLS-1 Iteration N

### Stories completed
[paste tracking table rows for this iteration]

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] No DB access in proxy (CP BackEnd is thin proxy)
- [ ] circuit_breaker pattern applied on all httpx calls (see E1-S1 card)
- [ ] X-Correlation-ID forwarded on all outbound httpx calls
- [ ] No env-specific values in code
- [ ] FE: loading + error + empty states on all data-fetching components
- [ ] Tests >= 80% coverage on new BE code"
```

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | `waooaw_router()` factory — never bare `APIRouter` | CI ruff ban — PR blocked |
| 2 | No DB sessions in CP proxy routes (proxy only) | Architecture violation |
| 3 | `X-Correlation-ID` forwarded on every outbound httpx call | Trace broken |
| 4 | Circuit breaker on every external httpx call | Cascading failure |
| 5 | Loading + error + empty states on every FE component | Silent failures |
| 6 | Tests >= 80% coverage on all new BE code | PR blocked by CI |
| 7 | `PLANT_GATEWAY_URL` from `os.getenv` only — never hardcoded | Image cannot be promoted |
| 8 | PR always `--base main` — never target an intermediate branch | Work never ships |
| 9 | CP BackEnd Pattern B: missing `/cp/*` route → new `api/cp_<resource>.py` | Architecture violation |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | E1: Customer sees skills for their hired agent | Create `api/cp_skills.py` (6 proxy routes) | � Done | feat/CP-SKILLS-1-it1-e1 |
| E1-S2 | 1 | E1: Customer sees skills for their hired agent | Tests for cp_skills routes ≥80% coverage | 🟢 Done | feat/CP-SKILLS-1-it1-e1 |
| E2-S1 | 2 | E2: FrontEnd service layer for skills & performance | Create `agentSkills.service.ts`, `platformConnections.service.ts`, `performanceStats.service.ts` | � Done | feat/CP-SKILLS-1-it2-e2 |
| E3-S1 | 2 | E3: Customer configures skills & sees performance | Create `SkillsPanel.tsx` with inline GoalConfigForm + PlatformConnectionsPanel | 🟢 Done | feat/CP-SKILLS-1-it2-e3 |
| E3-S2 | 2 | E3: Customer configures skills & sees performance | Add Skills + Performance tabs to `MyAgents.tsx` | 🟢 Done | feat/CP-SKILLS-1-it2-e3 |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — CP BackEnd Skills Proxy

**Scope:** Create a thin proxy file `api/cp_skills.py` in the CP BackEnd that exposes 6 new routes. The routes are authenticated (JWT), forward the customer's `Authorization` header to the Plant Gateway, and immediately return the Plant Gateway JSON response. No database access. No business logic.

**Branch:** `feat/CP-SKILLS-1-it1-e1`

**Docker integration test command:**
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit cp-backend-test
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```

---

### E1 — Customer sees skills for their hired agent

**Epic complete ✅** ← Agent: add this line here and commit when all E1 stories pass docker test.

---

#### E1-S1 — Create `api/cp_skills.py` (6 proxy routes)

**Branch:** `feat/CP-SKILLS-1-it1-e1`  
**BLOCKED UNTIL:** none — start here  
**Estimated time:** 45 minutes

**Context (2 sentences):**
CP BackEnd is a thin proxy to the Plant Gateway. The file `api/hired_agents_proxy.py` shows the exact pattern: `waooaw_router`, `PLANT_GATEWAY_URL` from `os.getenv`, raw `httpx.AsyncClient`, JWT auth forwarded via `Authorization` header. No database access in this file.

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/hired_agents_proxy.py` — lines 1–105 (pattern to copy exactly)
2. `src/CP/BackEnd/main.py` — find where routers are included, add cp_skills router there

**What to build:**

Create `src/CP/BackEnd/api/cp_skills.py` with the following 6 routes:

| Route | Method | Plant Gateway path | Notes |
|---|---|---|---|
| `/cp/hired-agents/{hired_instance_id}/skills` | GET | First: `GET /api/v1/hired-agents/by-subscription/{?}` to get `agent_id`, then `GET /api/v1/agents/{agent_id}/skills` | Two-hop: resolve agent_id then fetch skills |
| `/cp/skills/{skill_id}` | GET | `GET /api/v1/skills/{skill_id}` | Direct proxy |
| `/cp/hired-agents/{hired_instance_id}/platform-connections` | GET | `GET /api/v1/hired-agents/{hired_instance_id}/platform-connections` | Direct proxy |
| `/cp/hired-agents/{hired_instance_id}/platform-connections` | POST | `POST /api/v1/hired-agents/{hired_instance_id}/platform-connections` | Forward JSON body |
| `/cp/hired-agents/{hired_instance_id}/platform-connections/{connection_id}` | DELETE | `DELETE /api/v1/hired-agents/{hired_instance_id}/platform-connections/{connection_id}` | Direct proxy |
| `/cp/hired-agents/{hired_instance_id}/performance-stats` | GET | `GET /api/v1/hired-agents/{hired_instance_id}/performance-stats` | Direct proxy |

**Code pattern to copy exactly (from `hired_agents_proxy.py` — embed this, do not rewrite from scratch):**

```python
# src/CP/BackEnd/api/cp_skills.py
from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import Depends, HTTPException, Request
from core.routing import waooaw_router
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user
from models.user import User

router = waooaw_router(prefix="/cp", tags=["cp-skills"])


def _plant_base_url() -> str:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return base_url


async def _plant_get_json(
    *, url: str, authorization: str | None, correlation_id: str | None
) -> dict | list:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _plant_post_json(
    *, url: str, body: dict, authorization: str | None, correlation_id: str | None
) -> dict:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=body, headers=headers)
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


async def _plant_delete_json(
    *, url: str, authorization: str | None, correlation_id: str | None
) -> dict:
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(url, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        if resp.status_code == 204:
            return {}
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ─── Pydantic models ─────────────────────────────────────────────────────────

class PlatformConnectionBody(BaseModel):
    platform_name: str
    connection_type: str
    credentials: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.get("/hired-agents/{hired_instance_id}/skills")
async def list_hired_agent_skills(
    hired_instance_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    """
    Two-hop proxy:
    1. Resolve agent_id: GET /api/v1/hired-agents/by-subscription/{hired_instance_id}
       (hired_instance_id is used directly as the identifier)
    2. Fetch skills: GET /api/v1/agents/{agent_id}/skills
    """
    base = _plant_base_url()
    auth = request.headers.get("Authorization")
    cid = request.headers.get("X-Correlation-ID")

    # Hop 1: resolve hired agent to get agent_id
    hired_data = await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/by-id/{hired_instance_id}",
        authorization=auth,
        correlation_id=cid,
    )
    agent_id = (hired_data or {}).get("agent_id") or ""
    if not agent_id:
        raise HTTPException(status_code=404, detail="Hired agent or agent_id not found")

    # Hop 2: fetch skills
    return await _plant_get_json(
        url=f"{base}/api/v1/agents/{agent_id}/skills",
        authorization=auth,
        correlation_id=cid,
    )


@router.get("/skills/{skill_id}")
async def get_skill(
    skill_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    base = _plant_base_url()
    result = await _plant_get_json(
        url=f"{base}/api/v1/skills/{skill_id}",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result  # type: ignore[return-value]


@router.get("/hired-agents/{hired_instance_id}/platform-connections")
async def list_platform_connections(
    hired_instance_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    base = _plant_base_url()
    return await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/platform-connections",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.post("/hired-agents/{hired_instance_id}/platform-connections", status_code=201)
async def create_platform_connection(
    hired_instance_id: str,
    body: PlatformConnectionBody,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    base = _plant_base_url()
    result = await _plant_post_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/platform-connections",
        body=body.model_dump(),
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    return result


@router.delete(
    "/hired-agents/{hired_instance_id}/platform-connections/{connection_id}",
    status_code=204,
)
async def delete_platform_connection(
    hired_instance_id: str,
    connection_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> None:
    base = _plant_base_url()
    await _plant_delete_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/platform-connections/{connection_id}",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )


@router.get("/hired-agents/{hired_instance_id}/performance-stats")
async def get_performance_stats(
    hired_instance_id: str,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict | list:
    base = _plant_base_url()
    return await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/{hired_instance_id}/performance-stats",
        authorization=request.headers.get("Authorization"),
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
```

**Also update `src/CP/BackEnd/main.py`:**
After the other `include_router` calls, add:
```python
from api.cp_skills import router as cp_skills_router
app.include_router(cp_skills_router, prefix="/api")
```

> **⚠️ IMPORTANT NOTE on Hop 1:** The Plant Gateway endpoint `/api/v1/hired-agents/by-id/{id}` may not exist (Plant uses `/api/v1/hired-agents/by-subscription/{subscription_id}`). If Hop 1 returns 404, check `hired_agents_simple.py` in Plant BackEnd for the correct lookup route. If no by-id route exists, implement a fall-back: pass `hired_instance_id` directly as `agent_id` check (the seeds use predictable IDs), OR store the agent_id in `cp_skills.py` by calling `GET /api/v1/hired-agents/by-subscription/{hired_instance_id}` — the subscription_id and hired_instance_id are often the same value in demo data. Use whichever route returns a JSON with an `agent_id` field.

**Acceptance criteria:**
- [ ] File `src/CP/BackEnd/api/cp_skills.py` exists
- [ ] `router = waooaw_router(prefix="/cp", tags=["cp-skills"])` — no bare APIRouter
- [ ] `PLANT_GATEWAY_URL` read via `os.getenv` only — not hardcoded
- [ ] `Authorization` header forwarded on every outbound httpx call
- [ ] `X-Correlation-ID` header forwarded on every outbound httpx call
- [ ] Router included in `main.py` with `prefix="/api"`
- [ ] All 6 routes exist and return Plant Gateway response
- [ ] 404 from Plant → 404 to client; 4xx/5xx → forwarded; network error → 502

---

#### E1-S2 — Tests for `cp_skills.py` (≥80% coverage)

**Branch:** `feat/CP-SKILLS-1-it1-e1` (same branch as E1-S1)  
**BLOCKED UNTIL:** E1-S1 merged to same branch  
**Estimated time:** 30 minutes

**Context (2 sentences):**
Tests for CP BackEnd proxy routes use `pytest` with `unittest.mock.patch` on `httpx.AsyncClient` to avoid real Plant Gateway calls. See `src/CP/BackEnd/tests/test_cp_profile_routes.py` for the exact mock pattern: `TestClient` from FastAPI, patch `httpx.AsyncClient.request` with a mock returning `httpx.Response(200, json={...})`.

**Files to read first (max 3):**
1. `src/CP/BackEnd/tests/test_cp_otp_routes.py` — mocking pattern
2. `src/CP/BackEnd/api/cp_skills.py` — just created in E1-S1 (needed to write tests)

**What to build:**

Create `src/CP/BackEnd/tests/test_cp_skills_routes.py`:

```python
# src/CP/BackEnd/tests/test_cp_skills_routes.py
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

MOCK_HEADERS = {"Authorization": "Bearer test-token", "X-Correlation-ID": "test-cid"}


def _mock_httpx_get(status_code: int, json_body: dict | list):
    """Returns a context manager mock for httpx.AsyncClient that yields a GET response."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    mock_response.json.return_value = json_body
    mock_response.text = str(json_body)

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.delete = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


# ── GET /api/cp/hired-agents/{id}/skills ────────────────────────────────────

def test_list_hired_agent_skills_success():
    hop1_response = {"agent_id": "AGT-001", "hired_instance_id": "HIRED-001"}
    hop2_response = [{"skill_id": "SK-001", "name": "content-publisher"}]

    call_count = 0
    def side_effect_get(url, **kwargs):
        nonlocal call_count
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.text = "ok"
        if call_count == 0:
            mock_resp.status_code = 200
            mock_resp.json.return_value = hop1_response
        else:
            mock_resp.status_code = 200
            mock_resp.json.return_value = hop2_response
        call_count += 1
        return mock_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=side_effect_get)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client), \
         patch("api.cp_skills.get_current_user", return_value=MagicMock()), \
         patch.dict("os.environ", {"PLANT_GATEWAY_URL": "http://plant-gateway-test:8000"}):
        resp = client.get("/api/cp/hired-agents/HIRED-001/skills", headers=MOCK_HEADERS)

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_hired_agent_skills_not_found():
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"detail": "not found"}
    mock_resp.text = "not found"

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client), \
         patch("api.cp_skills.get_current_user", return_value=MagicMock()), \
         patch.dict("os.environ", {"PLANT_GATEWAY_URL": "http://plant-gateway-test:8000"}):
        resp = client.get("/api/cp/hired-agents/HIRED-MISSING/skills", headers=MOCK_HEADERS)

    assert resp.status_code == 404


# ── GET /api/cp/skills/{skill_id} ───────────────────────────────────────────

def test_get_skill_success():
    skill_payload = {"skill_id": "SK-001", "name": "content-publisher", "goal_schema": {"fields": []}}
    mock_client = _mock_httpx_get(200, skill_payload)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client), \
         patch("api.cp_skills.get_current_user", return_value=MagicMock()), \
         patch.dict("os.environ", {"PLANT_GATEWAY_URL": "http://plant-gateway-test:8000"}):
        resp = client.get("/api/cp/skills/SK-001", headers=MOCK_HEADERS)

    assert resp.status_code == 200
    assert resp.json()["skill_id"] == "SK-001"


# ── GET /api/cp/hired-agents/{id}/platform-connections ──────────────────────

def test_list_platform_connections_success():
    payload = [{"connection_id": "CONN-001", "platform_name": "linkedin"}]
    mock_client = _mock_httpx_get(200, payload)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client), \
         patch("api.cp_skills.get_current_user", return_value=MagicMock()), \
         patch.dict("os.environ", {"PLANT_GATEWAY_URL": "http://plant-gateway-test:8000"}):
        resp = client.get(
            "/api/cp/hired-agents/HIRED-001/platform-connections", headers=MOCK_HEADERS
        )

    assert resp.status_code == 200


# ── POST /api/cp/hired-agents/{id}/platform-connections ─────────────────────

def test_create_platform_connection_success():
    payload = {"connection_id": "CONN-002", "platform_name": "twitter"}
    mock_client = _mock_httpx_get(201, payload)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client), \
         patch("api.cp_skills.get_current_user", return_value=MagicMock()), \
         patch.dict("os.environ", {"PLANT_GATEWAY_URL": "http://plant-gateway-test:8000"}):
        resp = client.post(
            "/api/cp/hired-agents/HIRED-001/platform-connections",
            headers=MOCK_HEADERS,
            json={"platform_name": "twitter", "connection_type": "oauth2", "credentials": {}, "metadata": {}},
        )

    assert resp.status_code in (200, 201)


# ── DELETE /api/cp/hired-agents/{id}/platform-connections/{conn_id} ─────────

def test_delete_platform_connection_success():
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 204
    mock_resp.text = ""

    mock_client = AsyncMock()
    mock_client.delete = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client), \
         patch("api.cp_skills.get_current_user", return_value=MagicMock()), \
         patch.dict("os.environ", {"PLANT_GATEWAY_URL": "http://plant-gateway-test:8000"}):
        resp = client.delete(
            "/api/cp/hired-agents/HIRED-001/platform-connections/CONN-001",
            headers=MOCK_HEADERS,
        )

    assert resp.status_code == 204


# ── GET /api/cp/hired-agents/{id}/performance-stats ─────────────────────────

def test_get_performance_stats_success():
    payload = [{"stat_date": "2026-03-01", "metric_key": "posts_published", "metric_value": 5.0}]
    mock_client = _mock_httpx_get(200, payload)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client), \
         patch("api.cp_skills.get_current_user", return_value=MagicMock()), \
         patch.dict("os.environ", {"PLANT_GATEWAY_URL": "http://plant-gateway-test:8000"}):
        resp = client.get(
            "/api/cp/hired-agents/HIRED-001/performance-stats", headers=MOCK_HEADERS
        )

    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── Routing smoke test ───────────────────────────────────────────────────────

def test_plant_gateway_url_not_configured_raises_502():
    """When PLANT_GATEWAY_URL is missing, route must return 500/502, not crash."""
    with patch("api.cp_skills.get_current_user", return_value=MagicMock()), \
         patch.dict("os.environ", {}, clear=True):
        # Remove PLANT_GATEWAY_URL from env
        import os
        os.environ.pop("PLANT_GATEWAY_URL", None)
        resp = client.get("/api/cp/skills/SK-001", headers=MOCK_HEADERS)

    assert resp.status_code in (500, 502)
```

**Test run command:**
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit cp-backend-test
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```

**Acceptance criteria:**
- [ ] `src/CP/BackEnd/tests/test_cp_skills_routes.py` exists with ≥7 test functions
- [ ] All 6 routes covered (GET skills, GET skill, GET connections, POST connections, DELETE connection, GET perf-stats)
- [ ] Missing `PLANT_GATEWAY_URL` scenario tested
- [ ] 404 from Plant Gateway propagated correctly
- [ ] Coverage ≥80% on `api/cp_skills.py` (docker test exits 0)

---

## Iteration 2 — CP FrontEnd Skills + Performance

**Scope:** Wire the 6 new CP BackEnd routes into the CP FrontEnd: create 3 service files, one reusable `SkillsPanel` component with inline `GoalConfigForm`, and add two new sections ("Skills" and "Performance") to the existing `MyAgents.tsx` tab navigation.

**Branch naming:** E2 uses `feat/CP-SKILLS-1-it2-e2`, E3 uses `feat/CP-SKILLS-1-it2-e3`

**Docker integration test command (FE):**
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit \
  $(docker compose -f docker-compose.test.yml config --services | grep -i "cp-front\|cp-fe\|frontend" | head -1 || echo "cp-backend-test")
```
> If no dedicated FE test service exists in docker-compose.test.yml, run TypeScript type-check instead:
> ```bash
> cd src/CP/FrontEnd && npx tsc --noEmit
> ```

---

### E2 — CP FrontEnd service layer for skills & performance

**Epic complete ✅** ← Agent: add this line here and commit when all E2 stories pass.

---

#### E2-S1 — Create 3 TypeScript service files

**Branch:** `feat/CP-SKILLS-1-it2-e2`  
**BLOCKED UNTIL:** none (can start on main after Iteration 1 is merged)  
**Estimated time:** 45 minutes

**Context (2 sentences):**
The CP FrontEnd calls the CP BackEnd via relative paths (same origin). The existing `services/hiredAgents.service.ts` shows the exact pattern: `fetch('/api/cp/hired-agents/...')`, check `resp.ok`, throw a typed error on failure. All 3 new service files follow this same pattern.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/services/hiredAgents.service.ts` — lines 1–60 (HTTP + error pattern to copy)
2. `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` — lines 1–40 (TS types pattern)

**What to build:**

**File 1: `src/CP/FrontEnd/src/services/agentSkills.service.ts`**

```typescript
// src/CP/FrontEnd/src/services/agentSkills.service.ts

export interface GoalSchemaField {
  key: string
  label: string
  type: 'text' | 'number' | 'boolean' | 'enum' | 'list' | 'object'
  required?: boolean
  description?: string
  options?: string[]
  item_type?: string
  min?: number
  max?: number
  max_plan_gate?: string
}

export interface GoalSchema {
  fields: GoalSchemaField[]
  requires_platform_connections?: boolean
}

export interface AgentSkill {
  skill_id: string
  name: string
  display_name: string
  description?: string
  category?: string
  goal_schema?: GoalSchema
}

export interface AgentSkillsResponse {
  skills?: AgentSkill[]
  items?: AgentSkill[]
}

/**
 * Fetch all skills assigned to a hired agent.
 * Calls: GET /api/cp/hired-agents/{hired_instance_id}/skills
 */
export async function listHiredAgentSkills(
  hiredInstanceId: string
): Promise<AgentSkill[]> {
  const resp = await fetch(`/api/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/skills`)
  if (!resp.ok) {
    const text = await resp.text().catch(() => '')
    throw Object.assign(new Error(`Failed to load skills: ${text}`), { status: resp.status })
  }
  const data = await resp.json()
  if (Array.isArray(data)) return data as AgentSkill[]
  if (Array.isArray(data?.skills)) return data.skills as AgentSkill[]
  if (Array.isArray(data?.items)) return data.items as AgentSkill[]
  return []
}

/**
 * Fetch a single skill (including its full goal_schema).
 * Calls: GET /api/cp/skills/{skill_id}
 */
export async function getSkill(skillId: string): Promise<AgentSkill> {
  const resp = await fetch(`/api/cp/skills/${encodeURIComponent(skillId)}`)
  if (!resp.ok) {
    const text = await resp.text().catch(() => '')
    throw Object.assign(new Error(`Failed to load skill: ${text}`), { status: resp.status })
  }
  return resp.json() as Promise<AgentSkill>
}
```

**File 2: `src/CP/FrontEnd/src/services/platformConnections.service.ts`**

```typescript
// src/CP/FrontEnd/src/services/platformConnections.service.ts

export interface PlatformConnection {
  connection_id: string
  platform_name: string
  connection_type: string
  status?: string
  metadata?: Record<string, unknown>
}

export interface CreateConnectionBody {
  platform_name: string
  connection_type: string
  credentials?: Record<string, unknown>
  metadata?: Record<string, unknown>
}

/**
 * List all platform connections for a hired agent.
 * Calls: GET /api/cp/hired-agents/{hired_instance_id}/platform-connections
 */
export async function listPlatformConnections(
  hiredInstanceId: string
): Promise<PlatformConnection[]> {
  const resp = await fetch(
    `/api/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/platform-connections`
  )
  if (!resp.ok) {
    const text = await resp.text().catch(() => '')
    throw Object.assign(new Error(`Failed to load connections: ${text}`), { status: resp.status })
  }
  const data = await resp.json()
  return Array.isArray(data) ? (data as PlatformConnection[]) : (data?.connections ?? [])
}

/**
 * Create a new platform connection.
 * Calls: POST /api/cp/hired-agents/{hired_instance_id}/platform-connections
 */
export async function createPlatformConnection(
  hiredInstanceId: string,
  body: CreateConnectionBody
): Promise<PlatformConnection> {
  const resp = await fetch(
    `/api/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/platform-connections`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }
  )
  if (!resp.ok) {
    const text = await resp.text().catch(() => '')
    throw Object.assign(new Error(`Failed to create connection: ${text}`), { status: resp.status })
  }
  return resp.json() as Promise<PlatformConnection>
}

/**
 * Delete a platform connection.
 * Calls: DELETE /api/cp/hired-agents/{hired_instance_id}/platform-connections/{connection_id}
 */
export async function deletePlatformConnection(
  hiredInstanceId: string,
  connectionId: string
): Promise<void> {
  const resp = await fetch(
    `/api/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/platform-connections/${encodeURIComponent(connectionId)}`,
    { method: 'DELETE' }
  )
  if (!resp.ok && resp.status !== 204) {
    const text = await resp.text().catch(() => '')
    throw Object.assign(new Error(`Failed to delete connection: ${text}`), { status: resp.status })
  }
}
```

**File 3: `src/CP/FrontEnd/src/services/performanceStats.service.ts`**

```typescript
// src/CP/FrontEnd/src/services/performanceStats.service.ts

export interface PerformanceStat {
  stat_id?: string
  stat_date: string          // ISO date e.g. "2026-03-01"
  metric_key: string         // e.g. "posts_published", "emails_sent"
  metric_value: number
  metadata?: Record<string, unknown>
}

/**
 * Fetch performance stats for a hired agent.
 * Calls: GET /api/cp/hired-agents/{hired_instance_id}/performance-stats
 */
export async function listPerformanceStats(
  hiredInstanceId: string
): Promise<PerformanceStat[]> {
  const resp = await fetch(
    `/api/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/performance-stats`
  )
  if (!resp.ok) {
    const text = await resp.text().catch(() => '')
    throw Object.assign(new Error(`Failed to load performance stats: ${text}`), { status: resp.status })
  }
  const data = await resp.json()
  if (Array.isArray(data)) return data as PerformanceStat[]
  if (Array.isArray(data?.stats)) return data.stats as PerformanceStat[]
  if (Array.isArray(data?.items)) return data.items as PerformanceStat[]
  return []
}
```

**TypeScript compile check:**
```bash
cd src/CP/FrontEnd && npx tsc --noEmit
# Must exit 0 — no type errors
```

**Acceptance criteria:**
- [ ] `src/CP/FrontEnd/src/services/agentSkills.service.ts` exists with `listHiredAgentSkills()` + `getSkill()`
- [ ] `src/CP/FrontEnd/src/services/platformConnections.service.ts` exists with `listPlatformConnections()` + `createPlatformConnection()` + `deletePlatformConnection()`
- [ ] `src/CP/FrontEnd/src/services/performanceStats.service.ts` exists with `listPerformanceStats()`
- [ ] All functions: loading implied by `async`, error thrown with `status` field, empty array returned on empty response
- [ ] `npx tsc --noEmit` exits 0 (no TypeScript errors)

---

### E3 — Customer configures skills & sees performance

**Epic complete ✅** ← Agent: add this line here and commit when all E3 stories pass.

---

#### E3-S1 — Create `SkillsPanel.tsx` component

**Branch:** `feat/CP-SKILLS-1-it2-e3`  
**BLOCKED UNTIL:** E2-S1 merged to same iteration branch  
**Estimated time:** 90 minutes

**Context (2 sentences):**
`SkillsPanel` is a new React component that renders the skills assigned to a hired agent. Each skill card shows the skill name + description; if the skill has `goal_schema.fields`, a dynamic `GoalConfigForm` renders each field using the same field-type renderers already in `MyAgents.tsx` (`text`, `number`, `boolean`, `enum`, `list`, `object`). Platform connections required by the skill are shown inline with Add/Delete controls.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — lines 50–140 (field renderers: `renderListField`, `renderObjectField`, `validateRequiredField`, `JsonObjectTextarea`)
2. `src/CP/FrontEnd/src/services/agentSkills.service.ts` — (just created in E2-S1 — types reference)
3. `src/CP/FrontEnd/src/services/platformConnections.service.ts` — (just created in E2-S1 — types reference)

**What to build:**

Create `src/CP/FrontEnd/src/components/SkillsPanel.tsx`:

```typescript
// src/CP/FrontEnd/src/components/SkillsPanel.tsx
//
// Shows all skills assigned to a hired agent.
// For each skill, renders a GoalConfigForm driven by skill.goal_schema.
// Shows platform connections for skills that require them.

import { useState, useEffect, useCallback } from 'react'
import { Button, Badge, Input, Select, Textarea, Checkbox } from '@fluentui/react-components'
import { LoadingIndicator, FeedbackMessage } from './FeedbackIndicators'
import {
  listHiredAgentSkills,
  type AgentSkill,
  type GoalSchemaField,
} from '../services/agentSkills.service'
import {
  listPlatformConnections,
  createPlatformConnection,
  deletePlatformConnection,
  type PlatformConnection,
} from '../services/platformConnections.service'

// ── Helpers ──────────────────────────────────────────────────────────────────

function parseListText(value: string): string[] {
  return String(value || '')
    .split(/\n|,/g)
    .map((x) => x.trim())
    .filter(Boolean)
}

function safeJsonStringify(value: unknown): string {
  try { return JSON.stringify(value ?? {}, null, 2) } catch { return '{}' }
}

// ── GoalConfigForm ────────────────────────────────────────────────────────────

function GoalFieldRenderer(props: {
  field: GoalSchemaField
  value: unknown
  readOnly: boolean
  onChange: (key: string, value: unknown) => void
}) {
  const { field, value, readOnly, onChange } = props

  const label = field.required ? `${field.label} *` : field.label

  if (field.type === 'boolean') {
    return (
      <div style={{ marginBottom: '0.75rem' }}>
        <Checkbox
          label={label}
          checked={Boolean(value)}
          disabled={readOnly}
          onChange={(_, data) => onChange(field.key, Boolean(data.checked))}
        />
        {field.description && <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>}
      </div>
    )
  }

  if (field.type === 'enum' && Array.isArray(field.options) && field.options.length) {
    return (
      <div style={{ marginBottom: '0.75rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>{label}</label>
        <Select
          value={String(value ?? '')}
          disabled={readOnly}
          onChange={(_, data) => onChange(field.key, data.value)}
        >
          <option value="">— select —</option>
          {field.options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </Select>
        {field.description && <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>}
      </div>
    )
  }

  if (field.type === 'list') {
    const listValue = Array.isArray(value) ? value : []
    const text = listValue.map((x) => String(x ?? '')).join('\n')
    return (
      <div style={{ marginBottom: '0.75rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>{label}</label>
        <Textarea
          value={text}
          disabled={readOnly}
          placeholder="One per line"
          onChange={(_, data) => onChange(field.key, parseListText(String(data.value || '')))}
        />
        {field.description && <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>}
      </div>
    )
  }

  if (field.type === 'object') {
    const [localText, setLocalText] = useState(safeJsonStringify(value ?? {}))
    useEffect(() => { setLocalText(safeJsonStringify(value ?? {})) }, [value])
    return (
      <div style={{ marginBottom: '0.75rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>{label}</label>
        <Textarea
          value={localText}
          disabled={readOnly}
          onChange={(_, data) => {
            setLocalText(String(data.value || ''))
            try {
              const parsed = JSON.parse(String(data.value || '{}'))
              if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
                onChange(field.key, parsed)
              }
            } catch { /* keep raw */ }
          }}
        />
        {field.description && <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>}
      </div>
    )
  }

  // Default: text or number
  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <label style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 500 }}>{label}</label>
      <Input
        type={field.type === 'number' ? 'number' : 'text'}
        value={String(value ?? '')}
        disabled={readOnly}
        min={field.min}
        max={field.max}
        onChange={(_, data) =>
          onChange(field.key, field.type === 'number' ? Number(data.value) : data.value)
        }
      />
      {field.description && <div style={{ fontSize: '0.8rem', opacity: 0.7 }}>{field.description}</div>}
    </div>
  )
}

interface GoalConfigFormProps {
  skill: AgentSkill
  readOnly: boolean
}

function GoalConfigForm({ skill, readOnly }: GoalConfigFormProps) {
  const fields = skill.goal_schema?.fields ?? []
  const [values, setValues] = useState<Record<string, unknown>>({})
  const [saved, setSaved] = useState(false)

  if (fields.length === 0) {
    return (
      <div style={{ opacity: 0.6, fontSize: '0.9rem', paddingTop: '0.5rem' }}>
        No configurable goal fields for this skill.
      </div>
    )
  }

  const setField = (key: string, value: unknown) => {
    setSaved(false)
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div>
      <div style={{ fontWeight: 600, marginBottom: '0.5rem', fontSize: '0.9rem' }}>
        Goal Configuration
      </div>
      {fields.map((field) => (
        <GoalFieldRenderer
          key={field.key}
          field={field}
          value={values[field.key]}
          readOnly={readOnly}
          onChange={setField}
        />
      ))}
      {!readOnly && (
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <Button
            appearance="primary"
            size="small"
            onClick={() => setSaved(true)}
          >
            Save goal config
          </Button>
          {saved && <span style={{ opacity: 0.7, fontSize: '0.85rem' }}>Saved ✓</span>}
        </div>
      )}
    </div>
  )
}

// ── PlatformConnectionsPanel ──────────────────────────────────────────────────

interface PlatformConnectionsPanelProps {
  hiredInstanceId: string
  requiredPlatforms?: string[]   // from skill metadata
  readOnly: boolean
}

function PlatformConnectionsPanel({
  hiredInstanceId,
  requiredPlatforms = [],
  readOnly,
}: PlatformConnectionsPanelProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [connections, setConnections] = useState<PlatformConnection[]>([])
  const [newPlatform, setNewPlatform] = useState('')
  const [newToken, setNewToken] = useState('')
  const [adding, setAdding] = useState(false)

  const loadConnections = useCallback(async () => {
    if (!hiredInstanceId) return
    setLoading(true)
    setError(null)
    try {
      const data = await listPlatformConnections(hiredInstanceId)
      setConnections(data)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load connections')
    } finally {
      setLoading(false)
    }
  }, [hiredInstanceId])

  useEffect(() => { loadConnections() }, [loadConnections])

  const handleAdd = async () => {
    if (!newPlatform.trim()) { setError('Platform name is required'); return }
    setAdding(true)
    setError(null)
    try {
      const conn = await createPlatformConnection(hiredInstanceId, {
        platform_name: newPlatform.trim().toLowerCase(),
        connection_type: 'token',
        credentials: newToken ? { access_token: newToken } : {},
      })
      setConnections((prev) => [...prev, conn])
      setNewPlatform('')
      setNewToken('')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to add connection')
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (connectionId: string) => {
    setError(null)
    try {
      await deletePlatformConnection(hiredInstanceId, connectionId)
      setConnections((prev) => prev.filter((c) => c.connection_id !== connectionId))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to remove connection')
    }
  }

  return (
    <div style={{ marginTop: '0.75rem' }}>
      <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.5rem' }}>
        Platform Connections
        {requiredPlatforms.length > 0 && (
          <span style={{ marginLeft: '0.5rem', opacity: 0.7, fontWeight: 400 }}>
            (required: {requiredPlatforms.join(', ')})
          </span>
        )}
      </div>

      {loading && <LoadingIndicator message="Loading connections..." size="small" />}
      {error && <FeedbackMessage intent="error" title="Error" message={error} />}

      {!loading && connections.length === 0 && (
        <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>No platforms connected yet.</div>
      )}

      {connections.map((conn) => (
        <div
          key={conn.connection_id}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '0.4rem',
            padding: '0.4rem 0.6rem',
            borderRadius: '6px',
            border: '1px solid var(--colorNeutralStroke2)',
          }}
        >
          <Badge appearance="tint" size="small">{conn.platform_name}</Badge>
          <span style={{ flex: 1, fontSize: '0.85rem', opacity: 0.8 }}>
            {conn.status ?? 'connected'}
          </span>
          {!readOnly && (
            <Button
              appearance="subtle"
              size="small"
              onClick={() => handleDelete(conn.connection_id)}
            >
              Remove
            </Button>
          )}
        </div>
      ))}

      {!readOnly && (
        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
          <Input
            placeholder="Platform (e.g. linkedin)"
            value={newPlatform}
            onChange={(_, data) => setNewPlatform(String(data.value || ''))}
            style={{ width: '140px' }}
          />
          <Input
            placeholder="Access token (optional)"
            value={newToken}
            type="password"
            onChange={(_, data) => setNewToken(String(data.value || ''))}
            style={{ flex: 1, minWidth: '160px' }}
          />
          <Button
            appearance="outline"
            size="small"
            onClick={handleAdd}
            disabled={adding || !newPlatform.trim()}
          >
            {adding ? 'Adding...' : 'Add'}
          </Button>
        </div>
      )}
    </div>
  )
}

// ── SkillsPanel (main export) ─────────────────────────────────────────────────

interface SkillsPanelProps {
  hiredInstanceId: string
  readOnly: boolean
}

export function SkillsPanel({ hiredInstanceId, readOnly }: SkillsPanelProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [skills, setSkills] = useState<AgentSkill[]>([])
  const [expandedSkillId, setExpandedSkillId] = useState<string | null>(null)

  useEffect(() => {
    if (!hiredInstanceId) return
    let cancelled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await listHiredAgentSkills(hiredInstanceId)
        if (!cancelled) setSkills(data)
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load skills')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [hiredInstanceId])

  if (!hiredInstanceId) {
    return (
      <div style={{ opacity: 0.6, fontSize: '0.9rem', paddingTop: '0.5rem' }}>
        No hired agent selected.
      </div>
    )
  }

  if (loading) return <LoadingIndicator message="Loading skills..." size="medium" />

  if (error) return <FeedbackMessage intent="error" title="Failed to load skills" message={error} />

  if (skills.length === 0) {
    return (
      <div style={{ opacity: 0.6, fontSize: '0.9rem', paddingTop: '0.5rem' }}>
        No skills configured for this agent yet.
      </div>
    )
  }

  return (
    <div>
      {skills.map((skill) => {
        const isExpanded = expandedSkillId === skill.skill_id
        const hasGoalSchema = (skill.goal_schema?.fields?.length ?? 0) > 0
        const requiresPlatforms = skill.goal_schema?.requires_platform_connections === true

        return (
          <div
            key={skill.skill_id}
            style={{
              marginBottom: '0.75rem',
              borderRadius: '10px',
              border: '1px solid var(--colorNeutralStroke2)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                cursor: hasGoalSchema || requiresPlatforms ? 'pointer' : 'default',
                background: isExpanded ? 'var(--colorNeutralBackground2)' : undefined,
              }}
              onClick={() =>
                (hasGoalSchema || requiresPlatforms) &&
                setExpandedSkillId(isExpanded ? null : skill.skill_id)
              }
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600 }}>{skill.display_name || skill.name}</div>
                {skill.description && (
                  <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>{skill.description}</div>
                )}
              </div>
              {(hasGoalSchema || requiresPlatforms) && (
                <Button appearance="subtle" size="small">
                  {isExpanded ? 'Collapse ▲' : 'Configure ▼'}
                </Button>
              )}
            </div>

            {isExpanded && (
              <div style={{ padding: '0.75rem 1rem', borderTop: '1px solid var(--colorNeutralStroke2)' }}>
                {hasGoalSchema && <GoalConfigForm skill={skill} readOnly={readOnly} />}
                {requiresPlatforms && (
                  <PlatformConnectionsPanel
                    hiredInstanceId={hiredInstanceId}
                    readOnly={readOnly}
                  />
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default SkillsPanel
```

**TypeScript compile check:**
```bash
cd src/CP/FrontEnd && npx tsc --noEmit
```

**Acceptance criteria:**
- [ ] `src/CP/FrontEnd/src/components/SkillsPanel.tsx` created and exports `SkillsPanel`
- [ ] Loading state: shows `<LoadingIndicator>` while fetching
- [ ] Error state: shows `<FeedbackMessage intent="error">` on fetch failure
- [ ] Empty state: shows "No skills configured for this agent yet." when `skills.length === 0`
- [ ] Skill cards are expandable — only skills with `goal_schema.fields` or `requires_platform_connections` show Configure button
- [ ] `GoalConfigForm` renders field types: text, number, boolean, enum, list, object
- [ ] `PlatformConnectionsPanel` shows connections list, Add form, Remove button
- [ ] `npx tsc --noEmit` exits 0

---

#### E3-S2 — Add Skills + Performance tabs to `MyAgents.tsx`

**Branch:** `feat/CP-SKILLS-1-it2-e3` (same as E3-S1)  
**BLOCKED UNTIL:** E3-S1 complete (SkillsPanel.tsx must exist before importing it)  
**Estimated time:** 45 minutes

**Context (2 sentences):**
`MyAgents.tsx` already has two tab buttons ("Configure", "Goal Setting") that set `activeSection` state and conditionally render panels. This story adds two more: "Skills" (renders `SkillsPanel`) and "Performance" (renders inline performance stats). The active section is already managed by `activeSection` state and a `<div style={{ marginTop: '1rem', ... }}>` block — simply extend both.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — lines 1660–1800 (tab buttons + active section render block)
2. `src/CP/FrontEnd/src/services/performanceStats.service.ts` — (just created in E2-S1)
3. `src/CP/FrontEnd/src/components/SkillsPanel.tsx` — (just created in E3-S1)

**What to build:**

**Step 1 — Add imports at top of `MyAgents.tsx`:**
```typescript
import { SkillsPanel } from '../../components/SkillsPanel'
import { listPerformanceStats, type PerformanceStat } from '../../services/performanceStats.service'
```

**Step 2 — Add two new tab buttons** after the existing "Goal Setting" button (around line 1695):
```tsx
<Button
  appearance={activeSection === 'skills' ? 'primary' : 'outline'}
  onClick={() => setActiveSection('skills')}
  disabled={selectedReadOnlyExpired}
>
  Skills
</Button>
<Button
  appearance={activeSection === 'performance' ? 'primary' : 'outline'}
  onClick={() => setActiveSection('performance')}
  disabled={selectedReadOnlyExpired}
>
  Performance
</Button>
```

**Step 3 — Add `'skills' | 'performance'` to the `activeSection` type.** The current `activeSection` state is likely typed as `'configure' | 'goals'` or just `string`. Extend it to include `'skills'` and `'performance'`.

**Step 4 — Add a PerformancePanel inline component** (add before the main `return` in the file, near the other panel functions):
```tsx
function PerformancePanel(props: { instance: MyAgentInstanceSummary }) {
  const { instance } = props
  const hiredInstanceId = String(instance.hired_instance_id || '').trim()

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState<PerformanceStat[]>([])

  useEffect(() => {
    if (!hiredInstanceId) return
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await listPerformanceStats(hiredInstanceId)
        if (!cancelled) setStats(data)
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load performance stats')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [hiredInstanceId])

  if (!hiredInstanceId) {
    return <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>No hired agent selected.</div>
  }
  if (loading) return <LoadingIndicator message="Loading performance data..." size="medium" />
  if (error) return <FeedbackMessage intent="error" title="Error" message={error} />
  if (stats.length === 0) {
    return (
      <div style={{ opacity: 0.6, fontSize: '0.9rem', paddingTop: '0.5rem' }}>
        No performance data yet. Stats will appear here once the agent starts running.
      </div>
    )
  }

  // Group by metric_key for display
  const byKey: Record<string, PerformanceStat[]> = {}
  for (const s of stats) {
    if (!byKey[s.metric_key]) byKey[s.metric_key] = []
    byKey[s.metric_key].push(s)
  }

  return (
    <div>
      {Object.entries(byKey).map(([key, rows]) => {
        const latest = rows.sort((a, b) => b.stat_date.localeCompare(a.stat_date))[0]
        return (
          <div
            key={key}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0.6rem 0.75rem',
              marginBottom: '0.4rem',
              borderRadius: '8px',
              border: '1px solid var(--colorNeutralStroke2)',
            }}
          >
            <span style={{ fontWeight: 500 }}>{key.replace(/_/g, ' ')}</span>
            <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>{latest.metric_value}</span>
          </div>
        )
      })}
      <div style={{ fontSize: '0.8rem', opacity: 0.6, marginTop: '0.5rem' }}>
        Showing latest value per metric across {stats.length} recorded data points.
      </div>
    </div>
  )
}
```

**Step 5 — Extend the active section render block** (the big `{activeSection === 'configure' ? ... : ...}` block around line 1749). Add two more cases:
```tsx
{activeSection === 'configure' ? (
  <>
    {/* existing configure content — do not change */}
  </>
) : activeSection === 'goals' ? (
  <>
    {/* existing goals content — do not change */}
  </>
) : activeSection === 'skills' ? (
  <>
    <div style={{ fontWeight: 600 }}>Skills & Goal Configuration</div>
    <div style={{ marginTop: '0.25rem', opacity: 0.85 }}>
      View and configure goals for each skill assigned to this agent.
    </div>
    <SkillsPanel
      hiredInstanceId={String(selectedInstance.hired_instance_id || '').trim()}
      readOnly={selectedReadOnlyExpired || selectedInReadOnlyRetention}
    />
  </>
) : (
  <>
    <div style={{ fontWeight: 600 }}>Performance</div>
    <div style={{ marginTop: '0.25rem', opacity: 0.85 }}>
      Daily activity metrics from your agent's runs.
    </div>
    <PerformancePanel instance={selectedInstance} />
  </>
)}
```

**TypeScript compile check:**
```bash
cd src/CP/FrontEnd && npx tsc --noEmit
```

**Acceptance criteria:**
- [ ] `import { SkillsPanel }` and `import { listPerformanceStats, type PerformanceStat }` added to `MyAgents.tsx`
- [ ] "Skills" and "Performance" tab buttons render in the tab bar
- [ ] Clicking "Skills" renders `<SkillsPanel hiredInstanceId={...} readOnly={...} />`
- [ ] Clicking "Performance" renders `<PerformancePanel instance={selectedInstance} />`
- [ ] `PerformancePanel`: loading state, error state, empty state, data state all handled
- [ ] Existing "Configure" and "Goal Setting" tabs unchanged — no regression
- [ ] `npx tsc --noEmit` exits 0

---

## Post-Plan Notes (PM Only)

### Known Caveat — Two-Hop Skills Lookup

The route `GET /api/cp/hired-agents/{hired_instance_id}/skills` requires resolving `agent_id` first.
The CP proxy (`E1-S1`) uses `GET /api/v1/hired-agents/by-id/{hired_instance_id}` for this.
If that Plant route does not exist, the agent should:
1. Check `src/Plant/BackEnd/api/v1/hired_agents_simple.py` for available GET routes
2. Use whichever route returns JSON with `agent_id` field
3. If none exist, add a Story E1-S3: "Add `GET /api/v1/hired-agents/{id}` to Plant BackEnd" (Plant Pattern B, 30 minutes) and mark E1-S1 BLOCKED until E1-S3 merged

### GoalConfigForm — Save Destination TBD

The `GoalConfigForm` in `SkillsPanel.tsx` currently calls `setSaved(true)` on the "Save goal config" button (optimistic local state only). A proper save destination requires a `PUT /cp/hired-agents/{id}/skills/{skill_id}/goal-settings` endpoint which is not in scope for this plan. This is a known gap — add a TODO comment and a follow-up ticket.

### `goal_schema` `max_plan_gate` Fields

Some skill `goal_schema.fields` have a `max_plan_gate` property (e.g. `execute-trade-order` skill). These fields are rendered normally — the enforcement layer is out of scope. A TODO comment in `GoalFieldRenderer` is sufficient.

