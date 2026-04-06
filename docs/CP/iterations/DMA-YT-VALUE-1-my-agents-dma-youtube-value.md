# DMA-YT-VALUE-1 — My Agents DMA + YouTube Customer Value Plan

**Objective**
This plan exists to make My Agents feel like directing a capable marketing hire, not filling a software wizard.
The customer should pick the DMA hire immediately, give only the minimum necessary inputs through a consultative chat flow, and stay in control of YouTube connection and posting.
The first release must deepen YouTube-first DMA value before any channel breadth work resumes.
Every story must either reduce customer effort, increase customer trust, or shorten time-to-first-useful-content on My Agents.
If a story does not move one of those customer outcomes, cut it.

> **Template version**: 2.0 adapted to the live branch state on 2026-04-06.
> **Branch note**: `docs/CP/iterations/NFRReusable.md` is absent on this branch, so all inline NFR patterns below are copied from the active branch truth: `docs/CONTEXT_AND_INDEX.md` §5.6 plus live `core/` implementations.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `DMA-YT-VALUE-1` |
| Feature area | Customer Portal — My Agents DMA + YouTube operating experience |
| Created | 2026-04-06 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 2 |
| Total epics | 5 |
| Total stories | 8 |

---

## Vision Intake

- Area: CP FrontEnd on My Agents is the primary surface; Plant BackEnd changes are allowed only where richer YouTube evidence is required; CP BackEnd remains thin-proxy only.
- Outcome: A paying customer can select the DMA hire at the top of My Agents, move through a consultative chat-like YouTube setup and content flow, and reconnect or verify YouTube whenever needed without hunting through form-heavy steps.
- Out of scope: Hire Setup redesign, multi-channel expansion beyond YouTube, billing changes, infra changes, and autonomous no-approval posting.
- Lane: Iteration 1 is Lane A using existing APIs. Iteration 2 is Lane B only where Plant must expose richer YouTube proof data before the FE can deliver the final customer-confidence surface.
- Urgency: High priority. Keep this to 2 iterations maximum.
- Objective alignment: DMA value first. This removes the current customer-friction blocker that makes the YouTube-first DMA path feel like internal tooling instead of a premium managed-agent experience.

---

## Value-First Gap Ranking

| Rank | Gap | Customer impact | Why this must be closed now |
|---|---|---|---|
| 1 | My Agents starts in the wrong place and makes the customer step through selection and setup mechanics before value | Very high | A paying customer should land in control of the hired DMA immediately, not burn attention on wizard plumbing |
| 2 | The current DMA flow still behaves like a multi-step form instead of a consultative marketing assistant | Very high | Customers pay for guidance and execution confidence, not for typing into 3-4 early-step forms |
| 3 | YouTube connection and posting confidence are too weak: state is fragmented, reconnect is not first-class, and proof of what the agent will touch is limited | High | If customers do not trust channel state and content proof, they will not let DMA create or post useful YouTube work |

---

## Target State Definition

On My Agents, the customer sees the hired DMA selector at the top of the page and immediately enters a guided operating space for that hire. The operating space behaves like a consultative chat: the assistant asks only the next highest-value question, summarizes what it learned, proposes the next move, and progressively reveals structured inputs only when needed. YouTube connection management is always available in-context, with clear connect, reconnect, retest, and confirm actions plus fetched channel proof. The approval and publish area shows exactly what will happen next, why the agent is or is not ready, and what the customer must do to proceed.

### Target-state acceptance criteria

1. On My Agents, DMA hire selection is visible at the top of the page and the DMA activation experience no longer starts with an in-wizard “Select Agent” step.
2. The first customer interaction after selecting a DMA hire is consultative guidance, not a dense list of mandatory input fields.
3. The customer can connect, reconnect, retest, and persist YouTube from My Agents at any time without leaving the DMA operating surface.
4. After a YouTube validation call succeeds, the UI shows fetched channel identity and concrete proof data that helps the customer trust the connection.
5. The approval and readiness area tells the customer exactly what is blocking YouTube content creation or posting, and the next action is obvious.
6. Explicit customer approval remains required before external YouTube publish actions.

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous zero-cost model agents with limited context windows. Every story is self-contained and bounded to a small number of files.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is self-contained with no external references required mid-story |
| No working memory across files | NFR snippets are embedded inline from the live branch source |
| No planning ability | Stories are atomic and outcome-based |
| Token cost per file read | Max 3 files to read first per story |
| Binary inference only | Acceptance criteria are observable and pass/fail |

> **Agent:** Execute exactly one story at a time. Read only the assigned story card and the files listed there first.

---

## PM Review Checklist (tick every box before publishing)

