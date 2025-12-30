# WowAgentFactory Module

The WowAgentFactory is an autonomous agent generator for Platform CoE (Center of Excellence) agents. It automates the creation of new agents through an interactive questionnaire, code generation, and deployment pipeline.

## Architecture

```
waooaw/factory/
├── templates/          # Base CoE template
│   └── base_coe_template.py
├── interfaces/         # Type definitions
│   └── coe_interface.py
├── registry/           # Agent tracking
│   └── agent_registry.py
├── config/             # YAML configuration
│   ├── schema.py
│   └── parser.py
├── engine/             # Jinja2 templates
│   ├── template_engine.py
│   └── templates/
│       └── agent.py.j2
├── questionnaire/      # Requirements gathering
│   └── questionnaire.py
├── generator/          # Code generation
│   └── code_generator.py
├── deployer/           # Deployment automation
│   └── agent_deployer.py
└── validation/         # Quality checks
    └── validator.py
```

## Components

### 1. Base CoE Template (`templates/base_coe_template.py`)
Foundation class that all Platform CoE agents inherit from. Provides:
- Common agent initialization
- Wake protocol interface
- Decision framework interface
- Action execution interface
- Task execution interface

### 2. CoE Interface (`interfaces/coe_interface.py`)
Type definitions and protocols:
- `WakeEvent`: Event that triggers agent wakeup
- `DecisionRequest`: Request for agent decision
- `ActionContext`: Context for action execution
- `TaskDefinition`: Task specification
- `CoEInterface`: Protocol defining required methods

### 3. Agent Registry (`registry/agent_registry.py`)
Central registry for tracking all Platform CoE agents:
- Register/unregister agents
- Query by ID, DID, tier, status
- Track dependencies
- Manage lifecycle (draft → provisioned → active)
- Get platform statistics

### 4. Config System (`config/`)
YAML-based agent specification:
- `schema.py`: AgentSpecConfig dataclass, JSON schema validation
- `parser.py`: YAML file parsing, schema validation
- Supports all 14 Platform CoE agents

### 5. Template Engine (`engine/`)
Jinja2-based code generation:
- Render agent code from templates
- Custom filters (camel_case, snake_case, title_case)
- Template inheritance
- Macro support

### 6. WowAgentFactory Agent (`waooaw/agents/wow_agent_factory.py`)
Main factory agent that orchestrates:
- Interactive questionnaire
- Decision-making (approve/reject/defer)
- Code generation
- DID provisioning
- PR creation
- Agent registration
- Deployment

## Usage

### Creating a New Agent

```python
import asyncio
from waooaw.agents.wow_agent_factory import WowAgentFactory
from waooaw.factory.interfaces.coe_interface import TaskDefinition

async def create_agent():
    # Initialize factory
    factory = WowAgentFactory()
    
    # Create agent via task
    task = TaskDefinition(
        task_id="create-wow-example",
        task_type="create_new_agent",
        description="Create WowExample agent",
        parameters={
            "initial_spec": {
                "agent_id": "WowExample",
                "tier": 3,
                "domain": "example"
            }
        },
        priority=1
    )
    
    # Execute task
    result = await factory.execute_task(task)
    print(f"Agent created: {result}")

asyncio.run(create_agent())
```

### Using Agent Registry

```python
from waooaw.factory.registry import AgentRegistry, AgentStatus

# Get singleton instance
registry = AgentRegistry()

# List all agents
all_agents = registry.list_agents()

# List active agents
active_agents = registry.list_agents(status=AgentStatus.ACTIVE)

# Get specific agent
wow_domain = registry.get_agent("WowDomain")

# Get dependencies
deps = registry.get_dependencies("WowDomain")

# Get statistics
stats = registry.get_statistics()
```

### Using Config System

```python
from waooaw.factory.config import ConfigParser, AgentSpecConfig
from pathlib import Path

# Create parser
parser = ConfigParser()

# Load spec from file
spec = parser.load_spec(Path("config/specs/wowdomain.yaml"))

# Load all specs
all_specs = parser.load_all_specs()

# Save spec
parser.save_spec(spec, Path("output/wowdomain.yaml"))
```

