"""Diagnostic panel component"""

import reflex as rx
from typing import List
from ...state.helpdesk_state import DiagnosticResult


def diagnostic_panel(results: List[DiagnosticResult], is_running: bool) -> rx.Component:
    """Render automated diagnostic results"""
    
    return rx.vstack(
        rx.heading("Automated Diagnostics", size="5", weight="bold"),
        
        rx.cond(
            is_running,
            rx.hstack(
                rx.spinner(size="3"),
                rx.text("Running diagnostic checks...", color="cyan", font_weight="bold"),
                margin="2rem 0",
            ),
            rx.cond(
                rx.State.length(results) > 0,
                rx.vstack(
                    rx.foreach(
                        results,
                        lambda result: rx.card(
                            rx.hstack(
                                rx.cond(
                                    result.status == "pass",
                                    rx.icon("check-circle", size=28, color="green"),
                                    rx.cond(
                                        result.status == "fail",
                                        rx.icon("x-circle", size=28, color="red"),
                                        rx.cond(
                                            result.status == "warning",
                                            rx.icon("alert-triangle", size=28, color="yellow"),
                                            rx.icon("info", size=28, color="blue"),
                                        ),
                                    ),
                                ),
                                
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(result.check_name, weight="bold", font_size="1.1rem"),
                                        rx.badge(
                                            result.status.upper(),
                                            color_scheme=rx.cond(
                                                result.status == "pass",
                                                "green",
                                                rx.cond(
                                                    result.status == "fail",
                                                    "red",
                                                    rx.cond(
                                                        result.status == "warning",
                                                        "yellow",
                                                        "blue",
                                                    ),
                                                ),
                                            ),
                                        ),
                                        rx.spacer(),
                                        rx.text(result.timestamp, font_size="0.85rem", color="gray"),
                                        width="100%",
                                    ),
                                    rx.text(result.message, font_size="0.95rem", margin_top="0.25rem"),
                                    rx.text(result.details, color="gray", font_size="0.9rem", margin_top="0.5rem"),
                                    
                                    rx.cond(
                                        result.recommendation.is_some(),
                                        rx.callout(
                                            rx.icon("lightbulb", size=18),
                                            rx.text(result.recommendation),
                                            color_scheme="blue",
                                            margin_top="0.75rem",
                                        ),
                                        rx.fragment(),
                                    ),
                                    
                                    align_items="start",
                                    spacing="0.25rem",
                                    flex="1",
                                ),
                                
                                spacing="1rem",
                                align_items="start",
                                width="100%",
                            ),
                            padding="1.5rem",
                            margin_bottom="1rem",
                            border_left=rx.cond(
                                result.status == "pass",
                                "4px solid var(--green-9)",
                                rx.cond(
                                    result.status == "fail",
                                    "4px solid var(--red-9)",
                                    rx.cond(
                                        result.status == "warning",
                                        "4px solid var(--yellow-9)",
                                        "4px solid var(--blue-9)",
                                    ),
                                ),
                            ),
                        ),
                    ),
                    width="100%",
                    spacing="1rem",
                ),
                rx.callout(
                    rx.icon("info", size=20),
                    rx.text("Click 'Run Diagnostics' to execute automated checks for this incident."),
                    color_scheme="blue",
                    margin="2rem 0",
                ),
            ),
        ),
        
        width="100%",
        align_items="start",
        spacing="1rem",
    )
