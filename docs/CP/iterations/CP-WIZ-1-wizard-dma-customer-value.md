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
| Total stories | 11 |

---

## Objective — Why This Plan Exists

PLANT-DMA-2 ("Real Publishing Engine") built four backend capabilities:
1. **YouTubeAdapter** — real publishing adapter (registered and wired via `default_engine` in `marketing_scheduler.py`)
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
| Strategy approval is blind | `isThemeApproved` gate (wizard line 468) blocks content generation until customer approves — but no preview of the strategy is shown before the approve button | Trust gap — customer approves unknown content; undermines "try before hire" confidence | E2-S3 |

> ⚠️ **Known limitation — in-memory profile store:** `UserStore` in `src/CP/BackEnd/api/auth/user_store.py` persists profile data in a `Dict[str, User]` — server restart loses all profile fields added by E3-S1. This is pre-existing tech debt (not introduced by this plan). A follow-up plan should migrate to persistent storage.

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
| 1 | Lane B — Expose content analytics + brand voice + strategy preview: Plant API routes, CP Backend proxies, CP Frontend services, strategy preview gate | 2 | 6 | 5.5h | 2026-04-02 10:30 IST |
| 2 | Lane A/B — Profile field migration, hide unavailable platforms, wire performance insights + publish receipts to UI | 2 | 5 | 5h | 2026-04-03 10:00 IST |

**Estimate basis:** FE wiring = 30 min | New BE endpoint = 45 min | Full-stack = 90 min | Docker test = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

---

## How to Launch Each Iteration

> Launch these tasks from the GitHub repository Agents tab.
> These tasks must not assume shell, git, gh, or docker access is available.
> Use the GitHub task branch and PR flow provided by the execution surface.

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. If the UI exposes repository agents, select **platform-engineer**; otherwise use the default coding agent
5. Copy the block below and paste it into the task
6. Start the run
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

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

EXECUTION ORDER:
1. Read the "Agent Execution Rules" section in this plan file.
2. Read the "Iteration 1" section in this plan file.
3. Read nothing else before starting.
4. Work on the GitHub task branch created for this run. Do not assume terminal checkout or manual branch creation.
5. Execute Epics in this order: [E1] → [E2]
6. Add or update the tests listed in each story before moving on.
7. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
8. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:** confirm on GitHub that the Iteration 1 PR is merged to `main` before launching.

**Steps to launch:** same as Iteration 1 (GitHub repository → Agents tab)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior TypeScript / React / Fluent UI v9 engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-WIZ-1-wizard-dma-customer-value.md
YOUR SCOPE: Iteration 2 only — Epics [E3, E4]. Do not touch Iteration 1.
TIME BUDGET: 5h.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

PREREQUISITE CHECK (do before anything else):
  Confirm from GitHub that the Iteration 1 PR for this plan is merged to `main`.
  If you cannot verify that merge from the available GitHub context: post "Blocked: Iteration 1 merge to main could not be verified." and HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
2. Work on the GitHub task branch created for this run. Do not assume terminal checkout or manual branch creation.
3. Respect backend-before-frontend ordering in the Dependency Map.
4. Add or update the tests listed in each story before moving on.
5. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
6. Open or update the iteration PR to `main`, post URL, and HALT.
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

### Rule 0 — Use the GitHub task branch and open the iteration PR early

- Keep the full iteration on the GitHub task branch created for this run.
- If the UI lets you choose a branch name, prefer `feat/cp-wiz-1-itN-[scope]-[run-id]`.
- Open a draft PR to `main` as soon as the execution surface allows it, and keep updating that same PR through the iteration.
- Use the Tracking Table in this plan as the source of truth for story status updates.

---

### Rule 1 — Branch discipline
One iteration = one GitHub task branch and one PR.
Treat every `Branch:` value in story cards as a logical label only; on the GitHub Agents tab, keep the full iteration on the single branch created for the run.
Never push or merge directly to `main`.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside your scope: add a TODO comment and move on.

**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table.

