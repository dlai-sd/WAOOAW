"""
Unit tests for MetricsAggregator service
"""

import pytest
from datetime import datetime, timedelta
from waooaw_portal.services.metrics_aggregator import (
    MetricsAggregator,
    MetricPoint,
    AggregatedMetric,
)


@pytest.fixture
def aggregator():
    """Create metrics aggregator instance"""
    return MetricsAggregator(retention_hours=1, max_points_per_metric=100)


class TestMetricsAggregator:
    """Test MetricsAggregator basic functionality"""

    def test_record_metric(self, aggregator):
        """Test recording a metric"""
        aggregator.record("cpu_usage", 50.0)

        assert "cpu_usage" in aggregator.metrics
        assert len(aggregator.metrics["cpu_usage"]) == 1

    def test_record_metric_with_tags(self, aggregator):
        """Test recording metric with tags"""
        aggregator.record(
            "response_time", 100.0, {"service": "api", "region": "us-east"}
        )

        assert "response_time" in aggregator.metrics
        point = aggregator.metrics["response_time"][0]
        assert point.tags["service"] == "api"
        assert point.tags["region"] == "us-east"

    def test_record_multiple_metrics(self, aggregator):
        """Test recording multiple metrics"""
        aggregator.record("cpu_usage", 50.0)
        aggregator.record("cpu_usage", 60.0)
        aggregator.record("cpu_usage", 70.0)

        assert len(aggregator.metrics["cpu_usage"]) == 3

    def test_max_points_limit(self, aggregator):
        """Test max points limit enforcement"""
        # Record more than max
        for i in range(150):
            aggregator.record("test_metric", float(i))

        # Should be trimmed to max
        assert len(aggregator.metrics["test_metric"]) == 100


class TestMetricsAggregation:
    """Test metrics aggregation"""

    def test_get_aggregate_basic(self, aggregator):
        """Test basic aggregation"""
        aggregator.record("cpu_usage", 50.0)
        aggregator.record("cpu_usage", 60.0)
        aggregator.record("cpu_usage", 70.0)

        agg = aggregator.get_aggregate("cpu_usage")

        assert agg.count == 3
        assert agg.sum == 180.0
        assert agg.min == 50.0
        assert agg.max == 70.0
        assert agg.avg == 60.0

    def test_get_aggregate_single_value(self, aggregator):
        """Test aggregation with single value"""
        aggregator.record("cpu_usage", 50.0)

        agg = aggregator.get_aggregate("cpu_usage")

        assert agg.count == 1
        assert agg.avg == 50.0
        assert agg.min == 50.0
        assert agg.max == 50.0

    def test_get_aggregate_nonexistent(self, aggregator):
        """Test aggregation for nonexistent metric"""
        agg = aggregator.get_aggregate("nonexistent")

        assert agg.count == 0
        assert agg.sum == 0.0
        assert agg.avg == 0.0

    def test_get_aggregate_with_tags(self, aggregator):
        """Test aggregation filtered by tags"""
        aggregator.record("response_time", 100.0, {"service": "api"})
        aggregator.record("response_time", 200.0, {"service": "api"})
        aggregator.record("response_time", 300.0, {"service": "web"})

        agg = aggregator.get_aggregate("response_time", {"service": "api"})

        assert agg.count == 2
        assert agg.avg == 150.0


class TestMetricsSeries:
    """Test time-series queries"""

    def test_get_series_all(self, aggregator):
        """Test getting full series"""
        aggregator.record("cpu_usage", 50.0)
        aggregator.record("cpu_usage", 60.0)
        aggregator.record("cpu_usage", 70.0)

        series = aggregator.get_series("cpu_usage")

        assert len(series) == 3
        assert all(isinstance(p, MetricPoint) for p in series)

    def test_get_series_time_window(self, aggregator):
        """Test getting series within time window"""
        now = datetime.now()

        # Record with different timestamps
        for i in range(5):
            aggregator.record("cpu_usage", float(i * 10))

        # Get last 2 points
        start = now - timedelta(seconds=1)
        series = aggregator.get_series("cpu_usage", start_time=start)

        assert len(series) > 0

    def test_get_series_with_tags(self, aggregator):
        """Test getting series filtered by tags"""
        aggregator.record("response_time", 100.0, {"service": "api"})
        aggregator.record("response_time", 200.0, {"service": "api"})
        aggregator.record("response_time", 300.0, {"service": "web"})

        series = aggregator.get_series("response_time", tags={"service": "api"})

        assert len(series) == 2
        assert all(p.tags.get("service") == "api" for p in series)

    def test_get_series_nonexistent(self, aggregator):
        """Test getting series for nonexistent metric"""
        series = aggregator.get_series("nonexistent")
        assert len(series) == 0


