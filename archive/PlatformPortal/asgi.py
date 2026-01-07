"""
ASGI application for Gunicorn deployment.
This pre-compiles the Reflex app and exposes the ASGI application.
"""
from PlatformPortal_v2.PlatformPortal_v2 import app as reflex_app

# Compile and get the ASGI application
# This happens once at import time, not on every request
application = reflex_app()

# Alias for Gunicorn
app = application
