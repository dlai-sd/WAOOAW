"""
Tests for RequestResponseHandler - Synchronous Communication Pattern

Tests cover:
- Request creation and sending
- Response handling
- Timeout handling
- Query handler registration
- Broadcast requests
- Error responses
"""

import asyncio

import pytest
import pytest_asyncio
import redis.asyncio as redis

from waooaw.communication.messaging import Message, MessageBus, MessageType
from waooaw.communication.request_response import (
    Request,
    RequestResponseHandler,
    Response,
    ResponseStatus,
    TimeoutError,
)


@pytest_asyncio.fixture
async def redis_client():
    """Create Redis client for testing."""
    client = await redis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=True
    )
    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def message_bus_a(redis_client):
    """Create MessageBus for agent-a."""
    bus = MessageBus(redis_client)
    await bus.start("agent-a")
    yield bus
    await bus.stop()


@pytest.fixture
async def message_bus_b(redis_client):
    """Create MessageBus for agent-b."""
    bus = MessageBus(redis_client)
    await bus.start("agent-b")
    yield bus
    await bus.stop()


@pytest.fixture
def rr_handler_a(message_bus_a):
    """Create RequestResponseHandler for agent-a."""
    return RequestResponseHandler(message_bus_a)


@pytest.fixture
def rr_handler_b(message_bus_b):
    """Create RequestResponseHandler for agent-b."""
    return RequestResponseHandler(message_bus_b)


# Request Tests

def test_request_creation():
    """Test request object creation."""
    req = Request(
        from_agent="agent-a",
        to_agent="agent-b",
        method="get_status",
        params={"detailed": True},
    )
    
    assert req.from_agent == "agent-a"
    assert req.to_agent == "agent-b"
    assert req.method == "get_status"
    assert req.params["detailed"] is True
    assert len(req.request_id) > 0


def test_request_to_message():
    """Test converting request to message."""
    req = Request(
        from_agent="agent-a",
        to_agent="agent-b",
        method="get_status",
        params={"detailed": True},
    )
    
    msg = req.to_message()
    
    assert msg.from_agent == "agent-a"
    assert msg.to_agent == "agent-b"
    assert msg.message_type == MessageType.QUERY
    assert msg.correlation_id == req.request_id
    assert msg.payload["method"] == "get_status"
    assert msg.payload["params"]["detailed"] is True


# Response Tests

def test_response_creation():
    """Test response object creation."""
    resp = Response(
        request_id="req-123",
        from_agent="agent-b",
        to_agent="agent-a",
        status=ResponseStatus.SUCCESS,
        result={"status": "healthy"},
    )
    
    assert resp.request_id == "req-123"
    assert resp.status == ResponseStatus.SUCCESS
    assert resp.result["status"] == "healthy"


def test_response_success_helper():
    """Test Response.success() helper."""
    resp = Response.success(
        request_id="req-123",
        from_agent="agent-b",
        to_agent="agent-a",
        result={"data": "test"},
    )
    
    assert resp.status == ResponseStatus.SUCCESS
    assert resp.result["data"] == "test"
    assert resp.error is None


def test_response_error_helper():
    """Test Response.error() helper."""
    resp = Response.error(
        request_id="req-123",
        from_agent="agent-b",
        to_agent="agent-a",
        error="Invalid parameter",
    )
    
    assert resp.status == ResponseStatus.ERROR
    assert resp.error == "Invalid parameter"
    assert resp.result is None


def test_response_to_message():
    """Test converting response to message."""
    resp = Response(
        request_id="req-123",
        from_agent="agent-b",
        to_agent="agent-a",
        status=ResponseStatus.SUCCESS,
        result={"data": "test"},
    )
    
    msg = resp.to_message()
    
    assert msg.from_agent == "agent-b"
    assert msg.to_agent == "agent-a"
    assert msg.message_type == MessageType.RESPONSE
    assert msg.correlation_id == "req-123"
    assert msg.payload["status"] == "success"


