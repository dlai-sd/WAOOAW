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
| Total epics | 4 |
| Total stories | 8 |

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

This section records the fit between the latest design and the current live platform surfaces.

| Area | Root cause | Impact | Best possible solution/fix |
|---|---|---|---|
| Plant runtime | `AgentSpec`, `ConstructBindings`, approvals, and hired-agent lifecycle exist, but Team and Role are not first-class runtime envelopes | Strong component DNA exists, but single-agent and future team execution are not modeled with one stable shape | Add dormant Team and Role runtime entities and attach hired agents and skill runs to them without changing current single-agent UX |
| PP authoring | Skill certification, agent setup, constraint policy, and ops screens exist across separate flows | PP user cannot cleanly do define -> test construct -> publish for hire from one coherent platform flow | Introduce one PP authoring path that binds skill, construct, constraint policy, simulation, and publishability state |
| CP customer runtime | Discovery, hire wizard, My Agents, skills config, approvals, and operations exist but are split across marketplace, hire, and runtime views | Customer can hire and operate agents, but the skill/component story is implicit and hard to explain or govern | Keep the UX simple, but align route contracts and labels around Agent, Skill, SkillRun, approval, and result flow |
| Mobile runtime | Discover, hire, My Agents, TrialDashboard, AgentOperations, and approval queue exist or partially exist | Mobile is close to parity but still inherits some older naming and screen routing assumptions | Align mobile navigation and runtime actions to the same CP contract and hired-agent operations model |
| Data model | Team exists constitutionally, but runtime flows still mostly stop at customer -> hired agent | Future team model would require retrofitting collaboration later | Treat every current single-agent hire as Team(1) + Role(1) from day one, with team features dormant in UX |
| Route surface | Existing routes are spread across Plant `genesis`, `agent_mold`, `hired_agents_simple`, `approvals`, CP `hire_wizard`, `cp_skills`, `my_agents_summary`, PP `agent_setups`, `ops_hired_agents`, and mobile hooks | The platform works, but authoring/test/publish/runtime steps are not stitched into one lifecycle | Add missing stitching routes and summarize current routes behind a small number of durable flows |

---

## Walkthrough Simulation Target

The plan must prove one full single-agent journey that already fits the future team-ready model.

| Step | Actor | Current surface | What must be true after implementation |
|---|---|---|---|
| 1 | PP user | `GenesisConsole`, `AgentTypeSetupScreen`, `AgentManagement`, `agent_setups.py`, `genesis.py` | PP user can define skills, bind components, set constraints, and see readiness in one flow |
| 2 | PP user | `agent_mold.py`, `HiredAgentsOps.tsx`, `ops_hired_agents.py` | PP user can run a safe draft simulation that produces a SkillRun and output preview without publishing externally |
| 3 | PP user | `AgentManagement.tsx`, `agent_setups.py` | PP user can publish the agent type for hiring only when required bindings, policies, and hooks are valid |
| 4 | Customer | `AgentDiscovery.tsx`, `AgentDetail.tsx`, mobile `DiscoverScreen`, `AgentDetailScreen` | Customer sees a clean hiring story centered on what the agent does, what skills it has, and what setup is required |
| 5 | Customer | `HireSetupWizard.tsx`, mobile `HireWizardScreen`, CP `hire_wizard.py` | Customer can hire a single agent that is internally wrapped as Team(1) + Role(1) + Agent(1) |
| 6 | Customer | `MyAgents.tsx`, `SkillsPanel.tsx`, mobile `MyAgentsScreen`, `AgentOperationsScreen` | Customer can configure goals, connections, and approval preferences at the skill level |
| 7 | Plant runtime | `hired_agents_simple.py`, `agent_skills.py`, `skill_configs.py`, `approvals.py` | Skill runs move through reusable components, record outputs, and pause at approval gates where required |
| 8 | Customer | CP approvals and mobile approval queue | Customer can approve content drafts or trade plans and then see results and receipts in both CP and mobile |

