# PLANT-CONTENT-1 — Generic Content Creator & Publisher Skills

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-CONTENT-1` |
| Feature area | Plant BackEnd — `agent_mold/skills/` + campaign orchestration API + publish engine |
| Created | 2026-03-05 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §3 — Plant BackEnd architecture |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 4 |
| Total epics | 8 |
| Total stories | 11 |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in each card |
| Binary inference only | Acceptance criteria are pass/fail |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. All patterns you need are in your card.

---

## PM Review Checklist

- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] `waooaw_router()` in every new route story
- [x] Audit dependency in every new route story
- [x] `PIIMaskingFilter` in every new route story
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has time estimate and come-back datetime
- [x] STUCK PROTOCOL is in Agent Execution Rules
- [x] Lane A before Lane B
- [x] No placeholders remain
- [x] Cost estimator is in Iteration 1 scope
- [x] Publisher engine is plug-and-play (destination registry pattern)
- [x] Approval granularity (per-item or batch) is configurable in the model

---

## Vision Intake (confirmed)

1. **Area:** Plant BackEnd — two new plug-and-play skills (`content_creator`, `content_publisher`) registered in `agent_mold/`, new campaign models, Plant API routes, CP BackEnd proxy routes.
2. **User outcome:** A customer submits a campaign brief → gets instant cost estimate (₹0 for Grok free tier) → approves a generated daily-theme list (one item at a time, or batch) → reviews each platform-specific post at their own pace → posts are published on schedule to any registered destination.
3. **Out of scope (this plan):** Real social platform OAuth (Phase 1 uses `simulated_publish` destination adapter). CP FrontEnd campaign screens (separate plan). Mobile push for review requests. Image generation.
4. **Lane:** B throughout — all endpoints are new.
5. **Urgency:** None stated.

---

## Architecture Decision Record (read before coding)

### Two skills, clean separation

```
content_creator skill          content_publisher skill
─────────────────────          ────────────────────────
Input:  CampaignBrief          Input:  ApprovedPost + DestinationRef
Output: DailyThemeList         Output: PublishReceipt (or SimulatedReceipt)
        + ContentPost[]
        + CostEstimate

No knowledge of destinations.  No knowledge of content generation.
Purely agentic / LLM step.     Purely mechanical / I/O step.
```

### Publisher engine — plug-and-play destination registry

```
PublisherEngine
├── DestinationAdapter (abstract interface)
│   ├── SimulatedAdapter   ← Phase 1, always registered
│   ├── LinkedInAdapter    ← Phase 2 (separate plan, OAuth required)
│   ├── InstagramAdapter   ← Phase 2
│   └── YouTubeAdapter     ← Phase 2
└── DestinationRegistry    ← maps destination_type → adapter class
    (loaded at startup from env; new adapters = new file + registry entry)
```

### Data model (new tables / in-memory stores)

```
Campaign
├── campaign_id
├── hired_instance_id        ← links to existing HiredAgent
├── customer_id
├── brief: CampaignBrief     ← JSON (theme, duration_days, post_frequency, platforms[])
├── cost_estimate: CostEstimate
├── status: draft|theme_approved|running|paused|completed
└── created_at / updated_at

DailyThemeItem
├── theme_item_id
├── campaign_id
├── day_number               ← 1-based
├── scheduled_date           ← ISO date
├── theme_title
├── theme_description
├── review_status: pending_review|approved|rejected
└── approved_at

ContentPost
├── post_id
├── campaign_id
├── theme_item_id
├── destination: DestinationRef   ← {type, handle/channel}
├── content_text
├── scheduled_publish_at     ← datetime
├── review_status: pending_review|approved|rejected
├── publish_status: not_published|published|failed
├── publish_receipt          ← JSON (adapter-specific)
└── created_at / updated_at
```

### Cost estimation model

```
CostEstimate
├── total_posts: int          ← duration_days × post_frequency × len(platforms)
├── llm_calls: int            ← 1 (theme list) + total_posts
├── cost_per_call_usd: float  ← 0.0 for Grok free tier
├── total_cost_usd: float
├── total_cost_inr: float
└── model_used: str           ← "grok-3-latest" | "deterministic"
```

### Approval granularity — configurable per campaign

The `CampaignBrief` includes `approval_mode`:

| Mode | Behaviour |
|---|---|
| `"per_item"` | Customer approves each `DailyThemeItem` or `ContentPost` individually |
| `"batch"` | Customer receives a list and approves/rejects items in one call |
| `"auto"` | No customer review required; all items auto-approved (power users) |

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Core skill models + cost estimator + Grok content creator | E1, E2 | 3 | 4.5h | 2026-03-06 06:00 UTC |
| 2 | Campaign orchestration API (CRUD + theme generation + post generation) | E3, E4 | 3 | 4h | 2026-03-06 10:00 UTC |
| 3 | Publisher engine — plug-and-play destination registry + simulated adapter | E5, E6 | 3 | 3.5h | 2026-03-06 14:00 UTC |
| 4 | CP BackEnd proxy routes + skill registration in agent catalog | E7, E8 | 2 | 2.5h | 2026-03-06 17:00 UTC |

**Estimate basis:** New skill module = 90 min | New Plant API route file = 45 min | New adapter = 30 min | CP proxy = 45 min | Tests = included in each estimate. Add 20% buffer.

---

## Agent Execution Rules

1. **Start**: `git status && git log --oneline -3` — must be on `main` with clean tree.
2. **Branch**: create the exact branch listed in the story card before touching any file.
3. **Test**: run the exact test command in each story card before marking done.
4. **STUCK PROTOCOL**: If blocked for more than 15 min on a single story, open a draft PR titled `WIP: PLANT-CONTENT-1 [story-id] — [blocker description]`. Post the PR URL, then HALT.
5. **PR**: One PR per iteration. Title: `feat(plant-content-1): iteration N — [scope]`.
6. **Persistence mode**: Use in-memory stores (same pattern as `deliverables_simple.py`) for Phase 1. Do NOT add new database migrations in this plan.
7. **EXECUTOR_BACKEND env var**: default `deterministic`. When `EXECUTOR_BACKEND=grok` the Grok client is used. Cost estimate is always produced regardless of mode.
8. **Never put business logic in CP BackEnd** — Iteration 4 CP routes are thin proxies only.

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

EXPERT PERSONAS: Senior Python engineer specialising in plugin architectures and LLM integration
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python plugin-architecture engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-CONTENT-1-content-creator-publisher.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2. Do not touch Iterations 2, 3, 4.
TIME BUDGET: 4.5h. If you reach 4h15m without finishing, follow STUCK PROTOCOL.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3 — must be on main, clean tree.
2. Read "Agent Execution Rules" in this plan file.
3. Read "Iteration 1" section in this plan file.
4. Execute Epics: E1 → E2
5. When all docker-tested, open iteration PR. Post PR URL. HALT.
```

Come back at: **2026-03-06 06:00 UTC**

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python/FastAPI engineer specialising in campaign orchestration APIs
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python/FastAPI campaign-API engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-CONTENT-1-content-creator-publisher.md
YOUR SCOPE: Iteration 2 only — Epics E3, E4. Do not touch other iterations.
TIME BUDGET: 4h. If you reach 3h45m without finishing, follow STUCK PROTOCOL.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(plant-content-1): iteration 1. If not — HALT.

