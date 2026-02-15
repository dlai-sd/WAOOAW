"""Auth APIs.

AUTH-1.3: Plant becomes the auth source-of-truth. These endpoints are intended
to be called by the Gateway to validate customer context.
"""

from __future__ import annotations

import json
import os
import time
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi import Form
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.security import create_access_token, verify_token
from core.exceptions import (
    CustomerNotFoundError,
    PolymorphicIdentityError,
    JWTTokenExpiredError,
    JWTInvalidSignatureError,
    JWTInvalidTokenError,
    BearerTokenMissingError,
    JWTMissingClaimError,
)
from services.customer_service import CustomerService
from services.security_audit import SecurityAuditRecord, SecurityAuditStore, get_security_audit_store

from middleware.rate_limit import InMemoryRateLimitStore


router = APIRouter(prefix="/auth", tags=["auth"])


def _token_rate_limit_per_minute() -> int:
    try:
        return int(os.getenv("AUTH_TOKEN_RATE_LIMIT_PER_MINUTE", "100").strip())
    except Exception:
        return 100


_AUTH_TOKEN_RATE_STORE = InMemoryRateLimitStore()


def _load_oauth_clients() -> dict[str, str]:
    """Load allowed OAuth clients from environment."""

    raw_json = os.getenv("PLANT_OAUTH_CLIENTS_JSON")
    if raw_json:
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, dict):
                normalized: dict[str, str] = {}
                for key, value in parsed.items():
                    client = str(key or "").strip()
                    secret = str(value or "")
                    if client and secret:
                        normalized[client] = secret
                if normalized:
                    return normalized
        except Exception:
            pass

    client_id = (os.getenv("PLANT_OAUTH_CLIENT_ID") or "").strip()
    client_secret = os.getenv("PLANT_OAUTH_CLIENT_SECRET") or ""
    if client_id and client_secret:
        return {client_id: client_secret}

    if (os.getenv("ENVIRONMENT") or "development").strip().lower() in {"development", "dev", "local"}:
        return {"dev-client": "dev-secret"}

    return {}


