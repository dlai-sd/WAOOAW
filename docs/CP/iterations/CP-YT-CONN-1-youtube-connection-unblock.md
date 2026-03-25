# CP-YT-CONN-1 — CP Web YouTube Connection Unblock Iteration Plan

## Objective

Restore a working one-time YouTube connection flow in CP web so a customer can clear Google sign-in, save a reusable YouTube channel connection against their WAOOAW customer profile, attach it to the hired digital-marketing agent, and reuse it later for scheduled publishing without logging in again.

## Defect List

| Defect ID | Root cause | Impact | Best possible solution/fix |
|---|---|---|---|
| DEF-YT-01 | The Google OAuth app is requesting sensitive YouTube scopes, but the Google-side consent configuration is not ready for the current demo flow. | Customers hit the “Google hasn’t verified this app” warning before WAOOAW can finish YouTube sign-in. | Include an operator-gated Google OAuth setup checklist in this iteration, verify redirect URIs and test-user access, and capture proof before merge. |
| DEF-YT-02 | CP BackEnd YouTube proxy still forwards a prefixed customer identifier while Plant stores and queries YouTube credentials by exact customer identifier. | OAuth start/finalize/list/get/attach can drift from the actual customer record and produce broken saved-connection behavior after sign-in. | Normalize the CP YouTube proxy to the raw WAOOAW customer ID and lock it with route tests. |
| DEF-YT-03 | CP web has the pieces for start/finalize/list/attach, but the hire/setup journey still needs explicit closure around callback completion, saved-channel selection, and attach-to-hire continuity. | A customer can begin the flow but not reliably finish with a reusable, attached YouTube channel that is visibly ready for later publishing. | Harden the wizard callback, saved-channel selection, and attach flow so the chosen channel becomes the durable connection of record. |
| DEF-YT-04 | Runtime validation is split across backend, web UI, and Google-side setup with no single iteration-owned verification path. | Regressions can survive until demo deployment, and the team lacks a clean prove-it path for “connect once, publish later.” | Add explicit regression coverage and rollout evidence for Google setup, CP web flow, and attached YouTube readiness. |

## Story Tracker

| Tracking | Story ID | Epic | Customer outcome | Branch |
|---|---|---|---|---|
| Not started | E1-S1 | Customer reaches a trusted Google sign-in screen | Operator has the exact Google OAuth setup checklist and evidence requirements needed to unblock the warning screen. | feat/cp-yt-conn-1-it1-e1 |
| Not started | E1-S2 | Customer reaches a trusted Google sign-in screen | CP sends the same customer identity contract that Plant uses when saving YouTube connections. | feat/cp-yt-conn-1-it1-e1 |
| Not started | E2-S1 | Customer saves one reusable YouTube connection | Hire setup finalizes Google callback state and keeps the chosen YouTube channel selected in the wizard. | feat/cp-yt-conn-1-it1-e2 |
| Not started | E2-S2 | Customer saves one reusable YouTube connection | Saving the wizard attaches the selected YouTube credential to the hired agent so later publishing can reuse it. | feat/cp-yt-conn-1-it1-e2 |
| Not started | E3-S1 | Customer sees reliable YouTube readiness later | My Agents clearly shows not connected, ready to attach, connected, and reconnect-required states with the right next action. | feat/cp-yt-conn-1-it1-e3 |
| Not started | E3-S2 | Customer sees reliable YouTube readiness later | The team has a prove-it regression path and rollout evidence for connect once, publish later. | feat/cp-yt-conn-1-it1-e3 |

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | CP-YT-CONN-1 |
| Feature area | Customer Portal Web — YouTube connection unblock |
| Created | 2026-03-25 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | Copilot chat requirement dated 2026-03-25 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 3 |
| Total stories | 6 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous zero-cost model agents with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained with exact files and exact acceptance criteria. |
| No working memory across files | Required NFR and proxy/client patterns are embedded inline in each story card. |
| No planning ability | Stories are atomic: one deliverable, one file set, one verification path. |
| Token cost per file read | Each story caps “Files to read first” at 3 files. |
| Binary inference only | Acceptance criteria are pass/fail and customer-visible. |

> Agent: execute exactly one story at a time, update the Story Tracker row when done, push code, then move to the next story in the same epic branch.

---

## PM Review Checklist (tick every box before publishing)

