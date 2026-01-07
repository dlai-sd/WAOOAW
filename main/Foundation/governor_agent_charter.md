# Governor (Human) — Agent Charter
## Human Approval Authority & External Execution Control

**Version:** v1.0 (Constitutional Amendment AMENDMENT-001; 2026-01-07)  
**Status:** Active (Human Agent)  
**Authority Level:** External Execution Approval, Emergency Budget Approval, Job Pricing Approval  
**Primary Reader:** Human Governors (Customers)  
**Secondary Readers:** Governance Agents (Genesis, Manager, Vision Guardian)  

---

## 1. Role Definition

The Governor is the **human customer** who retains final authority over external execution, budget decisions, and policy choices within their engagement.

This role exists to preserve **human control** over agents' external actions, ensuring **L0 deny-by-default** principle: agents cannot take external actions without explicit Governor approval.

The Governor is responsible for:
- Approving external execution (publishing, API writes, customer communication, financial transactions)
- Approving emergency budget increases when agents hit 100% query budget utilization
- Approving Job pricing when deploying new specialized agents
- Escalating to Platform Governor when uncertain or when policy review needed

---

## 2. Source of Authority

The Governor operates under the **WaooaW Constitution (L0)** and **Canonical Foundational Model (L1)** in `main/Foundation.md`.

**L0 External Approval Requirement:**
> "All external actions (communication, execution, data access) require explicit Governor approval unless pre-approved via Precedent Seed."

**L0 Human Control Principle:**
> "Human Governors retain final authority over agent actions. Agents serve humans, not replace them."

---

## 3. Core Responsibilities

### 3.1 External Execution Approval

**Definition:** Any agent action that crosses the platform boundary (sends data externally, writes to customer systems, communicates with customer stakeholders) requires Governor approval.

**Examples of External Execution:**
- Publishing blog post to customer WordPress
- Sending email to customer's clients
- Writing to customer CRM (Salesforce, HubSpot)
- Posting to customer social media accounts
- Making financial transaction on customer's behalf
- Accessing customer private data (medical records, financial accounts)

**Approval Workflow:**
1. Agent completes **Think phase** (constitutional queries, decision made)
2. Agent pauses at **Act phase** if external execution detected
3. Manager emits approval request to Governor (mobile push notification)
4. Governor reviews **Think→Act→Observe context** (see Section 4)
5. Governor decides: **APPROVE** (agent executes) | **DENY** (agent fails skill, logs reason) | **DEFER** (pause until later) | **ESCALATE** (Platform Governor reviews)

**Approval SLA:**
- Target latency: **<5 minutes** median
- Offline queue: Requests queued if Governor offline, synced when reconnected
- Timeout: If no response in 24 hours, Manager escalates to Helpdesk (customer notified)

### 3.2 Emergency Budget Approval

**Trigger:** Agent hits **100% query budget** ($1/day default) and cannot execute Skills without additional budget.

**Process:**
1. Manager detects 100% utilization (agent_budget_tracking table)
2. Manager suspends agent execution
3. Manager emits emergency budget approval request to Governor
4. Governor reviews:
   - **Cost Analysis:** Which Skills consuming most queries (e.g., "Fact-Check Medical Claims" used 8/10 queries)
   - **Efficiency Recommendations:** Systems Architect proposes optimizations (cache-first, fine-tuning)
   - **Budget Options:** Approve $2/day increase ($30/month → $60/month for agent) | Suspend agent until tomorrow (budget resets daily) | Optimize agent (reduce query usage)
5. Governor decides: **APPROVE INCREASE** (agent resumes) | **SUSPEND AGENT** (wait for daily reset) | **OPTIMIZE AGENT** (Genesis reviews efficiency)

**Budget Limits:**
- Default per-agent budget: **$1/day** (30 agents max = $30/month)
- Platform total budget: **$100/month** (includes infrastructure, embeddings, vector DB)
- Governor emergency approval limit: **$50/month increase** (above requires Platform Governor approval)

### 3.3 Job Pricing Approval

**Trigger:** Customer deploying new Job (e.g., Healthcare Content Writer) with proposed pricing.

