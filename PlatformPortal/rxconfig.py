import reflex as rx
import os

# Disable WebSocket in production (Cloud Run + Load Balancer)
# WebSocket is only needed for hot-reload during development
env = os.getenv("ENV", "development")
connect_error_component = None if env == "production" or env == "staging" else "default"

config = rx.Config(
    app_name="waooaw_portal",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    # Disable WebSocket connection errors in production
    connect_error_component=connect_error_component,
)