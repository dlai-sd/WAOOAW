"""
Timeline Component

Activity feed with timestamps, avatars, actions, and filtering.
Used for displaying agent activity, audit logs, and system events.
"""

from typing import Optional, List, Tuple
from datetime import datetime
import reflex as rx
from waooaw_portal.theme import get_theme


def timeline_component(
    items: List[
        Tuple[str, str, str, Optional[str], Optional[str]]
    ],  # (timestamp, title, description, avatar, action_type)
    max_items: int = 10,
    show_avatars: bool = True,
    show_timestamps: bool = True,
    compact: bool = False,
    theme: str = "dark",
) -> rx.Component:
    """
    Display activity timeline with events.

    Args:
        items: List of timeline items (timestamp, title, description, avatar, action_type)
        max_items: Maximum items to display
        show_avatars: Show avatar/icon for each item
        show_timestamps: Show timestamp for each item
        compact: Use compact layout
        theme: Color theme

    Returns:
        Timeline component
    """
    theme_colors = get_theme(theme)

    # Limit items
    display_items = items[:max_items] if max_items > 0 else items

    timeline_items = [
        _timeline_item(
            timestamp=item[0],
            title=item[1],
            description=item[2],
            avatar=item[3] if len(item) > 3 else None,
            action_type=item[4] if len(item) > 4 else None,
            show_avatar=show_avatars,
            show_timestamp=show_timestamps,
            compact=compact,
            theme=theme,
        )
        for item in display_items
    ]

    return rx.box(
        rx.vstack(
            *timeline_items,
            spacing="0",
            width="100%",
        ),
        width="100%",
    )


def _timeline_item(
    timestamp: str,
    title: str,
    description: str,
    avatar: Optional[str] = None,
    action_type: Optional[str] = None,
    show_avatar: bool = True,
    show_timestamp: bool = True,
    compact: bool = False,
    theme: str = "dark",
) -> rx.Component:
    """Create a single timeline item"""
    theme_colors = get_theme(theme)

    # Action type colors
    action_colors = {
        "create": theme_colors["success"],
        "update": theme_colors["primary"],
        "delete": theme_colors["error"],
        "start": theme_colors["success"],
        "stop": theme_colors["warning"],
        "error": theme_colors["error"],
        "info": theme_colors["info"],
    }
    action_color = action_colors.get(action_type, theme_colors["primary"])

    # Avatar/Icon section
    avatar_section = None
    if show_avatar:
        if avatar:
            avatar_section = rx.box(
                rx.text(
                    avatar[:2].upper(),
                    color=theme_colors["text_primary"],
                    font_size="0.75rem",
                    font_weight="600",
                ),
                width="32px",
                height="32px",
                border_radius="50%",
                background=f"linear-gradient(135deg, {theme_colors['primary']}, {theme_colors['secondary']})",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            )
        else:
            avatar_section = rx.box(
                width="12px",
                height="12px",
                border_radius="50%",
                background=action_color,
                border=f"3px solid {theme_colors['bg_primary']}",
                flex_shrink="0",
            )

    # Timestamp
    timestamp_text = None
    if show_timestamp:
        timestamp_text = rx.text(
            _format_relative_time(timestamp),
            font_size="0.75rem",
            color=theme_colors["text_tertiary"],
            white_space="nowrap",
        )

    # Content
    content = rx.vstack(
        rx.hstack(
            rx.text(
                title,
                font_size="0.875rem" if compact else "1rem",
                font_weight="600",
                color=theme_colors["text_primary"],
            ),
            timestamp_text if show_timestamp else rx.fragment(),
            spacing="2",
            align_items="center",
        ),
        rx.text(
            description,
            font_size="0.75rem" if compact else "0.875rem",
            color=theme_colors["text_secondary"],
            line_height="1.5",
        ),
        spacing="0.25rem",
        align_items="flex-start",
        flex="1",
    )

    return rx.box(
        rx.hstack(
            avatar_section if show_avatar else rx.fragment(),
            rx.box(
                width="2px",
                height="100%",
                background=theme_colors["border"],
                margin_x="0.75rem" if show_avatar else "0",
                position="absolute",
                left="15px" if show_avatar else "5px",
                top="32px",
                bottom="-16px",
            ),
            content,
            spacing="0.75rem",
            align_items="flex-start",
            position="relative",
        ),
        padding_y="0.75rem" if compact else "1rem",
        border_bottom=f"1px solid {theme_colors['border']}",
        _last={"border_bottom": "none"},
    )


def _format_relative_time(timestamp: str) -> str:
    """Format timestamp as relative time (e.g., '2m ago', '1h ago')"""
    try:
        # Try parsing ISO format
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        delta = now - dt

        seconds = delta.total_seconds()
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days}d ago"
        else:
            weeks = int(seconds / 604800)
            return f"{weeks}w ago"
    except Exception:
        # Fallback: return timestamp as-is
        return timestamp


# Preset timeline components
def timeline_agent_activity(
    activities: List[Tuple[str, str, str, str]], theme: str = "dark"
) -> rx.Component:
    """Preset: Agent activity timeline"""
    return timeline_component(
        items=activities, show_avatars=True, show_timestamps=True, theme=theme
    )


def timeline_audit_log(
    logs: List[Tuple[str, str, str, str, str]], theme: str = "dark"
) -> rx.Component:
    """Preset: Audit log timeline with action types"""
    return timeline_component(
        items=logs, show_avatars=True, show_timestamps=True, theme=theme
    )


def timeline_system_events(
    events: List[Tuple[str, str, str]], theme: str = "dark"
) -> rx.Component:
    """Preset: System events timeline (compact)"""
    items = [(e[0], e[1], e[2], None, "info") for e in events]
    return timeline_component(
        items=items,
        show_avatars=True,
        show_timestamps=True,
        compact=True,
        theme=theme,
    )


def timeline_recent_changes(
    changes: List[Tuple[str, str, str, str]], max_items: int = 5, theme: str = "dark"
) -> rx.Component:
    """Preset: Recent changes timeline (limited items)"""
    return timeline_component(
        items=changes,
        max_items=max_items,
        show_avatars=False,
        show_timestamps=True,
        compact=True,
        theme=theme,
    )
