import reflex as rx
import os

config = rx.Config(
    app_name="PlatformPortal_v2",
    api_url="http://0.0.0.0:8000",
    frontend_port=3000,
    backend_port=8000,
    deploy_url="https://waooaw-platform-portal-demo-ryvhxvrdna-el.a.run.app",
    env=os.getenv("ENV", "prod"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)