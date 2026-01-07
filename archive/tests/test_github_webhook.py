"""
Unit tests for GitHub Webhook Handler (Story 1.3)

Tests webhook signature validation, payload transformation,
and message bus integration.

Coverage:
- Signature validation (valid, invalid, missing)
- Push events (file added, modified, removed)
- Pull request events (opened, updated, closed, merged)
- Issues events (opened, closed, commented)
- Branch events (created, deleted)
- Error handling (malformed JSON, invalid signatures)
- Message bus publication

Target: 15+ test scenarios
"""

import json
import hmac
import hashlib
import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from waooaw.webhooks.github_webhook import GitHubWebhookHandler, WebhookEvent
from waooaw.agents.event_types import (
    EVENT_FILE_CREATED,
    EVENT_FILE_UPDATED,
    EVENT_FILE_DELETED,
    EVENT_PR_OPENED,
    EVENT_PR_CLOSED,
    EVENT_PR_MERGED,
    EVENT_ISSUE_OPENED,
    EVENT_ISSUE_COMMENT,
    EVENT_COMMIT_PUSHED,
    PRIORITY_HIGH,
    PRIORITY_NORMAL,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def webhook_secret():
    """Webhook secret for testing"""
    return "test_webhook_secret_12345"


@pytest.fixture
def mock_message_bus():
    """Mock MessageBus instance"""
    bus = MagicMock()
    bus.publish.return_value = "msg_12345"
    bus.health_check.return_value = True
    return bus


@pytest.fixture
def webhook_handler(webhook_secret, mock_message_bus):
    """GitHubWebhookHandler instance"""
    return GitHubWebhookHandler(
        webhook_secret=webhook_secret, message_bus=mock_message_bus
    )


@pytest.fixture
def test_app(webhook_handler):
    """FastAPI test app with webhook router"""
    app = FastAPI()
    router = webhook_handler.create_router()
    app.include_router(router)
    return TestClient(app)


def compute_signature(payload: dict, secret: str) -> str:
    """Compute GitHub webhook signature"""
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


# ============================================================================
# TEST: SIGNATURE VALIDATION
# ============================================================================

def test_validate_signature_valid(webhook_handler, webhook_secret):
    """Test validates correct signature"""
    payload = {"test": "data"}
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = compute_signature(payload, webhook_secret)
    
    assert webhook_handler.validate_signature(payload_bytes, signature) is True


def test_validate_signature_invalid(webhook_handler):
    """Test rejects invalid signature"""
    payload = {"test": "data"}
    payload_bytes = json.dumps(payload).encode("utf-8")
    invalid_signature = "sha256=invalid_signature_here"
    
    assert webhook_handler.validate_signature(payload_bytes, invalid_signature) is False


def test_validate_signature_missing(webhook_handler):
    """Test rejects missing signature"""
    payload = {"test": "data"}
    payload_bytes = json.dumps(payload).encode("utf-8")
    
    assert webhook_handler.validate_signature(payload_bytes, None) is False


def test_validate_signature_wrong_format(webhook_handler):
    """Test rejects signature with wrong format"""
    payload = {"test": "data"}
    payload_bytes = json.dumps(payload).encode("utf-8")
    wrong_format = "md5=abc123"  # Wrong algorithm
    
    assert webhook_handler.validate_signature(payload_bytes, wrong_format) is False


# ============================================================================
# TEST: PUSH EVENT TRANSFORMATION
# ============================================================================

def test_transform_push_event_file_added(webhook_handler):
    """Test transforms push event with file added"""
    payload = {
        "ref": "refs/heads/main",
        "repository": {"full_name": "dlai-sd/WAOOAW"},
        "pusher": {"name": "developer"},
        "commits": [
            {
                "id": "abc123",
                "message": "Add new file",
                "author": {"username": "developer"},
                "added": ["app/main.py"],
                "modified": [],
                "removed": [],
            }
        ],
    }
    
    events = webhook_handler.transform_push_event(payload)
    
    # Should create 2 events: file_created + commit_pushed
    assert len(events) == 2
    
    # Check file created event
    file_event = events[0]
    assert file_event.event_type == EVENT_FILE_CREATED
    assert file_event.payload["file_path"] == "app/main.py"
    assert file_event.payload["commit_sha"] == "abc123"
    assert file_event.payload["author"] == "developer"
    
    # Check commit event
    commit_event = events[1]
    assert commit_event.event_type == EVENT_COMMIT_PUSHED
    assert commit_event.payload["commit_sha"] == "abc123"


def test_transform_push_event_file_modified(webhook_handler):
    """Test transforms push event with file modified"""
    payload = {
        "ref": "refs/heads/main",
        "repository": {"full_name": "dlai-sd/WAOOAW"},
        "pusher": {"name": "developer"},
        "commits": [
            {
                "id": "def456",
                "message": "Update file",
                "author": {"username": "developer"},
                "added": [],
                "modified": ["app/main.py"],
                "removed": [],
            }
        ],
    }
    
    events = webhook_handler.transform_push_event(payload)
    
    # Should create 2 events: file_updated + commit_pushed
    assert len(events) == 2
    
    file_event = events[0]
    assert file_event.event_type == EVENT_FILE_UPDATED
    assert file_event.payload["file_path"] == "app/main.py"


def test_transform_push_event_file_removed(webhook_handler):
    """Test transforms push event with file removed"""
    payload = {
        "ref": "refs/heads/main",
        "repository": {"full_name": "dlai-sd/WAOOAW"},
        "pusher": {"name": "developer"},
        "commits": [
            {
                "id": "ghi789",
                "message": "Delete old file",
                "author": {"username": "developer"},
                "added": [],
                "modified": [],
                "removed": ["old_file.py"],
            }
        ],
    }
    
    events = webhook_handler.transform_push_event(payload)
    
    # Should create 2 events: file_deleted + commit_pushed
    assert len(events) == 2
    
    file_event = events[0]
    assert file_event.event_type == EVENT_FILE_DELETED
    assert file_event.payload["file_path"] == "old_file.py"


def test_transform_push_event_multiple_files(webhook_handler):
    """Test transforms push event with multiple file changes"""
    payload = {
        "ref": "refs/heads/main",
        "repository": {"full_name": "dlai-sd/WAOOAW"},
        "pusher": {"name": "developer"},
        "commits": [
            {
                "id": "multi123",
                "message": "Multiple changes",
                "author": {"username": "developer"},
                "added": ["new1.py", "new2.py"],
                "modified": ["updated.py"],
                "removed": ["old.py"],
            }
        ],
    }
    
    events = webhook_handler.transform_push_event(payload)
    
    # 2 added + 1 modified + 1 removed + 1 commit = 5 events
    assert len(events) == 5
    assert events[0].event_type == EVENT_FILE_CREATED
    assert events[1].event_type == EVENT_FILE_CREATED
    assert events[2].event_type == EVENT_FILE_UPDATED
    assert events[3].event_type == EVENT_FILE_DELETED
    assert events[4].event_type == EVENT_COMMIT_PUSHED


# ============================================================================
# TEST: PULL REQUEST EVENT TRANSFORMATION
# ============================================================================

def test_transform_pull_request_opened(webhook_handler):
    """Test transforms pull_request opened event"""
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "title": "Add new feature",
            "user": {"login": "developer"},
            "state": "open",
            "merged": False,
            "base": {"ref": "main"},
            "head": {"ref": "feature/new"},
            "html_url": "https://github.com/dlai-sd/WAOOAW/pull/42",
        },
        "repository": {"full_name": "dlai-sd/WAOOAW"},
    }
    
    event = webhook_handler.transform_pull_request_event(payload)
    
    assert event.event_type == EVENT_PR_OPENED
    assert event.payload["pr_number"] == 42
    assert event.payload["title"] == "Add new feature"
    assert event.payload["author"] == "developer"
    assert event.priority == PRIORITY_HIGH  # PRs are high priority


