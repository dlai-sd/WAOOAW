# Evolution Proposal 001: Team Agent Coordination & Manager Agents

**Proposal ID:** EVOLUTION-001  
**Submission Date:** 2026-01-06  
**Submitting Agent:** Systems Architect (on behalf of Platform Governor)  
**Type:** Evolution (increases execution scope + adds agent types + changes approval boundaries)  
**Status:** ✅ APPROVED  
**Approval Date:** 2026-01-06  
**Approved By:** Platform Governor  
**Precedent Seed:** GEN-002 (created)  

---

## Executive Summary

**Current State:** WaooaW platform supports individual agents operating independently under customer Governor approval.

**Proposed State:** Add team-based agent coordination with Manager Agent role, enabling pre-packaged agent teams (e.g., "Digital Marketing Team") that collaborate on customer goals.

**Business Rationale:** 
- Customers want workforce solutions, not isolated tools
- Mid-size orgs need functional teams (marketing, sales) not individual agents
- Team value proposition: "try entire team before you hire"
- Revenue model: team bundles (₹30-60K/month) vs individual agents (₹8-25K/month)

**Constitutional Classification:** **EVOLUTION** because:
1. ✅ Increases execution scope (manager agent coordinates team members)
2. ✅ Adds new agent type (manager agent with delegation authority)
3. ✅ Changes approval boundaries (team outputs vs individual agent outputs)
4. ✅ Expands data access (team shared context)

---

## 1. Outcome Definition

**Success Criteria:**
- Customer can hire pre-packaged team (e.g., "Digital Marketing Team = 1 manager + 4 specialists")
- Manager agent delegates tasks to team members, reviews outputs, requests customer approval
- Team members collaborate via shared context (team workspace)
- Customer Governor approves team outputs (not individual agent actions)
- Team trial succeeds: deliverables produced by team, customer keeps outputs even if cancels
- Mobile app enables small customers to approve team outputs via push notifications

**Closure Conditions:**
- First team deployed to customer with trial success
- Team coordination proven via audit trail (manager→member→output)
- Team failure handled gracefully (helpdesk mode on manager suspension)
- Mobile approvals working (iOS + Android apps)

---

## 2. Scope Boundaries

**In Scope:**
- New agent type: Manager Agent (L3 agent with delegation authority)
- Team coordination protocol (message bus team-internal topics)
- Team shared context (database team_workspaces table)
- Team governance boundary (team approval flow: member→manager→customer_governor)
- Helpdesk mode (degraded operation when manager suspended)
- Mobile-first UX (approval flows, push notifications)
- Team pricing model (bundles with discount)
- Team trial success criteria

**Out of Scope (defer to future):**
- Dynamic team assembly (customer picks agents to form custom team) — MVP uses fixed bundles only
- Multi-team coordination (customer has 2+ teams working together) — single team per customer MVP
- Manager agent learning (improve delegation over time) — defer to post-MVP
- Enterprise features (team analytics, performance dashboards) — defer to tier 2+

**Refusal Classes:**
- Manager agent CANNOT approve external execution/communication (only internal delegation)
- Manager agent CANNOT access other teams' contexts (strict isolation)
- Team members CANNOT bypass manager approval (no direct customer communication)
- Helpdesk agent CANNOT execute work on behalf of team (only communication)

---

## 3. Required Inputs

**From Platform Governor:**
- Approval of Evolution proposal (this document)
- Approval of team pricing model (₹30-60K/month bundles)
- Approval of mobile app scope (MVP features)

**From Genesis:**
- Certification of Manager Agent Way of Working (ME-WoW)
- Certification of Helpdesk Agent Way of Working

**From Systems Architect:**
- Review of team coordination architecture
- Review of shared context isolation strategy
- Cost/performance impact assessment

**From Vision Guardian:**
- Constitutional alignment check
- Ethics review of manager delegation authority
- Mobile approval governance review

**Evidence Quality:**
- Simulation proof of team coordination flows
- Cost breakdown showing budget compliance
- Mobile UX mockups for approval flows

---

## 4. Outputs and Artifacts

**Governance Documents:**
- `manager_agent_charter.md` (L3 agent charter, similar to genesis/architect/vision_guardian)
- `helpdesk_agent_charter.md` (platform-level continuity agent)
- `team_coordination_protocol.yml` (message bus topics, delegation flows)
- `team_governance_policy.yml` (approval boundaries, shared context rules)
- `mobile_ux_requirements.yml` (MVP features, push notifications)

