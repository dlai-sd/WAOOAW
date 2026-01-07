"""
Metrics Collection - Story 5.6

Application metrics collection and reporting.
Part of Epic 5: Common Components.
"""
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Similar to histogram


@dataclass
class Metric:
    """Base metric."""
    name: str
    metric_type: MetricType
    help_text: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class HistogramBucket:
    """Histogram bucket."""
    le: float  # Less than or equal to
    count: int = 0


class Counter:
    """Counter metric (always increases)."""
    
    def __init__(self, name: str, help_text: str, labels: Optional[Dict[str, str]] = None):
        """
        Initialize counter.
        
        Args:
            name: Metric name
            help_text: Description
            labels: Metric labels
        """
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self.value = 0.0
    
    def inc(self, amount: float = 1.0) -> None:
        """
        Increment counter.
        
        Args:
            amount: Amount to increment
        """
        if amount < 0:
            raise ValueError("Counter can only increase")
        
        self.value += amount
    
    def get(self) -> float:
        """Get current value."""
        return self.value
    
    def to_metric(self) -> Metric:
        """Convert to metric."""
        return Metric(
            name=self.name,
            metric_type=MetricType.COUNTER,
            help_text=self.help_text,
            labels=self.labels,
            value=self.value
        )


class Gauge:
    """Gauge metric (can go up or down)."""
    
    def __init__(self, name: str, help_text: str, labels: Optional[Dict[str, str]] = None):
        """Initialize gauge."""
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        self.value = 0.0
    
    def set(self, value: float) -> None:
        """Set gauge value."""
        self.value = value
    
    def inc(self, amount: float = 1.0) -> None:
        """Increment gauge."""
        self.value += amount
    
    def dec(self, amount: float = 1.0) -> None:
        """Decrement gauge."""
        self.value -= amount
    
    def get(self) -> float:
        """Get current value."""
        return self.value
    
    def to_metric(self) -> Metric:
        """Convert to metric."""
        return Metric(
            name=self.name,
            metric_type=MetricType.GAUGE,
            help_text=self.help_text,
            labels=self.labels,
            value=self.value
        )


