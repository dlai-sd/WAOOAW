"""
Unit tests for metrics_widget component
"""

import pytest
from waooaw_portal.components.common.metrics_widget import (
    metrics_widget,
    metrics_widget_grid,
    metric_agents_online,
    metric_response_time,
    metric_success_rate,
    metric_requests_per_min,
)


class TestMetricsWidget:
    """Test basic metrics widget functionality"""

    def test_metrics_widget_basic(self):
        """Test basic metrics widget creation"""
        result = metrics_widget("Test Metric", "100")
        assert result is not None

    def test_metrics_widget_with_delta(self):
        """Test metrics widget with delta"""
        result = metrics_widget("Test Metric", "100", delta="+10%", trend="up")
        assert result is not None

    def test_metrics_widget_with_unit(self):
        """Test metrics widget with unit"""
        result = metrics_widget("Response Time", "1.5", unit="ms")
        assert result is not None

    def test_metrics_widget_sizes(self):
        """Test all size variants"""
        for size in ["sm", "md", "lg"]:
            result = metrics_widget("Test", "100", size=size)
            assert result is not None

    def test_metrics_widget_themes(self):
        """Test dark and light themes"""
        for theme in ["dark", "light"]:
            result = metrics_widget("Test", "100", theme=theme)
            assert result is not None

    def test_metrics_widget_trends(self):
        """Test all trend variants"""
        for trend in ["up", "down", "neutral"]:
            result = metrics_widget("Test", "100", delta="+5", trend=trend)
            assert result is not None

    def test_metrics_widget_with_sparkline(self):
        """Test metrics widget with sparkline data"""
        sparkline_data = [10, 15, 12, 18, 20, 17, 22]
        result = metrics_widget("Test", "100", sparkline_data=sparkline_data)
        assert result is not None

    def test_metrics_widget_no_delta(self):
        """Test metrics widget without delta"""
        result = metrics_widget("Test", "100")
        assert result is not None

    def test_metrics_widget_invalid_size(self):
        """Test metrics widget with invalid size defaults to md"""
        result = metrics_widget("Test", "100", size="invalid")
        assert result is not None


class TestMetricsWidgetGrid:
    """Test metrics widget grid layout"""

    def test_metrics_widget_grid_basic(self):
        """Test basic grid with multiple metrics"""
        metrics = [
            ("Metric 1", "100", "+10%", "up"),
            ("Metric 2", "200", "-5%", "down"),
            ("Metric 3", "300", None, "neutral"),
        ]
        result = metrics_widget_grid(metrics)
        assert result is not None

    def test_metrics_widget_grid_empty(self):
        """Test empty grid"""
        result = metrics_widget_grid([])
        assert result is not None

    def test_metrics_widget_grid_single(self):
        """Test grid with single metric"""
        metrics = [("Single", "100", None, "neutral")]
        result = metrics_widget_grid(metrics)
        assert result is not None

    def test_metrics_widget_grid_theme(self):
        """Test grid with dark theme"""
        metrics = [
            ("Metric 1", "100", "+10%", "up"),
            ("Metric 2", "200", "-5%", "down"),
        ]
        result = metrics_widget_grid(metrics, theme="dark")
        assert result is not None


class TestPresetMetrics:
    """Test preset metric widgets"""

    def test_metric_agents_online(self):
        """Test agents online preset"""
        result = metric_agents_online(10)
        assert result is not None

    def test_metric_agents_online_with_delta(self):
        """Test agents online with delta"""
        result = metric_agents_online(10, delta="+2")
        assert result is not None

    def test_metric_response_time(self):
        """Test response time preset"""
        result = metric_response_time(125.5)
        assert result is not None

    def test_metric_response_time_with_delta(self):
        """Test response time with delta"""
        result = metric_response_time(125.5, delta="-10ms")
        assert result is not None

    def test_metric_success_rate(self):
        """Test success rate preset"""
        result = metric_success_rate(98.5)
        assert result is not None

    def test_metric_success_rate_with_delta(self):
        """Test success rate with delta"""
        result = metric_success_rate(98.5, delta="+1.2%")
        assert result is not None

    def test_metric_requests_per_min(self):
        """Test requests per minute preset"""
        result = metric_requests_per_min(1500)
        assert result is not None

    def test_metric_requests_per_min_with_sparkline(self):
        """Test requests per minute with sparkline"""
        sparkline = [1000, 1200, 1100, 1400, 1500]
        result = metric_requests_per_min(1500, sparkline=sparkline)
        assert result is not None


class TestMetricsWidgetEdgeCases:
    """Test edge cases"""

    def test_empty_label(self):
        """Test with empty label"""
        result = metrics_widget("", "100")
        assert result is not None

    def test_empty_value(self):
        """Test with empty value"""
        result = metrics_widget("Test", "")
        assert result is not None

    def test_very_long_label(self):
        """Test with very long label"""
        long_label = "A" * 100
        result = metrics_widget(long_label, "100")
        assert result is not None

    def test_very_large_value(self):
        """Test with very large value"""
        result = metrics_widget("Test", "999999999")
        assert result is not None

    def test_negative_value(self):
        """Test with negative value"""
        result = metrics_widget("Test", "-50")
        assert result is not None

    def test_decimal_value(self):
        """Test with decimal value"""
        result = metrics_widget("Test", "123.456")
        assert result is not None

    def test_sparkline_single_point(self):
        """Test sparkline with single data point"""
        result = metrics_widget("Test", "100", sparkline_data=[50])
        assert result is not None

    def test_sparkline_empty(self):
        """Test sparkline with empty data"""
        result = metrics_widget("Test", "100", sparkline_data=[])
        assert result is not None

    def test_sparkline_all_same_values(self):
        """Test sparkline with all same values"""
        result = metrics_widget("Test", "100", sparkline_data=[50, 50, 50, 50])
        assert result is not None


class TestMetricsWidgetIntegration:
    """Test integration scenarios"""

    def test_dashboard_metrics(self):
        """Test complete dashboard metrics setup"""
        metrics = [
            ("Active Agents", "127", "+5", "up"),
            ("Response Time", "1.2ms", "-0.3ms", "down"),
            ("Success Rate", "98.5%", "+0.5%", "up"),
            ("Requests/min", "1500", "+200", "up"),
        ]
        result = metrics_widget_grid(metrics, theme="dark")
        assert result is not None

    def test_agent_metrics_panel(self):
        """Test agent-specific metrics"""
        sparkline = [100, 120, 110, 130, 125]
        result = metric_requests_per_min(125, "+15", sparkline)
        assert result is not None

    def test_mixed_trends_grid(self):
        """Test grid with mixed trends"""
        metrics = [
            ("Up Metric", "100", "+10", "up"),
            ("Down Metric", "50", "-5", "down"),
            ("Neutral Metric", "75", None, "neutral"),
        ]
        result = metrics_widget_grid(metrics)
        assert result is not None


# Fixtures
@pytest.fixture
def sample_sparkline_data():
    """Sample sparkline data for testing"""
    return [10, 15, 12, 18, 20, 17, 22, 25, 23, 28]


def test_with_fixture(sample_sparkline_data):
    """Test using fixture data"""
    result = metrics_widget(
        "Test Metric",
        "28",
        delta="+18%",
        trend="up",
        sparkline_data=sample_sparkline_data,
    )
    assert result is not None
