"""
OAuth 2.0 Implementation for Platform Portal
Exact mirror of WaooawPortal's oauth_v2.py
"""

import base64
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode, urlparse

import httpx
import structlog
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from jose import jwt
from pydantic import BaseModel

from .config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"


class GoogleTokenRequest(BaseModel):
    """Request model for Google token verification"""

    token: str


def get_request_host(request: Request) -> str:
    """
    Get the actual request host, checking forwarded headers first

    GitHub Codespaces uses X-Forwarded-Host header
    """
    # Check forwarded headers first (for proxies/Codespaces)
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_host:
        return forwarded_host

    # Fallback to standard host header
    return request.headers.get("host", "")


def detect_environment(request: Request) -> str:
    """
    Detect environment from request host

    Args:
        request: FastAPI Request object

    Returns:
        Environment name: 'demo', 'uat', 'production', 'codespace', or 'development'
    """
    # Check forwarded host first (for Codespace/proxies)
    forwarded_host = request.headers.get("x-forwarded-host", "")
    host = forwarded_host or request.headers.get("host", "")

    if "app.github.dev" in host:
        return "codespace"
    elif "demo-" in host or "demo." in host:
        return "demo"
    elif "uat-" in host or "uat." in host:
        return "uat"
    elif "localhost" in host or "127.0.0.1" in host:
        return "development"
    else:
        return "production"


def encode_state(data: dict) -> str:
    """
    Encode state parameter for OAuth

    Args:
        data: Dictionary to encode (e.g., {"frontend": "https://pp.waooaw.com"})

    Returns:
        Base64-encoded JSON string
    """
    json_str = json.dumps(data)
    encoded = base64.urlsafe_b64encode(json_str.encode()).decode()
    return encoded


def decode_state(state: str) -> dict:
    """
    Decode state parameter from OAuth

    Args:
        state: Base64-encoded string

    Returns:
        Decoded dictionary
    """
    try:
        decoded = base64.urlsafe_b64decode(state.encode()).decode()
        return json.loads(decoded)
    except Exception as e:
        logger.error("state_decode_failed", error=str(e))
        return {}


def get_frontend_from_referer(request: Request, env: str) -> str:
    """
    Detect which frontend initiated OAuth from Referer header

    Args:
        request: FastAPI Request object
        env: Environment name

    Returns:
        Frontend URL that initiated the OAuth flow
    """
    referer = request.headers.get("referer", "")
    config = settings.DOMAIN_CONFIG[env]

    if not referer:
        # Default to pp (Platform Portal)
        return config.get("pp", "")

    parsed = urlparse(referer)
    referer_host = f"{parsed.scheme}://{parsed.netloc}"

    # Check which domain the user came from
    for key, url in config.items():
        if url == referer_host:
            return url

    # Default to pp if no match
    return config.get("pp", "")


def get_user_role(email: str) -> str:
    """
    Determine user role based on email

    Args:
        email: User's email address

    Returns:
        Role: 'admin', 'operator', or 'viewer'
    """
    # Admin users
    if email in ["admin@waooaw.ai", "yogeshkhandge@gmail.com"]:
        return "admin"
    # Operators (internal team)
    elif email.endswith("@waooaw.ai"):
        return "operator"
    # Default viewer (customers)
    else:
        return "viewer"