- [x] **EXPERT PERSONAS filled** — each iteration task block has the correct expert persona list
- [x] Epic titles name customer outcomes, not technical actions
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no external NFR reference required
- [x] Every story card has max 3 files in “Files to read first”
- [x] Every story involving CP BackEnd states the exact pattern: A, B, C, or N/A
- [x] Every new backend route story embeds the `waooaw_router()` snippet
- [x] Every GET route story card says `get_read_db_session()` when a new GET route is introduced
- [x] Every story that adds env vars lists the exact Terraform file paths to update or explicitly says no env changes
- [x] Every story has `BLOCKED UNTIL` (or `none`)
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced backend before frontend where a backend dependency exists
- [x] Iteration count minimized for PR-only delivery
- [x] Related backend/frontend work kept in the same iteration unless merge-to-main is a hard dependency
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane A — make My Agents the right DMA entrypoint and replace form-heavy setup with a consultative YouTube-first operating flow using existing APIs | 3 | 6 | 5.5h | 2026-04-07 13:00 UTC |
| 2 | Lane B — add richer YouTube proof data and finish the customer-confidence surfaces that depend on it | 2 | 2 | 3.0h | 2026-04-08 13:00 UTC |

**Estimate basis:** FE wiring = 30 min | New BE endpoint = 45 min | Full-stack = 90 min | PR = 10 min. Add 20% buffer for zero-cost model context loading.

### PR-Overhead Optimization Rules

- Default to 2 iterations maximum.
- Size each iteration so one merge unlocks a meaningful product slice.
- Prefer vertical slices within the same iteration over extra merge gates.
- Deployment is assumed through the `waooaw deploy` workflow after the final merged iteration.

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
7. Go away. Come back at: **2026-04-07 13:00 UTC**

**Iteration 1 agent task** (paste verbatim — do not modify):

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React 18 / TypeScript / Vite engineer + Senior product-minded customer-portal UX engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-YT-VALUE-1-my-agents-dma-youtube-value.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2 content.
TIME BUDGET: 5.5h. If you reach 6.5h without finishing, follow STUCK PROTOCOL now.

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
5. Execute Epics in this order: E1 → E2 → E3
6. Add or update the tests listed in each story before moving on.
7. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
8. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` then an agent got stuck. Read the PR comment for the exact blocker.

---

### Iteration 2

> ⚠️ Do NOT launch until Iteration 1 PR is merged to `main`.

**Prerequisite evidence:**
- Iteration 1 merge status: `PENDING HUMAN UPDATE BEFORE LAUNCH`
- Iteration 1 PR: `TBD after Iteration 1 PR is opened`
- Merge commit on `main`: `TBD after Iteration 1 merge`
- Merged at: `TBD after Iteration 1 merge`

**Verify merge first:** use the prerequisite evidence block above as the source of truth. If it is still marked pending or missing a merged PR number and merge commit, do not launch Iteration 2.

**Steps to launch:** same as Iteration 1 (GitHub repository → Agents tab)

**Iteration 2 agent task** (paste verbatim):

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior React 18 / TypeScript / Vite engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-YT-VALUE-1-my-agents-dma-youtube-value.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5. Do not touch other iteration content.
TIME BUDGET: 3.0h.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

PREREQUISITE CHECK (do before anything else):
  Read the "Prerequisite evidence" block under Iteration 2 in this plan file.
  Treat Iteration 2 as unlaunchable only if that block is still marked pending or does not include both a merged PR reference and a merge commit on `main`.
  If the block is still pending or incomplete: post "Blocked: Iteration 1 merge evidence has not been recorded in the plan." and HALT.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify the Prerequisite evidence block for Iteration 2 is complete and not pending.
3. Verify this execution surface allows repository writes on the current task branch.
4. Verify this execution surface allows opening or updating a PR to `main`, or at minimum posting that PR controls are unavailable.
5. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read "Agent Execution Rules" and "Iteration 2" sections. Read nothing else.
2. Work on the GitHub task branch created for this run. Do not assume terminal checkout or manual branch creation.
3. Respect backend-before-frontend ordering in the Dependency Map.
4. Add or update the tests listed in each story before moving on.
5. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
6. Open or update the iteration PR to `main`, post URL, and HALT.
```

**Come back at:** 2026-04-08 13:00 UTC

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