class TestMetricsLatest:
    """Test getting latest metrics"""

    def test_get_latest_single(self, aggregator):
        """Test getting latest value"""
        aggregator.record("cpu_usage", 50.0)
        aggregator.record("cpu_usage", 60.0)
        aggregator.record("cpu_usage", 70.0)

        latest = aggregator.get_latest("cpu_usage", count=1)

        assert len(latest) == 1
        assert latest[0].value == 70.0

    def test_get_latest_multiple(self, aggregator):
        """Test getting latest N values"""
        for i in range(10):
            aggregator.record("cpu_usage", float(i))

        latest = aggregator.get_latest("cpu_usage", count=5)

        assert len(latest) == 5
        # Should be in reverse order (newest first)
        assert latest[0].value == 9.0
        assert latest[4].value == 5.0

    def test_get_latest_more_than_exists(self, aggregator):
        """Test getting more than available"""
        aggregator.record("cpu_usage", 50.0)
        aggregator.record("cpu_usage", 60.0)

        latest = aggregator.get_latest("cpu_usage", count=10)

        assert len(latest) == 2

    def test_get_latest_nonexistent(self, aggregator):
        """Test getting latest for nonexistent metric"""
        latest = aggregator.get_latest("nonexistent")
        assert len(latest) == 0


class TestMetricsCleanup:
    """Test metrics cleanup"""

    def test_cleanup_old_metrics(self, aggregator):
        """Test cleaning up old metrics"""
        # Set short retention
        aggregator.retention_hours = 0.001  # ~3.6 seconds

        aggregator.record("cpu_usage", 50.0)

        # Wait for retention period
        import time

        time.sleep(0.1)

        # Record new metric
        aggregator.record("cpu_usage", 60.0)

        # Cleanup
        aggregator.cleanup_old_metrics()

        # Should have removed old metric
        assert len(aggregator.metrics["cpu_usage"]) == 1
        assert aggregator.metrics["cpu_usage"][0].value == 60.0


class TestMetricsStats:
    """Test statistics and monitoring"""

    def test_get_all_metrics(self, aggregator):
        """Test getting all metrics"""
        aggregator.record("cpu_usage", 50.0)
        aggregator.record("memory_usage", 60.0)
        aggregator.record("disk_usage", 70.0)

        all_metrics = aggregator.get_all_metrics()

        assert len(all_metrics) == 3
        assert "cpu_usage" in all_metrics
        assert "memory_usage" in all_metrics
        assert "disk_usage" in all_metrics

    def test_get_stats(self, aggregator):
        """Test getting aggregator statistics"""
        aggregator.record("cpu_usage", 50.0)
        aggregator.record("cpu_usage", 60.0)
        aggregator.record("memory_usage", 70.0)

        stats = aggregator.get_stats()

        assert stats["total_metrics"] == 2
        assert stats["total_points"] == 3
        assert stats["retention_hours"] == 1
        assert stats["max_points_per_metric"] == 100
        assert "cpu_usage" in stats["metric_counts"]
        assert stats["metric_counts"]["cpu_usage"] == 2


class TestMetricsEdgeCases:
    """Test edge cases"""

    def test_record_zero_value(self, aggregator):
        """Test recording zero value"""
        aggregator.record("cpu_usage", 0.0)

        agg = aggregator.get_aggregate("cpu_usage")
        assert agg.avg == 0.0

    def test_record_negative_value(self, aggregator):
        """Test recording negative value"""
        aggregator.record("temperature", -10.0)

        agg = aggregator.get_aggregate("temperature")
        assert agg.avg == -10.0

    def test_record_large_value(self, aggregator):
        """Test recording large value"""
        aggregator.record("bytes_transferred", 1e12)

        agg = aggregator.get_aggregate("bytes_transferred")
        assert agg.avg == 1e12

    def test_empty_tags(self, aggregator):
        """Test recording with empty tags"""
        aggregator.record("cpu_usage", 50.0, {})

        assert len(aggregator.metrics["cpu_usage"]) == 1

    def test_multiple_tag_filters(self, aggregator):
        """Test filtering with multiple tags"""
        aggregator.record(
            "response_time",
            100.0,
            {"service": "api", "region": "us-east", "env": "prod"},
        )
        aggregator.record(
            "response_time",
            200.0,
            {"service": "api", "region": "us-west", "env": "prod"},
        )
        aggregator.record(
            "response_time",
            300.0,
            {"service": "web", "region": "us-east", "env": "prod"},
        )

        # Filter by multiple tags
        agg = aggregator.get_aggregate(
            "response_time", {"service": "api", "env": "prod"}
        )

        assert agg.count == 2


class TestMetricsDataClasses:
    """Test data classes"""

    def test_metric_point_creation(self):
        """Test MetricPoint creation"""
        now = datetime.now()
        point = MetricPoint(timestamp=now, value=50.0, tags={"service": "api"})

        assert point.timestamp == now
        assert point.value == 50.0
        assert point.tags["service"] == "api"

    def test_aggregated_metric_creation(self):
        """Test AggregatedMetric creation"""
        agg = AggregatedMetric(
            count=10, sum=500.0, min=30.0, max=70.0, avg=50.0, last_value=65.0
        )

        assert agg.count == 10
        assert agg.sum == 500.0
        assert agg.min == 30.0
        assert agg.max == 70.0
        assert agg.avg == 50.0
        assert agg.last_value == 65.0
