"""Customer APIs.

REG-1.5: Customer account entity + persistence.

Minimal endpoints:
- Idempotent create-by-email (upsert)
- Lookup by email
- GDPR erasure (E2-S1, Iteration 6) — admin only

Auth is intentionally not enforced on upsert/lookup; Gateway story (REG-1.6) will
layer policy. Erasure always requires admin JWT.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status as http_status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session, get_read_db_session
from core.exceptions import (
    DuplicateEntityError,
    JWTTokenExpiredError,
    JWTInvalidSignatureError,
    JWTInvalidTokenError,
)
from core.security import verify_token
from schemas.audit_log import AuditEventCreate
from schemas.customer import CustomerCreate, CustomerResponse, CustomerUpsertResponse
from services.audit_log_service import AuditLogService
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

    # E4-S1: Publish customer.registered domain event on first creation
    if created:
        try:
            from worker.tasks.registration_tasks import handle_customer_registered
            handle_customer_registered.delay(
                customer_id=str(customer.id),
                email=customer.email,
                full_name=customer.full_name or "",
                business_name=customer.business_name or "",
                registered_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception:  # noqa: BLE001 — broker unavailability must never block registration
            import logging as _log
            _log.getLogger(__name__).warning(
                "customers: could not enqueue handle_customer_registered for customer_id=%s",
                customer.id,
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


def get_read_customer_service(
    db: AsyncSession = Depends(get_read_db_session),  # E1-S2 (It-7): read replica
) -> CustomerService:
    """CustomerService backed by read replica — for lookup/read endpoints."""
    return CustomerService(db)


@router.get("/lookup", response_model=CustomerResponse)
async def lookup_customer(
    email: EmailStr,
    service: CustomerService = Depends(get_read_customer_service),  # E1-S2: replica
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

# ---------------------------------------------------------------------------
# E2-S1 (Iteration 6): GDPR Right to Erasure
# ---------------------------------------------------------------------------


def _require_admin_jwt(request: Request) -> Dict[str, Any]:
    """FastAPI dependency: require a valid JWT with admin role."""
    auth = (
        request.headers.get("X-Original-Authorization")
        or request.headers.get("Authorization")
        or ""
    )
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
        )
    try:
        claims = verify_token(parts[1])
    except (JWTTokenExpiredError, JWTInvalidSignatureError, JWTInvalidTokenError):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    if not claims:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    roles = claims.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]
    if "admin" not in roles:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return claims


class ErasureRequest(BaseModel):
    """Optional body for the erasure endpoint."""

    reason: Optional[str] = None


@router.delete(
    "/{customer_id}/erase",
    status_code=200,
    summary="GDPR erasure — anonymise all PII for a customer (admin only)",
)
async def erase_customer(
    request: Request,
    customer_id: str,
    body: ErasureRequest = ErasureRequest(),
    db: AsyncSession = Depends(get_db_session),
    _claims: Dict[str, Any] = Depends(_require_admin_jwt),
) -> Dict[str, str]:
    """E2-S1 (Iteration 6): GDPR Right to Erasure.

    Anonymises all PII for a customer across:
    - customer_entity table
    - audit_logs table
    - otp_sessions table

    Returns 200 on success, 404 if not found, 409 if already erased.
    """
    service = CustomerService(db)
    audit_svc = AuditLogService(db)

    # Resolve customer before erasure so we have the ID for audit records
    customer = await service.get_by_id(customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    if customer.deleted_at is not None:
        raise HTTPException(
            status_code=409,
            detail="Customer already erased",
            headers={"X-Error-Code": "CUSTOMER_ALREADY_ERASED"},
        )

    admin_user_id = _claims.get("sub") or _claims.get("user_id")

    # E2-S3: audit — erasure requested
    await audit_svc.log_event(
        AuditEventCreate(
            screen="admin",
            action="erasure_requested",
            outcome="success",
            email="[SYSTEM]",
            user_id=admin_user_id,
            metadata={
                "customer_id": customer_id,
                "reason": body.reason,
                "requested_by": admin_user_id,
            },
        )
    )

    try:
        await service.erase(customer_id, reason=body.reason)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    # E2-S3: audit — erasure complete
    await audit_svc.log_event(
        AuditEventCreate(
            screen="admin",
            action="erasure_complete",
            outcome="success",
            email="[SYSTEM]",
            user_id=admin_user_id,
            metadata={"customer_id": customer_id},
        )
    )

    return {"status": "erased", "customer_id": customer_id}