EXECUTION ORDER:
1. Run prerequisite check.
2. Read "Agent Execution Rules" in this plan file.
3. Read "Iteration 2" section in this plan file.
4. Execute Epics: E3 → E4
5. When docker-tested, open iteration PR. Post PR URL. HALT.
```

Come back at: **2026-03-06 10:00 UTC**

---

### Iteration 3

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Iteration 3 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python engineer specialising in plug-and-play integration engines
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python integration-engine engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-CONTENT-1-content-creator-publisher.md
YOUR SCOPE: Iteration 3 only — Epics E5, E6. Do not touch other iterations.
TIME BUDGET: 3.5h. If you reach 3h15m without finishing, follow STUCK PROTOCOL.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(plant-content-1): iteration 2. If not — HALT.

EXECUTION ORDER:
1. Run prerequisite check.
2. Read "Agent Execution Rules" in this plan file.
3. Read "Iteration 3" section in this plan file.
4. Execute Epics: E5 → E6
5. When docker-tested, open iteration PR. Post PR URL. HALT.
```

Come back at: **2026-03-06 14:00 UTC**

---

### Iteration 4

> ⚠️ Do NOT launch until Iteration 3 PR is merged to `main`.

**Iteration 4 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python/FastAPI thin-proxy engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior thin-proxy engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-CONTENT-1-content-creator-publisher.md
YOUR SCOPE: Iteration 4 only — Epics E7, E8. Do not touch other iterations.
TIME BUDGET: 2.5h. If you reach 2h15m without finishing, follow STUCK PROTOCOL.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(plant-content-1): iteration 3. If not — HALT.

EXECUTION ORDER:
1. Run prerequisite check.
2. Read "Agent Execution Rules" in this plan file.
3. Read "Iteration 4" section in this plan file.
4. Execute Epics: E7 → E8
5. When docker-tested, open iteration PR. Post PR URL. HALT.
```

Come back at: **2026-03-06 17:00 UTC**

---

## Iteration 1 — Core Skill Models + Cost Estimator + Grok Content Creator

**Scope:** Define the canonical data models for campaigns, theme items, and posts. Implement the `ContentCreatorSkill` with a Grok-backed executor (with deterministic fallback). Produce a `CostEstimate` on every request.
**Lane:** B — all new files.
**⏱ Estimated:** 4.5h | **Come back:** 2026-03-06 06:00 UTC

### Dependency Map (Iteration 1)

```
E1 (models + cost estimator) ──► independent — new file agent_mold/skills/content_models.py
E2 (content creator skill)   ──► BLOCKED UNTIL E1 merged — uses models from E1
```

---

### Epic E1: Shared content models and cost estimator are defined

**Branch:** `feat/plant-content-1-it1-e1-models`
**User story:** As a platform engineer, I have a single canonical schema for campaigns, theme items, posts, and cost estimates that all other skills and API endpoints import — so every component speaks the same language.

---

#### Story E1-S1: Content campaign models + cost estimator — BACKEND

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/plant-content-1-it1-e1-models`