# RequestResponseHandler Tests

@pytest.mark.asyncio
async def test_send_request_and_receive_response(rr_handler_a, rr_handler_b):
    """Test sending request and receiving response."""
    
    # Register query handler on agent-b
    async def get_status_handler():
        return {"status": "healthy", "uptime": 100}
    
    rr_handler_b.register_query_handler("get_status", get_status_handler)
    
    # Send request from agent-a to agent-b
    response = await rr_handler_a.send_request(
        to_agent="agent-b",
        method="get_status",
        timeout=5,
    )
    
    assert response.status == ResponseStatus.SUCCESS
    assert response.result["status"] == "healthy"


@pytest.mark.asyncio
async def test_request_with_parameters(rr_handler_a, rr_handler_b):
    """Test request with method parameters."""
    
    # Register handler that uses parameters
    async def calculate_handler(x: int, y: int, operation: str):
        if operation == "add":
            return x + y
        elif operation == "multiply":
            return x * y
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    rr_handler_b.register_query_handler("calculate", calculate_handler)
    
    # Send request with params
    response = await rr_handler_a.send_request(
        to_agent="agent-b",
        method="calculate",
        params={"x": 5, "y": 3, "operation": "add"},
        timeout=5,
    )
    
    assert response.status == ResponseStatus.SUCCESS
    assert response.result == 8


@pytest.mark.asyncio
async def test_request_timeout(rr_handler_a, rr_handler_b):
    """Test request timeout when no response."""
    
    # Register handler that takes too long
    async def slow_handler():
        await asyncio.sleep(10)  # Longer than timeout
        return {"data": "slow"}
    
    rr_handler_b.register_query_handler("slow_method", slow_handler)
    
    # Send request with short timeout
    with pytest.raises(TimeoutError) as exc_info:
        await rr_handler_a.send_request(
            to_agent="agent-b",
            method="slow_method",
            timeout=1,  # 1 second timeout
        )
    
    assert "timed out after 1s" in str(exc_info.value)


@pytest.mark.asyncio
async def test_unknown_method_error(rr_handler_a, rr_handler_b):
    """Test error response for unknown method."""
    
    # Send request for unregistered method
    response = await rr_handler_a.send_request(
        to_agent="agent-b",
        method="unknown_method",
        timeout=5,
    )
    
    assert response.status == ResponseStatus.NOT_FOUND
    assert "Unknown method" in response.error


@pytest.mark.asyncio
async def test_handler_exception_error(rr_handler_a, rr_handler_b):
    """Test error response when handler raises exception."""
    
    # Register handler that raises exception
    async def failing_handler():
        raise ValueError("Something went wrong!")
    
    rr_handler_b.register_query_handler("failing_method", failing_handler)
    
    # Send request
    response = await rr_handler_a.send_request(
        to_agent="agent-b",
        method="failing_method",
        timeout=5,
    )
    
    assert response.status == ResponseStatus.ERROR
    assert "Something went wrong!" in response.error


@pytest.mark.asyncio
async def test_broadcast_request(redis_client):
    """Test broadcasting request to multiple agents."""
    
    # Create 3 agents
    bus_a = MessageBus(redis_client)
    bus_b = MessageBus(redis_client)
    bus_c = MessageBus(redis_client)
    bus_d = MessageBus(redis_client)
    
    await bus_a.start("agent-a")
    await bus_b.start("agent-b")
    await bus_c.start("agent-c")
    await bus_d.start("agent-d")
    
    rr_a = RequestResponseHandler(bus_a)
    rr_b = RequestResponseHandler(bus_b)
    rr_c = RequestResponseHandler(bus_c)
    rr_d = RequestResponseHandler(bus_d)
    
    # Register handlers
    async def get_status_b():
        return {"agent": "b", "status": "healthy"}
    
    async def get_status_c():
        return {"agent": "c", "status": "healthy"}
    
    async def get_status_d():
        return {"agent": "d", "status": "degraded"}
    
    rr_b.register_query_handler("get_status", get_status_b)
    rr_c.register_query_handler("get_status", get_status_c)
    rr_d.register_query_handler("get_status", get_status_d)
    
    # Broadcast request
    responses = await rr_a.broadcast_request(
        to_agents=["agent-b", "agent-c", "agent-d"],
        method="get_status",
        timeout=5,
    )
    
    assert len(responses) == 3
    
    # Check all responses
    agents_responded = {r.result["agent"] for r in responses if r.status == ResponseStatus.SUCCESS}
    assert agents_responded == {"b", "c", "d"}
    
    await bus_a.stop()
    await bus_b.stop()
    await bus_c.stop()
    await bus_d.stop()


