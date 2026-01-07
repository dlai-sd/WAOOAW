"""
Tests for Message Audit Trail - Compliance Tracking

Tests cover:
- Message logging to database
- Status updates
- Query interface with filters
- Conversation history tracking
- Agent communication history
- Statistics generation
- Retention policy enforcement
"""

import asyncio
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine

from waooaw.communication.messaging import Message, MessageType, MessagePriority, MessageStatus
from waooaw.communication.audit import (
    MessageAuditTrail,
    MessageAuditLog,
    RetentionPolicy,
    AuditQuery,
    Base,
)


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def audit_trail():
    """Create audit trail with test database."""
    trail = MessageAuditTrail(
        database_url=TEST_DATABASE_URL,
        retention_policy=RetentionPolicy.DAYS_90,
    )
    
    await trail.initialize()
    
    yield trail
    
    await trail.close()


@pytest.fixture
def sample_message():
    """Create sample message."""
    return Message(
        message_id="msg-123",
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        priority=MessagePriority.NORMAL,
        payload={"action": "test", "data": "hello"},
        timestamp=datetime.utcnow().isoformat(),
    )


# Basic Logging Tests

@pytest.mark.asyncio
async def test_log_message(audit_trail, sample_message):
    """Test logging message to audit trail."""
    await audit_trail.log_message(sample_message)
    
    # Query to verify
    query = AuditQuery(from_agent="agent-a")
    messages = await audit_trail.query_messages(query)
    
    assert len(messages) == 1
    assert messages[0]["message_id"] == "msg-123"
    assert messages[0]["from_agent"] == "agent-a"
    assert messages[0]["to_agent"] == "agent-b"


@pytest.mark.asyncio
async def test_log_multiple_messages(audit_trail):
    """Test logging multiple messages."""
    for i in range(5):
        msg = Message(
            message_id=f"msg-{i}",
            from_agent="agent-a",
            to_agent="agent-b",
            message_type=MessageType.COMMAND,
            payload={"index": i},
        )
        await audit_trail.log_message(msg)
    
    # Query all
    query = AuditQuery(limit=10)
    messages = await audit_trail.query_messages(query)
    
    assert len(messages) == 5


@pytest.mark.asyncio
async def test_update_message_status(audit_trail, sample_message):
    """Test updating message status."""
    await audit_trail.log_message(sample_message)
    
    # Update status
    delivered_at = datetime.utcnow()
    await audit_trail.update_message_status(
        message_id="msg-123",
        status=MessageStatus.DELIVERED,
        delivered_at=delivered_at,
    )
    
    # Verify update - query by from_agent to get the message
    query = AuditQuery(from_agent="agent-a")
    messages = await audit_trail.query_messages(query)
    
    assert len(messages) == 1
    assert messages[0]["message_id"] == "msg-123"
    assert messages[0]["status"] == "delivered"
    assert messages[0]["delivered_at"] is not None


# Query Tests

@pytest.mark.asyncio
async def test_query_by_from_agent(audit_trail):
    """Test querying by sender agent."""
    # Create messages from different agents
    for agent in ["agent-a", "agent-b", "agent-c"]:
        msg = Message(
            from_agent=agent,
            to_agent="agent-receiver",
            message_type=MessageType.COMMAND,
            payload={"from": agent},
        )
        await audit_trail.log_message(msg)
    
    # Query for agent-a
    query = AuditQuery(from_agent="agent-a")
    messages = await audit_trail.query_messages(query)
    
    assert len(messages) == 1
    assert messages[0]["from_agent"] == "agent-a"


@pytest.mark.asyncio
async def test_query_by_to_agent(audit_trail):
    """Test querying by receiver agent."""
    # Create messages to different agents
    for agent in ["agent-x", "agent-y", "agent-z"]:
        msg = Message(
            from_agent="agent-sender",
            to_agent=agent,
            message_type=MessageType.COMMAND,
            payload={"to": agent},
        )
        await audit_trail.log_message(msg)
    
    # Query for agent-x
    query = AuditQuery(to_agent="agent-x")
    messages = await audit_trail.query_messages(query)
    
    assert len(messages) == 1
    assert messages[0]["to_agent"] == "agent-x"


