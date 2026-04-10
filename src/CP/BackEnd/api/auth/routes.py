"""
Authentication API routes
Handles Google OAuth login, token management, and user info
"""

import logging
import os
import secrets
import uuid
from typing import Optional

from fastapi import Depends, Header, HTTPException, Query, Request, Response, status
from core.routing import waooaw_router  # P-3
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from api.auth.dependencies import get_current_user, verify_refresh_token
from api.auth.google_oauth import verify_google_token
from api.auth.user_store import UserStore, get_user_store
from core.config import settings
from core.jwt_handler import create_tokens
from models.user import Token, User, UserCreate
from services.plant_client import PlantClient, ServiceUnavailableError
from services.cp_2fa import (
    build_otpauth_uri,
    get_cp_2fa_store,
    verify_totp,
    FileTwoFAStore,
)
from services.cp_refresh_revocations import (
    FileCPRefreshRevocationStore,
    get_cp_refresh_revocation_store,
)
from services.audit_dependency import AuditLogger, get_audit_logger  # C2 (NFR It-2)

router = waooaw_router(prefix="/auth", tags=["authentication"])
logger = logging.getLogger(__name__)
REFRESH_COOKIE_NAME = "refresh_token"

# In-memory state storage (refresh-token revocation uses REDIS_URL when configured)
_state_store = {}


def _refresh_cookie_secure() -> bool:
    return settings.API_URL.startswith("https://") or settings.FRONTEND_URL.startswith("https://")


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        secure=_refresh_cookie_secure(),
        samesite="lax",
        path="/api/auth",
        max_age=settings.refresh_token_expire_seconds,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        httponly=True,
        secure=_refresh_cookie_secure(),
        samesite="lax",
        path="/api/auth",
    )


async def _lookup_plant_customer_id(email: str, correlation_id: str = "") -> Optional[str]:
    """Return Plant's canonical customer_id UUID for *email*, or None.

    Returns None when:
    - PLANT_GATEWAY_URL / CP_REGISTRATION_KEY not configured (local/test env).
    - Plant responds 404 (customer hasn't registered yet via OTP flow).
    - Plant is temporarily unavailable (circuit open / connect error).

    Never raises — callers must handle None gracefully.
    """
    plant_url = (os.getenv("PLANT_GATEWAY_URL") or "").strip().rstrip("/")
    registration_key = (os.getenv("CP_REGISTRATION_KEY") or "").strip()

    if not plant_url or not registration_key:
        logger.debug(
            "PLANT_GATEWAY_URL or CP_REGISTRATION_KEY not set; skipping Plant UUID lookup for %s",
            email,
        )
        return None

    headers = {
        "X-CP-Registration-Key": registration_key,
        "X-Correlation-ID": correlation_id,
    }
    _client = PlantClient(base_url=plant_url)
    try:
        resp = await _client.get(
            "/api/v1/customers/lookup",
            params={"email": email},
            headers=headers,
        )
    except ServiceUnavailableError:
        logger.warning("plant_client: circuit open during customer UUID lookup for %s", email)
        return None
    except Exception as exc:  # pragma: no cover
        logger.warning("plant_client: unexpected error looking up customer UUID for %s: %s", email, exc)
        return None

    if resp.status_code == 200:
        data = resp.json()
        cid = data.get("customer_id")
        if cid:
            logger.debug("Plant UUID lookup: email=%s -> customer_id=%s", email, cid)
        return cid

    if resp.status_code == 404:
        logger.info("Plant UUID lookup: no customer found for %s (not yet registered)", email)
        return None

    logger.warning(
        "Plant /customers/lookup returned unexpected %d for %s", resp.status_code, email
    )
    return None

class GoogleTokenRequest(BaseModel):
    """Request to verify Google ID token from frontend"""

    id_token: str
    source: str = "cp"  # cp, pp, or mobile
    totp_code: str | None = None


class E2ESessionRequest(BaseModel):
    """Request payload for deterministic E2E session bootstrapping."""

    email: str = "e2e.cp@waooaw.com"
    name: str | None = "CP E2E User"
    user_id: str | None = None
    provider_id: str | None = None


def _verify_e2e_secret(x_e2e_secret: str | None = Header(None)) -> None:
    """Enable a secret-guarded auth bootstrap path for automated smoke tests."""
    if not settings.ENABLE_E2E_HOOKS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    if not settings.E2E_SHARED_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E2E hooks are enabled without E2E_SHARED_SECRET",
        )
    if not x_e2e_secret or not secrets.compare_digest(x_e2e_secret, settings.E2E_SHARED_SECRET):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _default_e2e_user_id(email: str) -> str:
    email_lower = email.strip().lower()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"waooaw-cp-e2e:{email_lower}"))

