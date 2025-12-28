# Orchestration Two Paths: Epic & Story Breakdown

**Version**: 1.0  
**Date**: December 28, 2025  
**Status**: Design Complete - Ready for Implementation  
**Document Structure**: 4 Chunks (Length Limit Management)

---

## Document Navigation

- **Chunk 1**: Overview + Agent Factory Path (Epics 1-3) ← YOU ARE HERE
- **Chunk 2**: Agent Factory Path (Epics 4-6) + Testing
- **Chunk 3**: Agent Service Path (Epics 1-3) 
- **Chunk 4**: Agent Service Path (Epics 4-6) + Integration Matrix

---

## Executive Summary

WAOOAW platform orchestration operates on **two distinct paths**:

1. **Agent Factory Path** - CREATE agents (bootstrap, configure, deploy)
2. **Agent Service Path** - USE agents (execute tasks, handle events, deliver value)

Both paths use **jBPM-inspired orchestration** but serve fundamentally different purposes and have different characteristics.

### Quick Comparison

| Aspect | Agent Factory | Agent Service |
|--------|--------------|---------------|
| **Purpose** | Create new agents | Execute tasks with existing agents |
| **Frequency** | Occasional (19-33 times) | Continuous (1000s/day) |
| **Duration** | Hours to days | Seconds to minutes |
| **Human Involvement** | Required (approvals) | Automated (escalate on failure) |
| **Pattern** | Sequential + approval gates | Parallel + decision gates |
| **Orchestration Type** | User Task heavy | Service Task heavy |
| **State** | Persistent (agent lives on) | Ephemeral (task completes) |
| **Rollback** | Full compensation | Partial compensation |
| **SLA** | Days | Seconds to minutes |

### Architecture Context

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────┐      ┌──────────────────────────┐   │
│  │  PATH 1: Agent Factory │      │ PATH 2: Agent Service    │   │
│  │  (Create Agents)       │      │ (Use Agents)             │   │
│  ├───────────────────────┤      ├──────────────────────────┤   │
│  │ • Bootstrap           │      │ • PR Review              │   │
│  │ • Configure           │      │ • Content Generation     │   │
│  │ • Test                │      │ • Validation             │   │
│  │ • Deploy              │      │ • Monitoring             │   │
│  │ • Register            │      │ • Alerting               │   │
│  └───────────────────────┘      └──────────────────────────┘   │
│           ↓                                ↓                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         Workflow Engine (jBPM-inspired patterns)           │ │
│  │  • Service Tasks  • User Tasks  • Timers  • Gateways      │ │
│  └────────────────────────────────────────────────────────────┘ │
│           ↓                                ↓                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Message Bus (Redis Streams)                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│           ↓                                ↓                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │           State Store (PostgreSQL)                         │ │
│  │  • Workflow instances  • Process variables  • Audit trail │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

# CHUNK 1: Agent Factory Path (Epics 1-3)

## PATH 1: Agent Factory Orchestration

**Mission**: Enable platform to scale from 1 agent to 200+ agents via automated agent creation, configuration, testing, and deployment.

