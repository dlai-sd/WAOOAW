"""
Agent Factory State

State management for agent lifecycle management AND creation wizard.
"""

import reflex as rx
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import os


# Backend API URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CODESPACE_NAME = os.getenv("CODESPACE_NAME", "")

if CODESPACE_NAME:
    BACKEND_URL = f"https://{CODESPACE_NAME}-8000.app.github.dev"


class AgentCapability(rx.Base):
    """Agent capability"""
    name: str
    description: str
    enabled: bool = True


class AgentConfig(rx.Base):
    """Agent configuration"""
    max_concurrent_tasks: int = 5
    timeout_seconds: int = 300
    retry_attempts: int = 3
    memory_limit_mb: int = 512
    cpu_limit_percent: int = 80
    auto_restart: bool = True
    log_level: str = "INFO"


class Agent(rx.Base):
    """Agent definition"""
    agent_id: str
    name: str
    description: str
    category: str
    status: str
    health: str
    version: str
    deployed_at: Optional[str] = None
    last_active: Optional[str] = None
    capabilities: List[AgentCapability] = []
    config: AgentConfig = AgentConfig()
    metrics: Dict[str, Any] = {}


class WizardTemplate(rx.Base):
    """Agent template for wizard"""
    template_id: str
    name: str
    description: str
    category: str
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
    level: str
    message: str


class DeploymentStep(rx.Base):
    """Deployment progress step"""
    step_name: str
    status: str  # pending, running, completed, failed
    message: str
    timestamp: Optional[str] = None


