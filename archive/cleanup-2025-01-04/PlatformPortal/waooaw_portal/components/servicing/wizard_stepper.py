"""Wizard stepper component for upgrade process"""

import reflex as rx


def wizard_stepper(current_step: int) -> rx.Component:
    """Render upgrade wizard step indicator"""
    
    return rx.hstack(
        # Step 0 - Plan
        step_indicator(0, "Plan", "clipboard-list", current_step),
        connector_line(0, current_step),
        
        # Step 1 - Backup
        step_indicator(1, "Backup", "database", current_step),
        connector_line(1, current_step),
        
        # Step 2 - Deploy
        step_indicator(2, "Deploy", "rocket", current_step),
        connector_line(2, current_step),
        
        # Step 3 - Test
        step_indicator(3, "Test", "check-circle", current_step),
        connector_line(3, current_step),
        
        # Step 4 - Cutover
        step_indicator(4, "Cutover", "repeat", current_step),
        connector_line(4, current_step),
        
        # Step 5 - Verify
        step_indicator(5, "Verify", "shield-check", current_step),
        
        justify="center",
        align_items="center",
        width="100%",
        padding="1rem 0",
    )


def step_indicator(step_num: int, label: str, icon: str, current_step: int) -> rx.Component:
    """Individual step indicator"""
    return rx.vstack(
        rx.box(
            rx.cond(
                current_step > step_num,
                rx.icon("check", size=20, color="white"),
                rx.cond(
                    current_step == step_num,
                    rx.icon(icon, size=20, color="white"),
                    rx.text(str(step_num + 1), color="gray", weight="bold"),
                ),
            ),
            background=rx.cond(
                current_step >= step_num,
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
            label,
            font_size="0.9rem",
            font_weight=rx.cond(
                current_step == step_num,
                "bold",
                "normal",
            ),
            color=rx.cond(
                current_step >= step_num,
                "cyan",
                "gray",
            ),
        ),
        align_items="center",
        spacing="2",
    )


def connector_line(step_num: int, current_step: int) -> rx.Component:
    """Connector line between steps"""
    return rx.cond(
        step_num < 5,  # Show connector for steps 0-4
        rx.box(
            width="80px",
            height="2px",
            background=rx.cond(
                current_step > step_num,
                "var(--cyan-9)",
                "var(--gray-6)",
            ),
            margin="0 1rem",
            margin_bottom="2rem",
        ),
        rx.fragment(),
    )

