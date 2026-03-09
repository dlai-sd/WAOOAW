# PP-MOBILE-DEFECTS-1 — Systematic Audit And Fix Program

> **Status**: Discovery in progress  
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
| 3. Fix bundle | Implement all approved PP + Mobile fixes together | Code and tests updated |
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
| DEF-PM-001 | Mobile | High | `src/mobile/src/services/hiredAgents/hiredAgents.service.ts` → My Agents summary + hired-agent detail flows | CP-backed routes (`/cp/my-agents/summary`, `/cp/hired-agents/by-subscription/{id}`) are called through `apiClient`, whose base URL comes from `apiBaseUrl` (`plant.*`), while the dedicated `cpApiClient` exists but is unused | Core My Agents and hired-agent detail flows are sent to the wrong service host and can 404 or bypass CP-specific behavior | Switch CP-backed hired-agent service calls to `cpApiClient` and keep Plant-only calls on `apiClient` | Open |
| DEF-PM-002 | Mobile | High | `src/mobile/src/hooks/useApprovalQueue.ts` and `src/mobile/src/screens/agents/AgentOperationsScreen.tsx` | Approval queue and pause/resume CP routes are also sent through `apiClient` instead of `cpApiClient` | Pending approvals and scheduler actions in mobile operations screens target the wrong backend host | Move all `/cp/...` mobile calls to `cpApiClient`; keep Plant calls on `apiClient` | Open |
| DEF-PM-003 | Mobile | High | `src/mobile/src/screens/agents/AgentOperationsScreen.tsx`, `src/mobile/src/navigation/types.ts`, `src/mobile/src/screens/profile/NotificationsScreen.tsx` | `AgentOperationsScreen` receives `hiredAgentId` but passes it into `useHiredAgent()`, which is explicitly a subscription-based hook that calls `/cp/hired-agents/by-subscription/{subscriptionId}` | Operations screen can fetch the wrong record or 404 because a hired-instance id is used where a subscription id is required | Add a hired-agent-by-id mobile fetch path or pass subscription id consistently into this screen and all deep links | Open |
| DEF-PM-004 | Mobile | High | `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` → approval queue | `TrialDashboardScreen` passes `trialId` (documented and typed as `subscription_id`) into `useApprovalQueue()`, which builds `/cp/hired-agents/{hiredAgentId}/approval-queue` paths that require a hired-instance id | Trial dashboard approval fetch, approve, and reject actions are called with the wrong identifier and can fail even if the CP route is healthy | Resolve the hired-instance id first from the loaded hired-agent record, then pass that value to the approval queue hook | Open |
| DEF-PM-005 | Mobile | High | `src/mobile/src/hooks/useHiredAgents.ts` → `useDeliverables()` / `src/mobile/src/screens/agents/TrialDashboardScreen.tsx` | Deliverables are fetched from `GET /api/v1/deliverables?subscription_id=...`, but current Plant routes only expose hired-agent-scoped deliverables at `GET /api/v1/hired-agents/{hired_instance_id}/deliverables` plus item actions under `/api/v1/deliverables/{id}/...` | Trial dashboard deliverables section points at a route shape that does not exist in the current backend surface | Rewire deliverables loading to use the hired-instance id and the hired-agent-scoped deliverables endpoint, likely through CP or the correct Plant path | Open |
| DEF-PM-006 | Mobile | Medium | `src/mobile/src/screens/hire/HireConfirmationScreen.tsx` | `handleGoToTrialDashboard()` navigates with `{ agentId }`, but navigation types and `TrialDashboardScreen` require `{ trialId }` | Post-hire success flow can navigate into the trial dashboard with the wrong param contract, breaking screen load or forcing fallback behavior | Pass the real `subscription_id` / trial id into navigation and align the screen params with the route type | Open |
| DEF-PM-007 | Mobile tests / config | Medium | `src/mobile/__tests__/integration/api.test.ts` vs `src/mobile/src/config/api.config.ts` | The integration test refers to a non-existent `apiConfig` export and assumes one CP-only base URL, while runtime config now has separate `apiBaseUrl` and `cpApiBaseUrl` | Mobile API integration tests are stale and cannot validate the actual split-client architecture | Update the test asset to assert the current dual-client config and the intended host per route family | Open |

---

## Repair Bundle Plan

| Wave | Scope | Files | Tests | Status |
|---|---|---|---|---|
| Pending | To be defined after discovery | TBD | TBD | Not started |

---

## Progress Log

| Timestamp | Update |
|---|---|
| 2026-03-09 | Created program tracker and branch. Discovery will begin with PP and Mobile surface mapping. |
| 2026-03-09 | First discovery wave completed. Verified seven mobile defects centered on wrong client selection, wrong identifier handoff, and stale test/config assumptions. PP ops slice inspected so far shows no verified defect yet. |
