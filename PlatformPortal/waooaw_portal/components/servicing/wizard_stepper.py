"""Wizard stepper component for upgrade process"""

import reflex as rx


def wizard_stepper(current_step: int) -> rx.Component:
    """Render upgrade wizard step indicator"""
    
    steps = [
        {"number": 0, "label": "Plan", "icon": "clipboard-list"},
        {"number": 1, "label": "Backup", "icon": "database"},
        {"number": 2, "label": "Deploy", "icon": "rocket"},
        {"number": 3, "label": "Test", "icon": "check-circle"},
        {"number": 4, "label": "Cutover", "icon": "repeat"},
        {"number": 5, "label": "Verify", "icon": "shield-check"},
    ]
    
    return rx.hstack(
        rx.foreach(
            steps,
            lambda step, idx: rx.fragment(
                # Step circle
                rx.vstack(
                    rx.box(
                        rx.cond(
                            current_step > step["number"],
                            rx.icon("check", size=20, color="white"),
                            rx.cond(
                                current_step == step["number"],
                                rx.icon(step["icon"], size=20, color="white"),
                                rx.text(step["number"] + 1, color="gray", weight="bold"),
                            ),
                        ),
                        background=rx.cond(
                            current_step >= step["number"],
                            "var(--cyan-9)",
                            "var(--gray-6)",
                        ),
                        border_radius="50%",
                        width="48px",
                        height="48px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.text(
                        step["label"],
                        font_size="0.9rem",
                        font_weight=rx.cond(
                            current_step == step["number"],
                            "bold",
                            "normal",
                        ),
                        color=rx.cond(
                            current_step >= step["number"],
                            "cyan",
                            "gray",
                        ),
                    ),
                    align_items="center",
                    spacing="2",
                ),
                
                # Connector line
                rx.cond(
                    idx < 5,
                    rx.box(
                        width="80px",
                        height="2px",
                        background=rx.cond(
                            current_step > step["number"],
                            "var(--cyan-9)",
                            "var(--gray-6)",
                        ),
                        margin="0 1rem",
                        margin_bottom="2rem",
                    ),
                    rx.fragment(),
                ),
            ),
        ),
        justify="center",
        align_items="center",
        width="100%",
        padding="1rem 0",
    )
