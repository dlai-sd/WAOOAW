"""Customer APIs.

REG-1.5: Customer account entity + persistence.

Minimal endpoints:
- Idempotent create-by-email (upsert)
- Lookup by email

Auth is intentionally not enforced yet; Gateway story (REG-1.6) will layer policy.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.exceptions import DuplicateEntityError
from schemas.customer import CustomerCreate, CustomerResponse, CustomerUpsertResponse
from services.customer_service import CustomerService
from services.security_audit import SecurityAuditRecord, SecurityAuditStore, get_security_audit_store
from services.security_throttle import SecurityThrottle, get_security_throttle


router = APIRouter(prefix="/customers", tags=["customers"])


def get_customer_service(db: AsyncSession = Depends(get_db_session)) -> CustomerService:
    return CustomerService(db)


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # First entry is the original client in standard proxy chains.
        return forwarded.split(",")[0].strip() or None

    if request.client is None:
        return None
    return request.client.host


@router.post("", response_model=CustomerUpsertResponse)
async def upsert_customer(
    request: Request,
    response: Response,
    payload: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
    throttle: SecurityThrottle = Depends(get_security_throttle),
    audit: SecurityAuditStore = Depends(get_security_audit_store),
) -> CustomerUpsertResponse:
    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")
    email = str(payload.email).strip().lower()

    # Throttle on both IP and email to reduce abuse.
    for scope, subject in (
        ("customer_upsert:ip", ip or "unknown"),
        ("customer_upsert:email", email),
    ):
        decision = throttle.check(scope=scope, subject=subject)
        if not decision.allowed:
            retry = decision.retry_after_seconds

            audit.append(
                SecurityAuditRecord(
                    event_type="throttle_block",
                    ip_address=ip,
                    user_agent=user_agent,
                    email=email,
                    http_method=request.method,
                    path=str(request.url.path),
                    success=False,
                    detail=decision.reason,
                    metadata={
                        "scope": scope,
                        "retry_after_seconds": retry,
                    },
                )
            )
            headers = {"Retry-After": str(int(retry))} if retry is not None else None
            raise HTTPException(status_code=429, detail="Too many attempts", headers=headers)

    try:
        customer, created = await service.upsert_by_email(payload)
    except DuplicateEntityError as exc:
        audit.append(
            SecurityAuditRecord(
                event_type="customer_upsert_conflict",
                ip_address=ip,
                user_agent=user_agent,
                email=email,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail=str(exc),
                metadata={
                    "phone": payload.phone,
                },
            )
        )
        raise

    audit.append(
        SecurityAuditRecord(
            event_type="customer_upsert",
            ip_address=ip,
            user_agent=user_agent,
            email=email,
            http_method=request.method,
            path=str(request.url.path),
            success=True,
            metadata={
                "created": bool(created),
                "customer_id": str(customer.id),
            },
        )
    )

    return CustomerUpsertResponse(
        created=created,
        customer_id=str(customer.id),
        email=customer.email,
        phone=customer.phone,
        full_name=customer.full_name,
        business_name=customer.business_name,
        business_industry=customer.business_industry,
        business_address=customer.business_address,
        website=customer.website,
        gst_number=customer.gst_number,
        preferred_contact_method=customer.preferred_contact_method,
        consent=bool(customer.consent),
    )


@router.get("/lookup", response_model=CustomerResponse)
async def lookup_customer(
    email: EmailStr,
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    customer = await service.get_by_email(str(email).strip().lower())
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    return CustomerResponse(
        customer_id=str(customer.id),
        email=customer.email,
        phone=customer.phone,
        full_name=customer.full_name,
        business_name=customer.business_name,
        business_industry=customer.business_industry,
        business_address=customer.business_address,
        website=customer.website,
        gst_number=customer.gst_number,
        preferred_contact_method=customer.preferred_contact_method,
        consent=bool(customer.consent),
    )
