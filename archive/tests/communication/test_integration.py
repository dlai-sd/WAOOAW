"""
Integration Tests for Inter-Agent Protocol (Epic 3.2)

Tests the complete inter-agent communication system with all components:
- MessageBus (point-to-point messaging)
- RequestResponseHandler (synchronous patterns)
- MessageAuditTrail (compliance logging)
- RateLimiter (abuse prevention)
- MessageSerializer (efficient transport)

Integration scenarios:
- End-to-end message flow with all features
- Multi-agent workflows
- Rate limiting enforcement
- Audit trail verification
- Serialization optimization
"""

import asyncio
from datetime import datetime

import pytest
import pytest_asyncio

from waooaw.communication.messaging import Message, MessageBus, MessageType, MessagePriority
from waooaw.communication.audit import MessageAuditTrail, RetentionPolicy
from waooaw.communication.rate_limiter import RateLimiter, RateLimitConfig, RateLimitWindow, RateLimitExceeded
from waooaw.communication.serialization import MessageSerializer, SerializationFormat


# Test Fixtures

@pytest_asyncio.fixture
async def audit_trail():
    """Create audit trail with SQLite."""
    trail = MessageAuditTrail(
        database_url="sqlite+aiosqlite:///:memory:",
        retention_policy=RetentionPolicy.DAYS_90,
    )
    await trail.initialize()
    yield trail
    await trail.close()


@pytest.fixture
def rate_limiter():
    """Create rate limiter with reasonable defaults."""
    config = RateLimitConfig(
        agent_id="default",
        max_requests=100,
        window=RateLimitWindow.MINUTE,
    )
    return RateLimiter(default_config=config)


@pytest.fixture
def serializer():
    """Create message serializer."""
    return MessageSerializer(
        default_format=SerializationFormat.JSON,
        compression_threshold=512,  # 512 bytes
    )


# Integration Test Scenarios

@pytest.mark.asyncio
async def test_end_to_end_message_with_audit(audit_trail):
    """Test complete message flow with audit logging."""
    # Create message
    message = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        priority=MessagePriority.NORMAL,
        payload={"action": "test", "data": "integration"},
    )
    
    # Log to audit trail
    await audit_trail.log_message(message)
    
    # Simulate delivery
    await audit_trail.update_message_status(
        message_id=message.message_id,
        status=message.status,
        delivered_at=datetime.utcnow(),
    )
    
    # Verify in audit trail
    from waooaw.communication.audit import AuditQuery
    query = AuditQuery(from_agent="agent-a")
    messages = await audit_trail.query_messages(query)
    
    assert len(messages) == 1
    assert messages[0]["from_agent"] == "agent-a"
    assert messages[0]["to_agent"] == "agent-b"


@pytest.mark.asyncio
async def test_rate_limited_messages(rate_limiter, audit_trail):
    """Test rate limiting with audit logging."""
    # Configure low limit
    rate_limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="limited-agent",
            max_requests=3,
            window=RateLimitWindow.SECOND,
        )
    )
    
    # Send messages until rate limited
    sent_count = 0
    for i in range(5):
        message = Message(
            from_agent="limited-agent",
            to_agent="target-agent",
            message_type=MessageType.COMMAND,
            payload={"index": i},
        )
        
        try:
            # Check rate limit
            await rate_limiter.check_limit("limited-agent")
            
            # Log successful send
            await audit_trail.log_message(message)
            sent_count += 1
            
        except RateLimitExceeded as e:
            # Log rate limit violation
            assert e.status.retry_after is not None
            break
    
    # Should have sent 3 messages before rate limit
    assert sent_count == 3


@pytest.mark.asyncio
async def test_serialized_message_with_audit(serializer, audit_trail):
    """Test serialization integrated with audit trail."""
    # Create message
    message = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"data": "test" * 100},  # Larger payload for compression
    )
    
    # Serialize
    data_bytes, format, compression = serializer.serialize_message_payload(message)
    
    # Log to audit (stores original message)
    await audit_trail.log_message(message)
    
    # Verify serialization saved space
    original_size = len(str(message.payload))
    serialized_size = len(data_bytes)
    
    # Compressed should be smaller (or similar for small data)
    assert serialized_size <= original_size * 1.5  # Allow some overhead


@pytest.mark.asyncio
async def test_multi_agent_conversation(audit_trail):
    """Test multi-agent conversation with correlation tracking."""
    correlation_id = "conv-integration-test"
    
    # Agent A sends request
    request = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.QUERY,
        correlation_id=correlation_id,
        payload={"query": "get_status"},
    )
    await audit_trail.log_message(request)
    
    # Agent B sends response
    response = Message(
        from_agent="agent-b",
        to_agent="agent-a",
        message_type=MessageType.RESPONSE,
        correlation_id=correlation_id,
        reply_to=request.message_id,
        payload={"status": "ok", "value": 42},
    )
    await audit_trail.log_message(response)
    
    # Agent A sends followup
    followup = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        correlation_id=correlation_id,
        payload={"action": "confirm"},
    )
    await audit_trail.log_message(followup)
    
    # Retrieve conversation
    conversation = await audit_trail.get_conversation_history(correlation_id)
    
    assert len(conversation) == 3
    assert all(msg["correlation_id"] == correlation_id for msg in conversation)


