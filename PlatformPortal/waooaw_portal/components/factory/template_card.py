"""
Template Card Component

Card for displaying agent templates.
"""

import reflex as rx
from waooaw_portal.state.factory_state import AgentTemplate


def get_complexity_color(complexity: str) -> str:
    """Get color for complexity level"""
    colors = {
        "low": "#10b981",    # Green
        "medium": "#f59e0b",  # Yellow
        "high": "#ef4444",    # Red
    }
    return colors.get(complexity, "#6b7280")


def template_card(template: AgentTemplate, is_selected: bool = False) -> rx.Component:
    """
    Template card component.
    
    Args:
        template: Agent template
        is_selected: Whether this template is selected
        
    Returns:
        Template card component
    """
    border_color = "#00f2fe" if is_selected else "#27272a"
    
    return rx.box(
        rx.vstack(
            # Icon and complexity badge
            rx.hstack(
                rx.text(
                    template.icon,
                    font_size="2.5rem",
                ),
                rx.spacer(),
                rx.badge(
                    template.complexity.upper(),
                    background=get_complexity_color(template.complexity),
                    color="white",
                    variant="solid",
                    font_size="0.625rem",
                ),
                width="100%",
                align_items="flex-start",
            ),
            # Title
            rx.text(
                template.name,
                font_size="1.25rem",
                font_weight="700",
                color="white",
                margin_top="1rem",
            ),
            # Description
            rx.text(
                template.description,
                font_size="0.875rem",
                color="#9ca3af",
                line_height="1.5",
            ),
            # Category and time
            rx.hstack(
                rx.badge(
                    template.category,
                    color_scheme="gray",
                    variant="outline",
                    font_size="0.75rem",
                ),
                rx.text(
                    f"⏱️ {template.estimated_time}",
                    font_size="0.75rem",
                    color="#6b7280",
                ),
                width="100%",
                justify_content="space-between",
                margin_top="1rem",
            ),
            # Required capabilities
            rx.box(
                rx.text(
                    "Required:",
                    font_size="0.75rem",
                    color="#9ca3af",
                    margin_bottom="0.25rem",
                ),
                rx.hstack(
                    *[
                        rx.badge(
                            cap,
                            color_scheme="cyan",
                            variant="subtle",
                            font_size="0.625rem",
                        )
                        for cap in template.required_capabilities[:3]  # Show first 3
                    ],
                    spacing="0.25rem",
                    wrap="wrap",
                ),
                margin_top="1rem",
            ),
            # Resources
            rx.hstack(
                rx.vstack(
                    rx.text(
                        f"{template.resource_requirements['cpu_cores']} CPU",
                        font_size="0.75rem",
                        color="#6b7280",
                    ),
                    rx.text(
                        f"{template.resource_requirements['memory_gb']}GB RAM",
                        font_size="0.75rem",
                        color="#6b7280",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                rx.vstack(
                    rx.text(
                        f"{template.resource_requirements['storage_gb']}GB Storage",
                        font_size="0.75rem",
                        color="#6b7280",
                    ),
                    rx.text(
                        f"{len(template.dependencies)} deps",
                        font_size="0.75rem",
                        color="#6b7280",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                width="100%",
                justify_content="space-between",
                margin_top="1rem",
            ),
            align_items="flex-start",
            spacing="2",
            width="100%",
        ),
        padding="1.5rem",
        background="#18181b",
        border=f"2px solid {border_color}",
        border_radius="1rem",
        _hover={
            "box_shadow": f"0 0 30px {border_color}33",
            "transform": "translateY(-4px)",
        },
        transition="all 0.3s ease",
        cursor="pointer",
        height="100%",
    )
