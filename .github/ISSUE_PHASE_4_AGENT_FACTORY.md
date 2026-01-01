# Phase 4: Agent Factory (Story 5.1.10)

**Story**: 5.1.10 Agent Factory Mode  
**Total Points**: 34  
**Duration**: Weeks 7-9 (February 12 - March 5, 2026)  
**Status**: 🚧 IN PROGRESS

**Started**: January 15, 2026  
**Team**: 1-2 developers

---

## Summary

Build a wizard-based interface to create and deploy new agents from templates in <5 minutes.

**Goal**: Reduce agent creation time from 30 minutes → 5 minutes

**Key Features**:
- 6 pre-built agent templates
- Step-by-step wizard interface
- Configuration validation
- Sandbox testing environment
- Automated infrastructure provisioning
- Real-time deployment monitoring

---

## Story 5.1.10: Agent Factory Mode (34 Points)

**Goal**: Wizard to create new agents from templates with sandbox testing

**Duration**: 3 weeks  
**Team**: 2 developers  
**Dependencies**: Phase 1 (components), Phase 2 (agent management), Phase 3 (observability)  
**Status**: 🚧 IN PROGRESS

### Features

#### 1. Agent Templates (6 templates)

Pre-built templates for common agent types:

| Template | Description | Use Case | Complexity |
|----------|-------------|----------|------------|
| **Memory Agent** | Short-term + long-term memory | Knowledge retention, context | Medium |
| **Orchestration Agent** | Multi-step workflows | Complex tasks, dependencies | High |
| **API Agent** | External API integration | Third-party services | Low |
| **Data Agent** | Data processing pipelines | ETL, transformations | Medium |
| **Monitoring Agent** | Health checks + alerting | System monitoring | Low |
| **Blank Agent** | Start from scratch | Custom requirements | High |

**Template Structure**:
```python
class AgentTemplate(rx.Base):
    template_id: str
    name: str
    description: str
    category: str  # memory, orchestration, api, data, monitoring, custom
    icon: str
    complexity: str  # low, medium, high
    estimated_time: str  # "5 min", "10 min", "15 min"
    default_config: dict
    required_capabilities: List[str]
    optional_capabilities: List[str]
    dependencies: List[str]
    resource_requirements: dict  # cpu, memory, storage
```

#### 2. Wizard Flow (6 steps)

**Step 1: Choose Template**
- Card-based template selection
- Filter by category, complexity
- Preview template details
- "Start from Blank" option

**Step 2: Configure Agent**
- **Basic Info**:
  - Agent name (validation: unique, alphanumeric)
  - Description (max 200 chars)
  - Tier (Starter/Professional/Enterprise)
  
- **Capabilities**:
  - Select from required capabilities
  - Add optional capabilities
  - Custom capabilities (text input)
  
- **Specializations**:
  - Industry (Healthcare, Education, Sales, etc.)
  - Domain expertise
  - Language support
  
- **Resources**:
  - CPU allocation (0.5, 1, 2, 4 cores)
  - Memory limit (512MB, 1GB, 2GB, 4GB)
  - Storage (1GB, 5GB, 10GB, 20GB)
  
- **Advanced**:
  - Environment variables (key-value pairs)
  - Dependencies (package names)
  - Rate limits (requests/sec)

**Step 3: Test in Sandbox**
- Isolated testing environment
- Run sample tasks
- View real-time logs
- Check performance metrics
- Error detection & validation

**Step 4: Provision Infrastructure**
- Automated setup (no manual steps)
- Docker container creation
- Message queue setup
- Storage allocation
- Monitoring configuration
- Progress tracking

**Step 5: Review & Deploy**
- Configuration summary
- Cost estimate ($X/month)
- Resource summary
- Deployment timeline
- Confirmation dialog

**Step 6: Monitor Deployment**
- Real-time progress bar
- Provisioning status updates
- Health check results
- First successful task notification
- Link to agent dashboard

#### 3. Validation & Testing

**Configuration Validation**:
- Name uniqueness check
- Resource availability check
- Dependency compatibility check
- Cost threshold validation

**Sandbox Testing**:
- Execute test tasks
- Verify capabilities
- Check memory/CPU usage
- Validate API connections
- Log output inspection

#### 4. Cost Estimation

Calculate operational costs:
- **Compute**: CPU hours × rate
- **Memory**: GB-hours × rate
- **Storage**: GB-months × rate
- **Network**: Data transfer × rate
- **Total**: Monthly estimate with breakdown

**Target**: <$2/month per agent

---

## Technical Design

### State Management

```python
# state/factory_state.py
class FactoryState(rx.State):
    # Wizard state
    current_step: int = 0
    templates: List[AgentTemplate] = []
    selected_template: Optional[AgentTemplate] = None
    
    # Configuration
    agent_config: dict = {}
    validation_errors: List[str] = []
    
    # Sandbox
    sandbox_active: bool = False
    sandbox_logs: List[str] = []
    sandbox_metrics: dict = {}
    
    # Deployment
    deployment_status: str = "idle"  # idle, provisioning, deploying, success, failed
    deployment_progress: int = 0
    deployment_logs: List[str] = []
    
    # Methods
    def load_templates(self)
    def select_template(self, template_id: str)
    def update_config(self, field: str, value: Any)
    def validate_config(self) -> bool
    def start_sandbox_test(self)
    def stop_sandbox_test(self)
    def calculate_cost_estimate(self) -> dict
    def deploy_agent(self)
    def reset_wizard(self)
```

### Pages

```python
# pages/factory.py
def factory_page() -> rx.Component:
    """
    Agent Factory wizard page.
    
    Steps:
    1. Choose Template
    2. Configure Agent
    3. Test in Sandbox
    4. Provision Infrastructure
    5. Review & Deploy
    6. Monitor Deployment
    """
```

