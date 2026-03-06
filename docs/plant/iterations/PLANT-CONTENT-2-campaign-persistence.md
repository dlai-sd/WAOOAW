# PLANT-CONTENT-2 — Campaign Persistence (in-memory → PostgreSQL)

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-CONTENT-2` |
| Feature area | Plant BackEnd — `models/campaign.py` + Alembic migration `026` + `api/v1/campaign_repository.py` + feature-flag swap in `api/v1/campaigns.py` |
| Created | 2026-03-06 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/plant/iterations/PLANT-CONTENT-1-content-creator-publisher.md` (Agent Execution Rule 6: "Use in-memory stores for Phase 1. Do NOT add new database migrations in this plan.") |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 4 |
| Total stories | 5 |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story — agent never opens NFRReusable.md |
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
- [x] `waooaw_router()` — no new routes in this plan; existing router (`campaigns.py`) is updated in-place
- [x] `PIIMaskingFilter` — campaigns.py already has one; no change needed
- [x] `get_read_db_session` for GET routes (embedded in S2.1 snippet)
- [x] `get_db_session` for write routes (embedded in S2.1 snippet)
- [x] Every story involving CP BackEnd — not applicable (all Plant BackEnd)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has time estimate and come-back datetime
- [x] STUCK PROTOCOL is in Agent Execution Rules
- [x] Lane A (wire existing routes) — this plan is one lane: DB migration
- [x] No placeholders remain

---

## Vision Intake (confirmed)

1. **Area:** Plant BackEnd — persistence layer for the three in-memory stores (`_campaigns`, `_theme_items`, `_posts`) introduced in PLANT-CONTENT-1.
2. **User outcome:** Campaign data (briefs, theme items, content posts) survives service restarts, Cloud Run cold starts, and horizontal scaling; customer-facing APIs return the same state across any instance.
3. **Out of scope:** Real social platform OAuth (Phase 2). CP FrontEnd campaign screens (separate plan). Any change to LLM generation or publisher engine logic. New API routes — only persistence layer changes.
4. **Lane:** A — all routes already exist; this plan adds the DB layer and switches existing routes to use it.
5. **Urgency:** Before production rollout of campaigns feature.

---

## Architecture Decision Record (read before coding)

### What was built in PLANT-CONTENT-1 (context, do not change)

`src/Plant/BackEnd/api/v1/campaigns.py` has three module-level in-memory dicts:

```python
_campaigns: dict[str, Campaign] = {}
_theme_items: dict[str, dict[str, DailyThemeItem]] = {}  # campaign_id → {item_id → item}
_posts: dict[str, dict[str, ContentPost]] = {}            # campaign_id → {post_id → post}
```

These power 12 endpoints. All LLM generation and publisher engine logic live in
`agent_mold/skills/content_creator.py` and `agent_mold/skills/publisher_engine.py`.

### Migration approach — feature flag, zero downtime

Identical to the `DELIVERABLE_PERSISTENCE_MODE` pattern in `deliverables_simple.py`:

```python
CAMPAIGN_PERSISTENCE_MODE = os.getenv("CAMPAIGN_PERSISTENCE_MODE", "memory").lower()
# "memory"  → existing in-memory dicts (default, backward-compatible)
# "db"      → CampaignRepository backed by PostgreSQL via AsyncSession
```

Two async dependency helpers are added to `campaigns.py`:

```python
async def _get_write_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Yield DB session for write operations; yield None in memory mode."""
    if CAMPAIGN_PERSISTENCE_MODE != "db":
        yield None
        return
    async for session in get_db_session():
        yield session

async def _get_read_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Yield read-replica session for GET operations; yield None in memory mode."""
    if CAMPAIGN_PERSISTENCE_MODE != "db":
        yield None
        return
    async for session in get_read_db_session():
        yield session
```

Each endpoint receives `db: Optional[AsyncSession] = Depends(_get_write_db)` (or `_get_read_db` for GETs).
When `db is not None`, it uses `CampaignRepository(db)`. When `db is None`, it uses the original dict logic (unchanged).

### New tables

| Table | Maps from | PK | Key columns |
|---|---|---|---|
| `campaigns` | `Campaign` Pydantic model | `campaign_id` (str) | `hired_instance_id`, `customer_id`, `brief` (JSONB), `cost_estimate` (JSONB), `status` |
| `daily_theme_items` | `DailyThemeItem` Pydantic model | `theme_item_id` (str) | `campaign_id` (FK), `day_number`, `scheduled_date` (Date), `theme_title`, `theme_description`, `dimensions` (JSONB), `review_status`, `approved_at` |
| `content_posts` | `ContentPost` Pydantic model | `post_id` (str) | `campaign_id` (FK), `theme_item_id` (FK), `destination` (JSONB), `content_text`, `hashtags` (JSONB), `scheduled_publish_at`, `review_status`, `publish_status`, `publish_receipt` (JSONB), `created_at`, `updated_at` |

All FKs use `ondelete="CASCADE"`. No circular FKs.

### Repository contract

```
CampaignRepository(db: AsyncSession)
├── create_campaign(c: Campaign) -> Campaign
├── get_campaign(campaign_id: str) -> Campaign | None
├── update_campaign(c: Campaign) -> Campaign
├── list_campaigns(customer_id: str, hired_instance_id: Optional[str]) -> list[Campaign]
├── save_theme_items(items: list[DailyThemeItem]) -> None
├── get_theme_items(campaign_id: str) -> list[DailyThemeItem]
├── update_theme_item(item: DailyThemeItem) -> DailyThemeItem
├── save_post(post: ContentPost) -> ContentPost
├── get_posts(campaign_id, review_status=None, publish_status=None) -> list[ContentPost]
├── get_post(post_id: str) -> ContentPost | None
└── update_post(post: ContentPost) -> ContentPost
```

