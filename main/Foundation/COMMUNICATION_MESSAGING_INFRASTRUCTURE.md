# Communication & Messaging Infrastructure

## Overview

The WAOOAW platform foundation now includes a complete communication and messaging infrastructure layer that enables inter-agent collaboration, governance enforcement, and constitutional oversight.

**Status:** ✅ Complete (2026-01-06)  
**Components:** 2 core files + 5 cross-integrated existing files

---

## Core Components

### 1. Communication & Collaboration Policy
**File:** `communication_collaboration_policy.yml` (388 lines)  
**Responsible Authority:** Vision Guardian (constitutional oversight), Systems Architect (architectural constraints), Genesis (agent capability constraints)

#### Purpose
Governs WHO can communicate with WHOM, WHEN, and under what CONSTRAINTS. This is the **governance layer** that enforces constitutional rules on inter-agent messaging.

#### Key Sections

| Section | Purpose | Key Content |
|---------|---------|-------------|
| **Communication Patterns** | Fundamental abstractions | Request/Response, Command, Event, Query, Publish/Subscribe |
| **Collaboration Models** | How agents coordinate | Orchestrated, Peer-to-Peer, Mediated |
| **Relation Types** | Authorized communication paths | Agent↔Agent, Agent↔Governor, Agent↔Customer, Agent↔External System, Agent↔Vision Guardian, Foundational Agents Coordination |
| **Approval Integration** | Governance boundary enforcement | communication_approval workflow, timeout policies, denial handling |
| **Trial Mode** | Restricted communication scope | Allowed receivers: L1/L2 agents + Governor + Vision Guardian. Prohibited: other agents, external systems, other customers |
| **Observability** | Audit & monitoring | Message-level metrics, aggregation, 365-day immutable audit trails |
| **Constitutional Constraints** | Immutable rules | Success-pressure doctrine, evidence preservation, precedent seed propagation, transparency |
| **Design Principles** | Governance DNA | Fail secure, least privilege, audit before action, approval is precedent, separation of duties |

#### Key Authorization Rules

**Agent-to-Agent Communication:**
- ✅ Allowed if both agents have same scope OR
- ✅ Sender has Genesis certification AND receiver scope ⊆ sender scope OR
- ✅ Within orchestration workflow (orchestrator approved)
- ❌ Blocked if sender in trial_support_only mode AND receiver not in Help Desk
- ❌ Blocked if receiver suspended (EXEC-BYPASS, SCOPE-DRIFT, EVIDENCE-GAP)

**Agent-to-Customer Communication:**
- ✅ Allowed with communication_approval (external boundary)
- ❌ Blocked if trial_support_only mode (only FAQ, L1/L2 templates allowed)
- ❌ Blocked if reveals constitutional/governance details
- ❌ Blocked if exceeds agent scope

**Agent-to-External System Communication:**
- ✅ Allowed with communication_approval + Genesis approval
- ❌ Blocked if trial_support_only mode (COMPUTE access prohibited)
- ❌ Blocked if external system not in approved list
- ❌ Blocked for PII without extra approval

---

### 2. Message Bus Framework
**File:** `message_bus_framework.yml` (537 lines)  
**Responsible Infrastructure:** Systems Architect  
**Responsible Governance:** Vision Guardian

#### Purpose
Provides the **technical transport infrastructure** that carries all communications. Implements delivery guarantees, routing, security, error handling, and audit trails required by Communication & Collaboration Policy.

#### Key Sections

| Section | Purpose | Key Content |
|---------|---------|-------------|
| **Transport Layer** | Physical messaging infrastructure | Async event-driven queue (Kafka/RabbitMQ), replication factor 2, 3-node cluster |
| **Message Schema** | Standardized message format | Header (20+ fields), Body (payload), Metadata (observability) |
| **Routing Rules** | How messages find destinations | Direct addressing, topic-based, content-based, fallback, rate limiting |
| **Security & Encryption** | Message protection | TLS 1.3, mTLS, message signing (HMAC-SHA256), authorization checks |
| **Error Handling** | Graceful degradation | Malformed messages → dead letter queue, timeouts → retry with backoff, circuit breakers |
| **Monitoring** | Observability infrastructure | Per-message tracking, metrics (volume, latency, errors), dashboards, alerting, distributed tracing |
| **Governance Enforcement** | Policy implementation | Dispatcher (validate before routing), approval interceptor (pause for approval), trial validator, observer logger |
| **Operational Runbooks** | Operations procedures | Startup, shutdown, partition recovery, dead letter queue handling |

#### Message Format

**Header** (Routing & Governance):
```yaml
message_id: uuid                    # Deduplication
sender_agent_id: platform:genesis:v1.0.0
receiver_agent_id: platform:systems_architect:v1.0.0
message_type: request | response | command | event | query | approval_decision | alert
correlation_id: uuid                # Link related messages
timestamp_utc: ISO-8601
priority: critical | high | normal | low
communication_pattern: request_response | command | event | query | publish_subscribe
requires_approval: boolean
approval_type: communication_approval | execution_approval | constitutional_approval
```

