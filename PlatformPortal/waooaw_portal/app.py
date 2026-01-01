"""
WAOOAW Platform Portal - Main Application

Professional operational control plane for WAOOAW Platform built with Reflex (Pure Python).
"""

import reflex as rx
from waooaw_portal.pages import login_page, dashboard_page, agents_page
from waooaw_portal.state import AuthState
from waooaw_portal.theme.colors import DARK_THEME


# App configuration
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="cyan",
    ),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap",
        "https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap",
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    ],
)

# Add routes
app.add_page(login_page, route="/login", title="Login | WAOOAW Platform Portal")
app.add_page(
    dashboard_page,
    route="/",
    title="Dashboard | WAOOAW Platform Portal",
    on_load=AuthState.update_activity,
)
app.add_page(
    agents_page,
    route="/agents",
    title="Agents | WAOOAW Platform Portal",
    on_load=AuthState.update_activity,
)

# Compile the app
app.compile()
