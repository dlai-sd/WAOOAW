# Story 5.1.10: Agent Factory Mode (Create New Agents)

**Story ID**: 5.1.10  
**Epic**: Epic 5.1 - Operational Portal  
**Priority**: P0  
**Points**: 34  
**Status**: Ready for Development  
**Dependencies**: Story 5.1.0 (Common Components - Progress Tracker, Status Badge, Provisioning Engine, Audit Logger, Health Checker)  
**Risk**: High

---

## User Story

**As a** platform operator  
**I want** a guided wizard to create new agents from templates with configuration, testing, and deployment  
**So that** I can rapidly onboard new agent types without manual infrastructure work

---

## Problem Statement

### Current State
- New agents created manually by editing Python code
- No standardized agent creation process
- Configuration requires code changes and redeployment
- Testing new agents requires manual setup
- No template library or best practices
- Agent registration is manual and error-prone
- Infrastructure provisioning is manual (Docker, K8s)
- No validation of agent capabilities before deployment

### User Pain Points
1. "Need to create 'Sales Agent' but don't know where to start"
2. "Copying WowMemory code and modifying. Is this the right approach?"
3. "Spent 2 hours debugging config file syntax errors"
4. "Agent doesn't work in production. Should have tested before deploying"
5. "Forgot to register agent in AgentRegistry. It's invisible to platform"
6. "Need to provision Redis, setup queues, configure memory. Too many steps"
7. "Every new agent takes 2-3 days of engineering time"
8. "No way to share agent templates across team"

### Impact
- **Time to Create Agent**: 2-3 days (engineering time)
- **Error Rate**: 40% of new agents have config/deployment issues
- **Knowledge Silos**: Only 2 engineers know how to create agents
- **Inconsistency**: Each agent has different structure and patterns
- **Business Risk**: Cannot scale agent creation to meet demand

---

## Proposed Solution

### Agent Factory Wizard

**Multi-Step Guided Creation Process:**

1. **Choose Template**: Start from existing agent or blank template
2. **Configure Basics**: Name, description, tier, capabilities
3. **Define Capabilities**: Skills, tools, memory requirements, integrations
4. **Configure Resources**: CPU, memory, storage, queue settings
5. **Set Policies**: Retry, timeout, rate limiting, security
6. **Test Agent**: Sandbox environment with sample inputs
7. **Review & Deploy**: Generate config, provision infrastructure, deploy

**Post-Creation:**
- Agent registered in AgentRegistry (DRAFT status)
- Infrastructure provisioned (Docker container, queues, memory store)
- Initial health check performed
- Documentation stub generated
- Ready for testing and activation

### Key Features

#### 1. Template Library
**Pre-Built Templates:**
- **Memory Agent**: Context storage and retrieval (WowMemory template)
- **Orchestration Agent**: Workflow coordination (WowOrchestrator template)
- **API Agent**: External service integration (WowAPI template)
- **Data Agent**: Processing and transformation (WowData template)
- **Monitoring Agent**: Observability and alerts (WowLogger template)
- **Blank Template**: Start from scratch

**Template Metadata:**
- Name, description, use case
- Default capabilities and tools
- Resource requirements
- Configuration schema
- Best practices and examples

#### 2. Configuration Builder
**Visual Form-Based Editor:**
- Agent name (auto-generates agent_id)
- Display name and description
- Tier (1-5) with recommendations
- Capabilities list (add/remove)
- Tools integration (API keys, endpoints)
- Memory configuration (type, size, TTL)
- Queue settings (routing, priority)
- Retry policies (max attempts, backoff)
- Timeout settings (operation, workflow)
- Rate limiting (requests/min, concurrency)

**Real-Time Validation:**
- Name uniqueness check
- Resource quota validation
- Configuration schema validation
- Dependency resolution

#### 3. Capability Designer
**Skills Definition:**
- Skill name and description
- Input schema (JSON Schema)
- Output schema (JSON Schema)
- Example inputs/outputs
- Execution timeout

