"""
Tests for MessageBus - Direct Agent-to-Agent Communication

Tests cover:
- Message creation and serialization
- Point-to-point messaging
- Message delivery
- Inbox management
- TTL and expiry
- Message status tracking
- Delivery receipts
- Priority handling
"""

import asyncio
import json
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
import redis.asyncio as redis

from waooaw.communication.messaging import (
    DeliveryReceipt,
    Message,
    MessageBus,
    MessagePriority,
    MessageStatus,
    MessageType,
)


@pytest_asyncio.fixture
async def redis_client():
    """Create Redis client for testing."""
    client = await redis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=True
    )
    
    # Clean up test keys
    await client.flushdb()
    
    yield client
    
    await client.flushdb()
    await client.aclose()


@pytest.fixture
def message_bus(redis_client):
    """Create MessageBus instance."""
    return MessageBus(redis_client)


@pytest.fixture
def sample_message():
    """Create sample message."""
    return Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        priority=MessagePriority.NORMAL,
        payload={"action": "test", "data": "hello"},
    )


# Message Tests

def test_message_creation():
    """Test message object creation."""
    msg = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"test": "data"},
    )
    
    assert msg.from_agent == "agent-a"
    assert msg.to_agent == "agent-b"
    assert msg.message_type == MessageType.COMMAND
    assert msg.priority == MessagePriority.NORMAL  # default
    assert msg.status == MessageStatus.PENDING  # default
    assert msg.retry_count == 0
    assert len(msg.message_id) > 0


def test_message_serialization(sample_message):
    """Test message to/from dict."""
    data = sample_message.to_dict()
    
    assert data["from_agent"] == "agent-a"
    assert data["to_agent"] == "agent-b"
    assert data["message_type"] == "command"
    assert data["payload"]["action"] == "test"
    
    # Deserialize
    restored = Message.from_dict(data)
    assert restored.from_agent == sample_message.from_agent
    assert restored.to_agent == sample_message.to_agent
    assert restored.message_type == sample_message.message_type


def test_message_expiry():
    """Test message TTL expiry check."""
    # Create message with short TTL
    msg = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        ttl_seconds=1,  # 1 second
    )
    
    # Not expired immediately
    assert not msg.is_expired()
    
    # Set timestamp in past
    past = datetime.utcnow() - timedelta(seconds=5)
    msg.timestamp = past.isoformat()
    
    # Should be expired now
    assert msg.is_expired()


def test_message_retry_logic():
    """Test message retry decision."""
    msg = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        max_retries=3,
    )
    
    # Pending message should not retry
    assert not msg.should_retry()
    
    # Failed message should retry
    msg.status = MessageStatus.FAILED
    msg.retry_count = 1
    assert msg.should_retry()
    
    # Exceeded max retries
    msg.retry_count = 3
    assert not msg.should_retry()
    
    # Expired message should not retry
    msg.retry_count = 0
    msg.timestamp = (datetime.utcnow() - timedelta(seconds=1000)).isoformat()
    assert not msg.should_retry()


# MessageBus Tests

@pytest.mark.asyncio
async def test_message_bus_start_stop(message_bus):
    """Test starting and stopping message bus."""
    await message_bus.start("agent-a")
    
    assert message_bus.agent_id == "agent-a"
    assert message_bus.running is True
    assert message_bus._delivery_task is not None
    
    await message_bus.stop()
    
    assert message_bus.running is False


@pytest.mark.asyncio
async def test_send_message(message_bus):
    """Test sending message to agent."""
    await message_bus.start("agent-a")
    
    message = await message_bus.send_message(
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"action": "test"},
    )
    
    assert message.from_agent == "agent-a"
    assert message.to_agent == "agent-b"
    assert message.status == MessageStatus.SENT
    assert message.message_id is not None
    
    await message_bus.stop()


@pytest.mark.asyncio
async def test_receive_messages(message_bus, redis_client):
    """Test receiving messages from inbox."""
    # Start bus for agent-b
    await message_bus.start("agent-b")
    
    # Manually add message to agent-b's inbox
    msg = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"action": "test"},
    )
    
    inbox_key = "agent:inbox:agent-b"
    await redis_client.rpush(inbox_key, json.dumps(msg.to_dict()))
    
    # Receive messages
    messages = await message_bus.receive_messages(timeout=1)
    
    assert len(messages) == 1
    assert messages[0].from_agent == "agent-a"
    assert messages[0].status == MessageStatus.DELIVERED
    
    await message_bus.stop()


@pytest.mark.asyncio
async def test_message_priority(message_bus, redis_client):
    """Test priority message delivery."""
    await message_bus.start("agent-a")
    
    # Send normal priority message
    normal_msg = await message_bus.send_message(
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"priority": "normal"},
        priority=MessagePriority.NORMAL,
    )
    
    # Send urgent priority message
    urgent_msg = await message_bus.send_message(
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"priority": "urgent"},
        priority=MessagePriority.URGENT,
    )
    
    # Check inbox - urgent should be at front
    inbox_key = "agent:inbox:agent-b"
    first_msg_str = await redis_client.lindex(inbox_key, 0)
    first_msg = json.loads(first_msg_str)
    
    # Urgent message should be first (LPUSH puts at front)
    assert first_msg["payload"]["priority"] == "urgent"
    
    await message_bus.stop()


