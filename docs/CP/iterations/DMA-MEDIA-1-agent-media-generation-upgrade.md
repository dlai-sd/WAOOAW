# DMA-MEDIA-1 — DMA Agent Media Generation Upgrade

**Objective**
This plan upgrades the Digital Marketing Agent from a text-only strategy and draft generator into an artifact-capable agent that can produce customer-requested tables, images, audio, video, and combined video+audio without breaking the current architectural guardrails.
The upgrade must preserve the existing strengths of the platform: CP BackEnd stays a thin proxy, Plant BackEnd owns business logic, approvals remain mandatory before publication, and all new media handling remains provider-agnostic and promotion-safe.
The first release bias is DMA value: customers should be able to ask for richer deliverables, review them safely, and use the same approval flow instead of learning a separate media subsystem.
If a story does not improve DMA value delivery, DMA enablement, or runtime safety for this path, cut it.

> **Template version**: 2.0 adapted for a durable branch-first execution workflow on 2026-04-10.

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `DMA-MEDIA-1` |
| Feature area | Customer Portal + Plant BackEnd — DMA artifact and media generation |
| Created | 2026-04-10 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 3 |
| Total epics | 7 |
| Total stories | 10 |

---

## Vision Intake

- Area: Plant BackEnd is the primary implementation owner for media generation, artifact typing, storage, and publish contracts; CP FrontEnd and CP BackEnd changes exist to let customers request, review, and approve those artifacts without violating the thin-proxy pattern.
- Outcome: A DMA customer can explicitly request a table, image, audio clip, video, or video+audio deliverable from the DMA workflow and receive a typed artifact they can preview, approve, and later publish through the existing channel flow.
- Out of scope: Generic SaaS media studio work, non-DMA agent lanes, billing changes, mobile app work, fully autonomous publish-without-approval behavior, and provider-specific lock-in in business logic.
- Lane: Lane B first because new Plant backend capabilities are required before CP can wire a usable customer experience. Lane A follows only after the backend contract is stable.
- Timeline constraint: Durable execution only. Commit and push the plan skeleton first, then commit and push each completed iteration section so disconnection cannot lose plan state.
- Objective alignment: DMA value and DMA enablement. This closes the current blocker where DMA can discuss rich outputs but cannot actually generate, store, route, or render them as first-class artifacts.

---

## Architecture Guardrails

| Guardrail | Required behavior |
|---|---|
| CP BackEnd role | Thin proxy only. No business logic, no media processing, no provider SDK coupling. |
| Plant ownership | Artifact contracts, routing, generation orchestration, storage metadata, review state, and publish readiness stay in Plant BackEnd. |
| Approval safety | Customer approval remains required before any external publish action. Media generation may be async, but publish stays gated. |
| Cloud portability | Media storage and generation providers must sit behind adapters. No provider SDK in business logic. |
| Image promotion | No environment-specific URIs or credentials baked into code or Dockerfiles. |
| Observability | New generation jobs and storage calls must be traceable with correlation IDs, structured logs, and metrics. |
| DMA-first scope | Build the minimal platform shape that unlocks DMA artifacts now; defer generalized marketplace-wide media tooling. |

---

## Target State Definition

The DMA workflow accepts a typed artifact request instead of treating every prompt as plain text strategy. Plant translates that request into a stable artifact contract, routes it to the right generation path, stores metadata and asset references, and returns draft artifacts that CP can preview in the normal review flow. The customer sees clear generation state, previews for each artifact type, and the next required approval action. Publishing stays separate from generation: a generated asset becomes publishable only after review, channel validation, and explicit approval.

### Target-state acceptance criteria

1. DMA can represent artifact intent explicitly as `table`, `image`, `audio`, `video`, or `video_audio` instead of collapsing all outputs into text.
2. Plant stores draft artifact metadata and binary asset references in a durable, provider-agnostic way.
3. Async generation exists for binary artifacts so long-running media work does not block the request-response path.
4. CP can request artifact types, poll or display job state, and preview returned artifacts inside the DMA operating surface.
5. Existing approval and publish flows continue to work, with richer readiness and validation states for media artifacts.
6. Docker-based validation exists for the new backend and frontend contract paths at the end of execution.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B foundation — define typed artifact contracts, persistence, adapter seams, and async job lifecycle for DMA media generation | 3 | 4 | 5.5h | 2026-04-10 18:30 UTC |
| 2 | Lane B execution — wire media generation providers, storage, artifact routing, review-state integration, and publish-ready backend responses | 2 | 3 | 5.0h | 2026-04-11 12:30 UTC |
| 3 | Lane A integration — proxy CP safely, render artifact previews in DMA UI, and complete Docker validation for the end-to-end contract | 2 | 3 | 4.5h | 2026-04-11 18:30 UTC |