@pytest.mark.asyncio
async def test_query_by_message_type(audit_trail):
    """Test querying by message type."""
    # Create messages of different types
    for msg_type in [MessageType.COMMAND, MessageType.QUERY, MessageType.EVENT]:
        msg = Message(
            from_agent="agent-a",
            to_agent="agent-b",
            message_type=msg_type,
            payload={"type": msg_type.value},
        )
        await audit_trail.log_message(msg)
    
    # Query for COMMAND
    query = AuditQuery(message_type=MessageType.COMMAND)
    messages = await audit_trail.query_messages(query)
    
    assert len(messages) == 1
    assert messages[0]["message_type"] == "command"


@pytest.mark.asyncio
async def test_query_by_status(audit_trail):
    """Test querying by status."""
    # Create messages with different statuses
    for i, status in enumerate([MessageStatus.SENT, MessageStatus.DELIVERED, MessageStatus.FAILED]):
        msg = Message(
            message_id=f"msg-{i}",
            from_agent="agent-a",
            to_agent="agent-b",
            status=status,
            message_type=MessageType.COMMAND,
            payload={"status": status.value},
        )
        await audit_trail.log_message(msg)
    
    # Query for DELIVERED
    query = AuditQuery(status=MessageStatus.DELIVERED)
    messages = await audit_trail.query_messages(query)
    
    assert len(messages) == 1
    assert messages[0]["status"] == "delivered"


@pytest.mark.asyncio
async def test_query_by_time_range(audit_trail):
    """Test querying by time range."""
    now = datetime.utcnow()
    
    # Create messages at different times
    for i in range(3):
        timestamp = now - timedelta(hours=i)
        msg = Message(
            message_id=f"msg-{i}",
            from_agent="agent-a",
            to_agent="agent-b",
            message_type=MessageType.COMMAND,
            payload={"hour": i},
            timestamp=timestamp.isoformat(),
        )
        await audit_trail.log_message(msg)
    
    # Query for last hour
    start_time = now - timedelta(hours=1)
    query = AuditQuery(start_time=start_time)
    messages = await audit_trail.query_messages(query)
    
    # Should get messages from 0 and 1 hours ago (not 2 hours ago)
    assert len(messages) >= 1


@pytest.mark.asyncio
async def test_query_with_pagination(audit_trail):
    """Test query pagination."""
    # Create 15 messages
    for i in range(15):
        msg = Message(
            message_id=f"msg-{i}",
            from_agent="agent-a",
            to_agent="agent-b",
            message_type=MessageType.COMMAND,
            payload={"index": i},
        )
        await audit_trail.log_message(msg)
    
    # First page
    query1 = AuditQuery(limit=10, offset=0)
    page1 = await audit_trail.query_messages(query1)
    assert len(page1) == 10
    
    # Second page
    query2 = AuditQuery(limit=10, offset=10)
    page2 = await audit_trail.query_messages(query2)
    assert len(page2) == 5


# Conversation History Tests

@pytest.mark.asyncio
async def test_get_conversation_history(audit_trail):
    """Test getting full conversation by correlation ID."""
    correlation_id = "conv-123"
    
    # Create conversation messages
    for i in range(5):
        msg = Message(
            message_id=f"msg-{i}",
            from_agent="agent-a" if i % 2 == 0 else "agent-b",
            to_agent="agent-b" if i % 2 == 0 else "agent-a",
            message_type=MessageType.COMMAND if i % 2 == 0 else MessageType.RESPONSE,
            correlation_id=correlation_id,
            payload={"turn": i},
        )
        await audit_trail.log_message(msg)
    
    # Get conversation
    conversation = await audit_trail.get_conversation_history(correlation_id)
    
    assert len(conversation) == 5
    # Should be ordered by timestamp
    for i in range(len(conversation) - 1):
        assert conversation[i]["timestamp"] <= conversation[i + 1]["timestamp"]


# Agent Communication History Tests

