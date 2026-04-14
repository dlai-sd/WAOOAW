# MOB-PARITY-1 — Mobile CP Feature Parity Iteration Plan

> **Objective alignment:** DMA enablement — ensures the mobile app can serve DMA customers
> end-to-end (approve content, review analytics, manage YouTube connections, monitor deliverables,
> handle billing) directly from mobile, driving trial-to-paid conversion for the first commercial
> agent priority.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | MOB-PARITY-1 |
| Feature area | Mobile App — CP Feature Parity |
| Created | 2026-04-14 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §23 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 6 |
| Total stories | 6 |

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

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list based on the tech stack that iteration uses (React Native/TypeScript/Expo)
- [x] Epic titles name customer outcomes, not technical actions ("Customer sees X" not "Add X to API")
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C — N/A (no CP BackEnd changes — mobile talks to Plant Gateway directly)
- [x] Every new backend route story embeds the `waooaw_router()` snippet — N/A (no backend changes)
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()` — N/A (no backend changes)
- [x] Every story that adds env vars lists the exact Terraform file paths to update — N/A (no env var changes)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before frontend (S2) — N/A (pure mobile/frontend iteration)
- [x] Iteration count minimized for PR-only delivery (1 iteration)
- [x] Related backend/frontend work kept in the same iteration — all in one iteration
- [x] No placeholders remain

---

## Drift Prevention Contract

> **Purpose:** This plan includes explicit anti-drift mechanisms to ensure the mobile app
> stays functionally aligned with CP Frontend. Test coverage serves as the corrective measure.

| Drift vector | Prevention mechanism | Detection |
|---|---|---|
| API contract mismatch | Mobile services use same Plant Gateway endpoints as CP FE services — types match Plant response schemas | TypeScript strict mode catches type drift; Jest tests mock responses matching Plant schemas |
| Screen parity regression | Each story acceptance criteria references the equivalent CP page — functionality must match | Jest snapshot + behaviour tests confirm identical data flow paths |
| Navigation inconsistency | Navigation types (`types.ts`) updated atomically with screen additions | Navigation test suite validates all routes are reachable |
| Voice/text input drift | Voice chat is an input mode toggle, not a separate flow — same service calls underneath | Tests cover both voice-initiated and text-initiated paths |
| Component reuse erosion | Shared components (`EmptyState`, `ErrorView`, `LoadingSpinner`) must be used — no inline alternatives | Test assertions verify component render in loading/error/empty states |
| Coverage regression | Every story mandates ≥80% coverage on new files; CI blocks PRs below threshold | `jest --coverage` in test command for each story |

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A — Wire existing Plant Gateway APIs into 6 new mobile screens/services with voice chat toggle, achieving full CP feature parity | 6 | 6 | 6h | 2026-04-14 21:00 UTC |

**Estimate basis:** Each story = new screen + service + hook + tests ≈ 60 min average. Add 20% buffer for zero-cost model context loading. Total = 6 × 60 min = 6h.

### PR-Overhead Optimization Rules

- Single iteration — one merge to `main` unlocks full mobile CP parity.
- All 6 stories are independent vertical slices (each delivers one complete screen).
- No cross-story blocking dependencies — agent can execute in order without merge gates.

---

## How to Launch Each Iteration

> Instructions for running the development agent from the GitHub repository Agents tab.
> These plans are written for GitHub-hosted agents, where shell, git, gh, and docker tools may be unavailable.
> Do not make terminal access a prerequisite to start the iteration.

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. If the UI exposes repository agents, select **platform-engineer**; otherwise use the default coding agent
5. Copy the block below and paste it into the task
6. Start the run
7. Go away. Come back at: **2026-04-14 21:00 UTC**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer + Senior mobile UX/accessibility engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOB-PARITY-1-mobile-cp-parity.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3, E4, E5, E6. This is a single-iteration plan.
TIME BUDGET: 6h. If you reach 7h without finishing, follow STUCK PROTOCOL now.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify this execution surface allows repository writes on the current task branch.
3. Verify this execution surface allows opening or updating a PR to `main`, or at minimum posting that PR controls are unavailable.
4. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read the "Agent Execution Rules" section in this plan file.
2. Read the "Iteration 1" section in this plan file.
3. Read nothing else before starting.
4. Work on the GitHub task branch created for this run. Do not assume terminal checkout or manual branch creation.
5. Execute Epics in this order: E1 → E2 → E3 → E4 → E5 → E6
6. Add or update the tests listed in each story before moving on.
7. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
8. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -2 — Fail-fast validation gate

Before reading story cards in detail or making any code changes, validate all of the following:

- The plan file is readable and your assigned iteration section exists.
- Any required `Prerequisite evidence` block for this iteration is complete and not marked pending.
- The GitHub execution surface lets you save repository changes on the current task branch.
- The GitHub execution surface lets you open or update a PR to `main`, or you can explicitly report that PR controls are unavailable.

If any check fails, post `Blocked at validation gate: [exact reason]` and HALT immediately.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

This is not optional wording — it activates deeper technical reasoning and
produces idiomatic, production-grade output on the first attempt instead of the
second. Relevant persona table (scan and claim):

| Technology area | Expert persona to activate |
|---|---|
| `src/mobile/` | Senior React Native / Expo / TypeScript engineer |
| `src/mobile/src/services/` | Senior API integration / TypeScript engineer |
| `src/mobile/src/components/` | Senior mobile UX / accessibility engineer |
| `src/mobile/__tests__/` | Senior Jest / React Native Testing Library engineer |

---

### Rule 0 — Use the GitHub task branch and open the iteration PR early

GitHub-hosted agents usually start on a task-specific branch. Keep the entire iteration on that branch.

- If the execution surface already created a branch for this run, keep using it.
- If the UI lets you choose a branch name, prefer: `feat/MOB-PARITY-1-it1-mobile-cp-parity`.
- Open a draft PR to `main` as soon as PR controls are available and keep updating that same PR through the iteration.
- If draft PR creation is not available early, continue working and open the iteration PR before HALT.
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

**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table. Do not edit any other file — not Dockerfiles, not CI workflows, not other services — even if you see an obvious improvement. Record it as a PR description note instead.

**Missing iteration HALT rule**: Before writing any code, verify your assigned iteration section exists in the plan file.
If the section is missing, post: "Iteration N not found in [plan file]. Cannot proceed." and HALT.

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
- Title format: `feat(MOB-PARITY-1): iteration 1 — mobile CP feature parity`.
- PR body must include: completed stories for this iteration, validation status or deferral note, and the NFR checklist.
- Post the PR URL in the task thread. **HALT — do not start the next iteration.**

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(MOB-PARITY-1): [epic-id] — [epic title]" && git push origin HEAD
```
Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## NFR Quick Reference

