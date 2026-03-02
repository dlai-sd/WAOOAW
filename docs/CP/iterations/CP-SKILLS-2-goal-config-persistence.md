# CP-SKILLS-2 — Goal Config Persistence

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-SKILLS-2` |
| Feature area | Customer Portal — Goal Configuration Persistence |
| Created | 2026-03-02 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CP/iterations/CP-SKILLS-1-skills-goals-performance.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 3 |
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
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [x] Every story that adds env vars lists the exact Terraform file paths to update (none in this plan)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (E1, E2) before frontend (E3)
- [x] No placeholders remain

---

## Background — What CP-SKILLS-1 Built (Already Merged — PRs #834, #835)

| Asset | Status | Key file |
|---|---|---|
| CP BackEnd: 6 proxy routes for skills, platform connections, performance stats | ✅ Live | `src/CP/BackEnd/api/cp_skills.py` |
| CP FrontEnd: `agentSkills.service.ts` — `listHiredAgentSkills()` + `getSkill()` | ✅ Live | `src/CP/FrontEnd/src/services/agentSkills.service.ts` |
| CP FrontEnd: `SkillsPanel.tsx` with `GoalConfigForm` | ✅ Live | `src/CP/FrontEnd/src/components/SkillsPanel.tsx` |
| CP FrontEnd: Skills + Performance tabs in `MyAgents.tsx` | ✅ Live | `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` |

**What is still broken after CP-SKILLS-1:**
- `GoalConfigForm` "Save goal config" button only sets local React state. Nothing is written to the DB.
- Page refresh loses all goal field values — no persistence whatsoever.
- `AgentSkillModel` (Plant DB) has no `goal_config` column — the table cannot store customer-entered values.
- `list_agent_skills` response does not include `goal_config` so the FE cannot seed saved values on load.

**What CP-SKILLS-2 fixes:** All three layers — DB column → Plant endpoint → CP proxy → FE wire.

---

## Proxy Architecture — Patterns Used

| Layer | Pattern | File |
|---|---|---|
| Plant BackEnd | New endpoint (Lane B) | `src/Plant/BackEnd/api/v1/agent_skills.py` |
| CP BackEnd | Pattern B — append to existing file | `src/CP/BackEnd/api/cp_skills.py` |
| CP FrontEnd | Pattern A — call existing `/cp/*` via `gatewayRequestJson` | `src/CP/FrontEnd/src/services/agentSkills.service.ts`, `SkillsPanel.tsx` |

```
Browser PATCH → CP BackEnd /cp/hired-agents/{id}/skills/{skill_id}/goal-config
  → [two-hop] resolve agent_id from hired agent record
  → Plant BackEnd PATCH /api/v1/agents/{agent_id}/skills/{skill_id}/goal-config
  → writes goal_config JSON to agent_skills.goal_config column
```

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — Plant BackEnd: DB migration + PATCH endpoint + GET response update | 1 | 2 | ~1h 30m | Start + 2h |
| 2 | Lane B — CP BackEnd: append PATCH proxy route to `cp_skills.py` + tests | 1 | 1 | ~45m | Start + 1h |
| 3 | Lane A — CP FrontEnd: service + GoalConfigForm wire | 1 | 2 | ~1h 30m | Start + 2h |

**Estimate basis:** DB migration = 20 min | New BE endpoint = 45 min | GET response update = 15 min | CP proxy route = 30 min | Tests = 15 min | FE service update = 20 min | FE component wire = 45 min | PR = 10 min. Add 20% buffer.

---

## How to Launch Each Iteration

### Iteration 1

**Pre-flight check (run in terminal before launching):**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(CP-SKILLS-1): iteration 2 — CP FrontEnd skills + performance
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

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy / Alembic engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11/FastAPI/SQLAlchemy/Alembic engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-SKILLS-2-goal-config-persistence.md
YOUR SCOPE: Iteration 1 only — Epic E1. Do not touch Iteration 2 or 3 content.
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

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(CP-SKILLS-2): iteration 1 — Plant BackEnd goal-config persistence
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / httpx engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior Python 3.11/FastAPI/httpx engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-SKILLS-2-goal-config-persistence.md
YOUR SCOPE: Iteration 2 only — Epic E2. Do not touch Iteration 1 or 3 content.
TIME BUDGET: 1h. If you reach 1h 30m without finishing, follow STUCK PROTOCOL now.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(CP-SKILLS-2): iteration 1 — Plant BackEnd goal-config persistence
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Execute Epic E2: E2-S1 only.
4. When docker-tested, open the iteration PR. Post URL. HALT.
```

**Come back at:** Start + 1h

---

### Iteration 3

> ⚠️ Do NOT launch until Iteration 2 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(CP-SKILLS-2): iteration 2 — CP BackEnd goal-config proxy
```

**Steps to launch:** same as above (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 3 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React / TypeScript / Fluent UI engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React/TypeScript/Fluent UI engineer, I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-SKILLS-2-goal-config-persistence.md
YOUR SCOPE: Iteration 3 only — Epic E3. Do not touch Iteration 1 or 2 content.
TIME BUDGET: 1h 30m. If you reach 2h without finishing, follow STUCK PROTOCOL now.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(CP-SKILLS-2): iteration 2 — CP BackEnd goal-config proxy
  If not: post "Blocked: Iteration 2 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 3" sections. Read nothing else.
3. Execute in order: E3-S1 → E3-S2
4. Respect BLOCKED UNTIL on E3-S2.
5. When all stories are docker-tested, open the iteration PR. Post URL. HALT.
```

**Come back at:** Start + 2h

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `src/Plant/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy / Alembic engineer |
| `src/CP/BackEnd/` | Senior Python 3.11 / FastAPI / httpx engineer |
| `src/CP/FrontEnd/` | Senior React / TypeScript / Fluent UI engineer |

---

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
# 1. Create the first epic branch from main
git checkout main && git pull
git checkout -b feat/CP-SKILLS-2-it1-e1

# 2. Push an empty init commit so the branch exists on remote
git commit --allow-empty -m "chore(CP-SKILLS-2): start iteration 1"
git push origin feat/CP-SKILLS-2-it1-e1

# 3. Open draft PR
gh pr create \
  --base main \
  --head feat/CP-SKILLS-2-it1-e1 \
  --draft \
  --title "tracking: CP-SKILLS-2 Iteration 1 — in progress" \
  --body "## tracking: CP-SKILLS-2 Iteration 1

Subscribe to this PR for story notifications.

### Stories
- [ ] [E1-S1] Alembic migration 025 — add goal_config JSONB to agent_skills
- [ ] [E1-S2] PATCH /api/v1/agents/{agent_id}/skills/{skill_id}/goal-config + GET response update

_Live updates posted as comments below ↓_"
```

---

### Rule 1 — Branch discipline
One epic = one branch: `feat/CP-SKILLS-2-itN-eN`.
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
git commit -m "feat(CP-SKILLS-2): [story title]"
git push origin feat/CP-SKILLS-2-itN-eN

# Update tracking table in this plan file
git add docs/CP/iterations/CP-SKILLS-2-goal-config-persistence.md
git commit -m "docs(CP-SKILLS-2): mark [story-id] done"
git push origin feat/CP-SKILLS-2-itN-eN

# Post progress comment to tracking draft PR
gh pr comment \
  $(gh pr list --head feat/CP-SKILLS-2-it1-e1 --json number -q '.[0].number') \
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
git push origin feat/CP-SKILLS-2-itN-eN
gh pr create \
  --base main \
  --head feat/CP-SKILLS-2-itN-eN \
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
git checkout -b feat/CP-SKILLS-2-itN
git merge --no-ff feat/CP-SKILLS-2-itN-e1
# For iteration 3: git merge --no-ff feat/CP-SKILLS-2-it3-e3
git push origin feat/CP-SKILLS-2-itN

gh pr create \
  --base main \
  --head feat/CP-SKILLS-2-itN \
  --title "feat(CP-SKILLS-2): iteration N — [one-line summary]" \
  --body "## CP-SKILLS-2 Iteration N

### Stories completed
[paste tracking table rows for this iteration]

### Docker integration
All containers exited 0 ✅

### NFR checklist
- [ ] waooaw_router() — no bare APIRouter
- [ ] GET routes use get_read_db_session()
- [ ] get_db_session() used only for PATCH/POST/DELETE writes
- [ ] X-Correlation-ID forwarded on all outbound httpx calls in CP proxy
- [ ] No env-specific values in code
- [ ] FE: loading + error + success states on GoalConfigForm Save button
- [ ] Tests >= 80% coverage on new BE code"
```

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | `waooaw_router()` factory — never bare `APIRouter` | CI ruff ban — PR blocked |
| 2 | `get_read_db_session()` on all GET routes | Primary DB overloaded |
| 3 | `get_db_session()` (write session) on PATCH/POST/DELETE | Writes go to wrong DB |
| 4 | `X-Correlation-ID` forwarded on every outbound httpx call | Trace broken |
| 5 | Loading + error + success states on every FE data-mutating action | Silent failures |
| 6 | Tests >= 80% coverage on all new BE code | PR blocked by CI |
| 7 | PR always `--base main` — never target an intermediate branch | Work never ships |
| 8 | CP BackEnd Pattern B: append new route to `api/cp_skills.py` (file already exists) | Architecture violation |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | E1: Customer's goal config is stored in the DB | Alembic migration 025 — add `goal_config` JSONB to `agent_skills` + update model | 🔴 Not Started | — |
| E1-S2 | 1 | E1: Customer's goal config is stored in the DB | `PATCH /api/v1/agents/{agent_id}/skills/{skill_id}/goal-config` endpoint + return `goal_config` in GET | 🔴 Not Started | — |
| E2-S1 | 2 | E2: CP BackEnd forwards goal config saves to Plant | Append `PATCH /api/cp/hired-agents/{id}/skills/{skill_id}/goal-config` to `cp_skills.py` + tests | 🔴 Not Started | — |
| E3-S1 | 3 | E3: Customer saves goal config and it survives a refresh | Add `saveGoalConfig()` to `agentSkills.service.ts` + update `AgentSkill` type with `goal_config` | 🔴 Not Started | — |
| E3-S2 | 3 | E3: Customer saves goal config and it survives a refresh | Wire `GoalConfigForm` in `SkillsPanel.tsx` — seed values, persist on Save, loading/success/error states | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Plant BackEnd: DB Column + Endpoint

**Scope:** Add `goal_config` JSONB column to `agent_skills` table (Alembic migration 025), update the SQLAlchemy model, extend `list_agent_skills` GET response to return `goal_config`, and add a new `PATCH /api/v1/agents/{agent_id}/skills/{skill_id}/goal-config` endpoint that writes customer goal values.

**Branch for Epic E1:** `feat/CP-SKILLS-2-it1-e1`

**Docker integration test command:**
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit plant-backend-test
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```

---

### E1 — Customer's goal config is stored in the DB

**Epic complete ✅** ← Agent: add this line here and commit when all E1 stories pass docker test.

---

#### Story E1-S1: Alembic migration 025 — add `goal_config` JSONB to `agent_skills` + update model

**BLOCKED UNTIL:** none
**Estimated time:** 30 min
**Branch:** `feat/CP-SKILLS-2-it1-e1`
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do:**
Create Alembic migration `025_agent_skill_goal_config` that adds a nullable JSONB column `goal_config` to the `agent_skills` table. Then update `AgentSkillModel` in `src/Plant/BackEnd/models/agent_skill.py` to include the new column. The migration must be idempotent (use `IF NOT EXISTS` guard pattern from migration 024).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/database/migrations/versions/024_seed_demo_hired_agents.py` | 1–40 | `revision`, `down_revision`, `op.execute` pattern, file header format |
| `src/Plant/BackEnd/models/agent_skill.py` | 1–60 | Existing columns, import style, `__tablename__`, `__table_args__` shape |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/database/migrations/versions/025_agent_skill_goal_config.py` | create | New Alembic migration — see code pattern below |
| `src/Plant/BackEnd/models/agent_skill.py` | modify | Add `goal_config` column after `ordinal` column — see code pattern below |

**Code patterns to copy exactly:**

```python
# src/Plant/BackEnd/database/migrations/versions/025_agent_skill_goal_config.py
"""Add goal_config JSONB column to agent_skills

Revision ID: 025_agent_skill_goal_config
Revises: 024_seed_demo_hired_agents
Create Date: 2026-03-02

Purpose:
    Adds a nullable JSONB column `goal_config` to `agent_skills`.
    Stores customer-entered goal configuration values (e.g. post_frequency,
    target_platforms) keyed by field name from the skill's goal_schema.
    Default NULL = no config saved yet.
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "025_agent_skill_goal_config"
down_revision = "024_seed_demo_hired_agents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE agent_skills
        ADD COLUMN IF NOT EXISTS goal_config JSONB DEFAULT NULL
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE agent_skills
        DROP COLUMN IF EXISTS goal_config
    """)
```

```python
# In src/Plant/BackEnd/models/agent_skill.py — add after the `ordinal` column:
from sqlalchemy.dialects.postgresql import JSONB

# Add this column after ordinal:
goal_config = Column(
    JSONB,
    nullable=True,
    default=None,
    comment="Customer-entered goal configuration values keyed by goal_schema field key",
)
```

**Acceptance criteria:**
1. Running `alembic upgrade head` in Docker adds `goal_config` column to `agent_skills` table without error
2. `alembic downgrade -1` removes the column without error
3. `AgentSkillModel` has a `goal_config` attribute that accepts `None` and a `dict`
4. Existing unit tests for `agent_skills.py` still pass (no model breaks)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/unit/test_agent_skill_model.py` | Create `AgentSkillModel` with `goal_config=None` | Object created, `goal_config is None` |
| E1-S1-T2 | same | Create `AgentSkillModel` with `goal_config={"post_frequency": 5}` | `goal_config["post_frequency"] == 5` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-backend-test \
  pytest src/Plant/BackEnd/tests/unit/test_agent_skill_model.py -v
```

**Commit message:** `feat(CP-SKILLS-2): migration 025 — add goal_config JSONB to agent_skills`

**Done signal:** `"E1-S1 done. Files: 025_agent_skill_goal_config.py, models/agent_skill.py. Tests: T1 ✅ T2 ✅"`

---

#### Story E1-S2: `PATCH /api/v1/agents/{agent_id}/skills/{skill_id}/goal-config` + return `goal_config` in GET

**BLOCKED UNTIL:** E1-S1 committed to `feat/CP-SKILLS-2-it1-e1`
**Estimated time:** 45 min
**Branch:** `feat/CP-SKILLS-2-it1-e1` (same branch, continue from E1-S1)
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do:**
In `src/Plant/BackEnd/api/v1/agent_skills.py`: (1) Add `goal_config` field to `AgentSkillResponse` Pydantic model; (2) Update `list_agent_skills` GET to return `goal_config` from the joined `AgentSkillModel` row; (3) Add a new `PATCH /{agent_id}/skills/{skill_id}/goal-config` route that writes `goal_config` to the `agent_skills` row. The PATCH route uses the **write** session (`get_db`) because it writes data.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/api/v1/agent_skills.py` | 1–200 (full file) | `AgentSkillResponse`, `list_agent_skills`, router definition, `waooaw_router` import |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/api/v1/agent_skills.py` | modify | Three changes — see code patterns below |

**Code patterns to copy exactly:**

```python
# 1. Add goal_config to AgentSkillResponse (after ordinal field):
class AgentSkillResponse(BaseModel):
    id: str
    agent_id: str
    skill_id: str
    is_primary: bool
    ordinal: int
    goal_config: Optional[dict] = None   # ← ADD THIS
    skill_name: Optional[str] = None
    skill_category: Optional[str] = None
    goal_schema: Optional[dict] = None   # ← ADD THIS (from joined Skill row)

    class Config:
        from_attributes = True
```

```python
# 2. In list_agent_skills — extend the return object to include goal_config:
# (existing return list comprehension — add goal_config and goal_schema fields)
return [
    AgentSkillResponse(
        id=row.AgentSkillModel.id,
        agent_id=str(row.AgentSkillModel.agent_id),
        skill_id=str(row.AgentSkillModel.skill_id),
        is_primary=row.AgentSkillModel.is_primary,
        ordinal=row.AgentSkillModel.ordinal,
        goal_config=row.AgentSkillModel.goal_config,     # ← ADD
        skill_name=row.Skill.name,
        skill_category=row.Skill.category,
        goal_schema=row.Skill.goal_schema,               # ← ADD
    )
    for row in rows
]
```

```python
# 3. New PATCH route — add after detach_skill, before the skills_router section:

class GoalConfigUpdateRequest(BaseModel):
    goal_config: dict


@router.patch("/{agent_id}/skills/{skill_id}/goal-config", response_model=AgentSkillResponse)
async def update_goal_config(
    agent_id: str,
    skill_id: str,
    body: GoalConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),   # write session — PATCH writes data
) -> AgentSkillResponse:
    """
    Persist customer-entered goal configuration values for an agent-skill link.
    Overwrites existing goal_config. Body: {"goal_config": {"field_key": value, ...}}
    """
    result = await db.execute(
        select(AgentSkillModel, Skill)
        .join(Skill, AgentSkillModel.skill_id == Skill.id)
        .where(AgentSkillModel.agent_id == _to_uuid(agent_id))
        .where(AgentSkillModel.skill_id == _to_uuid(skill_id))
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Agent-skill link not found")

    link, skill = row.AgentSkillModel, row.Skill
    link.goal_config = body.goal_config
    await db.commit()
    await db.refresh(link)

    return AgentSkillResponse(
        id=link.id,
        agent_id=str(link.agent_id),
        skill_id=str(link.skill_id),
        is_primary=link.is_primary,
        ordinal=link.ordinal,
        goal_config=link.goal_config,
        skill_name=skill.name,
        skill_category=skill.category,
        goal_schema=skill.goal_schema,
    )
```

**Acceptance criteria:**
1. `PATCH /api/v1/agents/{agent_id}/skills/{skill_id}/goal-config` with `{"goal_config": {"post_frequency": 5}}` returns 200 with `goal_config.post_frequency == 5`
2. Same PATCH followed by `GET /api/v1/agents/{agent_id}/skills` returns the skill with `goal_config.post_frequency == 5`
3. PATCH on a non-existent agent-skill link returns 404
4. `GET /api/v1/agents/{agent_id}/skills` response now includes both `goal_config` and `goal_schema` fields

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/Plant/BackEnd/tests/unit/test_agent_skills_route.py` | Mock DB returns valid `AgentSkillModel` row; PATCH with `{"goal_config": {"x": 1}}` | Response 200, `goal_config.x == 1` |
| E1-S2-T2 | same | Mock DB returns None | Response 404 |
| E1-S2-T3 | same | Mock GET query | `goal_config` and `goal_schema` fields present in list response |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run plant-backend-test \
  pytest src/Plant/BackEnd/tests/unit/test_agent_skills_route.py -v \
  --cov=src/Plant/BackEnd/api/v1/agent_skills --cov-fail-under=80
```

**Commit message:** `feat(CP-SKILLS-2): PATCH goal-config endpoint + return goal_config in GET list`

**Done signal:** `"E1-S2 done. Files: api/v1/agent_skills.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

## Iteration 2 — CP BackEnd: Goal Config Proxy Route

**Scope:** Append one new `PATCH` proxy route to the existing `src/CP/BackEnd/api/cp_skills.py`. The route performs the same two-hop as `list_hired_agent_skills` (resolve `agent_id` from hired agent record, then PATCH forward to Plant) and returns the Plant response.

**Branch for Epic E2:** `feat/CP-SKILLS-2-it2-e2`

**Docker integration test command:**
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit cp-backend-test
exit_code=$?; docker compose -f docker-compose.test.yml down; exit $exit_code
```

---

### E2 — CP BackEnd forwards goal config saves to Plant

**Epic complete ✅** ← Agent: add this line here and commit when E2 stories pass docker test.

---

#### Story E2-S1: Append `PATCH /api/cp/hired-agents/{id}/skills/{skill_id}/goal-config` to `cp_skills.py` + tests

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 45 min
**Branch:** `feat/CP-SKILLS-2-it2-e2`
**CP BackEnd pattern:** B — append new route to existing `src/CP/BackEnd/api/cp_skills.py` (file already exists from CP-SKILLS-1)

**What to do:**
`cp_skills.py` already has `_plant_get_json`, `_plant_post_json`, `_plant_delete_json` helpers. Add a `_plant_patch_json` helper using the same pattern. Then add one new route `PATCH /hired-agents/{hired_instance_id}/skills/{skill_id}/goal-config` that (1) resolves `agent_id` from Plant via the existing two-hop pattern in `list_hired_agent_skills`, then (2) PATCHes Plant at `PATCH /api/v1/agents/{agent_id}/skills/{skill_id}/goal-config`. Add a Pydantic `GoalConfigBody` model. Add 3 tests in `test_cp_skills_routes.py`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/BackEnd/api/cp_skills.py` | 1–211 (full file) | `_plant_get_json`, `_plant_post_json` helper patterns; `list_hired_agent_skills` two-hop pattern; existing `router` variable |
| `src/CP/BackEnd/tests/test_cp_skills_routes.py` | 1–50 | `_mock_httpx_get` helper; `client`, `auth_headers` fixture usage pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/BackEnd/api/cp_skills.py` | modify | Add `_plant_patch_json` helper + `GoalConfigBody` model + PATCH route — see code patterns below |
| `src/CP/BackEnd/tests/test_cp_skills_routes.py` | modify | Add 3 tests for the new PATCH route — see code patterns below |

**Code patterns to copy exactly:**

```python
# Add _plant_patch_json helper (after _plant_post_json, before Pydantic models section):

async def _plant_patch_json(
    *, url: str, body: dict, authorization: str | None, correlation_id: str | None
) -> dict:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if authorization:
        headers["Authorization"] = authorization
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(url, json=body, headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Resource not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
```

```python
# Add GoalConfigBody Pydantic model (in the "Pydantic models" section, after PlatformConnectionBody):

class GoalConfigBody(BaseModel):
    goal_config: dict[str, Any]
```

```python
# Add PATCH route (at the end of cp_skills.py, after get_performance_stats):

@router.patch("/hired-agents/{hired_instance_id}/skills/{skill_id}/goal-config")
async def save_goal_config(
    hired_instance_id: str,
    skill_id: str,
    body: GoalConfigBody,
    request: Request,
    _user: User = Depends(get_current_user),
) -> dict:
    """
    Two-hop proxy:
    1. Resolve agent_id: GET /api/v1/hired-agents/by-id/{hired_instance_id}
    2. PATCH goal_config: PATCH /api/v1/agents/{agent_id}/skills/{skill_id}/goal-config
    """
    base = _plant_base_url()
    auth = request.headers.get("Authorization")
    cid = request.headers.get("X-Correlation-ID")

    # Hop 1: resolve agent_id
    hired_data = await _plant_get_json(
        url=f"{base}/api/v1/hired-agents/by-id/{hired_instance_id}",
        authorization=auth,
        correlation_id=cid,
    )
    agent_id = (hired_data or {}).get("agent_id") or ""
    if not agent_id:
        raise HTTPException(status_code=404, detail="Hired agent or agent_id not found")

    # Hop 2: persist goal_config
    return await _plant_patch_json(
        url=f"{base}/api/v1/agents/{agent_id}/skills/{skill_id}/goal-config",
        body={"goal_config": body.goal_config},
        authorization=auth,
        correlation_id=cid,
    )
```

```python
# Tests to add at the end of test_cp_skills_routes.py:

# ── PATCH /api/cp/hired-agents/{id}/skills/{skill_id}/goal-config ─────────────

@pytest.mark.unit
def test_save_goal_config_success(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    hop1_response = {"agent_id": "AGT-001", "hired_instance_id": "HIRED-001"}
    hop2_response = {
        "id": "link-001",
        "agent_id": "AGT-001",
        "skill_id": "SK-001",
        "goal_config": {"post_frequency": 5},
    }
    call_count = 0

    def side_effect(url, **kwargs):
        nonlocal call_count
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.text = "ok"
        mock_resp.status_code = 200
        mock_resp.json.return_value = hop1_response if call_count == 0 else hop2_response
        call_count += 1
        return mock_resp

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=side_effect)
    mock_client.patch = AsyncMock(side_effect=side_effect)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.patch(
            "/api/cp/hired-agents/HIRED-001/skills/SK-001/goal-config",
            headers=auth_headers,
            json={"goal_config": {"post_frequency": 5}},
        )

    assert resp.status_code == 200
    assert resp.json()["goal_config"]["post_frequency"] == 5


@pytest.mark.unit
def test_save_goal_config_hired_agent_not_found(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 404
    mock_resp.text = "not found"

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.patch(
            "/api/cp/hired-agents/BAD-ID/skills/SK-001/goal-config",
            headers=auth_headers,
            json={"goal_config": {"x": 1}},
        )

    assert resp.status_code == 404


@pytest.mark.unit
def test_save_goal_config_plant_unavailable(client, auth_headers, monkeypatch):
    monkeypatch.setenv("PLANT_GATEWAY_URL", "http://plant-gateway-test:8000")
    # Hop 1 succeeds — hop 2 (PATCH) raises network error
    hop1_response = {"agent_id": "AGT-001"}

    get_resp = MagicMock(spec=httpx.Response)
    get_resp.status_code = 200
    get_resp.json.return_value = hop1_response
    get_resp.text = "ok"

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=get_resp)
    mock_client.patch = AsyncMock(side_effect=Exception("connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("api.cp_skills.httpx.AsyncClient", return_value=mock_client):
        resp = client.patch(
            "/api/cp/hired-agents/HIRED-001/skills/SK-001/goal-config",
            headers=auth_headers,
            json={"goal_config": {"x": 1}},
        )

    assert resp.status_code == 502
```

**Acceptance criteria:**
1. `PATCH /api/cp/hired-agents/HIRED-001/skills/SK-001/goal-config` with valid auth returns 200 and `goal_config` from Plant
2. Non-existent hired agent returns 404
3. Plant network error returns 502
4. Missing auth header returns 401

**Tests to write:** See code patterns above (T1, T2, T3 — 3 tests).

**Test command:**
```bash
docker compose -f docker-compose.test.yml run cp-backend-test \
  pytest src/CP/BackEnd/tests/test_cp_skills_routes.py -v \
  --cov=src/CP/BackEnd/api/cp_skills --cov-fail-under=80
```

**Commit message:** `feat(CP-SKILLS-2): CP BackEnd PATCH goal-config proxy + tests`

**Done signal:** `"E2-S1 done. Files: api/cp_skills.py, tests/test_cp_skills_routes.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

## Iteration 3 — CP FrontEnd: Wire GoalConfigForm

**Scope:** Update `agentSkills.service.ts` to add `saveGoalConfig()` and extend the `AgentSkill` type with `goal_config` and `goal_schema` fields returned by the updated GET. Then update `GoalConfigForm` in `SkillsPanel.tsx` to seed field values from `skill.goal_config` on mount and call `saveGoalConfig()` on Save — replacing the fake local-state-only save with a real API call that shows loading, success, and error feedback.

**Branch for Epic E3:** `feat/CP-SKILLS-2-it3-e3`

**TypeScript check command:**
```bash
cd src/CP/FrontEnd && node_modules/.bin/tsc --noEmit
```

---

### E3 — Customer saves goal config and it survives a refresh

**Epic complete ✅** ← Agent: add this line here and commit when all E3 stories pass tsc + docker test.

---

#### Story E3-S1: Add `saveGoalConfig()` to `agentSkills.service.ts` + update `AgentSkill` type

**BLOCKED UNTIL:** Iteration 2 merged to `main`
**Estimated time:** 25 min
**Branch:** `feat/CP-SKILLS-2-it3-e3`
**CP BackEnd pattern:** A — call existing `/cp/hired-agents/{id}/skills/{skill_id}/goal-config` via `gatewayRequestJson`

**What to do:**
Open `src/CP/FrontEnd/src/services/agentSkills.service.ts`. Extend `AgentSkill` interface to add `goal_config?: Record<string, unknown>` and `goal_schema` already has `fields` but also add `requires_platform_connections` is already there — also ensure the full `GoalSchema` type is complete. Add `saveGoalConfig(hiredInstanceId, skillId, goalConfig)` function that calls `PATCH /cp/hired-agents/{id}/skills/{skill_id}/goal-config` via `gatewayRequestJson`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/services/agentSkills.service.ts` | 1–54 (full file) | Existing `AgentSkill` interface, `GoalSchema`, `gatewayRequestJson` import, function signatures |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/services/agentSkills.service.ts` | modify | Add `goal_config` to `AgentSkill` + add `saveGoalConfig` function — see code patterns below |

**Code patterns to copy exactly:**

```typescript
// 1. Extend AgentSkill interface — add goal_config field:
export interface AgentSkill {
  skill_id: string
  name: string
  display_name: string
  description?: string
  category?: string
  goal_schema?: GoalSchema
  goal_config?: Record<string, unknown>  // ← ADD: saved values from DB, null if never saved
}

// 2. Add saveGoalConfig function (after getSkill at the end of the file):

/**
 * Persist goal configuration values for a hired agent's skill.
 * Calls: PATCH /api/cp/hired-agents/{hired_instance_id}/skills/{skill_id}/goal-config
 * Returns the updated AgentSkill row with the persisted goal_config.
 */