Every method converts between ORM model and Pydantic model internally.
Routes never touch ORM models directly.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | ORM models + Alembic migration + Repository layer | E1, E2 | 3 | 3h | 2026-03-06 22:00 UTC |
| 2 | Wire `campaigns.py` to repository + integration tests | E3, E4 | 2 | 3h | 2026-03-07 01:00 UTC |

**Estimate basis:** New ORM model file = 45 min | Alembic migration = 45 min | Repository class = 90 min | Route wiring = 90 min | Integration tests = 60 min. Add 20% buffer.

---

## Agent Execution Rules

1. **Start**: `git status && git log --oneline -3` — must be on `main` with clean tree.
2. **Branch**: create the exact branch listed in the story card before touching any file.
3. **Test**: run the exact test command in each story card before marking done.
4. **STUCK PROTOCOL**: If blocked for more than 15 min on a single story, open a draft PR titled `WIP: PLANT-CONTENT-2 [story-id] — [blocker description]`. Post the PR URL, then HALT.
5. **PR**: One PR per iteration. Title: `feat(plant-content-2): iteration N — [scope]`.
6. **CHECKPOINT RULE**: After completing each epic (all tests passing), run:
   ```bash
   git add -A && git commit -m "feat(plant-content-2): [epic-id] — [epic title]" && git push
   ```
   Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.
7. **Never rename `campaigns.py`** — this plan updates it in-place. The router registration in `api/v1/router.py` stays unchanged.
8. **Feature flag default is `"memory"`** — existing tests continue to work without any env var changes.
9. **`hired_agents` FK is soft** — `hired_instance_id` on the `campaigns` table does NOT have a DB-level FK to `hired_agents` (hired agents are the in-memory source of truth for Phase 1). Assert it only as a NOT NULL string.

---

## Iteration 1 — ORM Models + Migration + Repository

### Epic E1: Campaign data survives service restarts (ORM + Migration)

---

#### Story E1-S1 — SQLAlchemy ORM models for Campaign, DailyThemeItem, ContentPost

| Field | Value |
|---|---|
| Story ID | E1-S1 |
| Branch | `feat/plant-content-2-e1s1-orm-models` |
| Time budget | 45 min |
| BLOCKED UNTIL | none |

**What to build**

Create `src/Plant/BackEnd/models/campaign.py` with three SQLAlchemy ORM models.
Update `src/Plant/BackEnd/models/__init__.py` to export all three.

**Files to read first (max 3)**

1. `src/Plant/BackEnd/models/deliverable.py` — full ORM model pattern (Column types, FK syntax, Index, Base import)
2. `src/Plant/BackEnd/agent_mold/skills/content_models.py` — Pydantic models that these ORM models mirror
3. `src/Plant/BackEnd/models/__init__.py` — where to add the new imports and `__all__` exports

**Code pattern to copy exactly**

```python
# src/Plant/BackEnd/models/campaign.py
"""SQLAlchemy ORM models for content campaign persistence.

Tables: campaigns, daily_theme_items, content_posts
Alembic migration: 026_campaign_tables.py
Pydantic counterparts: CampaignBrief, Campaign, DailyThemeItem, ContentPost
  (all in agent_mold/skills/content_models.py)
"""
from __future__ import annotations

from sqlalchemy import (
    Column, String, Text, JSON, DateTime, Date, Integer, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from core.database import Base


class CampaignModel(Base):
    __tablename__ = "campaigns"

    campaign_id       = Column(String, primary_key=True)
    hired_instance_id = Column(String, nullable=False, index=True)
    customer_id       = Column(String, nullable=False, index=True)
    brief             = Column(JSON, nullable=False)          # JSONB – CampaignBrief
    cost_estimate     = Column(JSON, nullable=False)          # JSONB – CostEstimate
    status            = Column(String, nullable=False, default="draft", index=True)
    created_at        = Column(DateTime(timezone=True), nullable=False)
    updated_at        = Column(DateTime(timezone=True), nullable=False)

    theme_items = relationship(
        "DailyThemeItemModel", back_populates="campaign", cascade="all, delete-orphan"
    )
    posts = relationship(
        "ContentPostModel", back_populates="campaign", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_campaigns_customer_id", "customer_id"),
        Index("ix_campaigns_hired_instance", "hired_instance_id"),
        Index("ix_campaigns_status", "status"),
    )


class DailyThemeItemModel(Base):
    __tablename__ = "daily_theme_items"

    theme_item_id    = Column(String, primary_key=True)
    campaign_id      = Column(
        String, ForeignKey("campaigns.campaign_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    day_number        = Column(Integer, nullable=False)
    scheduled_date    = Column(Date, nullable=False)
    theme_title       = Column(String, nullable=False)
    theme_description = Column(Text, nullable=False)
    dimensions        = Column(JSON, nullable=False, default=list)  # list[str]
    review_status     = Column(String, nullable=False, default="pending_review", index=True)
    approved_at       = Column(DateTime(timezone=True), nullable=True)

    campaign = relationship("CampaignModel", back_populates="theme_items")

    __table_args__ = (
        Index("ix_theme_items_campaign", "campaign_id"),
        Index("ix_theme_items_review_status", "review_status"),
    )


class ContentPostModel(Base):
    __tablename__ = "content_posts"

    post_id              = Column(String, primary_key=True)
    campaign_id          = Column(
        String, ForeignKey("campaigns.campaign_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    theme_item_id        = Column(
        String, ForeignKey("daily_theme_items.theme_item_id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    destination          = Column(JSON, nullable=False)        # DestinationRef
    content_text         = Column(Text, nullable=False)
    hashtags             = Column(JSON, nullable=False, default=list)  # list[str]
    scheduled_publish_at = Column(DateTime(timezone=True), nullable=False)
    review_status        = Column(String, nullable=False, default="pending_review", index=True)
    publish_status       = Column(String, nullable=False, default="not_published", index=True)
    publish_receipt      = Column(JSON, nullable=True)
    created_at           = Column(DateTime(timezone=True), nullable=False)
    updated_at           = Column(DateTime(timezone=True), nullable=False)

    campaign   = relationship("CampaignModel", back_populates="posts")
    theme_item = relationship("DailyThemeItemModel")

    __table_args__ = (
        Index("ix_posts_campaign_id", "campaign_id"),
        Index("ix_posts_theme_item_id", "theme_item_id"),
        Index("ix_posts_review_status", "review_status"),
        Index("ix_posts_publish_status", "publish_status"),
    )
```