**Missing iteration HALT rule**: Before writing any code, verify your assigned iteration section exists in this plan file.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.
If this execution surface exposes test execution, run the story's listed command or the narrowest equivalent.
If not, add the tests anyway and note that execution is deferred to CI or local follow-up.

### Rule 4 — Save progress after every story
- Update this plan file's Tracking Table: change the story status to Done or Blocked.
- Save code and plan updates to the GitHub task branch for this run.
- If the PR already exists, add a concise progress update in the PR description or comments with files changed, tests added/run, and the next story.

### Rule 5 — Validate after every epic
- Prefer the narrowest relevant automated validation for the files you changed.
- If GitHub Agents exposes execution tools, run the relevant test command and record the result.
- If execution tools are unavailable, state clearly that validation is deferred to CI or local follow-up and continue.
- After validation, add `**Epic complete ✅**` under the epic heading if the epic is complete.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
- Mark the blocked story as `🚫 Blocked` in the Tracking Table.
- Open or update a draft PR titled `WIP: [story-id] — blocked` if PR controls are available.
- Include the exact blocker, the exact error message, and 1-2 attempted fixes.
- Post the PR URL if available. Otherwise post the blocker in the GitHub agent thread. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
- Use the same GitHub task branch for the final iteration PR to `main`.
- Title format: `feat(cp-wiz-1): iteration N — [one-line summary]`.
- PR body must include completed stories for this iteration, validation status or deferral note, and the NFR checklist.
- [ ] Tests >= 80% coverage on new BE code"
```

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(cp-wiz-1): [epic-id] — [epic title]" && git push origin HEAD
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
| E2-S3 | 1 | Customer sees actionable recommendations in Performance tab | Render strategy preview before approval gate | 🔴 Not Started | — |
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
                                                              ┌────────┴───────────────────────────┐
                                                              │                           │
                                                              ▼                           ▼
                                                          E2-S1 (Performance)  E2-S2 (Brand voice UI)
                                                                                        │
                                                                                        ▼
                                                                               E2-S3 (Strategy preview)
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
> 2. `src/Plant/BackEnd/api/v1/brand_voice.py` — GET `/v1/brand-voice/me` and PUT `/v1/brand-voice/me` (customer_id derived from JWT/auth context — prevents IDOR)
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
| `src/Plant/BackEnd/api/v1/brand_voice.py` | create | New route file. GET `/brand-voice/me` derives `customer_id` from JWT auth context (prevents IDOR — never accept customer_id as path param). PUT `/brand-voice/me` upserts brand voice. GET uses `get_read_db_session`, PUT uses `get_db_session`. |
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
3. GET `/api/v1/brand-voice/me` derives customer_id from JWT, returns 200 with brand voice JSON when exists, 404 when not
4. PUT `/api/v1/brand-voice/me` derives customer_id from JWT, creates brand voice on first call, updates on subsequent calls, returns 200
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
> 2. `src/CP/BackEnd/api/cp_brand_voice.py` — proxies GET and PUT `/cp/brand-voice` → Plant `/api/v1/brand-voice/me` (Plant derives customer_id from JWT — IDOR-safe)
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
| `src/CP/BackEnd/api/cp_brand_voice.py` | create | Proxy GET `/cp/brand-voice` → Plant GET `/api/v1/brand-voice/me` and PUT `/cp/brand-voice` → Plant PUT `/api/v1/brand-voice/me`. Forward auth token — Plant derives customer_id from JWT internally (IDOR-safe). |
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
5. When `total_posts_analyzed === 0` (trial cold-start), shows contextual guidance: "Your agent is analyzing your content — first insights appear within 24–48 hours"
6. When `0 < total_posts_analyzed < 3`, shows "Building insights — ${total_posts_analyzed} posts analyzed so far, need at least 3 for recommendations"
7. Loading spinner shown while fetching
8. Error message shown on API failure

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

#### Story E2-S3: Render strategy preview before approval gate

**BLOCKED UNTIL:** none (independent — reads existing wizard state)
**Estimated time:** 30 min
**Branch:** `feat/cp-wiz-1-it1-e2` (same branch, continue from E2-S2)
**CP BackEnd pattern:** N/A — frontend only

**What to do:**
> `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` line ~468 has an `isThemeApproved` gate that blocks content generation until the customer clicks "Approve". The problem: the customer cannot see what they are approving. The wizard stores strategy data in `nextActivation?.workspace.strategyWorkshop` (messages array) and `nextActivation?.workspace.strategySummary` (text summary), but neither is rendered before the approve button.
>
> Add a "Strategy Preview" panel directly above the approve button that renders:
> 1. The `strategySummary` text (if it exists) as a formatted summary block
> 2. Key strategy messages from `strategyWorkshop.messages` (last 3-5 messages, formatted as a conversation thread)
> 3. A clear label: "Review your content strategy before approving"
>
> This gives the customer transparency into what the agent planned before they commit.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 940–970 | Approval gate message rendering, `isThemeApproved` usage, approve button location |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 460–480 | `isThemeApproved` state variable, how it's toggled |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Above the existing "Approve" button in the strategy approval section (~line 960), add a `StrategyPreviewPanel` inline component that reads `nextActivation?.workspace.strategySummary` and `nextActivation?.workspace.strategyWorkshop?.messages`. Render summary as a styled blockquote, messages as a conversation thread (role + content), and show "No strategy generated yet" if both are empty. |

**Code patterns to copy exactly:**

```typescript
// Strategy preview (add directly above the Approve button):
{!isThemeApproved && (
  <div style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #333', borderRadius: '0.75rem', background: '#1a1a1a' }}>
    <h4 style={{ margin: '0 0 0.5rem', color: '#00f2fe' }}>Review Your Content Strategy</h4>
    {nextActivation?.workspace?.strategySummary ? (
      <blockquote style={{ borderLeft: '3px solid #667eea', paddingLeft: '1rem', margin: '0.5rem 0', color: '#ccc' }}>
        {nextActivation.workspace.strategySummary}
      </blockquote>
    ) : (
      <p style={{ color: '#666' }}>No strategy generated yet — the agent will create one after you provide your business context.</p>
    )}
    {(nextActivation?.workspace?.strategyWorkshop?.messages ?? []).slice(-5).map((msg: any, i: number) => (
      <div key={i} style={{ margin: '0.25rem 0', color: msg.role === 'assistant' ? '#00f2fe' : '#ccc' }}>
        <strong>{msg.role === 'assistant' ? 'Agent' : 'You'}:</strong> {msg.content}
      </div>
    ))}
  </div>
)}
```

**Acceptance criteria:**
1. Strategy preview panel is visible above the Approve button when `isThemeApproved === false`
2. `strategySummary` renders as a blockquote when present
3. Last 5 strategy workshop messages render as a conversation thread
4. When both `strategySummary` and messages are empty/absent, shows "No strategy generated yet" placeholder
5. Panel disappears after customer approves (when `isThemeApproved === true`)
6. No TypeScript errors

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S3-T1 | `src/CP/FrontEnd/src/__tests__/StrategyPreview.test.tsx` | Mock `nextActivation.workspace.strategySummary = "Focus on video content..."`, `isThemeApproved = false` | Blockquote with summary text in DOM, "Review Your Content Strategy" heading visible |
| E2-S3-T2 | same | Mock empty workspace (no strategySummary, no messages), `isThemeApproved = false` | "No strategy generated yet" placeholder in DOM |
| E2-S3-T3 | same | Mock `isThemeApproved = true` | Strategy preview panel NOT in DOM |

**Test command:**
```bash
cd src/CP/FrontEnd && npx jest src/__tests__/StrategyPreview.test.tsx --no-coverage
```

**Commit message:** `feat(cp-wiz-1): render strategy preview before approval gate`

**Done signal:** `"E2-S3 done. Changed: DigitalMarketingActivationWizard.tsx. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