class Histogram:
    """Histogram metric (distribution of values)."""
    
    def __init__(
        self,
        name: str,
        help_text: str,
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Initialize histogram.
        
        Args:
            name: Metric name
            help_text: Description
            buckets: Bucket boundaries (defaults: 0.005, 0.01, 0.025, ...)
            labels: Metric labels
        """
        self.name = name
        self.help_text = help_text
        self.labels = labels or {}
        
        # Default buckets (for latency in seconds)
        if buckets is None:
            buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        
        self.buckets = [HistogramBucket(le=b) for b in sorted(buckets)]
        self.buckets.append(HistogramBucket(le=float('inf')))  # +Inf bucket
        
        self.sum = 0.0
        self.count = 0
    
    def observe(self, value: float) -> None:
        """
        Observe a value.
        
        Args:
            value: Value to observe
        """
        self.sum += value
        self.count += 1
        
        # Update buckets
        for bucket in self.buckets:
            if value <= bucket.le:
                bucket.count += 1
    
    def get_count(self) -> int:
        """Get observation count."""
        return self.count
    
    def get_sum(self) -> float:
        """Get sum of observations."""
        return self.sum
    
    def get_average(self) -> float:
        """Get average value."""
        return self.sum / self.count if self.count > 0 else 0.0
    
    def to_metric(self) -> Metric:
        """Convert to metric."""
        return Metric(
            name=self.name,
            metric_type=MetricType.HISTOGRAM,
            help_text=self.help_text,
            labels=self.labels,
            value=self.get_average()
        )


class MetricsCollector:
    """
    Collects and manages application metrics.
    
    Features:
    - Counter, Gauge, Histogram metrics
    - Labeled metrics
    - Prometheus-compatible format
    - Custom metrics
    - Aggregation
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        
        logger.info("MetricsCollector initialized")
    
    def counter(
        self,
        name: str,
        help_text: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Counter:
        """
        Get or create counter.
        
        Args:
            name: Metric name
            help_text: Description
            labels: Metric labels
            
        Returns:
            Counter instance
        """
        key = self._make_key(name, labels)
        
        if key not in self.counters:
            self.counters[key] = Counter(name, help_text, labels)
        
        return self.counters[key]
    
    def gauge(
        self,
        name: str,
        help_text: str,
        labels: Optional[Dict[str, str]] = None
    ) -> Gauge:
        """
        Get or create gauge.
        
        Args:
            name: Metric name
            help_text: Description
            labels: Metric labels
            
        Returns:
            Gauge instance
        """
        key = self._make_key(name, labels)
        
        if key not in self.gauges:
            self.gauges[key] = Gauge(name, help_text, labels)
        
        return self.gauges[key]
    
    def histogram(
        self,
        name: str,
        help_text: str,
        buckets: Optional[List[float]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Histogram:
        """
        Get or create histogram.
        
        Args:
            name: Metric name
            help_text: Description
            buckets: Bucket boundaries
            labels: Metric labels
            
        Returns:
            Histogram instance
        """
        key = self._make_key(name, labels)
        
        if key not in self.histograms:
            self.histograms[key] = Histogram(name, help_text, buckets, labels)
        
        return self.histograms[key]
    
    def collect(self) -> List[Metric]:
        """
        Collect all metrics.
        
        Returns:
            List of all metrics
        """
        metrics = []
        
        # Collect counters
        for counter in self.counters.values():
            metrics.append(counter.to_metric())
        
        # Collect gauges
        for gauge in self.gauges.values():
            metrics.append(gauge.to_metric())
        
        # Collect histograms
        for histogram in self.histograms.values():
            metrics.append(histogram.to_metric())
        
        return metrics
    
    def to_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            Prometheus-formatted metrics
        """
        lines = []
        
        # Counters
        for counter in self.counters.values():
            lines.append(f"# HELP {counter.name} {counter.help_text}")
            lines.append(f"# TYPE {counter.name} counter")
            
            labels_str = self._format_labels(counter.labels)
            lines.append(f"{counter.name}{labels_str} {counter.value}")
        
        # Gauges
        for gauge in self.gauges.values():
            lines.append(f"# HELP {gauge.name} {gauge.help_text}")
            lines.append(f"# TYPE {gauge.name} gauge")
            
            labels_str = self._format_labels(gauge.labels)
            lines.append(f"{gauge.name}{labels_str} {gauge.value}")
        
        # Histograms
        for histogram in self.histograms.values():
            lines.append(f"# HELP {histogram.name} {histogram.help_text}")
            lines.append(f"# TYPE {histogram.name} histogram")
            
            labels_str = self._format_labels(histogram.labels)
            
            for bucket in histogram.buckets:
                bucket_labels = {**histogram.labels, "le": str(bucket.le)}
                bucket_labels_str = self._format_labels(bucket_labels)
                lines.append(f"{histogram.name}_bucket{bucket_labels_str} {bucket.count}")
            
            lines.append(f"{histogram.name}_sum{labels_str} {histogram.sum}")
            lines.append(f"{histogram.name}_count{labels_str} {histogram.count}")
        
        return "\n".join(lines)
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create unique key from name and labels."""
        if not labels:
            return name
        
        labels_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}@{labels_str}"
    
    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus."""
        if not labels:
            return ""
        
        labels_list = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return "{" + ",".join(labels_list) + "}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get metrics statistics."""
        return {
            "total_counters": len(self.counters),
            "total_gauges": len(self.gauges),
            "total_histograms": len(self.histograms),
            "total_metrics": len(self.counters) + len(self.gauges) + len(self.histograms)
        }


# Global metrics collector
_global_metrics: Optional[MetricsCollector] = None


def init_metrics() -> MetricsCollector:
    """
    Initialize global metrics collector.
    
    Returns:
        MetricsCollector instance
    """
    global _global_metrics
    _global_metrics = MetricsCollector()
    return _global_metrics


def get_metrics() -> MetricsCollector:
    """Get global metrics collector."""
    if _global_metrics is None:
        return init_metrics()
    return _global_metrics
