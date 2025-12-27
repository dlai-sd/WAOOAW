# GitHub Issues Manifest - WowVision Prime v0.2.8 → v0.4

**Project Board**: Create manually at https://github.com/dlai-sd/WAOOAW/projects/new
- Name: "WowVision Prime Development (v0.2.8 → v0.4)"
- Template: Board
- Views: Board (Kanban), Timeline (Gantt), Table (Filters)
- Columns: Backlog → Ready → In Progress → Testing → Done

---

## Epic 1: Message Bus & Event-Driven Wake 🚀
**Timeline**: Week 1-2 (10 days)  
**Branch**: `feature/epic-1-message-bus`  
**Labels**: `epic`, `wowvision-prime`, `priority:critical`  
**Dependencies**: BLOCKING - Must complete before Epic 2, 3

### Story 1.1: Implement Message Bus Core
**Estimate**: 3 days  
**Priority**: P0  
**Assignee**: TBD  
**Labels**: `story`, `epic-1`, `infrastructure`, `message-bus`

**Description**:
Implement Redis Streams-based message bus for event-driven agent wake.

**Acceptance Criteria**:
- [ ] MessageBus class created in `waooaw/messaging/message_bus.py`
- [ ] Methods: `publish(event)`, `subscribe(stream)`, `acknowledge(message_id)`
- [ ] SecurityLayer integration (HMAC signatures for event integrity)
- [ ] ObservabilityStack integration (metrics: events/sec, latency, errors)
- [ ] Unit tests 95%+ coverage
- [ ] Documentation: Architecture diagram, API reference

**Tasks**:
- Create MessageBus class with Redis Streams
- Implement publish/subscribe pattern
- Add HMAC signature validation
- Add metrics collection (ObservabilityStack)
- Write unit tests (10+ test cases)
- Document API and integration guide

**Testing**:
- Unit: 95%+ coverage
- Integration: Redis connection, pub/sub flow
- Performance: 1000 events/sec throughput
- Error handling: Redis down, invalid signatures

---

### Story 1.2: Implement should_wake() Filter
**Estimate**: 2 days  
**Priority**: P0  
**Assignee**: TBD  
**Labels**: `story`, `epic-1`, `agent-logic`, `filtering`

**Description**:
Add event filtering logic to BaseAgent and WowVisionPrime for intelligent wake decisions.

**Acceptance Criteria**:
- [ ] `should_wake(event)` method added to `waooaw/agents/base_agent.py`
- [ ] Override in `waooaw/agents/wowvision_prime.py` with vision-specific rules
- [ ] Wake on: `file_created`, `pr_opened`, `issue_comment.created`
- [ ] Skip: README edits, config changes, bot commits, docs-only PRs
- [ ] Unit tests: 10+ event scenarios (wake/skip)
- [ ] Metrics: wake_rate, skip_rate, false_positive_rate

**Tasks**:
- Design should_wake() decision tree
- Implement in base_agent.py (default: wake on all)
- Override in wowvision_prime.py (vision-specific rules)
- Add deterministic rules (file extensions, paths, authors)
- Write unit tests (10+ scenarios)
- Add metrics tracking

**Testing**:
- Unit: Test all wake/skip scenarios
- Integration: MessageBus → should_wake() → skip event
- Performance: Decision latency <10ms
- Accuracy: 0 false negatives, <5% false positives

---

### Story 1.3: GitHub Webhook Integration
**Estimate**: 3 days  
**Priority**: P0  
**Assignee**: TBD  
**Labels**: `story`, `epic-1`, `github`, `webhook`, `api`

**Description**:
Create FastAPI webhook endpoint to receive GitHub events and publish to message bus.

**Acceptance Criteria**:
- [ ] FastAPI endpoint created at `/webhooks/github`
- [ ] GitHub HMAC signature validation (X-Hub-Signature-256)
- [ ] Transform GitHub webhook → MessageBus event format
- [ ] GitHub webhook configured for: push, pull_request, issues
- [ ] Error handling: Invalid signature, malformed payload
- [ ] Unit tests: 95%+ coverage
- [ ] Integration tests: GitHub → Webhook → MessageBus