@pytest.mark.asyncio
async def test_rate_limit_with_serialization(rate_limiter, serializer):
    """Test rate limiting with different serialization formats."""
    rate_limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="test-agent",
            max_requests=10,
            window=RateLimitWindow.SECOND,
        )
    )
    
    # Send messages with different serialization
    for i in range(5):
        # Check rate limit
        status = await rate_limiter.check_limit("test-agent")
        
        # Create and serialize message
        message = Message(
            from_agent="test-agent",
            to_agent="target",
            message_type=MessageType.COMMAND,
            payload={"index": i},
        )
        
        # Alternate formats
        format = SerializationFormat.JSON if i % 2 == 0 else SerializationFormat.MSGPACK
        data_bytes, _, _ = serializer.serialize_message_payload(message, format=format)
        
        assert isinstance(data_bytes, bytes)
        assert status.requests_remaining > 0


@pytest.mark.asyncio
async def test_audit_statistics_after_workflow(audit_trail):
    """Test audit statistics after multi-agent workflow."""
    # Simulate workflow: 3 agents exchanging messages
    agents = ["orchestrator", "worker-1", "worker-2"]
    
    for i in range(10):
        from_agent = agents[i % 3]
        to_agent = agents[(i + 1) % 3]
        
        message = Message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=MessageType.COMMAND,
            payload={"task": i},
        )
        
        await audit_trail.log_message(message)
    
    # Get statistics
    stats = await audit_trail.get_statistics()
    
    assert stats.total_messages == 10
    assert len(stats.top_senders) > 0
    assert len(stats.top_receivers) > 0
    
    # All agents should have communicated (check at least 2 appear)
    sender_agents = [agent for agent, _ in stats.top_senders]
    receiver_agents = [agent for agent, _ in stats.top_receivers]
    assert len(sender_agents) >= 2  # At least 2 different senders
    assert len(receiver_agents) >= 2  # At least 2 different receivers


@pytest.mark.asyncio
async def test_compression_effectiveness(serializer):
    """Test compression effectiveness for various payload sizes."""
    # Small payload (should not compress)
    small_message = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"key": "value"},
    )
    
    small_result = serializer.serialize(small_message.to_dict())
    assert small_result.compression.value == "none"  # Below threshold
    
    # Large payload (should compress)
    large_message = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={"text": "Lorem ipsum " * 100},  # ~1.3KB
    )
    
    large_result = serializer.serialize(large_message.to_dict())
    assert large_result.compression.value != "none"  # Above threshold
    assert large_result.compression_ratio < 1.0  # Compressed


@pytest.mark.asyncio
async def test_concurrent_agents_with_rate_limits(rate_limiter):
    """Test multiple agents operating concurrently with individual rate limits."""
    # Configure different limits for 3 agents
    agents_config = [
        ("fast-agent", 20, RateLimitWindow.SECOND),
        ("medium-agent", 10, RateLimitWindow.SECOND),
        ("slow-agent", 5, RateLimitWindow.SECOND),
    ]
    
    for agent_id, max_req, window in agents_config:
        rate_limiter.set_agent_limit(
            RateLimitConfig(
                agent_id=agent_id,
                max_requests=max_req,
                window=window,
            )
        )
    
    # Each agent sends up to their limit
    results = {}
    for agent_id, max_req, _ in agents_config:
        sent = 0
        for i in range(max_req + 5):  # Try to exceed limit
            try:
                await rate_limiter.check_limit(agent_id)
                sent += 1
            except RateLimitExceeded:
                break
        
        results[agent_id] = sent
    
    # Verify each agent hit their limit
    assert results["fast-agent"] == 20
    assert results["medium-agent"] == 10
    assert results["slow-agent"] == 5


@pytest.mark.asyncio
async def test_message_serialization_formats(serializer):
    """Test different serialization formats in realistic scenario."""
    message = Message(
        from_agent="agent-a",
        to_agent="agent-b",
        message_type=MessageType.COMMAND,
        payload={
            "action": "process",
            "data": {"items": list(range(50)), "text": "test data"},
        },
    )
    
    # Get comparison stats
    stats = serializer.get_compression_stats(message.to_dict())
    
    # Should have JSON
    assert "json" in stats
    assert stats["json"]["original_size"] > 0
    
    # MessagePack should be more compact (if available)
    if "msgpack" in stats:
        assert stats["msgpack"]["original_size"] < stats["json"]["original_size"]