After creating `models/campaign.py`, update `models/__init__.py`:
- Add `from models.campaign import CampaignModel, DailyThemeItemModel, ContentPostModel`
- Add all three to `__all__`

**Create a minimal unit test** `src/Plant/BackEnd/tests/unit/test_campaign_models.py`:

```python
"""Smoke test: ORM models import cleanly and have correct __tablename__."""
from models.campaign import CampaignModel, DailyThemeItemModel, ContentPostModel

def test_tablenames():
    assert CampaignModel.__tablename__ == "campaigns"
    assert DailyThemeItemModel.__tablename__ == "daily_theme_items"
    assert ContentPostModel.__tablename__ == "content_posts"

def test_campaign_pk():
    assert CampaignModel.__table__.primary_key.columns.keys() == ["campaign_id"]

def test_post_fks():
    fk_cols = {c.target_fullname for fk in ContentPostModel.__table__.foreign_keys for c in [fk]}
    # campaigns.campaign_id and daily_theme_items.theme_item_id must be present
    targets = {fk.target_fullname for fk in ContentPostModel.__table__.foreign_keys}
    assert "campaigns.campaign_id" in targets
    assert "daily_theme_items.theme_item_id" in targets
```

**Test command**

```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/unit/test_campaign_models.py -v
```

**Acceptance criteria**

- [ ] `models/campaign.py` exists with `CampaignModel`, `DailyThemeItemModel`, `ContentPostModel`
- [ ] `models/__init__.py` exports all three
- [ ] `pytest tests/unit/test_campaign_models.py` — all tests pass
- [ ] No import errors on `from models.campaign import ...`

---

#### Story E1-S2 — Alembic migration 026: create campaigns, daily_theme_items, content_posts tables

| Field | Value |
|---|---|
| Story ID | E1-S2 |
| Branch | `feat/plant-content-2-e1s2-migration` |
| Time budget | 45 min |
| BLOCKED UNTIL | E1-S1 merged |

**What to build**

Create `src/Plant/BackEnd/database/migrations/versions/026_campaign_tables.py`.
This is a pure Alembic migration — no changes to Python application code.

**Files to read first (max 3)**

1. `src/Plant/BackEnd/database/migrations/versions/012_deliverables_and_approvals.py` — full migration pattern (create_table, op.create_index, ForeignKeyConstraint, downgrade)
2. `src/Plant/BackEnd/models/campaign.py` — the ORM models this migration materialises (created in E1-S1)
3. `src/Plant/BackEnd/tests/integration/test_alembic_migrations.py` — check what the CI migration test expects

**Code pattern to copy exactly**

```python
# src/Plant/BackEnd/database/migrations/versions/026_campaign_tables.py
"""create_campaign_tables

Revision ID: 026_campaign_tables
Revises: 025_agent_skill_goal_config
Create Date: 2026-03-06

Purpose: Persist Campaign, DailyThemeItem, ContentPost from PLANT-CONTENT-1
         in-memory stores to PostgreSQL.
         Enabled by CAMPAIGN_PERSISTENCE_MODE=db env var.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision      = "026_campaign_tables"
down_revision = "025_agent_skill_goal_config"
branch_labels = None
depends_on    = None


def upgrade() -> None:
    # 1. campaigns table
    op.create_table(
        "campaigns",
        sa.Column("campaign_id",       sa.String(), nullable=False),
        sa.Column("hired_instance_id", sa.String(), nullable=False),
        sa.Column("customer_id",       sa.String(), nullable=False),
        sa.Column("brief",             postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cost_estimate",     postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status",            sa.String(), nullable=False, server_default="draft"),
        sa.Column("created_at",        sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at",        sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("campaign_id", name="pk_campaigns"),
    )
    op.create_index("ix_campaigns_customer_id",     "campaigns", ["customer_id"])
    op.create_index("ix_campaigns_hired_instance",  "campaigns", ["hired_instance_id"])
    op.create_index("ix_campaigns_status",          "campaigns", ["status"])

    # 2. daily_theme_items table
    op.create_table(
        "daily_theme_items",
        sa.Column("theme_item_id",    sa.String(), nullable=False),
        sa.Column("campaign_id",      sa.String(), nullable=False),
        sa.Column("day_number",       sa.Integer(), nullable=False),
        sa.Column("scheduled_date",   sa.Date(),   nullable=False),
        sa.Column("theme_title",      sa.String(), nullable=False),
        sa.Column("theme_description",sa.Text(),   nullable=False),
        sa.Column("dimensions",       postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("review_status",    sa.String(), nullable=False, server_default="pending_review"),
        sa.Column("approved_at",      sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("theme_item_id", name="pk_daily_theme_items"),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.campaign_id"],
            name="fk_theme_items_campaign", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_theme_items_campaign",      "daily_theme_items", ["campaign_id"])
    op.create_index("ix_theme_items_review_status", "daily_theme_items", ["review_status"])

    # 3. content_posts table
    op.create_table(
        "content_posts",
        sa.Column("post_id",              sa.String(), nullable=False),
        sa.Column("campaign_id",          sa.String(), nullable=False),
        sa.Column("theme_item_id",        sa.String(), nullable=False),
        sa.Column("destination",          postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("content_text",         sa.Text(),   nullable=False),
        sa.Column("hashtags",             postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("scheduled_publish_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("review_status",        sa.String(), nullable=False, server_default="pending_review"),
        sa.Column("publish_status",       sa.String(), nullable=False, server_default="not_published"),
        sa.Column("publish_receipt",      postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at",           sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at",           sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("post_id", name="pk_content_posts"),
        sa.ForeignKeyConstraint(
            ["campaign_id"], ["campaigns.campaign_id"],
            name="fk_posts_campaign", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["theme_item_id"], ["daily_theme_items.theme_item_id"],
            name="fk_posts_theme_item", ondelete="CASCADE",
        ),
    )
    op.create_index("ix_posts_campaign_id",    "content_posts", ["campaign_id"])
    op.create_index("ix_posts_theme_item_id",  "content_posts", ["theme_item_id"])
    op.create_index("ix_posts_review_status",  "content_posts", ["review_status"])
    op.create_index("ix_posts_publish_status", "content_posts", ["publish_status"])


def downgrade() -> None:
    # Drop in reverse FK order
    op.drop_index("ix_posts_publish_status", table_name="content_posts")
    op.drop_index("ix_posts_review_status",  table_name="content_posts")
    op.drop_index("ix_posts_theme_item_id",  table_name="content_posts")
    op.drop_index("ix_posts_campaign_id",    table_name="content_posts")
    op.drop_table("content_posts")

    op.drop_index("ix_theme_items_review_status", table_name="daily_theme_items")
    op.drop_index("ix_theme_items_campaign",      table_name="daily_theme_items")
    op.drop_table("daily_theme_items")

    op.drop_index("ix_campaigns_status",         table_name="campaigns")
    op.drop_index("ix_campaigns_hired_instance", table_name="campaigns")
    op.drop_index("ix_campaigns_customer_id",    table_name="campaigns")
    op.drop_table("campaigns")
```

