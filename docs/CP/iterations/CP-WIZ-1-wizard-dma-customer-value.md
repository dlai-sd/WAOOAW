# CP-WIZ-1 — Customer Portal: Wizard & DMA Customer-Value Wiring

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | CP-WIZ-1 |
| Feature area | Customer Portal — DMA Wizard UX + PLANT-DMA-2 Feature Surfacing |
| Created | 2026-04-01 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/plant/iterations/PLANT-DMA-2-real-publishing-engine.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 4 |
| Total stories | 10 |

---

## Objective — Why This Plan Exists

PLANT-DMA-2 ("Real Publishing Engine") built four backend capabilities:
1. **YouTubeAdapter** — real publishing adapter (registered but scheduler bypasses it)
2. **PublishReceiptModel** — persists publish attempt records (API route exists at `/api/v1/publish-receipts/{id}`)
3. **Content Analytics** — `get_content_recommendations()` computes top dimensions, best posting hours, engagement rate (`src/Plant/BackEnd/services/content_analytics.py`, 110 lines, 4 passing unit tests)
4. **BrandVoiceModel** — stores customer tone/vocabulary for content generation (`src/Plant/BackEnd/models/brand_voice.py` + `brand_voice_service.py` with `get_brand_voice()` / `upsert_brand_voice()`)

**The problem:** None of these features are visible to the customer in the CP application.

| Gap | Root Cause | Impact | Fix in this plan |
|---|---|---|---|
| Content analytics is dead code | No Plant API route, no CP proxy, no UI | Customer sees raw stats only — no actionable insights, no "wow" moment | E1-S1 + E1-S2 + E2-S1 |
| Brand voice is dead code | No Plant API route, no CP proxy, no UI | Agent generates generic content — customer can't teach agent their tone | E1-S1 + E1-S2 + E2-S2 |
| Profile fields in wrong place | Wizard step 5 asks `brand_name`, `location`, `timezone`, `primary_language` — these are customer identity, not per-agent config | Customer re-enters same data for every agent they hire; feels like busywork | E3-S1 + E3-S2 |
| 5 "Unavailable" platforms shown | Instagram, Facebook, LinkedIn, WhatsApp, X cards render with "Unavailable" badge | Signals broken product — customer thinks platform is half-built | E4-S1 |
| Performance tab shows raw metrics only | `PerformancePanel` calls `listPerformanceStats()` but never calls content analytics | Customer sees numbers without context — "23 posts" means nothing without "best hours: 9 AM, 2 PM" | E2-S1 |
| Publish receipts not surfaced | CP reads `payload.publish_receipt` embedded in deliverable but never calls dedicated `/api/v1/publish-receipts/{id}` endpoint | Customer can't see publish confirmation, success/failure, or platform links | E4-S2 |

**Revenue impact:** The customer hired an agent and sees a wizard that asks redundant questions, raw numbers without insight, and zero evidence the agent published anything. There is no reason to pay. This plan wires PLANT-DMA-2's backend features through to the customer's screen so the agent demonstrably earns its keep.

**Reference:** Full PLANT-DMA-2 plan at `docs/plant/iterations/PLANT-DMA-2-real-publishing-engine.md`

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

## PM Review Checklist (tick every box before publishing)

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list based on the tech stack that iteration uses (Python/FastAPI, React Native, Terraform, Docker, GCP, etc.)
- [x] Epic titles name customer outcomes, not technical actions ("Customer sees X" not "Add X to API")
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before frontend (S2)
- [x] Iteration count minimized for PR-only delivery (default 1-2; Iteration 3 only if explicitly justified)
- [x] Related backend/frontend work kept in the same iteration unless merge-to-main is a hard dependency
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — Expose content analytics + brand voice: Plant API routes, CP Backend proxies, CP Frontend services | 2 | 5 | 5h | 2026-04-02 10:00 IST |
| 2 | Lane A/B — Profile field migration, hide unavailable platforms, wire performance insights + publish receipts to UI | 2 | 5 | 5h | 2026-04-03 10:00 IST |

