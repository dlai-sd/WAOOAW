# WowVision Prime Agent - Project Plan

**Project Type**: Agent Development Project  
**Agent**: WowVision Prime (Vision Guardian)  
**Status**: Planning → Implementation Ready  
**Timeline**: 8 weeks (parallelizable)  
**Baseline**: v0.2.7 (Common Components Library)  
**Target**: v0.4 (WowVision Prime Production-Ready)

---

## Executive Summary

### Project Objectives

Build **WowVision Prime** - WAOOAW's first production agent - as the Vision Guardian for the platform. WowVision Prime validates all architectural decisions, code, and documentation against WAOOAW's 3-layer vision stack.

**Success Criteria:**
1. ✅ Agent inherits from WAAOOWAgent base class correctly
2. ✅ Validates files against 3-layer vision stack (deterministic + LLM)
3. ✅ Creates GitHub issues for violations
4. ✅ Comments on PRs with approval/rejection
5. ✅ Wakes up on events (file creation, PR opened)
6. ✅ Learns from human feedback (escalation responses)
7. ✅ Operates within budget (<$25/month)
8. ✅ Achieves 95%+ vision compliance detection accuracy
9. ✅ Deploys to GitHub Actions (automated)
10. ✅ Integrates common components library (v0.2.7)

### Current Status (v0.2.7)

**Completed (80%)**:
- ✅ WAAOOWAgent base class (6-step wake protocol, decision framework)
- ✅ WowVisionPrime class structure (waooaw/agents/wowvision_prime.py)
- ✅ VisionStack class (waooaw/vision/vision_stack.py)
- ✅ Database schema (docs/vision/schema.sql - 10 tables)
- ✅ Specialization defined (coe_name, domain, expertise, constraints)
- ✅ Deterministic decision rules (phase rules, file type validation)
- ✅ Common components library designed (8 components for reuse)
- ✅ Message bus architecture designed
- ✅ Orchestration layer designed

**Gaps (20%)**:
- ❌ Event-driven wake (currently manual wake_up())
- ❌ GitHub integration (create issues, comment on PRs)
- ❌ LLM decision making (ambiguous cases)
- ❌ Learning from feedback (escalation processing)
- ❌ Common components integration (CacheHierarchy, ErrorHandler, ObservabilityStack)
- ❌ Resource management (token budgets, rate limiting)
- ❌ Production deployment (GitHub Actions workflow)
- ❌ Monitoring dashboard (metrics, alerts)

### Deliverables

**Code:**
- Updated `waooaw/agents/wowvision_prime.py` (production-ready)
- New `waooaw/messaging/message_bus.py` (event-driven wake)
- New `waooaw/integrations/github_helpers.py` (issue creation, PR comments)
- New `.github/workflows/wowvision-prime.yml` (GitHub Actions deployment)
- Updated `waooaw/agents/base_agent.py` (integrate common components)

**Documentation:**
- Updated docs/vision/WOWVISION_PRIME_SETUP.md (deployment guide)
- New docs/vision/OPERATIONS_GUIDE.md (runbook)
- New docs/vision/TESTING_GUIDE.md (test scenarios)

**Testing:**
- Unit tests (95% coverage)
- Integration tests (end-to-end scenarios)
- Load tests (100 wake cycles/day)
- Cost tests (verify <$25/month)

**Deployment:**
- GitHub Actions workflow (automated deployment)
- Monitoring dashboard (Grafana/Prometheus)
- Alert rules (error rate, cost, latency)

---

## Requirements

### Functional Requirements

**FR1: Vision Validation**
- **Description**: Validate files against 3-layer vision stack
- **Acceptance Criteria**:
  - Layer 1 (Core): Immutable constraints checked (e.g., "No Python in Phase 1")
  - Layer 2 (Policies): Agent-managed rules checked (e.g., phase_rules, file type rules)
  - Layer 3 (Context): Runtime state validated
  - Deterministic rules handle 80%+ of decisions (<1ms latency)
  - LLM handles ambiguous cases (<2s latency)
- **Priority**: P0 (Critical)

**FR2: GitHub Integration**
- **Description**: Create issues and comment on PRs
- **Acceptance Criteria**:
  - Violations → GitHub issue with title "🚨 Vision Violation: {filename}"
  - Issue body includes: file, commit, author, violation reason, confidence, citations
  - PR comments with approval ("✅ Vision compliant") or rejection ("❌ Violations found, see issue #X")
  - Issues tagged with "vision-violation", "agent-escalation"
- **Priority**: P0 (Critical)

