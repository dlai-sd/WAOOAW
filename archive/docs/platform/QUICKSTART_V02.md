# WAOOAW - Developer Quick Start

> **Version:** v0.3.6 | **Next:** v0.4.1 WowAgentFactory (Week 5-8)  
> **Updated:** December 28, 2024

---

## 🚀 Quick Links

| Document | Purpose |
|----------|---------|
| 📊 **[STATUS.md](STATUS.md)** | Current sprint status |
| 📈 **[PROJECT_TRACKING.md](PROJECT_TRACKING.md)** | Metrics, timeline, milestones |
| 🏗️ **[PLATFORM_ARCHITECTURE.md](PLATFORM_ARCHITECTURE.md)** | Complete architecture & journeys |
| 📖 **[VERSION.md](VERSION.md)** | Version history & changelog |
| 🔗 **[GitHub Issues](https://github.com/dlai-sd/WAOOAW/issues)** | All work items |
| 🎯 **[Epic #68](https://github.com/dlai-sd/WAOOAW/issues/68)** | Current sprint (WowAgentFactory) |

---

## 🎯 Current Status

**Platform Progress:**
- ✅ Infrastructure Layer: 100% complete
- 🔄 Platform CoE Layer: 7% complete (1/14 agents)
- 📋 Customer Layer: 0% complete

**Latest Milestone:** v0.3.6 (Dec 28, 2024)
- WowVision Prime operational
- Project infrastructure established
- 26+ GitHub issues created
- Documentation restructured

**Next Sprint:** v0.4.1 WowAgentFactory (Week 5-8)
- 12 stories, 39 story points
- Goal: Automate creation of remaining 12 CoE agents
- 77% time savings target

---

## 📁 Repository Structure

```
WAOOAW/
├── Root Documents (Single Source of Truth)
│   ├── README.md                     # Project overview
│   ├── PLATFORM_ARCHITECTURE.md      # Architecture & journeys
│   ├── PROJECT_TRACKING.md           # Sprint tracking
│   ├── STATUS.md                     # Quick status
│   ├── VERSION.md                    # Changelog
│   └── QUICKSTART_V02.md             # This file
│
├── docs/                             # Documentation
│   ├── infrastructure/               # Layer 1 docs (100%)
│   ├── platform/                     # Layer 2 docs (7%)
│   ├── customer/                     # Layer 3 docs (0%)
│   ├── projects/                     # Project management
│   ├── reference/                    # Historical docs
│   ├── research/                     # Research papers
│   ├── runbooks/                     # Operations
│   └── vision/                       # Future vision
│
├── waooaw/                           # Platform CoE code
│   ├── agents/                       # Agent implementations
│   │   ├── base_agent.py             # Base agent class
│   │   └── wowvision_prime.py        # WowVision Prime (v0.3.6)
│   ├── common/                       # Reusable components
│   ├── config/                       # Configuration
│   ├── memory/                       # Vector memory
│   └── messaging/                    # Message bus
│
├── backend/                          # FastAPI backend
├── frontend/                         # Marketplace UI
├── infrastructure/                   # Docker, Terraform
├── scripts/                          # Automation scripts
└── tests/                            # Test suite
```

---

## Common Tasks

### Set Up Dev Environment

```bash
# Clone repo
git clone https://github.com/yourusername/WAOOAW.git
cd WAOOAW

# Start services (PostgreSQL, Redis, Pinecone)
cd infrastructure/docker
docker-compose up -d

# Install Python dependencies
cd ../../backend
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Start backend
uvicorn app.main:app --reload
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Create New Agent (Use Template)

```bash
# Copy template
cp templates/new_coe_agent_template.py \
   waooaw/agents/marketing/content_marketing.py

# Edit:
# 1. Rename class (WowContentMarketing)
# 2. Fill in _load_specialization()
# 3. Implement _try_deterministic_decision()
# 4. Customize execute_task()

# Test
pytest tests/test_content_marketing.py

# Deploy (see deployment checklist in template)
```

### Implement Dimension (Use Template)

```bash
# Example: Week 1-2 Event-Driven Wake
cp templates/event_bus_template.py \
   waooaw/orchestration/event_bus.py

# Follow integration instructions in template:
# 1. Add should_wake() to base_agent.py
# 2. Create wake_events.py with patterns
# 3. Test event subscriptions
# 4. Deploy

# Run tests
pytest tests/test_event_bus.py
```

### Run Specific Agent

```bash
# Run WowVision Prime
cd waooaw
python -m agents.wowvision_prime

# Or via API
curl -X POST http://localhost:8000/api/agents/wowvision/wake \
  -H "Content-Type: application/json" \
  -d '{"event": "file_created", "file_path": "src/app.py"}'
```

---

## Cost Tracking

### Current (1 agent, v0.2)
- LLM: $5/month
- Pinecone: $70/month  
- **Total: $75/month**

### Target (200 agents, v1.0)
- LLM (with optimization): $50-150/month
- Pinecone: $70/month
- PostgreSQL: $25/month
- Redis: $30/month
- Observability: $50/month
- **Total: $225-325/month**
- **Per Agent: $1.12-1.62/month**

**Budget Alert:** Set alert at $150/month during development

---

## Phase Timeline (3 Go-Lives)

```
v0.2 (Dec 2024) ─────────────────────────────────────────────────────── v1.0 (Nov 2025)
  │                                                                             │
  ├─ Phase 1: Platform ─┬─ Phase 2: Marketplace ─┬─ Phase 3: Operations ──────┤
  │   (Weeks 1-12)      │   (Weeks 13-24)        │   (Weeks 25-46)             │
  │                     │                         │                             │
  └─ v0.5 Go-Live       └─ v0.8 Go-Live           └─ v1.0 Go-Live              
     (March 2025)           (June 2025)              (November 2025)
     200 agents working     14 CoEs live            All 15 dimensions
```

---

## Key Architecture Decisions

### 1. KEEP Foundation (Don't Start Over)
**Why:** 90% aligned with Dust.tt (500+ agents), research validated
**Saves:** $10K, 4 weeks
**Risk:** LOW

### 2. DO NOT Build Custom DL Model
**Why:** Not cost-effective at 200 agents (break-even: 10K+ agents)
**Use Instead:** Prompt orchestration with Claude/GPT-4
**Saves:** $100K-600K upfront

### 3. Hybrid Decision Framework
**Tier 1:** Deterministic rules (85% of decisions, $0 cost)  
**Tier 2:** Semantic cache (10%, near-free)  
**Tier 3:** LLM (5%, pay only for hard cases)  
**Result:** 20x cheaper than naive LLM approach

### 4. Event-Driven Wake (vs. Polling)
**Polling Cost:** $3,000/month (agents wake every 5 min)  
**Event-Driven Cost:** $50/month (agents wake on demand)  
**Savings:** $2,950/month

### 5. Template-Driven Development
**Problem:** 14 CoEs to build in 4 weeks  
**Solution:** new_coe_agent_template.py = Copy, customize, deploy  
**Result:** Parallel development, consistent quality

---

## Testing Strategy

### Unit Tests (Deterministic Rules)
```bash
# Test agent logic without LLM
pytest tests/test_base_agent.py -k test_deterministic
```

### Integration Tests (With Services)
```bash
# Test with PostgreSQL, Redis, Pinecone
pytest tests/test_integration.py
```

### Shadow Mode (Before Production)
```bash
# Run new agent alongside old logic, compare
pytest tests/test_shadow_mode.py --agent=content_marketing
```

### Load Tests (200 Agents)
```bash
# Simulate 1K events/hour
locust -f tests/load_test.py --users 200 --spawn-rate 10
```

---

## When to Use What Template

| Week | Dimension | Template | Purpose |
|------|-----------|----------|---------|
| 1-2 | Wake Protocol | event_bus_template.py | Event-driven wake |
| 3-4 | Context | output_generation_template.py | GitHub integration |
| 5-6 | Resource Mgmt | resource_manager_template.py | Budgets, rate limits |
| 7-8 | Error Handling | error_handler_template.py | Circuit breakers, retry |
| 9-10 | Observability | observability_template.py | Metrics, traces, costs |
| 13-14 | Coordinators | coe_coordinator_template.py | Regional coordinators |
| 15-18 | New CoEs | new_coe_agent_template.py | Create 13 CoEs |
| 19-20 | Communication | communication_protocol_template.py | Agent messaging |
| 25-28 | Security | security_template.py | Auth, encryption, audit |
| 29-32 | Learning | learning_template.py | Feedback loop, fine-tuning |

---

## Debugging Tips

### Agent Not Waking
```python
# Check should_wake() logic
agent.should_wake(event)  # Returns True/False + reason

# Check event bus subscriptions
event_bus.list_subscriptions()  # Shows active patterns
```

### High LLM Costs
```python
# Check decision breakdown
agent.get_cost_breakdown()  
# Should be: 85% deterministic, 10% cached, 5% LLM

# If > 20% LLM, add more deterministic rules
```

### Agent Conflicts (Multiple Agents on Same Task)
```python
# Check RACI assignments
coordinator.get_agent_for_task(task)  # Should return single agent

# Check handoff logic
agent.should_handoff(task)  # Returns target agent if needed
```

---

## Getting Help

### Documentation
- **Full Context**: [BASELINE_V02_README.md](./BASELINE_V02_README.md)
- **Roadmap**: [IMPLEMENTATION_PLAN](./docs/IMPLEMENTATION_PLAN_V02_TO_V10.md)
- **Research**: [docs/research/](./docs/research/)

### Code Examples
- **Base Agent**: [waooaw/agents/base_agent.py](./waooaw/agents/base_agent.py)
- **WowVision**: [waooaw/agents/wowvision_prime.py](./waooaw/agents/wowvision_prime.py)
- **Templates**: [templates/](./templates/)

### Architecture
- **Database**: [waooaw/database/base_agent_schema.sql](./waooaw/database/base_agent_schema.sql)
- **Infrastructure**: [infrastructure/docker/docker-compose.yml](./infrastructure/docker/docker-compose.yml)

---

## Version Progression

```
v0.1 (Dec 24) - Prototype, 5 dimensions only
v0.2 (Dec 25) - Baseline, research integrated, 15 dimensions scoped ← YOU ARE HERE
v0.3 (Week 2) - Event-driven wake working
v0.4 (Week 4) - Output generation working
v0.5 (Week 12) - Platform Go-Live (200 agents)
v0.6 (Week 14) - CoE Coordinators working
v0.7 (Week 20) - Communication protocol working
v0.8 (Week 24) - Marketplace Go-Live (14 CoEs)
v0.9 (Week 36) - Security, learning, reputation
v1.0 (Week 46) - Operations Go-Live (all 15 dimensions)
```

---

## Frequently Asked Questions

### Why keep existing code instead of starting over?
Research validated our foundation (90% aligned with Dust.tt). Starting over loses 4 weeks + $10K, higher risk.

### Why not build custom DL model?
Not cost-effective at 200 agents. Break-even: 10K+ agents, $5K+/month LLM costs. We're at $50-200/month with prompt orchestration.

### How to create new agent?
Use `templates/new_coe_agent_template.py`. Copy, customize specialization, deploy. ~2 days per agent.

### What's the critical path?
Week 1-2 (event-driven wake) → Week 3-4 (outputs) → Week 5-12 (infrastructure) → Platform Go-Live. Cannot skip.

### How to track costs?
Observability template (Week 9-10) adds cost tracking per agent/CoE/customer. Budget alerts at $150/month.

---

## Next Action

**Start Week 1-2 Implementation:**

```bash
# 1. Copy template
cp templates/event_bus_template.py waooaw/orchestration/event_bus.py

# 2. Add should_wake() to base_agent.py
# (See integration code in template)

# 3. Create wake_events.py
# Define event patterns per CoE

# 4. Test
pytest tests/test_event_driven_wake.py

# 5. Deploy v0.3
git commit -m "feat: event-driven wake (Dimension 1)"
git tag v0.3.0
```

**Follow:** [IMPLEMENTATION_PLAN Week 1-2](./docs/IMPLEMENTATION_PLAN_V02_TO_V10.md#week-1-2-event-driven-wake)

---

_v0.2 Baseline Established - December 25, 2024_