**Test command**

```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/integration/test_alembic_migrations.py -v
```

**Acceptance criteria**

- [ ] `026_campaign_tables.py` exists with correct `revision` and `down_revision = "025_agent_skill_goal_config"`
- [ ] `upgrade()` creates all 3 tables with correct columns, FKs, and indexes
- [ ] `downgrade()` drops all tables and indexes cleanly
- [ ] Alembic migration integration test passes

---

### Epic E2: Campaign reads and writes go through a typed async repository

---

#### Story E2-S1 — `CampaignRepository`: async CRUD class + unit tests

| Field | Value |
|---|---|
| Story ID | E2-S1 |
| Branch | `feat/plant-content-2-e2s1-repository` |
| Time budget | 90 min |
| BLOCKED UNTIL | E1-S1 merged (E1-S2 can be in-flight) |

**What to build**

Create `src/Plant/BackEnd/api/v1/campaign_repository.py` — a pure data-access class.
It receives an `AsyncSession`, performs all DB operations, and always returns Pydantic objects
(never ORM model instances outside this file).

Create `src/Plant/BackEnd/tests/unit/test_campaign_repository.py` — unit tests using
an in-process SQLite async engine (no Docker required).

**Files to read first (max 3)**

1. `src/Plant/BackEnd/api/v1/platform_connections.py` — async `select()`, `db.add()`, `db.flush()`, `db.execute()` pattern
2. `src/Plant/BackEnd/models/campaign.py` — ORM models to query (columns, FK names)
3. `src/Plant/BackEnd/agent_mold/skills/content_models.py` — Pydantic models to return (Campaign, DailyThemeItem, ContentPost, exact field names)

**Code pattern to copy exactly**

