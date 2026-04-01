# PLANT-DMA-2 — Real YouTube Publishing Engine + Analytics Feedback

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-DMA-2` |
| Feature area | Plant BackEnd — Publisher Engine unification, real YouTube publishing, analytics feedback loop |
| Created | 2026-04-01 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | DMA gap analysis (session context) + `PLANT-DMA-1` existing plan |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 4 |
| Total stories | 8 |

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

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list
- [x] Epic titles name customer outcomes, not technical actions
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
- [x] Iteration count minimized for PR-only delivery (2 iterations)
- [x] Related backend/frontend work kept in same iteration
- [x] No placeholders remain

---

## Vision Intake (confirmed)

1. **Area:** Plant BackEnd — publisher engine, integrations, scheduler, analytics
2. **User outcome:** A hired DMA agent publishes real YouTube content through a unified publisher engine (not simulated), and analytics from published content feed back into future content generation quality.
3. **Out of scope:** Other social platforms (Twitter, Instagram, LinkedIn), CP/PP/mobile UI changes, image/video generation pipelines, ad management, SEO automation, competitor monitoring.
4. **Lane:** B — new backend code required (adapter, analytics service, schema changes).
5. **Timeline:** 2 iterations.

---

## Architecture Decisions

### Problem statement

The current DMA has two critical architectural gaps:

1. **Dual-engine disconnect**: `marketing_scheduler.py` (lines 76–86) calls `YouTubeClient.post_text()` directly, bypassing the `PublisherEngine` entirely. Meanwhile, `PublisherEngine` only registers `SimulatedAdapter` — it never touches real YouTube. This means eligibility checks, receipt tracking, and the adapter abstraction are all bypassed in production.

2. **No analytics feedback**: `PerformanceStatModel` stores daily metrics (impressions, clicks, engagement_rate) in JSONB but nothing reads those metrics to improve future content. The content creator generates content with zero knowledge of what previously performed well.

### Solution shape

**Iteration 1** solves gap 1: Create a `YouTubeAdapter` that wraps the existing `YouTubeClient` and registers it in `PublisherEngine`. Rewire `marketing_scheduler.py` to use `PublisherEngine` instead of calling `YouTubeClient` directly. Persist publish receipts to a new DB table.

**Iteration 2** solves gap 2: Create an analytics feedback service that reads `performance_stats`, computes top-performing content patterns, and injects recommendations into the content creator's prompt. Add a brand voice model so content stays consistent.

### Key invariants

- `PublisherEngine` is the **only** path to external publishing. No service may call `YouTubeClient` (or any future social client) directly.
- YouTube eligibility checks (approval_id, credential_ref, public_release) remain in `PublisherEngine._check_publish_eligibility()` — the adapter does not duplicate them.
- Analytics recommendations are advisory — content creator retains final control of output.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Unified YouTube publishing — adapter, engine wiring, scheduler rewire, receipt persistence | E1, E2 | 4 | 5h | 2026-04-01 17:00 UTC |
| 2 | Analytics feedback loop — performance reader, content recommendations, brand voice | E3, E4 | 4 | 5h | 2026-04-02 00:00 UTC |

**Estimate basis:** New adapter/service = 45–90 min | Schema + model = 45 min | Rewire existing code = 45 min | Add 20% buffer for zero-cost model context loading.

### PR-Overhead Optimization Rules

- 2 iterations maximum.
- Each iteration: 4 stories / ~5 hours of agent work.
- Vertical slices within same iteration — no extra merge gates.
- Deployment via `waooaw deploy` workflow after final merged iteration.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check:**
```bash
git status && git log --oneline -3
# Must show: clean tree on main.
```

**Steps to launch:**
1. Open VS Code
2. Open Copilot Chat: `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac)
3. Click the model dropdown → select **Agent mode**
4. Click `+` to start a new agent session
5. Type `@` → select **platform-engineer** from the dropdown
6. Copy the block below and paste → press **Enter**
7. Go away. Come back at: **2026-04-01 17:00 UTC**

