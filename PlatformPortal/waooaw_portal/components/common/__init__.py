"""Common components package."""

from .status_badge import (
    status_badge,
    status_badge_list,
    badge_online,
    badge_offline,
    badge_working,
    badge_unknown,
)

from .metrics_widget import (
    metrics_widget,
    metrics_widget_grid,
    metric_agents_online,
    metric_response_time,
    metric_success_rate,
    metric_requests_per_min,
)

from .websocket_manager import (
    websocket_manager,
    websocket_send,
    websocket_subscribe,
    websocket_unsubscribe,
    websocket_agent_updates,
    websocket_system_events,
    websocket_logs_stream,
    WebSocketState,
)

from .timeline_component import (
    timeline_component,
    timeline_agent_activity,
    timeline_audit_log,
    timeline_system_events,
    timeline_recent_changes,
)

from .progress_tracker import (
    progress_tracker,
    progress_agent_provisioning,
    progress_deployment_pipeline,
    progress_upgrade_workflow,
)

from .context_selector import (
    context_selector,
    context_selector_agents,
    context_selector_environment,
    context_selector_services,
    context_selector_time_range,
    ContextSelectorState,
)

__all__ = [
    # Status badge
    "status_badge",
    "status_badge_list",
    "badge_online",
    "badge_offline",
    "badge_working",
    "badge_unknown",
    # Metrics widget
    "metrics_widget",
    "metrics_widget_grid",
    "metric_agents_online",
    "metric_response_time",
    "metric_success_rate",
    "metric_requests_per_min",
    # WebSocket manager
    "websocket_manager",
    "websocket_send",
    "websocket_subscribe",
    "websocket_unsubscribe",
    "websocket_agent_updates",
    "websocket_system_events",
    "websocket_logs_stream",
    "WebSocketState",
    # Timeline component
    "timeline_component",
    "timeline_agent_activity",
    "timeline_audit_log",
    "timeline_system_events",
    "timeline_recent_changes",
    # Progress tracker
    "progress_tracker",
    "progress_agent_provisioning",
    "progress_deployment_pipeline",
    "progress_upgrade_workflow",
    # Context selector
    "context_selector",
    "context_selector_agents",
    "context_selector_environment",
    "context_selector_services",
    "context_selector_time_range",
    "ContextSelectorState",
]
