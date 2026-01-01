"""
Navigation Header

Shared navigation component with context selector.
"""

import reflex as rx
from waooaw_portal.state.auth_state import AuthState
from waooaw_portal.components.common.context_selector_enhanced import context_selector_enhanced


def navigation_header() -> rx.Component:
    """
    Main navigation header.
    
    Features:
    - WAOOAW logo and branding
    - Navigation links (Dashboard, Agents)
    - Context selector (global filter)
    - User menu with profile and logout
    """
    return rx.box(
        rx.hstack(
            # Logo + Nav
            rx.hstack(
                # Logo
                rx.link(
                    rx.hstack(
                        rx.text(
                            "WAOOAW",
                            font_size="1.5rem",
                            font_weight="700",
                            background="linear-gradient(135deg, #00f2fe, #667eea)",
                            background_clip="text",
                            color="transparent",
                        ),
                        rx.badge(
                            "Portal",
                            color_scheme="cyan",
                            variant="subtle",
                        ),
                        spacing="0.75rem",
                        align_items="center",
                    ),
                    href="/",
                ),
                # Navigation links
                rx.hstack(
                    rx.link(
                        rx.button(
                            "Dashboard",
                            variant="ghost",
                            color_scheme="gray",
                        ),
                        href="/",
                    ),
                    rx.link(
                        rx.button(
                            "Agents",
                            variant="ghost",
                            color_scheme="gray",
                        ),
                        href="/agents",
                    ),
                    spacing="0.5rem",
                    margin_left="2rem",
                ),
                spacing="1rem",
                align_items="center",
            ),
            rx.spacer(),
            # Right side: Context selector + User menu
            rx.hstack(
                # Context selector
                context_selector_enhanced(),
                # User menu
                rx.menu(
                    rx.menu_button(
                        rx.hstack(
                            rx.avatar(
                                name=AuthState.user_display_name,
                                size="sm",
                                bg="linear-gradient(135deg, #667eea, #f093fb)",
                            ),
                            rx.vstack(
                                rx.text(
                                    AuthState.user_display_name,
                                    font_size="0.875rem",
                                    font_weight="500",
                                    color="white",
                                ),
                                rx.badge(
                                    AuthState.role,
                                    color_scheme=AuthState.role_badge_color,
                                    size="xs",
                                ),
                                spacing="0.25rem",
                                align_items="flex-start",
                            ),
                            rx.icon("chevron_down", size=16),
                            spacing="0.75rem",
                            align_items="center",
                        ),
                        variant="ghost",
                    ),
                    rx.menu_list(
                        rx.menu_item("Profile", icon="user"),
                        rx.menu_item("Settings", icon="settings"),
                        rx.menu_divider(),
                        rx.menu_item(
                            "Logout",
                            icon="log_out",
                            on_click=AuthState.logout,
                            color="red",
                        ),
                    ),
                ),
                spacing="1rem",
                align_items="center",
            ),
            width="100%",
            align_items="center",
            padding="1rem 2rem",
        ),
        width="100%",
        background="#18181b",
        border_bottom="1px solid #27272a",
        position="sticky",
        top="0",
        z_index="100",
    )