| Technology area | Expert persona to activate |
|---|---|
| `src/CP/BackEnd/` `src/Plant/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy engineer |
| `src/CP/FrontEnd/` | Senior React / TypeScript / Vite engineer |
| `cloud/` scripts, `gcloud` | GCP Cloud Logging / IAM expert |

### Rule 0 — Use the GitHub task branch and open the iteration PR early

GitHub-hosted agents usually start on a task-specific branch. Keep the entire iteration on that branch.

- If the execution surface already created a branch for this run, keep using it.
- If the UI lets you choose a branch name, prefer: `feat/dma-yt-value-1-itN-short-scope-runid`.
- Open a draft PR to `main` as soon as PR controls are available and keep updating that same PR through the iteration.
- If draft PR creation is not available early, continue working and open the iteration PR before HALT.
- Use the Tracking Table in this plan as the source of truth for story status updates.

### Rule 1 — Branch discipline

One iteration = one GitHub task branch and one PR.
Treat every `Branch:` value in story cards as a logical label only; on the GitHub Agents tab, keep the full iteration on the single branch created for the run.
Never push or merge directly to `main`.

### Rule 2 — Scope lock

Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.
If you notice a bug outside scope, add a TODO comment and move on.

**File scope**: Only create or modify files listed in your story card’s “Files to create / modify” table.

### Rule 3 — Tests before the next story

Write every test in the story’s test table before advancing to the next story.
If this execution surface exposes test execution, run the story’s listed command or the narrowest equivalent.
If not, add the tests anyway and note that execution is deferred to CI or local follow-up.

### Rule 4 — Save progress after every story

- Update this plan file’s Tracking Table: change the story status to Done or Blocked.
- Save code and plan updates to the GitHub task branch for this run.
- If the PR already exists, add a concise progress update in the PR description or comments with files changed, tests added or run, and the next story.

### Rule 5 — Validate after every epic

- Prefer the narrowest relevant automated validation for the files you changed.
- If GitHub Agents exposes execution tools, run the relevant test command and record the result.
- If execution tools are unavailable, state clearly that validation is deferred to CI or local follow-up and continue.
- After validation, add `**Epic complete ✅**` under the epic heading if the epic is complete.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)

- Mark the blocked story as `🚫 Blocked` in the Tracking Table.
- Open or update a draft PR titled `WIP: dma-yt-value-blocked-story — blocked` if PR controls are available.
- Include the exact blocker, the exact error message, and 1-2 attempted fixes.
- Post the PR URL if available. Otherwise post the blocker in the GitHub agent thread. **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)

- Use the same GitHub task branch for the final iteration PR to `main`.
- Title format: `feat(DMA-YT-VALUE-1): iteration N — one-line summary`.
- PR body must include: completed stories for this iteration, validation status or deferral note, and the NFR checklist.
- Post the PR URL in the task thread. **HALT — do not start the next iteration.**

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:

```bash
git add -A && git commit -m "feat(DMA-YT-VALUE-1): E1 — epic title" && git push origin HEAD
```

Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | `waooaw_router()` factory — never bare `APIRouter` | CI ruff ban — PR blocked |
| 2 | `get_read_db_session()` on all GET routes | Primary DB overloaded |
| 3 | `PIIMaskingFilter()` on every logger | PII incident |
| 4 | `@circuit_breaker(service=...)` on every external HTTP call | Cascading failure |
| 5 | Loading + error + empty states on every FE data-fetching component | Silent failures |
| 6 | Never embed env-specific values in Dockerfile or code | Image cannot be promoted |
| 7 | CP BackEnd is a thin proxy only — no business logic | Architecture violation |
| 8 | Pattern A: call existing `/cp/*` via `gatewayRequestJson` | No new CP BackEnd file |
| 9 | Pattern B: missing `/cp/*` route → thin proxy in `api/cp_<resource>.py` | CP stays proxy-only |
| 10 | Pattern C: existing Plant `/v1/*` route is already exposed through existing CP proxy or direct FE call path | No duplicate proxy route |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | Customer starts from the right DMA hire | Move DMA agent selection to the top of My Agents | 🔴 Not Started | — |
| E1-S2 | 1 | Customer starts from the right DMA hire | Remove in-wizard agent selection and collapse the stage model | 🔴 Not Started | — |
| E2-S1 | 1 | Customer gets consultative guidance instead of a form dump | Turn the strategy workshop into the primary chat-style input surface | 🔴 Not Started | — |
| E2-S2 | 1 | Customer gets consultative guidance instead of a form dump | Reveal structured inputs only when the chat flow actually needs them | 🔴 Not Started | — |
| E3-S1 | 1 | Customer can manage YouTube without leaving the operating surface | Upgrade channel control to always-available connect or reconnect or retest actions | 🔴 Not Started | — |
| E3-S2 | 1 | Customer can manage YouTube without leaving the operating surface | Unify approval and publish-readiness into one operating rail | 🔴 Not Started | — |
| E4-S1 | 2 | Customer sees proof of the real YouTube channel before trusting the agent | Enrich Plant YouTube validation with recent upload proof and next-action hints | 🟢 Done | copilot/iteration-2-epics-e4-e5 |
| E4-S2 | 2 | Customer sees proof of the real YouTube channel before trusting the agent | Render recent upload proof and reconnect guidance in My Agents | 🟢 Done | copilot/iteration-2-epics-e4-e5 |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — My Agents becomes the right DMA operating entrypoint

**Scope:** The customer lands on My Agents, picks the DMA hire immediately, moves through a consultative YouTube-first flow, and can manage channel state and approval without feeling trapped in a long wizard.
**Lane:** A — wire existing APIs only
**⏱ Estimated:** 5.5h | **Come back:** 2026-04-07 13:00 UTC
**Epics:** E1, E2, E3

### Dependency Map (Iteration 1)

```text
E1-S1 ──► E1-S2
E2-S1 ──► E2-S2
E3-S1 ──► E3-S2
```

---

### Epic E1: Customer starts from the right DMA hire

**Branch:** `feat/dma-yt-value-1-it1-e1`
**Objective alignment:** DMA value
**User story:** As a paying customer, I can pick the DMA hire at the top of My Agents and immediately work on that hire, so that setup starts from the hired relationship instead of from wizard mechanics.

#### Story E1-S1: Move DMA agent selection to the top of My Agents

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**Branch:** `feat/dma-yt-value-1-it1-e1`
**CP BackEnd pattern:** A — existing data comes from current FE service calls; no new CP BackEnd file

**What to do (self-contained — read this card, then act):**
> `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` lines 2268–2317 currently render the all-DMA path as a full-width card that drops the user directly into `DigitalMarketingActivationWizard`, while the non-DMA path keeps agent selection above the content area. Change the all-DMA path so it uses the same top-of-page agent-selection shell pattern, keeps the selected hire visible above the activation area, and makes the active DMA hire obvious before any wizard content appears. Preserve the existing selected-subscription state and keep the page on My Agents.

**Files to read first (max 3 — read only these, nothing else):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 2268–2495 | Current all-DMA branch, selector layout in non-DMA branch, selected subscription state |
| `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | 240–360 | Existing My Agents page assertions and selector behavior |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | 430–560 | Current wizard assumptions about selected instance changes |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Replace the all-DMA direct-card entry with a top-of-page selector shell that keeps the selected DMA hire above the activation content. Keep `onSelectedInstanceChange` wiring and read-only handling intact. |
| `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | modify | Add assertions that the DMA version of My Agents shows agent selection at the top and keeps the activation area below it. |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Remove any expectation that selection must begin inside the wizard when `selectedInstance` is already controlled by My Agents. |

**Code patterns to copy exactly** (no other file reads needed for these):

```typescript
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)

useEffect(() => {
  getMyAgentsSummary()
    .then((response) => setInstances(response.instances || []))
    .catch(() => setError('Failed to load your agents. Please try again.'))
    .finally(() => setLoading(false))
}, [])

if (loading) return <PageSkeleton variant="cards" />
if (error) return <FeedbackMessage intent="error" message={error} />
```

**Acceptance criteria (binary pass/fail only):**
1. On My Agents, DMA hire selection is visible above the activation experience instead of being hidden inside the wizard.
2. Switching the selected DMA hire updates the activation experience without leaving My Agents.
3. Existing read-only and stale-selection recovery behavior still works.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | Render My Agents with 2 DMA hires | Agent selector appears above activation content |
| E1-S1-T2 | same | Change selected DMA hire | Activation area updates to the new hire |
| E1-S1-T3 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Render wizard with controlled selected instance | No in-wizard select step is required to begin |

**Test command:**

```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgents.test.tsx src/test/MyAgentsDigitalMarketingWizard.test.tsx
```

**Commit message:** `feat(DMA-YT-VALUE-1): move DMA selection to My Agents header`

**Done signal (post as a comment then continue to E1-S2):**
`E1-S1 done. Changed: MyAgents.tsx, MyAgents.test.tsx, MyAgentsDigitalMarketingWizard.test.tsx. Tests: T1 ✅ T2 ✅ T3 ✅`

---

#### Story E1-S2: Remove in-wizard agent selection and collapse the stage model

**BLOCKED UNTIL:** E1-S1 committed to `feat/dma-yt-value-1-it1-e1`
**Estimated time:** 45 min
**Branch:** `feat/dma-yt-value-1-it1-e1`
**CP BackEnd pattern:** A — FE only, uses existing services

**What to do:**
> `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` lines 46–79 still define a seven-stage model that starts with `select` and pushes the customer through early-step setup mechanics. Remove the `select` stage, collapse the stage rail into a smaller set of outcome-led stages, and make the first visible stage about channel readiness and guidance instead of agent selection. Update tests so the wizard starts from the first productive stage whenever My Agents already controls the selected hire.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 46–120 | `DMA_STEPS`, supported platform rules, initial step behavior |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | 430–700 | Step-panel tests that currently expect `select` |
| `src/CP/FrontEnd/src/styles/globals.css` | 2018–2220 | Existing My Agents activation stage styles |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Remove the in-wizard selection stage and rename the remaining stages around customer outcomes, not internal mechanics. |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Update stage expectations so the wizard begins at the first productive panel when `selectedInstance` exists. |
| `src/CP/FrontEnd/src/styles/globals.css` | modify | Adjust stage-rail styling only as needed for the reduced set of stages. |

**Code patterns to copy exactly:**

```typescript
const DMA_STEPS = [
  { id: 'connect', title: 'Channel Ready', description: 'Connect or confirm the YouTube channel.' },
  { id: 'theme', title: 'Brief Chat', description: 'Guide the customer to a usable YouTube direction.' },
  { id: 'schedule', title: 'Plan', description: 'Confirm posting rhythm only after the brief is coherent.' },
  { id: 'activate', title: 'Review & Activate', description: 'Show exactly what is ready and what is blocked.' },
] as const
```

**Acceptance criteria:**
1. The wizard no longer shows a `Select Agent` stage when My Agents already controls the selected hire.
2. The first visible stage is productive for the customer and tied to YouTube readiness or consultative guidance.
3. Stage labels read like customer outcomes, not internal setup tasks.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Render with selected DMA hire | No `dma-step-panel-select` appears |
| E1-S2-T2 | same | Render with selected DMA hire | First visible panel is the new first productive panel |
| E1-S2-T3 | same | Navigate across the reduced stage model | Back and Continue still behave correctly |

**Test command:**

```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx
```

**Commit message:** `feat(DMA-YT-VALUE-1): remove DMA in-wizard selection step`

**Done signal:** `E1-S2 done. Tests: T1 ✅ T2 ✅ T3 ✅`

---

### Epic E2: Customer gets consultative guidance instead of a form dump

**Branch:** `feat/dma-yt-value-1-it1-e2`
**Objective alignment:** DMA value
**User story:** As a paying customer, I can describe my business in a consultative chat flow and get guided toward a usable YouTube direction, so that I do not have to fill multiple early-step forms before seeing value.

#### Story E2-S1: Turn the strategy workshop into the primary chat-style input surface

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/dma-yt-value-1-it1-e2`
**CP BackEnd pattern:** A — FE uses existing `generate-theme-plan` and activation workspace APIs

**What to do:**
> `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` already carries `strategy_workshop`, `assistant_message`, `current_focus_question`, and `next_step_options` payloads from Plant, but the overall experience still behaves like a wizard with many conventional fields. Reframe the main DMA brief experience so the default path is a chat-like consultative composer that displays the assistant guidance, suggested next answers, and concise locked-summary checkpoints before revealing structured fields. Keep using the existing theme-plan generation API rather than introducing new backend routes.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 1–220 | Workshop state types, summary state, strategy payload handling |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 1000–1320 | Existing theme-plan generation and draft-generation flow |
| `src/CP/FrontEnd/src/services/digitalMarketingActivation.service.ts` | 1–170 | Existing strategy workshop and workspace types |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Make the strategy workshop the default customer input mode and reduce visible structured inputs until they are explicitly needed. |
| `src/CP/FrontEnd/src/styles/globals.css` | modify | Add or adjust My Agents activation styles for a consultative chat-like assistant layout. |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Add coverage for assistant-message, next-step-option, and follow-up question rendering. |

**Code patterns to copy exactly:**

```typescript
const [strategyReply, setStrategyReply] = useState('')

const nextWorkshop = normalizeStrategyWorkshop(nextWorkspace.campaign_setup?.strategy_workshop)
setStrategyWorkshop(nextWorkshop)
setStrategySummary(nextWorkshop.summary || {})

const response = await generateDigitalMarketingThemePlan(hiredInstanceId, {
  campaign_setup: {
    strategy_workshop: {
      ...buildStrategyWorkshopPayload(strategyWorkshop, strategySummary, strategyWorkshop.status),
      pending_input: String(strategyReply || '').trim(),
    },
  },
})
```

**Acceptance criteria:**
1. The main DMA brief flow opens with consultative guidance and a reply composer, not a dense form.
2. The customer can answer with free text or choose a suggested next-step option.
3. The UI shows a compact checkpoint summary of what is already locked before asking for more input.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Render workshop payload with assistant message | Assistant guidance appears in the DOM |
| E2-S1-T2 | same | Workshop payload includes next step options | Suggested options are clickable |
| E2-S1-T3 | same | Submit reply through the composer | Theme-plan API is called with `pending_input` |

**Test command:**

```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx
```

**Commit message:** `feat(DMA-YT-VALUE-1): make DMA brief flow consultative`

**Done signal:** `E2-S1 done. Tests: T1 ✅ T2 ✅ T3 ✅`

---

#### Story E2-S2: Reveal structured inputs only when the chat flow actually needs them

**BLOCKED UNTIL:** E2-S1 committed to `feat/dma-yt-value-1-it1-e2`
**Estimated time:** 45 min
**Branch:** `feat/dma-yt-value-1-it1-e2`
**CP BackEnd pattern:** A — FE only

**What to do:**
> The wizard currently surfaces many business inputs too early even though the strategy workshop can collect most of the same information progressively. Change the activation flow so structured fields such as schedule, optional business context, and non-critical metadata appear only after the consultative brief is coherent or the user explicitly expands them. Keep required readiness rules intact, but hide low-value fields until they materially help the next decision.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 220–520 | Workspace state, summary payloads, and derived readiness helpers |
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | 1320–1820 | Current panel render order and input visibility |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | 700–920 | Existing input and step assertions |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/components/DigitalMarketingActivationWizard.tsx` | modify | Gate low-value structured inputs behind progressive disclosure and keep only the next necessary action visible by default. |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Assert that unnecessary fields are hidden until the flow reaches the point where they are needed. |

**Code patterns to copy exactly:**

```typescript
const canShowAdvancedInputs = strategyWorkshop.status === 'approval_ready' || strategyWorkshop.status === 'approved'

{canShowAdvancedInputs ? (
  <section>{/* advanced structured inputs */}</section>
) : (
  <div className="my-agents-activation-inline-note">The assistant will ask for more only if it helps the next YouTube decision.</div>
)}
```

**Acceptance criteria:**
1. The customer does not see multiple low-value structured inputs during the first consultative phase.
2. The UI reveals advanced inputs only when the workflow reaches a point where they are useful.
3. Readiness logic still blocks activation correctly if required data is missing.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Initial consultative phase | Advanced fields are hidden |
| E2-S2-T2 | same | Approval-ready workshop state | Advanced fields become visible |

**Test command:**

```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx
```

**Commit message:** `feat(DMA-YT-VALUE-1): reduce early DMA input load`

**Done signal:** `E2-S2 done. Tests: T1 ✅ T2 ✅`

---

### Epic E3: Customer can manage YouTube without leaving the operating surface

**Branch:** `feat/dma-yt-value-1-it1-e3`
**Objective alignment:** DMA value
**User story:** As a paying customer, I can connect, reconnect, verify, and approve YouTube work from one clear My Agents surface, so that I trust what the agent is doing and what still needs my action.

#### Story E3-S1: Upgrade channel control to always-available connect or reconnect or retest actions

**BLOCKED UNTIL:** none
**Estimated time:** 90 min
**Branch:** `feat/dma-yt-value-1-it1-e3`
**CP BackEnd pattern:** A — FE uses existing `/cp/youtube-connections` routes

**What to do:**
> `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` lines 1689–1708 and the current `DigitalMarketingChannelStatusCard` show basic channel state, but the customer journey is still split between setup actions and separate status cards. Move YouTube connect, reconnect, retest, and persist actions into an always-available in-context control panel on My Agents, using the existing start, list, validate, and attach endpoints already consumed by `DigitalMarketingActivationWizard`. Show fetched identity and validation metrics in the control panel instead of making the customer infer state from a label alone.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1640–1715 | Current channel card placement and action wiring |
| `src/CP/FrontEnd/src/components/DigitalMarketingChannelStatusCard.tsx` | 1–120 | Current limited status-card presentation |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | 740–920 | Existing connect, reconnect, validate, and persist expectations |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Pull YouTube control actions into the main DMA operating surface so they are available without leaving My Agents. |
| `src/CP/FrontEnd/src/components/DigitalMarketingChannelStatusCard.tsx` | modify | Expand the card into a richer control surface with fetched metrics and explicit action buttons. |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Add expectations for connect, reconnect, test, and persist actions inside the My Agents operating context. |

**Code patterns to copy exactly:**

```typescript
const result = await validateYouTubeConnection(savedYouTubeConnection.id)
setYoutubeValidationResult(result)
setOauthMessage(`Connection test succeeded for ${result.display_name || 'your YouTube channel'}.`)