**Tasks**:
- Create FastAPI app with /webhooks/github endpoint
- Implement GitHub HMAC validation
- Transform webhook JSON to MessageBus event schema
- Configure GitHub webhook (repo settings)
- Add error handling (400/401/500 responses)
- Write unit + integration tests
- Document webhook setup guide

**Testing**:
- Unit: HMAC validation, payload transformation
- Integration: GitHub test event → Webhook → MessageBus
- Security: Invalid signatures rejected
- Load: 100 webhooks/min handling

---

### Story 1.4: End-to-End Wake Test
**Estimate**: 2 days  
**Priority**: P0  
**Assignee**: TBD  
**Labels**: `story`, `epic-1`, `testing`, `e2e`

**Description**:
Validate complete flow: GitHub event → Webhook → MessageBus → Agent wake → 6-step protocol.

**Acceptance Criteria**:
- [ ] Test scenario: File created in repo
- [ ] Validate: Webhook received → Event published → Agent woke → Context loaded
- [ ] Measure wake latency (target <5s p95)
- [ ] Test idempotency (duplicate events handled gracefully)
- [ ] Test error recovery (Redis down, agent crash)
- [ ] Documentation: E2E flow diagram, troubleshooting guide

**Tasks**:
- Write E2E test script (create file via GitHub API)
- Validate 6-step wake protocol completion
- Measure latency at each step
- Test duplicate event handling
- Test error scenarios (Redis down, agent crash)
- Document E2E flow and troubleshooting

**Testing**:
- E2E: File created → Agent wake → Decision made
- Performance: Wake latency <5s p95
- Reliability: 99.9% wake success rate
- Idempotency: Duplicate events don't cause re-processing

---

## Epic 2: GitHub Integration & Output 🐙
**Timeline**: Week 3-4 (10 days)  
**Branch**: `feature/epic-2-github-integration`  
**Labels**: `epic`, `wowvision-prime`, `priority:high`  
**Dependencies**: Epic 1 complete  
**Parallel**: Can run parallel with Epic 3

### Story 2.1: GitHub API Helper Functions
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-2`, `github`, `api`, `helpers`

**Description**:
Create reusable GitHub API wrapper for common operations.

**Acceptance Criteria**:
- [ ] GitHubHelper class in `waooaw/integrations/github_helper.py`
- [ ] Methods: `get_file()`, `get_pr()`, `get_repo()`, `list_files()`
- [ ] ErrorHandler integration (retry logic, circuit breaker)
- [ ] Rate limiting handling (5000 req/hr GitHub limit)
- [ ] Unit tests 95%+ coverage
- [ ] API reference documentation

---

### Story 2.2: Implement create_issue()
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-2`, `github`, `issues`

**Description**:
Add ability for WowVisionPrime to create GitHub issues for violations.

**Acceptance Criteria**:
- [ ] `create_issue(title, body, labels)` method in wowvision_prime.py
- [ ] Issue body includes: Violation details, file path, recommended fix
- [ ] Labels: `vision-violation`, `wowvision-prime`, severity label
- [ ] ErrorHandler integration (retry on API failure)
- [ ] Unit + integration tests
- [ ] Example issue created in test repo

---

### Story 2.3: Implement comment_on_pr()
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-2`, `github`, `pull-requests`

**Description**:
Add ability to comment on PRs with validation results.

**Acceptance Criteria**:
- [ ] `comment_on_pr(pr_number, comment)` method in wowvision_prime.py
- [ ] Comment includes: Validation summary, violations list, approval/rejection
- [ ] Markdown formatting (tables, code blocks, emoji)
- [ ] ErrorHandler integration
- [ ] Unit + integration tests
- [ ] Example PR comment created in test repo

---

### Story 2.4: Output Templates
**Estimate**: 2 days  
**Priority**: P1  
**Labels**: `story`, `epic-2`, `templates`, `documentation`

**Description**:
Create Markdown templates for issues and PR comments.

**Acceptance Criteria**:
- [ ] Issue template: `templates/github_issue_violation.md`
- [ ] PR comment template: `templates/github_pr_comment.md`
- [ ] Templates use Jinja2 for variable substitution
- [ ] Professional formatting (tables, emoji, severity colors)
- [ ] Unit tests for template rendering
- [ ] Documentation: Template customization guide

---

### Story 2.5: End-to-End Output Test
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-2`, `testing`, `e2e`

