"""Login Page - Google OAuth"""
import reflex as rx
import os
from waooaw_portal.theme.colors import DARK_THEME

# Get backend URL from environment or default
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
CODESPACE_NAME = os.getenv("CODESPACE_NAME", "")

# If in Codespaces, use the proxied URL
if CODESPACE_NAME:
    BACKEND_URL = f"https://{CODESPACE_NAME}-8000.app.github.dev"

def login_page() -> rx.Component:
    """
    Login page with Google OAuth.
    
    This is the FROZEN login page - use consistently, do not recreate.
    """
    return rx.center(
        rx.card(
            rx.vstack(
                # Logo/Brand
                rx.heading("WAOOAW", size="9", color=DARK_THEME["accent_cyan"]),
                rx.text("Platform Portal", size="4", color=DARK_THEME["text_tertiary"], margin_bottom="1rem"),
                
                # Tagline
                rx.text(
                    "Agents Earn Your Business",
                    size="3",
                    color=DARK_THEME["accent_purple"],
                    font_weight="500",
                    margin_bottom="2rem",
                ),
                
                # OAuth Login Button
                rx.link(
                    rx.button(
                        rx.hstack(
                            rx.icon("log-in", size=20),
                            rx.text("Sign in with Google", size="3"),
                            spacing="2",
                        ),
                        size="3",
                        variant="solid",
                        color_scheme="blue",
                    ),
                    href=f"{BACKEND_URL}/auth/login",
                    is_external=False,
                ),
                
                # Info text
                rx.text(
                    "Secure authentication via Google OAuth",
                    size="1",
                    color=DARK_THEME["text_tertiary"],
                    margin_top="1rem",
                ),
                
                spacing="4",
                align="center",
                padding="2rem",
            ),
            max_width="400px",
        ),
        min_height="100vh",
        background=DARK_THEME["bg_primary"],
    )