const attachedConnection = await attachYouTubeConnection(savedYouTubeConnection.id, {
  hired_instance_id: hiredInstanceId,
  skill_id: youtubeSkillId,
})
markYouTubeAttached(attachedConnection, 'YouTube connection saved for future agent use.')
```

**Acceptance criteria:**
1. The customer can start connect, reconnect, retest, and persist YouTube from the My Agents DMA operating surface.
2. After a validation succeeds, the UI shows fetched channel metrics and identity instead of a generic success label alone.
3. The customer does not need to leave My Agents to restore a disconnected or stale YouTube binding.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Connected credential exists, hire not yet attached | Test connection action shows returned metrics |
| E3-S1-T2 | same | Persist action after successful validation | Attach call occurs and success state is visible |
| E3-S1-T3 | same | Reconnect path | OAuth start is called and browser redirect is triggered |

**Test command:**

```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx
```

**Commit message:** `feat(DMA-YT-VALUE-1): add always-available YouTube controls`

**Done signal:** `E3-S1 done. Tests: T1 ✅ T2 ✅ T3 ✅`

---

#### Story E3-S2: Unify approval and publish-readiness into one operating rail

**BLOCKED UNTIL:** E3-S1 committed to `feat/dma-yt-value-1-it1-e3`
**Estimated time:** 45 min
**Branch:** `feat/dma-yt-value-1-it1-e3`
**CP BackEnd pattern:** A — FE uses existing deliverable and marketing-review routes

**What to do:**
> `DigitalMarketingApprovalCard` and `DigitalMarketingPublishReadinessCard` currently present separate slices of the same customer decision. Rework the My Agents DMA right-rail so approval state, publish readiness, and next-action CTA are presented together as one operating decision surface. The customer should immediately understand what is approved, what is blocked, and what to do next.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | 1689–1715 | Current right-rail card order |
| `src/CP/FrontEnd/src/components/DigitalMarketingApprovalCard.tsx` | 1–120 | Current approval copy and actions |
| `src/CP/FrontEnd/src/components/DigitalMarketingPublishReadinessCard.tsx` | 1–80 | Current readiness-only presentation |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` | modify | Replace the fragmented approval/readiness display with one clearer operating rail composition. |
| `src/CP/FrontEnd/src/components/DigitalMarketingApprovalCard.tsx` | modify | Tighten the copy and action layout so approval is clearly tied to the next external YouTube action. |
| `src/CP/FrontEnd/src/components/DigitalMarketingPublishReadinessCard.tsx` | modify | Present readiness as part of the same decision context instead of as an isolated status badge. |

