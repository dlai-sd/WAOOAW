"""
Message Bus Implementation using Redis Streams

Core message bus for WAOOAW agent communication.
Based on MESSAGE_BUS_ARCHITECTURE.md v1.1
"""
import json
import logging
import hashlib
import hmac
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

import redis
from redis.exceptions import RedisError, ResponseError

from .models import Message, MessagePayload, MessageRouting, MessageMetadata, AuditInfo


logger = logging.getLogger(__name__)


class MessageBus:
    """
    Redis Streams-based message bus for agent communication.
    
    Features:
    - At-least-once delivery with consumer groups
    - Priority-based routing (5 streams for priorities 1-5)
    - HMAC signature verification
    - Message persistence and replay
    - Dead letter queue for failed messages
    
    Architecture:
    - waooaw:messages:p{1-5} - Priority streams
    - waooaw:topics:{topic} - Topic-based routing
    - waooaw:broadcast - Broadcast to all agents
    - waooaw:dlq - Dead letter queue
    """
    
    def __init__(
        self,
        redis_url: str,
        secret_key: Optional[str] = None,
        max_len: int = 10_000_000,  # 10M messages
        block_time: int = 5000,  # 5 seconds
    ):
        """
        Initialize Message Bus.
        
        Args:
            redis_url: Redis connection URL
            secret_key: Secret key for HMAC signatures (optional)
            max_len: Maximum messages per stream (auto-trim)
            block_time: Block time for XREAD in milliseconds
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.secret_key = secret_key
        self.max_len = max_len
        self.block_time = block_time
        
        # Stream name patterns
        self.PRIORITY_STREAM_PREFIX = "waooaw:messages:p"
        self.TOPIC_STREAM_PREFIX = "waooaw:topics:"
        self.BROADCAST_STREAM = "waooaw:broadcast"
        self.DLQ_STREAM = "waooaw:dlq"
        
        logger.info(f"MessageBus initialized: redis_url={redis_url}, max_len={max_len}")
    
    def _get_priority_stream(self, priority: int) -> str:
        """Get stream name for priority level."""
        return f"{self.PRIORITY_STREAM_PREFIX}{priority}"
    
    def _get_topic_stream(self, topic: str) -> str:
        """Get stream name for topic."""
        return f"{self.TOPIC_STREAM_PREFIX}{topic}"
    
    def _compute_signature(self, message: Message) -> str:
        """
        Compute HMAC-SHA256 signature for message authentication.
        
        Args:
            message: Message to sign
            
        Returns:
            Hex-encoded signature (64 characters)
        """
        if not self.secret_key:
            return ""
        
        # Create canonical representation
        canonical = json.dumps({
            "routing": message.routing.model_dump(),
            "payload": message.payload.model_dump(),
            "metadata": {
                "message_id": message.metadata.message_id,
                "timestamp": message.metadata.timestamp,
            }
        }, sort_keys=True)
        
        # Compute HMAC
        signature = hmac.new(
            self.secret_key.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _verify_signature(self, message: Message) -> bool:
        """
        Verify message signature.
        
        Args:
            message: Message to verify
            
        Returns:
            True if signature is valid or not required
        """
        if not self.secret_key:
            return True  # Signature not required
        
        if not message.metadata.signature:
            logger.warning(f"Message {message.metadata.message_id} has no signature")
            return False
        
        expected_signature = self._compute_signature(message)
        return hmac.compare_digest(expected_signature, message.metadata.signature)
    
    def publish(
        self,
        message: Message,
        use_topic_routing: bool = False,
    ) -> str:
        """
        Publish message to message bus.
        
        Args:
            message: Message to publish
            use_topic_routing: Use topic-based routing instead of priority
            
        Returns:
            Stream message ID (timestamp-sequence)
            
        Raises:
            RedisError: If publish fails
            ValueError: If message validation fails
        """
        try:
            # Sign message if secret key configured
            if self.secret_key and not message.metadata.signature:
                message.metadata.signature = self._compute_signature(message)
            
            # Serialize message
            message_data = {
                "routing": json.dumps(message.routing.model_dump()),
                "payload": json.dumps(message.payload.model_dump()),
                "metadata": json.dumps(message.metadata.model_dump()),
                "audit": json.dumps(message.audit.model_dump() if message.audit else {}),
            }
            
            # Determine target stream
            if message.routing.to_agents == ["*"]:
                # Broadcast
                stream = self.BROADCAST_STREAM
            elif use_topic_routing:
                # Topic-based routing
                stream = self._get_topic_stream(message.routing.topic)
            else:
                # Priority-based routing
                stream = self._get_priority_stream(message.payload.priority)
            
            # Publish to Redis Stream
            message_id = self.redis_client.xadd(
                stream,
                message_data,
                maxlen=self.max_len,
                approximate=True  # Allow Redis to trim efficiently
            )
            
            logger.info(
                f"Published message {message.metadata.message_id} to {stream} "
                f"(stream_id={message_id}, priority={message.payload.priority})"
            )
            
            return message_id
            
        except RedisError as e:
            logger.error(f"Failed to publish message: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error publishing message: {e}")
            raise
    
    def subscribe(
        self,
        consumer_group: str,
        consumer_name: str,
        streams: Optional[List[str]] = None,
        count: int = 10,
    ) -> List[Message]:
        """
        Subscribe to message streams and consume messages.
        
        Args:
            consumer_group: Consumer group name (e.g., "cg_wowvision")
            consumer_name: Consumer instance name (e.g., "wowvision_001")
            streams: List of streams to subscribe (None = all priority streams)
            count: Maximum messages to fetch per call
            
        Returns:
            List of messages (may be empty if no new messages)
            
        Raises:
            RedisError: If subscription fails
        """
        try:
            # Default to all priority streams + broadcast
            if streams is None:
                streams = [
                    self._get_priority_stream(5),  # Critical first
                    self._get_priority_stream(4),
                    self._get_priority_stream(3),
                    self._get_priority_stream(2),
                    self._get_priority_stream(1),
                    self.BROADCAST_STREAM,
                ]
            
            # Create consumer groups if they don't exist
            for stream in streams:
                try:
                    self.redis_client.xgroup_create(
                        stream,
                        consumer_group,
                        id="0",  # Read from beginning
                        mkstream=True  # Create stream if doesn't exist
                    )
                except ResponseError as e:
                    if "BUSYGROUP" not in str(e):
                        raise
            
            # Read from streams (blocking)
            stream_dict = {stream: ">" for stream in streams}  # ">" = new messages only
            
            response = self.redis_client.xreadgroup(
                consumer_group,
                consumer_name,
                stream_dict,
                count=count,
                block=self.block_time
            )
            
            # Parse messages
            messages = []
            for stream, stream_messages in response:
                for message_id, message_data in stream_messages:
                    try:
                        # Deserialize
                        routing = MessageRouting(**json.loads(message_data["routing"]))
                        payload = MessagePayload(**json.loads(message_data["payload"]))
                        metadata = MessageMetadata(**json.loads(message_data["metadata"]))
                        audit_data = json.loads(message_data.get("audit", "{}"))
                        audit = AuditInfo(**audit_data) if audit_data else None
                        
                        message = Message(
                            routing=routing,
                            payload=payload,
                            metadata=metadata,
                            audit=audit
                        )
                        
                        # Verify signature
                        if not self._verify_signature(message):
                            logger.error(f"Invalid signature for message {metadata.message_id}")
                            # Move to DLQ
                            self._move_to_dlq(stream, message_id, message_data, "invalid_signature")
                            continue
                        
                        # Store stream_id for acknowledgment
                        message.metadata.tags.append(f"stream_id:{stream}:{message_id}")
                        
                        messages.append(message)
                        
                    except Exception as e:
                        logger.error(f"Failed to parse message {message_id}: {e}")
                        self._move_to_dlq(stream, message_id, message_data, str(e))
            
            logger.debug(f"Consumed {len(messages)} messages for {consumer_group}/{consumer_name}")
            return messages
            
        except RedisError as e:
            logger.error(f"Failed to subscribe to streams: {e}")
            raise
    
    def acknowledge(self, message: Message) -> bool:
        """
        Acknowledge message processing completion.
        
        Args:
            message: Message to acknowledge
            
        Returns:
            True if acknowledgment succeeded
        """
        try:
            # Extract stream and message_id from tags
            stream_tag = next(
                (tag for tag in message.metadata.tags if tag.startswith("stream_id:")),
                None
            )
            
            if not stream_tag:
                logger.error(f"No stream_id tag found for message {message.metadata.message_id}")
                return False
            
            # Parse stream_id tag: "stream_id:{stream}:{message_id}"
            _, stream, message_id = stream_tag.split(":", 2)
            
            # Determine consumer group from to_agents
            consumer_group = f"cg_{message.routing.to_agents[0].replace('-', '_')}"
            
            # Acknowledge message
            ack_count = self.redis_client.xack(stream, consumer_group, message_id)
            
            if ack_count > 0:
                logger.debug(
                    f"Acknowledged message {message.metadata.message_id} "
                    f"(stream={stream}, id={message_id})"
                )
                return True
            else:
                logger.warning(
                    f"Failed to acknowledge message {message.metadata.message_id} "
                    f"(already acked or doesn't exist)"
                )
                return False
                
        except Exception as e:
            logger.error(f"Failed to acknowledge message: {e}")
            return False
    
    def _move_to_dlq(
        self,
        original_stream: str,
        message_id: str,
        message_data: Dict[str, Any],
        error: str
    ):
        """Move failed message to dead letter queue."""
        try:
            dlq_data = {
                **message_data,
                "original_stream": original_stream,
                "original_message_id": message_id,
                "error": error,
                "dlq_timestamp": datetime.utcnow().isoformat()
            }
            
            self.redis_client.xadd(self.DLQ_STREAM, dlq_data, maxlen=100_000)
            logger.warning(f"Moved message {message_id} to DLQ: {error}")
            
        except Exception as e:
            logger.error(f"Failed to move message to DLQ: {e}")
    
    def get_pending_count(self, consumer_group: str, stream: str) -> int:
        """
        Get count of pending (unacknowledged) messages.
        
        Args:
            consumer_group: Consumer group name
            stream: Stream name
            
        Returns:
            Number of pending messages
        """
        try:
            pending_info = self.redis_client.xpending(stream, consumer_group)
            return pending_info["pending"]
        except Exception as e:
            logger.error(f"Failed to get pending count: {e}")
            return 0
    
    def close(self):
        """Close Redis connection."""
        try:
            self.redis_client.close()
            logger.info("MessageBus connection closed")
        except Exception as e:
            logger.error(f"Error closing MessageBus: {e}")