**FR3: Event-Driven Wake**
- **Description**: Agent wakes up on relevant events (file creation, PR opened)
- **Acceptance Criteria**:
  - GitHub webhook → Message Bus → Agent wake
  - should_wake() filters irrelevant events (e.g., README edits don't wake agent)
  - Wake latency <5s (p95)
  - Idempotency (duplicate events handled gracefully)
- **Priority**: P0 (Critical)

**FR4: Learning from Feedback**
- **Description**: Agent learns from human escalation responses
- **Acceptance Criteria**:
  - Reads GitHub issue comments with "APPROVE:" or "REJECT:"
  - Updates decision patterns in knowledge_base table
  - Similar future cases use learned patterns (deterministic)
  - Learning recorded in agent_decisions table with confidence increase
- **Priority**: P1 (High)

**FR5: Common Components Integration**
- **Description**: Use common components library (v0.2.7) for infrastructure
- **Acceptance Criteria**:
  - CacheHierarchy: Decision caching (90% hit rate = 90% fewer LLM calls)
  - ErrorHandler: Retry LLM calls (exponential backoff), circuit breaker
  - ObservabilityStack: Structured logging, Prometheus metrics, OpenTelemetry traces
  - StateManager: Versioned context persistence (atomic updates)
  - SecurityLayer: HMAC message signatures (message bus)
  - ResourceManager: Token budgets ($25/month limit), rate limiting
- **Priority**: P1 (High)

**FR6: Resource Management**
- **Description**: Operate within budget and rate limits
- **Acceptance Criteria**:
  - Token budget: 500K tokens/month (~$25)
  - Cost tracking: Real-time cost accumulation (per decision, per day, per month)
  - Budget alerts: Alert at 80% budget ($20), hard stop at 100% ($25)
  - Graceful degradation: If budget exceeded, use deterministic only (no LLM)
- **Priority**: P1 (High)

### Non-Functional Requirements

**NFR1: Performance**
- Wake latency: <5s (p95)
- Decision latency: <500ms deterministic, <2s LLM (p95)
- Database queries: <100ms (p95)
- Vector search: <200ms (p95)

**NFR2: Reliability**
- Uptime: 99.5% (3.6 hours downtime/month acceptable)
- Error rate: <1% (99% success rate)
- Data durability: 99.999% (PostgreSQL ACID)
- Graceful degradation: Component failure ≠ agent failure

**NFR3: Cost**
- Total: <$25/month
- PostgreSQL: $0 (shared with platform)
- Pinecone: ~$5 (shared)
- Claude API: ~$20 (200 decisions/day)
- GitHub Actions: $0 (within free tier)

**NFR4: Security**
- HMAC signatures: All message bus messages
- JWT tokens: API authentication
- Audit logging: 7-year retention (compliance)
- Secret encryption: GitHub token, database password, API keys

**NFR5: Observability**
- Structured logging: JSON format, searchable
- Metrics: Prometheus (decision count, cost, latency, error rate)
- Traces: OpenTelemetry (distributed tracing)
- Dashboard: Grafana (real-time agent health)

**NFR6: Testability**
- Unit test coverage: 95% (critical infrastructure)
- Integration tests: 10+ end-to-end scenarios
- Load tests: 100 wake cycles/day sustained
- Chaos tests: Redis down, database slow, LLM timeout

### Vision Compliance Requirements

**VCR1: Cost Optimization**
- 90% cache hit rate (CacheHierarchy)
- Token budgets enforced (ResourceManager)
- Deterministic first, LLM only when necessary

**VCR2: Zero Risk**
- Circuit breaker prevents cascading failures
- Graceful degradation on component failure
- Human escalation for ambiguous/risky decisions
- Audit trail for all decisions

**VCR3: Human Escalation**
- Max 3 retries then escalate (ErrorHandler)
- GitHub issues for violations (human review)
- Learning from human feedback

**VCR4: Simplicity**
- 80% use deterministic rules (simple, fast, free)
- Sensible defaults (no config needed for basic use)
- Escape hatches (agent can bypass components if needed)

**VCR5: Marketplace DNA**
- Per-agent isolation (cache, budgets, state)
- Agent personality preserved (WowVision Prime = precise, principle-driven)
- Status visible (🟢 Available, 🟡 Working, 🔴 Offline)

---

## Architecture Blueprint

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL SYSTEMS                           │
├─────────────────────────────────────────────────────────────────────┤
│  GitHub                                                             │
│  - Webhook (file created, PR opened)                                │
│  - API (create issue, comment on PR)                                │
└─────────────────────────────────────────────────────────────────────┘
                            ↓ webhook
┌─────────────────────────────────────────────────────────────────────┐
│                       MESSAGE BUS (Redis Streams)                   │
│  - Event ingestion                                                  │
│  - Priority queues (5 levels)                                       │
│  - Consumer groups (per agent type)                                 │
└─────────────────────────────────────────────────────────────────────┘
                            ↓ event
┌─────────────────────────────────────────────────────────────────────┐
│                         WOWVISION PRIME AGENT                       │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  6-Step Wake Protocol                                         │ │
│  │  1. should_wake() → filter irrelevant events                  │ │
│  │  2. restore_identity() → load vision stack                    │ │
│  │  3. load_context() → cached context (CacheHierarchy)          │ │
│  │  4. get_pending_tasks() → file validations, PR reviews        │ │
│  │  5. execute_tasks() → validate against vision stack           │ │
│  │  6. save_context() → persist state (StateManager)             │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                            ↓                                        │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Decision Framework                                           │ │
│  │  - try_deterministic_decision() → 80% (phase rules, file     │ │
│  │    type rules)                                                │ │
│  │  - call_llm() → 20% (ambiguous cases, wrapped with           │ │
│  │    ErrorHandler)                                              │ │
│  │  - make_decision() → orchestrate deterministic + LLM          │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                            ↓                                        │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Actions (GitHub Integration)                                 │ │
│  │  - create_github_issue() → violations                         │ │
│  │  - comment_on_pr() → approval/rejection                       │ │
│  │  - escalate_to_human() → ambiguous decisions                  │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                            ↓                                        │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Learning & Improvement                                       │ │
│  │  - process_escalation() → read GitHub comments               │ │
│  │  - learn_from_outcome() → update knowledge_base               │ │
│  │  - improve_patterns() → increase confidence                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      COMMON COMPONENTS (v0.2.7)                     │
├─────────────────────────────────────────────────────────────────────┤
│  CacheHierarchy        ErrorHandler       ObservabilityStack        │
│  StateManager          SecurityLayer      ResourceManager           │
│  Validator             Messaging                                    │
└─────────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA STORES                                    │
├─────────────────────────────────────────────────────────────────────┤
│  PostgreSQL (10 tables)  Redis (cache)    Pinecone (vector memory) │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Components

**1. WowVisionPrime Agent Class**
- **Location**: `waooaw/agents/wowvision_prime.py`
- **Inherits**: WAAOOWAgent base class
- **Responsibilities**:
  - Override _load_specialization() → define CoE identity
  - Override _try_deterministic_decision() → vision-specific rules
  - Override _get_pending_tasks() → file validations, PR reviews
  - Override execute_task() → validate_file_creation(), validate_pr(), process_escalation()
- **Dependencies**: VisionStack, GitHub API, Common Components

**2. VisionStack Class**
- **Location**: `waooaw/vision/vision_stack.py`
- **Responsibilities**:
  - Load Layer 1 (Core Vision) from waooaw-core.yaml
  - Load Layer 2 (Policies) from waooaw-policies.yaml
  - Load Layer 3 (Context) from runtime state
  - Validate actions against all 3 layers
- **Methods**: get_core(), get_policies(), get_context(), validate_action()

**3. Message Bus**
- **Location**: `waooaw/messaging/message_bus.py`
- **Technology**: Redis Streams
- **Responsibilities**:
  - Ingest GitHub webhooks
  - Publish events to priority streams
  - Consumer groups for agent types
  - Acknowledge message processing
- **Integration**: SecurityLayer (HMAC signatures), ObservabilityStack (event metrics)

**4. GitHub Integration**
- **Location**: `waooaw/integrations/github_helpers.py`
- **Methods**:
  - create_issue(title, body, labels, assignee)
  - comment_on_pr(pr_number, comment)
  - get_recent_commits(since)
  - get_open_prs()
- **Auth**: GitHub Personal Access Token (repo, workflow scopes)

**5. Common Components Integration**
- **CacheHierarchy**: L1 (memory), L2 (Redis), L3 (PostgreSQL)
  - Use for: Decision caching, context caching, similarity search results
- **ErrorHandler**: Retry, circuit breaker, DLQ
  - Use for: LLM calls, GitHub API calls, database operations
- **ObservabilityStack**: Logs, metrics, traces
  - Use for: All wake cycles, decisions, actions
- **StateManager**: Versioned state persistence
  - Use for: Context saving, workflow state
- **SecurityLayer**: HMAC, JWT, audit logging
  - Use for: Message bus, API calls
- **ResourceManager**: Token budgets, rate limiting
  - Use for: LLM call gating, cost tracking

### Database Schema

**10 Tables (docs/vision/schema.sql)**:
1. `agent_context` - Versioned context snapshots
2. `agent_decisions` - Decision log with vision validation
3. `vision_violations` - Violation tracking
4. `human_escalations` - Escalation tracking
5. `agent_health` - Health metrics
6. `knowledge_base` - Learned patterns
7. `wowvision_memory` - Long-term memory
8. `wowvision_state` - Operational state
9. `wowvision_metrics` - Performance metrics
10. `wowvision_escalations` - Escalation history

### Data Flow: File Creation Scenario

**Step 1: Event Ingestion**
```
Developer creates frontend/new-page.html
   ↓ (GitHub webhook)
GitHub → Message Bus → wowvision.events.file_created
   ↓ (Redis Streams)
Message published to priority stream (priority=3, medium)
```

**Step 2: Agent Wake**
```
WowVision Prime polls message bus
   ↓ (should_wake())
Check: Is this event relevant? Yes (file creation)
   ↓ (restore_identity())
Load vision stack (Layer 1-3 from VisionStack)
   ↓ (load_context())
Load cached context from CacheHierarchy (L1 → L2 → L3)
```

**Step 3: Task Execution**
```
_get_pending_tasks() → [validate_file_creation]
   ↓ (execute_task())
validate_file_creation(filename="frontend/new-page.html")
   ↓ (make_decision())
try_deterministic_decision() → Check phase rules, file type rules
   ↓ (if ambiguous)
call_llm() → Claude Sonnet 4.5 with ErrorHandler (retry, circuit breaker)
   ↓ (decision)
Decision(approved=False, reason="Missing brand color", confidence=0.92)
```

**Step 4: Action**
```
if not decision.approved:
   ↓ (create_github_issue())
GitHub issue created: "🚨 Vision Violation: frontend/new-page.html"
   ↓ (ObservabilityStack)
Log event: "vision_violation_detected"
   ↓ (StateManager)
Save escalation to human_escalations table
```

**Step 5: Learning (Later)**
```
Human responds in GitHub issue: "APPROVE: This is acceptable, update vision rules"
   ↓ (process_escalation())
Read comment, extract decision (APPROVE)
   ↓ (learn_from_outcome())
Update knowledge_base: "frontend/*.html with missing brand color → acceptable if..."
   ↓ (improve_patterns())
Next time: Deterministic rule handles this case (confidence=1.0, cost=$0)
```

---

## Work Breakdown Structure (WBS)

### Epic 1: Message Bus & Event-Driven Wake (Week 1-2)

**Objective**: Agent wakes up on relevant events (file creation, PR opened)

**Story 1.1: Implement Message Bus Core** (3 days)
- **Tasks**:
  - Create `waooaw/messaging/message_bus.py` (MessageBus class)
  - Implement publish(topic, message, priority)
  - Implement subscribe(topics, consumer_group, handler)
  - Implement acknowledge(message_id)
  - Add SecurityLayer integration (HMAC signatures)
- **Acceptance Criteria**:
  - Messages published to Redis Streams
  - Consumer groups read messages with load balancing
  - Messages acknowledged after processing
  - HMAC signatures validated
- **Testing**: Unit tests (95% coverage), integration tests (publish → subscribe)
- **Estimate**: 3 days (S)

**Story 1.2: Implement should_wake() Filter** (2 days)
- **Tasks**:
  - Add should_wake(event) method to base_agent.py
  - Implement wake filters in wowvision_prime.py
    - Wake on: file_created, pr_opened, issue_comment (escalation)
    - Skip: README edits, config changes, bot commits
  - Add event type constants (EVENT_FILE_CREATED, EVENT_PR_OPENED)
- **Acceptance Criteria**:
  - Irrelevant events filtered (agent doesn't wake)
  - Relevant events processed (agent wakes)
  - Wake decision logged (ObservabilityStack)
- **Testing**: Unit tests (10+ event scenarios)
- **Estimate**: 2 days (S)

**Story 1.3: GitHub Webhook Integration** (3 days)
- **Tasks**:
  - Create webhook endpoint (FastAPI) at `/webhooks/github`
  - Validate GitHub webhook signature (HMAC)
  - Transform webhook payload to message bus event
  - Configure GitHub webhook (file push, PR events)
- **Acceptance Criteria**:
  - Webhook receives GitHub events
  - Signature validated (reject invalid)
  - Events published to message bus
  - Latency <1s (webhook → message bus)
- **Testing**: Integration tests (mock GitHub webhook), load tests (100 events/sec)
- **Estimate**: 3 days (M)

**Story 1.4: End-to-End Wake Test** (2 days)
- **Tasks**:
  - Create test scenario: File created → Webhook → Message Bus → Agent wake
  - Validate 6-step wake protocol executes
  - Measure wake latency (target <5s p95)
  - Test idempotency (duplicate events)
- **Acceptance Criteria**:
  - Wake latency <5s (p95)
  - Duplicate events handled gracefully
  - Context loaded correctly
  - Tasks queued correctly
- **Testing**: Integration tests (end-to-end), chaos tests (Redis down)
- **Estimate**: 2 days (S)

**Dependencies**: Common Components (SecurityLayer, ObservabilityStack)  
**Parallel Work**: Can start Story 1.1-1.2 immediately

---

### Epic 2: GitHub Integration & Output Generation (Week 3-4)

**Objective**: Agent creates GitHub issues for violations, comments on PRs

**Story 2.1: Implement GitHub Helpers** (3 days)
- **Tasks**:
  - Create `waooaw/integrations/github_helpers.py`
  - Implement create_issue(title, body, labels, assignee)
  - Implement comment_on_pr(pr_number, comment)
  - Implement get_recent_commits(since)
  - Implement get_open_prs()
  - Add ErrorHandler integration (retry GitHub API calls)
- **Acceptance Criteria**:
  - Issues created successfully
  - PR comments posted successfully
  - Commits fetched correctly
  - PRs fetched correctly
  - API errors retried (exponential backoff)
- **Testing**: Unit tests (mock GitHub API), integration tests (real GitHub)
- **Estimate**: 3 days (M)

**Story 2.2: Implement create_github_issue() in WowVision** (2 days)
- **Tasks**:
  - Add _escalate_violation() method to wowvision_prime.py
  - Format issue title: "🚨 Vision Violation: {filename}"
  - Format issue body: file, commit, author, violation reason, confidence, citations
  - Add labels: "vision-violation", "agent-escalation"
  - Log escalation to human_escalations table
- **Acceptance Criteria**:
  - Issues created with correct format
  - All required fields populated
  - Escalation logged in database
  - Issue number saved for tracking
- **Testing**: Integration tests (create issue, verify content)
- **Estimate**: 2 days (S)

**Story 2.3: Implement comment_on_pr() in WowVision** (2 days)
- **Tasks**:
  - Add _comment_on_pr() method to wowvision_prime.py
  - Format approval: "✅ Vision compliant. All checks passed."
  - Format rejection: "❌ Violations found. See issue #{issue_number}"
  - Add decision summary (method, confidence, violations count)
- **Acceptance Criteria**:
  - PR comments posted successfully
  - Approval/rejection clear
  - Issue linked in rejection
  - Decision summary included
- **Testing**: Integration tests (comment on PR, verify content)
- **Estimate**: 2 days (S)

**Story 2.4: Create Issue Template** (1 day)
- **Tasks**:
  - Create `.github/ISSUE_TEMPLATE/agent_violation.md`
  - Define fields: file, commit, author, violation, confidence, citations
  - Add response options: "APPROVE:", "REJECT:", "MODIFY:"
- **Acceptance Criteria**:
  - Template used automatically
  - Fields pre-filled
  - Response options clear
- **Testing**: Manual test (create issue via template)
- **Estimate**: 1 day (XS)

**Story 2.5: End-to-End Output Test** (2 days)
- **Tasks**:
  - Test scenario: Violation detected → Issue created → PR commented
  - Validate issue content correctness
  - Validate PR comment formatting
  - Measure output latency (target <2s)
- **Acceptance Criteria**:
  - Issue created within 2s of violation
  - PR comment within 1s of decision
  - All fields populated correctly
- **Testing**: Integration tests (end-to-end)
- **Estimate**: 2 days (S)

**Dependencies**: Epic 1 (message bus)  
**Parallel Work**: Can start Story 2.1 during Epic 1

---

### Epic 3: LLM Integration & Decision Making (Week 3-4)

**Objective**: Agent uses LLM for ambiguous decisions

**Story 3.1: Implement _call_llm() Method** (3 days)
- **Tasks**:
  - Add _call_llm(prompt) method to base_agent.py
  - Integrate Anthropic Claude Sonnet 4.5 API
  - Add ErrorHandler wrapper (retry, circuit breaker)
  - Add ResourceManager integration (token budget check)
  - Parse LLM response (approved, reason, confidence, citations)
  - Cache decision (CacheHierarchy)
- **Acceptance Criteria**:
  - LLM called successfully
  - Response parsed correctly
  - Errors retried (max 3 times)
  - Circuit breaker opens after 5 failures
  - Token budget enforced ($25/month limit)
  - Decisions cached (90% hit rate)
- **Testing**: Unit tests (mock LLM), integration tests (real LLM), chaos tests (LLM timeout)
- **Estimate**: 3 days (M)

**Story 3.2: Implement make_decision() Orchestration** (2 days)
- **Tasks**:
  - Add make_decision(request) method to base_agent.py
  - Try deterministic first (try_deterministic_decision())
  - Fallback to LLM if ambiguous (_call_llm())
  - Log decision (agent_decisions table)
  - Track cost (ObservabilityStack)
- **Acceptance Criteria**:
  - Deterministic tried first (80% success)
  - LLM called only when necessary (20%)
  - All decisions logged
  - Cost tracked per decision
- **Testing**: Unit tests (decision flow), integration tests (deterministic + LLM)
- **Estimate**: 2 days (S)

**Story 3.3: Enhance Deterministic Rules** (3 days)
- **Tasks**:
  - Add phase rules (phase1_foundation: no .py files)
  - Add file type rules (.md always allowed, .py forbidden in Phase 1)
  - Add path rules (waooaw/* exceptions)
  - Add brand rules (check for tagline, brand colors)
- **Acceptance Criteria**:
  - 80%+ decisions deterministic
  - Latency <1ms (deterministic)
  - Confidence 1.0 (deterministic rules)
  - Cost $0 (no LLM calls)
- **Testing**: Unit tests (50+ rule scenarios)
- **Estimate**: 3 days (M)

**Story 3.4: Decision Caching** (2 days)
- **Tasks**:
  - Integrate CacheHierarchy (L1 memory, L2 Redis, L3 PostgreSQL)
  - Cache key: hash(file_path, file_content, phase)
  - Cache LLM decisions (1 hour TTL)
  - Cache deterministic decisions (24 hour TTL)
  - Track cache hit rate (target 90%)
- **Acceptance Criteria**:
  - Cache hit rate 90%+
  - Cache latency <10ms (L1), <50ms (L2), <100ms (L3)
  - Cost savings: 90% fewer LLM calls
- **Testing**: Unit tests (cache scenarios), load tests (cache performance)
- **Estimate**: 2 days (S)

**Dependencies**: Common Components (CacheHierarchy, ErrorHandler, ResourceManager)  
**Parallel Work**: Can work on Story 3.1-3.3 in parallel

---

### Epic 4: Learning & Improvement (Week 5-6)

**Objective**: Agent learns from human feedback, improves over time

**Story 4.1: Implement process_escalation() Method** (3 days)
- **Tasks**:
  - Add process_escalation(escalation_data) to wowvision_prime.py
  - Fetch GitHub issue by number (github_helpers.get_issue())
  - Parse comments for "APPROVE:", "REJECT:", "MODIFY:"
  - Extract human decision and reasoning
  - Update escalation status (human_escalations table)
- **Acceptance Criteria**:
  - Escalations fetched correctly
  - Comments parsed accurately
  - Human decision extracted
  - Status updated (pending → resolved)
- **Testing**: Unit tests (comment parsing), integration tests (GitHub issue)
- **Estimate**: 3 days (M)

**Story 4.2: Implement learn_from_outcome() Method** (3 days)
- **Tasks**:
  - Add learn_from_outcome(decision, outcome, feedback) to base_agent.py
  - Update knowledge_base table (pattern, confidence, last_updated)
  - Increase confidence for similar patterns
  - Convert LLM decisions to deterministic rules (if confidence >0.9)
- **Acceptance Criteria**:
  - Patterns saved to knowledge_base
  - Confidence updated correctly
  - Deterministic rules created (when confidence high)
  - Learning logged (ObservabilityStack)
- **Testing**: Unit tests (learning scenarios), integration tests (pattern matching)
- **Estimate**: 3 days (M)

**Story 4.3: Implement Similarity Search** (2 days)
- **Tasks**:
  - Add _check_similar_past_decisions() to base_agent.py
  - Embed decision context (Pinecone text-embedding)
  - Search vector database (top 5 similar decisions)
  - Use similar decision if confidence >0.8
- **Acceptance Criteria**:
  - Similar decisions found (cosine similarity >0.85)
  - Latency <200ms (vector search)
  - Cost savings: Reuse past decisions
- **Testing**: Unit tests (vector search), integration tests (Pinecone)
- **Estimate**: 2 days (S)

**Story 4.4: End-to-End Learning Test** (2 days)
- **Tasks**:
  - Test scenario: Violation → Escalation → Human feedback → Learning → Future decision
  - Validate pattern saved correctly
  - Validate confidence increase
  - Validate deterministic rule created
  - Measure learning effectiveness (before/after accuracy)
- **Acceptance Criteria**:
  - Pattern reused in future decisions
  - Accuracy improvement >10%
  - Cost reduction (fewer LLM calls)
- **Testing**: Integration tests (end-to-end)
- **Estimate**: 2 days (S)

**Dependencies**: Epic 2 (GitHub integration), Epic 3 (decision making)  
**Parallel Work**: Stories can run sequentially (4.1 → 4.2 → 4.3 → 4.4)

---

### Epic 5: Common Components Integration (Week 5-6)

**Objective**: Integrate common components library (v0.2.7) into WowVision Prime

**Story 5.1: Integrate CacheHierarchy** (2 days)
- **Tasks**:
  - Add CacheHierarchy import to base_agent.py
  - Replace manual caching with CacheHierarchy
  - Cache decisions: L1 (memory), L2 (Redis), L3 (PostgreSQL)
  - Cache context: L2 (Redis), L3 (PostgreSQL)
  - Track cache metrics (hit rate, eviction rate)
- **Acceptance Criteria**:
  - Cache hit rate 90%+
  - Latency <10ms (L1), <50ms (L2), <100ms (L3)
  - Cost savings validated (90% fewer LLM calls)
- **Testing**: Unit tests (cache operations), load tests (cache performance)
- **Estimate**: 2 days (S)

**Story 5.2: Integrate ErrorHandler** (2 days)
- **Tasks**:
  - Add ErrorHandler import to base_agent.py
  - Wrap LLM calls with ErrorHandler
  - Wrap GitHub API calls with ErrorHandler
  - Wrap database operations with ErrorHandler
  - Configure retry (exponential backoff, max 3 retries)
  - Configure circuit breaker (5 failures → open 60s)
- **Acceptance Criteria**:
  - Transient errors retried (99.9% success rate)
  - Circuit breaker opens after 5 failures
  - DLQ messages sent after 3 retries
  - Escalation created for DLQ messages
- **Testing**: Chaos tests (LLM timeout, GitHub API down, database slow)
- **Estimate**: 2 days (S)

**Story 5.3: Integrate ObservabilityStack** (2 days)
- **Tasks**:
  - Add ObservabilityStack import to base_agent.py
  - Replace print() with obs.log_structured()
  - Add metrics: decision_count, decision_cost, decision_latency, error_rate
  - Add traces: wake_up(), make_decision(), execute_task()
  - Configure Prometheus metrics export
- **Acceptance Criteria**:
  - All logs structured (JSON format)
  - Metrics exported to Prometheus
  - Traces visible in Jaeger/OpenTelemetry
  - Dashboard shows real-time agent health
- **Testing**: Integration tests (metrics collection), manual test (Grafana dashboard)
- **Estimate**: 2 days (S)

**Story 5.4: Integrate StateManager** (1 day)
- **Tasks**:
  - Add StateManager import to base_agent.py
  - Replace manual context saving with StateManager
  - Versioned state persistence (atomic updates)
  - Audit trail for state changes
- **Acceptance Criteria**:
  - Context saved with version number
  - Atomic updates (no partial writes)
  - Audit trail visible in database
- **Testing**: Unit tests (state operations), chaos tests (database failure)
- **Estimate**: 1 day (XS)

**Story 5.5: Integrate SecurityLayer** (1 day)
- **Tasks**:
  - Add SecurityLayer import to message_bus.py
  - Sign messages with HMAC (message_bus.publish())
  - Verify signatures (message_bus.subscribe())
  - Audit log all decisions (security.audit_log())
- **Acceptance Criteria**:
  - Messages signed with HMAC
  - Invalid signatures rejected
  - Audit log retained for 7 years
- **Testing**: Unit tests (signature verification), security tests (tampered messages)
- **Estimate**: 1 day (XS)

**Story 5.6: Integrate ResourceManager** (2 days)
- **Tasks**:
  - Add ResourceManager import to base_agent.py
  - Check budget before LLM calls (resource_mgr.check_budget())
  - Record usage after LLM calls (resource_mgr.record_usage())
  - Set budget limit ($25/month)
  - Alert at 80% budget ($20)
  - Hard stop at 100% budget ($25)
- **Acceptance Criteria**:
  - Budget enforced (<$25/month)
  - Alerts sent at 80% budget
  - LLM calls blocked at 100% budget
  - Graceful degradation (deterministic only)
- **Testing**: Unit tests (budget scenarios), load tests (cost accumulation)
- **Estimate**: 2 days (S)

**Dependencies**: Common Components Library (Week 5-6 implementation)  
**Parallel Work**: Stories 5.1-5.6 can run in parallel

---

### Epic 6: Testing & Quality (Week 7)

**Objective**: Achieve 95% test coverage, validate all requirements

**Story 6.1: Unit Tests (95% Coverage)** (3 days)
- **Tasks**:
  - Test all methods in wowvision_prime.py (25+ tests)
  - Test decision framework (deterministic + LLM)
  - Test GitHub integration (mock API)
  - Test learning (mock database)
  - Test common components integration
  - Achieve 95% code coverage
- **Acceptance Criteria**:
  - 95% code coverage (pytest-cov)
  - All edge cases covered
  - Fast execution (<1 minute)
- **Testing**: Run pytest with coverage report
- **Estimate**: 3 days (M)

**Story 6.2: Integration Tests (End-to-End)** (3 days)
- **Tasks**:
  - Test wake → validate → issue creation (full flow)
  - Test wake → validate → PR comment (full flow)
  - Test escalation → learning → future decision (full flow)
  - Test budget enforcement → graceful degradation
  - Test error handling → retry → circuit breaker → DLQ
- **Acceptance Criteria**:
  - 10+ end-to-end scenarios
  - All requirements validated
  - Real dependencies (PostgreSQL, Redis, Pinecone, GitHub)
- **Testing**: Run integration tests in test environment
- **Estimate**: 3 days (M)

**Story 6.3: Load Tests** (2 days)
- **Tasks**:
  - Simulate 100 wake cycles/day
  - Measure latency (p50, p95, p99)
  - Measure throughput (decisions/second)
  - Validate performance targets (wake <5s, decision <500ms deterministic, <2s LLM)
- **Acceptance Criteria**:
  - Wake latency <5s (p95)
  - Decision latency <500ms deterministic, <2s LLM (p95)
  - Throughput >10 decisions/second
- **Testing**: Run locust or k6 load tests
- **Estimate**: 2 days (S)

**Story 6.4: Cost Tests** (1 day)
- **Tasks**:
  - Simulate 200 decisions/day for 30 days
  - Track LLM costs (tokens used, $ spent)
  - Validate budget enforcement (<$25/month)
  - Measure cache savings (90% hit rate)
- **Acceptance Criteria**:
  - Total cost <$25/month
  - Cache hit rate 90%+
  - Budget enforcement working
- **Testing**: Run cost simulation script
- **Estimate**: 1 day (XS)

**Story 6.5: Chaos Tests** (2 days)
- **Tasks**:
  - Test Redis down → graceful degradation (no cache, direct DB)
  - Test database slow → timeouts → fallback
  - Test LLM timeout → retry → circuit breaker
  - Test GitHub API down → DLQ → escalation
- **Acceptance Criteria**:
  - Component failure ≠ agent failure
  - Graceful degradation working
  - Escalations created for persistent failures
- **Testing**: Run chaos engineering tests (pumba, chaos-mesh)
- **Estimate**: 2 days (S)

**Dependencies**: All epics (1-5)  
**Parallel Work**: Stories 6.1-6.5 can run in parallel

---

### Epic 7: Deployment & Operations (Week 8)

**Objective**: Deploy to GitHub Actions, set up monitoring, create runbook

**Story 7.1: GitHub Actions Workflow** (2 days)
- **Tasks**:
  - Create `.github/workflows/wowvision-prime.yml`
  - Configure schedule (every 15 minutes)
  - Configure secrets (DATABASE_URL, GITHUB_TOKEN, ANTHROPIC_API_KEY)
  - Configure environment (Python 3.11, dependencies)
  - Add health check (exit code 0 = success)
- **Acceptance Criteria**:
  - Workflow runs on schedule
  - Agent wakes up successfully
  - Decisions logged
  - Issues created
- **Testing**: Test workflow in staging, deploy to production
- **Estimate**: 2 days (S)

**Story 7.2: Monitoring Dashboard** (2 days)
- **Tasks**:
  - Set up Prometheus (metrics collection)
  - Set up Grafana (dashboard)
  - Create dashboard: agent health, decision metrics, cost tracking, error rate
  - Add panels: wake count, decision count, LLM usage, cache hit rate, error rate
- **Acceptance Criteria**:
  - Dashboard shows real-time agent health
  - Metrics updated every 15 seconds
  - Historical data retained (30 days)
- **Testing**: Manual test (view dashboard during wake cycle)
- **Estimate**: 2 days (S)

**Story 7.3: Alert Rules** (1 day)
- **Tasks**:
  - Create alert rules:
    - Error rate >1% → Slack alert
    - Cost >$20 (80% budget) → Email alert
    - Wake latency >10s → Slack alert
    - LLM timeout >5 consecutive → Slack alert
  - Configure notification channels (Slack, email)
- **Acceptance Criteria**:
  - Alerts triggered correctly
  - Notifications received
  - Alert rules documented
- **Testing**: Trigger alerts manually, verify notifications
- **Estimate**: 1 day (XS)

**Story 7.4: Operations Guide** (2 days)
- **Tasks**:
  - Create docs/vision/OPERATIONS_GUIDE.md
  - Document runbook procedures:
    - How to deploy
    - How to monitor
    - How to troubleshoot
    - How to scale
    - How to rollback
  - Add troubleshooting scenarios (10+ scenarios)
- **Acceptance Criteria**:
  - Guide is comprehensive
  - Procedures tested
  - Scenarios covered
- **Testing**: Follow runbook to deploy agent
- **Estimate**: 2 days (S)

**Story 7.5: Production Deployment** (1 day)
- **Tasks**:
  - Deploy to production GitHub Actions
  - Validate agent wakes up successfully
  - Validate decisions logged
  - Validate issues created
  - Monitor for 24 hours
- **Acceptance Criteria**:
  - Agent operational in production
  - No errors for 24 hours
  - Metrics look healthy
- **Testing**: Production monitoring
- **Estimate**: 1 day (XS)

**Dependencies**: All epics (1-6)  
**Parallel Work**: Stories 7.1-7.3 can run in parallel, 7.4-7.5 sequential

---

## Roadmap

### Timeline (8 Weeks)

**Phase 1: Foundation (Week 1-2)**
- Epic 1: Message Bus & Event-Driven Wake
- Deliverable: Agent wakes on GitHub events

**Phase 2: Core Functionality (Week 3-4)**
- Epic 2: GitHub Integration & Output Generation
- Epic 3: LLM Integration & Decision Making
- Deliverable: Agent validates files, creates issues, comments on PRs

**Phase 3: Intelligence (Week 5-6)**
- Epic 4: Learning & Improvement
- Epic 5: Common Components Integration
- Deliverable: Agent learns from feedback, uses common components

**Phase 4: Production (Week 7-8)**
- Epic 6: Testing & Quality
- Epic 7: Deployment & Operations
- Deliverable: Agent deployed to production, monitored, documented

### Milestones

**M1: Event-Driven Wake (End of Week 2)**
- ✅ Agent wakes on GitHub events
- ✅ Message bus operational
- ✅ should_wake() filter working
- **Demo**: Trigger file creation → Agent wakes up

**M2: Vision Validation (End of Week 4)**
- ✅ Agent validates files against vision stack
- ✅ GitHub issues created for violations
- ✅ PR comments posted
- **Demo**: Create violating file → Issue created → PR commented

**M3: Learning Enabled (End of Week 6)**
- ✅ Agent learns from human feedback
- ✅ Common components integrated
- ✅ Resource management active
- **Demo**: Escalation → Human feedback → Learning → Future decision reuses pattern

**M4: Production Ready (End of Week 8)**
- ✅ 95% test coverage
- ✅ Deployed to GitHub Actions
- ✅ Monitoring dashboard live
- ✅ Operations guide complete
- **Demo**: Production agent operating autonomously

### Parallel Work Streams

**Stream 1: Infrastructure (Week 1-6)**
- Message bus (Week 1-2)
- Common components (Week 5-6)
- Database schema (Week 1)

**Stream 2: Agent Logic (Week 1-6)**
- Decision framework (Week 3-4)
- GitHub integration (Week 3-4)
- Learning (Week 5-6)

**Stream 3: Quality (Week 7)**
- Unit tests
- Integration tests
- Load tests
- Chaos tests

**Stream 4: Operations (Week 8)**
- Deployment
- Monitoring
- Documentation

**Dependencies**:
- Stream 2 depends on Stream 1 (message bus)
- Stream 3 depends on Stream 1 + 2 (code complete)
- Stream 4 depends on Stream 3 (tests passing)

---

## Risk Analysis

### Technical Risks

**R1: LLM API Instability** (HIGH)
- **Impact**: Agent cannot make decisions → violations missed
- **Probability**: Medium (Claude API reliability ~99.9%)
- **Mitigation**:
  - Circuit breaker (opens after 5 failures)
  - Fallback to deterministic only (degraded mode)
  - Retry with exponential backoff (3 attempts)
  - DLQ for persistent failures → human escalation

**R2: Cost Overrun** (MEDIUM)
- **Impact**: Budget exceeded → LLM calls blocked
- **Probability**: Medium (200 decisions/day = $20/month, close to $25 limit)
- **Mitigation**:
  - Decision caching (90% hit rate)
  - Token budgets enforced (hard stop at $25)
  - Alert at 80% budget ($20)
  - Graceful degradation (deterministic only)

**R3: Database Performance** (MEDIUM)
- **Impact**: Slow queries → wake latency >5s
- **Probability**: Low (PostgreSQL handles 10K+ QPS)
- **Mitigation**:
  - Indexes on all query columns
  - Connection pooling (Supavisor)
  - Cache context (CacheHierarchy L1/L2)
  - Read replicas (if needed)

**R4: Vector Search Latency** (LOW)
- **Impact**: Similarity search >200ms → decision latency >2s
- **Probability**: Low (Pinecone p95 = 50ms)
- **Mitigation**:
  - Top-5 results only (not full scan)
  - Fallback to LLM if similarity search timeout
  - Cache search results (CacheHierarchy)

**R5: GitHub API Rate Limiting** (MEDIUM)
- **Impact**: Cannot create issues/comments → violations unreported
- **Probability**: Medium (5000 requests/hour limit)
- **Mitigation**:
  - Rate limiting (ResourceManager)
  - Batch issue creation (queue violations, create periodically)
  - Exponential backoff on 429 errors
  - Use GitHub App instead of PAT (10x higher limits)

### Operational Risks

**R6: GitHub Actions Timeout** (MEDIUM)
- **Impact**: Wake cycle exceeds 6 hours → workflow canceled
- **Probability**: Low (wake cycle typically <5 minutes)
- **Mitigation**:
  - Task queue (process one task per wake, queue rest)
  - Timeout per task (2 minutes max)
  - Resume from last checkpoint (StateManager)

**R7: Agent Drift** (LOW)
- **Impact**: Agent behavior changes over time → vision violations
- **Probability**: Low (deterministic rules tested)
- **Mitigation**:
  - Version control for vision stack (Layer 1-2)
  - Regression tests (50+ scenarios)
  - Monitoring for accuracy drop
  - Rollback mechanism (revert to previous version)

**R8: Data Loss** (LOW)
- **Impact**: Context lost → agent forgets state
- **Probability**: Very Low (PostgreSQL ACID, 99.999% durability)
- **Mitigation**:
  - Database backups (daily)
  - Point-in-time recovery (Supabase)
  - StateManager versioning (audit trail)

### Vision Compliance Risks

**R9: Vision Drift** (MEDIUM)
- **Impact**: Agent bypasses vision checks → platform drift
- **Probability**: Medium (learning from feedback might relax rules)
- **Mitigation**:
  - Layer 1 (Core) is immutable (cannot be changed by agent)
  - WowVision Prime validates its own changes (meta validation)
  - Human review for Layer 2 policy changes
  - Regression tests for vision compliance

**R10: Over-Automation** (LOW)
- **Impact**: Agent approves too much → violations missed
- **Probability**: Low (conservative defaults)
- **Mitigation**:
  - Confidence threshold (only approve if confidence >0.8)
  - Human escalation for ambiguous cases
  - Monitoring for accuracy drop
  - Regular audits of decisions

---

## Success Metrics

### Quantitative Metrics

**M1: Vision Compliance Accuracy**
- **Target**: 95%+ (violations detected / total violations)
- **Measurement**: Manual review of 100 decisions/week
- **Threshold**: Alert if <90%

**M2: Wake Latency**
- **Target**: <5s (p95)
- **Measurement**: Prometheus histogram (wake_latency_seconds)
- **Threshold**: Alert if >10s (p95)

**M3: Decision Latency**
- **Target**: <500ms deterministic, <2s LLM (p95)
- **Measurement**: Prometheus histogram (decision_latency_seconds)
- **Threshold**: Alert if >1s deterministic, >5s LLM (p95)

**M4: Cost**
- **Target**: <$25/month
- **Measurement**: Cost tracking (tokens used × price/token)
- **Threshold**: Alert at $20 (80%), hard stop at $25 (100%)

**M5: Cache Hit Rate**
- **Target**: 90%+ (cache hits / total lookups)
- **Measurement**: Prometheus counter (cache_hits, cache_misses)
- **Threshold**: Alert if <80%

**M6: Error Rate**
- **Target**: <1% (errors / total decisions)
- **Measurement**: Prometheus counter (decisions_total, errors_total)
- **Threshold**: Alert if >1%

**M7: Test Coverage**
- **Target**: 95%+
- **Measurement**: pytest-cov
- **Threshold**: Build fails if <95%

### Qualitative Metrics

**M8: Human Feedback**
- **Target**: Positive feedback from escalations (>80% approved)
- **Measurement**: Count APPROVE vs REJECT in escalation responses
- **Threshold**: Alert if <70% approved

**M9: Learning Effectiveness**
- **Target**: Accuracy improvement >10% after learning
- **Measurement**: Before/after accuracy on similar cases
- **Threshold**: Alert if no improvement after 50 escalations

**M10: Developer Experience**
- **Target**: Developers find agent helpful (survey >4/5 stars)
- **Measurement**: Quarterly developer survey
- **Threshold**: Alert if <3/5 stars

---

## Issue Tracker Format

### Main Epic

**Epic: Build WowVision Prime Agent (Vision Guardian)**
- **Labels**: `epic`, `agent-development`, `wowvision-prime`
- **Description**: Build WAOOAW's first production agent - WowVision Prime - as the Vision Guardian for the platform. Validates all architectural decisions, code, and documentation against 3-layer vision stack.
- **Success Criteria**: 10 criteria (see Executive Summary)
- **Timeline**: 8 weeks
- **Dependencies**: Common Components Library (v0.2.7)
- **Assignee**: Engineering team

### Sub-Epics (7)

**Epic 1: Message Bus & Event-Driven Wake**
- **Labels**: `epic`, `message-bus`, `event-driven`, `week-1-2`
- **Stories**: 4 stories (1.1 - 1.4)
- **Estimate**: 10 days
- **Dependencies**: Common Components (SecurityLayer, ObservabilityStack)

**Epic 2: GitHub Integration & Output Generation**
- **Labels**: `epic`, `github-integration`, `output-generation`, `week-3-4`
- **Stories**: 5 stories (2.1 - 2.5)
- **Estimate**: 10 days
- **Dependencies**: Epic 1

**Epic 3: LLM Integration & Decision Making**
- **Labels**: `epic`, `llm-integration`, `decision-making`, `week-3-4`
- **Stories**: 4 stories (3.1 - 3.4)
- **Estimate**: 10 days
- **Dependencies**: Common Components (CacheHierarchy, ErrorHandler, ResourceManager)

**Epic 4: Learning & Improvement**
- **Labels**: `epic`, `learning`, `improvement`, `week-5-6`
- **Stories**: 4 stories (4.1 - 4.4)
- **Estimate**: 10 days
- **Dependencies**: Epic 2, Epic 3

**Epic 5: Common Components Integration**
- **Labels**: `epic`, `common-components`, `integration`, `week-5-6`
- **Stories**: 6 stories (5.1 - 5.6)
- **Estimate**: 10 days
- **Dependencies**: Common Components Library (Week 5-6 implementation)

**Epic 6: Testing & Quality**
- **Labels**: `epic`, `testing`, `quality`, `week-7`
- **Stories**: 5 stories (6.1 - 6.5)
- **Estimate**: 11 days
- **Dependencies**: All epics (1-5)

**Epic 7: Deployment & Operations**
- **Labels**: `epic`, `deployment`, `operations`, `week-8`
- **Stories**: 5 stories (7.1 - 7.5)
- **Estimate**: 8 days
- **Dependencies**: All epics (1-6)

### Story Format (Example)

**Story 1.1: Implement Message Bus Core**
- **Labels**: `story`, `message-bus`, `infrastructure`, `week-1`
- **Epic**: Epic 1 (Message Bus & Event-Driven Wake)
- **Description**: Create MessageBus class for Redis Streams integration
- **Acceptance Criteria**:
  - [ ] Messages published to Redis Streams
  - [ ] Consumer groups read messages with load balancing
  - [ ] Messages acknowledged after processing
  - [ ] HMAC signatures validated
- **Tasks**:
  - [ ] Create `waooaw/messaging/message_bus.py`
  - [ ] Implement publish(topic, message, priority)
  - [ ] Implement subscribe(topics, consumer_group, handler)
  - [ ] Implement acknowledge(message_id)
  - [ ] Add SecurityLayer integration (HMAC signatures)
- **Testing**:
  - [ ] Unit tests (95% coverage)
  - [ ] Integration tests (publish → subscribe)
- **Estimate**: 3 days (S)
- **Priority**: P0 (Critical)
- **Dependencies**: None (can start immediately)
- **Assignee**: Backend engineer

### Task Format (Example)

**Task: Create message_bus.py**
- **Labels**: `task`, `implementation`, `week-1`
- **Story**: Story 1.1 (Implement Message Bus Core)
- **Description**: Create MessageBus class with Redis Streams wrapper
- **Acceptance Criteria**:
  - [ ] File created: `waooaw/messaging/message_bus.py`
  - [ ] Class structure defined
  - [ ] Redis connection established
  - [ ] Basic publish/subscribe working
- **Estimate**: 1 day
- **Priority**: P0 (Critical)
- **Assignee**: Backend engineer

---

## Appendix

### A. Dependencies Graph

```
Common Components Library (v0.2.7)
  ├─► Epic 1 (Message Bus) → Epic 2 (GitHub Integration)
  ├─► Epic 3 (LLM Integration) → Epic 4 (Learning)
  └─► Epic 5 (Components Integration)
         ↓
      Epic 6 (Testing)
         ↓
      Epic 7 (Deployment)
```

### B. File Changes

**New Files (10)**:
- `waooaw/messaging/message_bus.py` (Message Bus class)
- `waooaw/integrations/github_helpers.py` (GitHub API integration)
- `.github/workflows/wowvision-prime.yml` (GitHub Actions workflow)
- `.github/ISSUE_TEMPLATE/agent_violation.md` (Issue template)
- `docs/vision/OPERATIONS_GUIDE.md` (Runbook)
- `docs/vision/TESTING_GUIDE.md` (Test scenarios)
- `tests/test_message_bus.py` (Message Bus tests)
- `tests/test_github_integration.py` (GitHub tests)
- `tests/test_wowvision_prime.py` (Agent tests)
- `infrastructure/grafana/wowvision_dashboard.json` (Monitoring dashboard)

**Modified Files (5)**:
- `waooaw/agents/wowvision_prime.py` (+300 lines: GitHub integration, learning, components)
- `waooaw/agents/base_agent.py` (+200 lines: should_wake, make_decision, common components)
- `docs/vision/WOWVISION_PRIME_SETUP.md` (+100 lines: deployment updates)
- `docs/vision/README.md` (+50 lines: status updates)
- `tests/test_base_agent.py` (+100 lines: new tests)

### C. Reference Documents

**Architecture**:
- [BASE_AGENT_CORE_ARCHITECTURE.md](../BASE_AGENT_CORE_ARCHITECTURE.md) - Base agent design
- [MESSAGE_BUS_ARCHITECTURE.md](../MESSAGE_BUS_ARCHITECTURE.md) - Message bus design
- [ORCHESTRATION_LAYER_DESIGN.md](../ORCHESTRATION_LAYER_DESIGN.md) - Workflow orchestration
- [COMMON_COMPONENTS_LIBRARY_DESIGN.md](../COMMON_COMPONENTS_LIBRARY_DESIGN.md) - Common components

**Implementation**:
- [IMPLEMENTATION_PLAN_V02_TO_V10.md](../IMPLEMENTATION_PLAN_V02_TO_V10.md) - Overall plan
- [WOWVISION_PRIME_SETUP.md](../vision/WOWVISION_PRIME_SETUP.md) - Setup guide
- [schema.sql](../vision/schema.sql) - Database schema

**Code**:
- `waooaw/agents/wowvision_prime.py` - Agent implementation
- `waooaw/agents/base_agent.py` - Base class
- `waooaw/vision/vision_stack.py` - Vision stack manager

### D. Glossary

**3-Layer Vision Stack**:
- Layer 1 (Core): Immutable constraints (e.g., "No Python in Phase 1")
- Layer 2 (Policies): Agent-managed rules (e.g., phase_rules, file type rules)
- Layer 3 (Context): Runtime state

**Deterministic Decision**: Rule-based decision (no LLM, <1ms, $0 cost, confidence 1.0)

**LLM Decision**: Language model decision (Claude Sonnet 4.5, <2s, ~$0.02 cost, confidence varies)

**Escalation**: Human review request (GitHub issue, "APPROVE:" or "REJECT:" response)

**Common Components**: Reusable infrastructure library (8 components: CacheHierarchy, ErrorHandler, ObservabilityStack, StateManager, SecurityLayer, ResourceManager, Validator, Messaging)

**Wake Cycle**: Agent lifecycle (wake → restore → load → execute → save → sleep)

**Vision Compliance**: Alignment with WAOOAW's core vision (5 pillars: Cost Optimization, Zero Risk, Human Escalation, Simplicity, Marketplace DNA)

---

**Document Version**: 1.0  
**Last Updated**: December 27, 2025  
**Author**: WAOOAW Engineering Team  
**Status**: Ready for Implementation  
**Next Steps**: Create GitHub issues for Epics 1-7, assign to engineering team, start Week 1 (Message Bus)