**Estimate basis:** FE wiring = 30 min | New BE endpoint = 45 min | Full-stack = 90 min | Docker test = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

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
7. Go away. Come back at: **2026-04-02 10:00 IST**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior TypeScript / React / Fluent UI v9 engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-WIZ-1-wizard-dma-customer-value.md
YOUR SCOPE: Iteration 1 only — Epics [E1, E2]. Do not touch Iteration 2 content.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this order: [E1] → [E2]
6. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(cp-wiz-1): iteration 1 — [summary]
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior TypeScript / React / Fluent UI v9 engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-WIZ-1-wizard-dma-customer-value.md
YOUR SCOPE: Iteration 2 only — Epics [E3, E4]. Do not touch Iteration 1.
TIME BUDGET: 5h.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(cp-wiz-1): iteration 1 — [summary]
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Respect backend-before-frontend ordering in the Dependency Map.
4. When all epics are docker-tested, open the iteration PR. Post URL. HALT.
```

**Come back at:** 2026-04-03 10:00 IST

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `src/CP/BackEnd/` `src/Plant/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy engineer |
| `src/CP/FrontEnd/` | Senior TypeScript / React / Fluent UI v9 engineer |
| `infrastructure/` `cloud/terraform/` | Senior Terraform / GCP Cloud Run engineer |

---

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
git checkout main && git pull
git checkout -b feat/cp-wiz-1-it1-e1
git commit --allow-empty -m "chore(cp-wiz-1): start iteration 1"
git push origin feat/cp-wiz-1-it1-e1

gh pr create \
  --base main \
  --head feat/cp-wiz-1-it1-e1 \
  --draft \
  --title "tracking: CP-WIZ-1 Iteration 1 — in progress" \
  --body "## tracking: CP-WIZ-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Plant API routes for content analytics + brand voice
- [ ] [E1-S2] CP Backend proxy routes for content analytics + brand voice
- [ ] [E1-S3] CP Frontend services for content analytics + brand voice
- [ ] [E2-S1] Wire Performance tab to show content recommendations
- [ ] [E2-S2] Add brand voice editor to wizard step 5

_Live updates posted as comments below ↓_"
```

---

### Rule 1 — Branch discipline
One epic = one branch: `feat/cp-wiz-1-itN-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside your scope: add a TODO comment and move on.

**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table.

**Missing iteration HALT rule**: Before writing any code, verify your assigned iteration section exists:
```bash
grep -n "## Iteration N" docs/CP/iterations/CP-WIZ-1-wizard-dma-customer-value.md
```

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat(cp-wiz-1): [story title]"
git push origin feat/cp-wiz-1-itN-eN

git add docs/CP/iterations/CP-WIZ-1-wizard-dma-customer-value.md
git commit -m "docs(cp-wiz-1): mark [story-id] done"
git push origin feat/cp-wiz-1-itN-eN

gh pr comment \
  $(gh pr list --head feat/cp-wiz-1-it1-e1 --json number -q '.[0].number') \
  --body "✅ **[story-id] done** — $(git rev-parse --short HEAD)
