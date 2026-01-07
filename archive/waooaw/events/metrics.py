"""
Event Bus Metrics System

Provides comprehensive observability for the WowEvent system including:
- Throughput tracking (events/sec, messages/sec)
- Latency measurements (p50, p95, p99)
- Subscriber health monitoring
- Pattern-based metrics aggregation

Usage:
    metrics = EventMetrics()
    
    # Record event publication
    metrics.record_publish("task.created")
    
    # Record delivery
    metrics.record_delivery("task.created", "worker-agent", 0.025)
    
    # Get metrics
    stats = metrics.get_metrics()
    print(f"Throughput: {stats['throughput']['events_per_sec']}")
    print(f"P95 latency: {stats['latency']['p95']}ms")
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Deque
import statistics


class MetricType(Enum):
    """Types of metrics tracked."""
    PUBLISH = "publish"
    DELIVERY = "delivery"
    ERROR = "error"
    RETRY = "retry"
    DLQ = "dlq"


class SubscriberHealth(Enum):
    """Health status of subscribers."""
    HEALTHY = "healthy"      # < 5% error rate, latency < 1s
    DEGRADED = "degraded"    # 5-20% error rate or latency 1-5s
    UNHEALTHY = "unhealthy"  # > 20% error rate or latency > 5s
    UNKNOWN = "unknown"      # No recent activity


@dataclass
class LatencyStats:
    """Statistical latency measurements."""
    count: int = 0
    min: float = 0.0
    max: float = 0.0
    mean: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    
    @classmethod
    def from_samples(cls, samples: List[float]) -> "LatencyStats":
        """Calculate stats from latency samples."""
        if not samples:
            return cls()
        
        sorted_samples = sorted(samples)
        count = len(sorted_samples)
        
        return cls(
            count=count,
            min=sorted_samples[0],
            max=sorted_samples[-1],
            mean=statistics.mean(sorted_samples),
            p50=cls._percentile(sorted_samples, 50),
            p95=cls._percentile(sorted_samples, 95),
            p99=cls._percentile(sorted_samples, 99)
        )
    
    @staticmethod
    def _percentile(sorted_samples: List[float], percentile: int) -> float:
        """Calculate percentile from sorted samples."""
        if not sorted_samples:
            return 0.0
        
        index = int((percentile / 100.0) * len(sorted_samples))
        index = min(index, len(sorted_samples) - 1)
        return sorted_samples[index]


@dataclass
class SubscriberMetrics:
    """Metrics for a single subscriber."""
    subscriber_id: str
    patterns: Set[str] = field(default_factory=set)
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    total_latency: float = 0.0
    last_activity: Optional[datetime] = None
    health: SubscriberHealth = SubscriberHealth.UNKNOWN
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate (0.0 to 1.0)."""
        if self.total_deliveries == 0:
            return 0.0
        return self.failed_deliveries / self.total_deliveries
    
    @property
    def avg_latency(self) -> float:
        """Calculate average latency in seconds."""
        if self.successful_deliveries == 0:
            return 0.0
        return self.total_latency / self.successful_deliveries
    
    def update_health(self) -> None:
        """Update health status based on error rate and latency."""
        if self.total_deliveries == 0:
            self.health = SubscriberHealth.UNKNOWN
            return
        
        error_rate = self.error_rate
        avg_latency = self.avg_latency
        
        if error_rate > 0.20 or avg_latency > 5.0:
            self.health = SubscriberHealth.UNHEALTHY
        elif error_rate > 0.05 or avg_latency > 1.0:
            self.health = SubscriberHealth.DEGRADED
        else:
            self.health = SubscriberHealth.HEALTHY


@dataclass
class EventTypeMetrics:
    """Metrics for a specific event type."""
    event_type: str
    publish_count: int = 0
    delivery_count: int = 0
    error_count: int = 0
    retry_count: int = 0
    dlq_count: int = 0
    latency_samples: Deque[float] = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_latency(self, latency: float) -> None:
        """Add a latency sample."""
        self.latency_samples.append(latency)
    
    def get_latency_stats(self) -> LatencyStats:
        """Get latency statistics."""
        return LatencyStats.from_samples(list(self.latency_samples))