## Iteration 2 — Customer profile owns identity + polished platform status

**Scope:** After this iteration, brand_name/location/timezone/language live in Customer Profile (wizard pre-fills from profile), unsupported platforms are hidden, publish receipts are visible in deliverable review, and exchange credentials stop showing for DMA agents.
**Lane:** B — profile model extension + frontend wiring
**⏱ Estimated:** 5h | **Come back:** 2026-04-03 10:00 IST
**Prerequisite:** Iteration 1 PR merged to `main`
**Epics:** E3, E4

### Dependency Map (Iteration 2)

```
E3-S1 (profile model) ──► E3-S2 (wizard pre-fill from profile)
E4-S1 (hide platforms)     (independent)
E4-S2 (publish receipts)   (independent)
E4-S3 (hide exchange creds)(independent)
```

---

### Epic E3: Customer profile owns identity fields — wizard pre-fills

**Branch:** `feat/cp-wiz-1-it2-e3`
**User story:** As a customer, I enter my brand name, location, timezone, and language once in my profile, and every agent I hire pre-fills from it — no repetitive data entry in the wizard.

---

#### Story E3-S1: Extend profile model with location, timezone, primary_language

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 45 min
**Branch:** `feat/cp-wiz-1-it2-e3`
**CP BackEnd pattern:** N/A — modifying existing CP Backend profile route (Pattern A)