export async function saveGoalConfig(
  hiredInstanceId: string,
  skillId: string,
  goalConfig: Record<string, unknown>,
): Promise<AgentSkill> {
  return gatewayRequestJson<AgentSkill>(
    `/cp/hired-agents/${encodeURIComponent(hiredInstanceId)}/skills/${encodeURIComponent(skillId)}/goal-config`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal_config: goalConfig }),
    },
  )
}
```

**Acceptance criteria:**
1. `tsc --noEmit` exits 0 — no TypeScript errors
2. `AgentSkill.goal_config` is typed as `Record<string, unknown> | undefined`
3. `saveGoalConfig` exported from the service file
4. `listHiredAgentSkills` return type includes `goal_config` (inherited from updated interface)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/CP/FrontEnd/src/__tests__/agentSkills.service.test.ts` | Mock `gatewayRequestJson` resolves `{skill_id: "SK-001", goal_config: {x: 1}}` | `saveGoalConfig` returns object with `goal_config.x === 1` |
| E3-S1-T2 | same | Mock `gatewayRequestJson` rejects | `saveGoalConfig` propagates rejection |

**Test command:**
```bash
cd src/CP/FrontEnd && node_modules/.bin/tsc --noEmit && \
  node_modules/.bin/jest src/__tests__/agentSkills.service.test.ts --no-coverage
```

