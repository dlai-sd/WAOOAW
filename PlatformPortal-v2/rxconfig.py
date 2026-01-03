import reflex as rx
import os

# In production (Cloud Run), frontend and backend are served from same URL
# Don't hardcode api_url - let Reflex auto-detect from browser origin
config = rx.Config(
    app_name="PlatformPortal_v2",
    backend_host="0.0.0.0",  # Bind to all interfaces (Cloud Run requirement)
    backend_port=8000,
    env=os.getenv("ENV", "prod"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)