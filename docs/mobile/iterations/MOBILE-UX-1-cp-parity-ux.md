# MOBILE-UX-1 — Mobile UX Parity + CP Wiring Iteration Plan

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | MOBILE-UX-1 |
| Feature area | Mobile App UX + CP Frontend Wiring — Make the product worth paying for |
| Created | 2026-03-10 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/mobile/iterations/MOBILE-UX-1-cp-parity-assessment.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 4 |
| Total stories | 10 |

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

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list based on the tech stack that iteration uses
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
- [x] Iteration count minimized for PR-only delivery (default 1-2)
- [x] Related backend/frontend work kept in the same iteration unless merge-to-main is a hard dependency
- [x] No placeholders remain

---

## Vision Intake

### What service/area?
CP FrontEnd + Mobile app (cross-cutting UX fix)

### What user outcome?
After this plan: (1) CP Deliverables page shows REAL agent output from the API instead of placeholder healthcare examples, (2) CP Command Centre dashboard shows live agent status instead of hardcoded "Today's Flight Plan", (3) DMA Wizard stops asking fields already in customer profile, (4) Mobile app has professional vector icons + functional search/filter + a Deliverables screen. The customer can now SEE their agent working and decide to pay.

### What is OUT of scope?
- New backend endpoints (all APIs already exist — this is pure Lane A wiring)
- DMA Wizard step restructuring (only deduplicating fields and showing draft before blind approval)
- Mobile payment integration (Razorpay)
- Mobile push notifications
- New agent types or industries

### Lane?
Lane A — wire existing APIs. No new backend endpoints required.

### Timeline constraint?
2 iterations. Each iteration ≤ 6 stories, ≤ 6 hours agent work.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | CP FrontEnd: Wire Deliverables + Command Centre to real APIs, deduplicate DMA wizard fields | 2 | 5 | 5h | +6h from launch |
| 2 | Mobile: Vector icons, functional search/filter, Deliverables screen | 2 | 5 | 5h | +6h from launch |

**Estimate basis:** FE wiring = 30 min | Data-fetching component = 45 min | Complex refactor = 90 min | Docker test = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

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
7. Go away. Come back at: **+6h from launch**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React/TypeScript/Fluent UI engineer + Senior FastAPI/Python engineer (thin proxy patterns only)
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOBILE-UX-1-cp-parity-ux.md
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

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Verify merge first:**
```bash
git fetch origin && git log --oneline origin/main | head -3
# Must show: feat(mobile-ux-1): iteration 1 — CP wiring
```

**Steps to launch:** same as Iteration 1 (VS Code → Copilot Chat → Agent mode → platform-engineer)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOBILE-UX-1-cp-parity-ux.md
YOUR SCOPE: Iteration 2 only — Epics E3, E4. Do not touch Iteration 1.
TIME BUDGET: 5h.

PREREQUISITE CHECK (do before anything else):
  Run: git log --oneline origin/main | head -5
  Must show: feat(mobile-ux-1): iteration 1 — CP wiring
  If not: post "Blocked: Iteration 1 not merged to main." and HALT.

EXECUTION ORDER:
1. git checkout main && git pull
2. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
3. Respect backend-before-frontend ordering in the Dependency Map.
4. When all epics are docker-tested, open the iteration PR. Post URL. HALT.
```

**Come back at:** +6h from launch

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `src/CP/FrontEnd/` | Senior React / TypeScript / Fluent UI engineer |
| `src/CP/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy engineer |
| `src/mobile/` | Senior React Native / Expo / TypeScript engineer |

### Rule 0 — Open tracking draft PR first (before writing any code)

```bash
git checkout main && git pull
git checkout -b feat/mobile-ux-1-it1-e1

git commit --allow-empty -m "chore(mobile-ux-1): start iteration 1"
git push origin feat/mobile-ux-1-it1-e1

gh pr create \
  --base main \
  --head feat/mobile-ux-1-it1-e1 \
  --draft \
  --title "tracking: MOBILE-UX-1 Iteration 1 — in progress" \
  --body "## tracking: MOBILE-UX-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Wire Deliverables page to listHiredAgentDeliverables API
- [ ] [E1-S2] Add deliverable review actions (approve/reject)
- [ ] [E1-S3] Wire Command Centre to live agent summary data
- [ ] [E2-S1] Deduplicate DMA Wizard fields — pull from customer profile
- [ ] [E2-S2] Show draft preview before strategy approval gate

_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline
One epic = one branch: `feat/mobile-ux-1-itN-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside your scope: add a TODO comment and move on.

