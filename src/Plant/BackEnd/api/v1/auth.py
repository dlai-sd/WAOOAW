"""Auth APIs.

AUTH-1.3: Plant becomes the auth source-of-truth. These endpoints are intended
to be called by the Gateway to validate customer context.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
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


# ---------------------------------------------------------------------------
# Mobile Google OAuth2 login  (AUTH-MOBILE-1)
# ---------------------------------------------------------------------------

class GoogleMobileVerifyRequest(BaseModel):
    id_token: str
    source: str = "mobile"
    totp_code: Optional[str] = None


@router.post("/google/verify", tags=["auth", "mobile"])
async def google_verify_mobile(
    payload: GoogleMobileVerifyRequest,
    service: CustomerService = Depends(get_customer_service),
) -> dict:
    """
    Mobile Google OAuth2 login (AUTH-MOBILE-1).

    Accepts a Google idToken from the mobile app (expo-auth-session),
    verifies it with Google's tokeninfo API, finds the matching customer
    account, and issues a signed WAOOAW JWT pair.

    Request:  { id_token: str, source: "mobile" }
    Response: { access_token, refresh_token, token_type, expires_in }
    """
    # ---- Step 1: Verify idToken with Google tokeninfo --------------------
    verify_url = (
        f"https://oauth2.googleapis.com/tokeninfo?id_token={payload.id_token}"
    )
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(verify_url)
        if r.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google ID token — Google tokeninfo rejected it.",
            )
        token_info = r.json()

    email = token_info.get("email", "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email claim missing from Google ID token.",
        )
    if not token_info.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is not verified.",
        )

    # ---- Step 2: Find customer by email ----------------------------------
    customer = await service.get_by_email(email)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No WAOOAW account found for {email}. "
                "Please register at cp.waooaw.com first."
            ),
        )

    # ---- Step 3: Issue JWT pair ------------------------------------------
    customer_id = str(customer.id)
    now = datetime.utcnow()
    access_expire = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_expire = timedelta(days=7)

    base_claims: dict = {
        "sub": customer_id,
        "user_id": customer_id,
        "customer_id": customer_id,
        "email": email,
        "roles": ["user"],
        "iss": "waooaw.com",
        "iat": now,
    }

    access_token = create_access_token(
        base_claims.copy(), expires_delta=access_expire
    )
    refresh_token = create_access_token(
        {**base_claims, "token_type": "refresh"},
        expires_delta=refresh_expire,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(access_expire.total_seconds()),
    }