### Components

| Component | Description | LOC | Status |
|-----------|-------------|-----|--------|
| `components/factory/template_card.py` | Template selection card | 120 | ⏳ |
| `components/factory/wizard_stepper.py` | Step progress indicator | 80 | ⏳ |
| `components/factory/config_form.py` | Configuration form | 250 | ⏳ |
| `components/factory/sandbox_panel.py` | Sandbox testing UI | 200 | ⏳ |
| `components/factory/cost_estimator.py` | Cost breakdown | 150 | ⏳ |
| `components/factory/deployment_monitor.py` | Deployment progress | 180 | ⏳ |

---

## APIs Required

```python
# Template management
GET  /api/platform/factory/templates          # List all templates
GET  /api/platform/factory/templates/{id}     # Get template details

# Configuration & validation
POST /api/platform/factory/validate           # Validate config
POST /api/platform/factory/cost-estimate      # Calculate costs

# Sandbox testing
POST /api/platform/factory/sandbox/start      # Start sandbox
POST /api/platform/factory/sandbox/execute    # Run test task
GET  /api/platform/factory/sandbox/logs       # Get sandbox logs
POST /api/platform/factory/sandbox/stop       # Stop sandbox

# Deployment
POST /api/platform/factory/agents             # Create & deploy agent
GET  /api/platform/factory/agents/{id}/status # Deployment status
WS   /ws/factory/deployment/{id}              # Real-time updates
```

---

## Database Schema

```sql
-- Agent templates
CREATE TABLE agent_templates (
  template_id VARCHAR(255) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(50) NOT NULL,
  complexity VARCHAR(20) NOT NULL,
  default_config JSONB NOT NULL,
  required_capabilities JSONB,
  optional_capabilities JSONB,
  dependencies JSONB,
  resource_requirements JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Factory deployments (tracking)
CREATE TABLE factory_deployments (
  deployment_id UUID PRIMARY KEY,
  agent_id VARCHAR(255) NOT NULL,
  template_id VARCHAR(255) NOT NULL,
  config JSONB NOT NULL,
  status VARCHAR(50) NOT NULL,  -- provisioning, deploying, success, failed
  progress INT DEFAULT 0,
  cost_estimate DECIMAL(10,2),
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP
);

-- Sandbox test results
CREATE TABLE sandbox_tests (
  test_id UUID PRIMARY KEY,
  deployment_id UUID REFERENCES factory_deployments(deployment_id),
  test_type VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL,  -- running, passed, failed
  logs TEXT,
  metrics JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_factory_deployments_status ON factory_deployments(status, created_at DESC);
CREATE INDEX idx_sandbox_tests_deployment ON sandbox_tests(deployment_id, created_at DESC);
```

---

## Success Criteria

- [ ] <5 minutes from start to production agent
- [ ] 100% config validation (no runtime errors)
- [ ] 90% agents use templates (not blank)
- [ ] <$2/month per agent operational cost
- [ ] 6 templates available
- [ ] Wizard completes all 6 steps
- [ ] Sandbox testing works
- [ ] Real-time deployment monitoring
- [ ] Cost estimation accurate within 10%

---

## Implementation Plan

### Week 1: Foundation (8 points)
- [ ] Create `state/factory_state.py` with FactoryState
- [ ] Create 6 agent templates (mock data)
- [ ] Create `pages/factory.py` with wizard layout
- [ ] Create `components/factory/wizard_stepper.py`
- [ ] Create `components/factory/template_card.py`
- [ ] Add /factory route to app.py
- [ ] Add Factory link to navigation

### Week 2: Wizard Steps (13 points)
- [ ] Step 1: Template selection UI
- [ ] Step 2: Configuration form (`config_form.py`)
- [ ] Step 3: Sandbox testing panel (`sandbox_panel.py`)
- [ ] Step 4: Provisioning automation (mock)
- [ ] Step 5: Review & cost estimator (`cost_estimator.py`)
- [ ] Step 6: Deployment monitor (`deployment_monitor.py`)

### Week 3: Polish & Testing (13 points)
- [ ] Configuration validation logic
- [ ] Error handling & user feedback
- [ ] Cost calculation logic
- [ ] Mock deployment simulation
- [ ] Navigation between steps
- [ ] Reset wizard functionality
- [ ] Integration testing
- [ ] Documentation

---

## Mock Data

### Templates
```python
templates = [
    AgentTemplate(
        template_id="tmpl-memory",
        name="Memory Agent",
        description="Agent with short-term and long-term memory capabilities",
        category="memory",
        complexity="medium",
        estimated_time="10 min",
        default_config={
            "memory_type": "hybrid",
            "retention_days": 30,
            "max_context_size": 10000
        },
        required_capabilities=["memory_storage", "context_retrieval"],
        optional_capabilities=["semantic_search", "summarization"],
        dependencies=["redis", "postgresql"],
        resource_requirements={
            "cpu_cores": 1,
            "memory_gb": 2,
            "storage_gb": 10
        }
    ),
    # ... 5 more templates
]
```

---

## Related Documents

- [Platform Portal Master Plan](../docs/platform/PLATFORM_PORTAL_MASTER_PLAN.md)
- [Phase 1 Tracking](.github/ISSUE_STORY_5.1.0.md)
- [Phase 2 Tracking](.github/ISSUE_PHASE_2_CORE_PORTAL.md)
- [Phase 3 Tracking](.github/ISSUE_PHASE_3_OBSERVABILITY.md)

---

**Last Updated**: January 15, 2026  
**Status**: 🚧 IN PROGRESS - Starting Phase 4  
**Target**: <5 min agent creation time
