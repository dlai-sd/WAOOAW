"""Auth APIs.

AUTH-1.3: Plant becomes the auth source-of-truth. These endpoints are intended
to be called by the Gateway to validate customer context.
"""

from __future__ import annotations

import asyncio
import functools
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Body, Depends, HTTPException, Request, Response, status
from core.routing import waooaw_router  # P-3
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from core.config import settings
from core.database import get_db_session
from core.security import (
    create_access_token,
    verify_token,
    generate_refresh_token,
    is_refresh_token_valid,
    revoke_refresh_token,
    decode_refresh_token_unverified,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_TTL_SECONDS,
)
from core.exceptions import (
    CustomerNotFoundError,
    PolymorphicIdentityError,
    JWTTokenExpiredError,
    JWTInvalidSignatureError,
    JWTInvalidTokenError,
    BearerTokenMissingError,
    JWTMissingClaimError,
    DuplicateEntityError,
)
from schemas.customer import CustomerCreate
from services.customer_service import CustomerService
from services.security_audit import SecurityAuditRecord, SecurityAuditStore, get_security_audit_store
from services.security_throttle import SecurityThrottle, get_security_throttle
from services.otp_service import OtpStore, get_otp_store
from core.observability import get_logger

router = waooaw_router(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)

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


class MobileTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api/v1/auth",
        max_age=REFRESH_TOKEN_TTL_SECONDS,
    )


async def _issue_mobile_tokens(
    response: Response,
    customer_id: str,
    email: str,
    token_version: int,
) -> MobileTokenResponse:
    now = datetime.utcnow()
    issued_at = int(now.timestamp())
    access_expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    base_claims: dict = {
        "sub": customer_id,
        "user_id": customer_id,
        "customer_id": customer_id,
        "email": email,
        "roles": ["user"],
        "iss": "waooaw.com",
        "iat": issued_at,
        "token_version": token_version,
    }

    access_token = create_access_token(base_claims.copy(), expires_delta=access_expire)
    refresh_token_str, _jti = await generate_refresh_token(
        customer_id,
        persist_in_redis=False,
    )
    _set_refresh_cookie(response, refresh_token_str)

    return MobileTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        expires_in=int(access_expire.total_seconds()),
    )


async def _refresh_token_is_revoked(jti: str) -> bool:
    try:
        return not await is_refresh_token_valid(jti)
    except Exception as exc:
        logger.warning(
            "Refresh token revocation check skipped because Redis is unavailable",
            extra={"jti": jti, "error": str(exc)},
        )
        return False


async def _best_effort_revoke_refresh_token(jti: str) -> None:
    try:
        await revoke_refresh_token(jti)
    except Exception as exc:
        logger.warning(
            "Refresh token revoke skipped because Redis is unavailable",
            extra={"jti": jti, "error": str(exc)},
        )

@router.post("/google/verify", tags=["auth", "mobile"], response_model=MobileTokenResponse)
async def google_verify_mobile(
    payload: GoogleMobileVerifyRequest,
    response: Response,
    service: CustomerService = Depends(get_customer_service),
) -> MobileTokenResponse:
    """
    Mobile Google OAuth2 login (AUTH-MOBILE-1).

    Accepts a Google idToken from the mobile app (expo-auth-session),
    verifies it with Google's tokeninfo API, finds the matching customer
    account, and issues a signed WAOOAW JWT pair.

    Request:  { id_token: str, source: "mobile" }
    Response: { access_token, refresh_token, token_type, expires_in }
    """
    # ---- Step 1: Verify idToken with Google (google-auth library) ----------
    # Uses cached JWKs — no HTTP call per login after the first request.
    # Verifies RSA signature, exp, aud (when google_client_id is configured),
    # and iss (accounts.google.com).
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: set GOOGLE_CLIENT_ID env var on the Plant backend.",
        )

    try:
        loop = asyncio.get_event_loop()
        token_info: dict = await loop.run_in_executor(
            None,
            functools.partial(
                google_id_token.verify_oauth2_token,
                payload.id_token,
                google_requests.Request(),
                settings.google_client_id,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google ID token: {exc}",
        )

    # Defence-in-depth: library already checks iss but be explicit.
    iss = token_info.get("iss", "")
    if iss not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not issued by Google.",
        )

    email = token_info.get("email", "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email claim missing from Google ID token.",
        )

    email_verified_raw = token_info.get("email_verified")
    email_verified = email_verified_raw is True or str(email_verified_raw).lower() == "true"
    if not email_verified:
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
    return await _issue_mobile_tokens(
        response=response,
        customer_id=customer_id,
        email=email,
        token_version=getattr(customer, "token_version", 1),
    )

