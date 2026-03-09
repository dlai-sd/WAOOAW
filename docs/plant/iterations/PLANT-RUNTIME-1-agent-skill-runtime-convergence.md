# PLANT-RUNTIME-1 — Agent-Skill-Runtime Convergence

> **Template version**: 2.0

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | `PLANT-RUNTIME-1` |
| Feature area | Plant BackEnd — SkillRuntimeResolver + GoalSchedulerService wiring |
| Created | 2026-03-09 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | `docs/CONTEXT_AND_INDEX.md` §4.6 (Construct Execution Flow) |
| Total iterations | 2 |
| Total epics | 4 |
| Total stories | 4 |

---

## Design Decision Log

**Why this work is needed:**

`GoalSchedulerService._execute_goal` gained a typed pump→processor pipeline in PLANT-MOULD-1,
but `run_goal_with_retry` never passes `agent_spec` or `goal_config` — so the typed path was
dead code. PLANT-SKILLS-1 added `AgentSkillModel.goal_config` JSONB for customer-configured
goals. This plan bridges them: a `SkillRuntimeResolver` maps DB entities to runtime objects,
and `run_goal_with_retry` is updated to accept and forward them.

| Decision | Rationale |
|---|---|
| `SkillRuntimeResolver` as a separate service | Keeps GoalSchedulerService pure (no DB access); callers inject the bundle |
| Soft-fail (returns None) on resolution miss | Legacy path already raises NotImplementedError; no regression |
| `goal_config` defaults to `{}` on None | Pump ABCs require `dict[str, Any]` — never pass None downstream |
| AgentSpecRegistry as in-memory source | Specs are compiled at startup; no DB round-trip needed for the spec |

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — SkillRuntimeResolver + GoalSchedulerService wiring | E1, E2 | 2 | 2h | +2.5h from launch |
| 2 | Lane A — Wire resolver into all run_goal_with_retry call-sites | E3, E4 | 2 | 2h | +2.5h from launch |

---

## Agent Execution Rules

### Rule 0 — Open tracking draft PR first
```bash
git checkout main && git pull
git checkout -b feat/PLANT-RUNTIME-1-it1
git commit --allow-empty -m "chore(PLANT-RUNTIME-1): start iteration 1"
git push origin feat/PLANT-RUNTIME-1-it1
gh pr create --base main --head feat/PLANT-RUNTIME-1-it1 --draft \
  --title "tracking: PLANT-RUNTIME-1 Iteration 1 — in progress" \
  --body "- [ ] E1: SkillRuntimeResolver\n- [ ] E2: GoalSchedulerService wiring"
```

### Rule 1 — Scope lock
Touch only files listed in the story card. No refactoring outside scope.

### Rule 2 — Tests before advancing
Write tests before advancing to next story.

### Rule 3 — Docker integration test after every epic
```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### CHECKPOINT RULE
After completing each epic:
```bash
git add -A && git commit -m "feat(PLANT-RUNTIME-1): [epic-id] — [title]" && git push
```

---

## Iteration 1

### Epic E1: SkillRuntimeResolver bridges DB to typed runtime pipeline

**Outcome:** Given a `goal_instance_id`, the platform can resolve the correct `AgentSpec`
(with `ConstructBindings`) and the customer's `goal_config` from the database, enabling the
typed pump→processor pipeline to run.

**Context:** `AgentSkillModel.goal_config` (PLANT-SKILLS-1) holds customer settings, and
`AgentSpecRegistry` (PLANT-MOULD-1) holds the in-memory specs — but nothing connects them
to a running goal. This epic adds the bridge.

**Files to create / modify:**

| Action | File |
|---|---|
| CREATE | `src/Plant/BackEnd/services/skill_runtime_resolver.py` |
| CREATE | `src/Plant/BackEnd/tests/unit/test_skill_runtime_resolver.py` |

**Acceptance criteria:**
- [x] `SkillRuntimeResolver.resolve_for_goal(goal_instance_id)` returns `SkillRuntimeBundle` on happy path
- [x] Returns `None` when goal, hired agent, or spec not found
- [x] `goal_config` defaults to `{}` when no primary `AgentSkillModel` row exists
- [x] `pytest tests/unit/test_skill_runtime_resolver.py` exits 0

---

### Epic E2: GoalSchedulerService accepts agent_spec + goal_config for typed dispatch

**Outcome:** `run_goal_with_retry` accepts `agent_spec` and `goal_config` and forwards them
to `_execute_goal`, enabling the typed pump→processor path in production.

**Context:** Before this change, `_execute_goal`'s typed path was only exercised in tests
(by calling `_execute_goal` directly). `run_goal_with_retry` always fell back to the legacy
stub. This epic wires the two together.

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/Plant/BackEnd/services/goal_scheduler_service.py` — add `agent_spec`, `goal_config` params to `run_goal_with_retry` |
| CREATE | `src/Plant/BackEnd/tests/unit/test_runtime_convergence_wiring.py` |

