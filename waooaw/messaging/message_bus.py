"""
Message Bus - Redis Streams based event-driven communication

This module provides the message bus infrastructure for agent-to-agent
communication and event-driven wake-up. Uses Redis Streams for:
- Pub/sub messaging with persistence
- Consumer groups for load balancing
- Priority queues (P1=high, P2=normal, P3=low)
- HMAC signature validation via SecurityLayer

Architecture:
- Topics: agent.{agent_name}.{event_type} (e.g., agent.wowvision.task.validate)
- Consumer Groups: cg_{agent_name} (e.g., cg_wowvision)
- Instances: {agent_name}_{instance_id} (e.g., wowvision_001)

Usage:
    bus = MessageBus(redis_url="redis://localhost:6379")
    
    # Publish
    bus.publish("agent.wowvision.task.validate", {"file": "test.md"}, priority=1)
    
    # Subscribe
    bus.subscribe(
        topics=["agent.wowvision.*"],
        consumer_group="cg_wowvision",
        consumer_name="wowvision_001",
        handler=process_message
    )
"""

import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import redis
from redis.exceptions import ResponseError

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Message structure for message bus"""
    
    message_id: str  # Redis stream ID
    topic: str  # Topic/stream name
    event_type: str  # Event type (file_created, pr_opened, etc.)
    payload: Dict[str, Any]  # Message payload
    priority: int  # 1=high, 2=normal, 3=low
    from_agent: str  # Sender agent ID
    to_agents: List[str]  # Target agent IDs (["*"] for broadcast)
    correlation_id: Optional[str] = None  # For request-response
    reply_to: Optional[str] = None  # Reply topic
    timestamp: Optional[str] = None  # ISO 8601 timestamp
    signature: Optional[str] = None  # HMAC signature
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis"""
        data = asdict(self)
        # Convert lists to JSON strings for Redis
        data['payload'] = json.dumps(data['payload'])
        data['to_agents'] = json.dumps(data['to_agents'])
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], message_id: str) -> 'Message':
        """Create from Redis dictionary"""
        # Parse JSON strings
        if isinstance(data.get('payload'), str):
            data['payload'] = json.loads(data['payload'])
        if isinstance(data.get('to_agents'), str):
            data['to_agents'] = json.loads(data['to_agents'])
        
        # Add message_id from Redis
        data['message_id'] = message_id
        
        return cls(**data)


