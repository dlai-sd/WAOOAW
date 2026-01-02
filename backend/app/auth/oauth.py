"""
OAuth2 with Google - Fixed redirect to frontend
"""

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from typing import Optional
import os
import httpx
import structlog

from .jwt_handler import create_access_token
from .models import UserRole

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

# Frontend URL - Get from environment or use Codespace URL
CODESPACE_NAME = os.getenv("CODESPACE_NAME", "")
if CODESPACE_NAME:
    FRONTEND_URL = f"https://{CODESPACE_NAME}-3000.app.github.dev"
else:
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_user_role(email: str) -> UserRole:
    """Determine user role based on email"""
    # Admin users
    if email in ["admin@waooaw.ai", "yogeshkhandge@gmail.com"]:
        return UserRole.ADMIN
    # Operators
    elif email.endswith("@waooaw.ai"):
        return UserRole.OPERATOR
    # Default to viewer
    else:
        return UserRole.VIEWER


def _build_request_base_url(request: Request) -> Optional[str]:
    """Derive external base URL from forwarded headers (works on Cloud Run)."""
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    if not host:
        return None
    return f"{proto}://{host}"


def _get_redirect_uri(request: Request) -> str:
    """Prefer explicit env; otherwise derive from request host (avoids localhost default in Cloud Run)."""
    if GOOGLE_REDIRECT_URI and "localhost" not in GOOGLE_REDIRECT_URI:
        return GOOGLE_REDIRECT_URI
    derived = _build_request_base_url(request)
    if derived:
        return f"{derived}/auth/callback"
    return GOOGLE_REDIRECT_URI


def _get_frontend_url(request: Request) -> str:
    """Pick frontend URL from env, otherwise use Origin/Host to avoid localhost default on Cloud Run."""
    if FRONTEND_URL and "localhost" not in FRONTEND_URL:
        return FRONTEND_URL
    origin = request.headers.get("origin")
    if origin:
        return origin.rstrip("/")
    derived = _build_request_base_url(request)
    if derived:
        return derived
    return FRONTEND_URL


@router.get("/login")
async def oauth_login(request: Request):
    """Initiate Google OAuth flow"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    redirect_uri = _get_redirect_uri(request)
    
    # Build OAuth authorization URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    from urllib.parse import urlencode
    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    
    logger.info("oauth_login_initiated", redirect_uri=redirect_uri)
    
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth_callback(code: str, request: Request):
    """Handle OAuth2 callback from Google"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    redirect_uri = _get_redirect_uri(request)
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            logger.error("oauth_token_exchange_failed", status=token_response.status_code)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to exchange authorization code"
            )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No access token received"
            )
        
        # Fetch user info from Google
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if userinfo_response.status_code != 200:
            logger.error("oauth_userinfo_failed", status=userinfo_response.status_code)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch user info"
            )
        
        user_info = userinfo_response.json()
    
    # Extract user details
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")
    
    if not email or not name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incomplete user info from Google"
        )
    
    # Determine user role
    role = get_user_role(email)
    
    # Create JWT token
    jwt_token = create_access_token(email=email, name=name, role=role)
    
    logger.info(
        "oauth_login_success",
        email=email,
        role=role.value,
        ip=request.client.host if request.client else "unknown",
        redirect_uri=redirect_uri
    )
    
    # FIXED: Always redirect to frontend URL
    from urllib.parse import urlencode
    params = urlencode({
        "token": jwt_token,
        "email": email,
        "name": name,
        "picture": picture or "",
        "role": role.value
    })
    frontend_target = _get_frontend_url(request)
    redirect_url = f"{frontend_target}/auth/callback?{params}"
    
    logger.info("oauth_redirect", url=redirect_url)
    
    return RedirectResponse(url=redirect_url)
