"""
Login Page

Google OAuth2 authentication page with WAOOAW branding.
"""

import reflex as rx
from waooaw_portal.state.auth_state import AuthState
from waooaw_portal.theme.colors import DARK_THEME, LIGHT_THEME


def login_page() -> rx.Component:
    """
    Login page with Google OAuth2.
    
    Features:
    - WAOOAW branding
    - Google Sign-In button
    - Professional dark theme
    - Loading states
    - Error handling
    """
    return rx.box(
        # Background gradient
        rx.box(
            width="100%",
            height="100vh",
            background=f"linear-gradient(135deg, {DARK_THEME['bg_black']}, {DARK_THEME['bg_gray_900']})",
            position="relative",
        ),
        # Login card (centered)
        rx.center(
            rx.card(
                # WAOOAW Logo
                rx.center(
                    rx.image(
                        src="/Waooaw-Logo.png",
                        width="120px",
                        height="auto",
                        alt="WAOOAW Logo",
                        margin_bottom="2rem",
                    ),
                ),
                # Title
                rx.heading(
                    "Platform Operations Portal",
                    size="8",
                    text_align="center",
                    color=DARK_THEME["text_white"],
                    margin_bottom="0.5rem",
                ),
                rx.text(
                    "Manage your AI agents and platform infrastructure",
                    size="3",
                    text_align="center",
                    color=DARK_THEME["text_gray_400"],
                    margin_bottom="3rem",
                ),
                # Sign in button
                rx.cond(
                    AuthState.is_loading,
                    # Loading state
                    rx.button(
                        rx.spinner(size="3"),
                        "Signing in...",
                        width="100%",
                        size="4",
                        disabled=True,
                    ),
                    # Normal state
                    rx.button(
                        rx.icon("log_in", size=20),
                        "Sign in with Google",
                        width="100%",
                        size="4",
                        background=DARK_THEME["neon_cyan"],
                        color=DARK_THEME["bg_black"],
                        _hover={
                            "background": DARK_THEME["neon_purple"],
                            "transform": "translateY(-2px)",
                            "box_shadow": f"0 0 30px {DARK_THEME['neon_cyan']}50",
                        },
                        on_click=AuthState.login_with_google,
                    ),
                ),
                # Error message
                rx.cond(
                    AuthState.error_message.length() > 0,
                    rx.callout(
                        AuthState.error_message,
                        icon="alert_triangle",
                        color_scheme="red",
                        margin_top="1rem",
                    ),
                    rx.box(),
                ),
                # Footer
                rx.text(
                    "By signing in, you agree to our Terms of Service and Privacy Policy",
                    size="1",
                    text_align="center",
                    color=DARK_THEME["text_gray_500"],
                    margin_top="2rem",
                ),
                # Card styling
                max_width="450px",
                width="90%",
                padding="3rem",
                background=DARK_THEME["bg_gray_900"],
                border=f"1px solid {DARK_THEME['bg_gray_800']}",
                border_radius="16px",
                box_shadow=f"0 0 60px {DARK_THEME['neon_cyan']}15",
            ),
            width="100%",
            height="100vh",
            position="absolute",
            top="0",
            left="0",
        ),
        width="100%",
        min_height="100vh",
        overflow="hidden",
    )