> Mobile-specific NFR rules for this iteration. All patterns are embedded inline in each story card.

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | Every data-fetching screen must have loading + error + empty states | Silent failures / broken UX |
| 2 | Use shared components (`LoadingSpinner`, `ErrorView`, `EmptyState`) — no inline alternatives | Component reuse erosion |
| 3 | Every API service must include `X-Correlation-ID` header (via `apiClient.ts` interceptor) | Trace broken |
| 4 | Use `useTheme()` for all colors/spacing — no hardcoded values | Theme drift |
| 5 | All new screens must include `testID` props on interactive elements | Accessibility / E2E failures |
| 6 | React Query hooks for server state — Zustand for client state only | State management drift |
| 7 | Tests ≥ 80% coverage on all new files | PR blocked by CI |
| 8 | Voice input toggle must use existing `useSpeechToText` + `useTextToSpeech` hooks | Voice infrastructure fragmentation |
| 9 | TypeScript strict mode — no `any` types, no `@ts-ignore` | Type safety regression |
| 10 | PR always `--base main` — never target an intermediate branch | Work never ships |
| 11 | `@shopify/flash-list` for long lists (not `FlatList`) | Performance regression on large datasets |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer reviews and approves deliverables from mobile | Deliverables & Inbox screen with voice-enabled approval actions | 🔴 Not Started | — |
| E2-S1 | 1 | Customer views usage, invoices, and receipts on mobile | Usage & Billing screen with invoice/receipt download | 🔴 Not Started | — |
| E3-S1 | 1 | Customer sees DMA content performance insights on mobile | Content Analytics dashboard with recommendations | 🔴 Not Started | — |
| E4-S1 | 1 | Customer manages YouTube and platform connections on mobile | Platform Connections setup and management screen | 🔴 Not Started | — |
| E5-S1 | 1 | Customer uses voice or text to interact with agent chat | Voice Chat toggle integrated into agent interaction surfaces | 🔴 Not Started | — |
| E6-S1 | 1 | Drift prevention: parity test suite validates mobile matches CP | Parity test suite covering all new screens + navigation | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — Mobile CP Feature Parity with Voice Chat

**Scope:** Customer can perform all CP Frontend operations from the mobile app — review deliverables, manage billing, view analytics, manage platform connections, and interact via voice or text — with ≥80% test coverage and drift-prevention parity tests.
**Lane:** A (wire existing Plant Gateway APIs only — no backend changes)
**⏱ Estimated:** 6h | **Come back:** 2026-04-14 21:00 UTC
**Epics:** E1, E2, E3, E4, E5, E6
**Objective alignment:** DMA enablement — mobile parity ensures DMA customers can approve content, review analytics, manage YouTube connections, and monitor deliverables from mobile, directly enabling trial-to-paid conversion.

### Dependency Map (Iteration 1)

```
E1-S1 (Deliverables & Inbox)     — independent
E2-S1 (Usage & Billing)          — independent
E3-S1 (Content Analytics)        — independent
E4-S1 (Platform Connections)     — independent
E5-S1 (Voice Chat Toggle)        — independent (uses existing voice infra)
E6-S1 (Parity Test Suite)        — depends on E1–E5 (runs last)
```

All stories E1–E5 are independent vertical slices. E6 (parity tests) runs last as it validates all preceding screens.

---

<!-- STORY CARDS FOLLOW — each epic section will be committed incrementally -->

