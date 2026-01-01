"""
Metrics Aggregator Service

Collects, aggregates, and stores metrics from agents and system components.
Provides real-time metrics querying and historical data analysis.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""

    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class AggregatedMetric:
    """Aggregated metric with statistics"""

    name: str
    count: int
    sum: float
    min: float
    max: float
    avg: float
    last_value: float
    last_updated: datetime


class MetricsAggregator:
    """
    Collects and aggregates time-series metrics.

    Features:
    - Real-time metric collection
    - Statistical aggregation (min, max, avg, sum, count)
    - Time-window queries
    - Tag-based filtering
    - Automatic retention management
    """

    def __init__(
        self, retention_hours: float = 1.0, max_points_per_metric: int = 10000
    ):
        """
        Initialize metrics aggregator.

        Args:
            retention_hours: How long to retain metrics in hours (default: 1 hour)
            max_points_per_metric: Maximum points to store per metric
        """
        self.retention_hours = retention_hours
        self.max_points_per_metric = max_points_per_metric
        self.metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.aggregates: Dict[str, AggregatedMetric] = {}

    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a metric value.

        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for filtering
        """
        point = MetricPoint(timestamp=datetime.now(), value=value, tags=tags or {})
        self.metrics[name].append(point)

        # Trim if exceeds max
        if len(self.metrics[name]) > self.max_points_per_metric:
            self.metrics[name] = self.metrics[name][-self.max_points_per_metric :]

        self._update_aggregate(name)
        logger.debug(f"Recorded metric: {name}={value}")

    def _update_aggregate(self, name: str):
        """Update aggregated statistics for a metric"""
        if name not in self.metrics or not self.metrics[name]:
            return

        points = list(self.metrics[name])
        values = [p.value for p in points]

        self.aggregates[name] = AggregatedMetric(
            name=name,
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            avg=statistics.mean(values),
            last_value=values[-1],
            last_updated=points[-1].timestamp,
        )

    def get_aggregate(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> AggregatedMetric:
        """
        Get aggregated statistics for a metric.

        Args:
            name: Metric name
            tags: Optional tags for filtering

        Returns:
            Aggregated statistics (returns empty aggregate if not found)
        """
        if name not in self.metrics or not self.metrics[name]:
            # Return empty aggregate
            return AggregatedMetric(
                name=name,
                count=0,
                sum=0.0,
                min=0.0,
                max=0.0,
                avg=0.0,
                last_value=0.0,
                last_updated=datetime.now(),
            )

        points = list(self.metrics[name])

        # Filter by tags if provided
        if tags:
            points = [
                p for p in points if all(p.tags.get(k) == v for k, v in tags.items())
            ]

        if not points:
            return AggregatedMetric(
                name=name,
                count=0,
                sum=0.0,
                min=0.0,
                max=0.0,
                avg=0.0,
                last_value=0.0,
                last_updated=datetime.now(),
            )

        values = [p.value for p in points]

        return AggregatedMetric(
            name=name,
            count=len(values),
            sum=sum(values),
            min=min(values),
            max=max(values),
            avg=statistics.mean(values),
            last_value=values[-1],
            last_updated=points[-1].timestamp,
        )

    def get_series(
        self,
        name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> List[MetricPoint]:
        """
        Get time-series data for a metric.

        Args:
            name: Metric name
            start_time: Start time filter
            end_time: End time filter
            tags: Tag filters

        Returns:
            List of metric points
        """
        if name not in self.metrics:
            return []

        points = list(self.metrics[name])

        # Apply time filters
        if start_time:
            points = [p for p in points if p.timestamp >= start_time]
        if end_time:
            points = [p for p in points if p.timestamp <= end_time]

        # Apply tag filters
        if tags:
            points = [
                p for p in points if all(p.tags.get(k) == v for k, v in tags.items())
            ]

        return points

    def get_latest(self, name: str, count: int = 10) -> List[MetricPoint]:
        """Get latest N metric points (newest first)"""
        if name not in self.metrics:
            return []
        # Return in reverse order (newest first)
        return list(reversed(self.metrics[name][-count:]))

    def cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff = datetime.now() - timedelta(hours=self.retention_hours)
        removed = 0

        for name in list(self.metrics.keys()):
            original_len = len(self.metrics[name])
            self.metrics[name] = [p for p in self.metrics[name] if p.timestamp > cutoff]
            removed += original_len - len(self.metrics[name])

            if not self.metrics[name]:
                del self.metrics[name]
                if name in self.aggregates:
                    del self.aggregates[name]

        logger.info(f"Cleaned up {removed} old metric points")

    def get_all_metrics(self) -> List[str]:
        """Get list of all metric names"""
        return list(self.metrics.keys())

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        return {
            "total_metrics": len(self.metrics),
            "total_points": sum(len(v) for v in self.metrics.values()),
            "retention_hours": self.retention_hours,
            "max_points_per_metric": self.max_points_per_metric,
            "metric_counts": {
                name: len(points) for name, points in self.metrics.items()
            },
        }
