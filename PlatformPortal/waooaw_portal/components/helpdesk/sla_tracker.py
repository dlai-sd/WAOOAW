"""SLA tracker component"""

import reflex as rx
from ...state.helpdesk_state import Incident


def sla_tracker(incident: Incident) -> rx.Component:
    """Render SLA compliance tracker"""
    
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("SLA Tracker", size="4", weight="bold"),
                rx.badge(
                    incident.sla_status.replace("_", " ").upper(),
                    color_scheme=rx.cond(
                        incident.sla_status == "on_track",
                        "green",
                        rx.cond(
                            incident.sla_status == "at_risk",
                            "yellow",
                            "red",
                        ),
                    ),
                    font_size="0.9rem",
                ),
                justify="between",
                width="100%",
            ),
            
            rx.grid(
                rx.vstack(
                    rx.text("Target Resolution Time:", font_size="0.85rem", color="gray"),
                    rx.text(
                        rx.cond(
                            incident.severity == "critical",
                            "1 hour",
                            rx.cond(
                                incident.severity == "high",
                                "4 hours",
                                rx.cond(
                                    incident.severity == "medium",
                                    "8 hours",
                                    "24 hours",
                                ),
                            ),
                        ),
                        font_size="1.1rem",
                        weight="bold",
                    ),
                    align_items="start",
                ),
                rx.vstack(
                    rx.text("SLA Deadline:", font_size="0.85rem", color="gray"),
                    rx.text(
                        incident.sla_deadline,
                        font_size="1.1rem",
                        weight="bold",
                    ),
                    align_items="start",
                ),
                rx.vstack(
                    rx.text("Current Status:", font_size="0.85rem", color="gray"),
                    rx.hstack(
                        rx.icon(
                            rx.cond(
                                incident.sla_status == "on_track",
                                "check-circle",
                                rx.cond(
                                    incident.sla_status == "at_risk",
                                    "alert-triangle",
                                    "x-circle",
                                ),
                            ),
                            size=20,
                            color=rx.cond(
                                incident.sla_status == "on_track",
                                "green",
                                rx.cond(
                                    incident.sla_status == "at_risk",
                                    "yellow",
                                    "red",
                                ),
                            ),
                        ),
                        rx.text(
                            rx.cond(
                                incident.sla_status == "on_track",
                                "On Track",
                                rx.cond(
                                    incident.sla_status == "at_risk",
                                    "At Risk",
                                    "Breached",
                                ),
                            ),
                            font_size="1.1rem",
                            weight="bold",
                            color=rx.cond(
                                incident.sla_status == "on_track",
                                "green",
                                rx.cond(
                                    incident.sla_status == "at_risk",
                                    "yellow",
                                    "red",
                                ),
                            ),
                        ),
                    ),
                    align_items="start",
                ),
                columns="3",
                spacing="8",
                width="100%",
            ),
            
            rx.cond(
                incident.time_to_resolve_min.is_some(),
                rx.callout(
                    rx.icon("check", size=20),
                    rx.text(f"Incident resolved in {incident.time_to_resolve_min} minutes"),
                    color_scheme="green",
                    margin_top="1rem",
                ),
                rx.fragment(),
            ),
            
            align_items="start",
            spacing="4",
            width="100%",
        ),
        padding="1.5rem",
    )