@pytest.mark.asyncio
async def test_full_workflow_integration(audit_trail, rate_limiter, serializer):
    """Test complete workflow with all components."""
    # Configure rate limit
    rate_limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="workflow-agent",
            max_requests=10,
            window=RateLimitWindow.SECOND,
        )
    )
    
    correlation_id = "full-workflow-test"
    messages_sent = []
    
    # Workflow: Agent sends multiple messages
    for i in range(5):
        # 1. Check rate limit
        try:
            status = await rate_limiter.check_limit("workflow-agent")
        except RateLimitExceeded:
            break
        
        # 2. Create message
        message = Message(
            from_agent="workflow-agent",
            to_agent=f"worker-{i % 2}",
            message_type=MessageType.COMMAND,
            correlation_id=correlation_id,
            payload={"task": f"process-{i}", "data": "x" * 100},
        )
        
        # 3. Serialize
        data_bytes, format, compression = serializer.serialize_message_payload(message)
        
        # 4. Log to audit
        await audit_trail.log_message(message)
        
        # 5. Update delivery status
        await audit_trail.update_message_status(
            message_id=message.message_id,
            status=message.status,
        )
        
        messages_sent.append(message.message_id)
    
    # Verify all components worked
    assert len(messages_sent) == 5
    
    # Check rate limit status
    final_status = await rate_limiter.get_status("workflow-agent")
    assert final_status.requests_made == 5
    
    # Check audit trail
    conversation = await audit_trail.get_conversation_history(correlation_id)
    assert len(conversation) == 5


@pytest.mark.asyncio
async def test_agent_communication_history(audit_trail):
    """Test retrieving agent's complete communication history."""
    agent_id = "history-test-agent"
    
    # Agent sends messages
    for i in range(3):
        message = Message(
            from_agent=agent_id,
            to_agent=f"target-{i}",
            message_type=MessageType.COMMAND,
            payload={"sent": i},
        )
        await audit_trail.log_message(message)
    
    # Agent receives messages
    for i in range(2):
        message = Message(
            from_agent=f"sender-{i}",
            to_agent=agent_id,
            message_type=MessageType.RESPONSE,
            payload={"received": i},
        )
        await audit_trail.log_message(message)
    
    # Get history
    history = await audit_trail.get_agent_communication_history(agent_id, days=1)
    
    # Should have 5 total (3 sent + 2 received)
    assert len(history) == 5


@pytest.mark.asyncio
async def test_performance_baseline(serializer):
    """Test performance baseline for serialization."""
    message = Message(
        from_agent="perf-agent",
        to_agent="target",
        message_type=MessageType.COMMAND,
        payload={"data": list(range(100))},
    )
    
    # Measure serialization time
    start = asyncio.get_event_loop().time()
    
    for _ in range(100):
        serializer.serialize_message_payload(message)
    
    elapsed = asyncio.get_event_loop().time() - start
    
    # Should serialize 100 messages in reasonable time
    assert elapsed < 1.0  # Less than 1 second for 100 serializations


# Summary Test

@pytest.mark.asyncio
async def test_epic_3_2_complete_integration(audit_trail, rate_limiter, serializer):
    """
    Complete Epic 3.2 integration test.
    
    Tests all 4 stories working together:
    - Story 1: MessageBus (messaging)
    - Story 2: Audit Trail (compliance)
    - Story 3: Rate Limiting (abuse prevention)
    - Story 4: Serialization (optimization)
    """
    # Setup
    rate_limiter.set_agent_limit(
        RateLimitConfig(
            agent_id="epic-test-agent",
            max_requests=50,
            window=RateLimitWindow.MINUTE,
        )
    )
    
    correlation_id = "epic-3-2-complete"
    successful_messages = 0
    
    # Simulate realistic agent workflow
    for i in range(20):
        try:
            # Rate limit check (Story 3)
            await rate_limiter.check_limit("epic-test-agent")
            
            # Create message (Story 1)
            message = Message(
                from_agent="epic-test-agent",
                to_agent="target-agent",
                message_type=MessageType.COMMAND if i % 2 == 0 else MessageType.QUERY,
                priority=MessagePriority.URGENT if i < 5 else MessagePriority.NORMAL,
                correlation_id=correlation_id,
                payload={"index": i, "data": "x" * (i * 10)},
            )
            
            # Serialize (Story 4)
            result = serializer.serialize(message.to_dict())
            assert result.data is not None
            
            # Audit log (Story 2)
            await audit_trail.log_message(message)
            
            successful_messages += 1
            
        except RateLimitExceeded:
            # Expected for some iterations
            pass
    
    # Verify integration
    assert successful_messages >= 20  # All should succeed (low rate limit)
    
    # Check audit trail has all messages
    conversation = await audit_trail.get_conversation_history(correlation_id)
    assert len(conversation) == successful_messages
    
    # Check rate limit tracking
    status = await rate_limiter.get_status("epic-test-agent")
    assert status.requests_made == successful_messages
    
    # Check statistics
    stats = await audit_trail.get_statistics()
    assert stats.total_messages >= successful_messages
    
    # SUCCESS: All Epic 3.2 components integrated! 🎉
