"""
Workflows Page

Workflow orchestration monitoring with Gantt chart.
"""

import reflex as rx
from waooaw_portal.state.workflow_state import WorkflowState, Workflow, WorkflowTask


def get_status_color(status: str) -> str:
    """Get color for workflow status"""
    colors = {
        "pending": "#6b7280",    # Gray
        "running": "#3b82f6",    # Blue
        "completed": "#10b981",  # Green
        "failed": "#ef4444",     # Red
        "paused": "#f59e0b",     # Yellow
    }
    return colors.get(status, "#6b7280")


def workflow_card(workflow: Workflow) -> rx.Component:
    """Individual workflow card"""
    status_color = get_status_color(workflow.status)
    
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.text(
                        workflow.workflow_name,
                        font_size="1.125rem",
                        font_weight="600",
                        color="white",
                    ),
                    rx.text(
                        workflow.customer_name,
                        font_size="0.875rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                rx.badge(
                    workflow.status.upper(),
                    background=status_color,
                    color="white",
                    variant="solid",
                ),
                width="100%",
                justify_content="space-between",
                align_items="flex-start",
            ),
            # Progress bar
            rx.box(
                rx.box(
                    width=f"{workflow.progress}%",
                    height="100%",
                    background=status_color,
                    border_radius="0.25rem",
                    transition="width 0.3s ease",
                ),
                width="100%",
                height="0.5rem",
                background="#27272a",
                border_radius="0.25rem",
                margin_top="1rem",
            ),
            # Stats
            rx.hstack(
                rx.vstack(
                    rx.text(
                        str(workflow.total_tasks),
                        font_size="1.25rem",
                        font_weight="700",
                        color="white",
                    ),
                    rx.text(
                        "Total Tasks",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                rx.vstack(
                    rx.text(
                        str(workflow.completed_tasks),
                        font_size="1.25rem",
                        font_weight="700",
                        color="#10b981",
                    ),
                    rx.text(
                        "Completed",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                rx.vstack(
                    rx.text(
                        str(workflow.failed_tasks),
                        font_size="1.25rem",
                        font_weight="700",
                        color="#ef4444" if workflow.failed_tasks > 0 else "#6b7280",
                    ),
                    rx.text(
                        "Failed",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                spacing="8",
                width="100%",
                margin_top="1rem",
            ),
            # Timestamp
            rx.text(
                f"Created: {workflow.created_at}",
                font_size="0.75rem",
                color="#6b7280",
                margin_top="0.5rem",
            ),
            align_items="flex-start",
            spacing="2",
            width="100%",
        ),
        padding="1.5rem",
        background="#18181b",
        border=f"1px solid {status_color}",
        border_radius="1rem",
        _hover={
            "box_shadow": f"0 0 20px {status_color}33",
        },
        transition="all 0.3s ease",
        cursor="pointer",
        on_click=lambda: WorkflowState.select_workflow(workflow.workflow_id),
    )


def task_bar(task: WorkflowTask) -> rx.Component:
    """Gantt chart task bar"""
    status_color = get_status_color(task.status)
    
    return rx.box(
        rx.hstack(
            # Task info
            rx.vstack(
                rx.text(
                    task.task_name,
                    font_size="0.875rem",
                    font_weight="600",
                    color="white",
                ),
                rx.text(
                    task.agent_name,
                    font_size="0.75rem",
                    color="#9ca3af",
                ),
                align_items="flex-start",
                spacing="0.25rem",
                width="15rem",
            ),
            # Task bar
            rx.box(
                rx.hstack(
                    rx.badge(
                        task.status.upper(),
                        background=status_color,
                        color="white",
                        variant="solid",
                        font_size="0.625rem",
                    ),
                    rx.cond(
                        task.duration_sec > 0,
                        rx.text(
                            f"{task.duration_sec}s",
                            font_size="0.75rem",
                            color="white",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align_items="center",
                ),
                padding="0.5rem 1rem",
                background=f"{status_color}33",
                border=f"1px solid {status_color}",
                border_radius="0.5rem",
                flex="1",
            ),
            spacing="4",
            align_items="center",
            width="100%",
        ),
        padding="0.75rem",
        background="#18181b",
        border="1px solid #27272a",
        border_radius="0.5rem",
        _hover={
            "background": "#27272a",
        },
        transition="all 0.2s ease",
        cursor="pointer",
        on_click=lambda: WorkflowState.select_task(task.task_id),
    )


def gantt_chart() -> rx.Component:
    """Gantt chart visualization"""
    return rx.cond(
        WorkflowState.selected_workflow is not None,
        rx.box(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.text(
                        "Task Timeline",
                        font_size="1.25rem",
                        font_weight="600",
                        color="white",
                    ),
                    rx.text(
                        f"{WorkflowState.selected_workflow.completed_tasks}/{WorkflowState.selected_workflow.total_tasks} completed",
                        font_size="0.875rem",
                        color="#9ca3af",
                    ),
                    width="100%",
                    justify_content="space-between",
                    align_items="center",
                ),
                # Task bars
                rx.cond(
                    len(WorkflowState.selected_workflow.tasks) > 0,
                    rx.vstack(
                        rx.foreach(
                            WorkflowState.selected_workflow.tasks,
                            task_bar,
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.text(
                        "No task details available",
                        font_size="0.875rem",
                        color="#9ca3af",
                        padding="2rem",
                        text_align="center",
                    ),
                ),
                spacing="6",
                width="100%",
            ),
            padding="1.5rem",
            background="#18181b",
            border="1px solid #27272a",
            border_radius="1rem",
            margin_top="2rem",
        ),
        rx.fragment(),
    )


def task_inspector() -> rx.Component:
    """Task detail inspector"""
    return rx.cond(
        WorkflowState.show_task_inspector,
        rx.box(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.text(
                        "Task Details",
                        font_size="1.25rem",
                        font_weight="600",
                        color="white",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=16),
                        size="2",
                        variant="ghost",
                        on_click=WorkflowState.close_task_inspector,
                    ),
                    width="100%",
                    align_items="center",
                ),
                # Task info
                rx.cond(
                    WorkflowState.selected_task is not None,
                    rx.vstack(
                        # Basic info
                        rx.hstack(
                            rx.vstack(
                                rx.text("Task Name", font_size="0.75rem", color="#9ca3af"),
                                rx.text(
                                    WorkflowState.selected_task.task_name,
                                    font_size="1rem",
                                    font_weight="600",
                                    color="white",
                                ),
                                align_items="flex-start",
                                spacing="0.25rem",
                            ),
                            rx.badge(
                                WorkflowState.selected_task.status.upper(),
                                background=get_status_color(WorkflowState.selected_task.status),
                                color="white",
                                variant="solid",
                            ),
                            width="100%",
                            justify_content="space-between",
                            align_items="flex-start",
                        ),
                        # Agent
                        rx.vstack(
                            rx.text("Assigned Agent", font_size="0.75rem", color="#9ca3af"),
                            rx.text(
                                WorkflowState.selected_task.agent_name,
                                font_size="1rem",
                                color="white",
                            ),
                            align_items="flex-start",
                            spacing="0.25rem",
                            margin_top="1rem",
                        ),
                        # Duration
                        rx.cond(
                            WorkflowState.selected_task.duration_sec > 0,
                            rx.vstack(
                                rx.text("Duration", font_size="0.75rem", color="#9ca3af"),
                                rx.text(
                                    f"{WorkflowState.selected_task.duration_sec} seconds",
                                    font_size="1rem",
                                    color="white",
                                ),
                                align_items="flex-start",
                                spacing="0.25rem",
                                margin_top="1rem",
                            ),
                            rx.fragment(),
                        ),
                        # Error message
                        rx.cond(
                            WorkflowState.selected_task.error_message is not None,
                            rx.vstack(
                                rx.text("Error", font_size="0.75rem", color="#9ca3af"),
                                rx.text(
                                    WorkflowState.selected_task.error_message,
                                    font_size="0.875rem",
                                    color="#ef4444",
                                ),
                                align_items="flex-start",
                                spacing="0.25rem",
                                margin_top="1rem",
                            ),
                            rx.fragment(),
                        ),
                        # Dependencies
                        rx.cond(
                            len(WorkflowState.selected_task.dependencies) > 0,
                            rx.vstack(
                                rx.text("Dependencies", font_size="0.75rem", color="#9ca3af"),
                                rx.hstack(
                                    rx.foreach(
                                        WorkflowState.selected_task.dependencies,
                                        lambda dep: rx.badge(dep, color_scheme="gray"),
                                    ),
                                    spacing="2",
                                    wrap="wrap",
                                ),
                                align_items="flex-start",
                                spacing="2",
                                margin_top="1rem",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.text(
                        "No task selected",
                        font_size="0.875rem",
                        color="#9ca3af",
                        padding="2rem",
                        text_align="center",
                    ),
                ),
                spacing="6",
                width="100%",
            ),
            padding="1.5rem",
            background="#18181b",
            border="1px solid #27272a",
            border_radius="1rem",
            margin_top="2rem",
        ),
        rx.fragment(),
    )


def workflow_actions() -> rx.Component:
    """Workflow action buttons"""
    return rx.cond(
        WorkflowState.selected_workflow is not None,
        rx.hstack(
            rx.cond(
                WorkflowState.selected_workflow.status == "running",
                rx.button(
                    "Pause",
                    size="2",
                    color_scheme="yellow",
                    on_click=lambda: WorkflowState.pause_workflow(WorkflowState.selected_workflow.workflow_id),
                ),
                rx.fragment(),
            ),
            rx.cond(
                WorkflowState.selected_workflow.status == "paused",
                rx.button(
                    "Resume",
                    size="2",
                    color_scheme="cyan",
                    on_click=lambda: WorkflowState.resume_workflow(WorkflowState.selected_workflow.workflow_id),
                ),
                rx.fragment(),
            ),
            rx.cond(
                WorkflowState.selected_workflow.status == "failed",
                rx.button(
                    "Retry",
                    size="2",
                    color_scheme="green",
                    on_click=lambda: WorkflowState.retry_workflow(WorkflowState.selected_workflow.workflow_id),
                ),
                rx.fragment(),
            ),
            rx.button(
                "Cancel",
                size="2",
                color_scheme="red",
                variant="outline",
                on_click=lambda: WorkflowState.cancel_workflow(WorkflowState.selected_workflow.workflow_id),
            ),
            rx.button(
                "Close",
                size="2",
                variant="ghost",
                on_click=WorkflowState.close_workflow_detail,
            ),
            spacing="2",
        ),
        rx.fragment(),
    )


def stats_bar() -> rx.Component:
    """Workflow statistics bar"""
    return rx.hstack(
        rx.vstack(
            rx.text(
                str(WorkflowState.workflow_count),
                font_size="1.5rem",
                font_weight="700",
                color="white",
            ),
            rx.text(
                "Total Workflows",
                font_size="0.75rem",
                color="#9ca3af",
            ),
            align_items="flex-start",
            spacing="0.25rem",
        ),
        rx.vstack(
            rx.text(
                str(WorkflowState.running_count),
                font_size="1.5rem",
                font_weight="700",
                color="#3b82f6",
            ),
            rx.text(
                "Running",
                font_size="0.75rem",
                color="#9ca3af",
            ),
            align_items="flex-start",
            spacing="0.25rem",
        ),
        rx.vstack(
            rx.text(
                str(WorkflowState.completed_count),
                font_size="1.5rem",
                font_weight="700",
                color="#10b981",
            ),
            rx.text(
                "Completed",
                font_size="0.75rem",
                color="#9ca3af",
            ),
            align_items="flex-start",
            spacing="0.25rem",
        ),
        rx.vstack(
            rx.text(
                str(WorkflowState.failed_count),
                font_size="1.5rem",
                font_weight="700",
                color="#ef4444",
            ),
            rx.text(
                "Failed",
                font_size="0.75rem",
                color="#9ca3af",
            ),
            align_items="flex-start",
            spacing="0.25rem",
        ),
        # Filters
        rx.select(
            ["all", "running", "completed", "failed"],
            value=WorkflowState.status_filter,
            on_change=WorkflowState.set_status_filter,
            size="2",
        ),
        rx.button(
            "Refresh",
            on_click=WorkflowState.load_workflows,
            size="2",
            color_scheme="cyan",
            variant="outline",
        ),
        spacing="8",
        align_items="center",
        width="100%",
        padding="1.5rem",
        background="#18181b",
        border="1px solid #27272a",
        border_radius="1rem",
    )


def workflows_grid() -> rx.Component:
    """Grid of workflow cards"""
    return rx.box(
        rx.foreach(
            WorkflowState.filtered_workflows,
            workflow_card,
        ),
        display="grid",
        grid_template_columns="repeat(auto-fill, minmax(20rem, 1fr))",
        gap="1.5rem",
        width="100%",
    )


def workflows_page() -> rx.Component:
    """
    Workflows orchestration monitoring page.
    
    Features:
    - Real-time workflow tracking
    - Gantt chart visualization
    - Task inspector
    - Workflow actions (pause, resume, retry)
    """
    return rx.box(
        rx.vstack(
            # Header
            rx.text(
                "Workflow Orchestration",
                font_size="2rem",
                font_weight="700",
                color="white",
            ),
            # Stats
            stats_bar(),
            # Workflows grid
            workflows_grid(),
            # Gantt chart
            gantt_chart(),
            # Workflow actions
            workflow_actions(),
            # Task inspector
            task_inspector(),
            spacing="8",
            width="100%",
            max_width="90rem",
            margin="0 auto",
            padding="2rem",
        ),
        width="100%",
        min_height="100vh",
        background="#0a0a0a",
        on_mount=WorkflowState.load_workflows,
    )