**Process:**
1. Genesis certifies Job (validates Skills, industry, geography)
2. Genesis calculates recommended pricing:
   - Base price: **₹8,000 - ₹50,000/month** (depends on number of Skills, complexity)
   - Complexity factor: **1.0x** (100% autonomy) to **1.5x** (50% autonomy, frequent approvals)
   - Industry premium: **Healthcare 1.5x** (HIPAA), **Education 1.2x**, **Sales 1.0x**
   - Geography premium: **North America 1.2x**, **Europe 1.3x** (GDPR), **India 1.0x**
3. Governor reviews pricing breakdown + rationale
4. Governor decides: **APPROVE** (Job deployed at price) | **COUNTER** (propose different price) | **REJECT** (Job not deployed)

**Pricing Transparency:**
- All pricing factors shown to Governor (no hidden fees)
- 7-day free trial regardless of pricing (Governor keeps deliverables even if cancels)
- Pricing locked during trial (no surprise increases)

---

## 4. Auto-Approval Oversight (Constitutional Simulation SIM-012)

### 4.1 Precedent Seed Auto-Approvals

**Context:** When agents auto-approve actions based on Precedent Seeds (e.g., GEN-004 "Healthcare content publishing auto-approval"), Governor retains oversight to prevent misinterpretation.

**Auto-Approval with Oversight Workflow:**

```yaml
agent_auto_approval:
  step_1: Agent checks Precedent Seed conditions (e.g., GEN-004: fact-check passed + HIPAA compliant + medical claims verified + no high-risk)
  step_2: If all conditions met → AUTO-APPROVE (agent proceeds immediately, no blocking)
  step_3: BUT agent STILL emits approval request to Governor (informational only)
  step_4: Governor receives low-priority notification: "Auto-approved per GEN-004 (informational, review at convenience)"

governor_oversight:
  notification_type: "low_priority_informational"
  notification_channel: "Mobile app (collapsed view, not push notification)"
  governor_action: "Review at convenience (not blocking agent execution)"
  governor_veto_window: "24 hours from auto-approval timestamp"
  
veto_workflow:
  if_governor_vetoes_within_24_hours:
    action: "Reverse agent action immediately (e.g., unpublish content, revoke API access)"
    reason_example: "Governor veto: Article contains experimental treatment claim (high-risk, agent missed it in footnote)"
    penalty: "Increment precedent_seed.false_positive_count in registry"
    threshold: "If false_positive_count >= 3 → DEPRECATE seed (too many errors, revert to manual approval)"
    notification: "Agent receives veto notification: 'GEN-004 auto-approval overridden, unpublish article immediately'"
  
  if_no_veto_within_24_hours:
    action: "Auto-approval confirmed (Governor had opportunity to review, no objection)"
    audit_trail: "Governor implicitly approved via non-veto within 24-hour oversight window"
    precedent_strengthening: "Auto-approval success count incremented (builds confidence in seed)"

audit_transparency:
  agent_logs: "Auto-approved per GEN-004, Governor notified for oversight"
  governor_logs: "Received informational approval {approval_id}, no veto within 24 hours (implicit approval)"
  systems_architect_logs: "GEN-004 used 47 times, 2 vetoes (4% false positive rate, below 10% threshold)"
```

**Veto Triggers Seed Review:**

If Precedent Seed accumulates 3+ false positives (Governor vetoes):
```yaml
seed_deprecation_workflow:
  trigger: "false_positive_count >= 3"
  alert: "Systems Architect emits alert: 'GEN-004 has 3 false positives, seed unreliable'"
  genesis_review:
    question: "Was pattern too broad? Conditions ambiguous? Edge cases missed?"
    options:
      - REVISE seed: "Tighten conditions (e.g., add 'no experimental treatments' to GEN-004)"
      - DEPRECATE seed: "Revert to manual approval (auto-approval too risky for this pattern)"
      - KEEP with warning: "Governor training issue (seed correct, Governor needs more context)"
  outcome: "Genesis updates seed status + rationale in precedent_seeds registry"
```

**Example Veto Scenario:**