@pytest.mark.asyncio
async def test_expired_message_filtering(message_bus, redis_client):
    """Test that expired messages are not delivered."""
    await message_bus.start("agent-b")
    
    # Create expired message
    past_time = datetime.utcnow() - timedelta(seconds=1000)
    msg = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"data": "expired"},
        ttl_seconds=1,  # Very short TTL
        timestamp=past_time.isoformat(),
    )
    
    inbox_key = "agent:inbox:agent-b"
    await redis_client.rpush(inbox_key, json.dumps(msg.to_dict()))
    
    # Receive messages - expired should be filtered
    messages = await message_bus.receive_messages()
    
    assert len(messages) == 0  # Expired message not delivered
    
    # Check that expired message was marked as expired
    stored = await message_bus.get_message_status(msg.message_id)
    assert stored is not None
    assert stored.status == MessageStatus.EXPIRED
    
    await message_bus.stop()


@pytest.mark.asyncio
async def test_get_inbox_size(message_bus, redis_client):
    """Test inbox size check."""
    await message_bus.start("agent-a")
    
    # Send 3 messages
    for i in range(3):
        await message_bus.send_message(
            to_agent="agent-b",
            message_type=MessageType.COMMAND,
            payload={"index": i},
        )
    
    # Check inbox size
    size = await message_bus.get_inbox_size("agent-b")
    assert size == 3
    
    await message_bus.stop()


@pytest.mark.asyncio
async def test_get_message_status(message_bus):
    """Test message status tracking."""
    await message_bus.start("agent-a")
    
    # Send message
    sent_msg = await message_bus.send_message(
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"test": "data"},
    )
    
    # Get status
    status = await message_bus.get_message_status(sent_msg.message_id)
    
    assert status is not None
    assert status.message_id == sent_msg.message_id
    assert status.status == MessageStatus.SENT
    
    await message_bus.stop()


@pytest.mark.asyncio
async def test_delivery_receipt(message_bus, redis_client):
    """Test delivery receipt creation."""
    await message_bus.start("agent-b")
    
    # Create and deliver message
    msg = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"test": "data"},
    )
    
    inbox_key = "agent:inbox:agent-b"
    await redis_client.rpush(inbox_key, json.dumps(msg.to_dict()))
    
    # Receive message (triggers receipt)
    messages = await message_bus.receive_messages()
    assert len(messages) == 1
    
    # Check receipt was created
    receipt_key = f"receipt:{msg.message_id}"
    receipt_data = await redis_client.hgetall(receipt_key)
    
    assert receipt_data is not None
    assert receipt_data["message_id"] == msg.message_id
    assert receipt_data["to_agent"] == "agent-b"
    assert receipt_data["status"] == "delivered"
    
    await message_bus.stop()


@pytest.mark.asyncio
async def test_handler_registration(message_bus):
    """Test registering and calling message handlers."""
    await message_bus.start("agent-b")
    
    received_messages = []
    
    def handler(message: Message):
        received_messages.append(message)
    
    # Register handler
    message_bus.register_handler(MessageType.COMMAND, handler)
    
    # Manually trigger handler
    msg = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"test": "data"},
    )
    
    await message_bus.handlers[MessageType.COMMAND][0](msg)
    
    assert len(received_messages) == 1
    assert received_messages[0].from_agent == "agent-a"
    
    await message_bus.stop()


@pytest.mark.asyncio
async def test_multiple_message_batch(message_bus, redis_client):
    """Test receiving multiple messages in batch."""
    await message_bus.start("agent-b")
    
    # Add 15 messages to inbox
    inbox_key = "agent:inbox:agent-b"
    for i in range(15):
        msg = Message(
            from_agent="agent-a",
            to_agent="agent-b",
            message_type=MessageType.COMMAND,
            payload={"index": i},
        )
        await redis_client.rpush(inbox_key, json.dumps(msg.to_dict()))
    
    # Receive messages (batch of 10 max)
    messages = await message_bus.receive_messages()
    
    assert len(messages) == 10  # Batch limit
    
    # Receive remaining
    messages2 = await message_bus.receive_messages()
    assert len(messages2) == 5
    
    await message_bus.stop()


@pytest.mark.asyncio
async def test_end_to_end_messaging(redis_client):
    """Test complete message flow between two agents."""
    # Create two message buses
    bus_a = MessageBus(redis_client)
    bus_b = MessageBus(redis_client)
    
    await bus_a.start("agent-a")
    await bus_b.start("agent-b")
    
    received_by_b = []
    
    async def handler(message: Message):
        received_by_b.append(message)
    
    bus_b.register_handler(MessageType.COMMAND, handler)
    
    # Send message from A to B
    await bus_a.send_message(
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"greeting": "Hello from A!"},
    )
    
    # Wait for delivery loop to process
    await asyncio.sleep(0.5)
    
    # Check message received
    assert len(received_by_b) == 1
    assert received_by_b[0].payload["greeting"] == "Hello from A!"
    
    await bus_a.stop()
    await bus_b.stop()