**Commit message:** `feat(CP-SKILLS-2): add saveGoalConfig to agentSkills.service.ts + extend AgentSkill type`

**Done signal:** `"E3-S1 done. Files: services/agentSkills.service.ts. Tests: T1 ✅ T2 ✅. tsc ✅"`

---

#### Story E3-S2: Wire `GoalConfigForm` in `SkillsPanel.tsx` — seed values + real Save

**BLOCKED UNTIL:** E3-S1 committed to `feat/CP-SKILLS-2-it3-e3`
**Estimated time:** 50 min
**Branch:** `feat/CP-SKILLS-2-it3-e3` (same branch, continue from E3-S1)
**CP BackEnd pattern:** A — uses `saveGoalConfig` from `agentSkills.service.ts` (added in E3-S1)

**What to do:**
Open `src/CP/FrontEnd/src/components/SkillsPanel.tsx`. Find `GoalConfigForm`. Currently `values` state is initialised to `{}` and Save only sets `setSaved(true)`. Make three changes: (1) seed `values` initial state from `skill.goal_config ?? {}`; (2) replace the Save `onClick` with an async handler that calls `saveGoalConfig(hiredInstanceId, skill.skill_id, values)` and shows loading/success/error states; (3) `GoalConfigForm` needs `hiredInstanceId` and `skillId` props added so it can call the service — update the props interface and `SkillsPanel`'s render site of `GoalConfigForm` to pass them.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/SkillsPanel.tsx` | 195–260 | `GoalConfigForm` component: `values` useState, `saved` useState, Save button onClick, current props interface |
| `src/CP/FrontEnd/src/components/SkillsPanel.tsx` | 440–514 | `SkillsPanel` render — where `<GoalConfigForm skill={skill} readOnly={readOnly} />` is called |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/SkillsPanel.tsx` | modify | Four precise changes — see code patterns below |

**Code patterns to copy exactly:**

```typescript
// 1. Update GoalConfigFormProps to add hiredInstanceId + skillId:
interface GoalConfigFormProps {
  skill: AgentSkill
  hiredInstanceId: string   // ← ADD
  skillId: string           // ← ADD
  readOnly: boolean
}
```

```typescript
// 2. In GoalConfigForm — add import (at top of file in imports section):
import { saveGoalConfig } from '../services/agentSkills.service'
```

```typescript
// 3. Replace GoalConfigForm component body — seed initial values + real Save:
function GoalConfigForm({ skill, hiredInstanceId, skillId, readOnly }: GoalConfigFormProps) {
  const fields = skill.goal_schema?.fields ?? []
  // Seed from DB-persisted goal_config; fall back to {} if never saved
  const [values, setValues] = useState<Record<string, unknown>>(
    () => (skill.goal_config as Record<string, unknown>) ?? {}
  )
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
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
    setSaveError(null)
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    setSaveError(null)
    try {
      await saveGoalConfig(hiredInstanceId, skillId, values)
      setSaved(true)
    } catch (e: unknown) {
      setSaveError(e instanceof Error ? e.message : 'Failed to save goal config')
    } finally {
      setSaving(false)
    }
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
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <Button appearance="primary" size="small" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save goal config'}
          </Button>
          {saved && <span style={{ opacity: 0.7, fontSize: '0.85rem', color: 'var(--colorBrandForeground1)' }}>Saved ✓</span>}
          {saveError && <span style={{ opacity: 0.9, fontSize: '0.85rem', color: 'var(--colorPaletteRedForeground1)' }}>{saveError}</span>}
        </div>
      )}
    </div>
  )
}
```

```typescript
// 4. In SkillsPanel render — update GoalConfigForm call site (inside the isExpanded block):
// Find: <GoalConfigForm skill={skill} readOnly={readOnly} />
// Replace with:
<GoalConfigForm
  skill={skill}
  hiredInstanceId={hiredInstanceId}
  skillId={skill.skill_id}
  readOnly={readOnly}