**What to do:**
Create `src/Plant/BackEnd/agent_mold/skills/content_models.py`. This single file defines all Pydantic models and the pure-function cost estimator that the content creator, publisher, and API routes will all import. No FastAPI routes here — pure models only.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/playbook.py` | 1–145 | Existing `SkillCategory`, `CanonicalMessage`, `ChannelName` — do NOT redefine these; extend or re-export them |
| `src/Plant/BackEnd/agent_mold/skills/executor.py` | 1–80 | `SkillExecutionInput` fields — understand what inputs the creator will receive |
| `src/Plant/BackEnd/agent_mold/skills/adapters.py` | 1–80 | Existing `ChannelVariant` — understand what publisher outputs look like per-channel |

**File to create:**

`src/Plant/BackEnd/agent_mold/skills/content_models.py`

**Code pattern to copy exactly:**

```python
"""Content creator and publisher — shared campaign models.

All skills, API routes, and adapters import from here.
Do NOT redefine ChannelName or CanonicalMessage — import from playbook.py.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from agent_mold.skills.playbook import ChannelName


# ─── Enums ────────────────────────────────────────────────────────────────────

class ApprovalMode(str, Enum):
    PER_ITEM = "per_item"   # customer approves each item individually
    BATCH = "batch"          # customer approves a list in one call
    AUTO = "auto"            # no customer review required


class ReviewStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    THEME_APPROVED = "theme_approved"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class PublishStatus(str, Enum):
    NOT_PUBLISHED = "not_published"
    PUBLISHED = "published"
    FAILED = "failed"


# ─── Campaign Brief (customer input) ─────────────────────────────────────────

class DestinationRef(BaseModel):
    """Reference to a publish destination. Adapter registered by destination_type."""
    destination_type: str = Field(..., min_length=1,
        description="Registered adapter key, e.g. 'simulated', 'linkedin', 'instagram'")
    handle: Optional[str] = Field(None,
        description="Platform handle or channel ID, e.g. '@waooaw' or 'UCxxx'")
    metadata: Dict[str, Any] = Field(default_factory=dict,
        description="Adapter-specific config, e.g. page_id, access_token_ref")


class PostingSchedule(BaseModel):
    """Defines how often to post within a campaign."""
    times_per_day: int = Field(1, ge=1, le=24,
        description="Number of posts per day per platform")
    preferred_hours_utc: List[int] = Field(
        default_factory=lambda: [9],
        description="Preferred UTC hours for posting, e.g. [9, 17]"
    )

    @validator("preferred_hours_utc", each_item=True)
    def _valid_hour(cls, v: int) -> int:
        if not 0 <= v <= 23:
            raise ValueError(f"Hour must be 0-23, got {v}")
        return v


class CampaignBrief(BaseModel):
    """Customer-submitted campaign brief. Immutable after creation."""
    theme: str = Field(..., min_length=3,
        description="Campaign master theme, e.g. 'Hire AI Agents — WAOOAW'")
    start_date: date = Field(...,
        description="ISO date for first post, e.g. '2026-03-06'")
    duration_days: int = Field(..., ge=1, le=365,
        description="Total campaign length in days")
    destinations: List[DestinationRef] = Field(..., min_items=1,
        description="One or more publish destinations")
    schedule: PostingSchedule = Field(default_factory=PostingSchedule)
    brand_name: str = Field("", description="Brand name for content personalisation")
    audience: str = Field("", description="Target audience description")
    tone: str = Field("professional", description="Content tone, e.g. 'inspiring', 'casual'")
    language: str = Field("en", description="ISO 639-1 language code")
    approval_mode: ApprovalMode = Field(ApprovalMode.PER_ITEM)
    additional_context: str = Field("",
        description="Free-text extra instructions for the content creator")


# ─── Cost Estimate ────────────────────────────────────────────────────────────

class CostEstimate(BaseModel):
    total_theme_items: int
    total_posts: int
    llm_calls: int
    cost_per_call_usd: float
    total_cost_usd: float
    total_cost_inr: float
    model_used: str
    note: str = ""


def estimate_cost(brief: CampaignBrief, model_used: str = "deterministic") -> CostEstimate:
    """Pure function — no I/O. Called before any LLM request is made.

    Cost is zero for deterministic mode and Grok free-tier models.
    Update cost_per_call_usd when switching to paid models.
    """
    total_theme_items = brief.duration_days
    posts_per_day = brief.schedule.times_per_day * len(brief.destinations)
    total_posts = total_theme_items * posts_per_day
    # 1 LLM call for full theme list + 1 LLM call per post
    llm_calls = 1 + total_posts

    # Pricing table — update when model changes
    COST_TABLE: Dict[str, float] = {
        "deterministic": 0.0,
        "grok-3-latest": 0.0,      # free tier as of 2026-03
        "grok-2-latest": 0.0,      # free tier as of 2026-03
    }
    cost_per_call = COST_TABLE.get(model_used, 0.001)  # default $0.001 for unknown models
    total_usd = llm_calls * cost_per_call
    # INR conversion — update via env var COST_USD_TO_INR (default 84)
    import os
    usd_to_inr = float(os.getenv("COST_USD_TO_INR", "84"))
    total_inr = total_usd * usd_to_inr

    return CostEstimate(
        total_theme_items=total_theme_items,
        total_posts=total_posts,
        llm_calls=llm_calls,
        cost_per_call_usd=cost_per_call,
        total_cost_usd=total_usd,
        total_cost_inr=total_inr,
        model_used=model_used,
        note="₹0 — Grok free tier" if cost_per_call == 0.0 else "",
    )


# ─── Campaign + Theme Items + Posts ───────────────────────────────────────────

class Campaign(BaseModel):
    campaign_id: str = Field(default_factory=lambda: str(uuid4()))
    hired_instance_id: str
    customer_id: str
    brief: CampaignBrief
    cost_estimate: CostEstimate
    status: CampaignStatus = CampaignStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DailyThemeItem(BaseModel):
    theme_item_id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    day_number: int = Field(..., ge=1)
    scheduled_date: date
    theme_title: str
    theme_description: str
    dimensions: List[str] = Field(default_factory=list,
        description="Content angles for this day, e.g. ['social proof', 'education']")
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    approved_at: Optional[datetime] = None


class ContentPost(BaseModel):
    post_id: str = Field(default_factory=lambda: str(uuid4()))
    campaign_id: str
    theme_item_id: str
    destination: DestinationRef
    content_text: str
    hashtags: List[str] = Field(default_factory=list)
    scheduled_publish_at: datetime
    review_status: ReviewStatus = ReviewStatus.PENDING_REVIEW
    publish_status: PublishStatus = PublishStatus.NOT_PUBLISHED
    publish_receipt: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Skill I/O contracts ──────────────────────────────────────────────────────

class ContentCreatorInput(BaseModel):
    """Input to the ContentCreatorSkill."""
    campaign: Campaign


class ContentCreatorOutput(BaseModel):
    """Output of the ContentCreatorSkill — theme list for the full campaign."""
    campaign_id: str
    theme_items: List[DailyThemeItem]
    cost_estimate: CostEstimate


class PostGeneratorInput(BaseModel):
    """Input to generate platform-specific posts for one approved theme item."""
    campaign: Campaign
    theme_item: DailyThemeItem


class PostGeneratorOutput(BaseModel):
    """Output — one ContentPost per destination, for one theme item."""
    theme_item_id: str
    posts: List[ContentPost]


class PublishInput(BaseModel):
    """Input to the PublisherEngine for one approved post."""
    post: ContentPost
    credential_ref: Optional[str] = Field(None,
        description="Secret Manager key for platform OAuth token, if required")


class PublishReceipt(BaseModel):
    post_id: str
    destination_type: str
    success: bool
    platform_post_id: Optional[str] = None
    published_at: Optional[datetime] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None
```

**Acceptance criteria:**
1. `python -c "from agent_mold.skills.content_models import CampaignBrief, estimate_cost, Campaign"` exits 0
2. `estimate_cost(brief)` with `duration_days=30`, `times_per_day=1`, 5 destinations, model `"grok-3-latest"` returns `total_cost_usd == 0.0` and `total_posts == 150`
3. `estimate_cost(brief)` with `duration_days=30`, `times_per_day=3`, 5 destinations returns `total_posts == 450`
4. All Pydantic models serialize to JSON without error

**Tests to write:**

| Test ID | File | Assert |
|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/test_content_models.py` (create) | `estimate_cost` with 30 days, 1×/day, 5 destinations → `total_posts == 150`, `total_cost_usd == 0.0` |
| E1-S1-T2 | same | `estimate_cost` with 30 days, 3×/day, 5 destinations → `total_posts == 450` |
| E1-S1-T3 | same | `PostingSchedule(preferred_hours_utc=[25])` raises `ValidationError` |
| E1-S1-T4 | same | `CampaignBrief(destinations=[])` raises `ValidationError` (min_items=1) |
| E1-S1-T5 | same | `Campaign` and `DailyThemeItem` `.json()` serialize without error |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/test_content_models.py -v --cov=src/Plant/BackEnd/agent_mold/skills/content_models --cov-fail-under=85
```

**Commit message:** `feat(plant-content-1): content campaign models and cost estimator`

**Done signal:** `"E1-S1 done. T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅."`

---

### Epic E2: Content creator skill produces theme list with cost estimate

**Branch:** `feat/plant-content-1-it1-e2-creator-skill`
**User story:** As a platform engineer, I can call `ContentCreatorSkill.generate_theme_list(campaign)` and receive a full `DailyThemeList` with per-day themes, angles, and a cost estimate — with Grok powering the content when `EXECUTOR_BACKEND=grok`, and a deterministic template when not set.

---

#### Story E2-S1: ContentCreatorSkill with Grok executor + deterministic fallback — BACKEND

**BLOCKED UNTIL:** E1-S1 merged to `main`
**Estimated time:** 90 min
**Branch:** `feat/plant-content-1-it1-e2-creator-skill`

**What to do:**
Create two files:
1. `src/Plant/BackEnd/agent_mold/skills/grok_client.py` — thin Grok API client (OpenAI-SDK-compatible). Uses `XAI_API_KEY` env var.
2. `src/Plant/BackEnd/agent_mold/skills/content_creator.py` — `ContentCreatorSkill` class with `generate_theme_list()` and `generate_posts_for_theme()` methods. Reads `EXECUTOR_BACKEND` env var: if `"grok"`, calls Grok; otherwise uses deterministic templates.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | all | All models needed — `Campaign`, `DailyThemeItem`, `ContentCreatorOutput`, `PostGeneratorOutput`, `ChannelName` |
| `src/Plant/BackEnd/agent_mold/skills/executor.py` | 1–80 | How the existing deterministic executor builds `CanonicalMessage` — copy the templating style |
| `src/Plant/BackEnd/agent_mold/skills/adapters.py` | 1–80 | `adapt_linkedin`, `adapt_instagram`, etc — call these to generate per-channel text |

**Files to create:**

`src/Plant/BackEnd/agent_mold/skills/grok_client.py`

```python
"""Thin Grok API client (OpenAI-SDK-compatible).

Uses XAI_API_KEY env var. If not set, raises GrokClientError.
Set EXECUTOR_BACKEND=grok to activate. Default is 'deterministic'.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from openai import OpenAI  # openai>=1.0 — already in requirements.txt


class GrokClientError(Exception):
    pass


def get_grok_client() -> OpenAI:
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise GrokClientError("XAI_API_KEY is not set. Set EXECUTOR_BACKEND=deterministic or provide the key.")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )


def grok_complete(
    client: OpenAI,
    system: str,
    user: str,
    model: str = "grok-3-latest",
    temperature: float = 0.7,
) -> str:
    """Single chat completion call. Returns assistant message text."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""
```

`src/Plant/BackEnd/agent_mold/skills/content_creator.py`

```python
"""ContentCreatorSkill — generates DailyThemeList + ContentPosts.

EXECUTOR_BACKEND env var controls the engine:
  "grok"          → Grok-3 API (requires XAI_API_KEY)
  "deterministic" → template-based, no API calls (default)
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone
from typing import List

