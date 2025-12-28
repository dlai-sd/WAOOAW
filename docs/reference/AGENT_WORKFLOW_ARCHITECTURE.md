# WAOOAW Agent Workflow Architecture

## Visual Representation: Agent Collaboration Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WAOOAW AGENT ECOSYSTEM                          │
│                     "14 Centers of Excellence"                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: FOUNDATION GUARDIAN                                           │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  🔍 WowVision Prime                                              │  │
│  │  ─────────────────                                               │  │
│  │  Role: Guardian & Quality Gatekeeper                            │  │
│  │  Phase: phase1_foundation                                        │  │
│  │  Status: ✅ PRODUCTION (Wake #2+, $0 cost)                      │  │
│  │                                                                  │  │
│  │  Responsibilities:                                               │  │
│  │  • Validate all file creations (Python, config, scripts)       │  │
│  │  • Enforce architecture boundaries                              │  │
│  │  • Create GitHub issues for violations                          │  │
│  │  • Learn patterns → deterministic decisions                     │  │
│  │  • Guard quality before other agents deploy                     │  │
│  │                                                                  │  │
│  │  Workflow Triggers:                                              │  │
│  │  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐      │  │
│  │  │   Cron      │───▶│   New File   │───▶│   Validate   │      │  │
│  │  │  (6 hours)  │    │   Detected   │    │   & Decide   │      │  │
│  │  └─────────────┘    └──────────────┘    └──────────────┘      │  │
│  │         │                                        │              │  │
│  │         │                                        ▼              │  │
│  │         │                                  ┌──────────┐         │  │
│  │         │                                  │ Approved │         │  │
│  │         │                                  └────┬─────┘         │  │
│  │         │                                       │               │  │
│  │         │                                       ▼               │  │
│  │         │                            ┌─────────────────────┐   │  │
│  │         │                            │ Signal other agents │   │  │
│  │         │                            │   to proceed work   │   │  │
│  │         │                            └─────────────────────┘   │  │
│  │         │                                                       │  │
│  │         └────────▶ If Violation ──────▶ Create GitHub Issue   │  │
│  │                                          Block deployment      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: DOMAIN SPECIALISTS (Next to Deploy)                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                          │
│  ┌─────────────────────┐          ┌─────────────────────┐              │
│  │  🌐 WowDomain        │          │  🏭 WowAgentFactory │              │
│  │  ─────────────       │          │  ─────────────────  │              │
│  │  Domain Knowledge    │          │  Agent Generator    │              │
│  │  Status: 📋 PLANNED  │          │  Status: 📋 PLANNED │              │
│  │                      │          │                     │              │
│  │  Manages:            │          │  Creates:           │              │
│  │  • Industry context  │          │  • New agent specs  │              │
│  │  • Business rules    │          │  • Agent configs    │              │
│  │  • Domain patterns   │          │  • Deployment code  │              │
│  │  • Knowledge base    │          │  • Test suites      │              │
│  └──────────┬───────────┘          └──────────┬──────────┘              │
│             │                                  │                         │
│             └─────────────┬────────────────────┘                         │
│                           │                                              │
│                           ▼                                              │
│              ┌────────────────────────┐                                  │
│              │  WowVision validates   │                                  │
│              │  before deployment     │                                  │
│              └────────────────────────┘                                  │
└─────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: OPERATIONAL AGENTS (11 Centers of Excellence)                │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                          │
│  MARKETPLACE OPERATIONS                    DEVELOPMENT & DEPLOYMENT     │
│  ┌──────────────────────┐                 ┌──────────────────────┐     │
│  │ 📊 WowMetrics        │                 │ 🔨 WowBuilder        │     │
│  │ 📞 WowConnect        │                 │ 🚀 WowDeploy         │     │
│  │ 💰 WowRevenue        │                 │ 🔍 WowMonitor        │     │
│  └──────────────────────┘                 └──────────────────────┘     │
│                                                                          │
│  CUSTOMER EXPERIENCE                       INTELLIGENCE & LEARNING      │
│  ┌──────────────────────┐                 ┌──────────────────────┐     │
│  │ 🎯 WowOnboard        │                 │ 🧠 WowIntel          │     │
│  │ 🎓 WowTrain          │                 │ 📚 WowLearn          │     │
│  │ 🆘 WowSupport        │                 │ 🔬 WowExperiment     │     │
│  └──────────────────────┘                 └──────────────────────┘     │
│                                                                          │
│  All operational agents inherit from WAAOOWAgent base class            │
│  All follow 6-step wake-up protocol                                     │
│  All validated by WowVision Prime before deployment                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Collaboration Workflow Patterns

### Pattern 1: Linear Handoff Chain
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Agent A     │─────▶│  Agent B     │─────▶│  Agent C     │
│  completes   │      │  takes over  │      │  finalizes   │
└──────────────┘      └──────────────┘      └──────────────┘
   │
   └──▶ Updates agent_handoffs table with context
   
Example: WowConnect → WowOnboard → WowTrain
(Lead captured → Customer onboarded → Training delivered)
```

### Pattern 2: Parallel Collaboration
```
                    ┌──────────────┐
                ┌──▶│  Agent B     │────┐
┌──────────────┐│   │  (parallel)  │    │   ┌──────────────┐
│  Agent A     ││   └──────────────┘    ├──▶│  Agent D     │
│  triggers    ││                       │   │  aggregates  │
└──────────────┘│   ┌──────────────┐    │   └──────────────┘
                └──▶│  Agent C     │────┘
                    │  (parallel)  │
                    └──────────────┘
   
Example: WowDomain triggers → WowMetrics + WowIntel + WowLearn
(Domain update triggers analysis by multiple agents simultaneously)
```

### Pattern 3: Guardian Approval Gate
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Any Agent   │─────▶│ WowVision    │─────▶│  Deploy/     │
│  requests    │      │  validates   │      │  Execute     │
│  change      │      │              │      │              │
└──────────────┘      └───────┬──────┘      └──────────────┘
                              │
                              │ If violation
                              ▼
                      ┌──────────────┐
                      │ Block + Issue│
                      │ to GitHub    │
                      └──────────────┘

Example: WowBuilder creates file → WowVision validates → Deploy or Block
```

### Pattern 4: Escalation to Human
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Agent X     │─────▶│  Confidence  │─────▶│  Human via   │
│  uncertain   │      │  threshold   │      │  GitHub      │
│              │      │  < 80%       │      │  issue       │
└──────────────┘      └──────────────┘      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │ Record in    │
                      │ human_       │
                      │ escalations  │
                      └──────────────┘

Example: WowConnect encounters edge case → Creates escalation → Human reviews
```

---

## Workflow Execution: Step-by-Step

### WowVision Prime Wake Cycle (Current Production)

```
┌────────────────────────────────────────────────────────────────────┐
│  WAKE CYCLE: Every 6 Hours (Cron Schedule)                         │
└────────────────────────────────────────────────────────────────────┘

  START: Cron triggers at 00:00, 06:00, 12:00, 18:00 UTC
    ↓
  ┌────────────────────────────────────────────────────────────────┐
  │ Step 1: Restore Identity                                       │
  │ • Load agent_id: WowVision-Prime                              │
  │ • Phase: phase1_foundation                                     │
  │ • Role: Quality Guardian                                       │
  └────────────────────────────────────────────────────────────────┘
    ↓
  ┌────────────────────────────────────────────────────────────────┐
  │ Step 2: Load Domain Context                                    │
  │ • Query: SELECT * FROM agent_context WHERE agent_id=...       │
  │ • Load previous wake's context                                 │
  │ • Increment wake_count (v1 → v2 → v3...)                      │
  │ • Log: "Loaded context version X, wake #Y"                    │
  └────────────────────────────────────────────────────────────────┘
    ↓
  ┌────────────────────────────────────────────────────────────────┐
  │ Step 3: Check Collaboration State                              │
  │ • Query: SELECT * FROM agent_handoffs WHERE target=...        │
  │ • Check if other agents handed off work                       │
  │ • Log pending handoffs count                                   │
  └────────────────────────────────────────────────────────────────┘
    ↓
  ┌────────────────────────────────────────────────────────────────┐
  │ Step 4: Review Learning Queue                                  │
  │ • Query: SELECT * FROM knowledge_base WHERE category=...       │
  │ • Apply learnings (deterministic rules)                        │
  │ • Example: "*.md files → always approve"                       │
  │ • Log: "Applied N learnings"                                   │
  └────────────────────────────────────────────────────────────────┘
    ↓
  ┌────────────────────────────────────────────────────────────────┐
  │ Step 5: Execute Assigned Work                                  │
  │ • Get pending tasks from database                              │
  │ • For each task:                                               │
  │   ├─ validate_file_creation → Check file path/extension       │
  │   │   └─ Check decision cache first (FREE)                    │
  │   │   └─ Apply deterministic rules (FREE)                     │
  │   │   └─ LLM only if needed ($0.0000 due to caching)          │
  │   │                                                             │
  │   ├─ If violation → Create GitHub issue                       │
  │   ├─ If approved → Mark task complete                         │
  │   └─ process_escalation → Handle human escalations            │
  │                                                                 │
  │ • Log: "Found N pending tasks", "Task complete"               │
  └────────────────────────────────────────────────────────────────┘
    ↓
  ┌────────────────────────────────────────────────────────────────┐
  │ Step 6: Save Context and Handoff                               │
  │ • Serialize current state (wake_count, context, metrics)       │
  │ • INSERT INTO agent_context (version = wake_count)            │
  │ • Create handoffs if needed for other agents                   │
  │ • Log: "Saved context (version N)"                            │
  └────────────────────────────────────────────────────────────────┘
    ↓
  END: Shutdown until next cron trigger
```

---

## Future Agent Workflows (Post-WowVision Validation)

### WowDomain: Domain Knowledge Manager

```
TRIGGER: On domain context change (new industry, new rules)
  ↓
┌────────────────────────────────────────────────────────────────┐
│ 1. Detect domain update (new agents added to marketplace)      │
│ 2. Load relevant knowledge from external sources               │
│ 3. Structure into knowledge_base entries                       │
│ 4. Hand off to WowVision for validation                        │
│ 5. If approved → Update domain context table                   │
│ 6. Signal WowMetrics, WowIntel, WowLearn about update          │
└────────────────────────────────────────────────────────────────┘

HANDOFF TARGETS:
• WowMetrics: "New domain added, track performance"
• WowIntel: "New patterns to learn from domain"
• WowLearn: "New training data available"
```

### WowAgentFactory: New Agent Generator

```
TRIGGER: Manual (workflow_dispatch) or GitHub issue labeled "new-agent"
  ↓
┌────────────────────────────────────────────────────────────────┐
│ 1. Load agent specification from issue or config               │
│ 2. Generate agent code (inherits WAAOOWAgent)                 │
│ 3. Create agent config YAML                                    │
│ 4. Generate tests (pytest suite)                              │
│ 5. Hand off to WowVision for approval                         │
│ 6. If approved → Create PR with new agent                     │
│ 7. Hand off to WowBuilder for deployment setup                │
└────────────────────────────────────────────────────────────────┘

HANDOFF CHAIN:
WowAgentFactory → WowVision (validate) → WowBuilder (deploy) → WowMonitor (track)
```

### WowConnect: Lead Capture & First Contact

```
TRIGGER: Webhook from marketplace (user clicks "Start Trial")
  ↓
┌────────────────────────────────────────────────────────────────┐
│ 1. Capture lead info (name, email, agent interest)            │
│ 2. Create conversation_session in database                     │
│ 3. Send welcome email (personalized to chosen agent)           │
│ 4. Schedule demo/onboarding                                    │
│ 5. Hand off to WowOnboard with full context                   │
└────────────────────────────────────────────────────────────────┘

HANDOFF PACKAGE:
{
  "customer_id": "uuid",
  "agent_selected": "Content Marketing Agent",
  "industry": "Healthcare",
  "trial_start": "2025-12-24",
  "context": "Interested in blog writing, CBSE specialist"
}
  ↓
WowOnboard receives and continues onboarding
```

### WowOnboard: Customer Onboarding

```
RECEIVES: Handoff from WowConnect
  ↓
┌────────────────────────────────────────────────────────────────┐
│ 1. Load handoff context from agent_handoffs table              │
│ 2. Schedule onboarding call (calendar integration)             │
│ 3. Prepare personalized demo (using customer context)          │
│ 4. Deliver agent-specific training materials                   │
│ 5. Set up trial workspace                                      │
│ 6. Hand off to WowTrain for deep training                     │
└────────────────────────────────────────────────────────────────┘

PARALLEL SIGNALS:
• WowMetrics: "New customer onboarded"
• WowSupport: "Customer now in trial, monitor for questions"
```

### WowMetrics: Performance Analytics

```
TRIGGER: Multiple sources (events, cron, handoffs)
  ↓
┌────────────────────────────────────────────────────────────────┐
│ 1. Collect agent performance data                              │
│    • Success rate, response time, cost per decision            │
│ 2. Analyze trends                                               │
│    • Which agents performing best?                             │
│    • Cost optimization opportunities?                          │
│ 3. Generate insights                                            │
│ 4. Store in agent_metrics table                               │
│ 5. Signal WowIntel with patterns                              │
│ 6. Create dashboard updates                                     │
└────────────────────────────────────────────────────────────────┘

OUTPUTS TO:
• WowIntel: Pattern data for learning
• WowLearn: Training signals
• Human: Performance dashboard
```

---

## Database-Driven Coordination

All agents communicate via shared database tables:

```
┌─────────────────────────────────────────────────────────────┐
│  agent_context                                              │
│  ────────────────────────────────────────────────────────  │
│  Each agent saves wake state here                          │
│  Other agents can read to understand current state         │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  agent_handoffs                                             │
│  ────────────────────────────────────────────────────────  │
│  Agent A completes → Creates handoff record → Agent B reads│
│  Status: pending → in_progress → completed                 │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  knowledge_base                                             │
│  ────────────────────────────────────────────────────────  │
│  Shared learnings across all agents                        │
│  Category: "WowVision-patterns", "WowDomain-healthcare"    │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│  decision_cache                                             │
│  ────────────────────────────────────────────────────────  │
│  Cached decisions for $0 cost operations                   │
│  All agents check cache before LLM calls                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Deployment Sequence (Roadmap)

```
✅ Phase 1: Foundation (CURRENT)
   ├─ WowVision Prime (PRODUCTION - Wake #2+)
   └─ Base architecture validated ($0 cost, 100% uptime)

📋 Phase 2: Domain & Generation (NEXT)
   ├─ WowDomain (domain knowledge manager)
   ├─ WowAgentFactory (agent generator)
   └─ Validate multi-agent coordination

📋 Phase 3: Customer Journey (Q1 2026)
   ├─ WowConnect (lead capture)
   ├─ WowOnboard (onboarding)
   ├─ WowTrain (training delivery)
   └─ WowSupport (customer support)

📋 Phase 4: Operations (Q2 2026)
   ├─ WowMetrics (analytics)
   ├─ WowRevenue (revenue ops)
   ├─ WowBuilder (development)
   ├─ WowDeploy (deployment)
   └─ WowMonitor (observability)

📋 Phase 5: Intelligence (Q2-Q3 2026)
   ├─ WowIntel (market intelligence)
   ├─ WowLearn (continuous learning)
   └─ WowExperiment (A/B testing)
```

---

## Cost Model: Multi-Agent System

```
AGENT COST STRUCTURE:

┌─────────────────────┬──────────────┬────────────┬──────────────┐
│ Agent Type          │ LLM Calls    │ Cache Hit  │ Monthly Cost │
├─────────────────────┼──────────────┼────────────┼──────────────┤
│ WowVision Prime     │ 0-2/wake     │ 95%+       │ $0.00        │
│ WowDomain           │ 1-5/update   │ 80%        │ $2-5         │
│ WowAgentFactory     │ 10-20/agent  │ 50%        │ $5-10        │
│ WowConnect          │ 1/customer   │ 90%        │ $10-20       │
│ WowOnboard          │ 2-3/customer │ 85%        │ $15-25       │
│ Operational Agents  │ 0-1/task     │ 95%+       │ $0-5 each    │
└─────────────────────┴──────────────┴────────────┴──────────────┘

TARGET: Total system cost < $100/month for 14 agents
STRATEGY: Aggressive caching, deterministic rules, shared knowledge
```

---

## Evolution: From Simple Handoffs to Orchestrated Workflows

**Current (v0.2)**: Database-based handoffs between agents  
**Future (v0.3+)**: jBPM-inspired workflow orchestration

### Migration Path

**Phase 1 (v0.2)**: Simple patterns documented here  
- Linear handoffs via `agent_handoffs` table
- Parallel consultation via async calls
- Guardian approval gates

**Phase 2 (v0.3)**: Orchestration layer introduction  
- Formal workflow definitions (BPMN-inspired)
- Human tasks (GitHub issue escalation)
- Timer events (7-day trials, SLA tracking)
- Compensation/rollback patterns

**See**: [ORCHESTRATION_LAYER_DESIGN.md](./ORCHESTRATION_LAYER_DESIGN.md) for complete workflow orchestration architecture

### Why Orchestration Layer?

Current patterns work for simple agent coordination but lack:
- ❌ Long-running workflows (7-day trials)
- ❌ Human-in-the-loop with timeouts
- ❌ Rollback/compensation on failure
- ❌ Process versioning (A/B testing workflows)
- ❌ Visual workflow representation (BPMN diagrams)

Orchestration layer (jBPM-inspired) provides:
- ✅ Workflow definitions as code (Python) or YAML
- ✅ Service tasks (agent work), User tasks (human work)
- ✅ Gateways (conditional routing), Timers (scheduled events)
- ✅ Process variables (shared context with audit trail)
- ✅ Compensation handlers (automatic rollback)
- ✅ Version management (gradual rollout, A/B testing)

### Compatibility

**Good news**: All patterns documented here remain valid!

- Simple linear handoffs → `Sequential ServiceTask` workflow
- Parallel consultation → `ParallelGateway` with fan-out/fan-in
- Guardian approval → `ExclusiveGateway` after validation
- Human escalation → `UserTask` with SLA timeout

The orchestration layer **formalizes** these patterns without breaking existing code.

---

## Key Principles

1. **WowVision Guards Everything**: No agent deploys code without WowVision approval
2. **Database-First Communication**: All coordination via PostgreSQL tables (v0.2) → Process variables (v0.3+)
3. **Cache-First Decisions**: Check cache before LLM for $0 operations
4. **Graceful Handoffs**: Rich context passed between agents
5. **Human Escalation**: Uncertainty triggers human review via GitHub issues (formalized as UserTask in v0.3+)
6. **Autonomous Evolution**: Agents learn patterns, reduce LLM dependency over time
7. **Workflow-Driven Coordination**: Complex multi-agent workflows use orchestration layer (NEW in v0.3+)

---

## Next Steps

### Immediate (v0.2)
1. ✅ **WowVision Prime**: Production validated (Wake #2+ with proper versioning)
2. 📋 **WowDomain**: Design spec + implementation (2-3 days)
3. 📋 **WowAgentFactory**: Generator logic + templates (3-5 days)
4. 📋 **Integration Tests**: Multi-agent handoff validation (2 days)

### Short-term (v0.3-0.5)
5. 📋 **Orchestration Layer**: jBPM-inspired workflow engine (2-3 weeks)
6. 📋 **Migrate PR Review**: Convert to formal workflow definition
7. 📋 **Customer Onboarding**: 7-day trial workflow with timers
8. 📋 **Campaign Creation**: Multi-agent parallel workflow

### Long-term (v0.6-1.0)
9. 📋 **Remaining 11 Agents**: Iterative deployment (Q1-Q2 2026)
10. 📋 **Advanced Patterns**: Sub-workflows, event-based routing, sagas

**Related Documents**:
- [ORCHESTRATION_LAYER_DESIGN.md](./ORCHESTRATION_LAYER_DESIGN.md) - Complete workflow architecture
- [MESSAGE_BUS_ARCHITECTURE.md](./MESSAGE_BUS_ARCHITECTURE.md) - Event-driven communication
- [BASE_AGENT_CORE_ARCHITECTURE.md](./BASE_AGENT_CORE_ARCHITECTURE.md) - Agent workflow integration

---

*Generated: December 27, 2025*  
*Status: WowVision Prime in production, orchestration layer designed, 13 agents in planning*  
*Version: 1.1 (Updated for Orchestration Layer)*
