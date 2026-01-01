"""Pages for WAOOAW Platform Portal"""

from waooaw_portal.pages.login import login_page
from waooaw_portal.pages.dashboard import dashboard_page
from waooaw_portal.pages.agents import agents_page
from waooaw_portal.pages.logs import logs_page
from waooaw_portal.pages.alerts import alerts_page
from waooaw_portal.pages.queues import queues_page
from waooaw_portal.pages.workflows import workflows_page
from waooaw_portal.pages.factory import factory_page
from waooaw_portal.pages.servicing import servicing_page

__all__ = ["login_page", "dashboard_page", "agents_page", "logs_page", "alerts_page", "queues_page", "workflows_page", "factory_page", "servicing_page"]