Files changed: [list]
Tests: [T1 ✅ T2 ✅ ...]
Next: [next-story-id]"
```

### Rule 5 — Docker integration test after every epic
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/cp-wiz-1-itN-eN
gh pr create \
  --base main \
  --head feat/cp-wiz-1-itN-eN \
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
git checkout -b feat/cp-wiz-1-itN
git merge --no-ff feat/cp-wiz-1-itN-e1 feat/cp-wiz-1-itN-e2
git push origin feat/cp-wiz-1-itN

gh pr create \
  --base main \
  --head feat/cp-wiz-1-itN \
  --title "feat(cp-wiz-1): iteration N — [one-line summary]" \
  --body "## CP-WIZ-1 Iteration N

### Stories completed
[paste tracking table rows for this iteration]

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] PIIMaskingFilter on all new loggers
- [ ] circuit_breaker on PlantGatewayClient and all external HTTP calls
- [ ] No env-specific values in Dockerfile or code
- [ ] FE: loading + error + empty states on all data-fetching components
- [ ] Tests >= 80% coverage on new BE code"
```

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(cp-wiz-1): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | `waooaw_router()` factory — never bare `APIRouter` | CI ruff ban — PR blocked |
| 2 | `get_read_db_session()` on all GET routes | Primary DB overloaded |
| 3 | `PIIMaskingFilter()` on every logger | PII incident |
| 4 | `@circuit_breaker(service=...)` on every external HTTP call | Cascading failure |
| 5 | `dependencies=[Depends(get_correlation_id), Depends(get_audit_log)]` on FastAPI() | Audit trail missing |
| 6 | `X-Correlation-ID` header on every outgoing HTTP request | Trace broken |
| 7 | Loading + error + empty states on every FE data-fetching component | Silent failures |
| 8 | Tests >= 80% coverage on all new BE code | PR blocked by CI |
| 9 | Never embed env-specific values in Dockerfile or code | Image cannot be promoted |
| 10 | PR always `--base main` — never target an intermediate branch | Work never ships |
| 11 | CP BackEnd is a thin proxy only — no business logic | Architecture violation |
| 12 | Pattern A: call existing `/cp/*` via `gatewayRequestJson` — no new BE file | |
| 13 | Pattern B: missing `/cp/*` route → new `api/cp_<resource>.py` with `waooaw_router` + `PlantGatewayClient` | |
| 14 | Pattern C: existing `/v1/*` Plant endpoint → call via `gatewayRequestJson` from FE — no new BE file | |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer gets AI-powered content insights | Plant API routes for content analytics + brand voice | 🔴 Not Started | — |
| E1-S2 | 1 | Customer gets AI-powered content insights | CP Backend proxy routes for analytics + brand voice | 🔴 Not Started | — |
| E1-S3 | 1 | Customer gets AI-powered content insights | CP Frontend services for analytics + brand voice | 🔴 Not Started | — |
| E2-S1 | 1 | Customer sees actionable recommendations in Performance tab | Wire Performance tab to show content recommendations | 🔴 Not Started | — |
| E2-S2 | 1 | Customer sees actionable recommendations in Performance tab | Add brand voice editor to wizard step 5 | 🔴 Not Started | — |
| E3-S1 | 2 | Customer profile owns identity fields — wizard pre-fills | Extend profile model with location, timezone, primary_language | 🔴 Not Started | — |
| E3-S2 | 2 | Customer profile owns identity fields — wizard pre-fills | Wizard pre-fills from profile and saves back | 🔴 Not Started | — |
| E4-S1 | 2 | Customer sees polished, honest platform status | Hide unsupported platforms from wizard step 3 | 🔴 Not Started | — |
| E4-S2 | 2 | Customer sees polished, honest platform status | Wire publish receipts to Deliverables review panel | 🔴 Not Started | — |
| E4-S3 | 2 | Customer sees polished, honest platform status | Hide exchange credentials section for DMA agents | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Customer gets AI-powered content insights and brand voice

**Scope:** After this iteration, the Performance tab shows content recommendations (best posting hours, top dimensions, engagement rate) alongside raw stats, and the wizard lets customers define their brand voice so the agent generates on-brand content.
**Lane:** B — new Plant API routes + CP Backend proxies + CP Frontend services + UI wiring
**⏱ Estimated:** 5h | **Come back:** 2026-04-02 10:00 IST
**Epics:** E1, E2

### Dependency Map (Iteration 1)

```
E1-S1 (Plant API routes) ──► E1-S2 (CP Backend proxies) ──► E1-S3 (CP Frontend services)
                                                                       │
                                                              ┌────────┴────────┐
                                                              ▼                 ▼
                                                          E2-S1 (Performance)  E2-S2 (Brand voice UI)
```

---

### Epic E1: Customer gets AI-powered content insights

**Branch:** `feat/cp-wiz-1-it1-e1`
**User story:** As a customer, I can see content recommendations and manage my brand voice, so that I understand what the agent is doing and can guide its content style.

