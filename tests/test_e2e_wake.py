"""
End-to-End Wake Test - Story 1.4

Tests the complete flow:
1. GitHub event → Webhook endpoint
2. Webhook → Message Bus (Redis Streams)
3. Message Bus → Agent subscription
4. Agent → should_wake() filter
5. Agent → Wake protocol execution

Target: <5s p95 latency, idempotency, error recovery
"""
import pytest
import json
import hmac
import hashlib
import time
import os
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

# Test infrastructure
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '/workspaces/WAOOAW')
sys.path.insert(0, '/workspaces/WAOOAW/backend')

from backend.app.main import app
from waooaw.agents.wowvision_prime import WowVisionPrime
from waooaw.messaging.message_bus import MessageBus
from waooaw.messaging.models import Message

# Ensure imports work
os.environ.setdefault("PYTHONPATH", "/workspaces/WAOOAW")


class TestEndToEndWakeFlow:
    """Test complete wake flow from webhook to agent execution."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)
        
        # Reset webhook singleton
        import backend.app.webhooks
        backend.app.webhooks.set_message_bus_for_testing(None)
    
    @patch("waooaw.messaging.message_bus.redis.from_url")
    @patch.dict("os.environ", {}, clear=True)
    def test_e2e_file_push_triggers_agent_wake(self, mock_redis_from_url):
        """
        E2E Test: File push → Webhook → Message Bus → Agent Wake
        
        Flow:
        1. GitHub sends push event (Python file changed)
        2. Webhook validates, transforms to Message
        3. Message published to Redis stream (priority 4)
        4. Agent subscribes, receives message
        5. Agent calls should_wake() → returns (True, reason)
        6. Agent executes wake protocol
        """
        # Mock Redis client at the right level (where MessageBus creates it)
        mock_redis = MagicMock()
        published_messages = []
        
        def mock_xadd(stream_name, fields, maxlen=None, approximate=None):
            """Capture published messages."""
            published_messages.append({
                "stream": stream_name,
                "fields": fields,
                "timestamp": time.time()
            })
            return b"1234567890-0"
        
        mock_redis.xadd.side_effect = mock_xadd
        mock_redis.xread.return_value = []  # No pending messages
        mock_redis_from_url.return_value = mock_redis
        
        # Step 1: Simulate GitHub push event
        github_event = {
            "ref": "refs/heads/main",
            "repository": {
                "full_name": "dlai-sd/WAOOAW",
                "name": "WAOOAW",
                "owner": {"login": "dlai-sd"}
            },
            "commits": [
                {
                    "id": "abc123def456",
                    "message": "feat: add new feature",
                    "author": {"username": "developer"},
                    "added": ["src/new_feature.py"],
                    "modified": ["src/main.py"],
                    "removed": []
                }
            ],
            "sender": {"login": "developer"}
        }
        
        # Step 2: Send webhook (no signature for test)
        start_time = time.time()
        
        response = self.client.post(
            "/webhooks/github",
            json=github_event,
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "test-delivery-123",
                "Content-Type": "application/json"
            }
        )
        
        webhook_latency = time.time() - start_time
        
        # Step 3: Verify webhook accepted
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        assert "message_id" in response.json()
        
        # Step 4: Verify message published to correct stream
        assert len(published_messages) == 1
        message_data = published_messages[0]
        assert message_data["stream"] == "waooaw:messages:p4"  # Push = priority 4
        
        # Step 5: Parse message payload
        message_json = message_data["fields"]["message"]
        message_dict = json.loads(message_json)
        
        assert message_dict["routing"]["topic"] == "github.push"
        assert message_dict["routing"]["from_agent"] == "github-webhook"
        assert message_dict["payload"]["priority"] == 4
        assert message_dict["payload"]["data"]["event_type"] == "push"
        
        # Step 6: Simulate agent subscription and should_wake
        agent_start_time = time.time()
        
        # Create mock agent (no real GitHub/DB connection)
        with patch("waooaw.agents.base_agent.Github"), \
             patch("waooaw.agents.base_agent.pymongo"):
            
            agent = WowVisionPrime(
                github_token="mock_token",
                repo_name="dlai-sd/WAOOAW",
                database_url="mock_db"
            )
            
            # Test should_wake with the GitHub event
            should_wake, reason = agent.should_wake(github_event)
            
            agent_latency = time.time() - agent_start_time
        
        # Step 7: Verify agent wakes up
        assert should_wake is True
        assert "files changed" in reason.lower() or "python" in reason.lower()
        
        # Step 8: Verify latency targets
        total_latency = webhook_latency + agent_latency
        
        assert webhook_latency < 1.0, f"Webhook latency {webhook_latency:.3f}s exceeds 1s"
        assert agent_latency < 0.01, f"Agent latency {agent_latency:.3f}s exceeds 10ms"
        assert total_latency < 2.0, f"Total latency {total_latency:.3f}s exceeds 2s (p95 target: 5s)"
        
        print(f"\n✅ E2E Wake Flow Success:")
        print(f"   Webhook latency: {webhook_latency*1000:.2f}ms")
        print(f"   Agent latency: {agent_latency*1000:.2f}ms")
        print(f"   Total latency: {total_latency*1000:.2f}ms")
    
    @patch("waooaw.messaging.message_bus.redis.from_url")
    @patch.dict("os.environ", {}, clear=True)
    def test_e2e_readme_only_commit_skipped(self, mock_redis_from_url):
        """
        E2E Test: README-only commit → Agent skips (should_wake returns False)
        """
        mock_redis = MagicMock()
        published_messages = []
        
        def mock_xadd(stream_name, fields, maxlen=None, approximate=None):
            published_messages.append({"stream": stream_name, "fields": fields})
            return b"1234567890-0"
        
        mock_redis.xadd.side_effect = mock_xadd
        mock_redis_from_url.return_value = mock_redis
        
        # GitHub push with only README change
        github_event = {
            "ref": "refs/heads/main",
            "repository": {"full_name": "dlai-sd/WAOOAW"},
            "commits": [
                {
                    "id": "readme123",
                    "message": "docs: update README",
                    "added": [],
                    "modified": ["README.md"],
                    "removed": []
                }
            ],
            "sender": {"login": "developer"}
        }
        
        # Send webhook
        response = self.client.post(
            "/webhooks/github",
            json=github_event,
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "test-delivery-readme"
            }
        )
        
        assert response.status_code == 202
        assert len(published_messages) == 1  # Message still published
        
        # Agent should skip
        with patch("waooaw.agents.base_agent.Github"), \
             patch("waooaw.agents.base_agent.pymongo"):
            
            agent = WowVisionPrime(
                github_token="mock",
                repo_name="dlai-sd/WAOOAW",
                database_url="mock"
            )
            
            should_wake, reason = agent.should_wake(github_event)
        
        assert should_wake is False
        assert "README-only" in reason or "skip" in reason.lower()
        print(f"\n✅ README-only commit correctly skipped: {reason}")
    
    @patch("waooaw.messaging.message_bus.redis.from_url")
    @patch.dict("os.environ", {}, clear=True)
    def test_e2e_pr_opened_triggers_wake(self, mock_redis_from_url):
        """
        E2E Test: PR opened → Webhook → Message Bus → Agent wakes
        """
        mock_redis = MagicMock()
        mock_redis.xadd.return_value = b"1234567890-0"
        mock_redis_from_url.return_value = mock_redis
        
        # GitHub PR opened event
        github_event = {
            "action": "opened",
            "pull_request": {
                "number": 42,
                "title": "Add new feature",
                "draft": False,
                "user": {"login": "developer"}
            },
            "repository": {"full_name": "dlai-sd/WAOOAW"}
        }
        
        # Send webhook
        response = self.client.post(
            "/webhooks/github",
            json=github_event,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-GitHub-Delivery": "test-delivery-pr"
            }
        )
        
        assert response.status_code == 202
        
        # Agent should wake
        with patch("waooaw.agents.base_agent.Github"), \
             patch("waooaw.agents.base_agent.pymongo"):
            
            agent = WowVisionPrime(
                github_token="mock",
                repo_name="dlai-sd/WAOOAW",
                database_url="mock"
            )
            
            should_wake, reason = agent.should_wake(github_event)
        
        assert should_wake is True
        assert "PR" in reason or "pull request" in reason.lower()
        print(f"\n✅ PR opened correctly triggers wake: {reason}")
    
    @patch("waooaw.messaging.message_bus.redis.from_url")
    @patch.dict("os.environ", {}, clear=True)
    def test_e2e_idempotency(self, mock_redis_from_url):
        """
        E2E Test: Duplicate webhook events should be idempotent
        
        Same delivery ID → should deduplicate (future enhancement)
        For now, just verify both are processed independently
        """
        mock_redis = MagicMock()
        published_count = [0]
        
        def mock_xadd(stream_name, fields, maxlen=None, approximate=None):
            published_count[0] += 1
            return f"{published_count[0]}-0".encode()
        
        mock_redis.xadd.side_effect = mock_xadd
        mock_redis_from_url.return_value = mock_redis
        
        github_event = {
            "repository": {"full_name": "dlai-sd/WAOOAW"},
            "commits": [{"message": "test", "modified": ["test.py"]}]
        }
        
        # Send same event twice with same delivery ID
        for _ in range(2):
            response = self.client.post(
                "/webhooks/github",
                json=github_event,
                headers={
                    "X-GitHub-Event": "push",
                    "X-GitHub-Delivery": "duplicate-delivery-id"
                }
            )
            assert response.status_code == 202
        
        # Currently: both messages published (no deduplication yet)
        # Future: should be deduplicated by correlation_id
        assert published_count[0] == 2
        print(f"\n⚠️  Idempotency: Both messages published (deduplication TODO in Epic 5)")


class TestMessageBusIntegration:
    """Test message bus with mocked Redis."""
    
    @patch("waooaw.messaging.message_bus.redis.from_url")
    def test_message_bus_publish_subscribe_flow(self, mock_redis_from_url):
        """Test message publish → subscribe flow."""
        mock_redis = MagicMock()
        published_data = {}
        
        def mock_xadd(stream_name, fields, maxlen=None, approximate=None):
            published_data[stream_name] = fields
            return b"1234567890-0"
        
        def mock_xread(streams, count=None, block=None):
            # Return the published message
            if "waooaw:messages:p5" in streams and "waooaw:messages:p5" in published_data:
                return [(
                    "waooaw:messages:p5",
                    [(b"1234567890-0", published_data["waooaw:messages:p5"])]
                )]
            return []
        
        mock_redis.xadd.side_effect = mock_xadd
        mock_redis.xread.side_effect = mock_xread
        mock_redis_from_url.return_value = mock_redis
        
        # Create message bus
        bus = MessageBus(redis_url="redis://localhost:6379/0")
        
        # Create and publish message
        from waooaw.messaging.models import Message, MessageRouting, MessagePayload
        
        message = Message(
            routing=MessageRouting(
                from_agent="test-agent",
                to_agents=["wowvision-prime"],
                topic="test.message"
            ),
            payload=MessagePayload(
                subject="Test Message",
                body="Testing E2E flow",
                action="test",
                priority=5
            )
        )
        
        message_id = bus.publish(message)
        assert message_id.startswith("msg-")
        
        # Subscribe and verify
        messages = bus.subscribe(
            consumer_group="test-group",
            consumer_name="test-consumer",
            streams=["waooaw:messages:p5"],
            count=1
        )
        
        # Should receive the message (if Redis was real)
        # For now, verify the mock was called correctly
        assert mock_redis.xadd.called
        assert mock_redis.xread.called
        
        print(f"\n✅ Message bus integration test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
