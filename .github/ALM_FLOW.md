# Application Lifecycle Management (ALM) for WAOOAW
## Constitutional Governance-Driven Development

**Version**: 1.0  
**Date**: 2026-01-18  
**Status**: Active on feature/github-project-management  
**Authority**: Based on Genesis + Vision Guardian + Systems Architect charters

---

## 📋 ALM Flow Overview

```
You (Governor) create EPIC
   ↓
Vision Guardian Story auto-created (constitutional review)
   ↓
Vision Guardian asks YOU constitutional questions
   ↓
You approve/reject → Vision Guardian stamps or blocks
   ↓
If approved → Systems Architect Story auto-created
   ↓
Architect creates 4 analysis issues (cost, compliance, simulation, gaps)
   ↓
Architect decides epic/story breakdown (empowered by story points)
   ↓
Architect creates stories for BA, Testing, Deployment agents
   ↓
BA creates user stories → Dev implements → Testing validates
   ↓
Deployment Agent prepares (front-runs, keeps equipped)
   ↓
You trigger deployment manually
   ↓
Post-deployment: Extract key takeaways to master docs
```

---

## 🔍 Vision Guardian Story (Auto-Created on Epic)

**When you create an epic**, GitHub automation creates **Issue: Vision Guardian Constitutional Review**

### Vision Guardian Review Content

Based on `/main/Foundation/vision_guardian_foundational_governance_agent.md`:

**Constitutional Oversight Checklist**:
1. **L0 Constitution Alignment** (from `main/Foundation.md`)
   - Does this preserve "Agents Earn Your Business" philosophy?
   - Does it maintain deny-by-default security posture?
   - Does it respect approval primitives (Artifact/Communication/Execution)?
   - Does it maintain precedent seed discipline?

2. **L1 Canonical Model Fit**
   - Does it align with 13 microservices architecture?
   - Does it respect agent certification process (Genesis authority)?
   - Does it maintain separation of duties (Vision Guardian ≠ Genesis ≠ Architect)?

3. **Brand & Vision Alignment** (from `/docs/BRAND_STRATEGY.md`, `/docs/PRODUCT_SPEC.md`)
   - Dark theme, tech-forward, marketplace DNA?
   - "Try before hire" 7-day trial philosophy?
   - Agent personality, status, specializations?
   - Pricing model (₹8k-18k/month)?

4. **Ethics & Risk Assessment**
   - Commercial pressure detection (success-pressure doctrine)
   - "Just this once" exception attempts?
   - Approval boundary blurring?
   - Long-term coherence vs short-term gain?

5. **Risk-Based Triage** (Level 1-4)
   - **Level 1 (Auto-block)**: Deceptive intent, privacy breach, regulated domain violation
   - **Level 2 (Escalate)**: High blast radius, sensitive context, commitment without approval
   - **Level 3 (Allow with disclaimer)**: Low blast radius, subjective opinion
   - **Level 4 (Log only)**: Routine communication, internal coordination

### Vision Guardian Output Format (Mandatory)

```markdown
## Vision Guardian Constitutional Review

**Alignment Score**: 0-100  
**Risk Level**: Level 1 (Auto-block) | Level 2 (Escalate) | Level 3 (Disclaimer) | Level 4 (Log)

### Constitutional Risks Identified
- [List specific risks, or "None detected"]

### Required Clarifications for Governor
1. **Question 1**: Does [proposed change] conflict with [constitutional principle]?
   - **Context**: [Why this matters]
   - **Options**: [A] Approve with [condition], [B] Revise to [alternative], [C] Reject
   
2. **Question 2**: ...

### Recommendation
- [ ] **Approve** (Alignment ≥80, Risk Level 3-4)
- [ ] **Revise** (Alignment 50-79, Risk Level 2-3, clarifications needed)
- [ ] **Reject** (Alignment <50, Risk Level 1-2, constitutional violation)

### Precedent Seed (if approved)
- **Seed ID**: PREC-VG-{epic-id}-001
- **Clarification**: [What this approval clarifies for future decisions]
- **Gates Added**: [New approval gates, if any]
- **Rationale**: [Why this preserves long-term coherence]
```

