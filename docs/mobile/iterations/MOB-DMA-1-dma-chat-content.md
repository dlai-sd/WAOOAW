# MOB-DMA-1 — Mobile DMA Chat, Content Viewing & YouTube DB Persistence

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `MOB-DMA-1` |
| Feature area | Mobile — Digital Marketing Agent chat, content artifact viewer, YouTube DB credential persistence |
| Created | 2026-04-15 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `.github/copilot-instructions.md` §DMA priority; `docs/CONTEXT_AND_INDEX.md` §1, §3, §13 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 5 |
| Total stories | 9 |

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | All service types and API paths are embedded inline — agent never reads a separate NFR file |
| No planning ability | Stories are atomic — one screen or one service file per story |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.

---

## PM Review Checklist

- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant code patterns inline
- [x] Every story card has max 3 files in "Files to read first"
- [x] CP BackEnd pattern: N/A — this plan is mobile-only (Lane A)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: services (S1) before screens (S2+)
- [x] Iteration count minimized — 2 iterations, each unlocks a meaningful product slice
- [x] No placeholders remain

---

## Objective Alignment

**This plan advances: DMA value.**

A mobile customer can manage the full Digital Marketing Agent lifecycle from their phone: activate the DMA via the strategy workshop chat that already powers CP, view themed content batches with table/image/mp4 artifacts, approve or reject individual posts, and manage the YouTube credential from the database-backed `CustomerPlatformCredential`. This removes mobile as a blocker to DMA trial-to-paid conversion.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A — DMA services + DMAConversationScreen + artifact renderer + voice wiring | E1, E2, E3 | 5 | 5h | +5h from start |
| 2 | Lane A — Staged DMA workflow + YouTube DB persistence + strip placeholder sections + BDD parity tests | E4, E5 | 4 | 4h | +4h after Iteration 1 merged |

**Estimate basis:** Service file = 45 min | New screen = 90 min | Component = 30 min | Navigation wiring = 20 min | Tests = 15 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

---

## How to Launch Each Iteration

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. If the UI exposes repository agents, select **platform-engineer**; otherwise use the default coding agent
5. Copy the block below and paste it into the task
6. Start the run
7. Go away. Come back in **~5 hours**.

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React Native / Expo / TypeScript engineer, I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOB-DMA-1-dma-chat-content.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2 content.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL now.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the Iteration 1 section exists.
2. Verify this execution surface allows repository writes on the current task branch.
3. Verify this execution surface allows opening or updating a PR to `main`, or at minimum posting that PR controls are unavailable.
4. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read the "Agent Execution Rules" section in this plan file.
2. Read the "Iteration 1" section in this plan file.
3. Read nothing else before starting.
4. Work on the GitHub task branch created for this run.
5. Execute Epics in this order: E1 → E2 → E3
6. Add or update the tests listed in each story before moving on.
7. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
8. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Prerequisite evidence:**
- Iteration 1 merge status: `[PENDING HUMAN UPDATE BEFORE LAUNCH]`
- Iteration 1 PR: `[PR URL or #NUMBER]`
- Merge commit on `main`: `[FULL SHA]`
- Merged at: `[UTC TIMESTAMP]`

**Verify merge first:** use the Prerequisite evidence block above as the source of truth. If it is still marked pending or missing a merged PR number and merge commit, do not launch Iteration 2.

**Steps to launch:** same as Iteration 1 (GitHub repository → Agents tab)

**Iteration 2 agent task** (paste verbatim):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React Native / Expo / TypeScript engineer
Activate this persona NOW. Begin each epic with:
  "Acting as a Senior React Native / Expo / TypeScript engineer, I will [what] by [approach]."

PLAN FILE: docs/mobile/iterations/MOB-DMA-1-dma-chat-content.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5. Do not touch Iteration 1 content.
TIME BUDGET: 4h.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

PREREQUISITE CHECK (do before anything else):
  Read the "Prerequisite evidence" block under Iteration 2 in this plan file.
  Treat Iteration 2 as unlaunchable only if that block is still marked pending or does not include both a merged PR reference and a merge commit on `main`.
  If the block is still pending or incomplete: post "Blocked: Iteration 1 merge evidence has not been recorded in the plan." and HALT.

