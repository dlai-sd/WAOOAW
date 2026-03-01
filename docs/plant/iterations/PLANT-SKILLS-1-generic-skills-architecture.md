fuck, # PLANT-SKILLS-1 — Generic Skills Architecture

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-SKILLS-1` |
| Feature area | Plant BackEnd — Generic Skills Architecture + Platform Connections + Performance Stats |
| Created | 2026-03-01 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §24 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 3 |
| Total epics | 7 |
| Total stories | 12 |

---

## Design Decision Log

**Why this work is needed:**

The current `Agent` entity has a single `skill_id` FK — one Agent can only carry one Skill. Two example skills (`social-content-publisher` and `execute-trade-order`) prove this is a blocker: a real-world agent may need both. This plan implements a generic, multi-skill architecture.

**Key decisions locked:**

| Decision | Rationale |
|---|---|
| `agent_skills` join table (not ARRAY column) | FK integrity, queryable, index-friendly |
| `Skill.goal_schema` JSONB | Schema-driven UI form — CP renders it dynamically, no hardcoding per skill |
| `PlatformConnection` is NOT a BaseEntity | Operational record, not a governed domain entity. No constitutional overhead needed. |
| `PerformanceStat` is a plain operational table | Day-keyed, append-only metrics. No versioning needed. |
| Keep `agent_entity.skill_id` (nullable) for backward compat | Avoids breaking existing data; deprecated FK stays until all consumers migrate |
| Seed two canonical skills with full `goal_schema` in Iteration 2 | Makes CP FrontEnd work immediately without manual admin data entry |
| CP BackEnd proxy pattern (b) for all new endpoints | CP BackEnd is a thin proxy — no business logic; all data lives in Plant |

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
| 1 | Lane B — Plant models + migrations 021/022/023 + AgentSkills API | E1, E2, E3 | 4 | ~3h | +3.5h from launch |
| 2 | Lane B — PlatformConnections + PerformanceStat APIs + 2 canonical skill seeds | E4, E5 | 4 | ~3h | +3.5h from launch |
| 3 | Lane B→A — CP BackEnd thin proxy routes + CP FrontEnd Goals + Performance tabs | E6, E7 | 4 | ~4h | +5h from launch |

**Estimate basis:** Migration = 30 min | New BE endpoint = 45 min | Seed data = 30 min | CP proxy = 45 min | FE wiring = 60 min | Docker test = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git checkout main && git pull && git status
# Must show: nothing to commit, working tree clean
```

**Iteration 1 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy / Alembic engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python/FastAPI/SQLAlchemy engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-SKILLS-1-generic-skills-architecture.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2 or 3.
TIME BUDGET: 3h. If you reach 3.5h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute in order: E1-S1 → E1-S2 → E2-S1 → E3-S1
6. When all epics are docker-tested, open the iteration PR. Post the PR URL. HALT.
```

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(PLANT-SKILLS-1): iteration 1 — agent_skills + platform_connections + performance_stats models
```

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python/FastAPI/SQLAlchemy engineer, I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-SKILLS-1-generic-skills-architecture.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5. Do not touch Iteration 3.
TIME BUDGET: 3h.

