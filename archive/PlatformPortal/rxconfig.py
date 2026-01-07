import reflex as rx
import os

# Environment detection
env = os.getenv("ENV", "development")

# Disable WebSocket connection errors in production
# Use "default" to show connection issues, None to hide them
connect_error_component = None if env in ["production", "staging"] else "default"

config = rx.Config(
    app_name="PlatformPortal_v2",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    # Disable WebSocket connection errors in production
    connect_error_component=connect_error_component,
)