### Walkthrough Simulation — Reference Scenario

The reference walkthrough for acceptance should be a single customer hiring one content agent with two skills.

| Layer | Example |
|---|---|
| Team | `Team(1)` created implicitly for the hire |
| Role | `primary_operator` |
| Agent | `marketing.content_operator.v1` |
| Skill 1 | Content Creation |
| Skill 2 | Content Publishing |
| Components reused | Scheduler, Input Loader, Config Resolver, Validator, Approval Gate, Connector, Result Recorder |

This same structure must also be able to host a Share Trader later with a different Processor, Validator, and Connector flavor.

### Walkthrough Simulation — PP, CP, and Mobile Proof Runs

#### Simulation A — PP platform team member daily workflow

| Step | Screen or route | Expected behavior |
|---|---|---|
| 1 | PP `AgentTypeSetupScreen.tsx` + `PUT /pp/agent-setups` | platform user defines agent identity, construct bindings, and constraint policy in one place |
| 2 | Plant `POST /api/v1/agent-mold/spec/validate` | PP sees whether the setup is structurally valid |
| 3 | New PP draft simulation action | PP runs a safe SkillRun preview without external publish or trade execution |
| 4 | PP `AgentManagement.tsx` | PP sees readiness and either block reasons or publish-for-hire action |
| 5 | PP `HiredAgentsOps.tsx` | after customers hire, PP monitors health, approvals, diagnostics, and policy denials |

#### Simulation B — CP paying customer workflow

| Step | Screen or route | Expected behavior |
|---|---|---|
| 1 | CP `AgentDiscovery.tsx` / `AgentDetail.tsx` | customer understands the agent as a bundle of skills with clear outcomes |
| 2 | CP `HireSetupWizard.tsx` + `hire_wizard.py` | customer sets nickname, connections, goals, and approval preference |
| 3 | payment and finalize route | customer completes paid hire or trial start without seeing team complexity |
| 4 | CP `MyAgents.tsx` + `SkillsPanel.tsx` | customer configures skill-level settings and sees runtime outputs |
| 5 | CP approval queue routes | customer approves content drafts or trade plans and then sees resulting deliverables |

#### Simulation C — Mobile customer workflow

| Step | Screen or route | Expected behavior |
|---|---|---|
| 1 | mobile `DiscoverScreen` / `AgentDetailScreen` | customer discovers and starts hire from phone |
| 2 | mobile `HireWizardScreen` | customer completes lightweight setup flow |
| 3 | mobile `MyAgentsScreen` | customer sees active trials and hired agents with clear next actions |
| 4 | mobile `AgentOperationsScreen` | customer handles approvals, scheduler actions, and recent outputs |
| 5 | mobile approval queue hooks | customer can approve urgent items from mobile and trust that CP reflects the same state |

#### Proof standard

This plan is only considered proven when these three simulations are coherent without inventing separate business logic for PP, CP, and mobile. All three must sit on the same Plant runtime contracts.

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Plant contract fit + PP authoring, simulation, and publish-for-hire flow | 2 | 4 | 6h | 2026-03-11 11:00 UTC |
| 2 | CP/mobile runtime fit + walkthrough validation + rollout gates | 2 | 4 | 6h | 2026-03-12 11:00 UTC |

**Estimate basis:** schema and new Plant route = 45 min, PP or CP wiring = 30-45 min, mobile parity = 45 min, end-to-end validation = 60 min.

---

## Dependency Map

| Order | Why |
|---|---|
| Plant runtime first | All surfaces depend on the runtime vocabulary and durable route contracts |
| PP next | PP is the authoring and publish gate for platform users |
| CP next | CP is the primary customer web runtime |
| Mobile last | Mobile should inherit the stabilized CP/runtime contracts, not invent its own |

---

## Iteration 1 — Plant Fit + PP Authoring/Test/Publish

**Outcome:** the platform user can define a single-agent-first agent type using reusable skills and components, run a safe simulation, and publish it for hiring.