---

#### Story E1-S1: Plant API routes for content analytics + brand voice

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/cp-wiz-1-it1-e1`
**CP BackEnd pattern:** N/A — this is Plant Backend work

**What to do (self-contained — read this card, then act):**
> `src/Plant/BackEnd/services/content_analytics.py` has `get_content_recommendations(hired_instance_id, db, lookback_days=30)` returning a `ContentRecommendation` pydantic model — but NO API route exposes it. Similarly, `src/Plant/BackEnd/services/brand_voice_service.py` has `get_brand_voice(customer_id, db)` and `upsert_brand_voice(customer_id, data, db)` — but NO API route exposes them.
>
> Create two new API route files:
> 1. `src/Plant/BackEnd/api/v1/content_analytics.py` — GET `/v1/hired-agents/{hired_instance_id}/content-recommendations`
> 2. `src/Plant/BackEnd/api/v1/brand_voice.py` — GET `/v1/brand-voice/{customer_id}` and PUT `/v1/brand-voice/{customer_id}`
>
> Register both routers in `src/Plant/BackEnd/main.py`.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/services/content_analytics.py` | 1–110 | `ContentRecommendation` model, `get_content_recommendations()` signature |
| `src/Plant/BackEnd/services/brand_voice_service.py` | 1–60 | `get_brand_voice()`, `upsert_brand_voice()` signatures, return types |
| `src/Plant/BackEnd/api/v1/performance_stats.py` | 1–40 | Pattern for `waooaw_router`, imports, `get_read_db_session` usage |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/content_analytics.py` | create | New route file. One GET endpoint: `/hired-agents/{hired_instance_id}/content-recommendations`. Uses `get_read_db_session`. Returns `ContentRecommendation` from service. |
| `src/Plant/BackEnd/api/v1/brand_voice.py` | create | New route file. GET `/brand-voice/{customer_id}` returns brand voice or 404. PUT `/brand-voice/{customer_id}` upserts brand voice. GET uses `get_read_db_session`, PUT uses `get_db_session`. |
| `src/Plant/BackEnd/main.py` | modify | Add `from api.v1.content_analytics import router as content_analytics_router` and `from api.v1.brand_voice import router as brand_voice_router`. Add `app.include_router(content_analytics_router, prefix="/api/v1")` and `app.include_router(brand_voice_router, prefix="/api/v1")`. |

**Code patterns to copy exactly** (no other file reads needed for these):

```python
# Pattern — Plant Backend API route (copy exactly, replace [] placeholders):
"""[Resource] API — CP-WIZ-1 E1-S1"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, get_read_db_session
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router

router = waooaw_router(prefix="/[resource-path]", tags=["[tag]"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())
```

**Acceptance criteria (binary pass/fail only):**
1. GET `/api/v1/hired-agents/{hired_instance_id}/content-recommendations` returns 200 with `ContentRecommendation` JSON when performance data exists
2. GET `/api/v1/hired-agents/{hired_instance_id}/content-recommendations` returns 200 with empty recommendation (not 404) when no data exists
3. GET `/api/v1/brand-voice/{customer_id}` returns 200 with brand voice JSON when exists, 404 when not
4. PUT `/api/v1/brand-voice/{customer_id}` creates brand voice on first call, updates on subsequent calls, returns 200
5. All GET routes use `get_read_db_session()`

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/test_content_analytics_api.py` | Mock `get_content_recommendations` returning populated `ContentRecommendation` | Response 200, JSON has `top_dimensions`, `best_posting_hours`, `recommendation_text` |
| E1-S1-T2 | same | Mock `get_content_recommendations` returning empty recommendation | Response 200, `total_posts_analyzed` is 0 |
| E1-S1-T3 | `src/Plant/BackEnd/tests/test_brand_voice_api.py` | Mock `get_brand_voice` returning None | Response 404 |
| E1-S1-T4 | same | Mock `upsert_brand_voice` returning model | Response 200, correct fields |

**Test command:**
```bash
cd src/Plant/BackEnd && python -m pytest tests/test_content_analytics_api.py tests/test_brand_voice_api.py -v
```

**Commit message:** `feat(cp-wiz-1): Plant API routes for content analytics + brand voice`

**Done signal:** `"E1-S1 done. Changed: api/v1/content_analytics.py (created), api/v1/brand_voice.py (created), main.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S2: CP Backend proxy routes for content analytics + brand voice

**BLOCKED UNTIL:** E1-S1 committed to `feat/cp-wiz-1-it1-e1`
**Estimated time:** 45 min
**Branch:** `feat/cp-wiz-1-it1-e1` (same branch, continue from E1-S1)
**CP BackEnd pattern:** B — create new `api/cp_content_analytics.py` and `api/cp_brand_voice.py`

**What to do:**
> CP Backend has no proxy routes for content analytics or brand voice. Create two thin proxy files that forward requests to the Plant API routes created in E1-S1.
>
> 1. `src/CP/BackEnd/api/cp_content_analytics.py` — proxies GET `/cp/content-recommendations/{hired_instance_id}` → Plant `/api/v1/hired-agents/{hired_instance_id}/content-recommendations`
> 2. `src/CP/BackEnd/api/cp_brand_voice.py` — proxies GET and PUT `/cp/brand-voice` → Plant `/api/v1/brand-voice/{customer_id}` (customer_id injected from auth)
>
> Register both routers in `src/CP/BackEnd/main.py`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/api/marketing_review.py` | 1–60 | `PlantGatewayClient` proxy pattern, `_forward_headers`, `get_plant_gateway_client` |
| `src/CP/BackEnd/api/cp_profile.py` | 1–50 | `waooaw_router` usage, `get_current_user` dependency, `AuditLogger` |
| `src/CP/BackEnd/main.py` | 1–80 | Router include pattern, import order |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/BackEnd/api/cp_content_analytics.py` | create | Proxy GET `/cp/content-recommendations/{hired_instance_id}` → Plant. Use `PlantGatewayClient.request_json(method="GET", path=f"/api/v1/hired-agents/{hired_instance_id}/content-recommendations", headers=_forward_headers(request))`. |
| `src/CP/BackEnd/api/cp_brand_voice.py` | create | Proxy GET `/cp/brand-voice` → Plant GET `/api/v1/brand-voice/{customer_id}` and PUT `/cp/brand-voice` → Plant PUT `/api/v1/brand-voice/{customer_id}`. Inject `customer_id` from `current_user.id`. |
| `src/CP/BackEnd/main.py` | modify | Add imports and `app.include_router()` for both new routers. |

**Code patterns to copy exactly:**

```python
# CP Backend thin proxy pattern (copy exactly):
"""CP [Resource] proxy — CP-WIZ-1 E1-S2"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

