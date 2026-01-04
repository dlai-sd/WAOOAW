"""
Event Bus Template - Week 1-2 Implementation
Redis Pub/Sub wrapper for event-driven agent wake protocol
"""

import json
import logging
import redis
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Standard event types for agent wake triggers"""
    FILE_CREATED = "file.created"
    FILE_MODIFIED = "file.modified"
    FILE_DELETED = "file.deleted"
    PR_OPENED = "pull_request.opened"
    PR_SYNCHRONIZED = "pull_request.synchronized"
    PR_CLOSED = "pull_request.closed"
    ISSUE_OPENED = "issue.opened"
    ISSUE_COMMENTED = "issue.commented"
    COMMIT_PUSHED = "commit.pushed"
    SCHEDULED_WAKE = "scheduled.wake"
    THRESHOLD_BREACHED = "threshold.breached"
    AGENT_HANDOFF = "agent.handoff"
    HUMAN_ESCALATION = "human.escalation"


@dataclass
class Event:
    """Standard event structure for inter-agent communication"""
    event_id: str  # Unique identifier
    event_type: EventType  # Type of event
    timestamp: datetime  # When event occurred
    source: str  # Who triggered (github, agent, scheduler)
    
    # Payload
    payload: Dict[str, Any]  # Event-specific data
    
    # Metadata
    repository: Optional[str] = None
    branch: Optional[str] = None
    file_path: Optional[str] = None
    phase: Optional[str] = None  # phase1, phase2, phase3
    priority: str = "normal"  # urgent, normal, low
    
    # Correlation
    correlation_id: Optional[str] = None  # Link related events
    parent_event_id: Optional[str] = None  # Chain of events
    
    def to_json(self) -> str:
        """Serialize event to JSON"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return json.dumps(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Deserialize event from JSON"""
        data = json.loads(json_str)
        data['event_type'] = EventType(data['event_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class EventBus:
    """
    Redis-based pub/sub event bus for agent wake protocol.
    
    Agents subscribe to specific event patterns and wake when events match.
    Supports:
    - Topic-based subscriptions (pattern matching)
    - Event filtering (deterministic wake decisions)
    - Event replay (missed events while agent sleeping)
    - Dead letter queue (failed event processing)
    """
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        """Initialize event bus connection"""
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        self.subscribers: Dict[str, List[Callable]] = {}
        
        logger.info(f"✅ EventBus connected to Redis at {redis_host}:{redis_port}")
    
    def publish(self, event: Event) -> int:
        """
        Publish event to bus.
        
        Args:
            event: Event to publish
            
        Returns:
            Number of subscribers that received the event
        """
        # Construct channel name from event type
        channel = f"events.{event.event_type.value}"
        
        # Serialize event
        message = event.to_json()
        
        # Publish to Redis
        num_subscribers = self.redis_client.publish(channel, message)
        
        # Log event
        logger.info(
            f"📢 Published {event.event_type.value} to {channel} "
            f"({num_subscribers} subscribers)"
        )
        
        # Store in event log for replay
        self._store_event_log(event)
        
        return num_subscribers
    
    def subscribe(self, event_pattern: str, callback: Callable[[Event], None]):
        """
        Subscribe to events matching pattern.
        
        Args:
            event_pattern: Pattern like "file.*", "pull_request.*", or specific "file.created"
            callback: Function to call when event matches
        """
        channel = f"events.{event_pattern}"
        
        # Add to local registry
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)
        
        # Subscribe to Redis channel
        if event_pattern.endswith('*'):
            # Pattern subscription
            self.pubsub.psubscribe(**{channel: self._handle_message})
        else:
            # Exact subscription
            self.pubsub.subscribe(**{channel: self._handle_message})
        
        logger.info(f"✅ Subscribed to {channel}")
    
    def _handle_message(self, message):
        """Internal: Handle incoming message from Redis"""
        if message['type'] not in ['message', 'pmessage']:
            return  # Ignore subscription confirmations
        
        try:
            # Parse event
            event = Event.from_json(message['data'])
            
            # Find matching callbacks
            channel = message['channel']
            callbacks = self.subscribers.get(channel, [])
            
            # Execute callbacks
            for callback in callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Callback failed for {event.event_id}: {e}")
                    self._send_to_dlq(event, str(e))
        
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")
    
    def start_listening(self):
        """
        Start listening for events (blocking).
        
        This runs in a separate thread for each agent.
        """
        logger.info("👂 EventBus listening for events...")
        for message in self.pubsub.listen():
            self._handle_message(message)
    
    def stop_listening(self):
        """Stop listening and close connections"""
        self.pubsub.unsubscribe()
        self.pubsub.close()
        logger.info("🛑 EventBus stopped listening")
    
    def _store_event_log(self, event: Event):
        """Store event in Redis for replay (7 day TTL)"""
        key = f"event_log:{event.event_id}"
        self.redis_client.setex(
            key,
            7 * 24 * 3600,  # 7 days
            event.to_json()
        )
    
    def get_events_since(self, timestamp: datetime, event_type: Optional[EventType] = None) -> List[Event]:
        """
        Retrieve events since timestamp (for replay).
        
        Args:
            timestamp: Get events after this time
            event_type: Filter by event type (optional)
            
        Returns:
            List of events
        """
        # Scan for event logs
        cursor = 0
        events = []
        
        while True:
            cursor, keys = self.redis_client.scan(cursor, match="event_log:*", count=100)
            
            for key in keys:
                event_json = self.redis_client.get(key)
                if event_json:
                    event = Event.from_json(event_json)
                    
                    # Filter by timestamp
                    if event.timestamp <= timestamp:
                        continue
                    
                    # Filter by type
                    if event_type and event.event_type != event_type:
                        continue
                    
                    events.append(event)
            
            if cursor == 0:
                break
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        return events
    
    def _send_to_dlq(self, event: Event, error: str):
        """Send failed event to dead letter queue"""
        dlq_key = f"dlq:{event.event_id}"
        dlq_data = {
            'event': event.to_json(),
            'error': error,
            'failed_at': datetime.now().isoformat()
        }
        self.redis_client.setex(dlq_key, 24 * 3600, json.dumps(dlq_data))
        logger.warning(f"💀 Sent event {event.event_id} to DLQ: {error}")


# ============================================
# USAGE EXAMPLES
# ============================================

def example_usage():
    """Example: How agents use EventBus"""
    
    # Initialize event bus
    event_bus = EventBus(redis_host="localhost", redis_port=6379)
    
    # Example 1: Agent subscribes to file events
    def on_file_created(event: Event):
        """WowVision Prime wakes on file.created"""
        print(f"🌅 WowVision waking for: {event.payload.get('file_path')}")
        # Agent's should_wake() logic here
    
    event_bus.subscribe("file.created", on_file_created)
    event_bus.subscribe("file.modified", on_file_created)
    
    # Example 2: GitHub webhook publishes event
    def simulate_github_webhook():
        event = Event(
            event_id="evt_12345",
            event_type=EventType.FILE_CREATED,
            timestamp=datetime.now(),
            source="github",
            payload={
                "file_path": "docs/README.md",
                "author": "user123",
                "commit_sha": "abc123"
            },
            repository="WAOOAW",
            branch="main",
            file_path="docs/README.md",
            phase="phase1"
        )
        event_bus.publish(event)
    
    # Example 3: Scheduled wake
    def simulate_scheduled_wake():
        event = Event(
            event_id="evt_scheduled_001",
            event_type=EventType.SCHEDULED_WAKE,
            timestamp=datetime.now(),
            source="scheduler",
            payload={
                "agent_id": "wowvision_prime",
                "schedule": "0 9 * * *"  # Daily at 9am
            },
            priority="normal"
        )
        event_bus.publish(event)
    
    # Start listening (in production, this runs in background thread)
    # event_bus.start_listening()


# ============================================
# INTEGRATION WITH BASE AGENT
# ============================================

"""
Add to waooaw/agents/base_agent.py:

class WAAOOWAgent:
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        # ... existing init code ...
        
        # Event bus integration
        self.event_bus = EventBus(
            redis_host=config.get('redis_host', 'localhost'),
            redis_port=config.get('redis_port', 6379)
        )
        
        # Subscribe to relevant events
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        '''Subscribe to events based on agent specialization'''
        for event_pattern in self.wake_events:
            self.event_bus.subscribe(event_pattern, self._on_event_received)
    
    def _on_event_received(self, event: Event):
        '''Handle incoming event'''
        # Check if agent should wake
        if self.should_wake(event):
            # Wake up and process
            self.wake_up()
            self.execute_task(event.payload)
    
    def should_wake(self, event: Event) -> bool:
        '''Deterministic wake decision (IMPLEMENT IN WEEK 1-2)'''
        # Check event type
        if event.event_type.value not in self.wake_events:
            return False
        
        # Check file pattern (if file event)
        if event.file_path and not self._matches_file_pattern(event.file_path):
            return False
        
        # Check phase
        if event.phase and event.phase not in self.scope.phases:
            return False
        
        # Check constraints
        if self.specialization.is_constrained(event.payload.get('action', '')):
            return False
        
        return True
"""


if __name__ == "__main__":
    example_usage()
