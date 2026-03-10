"""Auth routes for Platform Portal.

Implements Option 2:
- Frontend uses Google OAuth to get a Google ID token (credential)
- PP backend verifies it with Google
- PP backend issues a WAOOAW access token (JWT) that Plant Gateway accepts
"""

from __future__ import annotations

import asyncio
import functools
import secrets
import time
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Depends, Header, HTTPException, Response, status
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from pydantic import BaseModel

from api.security import require_admin
from core.config import settings, get_settings

from core.routing import waooaw_router  # PP-N3b
from core.observability import get_pp_tracer  # E7: OTel spans
from core.metrics import pp_login_counter  # E8: Prometheus metrics
from services.audit_dependency import AuditLogger, get_audit_logger  # PP-N4

router = waooaw_router(prefix="/auth", tags=["auth"])

_tracer = get_pp_tracer()


class GoogleVerifyRequest(BaseModel):
    credential: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]


class UserProfile(BaseModel):
    id: str
    email: str
    name: str | None = None
    provider: str = "google"
    environment: str


class E2EAdminTokenRequest(BaseModel):
    email: str = "admin@waooaw.com"
    user_id: str = "pp-e2e-admin"
    roles: List[str] = ["admin"]


@router.get("/me", response_model=UserProfile)
async def me(app_settings: settings.__class__ = Depends(get_settings)) -> UserProfile:
    """Return a mock user profile; replace with real auth once backend is wired."""
    if not app_settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: set GOOGLE_CLIENT_ID",
        )

    return UserProfile(
        id="demo-user",
        email="demo@waooaw.com",
        name="Demo User",
        provider="google",
        environment=app_settings.ENVIRONMENT,
    )


def _allowed_email(app_settings: settings.__class__, email: str) -> bool:
    allowed_domains = getattr(app_settings, "ALLOWED_EMAIL_DOMAINS", "")
    domains = [d.strip().lower() for d in allowed_domains.split(",") if d.strip()]
    if not domains:
        # Default to conservative allowlist if not configured
        domains = ["dlaisd.com", "waooaw.com"]
    email_l = email.lower()
    return any(email_l.endswith("@" + d) for d in domains)


async def _verify_google_id_token(app_settings: settings.__class__, credential: str) -> Dict[str, Any]:
    """
    Verify a Google ID token using the google-auth library.

    Replaces the deprecated tokeninfo endpoint HTTP call with local JWK
    signature verification. google-auth caches Google's public JWKs, so only
    the first call makes a network round-trip to fetch them.

    Checks performed (by the library + explicit guards below):
      - RSA signature against Google's JWKs
      - aud == GOOGLE_CLIENT_ID
      - iss in {accounts.google.com, https://accounts.google.com}
      - exp not expired
      - email_verified
      - email domain in ALLOWED_EMAIL_DOMAINS
    """
    if not app_settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: set GOOGLE_CLIENT_ID",
        )

    try:
        loop = asyncio.get_event_loop()
        claims: Dict[str, Any] = await loop.run_in_executor(
            None,
            functools.partial(
                google_id_token.verify_oauth2_token,
                credential,
                google_requests.Request(),
                app_settings.GOOGLE_CLIENT_ID,
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google credential: {exc}",
        )

    email: str = claims.get("email", "")
    sub: str = claims.get("sub", "")
    email_verified = claims.get("email_verified", False)

    if not email or not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google credential missing email/sub",
        )
    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google email not verified",
        )
    if not _allowed_email(app_settings, email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not allowed",
        )

    return claims


def _issue_waooaw_access_token(
    app_settings: settings.__class__,
    *,
    user_id: str,
    email: str,
    roles: Optional[List[str]] = None,
) -> TokenResponse:
    if not app_settings.JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: set JWT_SECRET",
        )

    now = int(time.time())
    exp = now + int(app_settings.ACCESS_TOKEN_EXPIRE_MINUTES) * 60
    issuer = getattr(app_settings, "JWT_ISSUER", "waooaw.com")

    # Default roles: admin for PP console. Make this configurable later.
    effective_roles: List[str] = roles or ["admin"]

    payload: Dict[str, Any] = {
        "user_id": user_id,
        "email": email,
        "roles": effective_roles,
        "iat": now,
        "exp": exp,
        "iss": issuer,
        "sub": user_id,
        # Optional contract fields
        "customer_id": None,
        "governor_agent_id": None,
        "trial_mode": False,
        "trial_expires_at": None,
    }

    token = jwt.encode(payload, app_settings.JWT_SECRET, algorithm=app_settings.JWT_ALGORITHM)
    return TokenResponse(
        access_token=token,
        expires_in=exp - now,
        user={"id": user_id, "email": email, "roles": effective_roles},
    )


