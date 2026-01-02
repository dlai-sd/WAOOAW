"""Incident card component"""

import reflex as rx
from ...state.helpdesk_state import Incident, HelpDeskState


def incident_card(incident: Incident, compact: bool = False) -> rx.Component:
    """Render incident card"""
    
    if compact:
        # Compact view for sidebar
        return rx.card(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        incident.incident_id,
                        font_size="0.75rem",
                        color="gray",
                        font_family="monospace",
                    ),
                    rx.badge(
                        incident.severity[0].upper(),
                        color_scheme=rx.cond(
                            incident.severity == "critical",
                            "red",
                            rx.cond(
                                incident.severity == "high",
                                "orange",
                                "yellow",
                            ),
                        ),
                        size="1",
                    ),
                    justify="between",
                    width="100%",
                ),
                rx.text(
                    incident.title,
                    font_size="0.9rem",
                    font_weight="bold",
                    white_space="nowrap",
                    overflow="hidden",
                    text_overflow="ellipsis",
                    width="100%",
                ),
                rx.hstack(
                    rx.icon(
                        rx.cond(
                            incident.status == "open",
                            "circle",
                            rx.cond(
                                incident.status == "investigating",
                                "search",
                                rx.cond(
                                    incident.status == "in_progress",
                                    "loader",
                                    rx.cond(
                                        incident.status == "resolved",
                                        "check-circle",
                                        "x-circle",
                                    ),
                                ),
                            ),
                        ),
                        size=14,
                        color=rx.cond(
                            incident.status == "resolved",
                            "green",
                            rx.cond(
                                incident.status == "closed",
                                "gray",
                                "cyan",
                            ),
                        ),
                    ),
                    rx.text(
                        incident.category,
                        font_size="0.75rem",
                        color="gray",
                    ),
                    spacing="2",
                ),
                align_items="start",
                spacing="2",
                width="100%",
            ),
            padding="0.75rem",
            cursor="pointer",
            on_click=HelpDeskState.select_incident(incident.incident_id),
            border=rx.cond(
                HelpDeskState.selected_incident == incident.incident_id,
                "2px solid var(--cyan-9)",
                "1px solid var(--gray-6)",
            ),
            _hover={"border_color": "var(--cyan-9)"},
        )
    
    # Full view for main list
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            incident.incident_id,
                            font_size="0.85rem",
                            color="gray",
                            font_family="monospace",
                        ),
                        rx.badge(
                            incident.severity.upper(),
                            color_scheme=rx.cond(
                                incident.severity == "critical",
                                "red",
                                rx.cond(
                                    incident.severity == "high",
                                    "orange",
                                    rx.cond(
                                        incident.severity == "medium",
                                        "yellow",
                                        "gray",
                                    ),
                                ),
                            ),
                        ),
                        rx.badge(
                            incident.status.replace("_", " ").upper(),
                            color_scheme=rx.cond(
                                incident.status == "resolved",
                                "green",
                                rx.cond(
                                    incident.status == "closed",
                                    "gray",
                                    "cyan",
                                ),
                            ),
                        ),
                        rx.badge(incident.category, color_scheme="blue"),
                    ),
                    rx.heading(incident.title, size="4", weight="bold", margin_top="0.5rem"),
                    rx.text(incident.description, color="gray", font_size="0.9rem", margin_top="0.25rem"),
                    align_items="start",
                    spacing="0.25rem",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text("SLA Status:", font_size="0.75rem", color="gray"),
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
                    ),
                    align_items="end",
                ),
                justify="between",
                align_items="start",
                width="100%",
            ),
            rx.divider(margin="0.75rem 0"),
            rx.hstack(
                rx.hstack(
                    rx.icon("user", size=14, color="gray"),
                    rx.text(
                        rx.cond(
                            incident.assigned_to.is_some(),
                            incident.assigned_to,
                            "Unassigned",
                        ),
                        font_size="0.85rem",
                        color="gray",
                    ),
                ),
                rx.hstack(
                    rx.icon("server", size=14, color="gray"),
                    rx.text(incident.affected_agent, font_size="0.85rem", color="gray"),
                ),
                rx.hstack(
                    rx.icon("clock", size=14, color="gray"),
                    rx.text(incident.created_at, font_size="0.85rem", color="gray"),
                ),
                rx.spacer(),
                rx.button(
                    "View Details",
                    on_click=HelpDeskState.select_incident(incident.incident_id),
                    size="2",
                    variant="outline",
                ),
                justify="between",
                align_items="center",
                width="100%",
            ),
            align_items="start",
            spacing="2",
            width="100%",
        ),
        padding="1.5rem",
        cursor="pointer",
        on_click=HelpDeskState.select_incident(incident.incident_id),
        _hover={"box_shadow": "0 0 20px rgba(0, 242, 254, 0.3)"},
    )