**Tools Integration:**
- Select from tool registry (APIs, databases, services)
- Configure credentials (use Secrets Manager)
- Define tool parameters
- Test connectivity

**Memory Configuration:**
- Memory type (short-term, long-term, episodic)
- Storage backend (Redis, PostgreSQL, vector DB)
- Capacity and TTL
- Access patterns

#### 4. Sandbox Testing Environment
**Test Agent Before Deployment:**
- Isolated container with agent code
- Mock dependencies and tools
- Sample input/output scenarios
- Real-time logs and output
- Performance metrics (latency, memory usage)
- Error simulation (timeouts, failures)

**Test Scenarios:**
- Basic functionality (simple request/response)
- Error handling (invalid input, timeout)
- Performance (high load, large inputs)
- Integration (calls to other agents/tools)

#### 5. Infrastructure Provisioning
**Automated Setup:**
- Docker container creation
- Message queues (commands, events, results)
- Memory store (Redis/PostgreSQL)
- Health check endpoint
- Logging configuration
- Metrics collection

**Resource Allocation:**
- CPU: 0.5-4 cores (based on tier)
- Memory: 512MB-8GB (based on tier)
- Storage: 1GB-100GB (based on needs)
- Network: Internal (agents) + External (tools)

#### 6. Agent Registration
**AgentRegistry Entry:**
- Agent ID (unique)
- Metadata (name, description, version)
- Tier and capabilities
- Status (DRAFT)
- Configuration (JSON)
- Created timestamp
- Owner (user who created)

**Post-Creation Actions:**
- Generate API documentation
- Create default health checks
- Setup monitoring dashboards
- Add to agent discovery

---

## User Flows

### Flow 1: Create Agent from Template
```
1. User navigates to "Agent Factory" page
2. User clicks "Create New Agent"
3. Wizard opens → Step 1: Choose Template
4. User sees 6 templates:
   - Memory Agent (Store and retrieve context)
   - Orchestration Agent (Coordinate workflows)
   - API Agent (Integrate external services)
   - Data Agent (Process and transform data)
   - Monitoring Agent (Observe and alert)
   - Blank Template (Start from scratch)
5. User clicks "Memory Agent" template
6. Preview shows:
   - Description: "Stores and retrieves context with semantic search"
   - Default capabilities: [store, retrieve, search, summarize]
   - Default tools: [Redis, VectorDB, Embeddings API]
   - Resource requirements: CPU 1 core, RAM 2GB, Storage 10GB
7. User clicks "Use Template"
```

### Flow 2: Configure Agent Basics
```
8. Wizard → Step 2: Configure Basics
9. User fills form:
   - Agent Name: "Customer Context Agent"
   - Agent ID: (auto-generated) "WowCustomerContext"
   - Display Name: "Customer Context Manager"
   - Description: "Stores customer conversation history and preferences"
   - Tier: 3 (Recommended for memory agents)
   - Tags: ["customer", "memory", "sales"]
10. Real-time validation:
    ✓ Agent ID is unique
    ✓ Name meets naming conventions
    ✓ Tier 3 quota available (3/10 used)
11. User clicks "Next"
```

### Flow 3: Define Capabilities
```
12. Wizard → Step 3: Define Capabilities
13. Pre-populated from template:
    - store_context (Store customer conversation)
    - retrieve_context (Get conversation history)
    - search_context (Semantic search in history)
    - summarize_context (Generate summary)
14. User adds new capability:
    - Click "Add Capability"
    - Name: "analyze_sentiment"
    - Description: "Analyze customer sentiment from conversation"
    - Input schema: {"text": "string", "customer_id": "string"}
    - Output schema: {"sentiment": "positive|neutral|negative", "confidence": "float"}
    - Timeout: 30 seconds
15. User configures tools:
    - Redis (for short-term storage) ✓ Connected
    - VectorDB (for semantic search) → Configure endpoint
    - Embeddings API → Add API key (use Secrets Manager)
16. User clicks "Next"
```

