"""
Help Desk Page - Story 5.1.12
Real-time incident tracking and automated diagnostics
"""

import reflex as rx
from ..state.helpdesk_state import HelpDeskState
from ..state.theme_state import ThemeState
from ..state.auth_state import AuthState
from ..components.helpdesk import incident_card, diagnostic_panel, resolution_workflow, sla_tracker


def helpdesk_page() -> rx.Component:
    """Main help desk page with incident tracking"""
    return rx.box(
        rx.vstack(
            # Navigation Header
            rx.hstack(
                rx.text(
                    "Help Desk",
                    font_size="2rem",
                    font_weight="700",
                    color=ThemeState.theme["text_primary"],
                ),
                rx.spacer(),
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
                rx.link(
                    rx.button(
                        rx.icon("package", size=18),
                        "Agent Factory",
                        size="3",
                        variant="outline",
                        color_scheme="green",
                    ),
                    href="/factory",
                ),
                rx.link(
                    rx.button(
                        rx.icon("wrench", size=18),
                        "Servicing",
                        size="3",
                        variant="outline",
                        color_scheme="purple",
                    ),
                    href="/servicing",
                ),
                # Theme Selector
                rx.button(
                    rx.icon(ThemeState.theme_icon, size=18),
                    ThemeState.theme_label,
                    size="3",
                    variant="ghost",
                    on_click=ThemeState.toggle_theme,
                ),
                # Logout Button
                rx.button(
                    rx.icon("log-out", size=18),
                    "Logout",
                    size="3",
                    variant="ghost",
                    color_scheme="red",
                    on_click=AuthState.logout,
                ),
                width="100%",
                align_items="center",
                margin_bottom="2rem",
            ),
            
            # Header with statistics
            rx.hstack(
                rx.heading("Incident Dashboard", size="6", weight="bold", color=ThemeState.theme["text_primary"]),
                rx.spacer(),
                rx.hstack(
                    rx.vstack(
                        rx.text(HelpDeskState.total_incidents, font_size="1.5rem", weight="bold", color=ThemeState.theme["accent_cyan"]),
                        rx.text("Total", font_size="0.8rem", color=ThemeState.theme["text_tertiary"]),
                        align_items="center",
                    ),
                    rx.vstack(
                        rx.text(HelpDeskState.open_incidents, font_size="1.5rem", weight="bold", color=ThemeState.theme["warning"]),
                        rx.text("Open", font_size="0.8rem", color=ThemeState.theme["text_tertiary"]),
                        align_items="center",
                    ),
                    rx.vstack(
                        rx.text(HelpDeskState.critical_incidents, font_size="1.5rem", weight="bold", color=ThemeState.theme["error"]),
                        rx.text("Critical", font_size="0.8rem", color=ThemeState.theme["text_tertiary"]),
                        align_items="center",
                    ),
                    rx.vstack(
                        rx.text(f"{HelpDeskState.avg_resolution_time_min:.0f}m", font_size="1.5rem", weight="bold", color=ThemeState.theme["success"]),
                        rx.text("Avg Resolution", font_size="0.8rem", color=ThemeState.theme["text_tertiary"]),
                        align_items="center",
                    ),
                    rx.vstack(
                        rx.text(f"{HelpDeskState.sla_compliance_pct:.0f}%", font_size="1.5rem", weight="bold", color=ThemeState.theme["accent_cyan"]),
                        rx.text("SLA Compliance", font_size="0.8rem", color=ThemeState.theme["text_tertiary"]),
                        align_items="center",
                    ),
                    spacing="8",
                ),
                justify="between",
                align_items="center",
                width="100%",
                padding="1.5rem",
                background=ThemeState.theme["bg_secondary"],
                border=f"1px solid {ThemeState.theme['bg_tertiary']}",
                border_radius="1rem",
                margin_bottom="1.5rem",
            ),
            
            # Filters and search
            rx.hstack(
                rx.input(
                    placeholder="Search incidents...",
                    value=HelpDeskState.search_query,
                    on_change=HelpDeskState.set_search_query,
                    width="300px",
                ),
                rx.select(
                    ["all", "critical", "high", "medium", "low"],
                    value=HelpDeskState.filter_severity,
                    on_change=HelpDeskState.set_filter_severity,
                    placeholder="Severity",
                ),
                rx.select(
                    ["all", "open", "investigating", "in_progress", "resolved", "closed"],
                    value=HelpDeskState.filter_status,
                    on_change=HelpDeskState.set_filter_status,
                    placeholder="Status",
                ),
                rx.select(
                    ["all", "performance", "availability", "error", "security", "configuration"],
                    value=HelpDeskState.filter_category,
                    on_change=HelpDeskState.set_filter_category,
                    placeholder="Category",
                ),
                rx.spacer(),
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.button(
                            rx.icon("plus", size=18),
                            "New Incident",
                            color_scheme="cyan",
                        ),
                    ),
                    rx.dialog.content(
                        rx.dialog.title("Create New Incident"),
                        rx.dialog.description("Report a new incident for tracking and resolution"),
                        rx.vstack(
                            rx.input(
                                placeholder="Incident Title",
                                value=HelpDeskState.new_incident_title,
                                on_change=HelpDeskState.set_new_incident_title,
                                width="100%",
                            ),
                            rx.text_area(
                                placeholder="Description...",
                                value=HelpDeskState.new_incident_description,
                                on_change=HelpDeskState.set_new_incident_description,
                                width="100%",
                                rows="4",
                            ),
                            rx.select(
                                ["critical", "high", "medium", "low"],
                                value=HelpDeskState.new_incident_severity,
                                on_change=HelpDeskState.set_new_incident_severity,
                                placeholder="Severity",
                                width="100%",
                            ),
                            rx.select(
                                ["performance", "availability", "error", "security", "configuration"],
                                value=HelpDeskState.new_incident_category,
                                on_change=HelpDeskState.set_new_incident_category,
                                placeholder="Category",
                                width="100%",
                            ),
                            rx.input(
                                placeholder="Affected Agent ID",
                                value=HelpDeskState.new_incident_agent,
                                on_change=HelpDeskState.set_new_incident_agent,
                                width="100%",
                            ),
                            spacing="4",
                            width="100%",
                        ),
                        rx.dialog.close(
                            rx.button(
                                "Create Incident",
                                on_click=HelpDeskState.create_incident,
                                color_scheme="cyan",
                                margin_top="1rem",
                            ),
                        ),
                        max_width="500px",
                    ),
                ),
                spacing="4",
                width="100%",
                margin_bottom="1rem",
            ),
            
            # Main content area
            rx.cond(
                HelpDeskState.selected_incident != None,
                # Incident details view
                rx.hstack(
                    # Left panel: Incident list (30%)
                    rx.vstack(
                        rx.heading("Incidents", size="5", weight="bold"),
                        rx.button(
                            "← Back to All",
                            on_click=HelpDeskState.set_selected_incident(None),
                            variant="ghost",
                            size="2",
                            margin_bottom="0.5rem",
                        ),
                        rx.vstack(
                            rx.foreach(
                                HelpDeskState.filtered_incidents,
                                lambda incident: incident_card(incident, compact=True),
                            ),
                            width="100%",
                            spacing="2",
                            max_height="calc(100vh - 300px)",
                            overflow_y="auto",
                        ),
                        width="30%",
                        align_items="start",
                        spacing="4",
                    ),
                    
                    # Right panel: Incident details (70%)
                    rx.vstack(
                        # Incident header
                        rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.heading(
                                        HelpDeskState.selected_incident_details.title,
                                        size="6",
                                        weight="bold",
                                    ),
                                    rx.spacer(),
                                    rx.badge(
                                        HelpDeskState.selected_incident_details.severity.upper(),
                                        color_scheme=rx.cond(
                                            HelpDeskState.selected_incident_details.severity == "critical",
                                            "red",
                                            rx.cond(
                                                HelpDeskState.selected_incident_details.severity == "high",
                                                "orange",
                                                rx.cond(
                                                    HelpDeskState.selected_incident_details.severity == "medium",
                                                    "yellow",
                                                    "gray",
                                                ),
                                            ),
                                        ),
                                        font_size="0.9rem",
                                    ),
                                    rx.badge(
                                        HelpDeskState.selected_incident_details.status.replace("_", " ").upper(),
                                        color_scheme=rx.cond(
                                            HelpDeskState.selected_incident_details.status == "resolved",
                                            "green",
                                            rx.cond(
                                                HelpDeskState.selected_incident_details.status == "closed",
                                                "gray",
                                                "cyan",
                                            ),
                                        ),
                                        font_size="0.9rem",
                                    ),
                                    justify="between",
                                    align_items="center",
                                    width="100%",
                                ),
                                rx.text(
                                    HelpDeskState.selected_incident_details.description,
                                    color="gray",
                                    margin_top="0.5rem",
                                ),
                                rx.divider(margin="1rem 0"),
                                rx.grid(
                                    rx.vstack(
                                        rx.text("Incident ID:", weight="bold", font_size="0.85rem"),
                                        rx.text(HelpDeskState.selected_incident_details.incident_id, font_size="0.85rem"),
                                        align_items="start",
                                    ),
                                    rx.vstack(
                                        rx.text("Category:", weight="bold", font_size="0.85rem"),
                                        rx.text(HelpDeskState.selected_incident_details.category, font_size="0.85rem"),
                                        align_items="start",
                                    ),
                                    rx.vstack(
                                        rx.text("Affected Agent:", weight="bold", font_size="0.85rem"),
                                        rx.text(HelpDeskState.selected_incident_details.affected_agent, font_size="0.85rem"),
                                        align_items="start",
                                    ),
                                    rx.vstack(
                                        rx.text("Assigned To:", weight="bold", font_size="0.85rem"),
                                        rx.text(
                                            rx.cond(
                                                HelpDeskState.selected_incident_details.assigned_to != None,
                                                HelpDeskState.selected_incident_details.assigned_to,
                                                "Unassigned",
                                            ),
                                            font_size="0.85rem",
                                        ),
                                        align_items="start",
                                    ),
                                    rx.vstack(
                                        rx.text("Created:", weight="bold", font_size="0.85rem"),
                                        rx.text(HelpDeskState.selected_incident_details.created_at, font_size="0.85rem"),
                                        align_items="start",
                                    ),
                                    rx.vstack(
                                        rx.text("SLA Deadline:", weight="bold", font_size="0.85rem"),
                                        rx.text(HelpDeskState.selected_incident_details.sla_deadline, font_size="0.85rem"),
                                        align_items="start",
                                    ),
                                    columns="3",
                                    spacing="4",
                                    width="100%",
                                ),
                                rx.hstack(
                                    rx.button(
                                        "Run Diagnostics",
                                        on_click=HelpDeskState.run_diagnostics(HelpDeskState.selected_incident),
                                        color_scheme="cyan",
                                        size="2",
                                    ),
                                    rx.button(
                                        "Assign to Me",
                                        on_click=HelpDeskState.assign_incident(HelpDeskState.selected_incident, "admin@waooaw.com"),
                                        variant="outline",
                                        size="2",
                                    ),
                                    rx.menu.root(
                                        rx.menu.trigger(
                                            rx.button("Update Status", variant="outline", size="2"),
                                        ),
                                        rx.menu.content(
                                            rx.menu.item("Open", on_click=HelpDeskState.update_incident_status(HelpDeskState.selected_incident, "open")),
                                            rx.menu.item("Investigating", on_click=HelpDeskState.update_incident_status(HelpDeskState.selected_incident, "investigating")),
                                            rx.menu.item("In Progress", on_click=HelpDeskState.update_incident_status(HelpDeskState.selected_incident, "in_progress")),
                                            rx.menu.separator(),
                                            rx.menu.item("Resolved", on_click=HelpDeskState.update_incident_status(HelpDeskState.selected_incident, "resolved")),
                                            rx.menu.item("Closed", on_click=HelpDeskState.update_incident_status(HelpDeskState.selected_incident, "closed")),
                                        ),
                                    ),
                                    spacing="4",
                                    margin_top="1rem",
                                ),
                                align_items="start",
                                spacing="2",
                            ),
                            padding="1.5rem",
                        ),
                        
                        # SLA Tracker
                        sla_tracker(HelpDeskState.selected_incident_details),
                        
                        # Tabs for diagnostics and resolution
                        rx.tabs.root(
                            rx.tabs.list(
                                rx.tabs.trigger("Diagnostics", value="diagnostics"),
                                rx.tabs.trigger("Resolution Workflow", value="resolution"),
                                rx.tabs.trigger("Knowledge Base", value="kb"),
                            ),
                            rx.tabs.content(
                                diagnostic_panel(HelpDeskState.diagnostic_results, HelpDeskState.is_running_diagnostics),
                                value="diagnostics",
                            ),
                            rx.tabs.content(
                                resolution_workflow(HelpDeskState.resolution_steps, HelpDeskState.current_resolution_step),
                                value="resolution",
                            ),
                            rx.tabs.content(
                                rx.vstack(
                                    rx.heading("Relevant Knowledge Base Articles", size="5", weight="bold"),
                                    rx.vstack(
                                        rx.foreach(
                                            HelpDeskState.knowledge_articles,
                                            lambda article: rx.card(
                                                rx.vstack(
                                                    rx.heading(article.title, size="4", weight="bold"),
                                                    rx.text(article.summary, color="gray", font_size="0.9rem"),
                                                    rx.hstack(
                                                        rx.badge(article.category, color_scheme="blue"),
                                                        rx.text(f"👁 {article.views} views", font_size="0.85rem", color="gray"),
                                                        rx.text(f"👍 {article.helpful_count} helpful", font_size="0.85rem", color="gray"),
                                                    ),
                                                    align_items="start",
                                                    spacing="2",
                                                ),
                                                padding="1rem",
                                                margin_bottom="0.5rem",
                                                cursor="pointer",
                                                _hover={"box_shadow": "0 0 15px rgba(0, 242, 254, 0.3)"},
                                            ),
                                        ),
                                        width="100%",
                                        spacing="2",
                                    ),
                                    width="100%",
                                    align_items="start",
                                    spacing="4",
                                ),
                                value="kb",
                            ),
                            default_value="diagnostics",
                            width="100%",
                        ),
                        
                        width="70%",
                        align_items="start",
                        spacing="4",
                    ),
                    
                    spacing="8",
                    align_items="start",
                    width="100%",
                ),
                
                # Incident list view
                rx.vstack(
                    rx.heading(
                        f"Active Incidents ({HelpDeskState.filtered_incidents_count})",
                        size="5",
                        weight="bold",
                        margin_bottom="1rem",
                    ),
                    rx.vstack(
                        rx.foreach(
                            HelpDeskState.filtered_incidents,
                            lambda incident: incident_card(incident, compact=False),
                        ),
                        width="100%",
                        spacing="4",
                    ),
                    width="100%",
                    align_items="start",
                ),
            ),
            
            width="100%",
            spacing="4",
        ),
        padding="2rem",
        max_width="1600px",
        background=ThemeState.theme["bg_primary"],
        min_height="100vh",
        on_mount=lambda: [
            HelpDeskState.load_incidents(),
            HelpDeskState.load_knowledge_articles(),
        ],
    )
