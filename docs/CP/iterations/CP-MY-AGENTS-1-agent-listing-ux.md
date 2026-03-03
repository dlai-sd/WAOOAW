# CP-MY-AGENTS-1 — Agent Listing & Portal UX Fixes

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-MY-AGENTS-1` |
| Feature area | Customer Portal — Agent listing, error skeleton, nav cleanup |
| Created | 2026-03-03 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | Gap analysis from `docs/CP/iterations/CP-NAV-1-navigation-structure.md`, `CP-SKILLS-1`, `CP-SKILLS-2` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 2 |
| Total stories | 4 |

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
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update (none in this plan)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (E1) before frontend (E2)
- [x] No placeholders remain

---

## Background

### What is broken today

1. **My Agents shows "No agents yet"** for `yogeshkhandge@gmail.com` and `rupalikhandge@gmail.com`.
   - Alembic migration `024_seed_demo_hired_agents` seeded two agents (Share Trader + Content Creator & Publisher) for both users into the Plant `hired_agents` table.
   - But `CP BackEnd /cp/my-agents/summary` reads from `cp_subscriptions_simple._by_id` — an **in-memory Python dict** that is empty on every server restart.
   - Even when `PLANT_GATEWAY_URL` is set and the Plant BackEnd is up, Plant has no `GET /api/v1/hired-agents/by-customer/{customer_id}` endpoint, so CP can never fall back to reading directly from `hired_agents`.
   - Result: `_list_subscriptions()` returns `[]`; `_enrich_with_hired_agent` is never called; response is always `{"instances": []}`.

2. **My Agents error state shows raw error text**, not graceful skeleton cards.
   - YouTube-style empty card shells (ghost skeleton) should appear when the API is down, so the layout doesn't break.

3. **"Discover" nav item is hardcoded outside the `menuItems` array** in `AuthenticatedPortal.tsx`.
   - It always appears last, cannot be reordered, and duplicates DOM logic.

### Fix strategy

**Iteration 1 (BE):**
- E1-S1: Add `GET /api/v1/hired-agents/by-customer/{customer_id}` to Plant BackEnd `hired_agents_simple.py` — returns all active `hired_agents` rows for a customer from the DB.
- E1-S2: CP BackEnd `my_agents_summary.py` — add a fallback: when `_list_subscriptions()` returns empty AND `PLANT_GATEWAY_URL` is set, call Plant `/api/v1/hired-agents/by-customer/{customer_id}` and synthesise `MyAgentInstanceSummary` objects directly, bypassing the subscription layer.

**Iteration 2 (FE):**
- E2-S1: `MyAgents.tsx` — replace the raw error text with `ListItemSkeleton count={2}` ghost cards + a soft inline error chip.
- E2-S2: `AuthenticatedPortal.tsx` — move `discover` into `menuItems[]`; delete the duplicate hardcoded button.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — Plant BackEnd new endpoint + CP BackEnd fallback | 1 | 2 | ~1h 45m | Start + 2h |
| 2 | Lane A — CP FrontEnd ghost skeletons + Discover nav fix | 1 | 2 | ~45m | Start + 1h |

**Estimate basis:** New Plant GET route = 30 min | CP proxy fallback = 45 min | Tests = 20 min | PR = 10 min | FE skeleton = 20 min | FE nav fix = 10 min | FE tests = 10 min | PR = 10 min. Add 20% buffer.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git status && git log --oneline -3
# Must show: clean tree on main. If not, resolve before launching.
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

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11/FastAPI/SQLAlchemy engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-MY-AGENTS-1-agent-listing-ux.md
YOUR SCOPE: Iteration 1 only — Epic E1. Do not touch Iteration 2 content.
TIME BUDGET: 1h 45m. If you reach 2h without finishing, follow STUCK PROTOCOL now.

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
# Must show: feat(CP-MY-AGENTS-1): iteration 1 — by-customer endpoint + summary fallback
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Fluent UI v9 engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React 18/TypeScript/Fluent UI v9 engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-MY-AGENTS-1-agent-listing-ux.md
YOUR SCOPE: Iteration 2 only — Epic E2. Do not touch Iteration 1 content.
TIME BUDGET: 1h. If you reach 1h 30m without finishing, follow STUCK PROTOCOL now.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(CP-MY-AGENTS-1): iteration 1 — by-customer endpoint + summary fallback
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Execute Epic E2 in order: E2-S1 → E2-S2
4. When all stories are tested, open the iteration PR. Post URL. HALT.
```