# ---------------------------------------------------------------------------
# Mobile customer registration  (AUTH-MOBILE-REG-1)
# ---------------------------------------------------------------------------

class MobileRegistrationResponse(BaseModel):
    """Response from POST /auth/register.

    ``registration_id`` maps to the customer's internal UUID and is used by
    the client to reference this registration in subsequent OTP / sign-in calls.
    """

    registration_id: str
    email: str
    phone: str
    created: bool

@router.post("/register", tags=["auth", "mobile"])
async def register_mobile(
    request: Request,
    payload: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
    throttle: SecurityThrottle = Depends(get_security_throttle),
    audit: SecurityAuditStore = Depends(get_security_audit_store),
) -> MobileRegistrationResponse:
    """Mobile customer registration (AUTH-MOBILE-REG-1).

    Public endpoint — no JWT required.  Creates (or upserts) a customer record
    in Plant and returns a ``registration_id`` for the subsequent sign-in flow.

    Internally delegates to the same ``CustomerService.upsert_by_email`` used by
    the CP → Gateway → Plant server-to-server path but without requiring the
    ``X-CP-Registration-Key`` header, making it usable from mobile clients.

    Request body: same camelCase fields as ``CustomerCreate`` (full_name /
    fullName aliases accepted).

    Returns 200 when the account already exists (idempotent), 201 on first
    creation.  409 on a phone conflict (email is the upsert key).
    """
    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")
    email = str(payload.email).strip().lower()

    # Rate-limit on both IP and email to limit abuse of this public endpoint.
    for scope, subject in (
        ("mobile_register:ip", ip or "unknown"),
        ("mobile_register:email", email),
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
                    metadata={"scope": scope, "retry_after_seconds": retry},
                )
            )
            headers = {"Retry-After": str(int(retry))} if retry is not None else None
            raise HTTPException(status_code=429, detail="Too many attempts", headers=headers)

    try:
        customer, created = await service.upsert_by_email(payload)
    except DuplicateEntityError as exc:
        audit.append(
            SecurityAuditRecord(
                event_type="mobile_register_conflict",
                ip_address=ip,
                user_agent=user_agent,
                email=email,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail=str(exc),
                metadata={"phone": payload.phone},
            )
        )
        raise HTTPException(status_code=409, detail=str(exc))

    audit.append(
        SecurityAuditRecord(
            event_type="mobile_register",
            ip_address=ip,
            user_agent=user_agent,
            email=email,
            http_method=request.method,
            path=str(request.url.path),
            success=True,
            metadata={"created": bool(created), "customer_id": str(customer.id)},
        )
    )

    return MobileRegistrationResponse(
        registration_id=str(customer.id),
        email=customer.email,
        phone=customer.phone,
        created=created,
    )

# ---------------------------------------------------------------------------
# Mobile OTP challenge  (AUTH-MOBILE-OTP-1)
# ---------------------------------------------------------------------------

def _mask_destination(destination: str) -> str:
    """Return a partially obfuscated version of an email / phone."""
    value = (destination or "").strip()
    if "@" in value:
        name, domain = value.split("@", 1)
        if len(name) <= 2:
            return f"**@{domain}"
        return f"{name[0]}***{name[-1]}@{domain}"
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}***{value[-2:]}"