**What to do:**
> `src/CP/BackEnd/models/user.py` lines 30-38 define the `User` model with fields up to `industry`. Add three new optional fields: `location: Optional[str]`, `timezone: Optional[str]`, `primary_language: Optional[str]`.
>
> `src/CP/BackEnd/api/cp_profile.py` lines 57-66 define `ProfileResponse` — add the three new fields. Lines 69-76 define `ProfileUpdate` — add the three new fields as optional.
>
> `src/CP/FrontEnd/src/services/profile.service.ts` — add the three fields to `ProfileData` interface and `ProfileUpdatePayload` interface.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/models/user.py` | 1–40 | `User` model fields, `model_config` |
| `src/CP/BackEnd/api/cp_profile.py` | 55–95 | `ProfileResponse`, `ProfileUpdate`, `_to_response` mapper |
| `src/CP/FrontEnd/src/services/profile.service.ts` | 1–40 | `ProfileData`, `ProfileUpdatePayload` interfaces |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/BackEnd/models/user.py` | modify | After `industry: Optional[str] = None` (line 37), add: `location: Optional[str] = None`, `timezone: Optional[str] = None`, `primary_language: Optional[str] = None` |
| `src/CP/BackEnd/api/cp_profile.py` | modify | Add `location`, `timezone`, `primary_language` as `Optional[str] = None` to both `ProfileResponse` and `ProfileUpdate`. Add them to `_to_response` mapper. |
| `src/CP/FrontEnd/src/services/profile.service.ts` | modify | Add `location?: string`, `timezone?: string`, `primary_language?: string` to `ProfileData` interface. Add same to `ProfileUpdatePayload`. |

**Code patterns to copy exactly:**

```python
# User model fields to add (after industry line):
    location: Optional[str] = None
    timezone: Optional[str] = None
    primary_language: Optional[str] = None
```

```python
# ProfileResponse / ProfileUpdate fields to add:
    location: Optional[str] = None
    timezone: Optional[str] = None
    primary_language: Optional[str] = None
```

```python
# _to_response mapper — add these lines:
        location=user.location,
        timezone=user.timezone,
        primary_language=user.primary_language,
```