from api.auth.dependencies import get_current_user
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.user import User
from services.audit_dependency import AuditLogger, get_audit_logger
from services.plant_gateway_client import PlantGatewayClient

router = waooaw_router(prefix="/cp/[resource]", tags=["cp-[resource]"])

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


def _get_plant_client() -> PlantGatewayClient:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise HTTPException(status_code=503, detail="PLANT_GATEWAY_URL not configured")
    return PlantGatewayClient(base_url=base_url)


def _forward_headers(request: Request) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if auth := request.headers.get("authorization"):
        headers["Authorization"] = auth
    if cid := request.headers.get("x-correlation-id"):
        headers["X-Correlation-ID"] = cid
    return headers
```

**Acceptance criteria:**
1. GET `/cp/content-recommendations/{hired_instance_id}` returns 200 proxying Plant response
2. GET `/cp/brand-voice` returns brand voice for authenticated user's customer_id
3. PUT `/cp/brand-voice` with JSON body upserts brand voice for authenticated user
4. All routes require authentication (`get_current_user` dependency)
5. 503 returned when `PLANT_GATEWAY_URL` is not set

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/CP/BackEnd/tests/test_cp_content_analytics.py` | Mock PlantGatewayClient returns 200 with recommendation JSON | Response 200, fields match |
| E1-S2-T2 | same | Mock PlantGatewayClient returns 500 | Response 503 |
| E1-S2-T3 | `src/CP/BackEnd/tests/test_cp_brand_voice.py` | Mock PlantGatewayClient GET returns 200 | Response 200, correct shape |
| E1-S2-T4 | same | Mock PlantGatewayClient PUT returns 200 | Response 200, audit logged |