**Description**:
Validate complete flow: Violation detected → Issue created + PR commented.

**Acceptance Criteria**:
- [ ] Test: Create violating file → Issue created with correct details
- [ ] Test: Open PR with violating file → PR comment with rejection
- [ ] Validate issue/comment formatting
- [ ] Measure output latency (target <2s)
- [ ] Documentation: E2E flow diagram

---

## Epic 3: LLM Integration & Decision Making 🧠
**Timeline**: Week 3-4 (10 days)  
**Branch**: `feature/epic-3-llm-integration`  
**Labels**: `epic`, `wowvision-prime`, `priority:high`  
**Dependencies**: Epic 1 complete  
**Parallel**: Can run parallel with Epic 2

### Story 3.1: Implement _call_llm()
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-3`, `llm`, `claude`, `api`

**Description**:
Add LLM integration for complex validation decisions.

**Acceptance Criteria**:
- [ ] `_call_llm(prompt, context)` method in wowvision_prime.py
- [ ] Claude Sonnet 4.5 API integration
- [ ] CacheHierarchy integration (L1: in-memory, L2: Redis)
- [ ] ErrorHandler integration (retry, circuit breaker, fallback)
- [ ] Token usage tracking (target <1000 tokens/wake)
- [ ] Unit tests with mocked LLM responses
- [ ] Documentation: Prompt engineering guide

---

### Story 3.2: Implement make_decision()
**Estimate**: 3 days  
**Priority**: P0  
**Labels**: `story`, `epic-3`, `decision`, `logic`

**Description**:
Implement hybrid decision-making: 80% deterministic, 20% LLM.

**Acceptance Criteria**:
- [ ] `make_decision(file, context)` method in wowvision_prime.py
- [ ] Deterministic rules checked first (fast path)
- [ ] LLM called only for ambiguous cases
- [ ] Decision logged with rationale
- [ ] Metrics: deterministic_rate, llm_rate, decision_latency
- [ ] Unit tests: 20+ scenarios (deterministic + LLM)
- [ ] Documentation: Decision flow diagram

---

### Story 3.3: Deterministic Rules Engine
**Estimate**: 3 days  
**Priority**: P0  
**Labels**: `story`, `epic-3`, `rules`, `validation`

**Description**:
Implement deterministic rules for common violation patterns.

**Acceptance Criteria**:
- [ ] Phase rules: phase1 no .py files
- [ ] File type rules: .md always allowed, .py in waooaw/* exceptions
- [ ] Path rules: backend/tests/* exceptions
- [ ] Brand rules: "WAOOAW" capitalization
- [ ] Rules configurable in `waooaw/config/vision_rules.yaml`
- [ ] Unit tests: 95%+ coverage
- [ ] Documentation: Rules reference guide

---

### Story 3.4: LLM Response Caching
**Estimate**: 2 days  
**Priority**: P1  
**Labels**: `story`, `epic-3`, `caching`, `performance`

**Description**:
Implement multi-tier caching to reduce LLM API costs.

**Acceptance Criteria**:
- [ ] CacheHierarchy integration (L1 in-memory, L2 Redis)
- [ ] Cache key: hash(file_path, file_content, vision_context)
- [ ] Cache hit rate 90%+ (target: $0.50 vs $5.00 per wake)
- [ ] TTL: 24 hours (vision policies may change)
- [ ] Cache invalidation on vision policy update
- [ ] Metrics: cache_hit_rate, cost_per_wake
- [ ] Documentation: Caching strategy guide

---

## Epic 4: Learning & Improvement 📚
**Timeline**: Week 5-6 (10 days)  
**Branch**: `feature/epic-4-learning`  
**Labels**: `epic`, `wowvision-prime`, `priority:medium`  
**Dependencies**: Epic 2, 3 complete  
**Parallel**: Can run parallel with Epic 5

### Story 4.1: Human Feedback Collection
**Estimate**: 3 days  
**Priority**: P0  
**Labels**: `story`, `epic-4`, `feedback`, `database`

**Description**:
Capture human feedback on agent decisions for learning.

**Acceptance Criteria**:
- [ ] `human_escalations` table updated (approved/rejected, feedback)
- [ ] GitHub issue escalation flow (agent creates issue → human responds)
- [ ] Parse feedback from issue comments
- [ ] Store in PostgreSQL with decision context
- [ ] Metrics: escalation_rate, approval_rate
- [ ] Unit + integration tests

---

### Story 4.2: Pattern Extraction
**Estimate**: 3 days  
**Priority**: P0  
**Labels**: `story`, `epic-4`, `learning`, `ml`

**Description**:
Extract reusable patterns from approved/rejected decisions.

**Acceptance Criteria**:
- [ ] `extract_patterns()` method analyzes feedback
- [ ] Patterns stored in `knowledge_base` table
- [ ] Pattern format: (context, action, outcome, confidence)
- [ ] Pinecone vector search integration
- [ ] Similarity search for new decisions (cosine >0.85)
- [ ] Unit tests with sample feedback

---

### Story 4.3: Knowledge Base Integration
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-4`, `vector-search`, `pinecone`

