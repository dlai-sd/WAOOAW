"""
WAOOAW Platform Portal

Main application entry point with all page routes.
"""

import reflex as rx
from rxconfig import config

# Import all pages
from waooaw_portal.pages.login import login_page
from waooaw_portal.pages.dashboard import dashboard_page
from waooaw_portal.pages.agents import agents_page
from waooaw_portal.pages.logs import logs_page
from waooaw_portal.pages.alerts import alerts_page
from waooaw_portal.pages.queues import queues_page
from waooaw_portal.pages.workflows import workflows_page
from waooaw_portal.pages.factory import factory_page
from waooaw_portal.pages.servicing import servicing_page
from waooaw_portal.pages.helpdesk import helpdesk_page


# Create app
app = rx.App()

# Add all routes
app.add_page(login_page, route="/login", title="Login - WAOOAW")
app.add_page(dashboard_page, route="/dashboard", title="Dashboard - WAOOAW")
app.add_page(dashboard_page, route="/", title="WAOOAW Platform Portal")  # Default route
app.add_page(agents_page, route="/agents", title="Agents - WAOOAW")
app.add_page(logs_page, route="/logs", title="Logs - WAOOAW")
app.add_page(alerts_page, route="/alerts", title="Alerts - WAOOAW")
app.add_page(queues_page, route="/queues", title="Queues - WAOOAW")
app.add_page(workflows_page, route="/workflows", title="Workflows - WAOOAW")
app.add_page(factory_page, route="/factory", title="Factory - WAOOAW")
app.add_page(servicing_page, route="/servicing", title="Servicing - WAOOAW")
app.add_page(helpdesk_page, route="/helpdesk", title="Helpdesk - WAOOAW")
