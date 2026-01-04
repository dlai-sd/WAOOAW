"""
WAOOAW Platform Portal - Simplified Working Version

This is a minimal working version while we fix the full portal.
"""

import reflex as rx
from rxconfig import config


class PortalState(rx.State):
    """Simple portal state"""
    pass


def index_page() -> rx.Component:
    """Main portal landing page"""
    return rx.container(
        rx.vstack(
            # Header
            rx.heading("WAOOAW Platform Portal", size="9", margin_bottom="4"),
            rx.text(
                "Welcome to the WAOOAW AI Agent Platform Operations Portal",
                size="5",
                color="gray",
                margin_bottom="8",
            ),
            
            # Status Cards
            rx.grid(
                rx.card(
                    rx.vstack(
                        rx.heading("14", size="8"),
                        rx.text("Total Agents"),
                        spacing="2",
                        align="center",
                    ),
                ),
                rx.card(
                    rx.vstack(
                        rx.heading("245", size="8"),
                        rx.text("Active Tasks"),
                        spacing="2",
                        align="center",
                    ),
                ),
                rx.card(
                    rx.vstack(
                        rx.heading("12", size="8"),
                        rx.text("Queue Pending"),
                        spacing="2",
                        align="center",
                    ),
                ),
                rx.card(
                    rx.vstack(
                        rx.heading("0.2%", size="8"),
                        rx.text("Error Rate"),
                        spacing="2",
                        align="center",
                    ),
                ),
                columns="4",
                spacing="4",
                width="100%",
            ),
            
            # Quick Links
            rx.heading("Quick Access", size="6", margin_top="8", margin_bottom="4"),
            rx.grid(
                rx.link(
                    rx.card(
                        rx.vstack(
                            rx.icon("users", size=32),
                            rx.text("Agents", size="4", weight="bold"),
                            spacing="2",
                            align="center",
                        ),
                    ),
                    href="/agents",
                ),
                rx.link(
                    rx.card(
                        rx.vstack(
                            rx.icon("file_text", size=32),
                            rx.text("Logs", size="4", weight="bold"),
                            spacing="2",
                            align="center",
                        ),
                    ),
                    href="/logs",
                ),
                rx.link(
                    rx.card(
                        rx.vstack(
                            rx.icon("bell", size=32),
                            rx.text("Alerts", size="4", weight="bold"),
                            spacing="2",
                            align="center",
                        ),
                    ),
                    href="/alerts",
                ),
                rx.link(
                    rx.card(
                        rx.vstack(
                            rx.icon("list", size=32),
                            rx.text("Queues", size="4", weight="bold"),
                            spacing="2",
                            align="center",
                        ),
                    ),
                    href="/queues",
                ),
                columns="4",
                spacing="4",
                width="100%",
            ),
            
            spacing="4",
            padding="8",
            max_width="1200px",
        ),
    )


def placeholder_page(title: str) -> rx.Component:
    """Placeholder page for other routes"""
    return rx.container(
        rx.vstack(
            rx.heading(title, size="9"),
            rx.text(f"The {title} page is under development.", size="5", color="gray"),
            rx.link(
                rx.button("← Back to Dashboard"),
                href="/",
            ),
            spacing="4",
            padding="8",
            align="center",
            min_height="100vh",
            justify="center",
        ),
    )


# Create app
app = rx.App()

# Add routes
app.add_page(index_page, route="/", title="WAOOAW Platform Portal")
app.add_page(lambda: placeholder_page("Agents"), route="/agents", title="Agents - WAOOAW")
app.add_page(lambda: placeholder_page("Logs"), route="/logs", title="Logs - WAOOAW")
app.add_page(lambda: placeholder_page("Alerts"), route="/alerts", title="Alerts - WAOOAW")
app.add_page(lambda: placeholder_page("Queues"), route="/queues", title="Queues - WAOOAW")
