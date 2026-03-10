# PP-MOBILE-DEFECTS-1 — Systematic Audit And Fix Program

> **Status**: Mobile repair wave 1 validated  
> **Branch**: `fix/pp-mobile-defect-program`  
> **Created**: 2026-03-09  
> **Author**: GitHub Copilot

---

## Objective

Systematically inspect PP and Mobile surfaces of the WAOOAW platform, record verified defects in one durable place, and then apply the fixes as one coordinated repair bundle after discovery is complete.

This document is the live operating log for the program. If the session disconnects, resume from this file first.

---

## Scope

| Surface | In scope | Primary goal |
|---|---|---|
| PP FrontEnd | Yes | Verify screen wiring, service contracts, and admin/operator flows |
| PP BackEnd | Yes | Verify route correctness, Plant/Gateway proxy targets, validation, and payload shapes |
| Mobile app | Yes | Verify service calls, CP/Gateway/Plant contract usage, and runtime flow integrity |
| Plant / Gateway | Conditional | Only when a PP or Mobile defect is caused upstream |
| CP FrontEnd / CP BackEnd | No | Already addressed in separate work unless directly required for mobile defect root cause |

---

## Working Method

| Phase | Description | Exit condition |
|---|---|---|
| 1. Surface mapping | Identify the exact PP and Mobile entrypoints, services, proxies, and tests | Canonical file set is listed in this document |
| 2. Defect discovery | Inspect routes, payload contracts, and flow wiring; record only verified defects | Findings table is complete enough to fix in one batch |
| 3. Fix bundle | Implement the approved mobile repair bundle | Code and tests updated |
| 4. Validation | Run targeted tests and summarize remaining risk | Repair bundle is ready for PR review |

---

## Checkpoint Rules

1. Update this file after each discovery wave or repair wave.
2. Commit and push this file before starting a new wave of work.
3. Keep findings factual: file path, route/screen, root cause, impact, best fix.
4. Do not mark a defect as verified unless the relevant code path has been read.
5. Do not start the fix bundle until the current discovery pass is summarized in the findings table.

---

## Discovery Inventory

| Area | Status | Canonical entrypoints | Notes |
|---|---|---|---|
| PP FrontEnd | In progress | `src/PP/FrontEnd/src/services/gatewayApiClient.ts`, `src/PP/FrontEnd/src/pages/HiredAgentsOps.tsx`, `src/PP/FrontEnd/src/pages/ApprovalsQueueScreen.tsx` | First-pass ops screens align with current PP backend surface; no verified defect yet in this slice |
| PP BackEnd | In progress | `src/PP/BackEnd/api/ops_subscriptions.py`, `src/PP/BackEnd/api/ops_hired_agents.py`, `src/PP/BackEnd/api/ops_dlq.py`, `src/PP/BackEnd/api/approvals.py` | Current ops proxy paths inspected so far are consistent with current Plant routes |
| Mobile app | In progress | `src/mobile/src/lib/apiClient.ts`, `src/mobile/src/lib/cpApiClient.ts`, `src/mobile/src/services/hiredAgents/hiredAgents.service.ts`, `src/mobile/src/hooks/useHiredAgents.ts`, `src/mobile/src/hooks/useApprovalQueue.ts`, `src/mobile/src/screens/agents/TrialDashboardScreen.tsx`, `src/mobile/src/screens/agents/AgentOperationsScreen.tsx`, `src/mobile/src/screens/hire/HireConfirmationScreen.tsx` | Verified defects cluster around wrong client selection and wrong identifier handoff |
| Shared upstream dependencies | In progress | `src/Plant/BackEnd/api/v1/hired_agents_simple.py`, `src/Plant/BackEnd/api/v1/deliverables_simple.py`, `src/Plant/BackEnd/api/v1/customers.py` | Used to verify whether suspected PP/mobile paths exist upstream |

---

## Verified Findings