class MessageBus:
    """
    Redis Streams-based message bus for agent communication.
    
    Features:
    - Event-driven wake-up (agents subscribe to relevant topics)
    - Consumer groups (load balancing across instances)
    - Priority queues (3 streams: P1, P2, P3)
    - HMAC signatures (via SecurityLayer)
    - Persistence (messages stored in Redis)
    - Acknowledgment (prevents duplicate processing)
    """
    
    # Priority stream names
    STREAM_P1 = "waooaw:messages:p1"  # High priority
    STREAM_P2 = "waooaw:messages:p2"  # Normal priority
    STREAM_P3 = "waooaw:messages:p3"  # Low priority
    
    # Consumer group prefix
    CONSUMER_GROUP_PREFIX = "cg_"
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        security_layer: Optional[Any] = None
    ):
        """
        Initialize message bus.
        
        Args:
            redis_url: Redis connection URL
            security_layer: SecurityLayer instance for HMAC signatures
        """
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=50
        )
        self.security_layer = security_layer
        
        # Create priority streams if they don't exist
        self._ensure_streams_exist()
        
        logger.info(f"MessageBus initialized with Redis: {redis_url}")
    
    def _ensure_streams_exist(self) -> None:
        """Create priority streams if they don't exist"""
        for stream in [self.STREAM_P1, self.STREAM_P2, self.STREAM_P3]:
            try:
                # XGROUP CREATE creates stream if it doesn't exist
                self.redis_client.xgroup_create(
                    stream,
                    "init",  # Temporary group
                    id='0',
                    mkstream=True
                )
                # Destroy temporary group
                self.redis_client.xgroup_destroy(stream, "init")
                logger.debug(f"Stream created: {stream}")
            except ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    logger.debug(f"Stream already exists: {stream}")
    
    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        priority: int = 2,
        event_type: str = "task",
        from_agent: str = "system",
        to_agents: List[str] = None,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> str:
        """
        Publish message to message bus.
        
        Args:
            topic: Topic name (e.g., "agent.wowvision.task.validate")
            payload: Message payload (dict)
            priority: 1=high, 2=normal, 3=low
            event_type: Event type (task, event, response, etc.)
            from_agent: Sender agent ID
            to_agents: Target agent IDs (["*"] for broadcast)
            correlation_id: For request-response patterns
            reply_to: Reply topic
            
        Returns:
            message_id: Redis stream message ID
        """
        if to_agents is None:
            to_agents = ["*"]  # Broadcast by default
        
        # Select stream based on priority
        stream = {
            1: self.STREAM_P1,
            2: self.STREAM_P2,
            3: self.STREAM_P3
        }.get(priority, self.STREAM_P2)
        
        # Create message
        message = Message(
            message_id="",  # Will be set by Redis
            topic=topic,
            event_type=event_type,
            payload=payload,
            priority=priority,
            from_agent=from_agent,
            to_agents=to_agents,
            correlation_id=correlation_id,
            reply_to=reply_to,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )
        
        # Add HMAC signature if SecurityLayer available
        if self.security_layer:
            message.signature = self.security_layer.sign_message(message.to_dict())
        
        # Publish to Redis Stream
        message_dict = message.to_dict()
        message_id = self.redis_client.xadd(stream, message_dict)
        
        logger.info(
            f"Message published: topic={topic}, priority={priority}, "
            f"stream={stream}, message_id={message_id}"
        )
        
        return message_id
    
    def subscribe(
        self,
        topics: List[str],
        consumer_group: str,
        consumer_name: str,
        handler: Callable[[Message], None],
        block_ms: int = 5000,
        count: int = 10
    ) -> None:
        """
        Subscribe to topics and process messages.
        
        This is a blocking call that continuously reads from streams.
        Run in separate thread or process.
        
        Args:
            topics: List of topic patterns (e.g., ["agent.wowvision.*"])
            consumer_group: Consumer group name (e.g., "cg_wowvision")
            consumer_name: Consumer instance name (e.g., "wowvision_001")
            handler: Callback function to process messages
            block_ms: Block timeout in milliseconds
            count: Max messages per read
        """
        # Ensure consumer groups exist
        self._ensure_consumer_groups(consumer_group)
        
        logger.info(
            f"Subscribing: topics={topics}, group={consumer_group}, "
            f"consumer={consumer_name}"
        )
        
        # Read from all priority streams
        streams = {
            self.STREAM_P1: '>',
            self.STREAM_P2: '>',
            self.STREAM_P3: '>'
        }
        
        while True:
            try:
                # Read from streams (priority order: P1 → P2 → P3)
                messages = self.redis_client.xreadgroup(
                    groupname=consumer_group,
                    consumername=consumer_name,
                    streams=streams,
                    count=count,
                    block=block_ms
                )
                
                if not messages:
                    continue
                
                # Process messages
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        try:
                            # Parse message
                            message = Message.from_dict(message_data, message_id)
                            
                            # Verify HMAC signature
                            if self.security_layer and message.signature:
                                if not self._verify_signature(message):
                                    logger.warning(
                                        f"Invalid signature: message_id={message_id}"
                                    )
                                    continue
                            
                            # Filter by topic
                            if self._matches_topics(message.topic, topics):
                                # Process message
                                handler(message)
                                
                                # Acknowledge message
                                self.acknowledge(
                                    stream_name,
                                    consumer_group,
                                    message_id
                                )
                        
                        except Exception as e:
                            logger.error(
                                f"Error processing message {message_id}: {e}",
                                exc_info=True
                            )
                            # Don't acknowledge failed messages
            
            except Exception as e:
                logger.error(f"Error in subscribe loop: {e}", exc_info=True)
                time.sleep(1)  # Backoff before retry
    
    def acknowledge(
        self,
        stream: str,
        consumer_group: str,
        message_id: str
    ) -> None:
        """
        Acknowledge message processing.
        
        Args:
            stream: Stream name
            consumer_group: Consumer group name
            message_id: Message ID to acknowledge
        """
        try:
            self.redis_client.xack(stream, consumer_group, message_id)
            logger.debug(f"Message acknowledged: {message_id}")
        except Exception as e:
            logger.error(f"Error acknowledging message {message_id}: {e}")
    
    def _ensure_consumer_groups(self, consumer_group: str) -> None:
        """Create consumer groups for all streams"""
        for stream in [self.STREAM_P1, self.STREAM_P2, self.STREAM_P3]:
            try:
                self.redis_client.xgroup_create(
                    stream,
                    consumer_group,
                    id='0',
                    mkstream=True
                )
                logger.debug(f"Consumer group created: {consumer_group} on {stream}")
            except ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.debug(f"Consumer group exists: {consumer_group} on {stream}")
                else:
                    raise
    
    def _verify_signature(self, message: Message) -> bool:
        """Verify HMAC signature"""
        if not self.security_layer:
            return True
        
        message_dict = message.to_dict()
        signature = message_dict.pop('signature', None)
        
        return self.security_layer.verify_signature(message_dict, signature)
    
    def _matches_topics(self, message_topic: str, subscribed_topics: List[str]) -> bool:
        """
        Check if message topic matches subscribed topics.
        
        Supports wildcards:
        - "agent.wowvision.*" matches "agent.wowvision.task.validate"
        - "agent.*" matches all agent topics
        """
        for pattern in subscribed_topics:
            # Simple wildcard matching (can be enhanced)
            if pattern == "*":
                return True
            
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if message_topic.startswith(prefix):
                    return True
            elif pattern == message_topic:
                return True
        
        return False
    
    def get_pending_messages(
        self,
        consumer_group: str,
        consumer_name: str,
        min_idle_ms: int = 60000
    ) -> List[Message]:
        """
        Get pending messages (not acknowledged) for consumer.
        
        Useful for recovering from failures.
        
        Args:
            consumer_group: Consumer group name
            consumer_name: Consumer instance name
            min_idle_ms: Minimum idle time in milliseconds
            
        Returns:
            List of pending messages
        """
        pending = []
        
        for stream in [self.STREAM_P1, self.STREAM_P2, self.STREAM_P3]:
            try:
                # Get pending messages
                result = self.redis_client.xpending_range(
                    stream,
                    consumer_group,
                    min='-',
                    max='+',
                    count=100,
                    consumername=consumer_name
                )
                
                for item in result:
                    message_id = item['message_id']
                    idle_ms = item['time_since_delivered']
                    
                    if idle_ms >= min_idle_ms:
                        # Fetch message content
                        messages = self.redis_client.xrange(
                            stream,
                            min=message_id,
                            max=message_id,
                            count=1
                        )
                        
                        if messages:
                            msg_id, msg_data = messages[0]
                            message = Message.from_dict(msg_data, msg_id)
                            pending.append(message)
            
            except Exception as e:
                logger.error(f"Error getting pending messages from {stream}: {e}")
        
        return pending
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check message bus health.
        
        Returns:
            Health status dict
        """
        try:
            # Ping Redis
            self.redis_client.ping()
            
            # Get stream lengths
            stream_lengths = {}
            for stream in [self.STREAM_P1, self.STREAM_P2, self.STREAM_P3]:
                length = self.redis_client.xlen(stream)
                stream_lengths[stream] = length
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "stream_lengths": stream_lengths
            }
        
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "error": str(e)
            }
    
    def close(self) -> None:
        """Close Redis connection"""
        self.redis_client.close()
        logger.info("MessageBus closed")
