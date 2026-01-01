"""
Status Badge Component
Displays status indicators with traffic light colors (🟢🟡🔴⚫)
Used across all portal pages for consistent status visualization
"""

import reflex as rx
from typing import Literal
from waooaw_portal.theme import get_status_color, get_status_emoji, DARK_THEME

StatusType = Literal[
    "healthy",
    "success",
    "online",
    "active",
    "degraded",
    "warning",
    "working",
    "pending",
    "critical",
    "error",
    "failed",
    "offline",
    "info",
    "unknown",
    "stopped",
]


def status_badge(
    status: StatusType,
    label: str | None = None,
    show_emoji: bool = True,
    size: Literal["sm", "md", "lg"] = "md",
    theme: Literal["dark", "light"] = "dark",
) -> rx.Component:
    """
    Render a status badge with color-coded indicator.

    Args:
        status: Status type (healthy, warning, error, etc.)
        label: Optional text label. If None, uses status name.
        show_emoji: Whether to show emoji indicator
        size: Badge size (sm=12px, md=14px, lg=16px)
        theme: Color theme (dark or light)

    Returns:
        Reflex badge component

    Example:
        ```python
        status_badge("online", "Agent Online")
        status_badge("error", "Failed", show_emoji=False)
        status_badge("working", size="lg")
        ```
    """
    # Get color for this status
    color = get_status_color(status, theme)
    emoji = get_status_emoji(status) if show_emoji else ""

    # Use status name if no label provided
    display_text = label if label else status.capitalize()
    full_text = f"{emoji} {display_text}" if emoji else display_text

    # Size mappings
    size_config = {
        "sm": {
            "font_size": "12px",
            "padding": "4px 8px",
        },
        "md": {
            "font_size": "14px",
            "padding": "6px 12px",
        },
        "lg": {
            "font_size": "16px",
            "padding": "8px 16px",
        },
    }

    config = size_config.get(size, size_config["md"])

    # Background color with transparency
    bg_color = f"{color}1a"  # 10% opacity

    return rx.badge(
        full_text,
        color=color,
        background=bg_color,
        border=f"1px solid {color}40",  # 25% opacity border
        border_radius="9999px",  # Pill shape
        font_size=config["font_size"],
        font_weight="500",
        padding=config["padding"],
        display="inline-flex",
        align_items="center",
        gap="4px",
        transition="all 0.2s ease",
        _hover={
            "transform": "scale(1.05)",
            "box_shadow": f"0 0 10px {color}40",
        },
    )


def status_badge_list(
    statuses: list[tuple[StatusType, str]],
    theme: Literal["dark", "light"] = "dark",
) -> rx.Component:
    """
    Render multiple status badges in a horizontal list.

    Args:
        statuses: List of (status, label) tuples
        theme: Color theme

    Returns:
        Flex container with badges

    Example:
        ```python
        status_badge_list([
            ("online", "API Online"),
            ("warning", "High Load"),
            ("error", "DB Connection Lost"),
        ])
        ```
    """
    return rx.flex(
        *[status_badge(status, label, theme=theme) for status, label in statuses],
        gap="8px",
        flex_wrap="wrap",
        align_items="center",
    )


# =============================================================================
# PRESET BADGE FUNCTIONS (Convenience wrappers)
# =============================================================================


def badge_online(label: str = "Online") -> rx.Component:
    """Green badge indicating online/healthy status."""
    return status_badge("online", label)


def badge_offline(label: str = "Offline") -> rx.Component:
    """Red badge indicating offline/failed status."""
    return status_badge("offline", label)


def badge_working(label: str = "Working") -> rx.Component:
    """Yellow badge indicating working/pending status."""
    return status_badge("working", label)


def badge_unknown(label: str = "Unknown") -> rx.Component:
    """Gray badge indicating unknown status."""
    return status_badge("unknown", label)
