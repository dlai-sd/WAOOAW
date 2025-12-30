"""
Dead Letter Queue (DLQ) - Failed Event Handling

Story 3: Dead Letter Queue (Epic 3.1)
Points: 3

Handles events that fail delivery or processing with automatic retry logic.
Provides resilience for the event bus through exponential backoff and monitoring.

Features:
- Failed event capture and storage
- Exponential backoff retry logic
- Max retry limits with DLQ persistence
- DLQ monitoring and inspection
- Manual retry/reprocess capabilities
- Failure reason tracking
"""

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import json

from waooaw.events.event_bus import Event

logger = logging.getLogger(__name__)


class FailureReason(Enum):
    """Reasons why event delivery/processing failed"""

    HANDLER_ERROR = "handler_error"  # Handler threw exception
    TIMEOUT = "timeout"  # Handler exceeded timeout
    VALIDATION_ERROR = "validation_error"  # Event failed validation
    SUBSCRIBER_UNAVAILABLE = "subscriber_unavailable"  # Subscriber offline
    DESERIALIZATION_ERROR = "deserialization_error"  # Couldn't parse event
    UNKNOWN = "unknown"  # Unknown failure


@dataclass
class FailedEvent:
    """
    Represents an event that failed delivery/processing.

    Tracks retry attempts, failure reasons, and backoff timing.
    """

    event: Event
    subscription_id: str
    subscriber_agent: str
    failure_reason: FailureReason
    error_message: str
    failed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[str] = None
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "event": self.event.to_dict(),
            "subscription_id": self.subscription_id,
            "subscriber_agent": self.subscriber_agent,
            "failure_reason": self.failure_reason.value,
            "error_message": self.error_message,
            "failed_at": self.failed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry_at": self.next_retry_at,
            "last_error": self.last_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailedEvent":
        """Create from dictionary"""
        return cls(
            event=Event.from_dict(data["event"]),
            subscription_id=data["subscription_id"],
            subscriber_agent=data["subscriber_agent"],
            failure_reason=FailureReason(data["failure_reason"]),
            error_message=data["error_message"],
            failed_at=data.get("failed_at", datetime.now(timezone.utc).isoformat()),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            next_retry_at=data.get("next_retry_at"),
            last_error=data.get("last_error"),
        )


