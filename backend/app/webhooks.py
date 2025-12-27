"""
GitHub Webhook Handler for WAOOAW Platform

Receives GitHub webhook events, validates HMAC signatures,
and publishes to message bus for agent processing.
"""
import hashlib
import hmac
import json
import logging
import os
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse

from waooaw.messaging.message_bus import MessageBus
from waooaw.messaging.models import Message, MessageRouting, MessagePayload

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Initialize message bus (lazy loading - can be overridden for testing)
_message_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """
    Get or initialize message bus singleton.
    
    For testing, set backend.app.webhooks._message_bus to a mock before calling.
    """
    global _message_bus
    if _message_bus is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        _message_bus = MessageBus(redis_url=redis_url, secret_key=webhook_secret)
    return _message_bus


def set_message_bus_for_testing(bus: Optional[MessageBus]):
    """Set message bus instance for testing (bypasses singleton)."""
    global _message_bus
    _message_bus = bus


def verify_github_signature(
    payload_body: bytes,
    signature_header: str,
    secret: str
) -> bool:
    """
    Verify GitHub webhook HMAC signature.
    
    Args:
        payload_body: Raw request body
        signature_header: X-Hub-Signature-256 header value
        secret: GitHub webhook secret
        
    Returns:
        True if signature is valid
        
    Raises:
        ValueError: If signature format is invalid
    """
    if not signature_header:
        raise ValueError("Missing signature header")
    
    # Parse signature header (format: "sha256=...")
    if not signature_header.startswith("sha256="):
        raise ValueError("Invalid signature format")
    
    expected_signature = signature_header[7:]  # Remove "sha256=" prefix
    
    # Compute HMAC
    computed_signature = hmac.new(
        secret.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(expected_signature, computed_signature)


def transform_github_event_to_message(
    event_type: str,
    event_data: Dict[str, Any],
    delivery_id: str
) -> Message:
    """
    Transform GitHub webhook event into MessageBus message.
    
    Args:
        event_type: GitHub event type (push, pull_request, etc.)
        event_data: Webhook payload
        delivery_id: GitHub delivery ID (X-GitHub-Delivery header)
        
    Returns:
        Message ready for publishing to message bus
    """
    # Determine priority based on event type
    priority_map = {
        "push": 4,  # High priority (file changes)
        "pull_request": 4,  # High priority (PR review)
        "issue_comment": 3,  # Normal priority (human feedback)
        "issues": 3,  # Normal priority
        "create": 2,  # Low priority (branch/tag created)
        "delete": 2,  # Low priority
        "star": 1,  # Bulk priority (not critical)
        "fork": 1,  # Bulk priority
    }
    priority = priority_map.get(event_type, 3)
    
    # Extract repository info
    repository = event_data.get("repository", {})
    repo_name = repository.get("full_name", "unknown")
    
    # Create message
    message = Message(
        routing=MessageRouting(
            from_agent="github-webhook",
            to_agents=["*"],  # Broadcast to all agents (they filter via should_wake)
            topic=f"github.{event_type}",
            correlation_id=delivery_id
        ),
        payload=MessagePayload(
            subject=f"GitHub {event_type} event from {repo_name}",
            body=f"GitHub webhook event received: {event_type}",
            action="notify",
            priority=priority,
            data={
                "event_type": event_type,
                "repository": repo_name,
                "data": event_data
            }
        )
    )
    
    # Add tags for filtering
    message.metadata.tags.extend([
        f"source:github",
        f"event:{event_type}",
        f"repo:{repo_name}"
    ])
    
    # Set audit info
    message.audit.sender_version = "v0.2.8"
    message.audit.sender_instance_id = "github-webhook-001"
    message.audit.environment = os.getenv("ENV", "development")
    
    return message


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """
    GitHub webhook endpoint.
    
    Receives GitHub events, validates signatures, and publishes to message bus.
    
    Headers:
        X-GitHub-Event: Event type (push, pull_request, etc.)
        X-GitHub-Delivery: Unique delivery ID
        X-Hub-Signature-256: HMAC-SHA256 signature
        
    Returns:
        202 Accepted: Event queued for processing
        400 Bad Request: Invalid payload
        401 Unauthorized: Invalid signature
        500 Internal Server Error: Message bus error
    """
    try:
        # Read raw body for signature verification
        body = await request.body()
        
        # Verify signature (if secret configured)
        webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        if webhook_secret:
            if not x_hub_signature_256:
                logger.warning("GitHub webhook secret configured but no signature provided")
                raise HTTPException(status_code=401, detail="Missing signature")
            
            try:
                if not verify_github_signature(body, x_hub_signature_256, webhook_secret):
                    logger.error("Invalid GitHub webhook signature")
                    raise HTTPException(status_code=401, detail="Invalid signature")
            except ValueError as e:
                logger.error(f"Signature validation error: {e}")
                raise HTTPException(status_code=401, detail=str(e))
        else:
            logger.warning("GitHub webhook secret not configured - signature verification disabled")
        
        # Parse JSON payload
        try:
            event_data = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Transform to message bus event
        message = transform_github_event_to_message(
            event_type=x_github_event,
            event_data=event_data,
            delivery_id=x_github_delivery
        )
        
        # Publish to message bus
        bus = get_message_bus()
        message_id = bus.publish(message)
        
        logger.info(
            f"GitHub webhook processed: {x_github_event} -> {message_id}",
            extra={
                "event_type": x_github_event,
                "delivery_id": x_github_delivery,
                "message_id": message_id
            }
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "status": "accepted",
                "message_id": message_id,
                "event_type": x_github_event,
                "delivery_id": x_github_delivery
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing GitHub webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/github/health")
async def webhook_health():
    """
    Webhook health check.
    
    Returns:
        200 OK: Webhook endpoint is operational
        503 Service Unavailable: Message bus unavailable
    """
    try:
        # Check message bus connectivity
        bus = get_message_bus()
        # Simple ping (try to get pending count on a test stream)
        bus.redis_client.ping()
        
        return {
            "status": "healthy",
            "endpoint": "/webhooks/github",
            "message_bus": "connected"
        }
    except Exception as e:
        logger.error(f"Webhook health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Message bus unavailable"
        )