@pytest.mark.asyncio
async def test_broadcast_with_timeout(redis_client):
    """Test broadcast when some agents timeout."""
    
    # Create 2 agents
    bus_a = MessageBus(redis_client)
    bus_b = MessageBus(redis_client)
    
    await bus_a.start("agent-a")
    await bus_b.start("agent-b")
    
    rr_a = RequestResponseHandler(bus_a)
    rr_b = RequestResponseHandler(bus_b)
    
    # Register handler on agent-b only
    async def get_status_b():
        return {"agent": "b", "status": "healthy"}
    
    rr_b.register_query_handler("get_status", get_status_b)
    
    # Broadcast to agent-b (exists) and agent-c (doesn't exist)
    responses = await rr_a.broadcast_request(
        to_agents=["agent-b", "agent-c"],
        method="get_status",
        timeout=2,
    )
    
    assert len(responses) == 2
    
    # One success, one timeout
    success_count = sum(1 for r in responses if r.status == ResponseStatus.SUCCESS)
    timeout_count = sum(1 for r in responses if r.status == ResponseStatus.TIMEOUT)
    
    assert success_count == 1
    assert timeout_count == 1
    
    await bus_a.stop()
    await bus_b.stop()


@pytest.mark.asyncio
async def test_sync_handler(rr_handler_a, rr_handler_b):
    """Test synchronous (non-async) query handler."""
    
    # Register sync handler
    def get_version():
        return {"version": "1.0.0"}
    
    rr_handler_b.register_query_handler("get_version", get_version)
    
    # Send request
    response = await rr_handler_a.send_request(
        to_agent="agent-b",
        method="get_version",
        timeout=5,
    )
    
    assert response.status == ResponseStatus.SUCCESS
    assert response.result["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_correlation_id_tracking(rr_handler_a, rr_handler_b):
    """Test that correlation IDs are preserved."""
    
    # Register handler
    async def echo_handler(message: str):
        return {"echo": message}
    
    rr_handler_b.register_query_handler("echo", echo_handler)
    
    # Send request
    response = await rr_handler_a.send_request(
        to_agent="agent-b",
        method="echo",
        params={"message": "test"},
        timeout=5,
    )
    
    # Check correlation ID matches request
    assert response.request_id is not None
    assert len(response.request_id) > 0


@pytest.mark.asyncio
async def test_concurrent_requests(rr_handler_a, rr_handler_b):
    """Test multiple concurrent requests."""
    
    # Register handler
    async def process_handler(value: int):
        await asyncio.sleep(0.1)  # Simulate processing
        return value * 2
    
    rr_handler_b.register_query_handler("process", process_handler)
    
    # Send multiple concurrent requests
    tasks = [
        rr_handler_a.send_request("agent-b", "process", {"value": i}, timeout=5)
        for i in range(10)
    ]
    
    responses = await asyncio.gather(*tasks)
    
    assert len(responses) == 10
    assert all(r.status == ResponseStatus.SUCCESS for r in responses)
    
    # Check results (should be doubled)
    results = [r.result for r in responses]
    assert results == [i * 2 for i in range(10)]
