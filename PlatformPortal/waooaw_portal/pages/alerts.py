"""
Alerts Page

Alert management with acknowledge and resolve actions.
"""

import reflex as rx
from typing import List, Optional
from datetime import datetime
from waooaw_portal.state.context_state import ContextState


class Alert(rx.Base):
    """Alert model"""
    
    alert_id: str
    timestamp: str
    severity: str  # critical, warning, info
    agent_id: str
    agent_name: str
    title: str
    message: str
    status: str  # active, acknowledged, resolved
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None


class AlertsState(rx.State):
    """
    Alerts page state.
    
    Features:
    - View active alerts
    - Filter by severity
    - Filter by selected agents
    - Acknowledge alerts
    - Resolve alerts
    - Real-time updates via WebSocket
    """
    
    # Alerts
    alerts: List[Alert] = []
    
    # Filters
    severity_filter: str = "all"  # all, critical, warning, info
    status_filter: str = "active"  # all, active, acknowledged, resolved
    
    # UI state
    is_loading: bool = False
    selected_alert_id: Optional[str] = None
    show_resolve_modal: bool = False
    
    def load_alerts(self):
        """Load alerts"""
        self.is_loading = True
        
        # In production: API call GET /api/platform/alerts?agent_ids=...&status=...
        # For now, use mock data
        self.alerts = [
            Alert(
                alert_id="alert-1",
                timestamp="1 minute ago",
                severity="critical",
                agent_id="agent-4",
                agent_name="WowSDK",
                title="API Rate Limit Exceeded",
                message="429 responses detected. Automatic backoff initiated.",
                status="active",
            ),
            Alert(
                alert_id="alert-2",
                timestamp="5 minutes ago",
                severity="warning",
                agent_id="agent-3",
                agent_name="WowOrchestrator",
                title="Workflow Execution Delayed",
                message="Task execution delayed by 2.3s (within threshold but approaching limit).",
                status="acknowledged",
                acknowledged_by="operator@waooaw.com",
            ),
            Alert(
                alert_id="alert-3",
                timestamp="15 minutes ago",
                severity="info",
                agent_id="agent-1",
                agent_name="WowMemory",
                title="Cache Hit Rate Below Target",
                message="Cache hit rate: 94.2% (target: 95%). Consider cache warm-up.",
                status="resolved",
                resolved_by="operator@waooaw.com",
            ),
            Alert(
                alert_id="alert-4",
                timestamp="20 minutes ago",
                severity="warning",
                agent_id="agent-2",
                agent_name="WowQueue",
                title="Queue Depth Increasing",
                message="Queue depth: 1,523 messages (threshold: 1,500). Monitor closely.",
                status="active",
            ),
        ]
        
        self.is_loading = False
    
    def set_severity_filter(self, severity: str):
        """Set severity filter"""
        self.severity_filter = severity
    
    def set_status_filter(self, status: str):
        """Set status filter"""
        self.status_filter = status
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id and alert.status == "active":
                alert.status = "acknowledged"
                alert.acknowledged_by = "operator@waooaw.com"
                break
        
        # In production: API call POST /api/platform/alerts/{alert_id}/acknowledge
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.status = "resolved"
                alert.resolved_by = "operator@waooaw.com"
                break
        
        self.show_resolve_modal = False
        
        # In production: API call POST /api/platform/alerts/{alert_id}/resolve
    
    def open_resolve_modal(self, alert_id: str):
        """Open resolve confirmation modal"""
        self.selected_alert_id = alert_id
        self.show_resolve_modal = True
    
    def close_resolve_modal(self):
        """Close resolve modal"""
        self.selected_alert_id = None
        self.show_resolve_modal = False
    
    @rx.var
    def filtered_alerts(self) -> List[Alert]:
        """Get filtered alerts"""
        filtered = self.alerts
        
        # Apply context filter (by selected agents)
        context_state = self.get_state(ContextState)
        if context_state.filter_active and context_state.selected_agent_ids:
            filtered = [
                alert for alert in filtered 
                if alert.agent_id in context_state.selected_agent_ids
            ]
        
        # Apply severity filter
        if self.severity_filter != "all":
            filtered = [a for a in filtered if a.severity == self.severity_filter]
        
        # Apply status filter
        if self.status_filter != "all":
            filtered = [a for a in filtered if a.status == self.status_filter]
        
        return filtered
    
    @rx.var
    def alert_count(self) -> int:
        """Total alert count"""
        return len(self.alerts)
    
    @rx.var
    def active_count(self) -> int:
        """Active alert count"""
        return len([a for a in self.alerts if a.status == "active"])
    
    @rx.var
    def critical_count(self) -> int:
        """Critical alert count"""
        return len([a for a in self.alerts if a.severity == "critical" and a.status == "active"])


