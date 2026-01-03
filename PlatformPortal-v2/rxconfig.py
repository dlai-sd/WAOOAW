import reflex as rx
import os

# Cloud Run production configuration
config = rx.Config(
    app_name="PlatformPortal_v2",
    backend_host="0.0.0.0",
    backend_port=int(os.getenv("PORT", "8080")),
    frontend_port=int(os.getenv("PORT", "8080")),  # Same port as backend for Cloud Run
    env=os.getenv("ENV", "prod"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)