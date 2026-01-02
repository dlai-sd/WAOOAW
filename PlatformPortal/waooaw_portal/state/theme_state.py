"""
Theme State Management

Handles theme selection and switching between dark and light modes.
"""

import reflex as rx
from waooaw_portal.theme.colors import DARK_THEME, LIGHT_THEME


class ThemeState(rx.State):
    """
    Theme state for portal appearance.
    
    Features:
    - Dark/Light theme switching
    - Persistent theme selection
    - Dynamic theme application
    """
    
    # Current theme name
    current_theme: str = "dark"
    
    def toggle_theme(self):
        """Toggle between dark and light themes"""
        if self.current_theme == "dark":
            self.current_theme = "light"
        else:
            self.current_theme = "dark"
    
    def set_theme(self, theme_name: str):
        """Set specific theme"""
        if theme_name in ["dark", "light"]:
            self.current_theme = theme_name
    
    @rx.var
    def theme(self) -> dict:
        """Get current theme colors"""
        if self.current_theme == "light":
            return LIGHT_THEME
        return DARK_THEME
    
    @rx.var
    def theme_icon(self) -> str:
        """Get icon for current theme"""
        return "sun" if self.current_theme == "dark" else "moon"
    
    @rx.var
    def theme_label(self) -> str:
        """Get label for theme toggle button"""
        return "Light Mode" if self.current_theme == "dark" else "Dark Mode"