### Flow 4: Configure Resources
```
17. Wizard → Step 4: Configure Resources
18. Form shows:
    - CPU: [1 core] (slider: 0.5-4 cores)
    - Memory: [2 GB] (slider: 512MB-8GB)
    - Storage: [10 GB] (slider: 1GB-100GB)
    - Queue Priority: [NORMAL] (HIGH, NORMAL, LOW)
    - Max Concurrency: [5] (1-50 concurrent requests)
19. Advanced settings (collapsed):
    - Retry Policy: Max 3 attempts, Exponential backoff
    - Timeout: Operation 30s, Workflow 300s
    - Rate Limiting: 100 requests/min
    - Security: Network isolation: Internal only
20. User adjusts Memory to 4GB (large context storage)
21. System shows: "Estimated cost: ₹15,000/month"
22. User clicks "Next"
```

### Flow 5: Test Agent in Sandbox
```
23. Wizard → Step 5: Test Agent
24. System creates isolated container with agent
25. User sees test scenarios:
    [Scenario 1: Store Context] [Run]
    [Scenario 2: Retrieve Context] [Run]
    [Scenario 3: Search Context] [Run]
    [Custom Test] [Add]
26. User clicks "Run" on Scenario 1
27. Test executes:
    Input: {"customer_id": "cust-123", "text": "Customer wants premium plan"}
    Output: {"status": "stored", "context_id": "ctx-456"}
    Logs: "Connected to Redis... Storing context... Success"
    Duration: 85ms
    Memory: 120MB
    Status: ✅ PASSED
28. User clicks "Run All Scenarios"
29. Results:
    Scenario 1: ✅ PASSED (85ms)
    Scenario 2: ✅ PASSED (45ms)
    Scenario 3: ✅ PASSED (120ms)
30. User clicks "Next"
```

### Flow 6: Review & Deploy
```
31. Wizard → Step 6: Review & Deploy
32. Summary shows:
    ┌──────────────────────────────────────┐
    │ Agent: WowCustomerContext           │
    │ Tier: 3 • Status: DRAFT             │
    ├──────────────────────────────────────┤
    │ Capabilities: 5                      │
    │ • store_context                      │
    │ • retrieve_context                   │
    │ • search_context                     │
    │ • summarize_context                  │
    │ • analyze_sentiment                  │
    ├──────────────────────────────────────┤
    │ Resources                            │
    │ • CPU: 1 core                        │
    │ • Memory: 4 GB                       │
    │ • Storage: 10 GB                     │
    ├──────────────────────────────────────┤
    │ Infrastructure                       │
    │ • Docker container                   │
    │ • Message queues (3)                 │
    │ • Redis (memory store)               │
    │ • VectorDB (semantic search)         │
    ├──────────────────────────────────────┤
    │ Estimated Cost: ₹15,000/month       │
    └──────────────────────────────────────┘
33. User clicks "Deploy Agent"
34. Progress modal shows:
    ⚙️ Creating Docker container... ✅ Done (10s)
    ⚙️ Provisioning message queues... ✅ Done (3s)
    ⚙️ Setting up Redis store... ✅ Done (5s)
    ⚙️ Configuring VectorDB... ✅ Done (8s)
    ⚙️ Registering agent... ✅ Done (1s)
    ⚙️ Running health check... ✅ Done (2s)
35. Success message:
    "✅ Agent WowCustomerContext created successfully!"
    [View Agent] [Create Another] [Done]
36. User clicks "View Agent"
37. Portal navigates to agent detail page (DRAFT status)
```

---

## Technical Implementation

### Backend APIs

**1. Template List API**
```
GET /api/platform/agent-factory/templates

Response:
{
  "templates": [
    {
      "id": "memory-agent",
      "name": "Memory Agent",
      "description": "Store and retrieve context with semantic search",
      "use_case": "Context management, conversation history",
      "tier_recommendation": 3,
      "default_capabilities": ["store", "retrieve", "search", "summarize"],
      "default_tools": ["Redis", "VectorDB", "Embeddings"],
      "resource_defaults": {
        "cpu_cores": 1,
        "memory_mb": 2048,
        "storage_gb": 10
      },
      "config_schema": {...},
      "created_at": "2025-12-01T00:00:00Z",
      "usage_count": 15
    },
    ...
  ]
}
```

