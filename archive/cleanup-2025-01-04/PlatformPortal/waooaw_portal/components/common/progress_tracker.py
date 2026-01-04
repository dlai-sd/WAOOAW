"""
Progress Tracker Component

Multi-step workflow progress visualization with status indicators.
Used for agent provisioning, deployment pipelines, and multi-stage processes.
"""

from typing import Optional, List, Tuple
import reflex as rx
from waooaw_portal.theme import get_theme, get_status_emoji


def progress_tracker(
    steps: List[Tuple[str, str, Optional[str]]],  # (label, status, description)
    current_step: int = 0,
    orientation: str = "horizontal",
    show_descriptions: bool = True,
    show_step_numbers: bool = True,
    theme: str = "dark",
) -> rx.Component:
    """
    Display multi-step progress tracker.

    Args:
        steps: List of steps (label, status, description)
               status: 'completed', 'current', 'pending', 'error', 'skipped'
        current_step: Current step index (0-based)
        orientation: 'horizontal' or 'vertical'
        show_descriptions: Show step descriptions
        show_step_numbers: Show step numbers
        theme: Color theme

    Returns:
        Progress tracker component
    """
    theme_colors = get_theme(theme)

    if orientation == "horizontal":
        return _horizontal_progress_tracker(
            steps, current_step, show_descriptions, show_step_numbers, theme
        )
    else:
        return _vertical_progress_tracker(
            steps, current_step, show_descriptions, show_step_numbers, theme
        )


def _horizontal_progress_tracker(
    steps: List[Tuple[str, str, Optional[str]]],
    current_step: int,
    show_descriptions: bool,
    show_step_numbers: bool,
    theme: str,
) -> rx.Component:
    """Horizontal progress tracker layout"""
    theme_colors = get_theme(theme)

    step_components = []
    for idx, (label, status, description) in enumerate(steps):
        step_comp = _progress_step(
            label=label,
            status=status,
            description=description if show_descriptions else None,
            step_number=idx + 1 if show_step_numbers else None,
            is_current=idx == current_step,
            theme=theme,
        )
        step_components.append(step_comp)

        # Add connector line (except after last step)
        if idx < len(steps) - 1:
            next_status = steps[idx + 1][1]
            connector = _step_connector(
                completed=status == "completed",
                orientation="horizontal",
                theme=theme,
            )
            step_components.append(connector)

    return rx.box(
        rx.hstack(
            *step_components,
            spacing="0",
            align_items="flex-start",
            width="100%",
        ),
        width="100%",
        padding="1.5rem",
        background=theme_colors["bg_secondary"],
        border=f"1px solid {theme_colors['border']}",
        border_radius="1rem",
    )


def _vertical_progress_tracker(
    steps: List[Tuple[str, str, Optional[str]]],
    current_step: int,
    show_descriptions: bool,
    show_step_numbers: bool,
    theme: str,
) -> rx.Component:
    """Vertical progress tracker layout"""
    theme_colors = get_theme(theme)

    step_components = []
    for idx, (label, status, description) in enumerate(steps):
        step_comp = _progress_step_vertical(
            label=label,
            status=status,
            description=description if show_descriptions else None,
            step_number=idx + 1 if show_step_numbers else None,
            is_current=idx == current_step,
            theme=theme,
        )
        step_components.append(step_comp)

        # Add connector line (except after last step)
        if idx < len(steps) - 1:
            connector = _step_connector(
                completed=status == "completed", orientation="vertical", theme=theme
            )
            step_components.append(connector)

    return rx.box(
        rx.vstack(
            *step_components,
            spacing="0",
            align_items="flex-start",
            width="100%",
        ),
        width="100%",
        padding="1.5rem",
        background=theme_colors["bg_secondary"],
        border=f"1px solid {theme_colors['border']}",
        border_radius="1rem",
    )


