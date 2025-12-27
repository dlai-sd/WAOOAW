"""
Unit Tests for Metrics Collection - Story 5.6
"""
import pytest

import sys
sys.path.insert(0, '/workspaces/WAOOAW')

from waooaw.common.metrics import (
    MetricsCollector,
    Counter,
    Gauge,
    Histogram
)


class TestCounter:
    """Test counter metric."""
    
    def test_init(self):
        """Should initialize counter."""
        counter = Counter("requests_total", "Total requests")
        
        assert counter.value == 0.0
    
    def test_increment(self):
        """Should increment counter."""
        counter = Counter("requests_total", "Total requests")
        
        counter.inc()
        counter.inc(5)
        
        assert counter.value == 6.0
    
    def test_negative_increment_fails(self):
        """Should reject negative increments."""
        counter = Counter("requests_total", "Total requests")
        
        with pytest.raises(ValueError):
            counter.inc(-1)


class TestGauge:
    """Test gauge metric."""
    
    def test_init(self):
        """Should initialize gauge."""
        gauge = Gauge("memory_usage", "Memory usage")
        
        assert gauge.value == 0.0
    
    def test_set(self):
        """Should set gauge value."""
        gauge = Gauge("memory_usage", "Memory usage")
        
        gauge.set(100.0)
        
        assert gauge.value == 100.0
    
    def test_increment_decrement(self):
        """Should increment and decrement."""
        gauge = Gauge("queue_size", "Queue size")
        
        gauge.inc(10)
        gauge.dec(3)
        
        assert gauge.value == 7.0


class TestHistogram:
    """Test histogram metric."""
    
    def test_init(self):
        """Should initialize histogram."""
        histogram = Histogram(
            "request_duration",
            "Request duration",
            buckets=[0.1, 0.5, 1.0]
        )
        
        assert histogram.count == 0
        assert histogram.sum == 0.0
    
    def test_observe(self):
        """Should observe values."""
        histogram = Histogram(
            "request_duration",
            "Request duration",
            buckets=[0.1, 0.5, 1.0]
        )
        
        histogram.observe(0.05)
        histogram.observe(0.3)
        histogram.observe(0.8)
        
        assert histogram.count == 3
        assert histogram.sum == pytest.approx(1.15)
    
    def test_average(self):
        """Should calculate average."""
        histogram = Histogram("duration", "Duration")
        
        histogram.observe(1.0)
        histogram.observe(2.0)
        histogram.observe(3.0)
        
        assert histogram.get_average() == 2.0
    
    def test_buckets(self):
        """Should populate buckets correctly."""
        histogram = Histogram("duration", "Duration", buckets=[0.5, 1.0])
        
        histogram.observe(0.3)  # In first bucket
        histogram.observe(0.7)  # In second bucket
        histogram.observe(2.0)  # In +Inf bucket
        
        assert histogram.buckets[0].count == 1  # 0.5 bucket
        assert histogram.buckets[1].count == 2  # 1.0 bucket
        assert histogram.buckets[2].count == 3  # +Inf bucket


class TestMetricsCollector:
    """Test metrics collector."""
    
    def test_init(self):
        """Should initialize collector."""
        collector = MetricsCollector()
        
        assert len(collector.counters) == 0
        assert len(collector.gauges) == 0
        assert len(collector.histograms) == 0
    
    def test_create_counter(self):
        """Should create counter."""
        collector = MetricsCollector()
        
        counter = collector.counter("requests_total", "Total requests")
        
        assert isinstance(counter, Counter)
        assert len(collector.counters) == 1
    
    def test_create_gauge(self):
        """Should create gauge."""
        collector = MetricsCollector()
        
        gauge = collector.gauge("memory_usage", "Memory usage")
        
        assert isinstance(gauge, Gauge)
        assert len(collector.gauges) == 1
    
    def test_create_histogram(self):
        """Should create histogram."""
        collector = MetricsCollector()
        
        histogram = collector.histogram("duration", "Duration")
        
        assert isinstance(histogram, Histogram)
        assert len(collector.histograms) == 1
    
    def test_collect(self):
        """Should collect all metrics."""
        collector = MetricsCollector()
        
        counter = collector.counter("requests", "Requests")
        counter.inc(5)
        
        gauge = collector.gauge("memory", "Memory")
        gauge.set(100)
        
        metrics = collector.collect()
        
        assert len(metrics) == 2
    
    def test_labeled_metrics(self):
        """Should support labeled metrics."""
        collector = MetricsCollector()
        
        counter1 = collector.counter(
            "requests_total",
            "Total requests",
            labels={"method": "GET"}
        )
        counter2 = collector.counter(
            "requests_total",
            "Total requests",
            labels={"method": "POST"}
        )
        
        counter1.inc()
        counter2.inc(2)
        
        assert counter1.value == 1.0
        assert counter2.value == 2.0
    
    def test_prometheus_format(self):
        """Should export in Prometheus format."""
        collector = MetricsCollector()
        
        counter = collector.counter("requests_total", "Total requests")
        counter.inc(5)
        
        output = collector.to_prometheus_format()
        
        assert "# HELP requests_total" in output
        assert "# TYPE requests_total counter" in output
        assert "requests_total 5" in output
    
    def test_stats(self):
        """Should report statistics."""
        collector = MetricsCollector()
        
        collector.counter("c1", "Counter 1")
        collector.gauge("g1", "Gauge 1")
        collector.histogram("h1", "Histogram 1")
        
        stats = collector.get_stats()
        
        assert stats["total_counters"] == 1
        assert stats["total_gauges"] == 1
        assert stats["total_histograms"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
