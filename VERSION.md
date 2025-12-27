# WAOOAW Platform Version History

## v0.2.5 - Message Bus Implementation Notes (December 27, 2025)

**Status:** BASELINE - Implementation Ready (Option A: Fast Track)

**What's New:**
- ✅ 5 critical design gaps addressed (validation, security, config, observability, error handling)
- ✅ Message schema validation design (JSON Schema at boundaries)
- ✅ Security & authentication design (HMAC-SHA256 signatures)
- ✅ Configuration management design (env vars + YAML, 12-factor app)
- ✅ Observability design (structured logging, OpenTelemetry, Prometheus metrics)
- ✅ Error handling strategy (3-tier: fail fast, retry, DLQ)
- ✅ Configuration files created (.env.example, message_bus_config.yaml, message_schema.json)
- ✅ Config loader extended (AppConfig dataclass, secret key management)
- ✅ Implementation notes added to MESSAGE_BUS_ARCHITECTURE.md (400+ lines)
- ✅ All configs tested and validated

**Critical Design Decisions:**

**1. Message Schema Validation:**
- JSON Schema validation at message bus boundaries
- Validate on send() (fail fast) and receive() (reject malformed)
- Invalid messages → immediate exception, NOT DLQ (schema errors are code bugs)
- Schema location: `waooaw/messaging/schemas/message_schema.json`
- Validates: routing (from/to/topic), payload (subject/priority), metadata, audit

**2. Security & Authentication:**
- HMAC-SHA256 message signatures (v0.2.x)
- Each agent has secret key (env var: `AGENT_SECRET_KEY_<AGENT_ID>`)
- Sender computes HMAC, adds to metadata.signature
- Receiver verifies before processing
- Invalid signature → reject, log security event, DO NOT DLQ
- Future: Upgrade to mTLS in v0.3.x for external integrations

**3. Configuration Management:**
- **Approach**: Environment variables + YAML config (12-factor app style)
- **Infrastructure config**: .env file (Redis URL, ports, limits)
- **Agent-specific config**: waooaw/config/agent_config.yaml
- **Message bus config**: waooaw/config/message_bus_config.yaml
- **Loader**: waooaw/config/loader.py (extended with AppConfig dataclass)
- **Secret keys**: Generated with `python -c "import secrets; print(secrets.token_hex(32))"`

**4. Observability Design:**
- **Structured Logging**: JSON format for log aggregation
  - Every message operation logs: message_id, from/to agents, topic, priority, size, correlation_id, timestamp
- **OpenTelemetry Spans**: Distributed tracing with trace_id, span_id
- **Prometheus Metrics**: 
  - Counters: messages_sent_total, messages_received_total, messages_dlq_total
  - Histograms: message_send_duration_seconds
  - Gauges: message_queue_depth
- **Key Metrics**: throughput, DLQ rate, latency (p50/p95/p99), queue depth, consumer lag

**5. Error Handling Strategy:**
- **Tier 1 - Immediate Failure** (no retry):
  - Schema validation errors → InvalidMessageError
  - Signature verification failures → SecurityError
  - Redis connection errors → MessageBusUnavailableError (caller retries)
- **Tier 2 - Retry with Exponential Backoff**:
  - Transient Redis errors, consumer processing errors
  - Max retries: 3 attempts, Backoff: 1s, 2s, 4s
- **Tier 3 - Dead Letter Queue**:
  - After 3 failed retries → move to DLQ stream
  - DLQ monitoring: alert if depth > 10, daily digest
  - DLQ API: inspect, retry by ID/error pattern, delete

**Files Created:**
```
.env.example (2,317 bytes)
├── Redis configuration
├── PostgreSQL configuration
├── Message bus settings (priority streams, retries, retention)
├── Agent secret keys (template)
└── Observability settings (logging, metrics, tracing)

waooaw/config/message_bus_config.yaml (3,116 bytes)
├── Priority streams (5 levels: p1-p5)
├── Consumer group settings (read count, block time, claim idle)
├── DLQ configuration (max retries, alert threshold, retention)
├── Audit trail settings (batch size, flush interval, retention years)
├── Retry strategy (exponential backoff)
├── Message limits (max size, depth, array length, string length)
└── Security settings (signature required, algorithm)

waooaw/messaging/schemas/message_schema.json (6,524 bytes)
├── JSON Schema (draft-07)
├── Required fields: routing, payload, metadata
├── Routing validation (from/to pattern, topic hierarchy)
├── Payload validation (subject, priority 1-5, action enum)
├── Metadata validation (ttl, retry_count, tags, signature)
└── Example messages with full structure
```

