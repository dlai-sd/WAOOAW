"""
WAOOAW Platform Portal - Color Theme System
Brand colors and design tokens for dark/light themes
"""

# =============================================================================
# DARK THEME (DEFAULT - Operators prefer dark mode)
# =============================================================================

DARK_THEME = {
    # Backgrounds
    "bg_primary": "#0a0a0a",  # Deep black - main background
    "bg_secondary": "#18181b",  # Gray-900 - card backgrounds
    "bg_tertiary": "#27272a",  # Gray-800 - secondary surfaces
    "bg_hover": "#3f3f46",  # Gray-700 - hover states
    # Text
    "text_primary": "#ffffff",  # White - primary text
    "text_secondary": "#a1a1aa",  # Gray-400 - secondary text
    "text_tertiary": "#71717a",  # Gray-500 - tertiary text/captions
    # Borders
    "border_primary": "#27272a",  # Gray-800
    "border_secondary": "#3f3f46",  # Gray-700
    "border_accent": "#667eea",  # Purple accent
    # Neon Accents (WAOOAW Brand)
    "accent_cyan": "#00f2fe",  # Primary - links, actions
    "accent_purple": "#667eea",  # Secondary - borders, highlights
    "accent_pink": "#f093fb",  # Tertiary - special highlights
    # Status Colors (Traffic Light System)
    "status_success": "#10b981",  # 🟢 Healthy, Online, Active
    "status_warning": "#f59e0b",  # 🟡 Degraded, Working, Pending
    "status_error": "#ef4444",  # 🔴 Critical, Failed, Offline
    "status_info": "#3b82f6",  # 🔵 Info, Neutral
    "status_unknown": "#71717a",  # ⚫ Unknown, Stopped
    # Effects
    "shadow": "rgba(0, 0, 0, 0.5)",
    "glow_cyan": "rgba(0, 242, 254, 0.2)",
    "glow_purple": "rgba(102, 126, 234, 0.2)",
    "glow_success": "rgba(16, 185, 129, 0.2)",
    "glow_error": "rgba(239, 68, 68, 0.2)",
}

# =============================================================================
# LIGHT THEME (Optional - for operators who prefer light mode)
# =============================================================================

LIGHT_THEME = {
    # Backgrounds
    "bg_primary": "#ffffff",  # White
    "bg_secondary": "#f8f9fa",  # Gray-50
    "bg_tertiary": "#e9ecef",  # Gray-100
    "bg_hover": "#dee2e6",  # Gray-200
    # Text
    "text_primary": "#1a1a1a",  # Near-black
    "text_secondary": "#495057",  # Gray-600
    "text_tertiary": "#6c757d",  # Gray-500
    # Borders
    "border_primary": "#dee2e6",  # Gray-200
    "border_secondary": "#ced4da",  # Gray-300
    "border_accent": "#5a67d8",  # Purple (adjusted for light)
    # Neon Accents (adjusted for light background)
    "accent_cyan": "#0099ff",  # Slightly darker cyan
    "accent_purple": "#5a67d8",  # Adjusted purple
    "accent_pink": "#d946ef",  # Adjusted pink
    # Status Colors (same as dark)
    "status_success": "#059669",  # Slightly darker green
    "status_warning": "#d97706",  # Slightly darker yellow
    "status_error": "#dc2626",  # Slightly darker red
    "status_info": "#2563eb",  # Slightly darker blue
    "status_unknown": "#6c757d",  # Gray
    # Effects
    "shadow": "rgba(0, 0, 0, 0.1)",
    "glow_cyan": "rgba(0, 153, 255, 0.15)",
    "glow_purple": "rgba(90, 103, 216, 0.15)",
    "glow_success": "rgba(5, 150, 105, 0.15)",
    "glow_error": "rgba(220, 38, 38, 0.15)",
}

# =============================================================================
# TYPOGRAPHY
# =============================================================================

FONTS = {
    "display": "Space Grotesk, system-ui, sans-serif",  # Headings, hero
    "heading": "Outfit, system-ui, sans-serif",  # Section titles
    "body": "Inter, system-ui, sans-serif",  # Body text, UI
    "mono": "JetBrains Mono, Courier New, monospace",  # Code, logs, metrics
}

