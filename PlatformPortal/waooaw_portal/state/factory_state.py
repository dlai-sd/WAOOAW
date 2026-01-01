"""
Factory State

Manages agent factory wizard state and deployment.
"""

import reflex as rx
from datetime import datetime
from typing import List, Optional, Dict, Any


class AgentTemplate(rx.Base):
    """Agent template definition"""
    template_id: str
    name: str
    description: str
    category: str  # memory, orchestration, api, data, monitoring, custom
    icon: str
    complexity: str  # low, medium, high
    estimated_time: str
    default_config: Dict[str, Any]
    required_capabilities: List[str]
    optional_capabilities: List[str]
    dependencies: List[str]
    resource_requirements: Dict[str, Any]


class SandboxLog(rx.Base):
    """Sandbox test log entry"""
    timestamp: str
    level: str  # info, success, warning, error
    message: str


class DeploymentStep(rx.Base):
    """Deployment progress step"""
    step_name: str
    status: str  # pending, running, completed, failed
    message: str
    timestamp: Optional[str] = None


class FactoryState(rx.State):
    """State management for agent factory"""
    
    # Wizard state
    current_step: int = 0  # 0-5 (6 steps total)
    templates: List[AgentTemplate] = []
    selected_template: Optional[AgentTemplate] = None
    
    # Configuration
    agent_name: str = ""
    agent_description: str = ""
    agent_tier: str = "Professional"  # Starter, Professional, Enterprise
    selected_capabilities: List[str] = []
    custom_capabilities: str = ""
    industry: str = ""
    specialization: str = ""
    cpu_cores: float = 1.0
    memory_gb: int = 2
    storage_gb: int = 10
    environment_vars: str = ""  # JSON string of key-value pairs
    dependencies_list: str = ""  # Comma-separated
    rate_limit: int = 100
    
    # Validation
    validation_errors: List[str] = []
    config_valid: bool = False
    
    # Sandbox
    sandbox_active: bool = False
    sandbox_logs: List[SandboxLog] = []
    sandbox_status: str = "idle"  # idle, running, passed, failed
    
    # Deployment
    deployment_status: str = "idle"  # idle, provisioning, deploying, success, failed
    deployment_progress: int = 0
    deployment_steps: List[DeploymentStep] = []
    deployed_agent_id: str = ""
    
    # Cost estimation
    estimated_monthly_cost: float = 0.0
    cost_breakdown: Dict[str, float] = {}
    
    def load_templates(self):
        """Load agent templates"""
        self.templates = [
            AgentTemplate(
                template_id="tmpl-memory",
                name="Memory Agent",
                description="Agent with short-term and long-term memory capabilities for knowledge retention and context management",
                category="memory",
                icon="🧠",
                complexity="medium",
                estimated_time="10 min",
                default_config={
                    "memory_type": "hybrid",
                    "retention_days": 30,
                    "max_context_size": 10000
                },
                required_capabilities=["memory_storage", "context_retrieval"],
                optional_capabilities=["semantic_search", "summarization", "knowledge_graph"],
                dependencies=["redis", "postgresql"],
                resource_requirements={
                    "cpu_cores": 1.0,
                    "memory_gb": 2,
                    "storage_gb": 10
                }
            ),
            AgentTemplate(
                template_id="tmpl-orchestration",
                name="Orchestration Agent",
                description="Multi-step workflow orchestration with task dependencies, parallel execution, and error handling",
                category="orchestration",
                icon="🎭",
                complexity="high",
                estimated_time="15 min",
                default_config={
                    "max_parallel_tasks": 5,
                    "retry_strategy": "exponential",
                    "timeout_seconds": 300
                },
                required_capabilities=["workflow_engine", "task_scheduling", "dependency_resolution"],
                optional_capabilities=["parallel_execution", "conditional_branching", "rollback"],
                dependencies=["celery", "redis", "postgresql"],
                resource_requirements={
                    "cpu_cores": 2.0,
                    "memory_gb": 4,
                    "storage_gb": 5
                }
            ),
            AgentTemplate(
                template_id="tmpl-api",
                name="API Integration Agent",
                description="External API integration with authentication, rate limiting, retry logic, and response caching",
                category="api",
                icon="🔌",
                complexity="low",
                estimated_time="5 min",
                default_config={
                    "auth_type": "oauth2",
                    "rate_limit_per_min": 60,
                    "cache_ttl_seconds": 300
                },
                required_capabilities=["http_client", "authentication", "rate_limiting"],
                optional_capabilities=["caching", "retry_logic", "circuit_breaker", "webhook_handler"],
                dependencies=["httpx", "redis"],
                resource_requirements={
                    "cpu_cores": 0.5,
                    "memory_gb": 1,
                    "storage_gb": 1
                }
            ),
            AgentTemplate(
                template_id="tmpl-data",
                name="Data Processing Agent",
                description="ETL pipelines with data validation, transformation, enrichment, and batch processing capabilities",
                category="data",
                icon="📊",
                complexity="medium",
                estimated_time="10 min",
                default_config={
                    "batch_size": 1000,
                    "validation_strict": True,
                    "error_threshold": 0.01
                },
                required_capabilities=["data_validation", "transformation", "batch_processing"],
                optional_capabilities=["enrichment", "deduplication", "compression", "encryption"],
                dependencies=["pandas", "redis", "postgresql"],
                resource_requirements={
                    "cpu_cores": 2.0,
                    "memory_gb": 4,
                    "storage_gb": 20
                }
            ),
            AgentTemplate(
                template_id="tmpl-monitoring",
                name="Monitoring Agent",
                description="System health checks, performance monitoring, alerting, and automated diagnostics",
                category="monitoring",
                icon="📡",
                complexity="low",
                estimated_time="5 min",
                default_config={
                    "check_interval_seconds": 60,
                    "alert_threshold": 0.8,
                    "auto_remediate": False
                },
                required_capabilities=["health_checks", "metrics_collection", "alerting"],
                optional_capabilities=["auto_remediation", "predictive_alerts", "log_analysis"],
                dependencies=["prometheus_client", "redis"],
                resource_requirements={
                    "cpu_cores": 0.5,
                    "memory_gb": 1,
                    "storage_gb": 5
                }
            ),
            AgentTemplate(
                template_id="tmpl-blank",
                name="Blank Agent",
                description="Start from scratch with no pre-configured capabilities. Full customization available.",
                category="custom",
                icon="📝",
                complexity="high",
                estimated_time="20 min",
                default_config={},
                required_capabilities=[],
                optional_capabilities=["custom_logic", "event_handlers", "state_management"],
                dependencies=[],
                resource_requirements={
                    "cpu_cores": 1.0,
                    "memory_gb": 2,
                    "storage_gb": 5
                }
            ),
        ]
    
    def select_template(self, template_id: str):
        """Select a template and apply defaults"""
        self.selected_template = next(
            (t for t in self.templates if t.template_id == template_id),
            None
        )
        if self.selected_template:
            # Apply template defaults
            self.selected_capabilities = self.selected_template.required_capabilities.copy()
            self.cpu_cores = self.selected_template.resource_requirements["cpu_cores"]
            self.memory_gb = self.selected_template.resource_requirements["memory_gb"]
            self.storage_gb = self.selected_template.resource_requirements["storage_gb"]
            self.dependencies_list = ", ".join(self.selected_template.dependencies)
            # Move to config step
            self.current_step = 1
    
    def next_step(self):
        """Move to next wizard step"""
        if self.current_step < 5:
            self.current_step += 1
    
    def previous_step(self):
        """Move to previous wizard step"""
        if self.current_step > 0:
            self.current_step -= 1
    
    def update_agent_name(self, value: str):
        """Update agent name"""
        self.agent_name = value
        self.validate_config()
    
    def update_agent_description(self, value: str):
        """Update agent description"""
        self.agent_description = value
    
    def update_agent_tier(self, value: str):
        """Update agent tier"""
        self.agent_tier = value
        self.calculate_cost_estimate()
    
    def toggle_capability(self, capability: str):
        """Toggle capability selection"""
        if capability in self.selected_capabilities:
            self.selected_capabilities.remove(capability)
        else:
            self.selected_capabilities.append(capability)
    
    def validate_config(self):
        """Validate agent configuration"""
        errors = []
        
        # Validate name
        if not self.agent_name:
            errors.append("Agent name is required")
        elif len(self.agent_name) < 3:
            errors.append("Agent name must be at least 3 characters")
        elif not self.agent_name.replace("-", "").replace("_", "").isalnum():
            errors.append("Agent name must be alphanumeric")
        
        # Validate description
        if self.agent_description and len(self.agent_description) > 200:
            errors.append("Description must be less than 200 characters")
        
        # Validate capabilities
        if not self.selected_capabilities and self.selected_template and self.selected_template.required_capabilities:
            errors.append("At least one capability must be selected")
        
        self.validation_errors = errors
        self.config_valid = len(errors) == 0
    
    def start_sandbox_test(self):
        """Start sandbox testing"""
        self.sandbox_active = True
        self.sandbox_status = "running"
        self.sandbox_logs = [
            SandboxLog(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                level="info",
                message="Initializing sandbox environment..."
            ),
            SandboxLog(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                level="info",
                message=f"Loading {self.agent_name} configuration..."
            ),
            SandboxLog(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                level="success",
                message="Sandbox environment ready"
            ),
            SandboxLog(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                level="info",
                message="Running test task: Hello World"
            ),
            SandboxLog(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                level="success",
                message="✓ Task completed successfully (42ms)"
            ),
            SandboxLog(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                level="info",
                message=f"Memory usage: {self.memory_gb}GB / CPU: {self.cpu_cores} cores"
            ),
            SandboxLog(
                timestamp=datetime.now().strftime("%H:%M:%S"),
                level="success",
                message="All tests passed ✓"
            ),
        ]
        self.sandbox_status = "passed"
    
    def calculate_cost_estimate(self):
        """Calculate estimated monthly cost"""
        # Cost rates (mock)
        cpu_rate = 10.0  # $/core/month
        memory_rate = 5.0  # $/GB/month
        storage_rate = 0.10  # $/GB/month
        
        # Tier multipliers
        tier_multipliers = {
            "Starter": 0.5,
            "Professional": 1.0,
            "Enterprise": 1.5
        }
        multiplier = tier_multipliers.get(self.agent_tier, 1.0)
        
        # Calculate costs
        cpu_cost = self.cpu_cores * cpu_rate * multiplier
        memory_cost = self.memory_gb * memory_rate * multiplier
        storage_cost = self.storage_gb * storage_rate
        
        self.cost_breakdown = {
            "Compute (CPU)": cpu_cost,
            "Memory": memory_cost,
            "Storage": storage_cost,
            "Network": 1.0  # Flat rate
        }
        self.estimated_monthly_cost = sum(self.cost_breakdown.values())
    
    def deploy_agent(self):
        """Deploy the agent"""
        self.deployment_status = "provisioning"
        self.deployment_progress = 0
        self.deployed_agent_id = f"agent-{self.agent_name.lower().replace(' ', '-')}"
        
        # Simulate deployment steps
        self.deployment_steps = [
            DeploymentStep(
                step_name="Creating Docker container",
                status="completed",
                message="Container created successfully",
                timestamp=datetime.now().strftime("%H:%M:%S")
            ),
            DeploymentStep(
                step_name="Setting up message queue",
                status="completed",
                message="Queue configured and ready",
                timestamp=datetime.now().strftime("%H:%M:%S")
            ),
            DeploymentStep(
                step_name="Allocating storage",
                status="completed",
                message=f"{self.storage_gb}GB allocated",
                timestamp=datetime.now().strftime("%H:%M:%S")
            ),
            DeploymentStep(
                step_name="Configuring monitoring",
                status="running",
                message="Setting up health checks...",
                timestamp=datetime.now().strftime("%H:%M:%S")
            ),
            DeploymentStep(
                step_name="Deploying agent",
                status="pending",
                message="Waiting for deployment...",
                timestamp=None
            ),
        ]
        self.deployment_progress = 60
        # In real implementation, this would be async with WebSocket updates
    
    def complete_deployment(self):
        """Complete deployment (simulated)"""
        self.deployment_status = "success"
        self.deployment_progress = 100
        for step in self.deployment_steps:
            step.status = "completed"
        self.deployment_steps[-1].message = "Agent deployed and operational ✓"
        self.deployment_steps[-1].timestamp = datetime.now().strftime("%H:%M:%S")
    
    def reset_wizard(self):
        """Reset wizard to start"""
        self.current_step = 0
        self.selected_template = None
        self.agent_name = ""
        self.agent_description = ""
        self.agent_tier = "Professional"
        self.selected_capabilities = []
        self.custom_capabilities = ""
        self.industry = ""
        self.specialization = ""
        self.validation_errors = []
        self.config_valid = False
        self.sandbox_active = False
        self.sandbox_logs = []
        self.sandbox_status = "idle"
        self.deployment_status = "idle"
        self.deployment_progress = 0
        self.deployment_steps = []
        self.deployed_agent_id = ""
    
    @rx.var
    def step_titles(self) -> List[str]:
        """Get wizard step titles"""
        return [
            "Choose Template",
            "Configure Agent",
            "Test in Sandbox",
            "Provision Infrastructure",
            "Review & Deploy",
            "Monitor Deployment"
        ]
    
    @rx.var
    def current_step_title(self) -> str:
        """Get current step title"""
        titles = self.step_titles
        if 0 <= self.current_step < len(titles):
            return titles[self.current_step]
        return ""
    
    @rx.var
    def can_proceed(self) -> bool:
        """Check if can proceed to next step"""
        if self.current_step == 0:
            return self.selected_template is not None
        elif self.current_step == 1:
            return self.config_valid
        elif self.current_step == 2:
            return self.sandbox_status == "passed"
        elif self.current_step == 3:
            return True
        elif self.current_step == 4:
            return True
        return False