**Description**:
Integrate Pinecone for semantic pattern matching.

**Acceptance Criteria**:
- [ ] Pinecone client in `waooaw/memory/vector_memory.py`
- [ ] Store: Decision embeddings (file, context, outcome)
- [ ] Query: Similar decisions for new files
- [ ] Threshold: Reuse pattern if similarity >0.85
- [ ] Metrics: reuse_rate, pattern_match_latency
- [ ] Unit + integration tests

---

### Story 4.4: Learning Effectiveness Test
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-4`, `testing`, `e2e`

**Description**:
Validate learning improves decision accuracy over time.

**Acceptance Criteria**:
- [ ] Test: 10 similar files → First needs LLM, rest reuse pattern
- [ ] Validate: Cost reduction 90% (10 → 1 LLM call)
- [ ] Validate: Latency reduction 75% (<2s vs <500ms)
- [ ] Validate: Accuracy maintained (95%+)
- [ ] Documentation: Learning flow diagram

---

## Epic 5: Common Components Integration 🔧
**Timeline**: Week 5-6 (10 days)  
**Branch**: `feature/epic-5-common-components`  
**Labels**: `epic`, `wowvision-prime`, `priority:high`  
**Dependencies**: Epic 2, 3 complete  
**Parallel**: Can run parallel with Epic 4

### Story 5.1: CacheHierarchy Integration
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-5`, `caching`, `component`

**Description**:
Replace custom caching with CacheHierarchy component.

**Acceptance Criteria**:
- [ ] Import CacheHierarchy from common components
- [ ] Replace custom cache code (L1/L2 logic)
- [ ] Configure TTLs: L1=60s, L2=3600s
- [ ] Metrics: cache_hit_rate, latency_reduction
- [ ] Unit tests validate behavior unchanged
- [ ] Code reduction: Estimate 50-100 lines removed

---

### Story 5.2: ErrorHandler Integration
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-5`, `error-handling`, `component`

**Description**:
Replace custom error handling with ErrorHandler component.

**Acceptance Criteria**:
- [ ] Import ErrorHandler from common components
- [ ] Replace try/catch blocks with @with_retry decorator
- [ ] Configure retry: 3 attempts, exponential backoff
- [ ] Configure circuit breaker: 5 failures → open
- [ ] Metrics: error_rate, retry_count
- [ ] Code reduction: Estimate 80-120 lines removed

---

### Story 5.3: ObservabilityStack Integration
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-5`, `observability`, `component`