**Come back at:** Start + 1h

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given. Activate each persona now.
For every epic you execute, open with one line:
> *"Acting as a [persona], I will [what you're building] by [approach]."*

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
git checkout main && git pull
git checkout -b feat/CP-MY-AGENTS-1-it1-e1

git commit --allow-empty -m "chore(CP-MY-AGENTS-1): start iteration 1"
git push origin feat/CP-MY-AGENTS-1-it1-e1

gh pr create \
  --base main \
  --head feat/CP-MY-AGENTS-1-it1-e1 \
  --draft \
  --title "tracking: CP-MY-AGENTS-1 Iteration 1 — in progress" \
  --body "## tracking: CP-MY-AGENTS-1 Iteration 1
Subscribe to this PR to receive notifications.
Stories: E1-S1 🔴 | E1-S2 🔴"
```

### Rule 1 — Scope lock

Implement exactly the acceptance criteria. Do not refactor unrelated code.

### Rule 2 — Tests before marking story done

Write the tests listed in the story card. Run the docker test command. Do not mark Done without green tests.

### Rule 3 — STUCK PROTOCOL

If blocked on one story for more than 30 min:
1. `git add -A && git commit -m "wip(CP-MY-AGENTS-1): stuck on [story-id] — [reason]"`
2. `git push origin feat/CP-MY-AGENTS-1-it1-e1`
3. Comment on the PR: "STUCK: [exact error / blocker]. Halting for human review."
4. HALT.

### Rule 4 — Iteration PR when all stories done

```bash
gh pr create \
  --base main \
  --title "feat(CP-MY-AGENTS-1): iteration 1 — by-customer endpoint + summary fallback" \
  --body "Closes Iteration 1 of CP-MY-AGENTS-1.

Stories done:
- E1-S1: Plant BackEnd GET /api/v1/hired-agents/by-customer/{customer_id}
- E1-S2: CP BackEnd my_agents_summary fallback when subscriptions empty"
```

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer sees their seeded agents | Plant BackEnd: add GET /api/v1/hired-agents/by-customer | 🔴 Not Started | — |
| E1-S2 | 1 | Customer sees their seeded agents | CP BackEnd: fallback in my_agents_summary.py | 🔴 Not Started | — |
| E2-S1 | 2 | Portal shows graceful offline state | CP FrontEnd: ghost skeleton cards on error in MyAgents.tsx | 🔴 Not Started | — |
| E2-S2 | 2 | Portal shows graceful offline state | CP FrontEnd: move Discover into menuItems | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Plant BackEnd endpoint + CP BackEnd summary fallback

**Scope:** `yogeshkhandge@gmail.com` and `rupalikhandge@gmail.com` see their two seeded agents (Share Trader + Content Creator & Publisher) on the My Agents page after server restart — no subscription record required.
**Lane:** B — two new backend paths, no migrations
**⏱ Estimated:** 1h 45m | **Come back:** Start + 2h
**Epics:** E1

### Dependency Map

```
E1-S1 ──► E1-S2
```

---

### Epic E1: Customer sees their seeded agents in My Agents

**Branch:** `feat/CP-MY-AGENTS-1-it1-e1`
**User story:** As `yogeshkhandge@gmail.com` or `rupalikhandge@gmail.com`, when I open My Agents, I see two agent cards — "Share Trader" and "Content Creator & Publisher" — even after a full server restart, because the CP BackEnd falls back directly to the Plant hired_agents table when the in-memory subscription store is empty.

---

#### Story E1-S1: Plant BackEnd — add GET /api/v1/hired-agents/by-customer/{customer_id}

**BLOCKED UNTIL:** none
**Estimated time:** 40 min
**Branch:** `feat/CP-MY-AGENTS-1-it1-e1`
**CP BackEnd pattern:** N/A — this is Plant BackEnd

**Context (read before acting):**
- The Plant `hired_agents` table has seeded rows with `customer_id` from migration `024_seed_demo_hired_agents`. Two rows for each demo user: `hired_instance_id = INST-YOGESH-01/02`, `SUB-YOGESH-01/02` for `customer_id = 1a9c1294-073e-4565-a359-27eae94a05b4`; and `INST-RUPALI-01/02`, `SUB-RUPALI-01/02` for `customer_id = 8a8e1d58-949f-41f3-81ff-7abf5d4a172e`.
- The seeded rows have `agent_type_id = NULL` (stripped at seed time for demo-DB compatibility). `_db_model_to_record()` raises HTTP 500 when `agent_type_id` is empty. The new endpoint must handle this by inferring `agent_type_id` from `agent_id` prefix instead of failing.

**Files to read first:**
1. `src/Plant/BackEnd/api/v1/hired_agents_simple.py` lines 254–360 (response models + `_db_model_to_record`)
2. `src/Plant/BackEnd/repositories/hired_agent_repository.py` lines 1–80 (session + existing query patterns)
3. `src/Plant/BackEnd/models/hired_agent.py` lines 1–60 (column names)

**What to build:**
Add `GET /api/v1/hired-agents/by-customer/{customer_id}` to `src/Plant/BackEnd/api/v1/hired_agents_simple.py`.
The endpoint returns a list of all `HiredAgentInstanceResponse` objects for the given `customer_id`, DB-backed only.

Add this response model immediately after `GoalsListResponse`:
```python
class HiredAgentsByCustomerResponse(BaseModel):
    customer_id: str
    instances: list[HiredAgentInstanceResponse] = Field(default_factory=list)
