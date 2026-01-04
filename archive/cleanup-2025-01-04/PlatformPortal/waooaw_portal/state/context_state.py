"""
Context State Management

Global agent/service context filtering across all portal pages.
"""

import reflex as rx
from typing import List, Set, Any, Dict, Optional


class ContextState(rx.State):
    """
    Global context filtering state.
    
    Manages selected agents for filtering across all pages:
    - Dashboard metrics
    - Logs
    - Alerts
    - Metrics
    - Events
    
    Features:
    - Multi-select agent filtering
    - Persistent across page navigation
    - localStorage integration (browser persistence)
    - Apply filter to any data list
    """
    
    # Selected agent IDs for filtering
    selected_agent_ids: Set[str] = set()
    
    # Filter active flag
    filter_active: bool = False
    
    # Available agents (loaded from agents_state)
    available_agents: List[str] = []
    
    def load_available_agents(self):
        """Load available agents from agents state"""
        # In production: Fetch from API or use AgentsState
        self.available_agents = [
            "agent-1",  # WowMemory
            "agent-2",  # WowQueue
            "agent-3",  # WowOrchestrator
            "agent-4",  # WowSDK
            "agent-5",  # WowAnalytics
        ]
    
    def set_selected_agents(self, agent_ids: Set[str]):
        """Set selected agent IDs and activate filter"""
        self.selected_agent_ids = agent_ids
        self.filter_active = len(agent_ids) > 0
        # In production: Save to localStorage
        # self._save_to_local_storage()
    
    def add_agent_to_filter(self, agent_id: str):
        """Add agent to filter"""
        new_set = self.selected_agent_ids.copy()
        new_set.add(agent_id)
        self.selected_agent_ids = new_set
        self.filter_active = True
    
    def remove_agent_from_filter(self, agent_id: str):
        """Remove agent from filter"""
        new_set = self.selected_agent_ids.copy()
        new_set.discard(agent_id)
        self.selected_agent_ids = new_set
        self.filter_active = len(new_set) > 0
    
    def clear_filter(self):
        """Clear all filters"""
        self.selected_agent_ids = set()
        self.filter_active = False
    
    def toggle_filter_active(self):
        """Toggle filter on/off (keeps selection)"""
        self.filter_active = not self.filter_active
    
    def apply_filter(self, data: List[Any], agent_id_field: str = "agent_id") -> List[Any]:
        """
        Apply context filter to data list.
        
        Args:
            data: List of objects with agent_id field
            agent_id_field: Name of the field containing agent_id
            
        Returns:
            Filtered list (all items if filter inactive or empty)
        """
        if not self.filter_active or not self.selected_agent_ids:
            return data
        
        filtered = []
        for item in data:
            # Handle both dict and object attribute access
            if isinstance(item, dict):
                item_agent_id = item.get(agent_id_field)
            else:
                item_agent_id = getattr(item, agent_id_field, None)
            
            if item_agent_id in self.selected_agent_ids:
                filtered.append(item)
        
        return filtered
    
    def filter_dict_list(self, data: List[Dict], agent_id_field: str = "agent_id") -> List[Dict]:
        """Apply filter to list of dictionaries"""
        return self.apply_filter(data, agent_id_field)
    
    def get_filter_query_params(self) -> str:
        """
        Get query params for API calls.
        
        Returns:
            Query string like "agent_ids=agent-1,agent-2"
        """
        if not self.filter_active or not self.selected_agent_ids:
            return ""
        
        agent_ids_str = ",".join(self.selected_agent_ids)
        return f"agent_ids={agent_ids_str}"
    
    @rx.var
    def selected_count(self) -> int:
        """Count of selected agents"""
        return len(self.selected_agent_ids)
    
    @rx.var
    def filter_summary(self) -> str:
        """Human-readable filter summary"""
        if not self.filter_active or not self.selected_agent_ids:
            return "All Agents"
        
        count = self.selected_count
        if count == 1:
            return list(self.selected_agent_ids)[0]
        else:
            return f"{count} agents selected"
    
    @rx.var
    def is_agent_selected(self) -> bool:
        """Check if any agent is selected"""
        return self.filter_active and len(self.selected_agent_ids) > 0
