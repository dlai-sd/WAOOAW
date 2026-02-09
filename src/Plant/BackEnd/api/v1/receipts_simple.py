"""Receipts API (Phase-1 simple implementation).

HIRE-2.9 (billing artifacts):
- Provide a receipt artifact for paid orders.
- Expose customer-scoped receipt list + retrieval + HTML download.

This is an in-memory implementation intended to unblock CP flows in lower envs.
A DB-backed version can replace this later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


Currency = Literal["INR"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReceiptLineItem(BaseModel):
    description: str
    quantity: int = Field(default=1, ge=1)
    unit_amount: int = Field(default=0, ge=0, description="Minor units, e.g. paise")

    @property
    def line_amount(self) -> int:
        return int(self.quantity) * int(self.unit_amount)


class ReceiptRecord(BaseModel):
    receipt_id: str
    receipt_number: str
    created_at: datetime

    customer_id: str
    order_id: str
    subscription_id: str

    currency: Currency = "INR"
    total_amount: int = 0

    payment_status: str = "paid"
    items: list[ReceiptLineItem] = Field(default_factory=list)


class ReceiptListResponse(BaseModel):
    receipts: list[ReceiptRecord]


_receipts_by_id: dict[str, ReceiptRecord] = {}
_receipts_by_order_id: dict[str, str] = {}
_receipt_seq_by_ymd: dict[str, int] = {}


router = APIRouter(prefix="/receipts", tags=["receipts"])


def _next_receipt_number(now: datetime) -> str:
    ymd = now.strftime("%Y%m%d")
    seq = _receipt_seq_by_ymd.get(ymd, 0) + 1
    _receipt_seq_by_ymd[ymd] = seq
    return f"RCT-{ymd}-{seq:04d}"


def create_receipt_for_paid_order(
    *,
    customer_id: str,
    order_id: str,
    subscription_id: str,
    amount: int,
    currency: str,
    agent_id: str,
    duration: str,
) -> ReceiptRecord:
    """Create (or return existing) receipt for an order."""

    normalized_customer_id = (customer_id or "").strip()
    if not normalized_customer_id:
        raise ValueError("customer_id is required")

    existing_receipt_id = _receipts_by_order_id.get(order_id)
    if existing_receipt_id:
        return _receipts_by_id[existing_receipt_id]

    now = _utc_now()
    receipt_id = f"RCT-ID-{uuid4()}"
    receipt_number = _next_receipt_number(now)

    items = [
        ReceiptLineItem(
            description=f"WAOOAW agent hire: {agent_id} ({duration})",
            quantity=1,
            unit_amount=int(amount),
        )
    ]
    total_amount = sum(i.line_amount for i in items)

    record = ReceiptRecord(
        receipt_id=receipt_id,
        receipt_number=receipt_number,
        created_at=now,
        customer_id=normalized_customer_id,
        order_id=order_id,
        subscription_id=subscription_id,
        currency=(currency if currency == "INR" else "INR"),
        total_amount=total_amount,
        items=items,
    )

    _receipts_by_id[receipt_id] = record
    _receipts_by_order_id[order_id] = receipt_id
    return record


def _require_customer_id(customer_id: str | None) -> str:
    normalized = (customer_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="customer_id is required")
    return normalized


def _get_receipt_or_404(receipt_id: str) -> ReceiptRecord:
    record = _receipts_by_id.get(receipt_id)
    if not record:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return record


def _render_receipt_html(record: ReceiptRecord) -> str:
    item_rows = "\n".join(
        f"<tr><td>{i.description}</td><td>{i.quantity}</td><td>{i.unit_amount}</td><td>{i.line_amount}</td></tr>"
        for i in record.items
    )

    return (
        "<!doctype html>"
        "<html><head><meta charset='utf-8'><title>Receipt</title></head><body>"
        f"<h1>Receipt</h1>"
        f"<p><strong>Receipt #</strong>: {record.receipt_number}</p>"
        f"<p><strong>Receipt ID</strong>: {record.receipt_id}</p>"
        f"<p><strong>Date</strong>: {record.created_at.isoformat()}</p>"
        f"<hr/>"
        f"<p><strong>Customer ID</strong>: {record.customer_id}</p>"
        f"<p><strong>Order</strong>: {record.order_id}</p>"
        f"<p><strong>Subscription</strong>: {record.subscription_id}</p>"
        f"<hr/>"
        "<table border='1' cellspacing='0' cellpadding='6'>"
        "<thead><tr><th>Description</th><th>Qty</th><th>Unit</th><th>Amount</th></tr></thead>"
        f"<tbody>{item_rows}</tbody>"
        "</table>"
        f"<p><strong>Total</strong>: {record.total_amount} {record.currency}</p>"
        "</body></html>"
    )


@router.get("", response_model=ReceiptListResponse)
async def list_receipts(customer_id: str | None = None) -> ReceiptListResponse:
    normalized = _require_customer_id(customer_id)

    receipts = [r for r in _receipts_by_id.values() if r.customer_id == normalized]
    receipts.sort(key=lambda r: r.created_at, reverse=True)
    return ReceiptListResponse(receipts=receipts)


@router.get("/by-order/{order_id}", response_model=ReceiptRecord)
async def get_receipt_by_order(order_id: str, customer_id: str | None = None) -> ReceiptRecord:
    normalized = _require_customer_id(customer_id)

    receipt_id = _receipts_by_order_id.get(order_id)
    if not receipt_id:
        raise HTTPException(status_code=404, detail="Receipt not found")

    record = _get_receipt_or_404(receipt_id)
    if record.customer_id != normalized:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return record


@router.get("/{receipt_id}", response_model=ReceiptRecord)
async def get_receipt(receipt_id: str, customer_id: str | None = None) -> ReceiptRecord:
    normalized = _require_customer_id(customer_id)

    record = _get_receipt_or_404(receipt_id)
    if record.customer_id != normalized:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return record


@router.get("/{receipt_id}/html")
async def download_receipt_html(receipt_id: str, customer_id: str | None = None) -> HTMLResponse:
    normalized = _require_customer_id(customer_id)

    record = _get_receipt_or_404(receipt_id)
    if record.customer_id != normalized:
        raise HTTPException(status_code=404, detail="Receipt not found")

    html = _render_receipt_html(record)
    headers = {"Content-Disposition": f'attachment; filename="{record.receipt_number}.html"'}
    return HTMLResponse(content=html, headers=headers)
