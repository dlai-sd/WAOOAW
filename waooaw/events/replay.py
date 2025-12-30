"""
Event Replay - Time Travel for Events

Story 4: Event Replay (Epic 3.1)
Points: 3

Enables replaying historical events for debugging, catch-up, and event sourcing.
Agents can "time travel" to see past events or catch up after being offline.

Features:
- Time-based event replay (from timestamp)
- Event stream storage and retrieval
- Pattern-based replay filtering
- Agent catch-up on join/restart
- Event sourcing support
- Replay speed control (real-time vs fast-forward)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Callable
from collections import deque

from waooaw.events.event_bus import Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class ReplayConfig:
    """Configuration for event replay"""

    start_time: Optional[str] = None  # ISO timestamp to start from
    end_time: Optional[str] = None  # ISO timestamp to end at
    pattern: Optional[str] = None  # Event pattern filter (e.g., "task.*")
    max_events: Optional[int] = None  # Maximum events to replay
    speed_multiplier: float = 1.0  # Replay speed (1.0 = real-time, 2.0 = 2x, 0 = instant)
    include_failures: bool = False  # Include events that failed delivery


class EventStore:
    """
    Stores events for replay.

    In production, this would be backed by a database or event store
    (e.g., PostgreSQL, Kafka, EventStoreDB). For now, uses in-memory storage.
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize event store.

        Args:
            max_size: Maximum events to store (FIFO eviction)
        """
        self.max_size = max_size
        self.events: deque = deque(maxlen=max_size)
        self.events_by_type: Dict[str, List[Event]] = {}
        self.total_stored = 0

        logger.info(f"Event store initialized (max_size: {max_size})")

    def store(self, event: Event) -> None:
        """
        Store an event.

        Args:
            event: Event to store
        """
        self.events.append(event)
        self.total_stored += 1

        # Index by type
        event_type = (
            event.event_type.value
            if isinstance(event.event_type, EventType)
            else event.event_type
        )

        if event_type not in self.events_by_type:
            self.events_by_type[event_type] = []

        self.events_by_type[event_type].append(event)

        logger.debug(f"Stored event: {event.event_id} ({event_type})")

    def get_events(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        pattern: Optional[str] = None,
        max_events: Optional[int] = None,
    ) -> List[Event]:
        """
        Retrieve events matching criteria.

        Args:
            start_time: ISO timestamp to start from
            end_time: ISO timestamp to end at
            pattern: Event type pattern (e.g., "task.*")
            max_events: Maximum events to return

        Returns:
            List of matching events
        """
        matching_events = []

        # Parse time filters
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        for event in self.events:
            # Time filter
            event_time = datetime.fromisoformat(event.timestamp)

            if start_dt and event_time < start_dt:
                continue
            if end_dt and event_time > end_dt:
                continue

            # Pattern filter
            if pattern:
                event_type = (
                    event.event_type.value
                    if isinstance(event.event_type, EventType)
                    else event.event_type
                )

                if not self._matches_pattern(event_type, pattern):
                    continue

            matching_events.append(event)

            # Max events limit
            if max_events and len(matching_events) >= max_events:
                break

        logger.info(
            f"Retrieved {len(matching_events)} events "
            f"(filters: start={start_time}, end={end_time}, pattern={pattern})"
        )

        return matching_events

    def get_events_since(self, timestamp: str) -> List[Event]:
        """
        Get all events since a timestamp.

        Args:
            timestamp: ISO timestamp

        Returns:
            List of events since timestamp
        """
        return self.get_events(start_time=timestamp)

    def get_events_by_type(self, event_type: str) -> List[Event]:
        """
        Get all events of a specific type.

        Args:
            event_type: Event type to filter by

        Returns:
            List of matching events
        """
        return self.events_by_type.get(event_type, []).copy()

    def get_latest_events(self, count: int = 10) -> List[Event]:
        """
        Get the most recent events.

        Args:
            count: Number of events to return

        Returns:
            List of latest events
        """
        return list(self.events)[-count:]

    def clear(self) -> int:
        """
        Clear all stored events.

        Returns:
            Number of events cleared
        """
        count = len(self.events)
        self.events.clear()
        self.events_by_type.clear()
        logger.info(f"Cleared {count} events from store")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get event store statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "current_size": len(self.events),
            "max_size": self.max_size,
            "total_stored": self.total_stored,
            "event_types": len(self.events_by_type),
            "oldest_event": (
                self.events[0].timestamp if len(self.events) > 0 else None
            ),
            "newest_event": (
                self.events[-1].timestamp if len(self.events) > 0 else None
            ),
        }

    def _matches_pattern(self, event_type: str, pattern: str) -> bool:
        """
        Check if event type matches pattern.

        Supports simple glob patterns:
        - "task.*" matches "task.created", "task.completed", etc.
        - "*" matches all
        - "task.completed" matches exactly "task.completed"

        Args:
            event_type: Event type to check
            pattern: Pattern to match against

        Returns:
            True if matches
        """
        if pattern == "*":
            return True

        if "*" in pattern:
            # Simple glob pattern matching
            prefix = pattern.rstrip("*")
            return event_type.startswith(prefix)

        return event_type == pattern


class EventReplayer:
    """
    Replays historical events.

    Enables agents to "catch up" on missed events or replay events for debugging.
    """

    def __init__(self, event_store: EventStore):
        """
        Initialize replayer.

        Args:
            event_store: Event store to replay from
        """
        self.event_store = event_store
        self.active_replays: Dict[str, asyncio.Task] = {}

        logger.info("Event replayer initialized")

    async def replay(
        self,
        handler: Callable[[Event], None],
        config: ReplayConfig,
        replay_id: Optional[str] = None,
    ) -> int:
        """
        Replay events to a handler.

        Args:
            handler: Function to call for each event
            config: Replay configuration
            replay_id: Optional ID to track this replay

        Returns:
            Number of events replayed
        """
        replay_id = replay_id or f"replay-{datetime.now(timezone.utc).timestamp()}"

        logger.info(f"Starting replay: {replay_id} (config: {config})")

        # Get events to replay
        events = self.event_store.get_events(
            start_time=config.start_time,
            end_time=config.end_time,
            pattern=config.pattern,
            max_events=config.max_events,
        )

        if not events:
            logger.warning(f"No events to replay for {replay_id}")
            return 0

        # Replay events
        replayed = 0
        prev_timestamp = None

        for event in events:
            try:
                # Calculate delay for real-time replay
                if config.speed_multiplier > 0 and prev_timestamp:
                    event_time = datetime.fromisoformat(event.timestamp)
                    prev_time = datetime.fromisoformat(prev_timestamp)
                    real_delay = (event_time - prev_time).total_seconds()
                    adjusted_delay = real_delay / config.speed_multiplier

                    if adjusted_delay > 0:
                        await asyncio.sleep(adjusted_delay)

                prev_timestamp = event.timestamp

                # Call handler
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)

                replayed += 1

            except Exception as e:
                logger.error(f"Error replaying event {event.event_id}: {e}")

        logger.info(f"Replay complete: {replay_id} ({replayed} events)")
        return replayed

    async def replay_async(
        self,
        handler: Callable[[Event], None],
        config: ReplayConfig,
        replay_id: Optional[str] = None,
    ) -> str:
        """
        Start asynchronous replay (non-blocking).

        Args:
            handler: Function to call for each event
            config: Replay configuration
            replay_id: Optional ID to track this replay

        Returns:
            Replay ID
        """
        replay_id = replay_id or f"replay-{datetime.now(timezone.utc).timestamp()}"

        # Start replay task
        task = asyncio.create_task(self.replay(handler, config, replay_id))
        self.active_replays[replay_id] = task

        logger.info(f"Started async replay: {replay_id}")
        return replay_id

    async def cancel_replay(self, replay_id: str) -> bool:
        """
        Cancel an active replay.

        Args:
            replay_id: Replay ID to cancel

        Returns:
            True if cancelled successfully
        """
        if replay_id not in self.active_replays:
            logger.warning(f"Replay not found: {replay_id}")
            return False

        task = self.active_replays[replay_id]
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        del self.active_replays[replay_id]
        logger.info(f"Cancelled replay: {replay_id}")
        return True

    def get_active_replays(self) -> List[str]:
        """
        Get list of active replay IDs.

        Returns:
            List of replay IDs
        """
        return list(self.active_replays.keys())

    async def catch_up(
        self,
        handler: Callable[[Event], None],
        last_seen_timestamp: str,
        pattern: Optional[str] = None,
    ) -> int:
        """
        Catch up on events since last seen timestamp.

        Useful for agents joining late or recovering from downtime.

        Args:
            handler: Function to call for each event
            last_seen_timestamp: ISO timestamp of last event agent saw
            pattern: Optional event pattern filter

        Returns:
            Number of events replayed
        """
        logger.info(f"Agent catching up from {last_seen_timestamp}")

        config = ReplayConfig(
            start_time=last_seen_timestamp,
            pattern=pattern,
            speed_multiplier=0,  # Instant replay (no delays)
        )

        return await self.replay(handler, config)

    async def replay_event_stream(
        self,
        handler: Callable[[Event], None],
        event_ids: List[str],
    ) -> int:
        """
        Replay specific events by ID.

        Args:
            handler: Function to call for each event
            event_ids: List of event IDs to replay

        Returns:
            Number of events replayed
        """
        logger.info(f"Replaying {len(event_ids)} specific events")

        replayed = 0

        for event in self.event_store.events:
            if event.event_id in event_ids:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)

                    replayed += 1
                except Exception as e:
                    logger.error(f"Error replaying event {event.event_id}: {e}")

        logger.info(f"Replayed {replayed} events")
        return replayed

    def get_replay_stats(self) -> Dict[str, Any]:
        """
        Get replay statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "active_replays": len(self.active_replays),
            "replay_ids": list(self.active_replays.keys()),
        }