**Acceptance criteria:**
1. GET `/cp/profile` response includes `location`, `timezone`, `primary_language` fields (null when not set)
2. PATCH `/cp/profile` accepts `location`, `timezone`, `primary_language` and persists them
3. `ProfileData` TypeScript interface includes the three new fields as optional strings
4. Existing profile tests still pass

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/CP/BackEnd/tests/test_cp_profile.py` | PATCH with `{"location": "Mumbai", "timezone": "Asia/Kolkata", "primary_language": "Hindi"}` | Response 200, all three fields returned |
| E3-S1-T2 | same | GET after PATCH | Response includes updated location, timezone, primary_language |

**Test command:**
```bash
cd src/CP/BackEnd && python -m pytest tests/test_cp_profile.py -v
```

**Commit message:** `feat(cp-wiz-1): extend profile model with location, timezone, primary_language`

**Done signal:** `"E3-S1 done. Changed: models/user.py, api/cp_profile.py, profile.service.ts. Tests: T1 ✅ T2 ✅"`

---

#### Story E3-S2: Wizard pre-fills from profile and saves back

**BLOCKED UNTIL:** E3-S1 committed to `feat/cp-wiz-1-it2-e3`
**Estimated time:** 45 min
**Branch:** `feat/cp-wiz-1-it2-e3` (same branch, continue from E3-S1)
**CP BackEnd pattern:** N/A — frontend only

**What to do:**
> `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` lines 530-550 populate state from `nextActivation?.workspace.*`. Currently, `brandName`, `location`, `primaryLanguage`, `timezone` are only set from workspace data. Add a `useEffect` that on wizard mount calls `getProfile()` from `profile.service.ts`. If the workspace fields are empty but profile has values, pre-fill from profile. On step 5 save (handleContinue), if user changed these fields, also call `updateProfile()` to sync back.
>
> This eliminates repeat data entry — the customer enters these fields once, every agent benefits.
>
> **Mapping note:** `profile.business_name` maps to wizard `brandName` — no new profile field is needed for brand_name. The wizard state variable `brandName` reads from and writes to `profile.business_name`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 530–560 | `loadState` effect that populates brand_name, location, timezone from workspace |
| `src/CP/FrontEnd/src/services/profile.service.ts` | 1–40 | `getProfile()`, `updateProfile()`, `ProfileData` with location/timezone/primary_language |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Import `getProfile`, `updateProfile` from `profile.service`. Add `useEffect` on mount that calls `getProfile()` and stores result in `profileRef` (useRef). In the existing loadState effect (~line 534), after setting state from workspace, check: if `brandName` is empty and `profile.business_name` exists, set `brandName` from it. Same for `location`, `timezone`, `primary_language`. In handleContinue for step 5 (~line 699), if location/timezone/primary_language changed, call `updateProfile({location, timezone, primary_language})`. |

**Code patterns to copy exactly:**

```typescript
// Profile pre-fill (add near top of component, after other useEffects):
import { getProfile, updateProfile, ProfileData } from '../services/profile.service'

const profileRef = useRef<ProfileData | null>(null)

useEffect(() => {
  getProfile()
    .then(p => { profileRef.current = p })
    .catch(() => {})  // profile load failure is non-blocking
}, [])

// In loadState effect, after setBrandName(normalizeText(nextActivation?.workspace.brand_name)):
const p = profileRef.current
if (!nextActivation?.workspace.brand_name && p?.business_name) setBrandName(p.business_name)
if (!nextActivation?.workspace.location && p?.location) setLocation(p.location)
if (!nextActivation?.workspace.timezone && p?.timezone) setTimezone(p.timezone)
if (!nextActivation?.workspace.primary_language && p?.primary_language) setPrimaryLanguage(p.primary_language)
```

**Acceptance criteria:**
1. When wizard opens and workspace has no brand_name but profile has business_name, brand_name field is pre-filled
2. When workspace has no location/timezone/language but profile has them, fields are pre-filled
3. When workspace already has values, workspace values take precedence (not overwritten)
4. On step 5 Continue, profile is updated with new location/timezone/language values
5. Profile API failure does not block wizard from loading

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S2-T1 | `src/CP/FrontEnd/src/__tests__/WizardProfilePrefill.test.tsx` | Mock `getProfile` returns `{business_name: "TestCo", location: "Delhi"}`, workspace is empty | Brand name shows "TestCo", location shows "Delhi" |
| E3-S2-T2 | same | Mock `getProfile` returns `{location: "Delhi"}`, workspace has `location: "Mumbai"` | Location shows "Mumbai" (workspace wins) |
| E3-S2-T3 | same | Trigger step 5 continue with changed location | `updateProfile` called with new location |

**Test command:**
```bash
cd src/CP/FrontEnd && npx jest src/__tests__/WizardProfilePrefill.test.tsx --no-coverage
```

**Commit message:** `feat(cp-wiz-1): wizard pre-fills from profile and saves back`

**Done signal:** `"E3-S2 done. Changed: DigitalMarketingActivationWizard.tsx. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