**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table.

**Missing iteration HALT rule**: Before writing any code, verify your assigned iteration section exists:
```bash
grep -n "## Iteration N" docs/mobile/iterations/MOBILE-UX-1-cp-parity-ux.md
```
If the section is missing, do not create story cards. HALT.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.
Run the test command listed in the story card — not a generic command.

### Rule 4 — Commit + push + notify after every story
```bash
git add -A
git commit -m "feat(mobile-ux-1): [story title]"
git push origin feat/mobile-ux-1-itN-eN

git add docs/mobile/iterations/MOBILE-UX-1-cp-parity-ux.md
git commit -m "docs(mobile-ux-1): mark [story-id] done"
git push origin feat/mobile-ux-1-itN-eN

gh pr comment \
  $(gh pr list --head feat/mobile-ux-1-it1-e1 --json number -q '.[0].number') \
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
Exit 0 → add `**Epic complete ✅**` under the epic heading, commit, push.
Non-zero → fix on same branch, retry. Max 3 attempts. Then: STUCK PROTOCOL.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
```bash
git add -A && git commit -m "WIP: [story-id] blocked — [exact error]"
git push origin feat/mobile-ux-1-itN-eN
gh pr create \
  --base main \
  --head feat/mobile-ux-1-itN-eN \
  --title "WIP: [story-id] — blocked" \
  --draft \
  --body "Blocked on: [test name]
Error: [exact error message]
Attempted fixes:
1. [what I tried]
2. [what I tried]"
```
Post the draft PR URL. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
```bash
git checkout main && git pull
git checkout -b feat/mobile-ux-1-itN
git merge --no-ff feat/mobile-ux-1-itN-e1 feat/mobile-ux-1-itN-e2
git push origin feat/mobile-ux-1-itN

gh pr create \
  --base main \
  --head feat/mobile-ux-1-itN \
  --title "feat(mobile-ux-1): iteration N — [summary]" \
  --body "## MOBILE-UX-1 Iteration N

### Stories completed
[paste tracking table rows]

### NFR checklist
- [ ] FE: loading + error + empty states on all data-fetching components
- [ ] No env-specific values in code
- [ ] Tests pass"
```
Post PR URL. **HALT — do not start the next iteration.**

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(mobile-ux-1): [epic-id] — [epic title]" && git push
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 7 | Loading + error + empty states on every FE data-fetching component | Silent failures |
| 11 | PR always `--base main` — never target an intermediate branch | Work never ships |
| 13 | CP BackEnd is a thin proxy only — no business logic | Architecture violation |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer sees real deliverables | Wire Deliverables page to listHiredAgentDeliverables API | 🔴 Not Started | — |
| E1-S2 | 1 | Customer sees real deliverables | Add deliverable review actions (approve/reject) | 🔴 Not Started | — |
| E1-S3 | 1 | Customer sees real deliverables | Wire Command Centre to live agent summary data | 🔴 Not Started | — |
| E2-S1 | 1 | DMA Wizard stops wasting time | Deduplicate DMA Wizard fields — pull from customer profile | 🔴 Not Started | — |
| E2-S2 | 1 | DMA Wizard stops wasting time | Show draft preview before strategy approval gate | 🔴 Not Started | — |
| E3-S1 | 2 | Mobile feels professional | Replace emoji tab icons with vector icons | 🔴 Not Started | — |
| E3-S2 | 2 | Mobile feels professional | Wire SearchResults + FilterAgents to API | 🔴 Not Started | — |
| E3-S3 | 2 | Mobile feels professional | Add tab badge counts for pending actions | 🔴 Not Started | — |
| E4-S1 | 2 | Mobile shows agent output | Create mobile Deliverables screen | 🔴 Not Started | — |
| E4-S2 | 2 | Mobile shows agent output | Wire SubscriptionManagement to real billing data | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

<!-- ITERATION 1 STORY CARDS WILL BE ADDED IN NEXT COMMIT -->

<!-- ITERATION 2 STORY CARDS WILL BE ADDED IN NEXT COMMIT -->
