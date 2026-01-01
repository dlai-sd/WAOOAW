"""
Authentication State Management

Handles user authentication, session management, and OAuth2 flow.
"""

import reflex as rx
from typing import Optional
from datetime import datetime, timedelta
import os


class AuthState(rx.State):
    """
    Authentication state for WAOOAW Platform Portal.
    
    Features:
    - Google OAuth2 integration
    - JWT token management
    - User session handling
    - Role-based access control
    """

    # User information
    is_authenticated: bool = False
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "viewer"  # admin, operator, viewer
    
    # Session management
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    # UI state
    is_loading: bool = False
    error_message: Optional[str] = None

    def login_with_google(self):
        """Initiate Google OAuth2 flow"""
        self.is_loading = True
        self.error_message = None
        
        # Redirect to OAuth endpoint
        # In production, this would be: return rx.redirect("/auth/login")
        # For now, simulate authentication
        self._simulate_login()

    def _simulate_login(self):
        """Simulate successful login (for development)"""
        self.is_authenticated = True
        self.user_id = "user-123"
        self.email = "operator@waooaw.com"
        self.name = "Platform Operator"
        self.avatar_url = "https://ui-avatars.com/api/?name=Platform+Operator&background=00f2fe&color=fff"
        self.role = "operator"
        self.access_token = "mock-jwt-token"
        self.token_expires_at = datetime.now() + timedelta(hours=24)
        self.last_activity = datetime.now()
        self.is_loading = False

    def logout(self):
        """Logout user and clear session"""
        self.is_authenticated = False
        self.user_id = None
        self.email = None
        self.name = None
        self.avatar_url = None
        self.role = "viewer"
        self.access_token = None
        self.token_expires_at = None
        self.last_activity = None
        self.error_message = None
        
        # Redirect to login
        return rx.redirect("/login")

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()

    def check_token_expiry(self):
        """Check if token is expired"""
        if not self.is_authenticated:
            return False
        
        if not self.token_expires_at:
            return True
        
        if datetime.now() >= self.token_expires_at:
            self.logout()
            return True
        
        return False

    def has_role(self, required_role: str) -> bool:
        """
        Check if user has required role.
        
        Role hierarchy: admin > operator > viewer
        """
        role_levels = {"admin": 3, "operator": 2, "viewer": 1}
        user_level = role_levels.get(self.role, 0)
        required_level = role_levels.get(required_role, 0)
        return user_level >= required_level

    @rx.var
    def user_display_name(self) -> str:
        """Get user display name"""
        return self.name or self.email or "User"

    @rx.var
    def user_initials(self) -> str:
        """Get user initials for avatar"""
        if self.name:
            parts = self.name.split()
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[1][0]}".upper()
            return self.name[:2].upper()
        return "U"

    @rx.var
    def role_badge_color(self) -> str:
        """Get role badge color"""
        colors = {
            "admin": "red",
            "operator": "blue",
            "viewer": "gray"
        }
        return colors.get(self.role, "gray")
