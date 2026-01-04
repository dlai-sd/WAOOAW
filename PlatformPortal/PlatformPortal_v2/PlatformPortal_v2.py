"""WAOOAW Platform Portal - Internal Operations Dashboard"""

import reflex as rx
import os
from rxconfig import config
from .components.google_signin import google_signin_modal, google_signin_script, google_signin_button


# Environment detection
def detect_environment():
    """Detect environment from CODESPACE_NAME env var or ENV"""
    # Check if running in Codespace (GitHub sets this)
    if os.getenv('CODESPACE_NAME'):
        return 'codespace'
    
    # Otherwise use ENV variable (set in Cloud Run, defaults to development)
    return os.getenv('ENV', 'development')


class PlatformState(rx.State):
    """Main application state"""
    
    # Environment
    environment: str = detect_environment()
    
    # User state
    is_authenticated: bool = False
    user_email: str = ""
    user_name: str = ""
    user_picture: str = ""
    user_role: str = "viewer"
    auth_token: str = ""
    
    # Modal state
    show_signin_modal: bool = False
    is_authenticating: bool = False
    auth_error: str = ""
    
    # Dashboard metrics
    active_agents: int = 19
    active_trials: int = 47
    total_customers: int = 156
    revenue_today: str = "₹45,000"
    
    def open_signin_modal(self):
        """Open Google Sign-In modal"""
        self.show_signin_modal = True
        self.auth_error = ""
    
    def close_signin_modal(self):
        """Close Google Sign-In modal"""
        self.show_signin_modal = False
        self.auth_error = ""
    
    def login_redirect(self):
        """Legacy: Redirect to OAuth login (kept for backward compatibility)"""
        # Now opens modal instead
        self.open_signin_modal()
    
    def handle_oauth_callback(self):
        """Handle OAuth callback from backend"""
        # Get URL parameters
        token = self.router.page.params.get("token", "")
        email = self.router.page.params.get("email", "")
        name = self.router.page.params.get("name", "")
        picture = self.router.page.params.get("picture", "")
        role = self.router.page.params.get("role", "viewer")
        
        if token and email:
            # Store user info
            self.auth_token = token
            self.user_email = email
            self.user_name = name
            self.user_picture = picture
            self.user_role = role
            self.is_authenticated = True
            
            # Redirect to dashboard
            return rx.redirect("/")
        else:
            # Redirect to login on error
            return rx.redirect("/login")
    
    def logout(self):
        """Logout user and redirect to login page"""
        self.is_authenticated = False
        self.user_email = ""
        self.user_name = ""
        self.user_picture = ""
        self.user_role = "viewer"
        self.auth_token = ""
        # Clear localStorage
        return rx.call_script("""
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_email');
            localStorage.removeItem('user_name');
            localStorage.removeItem('user_picture');
            window.location.href = '/';
        """)
    
    def get_backend_url(self) -> str:
        """Get backend URL based on environment"""
        if self.environment == 'codespace':
            # Auto-detect from CODESPACE_NAME
            codespace_name = os.getenv('CODESPACE_NAME', '')
            if codespace_name:
                return f'https://{codespace_name}-8000.app.github.dev'
            return 'http://localhost:8000'  # fallback
        elif self.environment == 'demo':
            return 'https://demo.waooaw.com/api'
        elif self.environment == 'uat':
            return 'https://uat-api.waooaw.com'  # UAT will use Load Balancer
        elif self.environment == 'production':
            return 'https://api.waooaw.com'  # Production will use Load Balancer
        else:
            return 'http://localhost:8000'


def nav_bar() -> rx.Component:
    """Navigation bar component"""
    return rx.box(
        rx.hstack(
            rx.heading(
                rx.text("WAOOAW", 
                    background_image="linear-gradient(135deg, #00f2fe 0%, #667eea 100%)",
                    background_clip="text",
                    color="transparent",
                    font_weight="700",
                ),
                size="7",
            ),
            rx.spacer(),
            rx.badge(
                PlatformState.environment.upper(),
                color_scheme="cyan",
                variant="solid",
            ),
            rx.spacer(),
            rx.cond(
                PlatformState.is_authenticated,
                rx.hstack(
                    rx.text(PlatformState.user_email, color="#a1a1aa"),
                    rx.button(
                        "Logout",
                        on_click=PlatformState.logout,
                        color_scheme="red",
                        variant="soft",
                    ),
                    spacing="4",
                ),
                rx.button(
                    "Sign In",
                    on_click=PlatformState.login_redirect,
                    color_scheme="cyan",
                    variant="solid",
                ),
            ),
            align="center",
            width="100%",
            padding="1rem 2rem",
        ),
        background="#18181b",
        border_bottom="1px solid #3f3f46",
    )