```

Add the endpoint after the `get_by_subscription` endpoint (around line 890):
```python
@router.get("/by-customer/{customer_id}", response_model=HiredAgentsByCustomerResponse)
async def list_hired_agents_by_customer(
    customer_id: str,
    db: AsyncSession | None = Depends(_get_read_hired_agents_db_session),
) -> HiredAgentsByCustomerResponse:
    """Return all hired agent instances for a customer.

    Uses get_read_db_session() — reads from read replica (NFR C6).
    Falls back to empty list when DB mode is not enabled.
    """
    if db is None:
        # Memory mode: scan in-memory dict for customer_id matches.
        records = [r for r in _by_id.values() if (r.customer_id or "").strip() == customer_id.strip()]
    else:
        from sqlalchemy import select
        stmt = (
            select(HiredAgentModel)
            .where(HiredAgentModel.customer_id == customer_id.strip())
            .where(HiredAgentModel.active == True)  # noqa: E712
        )
        result = await db.execute(stmt)
        models = result.scalars().all()
        records = []
        for model in models:
            # Seed rows may have agent_type_id = NULL — infer from agent_id prefix.
            raw_type_id = (getattr(model, "agent_type_id", None) or "").strip()
            if not raw_type_id:
                aid = (model.agent_id or "").strip().upper()
                if aid.startswith("AGT-TRD-"):
                    raw_type_id = "trading.share_trader.v1"
                elif aid.startswith("AGT-MKT-"):
                    raw_type_id = "marketing.digital_marketing.v1"
                else:
                    continue  # cannot infer — skip row
                # Temporarily patch the model attribute so _db_model_to_record works.
                object.__setattr__(model, "agent_type_id", raw_type_id)
            try:
                records.append(_db_model_to_record(model))
            except Exception:
                continue  # skip malformed rows

    instances = []
    for record in records:
        sub_status, ended_at = await _subscription_status_and_ended_at(
            subscription_id=record.subscription_id,
            db=db,
        )
        instances.append(_to_response(record, subscription_status=sub_status, ended_at=ended_at))

    return HiredAgentsByCustomerResponse(customer_id=customer_id, instances=instances)
```

**NFR patterns embedded (copy exactly):**
```python
# Router factory — always waooaw_router(), never bare APIRouter (AGENTS.md rule 1)
from core.routing import waooaw_router
router = waooaw_router(prefix="/hired-agents", tags=["hired-agents"])

# Read replica for GET routes (NFR C6 — catalog reads must NOT touch primary)
from core.database import get_read_db_session
db: AsyncSession | None = Depends(_get_read_hired_agents_db_session)
# _get_read_hired_agents_db_session already wraps get_read_db_session() — use it as-is.
```

**Acceptance criteria:**
- [ ] `GET /api/v1/hired-agents/by-customer/1a9c1294-073e-4565-a359-27eae94a05b4` returns 200 with 2 instances in `docker-compose` local env
- [ ] Each instance has `agent_id` = `AGT-TRD-001` or `AGT-MKT-001` and non-null `agent_type_id`
- [ ] `GET /api/v1/hired-agents/by-customer/nonexistent-id` returns 200 with `instances: []` (not 404)
- [ ] Route does NOT use `get_db_session()` — only `_get_read_hired_agents_db_session`

**Test to write:** `src/Plant/BackEnd/tests/unit/test_hired_agents_by_customer.py`
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_by_customer_unknown_returns_empty(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/hired-agents/by-customer/unknown-cust-id")
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer_id"] == "unknown-cust-id"
    assert body["instances"] == []
```