PREREQUISITE CHECK (first thing, before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(PLANT-SKILLS-1): iteration 1 — agent_skills + platform_connections + performance_stats models
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Execute in order: E4-S1 → E4-S2 → E5-S1 → E5-S2
4. When all epics are docker-tested, open the iteration PR. Post URL. HALT.
```

---

### Iteration 3

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Verify merge:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(PLANT-SKILLS-1): iteration 2 — platform-connections + performance-stats APIs + skill seeds
```

**Iteration 3 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior React 18 / TypeScript / Vite / Fluent UI engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/PLANT-SKILLS-1-generic-skills-architecture.md
YOUR SCOPE: Iteration 3 only — Epics E6, E7. Do not touch other content.
TIME BUDGET: 4h.

PREREQUISITE CHECK:
  Run: git log --oneline origin/main | head -5
  Must show: feat(PLANT-SKILLS-1): iteration 2 — platform-connections + performance-stats APIs + skill seeds
  If not: post "Blocked: Iteration 2 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 3" sections. Read nothing else.
3. Execute in order: E6-S1 → E6-S2 → E7-S1 → E7-S2
4. Open iteration PR when done. Post URL. HALT.
```

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona |
|---|---|
| `src/Plant/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy / Alembic engineer |
| `src/CP/BackEnd/` | Senior Python 3.11 / FastAPI engineer |
| `src/CP/FrontEnd/` | Senior React 18 / TypeScript / Vite / Fluent UI engineer |

---

### Rule 0 — Open tracking draft PR first

```bash
git checkout main && git pull
git checkout -b feat/PLANT-SKILLS-1-itN-eN
git commit --allow-empty -m "chore(PLANT-SKILLS-1): start iteration N"
git push origin feat/PLANT-SKILLS-1-itN-eN
gh pr create \
  --base main \
  --head feat/PLANT-SKILLS-1-itN-eN \
  --draft \
  --title "tracking: PLANT-SKILLS-1 Iteration N — in progress" \
  --body "Tracking PR. Subscribe for story-by-story progress."
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/PLANT-SKILLS-1-itN-eN`.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor outside scope.
If you notice a bug outside scope: add `# TODO(PLANT-SKILLS-1): <description>` and move on.

### Rule 3 — Docker-only testing. No virtualenv.
```bash
# Run tests inside Docker — never with a local venv
docker-compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/ -k "<test name>" -v 2>&1 | tail -30
```
Image promotion: images are built once and promoted through environments by injecting env vars.
Never bake environment-specific values into Dockerfile or code.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat(PLANT-SKILLS-1): [story summary]"
git push origin HEAD
gh pr comment <tracking-pr-number> --body "✅ [story id] done — [one line summary]"
```

### Rule 5 — Never edit files outside your story card's scope

### Rule 6 — STUCK PROTOCOL
If blocked for more than 15 minutes on a single issue:
1. Commit current state with prefix `WIP:`
2. Push branch
3. Open a draft PR titled `WIP: PLANT-SKILLS-1 — stuck on [issue]`
4. Post comment: "Stuck: [exact error / file / line]. Attempted: [what]. Need: [what]."
5. HALT.

### Rule 7 — Final iteration PR
```bash
gh pr create \
  --base main \
  --title "feat(PLANT-SKILLS-1): iteration N — [summary]" \
  --body "Closes stories: [list]

## What changed
[bullet list]

## Test evidence
[paste test output]"
```
Post PR URL in Copilot Chat. HALT.

---

## Iteration 1 — Plant models, migrations, and AgentSkills API

**Lane B — all new. No existing endpoints to call.**

### Epic E1 — An Agent can carry multiple Skills (many-to-many)

**Branch:** `feat/PLANT-SKILLS-1-it1-e1`
**Estimated time:** 1.5h (2 stories × 45 min)

---

#### E1-S1: Migration 021 — `agent_skills` join table + `goal_schema` on `skill_entity`

**Branch:** `feat/PLANT-SKILLS-1-it1-e1`
**BLOCKED UNTIL:** none
**Pattern:** Plant BackEnd — Alembic migration only

**Context (2 sentences):**
`Agent` in `src/Plant/BackEnd/models/team.py` currently has a single `skill_id` FK column (`agent_entity.skill_id`) which limits each agent to one skill. This story adds migration `021_agent_skills_and_skill_goal_schema.py` that creates a new `agent_skills` join table and adds a `goal_schema` JSONB column to the existing `skill_entity` table — both without dropping the old `skill_id` column (kept nullable for backward compatibility).

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/team.py` — current Agent model (lines 1–65)
2. `src/Plant/BackEnd/models/skill.py` — current Skill model (lines 1–60)
3. `src/Plant/BackEnd/database/migrations/versions/020_pii_encryption.py` — reference for migration file structure

**What to build:**

Create `src/Plant/BackEnd/database/migrations/versions/021_agent_skills_and_skill_goal_schema.py`:

```python
"""021 — agent_skills join table + goal_schema on skill_entity

Revision ID: 021
Revises: 020
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add goal_schema JSONB to skill_entity (nullable — existing rows get NULL)
    op.add_column(
        "skill_entity",
        sa.Column("goal_schema", postgresql.JSONB, nullable=True),
    )

    # 2. Create agent_skills join table
    op.create_table(
        "agent_skills",
        sa.Column("id", sa.String, primary_key=True, nullable=False),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skill_entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("ordinal", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_agent_skills_agent_skill", "agent_skills", ["agent_id", "skill_id"]
    )
    op.create_index("ix_agent_skills_agent_id", "agent_skills", ["agent_id"])
    op.create_index("ix_agent_skills_skill_id", "agent_skills", ["skill_id"])

    # 3. Make agent_entity.skill_id nullable (backward compat — do NOT drop it)
    op.alter_column("agent_entity", "skill_id", nullable=True)


def downgrade() -> None:
    op.drop_table("agent_skills")
    op.drop_column("skill_entity", "goal_schema")
    op.alter_column("agent_entity", "skill_id", nullable=False)
```

Create `src/Plant/BackEnd/models/agent_skill.py`:

```python
"""AgentSkill — join model for Agent ↔ Skill many-to-many relationship."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from core.database import Base


class AgentSkillModel(Base):
    """Join table linking Agents to Skills.

    One Agent can carry N Skills. One Skill can be attached to M Agents.
    is_primary marks the canonical skill for display purposes.
    ordinal controls display order on the CP agent card.
    """

    __tablename__ = "agent_skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("agent_entity.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("skill_entity.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_primary = Column(Boolean, nullable=False, default=False)
    ordinal = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("agent_id", "skill_id", name="uq_agent_skills_agent_skill"),
        Index("ix_agent_skills_agent_id", "agent_id"),
        Index("ix_agent_skills_skill_id", "skill_id"),
    )
```

Also add `goal_schema` column to the Python `Skill` model in `src/Plant/BackEnd/models/skill.py`:
```python
# Add this column to Skill class (after existing columns):
goal_schema = Column(JSON, nullable=True, doc="JSON schema defining goal configuration fields for this skill")
```

**Acceptance criteria:**
- [ ] File `021_agent_skills_and_skill_goal_schema.py` exists in `database/migrations/versions/`
- [ ] File `models/agent_skill.py` exists
- [ ] `skill_entity.goal_schema` column added to `Skill` model class
- [ ] Migration runs without error:
```bash
docker-compose -f docker-compose.test.yml run plant-test \
  alembic upgrade head 2>&1 | tail -5
```
- [ ] Migration is reversible (downgrade then upgrade again — no errors)

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run plant-test \
  alembic upgrade head 2>&1 | tail -5
# Expected: "Running upgrade 020 -> 021"
```

---

#### E1-S2: Plant API — GET/POST/DELETE `/v1/agents/{agent_id}/skills`

**Branch:** `feat/PLANT-SKILLS-1-it1-e1`
**BLOCKED UNTIL:** E1-S1 (migration must exist before API can use table)
**Pattern:** Plant BackEnd — new route file `src/Plant/BackEnd/api/v1/agent_skills.py`

**Context (2 sentences):**
After E1-S1, the `agent_skills` table and `AgentSkillModel` exist but no API endpoint allows listing or managing them. This story creates `src/Plant/BackEnd/api/v1/agent_skills.py` with three endpoints — GET list, POST attach, DELETE detach — and registers it in `src/Plant/BackEnd/main.py`.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/agent_skill.py` — the model just created in E1-S1
2. `src/Plant/BackEnd/api/v1/agents.py` — reference for `waooaw_router` + `get_read_db_session` pattern (lines 1–30)
3. `src/Plant/BackEnd/main.py` — to find where to add `include_router` (lines 1–80)

**Code patterns to copy exactly:**

```python
# Pattern 1 — waooaw_router (MANDATORY — bare APIRouter is banned by ruff TID251)
from core.routing import waooaw_router
router = waooaw_router(prefix="/v1/agents", tags=["agent-skills"])

# Pattern 2 — Read replica for GET routes
from core.database import get_read_db_session, get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

@router.get("/{agent_id}/skills")
async def list_agent_skills(
    agent_id: str,
    db: AsyncSession = Depends(get_read_db_session),  # ← read replica, NOT get_db_session
):
    ...

# Pattern 3 — Write session for POST/DELETE routes
@router.post("/{agent_id}/skills")
async def attach_skill(
    agent_id: str,
    body: AttachSkillRequest,
    db: AsyncSession = Depends(get_db_session),  # ← primary for writes
):
    ...
```

**What to build:**

Create `src/Plant/BackEnd/api/v1/agent_skills.py`:

```python
"""Agent-Skill relationship endpoints — PLANT-SKILLS-1 E1-S2.

GET    /v1/agents/{agent_id}/skills          — list skills attached to an agent
POST   /v1/agents/{agent_id}/skills          — attach a skill to an agent
DELETE /v1/agents/{agent_id}/skills/{skill_id} — detach a skill from an agent
PATCH  /v1/skills/{skill_id}/goal-schema     — update skill goal_schema
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_read_db_session, get_db_session
from core.routing import waooaw_router
from models.agent_skill import AgentSkillModel
from models.skill import Skill

router = waooaw_router(prefix="/v1", tags=["agent-skills"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class AgentSkillResponse(BaseModel):
    id: str
    agent_id: str
    skill_id: str
    is_primary: bool
    ordinal: int
    skill_name: Optional[str] = None
    skill_category: Optional[str] = None

    class Config:
        from_attributes = True


class AttachSkillRequest(BaseModel):
    skill_id: str
    is_primary: bool = False
    ordinal: int = 0


class GoalSchemaUpdateRequest(BaseModel):
    goal_schema: dict  # Free-form JSON; validated by skill-specific logic in future


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/agents/{agent_id}/skills", response_model=List[AgentSkillResponse])
async def list_agent_skills(
    agent_id: str,
    db: AsyncSession = Depends(get_read_db_session),
) -> List[AgentSkillResponse]:
    """List all skills attached to an agent."""
    result = await db.execute(
        select(AgentSkillModel, Skill)
        .join(Skill, AgentSkillModel.skill_id == Skill.id)
        .where(AgentSkillModel.agent_id == agent_id)
        .order_by(AgentSkillModel.ordinal)
    )
    rows = result.all()
    return [
        AgentSkillResponse(
            id=row.AgentSkillModel.id,
            agent_id=str(row.AgentSkillModel.agent_id),
            skill_id=str(row.AgentSkillModel.skill_id),
            is_primary=row.AgentSkillModel.is_primary,
            ordinal=row.AgentSkillModel.ordinal,
            skill_name=row.Skill.name,
            skill_category=row.Skill.category,
        )
        for row in rows
    ]


@router.post("/agents/{agent_id}/skills", response_model=AgentSkillResponse, status_code=201)
async def attach_skill(
    agent_id: str,
    body: AttachSkillRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AgentSkillResponse:
    """Attach a skill to an agent."""
    link = AgentSkillModel(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        skill_id=body.skill_id,
        is_primary=body.is_primary,
        ordinal=body.ordinal,
        created_at=datetime.now(timezone.utc),
    )
    db.add(link)
    try:
        await db.commit()
        await db.refresh(link)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Skill already attached to this agent")
    return AgentSkillResponse(
        id=link.id,
        agent_id=str(link.agent_id),
        skill_id=str(link.skill_id),
        is_primary=link.is_primary,
        ordinal=link.ordinal,
    )


@router.delete("/agents/{agent_id}/skills/{skill_id}", status_code=204)
async def detach_skill(
    agent_id: str,
    skill_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Detach a skill from an agent."""
    result = await db.execute(
        delete(AgentSkillModel)
        .where(AgentSkillModel.agent_id == agent_id)
        .where(AgentSkillModel.skill_id == skill_id)
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Skill not attached to this agent")


@router.patch("/skills/{skill_id}/goal-schema", response_model=dict)
async def update_goal_schema(
    skill_id: str,
    body: GoalSchemaUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Update the goal_schema for a skill (defines CP goal-config form fields)."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill.goal_schema = body.goal_schema
    await db.commit()
    return {"skill_id": skill_id, "goal_schema": skill.goal_schema}
```

Register in `src/Plant/BackEnd/main.py` — add after the existing agents router import:
```python
# In imports section:
from api.v1.agent_skills import router as agent_skills_router

# In include_router section:
app.include_router(agent_skills_router)
```

**Acceptance criteria:**
- [ ] `GET /v1/agents/{agent_id}/skills` returns 200 with empty list for a new agent
- [ ] `POST /v1/agents/{agent_id}/skills` returns 201 when skill exists; 409 on duplicate
- [ ] `DELETE /v1/agents/{agent_id}/skills/{skill_id}` returns 204; 404 if not attached
- [ ] `PATCH /v1/skills/{skill_id}/goal-schema` returns 200 with updated schema
- [ ] All GET routes use `get_read_db_session`; all writes use `get_db_session`
- [ ] `waooaw_router` used (not bare `APIRouter`)
- [ ] Tests pass:
```bash
docker-compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/ -k "agent_skill" -v 2>&1 | tail -20
```

**Tests to write** (in `src/Plant/BackEnd/tests/test_agent_skills.py`):
```python
"""Tests for GET/POST/DELETE /v1/agents/{id}/skills — PLANT-SKILLS-1 E1-S2"""
# Cover: list empty, attach skill, list returns skill, duplicate returns 409,
# detach returns 204, detach unknown returns 404, goal-schema PATCH updates correctly
```

---

### Epic E2 — Customer can connect external platforms to their hired agent

**Branch:** `feat/PLANT-SKILLS-1-it1-e2`
**Estimated time:** 30 min (migration only — API in Iteration 2)

---

#### E2-S1: Migration 022 — `platform_connections` table

**Branch:** `feat/PLANT-SKILLS-1-it1-e2`
**BLOCKED UNTIL:** none (independent from E1)
**Pattern:** Plant BackEnd — Alembic migration + plain SQLAlchemy model (NOT BaseEntity)

**Context (2 sentences):**
When a customer hires an agent with a Skill that needs external access (social platforms, crypto exchange), they must connect their account via API key/secret. This table stores only the GCP Secret Manager resource path (`secret_ref`) — never the secret value itself — linked to the `HiredAgent` instance and the specific `Skill`.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/database/migrations/versions/021_agent_skills_and_skill_goal_schema.py` — reference for migration file structure
2. `src/Plant/BackEnd/models/hired_agent.py` — to see the `hired_agents` table name (line 30: `__tablename__ = "hired_agents"`)

**What to build:**

Create `src/Plant/BackEnd/database/migrations/versions/022_platform_connections.py`:

```python
"""022 — platform_connections table

Revision ID: 022
Revises: 021
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_connections",
        sa.Column("id", sa.String, primary_key=True, nullable=False),
        sa.Column(
            "hired_instance_id",
            sa.String,
            sa.ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.String, nullable=False),  # informational — no FK to keep it flexible
        sa.Column("platform_key", sa.String(100), nullable=False),  # e.g. "delta_exchange", "instagram"
        sa.Column("secret_ref", sa.Text, nullable=False),  # GCP Secret Manager resource path ONLY
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),  # pending | connected | error
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_platform_conn_hired_skill_platform",
        "platform_connections",
        ["hired_instance_id", "skill_id", "platform_key"],
    )
    op.create_index("ix_platform_connections_hired_instance_id", "platform_connections", ["hired_instance_id"])


def downgrade() -> None:
    op.drop_table("platform_connections")
```

Create `src/Plant/BackEnd/models/platform_connection.py`:

```python
"""PlatformConnection — stores external platform connection refs per HiredAgent+Skill."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from core.database import Base


class PlatformConnectionModel(Base):
    """Stores a reference to external platform credentials in Secret Manager.

    NEVER stores the actual secret value.
    secret_ref is a GCP Secret Manager resource path:
      e.g. "projects/waooaw-oauth/secrets/hired-abc123-delta-exchange/versions/latest"
    """

    __tablename__ = "platform_connections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hired_instance_id = Column(
        String,
        ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id = Column(String, nullable=False)
    platform_key = Column(String(100), nullable=False)
    secret_ref = Column(Text, nullable=False)  # Secret Manager path — NEVER the secret value
    status = Column(String(50), nullable=False, default="pending")
    connected_at = Column(DateTime(timezone=True), nullable=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint(
            "hired_instance_id", "skill_id", "platform_key",
            name="uq_platform_conn_hired_skill_platform",
        ),
        Index("ix_platform_connections_hired_instance_id", "hired_instance_id"),
    )
```

**Acceptance criteria:**
- [ ] Migration 022 file exists and runs without error: `alembic upgrade head`
- [ ] `platform_connections` table created with unique constraint on `(hired_instance_id, skill_id, platform_key)`
- [ ] `PlatformConnectionModel` class exists in `models/platform_connection.py`
- [ ] `secret_ref` column is `Text` (never an enum of the secret value)

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run plant-test \
  alembic upgrade head 2>&1 | tail -5
# Expected: "Running upgrade 021 -> 022"
```

---

### Epic E3 — Customer can see daily performance stats for each hired agent

**Branch:** `feat/PLANT-SKILLS-1-it1-e3`
**Estimated time:** 30 min (migration only — API in Iteration 2)

---

#### E3-S1: Migration 023 — `performance_stats` table

**Branch:** `feat/PLANT-SKILLS-1-it1-e3`
**BLOCKED UNTIL:** none (independent from E2)
**Pattern:** Plant BackEnd — Alembic migration + plain SQLAlchemy model (NOT BaseEntity)

**Context (2 sentences):**
The Performance tab (`My Agents → Agent → Performance`) needs day-keyed stats per hired agent per skill per platform. A daily Celery job (out of scope for this plan) will write one row per `(hired_instance_id, skill_id, platform_key, stat_date)` — this story creates the table and model that job will write to.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/database/migrations/versions/022_platform_connections.py` — reference for migration structure
2. `src/Plant/BackEnd/models/platform_connection.py` — reference for plain model structure (no BaseEntity)

**What to build:**

Create `src/Plant/BackEnd/database/migrations/versions/023_performance_stats.py`:

```python
"""023 — performance_stats table

Revision ID: 023
Revises: 022
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "performance_stats",
        sa.Column("id", sa.String, primary_key=True, nullable=False),
        sa.Column(
            "hired_instance_id",
            sa.String,
            sa.ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("skill_id", sa.String, nullable=False),
        sa.Column("platform_key", sa.String(100), nullable=False),
        sa.Column("stat_date", sa.Date, nullable=False),
        sa.Column("metrics", postgresql.JSONB, nullable=False, server_default="{}"),
        # metrics shape depends on skill type, e.g.:
        # social: { impressions, clicks, engagement_rate, posts_published }
        # trading: { trades_count, pnl_pct, win_rate, stop_loss_count, profit_count }
        sa.Column(
            "collected_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_unique_constraint(
        "uq_perf_stats_hired_skill_platform_date",
        "performance_stats",
        ["hired_instance_id", "skill_id", "platform_key", "stat_date"],
    )
    op.create_index("ix_performance_stats_hired_instance_id", "performance_stats", ["hired_instance_id"])
    op.create_index("ix_performance_stats_stat_date", "performance_stats", ["stat_date"])


def downgrade() -> None:
    op.drop_table("performance_stats")
```

Create `src/Plant/BackEnd/models/performance_stat.py`:

```python
"""PerformanceStat — day-keyed skill performance metrics per hired agent."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class PerformanceStatModel(Base):
    """Day-keyed performance metrics written by the daily Celery stats-collector job.

    metrics JSONB shape by skill type:
      social-content-publisher:
        { "impressions": int, "clicks": int, "engagement_rate": float, "posts_published": int }
      execute-trade-order:
        { "trades_count": int, "pnl_pct": float, "win_rate": float,
          "stop_loss_count": int, "profit_count": int }
    """

    __tablename__ = "performance_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    hired_instance_id = Column(
        String,
        ForeignKey("hired_agents.hired_instance_id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id = Column(String, nullable=False)
    platform_key = Column(String(100), nullable=False)
    stat_date = Column(Date, nullable=False)
    metrics = Column(JSONB, nullable=False, default=dict)
    collected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint(
            "hired_instance_id", "skill_id", "platform_key", "stat_date",
            name="uq_perf_stats_hired_skill_platform_date",
        ),
        Index("ix_performance_stats_hired_instance_id", "hired_instance_id"),
        Index("ix_performance_stats_stat_date", "stat_date"),
    )
```

**Acceptance criteria:**
- [ ] Migration 023 file exists and runs without error: `alembic upgrade head`
- [ ] `performance_stats` table created with unique constraint on `(hired_instance_id, skill_id, platform_key, stat_date)`
- [ ] `PerformanceStatModel` exists in `models/performance_stat.py`
- [ ] `metrics` is JSONB (not JSON) — supports GIN indexing in future

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run plant-test \
  alembic upgrade head 2>&1 | tail -5
# Expected: "Running upgrade 022 -> 023"
```

---

## Iteration 2 — Platform Connections + Performance Stats APIs + Canonical Skill Seeds

**Lane B — all new endpoints and seed data.**

### Epic E4 — Customer can manage platform connections and read performance data via API

**Branch:** `feat/PLANT-SKILLS-1-it2-e4`
**Estimated time:** 1.5h (2 stories × 45 min)

---

#### E4-S1: Plant API — GET/POST/DELETE `/v1/hired-agents/{id}/platform-connections`

**Branch:** `feat/PLANT-SKILLS-1-it2-e4`
**BLOCKED UNTIL:** E2-S1 (migration 022 must be on main)
**Pattern:** Plant BackEnd — new route file `src/Plant/BackEnd/api/v1/platform_connections.py`

**Context (2 sentences):**
After Iteration 1, the `platform_connections` table and `PlatformConnectionModel` exist but no API exposes them. This story creates the CRUD endpoints so CP BackEnd (and Iteration 3's CP FrontEnd) can store and read connection records — crucially, the POST endpoint accepts only a `secret_ref` (GCP Secret Manager path), never the raw secret.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/platform_connection.py` — model from E2-S1
2. `src/Plant/BackEnd/api/v1/agent_skills.py` — reference for `waooaw_router` + async DB pattern (E1-S2)
3. `src/Plant/BackEnd/main.py` — where to add `include_router` (lines 1–80)

**Code patterns to copy exactly:**

```python
# waooaw_router — mandatory (bare APIRouter banned by ruff TID251)
from core.routing import waooaw_router
router = waooaw_router(prefix="/v1/hired-agents", tags=["platform-connections"])

# Read replica for GET
from core.database import get_read_db_session, get_db_session
@router.get("/{hired_instance_id}/platform-connections")
async def list_connections(
    hired_instance_id: str,
    db: AsyncSession = Depends(get_read_db_session),  # ← read replica
): ...

# Write session for POST/DELETE
@router.post("/{hired_instance_id}/platform-connections")
async def create_connection(
    hired_instance_id: str,
    body: CreateConnectionRequest,
    db: AsyncSession = Depends(get_db_session),  # ← primary for writes
): ...

# NEVER log secret_ref or any credential — PII masking is global but add explicit comment
# logger.info("Platform connection created for %s/%s", hired_instance_id, body.platform_key)
# DO NOT log body.secret_ref
```

**What to build:**

Create `src/Plant/BackEnd/api/v1/platform_connections.py` with:
- `GET /v1/hired-agents/{hired_instance_id}/platform-connections` — list connections, returns `id, skill_id, platform_key, status, connected_at` (NEVER returns `secret_ref`)
- `POST /v1/hired-agents/{hired_instance_id}/platform-connections` — create connection record (accepts `skill_id, platform_key, secret_ref`)
- `DELETE /v1/hired-agents/{hired_instance_id}/platform-connections/{connection_id}` — delete connection record
- `PATCH /v1/hired-agents/{hired_instance_id}/platform-connections/{connection_id}/verify` — set `status=connected`, `last_verified_at=now()`

Register in `src/Plant/BackEnd/main.py`.

**Acceptance criteria:**
- [ ] `secret_ref` is accepted on POST but NEVER returned in any GET response
- [ ] `waooaw_router` used
- [ ] GET uses `get_read_db_session`; POST/DELETE/PATCH use `get_db_session`
- [ ] Duplicate `(hired_instance_id, skill_id, platform_key)` returns 409
- [ ] Tests pass:
```bash
docker-compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/ -k "platform_connection" -v 2>&1 | tail -20
```

---

#### E4-S2: Plant API — GET `/v1/hired-agents/{id}/performance-stats` + POST (upsert)

**Branch:** `feat/PLANT-SKILLS-1-it2-e4`
**BLOCKED UNTIL:** E3-S1 (migration 023 must be on main)
**Pattern:** Plant BackEnd — new route file `src/Plant/BackEnd/api/v1/performance_stats.py`

**Context (2 sentences):**
The `performance_stats` table from E3-S1 needs two endpoints: a GET for CP FrontEnd to read day-by-day stats for the Performance tab, and a POST/upsert that the daily Celery stats-collector job will call. The GET supports `?skill_id=&platform_key=&from_date=&to_date=` query params to filter results.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/performance_stat.py` — model from E3-S1
2. `src/Plant/BackEnd/api/v1/platform_connections.py` — reference for pattern (E4-S1, just created)
3. `src/Plant/BackEnd/main.py` — where to add `include_router`

**Code patterns to copy exactly:**

```python
# waooaw_router — mandatory
from core.routing import waooaw_router
router = waooaw_router(prefix="/v1/hired-agents", tags=["performance-stats"])

# Read replica for GET (catalog/analytics reads must never hit primary)
@router.get("/{hired_instance_id}/performance-stats")
async def get_performance_stats(
    hired_instance_id: str,
    skill_id: Optional[str] = None,
    platform_key: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: AsyncSession = Depends(get_read_db_session),  # ← read replica, NOT get_db_session
): ...

# Write session for POST upsert
@router.post("/{hired_instance_id}/performance-stats", status_code=201)
async def upsert_performance_stat(
    hired_instance_id: str,
    body: UpsertPerformanceStatRequest,
    db: AsyncSession = Depends(get_db_session),
): ...
```

**What to build:**

Create `src/Plant/BackEnd/api/v1/performance_stats.py` with:
- `GET /v1/hired-agents/{hired_instance_id}/performance-stats` — filtered list, `ORDER BY stat_date DESC`, max 90 rows
- `POST /v1/hired-agents/{hired_instance_id}/performance-stats` — upsert by `(hired_instance_id, skill_id, platform_key, stat_date)`, updates `metrics` if row already exists

Register in `src/Plant/BackEnd/main.py`.

**Acceptance criteria:**
- [ ] GET returns empty list for unknown `hired_instance_id` (not 404)
- [ ] GET filters correctly by `skill_id`, `platform_key`, `from_date`, `to_date`
- [ ] POST upserts correctly — second POST with same date updates `metrics`
- [ ] GET uses `get_read_db_session`; POST uses `get_db_session`
- [ ] `waooaw_router` used
- [ ] Tests pass:
```bash
docker-compose -f docker-compose.test.yml run plant-test \
  pytest src/Plant/BackEnd/tests/ -k "performance_stat" -v 2>&1 | tail -20
```

---

### Epic E5 — Two canonical skills are seeded with complete goal configuration schemas

**Branch:** `feat/PLANT-SKILLS-1-it2-e5`
**Estimated time:** 1h (2 stories × 30 min)

---

#### E5-S1: Seed `social-content-publisher` skill with full `goal_schema`

**Branch:** `feat/PLANT-SKILLS-1-it2-e5`
**BLOCKED UNTIL:** E1-S1 (migration 021 must be on main — `goal_schema` column must exist)
**Pattern:** Plant BackEnd — seed script (run once via migration or standalone seed script)

**Context (2 sentences):**
The `social-content-publisher` skill enables an agent to take customer ideas, generate scripts via Grok API, get approval, produce platform-specific content, and publish to Facebook/LinkedIn/Instagram/X/WhatsApp. Its `goal_schema` defines the dynamic form CP FrontEnd will render when a customer configures this skill on their hired agent.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/models/skill.py` — Skill model fields (lines 1–55)
2. `src/Plant/BackEnd/database/seeds/agent_type_definitions_seed.py` — reference for seed script pattern

**What to build:**

Create `src/Plant/BackEnd/database/seeds/skill_social_content_publisher_seed.py`:

```python
"""Seed: social-content-publisher skill with goal_schema.

Run: python -m database.seeds.skill_social_content_publisher_seed
"""
from __future__ import annotations

SOCIAL_CONTENT_PUBLISHER_GOAL_SCHEMA = {
    "fields": [
        {
            "key": "target_audience",
            "type": "string",
            "required": True,
            "label": "Target Audience",
            "placeholder": "e.g. Indian SMB owners aged 30–50",
            "help": "Describe your ideal customer. The agent uses this to tailor every script.",
        },
        {
            "key": "platforms",
            "type": "multiselect",
            "required": True,
            "label": "Platforms to publish on",
            "options": ["facebook", "linkedin", "instagram", "x", "whatsapp"],
            "max_selections_plan_gate": "max_platforms",
            "help": "Select platforms. Maximum determined by your subscription plan.",
        },
        {
            "key": "posts_per_week",
            "type": "integer",
            "required": True,
            "label": "Posts per week",
            "min": 1,
            "max_plan_gate": "posts_per_week",
            "help": "How many posts per week. Maximum determined by your plan.",
        },
        {
            "key": "content_tone",
            "type": "select",
            "required": True,
            "label": "Content tone",
            "options": ["professional", "casual", "educational", "inspirational"],
            "default": "professional",
        },
        {
            "key": "brand_voice_notes",
            "type": "textarea",
            "required": False,
            "label": "Brand voice notes",
            "placeholder": "Any specific phrases, values, or topics to always/never include",
        },
    ],
    "platform_connections_required": True,
    "platform_connection_keys": ["facebook", "linkedin", "instagram", "x", "whatsapp"],
    "approval_workflow": "script_approval",
}

# Seed logic: upsert Skill with external_id = "social-content-publisher"
# ... (full async SQLAlchemy upsert using Skill model, sets goal_schema, category, name)
```

Include the full upsert logic referencing the `Skill` model's `external_id = "social-content-publisher"` as the idempotent key.

**Acceptance criteria:**
- [ ] Seed runs without error: `python -m database.seeds.skill_social_content_publisher_seed`
- [ ] Skill with `external_id = "social-content-publisher"` exists in the DB
- [ ] `goal_schema` JSON has `fields` array with at least 4 entries
- [ ] Seed is idempotent (running twice does not create duplicates)

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run plant-test \
  python -m database.seeds.skill_social_content_publisher_seed 2>&1 | tail -5
```

---

#### E5-S2: Seed `execute-trade-order` skill with full `goal_schema`

**Branch:** `feat/PLANT-SKILLS-1-it2-e5`
**BLOCKED UNTIL:** E5-S1 (use same branch, sequential)
**Pattern:** Plant BackEnd — seed script

**Context (2 sentences):**
The `execute-trade-order` skill enables an agent to trade on a crypto/equity exchange on behalf of the customer with configurable entry conditions, stop-loss, profit targets, and run-window. Its `goal_schema` encodes all the required fields, exchange-specific options, and plan-gated limits.

**Files to read first (max 3):**
1. `src/Plant/BackEnd/database/seeds/skill_social_content_publisher_seed.py` — reference pattern (E5-S1, just created)
2. `src/Plant/BackEnd/models/skill.py` — Skill model

**What to build:**

Create `src/Plant/BackEnd/database/seeds/skill_execute_trade_order_seed.py`:

```python
EXECUTE_TRADE_ORDER_GOAL_SCHEMA = {
    "fields": [
        {
            "key": "exchange",
            "type": "string",
            "required": True,
            "label": "Exchange name",
            "placeholder": "e.g. delta_exchange",
            "help": "Must match a connected PlatformConnection platform_key",
        },
        {
            "key": "instrument",
            "type": "string",
            "required": True,
            "label": "Instrument / Symbol",
            "placeholder": "e.g. BTC-USDT, NIFTY",
        },
        {
            "key": "leverage",
            "type": "integer",
            "required": False,
            "label": "Leverage (if supported by exchange)",
            "min": 1,
            "max": 100,
            "default": 1,
        },
        {
            "key": "interval",
            "type": "select",
            "required": True,
            "label": "Candle interval",
            "options": ["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"],
            "default": "5m",
        },
        {
            "key": "trade_amount_usdt",
            "type": "decimal",
            "required": True,
            "label": "Trade amount (USDT)",
            "min": 10,
            "max_plan_gate": "max_trade_amount_usdt",
            "help": "Amount per trade. Maximum set by your subscription plan.",
        },
        {
            "key": "direction",
            "type": "select",
            "required": True,
            "label": "Trade direction",
            "options": ["buy", "sell", "both"],
            "default": "both",
        },
        {
            "key": "entry_condition",
            "type": "textarea",
            "required": True,
            "label": "Entry condition",
            "placeholder": "e.g. RSI < 30 AND price crosses above 200 EMA",
        },
        {
            "key": "stop_loss_pct",
            "type": "decimal",
            "required": True,
            "label": "Stop loss (%)",
            "min": 0.1,
            "max": 50,
            "default": 2.5,
        },
        {
            "key": "profit_target_pct",
            "type": "decimal",
            "required": True,
            "label": "Profit target (%)",
            "min": 0.1,
            "max": 100,
            "default": 5.0,
        },
        {
            "key": "max_stop_losses",
            "type": "integer",
            "required": True,
            "label": "Stop trading after N stop-losses",
            "min": 1,
            "max": 10,
            "default": 2,
            "help": "Agent halts the session after this many consecutive stop-losses",
        },
        {
            "key": "max_profit_exits",
            "type": "integer",
            "required": True,
            "label": "Stop trading after N profit exits",
            "min": 1,
            "max": 10,
            "default": 2,
        },
        {
            "key": "run_window",
            "type": "select",
            "required": True,
            "label": "Trading window",
            "options": ["24x7", "market_open_close", "custom"],
            "default": "24x7",
            "help": "24x7 for crypto; market_open_close = first/last 1hr for equity; custom for specific window",
        },
        {
            "key": "run_window_custom",
            "type": "string",
            "required": False,
            "label": "Custom window (IST, HH:MM-HH:MM)",
            "placeholder": "e.g. 09:15-10:15,14:30-15:30",
            "show_if": {"key": "run_window", "value": "custom"},
        },
    ],
    "platform_connections_required": True,
    "platform_connection_keys": ["exchange"],
    "approval_workflow": None,
    "halt_logic": {
        "stop_after_stop_losses": "max_stop_losses",
        "stop_after_profit_exits": "max_profit_exits",
    },
}
# Full upsert using external_id = "execute-trade-order"
```

**Acceptance criteria:**
- [ ] Seed runs without error
- [ ] Skill with `external_id = "execute-trade-order"` exists in the DB
- [ ] `goal_schema.fields` has 13 entries
- [ ] `halt_logic` key is present in `goal_schema`
- [ ] Seed is idempotent

**Test command:**
```bash
docker-compose -f docker-compose.test.yml run plant-test \
  python -m database.seeds.skill_execute_trade_order_seed 2>&1 | tail -5
```

---

## Iteration 3 — CP BackEnd Proxy + CP FrontEnd Goals & Performance Tabs

**Lane B→A — CP BackEnd thin proxy first, then CP FrontEnd wires to it.**

### Epic E6 — CP FrontEnd can read skill definitions and submit goal configurations

**Branch:** `feat/PLANT-SKILLS-1-it3-e6`
**Estimated time:** 1.5h (2 stories)

---

#### E6-S1: CP BackEnd thin proxy — skills, agent-skills, platform connections, performance stats

**Branch:** `feat/PLANT-SKILLS-1-it3-e6`
**BLOCKED UNTIL:** Iteration 2 merged (Plant APIs must exist at `/v1/...`)
**Pattern:** CP BackEnd — pattern (b): new `api/cp_skills.py` with `waooaw_router` + `PlantGatewayClient`

**Context (2 sentences):**
After Iteration 2, Plant BackEnd has all the APIs but CP FrontEnd cannot reach them directly — it must go through CP BackEnd (the thin proxy). This story creates one CP BackEnd file `api/cp_skills.py` that proxies four Plant endpoints: agent skills, goal-schema, platform connections, and performance stats.

**Files to read first (max 3):**
1. `src/CP/BackEnd/api/my_agents_summary.py` — reference for `waooaw_router` + `PlantGatewayClient` proxy pattern (lines 1–60)
2. `src/CP/BackEnd/services/plant_gateway_client.py` — client interface (full file, ~100 lines)
3. `src/CP/BackEnd/main.py` — where to add `include_router` (lines 1–80)

**Code patterns to copy exactly:**

```python
# src/CP/BackEnd/api/cp_skills.py

from core.routing import waooaw_router           # ← mandatory, never bare APIRouter
from fastapi import Depends, HTTPException, Request
from api.auth.dependencies import get_current_user
from services.plant_gateway_client import PlantGatewayClient
import os

router = waooaw_router(prefix="/cp", tags=["cp-skills"])

def _plant_client() -> PlantGatewayClient:
    base_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    if not base_url:
        raise RuntimeError("PLANT_GATEWAY_URL not configured")
    return PlantGatewayClient(base_url=base_url)

# CP BackEnd is a THIN PROXY — no business logic here.
# Pattern (b): new api/cp_skills.py with waooaw_router + PlantGatewayClient.
# All data lives in Plant; CP just forwards auth + request.

@router.get("/agents/{agent_id}/skills")
async def proxy_list_agent_skills(
    agent_id: str,
    request: Request,
    current_user=Depends(get_current_user),
):
    client = _plant_client()
    auth = request.headers.get("Authorization", "")
    resp = await client.request_json(
        method="GET",
        path=f"/v1/agents/{agent_id}/skills",
        headers={"Authorization": auth},
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Upstream error")
    return resp.json
```

Build equivalent proxy methods for:
- `GET /cp/agents/{agent_id}/skills` → `GET /v1/agents/{agent_id}/skills`
- `POST /cp/agents/{agent_id}/skills` → `POST /v1/agents/{agent_id}/skills`
- `DELETE /cp/agents/{agent_id}/skills/{skill_id}` → `DELETE /v1/agents/{agent_id}/skills/{skill_id}`
- `GET /cp/skills/{skill_id}/goal-schema` → `PATCH /v1/skills/{skill_id}/goal-schema` (GET only — reads current schema)
- `GET /cp/hired-agents/{id}/platform-connections` → proxied
- `POST /cp/hired-agents/{id}/platform-connections` → proxied
- `DELETE /cp/hired-agents/{id}/platform-connections/{conn_id}` → proxied
- `GET /cp/hired-agents/{id}/performance-stats` → proxied (pass through query params)

Register `cp_skills_router` in `src/CP/BackEnd/main.py`.

**Acceptance criteria:**
- [ ] `src/CP/BackEnd/api/cp_skills.py` exists
- [ ] All 8 proxy routes registered — none contain business logic (pure forwarding)
- [ ] `waooaw_router` used (not bare `APIRouter`)
- [ ] `PLANT_GATEWAY_URL` env var sourced from `os.getenv` — not hardcoded
- [ ] Tests pass:
```bash
docker-compose -f docker-compose.test.yml run cp-test \
  pytest src/CP/BackEnd/tests/ -k "cp_skills" -v 2>&1 | tail -20
```

---

#### E6-S2: CP FrontEnd — Goals tab renders dynamic form from `Skill.goal_schema`

**Branch:** `feat/PLANT-SKILLS-1-it3-e6`
**BLOCKED UNTIL:** E6-S1 (CP BackEnd proxy must exist)
**Pattern:** CP FrontEnd only — new component, no backend change

**Context (2 sentences):**
Today the Goals tab in `My Agents → Agent → Goals` shows a placeholder screen. This story replaces it with a real form: the UI fetches the `goal_schema` for each skill the agent carries, renders a dynamic form using the schema's `fields` array, and POSTs the customer's answers to `PUT /cp/goal-instances/{id}/settings`.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — current agent detail panel, find Goals tab render point
2. `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` — reference for existing service pattern

**What to build:**

Create `src/CP/FrontEnd/src/components/GoalConfigForm.tsx` — a generic form renderer driven by `goal_schema.fields`:

```typescript
import { useState } from 'react'
import { Button, Input, Dropdown, Textarea } from '@fluentui/react-components'

interface FieldDef {
  key: string
  type: 'string' | 'integer' | 'decimal' | 'select' | 'multiselect' | 'textarea' | 'boolean'
  label: string
  required?: boolean
  placeholder?: string
  help?: string
  options?: string[]
  min?: number
  max?: number
  default?: unknown
  show_if?: { key: string; value: unknown }
}

interface GoalSchema { fields: FieldDef[] }

interface Props {
  schema: GoalSchema
  initialValues?: Record<string, unknown>
  onSave: (values: Record<string, unknown>) => Promise<void>
  saving?: boolean
}

export default function GoalConfigForm({ schema, initialValues = {}, onSave, saving }: Props) {
  const [values, setValues] = useState<Record<string, unknown>>(
    Object.fromEntries(schema.fields.map(f => [f.key, initialValues[f.key] ?? f.default ?? '']))
  )

  const visible = (f: FieldDef) => {
    if (!f.show_if) return true
    return values[f.show_if.key] === f.show_if.value
  }

  const renderField = (f: FieldDef) => {
    if (!visible(f)) return null
    switch (f.type) {
      case 'select':
        return <Dropdown key={f.key} ... />
      case 'textarea':
        return <Textarea key={f.key} ... />
      default:
        return <Input key={f.key} type={f.type === 'integer' || f.type === 'decimal' ? 'number' : 'text'} ... />
    }
  }

  return (
    <form onSubmit={e => { e.preventDefault(); onSave(values) }}>
      {schema.fields.map(renderField)}
      <Button type="submit" appearance="primary" disabled={saving}>
        {saving ? 'Saving…' : 'Save Goals'}
      </Button>
    </form>
  )
}
```

Wire `GoalConfigForm` into the Goals tab of the agent detail panel in `MyAgents.tsx`:
- On tab open: `GET /api/cp/agents/{agent_id}/skills` → for each skill, `GET /api/cp/skills/{skill_id}/goal-schema`
- Render one `GoalConfigForm` per skill with loading + error states
- On save: POST to `PUT /api/cp/goal-instances/{goal_instance_id}/settings`

**Acceptance criteria:**
- [ ] `GoalConfigForm.tsx` exists and renders all field types: string, integer, select, multiselect, textarea
- [ ] `show_if` conditional fields hide/show correctly
- [ ] Goals tab shows one form per skill (not one combined form)
- [ ] Loading state while schema fetches
- [ ] Error state if schema fetch fails
- [ ] Build passes: `cd src/CP/FrontEnd && npm run build` exits 0

**Test command:**
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -5
```

---

### Epic E7 — Customer can see daily performance stats for each skill on their hired agent

**Branch:** `feat/PLANT-SKILLS-1-it3-e7`
**Estimated time:** 1h (2 stories × 30 min)

---

#### E7-S1: CP FrontEnd — Platform connections setup in Configure tab

**Branch:** `feat/PLANT-SKILLS-1-it3-e7`
**BLOCKED UNTIL:** E6-S1 (proxy must exist)
**Pattern:** CP FrontEnd only

**Context (2 sentences):**
The Configure tab in the agent detail panel currently shows generic settings. This story adds a "Connected Platforms" section that lists `PlatformConnection` records for this hired agent and shows a "Connect" button per required platform (from `goal_schema.platform_connection_keys`), which opens a modal for the customer to enter their API key — which is then sent to CP BackEnd and stored as a Secret Manager reference.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — Configure tab render point
2. `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` — pattern for service file

**What to build:**

Create `src/CP/FrontEnd/src/services/platformConnections.service.ts`:
```typescript
export async function listPlatformConnections(hiredInstanceId: string)
export async function createPlatformConnection(hiredInstanceId: string, body: CreateConnectionPayload)
export async function deletePlatformConnection(hiredInstanceId: string, connectionId: string)
```

Create `src/CP/FrontEnd/src/components/PlatformConnectionsPanel.tsx`:
- Lists existing connections (status badge: connected/pending/error)
- Shows "Connect [Platform]" buttons for `platform_connection_keys` not yet connected
- "Connect" button opens inline form accepting API key + secret → on submit calls `createPlatformConnection`
- DELETE button removes connection

Wire into Configure tab in `MyAgents.tsx`.

**Acceptance criteria:**
- [ ] `platformConnections.service.ts` exists with 3 exported functions
- [ ] `PlatformConnectionsPanel.tsx` renders connected and not-connected platforms
- [ ] API key/secret input fields are `type="password"` — never logged or stored in component state after submission
- [ ] Build passes: `cd src/CP/FrontEnd && npm run build` exits 0

**Test command:**
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -5
```

---

#### E7-S2: CP FrontEnd — Performance tab shows day-by-day stats per skill

**Branch:** `feat/PLANT-SKILLS-1-it3-e7`
**BLOCKED UNTIL:** E7-S1 (same branch, sequential)
**Pattern:** CP FrontEnd only

**Context (2 sentences):**
The Performance tab (`My Agents → Agent → Performance`) currently shows a placeholder. This story replaces it with a data table showing `PerformanceStat` rows returned from `GET /api/cp/hired-agents/{id}/performance-stats`, grouped by skill and platform with the most recent date first.

**Files to read first (max 3):**
1. `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` — Performance tab render point
2. `src/CP/FrontEnd/src/services/myAgentsSummary.service.ts` — reference service pattern

**What to build:**

Create `src/CP/FrontEnd/src/services/performanceStats.service.ts`:
```typescript
export interface PerformanceStat {
  id: string
  skill_id: string
  platform_key: string
  stat_date: string       // YYYY-MM-DD
  metrics: Record<string, number | string>
  collected_at: string
}

export async function getPerformanceStats(
  hiredInstanceId: string,
  filters?: { skillId?: string; platformKey?: string; fromDate?: string; toDate?: string }
): Promise<PerformanceStat[]>
```

Wire into Performance tab in `MyAgents.tsx`:
- On tab open: fetch stats for last 30 days
- Render a `<Table>` (Fluent UI) with columns: Date | Platform | and one column per metric key
- Loading state, error state, empty state ("Stats are collected daily. Check back after your agent's first run.")
- Skill selector dropdown to filter by skill when agent has multiple skills

**Acceptance criteria:**
- [ ] `performanceStats.service.ts` exists with `getPerformanceStats` exported
- [ ] Performance tab renders Fluent UI table with data
- [ ] Empty state message shown when `stats.length === 0`
- [ ] Loading state shown while data fetches
- [ ] Skill filter dropdown visible when agent has >1 skill
- [ ] Build passes: `cd src/CP/FrontEnd && npm run build` exits 0

**Test command:**
```bash
cd src/CP/FrontEnd && npm run build 2>&1 | tail -5
```