from agent_mold.skills.adapters import (
    adapt_facebook,
    adapt_instagram,
    adapt_linkedin,
    adapt_whatsapp,
    adapt_youtube,
)
from agent_mold.skills.content_models import (
    Campaign,
    CanonicalMessage,
    ChannelName,
    ContentCreatorOutput,
    ContentPost,
    DailyThemeItem,
    DestinationRef,
    PostGeneratorInput,
    PostGeneratorOutput,
    ReviewStatus,
    estimate_cost,
)

# Channel → adapter map (add new channels here when adapters are created)
_CHANNEL_ADAPTER_MAP = {
    ChannelName.LINKEDIN: adapt_linkedin,
    ChannelName.INSTAGRAM: adapt_instagram,
    ChannelName.YOUTUBE: adapt_youtube,
    ChannelName.FACEBOOK: adapt_facebook,
    ChannelName.WHATSAPP: adapt_whatsapp,
}

_CONTENT_DIMENSIONS = [
    "social proof", "education", "inspiration", "product demo",
    "customer story", "behind the scenes", "FAQ", "trend commentary",
    "comparison", "how-to", "quick tip", "milestone celebration",
]


def _executor_backend() -> str:
    return os.getenv("EXECUTOR_BACKEND", "deterministic").lower()


class ContentCreatorSkill:
    """Plug-and-play skill. Register against any agent that needs content creation."""

    SKILL_ID = "content.creator.v1"

    def generate_theme_list(self, campaign: Campaign) -> ContentCreatorOutput:
        """Step 1: Generate DailyThemeItems for the full campaign duration."""
        brief = campaign.brief
        model_used = "grok-3-latest" if _executor_backend() == "grok" else "deterministic"
        cost = estimate_cost(brief, model_used=model_used)

        if _executor_backend() == "grok":
            theme_items = self._grok_theme_list(campaign)
        else:
            theme_items = self._deterministic_theme_list(campaign)

        return ContentCreatorOutput(
            campaign_id=campaign.campaign_id,
            theme_items=theme_items,
            cost_estimate=cost,
        )

    def generate_posts_for_theme(self, inp: PostGeneratorInput) -> PostGeneratorOutput:
        """Step 2: Generate ContentPosts for one approved DailyThemeItem."""
        if _executor_backend() == "grok":
            posts = self._grok_posts(inp)
        else:
            posts = self._deterministic_posts(inp)
        return PostGeneratorOutput(theme_item_id=inp.theme_item.theme_item_id, posts=posts)

    # ── Deterministic engine ──────────────────────────────────────────────────

    def _deterministic_theme_list(self, campaign: Campaign) -> List[DailyThemeItem]:
        brief = campaign.brief
        items: List[DailyThemeItem] = []
        for day in range(brief.duration_days):
            day_date = brief.start_date + timedelta(days=day)
            dim = _CONTENT_DIMENSIONS[day % len(_CONTENT_DIMENSIONS)]
            items.append(DailyThemeItem(
                campaign_id=campaign.campaign_id,
                day_number=day + 1,
                scheduled_date=day_date,
                theme_title=f"Day {day+1}: {brief.theme} — {dim.title()}",
                theme_description=(
                    f"Focus: {dim}. Brand: {brief.brand_name or 'WAOOAW'}. "
                    f"Audience: {brief.audience or 'general'}. Tone: {brief.tone}."
                ),
                dimensions=[dim],
            ))
        return items

    def _deterministic_posts(self, inp: PostGeneratorInput) -> List[ContentPost]:
        brief = inp.campaign.brief
        theme = inp.theme_item
        posts: List[ContentPost] = []

        canonical = CanonicalMessage(
            theme=theme.theme_title,
            core_message=f"{theme.theme_title}. {theme.theme_description}",
            call_to_action="Try WAOOAW — agents that earn your business.",
            key_points=theme.dimensions,
            hashtags=["WAOOAW", (brief.brand_name or "WAH").replace(" ", ""), "AIAgents"],
        )

        for dest in brief.destinations:
            channel_name = _destination_to_channel(dest.destination_type)
            adapter = _CHANNEL_ADAPTER_MAP.get(channel_name)
            if adapter is None:
                text = canonical.core_message
                hashtags = canonical.hashtags
            else:
                variant = adapter(canonical)
                text = variant.text
                hashtags = variant.hashtags

            scheduled = _compute_schedule(
                base_date=theme.scheduled_date,
                preferred_hours=brief.schedule.preferred_hours_utc,
                post_index=posts.__len__(),
            )
            posts.append(ContentPost(
                campaign_id=inp.campaign.campaign_id,
                theme_item_id=theme.theme_item_id,
                destination=dest,
                content_text=text,
                hashtags=hashtags,
                scheduled_publish_at=scheduled,
            ))
        return posts

    # ── Grok engine ───────────────────────────────────────────────────────────

    def _grok_theme_list(self, campaign: Campaign) -> List[DailyThemeItem]:
        from agent_mold.skills.grok_client import get_grok_client, grok_complete
        client = get_grok_client()
        brief = campaign.brief

        system = (
            "You are an expert content strategist. "
            "Return ONLY a valid JSON array — no markdown, no explanation."
        )
        user = (
            f"Create a {brief.duration_days}-day content calendar for the theme: "
            f"'{brief.theme}'. Brand: '{brief.brand_name}'. Audience: '{brief.audience}'. "
            f"Platforms: {[d.destination_type for d in brief.destinations]}. "
            f"Tone: {brief.tone}. Language: {brief.language}.\n"
            f"Return a JSON array of {brief.duration_days} objects, each with keys: "
            f"theme_title (string), theme_description (string), dimensions (list of strings). "
            f"Start date: {brief.start_date.isoformat()}."
        )
        raw = grok_complete(client, system, user)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Graceful fallback to deterministic if Grok returns non-JSON
            return self._deterministic_theme_list(campaign)

        items: List[DailyThemeItem] = []
        for i, item in enumerate(data[: brief.duration_days]):
            items.append(DailyThemeItem(
                campaign_id=campaign.campaign_id,
                day_number=i + 1,
                scheduled_date=brief.start_date + timedelta(days=i),
                theme_title=item.get("theme_title", f"Day {i+1}"),
                theme_description=item.get("theme_description", ""),
                dimensions=item.get("dimensions", []),
            ))
        return items

    def _grok_posts(self, inp: PostGeneratorInput) -> List[ContentPost]:
        from agent_mold.skills.grok_client import get_grok_client, grok_complete
        client = get_grok_client()
        brief = inp.campaign.brief
        theme = inp.theme_item
        posts: List[ContentPost] = []

        for dest in brief.destinations:
            system = (
                "You are a professional social media copywriter. "
                "Write ready-to-publish content. Return ONLY the post text, no explanation."
            )
            user = (
                f"Platform: {dest.destination_type}. "
                f"Theme: {theme.theme_title}. Context: {theme.theme_description}. "
                f"Brand: {brief.brand_name}. Audience: {brief.audience}. Tone: {brief.tone}. "
                f"Language: {brief.language}. "
                f"Include 3-5 relevant hashtags at the end."
            )
            text = grok_complete(client, system, user, temperature=0.8)
            scheduled = _compute_schedule(
                base_date=theme.scheduled_date,
                preferred_hours=brief.schedule.preferred_hours_utc,
                post_index=len(posts),
            )
            posts.append(ContentPost(
                campaign_id=inp.campaign.campaign_id,
                theme_item_id=theme.theme_item_id,
                destination=dest,
                content_text=text,
                scheduled_publish_at=scheduled,
            ))
        return posts