### E1 — Fit the Plant runtime to the new Team -> Role -> Agent -> Skill -> Component model

**Outcome:** Plant keeps current single-agent behavior, but the runtime becomes compatible with a dormant Team/Role envelope and explicit publishability checks.

#### Story E1-S1 — Add dormant Team and Role runtime fit to single-agent hire lifecycle

| Field | Value |
|---|---|
| Branch | `feat/AGENT-WORKFORCE-1-it1-e1` |
| BLOCKED UNTIL | none |
| Files to read first | `src/Plant/BackEnd/api/v1/hired_agents_simple.py`, `src/Plant/BackEnd/models/team.py`, `src/Plant/BackEnd/models/job_role.py` |
| Files to create / modify | `src/Plant/BackEnd/api/v1/hired_agents_simple.py`, `src/Plant/BackEnd/models/hired_agent.py`, `src/Plant/BackEnd/database/migrations/`, `src/Plant/BackEnd/tests/unit/test_hired_agents_api.py` |
| Change | Every finalized single-agent hire stores optional `team_id` and `role_id`, with defaults that model Team(1) and Role(1) without changing the customer-facing hire flow |
| Acceptance | finalize response includes team and role fields; existing hire flows still work; GET routes expose the fields; no UI breakage |
| Test command | `docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest src/Plant/BackEnd/tests/unit/test_hired_agents_api.py -x -v` |

#### Story E1-S2 — Add publishability and construct-readiness contract to Plant agent mold

| Field | Value |
|---|---|
| Branch | `feat/AGENT-WORKFORCE-1-it1-e1` |
| BLOCKED UNTIL | E1-S1 merged |
| Files to read first | `src/Plant/BackEnd/agent_mold/spec.py`, `src/Plant/BackEnd/api/v1/agent_mold.py`, `src/Plant/BackEnd/agent_mold/contracts.py` |
| Files to create / modify | `src/Plant/BackEnd/agent_mold/spec.py`, `src/Plant/BackEnd/api/v1/agent_mold.py`, `src/Plant/BackEnd/tests/unit/test_agent_mold_enforcement_api.py` |
| Change | Add a readiness contract that reports whether an agent type is safe to publish for hire based on required processor, validator, connector, approval mode, and hooks |
| Acceptance | Plant exposes readiness reasons as structured JSON; missing pieces return actionable readiness failures; existing spec validation still passes |
| Test command | `docker compose -f docker-compose.test.yml run --rm plant-backend-test pytest src/Plant/BackEnd/tests/unit/test_agent_mold_enforcement_api.py -x -v` |

### E2 — Make PP the coherent authoring, simulation, and publish surface

**Outcome:** PP user gets one working flow to define, simulate, and publish an agent type.

#### Story E2-S1 — Stitch PP setup screens to construct readiness and draft simulation

| Field | Value |
|---|---|
| Branch | `feat/AGENT-WORKFORCE-1-it1-e2` |
| BLOCKED UNTIL | E1-S2 merged |
| Files to read first | `src/PP/FrontEnd/src/pages/AgentTypeSetupScreen.tsx`, `src/PP/FrontEnd/src/services/useAgentTypeSetup.ts`, `src/PP/BackEnd/api/agent_setups.py` |
| Files to create / modify | `src/PP/FrontEnd/src/pages/AgentTypeSetupScreen.tsx`, `src/PP/FrontEnd/src/services/useAgentTypeSetup.ts`, `src/PP/BackEnd/api/agent_setups.py`, `src/PP/BackEnd/tests/test_agent_setups.py` |
| Change | PP setup screen shows construct readiness and adds a test-simulation action that calls Plant through PP without publishing externally |
| Acceptance | PP user can save setup, read readiness, and trigger test run preview; audit emitted; failures visible inline |
| Test command | `docker compose -f docker-compose.test.yml run --rm pp-backend-test pytest src/PP/BackEnd/tests/test_agent_setups.py -x -v` |

#### Story E2-S2 — Add publish-for-hire gate in PP Agent Management

