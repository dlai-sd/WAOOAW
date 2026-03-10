# AGENT-WORKFORCE-1 — Single-Agent-First Platform Fit

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `AGENT-WORKFORCE-1` |
| Feature area | Platform-wide Agent, Skill, Component fit across Plant, PP, CP, and mobile |
| Created | 2026-03-10 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | [docs/WAOOAW Design.md](/workspaces/WAOOAW/docs/WAOOAW%20Design.md) |
| Platform index | [docs/CONTEXT_AND_INDEX.md](/workspaces/WAOOAW/docs/CONTEXT_AND_INDEX.md) |
| Total iterations | 2 |
| Total epics | 0 |
| Total stories | 0 |

---

## Vision Intake

- Service or area: Plant core runtime with PP admin authoring, CP customer runtime, and mobile runtime parity.
- User outcome: a platform user can define and test a single agent from reusable skills and components in PP, publish it for hiring, and a customer can hire, configure, review, approve, and operate it from CP and mobile.
- Out of scope: full multi-agent team execution, autonomous team-to-team collaboration, and broad marketplace redesign.
- Delivery lane: Lane B first where new backend contracts and schema are needed, then Lane A wiring into PP, CP, and mobile.
- Timeline constraint: design for staged rollout, single-agent-first now, team-ready later.

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for autonomous agents with limited context windows.
Every story card will be self-contained, file-scoped, and include the exact NFR patterns needed.

---

## Current-State Compliance Audit

This section records the current platform fit against the target design before implementation planning.

| Area | Current state | Fit with target design |
|---|---|---|
| Plant runtime | Has AgentSpec, ConstructBindings, hired agent lifecycle, approvals, goal and deliverable flows | Partial fit — strong construct base, weak first-class Team and Role runtime model |
| PP | Has genesis, agent setups, constraint policy, approvals, ops hired-agent diagnostics | Partial fit — governance exists, but authoring/testing/publish workflow is fragmented |
| CP | Has marketplace, hire, my agents, skills config, approvals, runtime operations | Partial fit — customer runtime exists, but capability contracts are not exposed cleanly as Skills and Components |
| Mobile | Has discovery, hire, my agents, trial dashboard, approvals, operations | Partial fit — runtime parity is improving, but not yet aligned to the target skill/component narrative |
| Data model | Has Agent, Skill, JobRole, Team entities in constitutional layer | Partial fit — Team exists conceptually, but not yet as a dormant single-agent-first runtime envelope |

---

## Walkthrough Simulation Target

The implementation plan must prove this customer and platform walkthrough:

1. PP user creates or certifies reusable skills and assigns them to an agent type.
2. PP user tests the construct on the fly using a safe draft SkillRun path.
3. PP user publishes the agent type for hiring.
4. Customer discovers and hires the agent in CP or mobile.
5. Customer configures allowed inputs and goals for that hired agent.
6. The skill runs through reusable components in Plant.
7. Customer reviews drafts, approvals, results, and operations in CP or mobile.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Platform contracts, data model fit, and PP authoring/test/publish path | 0 | 0 | 0h | 2026-03-10 20:00 UTC |
| 2 | CP/mobile customer runtime fit, walkthrough validation, and rollout gating | 0 | 0 | 0h | 2026-03-11 20:00 UTC |

---

## Agent Execution Rules

> **CHECKPOINT RULE**: After completing each epic (all tests passing), run:
> ```bash
> git add -A && git commit -m "feat(AGENT-WORKFORCE-1): [epic-id] — [epic title]" && git push
> ```
> Do this BEFORE starting the next epic. If interrupted, completed epics are already saved.

- Scope lock: stories may only touch files named in the story card.
- Use `waooaw_router()` for every new API route.
- Use `get_read_db_session()` for reads and `get_db_session()` only for writes.
- CP and PP remain thin surfaces over Plant runtime logic.
- Single-agent-first UX is the product priority; team model stays dormant but real in design.
- STUCK PROTOCOL: if blocked for more than 30 minutes, post the blocker and halt.
