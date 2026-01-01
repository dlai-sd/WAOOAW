"""
Agents Page

List all agents with state machine integration.
"""

import reflex as rx
from waooaw_portal.state.agents_state import AgentsState, AgentData
from waooaw_portal.services.agent_state_machine import AgentStateMachine


def agent_card(agent: AgentData) -> rx.Component:
    """
    Individual agent card component.
    
    Features:
    - Agent avatar with gradient background
    - Name, type, tier
    - Current state badge with color
    - Health score and uptime
    - Tasks completed count
    - Actions dropdown menu
    """
    state_machine = AgentStateMachine()
    
    # Get state display info
    state_enum = AgentStateMachine.get_state_enum(agent.current_state)
    state_color = state_machine.get_state_color(state_enum)
    state_label = state_machine.get_state_label(state_enum)
    
    return rx.box(
        # Agent card
        rx.box(
            # Header: Avatar + Name
            rx.hstack(
                # Avatar
                rx.box(
                    rx.text(
                        agent.agent_name[:2].upper(),
                        font_size="1.25rem",
                        font_weight="700",
                        color="white",
                    ),
                    width="3.5rem",
                    height="3.5rem",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    border_radius="1rem",
                    background=f"linear-gradient(135deg, {state_color}, #667eea)",
                    flex_shrink="0",
                ),
                # Name + State
                rx.vstack(
                    rx.text(
                        agent.agent_name,
                        font_size="1.125rem",
                        font_weight="600",
                        color="white",
                    ),
                    rx.badge(
                        state_label,
                        color_scheme=state_color.split("#")[0] if "#" not in state_color else "gray",
                        variant="solid",
                        size="sm",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                    flex="1",
                ),
                spacing="1rem",
                align_items="center",
                width="100%",
            ),
            # Tier
            rx.text(
                agent.tier,
                font_size="0.875rem",
                color="#9ca3af",
                margin_top="0.75rem",
            ),
            # Description
            rx.text(
                agent.description,
                font_size="0.875rem",
                color="#d1d5db",
                margin_top="0.5rem",
                line_height="1.5",
            ),
            # Metrics
            rx.hstack(
                rx.vstack(
                    rx.text(
                        f"{agent.health_score}%",
                        font_size="1.25rem",
                        font_weight="600",
                        color="#00f2fe",
                    ),
                    rx.text(
                        "Health",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                rx.vstack(
                    rx.text(
                        str(agent.tasks_completed),
                        font_size="1.25rem",
                        font_weight="600",
                        color="#667eea",
                    ),
                    rx.text(
                        "Tasks",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                rx.vstack(
                    rx.text(
                        f"{agent.uptime_percentage}%",
                        font_size="1.25rem",
                        font_weight="600",
                        color="#10b981",
                    ),
                    rx.text(
                        "Uptime",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                spacing="2rem",
                margin_top="1.5rem",
            ),
            # Last Active
            rx.text(
                f"Last active: {agent.last_active}",
                font_size="0.75rem",
                color="#6b7280",
                margin_top="1rem",
            ),
            # Actions
            rx.hstack(
                rx.button(
                    "Start",
                    size="sm",
                    color_scheme="green",
                    on_click=AgentsState.start_agent(agent.agent_id),
                    display="flex" if agent.current_state in ["stopped", "deployed"] else "none",
                ),
                rx.button(
                    "Stop",
                    size="sm",
                    color_scheme="red",
                    on_click=AgentsState.stop_agent(agent.agent_id),
                    display="flex" if agent.current_state == "running" else "none",
                ),
                rx.button(
                    "Restart",
                    size="sm",
                    color_scheme="cyan",
                    on_click=AgentsState.restart_agent(agent.agent_id),
                    display="flex" if agent.current_state == "running" else "none",
                ),
                rx.button(
                    "Suspend",
                    size="sm",
                    color_scheme="yellow",
                    on_click=AgentsState.suspend_agent(agent.agent_id),
                    display="flex" if agent.current_state == "running" else "none",
                ),
                spacing="0.5rem",
                margin_top="1.5rem",
            ),
            padding="1.5rem",
            background="#18181b",
            border="1px solid #27272a",
            border_radius="1.5rem",
            transition="all 0.3s ease",
            _hover={
                "transform": "translateY(-4px)",
                "box_shadow": f"0 0 20px rgba(0, 242, 254, 0.2)",
                "border_color": "#00f2fe",
            },
        ),
        width="100%",
    )


def filters_bar() -> rx.Component:
    """Filter controls"""
    return rx.hstack(
        # Search
        rx.input(
            placeholder="Search agents...",
            value=AgentsState.search_query,
            on_change=AgentsState.set_search_query,
            width="20rem",
        ),
        # State filter
        rx.select(
            ["all", "running", "stopped", "errored", "deployed"],
            value=AgentsState.filter_state,
            on_change=AgentsState.set_filter_state,
            placeholder="Filter by state",
        ),
        # Tier filter
        rx.select(
            ["all", "platform", "business", "custom"],
            value=AgentsState.filter_tier,
            on_change=AgentsState.set_filter_tier,
            placeholder="Filter by tier",
        ),
        # Bulk actions
        rx.cond(
            AgentsState.selected_count > 0,
            rx.hstack(
                rx.text(
                    f"{AgentsState.selected_count} selected",
                    font_size="0.875rem",
                    color="#9ca3af",
                ),
                rx.button(
                    "Start All",
                    size="sm",
                    color_scheme="green",
                    on_click=AgentsState.execute_bulk_action("start"),
                ),
                rx.button(
                    "Stop All",
                    size="sm",
                    color_scheme="red",
                    on_click=AgentsState.execute_bulk_action("stop"),
                ),
                rx.button(
                    "Deselect",
                    size="sm",
                    variant="ghost",
                    on_click=AgentsState.deselect_all_agents,
                ),
                spacing="0.5rem",
            ),
            rx.fragment(),
        ),
        spacing="1rem",
        align_items="center",
        width="100%",
        padding="1.5rem",
        background="#18181b",
        border="1px solid #27272a",
        border_radius="1rem",
    )


def agents_grid() -> rx.Component:
    """Grid of agent cards"""
    return rx.cond(
        AgentsState.filtered_count > 0,
        rx.box(
            rx.foreach(
                AgentsState.get_filtered_agents(),
                agent_card,
            ),
            display="grid",
            grid_template_columns="repeat(auto-fill, minmax(24rem, 1fr))",
            gap="1.5rem",
            width="100%",
        ),
        # Empty state
        rx.box(
            rx.vstack(
                rx.text(
                    "🔍",
                    font_size="4rem",
                ),
                rx.text(
                    "No agents found",
                    font_size="1.5rem",
                    font_weight="600",
                    color="white",
                ),
                rx.text(
                    "Try adjusting your filters",
                    font_size="1rem",
                    color="#9ca3af",
                ),
                spacing="1rem",
                align_items="center",
            ),
            padding="4rem",
            text_align="center",
        ),
    )


def agents_page() -> rx.Component:
    """
    Agents management page.
    
    Features:
    - Agent list with state machine
    - Search and filters
    - Bulk actions
    - Real-time status updates
    """
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Agents",
                        font_size="2rem",
                        font_weight="700",
                        color="white",
                    ),
                    rx.text(
                        f"{AgentsState.agent_count} total • {AgentsState.running_count} running • {AgentsState.stopped_count} stopped",
                        font_size="1rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.5rem",
                ),
                rx.spacer(),
                rx.button(
                    "Refresh",
                    on_click=AgentsState.load_agents,
                    color_scheme="cyan",
                    variant="outline",
                ),
                width="100%",
                align_items="center",
            ),
            # Filters
            filters_bar(),
            # Agent grid
            agents_grid(),
            spacing="2rem",
            width="100%",
            max_width="90rem",
            margin="0 auto",
            padding="2rem",
        ),
        width="100%",
        min_height="100vh",
        background="#0a0a0a",
        on_mount=AgentsState.load_agents,
    )