| Field | Value |
|---|---|
| Branch | `feat/AGENT-WORKFORCE-1-it1-e2` |
| BLOCKED UNTIL | E2-S1 merged |
| Files to read first | `src/PP/FrontEnd/src/pages/AgentManagement.tsx`, `src/PP/FrontEnd/src/App.tsx`, `src/PP/BackEnd/api/genesis.py` |
| Files to create / modify | `src/PP/FrontEnd/src/pages/AgentManagement.tsx`, `src/PP/FrontEnd/src/App.tsx`, `src/PP/BackEnd/api/genesis.py`, `src/PP/FrontEnd/src/__tests__/AgentManagement.test.tsx` |
| Change | Publish button becomes a guarded action: only ready agent types can be published for hire; PP shows why a type is blocked |
| Acceptance | blocked publish shows readiness reasons; ready publish marks the type as hireable; PP navigation exposes the full lifecycle cleanly |
| Test command | `docker compose -f docker-compose.test.yml run --rm pp-frontend-test npm test -- AgentManagement.test.tsx` |

---

## Iteration 2 — CP/Mobile Runtime Fit + Walkthrough Validation

**Outcome:** the customer can discover, hire, configure, approve, and operate the new single-agent-first runtime from CP and mobile using the same platform contracts.

### E3 — Fit CP to skill-centric customer runtime without breaking current flows

**Outcome:** CP keeps the existing marketplace feel, but it speaks the new runtime model more clearly.

#### Story E3-S1 — Align CP backend summary and skill routes to runtime vocabulary

| Field | Value |
|---|---|
| Branch | `feat/AGENT-WORKFORCE-1-it2-e3` |
| BLOCKED UNTIL | Iteration 1 merged |
| Pattern | CP BackEnd pattern A — existing `/cp/*` routes proxy to Plant via thin CP layer |
| Files to read first | `src/CP/BackEnd/api/my_agents_summary.py`, `src/CP/BackEnd/api/cp_skills.py`, `src/CP/BackEnd/main.py` |
| Files to create / modify | `src/CP/BackEnd/api/my_agents_summary.py`, `src/CP/BackEnd/api/cp_skills.py`, `src/CP/BackEnd/tests/test_my_agents_summary.py`, `src/CP/BackEnd/tests/test_cp_skills.py` |
| Change | Summaries and skill routes expose skill-centric fields, publishability state, team/role envelope fields, and a durable approval queue contract |
| Acceptance | CP can read current hired agents, skills, approvals, and new runtime fields without changing auth flow; all reads stay read-only where appropriate |
| Test command | `docker compose -f docker-compose.test.yml run --rm cp-backend-test pytest src/CP/BackEnd/tests/test_my_agents_summary.py src/CP/BackEnd/tests/test_cp_skills.py -x -v` |

#### Story E3-S2 — Align CP discovery, hire, and My Agents walkthrough

| Field | Value |
|---|---|
| Branch | `feat/AGENT-WORKFORCE-1-it2-e3` |
| BLOCKED UNTIL | E3-S1 merged |
| Files to read first | `src/CP/FrontEnd/src/pages/AgentDiscovery.tsx`, `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx`, `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx` |
| Files to create / modify | `src/CP/FrontEnd/src/pages/AgentDiscovery.tsx`, `src/CP/FrontEnd/src/pages/AgentDetail.tsx`, `src/CP/FrontEnd/src/pages/HireSetupWizard.tsx`, `src/CP/FrontEnd/src/pages/authenticated/MyAgents.tsx`, `src/CP/FrontEnd/src/components/SkillsPanel.tsx` |
| Change | Keep marketplace DNA, but make the customer journey explicitly explain agent skills, required setup, approval mode, and post-hire operations |
| Acceptance | customer can understand what is being hired, what each skill does, and what approvals will happen later; My Agents surfaces skill-level configuration and outputs clearly |
| Test command | `docker compose -f docker-compose.test.yml run --rm cp-frontend-test npm test -- MyAgents` |

