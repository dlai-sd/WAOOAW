"""
WowEvent Core - Event Bus Implementation

Story 1: WowEvent Core (Epic 3.1)
Points: 8

The event bus is the central nervous system of WAOOAW, enabling agents to:
- Publish events to notify others of actions/state changes
- Subscribe to event patterns to react to relevant changes
- Route messages efficiently using Redis pub/sub
- Handle events asynchronously without blocking

Event Flow:
1. Agent publishes event → Event bus receives → Redis distributes
2. Redis notifies subscribers → Event bus routes to handlers → Handlers process

Architecture:
- Publisher: Agent → EventBus.publish() → Redis PUBLISH
- Subscriber: Agent → EventBus.subscribe() → Redis SUBSCRIBE → Handler callback
- Pattern Matching: Redis glob patterns (agent.*, task.completed.*)
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types across the platform"""

    # Agent lifecycle events
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    AGENT_ERROR = "agent.error"

    # Task events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    # Capability events
    CAPABILITY_INVOKED = "capability.invoked"
    CAPABILITY_SUCCEEDED = "capability.succeeded"
    CAPABILITY_FAILED = "capability.failed"

    # Consciousness events
    CONSCIOUSNESS_WAKE = "consciousness.wake"
    CONSCIOUSNESS_SLEEP = "consciousness.sleep"
    CONSCIOUSNESS_REFLECTION = "consciousness.reflection"

    # System events
    SYSTEM_HEALTH_CHECK = "system.health_check"
    SYSTEM_ALERT = "system.alert"
    SYSTEM_METRIC = "system.metric"

    # Custom events (agents can define their own)
    CUSTOM = "custom"