**Data Contracts:**
- `team_workspace_schema` (shared context storage)
- `manager_delegation_event` (task assignment messages)
- `team_approval_request` (manager→customer_governor)
- `helpdesk_interaction` (customer↔helpdesk agent)

**Code Artifacts:**
- Manager Agent service (Cloud Run)
- Helpdesk Agent service (Cloud Run)
- Team coordination orchestrator (extends agent_creation_orchestration.yml)
- Mobile app (Flutter iOS/Android)
- Team pricing calculator

**Test Artifacts:**
- Simulation: team coordination flows (5 scenarios)
- Integration test: manager delegates to 3 team members
- Mobile approval test: push notification → approve → audit entry

---

## 5. Interfaces (Read/Write)

**Read Interfaces:**
- Manager Agent reads:
  - Customer goal (from customer_governor)
  - Team member outputs (from team workspace)
  - Team member status (from health_events topic)
  - Precedent seeds (delegation patterns)

- Team Member reads:
  - Task assignment (from manager via team.{team_id}.task_assignment topic)
  - Team shared context (from team_workspaces table)
  - Approval decisions (from manager via team.{team_id}.draft_review topic)

**Write Interfaces:**
- Manager Agent writes:
  - Task assignments (to team.{team_id}.task_assignment topic)
  - Draft reviews (to team.{team_id}.draft_review topic)
  - Approval requests (to approvals topic → customer_governor)
  - Team status updates (to team.{team_id}.status_update topic)

- Team Member writes:
  - Draft outputs (to team workspace)
  - Status updates (to team.{team_id}.status_update topic)
  - Completion signals (to manager via draft_review topic)

**External Interfaces (New):**
- Mobile app → API Gateway (OAuth2, approvals API)
- Firebase Cloud Messaging → Mobile app (push notifications)

---

## 6. Decision Rights

**Manager Agent Decides:**
- Task breakdown (customer goal → subtasks)
- Task assignment (which team member does what)
- Internal approval (draft quality, ready for customer review)
- Revision requests (send back to team member for changes)
- Team member performance (recommend suspension to Genesis)

**Manager Agent CANNOT Decide:**
- External execution (requires customer Governor approval)
- External communication (requires customer Governor approval)
- Budget allocation (platform Governor sets team budget)
- Team composition (Genesis certifies team manifest)
- Policy exceptions (Vision Guardian authority)

**Customer Governor Decides:**
- Approve/deny team outputs for external communication/execution
- Approve team trial-to-production promotion
- Suspend team operations
- Cancel subscription

**Platform Governor Decides:**
- Approve team bundles (composition, pricing)
- Approve helpdesk mode activation
- Approve mobile app release

---

## 7. Critique & Self-Examination

**Assumptions:**
- ⚠️ Assume manager agent can effectively coordinate 4-7 team members (untested at scale)
- ⚠️ Assume team shared context doesn't create security vulnerabilities (isolation must be perfect)
- ⚠️ Assume mobile app UX sufficient for approval flows (need user testing)
- ⚠️ Assume helpdesk mode acceptable to customers (may expect full refund instead)

**Failure Modes:**
- Manager agent fails → team suspended, customer experiences service interruption
- Team member leaks data to another team → customer data breach
- Mobile push notification fails → customer misses approval deadline
- Team coordination overhead → slower than individual agents
- Shared context conflicts → two team members edit same artifact

**Mitigation Strategies:**
- Manager failure → helpdesk mode (continuity)
- Data isolation → strict DB row-level security per team_id
- Push notification failure → fallback to email + SMS
- Coordination overhead → manager agent optimizes delegation via precedent seeds
- Conflict resolution → optimistic locking + last-write-wins with audit trail

---

## 8. Escalation Triggers

**Escalate to Genesis:**
- Manager agent exceeds delegation authority (tries to execute externally)
- Team composition change requested (add/remove members)
- Team member consistently fails quality reviews

**Escalate to Systems Architect:**
- Team coordination latency >10s (architecture bottleneck)
- Shared context storage >1GB per team (cost concern)
- Mobile API latency >500ms (UX degradation)

**Escalate to Vision Guardian:**
- Manager agent delegation patterns show bias (always assigns hard tasks to same member)
- Team outputs show quality degradation over time (learning failure)
- Mobile approval flow bypasses audit (constitutional violation)

**Escalate to Customer Governor:**
- Team deliverable ready for external communication/execution
- Team trial ends (promotion decision)
- Manager agent suspended (service interruption)

**Escalate to Platform Governor:**
- Team cost exceeds budget (₹60K/month bundle generates >$100 platform cost)
- Multiple teams request same architectural change (systemic issue)
- Mobile app store rejection (deployment blocker)