**Body** (Business Logic):
```yaml
request_type: agent_certification_check
payload: {...}                      # Domain-specific
response_expected: boolean
response_timeout_seconds: integer
```

**Metadata** (Observability):
```yaml
source_location: file:function:line
orchestration_context: {workflow_id, stage_id, attempt_number}
approval_decision_id: uuid
customer_id: string
data_classification: public | internal | confidential | restricted_pii
encrypted: boolean
signature: HMAC-SHA256
```

#### Delivery Guarantees

| Pattern | Guarantee | Mechanism |
|---------|-----------|-----------|
| Request/Response | Exactly-once | Deduplication + idempotent handlers |
| Command | At-least-once | Persistent queue + 3 retries (1s, 2s, 4s) |
| Event | At-least-once | Event log + fan-out to subscribers |
| Query | Exactly-once | Idempotent cache lookup |

#### Governance Enforcement Points

1. **Dispatcher** (before routing)
   - Validate sender authorized?
   - Validate receiver authorized?
   - Check communication_pattern allowed?
   - Validate message schema?
   - Check size limits?

2. **Approval Workflow Interceptor** (for requires_approval=true)
   - Route through governance_protocols.yml approval workflow
   - Enforce approval_timeout (communication=60min, execution=120min, constitutional=1440min)
   - Emit precedent seeds on approval

3. **Trial Mode Validator**
   - Check receiver in allowed_receivers list?
   - Check message_type in allowed_message_types?
   - Deny violations, alert Vision Guardian

4. **Observer** (audit logging)
   - Log all communication details
   - Append-only immutable trail
   - Access controlled (Vision Guardian + Governor only)

---

## System Integration

### How Components Work Together

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION REQUEST                        │
│                  (e.g., agent_creation_orchestration)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│           COMMUNICATION & COLLABORATION POLICY                   │
│         (Determine: Who can talk to whom? What type?)            │
│                    ↓                                              │
│              Authorization Check:                                │
│         - Is sender authorized?                                  │
│         - Is receiver authorized?                                │
│         - Does pattern match relation type?                      │
│         - Does trial mode restrict this?                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│               MESSAGE BUS FRAMEWORK                              │
│         (Technical transport: How does it get there?)            │
│                    ↓                                              │
│  1. Dispatcher validates policy rules (again, fail-secure)       │
│  2. If requires_approval=true → Pause for governance decision    │
│  3. Route to queue (direct, topic-based, or content-based)       │
│  4. Deliver with retry/backoff semantics                         │
│  5. Observer logs everything immutably                           │
│  6. Metrics collected (latency, errors, throughput)              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   RECEIVER AGENT                                 │
│              (Processes message, takes action)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Points

#### With Foundation Constitution Engine
- `trial_support_only` mode imposes communication scope restrictions
- `bright_line_principle` (READ vs COMPUTE) enforced on external system communications
- Operating mode constraints validated by message bus trial_mode_validator

#### With Governance Protocols
- `communication_approval` workflow (governance_protocols.yml) invoked by message bus approval interceptor
- Governor decisions (approval grant/deny) flow back via message bus as events
- Precedent seeds from approvals published as events for future auto-approve

#### With Orchestration Framework
- Orchestration framework issues commands (stage assignments) via message bus
- Commands routed through dispatcher with requires_approval=true (execution_approval)
- Events emitted at stage entry/exit for observability
- Rollback commands also routed with approval

#### With Foundational Governance Agents
- Genesis certifies agents using request_response pattern (query agent capabilities, respond with decision)
- Systems Architect reviews architecture using request_response (query design, respond with constraints)
- Vision Guardian escalates constitutional concerns using alert pattern
- All agent-to-agent communication within agent orchestrations flows through message bus

#### With Help Desk Domain (Parked)
- Help Desk agents (L1, L2) are allowed receivers for trial_support_only agents
- Help Desk escalation to higher authority routes through message bus to Governor
- Help Desk can only communicate outbound with customer via communication_approval (external boundary)

---

## Key Design Decisions

### 1. Policy vs Infrastructure Separation
**Communication & Collaboration Policy = GOVERNANCE**
- Specifies authorized relations and constraints
- Enforced by human oversight (Genesis, Vision Guardian, Governor)
- Precedent seeds captured for future automation