**Acceptance criteria:**
- [x] `run_goal_with_retry` accepts `agent_spec: Optional[AgentSpec] = None` and `goal_config: Optional[dict] = None`
- [x] When `agent_spec` is provided with bindings, typed path fires (pump + processor called)
- [x] When `agent_spec` is None, legacy path fires (`NotImplementedError`)
- [x] `pytest tests/unit/test_runtime_convergence_wiring.py` exits 0

---

## Iteration 2

### Epic E3: Wire SkillRuntimeResolver into the scheduler trigger API

**Outcome:** `POST /scheduler/trigger/{goal_instance_id}` resolves `agent_spec` and
`goal_config` via `SkillRuntimeResolver` before calling `run_goal_with_retry`, so
manual triggers use the typed pump→processor path when a spec is available.

**Context:** After E1 and E2, `SkillRuntimeResolver` can bridge DB → runtime bundle
and `run_goal_with_retry` can accept the bundle, but the trigger API endpoint
(`trigger_goal_run` in `scheduler_admin.py`) still calls `run_goal_with_retry`
without `agent_spec` or `goal_config` — so manual triggers always fall through to
the legacy stub path.  This epic closes the gap at the API layer.

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/Plant/BackEnd/api/v1/scheduler_admin.py` — inject `AsyncSession` into `trigger_goal_run` and call `SkillRuntimeResolver.resolve_for_goal` |
| CREATE | `src/Plant/BackEnd/tests/unit/test_scheduler_admin_uses_resolver.py` |

**Acceptance criteria:**
- [x] `trigger_goal_run` accepts `db: AsyncSession = Depends(get_read_db_session)`
- [x] A `SkillRuntimeResolver(db)` is constructed inside the handler
- [x] When resolver returns a bundle, `run_goal_with_retry` is called with `agent_spec` and `goal_config`
- [x] When resolver returns `None` (soft-fail), `run_goal_with_retry` is called without them (legacy path)
- [x] `pytest tests/unit/test_scheduler_admin_uses_resolver.py` exits 0

---

### Epic E4: Wire SkillRuntimeResolver into SchedulerPersistenceService recovery

**Outcome:** `SchedulerPersistenceService._replay_missed_run` uses
`SkillRuntimeResolver` when one is injected, enabling the typed pipeline for
recovered/replayed goal runs — not just manually triggered ones.

**Context:** `_replay_missed_run` in `scheduler_persistence_service.py` is the
recovery path that fires when the scheduler restarts and replays missed runs.
Like the trigger API, it calls `run_goal_with_retry` without `agent_spec` /
`goal_config`, leaving replayed runs on the legacy stub path even after E3 fixes
the manual-trigger path.

**Files to create / modify:**

| Action | File |
|---|---|
| MODIFY | `src/Plant/BackEnd/services/scheduler_persistence_service.py` — add optional `resolver` param to `__init__`; use it in `_replay_missed_run` |
| CREATE | `src/Plant/BackEnd/tests/unit/test_persistence_service_uses_resolver.py` |

**Acceptance criteria:**
- [x] `SchedulerPersistenceService.__init__` accepts `resolver: Optional[SkillRuntimeResolver] = None`
- [x] When resolver is provided, `_replay_missed_run` awaits `resolver.resolve_for_goal` and passes the bundle to `run_goal_with_retry`
- [x] When resolver is `None`, behaviour is unchanged (no regression)
- [x] `pytest tests/unit/test_persistence_service_uses_resolver.py` exits 0
