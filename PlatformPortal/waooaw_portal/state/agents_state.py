"""
Agent State Management

Manages agent data, state, and lifecycle operations.
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from datetime import datetime
from waooaw_portal.services.agent_state_machine import AgentState, AgentStateMachine


class AgentData(rx.Base):
    """Agent data model"""

    agent_id: str
    agent_name: str
    agent_type: str
    current_state: str
    tier: str
    description: str
    last_active: str
    health_score: float
    tasks_completed: int
    uptime_percentage: float


class AgentsState(rx.State):
    """
    Agent management state.

    Features:
    - Agent list with state machine
    - Lifecycle actions (start, stop, restart, etc.)
    - Real-time status updates
    - Agent filtering and search
    """
    
    # Class-level state machine (not serialized in state)
    _state_machine = AgentStateMachine()

    # Agent list
    agents: List[AgentData] = []
    
    # Selected agents (for bulk operations)
    selected_agent_ids: List[str] = []
    
    # Filters
    search_query: str = ""
    filter_state: str = "all"  # all, running, stopped, errored
    filter_tier: str = "all"  # all, platform, business, custom
    
    # UI state
    is_loading: bool = False
    selected_agent_for_action: Optional[str] = None
    show_action_modal: bool = False
    action_type: Optional[str] = None

    def load_agents(self):
        """Load all agents"""
        self.is_loading = True
        
        # In production: API call to /api/platform/agents
        # For now, use mock data
        self.agents = [
            AgentData(
                agent_id="agent-1",
                agent_name="WowMemory",
                agent_type="platform",
                current_state="running",
                tier="Platform CoE",
                description="Memory management and persistence",
                last_active="2 minutes ago",
                health_score=98.5,
                tasks_completed=1247,
                uptime_percentage=99.8,
            ),
            AgentData(
                agent_id="agent-2",
                agent_name="WowQueue",
                agent_type="platform",
                current_state="running",
                tier="Platform CoE",
                description="Message queue management",
                last_active="1 minute ago",
                health_score=99.2,
                tasks_completed=3521,
                uptime_percentage=99.9,
            ),
            AgentData(
                agent_id="agent-3",
                agent_name="WowOrchestrator",
                agent_type="platform",
                current_state="running",
                tier="Platform CoE",
                description="Workflow orchestration",
                last_active="5 minutes ago",
                health_score=97.8,
                tasks_completed=892,
                uptime_percentage=98.5,
            ),
            AgentData(
                agent_id="agent-4",
                agent_name="WowSDK",
                agent_type="business",
                current_state="stopped",
                tier="Business",
                description="SDK agent for custom integrations",
                last_active="2 hours ago",
                health_score=95.0,
                tasks_completed=456,
                uptime_percentage=96.2,
            ),
            AgentData(
                agent_id="agent-5",
                agent_name="WowAnalytics",
                agent_type="business",
                current_state="deployed",
                tier="Business",
                description="Analytics and reporting",
                last_active="10 minutes ago",
                health_score=88.0,
                tasks_completed=234,
                uptime_percentage=92.1,
            ),
        ]
        
        self.is_loading = False

    def toggle_agent_selection(self, agent_id: str):
        """Toggle agent selection for bulk operations"""
        if agent_id in self.selected_agent_ids:
            self.selected_agent_ids.remove(agent_id)
        else:
            self.selected_agent_ids.append(agent_id)

    def select_all_agents(self):
        """Select all filtered agents"""
        filtered = self.get_filtered_agents()
        self.selected_agent_ids = [a.agent_id for a in filtered]

    def deselect_all_agents(self):
        """Deselect all agents"""
        self.selected_agent_ids = []

    def set_search_query(self, query: str):
        """Update search query"""
        self.search_query = query

    def set_filter_state(self, state: str):
        """Update state filter"""
        self.filter_state = state

    def set_filter_tier(self, tier: str):
        """Update tier filter"""
        self.filter_tier = tier

    def get_filtered_agents(self) -> List[AgentData]:
        """Get filtered agent list"""
        filtered = self.agents

        # Apply search
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                a for a in filtered
                if query in a.agent_name.lower() or query in a.description.lower()
            ]

        # Apply state filter
        if self.filter_state != "all":
            filtered = [a for a in filtered if a.current_state == self.filter_state]

        # Apply tier filter
        if self.filter_tier != "all":
            filtered = [a for a in filtered if self.filter_tier.lower() in a.tier.lower()]

        return filtered

    def start_agent(self, agent_id: str):
        """Start an agent"""
        agent = next((a for a in self.agents if a.agent_id == agent_id), None)
        if not agent:
            return

        current_state = AgentState(agent.current_state)
        target_state = AgentState.RUNNING

        try:
            self._state_machine.transition(
                agent_id=agent_id,
                current=current_state,
                target=target_state,
                triggered_by="operator@waooaw.com",
                metadata={"action": "start", "timestamp": str(datetime.now())},
            )
            agent.current_state = target_state.value
            agent.last_active = "just now"
        except ValueError as e:
            # Invalid transition
            print(f"Cannot start agent: {e}")

    def stop_agent(self, agent_id: str):
        """Stop an agent"""
        agent = next((a for a in self.agents if a.agent_id == agent_id), None)
        if not agent:
            return

        current_state = AgentState(agent.current_state)
        target_state = AgentState.STOPPED

        try:
            self._state_machine.transition(
                agent_id=agent_id,
                current=current_state,
                target=target_state,
                triggered_by="operator@waooaw.com",
                metadata={"action": "stop", "timestamp": str(datetime.now())},
            )
            agent.current_state = target_state.value
        except ValueError as e:
            print(f"Cannot stop agent: {e}")

    def restart_agent(self, agent_id: str):
        """Restart an agent"""
        # Stop then start
        self.stop_agent(agent_id)
        self.start_agent(agent_id)

    def suspend_agent(self, agent_id: str):
        """Suspend an agent"""
        agent = next((a for a in self.agents if a.agent_id == agent_id), None)
        if not agent:
            return

        current_state = AgentState(agent.current_state)
        target_state = AgentState.SUSPENDED

        try:
            self._state_machine.transition(
                agent_id=agent_id,
                current=current_state,
                target=target_state,
                triggered_by="operator@waooaw.com",
                metadata={"action": "suspend", "timestamp": str(datetime.now())},
            )
            agent.current_state = target_state.value
        except ValueError as e:
            print(f"Cannot suspend agent: {e}")

    def open_action_modal(self, agent_id: str, action: str):
        """Open confirmation modal for action"""
        self.selected_agent_for_action = agent_id
        self.action_type = action
        self.show_action_modal = True

    def close_action_modal(self):
        """Close action modal"""
        self.selected_agent_for_action = None
        self.action_type = None
        self.show_action_modal = False

    def execute_bulk_action(self, action: str):
        """Execute action on all selected agents"""
        for agent_id in self.selected_agent_ids:
            if action == "start":
                self.start_agent(agent_id)
            elif action == "stop":
                self.stop_agent(agent_id)
            elif action == "restart":
                self.restart_agent(agent_id)

        self.deselect_all_agents()

    @rx.var
    def agent_count(self) -> int:
        """Total agent count"""
        return len(self.agents)

    @rx.var
    def running_count(self) -> int:
        """Count of running agents"""
        return len([a for a in self.agents if a.current_state == "running"])

    @rx.var
    def stopped_count(self) -> int:
        """Count of stopped agents"""
        return len([a for a in self.agents if a.current_state == "stopped"])

    @rx.var
    def errored_count(self) -> int:
        """Count of errored agents"""
        return len([a for a in self.agents if a.current_state == "errored"])

    @rx.var
    def filtered_count(self) -> int:
        """Count of filtered agents"""
        return len(self.get_filtered_agents())

    @rx.var
    def selected_count(self) -> int:
        """Count of selected agents"""
        return len(self.selected_agent_ids)
