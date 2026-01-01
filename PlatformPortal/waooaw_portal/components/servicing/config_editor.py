"""Hot configuration editor component"""

import reflex as rx
from ...state.servicing_state import ServicingState


def config_editor() -> rx.Component:
    """Render hot configuration patch editor"""
    
    return rx.vstack(
        rx.heading("Hot Configuration Patching", size="5", weight="bold"),
        rx.text("Update agent configuration without restart", color="gray"),
        
        rx.card(
            rx.vstack(
                rx.vstack(
                    rx.text("Memory Limit (MB):", weight="bold"),
                    rx.input(
                        placeholder="2048",
                        on_change=lambda v: ServicingState.update_config_patch("memory_limit_mb", v),
                        width="100%",
                    ),
                    align_items="start",
                    width="100%",
                ),
                
                rx.vstack(
                    rx.text("Environment Variables:", weight="bold"),
                    rx.text_area(
                        placeholder="KEY1=value1\nKEY2=value2",
                        on_change=lambda v: ServicingState.update_config_patch("env_vars", v),
                        width="100%",
                        rows=4,
                    ),
                    align_items="start",
                    width="100%",
                ),
                
                rx.vstack(
                    rx.text("Feature Flags:", weight="bold"),
                    rx.hstack(
                        rx.checkbox(
                            "Enable Beta Features",
                            on_change=lambda v: ServicingState.update_config_patch("beta_features", v),
                        ),
                        rx.checkbox(
                            "Debug Mode",
                            on_change=lambda v: ServicingState.update_config_patch("debug_mode", v),
                        ),
                    ),
                    align_items="start",
                    width="100%",
                ),
                
                rx.button(
                    "Apply Patches",
                    on_click=ServicingState.apply_config_patches,
                    color_scheme="cyan",
                    size="3",
                    margin_top="1rem",
                ),
                
                align_items="start",
                spacing="1.5rem",
                width="100%",
            ),
            padding="1.5rem",
            width="100%",
        ),
        
        rx.callout(
            rx.icon("zap", size=20),
            rx.text("Configuration changes are applied instantly without restarting agents."),
            color_scheme="blue",
            margin_top="1rem",
            width="100%",
        ),
        
        width="100%",
        align_items="start",
        spacing="1rem",
    )