**Description**:
Replace custom logging/metrics with ObservabilityStack.

**Acceptance Criteria**:
- [ ] Import ObservabilityStack from common components
- [ ] Replace custom logging (structured logs)
- [ ] Replace custom metrics (Prometheus format)
- [ ] Add tracing (OpenTelemetry spans)
- [ ] Metrics: wake_count, decision_latency, error_count
- [ ] Code reduction: Estimate 60-100 lines removed

---

### Story 5.4: StateManager Integration
**Estimate**: 1 day  
**Priority**: P1  
**Labels**: `story`, `epic-5`, `state`, `component`

**Description**:
Use StateManager for agent state persistence.

**Acceptance Criteria**:
- [ ] Import StateManager from common components
- [ ] Replace custom state save/load logic
- [ ] State includes: last_wake, decision_count, error_count
- [ ] PostgreSQL backend (agent_context table)
- [ ] Unit tests validate state persistence
- [ ] Code reduction: Estimate 40-60 lines removed

---

### Story 5.5: SecurityLayer Integration
**Estimate**: 1 day  
**Priority**: P0  
**Labels**: `story`, `epic-5`, `security`, `component`

**Description**:
Use SecurityLayer for event/API authentication.

**Acceptance Criteria**:
- [ ] Import SecurityLayer from common components
- [ ] Replace custom HMAC validation logic
- [ ] Validate GitHub webhook signatures
- [ ] Validate MessageBus event signatures
- [ ] Unit tests validate security unchanged
- [ ] Code reduction: Estimate 30-50 lines removed

---

### Story 5.6: Integration Cleanup & Validation
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-5`, `refactoring`, `testing`

**Description**:
Validate all components integrated correctly and remove dead code.

**Acceptance Criteria**:
- [ ] All custom code replaced with common components
- [ ] Dead code removed (logging, caching, error handling)
- [ ] Unit tests updated for component usage
- [ ] Integration tests pass (E2E scenarios)
- [ ] Code reduction: 40-60% (250-350 lines removed)
- [ ] Metrics: All metrics preserved or improved
- [ ] Documentation: Component integration guide

---

## Epic 6: Testing & Quality ✅
**Timeline**: Week 7 (11 days)  
**Branch**: `feature/epic-6-testing`  
**Labels**: `epic`, `wowvision-prime`, `priority:high`  
**Dependencies**: Epic 1-5 complete  
**Parallel**: All 5 stories can run in parallel

### Story 6.1: Unit Test Coverage (95%+)
**Estimate**: 3 days  
**Priority**: P0  
**Labels**: `story`, `epic-6`, `testing`, `unit`

**Description**:
Achieve 95%+ unit test coverage for all WowVisionPrime code.

**Acceptance Criteria**:
- [ ] pytest coverage report 95%+ for wowvision_prime.py
- [ ] pytest coverage report 95%+ for vision_stack.py
- [ ] All edge cases covered (errors, timeouts, invalid inputs)
- [ ] Mock LLM responses for deterministic tests
- [ ] CI/CD integration (tests run on every PR)
- [ ] Documentation: Testing guide

---

### Story 6.2: Integration Tests
**Estimate**: 3 days  
**Priority**: P0  
**Labels**: `story`, `epic-6`, `testing`, `integration`

**Description**:
Test integration between WowVisionPrime and all dependencies.

**Acceptance Criteria**:
- [ ] Test: MessageBus → Agent wake
- [ ] Test: GitHub API → Issue/comment creation
- [ ] Test: LLM API → Decision making
- [ ] Test: Pinecone → Pattern matching
- [ ] Test: PostgreSQL → State persistence
- [ ] Use docker-compose for test infrastructure
- [ ] CI/CD integration

---

### Story 6.3: Load & Performance Tests
**Estimate**: 2 days  
**Priority**: P1  
**Labels**: `story`, `epic-6`, `testing`, `performance`

**Description**:
Validate performance under load.

**Acceptance Criteria**:
- [ ] Test: 100 events/min sustained for 1 hour
- [ ] Validate: Wake latency <5s p95
- [ ] Validate: Decision latency <2s p95 (deterministic <500ms)
- [ ] Validate: Memory usage <512MB
- [ ] Validate: CPU usage <50%
- [ ] Load testing tool: Locust or k6
- [ ] Documentation: Performance benchmarks

---

### Story 6.4: Cost Validation Tests
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-6`, `testing`, `cost`

