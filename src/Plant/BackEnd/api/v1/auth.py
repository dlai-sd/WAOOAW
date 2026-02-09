"""Auth APIs.

AUTH-1.3: Plant becomes the auth source-of-truth. These endpoints are intended
to be called by the Gateway to validate customer context.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.security import verify_token
from services.customer_service import CustomerService
from services.security_audit import SecurityAuditRecord, SecurityAuditStore, get_security_audit_store


router = APIRouter(prefix="/auth", tags=["auth"])


def get_customer_service(db: AsyncSession = Depends(get_db_session)) -> CustomerService:
    return CustomerService(db)


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None

    if request.client is None:
        return None
    return request.client.host


def _get_bearer_token(request: Request) -> str | None:
    auth = request.headers.get("X-Original-Authorization") or request.headers.get("Authorization") or ""
    parts = auth.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


class TokenValidateResponse(BaseModel):
    valid: bool
    customer_id: str
    email: EmailStr


@router.get("/validate", response_model=TokenValidateResponse)
async def validate_token(
    request: Request,
    service: CustomerService = Depends(get_customer_service),
    audit: SecurityAuditStore = Depends(get_security_audit_store),
) -> TokenValidateResponse:
    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    token = _get_bearer_token(request)
    if not token:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_validate",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="Missing Bearer token",
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    claims = verify_token(token)
    if not claims:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_validate",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="Invalid token",
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    token_type = claims.get("token_type")
    if token_type not in (None, "access"):
        audit.append(
            SecurityAuditRecord(
                event_type="auth_validate",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="Wrong token type",
                metadata={"token_type": token_type},
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email = claims.get("email")
    if not isinstance(email, str) or not email.strip():
        audit.append(
            SecurityAuditRecord(
                event_type="auth_validate",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="Token missing email claim",
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    email_norm = email.strip().lower()
    customer = await service.get_by_email(email_norm)
    if customer is None:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_validate",
                ip_address=ip,
                user_agent=user_agent,
                email=email_norm,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="Customer not found",
            )
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    audit.append(
        SecurityAuditRecord(
            event_type="auth_validate",
            ip_address=ip,
            user_agent=user_agent,
            email=email_norm,
            http_method=request.method,
            path=str(request.url.path),
            success=True,
            metadata={
                "customer_id": str(customer.id),
            },
        )
    )

    return TokenValidateResponse(valid=True, customer_id=str(customer.id), email=email_norm)