```python
# src/Plant/BackEnd/api/v1/campaign_repository.py
"""CampaignRepository — async PostgreSQL CRUD for campaigns, theme items, posts.

Used by campaigns.py when CAMPAIGN_PERSISTENCE_MODE=db.
Returns Pydantic domain objects; never exposes ORM models outside this file.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.skills.content_models import (
    Campaign,
    CampaignStatus,
    ContentPost,
    DailyThemeItem,
    ReviewStatus,
    PublishStatus,
)
from core.logging import PiiMaskingFilter
from models.campaign import CampaignModel, ContentPostModel, DailyThemeItemModel

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── ORM → Pydantic converters ─────────────────────────────────────────────────

def _to_campaign(m: CampaignModel) -> Campaign:
    return Campaign.model_validate({
        "campaign_id":       m.campaign_id,
        "hired_instance_id": m.hired_instance_id,
        "customer_id":       m.customer_id,
        "brief":             m.brief,
        "cost_estimate":     m.cost_estimate,
        "status":            m.status,
        "created_at":        m.created_at,
        "updated_at":        m.updated_at,
    })


def _to_theme_item(m: DailyThemeItemModel) -> DailyThemeItem:
    return DailyThemeItem.model_validate({
        "theme_item_id":    m.theme_item_id,
        "campaign_id":      m.campaign_id,
        "day_number":       m.day_number,
        "scheduled_date":   m.scheduled_date,
        "theme_title":      m.theme_title,
        "theme_description":m.theme_description,
        "dimensions":       m.dimensions or [],
        "review_status":    m.review_status,
        "approved_at":      m.approved_at,
    })


def _to_post(m: ContentPostModel) -> ContentPost:
    return ContentPost.model_validate({
        "post_id":              m.post_id,
        "campaign_id":          m.campaign_id,
        "theme_item_id":        m.theme_item_id,
        "destination":          m.destination,
        "content_text":         m.content_text,
        "hashtags":             m.hashtags or [],
        "scheduled_publish_at": m.scheduled_publish_at,
        "review_status":        m.review_status,
        "publish_status":       m.publish_status,
        "publish_receipt":      m.publish_receipt,
        "created_at":           m.created_at,
        "updated_at":           m.updated_at,
    })


# ── Repository ────────────────────────────────────────────────────────────────

class CampaignRepository:
    """Async CRUD for campaigns, daily_theme_items, content_posts tables."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Campaign ──────────────────────────────────────────────────────────────

    async def create_campaign(self, c: Campaign) -> Campaign:
        m = CampaignModel(
            campaign_id       = c.campaign_id,
            hired_instance_id = c.hired_instance_id,
            customer_id       = c.customer_id,
            brief             = c.brief.model_dump(mode="json"),
            cost_estimate     = c.cost_estimate.model_dump(mode="json"),
            status            = c.status.value,
            created_at        = c.created_at,
            updated_at        = c.updated_at,
        )
        self._db.add(m)
        await self._db.flush()
        logger.info("campaign created campaign_id=%s customer_id=%s", c.campaign_id, c.customer_id)
        return _to_campaign(m)

    async def get_campaign(self, campaign_id: str) -> Campaign | None:
        result = await self._db.execute(
            select(CampaignModel).where(CampaignModel.campaign_id == campaign_id)
        )
        m = result.scalar_one_or_none()
        return _to_campaign(m) if m else None

    async def update_campaign(self, c: Campaign) -> Campaign:
        result = await self._db.execute(
            select(CampaignModel).where(CampaignModel.campaign_id == c.campaign_id)
        )
        m = result.scalar_one_or_none()
        if m is None:
            raise KeyError(f"Campaign {c.campaign_id!r} not found")
        m.status     = c.status.value
        m.updated_at = _now()
        await self._db.flush()
        return _to_campaign(m)

    async def list_campaigns(
        self,
        customer_id: str,
        hired_instance_id: Optional[str] = None,
    ) -> list[Campaign]:
        stmt = select(CampaignModel).where(CampaignModel.customer_id == customer_id)
        if hired_instance_id:
            stmt = stmt.where(CampaignModel.hired_instance_id == hired_instance_id)
        result = await self._db.execute(stmt.order_by(CampaignModel.created_at.desc()))
        return [_to_campaign(m) for m in result.scalars().all()]

    # ── Theme items ───────────────────────────────────────────────────────────

    async def save_theme_items(self, items: list[DailyThemeItem]) -> None:
        for item in items:
            self._db.add(DailyThemeItemModel(
                theme_item_id    = item.theme_item_id,
                campaign_id      = item.campaign_id,
                day_number       = item.day_number,
                scheduled_date   = item.scheduled_date,
                theme_title      = item.theme_title,
                theme_description= item.theme_description,
                dimensions       = item.dimensions,
                review_status    = item.review_status.value,
                approved_at      = item.approved_at,
            ))
        await self._db.flush()

    async def get_theme_items(self, campaign_id: str) -> list[DailyThemeItem]:
        result = await self._db.execute(
            select(DailyThemeItemModel)
            .where(DailyThemeItemModel.campaign_id == campaign_id)
            .order_by(DailyThemeItemModel.day_number)
        )
        return [_to_theme_item(m) for m in result.scalars().all()]

    async def update_theme_item(self, item: DailyThemeItem) -> DailyThemeItem:
        result = await self._db.execute(
            select(DailyThemeItemModel)
            .where(DailyThemeItemModel.theme_item_id == item.theme_item_id)
        )
        m = result.scalar_one_or_none()
        if m is None:
            raise KeyError(f"ThemeItem {item.theme_item_id!r} not found")
        m.review_status = item.review_status.value
        m.approved_at   = item.approved_at
        await self._db.flush()
        return _to_theme_item(m)

    # ── Posts ─────────────────────────────────────────────────────────────────

    async def save_post(self, post: ContentPost) -> ContentPost:
        m = ContentPostModel(
            post_id              = post.post_id,
            campaign_id          = post.campaign_id,
            theme_item_id        = post.theme_item_id,
            destination          = post.destination.model_dump(mode="json"),
            content_text         = post.content_text,
            hashtags             = post.hashtags,
            scheduled_publish_at = post.scheduled_publish_at,
            review_status        = post.review_status.value,
            publish_status       = post.publish_status.value,
            publish_receipt      = post.publish_receipt,
            created_at           = post.created_at,
            updated_at           = post.updated_at,
        )
        self._db.add(m)
        await self._db.flush()
        return _to_post(m)

    async def get_posts(
        self,
        campaign_id: str,
        review_status: Optional[str] = None,
        publish_status: Optional[str] = None,
    ) -> list[ContentPost]:
        stmt = select(ContentPostModel).where(ContentPostModel.campaign_id == campaign_id)
        if review_status:
            stmt = stmt.where(ContentPostModel.review_status == review_status)
        if publish_status:
            stmt = stmt.where(ContentPostModel.publish_status == publish_status)
        result = await self._db.execute(stmt.order_by(ContentPostModel.created_at))
        return [_to_post(m) for m in result.scalars().all()]

    async def get_post(self, post_id: str) -> ContentPost | None:
        result = await self._db.execute(
            select(ContentPostModel).where(ContentPostModel.post_id == post_id)
        )
        m = result.scalar_one_or_none()
        return _to_post(m) if m else None

    async def update_post(self, post: ContentPost) -> ContentPost:
        result = await self._db.execute(
            select(ContentPostModel).where(ContentPostModel.post_id == post.post_id)
        )
        m = result.scalar_one_or_none()
        if m is None:
            raise KeyError(f"Post {post.post_id!r} not found")
        m.review_status   = post.review_status.value
        m.publish_status  = post.publish_status.value
        m.publish_receipt = post.publish_receipt
        m.updated_at      = _now()
        await self._db.flush()
        return _to_post(m)
```

**Unit test pattern (SQLite async, no Docker)**

