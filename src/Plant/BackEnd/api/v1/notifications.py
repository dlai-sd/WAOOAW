"""Notification processing APIs (Phase-1).

NOTIF-1.2:
- Provide an env-configurable email provider integration.

Phase-1 design:
- Deterministic processing endpoint (similar to process-period-end / process-trial-end)
  so lower envs and tests can validate without background workers.
"""

from __future__ import annotations

import os

from fastapi import APIRouter
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_connector
from services.customer_service import CustomerService
from services.email_providers import EmailProvider, get_email_provider
from services.notification_delivery_store import delivery_key, get_notification_delivery_store
from services.notification_email_templates import render_email_for_event
from services.notification_events import NotificationEventRecord, get_notification_event_store
from services.notification_sms_templates import render_sms_for_event
from services.sms_providers import SmsProvider, get_sms_provider


router = APIRouter(prefix="/notifications", tags=["notifications"])


def _require_cp_registration_key(request: Request) -> None:
    expected = (os.getenv("CP_REGISTRATION_KEY") or "").strip()
    provided = (request.headers.get("X-CP-Registration-Key") or "").strip()

    if not expected:
        raise HTTPException(status_code=500, detail="CP_REGISTRATION_KEY not configured")
    if not provided or provided != expected:
        raise HTTPException(status_code=401, detail="Missing or invalid registration key")


class ProcessEmailNotificationsRequest(BaseModel):
    limit: int = Field(default=200, ge=1, le=5000)


class ProcessEmailNotificationsResponse(BaseModel):
    scanned: int
    sent: int
    skipped: int


class ProcessSmsNotificationsRequest(BaseModel):
    limit: int = Field(default=200, ge=1, le=5000)


class ProcessSmsNotificationsResponse(BaseModel):
    scanned: int
    sent: int
    skipped: int


class IngestNotificationEventRequest(BaseModel):
    event_type: str = Field(..., min_length=1)
    customer_id: str | None = None
    subscription_id: str | None = None
    order_id: str | None = None
    hired_instance_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class IngestNotificationEventResponse(BaseModel):
    ok: bool = True


def _get_customer_service(db: AsyncSession) -> CustomerService:
    return CustomerService(db)


def _recipient_from_metadata(metadata: object) -> str | None:
    if not isinstance(metadata, dict):
        return None
    for k in ("to_email", "customer_email", "email"):
        raw = metadata.get(k)
        if raw is None:
            continue
        candidate = str(raw).strip()
        if candidate:
            return candidate
    return None


def _recipient_phone_from_metadata(metadata: object) -> str | None:
    if not isinstance(metadata, dict):
        return None
    for k in ("to_phone", "customer_phone", "phone"):
        raw = metadata.get(k)
        if raw is None:
            continue
        candidate = str(raw).strip()
        if candidate:
            return candidate
    return None


@router.post("/events", response_model=IngestNotificationEventResponse)
async def ingest_event(
    body: IngestNotificationEventRequest,
    request: Request,
) -> IngestNotificationEventResponse:
    """Append a notification event (best-effort ingestion).

    This endpoint exists so CP can record OTP events before a JWT/customer context
    exists, while still protecting ingestion with the CP registration key.
    """

    _require_cp_registration_key(request)

    get_notification_event_store().append(
        NotificationEventRecord(
            event_type=body.event_type,
            customer_id=(body.customer_id or None),
            subscription_id=(body.subscription_id or None),
            order_id=(body.order_id or None),
            hired_instance_id=(body.hired_instance_id or None),
            metadata=dict(body.metadata or {}),
        )
    )
    return IngestNotificationEventResponse(ok=True)


@router.post("/process-email", response_model=ProcessEmailNotificationsResponse)
async def process_email_notifications(
    body: ProcessEmailNotificationsRequest,
) -> ProcessEmailNotificationsResponse:
    events = get_notification_event_store().list_records(limit=int(body.limit))
    delivery = get_notification_delivery_store()
    provider: EmailProvider = get_email_provider()
    db_session: AsyncSession | None = None
    customers: CustomerService | None = None
    db_unavailable = False

    scanned = 0
    sent = 0
    skipped = 0

    for ev in events:
        scanned += 1
        key = delivery_key("email", ev)
        if delivery.has(key):
            skipped += 1
            continue

        rendered = render_email_for_event(ev)
        if rendered is None:
            skipped += 1
            delivery.mark(key)
            continue

        to_email = _recipient_from_metadata(ev.metadata)
        if not to_email:
            if not ev.customer_id:
                skipped += 1
                delivery.mark(key)
                continue

            if db_unavailable:
                skipped += 1
                # Retry-able: do not mark delivered.
                continue

            if db_session is None or customers is None:
                try:
                    db_session = await get_connector().get_session()
                    customers = _get_customer_service(db_session)
                except Exception:
                    db_unavailable = True
                    skipped += 1
                    continue

            customer = await customers.get_by_id(ev.customer_id)
            if customer is None or not (customer.email or "").strip():
                skipped += 1
                delivery.mark(key)
                continue
            to_email = customer.email

        # Best-effort: if provider is null, this becomes a no-op; we still mark delivered.
        try:
            provider.send_email(
                to_email=to_email,
                subject=rendered.subject,
                text_body=rendered.text_body,
                html_body=rendered.html_body,
            )
        except Exception:
            # Do not mark as delivered on hard failure; allow retry on next processing run.
            skipped += 1
            continue

        delivery.mark(key)
        sent += 1

    if db_session is not None:
        try:
            await db_session.close()
        except Exception:
            pass

    return ProcessEmailNotificationsResponse(scanned=scanned, sent=sent, skipped=skipped)


@router.post("/process-sms", response_model=ProcessSmsNotificationsResponse)
async def process_sms_notifications(
    body: ProcessSmsNotificationsRequest,
) -> ProcessSmsNotificationsResponse:
    events = get_notification_event_store().list_records(limit=int(body.limit))
    delivery = get_notification_delivery_store()
    provider: SmsProvider = get_sms_provider()

    db_session: AsyncSession | None = None
    customers: CustomerService | None = None
    db_unavailable = False

    scanned = 0
    sent = 0
    skipped = 0

    for ev in events:
        scanned += 1
        key = delivery_key("sms", ev)
        if delivery.has(key):
            skipped += 1
            continue

        rendered = render_sms_for_event(ev)
        if rendered is None:
            skipped += 1
            delivery.mark(key)
            continue

        to_phone = _recipient_phone_from_metadata(ev.metadata)
        if not to_phone:
            if not ev.customer_id:
                skipped += 1
                delivery.mark(key)
                continue

            if db_unavailable:
                skipped += 1
                continue

            if db_session is None or customers is None:
                try:
                    db_session = await get_connector().get_session()
                    customers = _get_customer_service(db_session)
                except Exception:
                    db_unavailable = True
                    skipped += 1
                    continue

            customer = await customers.get_by_id(ev.customer_id)
            if customer is None or not (customer.phone or "").strip():
                skipped += 1
                delivery.mark(key)
                continue
            to_phone = customer.phone

        try:
            await provider.send_sms(to_phone=to_phone, message=rendered.message)
        except Exception:
            skipped += 1
            continue

        delivery.mark(key)
        sent += 1

    if db_session is not None:
        try:
            await db_session.close()
        except Exception:
            pass

    return ProcessSmsNotificationsResponse(scanned=scanned, sent=sent, skipped=skipped)
