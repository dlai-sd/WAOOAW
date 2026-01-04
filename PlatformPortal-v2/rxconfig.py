import reflex as rx
import os

# Environment-specific configuration
# Codespace: backend on 3000, frontend on 3001
# Production (Cloud Run): both on same PORT env var
is_codespace = "CODESPACE_NAME" in os.environ

if is_codespace:
    backend_port = 3000
    frontend_port = 3001
else:
    backend_port = int(os.getenv("PORT", "8080"))
    frontend_port = int(os.getenv("PORT", "8080"))

config = rx.Config(
    app_name="PlatformPortal_v2",
    backend_host="0.0.0.0",
    backend_port=backend_port,
    frontend_port=frontend_port,
    env=os.getenv("ENV", "prod"),
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)