### Using Template Engine

```python
from waooaw.factory.engine import render_agent_code
from waooaw.factory.config.schema import AgentSpecConfig, AgentDomain

# Create spec
spec = AgentSpecConfig(
    coe_name="WowExample",
    display_name="WowExample",
    tier=3,
    domain=AgentDomain.COMMUNICATION,
    version="0.4.2",
    description="Example agent",
    capabilities={"messaging": ["send", "receive"]},
    dependencies=["WowAgentFactory"],
    wake_patterns=["example.*"]
)

# Render agent code
code = render_agent_code(spec)
print(code)
```

## Workflow

1. **Requirements Gathering**: Factory conducts interactive questionnaire
2. **Validation**: Spec validated against schema and architecture principles
3. **Decision**: Factory decides to approve/reject/defer based on:
   - Tier validation (1-6)
   - Dependency availability
   - Resource constraints
   - Duplicate checking
4. **Generation**: Code generated from Jinja2 templates + config
5. **Provisioning**: DID (decentralized identifier) created
6. **PR Creation**: Code submitted as GitHub PR
7. **Registration**: Agent registered in agent registry
8. **Approval**: Awaits WowVision Prime approval
9. **Deployment**: Deployed to Kubernetes

## Testing

```bash
# Run all factory tests
pytest tests/factory/

# Run specific test file
pytest tests/factory/test_base_template.py
pytest tests/factory/test_registry.py

# Run with coverage
pytest tests/factory/ --cov=waooaw/factory --cov-report=html
```

## Configuration

### Agent Spec YAML Format

```yaml
coe_name: WowDomain
display_name: WowDomain
tier: 2
domain: domain
version: 0.4.2
description: Domain-Driven Design Specialist

capabilities:
  modeling:
    - entities
    - aggregates
    - value_objects
  validation:
    - domain_integrity
    - ddd_compliance

constraints:
  - rule: infrastructure-independent
    reason: DDD separation of concerns

dependencies:
  - WowAgentFactory
  - WowEvent

wake_patterns:
  - domain.*
  - wowdomain.*

resource_budget: 30.0

specialization:
  bounded_contexts:
    - agent
    - marketplace
    - billing
```

## Architecture Principles

1. **Template Inheritance**: All agents inherit from `BasePlatformCoE`
2. **Protocol-Based**: Uses Python protocols for duck typing
3. **Async-First**: All agent methods are async
4. **Event-Driven**: Agents wake on event patterns
5. **Stateful**: Agents maintain state (draft → provisioned → active)
6. **Validated**: All specs validated against JSON schema
7. **Testable**: Comprehensive unit tests
8. **Observable**: Extensive logging

## Dependencies

- `jinja2`: Template engine
- `jsonschema`: Config validation
- `pyyaml`: YAML parsing
- `pytest`: Testing
- `pytest-asyncio`: Async test support

## Story Tracking

- Story 1: Base CoE Template (3 pts) ✅
- Story 2: CoE Interface (2 pts) ✅
- Story 3: Agent Registry (3 pts) ✅
- Story 4: Factory Core Logic (5 pts) ✅
- Story 5: Config System (3 pts) ✅
- Story 6: Template Engine (3 pts) ✅
- Story 7: Tests & Docs (2 pts) ✅
- Story 8: Questionnaire System (3 pts) 🔄
- Story 9: Code Generator (5 pts) 🔄
- Story 10: Agent Deployer (3 pts) 🔄
- Story 11: Validation Pipeline (3 pts) 🔄
- Story 12: Integration Tests (3 pts) 🔄

## Epic Details

- **Epic**: #68 WowAgentFactory Core (v0.4.1)
- **Theme**: CONCEIVE
- **Points**: 39
- **Status**: In Progress

---

Generated by WowAgentFactory  
Version: 0.4.1  
Last Updated: 2024-12-27