**Code patterns to copy exactly:**

```typescript
<Card style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
  <div style={{ fontWeight: 700 }}>Customer approval</div>
  <div style={{ fontSize: '13px', color: 'var(--colorNeutralForeground2)' }}>
    This exact deliverable must be approved before the agent can take any external YouTube action.
  </div>
</Card>
```

**Acceptance criteria:**
1. Approval state and publish readiness are shown together as one customer decision surface.
2. The next action is obvious from the card copy and CTA placement.
3. Explicit approval remains visibly required before external YouTube publish.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S2-T1 | `src/CP/FrontEnd/src/test/MyAgents.test.tsx` | Render DMA My Agents with pending deliverable | Unified operating rail copy appears |
| E3-S2-T2 | same | Render with blocked readiness | Blocking reason is visible alongside approval state |

**Test command:**

```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgents.test.tsx
```

**Commit message:** `feat(DMA-YT-VALUE-1): unify DMA approval and readiness rail`

**Done signal:** `E3-S2 done. Tests: T1 ✅ T2 ✅`

---

## Iteration 2 — My Agents shows proof of the real YouTube channel and content surface

**Scope:** The customer sees actual YouTube proof data and clearer reconnect guidance before trusting the DMA to work on the channel.
**Lane:** B (new backend support required in Plant)
**⏱ Estimated:** 3.0h | **Come back:** 2026-04-08 13:00 UTC
**Prerequisite:** Iteration 1 PR merged to `main`
**Epics:** E4, E5

