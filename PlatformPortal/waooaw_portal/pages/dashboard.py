"""Dashboard Page - With Real API Data"""
import reflex as rx
from waooaw_portal.state.dashboard_state import DashboardState

def dashboard_page() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.hstack(
                rx.heading("WAOOAW Dashboard", size="9"),
                rx.button(
                    "🔄 Refresh", 
                    on_click=DashboardState.refresh_metrics,
                    loading=DashboardState.is_loading,
                    size="3"
                ),
                justify="between",
                width="100%",
            ),
            rx.grid(
                rx.card(
                    rx.vstack(
                        rx.heading(DashboardState.total_agents, size="8"), 
                        rx.text("Total Agents", size="2", color="gray"),
                        rx.text(f"Running: {DashboardState.agents_running}", size="1", color="green"),
                        spacing="2", 
                        align="center"
                    )
                ),
                rx.card(
                    rx.vstack(
                        rx.heading(DashboardState.active_tasks, size="8"), 
                        rx.text("Tasks/Min", size="2", color="gray"),
                        rx.text(f"{DashboardState.requests_per_minute} req/min", size="1", color="blue"),
                        spacing="2", 
                        align="center"
                    )
                ),
                rx.card(
                    rx.vstack(
                        rx.heading(f"{DashboardState.error_rate}%", size="8"), 
                        rx.text("Error Rate", size="2", color="gray"),
                        rx.text(f"P95: {DashboardState.p95_latency}ms", size="1", color="orange"),
                        spacing="2", 
                        align="center"
                    )
                ),
                rx.card(
                    rx.vstack(
                        rx.heading(f"{DashboardState.system_uptime_percentage}%", size="8"), 
                        rx.text("System Health", size="2", color="gray"),
                        rx.text(DashboardState.agents_health_label, size="1", color="green"),
                        spacing="2", 
                        align="center"
                    )
                ),
                columns="4", spacing="4", width="100%",
            ),
            rx.text("💡 Live data from: http://localhost:8000/api/platform/metrics", size="1", color="gray", margin_top="4"),
            spacing="4", padding="8", max_width="1200px",
        ),
        on_mount=DashboardState.on_load,
    )