# ── Helpers ───────────────────────────────────────────────────────────────────

def _destination_to_channel(destination_type: str) -> ChannelName:
    """Map destination_type string to ChannelName enum. Defaults to LINKEDIN."""
    mapping = {
        "linkedin": ChannelName.LINKEDIN,
        "instagram": ChannelName.INSTAGRAM,
        "youtube": ChannelName.YOUTUBE,
        "facebook": ChannelName.FACEBOOK,
        "whatsapp": ChannelName.WHATSAPP,
        "x": ChannelName.LINKEDIN,  # X uses LinkedIn-style text for now
        "twitter": ChannelName.LINKEDIN,
        "simulated": ChannelName.LINKEDIN,
    }
    return mapping.get(destination_type.lower(), ChannelName.LINKEDIN)


def _compute_schedule(
    *,
    base_date: date,
    preferred_hours: List[int],
    post_index: int,
) -> datetime:
    hour = preferred_hours[post_index % len(preferred_hours)] if preferred_hours else 9
    return datetime(base_date.year, base_date.month, base_date.day, hour, 0, 0, tzinfo=timezone.utc)
```

**Acceptance criteria:**
1. `ContentCreatorSkill().generate_theme_list(campaign)` (deterministic mode) for 30-day brief with 5 destinations returns `ContentCreatorOutput` with `len(theme_items) == 30`
2. `generate_posts_for_theme(inp)` for one theme item with 3 destinations returns 3 `ContentPost` objects
3. Cost estimate in output has `total_cost_usd == 0.0` in deterministic mode
4. `EXECUTOR_BACKEND=grok` with `XAI_API_KEY` unset raises `GrokClientError` (not a 500 crash)

**Tests to write:**

| Test ID | File | Assert |
|---|---|---|
| E2-S1-T1 | `src/Plant/BackEnd/tests/test_content_creator.py` (create) | `generate_theme_list` deterministic, 30 days, 5 destinations → 30 theme items |
| E2-S1-T2 | same | `generate_posts_for_theme` 3 destinations → 3 posts |
| E2-S1-T3 | same | Post `content_text` is non-empty string for all destinations |
| E2-S1-T4 | same | With `EXECUTOR_BACKEND=grok` and no `XAI_API_KEY`, calling `generate_theme_list` raises `GrokClientError` |
| E2-S1-T5 | same | `scheduled_publish_at.hour` matches `preferred_hours_utc[0]` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/test_content_creator.py -v \
  --cov=src/Plant/BackEnd/agent_mold/skills/content_creator \
  --cov=src/Plant/BackEnd/agent_mold/skills/content_models \
  --cov-fail-under=85
```

**Commit message:** `feat(plant-content-1): ContentCreatorSkill with Grok executor and deterministic fallback`

**Done signal:** `"E2-S1 done. T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅."`

---

## Iteration 2 — Campaign Orchestration API

**Scope:** Plant BackEnd API routes for campaign lifecycle: create campaign (→ cost estimate), submit theme list for approval, approve/reject theme items, trigger post generation, approve/reject posts.
**Lane:** B — all new route files.
**⏱ Estimated:** 4h | **Come back:** 2026-03-06 10:00 UTC
**Prerequisite:** Iteration 1 merged to `main`

### Dependency Map (Iteration 2)

```
E3 (campaign CRUD + theme list generation) ──► independent
E4 (post generation + post approval)        ──► BLOCKED UNTIL E3 merged
```

---

### Epic E3: Customer can create a campaign and approve the daily theme list

**Branch:** `feat/plant-content-1-it2-e3-campaign-api`
**User story:** As a customer, I POST a campaign brief, immediately see a cost estimate and the full daily theme list, then approve each theme item (or the whole batch) at my own pace — so I control what content gets created before any LLM call for posts is made.

---

#### Story E3-S1: Campaign create + theme list generation API — BACKEND

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 90 min
**Branch:** `feat/plant-content-1-it2-e3-campaign-api`

**What to do:**
Create `src/Plant/BackEnd/api/v1/campaigns.py`. Register router in `src/Plant/BackEnd/main.py`. Implement:
- `POST /api/v1/campaigns` — create campaign from brief, call `ContentCreatorSkill.generate_theme_list()`, store campaign + theme items in memory, return estimate + theme list
- `GET /api/v1/campaigns/{campaign_id}` — get campaign status
- `GET /api/v1/campaigns/{campaign_id}/theme-items` — list theme items with review status
- `POST /api/v1/campaigns/{campaign_id}/theme-items/approve` — approve items (batch or per-item based on `approval_mode`)
- `PATCH /api/v1/campaigns/{campaign_id}/theme-items/{item_id}` — approve or reject a single item

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/deliverables_simple.py` | 1–120 | In-memory store pattern (`_deliverables_by_id` dict), router pattern with `waooaw_router`, auth header passing — copy exactly |
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | all | All models used in request/response bodies |
| `src/Plant/BackEnd/agent_mold/skills/content_creator.py` | all | `ContentCreatorSkill` API — `generate_theme_list(campaign)` |

**NFR code patterns to copy exactly:**

```python
# Router factory — MANDATORY (CI bans bare APIRouter)
from core.routing import waooaw_router
router = waooaw_router(prefix="/campaigns", tags=["campaigns"])

# App-level dependency check — verify main.py has:
#   app = FastAPI(dependencies=[Depends(get_correlation_id), Depends(get_audit_log)])

# PII masking on every logger
import logging
logger = logging.getLogger(__name__)
# Add PIIMaskingFilter in app startup — do NOT log customer_id or brand raw PII

# Circuit breaker — not needed here (no external HTTP calls in this route file)
# All data is in-memory; ContentCreatorSkill is in-process.

# In-memory store pattern (copy from deliverables_simple.py):
_campaigns: dict[str, Campaign] = {}
_theme_items: dict[str, dict[str, DailyThemeItem]] = {}  # campaign_id → {item_id → item}
```

**Request/Response schemas to use (import from content_models.py):**

```python
class CreateCampaignRequest(BaseModel):
    hired_instance_id: str
    customer_id: str
    brief: CampaignBrief

class CreateCampaignResponse(BaseModel):
    campaign: Campaign
    theme_items: list[DailyThemeItem]
    cost_estimate: CostEstimate
    message: str

class ApproveThemeItemsRequest(BaseModel):
    item_ids: list[str]    # empty = approve ALL pending items in batch mode
    decision: Literal["approved", "rejected"]
    notes: str = ""

class ThemeItemPatchRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: str = ""
```

**Acceptance criteria:**
1. `POST /api/v1/campaigns` with valid brief returns 201 + `campaign.cost_estimate.total_cost_usd == 0.0`
2. `GET /api/v1/campaigns/{id}/theme-items` returns list with all items in `pending_review`
3. `POST /api/v1/campaigns/{id}/theme-items/approve` with `item_ids=[]` approves all items (batch mode)
4. `PATCH /api/v1/campaigns/{id}/theme-items/{item_id}` with `decision=approved` sets item to `approved`
5. Approving all theme items transitions campaign status to `theme_approved`
6. All routes return 401 without auth header

**Tests to write:**

| Test ID | File | Assert |
|---|---|---|
| E3-S1-T1 | `src/Plant/BackEnd/tests/test_campaigns_api.py` (create) | POST create campaign → 201, `cost_estimate` present |
| E3-S1-T2 | same | GET theme items → all `pending_review` |
| E3-S1-T3 | same | Batch approve all → campaign status `theme_approved` |
| E3-S1-T4 | same | Patch single item → `approved` |
| E3-S1-T5 | same | No auth header → 401 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/test_campaigns_api.py -v \
  --cov=src/Plant/BackEnd/api/v1/campaigns --cov-fail-under=80
```

