"""
Logs Page

Real-time log viewer with agent filtering.
"""

import reflex as rx
from typing import List, Optional
from datetime import datetime
from waooaw_portal.state.context_state import ContextState


class LogEntry(rx.Base):
    """Log entry model"""
    
    log_id: str
    timestamp: str
    level: str  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    agent_id: str
    agent_name: str
    message: str
    metadata: Optional[dict] = None


class LogsState(rx.State):
    """
    Logs page state.
    
    Features:
    - Real-time log streaming via WebSocket
    - Filter by selected agents
    - Filter by log level
    - Search in log messages
    - Auto-scroll with pause option
    """
    
    # Log entries
    logs: List[LogEntry] = []
    
    # Filters
    level_filter: str = "all"  # all, debug, info, warning, error, critical
    search_query: str = ""
    
    # UI state
    is_loading: bool = False
    auto_scroll: bool = True
    max_logs: int = 1000
    
    def load_logs(self):
        """Load recent logs"""
        self.is_loading = True
        
        # In production: API call GET /api/platform/logs?agent_ids=...&level=...
        # For now, use mock data
        self.logs = [
            LogEntry(
                log_id="log-1",
                timestamp="2 minutes ago",
                level="INFO",
                agent_id="agent-1",
                agent_name="WowMemory",
                message="Memory sync completed successfully (1,247 records)",
            ),
            LogEntry(
                log_id="log-2",
                timestamp="3 minutes ago",
                level="INFO",
                agent_id="agent-2",
                agent_name="WowQueue",
                message="Queue health check: 3,521 messages processed",
            ),
            LogEntry(
                log_id="log-3",
                timestamp="5 minutes ago",
                level="WARNING",
                agent_id="agent-3",
                agent_name="WowOrchestrator",
                message="Workflow execution delayed by 2.3s (within threshold)",
            ),
            LogEntry(
                log_id="log-4",
                timestamp="8 minutes ago",
                level="ERROR",
                agent_id="agent-4",
                agent_name="WowSDK",
                message="API rate limit exceeded (429) - backing off for 30s",
            ),
            LogEntry(
                log_id="log-5",
                timestamp="10 minutes ago",
                level="INFO",
                agent_id="agent-1",
                agent_name="WowMemory",
                message="Cache hit rate: 98.5% (excellent performance)",
            ),
        ]
        
        self.is_loading = False
    
    def set_level_filter(self, level: str):
        """Set log level filter"""
        self.level_filter = level
    
    def set_search_query(self, query: str):
        """Set search query"""
        self.search_query = query
    
    def toggle_auto_scroll(self):
        """Toggle auto-scroll"""
        self.auto_scroll = not self.auto_scroll
    
    def clear_logs(self):
        """Clear all logs"""
        self.logs = []
    
    @rx.var
    def filtered_logs(self) -> List[LogEntry]:
        """Get filtered logs"""
        filtered = self.logs
        
        # Apply context filter (by selected agents)
        context_state = self.get_state(ContextState)
        if context_state.filter_active and context_state.selected_agent_ids:
            filtered = [
                log for log in filtered 
                if log.agent_id in context_state.selected_agent_ids
            ]
        
        # Apply level filter
        if self.level_filter != "all":
            filtered = [log for log in filtered if log.level.lower() == self.level_filter.lower()]
        
        # Apply search filter
        if self.search_query:
            query = self.search_query.lower()
            filtered = [
                log for log in filtered
                if query in log.message.lower() or query in log.agent_name.lower()
            ]
        
        return filtered
    
    @rx.var
    def log_count(self) -> int:
        """Total log count"""
        return len(self.logs)
    
    @rx.var
    def filtered_count(self) -> int:
        """Filtered log count"""
        return len(self.filtered_logs)


def get_level_color(level: str) -> str:
    """Get color for log level"""
    level_colors = {
        "DEBUG": "#6b7280",    # Gray
        "INFO": "#3b82f6",     # Blue
        "WARNING": "#f59e0b",  # Yellow
        "ERROR": "#ef4444",    # Red
        "CRITICAL": "#dc2626", # Dark red
    }
    return level_colors.get(level.upper(), "#6b7280")


