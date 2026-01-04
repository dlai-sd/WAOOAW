"""
Wizard Stepper Component

Progress indicator for multi-step wizard.
"""

import reflex as rx
from typing import List


def step_indicator(step_number: int, step_title: str, is_current: bool, is_completed: bool) -> rx.Component:
    """Individual step indicator"""
    # Colors
    active_color = "#00f2fe"
    completed_color = "#10b981"
    inactive_color = "#6b7280"
    
    if is_completed:
        color = completed_color
        icon = "check"
    elif is_current:
        color = active_color
        icon = "circle"
    else:
        color = inactive_color
        icon = "circle"
    
    return rx.box(
        rx.vstack(
            # Circle with number/icon
            rx.box(
                rx.cond(
                    is_completed,
                    rx.icon(icon, size=20, color="white"),
                    rx.text(
                        str(step_number + 1),
                        font_size="1rem",
                        font_weight="600",
                        color="white" if is_current or is_completed else inactive_color,
                    ),
                ),
                width="2.5rem",
                height="2.5rem",
                border_radius="50%",
                background=color if is_current or is_completed else "transparent",
                border=f"2px solid {color}",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            # Step title
            rx.text(
                step_title,
                font_size="0.875rem",
                font_weight="600" if is_current else "400",
                color="white" if is_current else inactive_color,
                text_align="center",
                width="100%",
            ),
            align_items="center",
            spacing="2",
        ),
        flex="1",
    )


def wizard_stepper(current_step: int, step_titles: List[str]) -> rx.Component:
    """
    Wizard stepper component.
    
    Args:
        current_step: Current step index (0-based)
        step_titles: List of step titles
        
    Returns:
        Stepper component
    """
    return rx.box(
        rx.hstack(
            # Render steps
            *[
                step_indicator(
                    step_number=i,
                    step_title=step_titles[i],
                    is_current=i == current_step,
                    is_completed=i < current_step,
                )
                for i in range(len(step_titles))
            ],
            width="100%",
            spacing="0",
            align_items="flex-start",
        ),
        width="100%",
        padding="2rem 0",
    )