### Epic E4: Customer sees polished, honest platform status

**Branch:** `feat/cp-wiz-1-it2-e4`
**User story:** As a customer, I see only platforms the agent actually supports, I can view publish receipts proving the agent published content, and I don't see irrelevant exchange credential forms for my marketing agent.

---

#### Story E4-S1: Hide unsupported platforms from wizard step 3

**BLOCKED UNTIL:** none (independent of E3)
**Estimated time:** 30 min
**Branch:** `feat/cp-wiz-1-it2-e4`
**CP BackEnd pattern:** N/A — frontend only

**What to do:**
> `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` step 3 ("platforms") renders platform cards including Instagram, Facebook, LinkedIn, WhatsApp, and X — all showing "Unavailable" badges. These signal a broken product. Filter the platform list to only show platforms the agent actually supports (currently only `youtube`). Hide unsupported platforms entirely rather than showing them as unavailable.
>
> Find the platforms rendering section in step 3 and wrap it with a filter: only render platforms where `available === true` or where the platform key is in the agent's supported platforms list.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 1200–1350 | Step 3 ("platforms") rendering: platform card array, `.map()` call, "Unavailable" badge rendering |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | In the platforms step rendering section, add `.filter(p => p.available !== false)` before the `.map()` that renders platform cards. This hides platforms marked unavailable. If the platform list is a constant array, filter out entries where `available: false` or where key is not in `['youtube']`. |

**Code patterns to copy exactly:**

```typescript
// Filter pattern — add before .map() on platform cards:
.filter(platform => platform.available !== false)
```

