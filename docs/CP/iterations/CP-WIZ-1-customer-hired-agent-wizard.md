# CP-WIZ-1 — Customer Hired-Agent Wizard Iteration Plan

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `CP-WIZ-1` |
| Feature area | Customer Portal — Hired Agent Wizard |
| Created | 2026-03-17 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/plant/iterations/CP_MyAgents.md` |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 3 |
| Total stories | 6 |

---

## Objective

Replace CP's long hired-agent management surface with one wizard-based customer experience. Customers coming from the hire journey should land directly on the newly hired agent's wizard, while customers opening My Agents should begin with agent selection and then follow the same step model for activation or lighter post-activation edits.

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous zero-cost model agents with limited context windows.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is self-contained and names exact files |
| No working memory across files | NFR code patterns are embedded inline in each backend story |
| No planning ability | Stories are atomic, sequential, and acceptance criteria are binary |
| Token cost per file read | Max 3 files to read first per story |
| User requested single iteration | All work is sequenced into one iteration with sequential checkpoints |

---

## PM Review Checklist (tick every box before publishing)

- [ ] EXPERT PERSONAS filled
- [ ] Epic titles name customer outcomes, not technical actions
- [ ] Every story has an exact branch name
- [ ] Every story card embeds relevant NFR code snippets inline
- [ ] Every story card has max 3 files in Files to read first
- [ ] Every story involving CP BackEnd states the exact pattern: A, B, or C
- [ ] Every new backend route story embeds the `waooaw_router()` snippet
- [ ] Every GET route story card says `get_read_db_session()` not `get_db_session()`
- [ ] Every story has `BLOCKED UNTIL` or `none`
- [ ] Iteration count minimized to one
- [ ] Agent execution rules include sequential push checkpoints and final testing rule
- [ ] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — unify CP hire and My Agents into one shared wizard, adding Plant/CP thin-proxy support where the current contract is too weak | 3 | 6 | 6h | 2026-03-17 21:00 IST |

---

## How to Launch Each Iteration

### Iteration 1

TBD in final plan draft.

---

## Agent Execution Rules

TBD in final plan draft.

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | TBD | TBD | 🔴 Not Started | — |
| E1-S2 | 1 | TBD | TBD | 🔴 Not Started | — |
| E2-S1 | 1 | TBD | TBD | 🔴 Not Started | — |
| E2-S2 | 1 | TBD | TBD | 🔴 Not Started | — |
| E2-S3 | 1 | TBD | TBD | 🔴 Not Started | — |
| E3-S1 | 1 | TBD | TBD | 🔴 Not Started | — |

---

## Iteration 1 — Customer Uses One Wizard Everywhere

Content to be completed in the final plan draft.