```yaml
scenario:
  agent: "Healthcare Content Writer"
  action: "Published article about metformin"
  auto_approval: "GEN-004 conditions met (fact-check passed, HIPAA compliant, claims verified)"
  
  hour_18_after_publication:
    governor_review: "Governor notices article footnote mentions experimental metformin use for weight loss (high-risk, off-label)"
    governor_veto: "VETO - Article contains experimental treatment claim (agent missed it in footnote)"
    system_action: "Unpublish article immediately, increment GEN-004 false_positive_count to 1"
  
  learning_outcome:
    agent: "Agent learns: Check footnotes for experimental claims"
    seed: "GEN-004 penalty count: 1 / 3 (still active, but being watched)"
    governance: "Governor oversight prevented potential FDA compliance issue"
```

---

## 5. Mobile UI Integration (Skill Approval Context)

When Governor receives approval request (mobile push notification), Governor sees **Think→Act→Observe context** to make informed decision.

### 5.1 Think Phase Context (Why Agent Wants Approval)

**Constitutional Queries Shown:**
```yaml
think_phase_summary:
  query: "Can I publish blog post to customer WordPress?"
  retrieved_chunks:
    - layer: L0
      content: "L0 deny-by-default: All external actions require explicit approval"
      relevance_score: 0.94
    - layer: L1
      content: "Governor approval required for external execution (publishing, API writes, customer data access)"
      relevance_score: 0.91
    - layer: L1
      content: "GEN-002: Manager can delegate internal tasks without Governor approval"
      relevance_score: 0.87
  precedent_seeds_used: ["GEN-001", "GEN-002", "GEN-003"]
  decision: "ESCALATE (requires Governor approval)"
  confidence: 0.94
  recommendation: "APPROVE (constitutional queries passed, high confidence)"
```

**Purpose:** Governor sees agent's constitutional reasoning (not just "approve Y/N?"). Increases trust.

### 4.2 Act Phase Context (What Agent Will Do If Approved)

**Execution Steps Shown:**
```yaml
act_phase_preview:
  execution_steps:
    - "1. Validate WordPress API credentials (read-only check)"
    - "2. Upload draft_blog_post.md to WordPress as draft (not published)"
    - "3. Attach regulation_summary.json as metadata"
    - "4. Generate preview URL, send to customer Governor"
    - "5. Wait for Governor final approval before publishing"
  apis_called: ["WordPress REST API (POST /wp-json/wp/v2/posts)"]
  estimated_time: "2 minutes"
  external_interactions:
    - type: "API Write"
      target: "customer_wordpress_instance"
      reversible: true  # Can delete draft if Governor rejects
```

**Purpose:** Governor knows exactly what agent will do (no black box). Can deny if uncomfortable.

### 4.3 Observe Phase Context (What Gets Logged After Execution)

**Audit Trail Preview:**
```yaml
observe_phase_preview:
  audit_trail_entries:
    - "Skill execution outcome (SUCCESS/FAILURE)"
    - "WordPress post ID"
    - "Preview URL for Governor review"
    - "Execution time (actual vs estimated)"
    - "Hash-chained audit entry (tamper-proof)"
  metrics_tracked:
    - "Skill execution time (target: <10 min)"
    - "Customer rating (after post published)"
  checkpoint_marked: true  # plan.md updated with checkbox ✅
```

**Purpose:** Governor sees transparency (everything logged, auditable, hash-chained).

### 4.4 Approval Actions

**Mobile UI Buttons:**
```yaml
approval_actions:
  - action: "Approve"
    color: "green"
    confirmation: "Are you sure? Agent will publish to WordPress."
    next_step: "Agent executes Act phase, logs Observe phase, Manager marks skill COMPLETED"
    
  - action: "Deny"
    color: "red"
    confirmation: "Provide reason for denial (helps agent learn)"
    next_step: "Agent logs denial reason to errors.jsonl, marks skill FAILED, Manager notified"
    
  - action: "Defer"
    color: "yellow"
    confirmation: "Defer until when? (1 hour, 1 day, custom)"
    next_step: "Agent pauses skill execution, Manager queues retry at specified time"
    
  - action: "Escalate to Platform Governor"
    color: "orange"
    confirmation: "Escalate if uncertain or needs policy review"
    next_step: "Platform Governor reviews, provides binding decision, becomes Precedent Seed"
```

---

## 5. Approval Boundaries (What Governor Can/Cannot Approve)

### 5.1 Governor CAN Approve

**External Execution:**
- ✅ Publishing content to customer systems (WordPress, social media, CRM)
- ✅ Sending communication to customer stakeholders (emails, messages)
- ✅ Writing to customer databases (CRM updates, inventory changes)
- ✅ Accessing customer private data (financial records, medical records, PII)
- ✅ Making customer-authorized financial transactions (payments, refunds)

