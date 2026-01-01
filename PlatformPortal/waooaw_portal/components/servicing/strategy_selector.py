"""Deployment strategy selector component"""

import reflex as rx
from ...state.servicing_state import ServicingState


def strategy_selector() -> rx.Component:
    """Render deployment strategy selection"""
    
    return rx.grid(
        rx.foreach(
            ServicingState.strategies,
            lambda strategy: rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.text(strategy.icon, font_size="2rem"),
                        rx.vstack(
                            rx.text(strategy.name, weight="bold", font_size="1.1rem"),
                            rx.badge(
                                f"Risk: {strategy.risk_level}",
                                color_scheme=rx.cond(
                                    strategy.risk_level == "low",
                                    "green",
                                    rx.cond(
                                        strategy.risk_level == "medium",
                                        "yellow",
                                        "red",
                                    ),
                                ),
                            ),
                            align_items="start",
                            spacing="0.25rem",
                        ),
                        spacing="1rem",
                        align_items="center",
                    ),
                    
                    rx.text(strategy.description, color="gray", font_size="0.9rem", margin_top="0.5rem"),
                    
                    rx.hstack(
                        rx.hstack(
                            rx.icon("clock", size=16, color="gray"),
                            rx.text(strategy.estimated_time, font_size="0.85rem", color="gray"),
                        ),
                        rx.hstack(
                            rx.icon(
                                "shield-check" if strategy.supports_rollback else "shield-off",
                                size=16,
                                color="green" if strategy.supports_rollback else "red",
                            ),
                            rx.text(
                                "Rollback supported" if strategy.supports_rollback else "No rollback",
                                font_size="0.85rem",
                                color="green" if strategy.supports_rollback else "red",
                            ),
                        ),
                        margin_top="0.5rem",
                    ),
                    
                    rx.button(
                        "Select Strategy",
                        on_click=ServicingState.select_strategy(strategy.strategy_id),
                        color_scheme=rx.cond(
                            ServicingState.selected_strategy == strategy.strategy_id,
                            "cyan",
                            "gray",
                        ),
                        width="100%",
                        margin_top="1rem",
                    ),
                    
                    align_items="start",
                    spacing="0.5rem",
                    width="100%",
                ),
                padding="1.5rem",
                cursor="pointer",
                _hover={
                    "box_shadow": "0 0 20px rgba(0, 242, 254, 0.3)",
                    "border_color": "var(--cyan-9)",
                },
                border=rx.cond(
                    ServicingState.selected_strategy == strategy.strategy_id,
                    "2px solid var(--cyan-9)",
                    "1px solid var(--gray-6)",
                ),
            ),
        ),
        columns="3",
        spacing="1rem",
        width="100%",
    )