**Commit message:** `feat(plant-content-1): campaign create and theme list approval API`

**Done signal:** `"E3-S1 done. T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅."`

---

### Epic E4: Customer can review and approve individual posts before publishing

**Branch:** `feat/plant-content-1-it2-e4-post-approval-api`
**User story:** As a customer, once the theme list is approved, I trigger post generation for each day and review the platform-specific posts one by one (or in a batch) — so I see exactly what will be published before it goes live.

---

#### Story E4-S1: Post generation + post approval API — BACKEND

**BLOCKED UNTIL:** E3-S1 merged to `main`
**Estimated time:** 60 min
**Branch:** `feat/plant-content-1-it2-e4-post-approval-api`

**What to do:**
Add to `src/Plant/BackEnd/api/v1/campaigns.py`:
- `POST /api/v1/campaigns/{campaign_id}/theme-items/{item_id}/generate-posts` — calls `ContentCreatorSkill.generate_posts_for_theme()`, stores posts in memory
- `GET /api/v1/campaigns/{campaign_id}/posts` — list all posts with review/publish status, supports `?destination_type=` and `?review_status=` filters
- `PATCH /api/v1/campaigns/{campaign_id}/posts/{post_id}` — approve or reject a single post
- `POST /api/v1/campaigns/{campaign_id}/posts/approve` — batch approve posts

Add in-memory store: `_posts: dict[str, dict[str, ContentPost]] = {}` (campaign_id → {post_id → post})

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/campaigns.py` | all | In-memory store pattern already in use, router already registered — extend this file only |
| `src/Plant/BackEnd/agent_mold/skills/content_creator.py` | all | `generate_posts_for_theme(PostGeneratorInput)` API |
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | all | `ContentPost`, `PostGeneratorInput`, `ReviewStatus`, `PublishStatus` |

**Acceptance criteria:**
1. `POST .../theme-items/{item_id}/generate-posts` on an approved theme item returns post list, one per destination
2. `GET .../posts` returns all posts, filterable by `destination_type`
3. Batch approve posts sets all to `review_status=approved`
4. Attempting to generate posts for a `pending_review` theme item returns 409
5. All routes return 401 without auth

**Tests to write:**

| Test ID | File | Assert |
|---|---|---|
| E4-S1-T1 | `src/Plant/BackEnd/tests/test_campaigns_api.py` (extend) | generate-posts on approved theme item → posts created |
| E4-S1-T2 | same | generate-posts on pending theme item → 409 |
| E4-S1-T3 | same | GET posts with `?destination_type=linkedin` filters correctly |
| E4-S1-T4 | same | Batch approve posts → all `approved` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/test_campaigns_api.py -v \
  --cov=src/Plant/BackEnd/api/v1/campaigns --cov-fail-under=80
```

**Commit message:** `feat(plant-content-1): post generation and post approval API`

**Done signal:** `"E4-S1 done. T1 ✅ T2 ✅ T3 ✅ T4 ✅."`

---

## Iteration 3 — Publisher Engine (Plug-and-Play Destination Registry)

**Scope:** Build the `PublisherEngine` with a `DestinationRegistry` and a `SimulatedAdapter` (Phase 1). Add a `POST /api/v1/campaigns/{id}/posts/{post_id}/publish` route. Engine is designed so adding a new real platform = one new file + one registry entry.
**Lane:** B — all new files.
**⏱ Estimated:** 3.5h | **Come back:** 2026-03-06 14:00 UTC
**Prerequisite:** Iteration 2 merged to `main`

### Dependency Map (Iteration 3)

```
E5 (publisher engine + registry + simulated adapter) ──► independent
E6 (publish API route + scheduled publisher)          ──► BLOCKED UNTIL E5 merged
```

---

### Epic E5: Publisher engine with plug-and-play destination registry

**Branch:** `feat/plant-content-1-it3-e5-publisher-engine`
**User story:** As a platform engineer, I can add support for a new publishing destination by creating one file and adding one registry entry — without modifying any other code.

---

#### Story E5-S1: DestinationRegistry + DestinationAdapter ABC + SimulatedAdapter — BACKEND

**BLOCKED UNTIL:** Iteration 2 merged to `main`
**Estimated time:** 90 min
**Branch:** `feat/plant-content-1-it3-e5-publisher-engine`

**What to do:**
Create two files:
1. `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py` — `DestinationAdapter` ABC, `DestinationRegistry`, `PublisherEngine`
2. `src/Plant/BackEnd/agent_mold/skills/adapters_publish.py` — `SimulatedAdapter` (Phase 1 — marks post as published, returns fake receipt)

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | all | `PublishInput`, `PublishReceipt`, `ContentPost`, `PublishStatus` |
| `src/Plant/BackEnd/agent_mold/skills/adapters.py` | 1–80 | Existing channel adapter pattern (dataclasses, pure functions) |
| `src/Plant/BackEnd/agent_mold/skills/trading_executor.py` | 1–60 | Another executor pattern in the codebase for reference |

**Code pattern to copy exactly:**

`src/Plant/BackEnd/agent_mold/skills/publisher_engine.py`

```python
"""Publisher Engine — plug-and-play destination registry.

Adding a new publish destination:
1. Create a new file e.g. agent_mold/skills/adapters_linkedin.py
2. Define class LinkedInAdapter(DestinationAdapter)
3. Register: registry.register("linkedin", LinkedInAdapter)

The registry is populated at app startup from env config.
No other files need to change.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Optional, Type

from agent_mold.skills.content_models import PublishInput, PublishReceipt


class DestinationAdapter(ABC):
    """Abstract base class for all publish destination adapters.

    Every adapter must implement publish(). It receives a PublishInput
    and returns a PublishReceipt. It must be stateless — all auth
    credentials are referenced by key in inp.credential_ref.
    """

    DESTINATION_TYPE: str = ""  # Must be set by each subclass

    @abstractmethod
    def publish(self, inp: PublishInput) -> PublishReceipt:
        """Publish the post to the destination platform.

        Must be idempotent — calling twice with the same post_id
        must not create duplicate posts.
        """
        ...

    def estimate_cost(self, inp: PublishInput) -> float:
        """Optional: return cost in USD for this publish call. Default: free."""
        return 0.0


class DestinationRegistry:
    """Maps destination_type string → DestinationAdapter class.

    Thread-safe for reads (register only at startup).
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[DestinationAdapter]] = {}

    def register(self, destination_type: str, adapter_class: Type[DestinationAdapter]) -> None:
        self._registry[destination_type.lower()] = adapter_class

    def get(self, destination_type: str) -> Optional[Type[DestinationAdapter]]:
        return self._registry.get(destination_type.lower())

    def list_registered(self) -> list[str]:
        return list(self._registry.keys())

    def is_registered(self, destination_type: str) -> bool:
        return destination_type.lower() in self._registry


class PublisherEngine:
    """Orchestrates publishing across multiple destinations.

    Usage:
        engine = PublisherEngine(registry)
        receipt = engine.publish(publish_input)
    """

    def __init__(self, registry: DestinationRegistry) -> None:
        self._registry = registry

    def publish(self, inp: PublishInput) -> PublishReceipt:
        dest_type = inp.post.destination.destination_type.lower()
        adapter_class = self._registry.get(dest_type)
        if adapter_class is None:
            return PublishReceipt(
                post_id=inp.post.post_id,
                destination_type=dest_type,
                success=False,
                error=f"No adapter registered for destination_type '{dest_type}'. "
                      f"Registered: {self._registry.list_registered()}",
            )
        adapter = adapter_class()
        try:
            return adapter.publish(inp)
        except Exception as exc:
            return PublishReceipt(
                post_id=inp.post.post_id,
                destination_type=dest_type,
                success=False,
                error=str(exc),
            )


# ── Default registry (populated at module import) ─────────────────────────────
# Import adapters here and register. New adapters = add two lines below.

def build_default_registry() -> DestinationRegistry:
    from agent_mold.skills.adapters_publish import SimulatedAdapter
    registry = DestinationRegistry()
    registry.register("simulated", SimulatedAdapter)
    registry.register("x", SimulatedAdapter)          # X/Twitter: simulated in Phase 1
    registry.register("twitter", SimulatedAdapter)    # alias
    # Phase 2: uncomment when OAuth adapters are built
    # from agent_mold.skills.adapters_linkedin import LinkedInAdapter
    # registry.register("linkedin", LinkedInAdapter)
    return registry

default_registry = build_default_registry()
default_engine = PublisherEngine(default_registry)
```