def _enforce_oauth_client(client_id: str, client_secret: str) -> None:
    allowed = _load_oauth_clients()
    expected = allowed.get((client_id or "").strip())
    if not expected or expected != (client_secret or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OAuth client credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _enforce_token_rate_limit(tenant_id: str) -> None:
    tenant = (tenant_id or "").strip() or "anonymous"
    limit = _token_rate_limit_per_minute()
    count, reset = _AUTH_TOKEN_RATE_STORE.increment(f"tenant:{tenant}:minute", 60)
    if count > limit:
        retry_after = max(0, reset - int(time.time()))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


def get_customer_service(db: AsyncSession = Depends(get_db_session)) -> CustomerService:
    return CustomerService(db)


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None

    if request.client is None:
        return None
    return request.client.host


def _get_bearer_token(request: Request) -> str:
    """
    Extract Bearer token from Authorization header.
    
    Checks both X-Original-Authorization (from gateway) and Authorization headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Extracted JWT token
        
    Raises:
        BearerTokenMissingError: If header is missing or malformed
    """
    auth = request.headers.get("X-Original-Authorization") or request.headers.get("Authorization") or ""
    
    if not auth:
        raise BearerTokenMissingError()
    
    parts = auth.split(" ", 1)
    
    if len(parts) != 2:
        raise BearerTokenMissingError(header_value=auth)
    
    if parts[0].lower() != "bearer":
        raise BearerTokenMissingError(header_value=auth)
    
    token = parts[1].strip()
    if not token:
        raise BearerTokenMissingError(header_value=auth)
    
    return token


class TokenValidateResponse(BaseModel):
    valid: bool
    customer_id: str
    email: EmailStr


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None


@router.get("/validate", response_model=TokenValidateResponse)
async def validate_token(
    request: Request,
    service: CustomerService = Depends(get_customer_service),
    audit: SecurityAuditStore = Depends(get_security_audit_store),
) -> TokenValidateResponse:
    """
    Validate JWT token and return customer context.
    
    Called by Gateway to validate customer authentication.
    Enhanced with detailed error messages for all authentication failures.
    """
    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    # Extract Bearer token with detailed error handling
    try:
        token = _get_bearer_token(request)
    except BearerTokenMissingError as e:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_validate",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="Missing or malformed Bearer token",
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Verify JWT token with specific error types
    try:
        claims = verify_token(token)
    except JWTTokenExpiredError as e:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_validate",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="JWT token expired",
                metadata={"expired_at": e.expired_at},
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except JWTInvalidSignatureError as e:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_validate",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="JWT signature verification failed",
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except JWTInvalidTokenError as e:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_validate",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="JWT token format invalid",
                metadata={"reason": e.reason},
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Validate token type
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
                detail="Wrong token type - must be access token",
                metadata={"token_type": token_type},
            )
        )
        detail_msg = (
            f"❌ Wrong Token Type\n\n"
            f"Received token_type: {token_type}\n"
            f"Expected: 'access' or null\n\n"
            f"REQUIRED ACTION:\n"
            f"Use an access token for API authentication, not a refresh token.\n"
            f"Obtain a new access token from the authentication provider."
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail_msg)

    # Validate email claim
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
        detail_msg = (
            f"❌ JWT Missing Email Claim\n\n"
            f"PROBLEM:\n"
            f"JWT token payload must include 'email' claim for authentication.\n\n"
            f"REQUIRED ACTIONS:\n"
            f"1. Ensure authentication provider includes email in JWT payload\n"
            f"2. For Google OAuth: Request 'email' scope during authentication\n"
            f"3. Verify token payload contains: {{'email': 'user@example.com', ...}}\n\n"
            f"DEBUG:\n"
            f"Decode your token at https://jwt.io to verify claims\n"
            f"(NEVER paste real tokens on public sites in production)\n\n"
            f"DOCUMENTATION:\n"
            f"- Required claims: https://docs.waooaw.com/auth/jwt-claims"
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail_msg)

    email_norm = email.strip().lower()
    
    # Try to get customer with better error handling
    try:
        customer = await service.get_by_email(email_norm)
    except AssertionError as e:
        # SQLAlchemy polymorphic identity mismatch
        error_msg = str(e)
        if "polymorphic_identity" in error_msg.lower():
            # Extract identity from error message
            import re
            match = re.search(r"No such polymorphic_identity '([^']+)'", error_msg)
            found_identity = match.group(1) if match else "unknown"
            
            audit.append(
                SecurityAuditRecord(
                    event_type="auth_validate_error",
                    ip_address=ip,
                    user_agent=user_agent,
                    email=email_norm,
                    http_method=request.method,
                    path=str(request.url.path),
                    success=False,
                    detail=f"Polymorphic identity mismatch: found '{found_identity}', expected 'Customer'",
                )
            )
            
            detail = (
                f"Database configuration error: Customer record exists but entity_type is incorrect.\n\n"
                f"❌ Current: entity_type = '{found_identity}'\n"
                f"✅ Required: entity_type = 'Customer' (capital C)\n\n"
                f"FIX: UPDATE base_entity SET entity_type = 'Customer' "
                f"WHERE email IN (SELECT email FROM customer_entity WHERE email = '{email_norm}');\n\n"
                f"Contact system administrator or see: /docs/troubleshooting/polymorphic-identity.md"
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
        else:
            # Re-raise other assertion errors
            raise
    
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
        
        # Build actionable error message
        detail = (
            f"Customer account not found for email: {email_norm}\n\n"
            f"⚠️  REQUIRED ACTION:\n"
            f"1. Create customer record in database:\n"
            f"   - Table: base_entity + customer_entity\n"
            f"   - Email: {email_norm}\n\n"
            f"2. Sample SQL:\n"
            f"   DO $$\n"
            f"   DECLARE new_id UUID := gen_random_uuid();\n"
            f"   BEGIN\n"
            f"     INSERT INTO base_entity (id, entity_type, status)\n"
            f"     VALUES (new_id, 'Customer', 'active');\n"
            f"     \n"
            f"     INSERT INTO customer_entity (id, email, phone, full_name, business_name,\n"
            f"                                   business_industry, business_address,\n"
            f"                                   preferred_contact_method, consent)\n"
            f"     VALUES (new_id, '{email_norm}', '+91-9999999999', 'User Name',\n"
            f"             'Company Name', 'Technology', 'India', 'email', true);\n"
            f"   END $$;\n\n"
            f"3. CRITICAL: entity_type must be 'Customer' (capital C)\n\n"
            f"📖 Documentation: /docs/runbooks/customer-onboarding.md\n"
            f"🔧 Admin Portal: https://pp.demo.waooaw.com/admin/customers"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

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


@router.post("/token", response_model=OAuthTokenResponse)
async def issue_token(
    request: Request,
    grant_type: str = Form("client_credentials"),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    tenant_id: str = Form(...),
    customer_email: EmailStr | None = Form(None),
    service: CustomerService = Depends(get_customer_service),
    audit: SecurityAuditStore = Depends(get_security_audit_store),
) -> OAuthTokenResponse:
    """Issue access + refresh tokens.

    This is intentionally lightweight: it validates OAuth client credentials,
    resolves a Customer, then mints JWTs with tenant isolation claims.
    """

    if (grant_type or "").strip() != "client_credentials":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported grant_type")

    _enforce_oauth_client(client_id=client_id, client_secret=client_secret)
    _enforce_token_rate_limit(tenant_id=tenant_id)

    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")
    email_norm: str | None = customer_email.strip().lower() if customer_email else None

    # Customer lookup: prefer explicit customer_email; fallback to tenant_id if it looks like an email.
    customer = None
    if email_norm:
        customer = await service.get_by_email(email_norm)
    if customer is None and tenant_id and "@" in tenant_id:
        email_norm = tenant_id.strip().lower()
        customer = await service.get_by_email(email_norm)

    if customer is None:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_token_issue",
                ip_address=ip,
                user_agent=user_agent,
                email=email_norm,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="Customer not found",
                metadata={"tenant_id": tenant_id, "client_id": client_id},
            )
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

    claims_common: dict[str, Any] = {
        "email": (email_norm or customer.email).strip().lower(),
        "customer_id": str(customer.id),
        "tenant_id": str(tenant_id),
        "user_id": str(customer.id),
    }

    access_token = create_access_token(
        data={**claims_common, "token_type": "access"},
        expires_delta=timedelta(hours=1),
    )
    refresh_token = create_access_token(
        data={**claims_common, "token_type": "refresh"},
        expires_delta=timedelta(days=30),
    )

    audit.append(
        SecurityAuditRecord(
            event_type="auth_token_issue",
            ip_address=ip,
            user_agent=user_agent,
            email=claims_common["email"],
            http_method=request.method,
            path=str(request.url.path),
            success=True,
            metadata={"tenant_id": tenant_id, "client_id": client_id, "customer_id": str(customer.id)},
        )
    )

    return OAuthTokenResponse(access_token=access_token, expires_in=3600, refresh_token=refresh_token)


@router.post("/token/refresh", response_model=OAuthTokenResponse)
async def refresh_token(
    request: Request,
    grant_type: str = Form("refresh_token"),
    refresh_token: str = Form(...),
    tenant_id: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    audit: SecurityAuditStore = Depends(get_security_audit_store),
) -> OAuthTokenResponse:
    """Exchange a refresh token for a new access token."""

    if (grant_type or "").strip() != "refresh_token":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported grant_type")

    _enforce_oauth_client(client_id=client_id, client_secret=client_secret)
    _enforce_token_rate_limit(tenant_id=tenant_id)

    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    try:
        claims = verify_token(refresh_token)
    except JWTTokenExpiredError as e:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_token_refresh",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="JWT refresh token expired",
                metadata={"expired_at": e.expired_at, "tenant_id": tenant_id, "client_id": client_id},
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except JWTInvalidSignatureError as e:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_token_refresh",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="JWT refresh signature verification failed",
                metadata={"tenant_id": tenant_id, "client_id": client_id},
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except JWTInvalidTokenError as e:
        audit.append(
            SecurityAuditRecord(
                event_type="auth_token_refresh",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail="JWT refresh token format invalid",
                metadata={"reason": e.reason, "tenant_id": tenant_id, "client_id": client_id},
            )
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    token_type = claims.get("token_type")
    if token_type != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    decoded_tenant = str(claims.get("tenant_id") or "")
    if decoded_tenant and decoded_tenant != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")

    email = str(claims.get("email") or "").strip().lower()
    customer_id = str(claims.get("customer_id") or "").strip()
    user_id = str(claims.get("user_id") or "").strip() or customer_id
    if not email or not customer_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing required claims")

    new_access = create_access_token(
        data={
            "email": email,
            "customer_id": customer_id,
            "tenant_id": str(tenant_id),
            "user_id": user_id,
            "token_type": "access",
        },
        expires_delta=timedelta(hours=1),
    )

    audit.append(
        SecurityAuditRecord(
            event_type="auth_token_refresh",
            ip_address=ip,
            user_agent=user_agent,
            email=email,
            http_method=request.method,
            path=str(request.url.path),
            success=True,
            metadata={"tenant_id": tenant_id, "client_id": client_id, "customer_id": customer_id},
        )
    )

    return OAuthTokenResponse(access_token=new_access, expires_in=3600)