**Iteration 1 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python/FastAPI engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-DMA-2-real-publishing-engine.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2. Do not touch Iteration 2 content.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this order: E1 → E2
6. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(plant-dma-2): iteration 1 — unified YouTube publishing
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python/FastAPI engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-DMA-2-real-publishing-engine.md
YOUR SCOPE: Iteration 2 only — Epics E3, E4. Do not touch Iteration 1 content.
TIME BUDGET: 5h.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(plant-dma-2): iteration 1 — unified YouTube publishing
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. When all epics are docker-tested, open the iteration PR. Post URL. HALT.
```

**Come back at:** 2026-04-02 00:00 UTC

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with:

> *"Acting as a Senior Python/FastAPI engineer, I will [what] by [approach]."*

### Rule 0 — Open tracking draft PR first

```bash
git checkout main && git pull
git checkout -b feat/plant-dma-2-it1-e1
git commit --allow-empty -m "chore(plant-dma-2): start iteration 1"
git push origin feat/plant-dma-2-it1-e1

gh pr create \
  --base main \
  --head feat/plant-dma-2-it1-e1 \
  --draft \
  --title "tracking: PLANT-DMA-2 Iteration 1 — in progress" \
  --body "## tracking: PLANT-DMA-2 Iteration 1

Subscribe for progress notifications.

### Stories
- [ ] [E1-S1] Create YouTubeAdapter wrapping YouTubeClient
- [ ] [E1-S2] Register YouTubeAdapter and rewire scheduler
- [ ] [E2-S1] Create publish_receipt DB model
- [ ] [E2-S2] Persist receipts from PublisherEngine and add query endpoint

_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/plant-dma-2-itN-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing.

### Rule 4 — Commit + push after every story
```bash
git add -A
git commit -m "feat(plant-dma-2): [story title]"
git push origin feat/plant-dma-2-itN-eN
```

### Rule 5 — Docker integration test after every epic
```bash
docker compose -f docker-compose.test.yml run plant-test pytest --cov=app --cov-fail-under=80 -v
```

### Rule 6 — STUCK PROTOCOL (3 failures = stop)
```bash
git add -A && git commit -m "WIP: plant-dma-2 [story-id] blocked — [error]"
git push origin feat/plant-dma-2-itN-eN
gh pr create --base main --head feat/plant-dma-2-itN-eN --draft \
  --title "WIP: PLANT-DMA-2 [story-id] — blocked" \
  --body "Blocked on: [test name]\nError: [exact message]"
```
Post the PR URL. **HALT.**

### Rule 7 — Iteration PR (after ALL epics complete)
```bash
git checkout main && git pull
git checkout -b feat/plant-dma-2-itN
git merge --no-ff feat/plant-dma-2-itN-e1 feat/plant-dma-2-itN-e2
git push origin feat/plant-dma-2-itN

gh pr create --base main --head feat/plant-dma-2-itN \
  --title "feat(plant-dma-2): iteration N — [summary]" \
  --body "## PLANT-DMA-2 Iteration N\n\n[stories completed]\n\nDocker: all tests pass ✅"
```