**Budget Decisions:**
- ✅ Emergency budget increases up to $50/month per engagement
- ✅ Agent suspension due to budget exhaustion
- ✅ Query budget optimization (reduce queries vs increase budget)

**Job Deployment:**
- ✅ Approving Job pricing for new specialized agents
- ✅ Starting 7-day free trial for Jobs
- ✅ Canceling trial or subscribing to Job

### 5.2 Governor CANNOT Approve (Must Escalate to Platform Governor)

**Constitutional Changes:**
- ❌ Weakening L0 principles (deny-by-default, human control, auditability)
- ❌ Bypassing approval gates for convenience
- ❌ Creating customer-specific execution forks (exceptions become permanent)

**Platform Budget Increases:**
- ❌ Emergency budget increases >$50/month (Platform Governor approval required)
- ❌ Platform-wide budget changes (affects all customers)

**Governance Policy Changes:**
- ❌ Changing Agent DNA initialization process
- ❌ Changing Precedent Seed approval workflow
- ❌ Suspending governance agents (Genesis, Vision Guardian, Systems Architect)

**Ethics Violations:**
- ❌ Approving actions that violate L0 ethics doctrine (deception, privacy breaches, unfair treatment)
- ❌ Overriding Vision Guardian decisions (Vision Guardian has veto on constitutional risk)

---

## 6. Session Management (Single Governor Invariant)

**Governance Rule:** Each engagement has **exactly one Governor** at any time (governance_session_rules.single_governor_invariant).

### 6.1 Single Governor Benefits

**Prevents Conflicts:**
- No conflicting approvals (Governor A approves, Governor B denies same action)
- No split approval authority (who decides if disagreement?)
- No diluted accountability (one Governor = clear responsibility)

**Enables Mobile UI:**
- Mobile push notifications go to single Governor (not multiple)
- Approval requests don't queue indefinitely (Governor always available or designated backup)

### 6.2 Governor Delegation (Backup Governor)

**Scenario:** Primary Governor unavailable (vacation, offline, emergency).

**Process:**
1. Primary Governor designates **Backup Governor** (colleague, manager, customer team member)
2. Backup Governor gains temporary approval authority
3. Approval requests route to Backup Governor while Primary offline
4. When Primary returns, Backup Governor approval authority revoked

**Constraints:**
- Only 1 Backup Governor at a time (preserves single Governor invariant)
- Backup Governor sees same Think→Act→Observe context (no reduced transparency)
- All Backup approvals logged with backup_governor_id (audit trail preserved)

### 6.3 Vision Guardian Break-Glass Authority

**Exception to Single Governor Rule:**

Vision Guardian can **forcibly terminate Governor session** if ethics violation pattern detected:

**When Exercised:**
- Governor approving actions that violate L0 ethics rules repeatedly (>3 violations in 24 hours)
- Governor bypassing Precedent Seeds without justification (weakening governance)
- Governor pressuring agents to skip approval gates for commercial urgency

**Process:**
1. Vision Guardian detects pattern (automated ethics checks on Governor approvals)
2. Vision Guardian terminates Governor session immediately
3. All approvals frozen pending constitutional review
4. Platform Governor receives escalation (human intervention required)
5. Vision Guardian emits **CONSTITUTIONAL-BREACH** audit entry (hash-chained, immutable)

**Safeguard:** This is **last resort** failsafe. Vision Guardian cannot override legitimate Governor decisions, only terminate sessions exhibiting systemic ethics violations.

---

## 7. Escalation to Platform Governor

**When to Escalate:**

**Uncertain Constitutional Implications:**
- Approval request has unclear ethics implications (e.g., medical advice, financial commitments)
- Approval would set precedent affecting other customers (becomes Precedent Seed)
- Approval conflicts with L0/L1 principles (Governor unsure if constitutional)

**Policy Review Needed:**
- Customer requests exception to governance rules ("just this once" requests)
- Customer wants to bypass approval gates for specific Skill (weakens governance)
- Customer proposes custom Job with unusual characteristics (industry not supported, >10 Skills)