/>
```

**Acceptance criteria:**
1. `tsc --noEmit` exits 0
2. Opening Skills tab for an agent that has saved goal config shows the previously saved values in the fields (not empty)
3. Editing a field and clicking "Save goal config" calls `saveGoalConfig` (verified by mock in test)
4. While saving, button shows "Saving..." and is disabled
5. On save success, "Saved ✓" appears next to the button
6. On save failure, error message appears next to the button
7. `readOnly=true` hides the Save button entirely

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S2-T1 | `src/CP/FrontEnd/src/__tests__/SkillsPanel.test.tsx` | Render with `skill.goal_config = {post_frequency: 10}` | Input for `post_frequency` shows value `"10"` |
| E3-S2-T2 | same | Mock `saveGoalConfig` resolves; click Save | "Saved ✓" appears in DOM |
| E3-S2-T3 | same | Mock `saveGoalConfig` rejects with "Network error"; click Save | "Network error" text appears in DOM |
| E3-S2-T4 | same | Render with `readOnly={true}` | Save button not in DOM |

**Test command:**
```bash
cd src/CP/FrontEnd && node_modules/.bin/tsc --noEmit && \
  node_modules/.bin/jest src/__tests__/SkillsPanel.test.tsx --no-coverage
```

**Commit message:** `feat(CP-SKILLS-2): wire GoalConfigForm — seed values + real save with loading/error states`

**Done signal:** `"E3-S2 done. Files: components/SkillsPanel.tsx. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅. tsc ✅"`