**Test command:** `cd src/Plant/BackEnd && docker-compose -f docker-compose.test.yml run plant-test pytest tests/unit/test_hired_agents_by_customer.py -v`

---

#### Story E1-S2: CP BackEnd — fallback in my_agents_summary.py when subscriptions empty

**BLOCKED UNTIL:** E1-S1 merged (same PR is fine — the Plant endpoint must exist before this code executes)
**Estimated time:** 45 min
**Branch:** `feat/CP-MY-AGENTS-1-it1-e1` (same branch, same PR)
**CP BackEnd pattern:** Pattern A — call existing Plant `/api/v1/hired-agents/by-customer/{customer_id}` via the existing `_plant_get_json` helper

**Context (read before acting):**
- `src/CP/BackEnd/api/my_agents_summary.py` currently calls `_list_subscriptions()` which returns `[]` when `cp_subscriptions_simple._by_id` is empty (in-memory mode, default). When the list is empty the function returns `{"instances": []}` immediately — the hired_agents data in Plant is never surfaced.
- The seeded demo hired_agents have `subscription_id = SUB-YOGESH-01, SUB-YOGESH-02` (yogesh) and `SUB-RUPALI-01, SUB-RUPALI-02` (rupali). When these are returned by Plant's new by-customer endpoint, CP must synthesise `MyAgentInstanceSummary` objects from them, filling in the subscription fields from the hired agent data.

**Files to read first:**
1. `src/CP/BackEnd/api/my_agents_summary.py` (full file — 185 lines)

**What to build:**
Add a new helper `_fallback_from_plant_hired_agents()` in `my_agents_summary.py` that queries Plant's new endpoint and synthesises summary objects. Then wire it into `get_my_agents_summary`.

Add this function after `_list_subscriptions()`:
```python
async def _fallback_from_plant_hired_agents(
    *, authorization: str | None, customer_id: str
) -> list[MyAgentInstanceSummary]:
    """
    Fallback: when cp_subscriptions_simple has no records (in-memory mode / fresh
    restart), read hired agents directly from Plant by customer_id and synthesise
    MyAgentInstanceSummary objects so My Agents page shows seeded data.

    This is a read-only path — it never writes to cp_subscriptions_simple.
    """
    try:
        base = _plant_base_url()
    except RuntimeError:
        return []

    try:
        data = await _plant_get_json(
            url=f"{base}/api/v1/hired-agents/by-customer/{customer_id}",
            authorization=authorization,
        )
    except (HTTPException, Exception):
        return []

    if not isinstance(data, dict):
        return []

    raw_instances = data.get("instances") or []
    if not isinstance(raw_instances, list):
        return []

    now = datetime.now(timezone.utc)
    period_end = (now + timedelta(days=30)).isoformat()

    results: list[MyAgentInstanceSummary] = []
    for item in raw_instances:
        if not isinstance(item, dict):
            continue
        sub_id = str(item.get("subscription_id") or "").strip()
        agent_id = str(item.get("agent_id") or "").strip()
        if not sub_id or not agent_id:
            continue

        results.append(
            MyAgentInstanceSummary(
                subscription_id=sub_id,
                agent_id=agent_id,
                duration="monthly",
                status="active",
                current_period_start=now.isoformat(),
                current_period_end=period_end,
                cancel_at_period_end=False,
                hired_instance_id=str(item.get("hired_instance_id") or "").strip() or None,
                agent_type_id=str(item.get("agent_type_id") or "").strip() or None,
                nickname=str(item.get("nickname") or "").strip() or None,
                configured=bool(item.get("configured")) if item.get("configured") is not None else None,
                goals_completed=bool(item.get("goals_completed")) if item.get("goals_completed") is not None else None,
                trial_status=str(item.get("trial_status") or "").strip() or None,
                trial_start_at=item.get("trial_start_at"),
                trial_end_at=item.get("trial_end_at"),
            )
        )
    return results
```

You also need `from datetime import timedelta` — add it to the existing `from datetime import datetime` import at the top of the file.

Wire the fallback into `get_my_agents_summary`. Find this block:
```python
    if not base_url or not instances:
        return MyAgentsSummaryResponse(instances=instances)
```
Replace it with:
```python
    if not instances and base_url:
        instances = await _fallback_from_plant_hired_agents(
            authorization=authorization,
            customer_id=current_user.id,
        )

    if not base_url or not instances:
        return MyAgentsSummaryResponse(instances=instances)
```