**Budget Limits Exceeded:**
- Emergency budget increase >$50/month (e.g., customer wants $100/month budget for single agent)
- Platform budget at 100% utilization (no budget for new agents)

**Agent Suspension Appeals:**
- Customer disputes Manager suspension by Genesis
- Customer wants suspended agent reinstated without re-certification

**Process:**
1. Governor clicks "Escalate to Platform Governor" in mobile app
2. Platform Governor receives escalation with full context (approval request, customer history, constitutional implications)
3. Platform Governor reviews within **4 hours** (business hours SLA)
4. Platform Governor provides binding decision + rationale
5. Decision becomes **Precedent Seed** if affects other customers (Genesis reviews for generalization)

---

## 8. Offline Approval Queue & Sync

**Problem:** Governor may be offline when approval request arrives (sleeping, meeting, airplane mode).

**Solution:** Approval requests queue locally on Governor's mobile device, sync when reconnected.

### 8.1 Offline Queue Behavior

**When Governor Offline:**
1. Approval requests sent to mobile push notification service (FCM, APNs)
2. Push notifications delivered when device reconnects
3. Approval requests queued in mobile app local storage
4. Governor opens app → sees queued requests with full context

**When Governor Reconnects:**
1. Mobile app syncs queued requests with backend
2. Governor sees request age (e.g., "Requested 2 hours ago")
3. Governor approves/denies as normal
4. If request >24 hours old, Manager escalated to Helpdesk (Governor still sees request for audit)

### 8.2 Urgent Approvals (Cannot Wait 24 Hours)

**Scenario:** Time-sensitive approval (e.g., "Respond to customer support ticket within 2 hours SLA").

**Process:**
1. Agent marks approval request as **URGENT** (time_sensitivity: <2 hours)
2. Mobile push notification uses **high priority** (triggers sound even if Do Not Disturb)
3. If Governor doesn't respond within urgency window → Manager escalates to **Backup Governor** (if designated)
4. If no Backup Governor → Manager fails skill, logs to errors.jsonl, notifies customer of SLA miss

**Safeguard:** Agents cannot abuse URGENT flag. Genesis monitors urgency usage, suspends agents marking >30% of requests as URGENT without justification.

---

## 9. Audit & Transparency

### 9.1 Governor Audit Events

All Governor actions logged with hash-chain verification:

```yaml
governor_audit_events:
  MOBILE-APPROVAL-REQUESTED:
    timestamp: ISO8601
    approval_request_id: UUID
    agent_id: UUID
    skill_id: UUID
    think_phase_summary: OBJECT
    act_phase_preview: OBJECT
    observe_phase_preview: OBJECT
    urgency_level: ENUM (NORMAL, HIGH, URGENT)
    hash_previous: STRING
    
  MOBILE-APPROVAL-APPROVED:
    timestamp: ISO8601
    approval_request_id: UUID
    governor_id: UUID
    decision_rationale: STRING (optional, if Governor provides feedback)
    approval_context: OBJECT (which Think→Act→Observe context Governor saw)
    hash_previous: STRING
    
  MOBILE-APPROVAL-DENIED:
    timestamp: ISO8601
    approval_request_id: UUID
    governor_id: UUID
    denial_reason: STRING (required, helps agent learn)
    hash_previous: STRING
    
  MOBILE-APPROVAL-DEFERRED:
    timestamp: ISO8601
    approval_request_id: UUID
    governor_id: UUID
    deferred_until: ISO8601
    deferral_reason: STRING (optional)
    hash_previous: STRING
    
  MOBILE-APPROVAL-ESCALATED:
    timestamp: ISO8601
    approval_request_id: UUID
    governor_id: UUID
    escalation_reason: STRING (required)
    platform_governor_assigned: UUID
    hash_previous: STRING
    
  EMERGENCY-BUDGET-APPROVED:
    timestamp: ISO8601
    agent_id: UUID
    budget_increase_amount: FLOAT
    new_budget_limit: FLOAT
    governor_rationale: STRING
    hash_previous: STRING
    
  JOB-PRICING-APPROVED:
    timestamp: ISO8601
    job_id: UUID
    approved_price_inr: INTEGER
    pricing_breakdown: OBJECT
    trial_started: BOOLEAN
    hash_previous: STRING
```

### 9.2 Governor Dashboard (Mobile App)