### CHECKPOINT RULE
After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(plant-dma-2): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## NFR Quick Reference (PM review only — agents use inline snippets)

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | `waooaw_router()` — never bare `APIRouter` | CI blocked |
| 2 | `get_read_db_session()` on GET routes | Primary DB overloaded |
| 3 | `PIIMaskingFilter()` on every logger | PII incident |
| 4 | `@circuit_breaker(service=...)` on external HTTP calls | Cascading failure |
| 5 | `dependencies=[Depends(get_correlation_id), Depends(get_audit_log)]` on FastAPI() | Audit trail missing |
| 8 | Tests >= 80% coverage on new BE code | PR blocked |
| 9 | Never embed env-specific values in code | Image promotion broken |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Unified YouTube Publishing | Create YouTubeAdapter wrapping YouTubeClient | 🔴 Not Started | — |
| E1-S2 | 1 | Unified YouTube Publishing | Register adapter and rewire scheduler | 🔴 Not Started | — |
| E2-S1 | 1 | Publish Receipt Persistence | Create publish_receipt DB model | 🔴 Not Started | — |
| E2-S2 | 1 | Publish Receipt Persistence | Persist receipts and add query endpoint | 🔴 Not Started | — |
| E3-S1 | 2 | Analytics-Driven Content | Performance analytics reader service | 🔴 Not Started | — |
| E3-S2 | 2 | Analytics-Driven Content | Wire analytics into content creator prompts | 🔴 Not Started | — |
| E4-S1 | 2 | Brand Voice Consistency | Brand voice model and storage | 🔴 Not Started | — |
| E4-S2 | 2 | Brand Voice Consistency | Apply brand voice to content generation | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Unified YouTube Publishing Engine

**Scope:** DMA publishes real YouTube content through the unified PublisherEngine — no more direct YouTubeClient calls from scheduler.
**Lane:** B — new adapter file, interface change, scheduler rewire, new DB model
**⏱ Estimated:** 5h | **Come back:** 2026-04-01 17:00 UTC
**Epics:** E1, E2

### Dependency Map (Iteration 1)

```
E1-S1 ──► E1-S2    (same branch, S2 starts after S1 committed + pushed)
E2-S1 ──► E2-S2    (same branch, S2 starts after S1 committed + pushed)
E2 depends on E1 being committed (YouTubeAdapter must exist before receipt persistence)
```

---

### Epic E1: Agent publishes real YouTube content via unified engine

**Branch:** `feat/plant-dma-2-it1-e1`
**User story:** As a DMA agent, I publish content to YouTube through the unified PublisherEngine so that all publishing goes through one governed path with eligibility checks.

---

