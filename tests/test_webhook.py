"""
Unit Tests for GitHub Webhook Integration - Story 1.3

Tests webhook endpoint, HMAC validation, and event transformation.
Target: 95%+ coverage, all security scenarios covered.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import json
import hashlib
import hmac
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Import from correct location
import sys
sys.path.insert(0, '/workspaces/WAOOAW')
sys.path.insert(0, '/workspaces/WAOOAW/backend')

from backend.app.main import app
from backend.app.webhooks import verify_github_signature, transform_github_event_to_message

client = TestClient(app)


class TestGitHubSignatureVerification:
    """Test HMAC-SHA256 signature verification."""
    
    def test_valid_signature(self):
        """Should accept valid GitHub signature."""
        secret = "my_webhook_secret"
        payload = b'{"test": "data"}'
        
        # Compute valid signature
        signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        assert verify_github_signature(payload, signature, secret) is True
    
    def test_invalid_signature(self):
        """Should reject invalid signature."""
        secret = "my_webhook_secret"
        payload = b'{"test": "data"}'
        signature = "sha256=" + "0" * 64
        
        assert verify_github_signature(payload, signature, secret) is False
    
    def test_missing_signature(self):
        """Should raise error for missing signature."""
        with pytest.raises(ValueError, match="Missing signature"):
            verify_github_signature(b"data", "", "secret")
    
    def test_invalid_signature_format(self):
        """Should raise error for invalid format."""
        with pytest.raises(ValueError, match="Invalid signature format"):
            verify_github_signature(b"data", "invalid_format", "secret")


class TestEventTransformation:
    """Test GitHub event to MessageBus message transformation."""
    
    def test_push_event_transformation(self):
        """Should transform push event correctly."""
        event_data = {
            "repository": {"full_name": "test/repo"},
            "commits": [{"id": "abc123", "message": "test commit"}],
            "sender": {"login": "testuser"}
        }
        
        message = transform_github_event_to_message(
            event_type="push",
            event_data=event_data,
            delivery_id="12345"
        )
        
        assert message.routing.topic == "github.push"
        assert message.routing.from_agent == "github-webhook"
        assert message.routing.to_agents == ["*"]
        assert message.routing.correlation_id == "12345"
        assert message.payload.priority == 4  # High priority
        assert message.payload.data["event_type"] == "push"
        assert "source:github" in message.metadata.tags
        assert "event:push" in message.metadata.tags
    
    def test_pull_request_event_transformation(self):
        """Should transform PR event correctly."""
        event_data = {
            "repository": {"full_name": "test/repo"},
            "pull_request": {"number": 42, "title": "Test PR"},
            "action": "opened"
        }
        
        message = transform_github_event_to_message(
            event_type="pull_request",
            event_data=event_data,
            delivery_id="67890"
        )
        
        assert message.routing.topic == "github.pull_request"
        assert message.payload.priority == 4  # High priority
        assert message.payload.data["event_type"] == "pull_request"
    
    def test_low_priority_event_transformation(self):
        """Should assign low priority to star events."""
        event_data = {
            "repository": {"full_name": "test/repo"},
            "action": "created"
        }
        
        message = transform_github_event_to_message(
            event_type="star",
            event_data=event_data,
            delivery_id="11111"
        )
        
        assert message.payload.priority == 1  # Bulk priority


class TestWebhookEndpoint:
    """Test /webhooks/github endpoint."""
    
    def setup_method(self):
        """Reset message bus singleton before each test."""
        import backend.app.webhooks
        backend.app.webhooks.set_message_bus_for_testing(None)
    
    @patch.dict("os.environ", {}, clear=True)  # No webhook secret
    @patch("redis.Redis")
    def test_webhook_without_signature(self, mock_redis_class):
        """Should accept webhook without signature if secret not configured."""
        # Mock Redis client to avoid connection
        mock_redis = MagicMock()
        mock_redis.xadd.return_value = b"1234567890-0"  # Redis stream ID
        mock_redis_class.from_url.return_value = mock_redis
        
        event_data = {"repository": {"full_name": "test/repo"}}
        
        response = client.post(
            "/webhooks/github",
            json=event_data,
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "12345"
            }
        )
        
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        assert response.json()["event_type"] == "push"
        assert "message_id" in response.json()
    
    @patch.dict("os.environ", {"GITHUB_WEBHOOK_SECRET": "test_secret"})
    @patch("redis.Redis")
    def test_webhook_with_valid_signature(self, mock_redis_class):
        """Should accept webhook with valid signature."""
        # Mock Redis client
        mock_redis = MagicMock()
        mock_redis.xadd.return_value = b"1234567890-0"
        mock_redis_class.from_url.return_value = mock_redis
        
        event_data = {"repository": {"full_name": "test/repo"}}
        payload = json.dumps(event_data).encode()
        
        # Compute valid signature
        signature = "sha256=" + hmac.new(
            b"test_secret",
            payload,
            hashlib.sha256
        ).hexdigest()
        
        response = client.post(
            "/webhooks/github",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "12345",
                "X-Hub-Signature-256": signature
            }
        )
        
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
    
    @patch.dict("os.environ", {"GITHUB_WEBHOOK_SECRET": "test_secret"})
    def test_webhook_with_invalid_signature(self):
        """Should reject webhook with invalid signature."""
        event_data = {"repository": {"full_name": "test/repo"}}
        
        response = client.post(
            "/webhooks/github",
            json=event_data,
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "12345",
                "X-Hub-Signature-256": "sha256=" + "0" * 64
            }
        )
        
        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]
    
    @patch.dict("os.environ", {"GITHUB_WEBHOOK_SECRET": "test_secret"})
    def test_webhook_with_missing_signature(self):
        """Should reject webhook when secret configured but signature missing."""
        event_data = {"repository": {"full_name": "test/repo"}}
        
        response = client.post(
            "/webhooks/github",
            json=event_data,
            headers={
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "12345"
            }
        )
        
        assert response.status_code == 401
        assert "Missing signature" in response.json()["detail"]
    
    def test_webhook_with_invalid_json(self):
        """Should reject invalid JSON payload."""
        response = client.post(
            "/webhooks/github",
            content=b"invalid json {",
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": "push",
                "X-GitHub-Delivery": "12345"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["detail"]
    
    @patch("redis.Redis")
    def test_webhook_health_check(self, mock_redis_class):
        """Should return healthy status when message bus connected."""
        # Mock Redis with ping method
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.from_url.return_value = mock_redis
        
        response = client.get("/webhooks/github/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["message_bus"] == "connected"
    
    @patch("backend.app.webhooks.get_message_bus")
    def test_webhook_health_check_failure(self, mock_bus):
        """Should return 503 when message bus unavailable."""
        mock_bus.side_effect = Exception("Redis connection failed")
        
        response = client.get("/webhooks/github/health")
        
        assert response.status_code == 503
        assert "Message bus unavailable" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