# Helper functions for Google OAuth flow
async def google_login(source: str):
    """Initiate Google OAuth login"""
    state = secrets.token_urlsafe(32)
    _state_store[state] = source
    
    redirect_uri = f"{settings.API_URL}/auth/google/callback"
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid%20email%20profile"
        f"&state={state}"
    )
    return RedirectResponse(url=google_auth_url)

async def google_callback(code: Optional[str], state: Optional[str], error: Optional[str], user_store: UserStore):
    """Handle Google OAuth callback"""
    if error:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?error={error}", status_code=302)
    
    if not code or not state:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?error=missing_params", status_code=302)
    
    # Verify state
    source = _state_store.pop(state, None)
    if not source:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?error=invalid_state", status_code=302)
    
    try:
        import api.auth.google_oauth as google_oauth
        redirect_uri = f"{settings.API_URL}/auth/google/callback"
        user_info = await google_oauth.get_user_from_google(code, redirect_uri)
        
        user_data = UserCreate(
            email=user_info["email"],
            name=user_info.get("name"),
            picture=user_info.get("picture"),
            provider="google",
            provider_id=user_info["id"],
        )
        user = user_store.get_or_create_user(user_data)

        # Resolve Plant's canonical UUID so the JWT sub stays stable across
        # CP Backend cold starts (in-memory UserStore generates a new UUID per
        # container restart, causing hired-agent lookups to fail).
        email_lower = (user.email or "").strip().lower()
        plant_customer_id = await _lookup_plant_customer_id(email_lower)
        jwt_subject = plant_customer_id if plant_customer_id else user.id

        # Register Plant UUID as a secondary lookup key so get_current_user can
        # resolve the user by jwt_subject even though the store was created with
        # an in-memory UUID.
        if plant_customer_id:
            user = user_store.normalize_user_id(user, plant_customer_id)

        tokens = create_tokens(jwt_subject, user.email)

        response = RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}",
            status_code=302
        )
        _set_refresh_cookie(response, tokens["refresh_token"])
        return response
    except Exception:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/?error=auth_failed", status_code=302)

@router.get("/google/login")
async def google_login_route(source: str = Query("cp", description="Source application: cp, pp, or mobile")):
    return await google_login(source)

@router.get("/google/callback")
async def google_callback_route(code: Optional[str], state: Optional[str], error: Optional[str], user_store: UserStore = Depends(get_user_store)):
    return await google_callback(code, state, error, user_store)

@router.post("/google/verify", response_model=Token)
async def verify_google_id_token(
    request: GoogleTokenRequest,
    http_request: Request,
    response: Response,
    user_store: UserStore = Depends(get_user_store),
    audit: AuditLogger = Depends(get_audit_logger),  # C2 (NFR It-2)
):
    """
    Verify Google ID token from frontend Google Sign-In
    Alternative flow using Google's JavaScript library

    Args:
        request: ID token from Google Sign-In
        user_store: User storage

    Returns:
        JWT access and refresh tokens
    """
    try:
        # Verify ID token with Google
        token_info = await verify_google_token(request.id_token)

        # Create or get user
        user_data = UserCreate(
            email=token_info["email"],
            name=token_info.get("name"),
            picture=token_info.get("picture"),
            provider="google",
            provider_id=token_info["sub"],
        )

        user = user_store.get_or_create_user(user_data)

        two_fa_store = get_cp_2fa_store()
        if two_fa_store.is_enabled(user.id):
            if not request.totp_code:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="2FA required",
                )
            secret = two_fa_store.get_secret(user.id)
            if not secret or not verify_totp(secret, request.totp_code):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA code",
                )

        # Resolve Plant's canonical UUID so the JWT sub is stable across CP
        # Backend restarts (in-memory UserStore generates a new UUID per
        # container cold start, causing hired-agent lookups to fail).
        email_lower = (user.email or "").strip().lower()
        correlation_id = getattr(http_request.state, "correlation_id", "")
        plant_customer_id = await _lookup_plant_customer_id(email_lower, correlation_id)
        jwt_subject = plant_customer_id if plant_customer_id else user.id

        # Register the Plant UUID as a secondary key in the UserStore so that
        # get_current_user (which calls user_store.get_user_by_id(jwt_sub)) can
        # resolve the user even though the store was created with an in-memory UUID.
        if plant_customer_id:
            user = user_store.normalize_user_id(user, plant_customer_id)

        # Create JWT tokens using Plant's stable UUID as sub
        tokens = create_tokens(jwt_subject, user.email)
        _set_refresh_cookie(response, tokens["refresh_token"])
        await audit.log(
            "cp_auth",
            "google_login_success",
            "success",
            email=user.email,
        )
        return Token(**tokens)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify Google token: {str(e)}",
        )

