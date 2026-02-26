"""Pydantic schemas for audit log events — Iteration 2, E1-S2."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class AuditEventCreate(BaseModel):
    """Schema for writing a new audit log event (POST /audit/events body)."""

    # Required fields
    screen: str = Field(
        ...,
        description="Screen or context that generated the event (e.g. cp_registration, cp_login)",
    )
    action: str = Field(
        ...,
        description="Specific action that occurred (e.g. otp_sent, captcha_failed)",
    )
    outcome: Literal["success", "failure"] = Field(
        ...,
        description="Must be 'success' or 'failure'",
    )

    # Optional context fields
    user_id: Optional[uuid.UUID] = None
    email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    detail: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    correlation_id: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditEventResponse(BaseModel):
    """Schema for reading an audit log event (GET /audit/events response item).

    deleted_at is intentionally excluded from the public response.
    """

    id: uuid.UUID
    timestamp: datetime

    # User identity
    user_id: Optional[uuid.UUID] = None
    email: Optional[str] = None

    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Event classification
    screen: str
    action: str
    outcome: Literal["success", "failure"]

    # Detail + metadata
    detail: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj: Any) -> "AuditEventResponse":
        """Build from AuditLog ORM model, handling metadata_json column alias."""
        return cls(
            id=obj.id,
            timestamp=obj.timestamp,
            user_id=obj.user_id,
            email=obj.email,
            ip_address=obj.ip_address,
            user_agent=obj.user_agent,
            screen=obj.screen,
            action=obj.action,
            outcome=obj.outcome,
            detail=obj.detail,
            metadata=obj.metadata_json,
            correlation_id=obj.correlation_id,
        )


class AuditEventsListResponse(BaseModel):
    """Paginated list of audit events."""

    items: list[AuditEventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