**NFR patterns embedded (copy exactly):**
```python
# Pattern A — call existing Plant route via the existing _plant_get_json helper.
# No new CP DB writes. No new router. Just a new helper function.
# _plant_get_json already handles 4xx → HTTPException and 5xx → RuntimeError.
# Wrap the call in try/except so fallback never crashes the endpoint.
```

**Acceptance criteria:**
- [ ] `GET /cp/my-agents/summary` returns 2 instances for yogesh's JWT when `cp_subscriptions_simple._by_id` is empty
- [ ] Each instance has non-empty `subscription_id`, `agent_id`, `hired_instance_id`, `nickname`
- [ ] When Plant is unreachable the endpoint still returns 200 with `instances: []` (the fallback swallows errors)
- [ ] When `cp_subscriptions_simple` already has records, the fallback is NOT called (existing behaviour preserved)

**Test to write:** `src/CP/BackEnd/tests/unit/test_my_agents_summary_fallback.py`
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_fallback_returns_instances_when_subscriptions_empty(async_client):
    """Fallback path synthesises summaries from Plant hired-agents data."""
    plant_response = {
        "customer_id": "cust-001",
        "instances": [
            {
                "hired_instance_id": "INST-YOGESH-01",
                "subscription_id": "SUB-YOGESH-01",
                "agent_id": "AGT-TRD-001",
                "agent_type_id": "trading.share_trader.v1",
                "nickname": "Share Trader",
                "configured": False,
                "goals_completed": False,
                "trial_status": "active",
            }
        ]
    }
    with patch("api.my_agents_summary._plant_get_json", new=AsyncMock(return_value=plant_response)), \
         patch("api.my_agents_summary._list_subscriptions", new=AsyncMock(return_value=[])), \
         patch("api.my_agents_summary._plant_base_url", return_value="http://plant"):
        resp = async_client.get(...)  # inject JWT headers as appropriate
```

**Test command:** `cd src/CP/BackEnd && docker-compose -f docker-compose.test.yml run cp-test pytest tests/unit/test_my_agents_summary_fallback.py -v`

---

## Iteration 2 — CP FrontEnd: Ghost skeleton on error + Discover nav fix

**Scope:** My Agents shows YouTube-style ghost cards instead of blank error text when the API is down. "Discover" is a first-class nav item.
**Lane:** A — pure frontend wiring, no new backend endpoints
**⏱ Estimated:** 45m | **Come back:** Start + 1h
**Epics:** E2

### Dependency Map

```
E2-S1  (independent of E2-S2 — can be done in either order)
E2-S2  (independent of E2-S1)
```

---

### Epic E2: Portal shows graceful offline state and correct navigation

**Branch:** `feat/CP-MY-AGENTS-1-it2-e2`
**User story:** As a customer, when the My Agents API returns an error I see two ghost agent card skeletons instead of an empty broken screen; and "Discover" appears in the correct position in the sidebar menu.

---

#### Story E2-S1: CP FrontEnd — YouTube-style ghost skeleton on My Agents error

**BLOCKED UNTIL:** none
**Estimated time:** 25 min
**Branch:** `feat/CP-MY-AGENTS-1-it2-e2`
**CP BackEnd pattern:** N/A — FE-only

**Context (read before acting):**
- `MyAgents.tsx` (the outer `MyAgents` component starting around line 1720) has this render logic when `error` is set and loading is false:
  - It currently renders **nothing** in the agent selector area. The `AgentSelector` receives an empty `instances` array and shows an italic "no agents" message.
  - The goal: show 2 `ListItemSkeleton` ghost cards + a soft dismissible error chip above them so the layout doesn't look broken.
- `ListItemSkeleton` is already imported in `MyAgents.tsx` via `import { ListItemSkeleton, PageSkeleton } from '../../components/SkeletonLoaders'`.

**Files to read first:**
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` lines 1720–1780 (the outer MyAgents component opening + loading state render)
2. `src/CP/FrontEnd/src/components/SkeletonLoaders.tsx` lines 207–237 (ListItemSkeleton definition)

**What to build:**
In the outer `MyAgents` component, find the JSX block that renders the `AgentSelector`. It looks like:

```tsx
  // around line 1721 — the outer wrapper div
  return (
    <div className="my-agents-page">
```