def _otp_echo_enabled() -> bool:
    """Return True if the plain OTP code should be echoed back in the response.

    Enabled in development / demo environments; suppressed in uat and production
    so codes must be delivered via the real channel.
    """
    env = (settings.environment or "").strip().lower()
    return env not in {"uat", "prod", "production"}

class OtpStartRequest(BaseModel):
    registration_id: str
    channel: Optional[str] = None  # "email" | "phone"; defaults to customer preference

class OtpStartResponse(BaseModel):
    otp_id: str
    channel: str
    destination_masked: str
    expires_in_seconds: int
    otp_code: Optional[str] = None  # Only present in dev/demo environments

@router.post("/otp/start", tags=["auth", "mobile"])
async def otp_start(
    request: Request,
    payload: OtpStartRequest,
    service: CustomerService = Depends(get_customer_service),
    otp_store: OtpStore = Depends(get_otp_store),
    audit: SecurityAuditStore = Depends(get_security_audit_store),
) -> OtpStartResponse:
    """Start an OTP challenge for a registered customer (AUTH-MOBILE-OTP-1).

    Public endpoint — no JWT required.  The ``registration_id`` is the
    ``customer.id`` UUID returned by ``POST /auth/register``.

    In development / demo environments the plain OTP code is returned in
    ``otp_code`` so the flow can be completed without a real email / SMS
    delivery provider.  In uat / production ``otp_code`` is ``null`` and the
    code is dispatched to the customer's email or phone.
    """
    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    customer = await service.get_by_id(payload.registration_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found. Please complete registration first.",
        )

    # Determine channel — caller may override, otherwise use customer preference.
    raw_channel = (payload.channel or "").strip().lower()
    channel = raw_channel if raw_channel in ("email", "phone") else customer.preferred_contact_method
    if channel not in ("email", "phone"):
        channel = "email"

    destination: Optional[str] = customer.email if channel == "email" else customer.phone
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No {channel} on file for this customer.",
        )

    if not otp_store.can_issue(destination=destination):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please wait and try again.",
        )

    from services.otp_service import OTP_TTL_SECONDS
    challenge, plain_code = otp_store.create_challenge(
        registration_id=str(customer.id),
        channel=channel,  # type: ignore[arg-type]
        destination=destination,
        ttl_seconds=OTP_TTL_SECONDS,
    )

    # Production delivery would call an email/SMS provider here.
    # For now, log so ops can see codes even in the absence of a configured provider.
    if not _otp_echo_enabled():
        import logging as _log
        _log.getLogger(__name__).warning(
            "OTP delivery not configured — code for %s (otp_id=%s) not sent",
            _mask_destination(destination),
            challenge.otp_id,
        )

    audit.append(
        SecurityAuditRecord(
            event_type="mobile_otp_start",
            ip_address=ip,
            user_agent=user_agent,
            email=customer.email,
            http_method=request.method,
            path=str(request.url.path),
            success=True,
            metadata={
                "otp_id": challenge.otp_id,
                "channel": channel,
                "customer_id": str(customer.id),
            },
        )
    )

    return OtpStartResponse(
        otp_id=challenge.otp_id,
        channel=channel,
        destination_masked=_mask_destination(destination),
        expires_in_seconds=OTP_TTL_SECONDS,
        otp_code=plain_code if _otp_echo_enabled() else None,
    )

class OtpVerifyRequest(BaseModel):
    otp_id: str
    code: str

