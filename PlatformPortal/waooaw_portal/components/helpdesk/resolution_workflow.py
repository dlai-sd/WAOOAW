"""Resolution workflow component"""

import reflex as rx
from typing import List
from ...state.helpdesk_state import ResolutionStep


def resolution_workflow(steps: List[ResolutionStep], current_step: int) -> rx.Component:
    """Render resolution workflow progress"""
    
    return rx.vstack(
        rx.heading("Resolution Workflow", size="5", weight="bold"),
        rx.text(
            f"Progress: {current_step}/6 steps completed",
            color="gray",
            font_size="0.9rem",
        ),
        
        rx.cond(
            rx.State.length(steps) > 0,
            rx.vstack(
                rx.foreach(
                    steps,
                    lambda step: rx.card(
                        rx.hstack(
                            # Step number circle
                            rx.box(
                                rx.cond(
                                    step.status == "completed",
                                    rx.icon("check", size=20, color="white"),
                                    rx.cond(
                                        step.status == "in_progress",
                                        rx.spinner(size="2", color="white"),
                                        rx.text(step.step_number, color="white", weight="bold"),
                                    ),
                                ),
                                background=rx.cond(
                                    step.status == "completed",
                                    "var(--green-9)",
                                    rx.cond(
                                        step.status == "in_progress",
                                        "var(--cyan-9)",
                                        rx.cond(
                                            step.status == "skipped",
                                            "var(--gray-6)",
                                            "var(--gray-8)",
                                        ),
                                    ),
                                ),
                                border_radius="50%",
                                width="48px",
                                height="48px",
                                display="flex",
                                align_items="center",
                                justify_content="center",
                                flex_shrink="0",
                            ),
                            
                            # Step details
                            rx.vstack(
                                rx.hstack(
                                    rx.text(step.title, weight="bold", font_size="1.05rem"),
                                    rx.badge(
                                        step.status.replace("_", " ").upper(),
                                        color_scheme=rx.cond(
                                            step.status == "completed",
                                            "green",
                                            rx.cond(
                                                step.status == "in_progress",
                                                "cyan",
                                                rx.cond(
                                                    step.status == "skipped",
                                                    "gray",
                                                    "gray",
                                                ),
                                            ),
                                        ),
                                    ),
                                    width="100%",
                                ),
                                rx.text(step.description, color="gray", font_size="0.9rem"),
                                
                                rx.cond(
                                    step.assigned_to.is_some(),
                                    rx.hstack(
                                        rx.icon("user", size=14, color="gray"),
                                        rx.text(step.assigned_to, font_size="0.85rem", color="gray"),
                                    ),
                                    rx.fragment(),
                                ),
                                
                                rx.cond(
                                    step.duration_min.is_some(),
                                    rx.hstack(
                                        rx.icon("clock", size=14, color="gray"),
                                        rx.text(f"{step.duration_min} minutes", font_size="0.85rem", color="gray"),
                                    ),
                                    rx.fragment(),
                                ),
                                
                                rx.cond(
                                    step.notes.is_some(),
                                    rx.text(f"Notes: {step.notes}", font_size="0.85rem", color="gray", font_style="italic"),
                                    rx.fragment(),
                                ),
                                
                                align_items="start",
                                spacing="2",
                                flex="1",
                            ),
                            
                            spacing="6",
                            align_items="start",
                            width="100%",
                        ),
                        padding="1.5rem",
                        margin_bottom="1rem",
                        opacity=rx.cond(
                            step.status == "pending",
                            "0.6",
                            "1.0",
                        ),
                    ),
                ),
                width="100%",
                spacing="4",
            ),
            rx.text("No resolution workflow available", color="gray", margin="2rem 0"),
        ),
        
        # Progress bar
        rx.cond(
            rx.State.length(steps) > 0,
            rx.vstack(
                rx.text("Overall Progress", weight="bold", font_size="0.9rem"),
                rx.progress(
                    value=(current_step / 6) * 100,
                    color_scheme="cyan",
                    width="100%",
                ),
                rx.text(
                    f"{int((current_step / 6) * 100)}% complete",
                    font_size="0.85rem",
                    color="gray",
                ),
                width="100%",
                align_items="start",
                margin_top="1rem",
            ),
            rx.fragment(),
        ),
        
        width="100%",
        align_items="start",
        spacing="4",
    )