```python
# src/Plant/BackEnd/tests/unit/test_campaign_repository.py
"""Unit tests for CampaignRepository using SQLite async engine."""
import pytest
import pytest_asyncio
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base
from models.campaign import CampaignModel, DailyThemeItemModel, ContentPostModel
from api.v1.campaign_repository import CampaignRepository
from agent_mold.skills.content_models import (
    Campaign, CampaignBrief, CampaignStatus, CostEstimate,
    DailyThemeItem, ReviewStatus, PostingSchedule, DestinationRef,
)

TEST_BRIEF = CampaignBrief(
    theme="Test Theme",
    start_date=date(2026, 3, 6),
    duration_days=3,
    destinations=[DestinationRef(destination_type="simulated")],
)
TEST_COST = CostEstimate(
    total_theme_items=3, total_posts=3, llm_calls=4,
    cost_per_call_usd=0.0, total_cost_usd=0.0, total_cost_inr=0.0,
    model_used="deterministic",
)

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        async with session.begin():
            yield session
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_and_get_campaign(db_session):
    repo = CampaignRepository(db_session)
    c = Campaign(
        hired_instance_id="hired-001",
        customer_id="cust-001",
        brief=TEST_BRIEF,
        cost_estimate=TEST_COST,
    )
    created = await repo.create_campaign(c)
    assert created.campaign_id == c.campaign_id

    fetched = await repo.get_campaign(c.campaign_id)
    assert fetched is not None
    assert fetched.customer_id == "cust-001"
    assert fetched.status == CampaignStatus.DRAFT

@pytest.mark.asyncio
async def test_get_missing_campaign_returns_none(db_session):
    repo = CampaignRepository(db_session)
    result = await repo.get_campaign("nonexistent")
    assert result is None
```

**Test command**

```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/unit/test_campaign_repository.py -v \
  --cov=src/Plant/BackEnd/api/v1/campaign_repository --cov-fail-under=80
```

**Acceptance criteria**

- [ ] `api/v1/campaign_repository.py` exists with `CampaignRepository` class
- [ ] All `async def` methods listed in Architecture Decision Record are implemented
- [ ] `tests/unit/test_campaign_repository.py` — all tests pass
- [ ] Coverage ≥ 80% on `campaign_repository.py`
- [ ] No ORM model objects returned outside `campaign_repository.py`

---

## How to Launch Iteration 1

**Pre-flight check:**
```bash
git status && git log --oneline -3
# Must show: clean tree on main.
```

**Iteration 1 agent task** (paste verbatim into @platform-engineer):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python SQLAlchemy engineer specialising in async persistence and Alembic migrations
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python SQLAlchemy async persistence engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-CONTENT-2-campaign-persistence.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2. Do not touch Iteration 2.
TIME BUDGET: 3h. If you reach 2h45m without finishing, follow STUCK PROTOCOL.

SEQUENCE:
1. Start with E1-S1 (ORM models). Read story card fully before writing a single line.
2. After E1-S1 PR merged: start E1-S2 (migration) AND E2-S1 (repository) in parallel PRs.
3. After all three stories merged: open one iteration PR titled "feat(plant-content-2): iteration 1 — ORM models, migration 026, repository layer".

CHECKPOINT RULE: git add -A && git commit after each epic, before starting next.
STUCK PROTOCOL: If blocked >15 min, open WIP draft PR, post URL, HALT.
```

---

## Iteration 2 — Wire campaigns.py + Integration Tests

### Epic E3: Campaigns routes read and write to PostgreSQL in production

---

#### Story E3-S1 — Add `CAMPAIGN_PERSISTENCE_MODE` and wire all 12 endpoints to `CampaignRepository`

| Field | Value |
|---|---|
| Story ID | E3-S1 |
| Branch | `feat/plant-content-2-e3s1-wire-routes` |
| Time budget | 90 min |
| BLOCKED UNTIL | E2-S1 merged |

**What to build**

1. Update `src/Plant/BackEnd/api/v1/campaigns.py`:
   - Add `CAMPAIGN_PERSISTENCE_MODE` env var flag at module top
   - Add `_get_write_db()` and `_get_read_db()` async generator helpers (snippet below)
   - Add `db: Optional[AsyncSession] = Depends(_get_write_db)` (or `_get_read_db`) parameter to all 12 endpoints
   - In each endpoint, branch: `if db is not None: repo = CampaignRepository(db); # db path` / `else: # existing dict path`
   - The existing in-memory dict logic (`_campaigns`, `_theme_items`, `_posts`) must remain fully intact for memory mode — zero regressions

2. Update `cloud/terraform/stacks/plant/main.tf` — add `CAMPAIGN_PERSISTENCE_MODE = "memory"` inside the `env_vars = {` block at the plant Cloud Run module (approx line 93). Comment: `# "db" enables PostgreSQL persistence via CampaignRepository (PLANT-CONTENT-2)`

3. Update `docker-compose.local.yml` — add `CAMPAIGN_PERSISTENCE_MODE: memory` in the `plant-backend` service `environment:` block (approx line 54).

**Files to read first (max 3)**

1. `src/Plant/BackEnd/api/v1/campaigns.py` — the 12 endpoints and 3 in-memory dicts to augment
2. `src/Plant/BackEnd/api/v1/campaign_repository.py` — repository from E2-S1
3. `src/Plant/BackEnd/core/database.py` — `get_db_session` and `get_read_db_session` async generator signatures

**Code pattern to copy exactly**

Add these imports at the top of `campaigns.py` (after existing imports, before `router = waooaw_router(...)`):

```python
import os
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db_session, get_read_db_session
from api.v1.campaign_repository import CampaignRepository

# Feature flag — default "memory" keeps existing behaviour; set "db" for PostgreSQL.
# Requires: CAMPAIGN_PERSISTENCE_MODE=db + migration 026 applied.
CAMPAIGN_PERSISTENCE_MODE = os.getenv("CAMPAIGN_PERSISTENCE_MODE", "memory").lower()


async def _get_write_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Yield a write DB session when CAMPAIGN_PERSISTENCE_MODE=db; else yield None."""
    if CAMPAIGN_PERSISTENCE_MODE != "db":
        yield None
        return
    async for session in get_db_session():
        yield session


async def _get_read_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """Yield a read-replica session when CAMPAIGN_PERSISTENCE_MODE=db; else yield None."""
    if CAMPAIGN_PERSISTENCE_MODE != "db":
        yield None
        return
    async for session in get_read_db_session():
        yield session
```