Locate the section where `loading` and `error` are checked. Currently that area is:
```tsx
      {loading ? (
        <Card style={{ marginTop: '1.5rem', padding: '2.5rem' }}>
          <PageSkeleton variant="list" />
        </Card>
      ) : error ? (
        <Card style={{ marginTop: '1.5rem', padding: '2.5rem' }}>
          <FeedbackMessage intent="error" message={error} />
        </Card>
      ) : (
        /* agent selector + content */
      )}
```

Replace the `error ?` branch so it shows skeleton ghost cards + a soft error chip below them:
```tsx
      ) : error ? (
        <div style={{ marginTop: '1.5rem' }}>
          {/* Soft error chip — non-blocking, tells user what went wrong */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 0.75rem',
              borderRadius: '8px',
              border: '1px solid var(--colorPaletteRedBorder1)',
              background: 'var(--colorPaletteRedBackground1)',
              marginBottom: '1rem',
              fontSize: '0.875rem',
            }}
          >
            <span>⚠️</span>
            <span style={{ flex: 1 }}>{error}</span>
          </div>
          {/* Ghost skeleton cards — same layout as real agent cards */}
          <ListItemSkeleton count={2} />
        </div>
```

> Note: the exact JSX to find and replace might differ slightly from the excerpt above. Read the file first and find the correct lines before editing.

**Acceptance criteria:**
- [ ] When the API returns an error (simulate by setting `REACT_APP_API_BASE` to a bad URL or throwing in a test), Two skeleton ghost cards appear in the main content area
- [ ] A soft yellow/red error chip appears above the ghost cards with the error message
- [ ] No raw uncaught crash — the page remains stable
- [ ] `npm run test:run` passes with no new TypeScript errors

**Test command:** `cd src/CP/FrontEnd && npm run test:run`

---

#### Story E2-S2: CP FrontEnd — move Discover into menuItems in AuthenticatedPortal.tsx

**BLOCKED UNTIL:** none
**Estimated time:** 15 min
**Branch:** `feat/CP-MY-AGENTS-1-it2-e2` (same branch, same PR as E2-S1)
**CP BackEnd pattern:** N/A — FE-only

**Context (read before acting):**
- `AuthenticatedPortal.tsx` currently defines `menuItems` as an array of 7 objects, then has a **separate hardcoded `<button>` below the `menuItems.map()` loop** for Discover. This means Discover is always last, cannot be reordered with the others, and has duplicated className logic.

**Files to read first:**
1. `src/CP/FrontEnd/src/pages/AuthenticatedPortal.tsx` lines 38–140 (full menuItems array + sidebar render)

**What to build:**

Step 1 — Add `discover` to the `menuItems` array. The type `Page` already includes `'discover'`. Insert Discover between Goals and Deliverables (after `my-agents`, before `goals`):

Find:
```tsx
    { id: 'command-centre', icon: <Home20Regular />, label: 'Command Centre' },
    { id: 'my-agents', icon: <Bot20Regular />, label: 'My Agents' },
    { id: 'goals', icon: <Target20Regular />, label: 'Goals' },
```

Replace with:
```tsx
    { id: 'command-centre', icon: <Home20Regular />, label: 'Command Centre' },
    { id: 'my-agents', icon: <Bot20Regular />, label: 'My Agents' },
    { id: 'discover', icon: <Search20Regular />, label: 'Discover' },
    { id: 'goals', icon: <Target20Regular />, label: 'Goals' },
```

Step 2 — Delete the duplicate hardcoded Discover button. Find and remove exactly this block from the sidebar JSX:
```tsx
            {/* Discover is embedded within the portal shell */}
            <button
              className={`sidebar-item ${currentPage === 'discover' ? 'active' : ''}`}
              onClick={() => setCurrentPage('discover')}
              aria-label="Discover agents"
            >
              <span className="sidebar-icon"><Search20Regular /></span>
              {!sidebarCollapsed && <span className="sidebar-label">Discover</span>}
            </button>
```

The `Search20Regular` icon is already imported. No new imports needed.

**Acceptance criteria:**
- [ ] Sidebar renders exactly 8 nav items (Command Centre, My Agents, Discover, Goals, Deliverables, Inbox, Subscriptions & Billing, Profile & Settings) — one source of truth via `menuItems`
- [ ] Clicking Discover navigates to the Discover page (same as before)
- [ ] No duplicate Discover button exists in the DOM
- [ ] `npm run test:run` passes

**Test command:** `cd src/CP/FrontEnd && npm run test:run`