**Test command:**
```bash
cd src/CP/BackEnd && python -m pytest tests/test_cp_content_analytics.py tests/test_cp_brand_voice.py -v
```

**Commit message:** `feat(cp-wiz-1): CP Backend proxy routes for content analytics + brand voice`

**Done signal:** `"E1-S2 done. Changed: api/cp_content_analytics.py (created), api/cp_brand_voice.py (created), main.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S3: CP Frontend services for content analytics + brand voice

**BLOCKED UNTIL:** E1-S2 committed to `feat/cp-wiz-1-it1-e1`
**Estimated time:** 30 min
**Branch:** `feat/cp-wiz-1-it1-e1` (same branch, continue from E1-S2)
**CP BackEnd pattern:** N/A — frontend only

**What to do:**
> Create two new service files that call the CP Backend proxy routes from E1-S2. These services will be consumed by E2-S1 (Performance tab) and E2-S2 (brand voice editor).
>
> 1. `src/CP/FrontEnd/src/services/contentAnalytics.service.ts` — `getContentRecommendations(hiredInstanceId)` calls GET `/cp/content-recommendations/{id}`
> 2. `src/CP/FrontEnd/src/services/brandVoice.service.ts` — `getBrandVoice()` calls GET `/cp/brand-voice`, `updateBrandVoice(data)` calls PUT `/cp/brand-voice`

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/services/performanceStats.service.ts` | 1–40 | Existing service pattern: import, interface, export function, `gatewayRequestJson` usage |
| `src/CP/FrontEnd/src/services/gatewayApiClient.ts` | 1–40 | `gatewayRequestJson` signature, `GatewayApiError` type |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/services/contentAnalytics.service.ts` | create | Export `ContentRecommendation` interface matching Plant model fields: `top_dimensions: string[]`, `best_posting_hours: number[]`, `avg_engagement_rate: number`, `total_posts_analyzed: number`, `recommendation_text: string`. Export `getContentRecommendations(hiredInstanceId: string): Promise<ContentRecommendation>`. |
| `src/CP/FrontEnd/src/services/brandVoice.service.ts` | create | Export `BrandVoiceData` interface: `tone_keywords: string[]`, `vocabulary_preferences: string[]`, `messaging_patterns: string[]`, `example_phrases: string[]`, `voice_description: string`. Export `getBrandVoice(): Promise<BrandVoiceData>` and `updateBrandVoice(data: Partial<BrandVoiceData>): Promise<BrandVoiceData>`. |

**Code patterns to copy exactly:**

```typescript
// CP Frontend service pattern (copy exactly, replace [] placeholders):
import { gatewayRequestJson } from './gatewayApiClient'

export interface [TypeName] {
  [field]: [type]
}