FONT_SIZES = {
    "h1": "32px",  # Page titles
    "h2": "24px",  # Section headers
    "h3": "18px",  # Card titles
    "h4": "16px",  # Sub-sections
    "body_large": "16px",
    "body_medium": "14px",
    "body_small": "12px",
    "mono_large": "16px",
    "mono_medium": "14px",
}

FONT_WEIGHTS = {
    "light": 300,
    "regular": 400,
    "medium": 500,
    "semibold": 600,
    "bold": 700,
    "extrabold": 800,
}

# =============================================================================
# LAYOUT & SPACING
# =============================================================================

SPACING = {
    "xs": "8px",
    "sm": "16px",
    "md": "24px",
    "lg": "32px",
    "xl": "48px",
    "xxl": "64px",
}

RADII = {
    "sm": "8px",  # Badges, buttons
    "md": "12px",  # Cards
    "lg": "16px",  # Modals, large cards
    "full": "9999px",  # Pills, avatars
}

LAYOUT = {
    "container_max_width": "1400px",
    "grid_columns": 12,
    "gutter": "24px",
    "section_spacing": "48px",
    "card_spacing": "24px",
}

# =============================================================================
# GRADIENTS
# =============================================================================

GRADIENTS = {
    "cyan_purple": "linear-gradient(135deg, #00f2fe, #667eea)",
    "purple_pink": "linear-gradient(135deg, #667eea, #f093fb)",
    "success": "linear-gradient(135deg, #10b981, #059669)",
    "error": "linear-gradient(135deg, #ef4444, #dc2626)",
}

# =============================================================================
# SHADOWS & GLOWS
# =============================================================================

SHADOWS = {
    "sm": "0 1px 3px rgba(0, 0, 0, 0.1)",
    "md": "0 4px 6px rgba(0, 0, 0, 0.1)",
    "lg": "0 10px 15px rgba(0, 0, 0, 0.2)",
    "xl": "0 20px 25px rgba(0, 0, 0, 0.3)",
}

GLOWS = {
    "cyan": "0 0 20px rgba(0, 242, 254, 0.2)",
    "purple": "0 0 20px rgba(102, 126, 234, 0.2)",
    "success": "0 0 15px rgba(16, 185, 129, 0.2)",
    "error": "0 0 15px rgba(239, 68, 68, 0.2)",
    "warning": "0 0 15px rgba(245, 158, 11, 0.2)",
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_theme(theme_name: str = "dark") -> dict:
    """Get theme colors by name."""
    if theme_name.lower() == "light":
        return LIGHT_THEME
    return DARK_THEME


def get_status_color(status: str, theme: str = "dark") -> str:
    """Get color for a given status."""
    theme_colors = get_theme(theme)
    status_map = {
        "healthy": theme_colors["status_success"],
        "success": theme_colors["status_success"],
        "online": theme_colors["status_success"],
        "active": theme_colors["status_success"],
        "degraded": theme_colors["status_warning"],
        "warning": theme_colors["status_warning"],
        "working": theme_colors["status_warning"],
        "pending": theme_colors["status_warning"],
        "critical": theme_colors["status_error"],
        "error": theme_colors["status_error"],
        "failed": theme_colors["status_error"],
        "offline": theme_colors["status_error"],
        "info": theme_colors["status_info"],
        "unknown": theme_colors["status_unknown"],
        "stopped": theme_colors["status_unknown"],
    }
    return status_map.get(status.lower(), theme_colors["status_unknown"])


def get_status_emoji(status: str) -> str:
    """Get emoji for a given status."""
    status_map = {
        "healthy": "🟢",
        "success": "🟢",
        "online": "🟢",
        "active": "🟢",
        "degraded": "🟡",
        "warning": "🟡",
        "working": "🟡",
        "pending": "🟡",
        "critical": "🔴",
        "error": "🔴",
        "failed": "🔴",
        "offline": "🔴",
        "info": "🔵",
        "unknown": "⚫",
        "stopped": "⚫",
    }
    return status_map.get(status.lower(), "⚪")


# =============================================================================
# EXPORT ALL
# =============================================================================

__all__ = [
    "DARK_THEME",
    "LIGHT_THEME",
    "FONTS",
    "FONT_SIZES",
    "FONT_WEIGHTS",
    "SPACING",
    "RADII",
    "LAYOUT",
    "GRADIENTS",
    "SHADOWS",
    "GLOWS",
    "get_theme",
    "get_status_color",
    "get_status_emoji",
]