def _progress_step(
    label: str,
    status: str,
    description: Optional[str],
    step_number: Optional[int],
    is_current: bool,
    theme: str,
) -> rx.Component:
    """Single progress step (horizontal)"""
    theme_colors = get_theme(theme)

    # Status colors
    status_colors = {
        "completed": theme_colors["success"],
        "current": theme_colors["primary"],
        "pending": theme_colors["text_tertiary"],
        "error": theme_colors["error"],
        "skipped": theme_colors["text_tertiary"],
    }
    status_color = status_colors.get(status, theme_colors["text_tertiary"])

    # Status icons
    status_icons = {
        "completed": "✓",
        "current": "⟳",
        "pending": step_number or "○",
        "error": "✕",
        "skipped": "⊘",
    }
    icon = status_icons.get(status, "○")

    return rx.vstack(
        # Step indicator
        rx.box(
            rx.text(
                str(icon),
                color="white"
                if status in ["completed", "current", "error"]
                else status_color,
                font_size="1rem",
                font_weight="700",
            ),
            width="40px",
            height="40px",
            border_radius="50%",
            background=status_color
            if status in ["completed", "current", "error"]
            else "transparent",
            border=f"2px solid {status_color}",
            display="flex",
            align_items="center",
            justify_content="center",
            transition="all 0.3s ease",
            _hover={
                "transform": "scale(1.1)",
                "box_shadow": f"0 0 15px {status_color}60",
            }
            if is_current
            else {},
        ),
        # Label
        rx.text(
            label,
            font_size="0.875rem",
            font_weight="600" if is_current else "500",
            color=theme_colors["text_primary"]
            if is_current
            else theme_colors["text_secondary"],
            text_align="center",
            margin_top="0.5rem",
        ),
        # Description
        rx.text(
            description,
            font_size="0.75rem",
            color=theme_colors["text_tertiary"],
            text_align="center",
            margin_top="0.25rem",
            max_width="150px",
        )
        if description
        else rx.fragment(),
        align_items="center",
        spacing="0",
        flex="0 0 auto",
    )


def _progress_step_vertical(
    label: str,
    status: str,
    description: Optional[str],
    step_number: Optional[int],
    is_current: bool,
    theme: str,
) -> rx.Component:
    """Single progress step (vertical)"""
    theme_colors = get_theme(theme)

    status_colors = {
        "completed": theme_colors["success"],
        "current": theme_colors["primary"],
        "pending": theme_colors["text_tertiary"],
        "error": theme_colors["error"],
        "skipped": theme_colors["text_tertiary"],
    }
    status_color = status_colors.get(status, theme_colors["text_tertiary"])

    status_icons = {
        "completed": "✓",
        "current": "⟳",
        "pending": step_number or "○",
        "error": "✕",
        "skipped": "⊘",
    }
    icon = status_icons.get(status, "○")

    return rx.hstack(
        # Step indicator
        rx.box(
            rx.text(
                str(icon),
                color="white"
                if status in ["completed", "current", "error"]
                else status_color,
                font_size="0.875rem",
                font_weight="700",
            ),
            width="32px",
            height="32px",
            border_radius="50%",
            background=status_color
            if status in ["completed", "current", "error"]
            else "transparent",
            border=f"2px solid {status_color}",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        # Content
        rx.vstack(
            rx.text(
                label,
                font_size="0.875rem",
                font_weight="600" if is_current else "500",
                color=theme_colors["text_primary"]
                if is_current
                else theme_colors["text_secondary"],
            ),
            rx.text(
                description,
                font_size="0.75rem",
                color=theme_colors["text_tertiary"],
                line_height="1.4",
            )
            if description
            else rx.fragment(),
            spacing="0.25rem",
            align_items="flex-start",
        ),
        spacing="0.75rem",
        align_items="center",
    )


def _step_connector(completed: bool, orientation: str, theme: str) -> rx.Component:
    """Connector line between steps"""
    theme_colors = get_theme(theme)
    color = theme_colors["success"] if completed else theme_colors["border"]

    if orientation == "horizontal":
        return rx.box(
            width="60px",
            height="2px",
            background=color,
            margin_y="19px",
            flex="0 0 auto",
        )
    else:
        return rx.box(
            width="2px",
            height="30px",
            background=color,
            margin_left="15px",
        )


# Preset progress trackers
def progress_agent_provisioning(
    current_step: int = 0, theme: str = "dark"
) -> rx.Component:
    """Preset: Agent provisioning progress"""
    steps = [
        ("Initialize", "completed", "Setting up environment"),
        ("Configure", "current", "Applying configuration"),
        ("Deploy", "pending", "Deploying to cluster"),
        ("Verify", "pending", "Health checks"),
        ("Complete", "pending", "Agent ready"),
    ]
    return progress_tracker(steps, current_step, theme=theme)


def progress_deployment_pipeline(
    current_step: int = 0, theme: str = "dark"
) -> rx.Component:
    """Preset: Deployment pipeline progress"""
    steps = [
        ("Build", "completed", None),
        ("Test", "completed", None),
        ("Stage", "current", None),
        ("Production", "pending", None),
    ]
    return progress_tracker(steps, current_step, show_descriptions=False, theme=theme)


def progress_upgrade_workflow(
    current_step: int = 0, theme: str = "dark"
) -> rx.Component:
    """Preset: Agent upgrade workflow (vertical)"""
    steps = [
        ("Backup", "completed", "Configuration backed up"),
        ("Stop", "completed", "Agent stopped gracefully"),
        ("Upgrade", "current", "Installing new version"),
        ("Migrate", "pending", "Database migration"),
        ("Start", "pending", "Starting upgraded agent"),
        ("Verify", "pending", "Post-upgrade checks"),
    ]
    return progress_tracker(steps, current_step, orientation="vertical", theme=theme)