**2. Validate Configuration API**
```
POST /api/platform/agent-factory/validate

Body:
{
  "agent_id": "WowCustomerContext",
  "name": "Customer Context Agent",
  "tier": 3,
  "config": {...}
}

Response:
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Memory usage high for tier 3. Consider tier 4."
  ],
  "suggestions": [
    "Add health check capability for better monitoring"
  ]
}
```

**3. Test Agent API**
```
POST /api/platform/agent-factory/test

Body:
{
  "agent_config": {...},
  "test_scenarios": [
    {
      "name": "Store Context",
      "input": {"customer_id": "cust-123", "text": "..."},
      "expected_output": {"status": "stored"}
    }
  ]
}

Response:
{
  "test_id": "test-12345",
  "status": "running",
  "container_id": "sandbox-67890"
}

GET /api/platform/agent-factory/test/{test_id}/results

Response:
{
  "test_id": "test-12345",
  "status": "completed",
  "results": [
    {
      "scenario": "Store Context",
      "status": "PASSED",
      "duration_ms": 85,
      "memory_mb": 120,
      "output": {"status": "stored", "context_id": "ctx-456"},
      "logs": ["Connected to Redis...", "Storing context...", "Success"]
    }
  ]
}
```

**4. Create Agent API**
```
POST /api/platform/agent-factory/agents

Body:
{
  "agent_id": "WowCustomerContext",
  "name": "Customer Context Agent",
  "display_name": "Customer Context Manager",
  "description": "Stores customer conversation history",
  "tier": 3,
  "capabilities": [...],
  "tools": [...],
  "resources": {...},
  "policies": {...}
}

Response:
{
  "agent_id": "WowCustomerContext",
  "status": "provisioning",
  "provisioning_steps": [
    {"step": "create_container", "status": "in_progress"},
    {"step": "provision_queues", "status": "pending"},
    {"step": "setup_memory_store", "status": "pending"},
    {"step": "register_agent", "status": "pending"},
    {"step": "health_check", "status": "pending"}
  ],
  "estimated_duration_seconds": 45
}

GET /api/platform/agent-factory/agents/{agent_id}/provisioning

Response:
{
  "agent_id": "WowCustomerContext",
  "status": "completed",
  "steps": [
    {
      "step": "create_container",
      "status": "completed",
      "duration_seconds": 10,
      "details": "Container ID: abc123"
    },
    ...
  ],
  "registry_status": "DRAFT",
  "next_actions": [
    "Activate agent (POST /agents/{id}/activate)",
    "Run integration tests",
    "Update documentation"
  ]
}
```

**5. Cost Estimation API**
```
POST /api/platform/agent-factory/estimate-cost

Body:
{
  "tier": 3,
  "resources": {
    "cpu_cores": 1,
    "memory_mb": 4096,
    "storage_gb": 10
  },
  "usage_estimates": {
    "requests_per_month": 100000,
    "avg_duration_seconds": 2
  }
}

Response:
{
  "monthly_cost_inr": 15000,
  "breakdown": {
    "compute": 8000,
    "memory": 4000,
    "storage": 1000,
    "network": 1000,
    "other": 1000
  },
  "comparison": {
    "tier_2": 10000,
    "tier_3": 15000,
    "tier_4": 22000
  }
}
```

### Backend Implementation

**Agent Factory Service** (`app/services/agent_factory.py`)
- Load templates from registry
- Validate agent configuration
- Generate agent code from template
- Create sandbox environment for testing
- Provision infrastructure (Docker, queues, storage)
- Register agent in AgentRegistry
- Run post-creation health checks

**Provisioning Engine** (`app/services/provisioning_engine.py`)
- Create Docker container with agent image
- Setup message queues (agent.{id}.commands, agent.{id}.events)
- Configure memory store (Redis/PostgreSQL)
- Setup tool integrations (API keys, endpoints)
- Configure monitoring and logging
- Run initial health check