def log_entry_card(log: LogEntry) -> rx.Component:
    """Individual log entry card"""
    level_color = get_level_color(log.level)
    
    return rx.box(
        rx.hstack(
            # Timestamp
            rx.text(
                log.timestamp,
                font_size="0.75rem",
                color="#9ca3af",
                width="8rem",
                flex_shrink="0",
            ),
            # Level badge
            rx.badge(
                log.level,
                color_scheme="gray",
                variant="solid",
                background=level_color,
                width="5rem",
                text_align="center",
            ),
            # Agent name
            rx.text(
                log.agent_name,
                font_size="0.875rem",
                font_weight="600",
                color="#00f2fe",
                width="10rem",
                flex_shrink="0",
            ),
            # Message
            rx.text(
                log.message,
                font_size="0.875rem",
                color="#d1d5db",
                flex="1",
            ),
            spacing="1rem",
            align_items="center",
            width="100%",
        ),
        padding="0.75rem 1rem",
        border_bottom="1px solid #27272a",
        _hover={
            "background": "#18181b",
        },
    )


def filters_bar() -> rx.Component:
    """Filter controls"""
    return rx.hstack(
        # Search
        rx.input(
            placeholder="Search logs...",
            value=LogsState.search_query,
            on_change=LogsState.set_search_query,
            width="20rem",
        ),
        # Level filter
        rx.select(
            ["all", "debug", "info", "warning", "error", "critical"],
            value=LogsState.level_filter,
            on_change=LogsState.set_level_filter,
            placeholder="All Levels",
        ),
        # Auto-scroll toggle
        rx.switch(
            checked=LogsState.auto_scroll,
            on_change=LogsState.toggle_auto_scroll,
        ),
        rx.text(
            "Auto-scroll",
            font_size="0.875rem",
            color="#d1d5db",
        ),
        # Clear button
        rx.button(
            "Clear",
            on_click=LogsState.clear_logs,
            size="sm",
            variant="ghost",
            color_scheme="red",
        ),
        # Refresh button
        rx.button(
            "Refresh",
            on_click=LogsState.load_logs,
            size="sm",
            color_scheme="cyan",
            variant="outline",
        ),
        spacing="1rem",
        align_items="center",
        width="100%",
        padding="1rem",
        background="#18181b",
        border="1px solid #27272a",
        border_radius="0.75rem",
    )


def logs_list() -> rx.Component:
    """List of log entries"""
    return rx.cond(
        LogsState.filtered_count > 0,
        rx.box(
            rx.foreach(
                LogsState.filtered_logs,
                log_entry_card,
            ),
            width="100%",
            border="1px solid #27272a",
            border_radius="0.75rem",
            overflow_y="auto",
            max_height="70vh",
        ),
        # Empty state
        rx.box(
            rx.vstack(
                rx.text(
                    "📋",
                    font_size="4rem",
                ),
                rx.text(
                    "No logs found",
                    font_size="1.5rem",
                    font_weight="600",
                    color="white",
                ),
                rx.text(
                    "Try adjusting your filters or refresh",
                    font_size="1rem",
                    color="#9ca3af",
                ),
                spacing="1rem",
                align_items="center",
            ),
            padding="4rem",
            text_align="center",
            border="1px solid #27272a",
            border_radius="0.75rem",
        ),
    )


def logs_page() -> rx.Component:
    """
    Logs page with real-time streaming and filtering.
    
    Features:
    - Real-time log streaming via WebSocket
    - Filter by agent (context filter)
    - Filter by log level
    - Search in messages
    - Auto-scroll option
    """
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Logs",
                        font_size="2rem",
                        font_weight="700",
                        color="white",
                    ),
                    rx.text(
                        f"{LogsState.filtered_count} of {LogsState.log_count} logs",
                        font_size="1rem",
                        color="#9ca3af",
                    ),
                    align_items="flex-start",
                    spacing="0.5rem",
                ),
                rx.spacer(),
                width="100%",
                align_items="center",
            ),
            # Filters
            filters_bar(),
            # Logs list
            logs_list(),
            spacing="2rem",
            width="100%",
            max_width="90rem",
            margin="0 auto",
            padding="2rem",
        ),
        width="100%",
        min_height="100vh",
        background="#0a0a0a",
        on_mount=LogsState.load_logs,
    )
