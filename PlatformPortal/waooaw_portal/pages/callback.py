"""OAuth Callback Page"""
import reflex as rx

def callback_page() -> rx.Component:
    """OAuth callback handler page"""
    return rx.center(
        rx.card(
            rx.vstack(
                # Loading spinner
                rx.spinner(size="3"),
                rx.heading("Logging you in...", size="7"),
                rx.text("Please wait", size="3", color="gray"),
                spacing="4",
                align="center",
                padding="2rem",
            ),
            max_width="400px",
        ),
        min_height="100vh",
        background="#0a0a0a",
        on_mount=rx.redirect("/dashboard"),  # After auth, redirect to dashboard
    )