| ID | Surface | Severity | File / flow | Root cause | Impact | Best fix | Status |
|---|---|---|---|---|---|---|---|
| DEF-PM-001 | Mobile | High | `src/mobile/src/services/hiredAgents/hiredAgents.service.ts` → My Agents summary + hired-agent detail flows | CP-backed routes (`/cp/my-agents/summary`, `/cp/hired-agents/by-subscription/{id}`) were called through `apiClient` instead of `cpApiClient` | Core My Agents and hired-agent detail flows targeted the wrong service host | CP-backed hired-agent service calls were switched to `cpApiClient`, while Plant-only calls stayed on `apiClient` | Fixed |
| DEF-PM-002 | Mobile | High | `src/mobile/src/hooks/useApprovalQueue.ts` and `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | Approval queue and pause/resume CP routes were sent through `apiClient` instead of `cpApiClient` | Pending approvals and scheduler actions in mobile operations screens targeted the wrong backend host | All `/cp/...` mobile calls in this slice now use `cpApiClient` | Fixed |
| DEF-PM-003 | Mobile | High | `src/mobile/src/screens/agents/AgentOperationsScreen.tsx`, `src/mobile/src/navigation/types.ts`, `src/mobile/src/screens/profile/NotificationsScreen.tsx` | `AgentOperationsScreen` received a hired-instance id but used the subscription-based `useHiredAgent()` hook | Operations screen could fetch the wrong record or 404 | Added a hired-agent-by-id mobile fetch path and rewired the screen to use it | Fixed |
| DEF-PM-004 | Mobile | High | `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` → approval queue | `TrialDashboardScreen` passed `trialId` / subscription id into `useApprovalQueue()`, which requires a hired-instance id | Trial dashboard approval fetch, approve, and reject actions used the wrong identifier | The screen now resolves the hired-instance id from the loaded hired-agent record before invoking the approval queue hook | Fixed |
| DEF-PM-005 | Mobile | High | `src/mobile/src/hooks/useHiredAgents.ts` → `useDeliverables()` / `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` | Deliverables were fetched from a subscription-scoped route shape that does not exist in the current backend surface | Trial dashboard deliverables section targeted the wrong route family | Deliverables loading now uses the hired-instance id and the CP hired-agent deliverables endpoint | Fixed |
| DEF-PM-006 | Mobile | Medium | `src/mobile/src/screens/hire/HireConfirmationScreen.tsx` | `handleGoToTrialDashboard()` navigated with `{ agentId }` instead of `{ trialId }` | Post-hire success flow could enter the dashboard with the wrong param contract | The hire flow now forwards `subscription_id` / `trialId` through confirmation into the dashboard navigation path | Fixed |
| DEF-PM-007 | Mobile tests / config | Medium | `src/mobile/__tests__/integration/api.test.ts` vs `src/mobile/src/config/api.config.ts` | The integration test assumed a single `apiConfig` export instead of the split `apiBaseUrl` and `cpApiBaseUrl` model | Mobile API integration tests no longer validated the actual runtime config shape | The test asset now validates the split-client config and the intended CP vs Plant host separation | Fixed |

---

## Repair Bundle Plan

| Wave | Scope | Files | Tests | Status |
|---|---|---|---|---|
| 1 | Mobile client split, identifier handoff, and stale tests | `src/mobile/src/services/hiredAgents/hiredAgents.service.ts`, `src/mobile/src/hooks/useHiredAgents.ts`, `src/mobile/src/hooks/useApprovalQueue.ts`, `src/mobile/src/screens/agents/AgentOperationsScreen.tsx`, `src/mobile/src/screens/agents/TrialDashboardScreen.tsx`, `src/mobile/src/screens/hire/HireConfirmationScreen.tsx`, `src/mobile/src/screens/hire/HireWizardScreen.tsx`, `src/mobile/__tests__/AgentOperationsScreen.test.tsx`, `src/mobile/__tests__/hireConfirmationScreen.test.tsx`, `src/mobile/__tests__/hiredAgentsHooks.test.tsx`, `src/mobile/__tests__/hiredAgentsService.test.ts`, `src/mobile/__tests__/integration/api.test.ts` | `docker compose -f /workspaces/WAOOAW/docker-compose.mobile.yml run --rm mobile-typecheck`; `docker compose -f /workspaces/WAOOAW/docker-compose.mobile.yml run --rm mobile-test npm test -- --runInBand --runTestsByPath __tests__/AgentOperationsScreen.test.tsx __tests__/hireConfirmationScreen.test.tsx __tests__/hiredAgentsHooks.test.tsx __tests__/hiredAgentsService.test.ts __tests__/integration/api.test.ts` | Validated |

---

## Progress Log

| Timestamp | Update |
|---|---|
| 2026-03-09 | Created program tracker and branch. Discovery will begin with PP and Mobile surface mapping. |
| 2026-03-09 | First discovery wave completed. Verified seven mobile defects centered on wrong client selection, wrong identifier handoff, and stale test/config assumptions. PP ops slice inspected so far shows no verified defect yet. |
| 2026-03-10 | Mobile repair wave 1 completed. Docker mobile typecheck passed, and the focused Jest subset for the touched mobile service/hooks/screens/tests passed after updating stale client mocks in the test assets. |