**Description**:
Validate operational cost <$25/month target.

**Acceptance Criteria**:
- [ ] Test: 1000 wakes over 7 days
- [ ] Measure: LLM API cost (target: $15/month)
- [ ] Measure: Pinecone cost (target: $5/month)
- [ ] Measure: Redis/PostgreSQL cost (target: $5/month)
- [ ] Validate: 90%+ cache hit rate
- [ ] Validate: 80%+ deterministic decision rate
- [ ] Documentation: Cost breakdown and optimization guide

---

### Story 6.5: Chaos Engineering Tests
**Estimate**: 1 day  
**Priority**: P1  
**Labels**: `story`, `epic-6`, `testing`, `chaos`, `reliability`

**Description**:
Test resilience to infrastructure failures.

**Acceptance Criteria**:
- [ ] Test: Redis down → Graceful degradation (no cache)
- [ ] Test: PostgreSQL down → Agent logs error, retries
- [ ] Test: LLM API timeout → Fallback to deterministic
- [ ] Test: GitHub API rate limit → Exponential backoff
- [ ] Validate: Error rate <1% during failures
- [ ] Validate: Recovery within 60s of service restoration
- [ ] Documentation: Failure scenarios and recovery

---

## Epic 7: Deployment & Operations 🚀
**Timeline**: Week 8 (8 days)  
**Branch**: `feature/epic-7-deployment`  
**Labels**: `epic`, `wowvision-prime`, `priority:high`  
**Dependencies**: Epic 6 complete  
**Parallel**: Stories 7.1-7.3 parallel, 7.4-7.5 sequential