class EventMetrics:
    """
    Comprehensive metrics tracking for the event bus.
    
    Tracks:
    - Event publication counts by type
    - Delivery latencies (p50/p95/p99)
    - Subscriber health (error rates, latencies)
    - Throughput (events/sec, messages/sec)
    - System-wide statistics
    
    Thread-safe for async operations.
    """
    
    def __init__(self, window_seconds: int = 60):
        """
        Initialize metrics tracker.
        
        Args:
            window_seconds: Time window for throughput calculations (default: 60s)
        """
        self.window_seconds = window_seconds
        
        # Event type metrics
        self.event_types: Dict[str, EventTypeMetrics] = defaultdict(
            lambda: EventTypeMetrics(event_type="")
        )
        
        # Subscriber metrics
        self.subscribers: Dict[str, SubscriberMetrics] = {}
        
        # Time-windowed counters for throughput
        self.recent_publishes: Deque[float] = deque(maxlen=10000)
        self.recent_deliveries: Deque[float] = deque(maxlen=10000)
        
        # System totals
        self.total_publishes = 0
        self.total_deliveries = 0
        self.total_errors = 0
        self.total_retries = 0
        self.total_dlq = 0
        
        self.start_time = datetime.now()
        self._lock = asyncio.Lock()
    
    async def record_publish(self, event_type: str) -> None:
        """Record an event publication."""
        async with self._lock:
            self.total_publishes += 1
            self.recent_publishes.append(time.time())
            
            metrics = self.event_types[event_type]
            metrics.event_type = event_type
            metrics.publish_count += 1
    
    async def record_delivery(
        self,
        event_type: str,
        subscriber_id: str,
        latency: float,
        success: bool = True
    ) -> None:
        """
        Record event delivery to a subscriber.
        
        Args:
            event_type: Type of event delivered
            subscriber_id: ID of subscriber
            latency: Delivery latency in seconds
            success: Whether delivery succeeded
        """
        async with self._lock:
            now = time.time()
            self.recent_deliveries.append(now)
            
            # Update event type metrics
            metrics = self.event_types[event_type]
            metrics.event_type = event_type
            metrics.delivery_count += 1
            
            if success:
                self.total_deliveries += 1
                metrics.add_latency(latency)
            else:
                self.total_errors += 1
                metrics.error_count += 1
            
            # Update subscriber metrics
            if subscriber_id not in self.subscribers:
                self.subscribers[subscriber_id] = SubscriberMetrics(
                    subscriber_id=subscriber_id
                )
            
            sub_metrics = self.subscribers[subscriber_id]
            sub_metrics.total_deliveries += 1
            sub_metrics.last_activity = datetime.now()
            
            if success:
                sub_metrics.successful_deliveries += 1
                sub_metrics.total_latency += latency
            else:
                sub_metrics.failed_deliveries += 1
            
            sub_metrics.update_health()
    
    async def record_error(self, event_type: str) -> None:
        """Record an error for an event type."""
        async with self._lock:
            self.total_errors += 1
            metrics = self.event_types[event_type]
            metrics.event_type = event_type
            metrics.error_count += 1
    
    async def record_retry(self, event_type: str) -> None:
        """Record a retry attempt."""
        async with self._lock:
            self.total_retries += 1
            metrics = self.event_types[event_type]
            metrics.event_type = event_type
            metrics.retry_count += 1
    
    async def record_dlq(self, event_type: str) -> None:
        """Record an event sent to dead letter queue."""
        async with self._lock:
            self.total_dlq += 1
            metrics = self.event_types[event_type]
            metrics.event_type = event_type
            metrics.dlq_count += 1
    
    async def register_subscriber(
        self,
        subscriber_id: str,
        patterns: Set[str]
    ) -> None:
        """Register a subscriber with their patterns."""
        async with self._lock:
            if subscriber_id not in self.subscribers:
                self.subscribers[subscriber_id] = SubscriberMetrics(
                    subscriber_id=subscriber_id,
                    patterns=patterns
                )
            else:
                self.subscribers[subscriber_id].patterns.update(patterns)
    
    async def unregister_subscriber(self, subscriber_id: str) -> None:
        """Unregister a subscriber."""
        async with self._lock:
            if subscriber_id in self.subscribers:
                del self.subscribers[subscriber_id]
    
    def _calculate_throughput(
        self,
        recent_events: Deque[float]
    ) -> Dict[str, float]:
        """Calculate throughput from recent events."""
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Count events in window
        count = sum(1 for t in recent_events if t >= cutoff)
        
        return {
            "count": count,
            "per_second": count / self.window_seconds if self.window_seconds > 0 else 0.0,
            "per_minute": count * 60 / self.window_seconds if self.window_seconds > 0 else 0.0
        }
    
    async def get_metrics(self) -> Dict:
        """
        Get comprehensive metrics snapshot.
        
        Returns:
            Dictionary with throughput, latency, subscribers, and event type stats
        """
        async with self._lock:
            # Calculate throughput
            publish_throughput = self._calculate_throughput(self.recent_publishes)
            delivery_throughput = self._calculate_throughput(self.recent_deliveries)
            
            # Aggregate latency across all event types
            all_latencies = []
            for metrics in self.event_types.values():
                all_latencies.extend(metrics.latency_samples)
            
            overall_latency = LatencyStats.from_samples(all_latencies)
            
            # Subscriber health summary
            health_summary = {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "unknown": 0
            }
            
            for sub in self.subscribers.values():
                health_summary[sub.health.value] += 1
            
            # Event type stats
            event_type_stats = {}
            for event_type, metrics in self.event_types.items():
                event_type_stats[event_type] = {
                    "publishes": metrics.publish_count,
                    "deliveries": metrics.delivery_count,
                    "errors": metrics.error_count,
                    "retries": metrics.retry_count,
                    "dlq": metrics.dlq_count,
                    "latency": {
                        "p50": metrics.get_latency_stats().p50,
                        "p95": metrics.get_latency_stats().p95,
                        "p99": metrics.get_latency_stats().p99
                    }
                }
            
            return {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "throughput": {
                    "publishes": publish_throughput,
                    "deliveries": delivery_throughput
                },
                "latency": {
                    "count": overall_latency.count,
                    "min": overall_latency.min,
                    "max": overall_latency.max,
                    "mean": overall_latency.mean,
                    "p50": overall_latency.p50,
                    "p95": overall_latency.p95,
                    "p99": overall_latency.p99
                },
                "totals": {
                    "publishes": self.total_publishes,
                    "deliveries": self.total_deliveries,
                    "errors": self.total_errors,
                    "retries": self.total_retries,
                    "dlq": self.total_dlq
                },
                "subscribers": {
                    "total": len(self.subscribers),
                    "health": health_summary
                },
                "event_types": event_type_stats
            }
    
    async def get_subscriber_metrics(
        self,
        subscriber_id: str
    ) -> Optional[Dict]:
        """Get metrics for a specific subscriber."""
        async with self._lock:
            if subscriber_id not in self.subscribers:
                return None
            
            metrics = self.subscribers[subscriber_id]
            return {
                "subscriber_id": metrics.subscriber_id,
                "patterns": list(metrics.patterns),
                "health": metrics.health.value,
                "total_deliveries": metrics.total_deliveries,
                "successful_deliveries": metrics.successful_deliveries,
                "failed_deliveries": metrics.failed_deliveries,
                "error_rate": metrics.error_rate,
                "avg_latency": metrics.avg_latency,
                "last_activity": metrics.last_activity.isoformat() if metrics.last_activity else None
            }
    
    async def get_unhealthy_subscribers(self) -> List[str]:
        """Get list of unhealthy subscriber IDs."""
        async with self._lock:
            return [
                sub_id
                for sub_id, metrics in self.subscribers.items()
                if metrics.health == SubscriberHealth.UNHEALTHY
            ]
    
    async def reset(self) -> None:
        """Reset all metrics."""
        async with self._lock:
            self.event_types.clear()
            self.subscribers.clear()
            self.recent_publishes.clear()
            self.recent_deliveries.clear()
            self.total_publishes = 0
            self.total_deliveries = 0
            self.total_errors = 0
            self.total_retries = 0
            self.total_dlq = 0
            self.start_time = datetime.now()