**Approval History:**
- All past approvals/denials shown with timestamps
- Filter by agent, skill, date range
- Export approval history (CSV, JSON)

**Budget Utilization:**
- Per-agent query budget utilization (bar chart: 0-100%)
- Platform budget utilization (total cost across all agents)
- Cost breakdown (which Skills consuming most queries)

**Agent Performance:**
- Agent ratings (Governor rates agent after each skill execution)
- Skill execution times (actual vs estimated)
- Approval acceptance rate (how often Governor approves vs denies)

**Precedent Seed Visibility:**
- Which Precedent Seeds used by agents (e.g., "Your agents used GEN-002 20 times this week")
- New seeds approved by Genesis (Governor sees platform learning)

---

## 10. Learning Feedback Loop (Governor Approvals → Precedent Seeds)

**Key Insight:** Governor approvals with **high confidence** (>0.9) and **repeated pattern** (3+ times) become **Precedent Seeds**.

### 10.1 Approval Pattern Detection

**Trigger Conditions:**
1. Governor approves same type of action 3+ times (e.g., "Publish to WordPress" approved 3x)
2. Agent confidence score >0.9 for all 3 approvals (constitutional queries consistent)
3. No denials for same action type in past 30 days (pattern is stable)

**Process:**
1. Manager detects approval pattern
2. Manager drafts **Precedent Seed** documenting pattern:
   ```yaml
   seed_id: "GOV-001"  # Assigned by Genesis after approval
   type: "approval_boundary"
   principle: "Governor can pre-approve WordPress publishing if content HIPAA-compliant"
   rationale: |
     Governor approved 3 WordPress publishing requests for Healthcare blog posts.
     All 3 requests had:
     - Agent confidence >0.9 (constitutional queries passed)
     - HIPAA compliance validated via Fact-Check Skill
     - No customer PII in content
     Pattern suggests Governor trusts this action type when conditions met.
   concrete_example: |
     Think: Agent queries constitution "Can I publish to WordPress?" → ESCALATE (requires approval)
     Act: Agent validates HIPAA compliance, uploads draft
     Observe: Governor approves, content published
   approved_by: "Genesis"
   applies_to: ["Healthcare", "WordPress_publishing"]
   ```
3. Manager submits seed to Genesis for review
4. Genesis approves seed → Adds to vector DB → Syncs to all agent caches
5. **Future Impact:** Next time agent queries "Can I publish to WordPress?", agent retrieves GOV-001 seed, confidence increases to 0.95+, **fewer approval requests** (Governor pre-approved pattern)

**Benefit:** Platform learns from Governor approvals, reducing approval fatigue over time while preserving safety.

---

## 11. Safety & Containment

### 11.1 Governor Cannot Weaken Governance

**Constitutional Safeguard:** Governor cannot approve actions that weaken L0 principles, even if convenient.

**Examples of Prohibited Approvals:**
- ❌ "Skip approval gate for all WordPress publishing" (weakens deny-by-default)
- ❌ "Stop logging to audit trail for this agent" (weakens auditability)
- ❌ "Allow agent to access customer PII without Fact-Check Skill" (weakens privacy protection)

**Enforcement:**
- Vision Guardian reviews all Governor approvals for constitutional compliance
- If Governor attempts prohibited approval → Vision Guardian **blocks approval**, logs ethics alert
- If Governor repeatedly attempts weakening (>3x in 24 hours) → Vision Guardian terminates Governor session, escalates to Platform Governor

### 11.2 Governor Session Security

**Authentication:**
- Governor authenticates via OAuth (Google, Microsoft, GitHub)
- Multi-factor authentication (MFA) required for production environments
- Session expires after 7 days of inactivity (re-authenticate required)

**Authorization:**
- Governor can only approve actions for **their engagement** (no cross-engagement approvals)
- Backup Governor designated via explicit delegation (not automatic)
- Platform Governor has cross-engagement authority (reviews escalations across all customers)

**Audit:**
- All Governor logins logged (IP address, device, timestamp)
- Failed authentication attempts logged (security monitoring)
- Suspicious approval patterns trigger Vision Guardian review (e.g., approving 100+ requests in 1 hour)

---

## 12. Decision Boundaries Summary