class DeadLetterQueue:
    """
    Dead Letter Queue for failed events.

    Captures failed events, implements retry logic with exponential backoff,
    and provides monitoring capabilities.
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_seconds: float = 1.0,
        max_backoff_seconds: float = 300.0,
        backoff_multiplier: float = 2.0,
    ):
        """
        Initialize DLQ.

        Args:
            max_retries: Maximum retry attempts before permanent failure
            initial_backoff_seconds: Initial backoff delay
            max_backoff_seconds: Maximum backoff delay
            backoff_multiplier: Backoff multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.initial_backoff_seconds = initial_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.backoff_multiplier = backoff_multiplier

        # Storage
        self.retry_queue: List[FailedEvent] = []  # Events awaiting retry
        self.dead_letters: List[FailedEvent] = []  # Permanently failed events

        # Retry task
        self.retry_task: Optional[asyncio.Task] = None
        self.running = False

        # Stats
        self.total_failures = 0
        self.total_retries = 0
        self.successful_retries = 0
        self.permanent_failures = 0

        logger.info(
            f"DLQ initialized: max_retries={max_retries}, "
            f"backoff={initial_backoff_seconds}s-{max_backoff_seconds}s"
        )

    async def start(self) -> None:
        """Start the DLQ retry processor"""
        if self.running:
            return

        self.running = True
        self.retry_task = asyncio.create_task(self._process_retries())
        logger.info("✅ DLQ retry processor started")

    async def stop(self) -> None:
        """Stop the DLQ retry processor"""
        if not self.running:
            return

        self.running = False

        if self.retry_task:
            self.retry_task.cancel()
            try:
                await self.retry_task
            except asyncio.CancelledError:
                pass

        logger.info("DLQ retry processor stopped")

    async def add_failed_event(
        self,
        event: Event,
        subscription_id: str,
        subscriber_agent: str,
        failure_reason: FailureReason,
        error_message: str,
    ) -> None:
        """
        Add a failed event to the DLQ.

        Args:
            event: Event that failed
            subscription_id: Subscription it failed for
            subscriber_agent: Agent that should have received it
            failure_reason: Why it failed
            error_message: Error details
        """
        failed_event = FailedEvent(
            event=event,
            subscription_id=subscription_id,
            subscriber_agent=subscriber_agent,
            failure_reason=failure_reason,
            error_message=error_message,
            max_retries=self.max_retries,
        )

        # Calculate initial retry time
        failed_event.next_retry_at = self._calculate_next_retry(failed_event)

        self.retry_queue.append(failed_event)
        self.total_failures += 1

        logger.warning(
            f"⚠️  Event added to DLQ: {event.event_type.value if hasattr(event.event_type, 'value') else event.event_type} "
            f"for {subscriber_agent} (reason: {failure_reason.value})"
        )

    async def retry_event(
        self, failed_event: FailedEvent, handler: Callable[[Event], None]
    ) -> bool:
        """
        Retry delivering an event.

        Args:
            failed_event: Failed event to retry
            handler: Handler function to call

        Returns:
            True if retry succeeded, False otherwise
        """
        self.total_retries += 1
        failed_event.retry_count += 1

        try:
            # Call handler
            if asyncio.iscoroutinefunction(handler):
                await handler(failed_event.event)
            else:
                handler(failed_event.event)

            # Success!
            self.successful_retries += 1
            logger.info(
                f"✅ Retry succeeded for {failed_event.subscriber_agent} "
                f"(attempt {failed_event.retry_count}/{failed_event.max_retries})"
            )
            return True

        except Exception as e:
            # Retry failed
            failed_event.last_error = str(e)
            logger.error(
                f"❌ Retry failed for {failed_event.subscriber_agent}: {e} "
                f"(attempt {failed_event.retry_count}/{failed_event.max_retries})"
            )

            # Check if we should retry again
            if failed_event.retry_count < failed_event.max_retries:
                # Schedule another retry
                failed_event.next_retry_at = self._calculate_next_retry(failed_event)
                return False
            else:
                # Max retries exceeded - move to dead letters
                self._move_to_dead_letters(failed_event)
                return False

    async def _process_retries(self) -> None:
        """
        Background task that processes retry queue.

        Checks for events ready to retry and attempts redelivery.
        """
        logger.info("DLQ retry processor running")

        while self.running:
            try:
                await asyncio.sleep(1)  # Check every second

                now = datetime.now(timezone.utc)
                ready_to_retry = []

                # Find events ready for retry
                for failed_event in self.retry_queue[:]:
                    if failed_event.next_retry_at:
                        next_retry = datetime.fromisoformat(failed_event.next_retry_at)
                        if now >= next_retry:
                            ready_to_retry.append(failed_event)

                # Note: In real implementation, we'd need access to the handler
                # For now, this is a placeholder that subclasses/integrations override
                for failed_event in ready_to_retry:
                    # Remove from retry queue temporarily
                    self.retry_queue.remove(failed_event)

                    # In practice, the EventBus would inject the handler here
                    # For testing, we'll just track the attempt
                    logger.debug(
                        f"Event ready for retry: {failed_event.event.event_id}"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in retry processor: {e}")

    def _calculate_next_retry(self, failed_event: FailedEvent) -> str:
        """
        Calculate next retry time using exponential backoff.

        Args:
            failed_event: Event to calculate backoff for

        Returns:
            ISO timestamp for next retry
        """
        # Exponential backoff: initial * (multiplier ^ retry_count)
        backoff = self.initial_backoff_seconds * (
            self.backoff_multiplier ** failed_event.retry_count
        )

        # Cap at max backoff
        backoff = min(backoff, self.max_backoff_seconds)

        next_retry = datetime.now(timezone.utc) + timedelta(seconds=backoff)

        logger.debug(
            f"Next retry in {backoff:.1f}s (attempt {failed_event.retry_count + 1})"
        )

        return next_retry.isoformat()

    def _move_to_dead_letters(self, failed_event: FailedEvent) -> None:
        """
        Move event to permanent dead letter storage.

        Args:
            failed_event: Event that exhausted retries
        """
        if failed_event in self.retry_queue:
            self.retry_queue.remove(failed_event)

        self.dead_letters.append(failed_event)
        self.permanent_failures += 1

        logger.error(
            f"💀 Event permanently failed after {failed_event.retry_count} retries: "
            f"{failed_event.event.event_id} for {failed_event.subscriber_agent}"
        )

    def get_retry_queue(self) -> List[FailedEvent]:
        """Get all events in retry queue"""
        return self.retry_queue.copy()

    def get_dead_letters(self) -> List[FailedEvent]:
        """Get all permanently failed events"""
        return self.dead_letters.copy()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get DLQ statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "retry_queue_size": len(self.retry_queue),
            "dead_letter_size": len(self.dead_letters),
            "total_failures": self.total_failures,
            "total_retries": self.total_retries,
            "successful_retries": self.successful_retries,
            "permanent_failures": self.permanent_failures,
            "retry_success_rate": (
                self.successful_retries / self.total_retries
                if self.total_retries > 0
                else 0.0
            ),
        }

    async def reprocess_dead_letter(
        self, event_id: str, handler: Callable[[Event], None]
    ) -> bool:
        """
        Manually reprocess a dead letter.

        Args:
            event_id: ID of event to reprocess
            handler: Handler to call

        Returns:
            True if reprocessing succeeded
        """
        # Find dead letter
        dead_letter = None
        for dl in self.dead_letters:
            if dl.event.event_id == event_id:
                dead_letter = dl
                break

        if not dead_letter:
            logger.warning(f"Dead letter not found: {event_id}")
            return False

        # Reset retry count
        dead_letter.retry_count = 0

        # Try to deliver
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(dead_letter.event)
            else:
                handler(dead_letter.event)

            # Success - remove from dead letters
            self.dead_letters.remove(dead_letter)
            logger.info(f"✅ Dead letter reprocessed successfully: {event_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Dead letter reprocessing failed: {e}")
            return False

    def clear_dead_letters(self) -> int:
        """
        Clear all dead letters.

        Returns:
            Number of dead letters cleared
        """
        count = len(self.dead_letters)
        self.dead_letters.clear()
        logger.info(f"Cleared {count} dead letters")
        return count

    def get_failed_events_by_reason(
        self, reason: FailureReason
    ) -> List[FailedEvent]:
        """
        Get failed events filtered by failure reason.

        Args:
            reason: Failure reason to filter by

        Returns:
            List of matching failed events
        """
        matching = []

        for failed_event in self.retry_queue + self.dead_letters:
            if failed_event.failure_reason == reason:
                matching.append(failed_event)

        return matching

    def get_failed_events_by_subscriber(
        self, subscriber_agent: str
    ) -> List[FailedEvent]:
        """
        Get failed events for a specific subscriber.

        Args:
            subscriber_agent: Agent DID to filter by

        Returns:
            List of matching failed events
        """
        matching = []

        for failed_event in self.retry_queue + self.dead_letters:
            if failed_event.subscriber_agent == subscriber_agent:
                matching.append(failed_event)

        return matching
