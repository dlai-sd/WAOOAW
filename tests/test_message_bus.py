"""
Unit Tests for Message Bus Core - Story 1.1

Tests message publishing, subscription, and acknowledgment.
Target: 95%+ coverage
"""
import pytest
import time
from unittest.mock import patch, MagicMock
import json
from redis.exceptions import ResponseError

from waooaw.messaging.models import Message, MessageRouting, MessagePayload
from waooaw.messaging.message_bus import MessageBus


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    with patch('waooaw.messaging.message_bus.redis') as mock:
        client = MagicMock()
        mock.from_url.return_value = client
        yield client


@pytest.fixture
def message_bus_no_sig(mock_redis):
    """Create MessageBus instance without signature verification."""
    return MessageBus(
        redis_url="redis://localhost:6379/0",
        secret_key=None  # No signature required
    )


@pytest.fixture
def message_bus(mock_redis):
    """Create MessageBus instance with mocked Redis."""
    return MessageBus(
        redis_url="redis://localhost:6379/0",
        secret_key="test_secret"
    )


@pytest.fixture
def sample_message():
    """Create a sample message for testing."""
    return Message(
        routing=MessageRouting(
            from_agent="wow-vision-prime",
            to_agents=["wow-content"],
            topic="vision.test"
        ),
        payload=MessagePayload(
            subject="Test message",
            action="notify",
            priority=3
        )
    )


class TestMessageBusInit:
    def test_init(self, message_bus):
        assert message_bus.secret_key == "test_secret"
        assert message_bus.max_len == 10_000_000
        assert message_bus.block_time == 5000
    
    def test_priority_stream_names(self, message_bus):
        assert message_bus._get_priority_stream(1) == "waooaw:messages:p1"
        assert message_bus._get_priority_stream(5) == "waooaw:messages:p5"
    
    def test_topic_stream_names(self, message_bus):
        assert message_bus._get_topic_stream("test.topic") == "waooaw:topics:test.topic"


class TestMessageSignature:
    def test_compute_signature(self, message_bus, sample_message):
        sig = message_bus._compute_signature(sample_message)
        assert len(sig) == 64
        assert all(c in '0123456789abcdef' for c in sig)
    
    def test_verify_valid_signature(self, message_bus, sample_message):
        sig = message_bus._compute_signature(sample_message)
        sample_message.metadata.signature = sig
        assert message_bus._verify_signature(sample_message) is True
    
    def test_verify_invalid_signature(self, message_bus, sample_message):
        sample_message.metadata.signature = "0" * 64
        assert message_bus._verify_signature(sample_message) is False


class TestMessagePublish:
    def test_publish_priority(self, message_bus, mock_redis, sample_message):
        mock_redis.xadd.return_value = "123-0"
        msg_id = message_bus.publish(sample_message)
        assert msg_id == "123-0"
        call_args = mock_redis.xadd.call_args
        assert call_args[0][0] == "waooaw:messages:p3"
    
    def test_publish_broadcast(self, message_bus, mock_redis):
        msg = Message(
            routing=MessageRouting(from_agent="test", to_agents=["*"], topic="broadcast"),
            payload=MessagePayload(subject="Test", action="test", priority=5)
        )
        mock_redis.xadd.return_value = "123-0"
        message_bus.publish(msg)
        call_args = mock_redis.xadd.call_args
        assert call_args[0][0] == "waooaw:broadcast"
    
    def test_publish_topic_routing(self, message_bus, mock_redis, sample_message):
        mock_redis.xadd.return_value = "123-0"
        message_bus.publish(sample_message, use_topic_routing=True)
        call_args = mock_redis.xadd.call_args
        assert call_args[0][0] == "waooaw:topics:vision.test"


class TestMessageSubscribe:
    def test_subscribe_success(self, message_bus_no_sig, mock_redis):
        mock_redis.xgroup_create.side_effect = ResponseError("BUSYGROUP")
        mock_redis.xreadgroup.return_value = [[
            "waooaw:messages:p3",
            [["123-0", {
                "routing": json.dumps({"from_agent": "test", "to_agents": ["dest"], "topic": "test"}),
                "payload": json.dumps({"subject": "Test", "action": "test", "priority": 3, "data": {}}),
                "metadata": json.dumps({"message_id": "msg-" + "a" * 32, "timestamp": time.time(), "ttl": 0, "retry_count": 0, "tags": [], "signature": None, "signature_algo": "hmac-sha256"}),
                "audit": json.dumps({})
            }]]
        ]]
        
        messages = message_bus_no_sig.subscribe("cg_test", "test_001")
        assert len(messages) == 1
        assert messages[0].routing.from_agent == "test"
    
    def test_subscribe_no_messages(self, message_bus_no_sig, mock_redis):
        mock_redis.xgroup_create.side_effect = ResponseError("BUSYGROUP")
        mock_redis.xreadgroup.return_value = []
        messages = message_bus_no_sig.subscribe("cg_test", "test_001")
        assert len(messages) == 0


class TestMessageAcknowledge:
    def test_acknowledge_success(self, message_bus, mock_redis, sample_message):
        sample_message.metadata.tags.append("stream_id:waooaw:messages:p3:123-0")
        mock_redis.xack.return_value = 1
        assert message_bus.acknowledge(sample_message) is True
    
    def test_acknowledge_no_stream_tag(self, message_bus, sample_message):
        assert message_bus.acknowledge(sample_message) is False


class TestUtilityMethods:
    def test_get_pending_count(self, message_bus, mock_redis):
        mock_redis.xpending.return_value = {"pending": 42}
        count = message_bus.get_pending_count("cg_test", "stream")
        assert count == 42
    
    def test_close(self, message_bus, mock_redis):
        message_bus.close()
        mock_redis.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=waooaw.messaging", "--cov-report=term"])
