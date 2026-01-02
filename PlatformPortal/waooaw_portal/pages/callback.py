"""OAuth Callback Page"""
import reflex as rx
from waooaw_portal.theme.colors import DARK_THEME

def callback_page() -> rx.Component:
    """
    OAuth callback handler page.
    
    Receives token and user info from backend OAuth, stores in browser storage,
    then redirects to dashboard.
    
    FROZEN: Do not modify this OAuth flow logic.
    """
    return rx.fragment(
        rx.script("""
            // Extract token and user info from URL parameters
            const params = new URLSearchParams(window.location.search);
            const token = params.get('token');
            const email = params.get('email');
            const name = params.get('name');
            const picture = params.get('picture');
            const role = params.get('role');
            
            if (token) {
                // Store in localStorage
                localStorage.setItem('auth_token', token);
                localStorage.setItem('user_email', email);
                localStorage.setItem('user_name', name);
                localStorage.setItem('user_picture', picture);
                localStorage.setItem('user_role', role);
                
                // Redirect to dashboard after brief delay
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 500);
            } else {
                // No token, redirect back to login
                setTimeout(() => {
                    window.location.href = '/login';
                }, 1000);
            }
        """),
        rx.center(
            rx.card(
                rx.vstack(
                    # Loading spinner
                    rx.spinner(size="3"),
                    rx.heading("Logging you in...", size="7"),
                    rx.text("Please wait", size="3", color=DARK_THEME["text_tertiary"]),
                    spacing="4",
                    align="center",
                    padding="2rem",
                ),
                max_width="400px",
            ),
            min_height="100vh",
            background=DARK_THEME["bg_primary"],
        ),
    )
