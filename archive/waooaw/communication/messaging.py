"""
Message Bus - Direct Agent-to-Agent Communication

Provides point-to-point messaging with:
- Direct send/receive between agents
- Async message delivery with retries
- Message acknowledgments
- Delivery receipts
- Message prioritization
- TTL (time-to-live) for messages
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import redis.asyncio as redis


class MessageType(str, Enum):
    """Message type classification."""
    COMMAND = "command"  # Execute action
    QUERY = "query"  # Request information
    EVENT = "event"  # Notify of state change
    RESPONSE = "response"  # Reply to request
    ACK = "ack"  # Acknowledgment


class MessagePriority(str, Enum):
    """Message priority for delivery ordering."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(str, Enum):
    """Message delivery status."""
    PENDING = "pending"  # Not yet delivered
    SENT = "sent"  # Transmitted to recipient
    DELIVERED = "delivered"  # Received by recipient
    FAILED = "failed"  # Delivery failed
    EXPIRED = "expired"  # TTL exceeded


@dataclass
class Message:
    """Direct message between agents."""
    
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str = ""
    to_agent: str = ""
    message_type: MessageType = MessageType.COMMAND
    priority: MessagePriority = MessagePriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None  # For request-response pairing
    reply_to: Optional[str] = None  # Agent to send reply to
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    ttl_seconds: int = 300  # Time to live (5 minutes default)
    status: MessageStatus = MessageStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "message_id": self.message_id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp,
            "ttl_seconds": self.ttl_seconds,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return Message(
            message_id=data["message_id"],
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            message_type=MessageType(data["message_type"]),
            priority=MessagePriority(data["priority"]),
            payload=data["payload"],
            correlation_id=data.get("correlation_id"),
            reply_to=data.get("reply_to"),
            timestamp=data["timestamp"],
            ttl_seconds=data["ttl_seconds"],
            status=MessageStatus(data["status"]),
            retry_count=data["retry_count"],
            max_retries=data["max_retries"],
        )
    
    def is_expired(self) -> bool:
        """Check if message has exceeded TTL."""
        sent_time = datetime.fromisoformat(self.timestamp)
        expiry = sent_time + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry
    
    def should_retry(self) -> bool:
        """Check if message should be retried."""
        return (
            self.status == MessageStatus.FAILED
            and self.retry_count < self.max_retries
            and not self.is_expired()
        )


@dataclass
class DeliveryReceipt:
    """Receipt confirming message delivery."""
    
    message_id: str
    to_agent: str
    delivered_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: MessageStatus = MessageStatus.DELIVERED
    error: Optional[str] = None


