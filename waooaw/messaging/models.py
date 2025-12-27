"""
Message Models for WAOOAW Message Bus

Based on message_schema.json and MESSAGE_BUS_ARCHITECTURE.md
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid
import time


class MessageRouting(BaseModel):
    """Message routing information"""
    from_agent: str = Field(
        ...,
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
        min_length=3,
        max_length=64,
        description="Sending agent ID (kebab-case)"
    )
    to_agents: List[str] = Field(
        ...,
        description="Receiving agent IDs or ['*'] for broadcast"
    )
    topic: str = Field(
        ...,
        pattern=r"^[a-z0-9]+(\.[a-z0-9_]+)*$",
        min_length=1,
        max_length=255,
        description="Message topic (dot-separated hierarchy)"
    )
    reply_to: Optional[str] = Field(
        None,
        description="Topic for reply messages"
    )
    correlation_id: Optional[str] = Field(
        None,
        pattern=r"^[a-zA-Z0-9_-]+$",
        max_length=128,
        description="Correlation ID for request-response pairing"
    )


class MessagePayload(BaseModel):
    """Message content"""
    subject: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable subject line"
    )
    body: Optional[str] = Field(
        None,
        max_length=65535,
        description="Message body (plain text or markdown)"
    )
    action: str = Field(
        ...,
        description="Requested action (verb)"
    )
    priority: int = Field(
        3,
        ge=1,
        le=5,
        description="Message priority (1=bulk, 5=critical)"
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary payload data (action-specific)"
    )


class MessageMetadata(BaseModel):
    """Message metadata"""
    message_id: str = Field(
        default_factory=lambda: f"msg-{uuid.uuid4().hex}",
        pattern=r"^msg-[a-f0-9]{32}$",
        description="Unique message ID (auto-generated)"
    )
    timestamp: float = Field(
        default_factory=time.time,
        description="Unix timestamp (seconds since epoch)"
    )
    ttl: int = Field(
        0,
        ge=0,
        le=31536000,
        description="Time-to-live in seconds (0 = no expiry)"
    )
    retry_count: int = Field(
        0,
        ge=0,
        le=10,
        description="Number of delivery attempts"
    )
    idempotency_key: Optional[str] = Field(
        None,
        max_length=128,
        description="Key for idempotent processing"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Message tags for filtering/routing"
    )
    signature: Optional[str] = Field(
        None,
        pattern=r"^[a-f0-9]{64}$",
        description="HMAC-SHA256 signature for authentication"
    )
    signature_algo: str = Field(
        "hmac-sha256",
        description="Signature algorithm"
    )


class AuditInfo(BaseModel):
    """Audit trail metadata"""
    sender_version: Optional[str] = Field(
        None,
        pattern=r"^v\d+\.\d+\.\d+$",
        description="Sending agent version"
    )
    sender_instance_id: Optional[str] = Field(
        None,
        max_length=64,
        description="Sending agent instance ID"
    )
    trace_id: Optional[str] = Field(
        None,
        pattern=r"^[a-f0-9]{32}$",
        description="OpenTelemetry trace ID"
    )
    span_id: Optional[str] = Field(
        None,
        pattern=r"^[a-f0-9]{16}$",
        description="OpenTelemetry span ID"
    )
    environment: Optional[str] = Field(
        None,
        description="Deployment environment"
    )


class Message(BaseModel):
    """
    Standard message format for agent communication.
    
    Based on MESSAGE_BUS_ARCHITECTURE.md v1.1
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "routing": {
                "from_agent": "wow-vision-prime",
                "to_agents": ["wow-content"],
                "topic": "vision.analysis_complete",
                "correlation_id": "req-abc123"
            },
            "payload": {
                "subject": "Website analysis completed",
                "body": "Analyzed example.com. Found 3 areas for improvement.",
                "action": "notify",
                "priority": 4,
                "data": {
                    "url": "https://example.com",
                    "score": 78,
                    "issues_found": 3
                }
            },
            "metadata": {
                "ttl": 3600,
                "tags": ["vision", "analysis"]
            },
            "audit": {
                "sender_version": "v0.2.8",
                "environment": "development"
            }
        }
    })
    
    routing: MessageRouting
    payload: MessagePayload
    metadata: MessageMetadata = Field(default_factory=MessageMetadata)
    audit: Optional[AuditInfo] = Field(default_factory=AuditInfo)