- [ ] EXPERT PERSONAS filled
- [ ] Epic titles name customer outcomes, not technical actions
- [ ] Every story has an exact branch name
- [ ] Every story card embeds relevant NFR code snippets inline
- [ ] Every story card has max 3 files in “Files to read first”
- [ ] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [ ] Every new backend route story embeds the `waooaw_router()` snippet
- [ ] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [ ] Every story that adds env vars lists the exact Terraform file paths to update
- [ ] Every story has `BLOCKED UNTIL` (or `none`)
- [ ] Iteration has a time estimate and come-back datetime
- [ ] Iteration has a complete GitHub agent launch block
- [ ] STUCK PROTOCOL is in Agent Execution Rules section
- [ ] Stories sequenced: backend before frontend where required
- [ ] Iteration count minimized for PR-only delivery
- [ ] Related backend/frontend work kept in the same iteration unless merge-to-main is a hard dependency
- [ ] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Unblock CP web YouTube sign-in, saved credential attach, customer-visible readiness states, and Google-side setup evidence in one merge. | 3 | 6 | 5.5h | 2026-03-25 22:30 IST |

**Estimate basis:** CP proxy fix = 30 min | CP web wizard flow = 60 min | My Agents readiness UX = 45 min | Google operator checklist + evidence = 30 min | E2E/regression = 60 min | PR/test/update overhead = 75 min.

### PR-Overhead Optimization Rules

- This is a single-iteration plan by request.
- Backend and frontend changes stay in one iteration so one merge unlocks a working customer path.
- No separate deployment iteration is added; deployment validation happens after merge through the standard `waooaw deploy` workflow if needed.

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
7. Go away. Come back at: **2026-03-25 22:30 IST**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Fluent UI engineer + Senior Python 3.11 / FastAPI engineer + Google OAuth rollout operator for customer-facing integrations.
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/CP-YT-CONN-1-youtube-connection-unblock.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3.
TIME BUDGET: 5.5h. If you reach 6.5h without finishing, follow STUCK PROTOCOL now.

EXECUTION ORDER:
1. Run: git status && git log --oneline -3
   You must be on main with a clean tree. If not, post why and HALT.
2. Read the "Agent Execution Rules" section in this plan file.
3. Read the "Iteration 1" section in this plan file.
4. Read nothing else before starting.
5. Execute Epics in this order: E1 → E2 → E3
6. Update the Story Tracker row after each story, push the epic branch, and continue.
7. When all epics are tested and the iteration PR is open, post the PR URL. HALT.
```

---

## Agent Execution Rules

### Rule -1 — Activate Expert Personas

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

### Rule 0 — Open tracking draft PR first

```bash
git checkout main && git pull
git checkout -b feat/cp-yt-conn-1-it1-e1
git commit --allow-empty -m "chore(cp-yt-conn-1): start iteration 1"
git push origin feat/cp-yt-conn-1-it1-e1

gh pr create \
  --base main \
  --head feat/cp-yt-conn-1-it1-e1 \
  --draft \
  --title "tracking: CP-YT-CONN-1 Iteration 1 — in progress" \
  --body "## tracking: CP-YT-CONN-1 Iteration 1

Subscribe to this PR to receive one notification per story completion.

### Stories
- [ ] [E1-S1] Google OAuth operator checklist and evidence pack
- [ ] [E1-S2] CP YouTube proxy uses Plant customer ID contract
- [ ] [E2-S1] Hire setup finalizes saved YouTube channel selection
- [ ] [E2-S2] Hire setup attaches saved YouTube credential to the hire
- [ ] [E3-S1] My Agents shows reliable YouTube readiness states
- [ ] [E3-S2] Regression and rollout evidence prove connect once publish later

_Live updates posted as comments below ↓_"
```

### Rule 1 — Branch discipline

One epic = one branch: `feat/cp-yt-conn-1-it1-eN`.
All stories in one epic commit to the same branch sequentially.
Never push to `main` directly.

### Rule 2 — Scope lock

Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code.
Do not refactor outside listed files.

### Rule 3 — Tracker discipline

After each story is complete:
1. Update that Story Tracker row from `Not started` to `Completed` in this plan file.
2. If the next story has started, mark it `In progress`.
3. Commit that tracker update with the story code changes.

### Rule 4 — Test-plan discipline

Each story must either add tests, update existing tests, or explicitly state why no test changed.
If rollout or operator validation is part of the story, update an existing test-plan or testing asset file rather than creating a new document.

### Rule 5 — Google operator gate

Google OAuth consent-screen or test-user changes are outside repo code. For the Google setup story, the agent must:
1. Prepare the exact checklist and evidence requirements in the files named by the story card.
2. Post the manual actions clearly in the PR description or PR comment.
3. Mark the story complete only after the repo-side checklist and captured validation evidence are present.

### Rule 6 — STUCK PROTOCOL

If blocked for more than 20 minutes on one story:
1. Post the blocker in the tracking PR.
2. Commit any safe partial progress.
3. Stop only if the blocker is external and cannot be reduced further.

### CHECKPOINT RULE

After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(cp-yt-conn-1): [epic-id] — [epic title]" && git push
```

Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## Iteration 1

Story cards follow in the next section.