**Files Modified:**
```
docs/MESSAGE_BUS_ARCHITECTURE.md (+400 lines)
└── Implementation Notes section added (before "Next Steps")
    ├── 5 critical design decisions
    ├── Configuration files to create
    ├── Testing strategy (unit, integration, performance, security)
    └── Implementation phases (v0.2.5-v0.2.7)

waooaw/config/loader.py (+170 lines)
└── Extended with Message Bus support
    ├── RedisConfig dataclass
    ├── PostgresConfig dataclass
    ├── MessageBusConfig dataclass
    ├── ObservabilityConfig dataclass
    ├── AppConfig dataclass
    ├── load_app_config() function
    └── get_agent_secret_key() function
```

**Testing Performed:**
- ✅ Agent config loads successfully (database_url extracted)
- ✅ Message bus YAML valid (5 priority streams, DLQ settings, retry config)
- ✅ Message schema JSON valid (routing, payload, metadata required fields)
- ✅ All config files validated (2.3 KB + 3.1 KB + 6.5 KB = 11.9 KB total)
- ✅ Config loader functions work (AppConfig, get_agent_secret_key)

**Implementation Phases:**
- **Phase 1 (v0.2.5)**: Core + Config + Validation (THIS VERSION)
  - Implement message schema validation
  - Add HMAC signatures
  - Create config files + loader
  - Unit tests
  
- **Phase 2 (v0.2.6)**: Observability + Error Handling
  - Structured logging (JSON)
  - Key metrics (Prometheus)
  - 3-tier error handling + DLQ manager
  - Integration tests
  