---

## 9. Safety Containment Posture

**Default State:** Non-executing

**Manager Agent:**
- Starts in "coordination-only" mode (cannot delegate until certified)
- Delegation messages logged to audit before sending
- External execution requests blocked until customer Governor approves
- Suspension triggers: unauthorized execution attempt, ethics violation, performance failure

**Team Member:**
- Operates under manager supervision (cannot communicate directly with customer)
- Outputs go to team workspace (not directly to customer)
- Cannot access other teams' contexts (manifest enforces boundary)
- Suspension triggers: scope drift, quality failures, data leakage

**Helpdesk Agent:**
- Activated ONLY when team suspended (emergency mode)
- Cannot execute work (only communication)
- Cannot access team shared context (prevents data leakage during incident)
- All interactions logged to audit
- Deactivated when team reactivated

**Rollback Strategy:**
- If team coordination fails catastrophically → revert to individual agents (customer gets 4 individual agents instead of 1 team)
- If mobile app critical bug → customers use web portal (fallback)
- If manager agent unreliable → human Platform Governor acts as interim team coordinator

---

## 10. Auditability Requirements

**Audit Log Entries Required:**

**Team Lifecycle:**
- TEAM-CREATED: {team_id, composition, customer_id, pricing}
- TEAM-CERTIFIED: {team_id, genesis_decision_id}
- TEAM-DEPLOYED: {team_id, deployment_timestamp}
- TEAM-SUSPENDED: {team_id, reason, root_cause_agent_id}
- TEAM-REACTIVATED: {team_id, resolution}

**Manager Delegation:**
- MANAGER-TASK-ASSIGNED: {manager_id, team_member_id, task_description, correlation_id}
- MANAGER-DRAFT-REVIEWED: {manager_id, team_member_id, draft_id, decision: approved|revise}
- MANAGER-APPROVAL-REQUESTED: {manager_id, customer_governor_id, deliverable_id}

**Team Coordination:**
- TEAM-MEMBER-OUTPUT: {team_member_id, output_id, manager_review_status}
- TEAM-SHARED-CONTEXT-WRITE: {agent_id, team_id, artifact_id, hash}
- TEAM-STATUS-UPDATE: {team_id, status, triggered_by}

**Mobile Approvals:**
- MOBILE-APPROVAL-REQUESTED: {customer_governor_id, deliverable_id, push_notification_id}
- MOBILE-APPROVAL-GRANTED: {customer_governor_id, deliverable_id, device_id, timestamp}
- MOBILE-APPROVAL-DENIED: {customer_governor_id, deliverable_id, reason}

**Helpdesk Mode:**
- HELPDESK-ACTIVATED: {team_id, reason}
- HELPDESK-INTERACTION: {customer_id, helpdesk_agent_id, message, response}
- HELPDESK-DEACTIVATED: {team_id, resolution}

**Immutability:** All audit entries hash-chained per existing audit_logging_requirements.yml

---

## Genesis Review (Pending)

**ME-WoW Completeness Check:**

| Requirement | Status | Notes |
|-------------|--------|-------|
| 1. Outcome definition + closure | ✅ | Section 1 |
| 2. Scope boundaries (in/out) + refusals | ✅ | Section 2 |
| 3. Required inputs + evidence quality | ✅ | Section 3 |
| 4. Outputs and artifacts | ✅ | Section 4 |
| 5. Interfaces (read/write) | ✅ | Section 5 |
| 6. Decision rights | ✅ | Section 6 |
| 7. Critique/self-examination | ✅ | Section 7 |
| 8. Escalation triggers | ✅ | Section 8 |
| 9. Safety containment posture | ✅ | Section 9 |
| 10. Auditability requirements | ✅ | Section 10 |

**Evolution Classification Check:**

| Criterion | Present? | Impact |
|-----------|----------|--------|
| Increases execution scope | ✅ Yes | Manager agent coordinates team (new execution surface) |
| Reduces approvals | ❌ No | Customer Governor still approves all external actions |
| Adds data/system access | ✅ Yes | Team shared context (new data boundary) |
| Weakens safety/audit | ❌ No | Same audit requirements, stronger (team attribution) |

**Genesis Classification:** **EVOLUTION** (increases scope + adds data access)

**Genesis Recommendation:** **Pending full review** (requires Systems Architect + Vision Guardian input)

---

## Systems Architect Review (Pending)

**Architectural Impact Assessment:**