export async function get[Resource](id: string): Promise<[TypeName]> {
  return gatewayRequestJson<[TypeName]>(
    `/cp/[resource]/${encodeURIComponent(id)}`,
    { method: 'GET' }
  )
}
```

**Acceptance criteria:**
1. `contentAnalytics.service.ts` exports `ContentRecommendation` type and `getContentRecommendations` function
2. `brandVoice.service.ts` exports `BrandVoiceData` type, `getBrandVoice`, and `updateBrandVoice` functions
3. Both use `gatewayRequestJson` from `gatewayApiClient`
4. TypeScript compiles without errors

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S3-T1 | `src/CP/FrontEnd/src/__tests__/contentAnalytics.service.test.ts` | Mock `gatewayRequestJson` returns recommendation object | Function returns correct type |
| E1-S3-T2 | `src/CP/FrontEnd/src/__tests__/brandVoice.service.test.ts` | Mock `gatewayRequestJson` returns brand voice | `getBrandVoice()` returns correct type, `updateBrandVoice()` sends PUT |

**Test command:**
```bash
cd src/CP/FrontEnd && npx jest src/__tests__/contentAnalytics.service.test.ts src/__tests__/brandVoice.service.test.ts --no-coverage
```

**Commit message:** `feat(cp-wiz-1): CP Frontend services for content analytics + brand voice`

**Done signal:** `"E1-S3 done. Changed: contentAnalytics.service.ts (created), brandVoice.service.ts (created). Tests: T1 ✅ T2 ✅"`

---

### Epic E2: Customer sees actionable recommendations in Performance tab

**Branch:** `feat/cp-wiz-1-it1-e2`
**User story:** As a customer, I can see AI-generated content recommendations alongside raw performance stats and define my brand voice in the wizard, so that I know the agent is learning and improving.

---

#### Story E2-S1: Wire Performance tab to show content recommendations

**BLOCKED UNTIL:** E1-S3 committed (services must exist)
**Estimated time:** 45 min
**Branch:** `feat/cp-wiz-1-it1-e2`
**CP BackEnd pattern:** N/A — frontend wiring only

**What to do:**
> `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` lines 1730-1810 contain `PerformancePanel` which calls `listPerformanceStats()` and shows raw metric values grouped by `metric_key`. Below the raw stats section, add a new "Content Insights" section that calls `getContentRecommendations(hiredInstanceId)` from `contentAnalytics.service.ts` and displays:
> - Best posting hours (formatted as "9 AM, 2 PM, 6 PM")
> - Top content dimensions (as tags/badges)
> - Average engagement rate (as percentage)
> - Recommendation text (as a blockquote)
>
> Show `<Spinner />` while loading, error message on failure, "No insights yet — the agent needs more data" when `total_posts_analyzed < 3`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1730–1810 | `PerformancePanel` component: state vars, useEffect, render logic |
| `src/CP/FrontEnd/src/services/contentAnalytics.service.ts` | 1–30 | `ContentRecommendation` interface, `getContentRecommendations` signature |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Inside `PerformancePanel` after the existing stats render: add `useState` for `ContentRecommendation | null`, `useEffect` calling `getContentRecommendations(hiredInstanceId)`, render "Content Insights" section below existing stats. Import `getContentRecommendations` and `ContentRecommendation` from `contentAnalytics.service`. |

**Code patterns to copy exactly:**

```typescript
// 3-state data fetching (mandatory):
const [recommendations, setRecommendations] = useState<ContentRecommendation | null>(null)
const [recsLoading, setRecsLoading] = useState(true)
const [recsError, setRecsError] = useState<string | null>(null)

useEffect(() => {
  if (!hiredInstanceId) return
  let cancelled = false
  getContentRecommendations(hiredInstanceId)
    .then(data => { if (!cancelled) setRecommendations(data) })
    .catch(() => { if (!cancelled) setRecsError('Failed to load content insights.') })
    .finally(() => { if (!cancelled) setRecsLoading(false) })
  return () => { cancelled = true }
}, [hiredInstanceId])
```

**Acceptance criteria:**
1. Performance tab shows "Content Insights" section below raw stats
2. Best posting hours display as formatted times (e.g. "9 AM, 2 PM")
3. Top dimensions display as tag/badge elements
4. Engagement rate shows as percentage (e.g. "4.2%")
5. When `total_posts_analyzed < 3`, shows "No insights yet — the agent needs more data"
6. Loading spinner shown while fetching
7. Error message shown on API failure

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/CP/FrontEnd/src/__tests__/PerformancePanel.test.tsx` | Mock `getContentRecommendations` returns full recommendation | "Content Insights" heading in DOM, hours and dimensions rendered |
| E2-S1-T2 | same | Mock returns `total_posts_analyzed: 1` | "No insights yet" message in DOM |
| E2-S1-T3 | same | Mock rejects | Error message in DOM |

**Test command:**
```bash
cd src/CP/FrontEnd && npx jest src/__tests__/PerformancePanel.test.tsx --no-coverage
```