@router.get("/login")
async def oauth_login(request: Request, frontend: Optional[str] = None):
    """
    Initiate OAuth flow for Platform Portal

    Automatically detects:
    - Environment (demo/uat/prod) from hostname
    - Frontend that initiated login (defaults to 'pp')

    Args:
        frontend: Optional frontend identifier ('pp' for Platform Portal)

    Redirects to Google OAuth consent screen
    """
    # Detect environment
    env = detect_environment(request)

    # DEBUG: Log all headers
    logger.info(
        "oauth_login_initiated",
        environment=env,
        host=request.headers.get("host"),
        x_forwarded_host=request.headers.get("x-forwarded-host"),
        x_forwarded_proto=request.headers.get("x-forwarded-proto"),
        all_headers=dict(request.headers),
        frontend_param=frontend,
    )

    # Validate OAuth configuration
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured",
        )

    # Get redirect URI (this API endpoint's callback)
    config = settings.DOMAIN_CONFIG[env]

    # Get actual request host (handles Codespace forwarding)
    forwarded_host = request.headers.get("x-forwarded-host")

    if forwarded_host:
        # Codespace or proxy - use forwarded host
        scheme = "https" if "app.github.dev" in forwarded_host else request.url.scheme
        redirect_uri = f"{scheme}://{forwarded_host}/auth/callback"
        logger.info(
            "using_forwarded_host",
            forwarded_host=forwarded_host,
            redirect_uri=redirect_uri,
        )
    elif env == "codespace":
        # Fallback: Use codespace config
        redirect_uri = f"{config['api']}/auth/callback"
        logger.info("using_codespace_config", redirect_uri=redirect_uri)
    else:
        # Production/staging - use configured domain
        redirect_uri = f"{config['api']}/auth/callback"

    # Detect which frontend initiated login
    # Priority: query param > Referer header > default to 'pp'
    if frontend:
        # Map frontend identifier to URL
        frontend_url = config.get(frontend, config.get("pp", ""))
    else:
        # Default to Platform Portal
        frontend_url = config.get("pp", "")

    # Encode state with frontend URL and CSRF token
    state_data = {
        "frontend": frontend_url,
        "csrf": secrets.token_urlsafe(16),
        "env": env,
    }
    state = encode_state(state_data)

    # Build OAuth authorization URL
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    logger.info(
        "oauth_redirect_to_google",
        environment=env,
        redirect_uri=redirect_uri,
        frontend=frontend_url,
        frontend_param=frontend,
    )

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    request: Request = None,
):
    """
    Handle OAuth callback from Google

    Exchanges authorization code for access token,
    fetches user info, creates JWT, and redirects to
    Platform Portal frontend.
    """
    # Detect environment
    env = detect_environment(request)
    config = settings.DOMAIN_CONFIG[env]

    # Check for OAuth errors
    if error:
        logger.error("oauth_error_from_google", error=error, environment=env)
        frontend_url = config.get("pp", "")
        return RedirectResponse(url=f"{frontend_url}/?error={error}")

    # Validate required parameters
    if not code or not state:
        logger.error("oauth_callback_missing_params", environment=env)
        frontend_url = config.get("pp", "")
        return RedirectResponse(url=f"{frontend_url}/?error=missing_params")

    # Decode state to get frontend URL
    state_data = decode_state(state)
    frontend_url = state_data.get("frontend", config.get("pp", ""))

    logger.info(
        "oauth_callback_started",
        environment=env,
        frontend=frontend_url,
        has_code=bool(code),
    )

    # Validate OAuth configuration
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured",
        )

    # Get actual redirect URI (must match what was sent to Google)
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_host:
        scheme = "https" if "app.github.dev" in forwarded_host else request.url.scheme
        redirect_uri = f"{scheme}://{forwarded_host}/auth/callback"
    else:
        redirect_uri = f"{config['api']}/auth/callback"

    try:
        # Exchange authorization code for access token
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                logger.error(
                    "oauth_token_exchange_failed",
                    status=token_response.status_code,
                    response=token_response.text,
                    environment=env,
                )
                return RedirectResponse(
                    url=f"{frontend_url}/?error=token_exchange_failed"
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                logger.error("oauth_no_access_token", environment=env)
                return RedirectResponse(
                    url=f"{frontend_url}/?error=no_access_token"
                )

            # Fetch user info from Google
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
            )

            if userinfo_response.status_code != 200:
                logger.error(
                    "oauth_userinfo_failed",
                    status=userinfo_response.status_code,
                    environment=env,
                )
                return RedirectResponse(
                    url=f"{frontend_url}/?error=userinfo_failed"
                )

            user_info = userinfo_response.json()

    except Exception as e:
        logger.error("oauth_exception", error=str(e), environment=env)
        return RedirectResponse(url=f"{frontend_url}/?error=server_error")

    # Extract user details
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")

    if not email or not name:
        logger.error("oauth_incomplete_userinfo", environment=env)
        return RedirectResponse(url=f"{frontend_url}/?error=incomplete_userinfo")

    # Determine user role
    role = get_user_role(email)

    # Create JWT token
    token_payload = {
        "email": email,
        "name": name,
        "picture": picture,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }

    # Sign JWT with secret
    jwt_token = jwt.encode(
        token_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    logger.info(
        "oauth_login_success",
        email=email,
        role=role,
        environment=env,
        frontend=frontend_url,
    )

    # Build redirect URL with user info
    params = urlencode(
        {
            "token": jwt_token,
            "email": email,
            "name": name,
            "picture": picture or "",
            "role": role,
        }
    )

    redirect_url = f"{frontend_url}/auth/callback?{params}"

    logger.info("oauth_redirect_to_frontend", url=redirect_url)

    return RedirectResponse(url=redirect_url)


@router.get("/logout")
async def oauth_logout():
    """Logout endpoint - clears session"""
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(request: Request):
    """Get current user info from JWT token"""
    # TODO: Implement JWT validation and user info extraction
    return {"message": "Not implemented yet"}