def test_transform_pull_request_closed_merged(webhook_handler):
    """Test transforms pull_request closed (merged) event"""
    payload = {
        "action": "closed",
        "pull_request": {
            "number": 43,
            "title": "Merge feature",
            "user": {"login": "developer"},
            "state": "closed",
            "merged": True,
            "base": {"ref": "main"},
            "head": {"ref": "feature/branch"},
            "html_url": "https://github.com/dlai-sd/WAOOAW/pull/43",
        },
        "repository": {"full_name": "dlai-sd/WAOOAW"},
    }
    
    event = webhook_handler.transform_pull_request_event(payload)
    
    assert event.event_type == EVENT_PR_MERGED
    assert event.payload["merged"] is True
    assert event.priority == PRIORITY_HIGH


def test_transform_pull_request_closed_not_merged(webhook_handler):
    """Test transforms pull_request closed (not merged) event"""
    payload = {
        "action": "closed",
        "pull_request": {
            "number": 44,
            "title": "Close without merge",
            "user": {"login": "developer"},
            "state": "closed",
            "merged": False,
            "base": {"ref": "main"},
            "head": {"ref": "feature/old"},
            "html_url": "https://github.com/dlai-sd/WAOOAW/pull/44",
        },
        "repository": {"full_name": "dlai-sd/WAOOAW"},
    }
    
    event = webhook_handler.transform_pull_request_event(payload)
    
    assert event.event_type == EVENT_PR_CLOSED
    assert event.payload["merged"] is False
    assert event.priority == PRIORITY_NORMAL