class MessageBus:
    """
    Direct agent-to-agent message bus.
    
    Uses Redis for message queuing and delivery tracking.
    Each agent has a dedicated inbox (Redis list) for receiving messages.
    """
    
    def __init__(self, redis_client: redis.Redis):
        """
        Initialize message bus.
        
        Args:
            redis_client: Redis client for message storage and delivery
        """
        self.redis = redis_client
        self.agent_id: Optional[str] = None
        self.handlers: Dict[MessageType, List[Callable]] = {
            msg_type: [] for msg_type in MessageType
        }
        self.running = False
        self._delivery_task: Optional[asyncio.Task] = None
        self._active_subscriptions: Set[str] = set()
    
    async def start(self, agent_id: str):
        """
        Start message bus for an agent.
        
        Args:
            agent_id: Unique identifier for this agent
        """
        self.agent_id = agent_id
        self.running = True
        
        # Start delivery loop
        self._delivery_task = asyncio.create_task(self._delivery_loop())
    
    async def stop(self):
        """Stop message bus and cleanup."""
        self.running = False
        
        if self._delivery_task:
            self._delivery_task.cancel()
            try:
                await self._delivery_task
            except asyncio.CancelledError:
                pass
        
        self._active_subscriptions.clear()
    
    async def send_message(
        self,
        to_agent: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_seconds: int = 300,
        correlation_id: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> Message:
        """
        Send message to another agent.
        
        Args:
            to_agent: Recipient agent ID
            message_type: Type of message
            payload: Message payload
            priority: Message priority
            ttl_seconds: Time to live
            correlation_id: For request-response pairing
            reply_to: Agent to send reply to (default: sender)
            
        Returns:
            Message object with unique message_id
        """
        if not self.agent_id:
            raise RuntimeError("MessageBus not started. Call start() first.")
        
        message = Message(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            priority=priority,
            payload=payload,
            ttl_seconds=ttl_seconds,
            correlation_id=correlation_id,
            reply_to=reply_to or self.agent_id,
        )
        
        # Add to recipient's inbox (Redis list)
        inbox_key = f"agent:inbox:{to_agent}"
        
        # Use LPUSH for FIFO (right pop) or ZADD for priority queue
        if priority in (MessagePriority.URGENT, MessagePriority.HIGH):
            # High priority: add to front of queue
            await self.redis.lpush(inbox_key, self._serialize_message(message))
        else:
            # Normal/low priority: add to back of queue
            await self.redis.rpush(inbox_key, self._serialize_message(message))
        
        message.status = MessageStatus.SENT
        
        # Store message for tracking
        await self._store_message(message)
        
        return message
    
    async def receive_messages(self, timeout: int = 1) -> List[Message]:
        """
        Receive messages from this agent's inbox.
        
        Args:
            timeout: Timeout in seconds for blocking pop
            
        Returns:
            List of received messages
        """
        if not self.agent_id:
            raise RuntimeError("MessageBus not started. Call start() first.")
        
        inbox_key = f"agent:inbox:{self.agent_id}"
        messages: List[Message] = []
        
        # Try to receive multiple messages (batch processing)
        for _ in range(10):  # Max 10 messages per call
            result = await self.redis.rpop(inbox_key)
            if not result:
                break
            
            try:
                message = self._deserialize_message(result)
                
                # Check TTL
                if message.is_expired():
                    message.status = MessageStatus.EXPIRED
                    await self._store_message(message)
                    continue
                
                message.status = MessageStatus.DELIVERED
                await self._store_message(message)
                messages.append(message)
                
                # Send delivery receipt
                await self._send_receipt(message)
                
            except Exception as e:
                print(f"Error deserializing message: {e}")
                continue
        
        return messages
    
    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[Message], None],
    ):
        """
        Register handler for message type.
        
        Args:
            message_type: Type of message to handle
            handler: Async function to handle message
        """
        self.handlers[message_type].append(handler)
    
    async def _delivery_loop(self):
        """Continuously check inbox and deliver messages to handlers."""
        while self.running:
            try:
                messages = await self.receive_messages(timeout=1)
                
                for message in messages:
                    # Call registered handlers
                    handlers = self.handlers.get(message.message_type, [])
                    for handler in handlers:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(message)
                            else:
                                handler(message)
                        except Exception as e:
                            print(f"Handler error for message {message.message_id}: {e}")
                
                if not messages:
                    # No messages, wait a bit
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Delivery loop error: {e}")
                await asyncio.sleep(1)
    
    async def _store_message(self, message: Message):
        """Store message for tracking and audit."""
        key = f"message:{message.message_id}"
        await self.redis.hset(key, mapping=message.to_dict())
        await self.redis.expire(key, message.ttl_seconds * 2)  # 2x TTL for audit
    
    async def _send_receipt(self, message: Message):
        """Send delivery receipt to sender."""
        receipt = DeliveryReceipt(
            message_id=message.message_id,
            to_agent=message.to_agent,
            status=MessageStatus.DELIVERED,
        )
        
        # Store receipt
        receipt_key = f"receipt:{message.message_id}"
        await self.redis.hset(receipt_key, mapping={
            "message_id": receipt.message_id,
            "to_agent": receipt.to_agent,
            "delivered_at": receipt.delivered_at,
            "status": receipt.status.value,
        })
        await self.redis.expire(receipt_key, 3600)  # 1 hour
    
    async def get_message_status(self, message_id: str) -> Optional[Message]:
        """
        Get status of sent message.
        
        Args:
            message_id: Message ID to check
            
        Returns:
            Message object or None if not found
        """
        key = f"message:{message_id}"
        data = await self.redis.hgetall(key)
        
        if not data:
            return None
        
        return Message.from_dict(data)
    
    async def get_inbox_size(self, agent_id: Optional[str] = None) -> int:
        """
        Get number of pending messages in inbox.
        
        Args:
            agent_id: Agent ID to check (default: self)
            
        Returns:
            Number of pending messages
        """
        target_agent = agent_id or self.agent_id
        if not target_agent:
            raise RuntimeError("No agent_id specified")
        
        inbox_key = f"agent:inbox:{target_agent}"
        return await self.redis.llen(inbox_key)
    
    def _serialize_message(self, message: Message) -> str:
        """Serialize message to JSON string."""
        import json
        return json.dumps(message.to_dict())
    
    def _deserialize_message(self, data: str) -> Message:
        """Deserialize message from JSON string."""
        import json
        return Message.from_dict(json.loads(data))
