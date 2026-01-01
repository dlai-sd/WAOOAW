"""
Metrics Widget Component

Real-time metrics display with sparklines, value, delta, and trend indicators.
Used in dashboards, agent cards, and system monitoring pages.
"""

from typing import Optional, List, Tuple
import reflex as rx
from waooaw_portal.theme import get_theme, DARK_THEME


def metrics_widget(
    label: str,
    value: str,
    delta: Optional[str] = None,
    trend: str = "neutral",
    sparkline_data: Optional[List[float]] = None,
    unit: str = "",
    size: str = "md",
    theme: str = "dark",
) -> rx.Component:
    """
    Display a metric with optional delta, trend, and sparkline.

    Args:
        label: Metric label (e.g., "Active Agents", "Response Time")
        value: Current metric value (e.g., "127", "1.2")
        delta: Change from previous period (e.g., "+12%", "-5")
        trend: Trend direction - "up", "down", "neutral"
        sparkline_data: List of historical values for sparkline chart
        unit: Unit suffix (e.g., "ms", "%", "agents")
        size: Widget size - "sm", "md", "lg"
        theme: Color theme - "dark" or "light"

    Returns:
        Reflex component with metric display
    """
    theme_colors = get_theme(theme)

    # Size configurations
    sizes = {
        "sm": {"width": "160px", "font_size": "1.5rem", "label_size": "0.75rem"},
        "md": {"width": "220px", "font_size": "2rem", "label_size": "0.875rem"},
        "lg": {"width": "280px", "font_size": "2.5rem", "label_size": "1rem"},
    }
    size_config = sizes.get(size, sizes["md"])

    # Trend colors and icons
    trend_config = {
        "up": {
            "color": theme_colors["success"],
            "icon": "↑",
            "bg": "rgba(16, 185, 129, 0.1)",
        },
        "down": {
            "color": theme_colors["error"],
            "icon": "↓",
            "bg": "rgba(239, 68, 68, 0.1)",
        },
        "neutral": {
            "color": theme_colors["text_secondary"],
            "icon": "→",
            "bg": "rgba(156, 163, 175, 0.1)",
        },
    }
    trend_info = trend_config.get(trend, trend_config["neutral"])

    # Build components
    components = []

    # Label
    components.append(
        rx.text(
            label,
            font_size=size_config["label_size"],
            color=theme_colors["text_secondary"],
            font_weight="500",
            margin_bottom="0.5rem",
        )
    )

    # Value with unit
    value_text = f"{value}{unit}" if unit else value
    components.append(
        rx.text(
            value_text,
            font_size=size_config["font_size"],
            color=theme_colors["text_primary"],
            font_weight="700",
            line_height="1",
            margin_bottom="0.5rem",
        )
    )

    # Delta and trend indicator
    if delta:
        components.append(
            rx.hstack(
                rx.box(
                    rx.text(
                        f"{trend_info['icon']} {delta}",
                        color=trend_info["color"],
                        font_size="0.875rem",
                        font_weight="600",
                    ),
                    background=trend_info["bg"],
                    padding="0.25rem 0.5rem",
                    border_radius="0.375rem",
                ),
                spacing="0.5rem",
                margin_bottom="0.5rem" if sparkline_data else "0",
            )
        )

    # Sparkline chart (if data provided)
    if sparkline_data and len(sparkline_data) > 1:
        components.append(_sparkline_chart(sparkline_data, trend_info["color"], theme))

    return rx.box(
        rx.vstack(
            *components,
            align_items="flex-start",
            spacing="0",
        ),
        background=theme_colors["bg_secondary"],
        border=f"1px solid {theme_colors['border']}",
        border_radius="1rem",
        padding="1.25rem",
        width=size_config["width"],
        transition="all 0.3s ease",
        _hover={
            "transform": "translateY(-4px)",
            "box_shadow": f"0 0 20px {theme_colors['primary']}40",
            "border_color": theme_colors["primary"],
        },
    )


def _sparkline_chart(
    data: List[float], color: str, theme: str = "dark"
) -> rx.Component:
    """
    Create a simple sparkline chart from data points.

    Args:
        data: List of numeric values
        color: Line color
        theme: Color theme

    Returns:
        SVG sparkline component
    """
    if not data or len(data) < 2:
        return rx.box()

    # Normalize data to 0-100 range
    min_val = min(data)
    max_val = max(data)
    range_val = max_val - min_val if max_val != min_val else 1

    normalized = [(val - min_val) / range_val * 40 for val in data]

    # Create SVG path
    width = 180
    height = 40
    step = width / (len(normalized) - 1)

    points = [f"{i * step},{height - val}" for i, val in enumerate(normalized)]
    path = f"M {' L '.join(points)}"

    return rx.html(
        f"""
        <svg width="{width}" height="{height}" style="margin-top: 0.5rem;">
            <path d="{path}" 
                  fill="none" 
                  stroke="{color}" 
                  stroke-width="2" 
                  stroke-linecap="round"/>
        </svg>
        """
    )


def metrics_widget_grid(
    metrics: List[Tuple[str, str, Optional[str], str]], theme: str = "dark"
) -> rx.Component:
    """
    Display multiple metrics in a responsive grid.

    Args:
        metrics: List of tuples (label, value, delta, trend)
        theme: Color theme

    Returns:
        Grid of metric widgets
    """
    widgets = [
        metrics_widget(label, value, delta, trend, theme=theme)
        for label, value, delta, trend in metrics
    ]

    return rx.box(
        rx.hstack(
            *widgets,
            spacing="1rem",
            wrap="wrap",
        ),
        width="100%",
    )


# Preset metric widgets
def metric_agents_online(count: int, delta: Optional[str] = None) -> rx.Component:
    """Preset: Active agents metric"""
    trend = "up" if delta and "+" in delta else "neutral"
    return metrics_widget("Active Agents", str(count), delta, trend, unit=" agents")


def metric_response_time(ms: float, delta: Optional[str] = None) -> rx.Component:
    """Preset: Response time metric"""
    trend = "down" if delta and "+" in delta else "up"  # Lower is better
    return metrics_widget("Avg Response Time", f"{ms:.1f}", delta, trend, unit="ms")


def metric_success_rate(percentage: float, delta: Optional[str] = None) -> rx.Component:
    """Preset: Success rate metric"""
    trend = "up" if delta and "+" in delta else "neutral"
    return metrics_widget("Success Rate", f"{percentage:.1f}", delta, trend, unit="%")


def metric_requests_per_min(
    count: int, delta: Optional[str] = None, sparkline: Optional[List[float]] = None
) -> rx.Component:
    """Preset: Requests per minute with sparkline"""
    trend = "up" if delta and "+" in delta else "neutral"
    return metrics_widget(
        "Requests/min", str(count), delta, trend, sparkline_data=sparkline, unit=" req"
    )
