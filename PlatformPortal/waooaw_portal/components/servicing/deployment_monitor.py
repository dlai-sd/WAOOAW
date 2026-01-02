"""Deployment progress monitor component"""

import reflex as rx
from ...state.servicing_state import ServicingState


def deployment_monitor() -> rx.Component:
    """Render real-time deployment progress"""
    
    return rx.vstack(
        rx.cond(
            ServicingState.is_upgrading | ServicingState.rollback_in_progress,
            rx.hstack(
                rx.spinner(size="3"),
                rx.text(
                    rx.cond(
                        ServicingState.rollback_in_progress,
                        "Rollback in progress...",
                        "Upgrade in progress...",
                    ),
                    font_size="1.1rem",
                    font_weight="bold",
                    color="cyan",
                ),
                margin_bottom="1rem",
            ),
            rx.cond(
                ServicingState.upgrade_complete,
                rx.hstack(
                    rx.icon(
                        rx.cond(ServicingState.upgrade_success, "check-circle", "x-circle"),
                        size=28,
                        color=rx.cond(ServicingState.upgrade_success, "green", "red"),
                    ),
                    rx.text(
                        rx.cond(
                            ServicingState.upgrade_success,
                            "Upgrade completed successfully!",
                            "Upgrade failed - Rolled back",
                        ),
                        font_size="1.1rem",
                        font_weight="bold",
                        color=rx.cond(ServicingState.upgrade_success, "green", "red"),
                    ),
                    margin_bottom="1rem",
                ),
                rx.fragment(),
            ),
        ),
        
        # Progress steps
        rx.vstack(
            rx.foreach(
                ServicingState.upgrade_steps,
                lambda step: rx.card(
                    rx.hstack(
                        rx.cond(
                            step.status == "completed",
                            rx.icon("check-circle", size=24, color="green"),
                            rx.cond(
                                step.status == "running",
                                rx.spinner(size="3"),
                                rx.cond(
                                    step.status == "failed",
                                    rx.icon("x-circle", size=24, color="red"),
                                    rx.icon("circle", size=24, color="gray"),
                                ),
                            ),
                        ),
                        
                        rx.vstack(
                            rx.text(step.step_name, weight="bold", font_size="1rem"),
                            rx.text(step.message, color="gray", font_size="0.9rem"),
                            rx.hstack(
                                rx.text(f"Time: {step.timestamp}", color="gray", font_size="0.85rem"),
                                rx.cond(
                                    step.duration_sec.is_some(),
                                    rx.text(f"Duration: {step.duration_sec}s", color="gray", font_size="0.85rem"),
                                    rx.fragment(),
                                ),
                            ),
                            align_items="start",
                            spacing="0.25rem",
                        ),
                        
                        spacing="4",
                        align_items="center",
                        width="100%",
                    ),
                    padding="1rem",
                    margin_bottom="0.5rem",
                    border_left=rx.cond(
                        step.status == "completed",
                        "4px solid var(--green-9)",
                        rx.cond(
                            step.status == "running",
                            "4px solid var(--cyan-9)",
                            rx.cond(
                                step.status == "failed",
                                "4px solid var(--red-9)",
                                "4px solid var(--gray-6)",
                            ),
                        ),
                    ),
                ),
            ),
            width="100%",
            spacing="2",
        ),
        
        # Progress bar
        rx.cond(
            ServicingState.is_upgrading,
            rx.vstack(
                rx.text("Overall Progress", weight="bold", margin_top="1rem"),
                rx.progress(
                    value=(rx.State.length(ServicingState.upgrade_steps) / 6) * 100,
                    color_scheme="cyan",
                    width="100%",
                ),
                width="100%",
                align_items="start",
            ),
            rx.fragment(),
        ),
        
        width="100%",
        align_items="start",
        spacing="4",
    )
