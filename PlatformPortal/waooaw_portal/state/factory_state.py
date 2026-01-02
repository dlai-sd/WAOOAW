"""
Agent Factory State

State management for agent lifecycle and deployment.
"""

import reflex as rx
from typing import List, Optional, Dict, Any
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


class AgentTemplate(rx.Base):
    """Agent template"""
    template_id: str
    name: str
    description: str
    category: str
    capabilities: List[str] = []
    default_config: AgentConfig = AgentConfig()


class FactoryState(rx.State):
    """State management for Agent Factory"""
    
    agents: List[Agent] = []
    selected_agent: Optional[Agent] = None
    templates: List[AgentTemplate] = []
    using_mock_data: bool = False
    
    # Filters
    category_filter: str = "all"
    status_filter: str = "all"
    health_filter: str = "all"
    search_query: str = ""
    
    # Create agent form
    show_create_form: bool = False
    selected_template: Optional[AgentTemplate] = None
    new_agent_name: str = ""
    new_agent_description: str = ""
    
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
        """Open create agent form"""
        self.show_create_form = True
        self.load_templates()
    
    def close_create_form(self):
        """Close create agent form"""
        self.show_create_form = False
        self.selected_template = None
        self.new_agent_name = ""
        self.new_agent_description = ""
    
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