`src/Plant/BackEnd/agent_mold/skills/adapters_publish.py`

```python
"""Phase 1 publish adapters.

SimulatedAdapter: always succeeds, returns a fake receipt.
Used for all destinations until real OAuth adapters are built.

To add a real adapter:
1. Create adapters_<platform>.py
2. class <Platform>Adapter(DestinationAdapter): DESTINATION_TYPE = "<platform>"
3. Register in publisher_engine.py build_default_registry()
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from agent_mold.skills.content_models import PublishInput, PublishReceipt
from agent_mold.skills.publisher_engine import DestinationAdapter


class SimulatedAdapter(DestinationAdapter):
    """Simulates a successful publish. Phase 1 stand-in for all real platforms.

    Returns a deterministic fake platform_post_id so tests are reproducible.
    Does NOT make any external HTTP calls.
    """
    DESTINATION_TYPE = "simulated"

    def publish(self, inp: PublishInput) -> PublishReceipt:
        fake_id = f"sim_{inp.post.post_id[:8]}"
        return PublishReceipt(
            post_id=inp.post.post_id,
            destination_type=inp.post.destination.destination_type,
            success=True,
            platform_post_id=fake_id,
            published_at=datetime.now(timezone.utc),
            raw_response={"simulated": True, "post_id": fake_id},
        )
```

**Acceptance criteria:**
1. `default_registry.is_registered("simulated")` returns `True`
2. `default_engine.publish(inp)` with `destination_type="simulated"` returns `PublishReceipt(success=True)`
3. `default_engine.publish(inp)` with `destination_type="unknown_platform"` returns `PublishReceipt(success=False)` — does NOT raise
4. Adding a new adapter requires only: new file + 2 lines in `build_default_registry()` — verified by code review

**Tests to write:**

| Test ID | File | Assert |
|---|---|---|
| E5-S1-T1 | `src/Plant/BackEnd/tests/test_publisher_engine.py` (create) | `SimulatedAdapter` publish → `success=True`, `platform_post_id` set |
| E5-S1-T2 | same | Unregistered destination type → `success=False`, no exception raised |
| E5-S1-T3 | same | `registry.list_registered()` includes `"simulated"` |
| E5-S1-T4 | same | `SimulatedAdapter().estimate_cost(inp) == 0.0` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/test_publisher_engine.py -v \
  --cov=src/Plant/BackEnd/agent_mold/skills/publisher_engine \
  --cov=src/Plant/BackEnd/agent_mold/skills/adapters_publish \
  --cov-fail-under=85
```

**Commit message:** `feat(plant-content-1): publisher engine with plug-and-play destination registry`

**Done signal:** `"E5-S1 done. T1 ✅ T2 ✅ T3 ✅ T4 ✅."`

---

### Epic E6: Customer can publish approved posts on schedule

**Branch:** `feat/plant-content-1-it3-e6-publish-api`
**User story:** As a customer, once I approve a post, it gets published to the destination at the scheduled time — and I can see the publish receipt immediately on-demand publish, or wait for the scheduler to fire.

---

#### Story E6-S1: Publish API route (immediate + scheduled) — BACKEND

**BLOCKED UNTIL:** E5-S1 merged to `main`
**Estimated time:** 60 min
**Branch:** `feat/plant-content-1-it3-e6-publish-api`

**What to do:**
Add to `src/Plant/BackEnd/api/v1/campaigns.py`:
- `POST /api/v1/campaigns/{campaign_id}/posts/{post_id}/publish` — immediately publish one approved post via `default_engine`; update `post.publish_status` and `post.publish_receipt` in-memory
- `POST /api/v1/campaigns/{campaign_id}/publish-due` — publish all posts where `review_status=approved` AND `scheduled_publish_at <= now UTC` — batch action for scheduler/cron

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/campaigns.py` | all | In-memory `_posts` dict, existing route patterns, auth dependency wiring |
| `src/Plant/BackEnd/agent_mold/skills/publisher_engine.py` | all | `default_engine.publish(PublishInput)` API |
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | 60–100 (PublishInput, PublishReceipt) | Request/response models |

**Acceptance criteria:**
1. `POST .../publish` on an approved post returns `PublishReceipt(success=True)` and sets `post.publish_status = "published"`
2. `POST .../publish` on an unapproved post returns 409
3. `POST .../publish` on an already-published post returns 409 (idempotency guard)
4. `POST .../publish-due` publishes all eligible posts and returns count
5. All routes return 401 without auth

**Tests to write:**

| Test ID | File | Assert |
|---|---|---|
| E6-S1-T1 | `src/Plant/BackEnd/tests/test_campaigns_api.py` (extend) | Publish approved post → `success=True`, status `published` |
| E6-S1-T2 | same | Publish unapproved post → 409 |
| E6-S1-T3 | same | Publish already-published → 409 |
| E6-S1-T4 | same | `publish-due` publishes all eligible, returns count > 0 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/test_campaigns_api.py -v \
  --cov=src/Plant/BackEnd/api/v1/campaigns --cov-fail-under=80
