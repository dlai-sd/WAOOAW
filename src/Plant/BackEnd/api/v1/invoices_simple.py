"""Invoices API (Phase-1 simple implementation).

BILL-1 (GST invoicing day-1):
- Issue an invoice artifact for paid orders/subscriptions.
- Expose customer-scoped invoice list + retrieval + HTML download.

This is an in-memory implementation intended to unblock CP flows in lower envs.
A DB-backed version can replace this later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


Currency = Literal["INR"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _seller_state_code() -> str:
    # Maharashtra default (27). Override in real envs.
    return ("%s" % ((__import__("os").getenv("SELLER_GST_STATE_CODE") or "27"))).strip() or "27"


def _seller_gstin() -> str | None:
    v = (__import__("os").getenv("SELLER_GSTIN") or "").strip()
    return v or None


def _seller_legal_name() -> str:
    return ((__import__("os").getenv("SELLER_LEGAL_NAME") or "WAOOAW")).strip() or "WAOOAW"


def _infer_state_code_from_gstin(gstin: str | None) -> str | None:
    if not gstin:
        return None
    normalized = gstin.strip()
    if len(normalized) < 2:
        return None
    prefix = normalized[:2]
    return prefix if prefix.isdigit() else None


class InvoiceLineItem(BaseModel):
    description: str
    quantity: int = Field(default=1, ge=1)
    unit_amount: int = Field(default=0, ge=0, description="Minor units, e.g. paise")

    @property
    def line_amount(self) -> int:
        return int(self.quantity) * int(self.unit_amount)


class InvoiceRecord(BaseModel):
    invoice_id: str
    invoice_number: str
    created_at: datetime

    customer_id: str
    order_id: str
    subscription_id: str

    currency: Currency = "INR"

    # Seller (issuer)
    seller_legal_name: str
    seller_gstin: Optional[str] = None
    seller_state_code: str

    # Customer details (best-effort)
    customer_business_name: Optional[str] = None
    customer_business_address: Optional[str] = None
    customer_gstin: Optional[str] = None
    customer_state_code: Optional[str] = None

    # Tax + totals (minor units)
    subtotal_amount: int = 0
    cgst_amount: int = 0
    sgst_amount: int = 0
    igst_amount: int = 0
    total_amount: int = 0

    tax_regime: str = "GST"
    tax_type: str = "none"  # cgst_sgst | igst | none

    items: list[InvoiceLineItem] = Field(default_factory=list)


class InvoiceListResponse(BaseModel):
    invoices: list[InvoiceRecord]


_invoices_by_id: dict[str, InvoiceRecord] = {}
_invoices_by_order_id: dict[str, str] = {}
_invoice_seq_by_ymd: dict[str, int] = {}


def _next_invoice_number(now: datetime) -> str:
    ymd = now.strftime("%Y%m%d")
    seq = _invoice_seq_by_ymd.get(ymd, 0) + 1
    _invoice_seq_by_ymd[ymd] = seq
    return f"INV-{ymd}-{seq:04d}"


def _compute_gst_breakdown(*, taxable_amount: int, customer_gstin: str | None) -> tuple[str, int, int, int, int]:
    """Compute GST split based on GSTIN state code (best-effort).

    Assumptions (Phase-1):
    - taxable_amount is pre-tax.
    - GST rate is 18% (placeholder default).
    - If customer GSTIN state code matches seller state code -> CGST+SGST.
      Else -> IGST.

    Returns: (tax_type, cgst, sgst, igst, total)
    """

    rate_bps = 1800  # 18.00%
    gst_amount = (taxable_amount * rate_bps) // 10000

    customer_state = _infer_state_code_from_gstin(customer_gstin)
    if not customer_state:
        return ("none", 0, 0, 0, taxable_amount)

    if customer_state == _seller_state_code():
        half = gst_amount // 2
        cgst = half
        sgst = gst_amount - half
        total = taxable_amount + gst_amount
        return ("cgst_sgst", cgst, sgst, 0, total)

    total = taxable_amount + gst_amount
    return ("igst", 0, 0, gst_amount, total)


def create_invoice_for_paid_order(
    *,
    customer_id: str,
    order_id: str,
    subscription_id: str,
    amount: int,
    currency: str,
    agent_id: str,
    duration: str,
    customer_business_name: str | None = None,
    customer_business_address: str | None = None,
    customer_gstin: str | None = None,
) -> InvoiceRecord:
    """Create (or return existing) invoice for an order."""

    normalized_customer_id = (customer_id or "").strip()
    if not normalized_customer_id:
        raise ValueError("customer_id is required")

    existing_invoice_id = _invoices_by_order_id.get(order_id)
    if existing_invoice_id:
        return _invoices_by_id[existing_invoice_id]

    now = _utc_now()
    invoice_id = f"INV-ID-{uuid4()}"
    invoice_number = _next_invoice_number(now)

    items = [
        InvoiceLineItem(
            description=f"WAOOAW agent hire: {agent_id} ({duration})",
            quantity=1,
            unit_amount=int(amount),
        )
    ]
    subtotal_amount = sum(i.line_amount for i in items)

    tax_type, cgst, sgst, igst, total = _compute_gst_breakdown(
        taxable_amount=subtotal_amount,
        customer_gstin=customer_gstin,
    )

    record = InvoiceRecord(
        invoice_id=invoice_id,
        invoice_number=invoice_number,
        created_at=now,
        customer_id=normalized_customer_id,
        order_id=order_id,
        subscription_id=subscription_id,
        currency=(currency if currency == "INR" else "INR"),
        seller_legal_name=_seller_legal_name(),
        seller_gstin=_seller_gstin(),
        seller_state_code=_seller_state_code(),
        customer_business_name=customer_business_name,
        customer_business_address=customer_business_address,
        customer_gstin=(customer_gstin.strip() if customer_gstin else None),
        customer_state_code=_infer_state_code_from_gstin(customer_gstin),
        subtotal_amount=subtotal_amount,
        cgst_amount=cgst,
        sgst_amount=sgst,
        igst_amount=igst,
        total_amount=total,
        tax_type=tax_type,
        items=items,
    )

    _invoices_by_id[invoice_id] = record
    _invoices_by_order_id[order_id] = invoice_id
    return record


def _require_customer_id(customer_id: str | None) -> str:
    normalized = (customer_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="customer_id is required")
    return normalized


def _get_invoice_or_404(invoice_id: str) -> InvoiceRecord:
    record = _invoices_by_id.get(invoice_id)
    if not record:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return record


def _render_invoice_html(record: InvoiceRecord) -> str:
    # Phase-1 minimal artifact; CP can offer a download button.
    # Avoid styling hard-codes here; keep it plain and portable.
    item_rows = "\n".join(
        f"<tr><td>{i.description}</td><td>{i.quantity}</td><td>{i.unit_amount}</td><td>{i.line_amount}</td></tr>"
        for i in record.items
    )

    return (
        "<!doctype html>"
        "<html><head><meta charset='utf-8'><title>Tax Invoice</title></head><body>"
        f"<h1>Tax Invoice</h1>"
        f"<p><strong>Invoice #</strong>: {record.invoice_number}</p>"
        f"<p><strong>Invoice ID</strong>: {record.invoice_id}</p>"
        f"<p><strong>Date</strong>: {record.created_at.isoformat()}</p>"
        f"<hr/>"
        f"<p><strong>Seller</strong>: {record.seller_legal_name}</p>"
        f"<p><strong>Seller GSTIN</strong>: {record.seller_gstin or 'N/A'}</p>"
        f"<p><strong>Customer ID</strong>: {record.customer_id}</p>"
        f"<p><strong>Customer GSTIN</strong>: {record.customer_gstin or 'N/A'}</p>"
        f"<p><strong>Order</strong>: {record.order_id}</p>"
        f"<p><strong>Subscription</strong>: {record.subscription_id}</p>"
        f"<hr/>"
        "<table border='1' cellspacing='0' cellpadding='6'>"
        "<thead><tr><th>Description</th><th>Qty</th><th>Unit</th><th>Amount</th></tr></thead>"
        f"<tbody>{item_rows}</tbody>"
        "</table>"
        f"<p><strong>Subtotal</strong>: {record.subtotal_amount} {record.currency}</p>"
        f"<p><strong>CGST</strong>: {record.cgst_amount} {record.currency}</p>"
        f"<p><strong>SGST</strong>: {record.sgst_amount} {record.currency}</p>"
        f"<p><strong>IGST</strong>: {record.igst_amount} {record.currency}</p>"
        f"<p><strong>Total</strong>: {record.total_amount} {record.currency}</p>"
        "</body></html>"
    )


router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(customer_id: str | None = None) -> InvoiceListResponse:
    cid = _require_customer_id(customer_id)
    invoices = [inv for inv in _invoices_by_id.values() if inv.customer_id == cid]
    invoices.sort(key=lambda i: i.created_at)
    return InvoiceListResponse(invoices=invoices)


@router.get("/by-order/{order_id}", response_model=InvoiceRecord)
async def get_invoice_by_order(order_id: str, customer_id: str | None = None) -> InvoiceRecord:
    cid = _require_customer_id(customer_id)
    invoice_id = _invoices_by_order_id.get(order_id)
    if not invoice_id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    record = _get_invoice_or_404(invoice_id)
    if record.customer_id != cid:
        raise HTTPException(status_code=403, detail="Invoice does not belong to customer")
    return record


@router.get("/{invoice_id}", response_model=InvoiceRecord)
async def get_invoice(invoice_id: str, customer_id: str | None = None) -> InvoiceRecord:
    cid = _require_customer_id(customer_id)
    record = _get_invoice_or_404(invoice_id)
    if record.customer_id != cid:
        raise HTTPException(status_code=403, detail="Invoice does not belong to customer")
    return record


@router.get("/{invoice_id}/html")
async def download_invoice_html(invoice_id: str, customer_id: str | None = None) -> HTMLResponse:
    cid = _require_customer_id(customer_id)
    record = _get_invoice_or_404(invoice_id)
    if record.customer_id != cid:
        raise HTTPException(status_code=403, detail="Invoice does not belong to customer")

    html = _render_invoice_html(record)
    headers = {"Content-Disposition": f"attachment; filename={record.invoice_number}.html"}
    return HTMLResponse(content=html, headers=headers)