**Template Manager** (`app/services/template_manager.py`)
- Load template definitions
- Render template with user config
- Validate template schema
- Track template usage and updates

**Sandbox Manager** (`app/services/sandbox_manager.py`)
- Create isolated test container
- Execute test scenarios
- Collect logs and metrics
- Clean up after testing

### Frontend Components

**1. Agent Factory Wizard** (`agent-factory.html`)
- Multi-step wizard (6 steps)
- Progress indicator (Step 3/6)
- Back/Next/Cancel buttons
- Step validation before advancing

**2. Template Selector** (Step 1)
- Grid of template cards
- Template preview on hover
- Filter by use case, tier
- Search templates

**3. Configuration Form** (Steps 2-4)
- Dynamic form fields based on template
- Real-time validation with error messages
- Visual resource sliders
- Cost estimation widget

**4. Sandbox Test View** (Step 5)
- Test scenario list
- Run buttons and results
- Live logs stream
- Performance metrics display

**5. Review Summary** (Step 6)
- Collapsible sections (Capabilities, Resources, Infrastructure)
- Cost breakdown
- Edit buttons to go back to specific step
- Deploy button with progress modal

---

## Acceptance Criteria

### Functional Requirements
- [ ] Template library shows 6+ pre-built templates
- [ ] Click template → Preview with details
- [ ] Use template → Pre-fills wizard with defaults
- [ ] Configure agent basics (name, tier, description)
- [ ] Real-time validation (name uniqueness, tier quota)
- [ ] Add/edit/remove capabilities
- [ ] Configure tools with credential management
- [ ] Set resource limits (CPU, memory, storage)
- [ ] Configure policies (retry, timeout, rate limiting)
- [ ] Test agent in sandbox environment
- [ ] Run test scenarios with live results
- [ ] Review summary with full configuration
- [ ] Deploy agent → Provision infrastructure
- [ ] Track provisioning progress (5 steps)
- [ ] Agent registered in AgentRegistry (DRAFT status)
- [ ] Post-creation: Navigate to agent detail page

### Backend Requirements
- [ ] Template list API returns all templates
- [ ] Validate API checks name uniqueness, schema, quotas
- [ ] Test API creates sandbox and runs scenarios
- [ ] Create agent API provisions infrastructure
- [ ] Provisioning tracked with step-by-step status
- [ ] Agent code generated from template
- [ ] Docker container created and started
- [ ] Message queues provisioned
- [ ] Memory store configured
- [ ] Health check performed
- [ ] Cost estimation API calculates monthly cost

### Edge Cases
- [ ] Agent name already exists → Show error
- [ ] Tier quota exceeded → Show upgrade prompt
- [ ] Invalid configuration → Show validation errors
- [ ] Sandbox test fails → Allow retry or skip
- [ ] Provisioning step fails → Rollback previous steps
- [ ] Tool credentials invalid → Show error before deploy
- [ ] Resource limits exceed platform capacity → Show warning

### Performance
- [ ] Template list loads < 500ms
- [ ] Validation API < 200ms
- [ ] Sandbox creation < 10 seconds
- [ ] Test execution < 30 seconds per scenario
- [ ] Agent provisioning < 60 seconds
- [ ] Wizard responsive (no UI lag)

---

## UI/UX Design