> **Backend-first rule:** All S1 backend stories must be committed to `main` before their paired frontend story starts.

### Dependency Map (Iteration 2)

```text
E4-S1 (backend) ──► merge to main ──► E4-S2 (frontend)
```

---

### Epic E4: Customer sees proof of the real YouTube channel before trusting the agent

**Branch (S1):** `feat/dma-yt-value-1-it2-e4-backend`
**Branch (S2):** `feat/dma-yt-value-1-it2-e4-frontend` ← BLOCKED until E4-S1 merged to `main`
**Objective alignment:** DMA value
**User story:** As a paying customer, I can see real channel proof and reconnect guidance before I trust DMA on YouTube, so that I know exactly which channel the agent is about to affect.

#### Story E4-S1: Enrich Plant YouTube validation with recent upload proof and next-action hints — BACKEND

**BLOCKED UNTIL:** Iteration 1 merged to `main`
**Estimated time:** 45 min
**Branch:** `feat/dma-yt-value-1-it2-e4-backend`
**CP BackEnd pattern:** N/A — existing CP proxy route already forwards validate responses transparently

**What to do:**
> `src/Plant/BackEnd/services/youtube_connection_service.py` lines 280–383 currently return aggregate metrics such as subscriber count and view count, but they do not give the customer proof of recent uploads or a clearer hint about what to do next. Add a non-destructive preview payload to the existing validate response that includes a small recent-upload list plus concise next-action hints such as `connected_ready`, `reconnect_required`, or `token_expiring_soon`. Update the existing Plant validate endpoint response model instead of creating a parallel route so the current CP proxy stays thin.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/services/youtube_connection_service.py` | 280–383 | Current validate flow, available YouTube stats, safe enrichment pattern |
| `src/Plant/BackEnd/api/v1/platform_connections.py` | 96–111 and 406–418 | Current validate response model and endpoint wiring |
| `src/Plant/BackEnd/tests/unit/test_customer_platform_connections_api.py` | 1–220 | Existing route-contract tests to extend |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/services/youtube_connection_service.py` | modify | Extend validation to return recent upload preview items and a next-action hint without mutating unrelated behavior. |
| `src/Plant/BackEnd/api/v1/platform_connections.py` | modify | Extend the validate response model to include the new proof fields. Keep the existing route and customer scoping. |
| `src/Plant/BackEnd/tests/unit/test_customer_platform_connections_api.py` | modify | Assert the enriched validate payload shape and customer scoping. |