### E4 — Bring mobile to the same runtime story and prove the full walkthrough

**Outcome:** mobile works as a smaller surface over the same single-agent runtime model.

#### Story E4-S1 — Align mobile discover, hire, and operations routing

| Field | Value |
|---|---|
| Branch | `feat/AGENT-WORKFORCE-1-it2-e4` |
| BLOCKED UNTIL | E3-S2 merged |
| Files to read first | `src/mobile/src/screens/discover/AgentDetailScreen.tsx`, `src/mobile/src/screens/hire/HireWizardScreen.tsx`, `src/mobile/src/screens/agents/MyAgentsScreen.tsx` |
| Files to create / modify | `src/mobile/src/screens/discover/AgentDetailScreen.tsx`, `src/mobile/src/screens/hire/HireWizardScreen.tsx`, `src/mobile/src/screens/agents/MyAgentsScreen.tsx`, `src/mobile/src/screens/agents/AgentOperationsScreen.tsx`, `src/mobile/src/hooks/useHiredAgents.ts`, `src/mobile/src/navigation/types.ts` |
| Change | mobile shows the same hire and operate story as CP: what the agent does, what setup is required, what approvals are pending, and what happened after approval |
| Acceptance | hired agents route to the correct operations screen, not generic detail; approvals and operations reflect the same CP contract |
| Test command | `docker compose -f docker-compose.test.yml run --rm mobile-test npm test -- MyAgentsScreen AgentOperationsScreen` |

#### Story E4-S2 — Walkthrough proof, rollout flags, and release gate

| Field | Value |
|---|---|
| Branch | `feat/AGENT-WORKFORCE-1-it2-e4` |
| BLOCKED UNTIL | E4-S1 merged |
| Files to read first | `docs/WAOOAW Design.md`, `docs/plant/iterations/AGENT-WORKFORCE-1-single-agent-first-platform-fit.md`, `src/CP/BackEnd/api/feature_flag_dependency.py` |
| Files to create / modify | `docs/WAOOAW Design.md`, `docs/plant/iterations/AGENT-WORKFORCE-1-single-agent-first-platform-fit.md`, `src/CP/BackEnd/api/feature_flag_dependency.py`, `src/Plant/BackEnd/api/v1/feature_flag_dependency.py`, relevant Terraform env wiring files if new flags are added |
| Change | document the proven walkthrough, add rollout flags for the new single-agent-first runtime path, and lock the release gate criteria |
| Acceptance | the platform can enable the new runtime path safely behind flags; the walkthrough is documented with exact PP -> CP/mobile -> Plant steps; plan is updated with actual PR outcomes |
| Test command | `docker compose -f docker-compose.test.yml run --rm cp-backend-test pytest src/CP/BackEnd/tests/ -k feature_flag -x -v` |

---

## Release Gate

The implementation is not ready to ship until all of these are true.

| Gate | Required proof |
|---|---|
| Plant runtime fit | hired agent can carry team and role envelope fields without breaking current flows |
| PP authoring | platform user can save setup, see readiness, simulate, and publish |
| CP runtime | customer can discover, hire, configure, and approve |
| Mobile runtime | customer can hire, inspect, and operate the same hired agent |
| Approval flow | content and trading skill runs pause and resume correctly |
| Flags | new path can be enabled or disabled safely |
| Docs | final walkthrough is recorded and exact route ownership is clear |

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

---

## Tracking Table

| Story | Status | Notes |
|---|---|---|
| E1-S1 | planned | dormant Team/Role runtime envelope |
| E1-S2 | planned | publishability and construct readiness |
| E2-S1 | planned | PP setup + draft simulation stitch |
| E2-S2 | planned | PP publish-for-hire gate |
| E3-S1 | planned | CP backend runtime vocabulary fit |
| E3-S2 | planned | CP discovery/hire/my-agents walkthrough fit |
| E4-S1 | planned | mobile runtime parity |
| E4-S2 | planned | walkthrough proof + rollout gate |