**Commit message:** `feat(cp-wiz-1): wire Performance tab to show content recommendations`

**Done signal:** `"E2-S1 done. Changed: MyAgents.tsx. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E2-S2: Add brand voice editor to wizard step 5

**BLOCKED UNTIL:** E1-S3 committed (brand voice service must exist)
**Estimated time:** 45 min
**Branch:** `feat/cp-wiz-1-it1-e2` (same branch, continue from E2-S1)
**CP BackEnd pattern:** N/A — frontend wiring only

**What to do:**
> `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` step 5 ("theme") at lines 1490-1520 has the "Business brief" form with brand_name, location, timezone, etc. Below the existing business brief section, add a "Brand Voice" collapsible section that:
> 1. On step load, calls `getBrandVoice()` from `brandVoice.service.ts` and populates fields
> 2. Shows editable fields for: `voice_description` (textarea), `tone_keywords` (comma-separated input), `example_phrases` (textarea, one per line)
> 3. On step save (when user clicks Continue), calls `updateBrandVoice()` with the edited data
>
> This teaches the agent how the customer talks, enabling personalized content generation.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 1490–1550 | Step 5 form layout, existing Input/Textarea usage pattern, `readOnly` prop |
| `src/CP/FrontEnd/src/services/brandVoice.service.ts` | 1–40 | `BrandVoiceData` interface, `getBrandVoice`, `updateBrandVoice` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Add `useState` for brand voice fields (`voiceDescription`, `toneKeywords`, `examplePhrases`). Add `useEffect` on step 5 entry that calls `getBrandVoice()`. Add brand voice form section after the existing "Business brief" div, before the offerings textarea. On `handleContinue` for step 5, call `updateBrandVoice()`. |

**Code patterns to copy exactly:**

```typescript
// Brand voice state (add near other step-5 state vars ~line 315):
const [voiceDescription, setVoiceDescription] = useState('')
const [toneKeywords, setToneKeywords] = useState('')
const [examplePhrases, setExamplePhrases] = useState('')
const [brandVoiceLoading, setBrandVoiceLoading] = useState(false)

// Load brand voice on step 5 entry:
useEffect(() => {
  if (currentStep !== 4) return  // step index 4 = "theme" step
  let cancelled = false
  setBrandVoiceLoading(true)
  getBrandVoice()
    .then(bv => {
      if (cancelled) return
      setVoiceDescription(bv.voice_description || '')
      setToneKeywords((bv.tone_keywords || []).join(', '))
      setExamplePhrases((bv.example_phrases || []).join('\n'))
    })
    .catch(() => {})  // Brand voice not set yet — fields stay empty
    .finally(() => { if (!cancelled) setBrandVoiceLoading(false) })
  return () => { cancelled = true }
}, [currentStep])
```

**Acceptance criteria:**
1. Step 5 shows "Brand Voice" section below "Business brief"
2. Voice description textarea is populated from API when brand voice exists
3. Tone keywords show as comma-separated string
4. Example phrases show as newline-separated string
5. On Continue, `updateBrandVoice()` is called with parsed data
6. Fields are disabled when `readOnly` is true
7. Empty fields are acceptable (brand voice is optional)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/CP/FrontEnd/src/__tests__/BrandVoiceSection.test.tsx` | Mock `getBrandVoice` returns data, render step 5 | Voice description textarea populated, tone keywords shown |
| E2-S2-T2 | same | Mock `getBrandVoice` rejects (404) | Fields are empty, no error banner (brand voice is optional) |
| E2-S2-T3 | same | Fill fields, trigger continue | `updateBrandVoice` called with parsed arrays |

**Test command:**
```bash
cd src/CP/FrontEnd && npx jest src/__tests__/BrandVoiceSection.test.tsx --no-coverage
```

**Commit message:** `feat(cp-wiz-1): add brand voice editor to wizard step 5`

**Done signal:** `"E2-S2 done. Changed: DigitalMarketingActivationWizard.tsx. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