#### Story E1-S1: Create YouTubeAdapter wrapping YouTubeClient

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/plant-dma-2-it1-e1`
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained — read this card, then act):**
> `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py` defines the `DestinationAdapter` ABC (line 21) with a **sync** `publish()` method. The existing `YouTubeClient` (in `integrations/social/youtube_client.py`) uses **async** methods (`post_text`, `post_short`). To unify them:
>
> 1. Change `DestinationAdapter.publish()` from `def` to `async def` in `publisher_engine.py` (line 34). Also change `PublisherEngine.publish()` to `async def` (line 112).
> 2. Update `SimulatedAdapter.publish()` in `adapters_publish.py` (line 28) to `async def` (no other change — it does no I/O).
> 3. Create `src/Plant/BackEnd/agent_mold/skills/adapters_youtube.py` with `YouTubeAdapter(DestinationAdapter)` that wraps `YouTubeClient.post_text()`. Map `SocialPostResult` fields to `PublishReceipt` fields.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py` | 1–140 | `DestinationAdapter` ABC, `PublisherEngine.publish()` signature, `PublishInput`/`PublishReceipt` imports |
| `src/Plant/BackEnd/agent_mold/skills/adapters_publish.py` | 1–37 | `SimulatedAdapter.publish()` signature and return |
| `src/Plant/BackEnd/integrations/social/youtube_client.py` | 1–160 | `YouTubeClient.__init__()`, `post_text()` args and return type `SocialPostResult` |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py` | modify | Line 34: change `def publish(` to `async def publish(`. Line 112: change `def publish(` to `async def publish(`. Line 128: change `return adapter.publish(inp)` to `return await adapter.publish(inp)` |
| `src/Plant/BackEnd/agent_mold/skills/adapters_publish.py` | modify | Line 28: change `def publish(` to `async def publish(` |
| `src/Plant/BackEnd/agent_mold/skills/adapters_youtube.py` | create | New file — `YouTubeAdapter(DestinationAdapter)` with `DESTINATION_TYPE = "youtube"` |

**Code patterns to copy exactly:**

```python
# adapters_youtube.py — copy this structure exactly:
"""YouTube publish adapter — wraps YouTubeClient for the unified PublisherEngine.

Converts PublishInput → YouTubeClient.post_text() → PublishReceipt.
All eligibility checks (approval_id, credential_ref, visibility) are handled
by PublisherEngine._check_publish_eligibility() — do NOT duplicate them here.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from agent_mold.skills.content_models import PublishInput, PublishReceipt
from agent_mold.skills.publisher_engine import DestinationAdapter
from integrations.social.youtube_client import YouTubeClient

logger = logging.getLogger(__name__)


class YouTubeAdapter(DestinationAdapter):
    """Publishes to YouTube via the real YouTubeClient.

    Delegates to YouTubeClient.post_text() for community posts.
    credential_ref and customer_id are extracted from PublishInput metadata.
    """

    DESTINATION_TYPE = "youtube"

    async def publish(self, inp: PublishInput) -> PublishReceipt:
        metadata = inp.post.destination.metadata or {}
        customer_id = metadata.get("customer_id", "")
        credential_ref = inp.credential_ref or metadata.get("credential_ref", "")

        client = YouTubeClient(customer_id=customer_id)
        try:
            result = await client.post_text(
                credential_ref=credential_ref,
                text=inp.post.content_text,
            )
            return PublishReceipt(
                post_id=inp.post.post_id,
                destination_type=self.DESTINATION_TYPE,
                success=result.success,
                platform_post_id=result.post_id,
                published_at=result.posted_at or datetime.now(timezone.utc),
                raw_response=result.raw_response,
            )
        except Exception as exc:
            logger.error("YouTubeAdapter.publish failed: %s", exc, exc_info=True)
            return PublishReceipt(
                post_id=inp.post.post_id,
                destination_type=self.DESTINATION_TYPE,
                success=False,
                error=str(exc),
            )
```

**Acceptance criteria (binary pass/fail only):**
1. `DestinationAdapter.publish()` signature is `async def publish(self, inp: PublishInput) -> PublishReceipt`
2. `SimulatedAdapter.publish()` is `async def` and all existing tests still pass
3. `YouTubeAdapter` exists at `src/Plant/BackEnd/agent_mold/skills/adapters_youtube.py`
4. `YouTubeAdapter.publish()` calls `YouTubeClient.post_text()` and returns a real `PublishReceipt`
5. Unit test mocks `YouTubeClient.post_text()` and verifies `PublishReceipt` fields

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/unit/test_adapters_youtube.py` | Mock `YouTubeClient.post_text` returns `SocialPostResult(success=True, post_id="yt123", post_url="...", posted_at=now)` | `receipt.success is True`, `receipt.platform_post_id == "yt123"` |
| E1-S1-T2 | same | Mock `YouTubeClient.post_text` raises `SocialPlatformError` | `receipt.success is False`, `receipt.error` contains error message |
| E1-S1-T3 | `src/Plant/BackEnd/tests/unit/test_publisher_engine.py` | Use `SimulatedAdapter` with async engine | Existing simulated tests pass with `await engine.publish(...)` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/unit/test_adapters_youtube.py src/Plant/BackEnd/tests/unit/test_publisher_engine.py -v
```

**Commit message:** `feat(plant-dma-2): E1-S1 — create YouTubeAdapter wrapping YouTubeClient`

**Done signal:** `"E1-S1 done. Created: adapters_youtube.py. Modified: publisher_engine.py, adapters_publish.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E1-S2: Register YouTubeAdapter and rewire scheduler to use PublisherEngine

**BLOCKED UNTIL:** E1-S1 committed to `feat/plant-dma-2-it1-e1`
**Estimated time:** 45 min
**Branch:** `feat/plant-dma-2-it1-e1` (same branch, continue from E1-S1)
**CP BackEnd pattern:** N/A

**What to do:**
> `publisher_engine.py` `build_default_registry()` (line 142) currently registers `SimulatedAdapter` for `"youtube"`. Replace that line with `YouTubeAdapter`. Then `marketing_scheduler.py` lines 76–86 call `YouTubeClient` directly — replace this block with `await default_engine.publish(publish_input)`, constructing `PublishInput` from the existing post data. Remove the direct `from integrations.social.youtube_client import YouTubeClient` import from the scheduler.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py` | 140–170 | `build_default_registry()` function, SimulatedAdapter registrations |
| `src/Plant/BackEnd/services/marketing_scheduler.py` | 60–100 | YouTube-specific branch (lines 76–86), how post fields are accessed |
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | 285–316 | `PublishInput` and `PublishReceipt` field definitions |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py` | modify | In `build_default_registry()`: replace `registry.register("youtube", SimulatedAdapter)` with `from agent_mold.skills.adapters_youtube import YouTubeAdapter` + `registry.register("youtube", YouTubeAdapter)` |
| `src/Plant/BackEnd/services/marketing_scheduler.py` | modify | Remove direct `YouTubeClient` import and usage (lines 76–86). Replace with: import `default_engine` from `publisher_engine`, construct `PublishInput` from post data, call `receipt = await default_engine.publish(publish_input)`, extract `provider_post_id` and `provider_post_url` from receipt |

**Code patterns to copy exactly:**

```python
# In publisher_engine.py build_default_registry(), replace YouTube line:
def build_default_registry() -> DestinationRegistry:
    from agent_mold.skills.adapters_publish import SimulatedAdapter
    from agent_mold.skills.adapters_youtube import YouTubeAdapter
    registry = DestinationRegistry()
    registry.register("simulated", SimulatedAdapter)
    registry.register("x", SimulatedAdapter)
    registry.register("twitter", SimulatedAdapter)
    registry.register("youtube", YouTubeAdapter)  # real adapter
    return registry
```

```python
# In marketing_scheduler.py, replace the YouTube-specific branch (lines 76-86) with:
from agent_mold.skills.publisher_engine import default_engine
from agent_mold.skills.content_models import (
    PublishInput, ContentPost, DestinationRef,
)

# ... inside the post loop, replace the if/else block:
publish_input = PublishInput(
    post=ContentPost(
        post_id=post.post_id,
        campaign_id=batch.campaign_id if hasattr(batch, 'campaign_id') else "",
        theme_item_id="",
        destination=DestinationRef(
            destination_type=post.channel.value,
            metadata={"customer_id": batch.customer_id},
        ),
        content_text=post.text,
        hashtags=post.hashtags or [],
        scheduled_publish_at=post.scheduled_at,
    ),
    credential_ref=effective_credential_ref,
    approval_id=post.approval_id,
    visibility=getattr(post, "visibility", "private"),
    public_release_requested=getattr(post, "public_release_requested", False),
)
receipt = await default_engine.publish(publish_input)
if receipt.success:
    provider_post_id = receipt.platform_post_id
    provider_post_url = receipt.raw_response.get("post_url") if receipt.raw_response else None
else:
    raise RuntimeError(receipt.error or "Publish failed via engine")
```

**Acceptance criteria:**
1. `build_default_registry()` registers `YouTubeAdapter` for `"youtube"` instead of `SimulatedAdapter`
2. `marketing_scheduler.py` no longer imports `YouTubeClient` directly
3. `marketing_scheduler.py` constructs `PublishInput` and calls `await default_engine.publish()`
4. Existing scheduler tests pass (mock at engine level instead of YouTubeClient level)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/Plant/BackEnd/tests/unit/test_marketing_scheduler.py` | Mock `default_engine.publish` returns successful `PublishReceipt` | Post status becomes "posted", `provider_post_id` is set |
| E1-S2-T2 | same | Mock `default_engine.publish` returns failed `PublishReceipt` | Post status becomes "failed", error recorded |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/unit/test_marketing_scheduler.py -v
```

**Commit message:** `feat(plant-dma-2): E1-S2 — register YouTubeAdapter and rewire scheduler`

**Done signal:** `"E1-S2 done. Modified: publisher_engine.py, marketing_scheduler.py. Tests: T1 ✅ T2 ✅"`

---

### Epic E2: Customer sees real publish receipts persisted in database

**Branch:** `feat/plant-dma-2-it1-e2`
**User story:** As a customer, I can see real publish receipts (platform post ID, URL, timestamp) for my DMA's YouTube posts so I can verify content was actually published.

---

#### Story E2-S1: Create publish_receipt DB model

**BLOCKED UNTIL:** none (can start in parallel with E1, but E2-S2 depends on E1)
**Estimated time:** 45 min
**Branch:** `feat/plant-dma-2-it1-e2`
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do:**
> `src/Plant/BackEnd/agent_mold/skills/content_models.py` line 307 defines a Pydantic `PublishReceipt` but there is no SQLAlchemy model to persist it. Create a new `PublishReceiptModel` in `src/Plant/BackEnd/models/publish_receipt.py` with columns matching the Pydantic model fields: `post_id`, `destination_type`, `success`, `platform_post_id`, `published_at`, `error`, `raw_response` (JSONB). Add an Alembic migration.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | 307–316 | `PublishReceipt` Pydantic model fields |
| `src/Plant/BackEnd/models/performance_stat.py` | 1–35 | How existing models use `Base`, JSONB, UUID primary key pattern |
| `src/Plant/BackEnd/core/database.py` | 1–30 | `Base` import location |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/models/publish_receipt.py` | create | New SQLAlchemy model `PublishReceiptModel` with table name `publish_receipts` |
| `src/Plant/BackEnd/models/__init__.py` | modify | Add `from models.publish_receipt import PublishReceiptModel` |

**Code patterns to copy exactly:**

```python
# models/publish_receipt.py — copy this structure:
"""PublishReceiptModel — persisted record of every publish attempt.

PLANT-DMA-2 E2-S1

One row per publish attempt. Links to a campaign post by post_id.
Unique per (post_id, destination_type) — upsert-safe.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class PublishReceiptModel(Base):
    __tablename__ = "publish_receipts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String, nullable=False, index=True)
    destination_type = Column(String, nullable=False)
    success = Column(Boolean, nullable=False, default=False)
    platform_post_id = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    raw_response = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_publish_receipts_post_dest", "post_id", "destination_type"),
    )
```

**Acceptance criteria:**
1. `PublishReceiptModel` exists at `src/Plant/BackEnd/models/publish_receipt.py`
2. Model has columns: `id`, `post_id`, `destination_type`, `success`, `platform_post_id`, `published_at`, `error`, `raw_response`, `created_at`
3. Model is importable from `models` package
4. Unit test verifies model instantiation with valid data

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/Plant/BackEnd/tests/unit/test_publish_receipt_model.py` | Instantiate `PublishReceiptModel(post_id="p1", destination_type="youtube", success=True, platform_post_id="yt123")` | All fields set correctly, `id` is auto-generated UUID |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/unit/test_publish_receipt_model.py -v
```

**Commit message:** `feat(plant-dma-2): E2-S1 — create PublishReceiptModel`

**Done signal:** `"E2-S1 done. Created: models/publish_receipt.py. Modified: models/__init__.py. Tests: T1 ✅"`

---

#### Story E2-S2: Persist receipts from PublisherEngine and add query endpoint

**BLOCKED UNTIL:** E1-S2 and E2-S1 committed
**Estimated time:** 90 min
**Branch:** `feat/plant-dma-2-it1-e2`
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do:**
> After `PublisherEngine.publish()` returns a `PublishReceipt`, the caller (`marketing_scheduler.py`) must persist it to the `publish_receipts` table using `PublishReceiptModel`. Also create a Plant API endpoint `GET /api/v1/publish-receipts/{hired_instance_id}` that returns receipts for a given agent instance so CP/mobile can display them.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/services/marketing_scheduler.py` | 85–105 | Where post status is updated after publish — insert receipt persist here |
| `src/Plant/BackEnd/models/publish_receipt.py` | 1–40 | `PublishReceiptModel` columns (from E2-S1) |
| `src/Plant/BackEnd/api/v1/campaigns.py` | 1–30 | Existing Plant API route pattern for `waooaw_router`, response models |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/services/marketing_scheduler.py` | modify | After the `receipt = await default_engine.publish(publish_input)` call, persist a `PublishReceiptModel` row to the DB session |
| `src/Plant/BackEnd/api/v1/publish_receipts.py` | create | New route file with `GET /api/v1/publish-receipts/{hired_instance_id}` returning list of receipts |
| `src/Plant/BackEnd/main.py` | modify | Include the new router: `app.include_router(publish_receipts.router)` |

**Code patterns to copy exactly:**

```python
# api/v1/publish_receipts.py — use waooaw_router, GET uses read replica:
from typing import List

from fastapi import Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.routing import waooaw_router
from core.database import get_read_db_session
from models.publish_receipt import PublishReceiptModel

router = waooaw_router(prefix="/api/v1/publish-receipts", tags=["publish-receipts"])


class PublishReceiptResponse(BaseModel):
    id: str
    post_id: str
    destination_type: str
    success: bool
    platform_post_id: str | None = None
    published_at: str | None = None
    error: str | None = None

    class Config:
        from_attributes = True


@router.get("/{hired_instance_id}", response_model=List[PublishReceiptResponse])
async def list_publish_receipts(
    hired_instance_id: str,
    db: AsyncSession = Depends(get_read_db_session),
):
    """List publish receipts for a hired agent instance."""
    stmt = (
        select(PublishReceiptModel)
        .where(PublishReceiptModel.post_id.like(f"%{hired_instance_id}%"))
        .order_by(PublishReceiptModel.created_at.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
```

```python
# In marketing_scheduler.py, after receipt = await default_engine.publish(publish_input):
from models.publish_receipt import PublishReceiptModel

receipt_row = PublishReceiptModel(
    post_id=receipt.post_id,
    destination_type=receipt.destination_type,
    success=receipt.success,
    platform_post_id=receipt.platform_post_id,
    published_at=receipt.published_at,
    error=receipt.error,
    raw_response=receipt.raw_response,
)
session.add(receipt_row)
# session.commit() happens at the end of the batch loop
```

**Acceptance criteria:**
1. After every publish (success or failure), a `PublishReceiptModel` row is persisted to the database
2. `GET /api/v1/publish-receipts/{hired_instance_id}` returns 200 with list of receipts
3. GET endpoint uses `get_read_db_session()` (read replica)
4. Route uses `waooaw_router()`
5. Tests cover both persist-on-success and persist-on-failure paths

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/Plant/BackEnd/tests/unit/test_publish_receipt_persist.py` | Mock engine returns successful receipt, run scheduler | `PublishReceiptModel` row created with `success=True` |
| E2-S2-T2 | same | Mock engine returns failed receipt | `PublishReceiptModel` row created with `success=False`, error populated |
| E2-S2-T3 | `src/Plant/BackEnd/tests/unit/test_publish_receipts_api.py` | TestClient GET `/api/v1/publish-receipts/inst-1` with seeded rows | 200, returns list |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/unit/test_publish_receipt_persist.py src/Plant/BackEnd/tests/unit/test_publish_receipts_api.py -v
```

**Commit message:** `feat(plant-dma-2): E2-S2 — persist publish receipts and add query endpoint`

**Done signal:** `"E2-S2 done. Created: api/v1/publish_receipts.py. Modified: marketing_scheduler.py, main.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

<!-- ITERATION 2 STORY CARDS GO BELOW — next commit -->
