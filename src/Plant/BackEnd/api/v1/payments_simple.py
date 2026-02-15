"""Payments API (Phase-1 simple implementation).

HIRE-2.1 + HIRE-2.5:
- Create a payment order (intent) and a subscription record.
- In coupon mode, treat payment as already confirmed.

BILL-1 (Phase-1):
- Best-effort invoice issuance for paid orders.
- Invoice retrieval is customer-scoped via Gateway-enforced customer_id.

This is an in-memory implementation intended to unblock CP Hire flows in lower envs.
A DB-backed version + Razorpay integration can replace this later.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from repositories.subscription_repository import SubscriptionRepository
from services.notification_events import NotificationEventRecord, get_notification_event_store


PaymentsMode = Literal["razorpay", "coupon"]


def _should_issue_gst_invoice() -> bool:
    raw = (os.getenv("ISSUE_GST_INVOICE") or "true").strip().lower()
    return raw in {"1", "true", "yes", "y"}


def _is_production() -> bool:
    env = (os.getenv("ENVIRONMENT") or "").strip().lower()
    return env in {"prod", "production"}


def _get_payments_mode() -> PaymentsMode:
    raw_mode = (os.getenv("PAYMENTS_MODE") or "").strip().lower() or "coupon"
    if raw_mode not in {"razorpay", "coupon"}:
        raise HTTPException(status_code=500, detail="Invalid PAYMENTS_MODE; expected 'razorpay' or 'coupon'.")
    if _is_production() and raw_mode == "coupon":
        raise HTTPException(status_code=500, detail="PAYMENTS_MODE=coupon is not allowed in production.")
    return raw_mode  # type: ignore[return-value]


def _duration_to_period_end(duration: str, start: datetime) -> datetime:
    normalized = (duration or "").strip().lower()
    if normalized == "monthly":
        return start + timedelta(days=30)
    if normalized == "quarterly":
        return start + timedelta(days=90)
    if normalized == "yearly":
        return start + timedelta(days=365)
    raise HTTPException(status_code=400, detail="Unsupported duration.")


def _duration_to_amount_inr(duration: str) -> int:
    # Phase-1 heuristic pricing for Razorpay checkout.
    # Monthly baseline matches CP marketing defaults; quarterly is a 3x multiple.
    normalized = (duration or "").strip().lower()
    if normalized == "monthly":
        return 12000
    if normalized == "quarterly":
        return 36000
    if normalized == "yearly":
        return 144000
    raise HTTPException(status_code=400, detail="Unsupported duration.")


class CouponCheckoutRequest(BaseModel):
    coupon_code: str = Field(..., min_length=1)
    agent_id: str = Field(..., min_length=1)
    duration: str = Field(..., min_length=1, description="e.g. monthly, quarterly")
    customer_id: str | None = None
    gstin: str | None = Field(default=None, description="Optional GSTIN for billing (collection only).")


class CouponCheckoutResponse(BaseModel):
    order_id: str
    subscription_id: str

    payment_provider: Literal["coupon"] = "coupon"
    amount: int = 0
    currency: str = "INR"

    coupon_code: str
    agent_id: str
    duration: str

    subscription_status: str = "active"
    trial_status: str = "not_started"


class _OrderRecord(BaseModel):
    order_id: str
    payment_provider: str
    subscription_id: str | None = None
    amount: int
    currency: str
    agent_id: str
    duration: str
    customer_id: str | None
    gstin: str | None = None
    status: str
    created_at: datetime
    paid_at: datetime | None


class _SubscriptionRecord(BaseModel):
    subscription_id: str
    agent_id: str
    duration: str
    customer_id: str | None
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    ended_at: datetime | None = None


class SubscriptionResponse(BaseModel):
    subscription_id: str
    agent_id: str
    duration: str
    customer_id: str | None
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    ended_at: datetime | None = None


class ProcessPeriodEndRequest(BaseModel):
    now: datetime | None = None


_orders: dict[str, _OrderRecord] = {}
_subscriptions: dict[str, _SubscriptionRecord] = {}
_idempotency_cache: dict[str, dict] = {}
_idempotency_fingerprint: dict[str, dict] = {}

_razorpay_order_to_internal: dict[str, str] = {}


router = APIRouter(prefix="/payments", tags=["payments"])


def _persistence_mode() -> str:
    # Feature flag: PERSISTENCE_MODE (default: "memory" for Phase 1 compatibility)
    # Options: "memory" (in-memory dicts), "db" (PostgreSQL via repositories)
    return os.getenv("PERSISTENCE_MODE", "memory").strip().lower()


async def _get_payments_db_session() -> Any:
    """Return a DB session only when DB-backed mode is enabled.

    Important: Most Plant unit tests run without a Postgres service; keep Phase-1
    payments flows DB-free unless PERSISTENCE_MODE=db.
    """

    if _persistence_mode() != "db":
        yield None
        return

    async for session in get_db_session():
        yield session


async def _persist_subscription_to_db_if_enabled(
    *,
    db: AsyncSession | None,
    record: _SubscriptionRecord,
    now: datetime,
) -> None:
    if db is None:
        return

    repo = SubscriptionRepository(db)
    async with db.begin():
        await repo.upsert(
            subscription_id=record.subscription_id,
            agent_id=record.agent_id,
            duration=record.duration,
            customer_id=record.customer_id,
            status=record.status,
            current_period_start=record.current_period_start,
            current_period_end=record.current_period_end,
            cancel_at_period_end=bool(record.cancel_at_period_end),
            ended_at=record.ended_at,
            now=now,
        )


def _get_required_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise HTTPException(status_code=500, detail=f"Missing required env: {name}")
    return value


async def _razorpay_create_order(*, amount_in_paise: int, currency: str, receipt: str) -> dict[str, Any]:
    key_id = _get_required_env("RAZORPAY_KEY_ID")
    key_secret = _get_required_env("RAZORPAY_KEY_SECRET")

    auth_raw = f"{key_id}:{key_secret}".encode("utf-8")
    auth = base64.b64encode(auth_raw).decode("ascii")

    payload = {
        "amount": int(amount_in_paise),
        "currency": currency,
        "receipt": receipt,
        "payment_capture": 1,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.razorpay.com/v1/orders",
            headers={"Authorization": f"Basic {auth}"},
            json=payload,
        )

    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Razorpay order create failed ({resp.status_code})")

    data = resp.json()
    if not isinstance(data, dict) or not data.get("id"):
        raise HTTPException(status_code=502, detail="Razorpay order create returned invalid response")
    return data


def _verify_razorpay_checkout_signature(*, razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    key_secret = _get_required_env("RAZORPAY_KEY_SECRET")
    msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
    digest = hmac.new(key_secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, (razorpay_signature or "").strip())


def _verify_razorpay_webhook_signature(*, raw_body: bytes, signature: str) -> bool:
    webhook_secret = _get_required_env("RAZORPAY_WEBHOOK_SECRET")
    expected = hmac.new(webhook_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, (signature or "").strip())


class RazorpayOrderCreateRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    duration: str = Field(..., min_length=1)
    customer_id: str | None = None


class RazorpayOrderCreateResponse(BaseModel):
    order_id: str
    subscription_id: str

    payment_provider: Literal["razorpay"] = "razorpay"
    currency: str = "INR"
    amount: int

    razorpay_key_id: str
    razorpay_order_id: str


class RazorpayConfirmRequest(BaseModel):
    order_id: str = Field(..., min_length=1)
    razorpay_order_id: str = Field(..., min_length=1)
    razorpay_payment_id: str = Field(..., min_length=1)
    razorpay_signature: str = Field(..., min_length=1)
    customer_id: str | None = None


class RazorpayConfirmResponse(BaseModel):
    order_id: str
    subscription_id: str
    payment_provider: Literal["razorpay"] = "razorpay"
    subscription_status: str


@router.post("/razorpay/order", response_model=RazorpayOrderCreateResponse)
async def razorpay_create_order(body: RazorpayOrderCreateRequest) -> RazorpayOrderCreateResponse:
    mode = _get_payments_mode()
    if mode != "razorpay":
        raise HTTPException(status_code=403, detail="Razorpay checkout is disabled when PAYMENTS_MODE is not 'razorpay'.")

    now = datetime.now(timezone.utc)
    amount_inr = _duration_to_amount_inr(body.duration)
    amount_paise = int(amount_inr) * 100

    internal_order_id = f"ORDER-{uuid4()}"
    subscription_id = f"SUB-{uuid4()}"

    razorpay = await _razorpay_create_order(amount_in_paise=amount_paise, currency="INR", receipt=internal_order_id)
    razorpay_order_id = str(razorpay.get("id"))

    _orders[internal_order_id] = _OrderRecord(
        order_id=internal_order_id,
        payment_provider="razorpay",
        subscription_id=subscription_id,
        amount=amount_inr,
        currency="INR",
        agent_id=body.agent_id,
        duration=body.duration,
        customer_id=body.customer_id,
        status="created",
        created_at=now,
        paid_at=None,
    )

    # Create a subscription in pending state; activate on confirm/webhook.
    period_end = _duration_to_period_end(body.duration, now)
    _subscriptions[subscription_id] = _SubscriptionRecord(
        subscription_id=subscription_id,
        agent_id=body.agent_id,
        duration=body.duration,
        customer_id=body.customer_id,
        status="pending_payment",
        current_period_start=now,
        current_period_end=period_end,
    )

    _razorpay_order_to_internal[razorpay_order_id] = internal_order_id

    return RazorpayOrderCreateResponse(
        order_id=internal_order_id,
        subscription_id=subscription_id,
        amount=amount_inr,
        razorpay_key_id=_get_required_env("RAZORPAY_KEY_ID"),
        razorpay_order_id=razorpay_order_id,
    )


@router.post("/razorpay/confirm", response_model=RazorpayConfirmResponse)
async def razorpay_confirm(body: RazorpayConfirmRequest) -> RazorpayConfirmResponse:
    mode = _get_payments_mode()
    if mode != "razorpay":
        raise HTTPException(status_code=403, detail="Razorpay confirm is disabled when PAYMENTS_MODE is not 'razorpay'.")

    record = _orders.get(body.order_id)
    if not record:
        raise HTTPException(status_code=404, detail="Order not found.")
    if record.payment_provider != "razorpay":
        raise HTTPException(status_code=409, detail="Order is not a Razorpay order.")

    # Optional authz: if we know customer_id, require match.
    if record.customer_id and body.customer_id and record.customer_id != body.customer_id:
        raise HTTPException(status_code=403, detail="Order does not belong to customer")

    if not _verify_razorpay_checkout_signature(
        razorpay_order_id=body.razorpay_order_id,
        razorpay_payment_id=body.razorpay_payment_id,
        razorpay_signature=body.razorpay_signature,
    ):
        # NOTIF-1.1: emit payment failure (best-effort).
        try:
            get_notification_event_store().append(
                NotificationEventRecord(
                    event_type="payment_failed",
                    customer_id=(record.customer_id or None),
                    order_id=record.order_id,
                    metadata={
                        "payment_provider": "razorpay",
                        "reason": "invalid_checkout_signature",
                        "agent_id": record.agent_id,
                        "duration": record.duration,
                    },
                )
            )
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Invalid Razorpay signature")

    # Idempotent success.
    if record.status == "paid":
        if record.subscription_id and record.subscription_id in _subscriptions:
            return RazorpayConfirmResponse(
                order_id=record.order_id,
                subscription_id=record.subscription_id,
                subscription_status="active",
            )

        # Back-compat fallback: find subscription by scanning (phase-1).
        sub_id = None
        for sid, sub in _subscriptions.items():
            if sub.agent_id == record.agent_id and sub.duration == record.duration and sub.customer_id == record.customer_id:
                sub_id = sid
                if sub.status == "active":
                    break
        if not sub_id:
            raise HTTPException(status_code=500, detail="Subscription missing for paid order")
        _orders[body.order_id] = record.model_copy(update={"subscription_id": sub_id})
        return RazorpayConfirmResponse(order_id=record.order_id, subscription_id=sub_id, subscription_status="active")

    now = datetime.now(timezone.utc)
    _orders[body.order_id] = record.model_copy(update={"status": "paid", "paid_at": now})

    # Activate the newest matching pending subscription.
    matching_subs = [
        (sid, sub)
        for (sid, sub) in _subscriptions.items()
        if sub.agent_id == record.agent_id and sub.duration == record.duration and sub.customer_id == record.customer_id
    ]
    if not matching_subs:
        raise HTTPException(status_code=500, detail="Subscription missing for order")
    matching_subs.sort(key=lambda item: item[1].current_period_end)
    subscription_id, sub_record = matching_subs[-1]
    if sub_record.status != "active":
        _subscriptions[subscription_id] = sub_record.model_copy(update={"status": "active"})

    # Persist subscription id on the order for idempotency.
    _orders[body.order_id] = _orders[body.order_id].model_copy(update={"subscription_id": subscription_id})

    # NOTIF-1.1: emit payment success (best-effort).
    try:
        get_notification_event_store().append(
            NotificationEventRecord(
                event_type="payment_success",
                customer_id=(record.customer_id or None),
                order_id=record.order_id,
                subscription_id=subscription_id,
                metadata={
                    "payment_provider": "razorpay",
                    "agent_id": record.agent_id,
                    "duration": record.duration,
                    "amount": record.amount,
                    "currency": record.currency,
                },
            )
        )
    except Exception:
        pass

    # Best-effort receipt/invoice issuance.
    try:
        customer_id = (record.customer_id or "").strip()
        if customer_id:
            from api.v1.receipts_simple import create_receipt_for_paid_order

            create_receipt_for_paid_order(
                customer_id=customer_id,
                order_id=record.order_id,
                subscription_id=subscription_id,
                amount=record.amount,
                currency=record.currency,
                agent_id=record.agent_id,
                duration=record.duration,
            )

            if _should_issue_gst_invoice():
                from api.v1.invoices_simple import create_invoice_for_paid_order

                create_invoice_for_paid_order(
                    customer_id=customer_id,
                    order_id=record.order_id,
                    subscription_id=subscription_id,
                    amount=record.amount,
                    currency=record.currency,
                    agent_id=record.agent_id,
                    duration=record.duration,
                    customer_gstin=record.gstin,
                )
    except Exception:
        pass

    return RazorpayConfirmResponse(
        order_id=record.order_id,
        subscription_id=subscription_id,
        subscription_status="active",
    )


@router.post("/razorpay/webhook")
async def razorpay_webhook(request: Request) -> dict:
    mode = _get_payments_mode()
    if mode != "razorpay":
        raise HTTPException(status_code=403, detail="Razorpay webhook is disabled when PAYMENTS_MODE is not 'razorpay'.")

    signature = request.headers.get("X-Razorpay-Signature") or request.headers.get("x-razorpay-signature")
    raw = await request.body()
    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Razorpay-Signature")
    if not _verify_razorpay_webhook_signature(raw_body=raw, signature=signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook JSON")

    # Minimal extraction: payment.captured payloads include payload.payment.entity.order_id.
    razorpay_order_id = None
    try:
        razorpay_order_id = payload.get("payload", {}).get("payment", {}).get("entity", {}).get("order_id")
    except Exception:
        razorpay_order_id = None
    razorpay_order_id = (razorpay_order_id or "").strip() or None
    if not razorpay_order_id:
        return {"ok": True, "ignored": True}

    internal_order_id = _razorpay_order_to_internal.get(razorpay_order_id)
    if not internal_order_id:
        return {"ok": True, "ignored": True}

    record = _orders.get(internal_order_id)
    if not record:
        return {"ok": True, "ignored": True}

    if record.status == "paid":
        return {"ok": True, "already_paid": True}

    # Mark paid without requiring client signature (webhook is source-of-truth).
    now = datetime.now(timezone.utc)
    _orders[internal_order_id] = record.model_copy(update={"status": "paid", "paid_at": now})

    # Activate newest matching subscription.
    matching_subs = [
        (sid, sub)
        for (sid, sub) in _subscriptions.items()
        if sub.agent_id == record.agent_id and sub.duration == record.duration and sub.customer_id == record.customer_id
    ]
    if matching_subs:
        matching_subs.sort(key=lambda item: item[1].current_period_end)
        subscription_id, sub_record = matching_subs[-1]
        if sub_record.status != "active":
            _subscriptions[subscription_id] = sub_record.model_copy(update={"status": "active"})

        # NOTIF-1.1: emit payment success (best-effort).
        try:
            get_notification_event_store().append(
                NotificationEventRecord(
                    event_type="payment_success",
                    customer_id=(record.customer_id or None),
                    order_id=record.order_id,
                    subscription_id=subscription_id,
                    metadata={
                        "payment_provider": "razorpay",
                        "agent_id": record.agent_id,
                        "duration": record.duration,
                        "amount": record.amount,
                        "currency": record.currency,
                        "via": "webhook",
                    },
                )
            )
        except Exception:
            pass

        try:
            customer_id = (record.customer_id or "").strip()
            if customer_id:
                from api.v1.receipts_simple import create_receipt_for_paid_order

                create_receipt_for_paid_order(
                    customer_id=customer_id,
                    order_id=record.order_id,
                    subscription_id=subscription_id,
                    amount=record.amount,
                    currency=record.currency,
                    agent_id=record.agent_id,
                    duration=record.duration,
                )

                if _should_issue_gst_invoice():
                    from api.v1.invoices_simple import create_invoice_for_paid_order

                    create_invoice_for_paid_order(
                        customer_id=customer_id,
                        order_id=record.order_id,
                        subscription_id=subscription_id,
                        amount=record.amount,
                        currency=record.currency,
                        agent_id=record.agent_id,
                        duration=record.duration,
                        customer_gstin=record.gstin,
                    )
        except Exception:
            pass

    return {"ok": True}


def get_subscription_status(subscription_id: str) -> str | None:
    record = _subscriptions.get(subscription_id)
    if not record:
        return None
    return record.status


def get_subscription_ended_at(subscription_id: str) -> datetime | None:
    record = _subscriptions.get(subscription_id)
    if not record:
        return None
    return record.ended_at


def _get_subscription_or_404(subscription_id: str) -> _SubscriptionRecord:
    record = _subscriptions.get(subscription_id)
    if not record:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    return record


def _to_subscription_response(record: _SubscriptionRecord) -> SubscriptionResponse:
    return SubscriptionResponse(
        subscription_id=record.subscription_id,
        agent_id=record.agent_id,
        duration=record.duration,
        customer_id=record.customer_id,
        status=record.status,
        current_period_start=record.current_period_start,
        current_period_end=record.current_period_end,
        cancel_at_period_end=bool(record.cancel_at_period_end),
        ended_at=record.ended_at,
    )


def _deactivate_hired_agent_by_subscription(subscription_id: str, now: datetime) -> str | None:
    # Avoid import cycles: hired_agents_simple imports payments_simple.
    try:
        from api.v1 import hired_agents_simple

        return hired_agents_simple.deactivate_by_subscription(subscription_id=subscription_id, now=now)
    except Exception:
        # Phase-1 best-effort.
        return None


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    db: AsyncSession | None = Depends(_get_payments_db_session),
) -> SubscriptionResponse:
    if db is not None:
        repo = SubscriptionRepository(db)
        record = await repo.get_by_id(subscription_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Subscription not found.")
        return SubscriptionResponse(
            subscription_id=record.subscription_id,
            agent_id=record.agent_id,
            duration=record.duration,
            customer_id=record.customer_id,
            status=record.status,
            current_period_start=record.current_period_start,
            current_period_end=record.current_period_end,
            cancel_at_period_end=bool(record.cancel_at_period_end),
            ended_at=record.ended_at,
        )

    record = _get_subscription_or_404(subscription_id)
    return _to_subscription_response(record)


@router.get("/subscriptions/by-customer/{customer_id}", response_model=list[SubscriptionResponse])
async def list_subscriptions_by_customer(
    customer_id: str,
    db: AsyncSession | None = Depends(_get_payments_db_session),
) -> list[SubscriptionResponse]:
    normalized = (customer_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="customer_id is required")

    if db is not None:
        repo = SubscriptionRepository(db)
        records = await repo.list_by_customer_id(normalized)
        results = [
            SubscriptionResponse(
                subscription_id=r.subscription_id,
                agent_id=r.agent_id,
                duration=r.duration,
                customer_id=r.customer_id,
                status=r.status,
                current_period_start=r.current_period_start,
                current_period_end=r.current_period_end,
                cancel_at_period_end=bool(r.cancel_at_period_end),
                ended_at=r.ended_at,
            )
            for r in records
        ]
        # Stable ordering for UX/tests.
        results.sort(key=lambda r: r.current_period_end)
        return results

    results: list[SubscriptionResponse] = []
    for record in _subscriptions.values():
        if (record.customer_id or "") == normalized:
            results.append(_to_subscription_response(record))
    # Stable ordering for UX/tests.
    results.sort(key=lambda r: r.current_period_end)
    return results


@router.post("/subscriptions/{subscription_id}/cancel", response_model=SubscriptionResponse)
async def cancel_at_period_end(
    subscription_id: str,
    customer_id: str | None = None,
    db: AsyncSession | None = Depends(_get_payments_db_session),
) -> SubscriptionResponse:
    record = _get_subscription_or_404(subscription_id)

    # Phase-1 authz: if we know the subscription customer, require match.
    if record.customer_id and customer_id and record.customer_id != customer_id:
        raise HTTPException(status_code=403, detail="Subscription does not belong to customer")

    if record.status != "active":
        raise HTTPException(status_code=409, detail="Subscription is not active")

    updated = record.model_copy(update={"cancel_at_period_end": True})
    _subscriptions[subscription_id] = updated

    try:
        await _persist_subscription_to_db_if_enabled(db=db, record=updated, now=datetime.now(timezone.utc))
    except Exception:
        # Phase-1 best-effort: do not block cancel UX on persistence.
        pass

    # NOTIF-1.1: emit cancel scheduled (best-effort).
    try:
        get_notification_event_store().append(
            NotificationEventRecord(
                event_type="cancel_scheduled",
                customer_id=(record.customer_id or None),
                subscription_id=subscription_id,
                metadata={
                    "effective_at": record.current_period_end.isoformat(),
                },
            )
        )
    except Exception:
        pass
    return _to_subscription_response(updated)


def _process_period_end(now: datetime) -> int:
    processed = 0
    for sub_id, record in list(_subscriptions.items()):
        if record.status != "active":
            continue
        if not record.cancel_at_period_end:
            continue
        if record.current_period_end > now:
            continue

        updated = record.model_copy(update={"status": "canceled", "ended_at": now})
        _subscriptions[sub_id] = updated
        processed += 1

        # NOTIF-1.1: emit cancel effective (best-effort).
        try:
            get_notification_event_store().append(
                NotificationEventRecord(
                    event_type="cancel_effective",
                    customer_id=(record.customer_id or None),
                    subscription_id=sub_id,
                    metadata={
                        "ended_at": now.isoformat(),
                    },
                )
            )
        except Exception:
            pass

        hired_instance_id = _deactivate_hired_agent_by_subscription(subscription_id=sub_id, now=now)
        if hired_instance_id:
            # END-1.4: emit deactivation event (best-effort).
            try:
                get_notification_event_store().append(
                    NotificationEventRecord(
                        event_type="hired_agent_deactivated",
                        customer_id=(record.customer_id or None),
                        subscription_id=sub_id,
                        hired_instance_id=hired_instance_id,
                        metadata={
                            "deactivated_at": now.isoformat(),
                        },
                    )
                )
            except Exception:
                pass

    return processed


@router.post("/subscriptions/process-period-end")
async def process_period_end(
    body: ProcessPeriodEndRequest,
    db: AsyncSession | None = Depends(_get_payments_db_session),
) -> dict:
    now = body.now or datetime.now(timezone.utc)
    processed = _process_period_end(now)

    if db is not None:
        # Best-effort mirror in-memory transitions into the DB.
        try:
            for record in _subscriptions.values():
                if record.status not in {"active", "canceled"}:
                    continue
                await _persist_subscription_to_db_if_enabled(db=db, record=record, now=now)
        except Exception:
            pass

    return {"processed": processed, "now": now}


@router.post("/coupon/checkout", response_model=CouponCheckoutResponse)
async def coupon_checkout(
    body: CouponCheckoutRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: AsyncSession | None = Depends(_get_payments_db_session),
) -> CouponCheckoutResponse:
    mode = _get_payments_mode()
    if mode != "coupon":
        raise HTTPException(status_code=403, detail="Coupon checkout is disabled when PAYMENTS_MODE is not 'coupon'.")

    normalized = (body.coupon_code or "").strip()
    if normalized != "WAOOAW100":
        raise HTTPException(status_code=400, detail="Invalid coupon code.")

    gstin = (body.gstin or "").strip().upper() or None
    if gstin is not None:
        if not re.fullmatch(r"[0-9A-Z]{15}", gstin):
            raise HTTPException(status_code=400, detail="Invalid GSTIN.")

    fingerprint = {
        "coupon_code": normalized,
        "agent_id": body.agent_id,
        "duration": body.duration,
        "customer_id": body.customer_id,
        "gstin": gstin,
    }

    cache_key = None
    if idempotency_key:
        # Scope idempotency key by customer_id to avoid accidental collisions.
        cache_key = f"{body.customer_id or 'anon'}::{idempotency_key.strip()}"
        if cache_key in _idempotency_cache:
            if _idempotency_fingerprint.get(cache_key) != fingerprint:
                raise HTTPException(status_code=409, detail="Idempotency-Key reuse with different payload.")
            cached = _idempotency_cache[cache_key]
            return CouponCheckoutResponse(**cached)

    now = datetime.now(timezone.utc)

    order_id = f"ORDER-{uuid4()}"
    subscription_id = f"SUB-{uuid4()}"

    period_end = _duration_to_period_end(body.duration, now)

    _orders[order_id] = _OrderRecord(
        order_id=order_id,
        payment_provider="coupon",
        amount=0,
        currency="INR",
        agent_id=body.agent_id,
        duration=body.duration,
        customer_id=body.customer_id,
        gstin=gstin,
        status="paid",
        created_at=now,
        paid_at=now,
    )

    _subscriptions[subscription_id] = _SubscriptionRecord(
        subscription_id=subscription_id,
        agent_id=body.agent_id,
        duration=body.duration,
        customer_id=body.customer_id,
        status="active",
        current_period_start=now,
        current_period_end=period_end,
    )

    try:
        await _persist_subscription_to_db_if_enabled(db=db, record=_subscriptions[subscription_id], now=now)
    except Exception:
        # Phase-1 best-effort: do not block checkout on persistence.
        pass

    # HIRE-2.9 + BILL-1 (Phase-1): best-effort receipt issuance for paid orders.
    # BILL-1: invoice issuance is controlled via env flag (GST formatting can be disabled
    # while still collecting GST-related fields elsewhere).
    try:
        customer_id = (body.customer_id or "").strip()
        if customer_id:
            from api.v1.receipts_simple import create_receipt_for_paid_order

            create_receipt_for_paid_order(
                customer_id=customer_id,
                order_id=order_id,
                subscription_id=subscription_id,
                amount=0,
                currency="INR",
                agent_id=body.agent_id,
                duration=body.duration,
            )

            if _should_issue_gst_invoice():
                from api.v1.invoices_simple import create_invoice_for_paid_order

                create_invoice_for_paid_order(
                    customer_id=customer_id,
                    order_id=order_id,
                    subscription_id=subscription_id,
                    amount=0,
                    currency="INR",
                    agent_id=body.agent_id,
                    duration=body.duration,
                    customer_gstin=gstin,
                )
    except Exception:
        # Phase-1 best-effort: do not block checkout on artifact creation.
        pass

    response = CouponCheckoutResponse(
        order_id=order_id,
        subscription_id=subscription_id,
        coupon_code=normalized,
        agent_id=body.agent_id,
        duration=body.duration,
    )

    # NOTIF-1.1: emit payment success (best-effort).
    try:
        get_notification_event_store().append(
            NotificationEventRecord(
                event_type="payment_success",
                customer_id=(body.customer_id or None),
                order_id=order_id,
                subscription_id=subscription_id,
                metadata={
                    "payment_provider": "coupon",
                    "coupon_code": normalized,
                    "agent_id": body.agent_id,
                    "duration": body.duration,
                    "amount": 0,
                    "currency": "INR",
                },
            )
        )
    except Exception:
        pass

    if cache_key:
        _idempotency_cache[cache_key] = response.model_dump()
        _idempotency_fingerprint[cache_key] = fingerprint

    return response