### Governor (You) Response

You comment on Vision Guardian issue with:
```markdown
@vision-guardian-agent

**Decision**: Approve | Revise | Reject

**Responses to Clarifications**:
1. Answer to Question 1
2. Answer to Question 2

**Additional Context**: [Any additional governor guidance]

**Precedent Seed Approval**: Yes | No (if no, explain why)
```

Vision Guardian then:
- **If Approved**: Stamps epic, creates Systems Architect story, closes VG review issue
- **If Rejected**: Blocks epic, closes VG review issue with rejection rationale
- **If Revise**: Keeps issue open until clarifications resolved

---

## 🏗️ Systems Architect Deep Dive (Auto-Created After VG Approval)

**When Vision Guardian approves**, GitHub automation creates **Issue: Systems Architect Technical Analysis**

### Architect Creates 4 Analysis Issues

Architect reads repo compliance points and creates:

#### Issue 1: Cost Boundary Protection Analysis
**Type**: Task (Architecture)  
**Owner**: Systems Architect

**Content**:
```markdown
## Cost Analysis for [Epic Name]

**Budget Constraint**: ₹[X] per month (from BRAND_STRATEGY pricing model)

### Infrastructure Cost Breakdown
- Component 1: ₹[X]/month (GCP service + estimates)
- Component 2: ₹[X]/month
- **Total Infrastructure**: ₹[X]/month

### Alternative Cost Comparison
| Solution | Cost/month | Pros | Cons | Recommendation |
|----------|------------|------|------|----------------|
| RabbitMQ on Cloud Run | ₹X | Serverless, auto-scale | Limited config | ✅ Recommend |
| Cloud Pub/Sub | ₹Y | Fully managed | Higher latency | ❌ |
| Self-hosted RabbitMQ (GCE) | ₹Z | Full control | Maintenance overhead | ❌ |

### Cost Threshold Check
- [ ] Infrastructure cost < ₹5,000/month (20% of agent pricing)
- [ ] No cost increase to customer (absorbed by platform)
- [ ] Budget alert configured (70%/85%/100% per Finance component)

**Decision**: Proceed | Revise | Reject
```

#### Issue 2: Technical Architecture Compliance
**Type**: Task (Architecture)  
**Owner**: Systems Architect

**Content**:
```markdown
## Architecture Compliance Check for [Epic Name]

**Compliance Source**: `/main/Foundation.md`, `/policy/tech_stack.yaml`, agent charters

### Compliance Matrix

| Compliance Point | Policy | Implementation | Status | Gap/Fix |
|------------------|--------|----------------|--------|---------|
| Deny-by-default security | L0 Constitution | RabbitMQ private VPC | ✅ | None |
| Approval primitives | Vision Guardian | Events are Artifacts (internal) | ✅ | None |
| 13 microservices architecture | Foundation.md | New service or existing? | 🔄 | Decide: New port 8020 or extend 8002? |
| Genesis certification | Genesis charter | Does MQ require new agent? | ✅ | No new agent, library only |
| Precedent seed discipline | Vision Guardian | MQ events logged to audit | ✅ | None |
| Agent DNA filesystem | Genesis | MQ events don't touch DNA | ✅ | None |
| Tech stack policy | tech_stack.yaml | RabbitMQ approved? | 🔄 | Add to yaml or use existing Cloud Pub/Sub |

### Compliance Gaps Identified
1. **Gap**: RabbitMQ not in `tech_stack.yaml`
   - **Impact**: Constitutional approval needed before adding new tech
   - **Fix**: Add RabbitMQ to yaml with rationale, or use Cloud Pub/Sub (already approved)

2. **Gap**: [If any other gaps]

### Compliance Decision
- [ ] **Fully Compliant**: No gaps, proceed
- [ ] **Compliant with Fixes**: Apply fixes above, re-verify
- [ ] **Non-Compliant**: Architectural changes required
```

