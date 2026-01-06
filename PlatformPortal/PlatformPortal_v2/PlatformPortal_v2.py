"""WAOOAW Platform Portal - Simple Reflex App"""

import reflex as rx
import os


class State(rx.State):
    """Simple minimal state"""
    pass


def get_backend_url() -> str:
    """Get backend URL based on environment"""
    # This will be called during rendering on the server side
    # For now, default to localhost for development
    return "http://localhost:8000"


def index() -> rx.Component:
    """Login page - main entry point"""
    
    # For now, hardcode to localhost
    # In production, this would be determined at runtime
    backend_url = "http://localhost:8000"
    login_url = f"{backend_url}/auth/login?frontend=pp"
    
    return rx.vstack(
        rx.heading(
            "WAOOAW",
            size="9",
            background_image="linear-gradient(135deg, #00f2fe 0%, #667eea 100%)",
            background_clip="text",
            color="transparent",
            font_weight="bold",
        ),
        rx.text("Platform Portal", size="5", color="#a1a1aa"),
        rx.text(
            "Internal operations dashboard",
            size="3",
            color="#71717a",
        ),
        rx.link(
            rx.button(
                "Sign in with Google",
                size="3",
                padding="0.75rem 2rem",
                width="100%",
            ),
            href=login_url,
            is_external=True,
        ),
        rx.badge("CODESPACE", variant="soft"),
        spacing="4",
        align="center",
        justify="center",
        min_height="100vh",
        background="#0a0a0a",
        padding="2rem",
    )

# Create app
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="cyan",
    ),
)

# Add pages
app.add_page(
    index,
    route="/",
    title="WAOOAW Platform Portal - Login",
)