FAIL-FAST VALIDATION GATE:
1. Verify the plan file is readable and the Iteration 2 section exists.
2. Verify the Prerequisite evidence block for Iteration 2 is complete and not pending.
3. Verify this execution surface allows repository writes on the current task branch.
4. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
2. Execute Epics in this order: E4 → E5
3. Add or update the tests listed in each story before moving on.
4. Open or update the iteration PR to `main`, post URL, and HALT.
```

**Come back at:** +4 hours after Iteration 2 launch.

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -2 — Fail-fast validation gate

Before reading story cards in detail or making any code changes, validate all of the following:

- The plan file is readable and your assigned iteration section exists.
- Any required `Prerequisite evidence` block for this iteration is complete and not marked pending.
- The GitHub execution surface lets you save repository changes on the current task branch.

If any check fails, post `Blocked at validation gate: [exact reason]` and HALT immediately.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from your task. Activate each now.
For every epic you execute, open with one line:

> *"Acting as a Senior React Native / Expo / TypeScript engineer, I will [what] by [approach]."*

### Rule 0 — Use the GitHub task branch and open the iteration PR early

GitHub-hosted agents usually start on a task-specific branch. Keep the entire iteration on that branch.

- If the execution surface already created a branch for this run, keep using it.
- Open a draft PR to `main` as soon as PR controls are available.

### Rule 1 — Branch discipline
One iteration = one GitHub task branch and one PR.
Never push or merge directly to `main`.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.

### Rule 4 — Save progress after every story
Update this plan file's Tracking Table. Save code and plan updates to the GitHub task branch.

### Rule 5 — Validate after every epic
If GitHub Agents exposes execution tools, run the relevant test command.
If not, state clearly that validation is deferred to CI and continue.
After validation, add `**Epic complete ✅**` under the epic heading.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
- Mark the blocked story as `🚫 Blocked` in the Tracking Table.
- Open or update a draft PR titled `WIP: [story-id] — blocked`.
- Include the exact blocker, the exact error message, and 1-2 attempted fixes.
- Post the PR URL. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
- Title: `feat(MOB-DMA-1): iteration N — [one-line summary]`.
- PR body: completed stories, validation status, NFR checklist.
- Post the PR URL in the task thread. **HALT.**

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(MOB-DMA-1): [epic-id] — [epic title]" && git push origin HEAD
```
Do this BEFORE starting the next epic.

---

## NFR Quick Reference (mobile-only)

| # | Rule | Applies to |
|---|---|---|
| 1 | Every data-fetching component must render loading → error → empty → data states | All new screens/components |
| 2 | `X-Correlation-ID` header on every outgoing HTTP call | All new service files |
| 3 | No email/phone/name in logs or console.log — use stripped dev logging | All new code |
| 4 | Retry 429/5xx/network-drop with exponential backoff (3×, 1s/2s/4s+jitter) | Service layer |
| 5 | All new navigation routes must be in `MyAgentsStackParamList` in `types.ts` | Navigation |
| 6 | Jest tests ≥ 80% coverage on new service files | Tests |
| 7 | Voice input is an optional toggle — never the only input path | DMAConversationScreen |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | DMA services | Mirror DMA activation service | 🔴 Not Started | — |
| E1-S2 | 1 | DMA services | Mirror marketing review service | 🔴 Not Started | — |
| E2-S1 | 1 | Customer sees DMA chat | DMAConversationScreen + navigation wiring | 🔴 Not Started | — |
| E2-S2 | 1 | Customer sees DMA chat | ArtifactRenderer component (table/image/mp4) | 🔴 Not Started | — |
| E3-S1 | 1 | Voice as alt input | Wire voice toggle into DMAConversationScreen | 🔴 Not Started | — |
| E4-S1 | 2 | Staged DMA workflow | Theme-to-content batch staging in DMAConversationScreen | 🔴 Not Started | — |
| E4-S2 | 2 | Staged DMA workflow | YouTube credential ref passed to createContentBatch | 🔴 Not Started | — |
| E5-S1 | 2 | Clean mobile ops hub | Strip placeholder sections in AgentOperationsScreen | 🔴 Not Started | — |
| E5-S2 | 2 | DMA parity tests | BDD parity test suite | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