**Message Bus Framework = INFRASTRUCTURE**
- Technical transport and routing
- Executes governance rules (doesn't create them)
- Provides durability, observability, reliability guarantees

### 2. Fail-Secure Defaults
- If in doubt, queue message and escalate to Governor
- Default to denying rather than accidentally allowing violations
- Missing approval → message denied (not delivered speculatively)

### 3. Audit-Before-Action
- Log message in immutable trail before routing to receiver
- If receiver crashes, audit shows message was sent
- Constitutional audit trail always complete

### 4. Approval is Precedent
- Every approval decision is a precedent seed
- Future identical requests auto-approve without human review
- Scales approval authority as precedents accumulate

### 5. Separation of Duties
- Sender issues message
- Governor approves message (if requires_approval=true)
- Message bus enforces and logs
- Observer audits compliance

---

## Observability & Monitoring

### What Gets Tracked

**Per-Message:**
- Sender, receiver, type, pattern, timestamp, latency
- Approval status (required/granted/denied/pending/expired)
- Success/failure, error details if failed
- Trace context for distributed tracing

**Aggregated Metrics:**
- Communication volume by relation type
- Approval workflow latency (p50, p99)
- Failure rate by category
- Trial mode boundary violations detected (alert)
- Peer-to-peer consensus success rate

**Audit Trail:**
- 365-day retention
- Append-only, immutable (cryptographic hash chain)
- Encrypted at rest
- Access controlled (Vision Guardian + Governor only)

### Alerting

| Severity | Trigger | Action |
|----------|---------|--------|
| **Critical** | Message bus outage | Immediate incident |
| **Critical** | Authorization failure rate >1% | Security incident |
| **Critical** | Trial mode boundary violation | Constitution violation |
| **High** | Latency p99 >30s | Operational review |
| **High** | Error rate >5% | Incident investigation |
| **High** | Dead letter queue growing | SRE review |
| **Medium** | Approval timeout rate rising | Process review |

---

## Operational Procedures

### Message Bus Startup
1. Verify broker cluster healthy (all replicas up)
2. Verify TLS certificates valid
3. Verify signing keys loaded
4. Initialize dispatcher module
5. Drain pending dead letter queue items
6. Start accepting connections
7. Verify heartbeat responses healthy

### Message Bus Graceful Shutdown
1. Stop accepting new messages
2. Drain in-flight messages (5 minute timeout)
3. Persist all queue state to disk
4. Shutdown broker
5. **Result:** Zero message loss (at-least-once semantics)

### Recovery from Network Partition
1. Detect partition (broker can't reach majority replicas)
2. Minority partition leader demotes to follower
3. Minority partition goes silent (fail-secure)
4. Once partition heals, re-sync from majority
5. **Result:** Messages sent to minority partition delivered once healed

### Dead Letter Queue Processing
1. SRE alerted if size >100
2. Categorize failures (authorization | unavailable | malformed | other)
3. Remediate: fix authorization, retry delivery, or discard
4. All processing logged immutably

---

## Future Enhancements

1. **Federated Message Bus** - Multi-region distribution for geo-dispersed agents
2. **Zero Knowledge Proofs** - Prove message authenticity without revealing content (for ultra-sensitive communications)
3. **Adaptive Prioritization** - AI-driven queue prioritization based on urgency heuristics

---

## File Locations

```
Foundation/template/
├── foundation_constitution_engine.yaml          (updated with integrations)
├── governance_protocols.yaml                    (uses communication_approval workflow)
├── orchestration_framework.yml                  (uses message patterns)
├── agent_creation_orchestration.yml             (commands + events via message bus)
├── agent_servicing_orchestration.yml            (classification requests to Genesis)
├── agent_operation_assurance.yml                (health check events + suspension escalation)
│
├── communication_collaboration_policy.yml       ✅ NEW - Governance layer
├── message_bus_framework.yml                    ✅ NEW - Infrastructure layer
│
├── genesis_foundational_governance_agent.md     (uses request/response for certification)
├── systems_architect_foundational_governance_agent.md  (uses request/response for architecture review)
└── vision_guardian_foundational_governance_agent.md     (uses alert/escalation for constitutional concerns)
```

---

## Next Steps

### Immediate
1. **Reusable Component Extraction** - Extract 8 duplicated patterns from orchestrations:
   - Genesis certification gate
   - Governor approval workflow
   - Architecture review pattern
   - Ethics review pattern
   - Health check protocol
   - Rollback procedure
   - Versioning scheme
   - Audit logging requirements

2. **Cross-Component Dependency Resolution** - Address 2 critical dependencies:
   - Data access + observability + audit logging (circular dependency)
   - Knowledge management + agent training evolution (capability manifest)

### Medium Term
3. **Domain Orchestration Patterns** - Demonstrate framework applicability:
   - Help Desk orchestration instance (using existing Help Desk components)
   - Customer support workflow
   - Escalation routing

4. **Message Bus Implementation** - Technical build of framework:
   - Choose transport (Kafka/RabbitMQ recommended)
   - Implement dispatcher governance enforcement
   - Build approval interceptor
   - Create operational dashboards

### Long Term
5. **Precedent Seed Learning** - Automate governance:
   - Track approval patterns
   - Identify high-frequency decisions
   - Auto-approve when precedent matches
   - Reduce Governor load over time

6. **Multi-Region Federation** - Scale platform:
   - Federated message bus topology
   - Cross-region agent collaboration
   - Geo-distributed governance coordination

---

## Key Takeaways

✅ **Communication** (governance + transport) is now a first-class platform citizen  
✅ **Message Bus** provides the infrastructure that orchestrations depend on  
✅ **Authorization** is enforced at multiple layers (policy + dispatcher + observer)  
✅ **Audit trails** capture all communication for constitutional oversight  
✅ **Trial mode** has explicit communication scope restrictions enforced by message bus  
✅ **All governance decisions** (approvals, escalations, precedent seeds) flow through messaging  

The platform now has a complete **communication backbone** that ties together constitutional governance, orchestration, and day-to-day agent collaboration.