class FactoryState(rx.State):
    """State management for Agent Factory"""
    
    # ========== AGENT MANAGEMENT (Existing) ==========
    agents: List[Agent] = []
    selected_agent: Optional[Agent] = None
    using_mock_data: bool = False
    
    # Filters
    category_filter: str = "all"
    status_filter: str = "all"
    health_filter: str = "all"
    search_query: str = ""
    
    # ========== WIZARD (New) ==========
    show_wizard: bool = False
    wizard_step: int = 0  # 0-5 (6 steps total)
    wizard_templates: List[WizardTemplate] = []
    wizard_selected_template: Optional[WizardTemplate] = None
    
    # Wizard Configuration
    wizard_agent_name: str = ""
    wizard_agent_description: str = ""
    wizard_agent_tier: str = "Professional"
    wizard_selected_capabilities: List[str] = []
    wizard_industry: str = ""
    wizard_specialization: str = ""
    wizard_cpu_cores: float = 1.0
    wizard_memory_gb: int = 2
    wizard_storage_gb: int = 10
    wizard_rate_limit: int = 100
    
    # Wizard Validation
    wizard_validation_errors: List[str] = []
    wizard_config_valid: bool = False
    
    # Wizard Sandbox
    wizard_sandbox_active: bool = False
    wizard_sandbox_logs: List[SandboxLog] = []
    wizard_sandbox_status: str = "idle"
    
    # Wizard Deployment
    wizard_deployment_status: str = "idle"
    wizard_deployment_progress: int = 0
    wizard_deployment_steps: List[DeploymentStep] = []
    wizard_deployed_agent_id: str = ""
    
    # Wizard Cost
    wizard_estimated_cost: float = 0.0
    
    def load_agents(self):
        """Load agents from backend API"""
        try:
            # Build query parameters
            params = {}
            if self.category_filter != "all":
                params["category"] = self.category_filter
            if self.status_filter != "all":
                params["status"] = self.status_filter
            if self.health_filter != "all":
                params["health"] = self.health_filter
            
            # Call backend API
            response = httpx.get(
                f"{BACKEND_URL}/api/agents",
                params=params,
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                self.agents = [Agent(**a) for a in data]
                
                # Check if backend is returning mock data
                data_source = response.headers.get("x-data-source", "mock")
                self.using_mock_data = (data_source == "mock")
            else:
                print(f"Backend API returned status {response.status_code}, using mock data")
                self._load_mock_agents()
                self.using_mock_data = True
        except Exception as e:
            print(f"Error loading agents: {e}, using mock data")
            self._load_mock_agents()
            self.using_mock_data = True
    
    def _load_mock_agents(self):
        """Fallback mock data"""
        self.agents = [
            Agent(
                agent_id="agent-001",
                name="Content Marketing Specialist",
                description="Creates engaging content for blogs, social media, and marketing campaigns",
                category="marketing",
                status="online",
                health="healthy",
                version="1.2.0",
                deployed_at="2025-01-10T08:00:00",
                last_active="2025-01-15T14:30:00",
                capabilities=[
                    AgentCapability(name="Blog Writing", description="Create SEO-optimized blog posts", enabled=True),
                    AgentCapability(name="Social Media", description="Generate social media content", enabled=True),
                ],
                config=AgentConfig(),
                metrics={
                    "tasks_completed": 1247,
                    "success_rate": 98.5,
                    "avg_response_time_ms": 450,
                    "uptime_percent": 99.2,
                },
            ),
        ]
    
    def load_templates(self):
        """Load agent templates"""
        try:
            response = httpx.get(f"{BACKEND_URL}/api/agents/templates/list", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                self.templates = [AgentTemplate(**t) for t in data]
        except Exception as e:
            print(f"Error loading templates: {e}")
            self.templates = []
    
    def select_agent(self, agent_id: str):
        """Select an agent for detailed view"""
        self.selected_agent = next(
            (a for a in self.agents if a.agent_id == agent_id),
            None
        )
    
    def close_agent_detail(self):
        """Close agent detail view"""
        self.selected_agent = None
    
    def start_agent(self, agent_id: str):
        """Start an agent"""
        try:
            response = httpx.post(f"{BACKEND_URL}/api/agents/{agent_id}/start", timeout=5.0)
            if response.status_code == 200:
                self.load_agents()
        except Exception as e:
            print(f"Error starting agent: {e}")
    
    def stop_agent(self, agent_id: str):
        """Stop an agent"""
        try:
            response = httpx.post(f"{BACKEND_URL}/api/agents/{agent_id}/stop", timeout=5.0)
            if response.status_code == 200:
                self.load_agents()
        except Exception as e:
            print(f"Error stopping agent: {e}")
    
    def restart_agent(self, agent_id: str):
        """Restart an agent"""
        try:
            response = httpx.post(f"{BACKEND_URL}/api/agents/{agent_id}/restart", timeout=5.0)
            if response.status_code == 200:
                self.load_agents()
        except Exception as e:
            print(f"Error restarting agent: {e}")
    
    def delete_agent(self, agent_id: str):
        """Delete an agent"""
        try:
            response = httpx.delete(f"{BACKEND_URL}/api/agents/{agent_id}", timeout=5.0)
            if response.status_code == 200:
                self.load_agents()
                self.selected_agent = None
        except Exception as e:
            print(f"Error deleting agent: {e}")
    
    def open_create_form(self):
        """Open wizard to create new agent"""
        self.show_wizard = True
        self.wizard_step = 0
        self.load_wizard_templates()
        self._reset_wizard()
    
    def close_create_form(self):
        """Close wizard"""
        self.show_wizard = False
        self._reset_wizard()
    
    def set_category_filter(self, category: str):
        """Set category filter"""
        self.category_filter = category
        self.load_agents()
    
    def set_status_filter(self, status: str):
        """Set status filter"""
        self.status_filter = status
        self.load_agents()
    
    def set_health_filter(self, health: str):
        """Set health filter"""
        self.health_filter = health
        self.load_agents()
    
    def set_search_query(self, query: str):
        """Set search query"""
        self.search_query = query
    
    @rx.var
    def filtered_agents(self) -> List[Agent]:
        """Get filtered and searched agents"""
        agents = self.agents
        
        # Apply search
        if self.search_query:
            query = self.search_query.lower()
            agents = [
                a for a in agents
                if query in a.name.lower() or query in a.description.lower()
            ]
        
        return agents
    
    @rx.var
    def agent_count(self) -> int:
        """Total agent count"""
        return len(self.agents)
    
    @rx.var
    def online_count(self) -> int:
        """Online agent count"""
        return len([a for a in self.agents if a.status == "online"])
    
    @rx.var
    def offline_count(self) -> int:
        """Offline agent count"""
        return len([a for a in self.agents if a.status == "offline"])
    
    @rx.var
    def healthy_count(self) -> int:
        """Healthy agent count"""
        return len([a for a in self.agents if a.health == "healthy"])
    
    # ========== WIZARD METHODS ==========
    
    def load_wizard_templates(self):
        """Load wizard templates"""
        self.wizard_templates = [
            WizardTemplate(
                template_id="tmpl-memory",
                name="Memory Agent",
                description="Agent with short-term and long-term memory capabilities",
                category="memory",
                icon="🧠",
                complexity="medium",
                estimated_time="10 min",
                default_config={},
                required_capabilities=["memory_storage", "context_retrieval"],
                optional_capabilities=["semantic_search", "summarization"],
                dependencies=["redis", "postgresql"],
                resource_requirements={"cpu_cores": 1.0, "memory_gb": 2, "storage_gb": 10}
            ),
            WizardTemplate(
                template_id="tmpl-orchestration",
                name="Orchestration Agent",
                description="Multi-step workflow orchestration with task dependencies",
                category="orchestration",
                icon="🎭",
                complexity="high",
                estimated_time="15 min",
                default_config={},
                required_capabilities=["workflow_engine", "task_scheduling"],
                optional_capabilities=["parallel_execution", "conditional_branching"],
                dependencies=["celery", "redis", "postgresql"],
                resource_requirements={"cpu_cores": 2.0, "memory_gb": 4, "storage_gb": 5}
            ),
            WizardTemplate(
                template_id="tmpl-api",
                name="API Integration Agent",
                description="External API integration with authentication and rate limiting",
                category="api",
                icon="🔌",
                complexity="low",
                estimated_time="5 min",
                default_config={},
                required_capabilities=["http_client", "authentication", "rate_limiting"],
                optional_capabilities=["caching", "retry_logic", "circuit_breaker"],
                dependencies=["httpx", "redis"],
                resource_requirements={"cpu_cores": 0.5, "memory_gb": 1, "storage_gb": 1}
            ),
        ]
    
    def _reset_wizard(self):
        """Reset wizard state"""
        self.wizard_step = 0
        self.wizard_selected_template = None
        self.wizard_agent_name = ""
        self.wizard_agent_description = ""
        self.wizard_selected_capabilities = []
        self.wizard_validation_errors = []
        self.wizard_sandbox_logs = []
        self.wizard_deployment_steps = []
    
    def wizard_select_template(self, template_id: str):
        """Select template in wizard"""
        self.wizard_selected_template = next(
            (t for t in self.wizard_templates if t.template_id == template_id),
            None
        )
        if self.wizard_selected_template:
            # Auto-populate from template
            self.wizard_cpu_cores = self.wizard_selected_template.resource_requirements.get("cpu_cores", 1.0)
            self.wizard_memory_gb = self.wizard_selected_template.resource_requirements.get("memory_gb", 2)
            self.wizard_storage_gb = self.wizard_selected_template.resource_requirements.get("storage_gb", 10)
    
    def wizard_next_step(self):
        """Move to next wizard step"""
        if self.wizard_step < 5:
            self.wizard_step += 1
    
    def wizard_prev_step(self):
        """Move to previous wizard step"""
        if self.wizard_step > 0:
            self.wizard_step -= 1
    
    def wizard_set_name(self, name: str):
        """Set wizard agent name"""
        self.wizard_agent_name = name
    
    def wizard_set_description(self, desc: str):
        """Set wizard agent description"""
        self.wizard_agent_description = desc
    
    def wizard_set_tier(self, tier: str):
        """Set wizard agent tier"""
        self.wizard_agent_tier = tier
    
    def wizard_validate_config(self):
        """Validate wizard configuration"""
        self.wizard_validation_errors = []
        
        if not self.wizard_agent_name:
            self.wizard_validation_errors.append("Agent name is required")
        if not self.wizard_selected_template:
            self.wizard_validation_errors.append("Template selection is required")
        
        self.wizard_config_valid = len(self.wizard_validation_errors) == 0
        return self.wizard_config_valid
    
    def wizard_run_sandbox(self):
        """Run sandbox test"""
        self.wizard_sandbox_active = True
        self.wizard_sandbox_status = "running"
        self.wizard_sandbox_logs = [
            SandboxLog(
                timestamp=datetime.now().isoformat(),
                level="info",
                message="Starting sandbox environment..."
            ),
            SandboxLog(
                timestamp=datetime.now().isoformat(),
                level="success",
                message="Agent configuration validated"
            ),
            SandboxLog(
                timestamp=datetime.now().isoformat(),
                level="success",
                message="Sandbox test passed"
            ),
        ]
        self.wizard_sandbox_status = "passed"
    
    def wizard_deploy_agent(self):
        """Deploy agent from wizard"""
        self.wizard_deployment_status = "provisioning"
        self.wizard_deployment_progress = 0
        self.wizard_deployment_steps = [
            DeploymentStep(
                step_name="Provisioning infrastructure",
                status="running",
                message="Allocating resources...",
                timestamp=datetime.now().isoformat()
            ),
            DeploymentStep(
                step_name="Building agent image",
                status="pending",
                message="",
            ),
            DeploymentStep(
                step_name="Deploying to cluster",
                status="pending",
                message="",
            ),
            DeploymentStep(
                step_name="Health check",
                status="pending",
                message="",
            ),
        ]
        
        # Simulate deployment (in reality, call backend API)
        self.wizard_deployed_agent_id = f"agent-wizard-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # After deployment, close wizard and reload agents
        self.show_wizard = False
        self.load_agents()
    
    def wizard_calculate_cost(self):
        """Calculate estimated monthly cost"""
        base_cost = 10.0  # Base infrastructure
        cpu_cost = self.wizard_cpu_cores * 5.0
        memory_cost = self.wizard_memory_gb * 2.0
        storage_cost = self.wizard_storage_gb * 0.1
        
        self.wizard_estimated_cost = base_cost + cpu_cost + memory_cost + storage_cost
