"""
Dashboard State Management

Manages dashboard metrics, real-time updates, and agent status.
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from datetime import datetime
import random


class DashboardState(rx.State):
    """
    Dashboard state for platform metrics and agent status.
    
    Features:
    - Real-time metrics updates
    - Agent status overview
    - Recent activity feed
    - Quick actions
    """

    # Metrics
    total_agents: int = 14
    active_tasks: int = 245
    queue_pending: int = 12
    error_rate: float = 0.2
    
    # Trends
    agents_trend: str = "↑ 12%"
    tasks_trend: str = "→ Stable"
    queue_trend: str = "↓ 8%"
    error_trend: str = "↓ 15%"
    
    # Agent status counts
    agents_running: int = 12
    agents_stopped: int = 2
    agents_errored: int = 0
    
    # Recent events
    recent_events: List[Dict[str, Any]] = []
    
    # Loading state
    is_loading: bool = False
    last_updated: Optional[datetime] = None

    def load_metrics(self):
        """Load dashboard metrics"""
        self.is_loading = True
        
        # Simulate loading (in production, this would be an API call)
        self._fetch_metrics()
        self._fetch_agent_status()
        self._fetch_recent_events()
        
        self.last_updated = datetime.now()
        self.is_loading = False

    def _fetch_metrics(self):
        """Fetch platform metrics"""
        # In production: API call to /api/platform/metrics
        # For now, use static/simulated data
        pass

    def _fetch_agent_status(self):
        """Fetch agent status counts"""
        # In production: API call to /api/platform/agents/status
        pass

    def _fetch_recent_events(self):
        """Fetch recent activity events"""
        # In production: API call to /api/platform/events/recent
        self.recent_events = [
            {
                "id": "evt-1",
                "action": "start",
                "user": "Platform Operator",
                "resource": "WowMemory Agent",
                "timestamp": "2 minutes ago",
                "status": "success"
            },
            {
                "id": "evt-2",
                "action": "update",
                "user": "System",
                "resource": "WowQueue Configuration",
                "timestamp": "5 minutes ago",
                "status": "success"
            },
            {
                "id": "evt-3",
                "action": "create",
                "user": "Platform Operator",
                "resource": "New Agent: WowAnalytics",
                "timestamp": "15 minutes ago",
                "status": "success"
            },
        ]

    def refresh_metrics(self):
        """Refresh all metrics"""
        self.load_metrics()

    @rx.var
    def agents_health_status(self) -> str:
        """Get overall agent health status"""
        if self.agents_errored > 0:
            return "error"
        elif self.agents_stopped > 5:
            return "warning"
        else:
            return "success"

    @rx.var
    def agents_health_label(self) -> str:
        """Get health status label"""
        if self.agents_health_status == "error":
            return "Critical"
        elif self.agents_health_status == "warning":
            return "Degraded"
        else:
            return "Healthy"

    @rx.var
    def system_uptime_percentage(self) -> float:
        """Calculate system uptime percentage"""
        total = self.agents_running + self.agents_stopped + self.agents_errored
        if total == 0:
            return 100.0
        return round((self.agents_running / total) * 100, 1)
