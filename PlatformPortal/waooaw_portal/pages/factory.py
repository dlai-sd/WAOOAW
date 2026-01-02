"""
Agent Factory Page

Agent lifecycle management, deployment, and configuration.
"""

import reflex as rx
from waooaw_portal.state.factory_state import FactoryState, Agent, AgentCapability
from waooaw_portal.state.theme_state import ThemeState


def status_badge(status: str) -> rx.Component:
    """Status badge with dynamic color"""
    color = rx.cond(
        status == "online",
        ThemeState.theme["status_success"],
        rx.cond(
            status == "offline",
            ThemeState.theme["text_tertiary"],
            rx.cond(
                status == "starting",
                ThemeState.theme["info"],
                rx.cond(
                    status == "stopping",
                    ThemeState.theme["warning"],
                    ThemeState.theme["status_error"]
                )
            )
        )
    )
    
    return rx.badge(
        status.upper(),
        background=color,
        color=ThemeState.theme["text_primary"],
        variant="solid",
        font_size="0.75rem",
    )


def health_badge(health: str) -> rx.Component:
    """Health badge with dynamic color"""
    color = rx.cond(
        health == "healthy",
        ThemeState.theme["status_success"],
        rx.cond(
            health == "degraded",
            ThemeState.theme["warning"],
            ThemeState.theme["status_error"]
        )
    )
    
    icon = rx.cond(
        health == "healthy",
        "check_circle",
        rx.cond(
            health == "degraded",
            "alert_triangle",
            "x_circle"
        )
    )
    
    return rx.hstack(
        rx.icon(icon, size=14),
        rx.text(health.capitalize(), font_size="0.75rem"),
        color=color,
        spacing="1",
    )


def agent_card(agent: Agent) -> rx.Component:
    """Individual agent card"""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.text(
                        agent.name,
                        font_size="1.125rem",
                        font_weight="600",
                        color=ThemeState.theme["text_primary"],
                    ),
                    rx.text(
                        agent.description,
                        font_size="0.875rem",
                        color=ThemeState.theme["text_tertiary"],
                        line_height="1.4",
                    ),
                    align_items="flex-start",
                    spacing="1",
                    flex="1",
                ),
                rx.vstack(
                    status_badge(agent.status),
                    health_badge(agent.health),
                    spacing="2",
                    align_items="flex-end",
                ),
                width="100%",
                align_items="flex-start",
                spacing="4",
            ),
            
            # Category and version
            rx.hstack(
                rx.badge(
                    agent.category.capitalize(),
                    color_scheme="purple",
                    variant="soft",
                ),
                rx.text(
                    f"v{agent.version}",
                    font_size="0.75rem",
                    color=ThemeState.theme["text_tertiary"],
                ),
                spacing="2",
            ),
            
            # Metrics
            rx.hstack(
                rx.vstack(
                    rx.text(
                        agent.metrics.get("tasks_completed", 0),
                        font_size="1.25rem",
                        font_weight="700",
                        color=ThemeState.theme["text_primary"],
                    ),
                    rx.text(
                        "Tasks",
                        font_size="0.75rem",
                        color=ThemeState.theme["text_tertiary"],
                    ),
                    align_items="center",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text(
                        f"{agent.metrics.get('success_rate', 0)}%",
                        font_size="1.25rem",
                        font_weight="700",
                        color=ThemeState.theme["status_success"],
                    ),
                    rx.text(
                        "Success",
                        font_size="0.75rem",
                        color=ThemeState.theme["text_tertiary"],
                    ),
                    align_items="center",
                    spacing="1",
                ),
                rx.vstack(
                    rx.text(
                        f"{agent.metrics.get('uptime_percent', 0)}%",
                        font_size="1.25rem",
                        font_weight="700",
                        color=ThemeState.theme["info"],
                    ),
                    rx.text(
                        "Uptime",
                        font_size="0.75rem",
                        color=ThemeState.theme["text_tertiary"],
                    ),
                    align_items="center",
                    spacing="1",
                ),
                justify="between",
                width="100%",
                margin_top="1rem",
            ),
            
            # Actions
            rx.hstack(
                rx.cond(
                    agent.status == "online",
                    rx.button(
                        rx.icon("square", size=14),
                        "Stop",
                        size="1",
                        variant="soft",
                        color_scheme="red",
                        on_click=lambda: FactoryState.stop_agent(agent.agent_id),
                    ),
                    rx.button(
                        rx.icon("play", size=14),
                        "Start",
                        size="1",
                        variant="soft",
                        color_scheme="green",
                        on_click=lambda: FactoryState.start_agent(agent.agent_id),
                    ),
                ),
                rx.button(
                    rx.icon("refresh_cw", size=14),
                    "Restart",
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                    on_click=lambda: FactoryState.restart_agent(agent.agent_id),
                ),
                rx.button(
                    rx.icon("settings", size=14),
                    "Configure",
                    size="1",
                    variant="ghost",
                    on_click=lambda: FactoryState.select_agent(agent.agent_id),
                ),
                spacing="2",
                width="100%",
                margin_top="1rem",
            ),
            
            spacing="4",
            align_items="flex-start",
            width="100%",
        ),
        padding="1.5rem",
        background=ThemeState.theme["bg_secondary"],
        border=f"1px solid {ThemeState.theme['bg_tertiary']}",
        border_radius="1rem",
        _hover={
            "border_color": ThemeState.theme["info"],
            "box_shadow": f"0 0 20px {ThemeState.theme['info']}33",
        },
        transition="all 0.3s ease",
        cursor="pointer",
    )