def get_severity_color(severity: str) -> str:
    """Get color for severity"""
    colors = {
        "critical": "#ef4444",  # Red
        "warning": "#f59e0b",   # Yellow
        "info": "#3b82f6",      # Blue
    }
    return colors.get(severity, "#6b7280")


def get_status_badge_color(status: str) -> str:
    """Get badge color for status"""
    colors = {
        "active": "red",
        "acknowledged": "yellow",
        "resolved": "green",
    }
    return colors.get(status, "gray")


def alert_card(alert: Alert) -> rx.Component:
    """Individual alert card"""
    severity_color = get_severity_color(alert.severity)
    status_color = get_status_badge_color(alert.status)
    
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                # Severity indicator
                rx.box(
                    width="4px",
                    height="3rem",
                    background=severity_color,
                    border_radius="2px",
                ),
                # Alert info
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            alert.title,
                            font_size="1.125rem",
                            font_weight="600",
                            color="white",
                        ),
                        rx.badge(
                            alert.severity.upper(),
                            color_scheme=status_color,
                            variant="solid",
                            background=severity_color,
                        ),
                        rx.badge(
                            alert.status.upper(),
                            color_scheme=status_color,
                            variant="outline",
                        ),
                        spacing="0.75rem",
                        align_items="center",
                    ),
                    rx.hstack(
                        rx.text(
                            alert.agent_name,
                            font_size="0.875rem",
                            color="#00f2fe",
                        ),
                        rx.text(
                            "•",
                            font_size="0.875rem",
                            color="#6b7280",
                        ),
                        rx.text(
                            alert.timestamp,
                            font_size="0.875rem",
                            color="#9ca3af",
                        ),
                        spacing="0.5rem",
                        align_items="center",
                    ),
                    align_items="flex-start",
                    spacing="0.5rem",
                    flex="1",
                ),
                spacing="1rem",
                align_items="flex-start",
                width="100%",
            ),
            # Message
            rx.text(
                alert.message,
                font_size="0.875rem",
                color="#d1d5db",
                margin_top="0.75rem",
                line_height="1.5",
            ),
            # Actions
            rx.cond(
                alert.status == "active",
                rx.hstack(
                    rx.button(
                        "Acknowledge",
                        size="sm",
                        color_scheme="yellow",
                        variant="outline",
                        on_click=lambda: AlertsState.acknowledge_alert(alert.alert_id),
                    ),
                    rx.button(
                        "Resolve",
                        size="sm",
                        color_scheme="green",
                        on_click=lambda: AlertsState.open_resolve_modal(alert.alert_id),
                    ),
                    spacing="0.5rem",
                    margin_top="1rem",
                ),
                rx.cond(
                    alert.status == "acknowledged",
                    rx.hstack(
                        rx.text(
                            f"Acknowledged by {alert.acknowledged_by}",
                            font_size="0.75rem",
                            color="#9ca3af",
                        ),
                        rx.button(
                            "Resolve",
                            size="sm",
                            color_scheme="green",
                            on_click=lambda: AlertsState.open_resolve_modal(alert.alert_id),
                        ),
                        spacing="1rem",
                        align_items="center",
                        margin_top="1rem",
                    ),
                    rx.text(
                        f"Resolved by {alert.resolved_by}",
                        font_size="0.75rem",
                        color="#10b981",
                        margin_top="1rem",
                    ),
                ),
            ),
            align_items="flex-start",
            spacing="0.5rem",
            width="100%",
        ),
        padding="1.5rem",
        background="#18181b",
        border="1px solid #27272a",
        border_radius="1rem",
        _hover={
            "border_color": severity_color,
            "box_shadow": f"0 0 20px {severity_color}33",
        },
        transition="all 0.3s ease",
    )


