# PLANT-DMA-1 — Digital Marketing Agent MVP (Theme Discovery, Content Creation, Approved YouTube Publishing)

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-DMA-1` |
| Feature area | Cross-surface Digital Marketing Agent MVP across Plant, CP, PP, and mobile |
| Created | 2026-03-11 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §1, §4.6, §5.1, §5.3, §11, §26 |
| Platform index | `docs/CONTEXT_AND_INDEX.md` |
| Total iterations | 3 |
| Total epics | 6 |
| Total stories | 12 |

---

## Zero-Cost Agent Constraints (READ FIRST)

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is self-contained and names exact file paths |
| No working memory across files | Each backend story embeds the relevant route and dependency patterns inline |
| No planning ability | Stories are atomic and sequenced backend first, then customer surfaces, then PP and hardening |
| Token cost per file read | Max 3 files in each story card's `Files to read first` section |
| Binary inference only | Acceptance criteria are written as pass/fail behavioural outcomes |

> Agent: execute exactly one story at a time. Read only the story card you were assigned and the files listed in that card.

---

## PM Review Checklist

- [x] Epic titles name customer or operator outcomes
- [x] Every story has an exact branch name
- [x] Every story card will embed relevant NFR snippets inline
- [x] Every story card will keep `Files to read first` to 3 or fewer files
- [x] CP BackEnd stories follow thin-proxy discipline
- [x] New backend route stories use `waooaw_router()`
- [x] GET route stories call out `get_read_db_session()`
- [x] Stories involving secrets name the exact credential and adapter surfaces
- [x] Every story has `BLOCKED UNTIL` or `none`
- [x] Each iteration has an estimate and come-back time
- [x] STUCK PROTOCOL is included in Agent Execution Rules
- [x] Backend stories come before frontend/mobile stories that depend on them
- [x] Iteration count is justified by cross-surface scope and approval-publish governance requirements
- [x] No placeholders remain in the skeleton

---

## Vision Intake (confirmed)

1. **Area:** Plant runtime and agent mould first, then CP, PP, and mobile operating surfaces for the first sellable Digital Marketing Agent.
2. **User outcome:** A customer hires a Digital Marketing Agent, completes a guided Theme Discovery conversation, receives channel-ready content drafts, explicitly approves each deliverable, and only then allows YouTube publication through a governed scheduler flow.
3. **Out of scope:** Multi-channel live publishing beyond YouTube, image/video generation, auto-publish without customer approval, performance optimization loops, ads management, and broad analytics automation.
4. **Lane choice:** Mixed. Lane B first for new Plant and proxy routes, then Lane A for CP, PP, and mobile wiring onto the new contracts.
5. **Timeline constraint:** Not explicitly fixed by the user; optimize for a mergeable MVP plan that can drive immediate execution after review.

---

## Architecture Decisions (read before coding)

### Product shape

The first sellable Digital Marketing Agent exposes three customer-visible skills:

1. `Theme Discovery`
2. `Content Creation`
3. `Content Publishing`

`Theme Discovery` is not a plain text field. It is a guided conversation skill that produces a structured marketing brief. `Content Creation` consumes that brief and generates customer-reviewable deliverables. `Content Publishing` is a governed publish skill that remains hard-blocked until the customer approves the exact deliverable.

### Approval invariant

No external platform handshake, upload, schedule execution, or publish submit is allowed before customer approval of the exact deliverable. For this MVP, that invariant applies to YouTube first and must be enforced in Plant runtime state and scheduler logic, not only in CP/mobile UI.

### Channel scope

Iteration 1 channel scope is YouTube only. The model, stateless components, and destination abstractions must still be designed so Facebook, LinkedIn, X, Instagram, and future channels can be added later without redesigning customer or operator flows.

### Shared component principle

Common product components must be stateless and reusable across CP, PP, and mobile. Shared UI and runtime concepts include:

- Theme brief summary
- Objective and audience cards
- Channel selection and credential status
- Draft approval cards
- Publish cadence and schedule state
- Skill progress and run history
- Deliverable status timeline

### Runtime rule

Plant remains the source of truth for hired-agent state, skill config, deliverables, approval state, scheduler eligibility, publish receipts, and observability. CP and mobile are customer operating surfaces. PP is the operator and governance surface.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Agent contract, Theme Discovery brief model, approval-gated YouTube runtime and proxy layer | E1, E2 | 4 | 6h | 2026-03-12 06:00 UTC |
| 2 | Customer workflow on CP and mobile for Theme Discovery, review, approval, and publish readiness | E3, E4 | 4 | 6h | 2026-03-12 14:00 UTC |
| 3 | PP governance workflow, monitoring, scheduler hardening, and release regression | E5, E6 | 4 | 5h | 2026-03-12 20:00 UTC |

**Estimate basis:** new Plant model/runtime story = 90 min, new proxy/API story = 45 min, cross-surface customer story = 60–90 min, PP governance story = 60 min, regression/hardening story = 45–60 min.

---

## Agent Execution Rules

1. Start from `main` with a clean tree.
2. Execute only one story at a time.
3. Read only the files listed in the story card before editing.
4. Keep CP BackEnd and PP BackEnd as thin proxies only.
5. Plant owns publish eligibility, approval state, scheduler gating, and destination execution truth.
6. All external publish flows must fail closed if approval is absent, expired, revoked, or the platform credential reference is missing.
7. Every story ends with the exact validation command written in its card.
8. **CHECKPOINT RULE**: After completing each epic (all tests passing), run:

```bash
git add -A && git commit -m "feat([plan-id]): [epic-id] — [epic title]" && git push
```

Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

9. **STUCK PROTOCOL**: if blocked for more than 20 minutes on one story, open a draft PR titled `WIP: PLANT-DMA-1 [story-id] — [blocker]`, post the blocker, and halt.

---

## How to Launch Each Iteration

### Iteration 1

Acting personas: Senior Python/FastAPI engineer, Senior platform runtime engineer, Senior scheduler/secrets integration engineer.

### Iteration 2

Acting personas: Senior React/TypeScript engineer, Senior React Native/Expo engineer, Senior customer workflow designer.

### Iteration 3

Acting personas: Senior PP operations workflow engineer, Senior observability engineer, Senior release-hardening engineer.

---

## Iteration Details

Story cards intentionally omitted from the skeleton commit. They are added in the follow-up commit on this same branch.