@router.post("/otp/verify", tags=["auth", "mobile"], response_model=MobileTokenResponse)
async def otp_verify(
    request: Request,
    payload: OtpVerifyRequest,
    response: Response,
    service: CustomerService = Depends(get_customer_service),
    otp_store: OtpStore = Depends(get_otp_store),
    audit: SecurityAuditStore = Depends(get_security_audit_store),
) -> MobileTokenResponse:
    """Verify OTP and issue WAOOAW JWT tokens (AUTH-MOBILE-OTP-1).

    Public endpoint — no JWT required.  On success returns an access/refresh
    token pair identical in structure to ``POST /auth/google/verify``, so the
    mobile client uses the same token-handling path regardless of auth method.
    """
    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    ok, reason = otp_store.verify(otp_id=payload.otp_id, code=payload.code)
    if not ok:
        audit.append(
            SecurityAuditRecord(
                event_type="mobile_otp_verify_fail",
                ip_address=ip,
                user_agent=user_agent,
                http_method=request.method,
                path=str(request.url.path),
                success=False,
                detail=reason,
                metadata={"otp_id": payload.otp_id},
            )
        )
        # Map failure reasons to HTTP status codes the mobile client handles.
        # NOTE: "too many" must be checked before "invalid" — the too-many-attempts
        # reason string also contains the word "invalid".
        detail_lower = reason.lower()
        if "too many" in detail_lower:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=reason)
        if "expired" in detail_lower:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)
        if "invalid" in detail_lower:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    challenge = otp_store.get_challenge(payload.otp_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP state not found")

    customer = await service.get_by_id(challenge.registration_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer account not found",
        )

    customer_id = str(customer.id)
    token_version = getattr(customer, "token_version", 1)

    audit.append(
        SecurityAuditRecord(
            event_type="mobile_otp_verify_success",
            ip_address=ip,
            user_agent=user_agent,
            email=customer.email,
            http_method=request.method,
            path=str(request.url.path),
            success=True,
            metadata={"otp_id": payload.otp_id, "customer_id": customer_id},
        )
    )

    return await _issue_mobile_tokens(
        response=response,
        customer_id=customer_id,
        email=customer.email,
        token_version=token_version,
    )

# ---------------------------------------------------------------------------
# Silent refresh  (E1-S3)
# ---------------------------------------------------------------------------

@router.post("/refresh", tags=["auth"], response_model=MobileTokenResponse)
async def refresh_access_token(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = Body(default=None),
) -> MobileTokenResponse:
    """Issue a new access token using a refresh token from body or cookie.

    Mobile callers send the refresh token in the JSON body to match CP-style
    stateless auth. Cookie fallback is still accepted for older callers.

    Redis-backed revocation is best-effort only. If Redis is unavailable, a
    valid signed refresh token can still rotate successfully.
    """
    raw_token = (payload.refresh_token if payload else None) or request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_MISSING",
        )

    # Verify JWT signature and expiry
    try:
        claims = verify_token(raw_token)
    except JWTTokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_EXPIRED",
        )
    except (JWTInvalidSignatureError, JWTInvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_INVALID",
        )

    # Ensure this is actually a refresh token
    if claims.get("token_type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_INVALID",
        )

    jti = claims.get("jti")
    user_id = claims.get("sub")
    if not jti or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_INVALID",
        )

    if await _refresh_token_is_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="REFRESH_TOKEN_REVOKED",
        )

    await _best_effort_revoke_refresh_token(jti)
    new_refresh_token, _new_jti = await generate_refresh_token(
        user_id,
        persist_in_redis=False,
    )

    _set_refresh_cookie(response, new_refresh_token)

    # Issue new access token
    access_expire = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token({"sub": user_id}, expires_delta=access_expire)

    return MobileTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=int(access_expire.total_seconds()),
    )

# ---------------------------------------------------------------------------
# Logout  (E2-S1)
# ---------------------------------------------------------------------------

@router.post("/logout", tags=["auth"])
async def logout(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = Body(default=None),
) -> dict:
    """Invalidate the current refresh token and clear the cookie.

    E2-S1: Idempotent — always returns 200 even if no cookie is present.
    Public endpoint — user may have an expired access token at logout time.
    """
    raw_token = (payload.refresh_token if payload else None) or request.cookies.get("refresh_token")
    if raw_token:
        # Best-effort: extract jti without full validation (token may be expired)
        claims = decode_refresh_token_unverified(raw_token)
        jti = claims.get("jti")
        if jti:
            await _best_effort_revoke_refresh_token(jti)

    # Clear the cookie regardless
    response.delete_cookie("refresh_token", path="/api/v1/auth")

    return {"message": "Logged out successfully"}