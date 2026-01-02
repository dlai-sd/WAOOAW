"""Health check monitor component"""

import reflex as rx
from ...state.servicing_state import ServicingState


def health_monitor() -> rx.Component:
    """Render health check results"""
    
    return rx.vstack(
        # Run health checks button
        rx.cond(
            rx.State.length(ServicingState.health_checks) == 0,
            rx.button(
                "Run Health Checks",
                on_click=ServicingState.run_health_checks,
                color_scheme="cyan",
                size="3",
            ),
            rx.vstack(
                # Overall health status
                rx.card(
                    rx.hstack(
                        rx.text("Overall Health:", weight="bold", font_size="1.1rem"),
                        rx.badge(
                            ServicingState.health_status.upper(),
                            color_scheme=rx.cond(
                                ServicingState.health_status == "healthy",
                                "green",
                                rx.cond(
                                    ServicingState.health_status == "degraded",
                                    "yellow",
                                    "red",
                                ),
                            ),
                            font_size="1rem",
                        ),
                        rx.button(
                            "Re-run Checks",
                            on_click=ServicingState.run_health_checks,
                            variant="outline",
                            size="2",
                        ),
                        justify="between",
                        align_items="center",
                        width="100%",
                    ),
                    padding="1rem",
                    width="100%",
                ),
                
                # Individual health checks
                rx.vstack(
                    rx.foreach(
                        ServicingState.health_checks,
                        lambda check: rx.card(
                            rx.hstack(
                                rx.cond(
                                    check.status == "pass",
                                    rx.icon("check-circle", size=24, color="green"),
                                    rx.cond(
                                        check.status == "warning",
                                        rx.icon("alert-triangle", size=24, color="yellow"),
                                        rx.icon("x-circle", size=24, color="red"),
                                    ),
                                ),
                                
                                rx.vstack(
                                    rx.text(check.name, weight="bold", font_size="1rem"),
                                    rx.text(check.message, color="gray", font_size="0.9rem"),
                                    rx.hstack(
                                        rx.cond(
                                            check.response_time_ms.is_some(),
                                            rx.text(
                                                f"Response: {check.response_time_ms}ms",
                                                color="gray",
                                                font_size="0.85rem",
                                            ),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            check.error_rate.is_some() & (check.error_rate > 0),
                                            rx.text(
                                                f"Errors: {check.error_rate}%",
                                                color="red",
                                                font_size="0.85rem",
                                            ),
                                            rx.fragment(),
                                        ),
                                        rx.cond(
                                            check.latency_increase.is_some() & (check.latency_increase > 0),
                                            rx.text(
                                                f"Latency +{check.latency_increase}%",
                                                color="yellow",
                                                font_size="0.85rem",
                                            ),
                                            rx.fragment(),
                                        ),
                                    ),
                                    align_items="start",
                                    spacing="0.25rem",
                                ),
                                
                                rx.spacer(),
                                
                                rx.text(check.timestamp, color="gray", font_size="0.85rem"),
                                
                                spacing="4",
                                align_items="center",
                                width="100%",
                            ),
                            padding="1rem",
                            margin_bottom="0.5rem",
                            border_left=rx.cond(
                                check.status == "pass",
                                "4px solid var(--green-9)",
                                rx.cond(
                                    check.status == "warning",
                                    "4px solid var(--yellow-9)",
                                    "4px solid var(--red-9)",
                                ),
                            ),
                        ),
                    ),
                    width="100%",
                    spacing="2",
                    margin_top="1rem",
                ),
                
                width="100%",
                align_items="start",
            ),
        ),
        
        width="100%",
        align_items="start",
        spacing="4",
    )