def filters_bar() -> rx.Component:
    """Filter controls"""
    return rx.hstack(
        # Severity filter
        rx.select(
            ["all", "critical", "warning", "info"],
            value=AlertsState.severity_filter,
            on_change=AlertsState.set_severity_filter,
            placeholder="All Severities",
        ),
        # Status filter
        rx.select(
            ["all", "active", "acknowledged", "resolved"],
            value=AlertsState.status_filter,
            on_change=AlertsState.set_status_filter,
            placeholder="All Statuses",
        ),
        # Stats
        rx.hstack(
            rx.badge(
                f"{AlertsState.critical_count} Critical",
                color_scheme="red",
                variant="solid",
            ),
            rx.badge(
                f"{AlertsState.active_count} Active",
                color_scheme="yellow",
                variant="outline",
            ),
            spacing="0.5rem",
        ),
        # Refresh button
        rx.button(
            "Refresh",
            on_click=AlertsState.load_alerts,
            size="sm",
            color_scheme="cyan",
            variant="outline",
        ),
        spacing="1rem",
        align_items="center",
        width="100%",
        padding="1rem",
        background="#18181b",
        border="1px solid #27272a",
        border_radius="0.75rem",
    )


def alerts_grid() -> rx.Component:
    """Grid of alert cards"""
    return rx.cond(
        len(AlertsState.filtered_alerts) > 0,
        rx.box(
            rx.foreach(
                AlertsState.filtered_alerts,
                alert_card,
            ),
            display="grid",
            grid_template_columns="1fr",
            gap="1.5rem",
            width="100%",
        ),
        # Empty state
        rx.box(
            rx.vstack(
                rx.text(
                    "✅",
                    font_size="4rem",
                ),
                rx.text(
                    "No alerts found",
                    font_size="1.5rem",
                    font_weight="600",
                    color="white",
                ),
                rx.text(
                    "All systems operational",
                    font_size="1rem",
                    color="#10b981",
                ),
                spacing="1rem",
                align_items="center",
            ),
            padding="4rem",
            text_align="center",
            border="1px solid #27272a",
            border_radius="1rem",
        ),
    )


def alerts_page() -> rx.Component:
    """
    Alerts page with filtering and actions.
    
    Features:
    - View all alerts
    - Filter by severity (critical, warning, info)
    - Filter by status (active, acknowledged, resolved)
    - Filter by selected agents (context filter)
    - Acknowledge alerts
    - Resolve alerts
    - Real-time updates via WebSocket
    """
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Alerts",
                        font_size="2rem",
                        font_weight="700",
                        color="white",
                    ),
                    rx.text(
                        f"{len(AlertsState.filtered_alerts)} alerts",
                        font_size="1rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.5rem",
                ),
                rx.spacer(),
                width="100%",
                align_items="center",
            ),
            # Filters
            filters_bar(),
            # Alerts grid
            alerts_grid(),
            spacing="2rem",
            width="100%",
            max_width="90rem",
            margin="0 auto",
            padding="2rem",
        ),
        width="100%",
        min_height="100vh",
        background="#0a0a0a",
        on_mount=AlertsState.load_alerts,
    )