- **Phase 3 (v0.2.7)**: Production Readiness
  - OpenTelemetry spans
  - Performance tests
  - Security tests
  - Redis persistence fix (Issue #48)

**Configuration as Code:**
- All config in version control (Git)
- Code review for config changes
- Easy rollback (git revert)
- Environment parity (dev/staging/prod use same files, different values)
- .env for secrets, YAML for structure

**Why This Baseline:**
Before coding MessageBus class (Issue #45), need to lock down critical design decisions. Option A (Fast Track) documents decisions as implementation notes in existing architecture doc rather than creating separate design docs. This allows immediate progression to implementation while ensuring security, observability, and error handling are designed upfront.

**Dimension Progress:**
- Dimension 7 (Communication Protocol): 75% → 80% (implementation-ready)
- Overall Readiness: 37% (5.6/15 dimensions) → 38% (5.7/15 dimensions)

**Files Changed:**
- docs/MESSAGE_BUS_ARCHITECTURE.md (+939 lines implementation notes)
- .env.example (NEW, 2,317 bytes)
- waooaw/config/message_bus_config.yaml (NEW, 3,116 bytes)
- waooaw/messaging/schemas/message_schema.json (NEW, 6,524 bytes)
- waooaw/config/loader.py (+170 lines for message bus support)

**Ready For:**
- Issue #45 implementation (MessageBus class with validation, signatures, config)
- Issue #48 implementation (Redis persistence gap fix)
- Phase 1 coding can begin immediately

**Related:**
- v0.2.1: Message Bus Architecture design
- v0.2.2: Message Handler design
- Issue #45: MessageBus Implementation
- Issue #48: Redis Persistence Gap (Critical)

---

## v0.2.4 - GitHub Projects V2 Best Practices (December 27, 2025)

**Status:** BASELINE - Standard Project Management Approach

**What's New:**
- ✅ Complete GitHub Projects V2 best practices guide (391 lines)
- ✅ Standard approach documented (Projects V2 vs Classic)
- ✅ 5-column board structure (Backlog → Design → Implementation → Testing → Done)
- ✅ Custom fields configuration (Status, Dimension, Priority, Effort, Version)
- ✅ Automation workflows (auto-close, auto-move on PR merge)
- ✅ Mobile app workflows (update status, check tasks, comment with Copilot)
- ✅ Desktop workflows (code review, progress tracking, velocity metrics)
- ✅ Copilot integration patterns (implementation help, PR reviews)
- ✅ Slice & dice view examples (by dimension, phase, version, severity)
- ✅ Complete workflow example (Issue #45 lifecycle)
- ✅ Manual setup guide (6 steps, 5 minutes)

**Key Features:**
- **Projects V2 Standard**: Modern approach replacing Classic Projects, Jira, Trello
- **Cross-Repository**: Track work across multiple repos (future: frontend, mobile)
- **Multiple Views**: Board (Kanban), Table (Spreadsheet), Roadmap (Timeline)
- **Custom Fields**: Priority (P0-P3), Dimension (1-15), Effort (story points)
- **Automation**: Auto-add issues, auto-close on merge, SLA alerts
- **Mobile-First**: Full feature parity in GitHub mobile app
- **Copilot-Ready**: Integration patterns for AI-assisted development

**Documentation:**
```
docs/GITHUB_PROJECTS_BEST_PRACTICES.md
├── Why Projects V2 (vs Classic, third-party tools)
├── Standard setup for WAOOAW (structure, fields, automation)
├── Mobile app workflows (status updates, checklists, Copilot)
├── Desktop workflows (task management, velocity, burndown)
├── Copilot integration (issue comments, PR reviews)
├── Slice & dice views (filter patterns)
├── Workflow example (Issue #45 from backlog to done)
└── Manual setup guide (6 steps)
```

**Standard Board Structure:**
```
📥 Backlog → 🎨 Design → 💻 Implementation → 🧪 Testing → ✅ Done
```

**Custom Fields:**
- Status: Backlog, Design, Implementation, Testing, Done
- Dimension: 1-15, All (which dimensions affected)
- Priority: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
- Effort: 1-5 story points (size estimate)
- Version: v0.2.0, v0.2.1, v0.2.2, v0.2.3, etc.

**Automation Workflows:**
- Auto-add issues with dimension labels → Backlog
- Issue closed → Status: Done
- PR merged → Status: Done
- Critical label → Priority: P0, notify owner

**Mobile App Usage:**
- Profile → Projects tab → Tap project → Board view
- Tap issue → Update status dropdown
- Tap issue → Check off task checklists
- Tap issue → Comment with "@github-copilot help implement X"
- Filter icon → By dimension/priority/status

**Slice & Dice Views:**
- By Dimension: `label:dimension-7` → Communication Protocol work
- By Phase: `status:Implementation` → Active coding tasks
- By Version: `label:v0.2.3` → Current sprint work
- By Severity: `label:critical` → Urgent issues
- By Type: `label:design OR label:implementation` → Work category

**Integration:**
- Used by GitHub, Microsoft, Kubernetes, React, VS Code
- Replaces Classic Projects, Jira, Trello, Asana
- Standard for modern development teams
- Full mobile + desktop feature parity
- Native Copilot integration

**Files Changed:**
- docs/GITHUB_PROJECTS_BEST_PRACTICES.md (NEW - 391 lines)

**Dimension Progress:**
- Dimension 7 (Communication Protocol): 75% → 75% (documentation only)
- Overall Readiness: 37% (5.6/15 dimensions)

**Manual Setup Required:**
- Token lacks project permissions (requires web UI)
- 6-step setup: Create project, link repo, add issues, configure columns, enable automation
- Estimated time: 5 minutes
- Result: Full mobile + desktop project management

**Why This Baseline:**
Projects V2 is the modern, standard approach for GitHub project management, replacing Classic Projects and third-party tools. This documentation establishes WAOOAW's official project management methodology, enabling mobile-first development with Copilot integration. Critical for distributed teams and AI-assisted workflows.

**Related:**
- v0.2.3: GitHub Project Management infrastructure
- Issue #42-48: Created with labels/milestones
- Mobile app readiness: Issues visible, project pending manual setup

---

## v0.2.3 - GitHub Project Management Setup (December 27, 2025)

**Status:** BASELINE - Development Tracking Infrastructure

**What's New:**
- ✅ GitHub issue templates (design, implementation, gap, bug)
- ✅ Issue template configuration for guided creation
- ✅ Project board structure defined (Backlog → Design → Implementation → Testing → Done)
- ✅ Label system designed (15 dimensions + types + versions + severity)
- ✅ Milestone structure defined (versions + phases)
- ✅ Initial 7 issues documented (3 completed, 4 upcoming)
- ✅ GitHub CLI automation scripts
- ✅ Mobile app usage guide
- ✅ GitHub Copilot integration documented
- ✅ Slice & dice view patterns (dimension, phase, version, status)

**Key Features:**
- **Issue Templates**: Pre-structured forms for design, implementation, gap, bug
- **Project Board**: Kanban workflow aligned with development phases
- **Slice & Dice Views**: Filter by dimension, phase, version, severity, status
- **Mobile Compatible**: Full access via GitHub mobile app
- **Copilot Integration**: Comment "@github-copilot complete this task" in issues
- **Automation Ready**: GitHub CLI commands for batch operations

**Initial Issues Documented:**
```
Past Work (Completed):
- #1: [Design] Base Agent Architecture (v0.2.0) ✅
- #2: [Design] Message Bus Architecture (v0.2.1) ✅  
- #3: [Design] Message Handler (v0.2.2) ✅

Upcoming Work (Backlog):
- #4: [Implementation] MessageBus Class (v0.2.3) 📋
- #5: [Implementation] MessageHandler Class (v0.2.3) 📋
- #6: [Implementation] Base Agent Integration (v0.2.3) 📋
- #7: [Gap] Redis Persistence Configuration 🚨 Critical
```

**Label Categories:**
- **Dimensions**: dimension-1 through dimension-15, dimension-all
- **Types**: design, implementation, gap, bug
- **Versions**: v0.2.0, v0.2.1, v0.2.2, v0.2.3
- **Severity**: critical, high, medium, low
- **Components**: infrastructure, agent, database, messaging

**Milestones:**
- Foundation (v0.2.0) - Closed
- Communication Infrastructure (v0.2.1, v0.2.2) - Closed
- Week 1-2 Implementation (v0.2.3) - Open
- Week 1 Setup (gaps) - Open

**Usage Patterns:**
```bash
# View by dimension
gh issue list --label "dimension-7"

# View by phase
gh issue list --label "implementation"

# View by version  
gh issue list --label "v0.2.3"

# View critical gaps
gh issue list --label "gap,critical"

# Comment with Copilot
@github-copilot Implement MessageBus class following design
```

**New Files in v0.2.3:**
```
.github/ISSUE_TEMPLATE/
  design.yml (design component template)
  implementation.yml (implementation task template)
  gap.yml (gap/missing feature template)
  bug.yml (bug report template)
  config.yml (template configuration)

docs/
  GITHUB_PROJECT_SETUP.md (comprehensive guide)
    - Project board setup instructions
    - Initial issues ready to create (7 issues)
    - Label creation commands
    - Milestone setup commands
    - GitHub CLI automation
    - Mobile app usage guide
    - Copilot integration examples
```

**Manual Setup Required:**
1. Create GitHub Project board via web UI
2. Run label creation commands (or use web UI)
3. Create milestones (or use API commands)
4. Create initial 7 issues using templates
5. Assign issues to project board columns

**Overall Readiness:** 37% (5.6/15 dimensions)

**Next Milestone:** v0.2.4 - MessageBus + MessageHandler Implementation (Week 1-2)

---

## v0.2.2 - Agent Message Handler Design (December 27, 2025)

**Status:** BASELINE - Agent-Side Messaging Complete

**What's New:**
- ✅ Agent Message Handler component designed (MessageHandler class)
- ✅ 3 messaging patterns: always-on, wake-sleep, callback-based
- ✅ Handler registration: manual + decorator pattern
- ✅ Priority queue implementation (heap-based, 1-5 scale)
- ✅ Request-response patterns (sync with timeout + async with callback)
- ✅ Message state tracking (sent, pending_reply, processing, completed, failed)
- ✅ Correlation IDs for request-response pairing
- ✅ Integration design with base_agent.py
- ✅ Complete usage examples (WowVision → WowContent handoff)

**Key Design Decisions:**
- **Architecture**: Separate component (composition pattern) in base agent
- **Patterns**: Hybrid - async background loop + sync polling + event callbacks
- **Registration**: Manual `register(topic, handler)` + `@message_handler` decorator
- **Priority**: Weighted polling (critical 10x more than background)
- **Request-Response**: `send_and_wait()` with timeout or async callback
- **State Tracking**: In-memory with optional DB persistence

**MessageHandler Features:**
```python
# Send message
msg_id = await agent.send_message(to="target", subject="...", data={...})

# Poll messages (wake-sleep agents)
messages = await agent.receive_message(limit=10)

# Subscribe to topic (callback pattern)
agent.subscribe_to_channel("vision.*", handler_func)

# Request-response (sync)
response = await handler.send_and_wait(to="seo", data={...}, timeout=60)

# Broadcast
await handler.broadcast(subject="Maintenance", data={...}, priority=5)
```

**Agent Integration:**
- `base_agent.py` gets `self.message_handler` component
- `send_message()`, `receive_message()`, `subscribe_to_channel()` stubs replaced
- Default handlers: shutdown, pause, resume, health_check
- Configuration in `agent_config.yaml`

**Updated Dimensions Status:**
7. Communication Protocol: 🟡 DESIGNED (75% - architecture + agent integration designed)

**Overall Readiness:** 37% (5.6/15 dimensions)

**New Files in v0.2.2:**
```
docs/
  AGENT_MESSAGE_HANDLER_DESIGN.md (1000+ lines)
    - MessageHandler class structure
    - 3 messaging patterns (always-on, wake-sleep, callback)
    - Handler registration (manual + decorator)
    - Priority queue implementation
    - Request-response patterns (sync + async)
    - Integration with base_agent.py
    - Usage examples (5 complete patterns)
    - Testing strategy
    - 1.5-week implementation plan
```

**Implementation Plan:**
- Week 1, Days 1-2: Core MessageHandler (send, receive, register)
- Week 1, Day 3: Async background loop
- Week 1, Day 4: Request-response pattern
- Week 1, Day 5: Base agent integration
- Week 2, Days 1-3: Advanced features + testing
- ~600 LOC (message_handler.py)

**Next Milestone:** v0.2.3 - MessageBus + MessageHandler Implementation (Week 1-2)

---

## v0.2.1 - Message Bus Architecture (December 27, 2025)

**Status:** BASELINE - Communication Infrastructure Design Complete

**What's New:**
- ✅ Message Bus Architecture designed (Redis Streams-based)
- ✅ Complete message schema (routing, payload, metadata, audit)
- ✅ 5 message routing patterns (point-to-point, broadcast, topic, request-response, self)
- ✅ Priority handling (1-5 scale via 5 separate streams)
- ✅ At-least-once delivery with acknowledgment
- ✅ 2-year message retention + replay capability
- ✅ Separate audit trail design (PostgreSQL, 7-year compliance)
- ✅ Dead Letter Queue for failed messages
- ✅ Redis persistence verification & gap analysis

**Key Design Decisions:**
- **Technology**: Redis Streams (already in infrastructure, $0 cost)
- **Delivery**: At-least-once with consumer groups + pending entries
- **Scale**: 10K msg/day, 1K burst/sec (easily scales to 100K+)
- **Persistence**: AOF + RDB for durability
- **Audit**: Separate PostgreSQL store for compliance

**Redis Configuration Gaps Identified:**
- ⚠️ No AOF (Append-Only File) configured - needs `--appendonly yes`
- ❌ No memory limits - needs `--maxmemory 2gb`
- ❌ No eviction policy - needs `--maxmemory-policy noeviction`
- 📋 Action items documented in MESSAGE_BUS_ARCHITECTURE.md

**Updated Dimensions Status:**
7. Communication Protocol: 🟡 DESIGNED (50% - architecture complete, implementation pending)

**Overall Readiness:** 36% (5.4/15 dimensions)

**New Files in v0.2.1:**
```
docs/
  MESSAGE_BUS_ARCHITECTURE.md (1000+ lines)
    - Complete Redis Streams design
    - Message schema & routing patterns
    - Priority handling & DLQ
    - Audit trail design
    - Redis persistence gap analysis
    - 2-week implementation plan
```

**Implementation Plan:**
- Week 1: Core message bus + agent integration
- Week 2: Priority/DLQ + audit trail + testing
- ~800 LOC (message_bus.py + models.py + tests)

**Next Milestone:** v0.2.2 - Message Bus Implementation (Week 1)

---

## v0.2 - Foundation with Research Integration (December 25, 2025)

**Status:** BASELINE - Keep & Build Decision Point

**What's Included:**
- ✅ Dual-identity framework (Specialization + Personality)
- ✅ 6-step wake protocol (basic implementation)
- ✅ Base agent class (WAAOOWAgent)
- ✅ First production agent (WowVision Prime)
- ✅ Database schema (10 core tables)
- ✅ Infrastructure (PostgreSQL, Redis, Pinecone)
- ✅ CI/CD pipeline (Python linting, tests)
- ✅ Research documentation (110+ pages)

**Research Completed:**
- ✅ Systematic Literature Review - Multi-Agent Orchestration
- ✅ Agent Design Patterns at Scale (15 dimensions)
- ✅ Strategic Decision: Keep vs. Scrap Analysis

**Core 5 Dimensions Status:**
1. Wake Protocol: 🟡 PARTIAL (40% - needs event-driven upgrade)
2. Context Management: 🟡 PARTIAL (50% - needs progressive loading)
3. Identity System: 🟢 COMPLETE (100% - production ready)
4. Hierarchy: 🔴 MISSING (0% - needs CoE Coordinators)
5. Collaboration: 🟡 PARTIAL (30% - needs handoff methods)

**Advanced 10 Dimensions Status:**
6. Learning & Memory: 🟡 PARTIAL (40% - DB tables exist)
7. Communication Protocol: 🔴 MISSING (0% - needs structured messages)
8. Resource Management: 🔴 MISSING (0% - needs budgets)
9. Trust & Reputation: 🔴 MISSING (0% - needs scoring)
10. Error Handling: 🟡 PARTIAL (30% - basic try/catch)
11. Observability: 🟡 PARTIAL (20% - basic logging)
12. Security & Privacy: 🔴 MISSING (0% - needs RBAC)
13. Performance Optimization: 🟡 PARTIAL (40% - vector cache exists)
14. Testing & Validation: 🟡 PARTIAL (30% - 3 mock tests)
15. Lifecycle Management: 🔴 MISSING (0% - needs versioning)

**Overall Readiness:** 35% (5.25/15 dimensions complete)

**Files in v0.2:**
```
waooaw/
  agents/
    base_agent.py (560 lines)
    wowvision_prime.py (300+ lines)
  database/
    base_agent_schema.sql (10 tables)
  config/
    agent_config.yaml
    loader.py

docs/
  BASE_AGENT_CORE_ARCHITECTURE.md (600+ lines)
  STRATEGIC_DECISION_KEEP_OR_SCRAP.md
  research/
    SYSTEMATIC_LITERATURE_REVIEW_MULTI_AGENT_ARCHITECTURE.md (50+ pages)
    AGENT_DESIGN_PATTERNS_AT_SCALE.md (60+ pages)

infrastructure/
  docker/
    docker-compose.yml (PostgreSQL, Redis, Pinecone)

tests/
  test_identity.py
  run_mock_tests.py
  test_health.py
```

**Go-Live Roadmap from v0.2:**
- **v0.5 (Month 3, Week 12):** Platform Go-Live - 200 agents working
- **v0.8 (Month 6, Week 24):** Marketplace Go-Live - 14 CoEs selling
- **v1.0 (Month 11, Week 46):** Operations Go-Live - All 15 dimensions

**Next Version:** v0.3 (Week 4) - Event-driven wake + Output generation

---

## v0.1 - Initial Prototype (December 20-24, 2025)

**Status:** DEPRECATED - Superseded by v0.2

**What Was Built:**
- Basic WowVision Prime agent
- PostgreSQL integration
- GitHub integration prototype
- Vision stack concept

**Issues:**
- No framework for multiple agents
- No identity system
- No wake protocol
- No research backing

**Outcome:** Evolved into v0.2 after research phase

---

## Version Numbering Scheme

**Format:** vMAJOR.MINOR.PATCH

**MAJOR (0 → 1):** Production readiness
- v0.x = Development, pre-production
- v1.x = Production ready, all 15 dimensions
- v2.x = Scale (1000+ agents)

**MINOR (x.0 → x.9):** Feature additions
- +0.1 = Small feature (single method)
- +0.3 = Medium feature (dimension upgrade)
- +0.5 = Major milestone (go-live capability)

**PATCH (x.x.0 → x.x.9):** Bug fixes, docs
- No functional changes
- Documentation updates
- Test additions
- Linting fixes

**Current:** v0.2 (Foundation with Research)
**Target:** v1.0 (Production Ready, All 15 Dimensions)
**Timeline:** v0.2 → v1.0 in 46 weeks (11 months)
