"""
Queues Page

Real-time queue monitoring with DLQ management.
"""

import reflex as rx
from waooaw_portal.state.queue_state import QueueState, QueueMetrics, DLQMessage


def get_status_color(status: str) -> str:
    """Get color for queue status"""
    colors = {
        "healthy": "#10b981",   # Green
        "degraded": "#f59e0b",  # Yellow
        "critical": "#ef4444",  # Red
    }
    return colors.get(status, "#6b7280")


def queue_card(queue: QueueMetrics) -> rx.Component:
    """Individual queue card"""
    status_color = get_status_color(queue.status)
    
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.text(
                    queue.queue_name,
                    font_size="1.125rem",
                    font_weight="600",
                    color="white",
                ),
                rx.badge(
                    queue.status.upper(),
                    background=status_color,
                    color="white",
                    variant="solid",
                ),
                width="100%",
                justify_content="space-between",
                align_items="center",
            ),
            # Metrics grid
            rx.grid(
                # Messages pending
                rx.vstack(
                    rx.text(
                        str(queue.messages_pending),
                        font_size="1.5rem",
                        font_weight="700",
                        color="#00f2fe",
                    ),
                    rx.text(
                        "Pending",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                # Throughput
                rx.vstack(
                    rx.text(
                        f"{queue.throughput_per_sec}/s",
                        font_size="1.5rem",
                        font_weight="700",
                        color="#667eea",
                    ),
                    rx.text(
                        "Throughput",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                # Consumer lag
                rx.vstack(
                    rx.text(
                        str(queue.consumer_lag),
                        font_size="1.5rem",
                        font_weight="700",
                        color="#f59e0b",
                    ),
                    rx.text(
                        "Lag",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                # Error rate
                rx.vstack(
                    rx.text(
                        f"{queue.error_rate}%",
                        font_size="1.5rem",
                        font_weight="700",
                        color="#ef4444" if queue.error_rate > 1.0 else "#10b981",
                    ),
                    rx.text(
                        "Error Rate",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                columns="4",
                spacing="4",
                width="100%",
                margin_top="1rem",
            ),
            # Oldest message age
            rx.text(
                f"Oldest message: {queue.oldest_message_age_sec}s ago",
                font_size="0.75rem",
                color="#6b7280",
                margin_top="1rem",
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
        on_click=lambda: QueueState.select_queue(queue.queue_name),
    )


def dlq_message_card(msg: DLQMessage) -> rx.Component:
    """DLQ message card"""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.text(
                        msg.queue_name,
                        font_size="1rem",
                        font_weight="600",
                        color="white",
                    ),
                    rx.text(
                        msg.message_id,
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.25rem",
                ),
                rx.badge(
                    f"Retry: {msg.retry_count}",
                    color_scheme="red",
                    variant="solid",
                ),
                width="100%",
                justify_content="space-between",
                align_items="flex-start",
            ),
            # Error message
            rx.text(
                f"Error: {msg.error_message}",
                font_size="0.875rem",
                color="#ef4444",
                margin_top="0.5rem",
            ),
            # Payload
            rx.box(
                rx.text(
                    msg.payload,
                    font_size="0.75rem",
                    color="#d1d5db",
                    font_family="monospace",
                ),
                padding="0.75rem",
                background="#0a0a0a",
                border="1px solid #27272a",
                border_radius="0.5rem",
                width="100%",
                overflow_x="auto",
                margin_top="0.5rem",
            ),
            # Timestamps
            rx.hstack(
                rx.text(
                    f"Created: {msg.created_at}",
                    font_size="0.75rem",
                    color="#6b7280",
                ),
                rx.cond(
                    msg.last_retry_at is not None,
                    rx.text(
                        f"Last retry: {msg.last_retry_at}",
                        font_size="0.75rem",
                        color="#6b7280",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                margin_top="0.5rem",
            ),
            # Actions
            rx.hstack(
                rx.button(
                    "Retry",
                    size="2",
                    color_scheme="cyan",
                    on_click=lambda: QueueState.retry_message(msg.message_id),
                ),
                rx.button(
                    "Delete",
                    size="2",
                    color_scheme="red",
                    variant="outline",
                    on_click=lambda: QueueState.delete_message(msg.message_id),
                ),
                spacing="2",
                margin_top="1rem",
            ),
            align_items="flex-start",
            spacing="0.25rem",
            width="100%",
        ),
        padding="1rem",
        background="#18181b",
        border="1px solid #27272a",
        border_radius="0.75rem",
    )


def dlq_panel() -> rx.Component:
    """Dead Letter Queue panel"""
    return rx.cond(
        QueueState.show_dlq_panel,
        rx.box(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.text(
                        "Dead Letter Queue",
                        font_size="1.25rem",
                        font_weight="600",
                        color="white",
                    ),
                    rx.badge(
                        f"{QueueState.dlq_count} messages",
                        color_scheme="red",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=16),
                        size="2",
                        variant="ghost",
                        on_click=QueueState.close_dlq_panel,
                    ),
                    width="100%",
                    align_items="center",
                ),
                # DLQ messages
                rx.cond(
                    QueueState.dlq_count > 0,
                    rx.vstack(
                        rx.foreach(
                            QueueState.dlq_messages,
                            dlq_message_card,
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    rx.text(
                        "No failed messages",
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


def stats_bar() -> rx.Component:
    """Queue statistics bar"""
    return rx.hstack(
        rx.vstack(
            rx.text(
                str(QueueState.queue_count),
                font_size="1.5rem",
                font_weight="700",
                color="white",
            ),
            rx.text(
                "Total Queues",
                font_size="0.75rem",
                color="#9ca3af",
            ),
            align_items="flex-start",
            spacing="0.25rem",
        ),
        rx.vstack(
            rx.text(
                str(QueueState.healthy_count),
                font_size="1.5rem",
                font_weight="700",
                color="#10b981",
            ),
            rx.text(
                "Healthy",
                font_size="0.75rem",
                color="#9ca3af",
            ),
            align_items="flex-start",
            spacing="0.25rem",
        ),
        rx.vstack(
            rx.text(
                str(QueueState.degraded_count),
                font_size="1.5rem",
                font_weight="700",
                color="#f59e0b",
            ),
            rx.text(
                "Degraded",
                font_size="0.75rem",
                color="#9ca3af",
            ),
            align_items="flex-start",
            spacing="0.25rem",
        ),
        rx.vstack(
            rx.text(
                str(QueueState.critical_count),
                font_size="1.5rem",
                font_weight="700",
                color="#ef4444",
            ),
            rx.text(
                "Critical",
                font_size="0.75rem",
                color="#9ca3af",
            ),
            align_items="flex-start",
            spacing="0.25rem",
        ),
        rx.button(
            f"View DLQ ({QueueState.dlq_count})",
            on_click=QueueState.load_dlq,
            size="2",
            color_scheme="red",
            variant="outline",
        ),
        rx.button(
            "Refresh",
            on_click=QueueState.load_queues,
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


def queues_grid() -> rx.Component:
    """Grid of queue cards"""
    return rx.box(
        rx.foreach(
            QueueState.queues,
            queue_card,
        ),
        display="grid",
        grid_template_columns="repeat(auto-fill, minmax(20rem, 1fr))",
        gap="1.5rem",
        width="100%",
    )


def queues_page() -> rx.Component:
    """
    Queues monitoring page.
    
    Features:
    - Real-time queue metrics
    - Queue health status
    - DLQ management
    - Message retry
    """
    return rx.box(
        rx.vstack(
            # Header
            rx.text(
                "Queue Monitoring",
                font_size="2rem",
                font_weight="700",
                color="white",
            ),
            # Stats
            stats_bar(),
            # Queues grid
            queues_grid(),
            # DLQ panel
            dlq_panel(),
            spacing="8",
            width="100%",
            max_width="90rem",
            margin="0 auto",
            padding="2rem",
        ),
        width="100%",
        min_height="100vh",
        background="#0a0a0a",
        on_mount=QueueState.load_queues,
    )