Example of how to update one write endpoint (apply same pattern to all 12):

```python
# BEFORE:
@router.post("/campaigns", response_model=CreateCampaignResponse, status_code=201)
async def create_campaign(
    body: CreateCampaignRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> CreateCampaignResponse:
    _require_auth(authorization)
    # ... existing dict logic ...

# AFTER:
@router.post("/campaigns", response_model=CreateCampaignResponse, status_code=201)
async def create_campaign(
    body: CreateCampaignRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Optional[AsyncSession] = Depends(_get_write_db),
) -> CreateCampaignResponse:
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        campaign = Campaign(
            hired_instance_id=body.hired_instance_id,
            customer_id=body.customer_id,
            brief=body.brief,
            cost_estimate=estimate_cost(body.brief, model_used=_model()),
        )
        campaign = await repo.create_campaign(campaign)
        # generate theme list via ContentCreatorSkill (unchanged logic)
        skill = ContentCreatorSkill()
        creator_output = skill.run(ContentCreatorInput(campaign=campaign))
        await repo.save_theme_items(creator_output.theme_items)
        theme_items = creator_output.theme_items
        return CreateCampaignResponse(
            campaign=campaign,
            theme_items=theme_items,
            cost_estimate=campaign.cost_estimate,
            message="Campaign created and theme list generated.",
        )
    # --- memory mode (existing code, UNCHANGED) ---
    ...
```

**GET endpoint pattern** (uses `_get_read_db`):

```python
@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Optional[AsyncSession] = Depends(_get_read_db),
):
    _require_auth(authorization)
    if db is not None:
        repo = CampaignRepository(db)
        campaign = await repo.get_campaign(campaign_id)
        if campaign is None:
            raise HTTPException(status_code=404, detail="Campaign not found.")
        return campaign
    # --- memory mode ---
    ...
```

**Test command** (memory mode — existing tests must still pass):

```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/test_campaigns_api.py -v \
  --cov=src/Plant/BackEnd/api/v1/campaigns --cov-fail-under=80
```

**Acceptance criteria**

- [ ] `CAMPAIGN_PERSISTENCE_MODE` env var added to `campaigns.py`
- [ ] `_get_write_db()` and `_get_read_db()` async generators added
- [ ] All 12 endpoints have `db: Optional[AsyncSession] = Depends(...)` parameter
- [ ] All 12 endpoints have `if db is not None:` db branch + unchanged memory branch
- [ ] `cloud/terraform/stacks/plant/main.tf` has `CAMPAIGN_PERSISTENCE_MODE = "memory"` in env_vars
- [ ] `docker-compose.local.yml` has `CAMPAIGN_PERSISTENCE_MODE: memory` for plant-backend
- [ ] Existing `test_campaigns_api.py` — all tests still pass (memory mode untouched)

---

### Epic E4: DB mode is verified end-to-end by automated tests

---

#### Story E4-S1 — Integration tests: `CAMPAIGN_PERSISTENCE_MODE=db` full roundtrip

| Field | Value |
|---|---|
| Story ID | E4-S1 |
| Branch | `feat/plant-content-2-e4s1-integration-tests` |
| Time budget | 90 min |
| BLOCKED UNTIL | E3-S1 merged |

**What to build**

Create `src/Plant/BackEnd/tests/test_campaigns_api_db.py` — integration tests that
set `CAMPAIGN_PERSISTENCE_MODE=db` and run against a real SQLite async engine
(same pattern as `test_campaign_repository.py` from E2-S1).

The test creates an in-process SQLite DB, applies all SQLAlchemy `Base.metadata.create_all`,
then drives the FastAPI `TestClient` through the full campaign lifecycle:
create → GET → approve theme items → generate posts → approve posts → publish.

**Files to read first (max 3)**

1. `src/Plant/BackEnd/tests/test_campaigns_api.py` — existing memory-mode tests structure; copy fixtures, CREATE_PAYLOAD, AUTH, BRIEF_PAYLOAD constants
2. `src/Plant/BackEnd/api/v1/campaigns.py` — updated routes from E3-S1 (understand the `db` Depends structure)
3. `src/Plant/BackEnd/tests/unit/test_campaign_repository.py` — SQLite async engine + session fixture pattern from E2-S1

**Code pattern to copy exactly**