@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    response: Response,
    token_data=Depends(verify_refresh_token),
    user_store: UserStore = Depends(get_user_store),
):
    """
    Refresh access token using refresh token

    Args:
        token_data: Validated refresh token data
        user_store: User storage

    Returns:
        New access and refresh tokens
    """
    # Verify user still exists in the in-memory store.
    # After a CP Backend cold start the store is empty; we must not force
    # every user to re-login in that case.  The refresh token already carries
    # the canonically-correct user_id (Plant UUID, set by the auth routes) and
    # email, so we can re-issue tokens directly when the store has no record.
    user = user_store.get_user_by_id(token_data.user_id)

    if not user:
        # Cold-start / container-restart: user object not in memory but the
        # refresh token is valid (signature + expiry already verified above).
        # Re-create a minimal user entry keyed by token_data.user_id so that
        # subsequent GET /auth/me calls find the user without forcing a re-login.
        user = user_store.get_or_create_user(
            UserCreate(
                email=token_data.email or "",
                provider="refresh_restore",
                provider_id=token_data.user_id,
            )
        )
    user = user_store.normalize_user_id(user, token_data.user_id)
    tokens = create_tokens(user.id, user.email)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return Token(**tokens)


@router.post("/e2e/session", response_model=Token)
async def create_e2e_session(
    response: Response,
    payload: E2ESessionRequest,
    user_store: UserStore = Depends(get_user_store),
    _: None = Depends(_verify_e2e_secret),
):
    """Mint a deterministic CP session for smoke tests when explicitly enabled."""
    email = payload.email.strip().lower()
    canonical_user_id = (payload.user_id or "").strip() or _default_e2e_user_id(email)
    provider_id = (payload.provider_id or "").strip() or canonical_user_id

    user = user_store.get_or_create_user(
        UserCreate(
            email=email,
            name=payload.name,
            provider="e2e",
            provider_id=provider_id,
        )
    )
    user = user_store.normalize_user_id(user, canonical_user_id)
    tokens = create_tokens(user.id, user.email)
    _set_refresh_cookie(response, tokens["refresh_token"])
    return Token(**tokens)

@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    revocations: FileCPRefreshRevocationStore = Depends(get_cp_refresh_revocation_store),
):
    """
    Logout current user
    Revocation is recorded in the local file store — CP BackEnd must not
    connect to Redis directly (platform policy).

    Args:
        current_user: Authenticated user

    Returns:
        Success message
    """
    revocations.revoke_user(current_user.id)
    _clear_refresh_cookie(response)
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information

    Args:
        current_user: Authenticated user from token

    Returns:
        User profile information
    """
    return current_user

@router.get("/health")
async def auth_health():
    """Health check for auth service"""
    return {
        "status": "healthy",
        "service": "authentication",
        "oauth_configured": bool(settings.GOOGLE_CLIENT_ID),
    }

class TwoFAEnrollResponse(BaseModel):
    enabled: bool
    secret_base32: str
    otpauth_uri: str

@router.post("/2fa/enroll", response_model=TwoFAEnrollResponse)
async def enroll_2fa(
    current_user: User = Depends(get_current_user),
    two_fa_store: FileTwoFAStore = Depends(get_cp_2fa_store),
):
    state = two_fa_store.enroll(user_id=current_user.id, email=current_user.email)
    return TwoFAEnrollResponse(
        enabled=False,
        secret_base32=state.secret_base32 or "",
        otpauth_uri=build_otpauth_uri(current_user.email, state.secret_base32 or ""),
    )

class TwoFAConfirmRequest(BaseModel):
    code: str = Field(..., min_length=1)

@router.post("/2fa/confirm")
async def confirm_2fa(
    payload: TwoFAConfirmRequest,
    current_user: User = Depends(get_current_user),
    two_fa_store: FileTwoFAStore = Depends(get_cp_2fa_store),
):
    secret = two_fa_store.get_secret(current_user.id)
    if not secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA not enrolled")
    if not verify_totp(secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")

    two_fa_store.enable(user_id=current_user.id, email=current_user.email, secret_base32=secret)
    return {"enabled": True}

class TwoFADisableRequest(BaseModel):
    code: str = Field(..., min_length=1)

@router.post("/2fa/disable")
async def disable_2fa(
    payload: TwoFADisableRequest,
    current_user: User = Depends(get_current_user),
    two_fa_store: FileTwoFAStore = Depends(get_cp_2fa_store),
):
    secret = two_fa_store.get_secret(current_user.id)
    if not secret or not two_fa_store.is_enabled(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA not enabled")
    if not verify_totp(secret, payload.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid 2FA code")

    two_fa_store.disable(user_id=current_user.id, email=current_user.email)
    return {"enabled": False}
