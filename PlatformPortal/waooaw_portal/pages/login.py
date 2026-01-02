"""Login Page - Simplified"""
import reflex as rx

def login_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                rx.heading("WAOOAW Platform Portal", size="8"),
                rx.text("Operations Dashboard", size="3", color="gray"),
                rx.link(rx.button("Enter Dashboard", size="3"), href="/dashboard"),
                spacing="4",
                align="center",
            ),
        ),
        min_height="100vh",
    )