**Dependency Analysis:**
- New dependencies: Manager Agent ↔ Team Members (via team-internal topics)
- Shared context: Team workspace (introduces coupling, but isolated per team_id)
- Mobile app: New API client (adds load, but cacheable)

**Long-Term Risks:**
- Team coordination overhead scales with team size (4 agents OK, 10+ may need sub-teams)
- Shared context becomes performance bottleneck if >1GB per team
- Mobile app requires ongoing maintenance (iOS/Android updates)

**Cost Impact:**
- Additional Cloud Run services: +$10/month (manager agents, helpdesk)
- Additional DB storage: +$5/month (team workspaces)
- Additional Pub/Sub topics: +$5/month (team-internal)
- Mobile push notifications: $0 (FCM free tier)
- **Total:** +$20/month (offset by team revenue ₹30K/month = $360)

**Systems Architect Recommendation:** **Pending full review**

---

## Vision Guardian Review (Pending)

**Constitutional Alignment Assessment:**

**Alignment Score:** TBD (0-100)

**Constitutional Risks Identified:**
1. **Manager delegation authority:** Does internal delegation violate "execution requires Governor approval"?
   - **Mitigation:** Manager approves drafts (internal), customer Governor approves execution (external)
   - **Precedent:** Similar to Genesis certifying agents (internal) vs Governor approving deployment (external)

2. **Team shared context:** Does shared access violate data minimization?
   - **Mitigation:** Shared within team_id boundary only; strict isolation enforced
   - **Precedent:** Collaboration requires shared context; isolation per engagement_id already established

3. **Mobile approvals:** Do push notifications weaken approval attestation?
   - **Mitigation:** Same audit requirements; mobile device_id logged; same session enforcement
   - **Precedent:** Approval method (web vs mobile) doesn't change governance rigor

4. **Helpdesk mode:** Does degraded operation bypass governance?
   - **Mitigation:** Helpdesk cannot execute; only communication; all logged
   - **Precedent:** Containment strategy (similar to agent suspension)

**Required Clarifications:** None (proposal complete)

**Vision Guardian Recommendation:** **Pending full review**

---

## Platform Governor Decision

**Decision:** ✅ **APPROVED**  
**Date:** 2026-01-06  
**Decision Rationale:**
- Manager delegation acceptable for internal coordination (customer Governor retains external execution authority)
- Team shared context acceptable with strict per-team isolation enforced
- Mobile approvals same governance rigor as web
- Helpdesk mode acceptable for service continuity
- Cost increase ($20/month) offset by team revenue (₹30K/month = $360)
- Implementation timeline (7 weeks) acceptable

**Precedent Seed GEN-002 Created:**
```yaml
seed_id: "GEN-002"
version: 1
type: "agent_lifecycle"
decision: "Team coordination with Manager Agent approved"
principle: "Internal delegation permitted if customer Governor retains external execution authority"
rationale: |
  Manager agents may coordinate team members internally (task assignment, draft review)
  without customer Governor approval. Customer Governor approval STILL REQUIRED for:
  - External communication (sending to customer or outside world)
  - External execution (write/delete/execute on external systems)
  This preserves constitutional single-Governor principle while enabling team collaboration.
approved_by: "Platform Governor"
date: "2026-01-06"
supersedes: null
status: "active"
applies_to: ["manager_agents", "team_coordination", "delegation_authority"]
```

**Cost Impact Acknowledgment:**
- Team revenue (₹30K/month) covers platform cost increase ($20/month)
- Break-even: 0.07 team customers (platform pays for itself at 7% of 1 team subscription)

**Implementation Phases:**
- Phase 1: Manager Agent charter + team coordination protocol (2 weeks)
- Phase 2: Team governance integration + mobile app MVP (3 weeks)
- Phase 3: Helpdesk mode + first team trial (2 weeks)
- **Total:** 7 weeks to first team deployment

---

**End of Evolution Proposal 001**

---

## Appendix: Questions for Platform Governor

Before approving, confirm your understanding:

1. **Manager delegation:** You're comfortable with manager agents coordinating team members internally WITHOUT your approval for each delegation?
2. **Team shared context:** You accept the risk of team members accessing all team data (mitigated by isolation)?
3. **Mobile approvals:** You'll approve team outputs via mobile app (same rigor as web)?
4. **Helpdesk mode:** You accept temporary service degradation when manager suspended?
5. **Cost increase:** You approve $20/month platform cost increase (offset by team revenue)?
6. **Implementation timeline:** 7 weeks acceptable for first team deployment?

**Your decision will be logged as Precedent Seed GEN-002 or rejection rationale if denied.**
