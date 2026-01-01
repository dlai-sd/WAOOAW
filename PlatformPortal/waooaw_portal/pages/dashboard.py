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
        metrics_widget(
            label="Total Agents",
            value=DashboardState.total_agents,
            delta=DashboardState.agents_trend,
            trend="up",
            unit="agents",
            size="lg",
        ),
        # Active Tasks
        metrics_widget(
            label="Active Tasks",
            value=DashboardState.active_tasks,
            delta=DashboardState.tasks_trend,
            trend="neutral",
            unit="tasks",
            size="lg",
        ),
        # Queue Pending
        metrics_widget(
            label="Queue Pending",
            value=DashboardState.queue_pending,
            delta=DashboardState.queue_trend,
            trend="down",
            unit="messages",
            size="lg",
        ),
        # Error Rate
        metrics_widget(
            label="Error Rate",
            value=DashboardState.error_rate,
            delta=DashboardState.error_trend,
            trend="down",
            unit="%",
            size="lg",
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
                        color=DARK_THEME["text_gray_400"],
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
                        color=DARK_THEME["text_gray_400"],
                    ),
                    rx.text(
                        "Stopped",
                        size="2",
                        color=DARK_THEME["text_gray_400"],
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
                        color=DARK_THEME["text_gray_400"],
                    ),
                    align="center",
                    spacing="1",
                ),
                justify="space-around",
                width="100%",
            ),
            # Uptime percentage
            rx.separator(margin_y="1rem"),
            rx.hstack(
                rx.text("System Uptime:", size="2", color=DARK_THEME["text_gray_400"]),
                rx.text(
                    f"{DashboardState.system_uptime_percentage}%",
                    size="2",
                    font_weight="bold",
                    color=DARK_THEME["neon_cyan"],
                ),
                justify="between",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        background=DARK_THEME["bg_gray_900"],
        border=f"1px solid {DARK_THEME['bg_gray_800']}",
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
            # Timeline
            timeline_agent_activity(),
            spacing="4",
            width="100%",
        ),
        width="100%",
        background=DARK_THEME["bg_gray_900"],
        border=f"1px solid {DARK_THEME['bg_gray_800']}",
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
        background=DARK_THEME["bg_gray_900"],
        border=f"1px solid {DARK_THEME['bg_gray_800']}",
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
                    color=DARK_THEME["text_gray_400"],
                ),
                spacing="1",
                align_items="start",
            ),
            rx.hstack(
                rx.text(
                    f"Last updated: {DashboardState.last_updated or 'Never'}",
                    size="2",
                    color=DARK_THEME["text_gray_500"],
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
        background=DARK_THEME["bg_black"],
        min_height="100vh",
        # Load metrics on mount
        on_mount=DashboardState.load_metrics,
    )