**Timeline**: 12 weeks (3 months)  
**Owner**: WowAgentFactory (Platform CoE Agent #3)  
**Users**: Platform administrators, marketplace operators

---

## Epic 1: Agent Template System

**Goal**: Build DNA-based agent template library that enables rapid agent generation

**Duration**: 2 weeks  
**Priority**: P0 (Blocker for all agent creation)  
**Success Criteria**:
- ✅ 14 Platform CoE templates available
- ✅ 14 Customer-facing templates available (7 Marketing + 7 Education) - **For reference only**
- ✅ Template validation passes 100% of tests
- ✅ Generate agent from template in <5 minutes

### Story 1.1: Universal Agent Genome Implementation

**Description**: Implement the base DNA that all agents inherit (95% shared code)

**Acceptance Criteria**:
- [ ] `UniversalAgentGenome` class with 8 core genes
- [ ] Core genes: wake_protocol, decision_framework, task_execution, learning_system, message_handling, error_recovery, observability, resource_management
- [ ] DNA → Agent compiler (`express()` method)
- [ ] Gene expression produces functional agent class
- [ ] Unit tests for each core gene (8 x 10 tests = 80 tests)

**Technical Details**:
```python
# waooaw/dna/universal_genome.py
class UniversalAgentGenome:
    CORE_GENES = {
        'wake_protocol': WakeProtocolGene(),
        'decision_framework': DecisionFrameworkGene(),
        'task_execution': TaskExecutionGene(),
        'learning_system': LearningSystemGene(),
        'message_handling': MessageHandlingGene(),
        'error_recovery': ErrorRecoveryGene(),
        'observability': ObservabilityGene(),
        'resource_management': ResourceManagementGene()
    }
    
    specialization_genes: Dict[str, Gene] = {}
    
    def express(self) -> Agent:
        """DNA → Living Agent"""
        agent_class = self._generate_class()
        agent = agent_class()
        
        # Inject core capabilities
        for gene_name, gene in self.CORE_GENES.items():
            capability = gene.express()
            setattr(agent, gene_name, capability)
        
        # Inject specialization
        for gene_name, gene in self.specialization_genes.items():
            capability = gene.express()
            setattr(agent, gene_name, capability)
        
        return agent
```

**Files to Create**:
- `waooaw/dna/__init__.py`
- `waooaw/dna/universal_genome.py` (200 lines)
- `waooaw/dna/base_gene.py` (100 lines)
- `waooaw/dna/core_genes/wake_protocol_gene.py` (150 lines)
- `waooaw/dna/core_genes/decision_framework_gene.py` (150 lines)
- `waooaw/dna/core_genes/task_execution_gene.py` (150 lines)
- `waooaw/dna/core_genes/learning_system_gene.py` (150 lines)
- `waooaw/dna/core_genes/message_handling_gene.py` (150 lines)
- `waooaw/dna/core_genes/error_recovery_gene.py` (150 lines)
- `waooaw/dna/core_genes/observability_gene.py` (150 lines)
- `waooaw/dna/core_genes/resource_management_gene.py` (150 lines)
- `tests/dna/test_universal_genome.py` (300 lines, 80 tests)

**Estimated Effort**: 5 days  
**Dependencies**: None

---

### Story 1.2: Specialization Gene Library

**Description**: Implement 14 Platform CoE specialization genes (50 lines each)

**Acceptance Criteria**:
- [ ] 14 specialization genes implemented
- [ ] Each gene: 40-60 lines (avg 50)
- [ ] Genes can be combined with universal genome
- [ ] Gene validation ensures compliance with vision
- [ ] Unit tests for each gene (14 x 5 tests = 70 tests)

**Genes to Implement**:
1. VisionGene - Vision validation capability
2. DomainGene - Domain expertise (DDD patterns)
3. QualityGene - Testing capability
4. OpsGene - Engineering excellence
5. SecurityGene - Security & compliance
6. MarketplaceGene - Marketplace operations
7. AuthGene - Identity & access management
8. PaymentGene - Revenue operations
9. NotificationGene - Communication systems
10. AnalyticsGene - Business intelligence
11. ScalingGene - Performance & auto-scaling
12. IntegrationGene - External API management
13. SupportGene - Customer success
14. FactoryGene - Agent creation

**Technical Details**:
```python
# waooaw/dna/specialization_genes/vision_gene.py
class VisionGene(Gene):
    """Vision Guardian specialization"""
    
    def express(self) -> VisionValidationCapability:
        return VisionValidationCapability(
            layer1_constraints=IMMUTABLE,
            layer2_policies=LEARNABLE,
            layer3_guidelines=FLEXIBLE,
            validation_modes=['strict', 'permissive', 'learning'],
            escalation_threshold=0.7
        )
    
    def validate(self) -> bool:
        """Ensure gene complies with vision"""
        return (
            self.has_layer_separation() and
            self.has_escalation_logic() and
            self.has_learning_capability()
        )
```

**Files to Create**:
- `waooaw/dna/specialization_genes/__init__.py`
- `waooaw/dna/specialization_genes/vision_gene.py` (50 lines)
- `waooaw/dna/specialization_genes/domain_gene.py` (50 lines)
- `waooaw/dna/specialization_genes/quality_gene.py` (50 lines)
- ... (11 more genes, 50 lines each)
- `tests/dna/test_specialization_genes.py` (400 lines, 70 tests)

**Estimated Effort**: 3 days  
**Dependencies**: Story 1.1

---

### Story 1.3: Customer-Facing Agent Templates (Reference Only)

**Description**: Create 14 customer-facing agent templates (Marketing, Education) - **For reference and demonstration purposes only**

**Acceptance Criteria**:
- [ ] 7 Marketing agent templates (**Reference only**)
- [ ] 7 Education agent templates (**Reference only**)
- [ ] Each template includes: DNA, config YAML, test suite, README
- [ ] Template validation passes
- [ ] Generate customer agent from template in <5 minutes

**Note**: These templates are for demonstrating the agent factory capabilities, not for production deployment at this stage.

**Marketing Agents (7)**:
1. Content Marketing Agent (Healthcare specialist)
2. Social Media Agent (B2B specialist)
3. SEO Agent (E-commerce specialist)
4. Email Marketing Agent
5. PPC Advertising Agent
6. Brand Strategy Agent
7. Influencer Marketing Agent

**Education Agents (7)**:
1. Math Tutor (JEE/NEET specialist)
2. Science Tutor (CBSE specialist)
3. English Language Tutor
4. Test Prep Coach
5. Career Counseling Agent
6. Study Planning Agent
7. Homework Help Agent

**Technical Details**:
```yaml
# templates/customer/marketing/content_marketing_agent.yaml
agent:
  id: content_marketing_agent
  type: customer_facing
  domain: marketing
  role: content_creation
  
  dna:
    base: UniversalAgentGenome
    specialization_genes:
      - ContentCreationGene
      - SEOGene
      - BrandVoiceGene
  
  config:
    subscription_tier: professional  # Can create 20 posts/month
    industry: Healthcare  # From IndustryEnum (11 industries)
    specialty: satellite_data_health_insights
    content_types: [blog, social_post, email]
    voice: friendly
    
  capabilities:
    - create_content
    - optimize_seo
    - schedule_posts
    - analyze_performance
  
  integrations:
    - linkedin
    - twitter
    - wordpress
    - google_analytics
```

**Files to Create** (**Reference only**):
- `templates/customer/marketing/` (7 agent templates)
- `templates/customer/education/` (7 agent templates)
- Each template includes:
  - `{agent_name}_dna.py` (DNA definition)
  - `{agent_name}_config.yaml` (Configuration)
  - `{agent_name}_test.py` (Test suite)
  - `README.md` (Documentation)

**Estimated Effort**: 4 days  
**Dependencies**: Story 1.1, Story 1.2

---

### Story 1.4: Template Validation Framework

**Description**: Build validation system to ensure templates are correct, complete, and compliant

**Acceptance Criteria**:
- [ ] Template validator checks DNA integrity
- [ ] Config validation (required fields, types, ranges)
- [ ] Vision compliance validation
- [ ] Test suite validation (minimum coverage 80%)
- [ ] Performance validation (agent creation <5 min)
- [ ] CLI command: `python -m waooaw.dna.validate <template_path>`

**Technical Details**:
```python
# waooaw/dna/validator.py
class TemplateValidator:
    """Validates agent templates before use"""
    
    def validate(self, template_path: str) -> ValidationResult:
        results = []
        
        # 1. DNA integrity check
        results.append(self._validate_dna(template_path))
        
        # 2. Config validation
        results.append(self._validate_config(template_path))
        
        # 3. Vision compliance
        results.append(self._validate_vision_compliance(template_path))
        
        # 4. Test suite check
        results.append(self._validate_tests(template_path))
        
        # 5. Performance check
        results.append(self._validate_performance(template_path))
        
        return ValidationResult(
            passed=all(r.passed for r in results),
            checks=results
        )
    
    def _validate_dna(self, template_path: str) -> CheckResult:
        """Ensure DNA can express into functional agent"""
        try:
            dna = self._load_dna(template_path)
            agent = dna.express()
            return CheckResult(
                name="DNA Integrity",
                passed=isinstance(agent, WAAOOWAgent),
                message="DNA successfully expressed into agent"
            )
        except Exception as e:
            return CheckResult(
                name="DNA Integrity",
                passed=False,
                message=f"DNA expression failed: {str(e)}"
            )
```

**Files to Create**:
- `waooaw/dna/validator.py` (300 lines)
- `waooaw/dna/validation_rules.py` (200 lines)
- `tests/dna/test_validator.py` (250 lines, 30 tests)

**Estimated Effort**: 3 days  
**Dependencies**: Story 1.1, Story 1.2, Story 1.3

---

## Epic 2: Agent Factory Workflow Engine

**Goal**: Build WowAgentFactory agent with orchestrated workflows for agent creation

**Duration**: 3 weeks  
**Priority**: P0  
**Success Criteria**:
- ✅ WowAgentFactory can create agents from templates
- ✅ Full workflow orchestration (service tasks + user tasks + gateways)
- ✅ Human approval gates functional
- ✅ Rollback/compensation working
- ✅ End-to-end agent creation workflow completes in <30 minutes

### Story 2.1: WowAgentFactory Agent Implementation

**Description**: Build the agent that creates other agents (meta-agent)

**Acceptance Criteria**:
- [ ] WowAgentFactory inherits from WAAOOWAgent
- [ ] Core methods: generate_agent(), configure_agent(), test_agent(), deploy_agent()
- [ ] Integrates with template system (Epic 1)
- [ ] Can express DNA into functional agent code
- [ ] Unit tests (15 tests minimum)

**Technical Details**:
```python
# waooaw/agents/wowagent_factory.py
class WowAgentFactory(WAAOOWAgent):
    """
    Platform CoE Agent #3: Agent Bootstrapper
    
    Specialization: Create new agents from templates
    """
    
    def __init__(self, config: dict):
        super().__init__(agent_id="WowAgentFactory", config=config)
        self.template_library = TemplateLibrary()
        self.dna_compiler = DNACompiler()
    
    def generate_agent(
        self, 
        template_name: str, 
        customization: dict
    ) -> AgentSpec:
        """
        Generate agent from template + customizations
        
        Args:
            template_name: Name of template (e.g., "content_marketing_agent")
            customization: Dict with industry, specialty, config overrides
        
        Returns:
            AgentSpec with generated code, config, tests
        """
        # Load template
        template = self.template_library.get(template_name)
        
        # Apply customizations
        customized_dna = template.dna.customize(customization)
        customized_config = template.config.merge(customization)
        
        # Generate agent code
        agent_code = self.dna_compiler.express_to_code(customized_dna)
        
        # Generate test suite
        test_code = self._generate_tests(customized_dna)
        
        return AgentSpec(
            agent_id=f"{template_name}_{uuid.uuid4().hex[:8]}",
            code=agent_code,
            config=customized_config,
            tests=test_code,
            dna=customized_dna
        )
    
    def configure_agent(self, spec: AgentSpec, environment: str) -> ConfiguredAgent:
        """Set up agent environment (secrets, connections, subscriptions)"""
        # Create database tables
        self._create_agent_tables(spec.agent_id)
        
        # Set up secrets (API keys, credentials)
        self._provision_secrets(spec.agent_id, spec.config)
        
        # Register subscriptions
        self._register_subscriptions(spec.agent_id, spec.config)
        
        # Create monitoring dashboards
        self._create_dashboards(spec.agent_id)
        
        return ConfiguredAgent(spec, environment)
    
    def test_agent(self, agent: ConfiguredAgent) -> TestResults:
        """Run agent test suite in sandbox"""
        sandbox = AgentSandbox(agent)
        
        # Run unit tests
        unit_results = sandbox.run_tests(agent.spec.tests)
        
        # Run capability tests
        capability_results = self._test_capabilities(agent, sandbox)
        
        # Run integration tests
        integration_results = self._test_integrations(agent, sandbox)
        
        return TestResults(
            unit=unit_results,
            capability=capability_results,
            integration=integration_results,
            passed=all([
                unit_results.passed,
                capability_results.passed,
                integration_results.passed
            ])
        )
    
    def deploy_agent(self, agent: ConfiguredAgent, environment: str):
        """Deploy agent to production"""
        # Build Docker image
        image = self._build_docker_image(agent)
        
        # Deploy via WowOps
        deployment = self.handoff(
            to_agent="WowOps",
            task={
                'action': 'deploy',
                'image': image,
                'environment': environment,
                'agent_id': agent.spec.agent_id
            }
        )
        
        # Wait for deployment confirmation
        return deployment.wait_for_completion()
```

**Files to Create**:
- `waooaw/agents/wowagent_factory.py` (600 lines)
- `waooaw/factory/template_library.py` (200 lines)
- `waooaw/factory/dna_compiler.py` (300 lines)
- `waooaw/factory/agent_sandbox.py` (250 lines)
- `tests/agents/test_wowagent_factory.py` (400 lines, 15 tests)

**Estimated Effort**: 5 days  
**Dependencies**: Epic 1 complete

---

### Story 2.2: Agent Creation Workflow Definition

**Description**: Define complete agent creation workflow using jBPM patterns

**Acceptance Criteria**:
- [ ] Workflow includes all phases: generate → configure → test → approve → deploy
- [ ] Service tasks for automated steps
- [ ] User tasks for human approval
- [ ] Exclusive gateways for decision points
- [ ] Compensation handlers for rollback
- [ ] Workflow definition in Python DSL

**Technical Details**:
```python
# waooaw/factory/workflows/create_agent_workflow.py
from waooaw.orchestration import (
    Workflow, ServiceTask, UserTask, ExclusiveGateway
)

def create_agent_workflow() -> Workflow:
    """
    Complete agent creation workflow
    
    Flow:
    1. Generate agent from template (automated)
    2. Configure environment (automated)
    3. Run tests (automated)
    4. Architect review (human)
    5. Deploy (automated) OR Cleanup (rollback)
    """
    
    workflow = Workflow(
        id="create_agent",
        version="1.0",
        name="Agent Creation Workflow"
    )
    
    # Variables
    workflow.add_variables({
        'template_name': {'type': 'string', 'required': True},
        'customization': {'type': 'object', 'required': True},
        'environment': {'type': 'string', 'default': 'production'},
        'agent_spec': {'type': 'object'},
        'test_results': {'type': 'object'},
        'approved': {'type': 'boolean'}
    })
    
    # Service Task: Generate agent
    generate_task = ServiceTask(
        id="generate_agent",
        agent=WowAgentFactory,
        method="generate_agent",
        input_variables=["template_name", "customization"],
        output_variables=["agent_spec"],
        timeout=timedelta(minutes=10),
        compensation=cleanup_generated_files
    )
    
    # Service Task: Configure agent
    configure_task = ServiceTask(
        id="configure_agent",
        agent=WowAgentFactory,
        method="configure_agent",
        input_variables=["agent_spec", "environment"],
        output_variables=["configured_agent"],
        timeout=timedelta(minutes=5),
        compensation=delete_agent_resources
    )
    
    # Service Task: Test agent
    test_task = ServiceTask(
        id="test_agent",
        agent=WowAgentFactory,
        method="test_agent",
        input_variables=["configured_agent"],
        output_variables=["test_results"],
        timeout=timedelta(minutes=15),
        compensation=None  # Tests don't need cleanup
    )
    
    # User Task: Architect approval
    approval_task = UserTask(
        id="architect_approval",
        title="Review New Agent: {agent_spec.agent_id}",
        body_template="""
## New Agent Created

**Agent ID**: {agent_spec.agent_id}
**Template**: {template_name}
**Industry**: {customization.industry}
**Specialty**: {customization.specialty}

### Test Results
- Unit Tests: {test_results.unit.passed}/{test_results.unit.total}
- Capability Tests: {test_results.capability.passed}/{test_results.capability.total}
- Integration Tests: {test_results.integration.passed}/{test_results.integration.total}

### Agent Code
```python
{agent_spec.code}
```

**Action**: Approve deployment to {environment}?
""",
        assignee="engineering-lead",
        labels=["agent-factory", "review-required"],
        sla_hours=24,
        on_timeout=escalate_to_cto,
        decision_variable="approved"
    )
    
    # Gateway: Check approval
    approval_gateway = ExclusiveGateway(
        id="check_approval",
        conditions={
            "deploy": lambda ctx: ctx["approved"] == True and ctx["test_results"]["passed"],
            "reject": lambda ctx: ctx["approved"] == False or not ctx["test_results"]["passed"]
        }
    )
    
    # Service Task: Deploy agent
    deploy_task = ServiceTask(
        id="deploy_agent",
        agent=WowAgentFactory,
        method="deploy_agent",
        input_variables=["configured_agent", "environment"],
        output_variables=["deployment_url"],
        timeout=timedelta(minutes=10)
    )
    
    # Service Task: Cleanup (on rejection)
    cleanup_task = ServiceTask(
        id="cleanup",
        agent=WowAgentFactory,
        method="cleanup_agent",
        input_variables=["configured_agent"],
        output_variables=["cleanup_status"],
        timeout=timedelta(minutes=5)
    )
    
    # Build workflow flow
    workflow.start() \
        .then(generate_task) \
        .then(configure_task) \
        .then(test_task) \
        .then(approval_task) \
        .then(approval_gateway) \
        .route("deploy", deploy_task) \
        .route("reject", cleanup_task) \
        .end()
    
    return workflow
```

**Files to Create**:
- `waooaw/factory/workflows/__init__.py`
- `waooaw/factory/workflows/create_agent_workflow.py` (300 lines)
- `waooaw/factory/workflows/compensation_handlers.py` (200 lines)
- `tests/factory/test_create_agent_workflow.py` (350 lines, 20 tests)

**Estimated Effort**: 4 days  
**Dependencies**: Story 2.1, Orchestration Layer (Epic 1 from ORCHESTRATION_LAYER_DESIGN.md)

---

### Story 2.3: Workflow Execution Engine Integration

**Description**: Integrate agent creation workflow with workflow engine

**Acceptance Criteria**:
- [ ] WorkflowEngine can execute create_agent workflow
- [ ] Process variables tracked in database
- [ ] Workflow state persists across restarts
- [ ] Can pause/resume workflows
- [ ] Audit trail complete (who did what when)

**Technical Details**:
```python
# Usage example
from waooaw.orchestration import WorkflowEngine
from waooaw.factory.workflows import create_agent_workflow

# Initialize engine
engine = WorkflowEngine(
    state_store=PostgreSQLStateStore(),
    message_bus=RedisMessageBus()
)

# Register workflow
engine.register(create_agent_workflow())

# Start workflow
instance = engine.start_workflow(
    workflow_id="create_agent",
    variables={
        'template_name': 'content_marketing_agent',
        'customization': {
            'industry': 'Healthcare',  # IndustryEnum value
            'specialty': 'satellite_data_health_insights',
            'content_types': ['blog', 'social_post'],
            'voice': 'friendly'
        },
        'environment': 'production'
    },
    started_by='admin@waooaw.com'
)

# Workflow runs asynchronously...
# Human approves via GitHub issue...
# Workflow completes

# Check status
status = engine.get_status(instance.instance_id)
# status.state == "COMPLETED"
# status.end_time == datetime(2025, 12, 28, 15, 30, 0)
```

**Files to Create**:
- Integration code in existing `waooaw/orchestration/workflow_engine.py`
- `waooaw/factory/factory_orchestrator.py` (200 lines)
- `tests/factory/test_workflow_integration.py` (300 lines, 15 tests)

**Estimated Effort**: 3 days  
**Dependencies**: Story 2.2

---

### Story 2.4: Compensation & Rollback Handlers

**Description**: Implement compensation handlers for each workflow task to enable safe rollback

**Acceptance Criteria**:
- [ ] Compensation handler for file generation (delete files)
- [ ] Compensation handler for environment config (delete resources)
- [ ] Compensation handler for deployment (undeploy)
- [ ] Full rollback on workflow failure
- [ ] Rollback testing (simulate failures at each step)

**Technical Details**:
```python
# waooaw/factory/workflows/compensation_handlers.py

async def cleanup_generated_files(instance: WorkflowInstance):
    """Compensation: Delete generated agent files"""
    agent_spec = instance.get_variable("agent_spec")
    
    # Delete code files
    shutil.rmtree(f"/tmp/agents/{agent_spec.agent_id}")
    
    # Log compensation
    logger.info(
        f"Compensation: Deleted generated files for {agent_spec.agent_id}",
        instance_id=instance.instance_id
    )

async def delete_agent_resources(instance: WorkflowInstance):
    """Compensation: Delete agent environment resources"""
    configured_agent = instance.get_variable("configured_agent")
    agent_id = configured_agent.spec.agent_id
    
    # Delete database tables
    await db.execute(f"DROP SCHEMA IF EXISTS {agent_id} CASCADE")
    
    # Delete secrets
    await secrets_manager.delete_all(agent_id)
    
    # Unregister subscriptions
    await message_bus.unregister_all(agent_id)
    
    # Delete monitoring dashboards
    await monitoring.delete_dashboard(agent_id)
    
    logger.info(
        f"Compensation: Deleted resources for {agent_id}",
        instance_id=instance.instance_id
    )

async def undeploy_agent(instance: WorkflowInstance):
    """Compensation: Undeploy agent from production"""
    deployment_url = instance.get_variable("deployment_url")
    
    # Call WowOps to undeploy
    await wowops_client.undeploy(deployment_url)
    
    logger.info(
        f"Compensation: Undeployed {deployment_url}",
        instance_id=instance.instance_id
    )
```

**Files to Create**:
- `waooaw/factory/workflows/compensation_handlers.py` (300 lines)
- `tests/factory/test_compensation.py` (400 lines, 25 tests - test each failure scenario)

**Estimated Effort**: 4 days  
**Dependencies**: Story 2.2, Story 2.3

---

### Story 2.5: End-to-End Factory Workflow Test

**Description**: Complete integration test of agent creation from start to finish

**Acceptance Criteria**:
- [ ] Create real agent from template
- [ ] Run through complete workflow
- [ ] Simulate human approval
- [ ] Verify agent deployed and functional
- [ ] Test rollback scenarios
- [ ] Performance: Complete workflow in <30 minutes

**Test Scenarios**:
1. Happy path: Create Marketing agent, approve, deploy
2. Test failure: Tests fail, workflow stops, resources cleaned up
3. Rejection: Human rejects, workflow stops, resources cleaned up
4. Timeout: Human doesn't respond in 24h, escalation triggered
5. System failure: Database down during config, rollback works

**Files to Create**:
- `tests/factory/test_e2e_agent_creation.py` (500 lines, 5 comprehensive tests)
- `tests/factory/fixtures/` (Test fixtures for each scenario)

**Estimated Effort**: 4 days  
**Dependencies**: All Epic 2 stories

---

## Epic 3: Agent Marketplace Integration

**Goal**: Connect agent factory to marketplace so customers can order agents

**Duration**: 2 weeks  
**Priority**: P1  
**Success Criteria**:
- ✅ Marketplace UI can trigger agent creation
- ✅ Customer customization flows work
- ✅ Payment integration complete
- ✅ Agent delivery automated
- ✅ Customer onboarding workflow functional

### Story 3.1: Marketplace Order API

**Description**: Build API endpoint that marketplace UI calls to order new agents

**Acceptance Criteria**:
- [ ] POST /api/marketplace/orders endpoint
- [ ] Validates order (template exists, payment confirmed)
- [ ] Triggers agent creation workflow
- [ ] Returns order ID for tracking
- [ ] Webhook for order status updates

**Technical Details**:
```python
# backend/app/api/marketplace.py

@router.post("/orders", response_model=OrderResponse)
async def create_agent_order(
    order: AgentOrderRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Customer orders a new agent from marketplace
    
    Flow:
    1. Validate order (template exists, customization valid)
    2. Check payment (Stripe)
    3. Start agent creation workflow
    4. Return order ID for tracking
    """
    
    # Validate template
    template = await template_library.get(order.template_name)
    if not template:
        raise HTTPException(404, f"Template {order.template_name} not found")
    
    # Validate customization
    validation = template.validate_customization(order.customization)
    if not validation.valid:
        raise HTTPException(400, validation.errors)
    
    # Check payment
    payment = await stripe_client.verify_payment(order.payment_intent_id)
    if payment.status != 'succeeded':
        raise HTTPException(402, "Payment required")
    
    # Create order record
    order_record = await db.orders.create({
        'user_id': current_user.id,
        'template_name': order.template_name,
        'customization': order.customization,
        'payment_id': payment.id,
        'amount': payment.amount,
        'status': 'pending',
        'created_at': datetime.now()
    })
    
    # Start agent creation workflow
    workflow_instance = await workflow_engine.start_workflow(
        workflow_id="create_agent",
        variables={
            'template_name': order.template_name,
            'customization': order.customization,
            'environment': 'production',
            'order_id': order_record.id,
            'customer_id': current_user.id
        },
        started_by=f"customer:{current_user.id}"
    )
    
    # Update order with workflow ID
    await db.orders.update(order_record.id, {
        'workflow_instance_id': workflow_instance.instance_id
    })
    
    return OrderResponse(
        order_id=order_record.id,
        workflow_id=workflow_instance.instance_id,
        status='pending',
        estimated_completion=datetime.now() + timedelta(minutes=30)
    )
```

**Files to Create**:
- `backend/app/api/marketplace.py` (400 lines)
- `backend/app/models/order.py` (150 lines)
- `backend/app/services/order_service.py` (300 lines)
- `tests/api/test_marketplace_orders.py` (350 lines, 20 tests)

**Estimated Effort**: 4 days  
**Dependencies**: Epic 2 complete

---

### Story 3.2: Customer Onboarding Workflow

**Description**: Create workflow that guides customer through agent setup after purchase

**Acceptance Criteria**:
- [ ] Email sent to customer when agent ready
- [ ] Setup wizard in marketplace UI
- [ ] Customer configures: API keys, integrations, preferences
- [ ] Test agent functionality (customer sees demo)
- [ ] Activation confirmation

**Workflow Steps**:
1. Agent deployed → Email sent: "Your agent is ready!"
2. Customer clicks link → Setup wizard opens
3. Step 1: Configure integrations (LinkedIn, Twitter, etc.)
4. Step 2: Set preferences (posting schedule, tone, topics)
5. Step 3: Test agent (generate sample content)
6. Step 4: Activate agent (start subscription)

**Technical Details**:
```python
# waooaw/marketplace/workflows/customer_onboarding.py

def customer_onboarding_workflow() -> Workflow:
    workflow = Workflow(
        id="customer_onboarding",
        version="1.0",
        name="Customer Onboarding Workflow"
    )
    
    # Service Task: Send welcome email
    email_task = ServiceTask(
        id="send_welcome_email",
        agent=WowNotification,
        method="send_email",
        input_variables=["customer_email", "agent_id"],
        output_variables=["email_sent"]
    )
    
    # User Task: Customer configures agent
    config_task = UserTask(
        id="configure_agent",
        title="Set up your {agent_type} agent",
        body_template="Configure your agent via marketplace UI",
        assignee_variable="customer_email",
        sla_hours=72,
        decision_variable="configuration_complete"
    )
    
    # Service Task: Run demo
    demo_task = ServiceTask(
        id="run_demo",
        agent=WowAgentFactory,
        method="run_agent_demo",
        input_variables=["agent_id", "demo_inputs"],
        output_variables=["demo_results"]
    )
    
    # User Task: Customer activates
    activation_task = UserTask(
        id="activate_agent",
        title="Activate your agent",
        body_template="Review demo results and activate",
        assignee_variable="customer_email",
        sla_hours=168,  # 7 days trial
        decision_variable="activated"
    )
    
    workflow.start() \
        .then(email_task) \
        .then(config_task) \
        .then(demo_task) \
        .then(activation_task) \
        .end()
    
    return workflow
```

**Files to Create**:
- `waooaw/marketplace/workflows/customer_onboarding.py` (250 lines)
- `templates/emails/agent_ready.html` (email template)
- `frontend/pages/agent-setup-wizard.html` (UI)
- `tests/marketplace/test_customer_onboarding.py` (300 lines, 15 tests)

**Estimated Effort**: 5 days  
**Dependencies**: Story 3.1

---

### Story 3.3: Payment & Subscription Integration

**Description**: Integrate Stripe for payments and subscription management

**Acceptance Criteria**:
- [ ] Stripe checkout for agent purchase
- [ ] Subscription creation (monthly billing)
- [ ] Webhook handling for payment events
- [ ] Handle failed payments (suspend agent)
- [ ] Cancellation flow (what happens to agent?)

**Technical Details**:
```python
# backend/app/services/payment_service.py

class PaymentService:
    def __init__(self):
        self.stripe = stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    
    async def create_checkout_session(
        self, 
        template_name: str,
        user_id: str
    ) -> stripe.checkout.Session:
        """Create Stripe checkout session for agent purchase"""
        
        template = await template_library.get(template_name)
        
        session = stripe.checkout.Session.create(
            customer_email=user.email,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': template.display_name,
                        'description': template.description,
                    },
                    'unit_amount': template.monthly_price * 100,  # Paise
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{FRONTEND_URL}/orders/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/marketplace",
            metadata={
                'user_id': user_id,
                'template_name': template_name
            }
        )
        
        return session
    
    async def handle_payment_succeeded(self, event: stripe.Event):
        """Webhook: Payment succeeded → Start agent creation"""
        
        session = event.data.object
        metadata = session.metadata
        
        # Start agent creation workflow
        await workflow_engine.start_workflow(
            workflow_id="create_agent",
            variables={
                'template_name': metadata['template_name'],
                'customer_id': metadata['user_id'],
                'subscription_id': session.subscription
            }
        )
    
    async def handle_subscription_cancelled(self, event: stripe.Event):
        """Webhook: Subscription cancelled → Suspend agent"""
        
        subscription = event.data.object
        
        # Find agent by subscription ID
        order = await db.orders.find_one({
            'stripe_subscription_id': subscription.id
        })
        
        # Suspend agent (don't delete, customer keeps history)
        await agent_manager.suspend_agent(order.agent_id)
        
        # Send email notification
        await notification_service.send_email(
            to=order.customer_email,
            subject="Agent subscription ended",
            template="subscription_cancelled"
        )
```

**Files to Create**:
- `backend/app/services/payment_service.py` (500 lines)
- `backend/app/api/webhooks/stripe.py` (300 lines)
- `tests/services/test_payment_service.py` (400 lines, 25 tests)

**Estimated Effort**: 5 days  
**Dependencies**: Story 3.1

---

### Story 3.4: Agent Delivery & Handoff

**Description**: Automate agent delivery to customer after creation and setup

**Acceptance Criteria**:
- [ ] Agent URL generated (customer.agents.waooaw.com/{agent_id})
- [ ] Dashboard created (customer sees agent activity)
- [ ] API keys provisioned (customer can call agent)
- [ ] Documentation delivered (how to use agent)
- [ ] First task automatically triggered (demo)

**Technical Details**:
```python
# waooaw/marketplace/delivery_service.py

class AgentDeliveryService:
    async def deliver_agent(self, order_id: str):
        """
        Complete agent delivery to customer
        
        Steps:
        1. Generate agent URL
        2. Create customer dashboard
        3. Provision API keys
        4. Send delivery email with docs
        5. Trigger first demo task
        """
        
        order = await db.orders.get(order_id)
        agent_id = order.agent_id
        customer = await db.users.get(order.customer_id)
        
        # 1. Generate agent URL
        agent_url = f"https://{customer.subdomain}.agents.waooaw.com/{agent_id}"
        await dns_service.create_subdomain(customer.subdomain)
        await reverse_proxy.add_route(agent_url, agent_id)
        
        # 2. Create customer dashboard
        dashboard = await grafana.create_dashboard(
            name=f"{customer.name} - {agent_id}",
            agent_id=agent_id,
            panels=[
                'task_count',
                'execution_time',
                'success_rate',
                'cost_tracking'
            ]
        )
        
        # 3. Provision API keys
        api_key = await api_key_service.generate(
            agent_id=agent_id,
            customer_id=customer.id,
            scopes=['agent.execute', 'agent.status', 'agent.logs']
        )
        
        # 4. Send delivery email
        await email_service.send(
            to=customer.email,
            subject=f"Your {order.agent_type} agent is live!",
            template="agent_delivery",
            data={
                'agent_url': agent_url,
                'dashboard_url': dashboard.url,
                'api_key': api_key,
                'documentation_url': f"https://docs.waooaw.com/agents/{order.template_name}",
                'agent_id': agent_id
            }
        )
        
        # 5. Trigger first demo task
        await message_bus.publish({
            'type': 'agent.demo_task',
            'agent_id': agent_id,
            'task': order.template.demo_task
        })
        
        # Update order status
        await db.orders.update(order_id, {
            'status': 'delivered',
            'delivered_at': datetime.now(),
            'agent_url': agent_url,
            'api_key_id': api_key.id
        })
```

**Files to Create**:
- `waooaw/marketplace/delivery_service.py` (400 lines)
- `waooaw/marketplace/dns_service.py` (200 lines)
- `templates/emails/agent_delivery.html` (email template)
- `tests/marketplace/test_delivery.py` (350 lines, 20 tests)

**Estimated Effort**: 4 days  
**Dependencies**: Story 3.2, Story 3.3

---

## End of Chunk 1

**Total Epic 1-3 Summary**:
- **3 Epics**: Template System, Factory Engine, Marketplace Integration
- **13 Stories**: Detailed breakdown with acceptance criteria
- **Estimated Duration**: 7 weeks
- **Total Lines of Code**: ~8,500 lines
- **Total Tests**: ~3,500 lines, ~250 tests
- **Note**: Customer-facing templates (14) included for reference/demonstration only

**Next Chunk**: Agent Factory Path (Epics 4-6) covering:
- Epic 4: Agent Monitoring & Management
- Epic 5: Agent Evolution & Versioning  
- Epic 6: Factory Performance & Scale

---

**Document Status**: Chunk 1 Complete ✅  
**Next**: Create Chunk 2 with command: "create chunk 2"