class EventPriority(Enum):
    """Event priority levels"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """
    Event data structure.

    Every event in WAOOAW follows this structure for consistency
    and easy routing/filtering.

    Example:
        >>> event = Event(
        ...     event_type=EventType.TASK_COMPLETED,
        ...     source_agent="did:waooaw:agent:marketing",
        ...     payload={"task_id": "task-123", "result": "success"}
        ... )
    """

    event_type: EventType
    source_agent: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None  # For tracking related events
    target_agent: Optional[str] = None  # For direct messaging

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": (
                self.event_type.value
                if isinstance(self.event_type, EventType)
                else self.event_type
            ),
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "priority": (
                self.priority.value
                if isinstance(self.priority, EventPriority)
                else self.priority
            ),
            "correlation_id": self.correlation_id,
        }

    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary"""
        # Convert string values back to enums
        event_type = data.get("event_type")
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
            except ValueError:
                event_type = EventType.CUSTOM

        priority = data.get("priority", EventPriority.NORMAL.value)
        if isinstance(priority, int):
            priority = EventPriority(priority)

        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=event_type,
            source_agent=data["source_agent"],
            target_agent=data.get("target_agent"),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            priority=priority,
            correlation_id=data.get("correlation_id"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        """Create event from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Subscription:
    """
    Subscription to event patterns.

    Represents an agent's interest in specific events.
    """

    subscription_id: str
    subscriber_agent: str
    pattern: str  # Redis glob pattern (e.g., "agent.*", "task.completed")
    handler: Callable[[Event], None]
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    active: bool = True


class EventBus:
    """
    WowEvent Core - Redis-backed event bus.

    Enables pub/sub communication between agents using Redis as the
    message broker. Supports pattern-based subscriptions for flexible
    event routing.

    Example:
        >>> # Initialize event bus
        >>> bus = EventBus(redis_url="redis://localhost:6379")
        >>> await bus.start()
        >>> 
        >>> # Publish event
        >>> event = Event(
        ...     event_type=EventType.TASK_COMPLETED,
        ...     source_agent="did:waooaw:agent:marketing",
        ...     payload={"task_id": "task-123"}
        ... )
        >>> await bus.publish(event)
        >>> 
        >>> # Subscribe to events
        >>> def handle_task_completion(event: Event):
        ...     print(f"Task completed: {event.payload['task_id']}")
        >>> 
        >>> subscription = await bus.subscribe(
        ...     pattern="task.completed",
        ...     handler=handle_task_completion,
        ...     subscriber_agent="did:waooaw:agent:orchestrator"
        ... )
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        channel_prefix: str = "waooaw:events:",
    ):
        """
        Initialize event bus.

        Args:
            redis_url: Redis connection URL
            channel_prefix: Prefix for all Redis channels
        """
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix

        # Redis connections (separate for pub and sub)
        self.redis_client: Optional[redis.Redis] = None
        self.redis_pubsub: Optional[redis.client.PubSub] = None

        # Subscriptions
        self.subscriptions: Dict[str, Subscription] = {}
        self.pattern_to_subscriptions: Dict[str, Set[str]] = defaultdict(set)

        # Listener task
        self.listener_task: Optional[asyncio.Task] = None
        self.running = False

        # Stats
        self.events_published = 0
        self.events_delivered = 0
        self.subscription_count = 0

        logger.info(f"Event bus initialized with Redis: {redis_url}")

    async def start(self) -> None:
        """
        Start the event bus.

        Establishes Redis connections and starts listening for events.
        """
        if self.running:
            logger.warning("Event bus already running")
            return

        # Create Redis client
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)

        # Create pub/sub client
        self.redis_pubsub = self.redis_client.pubsub()

        # Start listener task
        self.running = True
        self.listener_task = asyncio.create_task(self._listen_for_events())

        logger.info("✅ Event bus started")

    async def stop(self) -> None:
        """
        Stop the event bus.

        Closes Redis connections and stops listening.
        """
        if not self.running:
            return

        self.running = False

        # Cancel listener task
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass

        # Close Redis connections
        if self.redis_pubsub:
            await self.redis_pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Event bus stopped")

    async def publish(self, event: Event) -> bool:
        """
        Publish an event to the bus.

        Args:
            event: Event to publish

        Returns:
            True if published successfully

        Raises:
            RuntimeError: If event bus is not running
        """
        if not self.running:
            raise RuntimeError("Event bus is not running")

        # Determine channel based on event type
        channel = self._get_channel_for_event(event)

        # Serialize event
        event_json = event.to_json()

        # Publish to Redis
        try:
            await self.redis_client.publish(channel, event_json)
            self.events_published += 1

            logger.debug(
                f"📤 Published {event.event_type.value if isinstance(event.event_type, EventType) else event.event_type} "
                f"from {event.source_agent} to {channel}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    async def subscribe(
        self,
        pattern: str,
        handler: Callable[[Event], None],
        subscriber_agent: str,
    ) -> Subscription:
        """
        Subscribe to events matching a pattern.

        Args:
            pattern: Redis glob pattern (e.g., "agent.*", "task.completed")
            handler: Async function to call when event matches
            subscriber_agent: DID of subscribing agent

        Returns:
            Subscription object
        """
        if not self.running:
            raise RuntimeError("Event bus is not running")

        # Create subscription
        subscription = Subscription(
            subscription_id=str(uuid.uuid4()),
            subscriber_agent=subscriber_agent,
            pattern=pattern,
            handler=handler,
        )

        # Store subscription
        self.subscriptions[subscription.subscription_id] = subscription
        self.pattern_to_subscriptions[pattern].add(subscription.subscription_id)
        self.subscription_count += 1

        # Subscribe to pattern in Redis
        channel_pattern = f"{self.channel_prefix}{pattern}"
        await self.redis_pubsub.psubscribe(channel_pattern)

        logger.info(
            f"📥 {subscriber_agent} subscribed to pattern '{pattern}' "
            f"(subscription: {subscription.subscription_id})"
        )

        return subscription

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.

        Args:
            subscription_id: Subscription ID to cancel

        Returns:
            True if unsubscribed successfully
        """
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            logger.warning(f"Subscription {subscription_id} not found")
            return False

        # Mark as inactive
        subscription.active = False

        # Remove from pattern mapping
        self.pattern_to_subscriptions[subscription.pattern].discard(subscription_id)

        # If no more subscriptions for this pattern, unsubscribe from Redis
        if not self.pattern_to_subscriptions[subscription.pattern]:
            channel_pattern = f"{self.channel_prefix}{subscription.pattern}"
            await self.redis_pubsub.punsubscribe(channel_pattern)
            del self.pattern_to_subscriptions[subscription.pattern]

        # Remove subscription
        del self.subscriptions[subscription_id]
        self.subscription_count -= 1

        logger.info(
            f"Unsubscribed {subscription.subscriber_agent} from {subscription.pattern}"
        )

        return True

    async def _listen_for_events(self) -> None:
        """
        Background task that listens for events from Redis.

        This runs continuously while the event bus is active,
        receiving events and routing them to subscribers.
        """
        logger.info("Event listener started")

        try:
            async for message in self.redis_pubsub.listen():
                if not self.running:
                    break

                if message["type"] == "pmessage":
                    # Extract event data
                    pattern = message["pattern"].decode("utf-8") if isinstance(message["pattern"], bytes) else message["pattern"]
                    channel = message["channel"].decode("utf-8") if isinstance(message["channel"], bytes) else message["channel"]
                    data = message["data"]

                    # Remove channel prefix from pattern
                    if pattern.startswith(self.channel_prefix):
                        pattern = pattern[len(self.channel_prefix):]

                    try:
                        # Deserialize event
                        event = Event.from_json(data)

                        # Route to matching subscriptions
                        await self._route_event(pattern, event)

                    except Exception as e:
                        logger.error(f"Failed to process event: {e}")

        except asyncio.CancelledError:
            logger.info("Event listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Event listener error: {e}")
        finally:
            logger.info("Event listener stopped")

    async def _route_event(self, pattern: str, event: Event) -> None:
        """
        Route an event to all matching subscriptions.

        Args:
            pattern: Pattern that matched this event
            event: Event to route
        """
        # Find subscriptions matching this pattern
        subscription_ids = self.pattern_to_subscriptions.get(pattern, set())

        for subscription_id in subscription_ids:
            subscription = self.subscriptions.get(subscription_id)

            if not subscription or not subscription.active:
                continue

            try:
                # Call handler (async or sync)
                if asyncio.iscoroutinefunction(subscription.handler):
                    await subscription.handler(event)
                else:
                    subscription.handler(event)

                self.events_delivered += 1

                logger.debug(
                    f"📨 Delivered {event.event_type.value if isinstance(event.event_type, EventType) else event.event_type} "
                    f"to {subscription.subscriber_agent}"
                )

            except Exception as e:
                logger.error(
                    f"Handler error for {subscription.subscriber_agent}: {e}",
                    exc_info=True,
                )

    def _get_channel_for_event(self, event: Event) -> str:
        """
        Determine Redis channel for an event.

        Args:
            event: Event to get channel for

        Returns:
            Redis channel name
        """
        event_type_str = (
            event.event_type.value
            if isinstance(event.event_type, EventType)
            else event.event_type
        )
        return f"{self.channel_prefix}{event_type_str}"

    def get_stats(self) -> Dict[str, Any]:
        """
        Get event bus statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "running": self.running,
            "events_published": self.events_published,
            "events_delivered": self.events_delivered,
            "active_subscriptions": self.subscription_count,
            "patterns": list(self.pattern_to_subscriptions.keys()),
        }
