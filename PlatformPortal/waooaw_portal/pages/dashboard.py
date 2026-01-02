"""
Dashboard Page

Main operations dashboard with metrics, agent status, and recent activity.
"""

import reflex as rx
from waooaw_portal.components.common import (
    metrics_widget,
    metric_agents_online,
    metric_response_time,
    metric_success_rate,
    metric_requests_per_min,
    timeline_component,
    timeline_agent_activity,
    status_badge,
)
from waooaw_portal.state.auth_state import AuthState
from waooaw_portal.state.dashboard_state import DashboardState
from waooaw_portal.state.theme_state import ThemeState


def metrics_grid() -> rx.Component:
    """Metrics cards grid"""
    return rx.grid(
        # Total Agents
        rx.card(
            rx.vstack(
                rx.text("Total Agents", size="2", color=ThemeState.theme["text_tertiary"]),
                rx.heading(DashboardState.total_agents, size="8"),
                rx.hstack(
                    rx.text("🟢", size="1"),
                    rx.text(DashboardState.agents_running, size="1", color=ThemeState.theme["status_success"]),
                    rx.text("online", size="1", color=ThemeState.theme["status_success"]),
                    rx.text("↑ +2", size="1", color=ThemeState.theme["status_success"], margin_left="0.5rem"),
                    spacing="1",
                ),
                align="center",
                spacing="2",
            )
        ),
        # Active Tasks
        rx.card(
            rx.vstack(
                rx.text("Active Tasks", size="2", color=ThemeState.theme["text_tertiary"]),
                rx.heading(DashboardState.active_tasks, size="8"),
                rx.hstack(
                    rx.text(DashboardState.requests_per_minute, size="1", color=ThemeState.theme["info"]),
                    rx.text("req/min", size="1", color=ThemeState.theme["info"]),
                    rx.text("→ Stable", size="1", color=ThemeState.theme["text_tertiary"], margin_left="0.5rem"),
                    spacing="1",
                ),
                align="center",
                spacing="2",
            )
        ),
        # Queue Pending
        rx.card(
            rx.vstack(
                rx.text("Queue Pending", size="2", color=ThemeState.theme["text_tertiary"]),
                rx.heading(DashboardState.queue_pending, size="8"),
                rx.hstack(
                    rx.text("P95:", size="1", color=ThemeState.theme["warning"]),
                    rx.text(DashboardState.p95_latency, size="1", color=ThemeState.theme["warning"]),
                    rx.text("ms", size="1", color=ThemeState.theme["warning"]),
                    rx.text("↓ -5", size="1", color=ThemeState.theme["status_success"], margin_left="0.5rem"),
                    spacing="1",
                ),
                align="center",
                spacing="2",
            )
        ),
        # Error Rate
        rx.card(
            rx.vstack(
                rx.text("Error Rate", size="2", color=ThemeState.theme["text_tertiary"]),
                rx.heading(f"{DashboardState.error_rate}%", size="8"),
                rx.hstack(
                    rx.text(DashboardState.agents_health_label, size="1", color=ThemeState.theme["status_success"]),
                    rx.text("↓ -0.3%", size="1", color=ThemeState.theme["status_success"], margin_left="0.5rem"),
                    spacing="1",
                ),
                align="center",
                spacing="2",
            )
        ),
        columns="4",
        spacing="4",
        width="100%",
    )