### Story 7.1: GitHub Actions Workflow
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-7`, `ci-cd`, `github-actions`

**Description**:
Create production-ready CI/CD pipeline.

**Acceptance Criteria**:
- [ ] Workflow: lint → test → build → deploy
- [ ] Trigger: Push to main, workflow_dispatch
- [ ] Deploy target: GitHub Actions runner (self-hosted or GitHub-hosted)
- [ ] Secrets: DATABASE_URL, PINECONE_API_KEY, ANTHROPIC_API_KEY, GITHUB_TOKEN
- [ ] Rollback strategy: Revert to previous tag
- [ ] Documentation: Deployment guide

---

### Story 7.2: Monitoring & Alerting
**Estimate**: 2 days  
**Priority**: P0  
**Labels**: `story`, `epic-7`, `monitoring`, `alerting`

**Description**:
Set up monitoring dashboard and alerts.

**Acceptance Criteria**:
- [ ] Prometheus metrics exposed (wake_count, decision_latency, error_rate)
- [ ] Grafana dashboard (or GitHub Actions dashboard)
- [ ] Alerts: Error rate >5%, wake latency >10s, cost >$30/month
- [ ] Alert channels: GitHub issue, email (optional)
- [ ] Documentation: Monitoring guide

---

### Story 7.3: Operations Runbook
**Estimate**: 2 days  
**Priority**: P1  
**Labels**: `story`, `epic-7`, `documentation`, `ops`

**Description**:
Create comprehensive operations guide.

**Acceptance Criteria**:
- [ ] Runbook: `docs/operations/WOWVISION_PRIME_RUNBOOK.md`
- [ ] Sections: Architecture, deployment, monitoring, troubleshooting, rollback
- [ ] Common issues: Redis down, LLM timeout, cost spike
- [ ] Resolution steps for each issue
- [ ] On-call guide (if applicable)
- [ ] Review by 2+ team members

---

### Story 7.4: Staging Deployment
**Estimate**: 1 day  
**Priority**: P0  
**Labels**: `story`, `epic-7`, `deployment`, `staging`

**Description**:
Deploy to staging environment for final validation.

**Acceptance Criteria**:
- [ ] Deploy to staging (separate GitHub repo or branch)
- [ ] Run full test suite (unit, integration, E2E)
- [ ] Validate: All tests pass
- [ ] Validate: Monitoring dashboard working
- [ ] Validate: Costs within budget (<$25/month projected)
- [ ] Approval: 2+ reviewers sign off

---

### Story 7.5: Production Deployment
**Estimate**: 1 day  
**Priority**: P0  
**Labels**: `story`, `epic-7`, `deployment`, `production`

**Description**:
Deploy WowVisionPrime to production.

**Acceptance Criteria**:
- [ ] Merge feature/epic-7 → develop → main
- [ ] Tag: v0.4 (WowVision Prime Production-Ready)
- [ ] Deploy via GitHub Actions workflow
- [ ] Validate: Agent operational (wake on real events)
- [ ] Validate: First 10 decisions correct
- [ ] Validate: Monitoring dashboard shows healthy metrics
- [ ] Re-enable scheduled workflow (6-hour cron)
- [ ] Documentation: Production deployment announcement
- [ ] Celebration: 🎉 WowVision Prime is LIVE!

---

## Labels Key

**Epic Labels**:
- `epic`: Main epic issue
- `wowvision-prime`: Related to WowVision Prime agent
- `priority:critical`: Blocking dependency
- `priority:high`: Important for milestone
- `priority:medium`: Nice to have
- `priority:low`: Future enhancement

**Story Labels**:
- `story`: User story
- `epic-N`: Belongs to Epic N
- `infrastructure`: Message bus, database, Redis
- `agent-logic`: Decision making, filtering
- `github`: GitHub API integration
- `llm`: Claude API integration
- `testing`: Unit, integration, E2E tests
- `documentation`: Docs, guides, runbooks
- `ci-cd`: GitHub Actions, deployment

**Priority Labels** (Poker Planning):
- `P0`: Critical (must have)
- `P1`: High (should have)
- `P2`: Medium (nice to have)
- `P3`: Low (future)

**Estimate Labels** (Story Points):
- `1-day`: 1 day
- `2-days`: 2 days
- `3-days`: 3 days

---

## Usage Instructions

### Create Issues via GitHub CLI:
```bash
# Install gh CLI
gh auth login

# Create Epic 1
gh issue create --title "Epic 1: Message Bus & Event-Driven Wake 🚀" \
  --body "$(cat .github/ISSUES_MANIFEST.md | sed -n '/## Epic 1/,/## Epic 2/p')" \
  --label "epic,wowvision-prime,priority:critical"

# Create Story 1.1
gh issue create --title "Story 1.1: Implement Message Bus Core" \
  --body "$(cat .github/ISSUES_MANIFEST.md | sed -n '/### Story 1.1/,/### Story 1.2/p')" \
  --label "story,epic-1,infrastructure,message-bus,P0"

# Repeat for all stories...
```

### Create Issues via GitHub Web UI:
1. Navigate to https://github.com/dlai-sd/WAOOAW/issues/new
2. Copy epic/story title and description from this manifest
3. Add labels, assignees, milestone
4. Link to parent epic (if story)
5. Save issue

### Create GitHub Project Board:
1. Navigate to https://github.com/dlai-sd/WAOOAW/projects/new
2. Select "Board" template
3. Name: "WowVision Prime Development (v0.2.8 → v0.4)"
4. Add columns: Backlog, Ready, In Progress, Testing, Done
5. Add all issues to Backlog
6. Set up automation: Move to "In Progress" when assigned, "Done" when closed
7. Enable Timeline view for Gantt chart
8. Enable Table view for filtering

---

**Created**: 2024-12-27  
**Version**: v0.2.8  
**Target**: v0.4 (8 weeks)  
**Restore Point**: git tag v0.2.8