**Acceptance criteria:**
1. Step 3 does NOT show Instagram, Facebook, LinkedIn, WhatsApp, or X cards
2. Step 3 shows YouTube card (available platform)
3. If all platforms are filtered out, show a message: "No platforms available yet — YouTube is coming soon" (edge case safety)
4. No "Unavailable" badge text appears anywhere in step 3

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/CP/FrontEnd/src/__tests__/WizardPlatforms.test.tsx` | Render step 3 with default platform list | "Unavailable" text NOT in DOM, YouTube card IS in DOM |
| E4-S1-T2 | same | Render step 3 | Instagram, Facebook, LinkedIn, WhatsApp, X text NOT rendered as platform cards |

**Test command:**
```bash
cd src/CP/FrontEnd && npx jest src/__tests__/WizardPlatforms.test.tsx --no-coverage
```

**Commit message:** `feat(cp-wiz-1): hide unsupported platforms from wizard step 3`

**Done signal:** `"E4-S1 done. Changed: DigitalMarketingActivationWizard.tsx. Tests: T1 ✅ T2 ✅"`

---

#### Story E4-S2: Wire publish receipts to Deliverables review panel

**BLOCKED UNTIL:** none (independent)
**Estimated time:** 45 min
**Branch:** `feat/cp-wiz-1-it2-e4` (same branch, continue from E4-S1)
**CP BackEnd pattern:** B — create new `api/cp_publish_receipts.py` proxy route (no existing CP proxy for publish receipts — grep confirmed zero matches)

**What to do:**
> Plant Backend already has `/api/v1/publish-receipts/{hired_instance_id}` returning publish receipt records. CP Frontend never calls this endpoint and **no CP Backend proxy exists** (grep confirmed). Create:
> 1. `src/CP/BackEnd/api/cp_publish_receipts.py` — thin proxy: GET `/cp/publish-receipts/{hired_instance_id}` → Plant GET `/api/v1/publish-receipts/{hired_instance_id}`. Use `PlantGatewayClient` + `_forward_headers` pattern (same as E1-S2). Register in `src/CP/BackEnd/main.py`.
> 2. `src/CP/FrontEnd/src/services/publishReceipts.service.ts` — FE service calling the new CP proxy.
> 3. Add a "Publish History" section to `MyAgents.tsx` showing publish date, platform, status badge, platform URL.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/api/marketing_review.py` | 1–60 | `PlantGatewayClient` proxy pattern, `_forward_headers`, `get_plant_gateway_client` — copy this pattern for cp_publish_receipts.py |
| `src/CP/FrontEnd/src/services/hiredAgentDeliverables.service.ts` | 1–60 | Existing service pattern, `Deliverable` type, `listHiredAgentDeliverables` |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1730–1760 | Where PerformancePanel is rendered — publish receipts section should go nearby |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/BackEnd/api/cp_publish_receipts.py` | create | Thin proxy: GET `/cp/publish-receipts/{hired_instance_id}` → Plant GET `/api/v1/publish-receipts/{hired_instance_id}`. Use `waooaw_router(prefix="/cp/publish-receipts")`, `PlantGatewayClient`, `_forward_headers`, `get_current_user`. Same pattern as `cp_content_analytics.py` from E1-S2. |
| `src/CP/BackEnd/main.py` | modify | Add import and `app.include_router()` for `cp_publish_receipts` router. || `src/CP/FrontEnd/src/services/publishReceipts.service.ts` | create | Export `PublishReceipt` interface: `id: string`, `hired_instance_id: string`, `platform_key: string`, `published_at: string`, `status: string`, `platform_url?: string`, `error_message?: string`. Export `listPublishReceipts(hiredInstanceId: string): Promise<PublishReceipt[]>` calling GET `/cp/publish-receipts/${id}` via `gatewayRequestJson`. |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | After the `PerformancePanel` component, add a `PublishHistoryPanel` component that fetches `listPublishReceipts(hiredInstanceId)` and renders a list of publish receipts with date, platform, status badge (green for success, red for failed), and platform URL as a link. |

**Code patterns to copy exactly:**

```typescript
// Publish receipts service (copy exactly):
import { gatewayRequestJson } from './gatewayApiClient'

export interface PublishReceipt {
  id: string
  hired_instance_id: string
  platform_key: string
  published_at: string
  status: string
  platform_url?: string
  error_message?: string
}