### Template Selector
```
┌─────────────────────────────────────────────────────────────────────┐
│ 🏭 Agent Factory - Create New Agent                                │
│ Step 1 of 6: Choose Template                                       │
├─────────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│ │  💾 Memory  │  │ ⚙️ Orchestr.│  │  🔌 API     │                │
│ │    Agent    │  │    Agent    │  │   Agent     │                │
│ │             │  │             │  │             │                │
│ │ Store and   │  │ Coordinate  │  │ Integrate   │                │
│ │ retrieve    │  │ workflows   │  │ external    │                │
│ │ context     │  │             │  │ services    │                │
│ │             │  │             │  │             │                │
│ │ Tier 3      │  │ Tier 4      │  │ Tier 2      │                │
│ │ 15 uses     │  │ 8 uses      │  │ 22 uses     │                │
│ └─────────────┘  └─────────────┘  └─────────────┘                │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│ │  📊 Data    │  │ 👁️ Monitor  │  │  📝 Blank   │                │
│ │    Agent    │  │    Agent    │  │   Template  │                │
│ └─────────────┘  └─────────────┘  └─────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

### Configuration Form
```
┌─────────────────────────────────────────────────────────────────────┐
│ 🏭 Agent Factory - Create New Agent                                │
│ Step 2 of 6: Configure Basics               [Back] [Next] [Cancel] │
├─────────────────────────────────────────────────────────────────────┤
│ Agent Name *                                                        │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Customer Context Agent                                    ✓     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ Agent ID (auto-generated)                                          │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ WowCustomerContext                                        ✓     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ Display Name *                                                     │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Customer Context Manager                                        │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ Description *                                                       │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Stores customer conversation history and preferences            │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ Tier *                                                             │
│ ○ Tier 1  ○ Tier 2  ● Tier 3  ○ Tier 4  ○ Tier 5                │
│ Recommended: Tier 3 (3/10 agents used)                            │
│                                                                     │
│ Tags (comma-separated)                                             │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ customer, memory, sales                                         │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Sandbox Test View
```
┌─────────────────────────────────────────────────────────────────────┐
│ 🏭 Agent Factory - Create New Agent                                │
│ Step 5 of 6: Test Agent                     [Back] [Next] [Cancel] │
├─────────────────────────────────────────────────────────────────────┤
│ Test Scenarios                                    [Run All]         │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ ✅ Scenario 1: Store Context                      85ms  [View] │ │
│ │ ✅ Scenario 2: Retrieve Context                   45ms  [View] │ │
│ │ ✅ Scenario 3: Search Context                    120ms  [View] │ │
│ │ ⏳ Scenario 4: Custom Test                              [Run]  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ Test Results: Scenario 1 (Store Context)                           │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Status: ✅ PASSED                                               │ │
│ │ Duration: 85ms                                                  │ │
│ │ Memory: 120 MB                                                  │ │
│ │                                                                 │ │
│ │ Input:                                                          │ │
│ │ {"customer_id": "cust-123", "text": "Customer wants premium"}  │ │
│ │                                                                 │ │
│ │ Output:                                                         │ │
│ │ {"status": "stored", "context_id": "ctx-456"}                  │ │
│ │                                                                 │ │
│ │ Logs:                                                           │ │
│ │ [12:00:00] Connected to Redis                                  │ │
│ │ [12:00:00] Storing context for cust-123                        │ │
│ │ [12:00:00] Success: Context stored as ctx-456                  │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Deployment Progress
```
┌─────────────────────────────────────────────────────────────────────┐
│ 🚀 Deploying Agent: WowCustomerContext                             │
├─────────────────────────────────────────────────────────────────────┤
│ ✅ Creating Docker container                              (10s)    │
│ ✅ Provisioning message queues                             (3s)    │
│ ✅ Setting up Redis store                                  (5s)    │
│ ⚙️ Configuring VectorDB                                    (8s)    │
│ ⏳ Registering agent                                               │
│ ⏳ Running health check                                            │
│                                                                     │
│ Progress: ▰▰▰▰▰▰▰▰▱▱ 80%                                           │
│ Estimated time remaining: 5 seconds                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Technical Tasks

### Phase 1: Templates & Validation (3 days)
1. Define template schema and structure
2. Create 6 pre-built templates (Memory, Orchestration, API, Data, Monitoring, Blank)
3. Build template manager service
4. Implement template list API
5. Implement validation API (name, schema, quotas)
6. Write unit tests for validation logic

### Phase 2: Configuration Builder (4 days)
7. Build wizard framework (multi-step, navigation)
8. Implement template selector UI (Step 1)
9. Implement basic config form (Step 2)
10. Implement capability designer (Step 3)
11. Implement resource configurator (Step 4)
12. Add real-time validation and error display
13. Implement cost estimation widget

