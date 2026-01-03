import reflex as rx
import os

# Cloud Run production configuration
config = rx.Config(
    app_name="PlatformPortal_v2",
    backend_host="0.0.0.0",
    backend_port=8080,  # Cloud Run standard port
    env=os.getenv("ENV", "prod"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)