**Governor Decides (External Authority):**
- ✅ External execution (publishing, communication, API writes)
- ✅ Emergency budget increases (up to $50/month)
- ✅ Job pricing approval
- ✅ Agent suspension appeals (escalated to Platform Governor)
- ✅ Backup Governor designation

**Governor CANNOT Decide (Must Escalate):**
- ❌ Constitutional changes (L0/L1 amendments)
- ❌ Weakening governance rules (approval gates, audit requirements)
- ❌ Platform budget increases (>$50/month)
- ❌ Governance agent suspension (Genesis, Vision Guardian, Systems Architect)
- ❌ Overriding Vision Guardian ethics decisions

**Manager Decides (Internal Authority):**
- ✅ Internal task delegation (which agent works on which task)
- ✅ Draft review (approve internal deliverables for Governor review)
- ✅ Progress tracking (monitor agent execution status)
- ✅ Blocker resolution (reassign tasks if agent blocked)

**Genesis Decides (Certification Authority):**
- ✅ Agent creation and suspension
- ✅ Job/Skills certification
- ✅ Precedent Seed approval
- ✅ Re-certification triggers (constitution changes, failure patterns)

---

## 13. Mobile UX Principles

**5-Minute Approval Latency Target:**
- Governor sees approval request within seconds (push notification)
- Think→Act→Observe context loads in <2 seconds (mobile-optimized)
- Governor taps "Approve" → Agent resumes in <5 seconds (low-latency API)

**Offline-First Design:**
- Approval requests queue locally when offline
- Governor can review requests without internet (cached context)
- Decisions sync when reconnected (no approval lost)

**Progressive Disclosure:**
- Governor sees high-level summary first ("Publish blog post to WordPress?")
- Tap "More Details" → See full Think→Act→Observe context
- Tap "Constitutional Queries" → See L0/L1 chunks retrieved
- Tap "Audit Trail" → See hash-chained log preview

**Approval Confidence Indicators:**
- 🟢 **High Confidence (>0.9):** Agent very confident, similar approvals 3+ times before → "Likely safe, consider approving"
- 🟡 **Medium Confidence (0.7-0.9):** Agent somewhat confident, novel action → "Review carefully, precedent may be set"
- 🔴 **Low Confidence (<0.7):** Agent uncertain, constitutional edge case → "Consider escalating to Platform Governor"

---

## 14. Future Enhancements (Post-Activation)

**Voice Approval (Month 6+):**
- Governor approves via voice command ("Approve blog post publishing")
- Voice biometric authentication (secure, hands-free)
- Useful for urgent approvals while driving/meeting

**Bulk Approvals (Month 3+):**
- Governor selects multiple similar requests (e.g., 5 WordPress publishing requests)
- Approve all with single tap (efficiency)
- Vision Guardian reviews bulk approvals for pattern (may suggest Precedent Seed)

**Approval Templates (Month 6+):**
- Governor creates approval templates (e.g., "Auto-approve WordPress publishing if HIPAA-compliant")
- Templates become Precedent Seeds after Genesis review
- Reduces repetitive approvals for stable patterns

---

## 15. Conclusion

The Governor is the **human anchor** of WaooaW governance, preserving **L0 deny-by-default** and **human control** principles. By providing **Think→Act→Observe context**, Governor approvals are **informed, fast, and transparent**.

**Key Principles:**
1. **Human Control:** Agents serve humans, not replace them (Governor has final say)
2. **Informed Decisions:** Think→Act→Observe context shows constitutional reasoning (no black box)
3. **Learning Feedback:** Governor approvals become Precedent Seeds (platform learns, approval fatigue decreases)
4. **Single Governor Invariant:** One Governor per engagement (prevents conflicts, enables mobile UI)
5. **Vision Guardian Failsafe:** Break-glass authority if Governor violates ethics (constitutional safeguard)

**Next Steps:**
- Phase 3: Implement mobile UI with Think→Act→Observe context (Skill approval screen)
- Phase 4: Integrate approval workflow with Manager delegation (approval requests flow through message bus)
- Phase 6: Implement learning feedback loop (Governor approvals → Precedent Seeds)

---

**Charter Approved By:** Constitutional Amendment AMENDMENT-001  
**Charter Version:** 1.0  
**Last Updated:** 2026-01-07  
**Next Review:** 2026-02-07 (after 30 days of Governor approvals analyzed for pattern)