def agent_status_card() -> rx.Component:
    """Agent status overview card"""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Agent Status", size="6"),
                status_badge(
                    status=DashboardState.agents_health_label,
                    size="md",
                ),
                justify="between",
                width="100%",
                margin_bottom="1rem",
            ),
            # Status breakdown
            rx.hstack(
                # Running
                rx.vstack(
                    rx.text(
                        DashboardState.agents_running,
                        size="8",
                        font_weight="bold",
                        color=ThemeState.theme["status_success"],
                    ),
                    rx.text(
                        "Running",
                        size="2",
                        color=ThemeState.theme["text_secondary"],
                    ),
                    align="center",
                    spacing="1",
                ),
                # Stopped
                rx.vstack(
                    rx.text(
                        DashboardState.agents_stopped,
                        size="8",
                        font_weight="bold",
                        color=ThemeState.theme["text_secondary"],
                    ),
                    rx.text(
                        "Stopped",
                        size="2",
                        color=ThemeState.theme["text_secondary"],
                    ),
                    align="center",
                    spacing="1",
                ),
                # Errored
                rx.vstack(
                    rx.text(
                        DashboardState.agents_errored,
                        size="8",
                        font_weight="bold",
                        color=ThemeState.theme["status_error"],
                    ),
                    rx.text(
                        "Errored",
                        size="2",
                        color=ThemeState.theme["text_secondary"],
                    ),
                    align="center",
                    spacing="1",
                ),
                justify="between",
                width="100%",
            ),
            # Uptime percentage
            rx.separator(margin_y="1rem"),
            rx.hstack(
                rx.text("System Uptime:", size="2", color=ThemeState.theme["text_secondary"]),
                rx.text(
                    f"{DashboardState.system_uptime_percentage}%",
                    size="2",
                    font_weight="bold",
                    color=ThemeState.theme["accent_cyan"],
                ),
                justify="between",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        background=ThemeState.theme["bg_secondary"],
        border=f"1px solid {ThemeState.theme['bg_tertiary']}",
    )


def recent_activity_card() -> rx.Component:
    """Recent activity timeline"""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Recent Activity", size="6"),
                rx.button(
                    rx.icon("refresh_cw", size=16),
                    size="1",
                    variant="ghost",
                    on_click=DashboardState.refresh_metrics,
                ),
                justify="between",
                width="100%",
                margin_bottom="1rem",
            ),
            # Activity placeholder
            rx.vstack(
                rx.text("📊 Agent deployment completed", size="2"),
                rx.text("🔄 Task processing started", size="2"),
                rx.text("✅ System health check passed", size="2"),
                spacing="3",
                align_items="start",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        background=ThemeState.theme["bg_secondary"],
        border=f"1px solid {ThemeState.theme['bg_tertiary']}",
    )