```python
# src/Plant/BackEnd/tests/test_campaigns_api_db.py
"""Integration tests for campaigns API with CAMPAIGN_PERSISTENCE_MODE=db.

Uses SQLite async in-process DB — no Docker or external DB required.
Tests the full lifecycle: create → get → approve themes → generate posts → publish.
"""
from __future__ import annotations

import os
import pytest
import pytest_asyncio
import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import api.v1.campaigns as camp_module
from core.database import Base, get_db_session, get_read_db_session
from models.campaign import CampaignModel, DailyThemeItemModel, ContentPostModel

# ── Constants (same as test_campaigns_api.py) ────────────────────────────────
AUTH         = "Bearer test-token"
BRIEF_PAYLOAD = {
    "theme": "WAOOAW AI Hire Campaign",
    "start_date": "2026-03-06",
    "duration_days": 2,
    "destinations": [{"destination_type": "simulated"}],
    "schedule": {"times_per_day": 1, "preferred_hours_utc": [9]},
    "brand_name": "WAOOAW",
    "audience": "SMB founders",
    "tone": "professional",
    "approval_mode": "per_item",
}
CREATE_PAYLOAD = {
    "hired_instance_id": "hired-db-001",
    "customer_id": "cust-db-001",
    "brief": BRIEF_PAYLOAD,
}


# ── DB fixtures ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function")
async def sqlite_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture(autouse=True)
def set_db_mode(monkeypatch, sqlite_engine):
    """Switch campaigns.py to db mode backed by the SQLite engine for this test."""
    monkeypatch.setattr(camp_module, "CAMPAIGN_PERSISTENCE_MODE", "db")
    Session = sessionmaker(sqlite_engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_write():
        async with Session() as session:
            async with session.begin():
                yield session

    async def _override_read():
        async with Session() as session:
            yield session

    from main import app
    app.dependency_overrides[camp_module._get_write_db] = _override_write
    app.dependency_overrides[camp_module._get_read_db]  = _override_read
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(set_db_mode):
    from main import app
    with httpx.Client(app=app, base_url="http://test") as c:
        yield c


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_create_campaign_db(client):
    r = client.post("/api/v1/campaigns", json=CREATE_PAYLOAD,
                    headers={"Authorization": AUTH})
    assert r.status_code == 201
    data = r.json()
    assert data["campaign"]["campaign_id"]
    assert data["campaign"]["status"] == "draft"
    assert len(data["theme_items"]) == 2   # duration_days=2

def test_get_campaign_db(client):
    # Create first
    r = client.post("/api/v1/campaigns", json=CREATE_PAYLOAD,
                    headers={"Authorization": AUTH})
    cid = r.json()["campaign"]["campaign_id"]
    # Then GET
    r2 = client.get(f"/api/v1/campaigns/{cid}",
                    headers={"Authorization": AUTH})
    assert r2.status_code == 200
    assert r2.json()["campaign_id"] == cid

def test_approve_theme_items_db(client):
    r = client.post("/api/v1/campaigns", json=CREATE_PAYLOAD,
                    headers={"Authorization": AUTH})
    cid = r.json()["campaign"]["campaign_id"]
    items = r.json()["theme_items"]
    # Approve all via batch
    r2 = client.post(
        f"/api/v1/campaigns/{cid}/theme-items/approve",
        json={"item_ids": [], "decision": "approved"},
        headers={"Authorization": AUTH},
    )
    assert r2.status_code == 200
    assert all(i["review_status"] == "approved" for i in r2.json()["items"])
```

**Test command**

```bash
docker compose -f docker-compose.test.yml run plant-test \
  pytest \
    src/Plant/BackEnd/tests/test_campaigns_api.py \
    src/Plant/BackEnd/tests/test_campaigns_api_db.py \
    src/Plant/BackEnd/tests/unit/test_campaign_repository.py \
    src/Plant/BackEnd/tests/unit/test_campaign_models.py \
  -v \
  --cov=src/Plant/BackEnd/api/v1/campaigns \
  --cov=src/Plant/BackEnd/api/v1/campaign_repository \
  --cov-fail-under=80
```

**Acceptance criteria**

- [ ] `tests/test_campaigns_api_db.py` exists with ≥ 3 tests covering create/get/approve
- [ ] All three tests pass in `db` mode against SQLite
- [ ] `test_campaigns_api.py` (memory mode) still passes — no regressions
- [ ] Combined coverage for `campaigns.py` + `campaign_repository.py` ≥ 80%

---

## How to Launch Iteration 2

**Pre-flight check:**
```bash
git fetch origin
git show origin/main:docs/plant/iterations/PLANT-CONTENT-2-campaign-persistence.md | grep "## Iteration 2"
# Must return the heading — confirms plan is on main before launching.
git status && git log --oneline -3
# Must show: clean tree on main with Iteration 1 merged.
```

**Iteration 2 agent task** (paste verbatim into @platform-engineer):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python FastAPI engineer specialising in feature-flag persistence migration and async DB integration tests
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python FastAPI async persistence engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-CONTENT-2-campaign-persistence.md
YOUR SCOPE: Iteration 2 only — Epics E3, E4. Do not touch Iteration 1.
TIME BUDGET: 3h. If you reach 2h45m without finishing, follow STUCK PROTOCOL.

SEQUENCE:
1. Start with E3-S1 (wire routes). Read story card fully before writing a single line.
2. After E3-S1 PR merged: start E4-S1 (integration tests).
3. After both stories merged: open iteration PR titled "feat(plant-content-2): iteration 2 — route wiring + integration tests".

CRITICAL: The existing `_campaigns`, `_theme_items`, `_posts` in-memory dicts in
campaigns.py MUST remain fully intact. Memory mode (CAMPAIGN_PERSISTENCE_MODE=memory)
must be regression-free — the existing test_campaigns_api.py tests must still pass.

CHECKPOINT RULE: git add -A && git commit after each epic, before starting next.
STUCK PROTOCOL: If blocked >15 min, open WIP draft PR, post URL, HALT.
```

---

## Reporting to the user after plan is on main

```
Plan ready: PLANT-CONTENT-2
File: docs/plant/iterations/PLANT-CONTENT-2-campaign-persistence.md
PR: [github PR URL]

| Iteration | Scope | ⏱ Est | Come back |
|---|---|---|---|
| 1 | ORM models + migration 026 + CampaignRepository | 3h | 2026-03-06 22:00 UTC |
| 2 | Wire campaigns.py + integration tests | 3h | 2026-03-07 01:00 UTC |

To launch Iteration 1 — GitHub Copilot Agent interface:
1. Open VS Code → Copilot Chat (Ctrl+Alt+I / Cmd+Alt+I)
2. Click model dropdown → Agent mode
3. Click + → type @ → select platform-engineer
4. Paste the Iteration 1 agent task from the "How to Launch Iteration 1" section above
5. Come back: 2026-03-06 22:00 UTC

To launch Iteration 2 (after Iteration 1 PR merged):
Same steps with the Iteration 2 agent task.
```