**Why 3 iterations are justified:** this upgrade changes the backend domain contract, introduces async binary-artifact infrastructure, and then wires customer review UX on top. Collapsing all three into 2 iterations would either overload a single PR or blur backend-before-frontend merge discipline.

---

## How to Launch Each Iteration

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. Select **platform-engineer** if available
5. Paste the task block below
6. Start the run
7. Come back at **2026-04-10 18:30 UTC**

**Iteration 1 agent task**

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior platform architecture engineer + Senior async job orchestration engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-MEDIA-1-agent-media-generation-upgrade.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3. Do not touch Iteration 2 or 3 content.
TIME BUDGET: 5.5h. If you reach 6.5h without finishing, follow STUCK PROTOCOL now.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell, git, gh, and docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch and PR flow for this run.

FAIL-FAST VALIDATION GATE:
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify repository writes are possible on the task branch.
3. Verify a PR to `main` can be opened or updated, or explicitly report that PR controls are unavailable.
4. If any gate fails, post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read the Agent Execution Rules section in this plan file.
2. Read the Iteration 1 section in this plan file.
3. Read nothing else before starting.
4. Execute Epics E1 → E2 → E3 in order.
5. Add or update the tests listed in each story before moving on.
6. If tool execution is available, run the narrowest relevant validation and record the result.
7. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

### Iteration 2

> Do not launch until Iteration 1 is merged to `main` and the evidence block below is updated.

**Prerequisite evidence:**
- Iteration 1 merge status: `PENDING HUMAN UPDATE BEFORE LAUNCH`
- Iteration 1 PR: `TBD`
- Merge commit on `main`: `TBD`
- Merged at: `TBD`

**Steps to launch:** same as Iteration 1

**Iteration 2 agent task**

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI / SQLAlchemy engineer + Senior media pipeline engineer + Senior cloud-portable storage adapter engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-MEDIA-1-agent-media-generation-upgrade.md
YOUR SCOPE: Iteration 2 only — Epics E4, E5. Do not touch other iterations.
TIME BUDGET: 5.0h.

PREREQUISITE CHECK:
1. Read the Prerequisite evidence block under Iteration 2.
2. If it is still pending or incomplete, post `Blocked: Iteration 1 merge evidence has not been recorded in the plan.` and HALT.

FAIL-FAST VALIDATION GATE:
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify repository writes are possible on the task branch.
3. Verify a PR to `main` can be opened or updated, or explicitly report that PR controls are unavailable.
4. If any gate fails, post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read Agent Execution Rules and Iteration 2 only.
2. Execute backend work in the listed order.
3. Add or update the tests listed in each story before moving on.
4. If execution tools are available, run the narrowest relevant validation and record the result.
5. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

### Iteration 3

> Do not launch until Iteration 2 is merged to `main` and the evidence block below is updated.

**Prerequisite evidence:**
- Iteration 2 merge status: `PENDING HUMAN UPDATE BEFORE LAUNCH`
- Iteration 2 PR: `TBD`
- Merge commit on `main`: `TBD`
- Merged at: `TBD`

**Steps to launch:** same as Iteration 1

**Iteration 3 agent task**