def quick_actions_card() -> rx.Component:
    """Quick action buttons"""
    return rx.card(
        rx.vstack(
            rx.heading("Quick Actions", size="6", margin_bottom="1rem"),
            rx.vstack(
                rx.link(
                    rx.button(
                        rx.icon("layers", size=16),
                        "📊 Queue Monitoring",
                        width="100%",
                        variant="soft",
                        color_scheme="purple",
                    ),
                    href="/queues",
                ),
                rx.button(
                    rx.icon("play", size=16),
                    "Deploy All Agents",
                    width="100%",
                    variant="soft",
                    color_scheme="blue",
                ),
                rx.button(
                    rx.icon("activity", size=16),
                    "View System Health",
                    width="100%",
                    variant="soft",
                    color_scheme="green",
                ),
                rx.button(
                    rx.icon("file_text", size=16),
                    "Check Recent Logs",
                    width="100%",
                    variant="soft",
                    color_scheme="gray",
                ),
                rx.button(
                    rx.icon("alert_triangle", size=16),
                    "View Active Alerts",
                    width="100%",
                    variant="soft",
                    color_scheme="yellow",
                ),
                spacing="2",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        background=ThemeState.theme["bg_secondary"],
        border=f"1px solid {ThemeState.theme['bg_tertiary']}",
    )


def dashboard_page() -> rx.Component:
    """
    Main dashboard page.
    
    Features:
    - Platform metrics (agents, tasks, queue, errors)
    - Agent status overview
    - Recent activity timeline
    - Quick action buttons
    - Real-time updates via WebSocket
    """
    return rx.box(
        # Navigation Header
        rx.hstack(
            rx.vstack(
                rx.heading("Platform Dashboard", size="8"),
                rx.text(
                    f"Welcome back, {AuthState.user_display_name}",
                    size="3",
                    color=ThemeState.theme["text_secondary"],
                ),
                spacing="1",
                align_items="start",
            ),
            rx.hstack(
                # Navigation Buttons
                rx.link(
                    rx.button(
                        rx.icon("home", size=18),
                        "Dashboard",
                        size="3",
                        variant="solid",
                        color_scheme="blue",
                    ),
                    href="/dashboard",
                ),
                rx.link(
                    rx.button(
                        rx.icon("layers", size=18),
                        "Queue Monitoring",
                        size="3",
                        variant="outline",
                        color_scheme="purple",
                    ),
                    href="/queues",
                ),
                rx.link(
                    rx.button(
                        rx.icon("workflow", size=18),
                        "Workflows",
                        size="3",
                        variant="outline",
                        color_scheme="cyan",
                    ),
                    href="/workflows",
                ),
                rx.link(
                    rx.button(
                        rx.icon("package", size=18),
                        "Agent Factory",
                        size="3",
                        variant="outline",
                        color_scheme="green",
                    ),
                    href="/factory",
                ),
                rx.link(
                    rx.button(
                        rx.icon("wrench", size=18),
                        "Servicing",
                        size="3",
                        variant="outline",
                        color_scheme="purple",
                    ),
                    href="/servicing",
                ),
                rx.link(
                    rx.button(
                        rx.icon("life-buoy", size=18),
                        "Help Desk",
                        size="3",
                        variant="outline",
                        color_scheme="red",
                    ),
                    href="/helpdesk",
                ),
                # Theme Selector
                rx.button(
                    rx.icon(ThemeState.theme_icon, size=18),
                    ThemeState.theme_label,
                    size="3",
                    variant="ghost",
                    on_click=ThemeState.toggle_theme,
                ),
                # Logout Button (direct JavaScript - no websocket needed)
                rx.el.button(
                    rx.icon("log_out", size=18),
                    "Logout",
                    on_click="localStorage.clear(); window.location.href='/login';",
                    style={
                        "background": "transparent",
                        "border": "none",
                        "color": "#ef4444",
                        "cursor": "pointer",
                        "display": "flex",
                        "align-items": "center",
                        "gap": "8px",
                        "padding": "8px 12px",
                        "font-size": "14px",
                    }
                ),
                rx.text(
                    "Last updated: ",
                    DashboardState.last_updated,
                    size="2",
                    color=ThemeState.theme["text_tertiary"],
                ),
                rx.button(
                    rx.icon("refresh_cw", size=16),
                    "Refresh",
                    size="2",
                    variant="soft",
                    on_click=DashboardState.refresh_metrics,
                ),
                spacing="2",
            ),
            justify="between",
            width="100%",
            margin_bottom="2rem",
        ),
        
        # Warning banner when using mock data
        rx.cond(
            DashboardState.using_mock_data,
            rx.box(
                rx.hstack(
                    rx.text("⚠️", font_size="1.5em"),
                    rx.vstack(
                        rx.text(
                            "Real Platform Data Not Available",
                            font_weight="bold",
                            color=ThemeState.theme["text_primary"],
                            font_size="1em",
                        ),
                        rx.text(
                            "Real platform data may not be available or working as expected. Using mocked data for demonstration. "
                            "Please work with Platform Administrator to bridge this gap. "
                            "When backend APIs are available for platform metrics, they will be integrated with this portal.",
                            color=ThemeState.theme["text_tertiary"],
                            font_size="0.9em",
                            line_height="1.5",
                        ),
                        spacing="1",
                        align_items="start",
                    ),
                    spacing="3",
                    align_items="start",
                ),
                padding="1rem 1.5rem",
                border_radius="0.75rem",
                background="rgba(245, 158, 11, 0.1)",
                border=f"1px solid {ThemeState.theme['warning']}",
                margin_bottom="1rem",
                width="100%",
            ),
        ),
        
        # Metrics Grid
        metrics_grid(),
        # Two-column layout
        rx.grid(
            # Left column
            rx.vstack(
                agent_status_card(),
                recent_activity_card(),
                spacing="4",
                width="100%",
            ),
            # Right column
            rx.vstack(
                quick_actions_card(),
                spacing="4",
                width="100%",
            ),
            columns="2",
            spacing="4",
            width="100%",
            margin_top="2rem",
        ),
        # Page container
        width="100%",
        padding="2rem",
        background=ThemeState.theme["bg_primary"],
        min_height="100vh",
        # Load metrics on mount
        on_mount=DashboardState.load_metrics,
    )