**Code patterns to copy exactly:**

```python
from core.routing import waooaw_router
from core.database import get_read_db_session

customer_router = waooaw_router(prefix="/customer-platform-connections", tags=["customer-platform-connections"])

@customer_router.get("/{customer_id}/{credential_id}")
async def get_customer_platform_credential(
    customer_id: str,
    credential_id: str,
    db = Depends(get_read_db_session),
):
  return await service.get_credential(customer_id=customer_id, credential_id=credential_id)
```

```python
class ValidateCustomerCredentialResponse(BaseModel):
    id: str
    customer_id: str
    platform_key: str
    display_name: Optional[str] = None
    verification_status: str
    connection_status: str
    recent_short_count: int
    recent_long_video_count: int
    subscriber_count: int
    view_count: int
```

**Acceptance criteria:**
1. Validating a YouTube credential returns recent upload proof data in addition to aggregate counts.
2. The response includes a machine-readable next-action hint that the FE can render directly.
3. Existing validate behavior for auth, customer scoping, and aggregate counts remains intact.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/Plant/BackEnd/tests/unit/test_customer_platform_connections_api.py` | Mock validate result with preview items | Response includes preview list and next-action hint |
| E4-S1-T2 | same | Existing customer-scoped validate call | Aggregate fields still exist |
| E4-S1-T3 | same | Wrong or missing credential | Existing error contract remains intact |

**Test command:**

```bash
docker compose -f docker-compose.test.yml run plant-test pytest src/Plant/BackEnd/tests/unit/test_customer_platform_connections_api.py -v
```

**Commit message:** `feat(DMA-YT-VALUE-1): enrich YouTube validation proof data`

**Done signal:** `E4-S1 done. PR #[N] opened for E4-S1 branch merge to main. Tests: T1 ✅ T2 ✅ T3 ✅`