### Phase 3: Sandbox Testing (4 days)
14. Build sandbox manager service
15. Create isolated test container infrastructure
16. Implement test execution engine
17. Build test API endpoints
18. Implement sandbox test UI (Step 5)
19. Add live logs streaming
20. Add performance metrics display

### Phase 4: Provisioning Engine (5 days)
21. Build provisioning engine service
22. Implement Docker container creation
23. Implement message queue provisioning
24. Implement memory store setup
25. Implement tool integration configuration
26. Build health check system
27. Implement create agent API
28. Add provisioning progress tracking

### Phase 5: Agent Code Generation (3 days)
29. Build code generator from templates
30. Implement configuration to code mapping
31. Generate agent entry point
32. Generate capability implementations
33. Generate tool integrations
34. Add code quality validation

### Phase 6: UI Polish & Testing (4 days)
35. Implement review summary UI (Step 6)
36. Add deployment progress modal
37. Build post-creation success page
38. E2E tests for full wizard flow
39. Test all templates end-to-end
40. Load testing (create 50 agents)
41. Error handling and rollback testing
42. Documentation and user guides

**Total Estimate**: 23 days (1 developer)

---

## Testing Strategy

### Unit Tests
- Template schema validation
- Configuration validation logic
- Code generation from templates
- Cost estimation calculations

### Integration Tests
- Template loading from registry
- Agent provisioning steps
- Docker container creation
- Queue and storage setup
- Health check execution

### E2E Tests
- User creates agent from Memory template → Success
- User creates agent with custom capabilities → Success
- User tests agent in sandbox → All tests pass
- User deploys agent → Infrastructure provisioned
- Provisioning fails → Rollback successful

### Performance Tests
- Create 50 agents sequentially
- Sandbox test execution time
- Provisioning speed
- Wizard UI responsiveness

---

## Success Metrics

### User Experience
- Time to create agent: 2-3 days → 30 minutes (96% reduction)
- Configuration errors: 40% → 5% (guided wizard + validation)
- Knowledge barrier: Only 2 engineers → All operators

### Technical
- Agent creation success rate: 60% → 95%
- Provisioning success rate: 80% → 98%
- Template usage: Track most popular templates

### Business
- Agents created per month: 2-3 → 10-15
- Agent creation cost: ₹50,000 → ₹5,000 (engineer time)
- Time to market: -90%

---

## Dependencies

### Prerequisites
- AgentRegistry with DRAFT status support (Story 5.1.1) ✅
- Infrastructure deployment system (Story 5.1.4) ✅
- Docker and Kubernetes access ✅

### Integrations
- Secrets Manager for tool credentials
- Message queue system (Redis/RabbitMQ)
- Container registry
- Vector database (for memory agents)

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Code generation produces buggy agents | High | Medium | Sandbox testing required, template validation |
| Provisioning failures leave partial state | High | Medium | Rollback mechanism, idempotent operations |
| Template library becomes outdated | Medium | High | Versioning, deprecation warnings, auto-updates |
| Sandbox test doesn't catch production issues | Medium | Medium | Add integration test step after deployment |
| Resource quota abuse | Medium | Low | Quota enforcement, approval for high-tier agents |

---

## Out of Scope

- ❌ Agent code editor (direct Python editing)
- ❌ Custom agent runtime (only Docker supported)
- ❌ Agent migration between environments
- ❌ Agent marketplace (sharing templates publicly)
- ❌ Advanced AI-assisted agent generation
- ❌ Multi-agent creation (bulk wizard)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Code reviewed and merged
- [ ] Unit tests passing (>85% coverage)
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] 6 templates created and tested
- [ ] Documentation updated (user guide, API docs)
- [ ] Deployed to staging and tested
- [ ] Product owner approval
- [ ] Deployed to production

---

**This story enables rapid, standardized agent creation with guided wizard, testing, and automated provisioning.** 🏭