def _verify_e2e_secret(
    x_e2e_secret: str | None = Header(None),
    app_settings: settings.__class__ = Depends(get_settings),
) -> None:
    if not app_settings.ENABLE_E2E_HOOKS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not app_settings.E2E_SHARED_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E2E hooks are enabled without E2E_SHARED_SECRET",
        )
    if not x_e2e_secret or not secrets.compare_digest(x_e2e_secret, app_settings.E2E_SHARED_SECRET):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/google/verify", response_model=TokenResponse)
async def google_verify(
    req: GoogleVerifyRequest,
    app_settings: settings.__class__ = Depends(get_settings),
    audit: AuditLogger = Depends(get_audit_logger),
) -> TokenResponse:
    """Verify Google ID token and exchange it for a WAOOAW access token."""
    with _tracer.start_as_current_span("pp.auth.google_verify") as span:
        if hasattr(span, "set_attribute"):
            span.set_attribute("pp.auth.provider", "google")
        google_claims = await _verify_google_id_token(app_settings, req.credential)
        user_id = str(google_claims.get("sub"))
        email = str(google_claims.get("email"))
        token_response = _issue_waooaw_access_token(app_settings, user_id=user_id, email=email)
        pp_login_counter.labels(outcome="success").inc()  # E8: Prometheus metric
        await audit.log(
            screen="pp_auth",
            action="google_login",
            outcome="success",
            email=email,
        )
        return token_response


@router.post("/dev-token", response_model=TokenResponse)
async def dev_token(app_settings: settings.__class__ = Depends(get_settings)) -> TokenResponse:
    """Mint a token for local/demo smoke tests. Disabled unless ENABLE_DEV_TOKEN is on."""
    if not app_settings.ENABLE_DEV_TOKEN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return _issue_waooaw_access_token(app_settings, user_id="demo-user", email="demo@waooaw.com")


@router.post("/e2e/admin-token", response_model=TokenResponse)
async def e2e_admin_token(
    payload: E2EAdminTokenRequest,
    _: None = Depends(_verify_e2e_secret),
    app_settings: settings.__class__ = Depends(get_settings),
) -> TokenResponse:
    """Mint an admin token for deterministic PP smoke tests when explicitly enabled."""
    return _issue_waooaw_access_token(
        app_settings,
        user_id=payload.user_id,
        email=payload.email.strip().lower(),
        roles=payload.roles,
    )


@router.post("/logout")
async def logout() -> Response:
    """Placeholder logout endpoint."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


class DbUpdatesTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


def _issue_db_updates_token(
    app_settings: settings.__class__,
    *,
    user_id: str,
    email: str,
    roles: List[str],
) -> DbUpdatesTokenResponse:
    if not app_settings.ENABLE_DB_UPDATES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    if not app_settings.JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: set JWT_SECRET",
        )

    now = int(time.time())
    exp = now + int(app_settings.DB_UPDATES_TOKEN_EXPIRE_MINUTES) * 60
    issuer = getattr(app_settings, "JWT_ISSUER", "waooaw.com")
    scope = getattr(app_settings, "DB_UPDATES_TOKEN_SCOPE", "db_updates")

    payload: Dict[str, Any] = {
        "user_id": user_id,
        "email": email,
        "roles": roles,
        "iat": now,
        "exp": exp,
        "iss": issuer,
        "sub": user_id,
        "scope": scope,
    }

    token = jwt.encode(payload, app_settings.JWT_SECRET, algorithm=app_settings.JWT_ALGORITHM)
    return DbUpdatesTokenResponse(access_token=token, expires_in=exp - now, scope=scope)


@router.post("/db-updates-token", response_model=DbUpdatesTokenResponse)
async def db_updates_token(
    claims: Dict[str, Any] = Depends(require_admin),
    app_settings: settings.__class__ = Depends(get_settings),
) -> DbUpdatesTokenResponse:
    """Mint a longer-lived scoped token for the DB Updates page.

    This is a break-glass mechanism intended only for dev/sandbox environments.
    It is gated behind ENABLE_DB_UPDATES and disabled in prod-like environments.
    """

    user_id = str(claims.get("sub") or claims.get("user_id") or "")
    email = str(claims.get("email") or "")
    roles = claims.get("roles") or []
    if isinstance(roles, str):
        roles = [roles]

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return _issue_db_updates_token(app_settings, user_id=user_id, email=email, roles=list(roles))
