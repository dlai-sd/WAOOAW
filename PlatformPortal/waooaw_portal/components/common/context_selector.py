"""
Context Selector Component

Agent/service filtering dropdown with search and multi-select.
Used for filtering views by agent, service, environment, or context.
"""

from typing import Optional, List, Tuple, Callable
import reflex as rx
from waooaw_portal.theme import get_theme


class ContextSelectorState(rx.State):
    """State management for context selector"""

    selected_items: List[str] = []
    search_query: str = ""
    is_open: bool = False


def context_selector(
    items: List[Tuple[str, str, Optional[str]]],  # (id, label, icon/avatar)
    selected: Optional[List[str]] = None,
    multi_select: bool = False,
    searchable: bool = True,
    placeholder: str = "Select context...",
    on_change: Optional[Callable[[List[str]], None]] = None,
    max_height: str = "300px",
    show_icons: bool = True,
    theme: str = "dark",
) -> rx.Component:
    """
    Context selector dropdown with search and multi-select.

    Args:
        items: List of items (id, label, icon/avatar)
        selected: Pre-selected item IDs
        multi_select: Allow multiple selections
        searchable: Enable search functionality
        placeholder: Placeholder text
        on_change: Callback when selection changes
        max_height: Maximum dropdown height
        show_icons: Show icons/avatars for items
        theme: Color theme

    Returns:
        Context selector component
    """
    theme_colors = get_theme(theme)

    # Initialize selected items
    if selected:
        ContextSelectorState.selected_items = selected

    # Search input
    search_input = None
    if searchable:
        search_input = rx.input(
            placeholder="Search...",
            value=ContextSelectorState.search_query,
            on_change=ContextSelectorState.set_search_query,
            width="100%",
            padding="0.5rem",
            background=theme_colors["bg_primary"],
            border=f"1px solid {theme_colors['border']}",
            border_radius="0.5rem",
            color=theme_colors["text_primary"],
            font_size="0.875rem",
            _focus={
                "outline": "none",
                "border_color": theme_colors["primary"],
            },
        )

    # Filter items based on search
    filtered_items = [
        item
        for item in items
        if not ContextSelectorState.search_query
        or ContextSelectorState.search_query.lower() in item[1].lower()
    ]

    # Item list
    item_components = [
        _selector_item(
            item_id=item[0],
            label=item[1],
            icon=item[2] if len(item) > 2 else None,
            is_selected=item[0] in ContextSelectorState.selected_items,
            multi_select=multi_select,
            show_icon=show_icons,
            theme=theme,
        )
        for item in filtered_items
    ]

    # Selected items display
    selected_display = _selected_items_display(
        items, ContextSelectorState.selected_items, theme
    )

    return rx.box(
        # Trigger button
        rx.button(
            selected_display,
            rx.text(
                "▼" if not ContextSelectorState.is_open else "▲",
                font_size="0.75rem",
                margin_left="auto",
            ),
            on_click=ContextSelectorState.set_is_open(~ContextSelectorState.is_open),
            width="100%",
            padding="0.75rem 1rem",
            background=theme_colors["bg_secondary"],
            border=f"1px solid {theme_colors['border']}",
            border_radius="0.75rem",
            color=theme_colors["text_primary"],
            display="flex",
            align_items="center",
            justify_content="space-between",
            cursor="pointer",
            transition="all 0.2s ease",
            _hover={
                "border_color": theme_colors["primary"],
                "background": theme_colors["bg_tertiary"],
            },
        ),
        # Dropdown menu
        rx.cond(
            ContextSelectorState.is_open,
            rx.box(
                rx.vstack(
                    search_input if searchable else rx.fragment(),
                    rx.box(
                        rx.vstack(
                            *item_components,
                            spacing="0.25rem",
                            width="100%",
                        ),
                        max_height=max_height,
                        overflow_y="auto",
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                ),
                position="absolute",
                top="calc(100% + 0.5rem)",
                left="0",
                width="100%",
                background=theme_colors["bg_secondary"],
                border=f"1px solid {theme_colors['border']}",
                border_radius="0.75rem",
                padding="0.75rem",
                box_shadow=f"0 4px 12px {theme_colors['shadow']}",
                z_index="1000",
            ),
            rx.fragment(),
        ),
        position="relative",
        width="100%",
    )


def _selector_item(
    item_id: str,
    label: str,
    icon: Optional[str],
    is_selected: bool,
    multi_select: bool,
    show_icon: bool,
    theme: str,
) -> rx.Component:
    """Single selector item"""
    theme_colors = get_theme(theme)

    # Icon/Avatar
    icon_component = None
    if show_icon and icon:
        icon_component = rx.box(
            rx.text(
                icon[:2].upper(),
                color=theme_colors["text_primary"],
                font_size="0.75rem",
                font_weight="600",
            ),
            width="24px",
            height="24px",
            border_radius="50%",
            background=f"linear-gradient(135deg, {theme_colors['primary']}, {theme_colors['secondary']})",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        )

    # Checkbox/Radio indicator
    indicator = None
    if multi_select:
        indicator = rx.box(
            rx.text("✓", color="white", font_size="0.75rem")
            if is_selected
            else rx.fragment(),
            width="16px",
            height="16px",
            border_radius="0.25rem",
            background=theme_colors["primary"] if is_selected else "transparent",
            border=f"2px solid {theme_colors['primary'] if is_selected else theme_colors['border']}",
            display="flex",
            align_items="center",
            justify_content="center",
            margin_left="auto",
            flex_shrink="0",
        )
    else:
        indicator = rx.box(
            rx.box(
                width="8px",
                height="8px",
                border_radius="50%",
                background="white",
            )
            if is_selected
            else rx.fragment(),
            width="16px",
            height="16px",
            border_radius="50%",
            background=theme_colors["primary"] if is_selected else "transparent",
            border=f"2px solid {theme_colors['primary'] if is_selected else theme_colors['border']}",
            display="flex",
            align_items="center",
            justify_content="center",
            margin_left="auto",
            flex_shrink="0",
        )

    return rx.box(
        rx.hstack(
            icon_component if show_icon else rx.fragment(),
            rx.text(
                label,
                font_size="0.875rem",
                color=theme_colors["text_primary"],
                font_weight="500" if is_selected else "400",
            ),
            indicator,
            spacing="0.75rem",
            align_items="center",
            width="100%",
        ),
        padding="0.5rem 0.75rem",
        border_radius="0.5rem",
        background=theme_colors["bg_tertiary"] if is_selected else "transparent",
        cursor="pointer",
        transition="all 0.2s ease",
        _hover={
            "background": theme_colors["bg_tertiary"],
        },
        # on_click would toggle selection in real implementation
    )


def _selected_items_display(
    all_items: List[Tuple[str, str, Optional[str]]],
    selected_ids: List[str],
    theme: str,
) -> rx.Component:
    """Display selected items in trigger button"""
    theme_colors = get_theme(theme)

    if not selected_ids:
        return rx.text(
            "Select context...",
            color=theme_colors["text_tertiary"],
            font_size="0.875rem",
        )

    # Get labels for selected items
    selected_labels = [item[1] for item in all_items if item[0] in selected_ids]

    if len(selected_labels) == 1:
        return rx.text(
            selected_labels[0],
            color=theme_colors["text_primary"],
            font_size="0.875rem",
            font_weight="500",
        )
    else:
        return rx.text(
            f"{len(selected_labels)} items selected",
            color=theme_colors["text_primary"],
            font_size="0.875rem",
            font_weight="500",
        )


# Preset context selectors
def context_selector_agents(
    agents: List[Tuple[str, str, str]], theme: str = "dark"
) -> rx.Component:
    """Preset: Agent selector"""
    return context_selector(
        items=agents,
        multi_select=True,
        searchable=True,
        placeholder="Select agents...",
        show_icons=True,
        theme=theme,
    )


def context_selector_environment(
    selected: Optional[str] = None, theme: str = "dark"
) -> rx.Component:
    """Preset: Environment selector (single)"""
    environments = [
        ("dev", "Development", "🔧"),
        ("staging", "Staging", "🎭"),
        ("prod", "Production", "🚀"),
    ]
    return context_selector(
        items=environments,
        selected=[selected] if selected else None,
        multi_select=False,
        searchable=False,
        placeholder="Select environment...",
        show_icons=True,
        theme=theme,
    )


def context_selector_services(
    services: List[Tuple[str, str]], theme: str = "dark"
) -> rx.Component:
    """Preset: Service selector (multi-select)"""
    items = [(s[0], s[1], None) for s in services]
    return context_selector(
        items=items,
        multi_select=True,
        searchable=True,
        placeholder="Select services...",
        show_icons=False,
        theme=theme,
    )


def context_selector_time_range(theme: str = "dark") -> rx.Component:
    """Preset: Time range selector"""
    ranges = [
        ("5m", "Last 5 minutes", "⏱️"),
        ("15m", "Last 15 minutes", "⏱️"),
        ("1h", "Last hour", "⏱️"),
        ("24h", "Last 24 hours", "⏱️"),
        ("7d", "Last 7 days", "📅"),
        ("30d", "Last 30 days", "📅"),
    ]
    return context_selector(
        items=ranges,
        selected=["1h"],
        multi_select=False,
        searchable=False,
        placeholder="Select time range...",
        show_icons=False,
        theme=theme,
    )