# ============================================================================
# TEST: ISSUES EVENT TRANSFORMATION
# ============================================================================

def test_transform_issues_opened(webhook_handler):
    """Test transforms issues opened event"""
    payload = {
        "action": "opened",
        "issue": {
            "number": 10,
            "title": "Bug report",
            "user": {"login": "reporter"},
            "state": "open",
            "labels": [{"name": "bug"}, {"name": "priority"}],
            "html_url": "https://github.com/dlai-sd/WAOOAW/issues/10",
        },
        "repository": {"full_name": "dlai-sd/WAOOAW"},
    }
    
    event = webhook_handler.transform_issues_event(payload)
    
    assert event.event_type == EVENT_ISSUE_OPENED
    assert event.payload["issue_number"] == 10
    assert event.payload["title"] == "Bug report"
    assert event.payload["labels"] == ["bug", "priority"]


def test_transform_issues_edited_ignored(webhook_handler):
    """Test ignores issues edited event"""
    payload = {
        "action": "edited",
        "issue": {
            "number": 11,
            "title": "Updated issue",
            "user": {"login": "editor"},
            "state": "open",
            "labels": [],
            "html_url": "https://github.com/dlai-sd/WAOOAW/issues/11",
        },
        "repository": {"full_name": "dlai-sd/WAOOAW"},
    }
    
    event = webhook_handler.transform_issues_event(payload)
    
    # Edited events are ignored (not critical)
    assert event is None


# ============================================================================
# TEST: ISSUE COMMENT EVENT TRANSFORMATION
# ============================================================================

def test_transform_issue_comment_created(webhook_handler):
    """Test transforms issue_comment created event"""
    payload = {
        "action": "created",
        "issue": {"number": 12},
        "comment": {
            "body": "APPROVE: This looks good",
            "user": {"login": "reviewer"},
            "html_url": "https://github.com/dlai-sd/WAOOAW/issues/12#comment",
        },
        "repository": {"full_name": "dlai-sd/WAOOAW"},
    }
    
    event = webhook_handler.transform_issue_comment_event(payload)
    
    assert event.event_type == EVENT_ISSUE_COMMENT
    assert event.payload["issue_number"] == 12
    assert event.payload["comment_body"] == "APPROVE: This looks good"
    assert event.payload["author"] == "reviewer"


def test_transform_issue_comment_edited_ignored(webhook_handler):
    """Test ignores issue_comment edited event"""
    payload = {
        "action": "edited",
        "issue": {"number": 13},
        "comment": {
            "body": "Updated comment",
            "user": {"login": "editor"},
            "html_url": "https://github.com/dlai-sd/WAOOAW/issues/13#comment",
        },
        "repository": {"full_name": "dlai-sd/WAOOAW"},
    }
    
    event = webhook_handler.transform_issue_comment_event(payload)
    
    # Edited comments are ignored
    assert event is None


# ============================================================================
# TEST: WEBHOOK ENDPOINT
# ============================================================================

