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

<!-- ITERATION 1 STORY CARDS GO BELOW — next commit -->

<!-- ITERATION 2 STORY CARDS GO BELOW — next commit -->