export async function listPublishReceipts(hiredInstanceId: string): Promise<PublishReceipt[]> {
  const data = await gatewayRequestJson<unknown>(
    `/cp/publish-receipts/${encodeURIComponent(hiredInstanceId)}`,
    { method: 'GET' }
  )
  if (Array.isArray(data)) return data as PublishReceipt[]
  if (Array.isArray((data as any)?.items)) return (data as any).items
  return []
}
```

```python
# CP Backend publish receipts proxy (copy exactly — same pattern as E1-S2):
"""CP Publish Receipts proxy — CP-WIZ-1 E4-S2"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request

from api.auth.dependencies import get_current_user
from core.logging import PiiMaskingFilter
from core.routing import waooaw_router
from models.user import User
from services.plant_gateway_client import PlantGatewayClient

router = waooaw_router(prefix="/cp/publish-receipts", tags=["cp-publish-receipts"])

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


@router.get("/{hired_instance_id}")
async def list_publish_receipts(
    hired_instance_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    client = _get_plant_client()
    resp = await client.request_json(
        method="GET",
        path=f"/api/v1/publish-receipts/{hired_instance_id}",
        headers=_forward_headers(request),
    )
    if resp.status_code >= 400:
        raise HTTPException(status_code=503, detail="Plant Backend error")
    return resp.json_body
```

**Acceptance criteria:**
1. New `cp_publish_receipts.py` backend proxy created with `waooaw_router`, `PlantGatewayClient`, `get_current_user` dependency
2. New `publishReceipts.service.ts` exports `PublishReceipt` type and `listPublishReceipts` function
3. MyAgents page shows "Publish History" section for DMA agents
4. Each receipt shows formatted date, platform name, status badge, and clickable URL
5. Empty state: "No publish history yet" when array is empty
6. Error state: error message shown when API fails
7. Loading state: spinner while fetching

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S2-T1 | `src/CP/BackEnd/tests/test_cp_publish_receipts.py` | Mock PlantGatewayClient returns 200 with receipt list | Response 200, fields match |
| E4-S2-T2 | same | Mock PlantGatewayClient returns 500 | Response 503 |
| E4-S2-T3 | `src/CP/FrontEnd/src/__tests__/PublishHistoryPanel.test.tsx` | Mock `listPublishReceipts` returns 2 receipts (1 success, 1 failed) | Both rendered, success has green badge, failed has red badge |
| E4-S2-T4 | same | Mock returns empty array | "No publish history yet" in DOM |
| E4-S2-T5 | same | Mock rejects | Error message in DOM |

**Test command:**
```bash
cd src/CP/BackEnd && python -m pytest tests/test_cp_publish_receipts.py -v
cd src/CP/FrontEnd && npx jest src/__tests__/PublishHistoryPanel.test.tsx --no-coverage
```

**Commit message:** `feat(cp-wiz-1): wire publish receipts to Deliverables review panel`

**Done signal:** `"E4-S2 done. Changed: cp_publish_receipts.py (created), main.py, publishReceipts.service.ts (created), MyAgents.tsx. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅"`

---

#### Story E4-S3: Hide exchange credentials section for DMA agents

**BLOCKED UNTIL:** none (independent)
**Estimated time:** 30 min
**Branch:** `feat/cp-wiz-1-it2-e4` (same branch, continue from E4-S2)
**CP BackEnd pattern:** N/A — frontend only

**What to do:**
> `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` lines 821-892 render an "Exchange credentials" form section for trading agents. This section currently shows for ALL agent types, including DMA (digital marketing activation) agents. DMA agents don't use exchange credentials — showing these fields confuses customers and wastes their time.
>
> Add a conditional check: only render the exchange credentials section when the agent's `agent_type` or `skill_type` indicates a trading/exchange agent. For DMA agents (identified by `agent_type === 'digital_marketing'` or by checking the hired instance's skill type), hide this section entirely.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 820–900 | Exchange credentials section — conditional rendering, how agent type is accessed |
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 240–260 | ConfigureAgentPanel props — how `instance` is passed, what fields it has |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Wrap the exchange credentials section (lines ~821-892) in a conditional: `if (instance.agent_type === 'trading' || instance.agent_type === 'exchange')` — only render for trading agents. If `agent_type` is not available, check `instance.skill_type` or `instance.industry`. For DMA/marketing agents, do NOT render this section. |

**Code patterns to copy exactly:**

```typescript
// Conditional rendering — wrap exchange credentials section:
{(instance.agent_type === 'trading' || instance.agent_type === 'exchange') && (
  // ... existing exchange credentials JSX ...
)}
```

**Acceptance criteria:**
1. Exchange credentials section does NOT render for DMA/marketing agents
2. Exchange credentials section STILL renders for trading/exchange agents
3. No visual change for trading agent users
4. No TypeScript errors

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S3-T1 | `src/CP/FrontEnd/src/__tests__/ExchangeCredentialsVisibility.test.tsx` | Render ConfigureAgentPanel with DMA agent instance | Exchange credentials section NOT in DOM |
| E4-S3-T2 | same | Render with trading agent instance | Exchange credentials section IS in DOM |

**Test command:**
```bash
cd src/CP/FrontEnd && npx jest src/__tests__/ExchangeCredentialsVisibility.test.tsx --no-coverage
```

**Commit message:** `feat(cp-wiz-1): hide exchange credentials section for DMA agents`

**Done signal:** `"E4-S3 done. Changed: MyAgents.tsx. Tests: T1 ✅ T2 ✅"`

