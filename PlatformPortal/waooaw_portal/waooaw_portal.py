"""
WAOOAW Platform Portal

Main application entry point with all page routes.
"""

import reflex as rx
from rxconfig import config

# Import working pages
from waooaw_portal.pages.login import login_page
from waooaw_portal.pages.callback import callback_page
from waooaw_portal.pages.dashboard import dashboard_page
# from waooaw_portal.pages.queues import queues_page
# from waooaw_portal.pages.workflows import workflows_page
# from waooaw_portal.pages.factory import factory_page
# from waooaw_portal.pages.servicing import servicing_page
# from waooaw_portal.pages.helpdesk import helpdesk_page


def placeholder_page(title: str) -> rx.Component:
    """Placeholder for pages under development"""
    return rx.container(
        rx.vstack(
            rx.heading(title, size="9"),
            rx.text(f"The {title} page is being updated to work with the latest Reflex version.", size="5", color="gray"),
            rx.link(rx.button("← Back to Dashboard"), href="/"),
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
app.add_page(login_page, route="/login", title="Login - WAOOAW")
app.add_page(callback_page, route="/auth/callback", title="Logging in - WAOOAW")
app.add_page(dashboard_page, route="/dashboard", title="Dashboard - WAOOAW")
app.add_page(dashboard_page, route="/", title="WAOOAW Platform Portal")

