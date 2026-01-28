"""Auth routes for Platform Portal.

Implements Option 2:
- Frontend uses Google OAuth to get a Google ID token (credential)
- PP backend verifies it with Google
- PP backend issues a WAOOAW access token (JWT) that Plant Gateway accepts
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from core.config import settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


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
    if not app_settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: set GOOGLE_CLIENT_ID",
        )

    url = "https://oauth2.googleapis.com/tokeninfo"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params={"id_token": credential})

    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credential")

    data = resp.json()
    aud = data.get("aud")
    email = data.get("email")
    email_verified = data.get("email_verified")
    sub = data.get("sub")

    if aud != app_settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google credential has wrong audience")
    if not email or not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google credential missing email/sub")
    if str(email_verified).lower() not in {"true", "1"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Google email not verified")
    if not _allowed_email(app_settings, email):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not allowed")

    return data


def _issue_waooaw_access_token(app_settings: settings.__class__, *, user_id: str, email: str) -> TokenResponse:
    if not app_settings.JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth not configured: set JWT_SECRET",
        )

    now = int(time.time())
    exp = now + int(app_settings.ACCESS_TOKEN_EXPIRE_MINUTES) * 60
    issuer = getattr(app_settings, "JWT_ISSUER", "waooaw.com")

    # Default roles: admin for PP console. Make this configurable later.
    roles: List[str] = ["admin"]

    payload: Dict[str, Any] = {
        "user_id": user_id,
        "email": email,
        "roles": roles,
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
        user={"id": user_id, "email": email, "roles": roles},
    )


@router.post("/google/verify", response_model=TokenResponse)
async def google_verify(
    req: GoogleVerifyRequest,
    app_settings: settings.__class__ = Depends(get_settings),
) -> TokenResponse:
    """Verify Google ID token and exchange it for a WAOOAW access token."""
    google_claims = await _verify_google_id_token(app_settings, req.credential)
    user_id = str(google_claims.get("sub"))
    email = str(google_claims.get("email"))
    return _issue_waooaw_access_token(app_settings, user_id=user_id, email=email)


@router.post("/dev-token", response_model=TokenResponse)
async def dev_token(app_settings: settings.__class__ = Depends(get_settings)) -> TokenResponse:
    """Mint a token for local/demo smoke tests. Disabled in prod-like environments."""
    if app_settings.ENVIRONMENT in {"prod", "production"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return _issue_waooaw_access_token(app_settings, user_id="demo-user", email="demo@waooaw.com")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout() -> None:
    """Placeholder logout endpoint."""
    return None