---

#### Story E4-S2: Render recent upload proof and reconnect guidance in My Agents — FRONTEND

**BLOCKED UNTIL:** E4-S1 merged to `main`
**Estimated time:** 90 min
**Branch:** `feat/dma-yt-value-1-it2-e4-frontend`
**CP BackEnd pattern:** A — call existing `/cp/youtube-connections/{id}/validate` via `gatewayRequestJson`

**What to do:**
> Once the enriched validate payload is available, extend the My Agents YouTube control surface so it shows recent upload proof, reconnect hints, and customer-facing confirmation details rather than only numeric counts. Keep the control surface in My Agents and use the existing CP proxy route. The goal is that a paying customer can confirm “yes, this is my channel and these are the recent items the agent is about to work around.”

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` | 1–130 | Current validate response type |
| `src/CP/FrontEnd/src/components/DigitalMarketingChannelStatusCard.tsx` | 1–120 | Current status-card rendering |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | 740–920 | Existing validation-metrics expectations |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/CP/FrontEnd/src/services/youtubeConnections.service.ts` | modify | Extend `ValidateYouTubeConnectionResponse` to include the new preview and hint fields. |
| `src/CP/FrontEnd/src/components/DigitalMarketingChannelStatusCard.tsx` | modify | Render recent upload proof and next-action hint in a customer-friendly format. |
| `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | modify | Assert that recent upload proof and reconnect guidance render from the enriched payload. |

**Code patterns to copy exactly:**

```typescript
export async function validateYouTubeConnection(
  credentialId: string
): Promise<ValidateYouTubeConnectionResponse> {
  return gatewayRequestJson<ValidateYouTubeConnectionResponse>(
    `/cp/youtube-connections/${encodeURIComponent(credentialId)}/validate`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    }
  )
}
```

```typescript
if (props.error) {
  return <Card><div>YouTube channel status unavailable</div></Card>
}
```

**Acceptance criteria:**
1. After validation, the My Agents YouTube panel shows recent upload proof data and a clear next-action hint.
2. Reconnect-required or token-warning states are visible in customer language, not only through raw status codes.
3. The existing validate action still works when proof fields are absent or empty.

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S2-T1 | `src/CP/FrontEnd/src/test/MyAgentsDigitalMarketingWizard.test.tsx` | Enriched validate response with preview items | Recent uploads render in the panel |
| E4-S2-T2 | same | Validate response with reconnect hint | Reconnect guidance text renders |
| E4-S2-T3 | same | Validate response without preview items | Existing fallback metrics view still works |

**Test command:**

```bash
cd src/CP/FrontEnd && npx vitest run src/test/MyAgentsDigitalMarketingWizard.test.tsx
```

**Commit message:** `feat(DMA-YT-VALUE-1): show YouTube proof on My Agents`

**Done signal:** `E4-S2 done. Tests: T1 ✅ T2 ✅ T3 ✅`

---

## Rollback

```bash
git log --oneline -10 origin/main
git revert -m 1 <merge-commit-sha>
git push origin main
```