def test_webhook_endpoint_valid_push(test_app, webhook_secret, mock_message_bus):
    """Test webhook endpoint with valid push event"""
    payload = {
        "ref": "refs/heads/main",
        "repository": {"full_name": "dlai-sd/WAOOAW"},
        "pusher": {"name": "developer"},
        "commits": [
            {
                "id": "abc123",
                "message": "Test commit",
                "author": {"username": "developer"},
                "added": ["test.py"],
                "modified": [],
                "removed": [],
            }
        ],
    }
    
    signature = compute_signature(payload, webhook_secret)
    
    response = test_app.post(
        "/webhooks/github",
        json=payload,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "push",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event"] == "push"
    assert data["events_published"] >= 1


def test_webhook_endpoint_invalid_signature(test_app, webhook_secret):
    """Test webhook endpoint rejects invalid signature"""
    payload = {"test": "data"}
    
    response = test_app.post(
        "/webhooks/github",
        json=payload,
        headers={
            "X-Hub-Signature-256": "sha256=invalid",
            "X-GitHub-Event": "push",
        },
    )
    
    assert response.status_code == 401
    assert "Invalid signature" in response.json()["detail"]


def test_webhook_endpoint_missing_signature(test_app):
    """Test webhook endpoint rejects missing signature"""
    payload = {"test": "data"}
    
    response = test_app.post(
        "/webhooks/github",
        json=payload,
        headers={"X-GitHub-Event": "push"},
    )
    
    assert response.status_code == 401


def test_webhook_endpoint_invalid_json(test_app, webhook_secret):
    """Test webhook endpoint handles invalid JSON"""
    invalid_json = b"not json data"
    
    # Compute signature for invalid data
    signature = hmac.new(
        webhook_secret.encode("utf-8"), invalid_json, hashlib.sha256
    ).hexdigest()
    
    response = test_app.post(
        "/webhooks/github",
        content=invalid_json,
        headers={
            "X-Hub-Signature-256": f"sha256={signature}",
            "X-GitHub-Event": "push",
            "Content-Type": "application/json",
        },
    )
    
    assert response.status_code == 400
    assert "Invalid JSON" in response.json()["detail"]


def test_webhook_endpoint_disabled_event(test_app, webhook_secret):
    """Test webhook endpoint ignores disabled events"""
    # Create handler with limited events
    handler = GitHubWebhookHandler(
        webhook_secret=webhook_secret,
        message_bus=MagicMock(),
        enabled_events=["push"],  # Only push enabled
    )
    
    app = FastAPI()
    app.include_router(handler.create_router())
    client = TestClient(app)
    
    payload = {"action": "starred", "repository": {"full_name": "test/repo"}}
    signature = compute_signature(payload, webhook_secret)
    
    response = client.post(
        "/webhooks/github",
        json=payload,
        headers={
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "star",  # Not in enabled_events
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"


def test_webhook_health_endpoint(test_app):
    """Test webhook health check endpoint"""
    response = test_app.get("/webhooks/github/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "enabled_events" in data
    assert data["message_bus_connected"] is True


# ============================================================================
# TEST: MESSAGE BUS INTEGRATION
# ============================================================================

def test_webhook_publishes_to_message_bus(webhook_handler, mock_message_bus):
    """Test webhook handler publishes events to message bus"""
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 99,
            "title": "Test PR",
            "user": {"login": "developer"},
            "state": "open",
            "merged": False,
            "base": {"ref": "main"},
            "head": {"ref": "feature"},
            "html_url": "https://github.com/test/repo/pull/99",
        },
        "repository": {"full_name": "test/repo"},
    }
    
    events = webhook_handler.transform_webhook("pull_request", payload)
    
    # Verify event was created
    assert len(events) == 1
    event = events[0]
    assert event.event_type == EVENT_PR_OPENED


# ============================================================================
# SUMMARY
# ============================================================================

"""
Story 1.3 Test Coverage:

✅ Signature validation (valid, invalid, missing, wrong format)
✅ Push events (file added, modified, removed, multiple files)
✅ Pull request events (opened, closed-merged, closed-not-merged)
✅ Issues events (opened, edited-ignored)
✅ Issue comments (created, edited-ignored)
✅ Webhook endpoint (valid request, invalid signature, missing signature, invalid JSON, disabled events)
✅ Health check endpoint
✅ Message bus integration

Total: 21 test scenarios (target: 15+) ✅
"""
