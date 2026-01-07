"""
Events Module - WowEvent Event Bus

Epic 3.1: Event Bus Implementation (Theme 3 TODDLER)

The events module provides the central nervous system for WAOOAW agents:
- Event publishing and subscription
- Redis-based pub/sub messaging
- Pattern-based routing
- Async event delivery
- Event lifecycle management
- Schema validation for data quality
- Dead letter queue for failed events
- Event replay for time-travel debugging

This enables agents to communicate, collaborate, and coordinate
actions across the platform with resilience, reliability, and history.
"""

from waooaw.events.event_bus import (
    EventBus,
    Event,
    EventType,
    EventPriority,
    Subscription,
)
from waooaw.events.schemas import (
    EventSchema,
    EventValidator,
    SchemaRegistry,
    ValidationError,
)
from waooaw.events.dlq import (
    DeadLetterQueue,
    FailedEvent,
    FailureReason,
)
from waooaw.events.replay import (
    EventStore,
    EventReplayer,
    ReplayConfig,
)
from waooaw.events.metrics import (
    EventMetrics,
    LatencyStats,
    MetricType,
    SubscriberHealth,
    SubscriberMetrics,
    EventTypeMetrics,
)

__version__ = "0.6.5-dev"

__all__ = [
    "EventBus",
    "Event",
    "EventType",
    "EventPriority",
    "Subscription",
    "EventSchema",
    "EventValidator",
    "SchemaRegistry",
    "ValidationError",
    "DeadLetterQueue",
    "FailedEvent",
    "FailureReason",
    "EventStore",
    "EventReplayer",
    "ReplayConfig",
    "EventMetrics",
    "LatencyStats",
    "MetricType",
    "SubscriberHealth",
    "SubscriberMetrics",
    "EventTypeMetrics",
]