def metric_card(title: str, value: str, icon: str, color: str = "cyan") -> rx.Component:
    """Metric card component"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.text(icon, font_size="2rem"),
                rx.spacer(),
                rx.badge("Live", color_scheme="green", variant="solid"),
                width="100%",
            ),
            rx.heading(value, size="8", margin_top="1rem"),
            rx.text(title, color="#a1a1aa", size="3"),
            spacing="2",
            align="start",
        ),
        background="#18181b",
        border=f"1px solid #{color}40",
        padding="1.5rem",
        _hover={
            "transform": "translateY(-4px)",
            "box_shadow": f"0 0 20px rgba(0, 242, 254, 0.3)",
        },
        transition="all 0.3s ease",
    )


def dashboard() -> rx.Component:
    """Main dashboard view - requires authentication"""
    return rx.fragment(
        # Include Google Sign-In script
        google_signin_script(),
        
        # Sign-In Modal
        google_signin_modal(PlatformState),
        
        # Dashboard content
        rx.cond(
            PlatformState.is_authenticated,
            # Authenticated: Show dashboard
            rx.container(
                nav_bar(),
                rx.vstack(
                    rx.heading(
                        "Platform Dashboard",
                        size="9",
                        margin_top="2rem",
                        margin_bottom="1rem",
                    ),
                    rx.text(
                        "Real-time operations monitoring",
                        color="#a1a1aa",
                        size="4",
                        margin_bottom="2rem",
                    ),
                    
                    # Metrics Grid
                    rx.grid(
                        metric_card("Active Agents", str(PlatformState.active_agents), "🤖", "cyan"),
                        metric_card("Active Trials", str(PlatformState.active_trials), "🎯", "purple"),
                        metric_card("Total Customers", str(PlatformState.total_customers), "👥", "pink"),
                        metric_card("Revenue Today", PlatformState.revenue_today, "💰", "green"),
                        columns="4",
                        spacing="4",
                        width="100%",
                    ),
                    
                    # Quick Actions
                    rx.heading("Quick Actions", size="7", margin_top="3rem", margin_bottom="1rem"),
                    rx.grid(
                        rx.button(
                            "View Agents",
                            color_scheme="cyan",
                            size="3",
                            width="100%",
                        ),
                        rx.button(
                            "Manage Trials",
                            color_scheme="purple",
                            size="3",
                            width="100%",
                        ),
                        rx.button(
                            "View Logs",
                            color_scheme="orange",
                            size="3",
                            width="100%",
                        ),
                        rx.button(
                            "System Health",
                            color_scheme="green",
                            size="3",
                            width="100%",
                        ),
                        columns="4",
                        spacing="4",
                        width="100%",
                    ),
                    
                    spacing="4",
                    padding="2rem",
                    max_width="1400px",
                ),
            background="#0a0a0a",
            min_height="100vh",
        ),
        # Not authenticated: Redirect to login
        login_page(),
    )


def login_page() -> rx.Component:
    """Login page with Google Sign-In modal"""
    return rx.fragment(
        # Include Google Sign-In script
        google_signin_script(),
        
        # Sign-In Modal
        google_signin_modal(PlatformState),
        
        # Login Page Content
        rx.center(
            rx.card(
                rx.vstack(
                    rx.heading(
                        rx.text("WAOOAW", 
                            background_image="linear-gradient(135deg, #00f2fe 0%, #667eea 100%)",
                            background_clip="text",
                            color="transparent",
                            font_weight="700",
                        ),
                        size="9",
                    ),
                    rx.text(
                        "Platform Portal",
                        size="5",
                        color="#a1a1aa",
                        margin_bottom="2rem",
                    ),
                    rx.button(
                        "Sign in with Google",
                        on_click=PlatformState.open_signin_modal,
                        color_scheme="cyan",
                        size="3",
                        width="100%",
                    ),
                    rx.badge(
                        PlatformState.environment.upper(),
                        color_scheme="gray",
                        variant="soft",
                        margin_top="2rem",
                    ),
                    spacing="4",
                    align="center",
                ),
                background="#18181b",
                padding="3rem",
                max_width="400px",
            ),
            background="#0a0a0a",
            min_height="100vh",
        ),
    )


def auth_callback_page() -> rx.Component:
    """OAuth callback page - handles redirect from backend"""
    return rx.center(
        rx.vstack(
            rx.heading(
                rx.text("WAOOAW", 
                    background_image="linear-gradient(135deg, #00f2fe 0%, #667eea 100%)",
                    background_clip="text",
                    color="transparent",
                    font_weight="700",
                ),
                size="9",
            ),
            rx.spinner(size="3"),
            rx.text(
                "Completing sign in...",
                size="4",
                color="#a1a1aa",
            ),
            spacing="4",
            align="center",
        ),
        background="#0a0a0a",
        min_height="100vh",
        on_mount=PlatformState.handle_oauth_callback,
    )


# App setup
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="cyan",
    ),
)

app.add_page(
    dashboard,
    route="/",
    title="WAOOAW Platform Portal - Dashboard",
)

app.add_page(
    login_page,
    route="/login",
    title="WAOOAW Platform Portal - Login",
)

app.add_page(
    auth_callback_page,
    route="/auth/callback",
    title="WAOOAW Platform Portal - Authenticating",
)