#### Issue 3: Simulation Runs & Validation
**Type**: Task (Testing)  
**Owner**: Systems Architect (devises simulations)

**Content**:
```markdown
## Simulation Plan for [Epic Name]

**Purpose**: Validate architectural assumptions before implementation

### Simulation 1: Load Test (Message Throughput)
**Hypothesis**: RabbitMQ can handle 1000 msg/sec with <100ms latency

**Method**:
- Tool: Locust or Apache JMeter
- Setup: RabbitMQ on Cloud Run (demo env), Python publisher client
- Test: Ramp up from 100 msg/sec → 1000 msg/sec over 10 minutes
- Metrics: Publish latency (p50, p95, p99), queue depth, CPU/memory

**Success Criteria**:
- p95 latency <100ms
- No message loss (dead letter queue empty)
- CPU <80%, Memory <80%

**Result**: [Run simulation, paste results]

---

### Simulation 2: Failure Scenario (RabbitMQ Unavailable)
**Hypothesis**: Base Agent continues working when RabbitMQ down (non-blocking)

**Method**:
- Setup: Base Agent with retry logic, RabbitMQ stopped
- Test: Base Agent completes task, attempts to publish event
- Observe: Retries 3x (1s, 2s, 4s), logs error, continues

**Success Criteria**:
- Base Agent doesn't crash
- Task completes successfully
- Error logged with context (task_id, retry count)

**Result**: [Run simulation, paste results]

---

### Simulation 3: Cost Projection (30-Day Forecast)
**Hypothesis**: RabbitMQ cost <₹5,000/month at 1M events/month

**Method**:
- Tool: GCP Pricing Calculator
- Assumptions: 1M events/month, avg 1KB per event, Cloud Run (1 instance)
- Calculation: Cloud Run ($0.00002400/vCPU-second) × 24hr × 30 days

**Success Criteria**:
- Total cost <₹5,000/month
- No surprises (hidden egress costs, etc.)

**Result**: [Calculate, paste breakdown]

---

### Conflicts/Concerns Identified
1. **Conflict**: [If simulation conflicts with vision/constitution]
   - **Example**: "Lazy queues write to disk, conflicts with deny-by-default security"
   - **Action**: Escalate to Vision Guardian (create issue)

2. **Concern**: [If simulation reveals risk]
   - **Example**: "Cost projection shows ₹7k/month (exceeds ₹5k limit)"
   - **Action**: Escalate to Vision Guardian for alternatives

### Escalation Decision
- [ ] **No Escalation**: All simulations passed, no conflicts
- [ ] **Escalate to Vision Guardian**: Conflict/concern identified (create VG review issue)
```

#### Issue 4: Gap Analysis & Resolutions
**Type**: Task (Architecture)  
**Owner**: Systems Architect

**Content**:
```markdown
## Gap Analysis for [Epic Name]

**Analysis Date**: 2026-01-18  
**Architect**: Systems Architect Agent

### Gaps Identified

#### Gap 1: RabbitMQ Client Library Missing
- **Impact**: Base Agent cannot publish events (blocker)
- **Resolution**: Create `waooaw-mq` Python library
- **Story Created**: #207 [TASK] Create Python MQ client library
- **Priority**: P0 (Critical)
- **Estimate**: 5 story points

#### Gap 2: VPC Connector for Private RabbitMQ Access
- **Impact**: RabbitMQ public = security risk
- **Resolution**: Create VPC connector in GCP
- **Story Created**: #204 [TASK] Setup VPC connector
- **Priority**: P0 (Critical)
- **Estimate**: 3 story points

#### Gap 3: [If any other gaps]

### Resolution Summary
- **Total Gaps**: 2
- **Blockers (P0)**: 2
- **High (P1)**: 0
- **Medium (P2)**: 0
- **Total Story Points**: 8

### Architecture Decision
- [ ] **Ready for Story Breakdown**: All gaps have resolutions, proceed
- [ ] **Revise Epic Scope**: Gaps too large, reduce scope or reject epic
- [ ] **Escalate to Vision Guardian**: Gaps reveal constitutional risk
```

