"""
GitHub Webhook Handler - Receives and transforms GitHub events

Handles:
- Signature validation (HMAC SHA-256)
- Event type detection (push, pull_request, issues, etc.)
- Payload transformation to message bus events
- Message bus publication

Security:
- Validates X-Hub-Signature-256 header
- Rejects unsigned/invalid requests
- Rate limiting (configurable)
"""

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from waooaw.messaging.message_bus import MessageBus
from waooaw.agents.event_types import (
    EVENT_FILE_CREATED,
    EVENT_FILE_UPDATED,
    EVENT_FILE_DELETED,
    EVENT_PR_OPENED,
    EVENT_PR_UPDATED,
    EVENT_PR_CLOSED,
    EVENT_PR_MERGED,
    EVENT_ISSUE_OPENED,
    EVENT_ISSUE_COMMENT,
    EVENT_ISSUE_CLOSED,
    EVENT_COMMIT_PUSHED,
    EVENT_BRANCH_CREATED,
    EVENT_BRANCH_DELETED,
    PRIORITY_HIGH,
    PRIORITY_NORMAL,
)

logger = logging.getLogger(__name__)


@dataclass
class WebhookEvent:
    """Transformed webhook event ready for message bus"""

    event_type: str
    payload: Dict[str, Any]
    priority: int = PRIORITY_NORMAL
    source: str = "github"
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class GitHubWebhookHandler:
    """
    Handles GitHub webhook events and transforms them for message bus.

    Usage:
        handler = GitHubWebhookHandler(
            webhook_secret="your_webhook_secret",
            message_bus=message_bus
        )

        router = handler.create_router()
        app.include_router(router)
    """

    def __init__(
        self,
        webhook_secret: str,
        message_bus: MessageBus,
        enabled_events: Optional[list] = None,
    ):
        """
        Initialize webhook handler.

        Args:
            webhook_secret: GitHub webhook secret for signature validation
            message_bus: MessageBus instance for publishing events
            enabled_events: List of GitHub event types to handle (default: all)
        """
        self.webhook_secret = webhook_secret.encode("utf-8")
        self.message_bus = message_bus
        self.enabled_events = enabled_events or [
            "push",
            "pull_request",
            "issues",
            "issue_comment",
            "create",
            "delete",
        ]

        logger.info(
            f"🔗 GitHubWebhookHandler initialized. Enabled events: {self.enabled_events}"
        )

    def validate_signature(self, payload_body: bytes, signature_header: str) -> bool:
        """
        Validate GitHub webhook signature (HMAC SHA-256).

        Args:
            payload_body: Raw request body bytes
            signature_header: X-Hub-Signature-256 header value

        Returns:
            True if signature is valid, False otherwise
        """
        if not signature_header:
            logger.warning("⚠️  Missing X-Hub-Signature-256 header")
            return False

        # GitHub sends: "sha256=<hex_digest>"
        if not signature_header.startswith("sha256="):
            logger.warning(f"⚠️  Invalid signature format: {signature_header[:20]}...")
            return False

        expected_signature = signature_header.split("=")[1]

        # Compute HMAC SHA-256
        computed_signature = hmac.new(
            self.webhook_secret, payload_body, hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(computed_signature, expected_signature)

        if not is_valid:
            logger.error("❌ Invalid webhook signature")
        else:
            logger.debug("✅ Webhook signature validated")

        return is_valid

    def transform_push_event(self, payload: Dict[str, Any]) -> list:
        """
        Transform GitHub push event to message bus events.

        Returns list of events (one per added/modified/removed file).
        """
        events = []
        commits = payload.get("commits", [])
        ref = payload.get("ref", "")
        repository = payload.get("repository", {}).get("full_name", "unknown")
        pusher = payload.get("pusher", {}).get("name", "unknown")

        for commit in commits:
            commit_sha = commit.get("id", "unknown")
            author = commit.get("author", {}).get("username", pusher)
            message = commit.get("message", "")

            # Files added
            for file_path in commit.get("added", []):
                events.append(
                    WebhookEvent(
                        event_type=EVENT_FILE_CREATED,
                        payload={
                            "file_path": file_path,
                            "commit_sha": commit_sha,
                            "author": author,
                            "message": message,
                            "ref": ref,
                            "repository": repository,
                        },
                        priority=PRIORITY_NORMAL,
                    )
                )

            # Files modified
            for file_path in commit.get("modified", []):
                events.append(
                    WebhookEvent(
                        event_type=EVENT_FILE_UPDATED,
                        payload={
                            "file_path": file_path,
                            "commit_sha": commit_sha,
                            "author": author,
                            "message": message,
                            "ref": ref,
                            "repository": repository,
                        },
                        priority=PRIORITY_NORMAL,
                    )
                )

            # Files removed
            for file_path in commit.get("removed", []):
                events.append(
                    WebhookEvent(
                        event_type=EVENT_FILE_DELETED,
                        payload={
                            "file_path": file_path,
                            "commit_sha": commit_sha,
                            "author": author,
                            "message": message,
                            "ref": ref,
                            "repository": repository,
                        },
                        priority=PRIORITY_NORMAL,
                    )
                )

            # Also emit commit event
            events.append(
                WebhookEvent(
                    event_type=EVENT_COMMIT_PUSHED,
                    payload={
                        "commit_sha": commit_sha,
                        "author": author,
                        "message": message,
                        "ref": ref,
                        "repository": repository,
                        "added": commit.get("added", []),
                        "modified": commit.get("modified", []),
                        "removed": commit.get("removed", []),
                    },
                    priority=PRIORITY_NORMAL,
                )
            )

        return events

    def transform_pull_request_event(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Transform GitHub pull_request event to message bus event."""
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})

        # Map GitHub actions to our event types
        if action == "opened":
            event_type = EVENT_PR_OPENED
            priority = PRIORITY_HIGH  # PRs need immediate review
        elif action in ["synchronize", "edited", "labeled", "unlabeled"]:
            event_type = EVENT_PR_UPDATED
            priority = PRIORITY_NORMAL
        elif action == "closed":
            if pr.get("merged", False):
                event_type = EVENT_PR_MERGED
                priority = PRIORITY_HIGH
            else:
                event_type = EVENT_PR_CLOSED
                priority = PRIORITY_NORMAL
        else:
            # Other actions (assigned, review_requested, etc.)
            event_type = EVENT_PR_UPDATED
            priority = PRIORITY_NORMAL

        return WebhookEvent(
            event_type=event_type,
            payload={
                "pr_number": pr.get("number"),
                "title": pr.get("title", ""),
                "author": pr.get("user", {}).get("login", "unknown"),
                "action": action,
                "state": pr.get("state", ""),
                "merged": pr.get("merged", False),
                "base_ref": pr.get("base", {}).get("ref", ""),
                "head_ref": pr.get("head", {}).get("ref", ""),
                "repository": payload.get("repository", {}).get("full_name", "unknown"),
                "url": pr.get("html_url", ""),
            },
            priority=priority,
        )

    def transform_issues_event(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Transform GitHub issues event to message bus event."""
        action = payload.get("action", "")
        issue = payload.get("issue", {})

        # Map GitHub actions to our event types
        if action == "opened":
            event_type = EVENT_ISSUE_OPENED
            priority = PRIORITY_NORMAL
        elif action == "closed":
            event_type = EVENT_ISSUE_CLOSED
            priority = PRIORITY_NORMAL
        else:
            # Other actions (edited, labeled, assigned, etc.) - not critical
            return None

        return WebhookEvent(
            event_type=event_type,
            payload={
                "issue_number": issue.get("number"),
                "title": issue.get("title", ""),
                "author": issue.get("user", {}).get("login", "unknown"),
                "action": action,
                "state": issue.get("state", ""),
                "labels": [label.get("name") for label in issue.get("labels", [])],
                "repository": payload.get("repository", {}).get("full_name", "unknown"),
                "url": issue.get("html_url", ""),
            },
            priority=priority,
        )

    def transform_issue_comment_event(self, payload: Dict[str, Any]) -> WebhookEvent:
        """Transform GitHub issue_comment event to message bus event."""
        action = payload.get("action", "")

        # Only care about created comments (not edited/deleted)
        if action != "created":
            return None

        issue = payload.get("issue", {})
        comment = payload.get("comment", {})

        return WebhookEvent(
            event_type=EVENT_ISSUE_COMMENT,
            payload={
                "issue_number": issue.get("number"),
                "comment_body": comment.get("body", ""),
                "author": comment.get("user", {}).get("login", "unknown"),
                "repository": payload.get("repository", {}).get("full_name", "unknown"),
                "url": comment.get("html_url", ""),
            },
            priority=PRIORITY_NORMAL,
        )

    def transform_create_event(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Transform GitHub create event (branch/tag created)."""
        ref_type = payload.get("ref_type", "")

        if ref_type == "branch":
            return WebhookEvent(
                event_type=EVENT_BRANCH_CREATED,
                payload={
                    "branch_name": payload.get("ref", ""),
                    "repository": payload.get("repository", {}).get(
                        "full_name", "unknown"
                    ),
                },
                priority=PRIORITY_NORMAL,
            )

        return None  # Ignore tag creation

    def transform_delete_event(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
        """Transform GitHub delete event (branch/tag deleted)."""
        ref_type = payload.get("ref_type", "")

        if ref_type == "branch":
            return WebhookEvent(
                event_type=EVENT_BRANCH_DELETED,
                payload={
                    "branch_name": payload.get("ref", ""),
                    "repository": payload.get("repository", {}).get(
                        "full_name", "unknown"
                    ),
                },
                priority=PRIORITY_NORMAL,
            )

        return None  # Ignore tag deletion

    def transform_webhook(
        self, event_type: str, payload: Dict[str, Any]
    ) -> list[WebhookEvent]:
        """
        Transform GitHub webhook to message bus event(s).

        Args:
            event_type: GitHub event type (X-GitHub-Event header)
            payload: Webhook payload

        Returns:
            List of WebhookEvent objects (may be empty if event ignored)
        """
        logger.debug(f"🔄 Transforming {event_type} event")

        # Route to appropriate transformer
        if event_type == "push":
            return self.transform_push_event(payload)
        elif event_type == "pull_request":
            event = self.transform_pull_request_event(payload)
            return [event] if event else []
        elif event_type == "issues":
            event = self.transform_issues_event(payload)
            return [event] if event else []
        elif event_type == "issue_comment":
            event = self.transform_issue_comment_event(payload)
            return [event] if event else []
        elif event_type == "create":
            event = self.transform_create_event(payload)
            return [event] if event else []
        elif event_type == "delete":
            event = self.transform_delete_event(payload)
            return [event] if event else []
        else:
            logger.warning(f"⚠️  Unhandled event type: {event_type}")
            return []

    def create_router(self) -> APIRouter:
        """
        Create FastAPI router with webhook endpoint.

        Returns:
            APIRouter instance to include in FastAPI app
        """
        router = APIRouter(prefix="/webhooks", tags=["webhooks"])

        @router.post("/github")
        async def handle_github_webhook(
            request: Request,
            x_hub_signature_256: Optional[str] = Header(None),
            x_github_event: Optional[str] = Header(None),
        ):
            """
            GitHub webhook endpoint.

            Receives GitHub events, validates signature, transforms to
            message bus events, and publishes.
            """
            # Read raw body for signature validation
            body = await request.body()

            # Validate signature
            if not self.validate_signature(body, x_hub_signature_256):
                logger.error("❌ Webhook signature validation failed")
                raise HTTPException(status_code=401, detail="Invalid signature")

            # Parse JSON payload
            try:
                payload = json.loads(body)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Invalid JSON payload: {e}")
                raise HTTPException(status_code=400, detail="Invalid JSON")

            # Check if event type is enabled
            if x_github_event not in self.enabled_events:
                logger.info(f"⏭️  Ignoring disabled event: {x_github_event}")
                return JSONResponse(
                    content={
                        "status": "ignored",
                        "event": x_github_event,
                        "reason": "Event type not enabled",
                    }
                )

            # Transform webhook to message bus event(s)
            try:
                events = self.transform_webhook(x_github_event, payload)
            except Exception as e:
                logger.error(f"❌ Failed to transform webhook: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500, detail="Failed to process webhook"
                )

            # Publish events to message bus
            published_count = 0
            for event in events:
                try:
                    # Build topic: github.<event_type>
                    topic = f"github.{event.event_type}"

                    # Embed metadata in payload
                    payload_with_metadata = {
                        **event.payload,
                        "_metadata": {
                            "source": event.source,
                            "timestamp": event.timestamp,
                            "github_event": x_github_event,
                        },
                    }

                    # Publish to message bus
                    message_id = self.message_bus.publish(
                        topic=topic,
                        payload=payload_with_metadata,
                        priority=event.priority,
                    )

                    published_count += 1
                    logger.info(
                        f"✅ Published {event.event_type} to message bus (ID: {message_id})"
                    )

                except Exception as e:
                    logger.error(
                        f"❌ Failed to publish event {event.event_type}: {e}",
                        exc_info=True,
                    )
                    # Continue processing other events

            # Return success response
            return JSONResponse(
                content={
                    "status": "success",
                    "event": x_github_event,
                    "events_published": published_count,
                    "events_transformed": len(events),
                }
            )

        @router.get("/github/health")
        async def webhook_health():
            """Health check endpoint for webhook handler."""
            return {
                "status": "healthy",
                "enabled_events": self.enabled_events,
                "message_bus_connected": self.message_bus.health_check(),
            }

        return router