```

**Commit message:** `feat(plant-content-1): publish API route with idempotency guard`

**Done signal:** `"E6-S1 done. T1 ✅ T2 ✅ T3 ✅ T4 ✅."`

---

## Iteration 4 — CP BackEnd Proxy Routes + Skill Registration

**Scope:** CP BackEnd thin proxy routes for campaign CRUD + skill registration in `agent_mold/registry.py` so the content creator and publisher skills appear in agent catalogs.
**Lane:** B — all new files.
**⏱ Estimated:** 2.5h | **Come back:** 2026-03-06 17:00 UTC
**Prerequisite:** Iteration 3 merged to `main`

### Dependency Map (Iteration 4)

```
E7 (skill registration in agent catalog) ──► independent
E8 (CP BackEnd proxy routes for campaigns) ──► independent
```

---

### Epic E7: Content creator and publisher skills appear in agent skill catalog

**Branch:** `feat/plant-content-1-it4-e7-skill-registration`
**User story:** As a platform operator, the content creator and publisher appear as registered skills in the agent catalog — so any agent can be configured to use them without code changes.

---

#### Story E7-S1: Register content.creator.v1 and content.publisher.v1 in skill registry — BACKEND

**BLOCKED UNTIL:** Iteration 3 merged to `main`
**Estimated time:** 30 min
**Branch:** `feat/plant-content-1-it4-e7-skill-registration`

**What to do:**
Open `src/Plant/BackEnd/agent_mold/registry.py`. Add two new skill entries following the exact pattern of existing skills in that file:
- `content.creator.v1` — category `CONTENT`, name `Content Creator`, description as below
- `content.publisher.v1` — category `CONTENT`, name `Content Publisher`, description as below

If the `SkillCategory` enum in `playbook.py` does not have `CONTENT`, add it there first.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/registry.py` | all | Exact pattern for adding a new skill entry — copy precisely |
| `src/Plant/BackEnd/agent_mold/skills/playbook.py` | 1–30 | `SkillCategory` enum — check if `CONTENT` exists, add if not |
| `src/Plant/BackEnd/agent_mold/skills/content_models.py` | 1–20 | `ContentCreatorSkill.SKILL_ID` value |

**Skill definitions to add:**
```python
# In registry.py — follow existing skill entry pattern exactly

SkillRegistryEntry(
    skill_id="content.creator.v1",
    name="Content Creator",
    category=SkillCategory.CONTENT,
    description=(
        "Generates a full content calendar and platform-specific posts from a campaign brief. "
        "Supports Grok LLM (XAI_API_KEY) or deterministic mode. "
        "Outputs: DailyThemeList + ContentPosts + CostEstimate."
    ),
    version="1.0.0",
    required_config_keys=[],           # no mandatory config — XAI_API_KEY is optional
    optional_config_keys=["executor_backend", "xai_api_key"],
),

SkillRegistryEntry(
    skill_id="content.publisher.v1",
    name="Content Publisher",
    category=SkillCategory.CONTENT,
    description=(
        "Publishes approved ContentPosts to registered destinations via the DestinationRegistry. "
        "Phase 1: simulated adapter. Phase 2: platform OAuth adapters (LinkedIn, Instagram, YouTube). "
        "Plug-and-play — new platform = new file + registry entry."
    ),
    version="1.0.0",
    required_config_keys=[],
    optional_config_keys=["destination_type", "credential_ref"],
),
```

**Acceptance criteria:**
1. `from agent_mold.registry import skill_registry; skill_registry.get("content.creator.v1")` returns entry
2. `skill_registry.get("content.publisher.v1")` returns entry
3. Existing skill entries are unchanged

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/ -k "registry" -v
```

**Commit message:** `feat(plant-content-1): register content creator and publisher skills in agent catalog`

**Done signal:** `"E7-S1 done. content.creator.v1 ✅ content.publisher.v1 ✅."`

---

### Epic E8: CP BackEnd proxies campaign endpoints so CP Frontend can use them

**Branch:** `feat/plant-content-1-it4-e8-cp-proxy`
**User story:** As a CP FrontEnd engineer, I can call campaign endpoints via the CP BackEnd proxy — so CP never calls Plant directly.

---

#### Story E8-S1: CP BackEnd campaign proxy routes — BACKEND

**BLOCKED UNTIL:** Iteration 3 merged to `main`
**Estimated time:** 60 min
**Branch:** `feat/plant-content-1-it4-e8-cp-proxy`

**What to do:**
Create `src/CP/BackEnd/api/campaigns.py`. Register router in `src/CP/BackEnd/main_proxy.py`. Proxy all 8 Plant campaign endpoints. Add 4 new methods to `src/CP/BackEnd/clients/plant_client.py`.

Plant endpoints to proxy (all exist after Iteration 3):
- `POST /api/v1/campaigns`
- `GET /api/v1/campaigns/{id}`
- `GET /api/v1/campaigns/{id}/theme-items`
- `POST /api/v1/campaigns/{id}/theme-items/approve`
- `PATCH /api/v1/campaigns/{id}/theme-items/{item_id}`
- `POST /api/v1/campaigns/{id}/theme-items/{item_id}/generate-posts`
- `GET /api/v1/campaigns/{id}/posts`
- `PATCH /api/v1/campaigns/{id}/posts/{post_id}`
- `POST /api/v1/campaigns/{id}/posts/{post_id}/publish`

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/api/genesis.py` | 1–60 | Exact import pattern, `waooaw_router`, `require_auth`, `get_authorization_header`, `PlantAPIClient` usage |
| `src/CP/BackEnd/clients/plant_client.py` | 270–380 | `_get`, `_post`, `_patch` helper methods — copy exactly for new methods |
| `src/CP/BackEnd/main_proxy.py` | 1–30 | `app.include_router(...)` lines |

**NFR code patterns to embed (copy from genesis.py):**
```python
from core.routing import waooaw_router
from api.security import require_auth          # customer auth (not require_admin)
from api.deps import get_authorization_header
from clients.plant_client import PlantAPIClient, PlantAPIError, get_plant_client
from services.audit_dependency import AuditLogger, get_audit_logger
import logging as _logging
_logger = _logging.getLogger(__name__)         # PIIMaskingFilter applied at app startup

router = waooaw_router(prefix="/campaigns", tags=["campaigns"])
```

**Acceptance criteria:**
1. `POST /campaigns` with valid customer JWT proxies to Plant and returns 201
2. All routes return 401 without customer JWT
3. All routes return 502 when Plant is unreachable
4. `grep "campaigns" src/CP/BackEnd/main_proxy.py` returns a match

**Tests to write:**

| Test ID | File | Assert |
|---|---|---|
| E8-S1-T1 | `src/CP/BackEnd/tests/test_campaigns_proxy.py` (create) | Mock Plant `POST /api/v1/campaigns` → 201, CP proxies it |
| E8-S1-T2 | same | No auth header → 401 |
| E8-S1-T3 | same | Plant unreachable → 502 |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-test \
  pytest src/CP/BackEnd/tests/test_campaigns_proxy.py -v \
  --cov=src/CP/BackEnd/api/campaigns --cov-fail-under=80
```

**Commit message:** `feat(plant-content-1): CP BackEnd campaign proxy routes`

**Done signal:** `"E8-S1 done. T1 ✅ T2 ✅ T3 ✅. campaigns router registered in CP main_proxy."`

---

## Skills Inventory Entry (for README / skill catalog)

```
┌─────────────────────────────────────────────────────────────────┐
│  SKILL: content.creator.v1                                       │
│  Category: CONTENT  |  Version: 1.0.0                           │
│  Engine: Grok-3 (EXECUTOR_BACKEND=grok) | deterministic default │
│  Cost: ₹0 on Grok free tier                                     │
│  Input:  CampaignBrief (theme, days, platforms, schedule)        │
│  Output: DailyThemeList + CostEstimate                           │
│  Plug-in point: any agent via skill_registry.get("content.creator.v1") │
├─────────────────────────────────────────────────────────────────┤
│  SKILL: content.publisher.v1                                     │
│  Category: CONTENT  |  Version: 1.0.0                           │
│  Engine: DestinationRegistry (plug-and-play adapters)            │
│  Phase 1 adapters: simulated (all platforms)                     │
│  Phase 2 adapters: linkedin, instagram, youtube, facebook, x     │
│  Input:  ApprovedContentPost + DestinationRef                    │
│  Output: PublishReceipt                                          │
│  Add new platform: 1 file + 2 lines in build_default_registry() │
└─────────────────────────────────────────────────────────────────┘
```