---

## 🎯 Architect Empowered Epic/Story Breakdown

**After 4 analysis issues complete**, Architect decides breakdown:

### Breakdown Logic (Architect's Decision Framework)

**Total Epic Story Points**: Sum all implementation work

**Breakdown Decision**:
- **<13 points**: Single epic, create stories directly (BA, Testing, Deployment)
- **13-21 points**: Consider 2 sub-epics (e.g., Infrastructure + Integration)
- **>21 points**: Must break into multiple epics (governance, feasibility)

**Architect creates GitHub issues**:
- Stories for BA Agent (#210, #211, #212, #213, #214, #215)
- Stories for Testing Agent (#218, #219)
- Stories for Deployment Agent (#203, #204, #205, #206, #216, #217)

**No epic template rigid rules** - Architect uses story points to decide structure organically.

---

## 📂 Documentation Structure

### Project Folder: `/docs/{project-name}/`

**Example: `/docs/message-queue/`**

```
/docs/message-queue/
  ├── vision-review.md (Vision Guardian constitutional review)
  ├── architecture/
  │   ├── cost-analysis.md (Issue #1 converted to doc)
  │   ├── compliance-matrix.md (Issue #2 converted)
  │   ├── simulation-results.md (Issue #3 converted)
  │   └── gap-analysis.md (Issue #4 converted)
  ├── user-stories/ (BA Agent stories)
  │   ├── 210-base-agent-publish-completed.md
  │   ├── 211-base-agent-publish-failed.md
  │   └── ...
  ├── test-plans/ (Testing Agent plans)
  │   ├── 218-unit-tests-mq-client.md
  │   └── 219-e2e-tests-publish-consume.md
  └── deployment/
      ├── terraform-stack.md (Deployment Agent runbook)
      └── rollback-plan.md
```

### Master Documents Updates (BEFORE Deployment)

**Before deployment trigger**, Architect updates master docs:

1. **`/main/Foundation.md`** (if constitutional pattern added)
   - Example: "Message Queue pattern approved for async event-driven architecture"

2. **`/policy/tech_stack.yaml`** (if new tech added)
   - Example: Add RabbitMQ with version, rationale, approval date

3. **`/docs/architecture-decisions.md`** (ADR registry)
   - Example: Link to ADR-001: Message Queue Architecture

4. **`/docs/testing-standards.md`** (if new test pattern)
   - Example: "Integration tests with RabbitMQ test container"

5. **Agent charters** (if agent capabilities expanded)
   - Example: Update Deployment Agent charter with "Message Queue deployment" capability

**Process**: 
- Architect creates PR with master doc updates
- You (Governor) review → Approve/reject
- **After merge**: You trigger deployment
- **Rationale**: Master docs reflect APPROVED architecture before deployment

---

## 🚀 Deployment Agent: Reactive Strategy

### Deployment Agent is REACTIVE (Trigger-Based)

Deployment Agent **only acts when you explicitly trigger**:

**During Development** (BA, Dev, Testing in progress):
- Deployment Agent creates **stories/tasks** for infrastructure needs
- Stories remain in backlog (not executed automatically)
- Example: #203 [TASK] Create Terraform stack for RabbitMQ

**When BA + Dev + Testing Complete**:
- Deployment Agent stories should also be complete (terraform code ready, reviewed, tested)
- But **nothing provisioned yet** (no GCP resources created)

**You Trigger Deployment**:
- Command: `@deployment-agent deploy demo message-queue`
- Deployment Agent executes:
  1. Run `terraform apply` (provisions resources)
  2. Deploy application code
  3. Run smoke tests
  4. Report success/failure

**Reactive Benefits**:
- You control timing and cost (no surprise infrastructure bills)
- Clear approval gate before any resource provisioning
- Deployment Agent prepared (code ready) but doesn't execute until triggered

---

## 🎮 Governor (You) Triggers

**Manual Deployment Triggers** (only you can execute):

1. **Deploy to Demo**: `@deployment-agent deploy demo message-queue`
   - Deployment Agent runs: `terraform apply -var="env=demo"`
   - Result: Posted in issue comments (success/failure)

2. **Deploy to Production**: `@deployment-agent deploy prod message-queue`
   - Deployment Agent checks: All tests passed? BA stories complete? Vision Guardian approved?
   - If yes: Runs production deployment
   - If no: Blocks with reason ("Testing not complete, #219 still open")

3. **Rollback**: `@deployment-agent rollback prod message-queue`
   - Deployment Agent reverts to previous version
   - Posts rollback report

**You control WHEN, Deployment Agent controls HOW.**

---

## 📊 ALM Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ GOVERNOR (You) creates EPIC                                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                ┌───────────────▼────────────────┐
                │ Vision Guardian Story Created  │
                │ (Constitutional Review)        │
                └───────────────┬────────────────┘
                                │
                ┌───────────────▼────────────────┐
                │ Vision Guardian asks YOU       │
                │ constitutional questions       │
                └───────────────┬────────────────┘
                                │
            ┌───────────────────┴──────────────────┐
            │ You approve?                         │
            └───┬──────────────────────────────┬───┘
                │ YES                          │ NO
        ┌───────▼────────┐           ┌────────▼────────┐
        │ VG Stamps Epic │           │ VG Blocks Epic  │
        │ Creates Arch   │           │ Closes Issue    │
        │ Story          │           └─────────────────┘
        └───────┬────────┘
                │
    ┌───────────▼──────────────┐
    │ Systems Architect Story  │
    │ (Technical Analysis)     │
    └───────────┬──────────────┘
                │
    ┌───────────▼──────────────────────────────────────┐
    │ Architect creates 4 analysis issues:             │
    │ 1. Cost Analysis                                 │
    │ 2. Compliance Check                              │
    │ 3. Simulation Runs                               │
    │ 4. Gap Analysis                                  │
    └───────────┬──────────────────────────────────────┘
                │
    ┌───────────▼──────────────┐
    │ All 4 issues complete?   │
    └───┬──────────────────┬───┘
        │ YES              │ NO
┌───────▼────────┐    ┌───▼────────────────┐
│ Architect      │    │ Escalate to Vision │
│ decides epic/  │    │ Guardian (if risk) │
│ story breakdown│    │ or revise analysis │
└───────┬────────┘    └────────────────────┘
        │
┌───────▼────────────────────────────────┐
│ Architect creates stories for:         │
│ - BA Agent (user stories)              │
│ - Testing Agent (test plans)           │
│ - Deployment Agent (infra tasks)       │
└───────┬────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────┐
│ Parallel Execcreates terraform/runbooks (code only) │
└───────┬─────────────────────────────────────────────┘
        │
┌───────▼────────────────────────────┐
│ BA + Dev + Testing complete?       │
└───┬────────────────────────────┬───┘
    │ YES                        │ NO
┌───▼────────────────┐      ┌────▼──────────────┐
│ Architect creates  │      │ Continue work     │
│ PR: Update master  │      │ (not ready)       │
│ docs (Foundation,  │      └───────────────────┘
│ tech_stack, etc)   │
└───┬────────────────┘
    │
┌───▼────────────────────────────────┐
│ GOVERNOR (You) reviews PR          │
│ Approves master doc updates        │
└───┬────────────────────────────────┘
    │
┌───▼────────────────────────────────┐
│ PR merged → Master docs reflect    │
│ APPROVED architecture              │
└───┬────────────────────────────────┘
    │
┌───▼────────────────────────────────┐
│ GOVERNOR (You) triggers deployment │
│ "@deployment-agent deploy demo"    │
└───┬────────────────────────────────┘
    │
┌───▼────────────────────────┐
│ Deployment Agent EXECUTES  │
│ (terraform apply, deploy,  │
│ smoke tests, monitoring)   │
└───┬────────────────────────┘
    │
┌───▼────────────────────────────────┐
│ Success? Governor triggers         │
│ "@deployment-agent deploy prod"    │
└───┬────────────────────────────────┘
    │
┌───▼────────────────────────────────┐
│ Production deployed, epic closed   │
│ - Extract key takeaways            │
│ - Update master docs               │
│ - Close epic                       │
└────────────────────────────────────┘
```

---

## 🔧 GitHub Automation Changes Needed

Based on this ALM, here's what automation should do:

### 1. Epic Created → Auto-Create Vision Guardian Story
**Trigger**: Issue labeled `epic`  
**Action**: Create issue:
```
Title: [VG Review] Epic #X - [Epic Title]
Labels: vision-guardian-review, story
Assignee: Vision Guardian Agent
Template: vision-guardian-review.yml
Links: Epic #X
```

### 2. Vision Guardian Approved → Auto-Create Architect Story
**Trigger**: Vision Guardian issue closed with label `approved`  
**Action**: Create issue:
```
Title: [Architect Analysis] Epic #X - [Epic Title]
Labels: systems-architect-analysis, story
Assignee: Systems Architect Agent
Template: architect-analysis.yml
Links: Epic #X, VG Review #Y
```

### 3. Architect Analysis Complete → Label Epic "ready-for-breakdown"
**Trigger**: All 4 analysis issues closed  
**Action**: Add label `ready-for-breakdown` to epic

### 4. Deployment Trigger → Check Readiness
**Trigger**: Comment `@deployment-agent deploy {env} {project}`  
**Action**: 
- Check: BA stories complete? Testing passed? VG approved?
- If yes: Run deployment workflow
- If no: Comment blockers ("Testing issue #219 still open")

---

## 📝 Summary: Your ALM Philosophy Implemented

**Constitutional Governance First**:
- Vision Guardian reviews BEFORE technical work
- Vision Guardian creates GitHub issue assigned to YOU with alternatives + known preferences
- You answer constitutional questions with precedent seeds
- Precedent seeds preserve long-term coherence

**Architect Deep Dive via Issues** (Not Documents):
- 4 analysis issues (cost, compliance, simulation, gaps)
- Architect escalates to Vision Guardian if conflict/concern detected
- Vision Guardian decides → escalates to you if needed
- Architect empowered to decide breakdown (story points guide, no rigid rules)

**Reactive Deployment** (No Front-Running):
- BA, Testing, Deployment agents create stories/code (not provision resources)
- Deployment Agent waits for your explicit trigger
- Only you provision infrastructure (`@deployment-agent deploy demo`)

**Documentation Timing**:
- `/docs/{project-name}/` for project-specific docs
- Master docs updated BEFORE deployment (architecture approved first)
- Architect creates PR → You approve → Then you trigger deployment

**Escalation Path**:
- Architect → Vision Guardian (if conflict) → Governor (if VG can't decide)

---

## ✅ Implementation Complete

**Templates Created**:
1. `vision-guardian-review.yml` - Constitutional review with alternatives + preferences
2. `architect-analysis.yml` - Technical analysis tracking (4 issues + breakdown)
3. `epic.yml`, `story.yml`, `task.yml`, `bug.yml` - Updated from earlier

**Automation Needed**:
1. Epic created → Auto-create Vision Guardian review issue
2. VG approved → Auto-create Systems Architect analysis issue
3. Comment `@deployment-agent deploy {env}` → Trigger deployment workflow

**Ready to test**: Create first epic to validate ALM workflow!