```text
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior React / TypeScript / Vite engineer + Senior Python 3.11 / FastAPI engineer + Senior product-minded DMA UX engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/CP/iterations/DMA-MEDIA-1-agent-media-generation-upgrade.md
YOUR SCOPE: Iteration 3 only — Epics E6, E7. Do not touch earlier iterations.
TIME BUDGET: 4.5h.

PREREQUISITE CHECK:
1. Read the Prerequisite evidence block under Iteration 3.
2. If it is still pending or incomplete, post `Blocked: Iteration 2 merge evidence has not been recorded in the plan.` and HALT.

FAIL-FAST VALIDATION GATE:
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify repository writes are possible on the task branch.
3. Verify a PR to `main` can be opened or updated, or explicitly report that PR controls are unavailable.
4. If any gate fails, post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read Agent Execution Rules and Iteration 3 only.
2. Respect backend-before-frontend sequencing inside the iteration.
3. Add or update the tests listed in each story before moving on.
4. Run Docker-only validation if execution tools are available; do not use virtual environments.
5. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

---

## Agent Execution Rules

### Rule -2 — Fail-fast validation gate

Before reading story cards in detail or making any code changes, validate all of the following:

- The plan file is readable and your assigned iteration section exists.
- Any required prerequisite-evidence block for the iteration is complete and not marked pending.
- The execution surface allows repository writes on the current task branch.
- The execution surface allows opening or updating a PR to `main`, or you can explicitly report that PR controls are unavailable.

If any check fails, post `Blocked at validation gate: [exact reason]` and HALT immediately.

### Rule -1 — Activate Expert Personas

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona immediately. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

### Rule 0 — Use the GitHub task branch and open the iteration PR early

- One iteration = one GitHub task branch and one PR.
- If the execution surface already created a branch, keep using it.
- If the UI lets you choose a branch name, prefer `feat/dma-media-1-itN-short-scope-runid`.
- Open a draft PR to `main` as soon as PR controls are available and keep updating that same PR.
- Use the Tracking Table in this plan as the source of truth for story status updates.

### Rule 1 — Scope lock

- Implement exactly the acceptance criteria in the story card.
- Do not refactor unrelated code.
- Do not edit files outside the story card’s allowed file list.
- If you discover out-of-scope issues, note them and move on.

### Rule 2 — Tests before the next story

- Add every listed test before moving to the next story.
- If test execution is available, run the narrowest relevant command.
- If execution tooling is unavailable, add the tests and record that execution is deferred.
- Final validation for this plan must use Docker only. Do not use a virtual environment.

### Rule 3 — Save progress after every story

- Update the Tracking Table status.
- Save code and plan updates to the iteration branch.
- If a PR already exists, add a concise progress update with changed files, tests, and next story.

### Rule 4 — Validate after every epic

- Prefer the narrowest relevant automated validation for the changed files.
- If execution tools are available, run the command and record the result.
- If not, state clearly that validation is deferred.
- After validation, add `**Epic complete ✅**` under the epic heading.

### Rule 5 — STUCK PROTOCOL

- After 3 failed implementation attempts on the same blocker, mark the story as `🚫 Blocked`.
- Open or update a draft PR titled `WIP: dma-media-blocked-story — blocked` if PR controls are available.
- Include the exact blocker, the exact error, and 1-2 attempted fixes.
- Post the PR URL if available, otherwise post the blocker in the thread, then HALT.

### Rule 6 — Iteration PR

- Use the same task branch for the final iteration PR to `main`.
- PR title format: `feat(DMA-MEDIA-1): iteration N — one-line summary`.
- PR body must include completed stories, validation status or deferral, and the NFR checklist.
- Post the PR URL in the task thread and HALT.

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:

```bash
git add -A && git commit -m "feat(DMA-MEDIA-1): [epic-id] — [epic title]" && git push
```

Do this before starting the next epic. If interrupted, completed work is already saved.

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1 | 1 | DMA speaks a typed artifact language | Story cards pending | 🔴 Not Started | — |
| E2 | 1 | DMA stores draft artifact metadata safely | Story cards pending | 🔴 Not Started | — |
| E3 | 1 | DMA generation jobs run asynchronously | Story cards pending | 🔴 Not Started | — |
| E4 | 2 | DMA routes artifacts to provider-safe generation adapters | Story cards pending | 🔴 Not Started | — |
| E5 | 2 | DMA returns review-ready artifact payloads | Story cards pending | 🔴 Not Started | — |
| E6 | 3 | CP proxies and types the artifact contract without owning logic | Story cards pending | 🔴 Not Started | — |
| E7 | 3 | DMA customers can preview and approve media artifacts in CP | Story cards pending | 🔴 Not Started | — |