def stats_bar() -> rx.Component:
    """Agent statistics bar"""
    return rx.hstack(
        rx.vstack(
            rx.text(
                FactoryState.agent_count,
                font_size="1.5rem",
                font_weight="700",
                color=ThemeState.theme["text_primary"],
            ),
            rx.text(
                "Total Agents",
                font_size="0.75rem",
                color=ThemeState.theme["text_tertiary"],
            ),
            align_items="center",
            spacing="1",
        ),
        rx.vstack(
            rx.text(
                FactoryState.online_count,
                font_size="1.5rem",
                font_weight="700",
                color=ThemeState.theme["status_success"],
            ),
            rx.text(
                "Online",
                font_size="0.75rem",
                color=ThemeState.theme["text_tertiary"],
            ),
            align_items="center",
            spacing="1",
        ),
        rx.vstack(
            rx.text(
                FactoryState.offline_count,
                font_size="1.5rem",
                font_weight="700",
                color=ThemeState.theme["text_tertiary"],
            ),
            rx.text(
                "Offline",
                font_size="0.75rem",
                color=ThemeState.theme["text_tertiary"],
            ),
            align_items="center",
            spacing="1",
        ),
        rx.vstack(
            rx.text(
                FactoryState.healthy_count,
                font_size="1.5rem",
                font_weight="700",
                color=ThemeState.theme["info"],
            ),
            rx.text(
                "Healthy",
                font_size="0.75rem",
                color=ThemeState.theme["text_tertiary"],
            ),
            align_items="center",
            spacing="1",
        ),
        # Filters
        rx.select(
            ["all", "marketing", "education", "sales", "operations"],
            value=FactoryState.category_filter,
            on_change=FactoryState.set_category_filter,
            size="2",
            placeholder="Category",
        ),
        rx.select(
            ["all", "online", "offline", "starting", "stopping", "error"],
            value=FactoryState.status_filter,
            on_change=FactoryState.set_status_filter,
            size="2",
            placeholder="Status",
        ),
        rx.select(
            ["all", "healthy", "degraded", "unhealthy"],
            value=FactoryState.health_filter,
            on_change=FactoryState.set_health_filter,
            size="2",
            placeholder="Health",
        ),
        rx.button(
            rx.icon("plus", size=16),
            "Deploy Agent",
            size="2",
            color_scheme="cyan",
            variant="solid",
            on_click=FactoryState.open_create_form,
        ),
        rx.button(
            rx.icon("refresh_cw", size=16),
            "Refresh",
            size="2",
            variant="soft",
            on_click=FactoryState.load_agents,
        ),
        spacing="8",
        align_items="center",
        width="100%",
        padding="1.5rem",
        background=ThemeState.theme["bg_secondary"],
        border=f"1px solid {ThemeState.theme['bg_tertiary']}",
        border_radius="1rem",
    )


def agents_grid() -> rx.Component:
    """Grid of agent cards"""
    return rx.box(
        rx.cond(
            FactoryState.filtered_agents.length() > 0,
            rx.box(
                rx.foreach(
                    FactoryState.filtered_agents,
                    agent_card,
                ),
                display="grid",
                grid_template_columns="repeat(auto-fill, minmax(22rem, 1fr))",
                gap="1.5rem",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("inbox", size=48, color=ThemeState.theme["text_tertiary"]),
                    rx.text(
                        "No agents found",
                        font_size="1.25rem",
                        font_weight="600",
                        color=ThemeState.theme["text_primary"],
                    ),
                    rx.text(
                        "Deploy your first agent to get started",
                        font_size="0.875rem",
                        color=ThemeState.theme["text_tertiary"],
                    ),
                    rx.button(
                        rx.icon("plus", size=16),
                        "Deploy Agent",
                        size="3",
                        color_scheme="cyan",
                        on_click=FactoryState.open_create_form,
                    ),
                    spacing="4",
                    align_items="center",
                ),
                padding="4rem",
                text_align="center",
            ),
        ),
    )


def factory_page() -> rx.Component:
    """
    Agent Factory page.
    
    Features:
    - Agent lifecycle management (start/stop/restart)
    - Agent deployment and configuration
    - Health monitoring
    - Performance metrics
    - Search and filtering
    """
    return rx.box(
        rx.vstack(
            # Navigation Header
            rx.hstack(
                rx.text(
                    "Agent Factory",
                    font_size="2rem",
                    font_weight="700",
                    color=ThemeState.theme["text_primary"],
                ),
                rx.spacer(),
                rx.hstack(
                    rx.link(
                        rx.button(
                            rx.icon("home", size=18),
                            "Dashboard",
                            size="3",
                            variant="outline",
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
                    spacing="2",
                ),
                width="100%",
                align_items="center",
                margin_bottom="1rem",
            ),
            
            # Warning banner
            rx.cond(
                FactoryState.using_mock_data,
                rx.box(
                    rx.hstack(
                        rx.text("⚠️", font_size="1.5em"),
                        rx.vstack(
                            rx.text(
                                "Real Agent Data Not Available",
                                font_weight="bold",
                                color=ThemeState.theme["text_primary"],
                                font_size="1em",
                            ),
                            rx.text(
                                "Real agent registry data may not be available or working as expected. Using mocked data for demonstration. "
                                "Please work with Platform Administrator to bridge this gap. "
                                "When backend APIs are available for agent management, they will be integrated with this portal.",
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
            
            # Stats bar
            stats_bar(),
            
            # Agents grid
            agents_grid(),
            
            spacing="6",
            width="100%",
        ),
        width="100%",
        padding="2rem",
        background=ThemeState.theme["bg_primary"],
        min_height="100vh",
        on_mount=FactoryState.load_agents,
    )
