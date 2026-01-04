"""
Queues Page

Real-time queue monitoring with DLQ management.
"""

import reflex as rx
from waooaw_portal.state.queue_state import QueueState, QueueMetrics, DLQMessage
from waooaw_portal.state.theme_state import ThemeState


def queue_card(queue: QueueMetrics) -> rx.Component:
    """Individual queue card"""
    # Use rx.cond to dynamically select status color based on queue.status
    status_color = rx.cond(
        queue.status == "healthy",
        ThemeState.theme["status_success"],
        rx.cond(
            queue.status == "degraded",
            ThemeState.theme["status_warning"],
            rx.cond(
                queue.status == "critical",
                ThemeState.theme["status_error"],
                ThemeState.theme["text_tertiary"]
            )
        )
    )
    
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.text(
                    queue.queue_name,
                    font_size="1.125rem",
                    font_weight="600",
                    color=ThemeState.theme["text_primary"],
                ),
                rx.badge(
                    queue.status.upper(),
                    background=status_color,
                    color=ThemeState.theme["text_primary"],
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
                        queue.messages_pending,
                        font_size="1.5rem",
                        font_weight="700",
                        color=ThemeState.theme["accent_cyan"],
                    ),
                    rx.text(
                        "Pending",
                        font_size="0.75rem",
                        color=ThemeState.theme["text_tertiary"],
                    ),
                    align_items="flex-start",
                    spacing="1",
                ),
                # Throughput
                rx.vstack(
                    rx.text(
                        queue.throughput_per_sec,
                        font_size="1.5rem",
                        font_weight="700",
                        color=ThemeState.theme["accent_purple"],
                    ),
                    rx.text(
                        "Throughput (msg/s)",
                        font_size="0.75rem",
                        color=ThemeState.theme["text_tertiary"],
                    ),
                    align_items="flex-start",
                    spacing="1",
                ),
                # Consumer lag
                rx.vstack(
                    rx.text(
                        queue.consumer_lag,
                        font_size="1.5rem",
                        font_weight="700",
                        color=ThemeState.theme["warning"],
                    ),
                    rx.text(
                        "Lag",
                        font_size="0.75rem",
                        color=ThemeState.theme["text_tertiary"],
                    ),
                    align_items="flex-start",
                    spacing="1",
                ),
                # Error rate
                rx.vstack(
                    rx.text(
                        queue.error_rate,
                        font_size="1.5rem",
                        font_weight="700",
                        color=ThemeState.theme["error"],
                    ),
                    rx.text(
                        "Error Rate (%)",
                        font_size="0.75rem",
                        color=ThemeState.theme["text_tertiary"],
                    ),
                    align_items="flex-start",
                    spacing="1",
                ),
                columns="4",
                spacing="4",
                width="100%",
                margin_top="1rem",
            ),
            # Oldest message age
            rx.hstack(
                rx.text(
                    "Oldest message: ",
                    font_size="0.75rem",
                    color=ThemeState.theme["text_tertiary"],
                ),
                rx.text(
                    queue.oldest_message_age_sec,
                    font_size="0.75rem",
                    color=ThemeState.theme["text_tertiary"],
                ),
                rx.text(
                    "s ago",
                    font_size="0.75rem",
                    color=ThemeState.theme["text_tertiary"],
                ),
                margin_top="1rem",
            ),
            align_items="flex-start",
            spacing="2",
            width="100%",
        ),
        padding="1.5rem",
        background=ThemeState.theme["bg_secondary"],
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
                        color=ThemeState.theme["text_primary"],
                    ),
                    rx.text(
                        msg.message_id,
                        font_size="0.75rem",
                        color=ThemeState.theme["text_tertiary"],
                    ),
                    align_items="flex-start",
                    spacing="1",
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
                color=ThemeState.theme["error"],
                margin_top="0.5rem",
            ),
            # Payload
            rx.box(
                rx.text(
                    msg.payload,
                    font_size="0.75rem",
                    color=ThemeState.theme["text_secondary"],
                    font_family="monospace",
                ),
                padding="0.75rem",
                background=ThemeState.theme["bg_primary"],
                border=f"1px solid {ThemeState.theme['bg_tertiary']}",
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
                    color=ThemeState.theme["text_tertiary"],
                ),
                rx.cond(
                    msg.last_retry_at is not None,
                    rx.text(
                        f"Last retry: {msg.last_retry_at}",
                        font_size="0.75rem",
                        color=ThemeState.theme["text_tertiary"],
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
            spacing="1",
            width="100%",
        ),
        padding="1rem",
        background=ThemeState.theme["bg_secondary"],
        border=f"1px solid {ThemeState.theme['bg_tertiary']}",
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
                        color=ThemeState.theme["text_primary"],
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
                        color=ThemeState.theme["text_tertiary"],
                        padding="2rem",
                        text_align="center",
                    ),
                ),
                spacing="6",
                width="100%",
            ),
            padding="1.5rem",
            background=ThemeState.theme["bg_secondary"],
            border=f"1px solid {ThemeState.theme['bg_tertiary']}",
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
                QueueState.queue_count.to_string(),
                font_size="1.5rem",
                font_weight="700",
                color=ThemeState.theme["text_primary"],
            ),
            rx.text(
                "Total Queues",
                font_size="0.75rem",
                color=ThemeState.theme["text_tertiary"],
            ),
            align_items="flex-start",
            spacing="1",
        ),
        rx.vstack(
            rx.text(
                QueueState.healthy_count.to_string(),
                font_size="1.5rem",
                font_weight="700",
                color=ThemeState.theme["success"],
            ),
            rx.text(
                "Healthy",
                font_size="0.75rem",
                color=ThemeState.theme["text_tertiary"],
            ),
            align_items="flex-start",
            spacing="1",
        ),
        rx.vstack(
            rx.text(
                QueueState.degraded_count.to_string(),
                font_size="1.5rem",
                font_weight="700",
                color=ThemeState.theme["warning"],
            ),
            rx.text(
                "Degraded",
                font_size="0.75rem",
                color=ThemeState.theme["text_tertiary"],
            ),
            align_items="flex-start",
            spacing="1",
        ),
        rx.vstack(
            rx.text(
                QueueState.critical_count.to_string(),
                font_size="1.5rem",
                font_weight="700",
                color=ThemeState.theme["error"],
            ),
            rx.text(
                "Critical",
                font_size="0.75rem",
                color=ThemeState.theme["text_tertiary"],
            ),
            align_items="flex-start",
            spacing="1",
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
        background=ThemeState.theme["bg_secondary"],
        border=f"1px solid {ThemeState.theme['bg_tertiary']}",
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
            # Navigation Header
            rx.hstack(
                rx.text(
                    "Queue Monitoring",
                    font_size="2rem",
                    font_weight="700",
                    color=ThemeState.theme["text_primary"],
                ),
                rx.spacer(),
                rx.link(
                    rx.button(
                        rx.icon("home", size=18),
                        "Dashboard",
                        size="3",
                        variant="solid",
                        color_scheme="blue",
                    ),
                    href="/dashboard",
                ),
                width="100%",
                align_items="center",
            ),
            
            # Warning banner when using mock data
            rx.cond(
                QueueState.using_mock_data,
                rx.box(
                    rx.hstack(
                        rx.text("⚠️", font_size="1.5em"),
                        rx.vstack(
                            rx.text(
                                "Real Platform Data Not Available",
                                font_weight="bold",
                                color=ThemeState.theme["text_primary"],
                                font_size="1em",
                            ),
                            rx.text(
                                "Real platform data may not be available or working as expected. Using mocked data for demonstration. "
                                "Please work with Platform Administrator to bridge this gap. "
                                "When backend APIs are available for queue monitoring, they will be integrated with this portal.",
                                color=ThemeState.theme["text_tertiary"],
                                font_size="0.9em",
                                line_height="1.5",
                            ),
                            spacing="1",
                            align_items="start",
                        ),
                        spacing="3",
                        align_items="start",
                    ),
                    padding="1rem 1.5rem",
                    border_radius="0.75rem",
                    background="rgba(245, 158, 11, 0.1)",
                    border=f"1px solid {ThemeState.theme['warning']}",
                    margin_bottom="1rem",
                    width="100%",
                ),
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
        background=ThemeState.theme["bg_primary"],
        on_mount=QueueState.load_queues,
    )
