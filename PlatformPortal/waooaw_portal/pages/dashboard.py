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
from waooaw_portal.theme.colors import DARK_THEME


def metrics_grid() -> rx.Component:
    """Metrics cards grid"""
    return rx.grid(
        # Total Agents
        rx.card(
            rx.vstack(
                rx.text("Total Agents", size="2", color=DARK_THEME["text_tertiary"]),
                rx.heading(DashboardState.total_agents, size="8"),
                rx.text(f"🟢 {DashboardState.agents_running} online", size="1", color=DARK_THEME["status_success"]),
                align="center",
                spacing="2",
            )
        ),
        # Active Tasks
        rx.card(
            rx.vstack(
                rx.text("Active Tasks", size="2", color=DARK_THEME["text_tertiary"]),
                rx.heading(DashboardState.active_tasks, size="8"),
                rx.text(f"{DashboardState.requests_per_minute} req/min", size="1", color=DARK_THEME["info"]),
                align="center",
                spacing="2",
            )
        ),
        # Queue Pending
        rx.card(
            rx.vstack(
                rx.text("Queue Pending", size="2", color=DARK_THEME["text_tertiary"]),
                rx.heading(DashboardState.queue_pending, size="8"),
                rx.text(f"P95: {DashboardState.p95_latency}ms", size="1", color=DARK_THEME["warning"]),
                align="center",
                spacing="2",
            )
        ),
        # Error Rate
        rx.card(
            rx.vstack(
                rx.text("Error Rate", size="2", color=DARK_THEME["text_tertiary"]),
                rx.heading(f"{DashboardState.error_rate}%", size="8"),
                rx.text(DashboardState.agents_health_label, size="1", color=DARK_THEME["status_success"]),
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
                        color=DARK_THEME["status_success"],
                    ),
                    rx.text(
                        "Running",
                        size="2",
                        color=DARK_THEME["text_secondary"],
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
                        color=DARK_THEME["text_secondary"],
                    ),
                    rx.text(
                        "Stopped",
                        size="2",
                        color=DARK_THEME["text_secondary"],
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
                        color=DARK_THEME["status_error"],
                    ),
                    rx.text(
                        "Errored",
                        size="2",
                        color=DARK_THEME["text_secondary"],
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
                rx.text("System Uptime:", size="2", color=DARK_THEME["text_secondary"]),
                rx.text(
                    f"{DashboardState.system_uptime_percentage}%",
                    size="2",
                    font_weight="bold",
                    color=DARK_THEME["accent_cyan"],
                ),
                justify="between",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        background=DARK_THEME["bg_secondary"],
        border=f"1px solid {DARK_THEME['bg_tertiary']}",
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
        background=DARK_THEME["bg_secondary"],
        border=f"1px solid {DARK_THEME['bg_tertiary']}",
    )


def quick_actions_card() -> rx.Component:
    """Quick action buttons"""
    return rx.card(
        rx.vstack(
            rx.heading("Quick Actions", size="6", margin_bottom="1rem"),
            rx.vstack(
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
        background=DARK_THEME["bg_secondary"],
        border=f"1px solid {DARK_THEME['bg_tertiary']}",
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
        # Header
        rx.hstack(
            rx.vstack(
                rx.heading("Platform Dashboard", size="8"),
                rx.text(
                    f"Welcome back, {AuthState.user_display_name}",
                    size="3",
                    color=DARK_THEME["text_secondary"],
                ),
                spacing="1",
                align_items="start",
            ),
            rx.hstack(
                rx.text(
                    "Last updated: ",
                    DashboardState.last_updated,
                    size="2",
                    color=DARK_THEME["text_tertiary"],
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
        background=DARK_THEME["bg_primary"],
        min_height="100vh",
        # Load metrics on mount
        on_mount=DashboardState.load_metrics,
    )
