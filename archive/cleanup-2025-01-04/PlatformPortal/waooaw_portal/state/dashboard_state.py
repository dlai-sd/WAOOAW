"""
Dashboard State Management
"""

import reflex as rx
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx


class DashboardState(rx.State):
    """Dashboard state for platform metrics"""

    backend_url: str = "http://localhost:8000"

    # Metrics
    total_agents: int = 0
    active_tasks: int = 0
    error_rate: float = 0.0
    requests_per_minute: int = 0
    tasks_per_minute: int = 0
    p95_latency: float = 0.0
    queue_pending: int = 0
    
    # Trend indicators (for metrics widgets)
    agents_trend: str = "+2"
    tasks_trend: str = "0"
    queue_trend: str = "-5"
    error_trend: str = "-0.3%"
    
    # Agent status counts
    agents_running: int = 0
    agents_stopped: int = 0
    agents_errored: int = 0
    
    # Loading state
    is_loading: bool = False
    last_updated: str = "Never"
    using_mock_data: bool = False  # Track if backend is serving mock data

    async def load_metrics(self):
        """Load dashboard metrics from backend API"""
        self.is_loading = True
        
        try:
            await self._fetch_metrics()
            await self._fetch_agent_status()
            self.last_updated = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            print(f"Error loading metrics: {e}")
            self.total_agents = 2
            self.active_tasks = 1200
            self.error_rate = 2.0
        finally:
            self.is_loading = False

    async def _fetch_metrics(self):
        """Fetch platform metrics from backend API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/api/platform/metrics", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    self.total_agents = data.get("active_agents", 0)
                    self.requests_per_minute = data.get("requests_per_minute", 0)
                    self.tasks_per_minute = data.get("tasks_per_minute", 0)
                    self.active_tasks = self.tasks_per_minute
                    self.error_rate = round(data.get("error_rate", 0.0) * 100, 2)
                    self.p95_latency = data.get("p95_latency", 0.0)
                    
                    # Check if backend is returning mock or real data
                    data_source = response.headers.get("x-data-source", "mock")
                    self.using_mock_data = (data_source == "mock")
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            self.using_mock_data = True
            raise

    async def _fetch_agent_status(self):
        """Fetch agent status counts from backend API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/api/platform/agents", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    agents = data.get("agents", [])
                    if agents:
                        self.total_agents = len(agents)
                        self.agents_running = sum(1 for a in agents if a.get("portal_status") == "online")
                        self.agents_stopped = sum(1 for a in agents if a.get("portal_status") == "offline")
                        self.agents_errored = sum(1 for a in agents if a.get("portal_status") == "error")
        except Exception as e:
            print(f"Error fetching agent status: {e}")

    async def refresh_metrics(self):
        """Refresh all metrics"""
        await self.load_metrics()
    
    async def on_load(self):
        """Auto-load metrics when page loads"""
        await self.load_metrics()

    @rx.var
    def agents_health_status(self) -> str:
        """Get overall agent health status"""
        if self.agents_errored > 0:
            return "error"
        elif self.agents_stopped > 5:
            return "warning"
        return "success"

    @rx.var
    def agents_health_label(self) -> str:
        """Get health status label"""
        if self.agents_health_status == "error":
            return "Critical"
        elif self.agents_health_status == "warning":
            return "Degraded"
        return "Healthy"

    @rx.var
    def system_uptime_percentage(self) -> float:
        """Calculate system uptime percentage"""
        total = self.agents_running + self.agents_stopped + self.agents_errored
        if total == 0:
            return 100.0
        return round((self.agents_running / total) * 100, 1)