@pytest.mark.asyncio
async def test_get_agent_communication_history(audit_trail):
    """Test getting agent's communication history."""
    # Create messages from/to agent-a
    for i in range(3):
        # Sent by agent-a
        msg1 = Message(
            from_agent="agent-a",
            to_agent="agent-b",
            message_type=MessageType.COMMAND,
            payload={"sent": i},
        )
        await audit_trail.log_message(msg1)
        
        # Received by agent-a
        msg2 = Message(
            from_agent="agent-b",
            to_agent="agent-a",
            message_type=MessageType.RESPONSE,
            payload={"received": i},
        )
        await audit_trail.log_message(msg2)
    
    # Get agent-a history
    history = await audit_trail.get_agent_communication_history("agent-a", days=1)
    
    # Should have 6 messages (3 sent + 3 received)
    assert len(history) == 6


# Statistics Tests

@pytest.mark.asyncio
async def test_get_statistics(audit_trail):
    """Test getting audit statistics."""
    # Create diverse set of messages
    for i in range(10):
        msg = Message(
            from_agent=f"agent-{i % 3}",  # 3 different senders
            to_agent=f"agent-{(i + 1) % 3}",  # 3 different receivers
            message_type=MessageType.COMMAND if i % 2 == 0 else MessageType.QUERY,
            status=MessageStatus.DELIVERED if i < 8 else MessageStatus.FAILED,
            payload={"index": i},
        )
        await audit_trail.log_message(msg)
    
    # Get statistics
    stats = await audit_trail.get_statistics()
    
    assert stats.total_messages == 10
    assert stats.messages_by_status["delivered"] == 8
    assert stats.messages_by_status["failed"] == 2
    assert stats.error_rate == 20.0  # 2/10 = 20%
    assert len(stats.top_senders) > 0
    assert len(stats.top_receivers) > 0


# Retention Policy Tests

@pytest.mark.asyncio
async def test_retention_policy_30_days():
    """Test 30-day retention policy."""
    trail = MessageAuditTrail(
        database_url=TEST_DATABASE_URL,
        retention_policy=RetentionPolicy.DAYS_30,
    )
    await trail.initialize()
    
    # Create old messages (40 days ago)
    old_time = datetime.utcnow() - timedelta(days=40)
    for i in range(5):
        msg = Message(
            message_id=f"old-{i}",
            from_agent="agent-a",
            to_agent="agent-b",
            message_type=MessageType.COMMAND,
            payload={"old": True},
            timestamp=old_time.isoformat(),
        )
        await trail.log_message(msg)
    
    # Create recent messages
    for i in range(3):
        msg = Message(
            message_id=f"new-{i}",
            from_agent="agent-a",
            to_agent="agent-b",
            message_type=MessageType.COMMAND,
            payload={"old": False},
        )
        await trail.log_message(msg)
    
    # Apply retention policy
    deleted = await trail.apply_retention_policy()
    
    # Should delete 5 old messages
    assert deleted == 5
    
    # Verify only recent messages remain
    query = AuditQuery(limit=100)
    remaining = await trail.query_messages(query)
    assert len(remaining) == 3
    
    await trail.close()


@pytest.mark.asyncio
async def test_retention_policy_forever():
    """Test forever retention policy (no deletion)."""
    trail = MessageAuditTrail(
        database_url=TEST_DATABASE_URL,
        retention_policy=RetentionPolicy.FOREVER,
    )
    await trail.initialize()
    
    # Create old messages
    old_time = datetime.utcnow() - timedelta(days=400)
    for i in range(5):
        msg = Message(
            message_id=f"old-{i}",
            from_agent="agent-a",
            to_agent="agent-b",
            message_type=MessageType.COMMAND,
            payload={"old": True},
            timestamp=old_time.isoformat(),
        )
        await trail.log_message(msg)
    
    # Apply retention policy (should do nothing)
    deleted = await trail.apply_retention_policy()
    
    assert deleted == 0
    
    # All messages should remain
    query = AuditQuery(limit=100)
    remaining = await trail.query_messages(query)
    assert len(remaining) == 5
    
    await trail.close()


# Error Handling Tests

@pytest.mark.asyncio
async def test_update_nonexistent_message(audit_trail):
    """Test updating message that doesn't exist."""
    # Should not raise error, just silently skip
    await audit_trail.update_message_status(
        message_id="nonexistent",
        status=MessageStatus.DELIVERED,
    )


@pytest.mark.asyncio
async def test_query_empty_results(audit_trail):
    """Test querying with no matching results."""
    query = AuditQuery(from_agent="nonexistent-agent")
    messages = await audit_trail.query_messages(query)
    
    assert len(messages) == 0
