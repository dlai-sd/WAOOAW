"""
OAuth 2.0 Implementation - Version 2.0
Multi-domain support with automatic environment detection
"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse
from typing import Optional
from pydantic import BaseModel
import httpx
import structlog
from urllib.parse import urlencode, urlparse
import secrets
import base64
import json
from jose import jwt
from datetime import datetime, timedelta

from ..config import settings

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
        data: Dictionary to encode (e.g., {"frontend": "https://www.waooaw.com"})
        
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
        # Default to www (customer portal)
        return config.get("www", "")
    
    parsed = urlparse(referer)
    referer_host = f"{parsed.scheme}://{parsed.netloc}"
    
    # Check which domain the user came from
    for key, url in config.items():
        if url == referer_host:
            return url
    
    # Default to www if no match
    return config.get("www", "")


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
    Initiate OAuth flow
    
    Automatically detects:
    - Environment (demo/uat/prod) from hostname
    - Frontend that initiated login from query param or Referer header
    
    Args:
        frontend: Optional frontend identifier ('pp' for Platform Portal, 'www' for Customer Portal)
    
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
        frontend_param=frontend
    )
    
    # Validate OAuth configuration
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    # Get redirect URI (this API endpoint's callback)
    config = settings.DOMAIN_CONFIG[env]
    
    # Get actual request host (handles Codespace forwarding)
    forwarded_host = request.headers.get("x-forwarded-host")
    
    if forwarded_host:
        # Codespace or proxy - use forwarded host
        scheme = "https" if "app.github.dev" in forwarded_host else request.url.scheme
        redirect_uri = f"{scheme}://{forwarded_host}/auth/callback"
        logger.info("using_forwarded_host", forwarded_host=forwarded_host, redirect_uri=redirect_uri)
    elif env == "codespace":
        # Fallback: Use codespace config
        redirect_uri = f"{config['api']}/auth/callback"
        logger.info("using_codespace_config", redirect_uri=redirect_uri)
    else:
        # Production/staging - use configured domain
        redirect_uri = f"{config['api']}/auth/callback"
    
    # Detect which frontend initiated login
    # Priority: query param > Referer header
    if frontend:
        # Map frontend identifier to URL
        frontend_url = config.get(frontend, config.get("www", ""))
    else:
        frontend_url = get_frontend_from_referer(request, env)
    
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
    request: Request = None
):
    """
    Handle OAuth callback from Google
    
    Exchanges authorization code for access token,
    fetches user info, creates JWT, and redirects to
    originating frontend.
    """
    # Detect environment
    env = detect_environment(request)
    config = settings.DOMAIN_CONFIG[env]
    
    # Check for OAuth errors
    if error:
        logger.error("oauth_error_from_google", error=error, environment=env)
        frontend_url = config.get("www", "")
        return RedirectResponse(url=f"{frontend_url}/login?error={error}")
    
    # Validate required parameters
    if not code or not state:
        logger.error("oauth_callback_missing_params", environment=env)
        frontend_url = config.get("www", "")
        return RedirectResponse(url=f"{frontend_url}/login?error=missing_params")
    
    # Decode state to get frontend URL
    state_data = decode_state(state)
    frontend_url = state_data.get("frontend", config.get("www", ""))
    
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
            detail="Google OAuth not configured"
        )
    
    redirect_uri = f"{config['api']}/auth/callback"
    
    try:
        # Exchange authorization code for access token
        # Use timeout to prevent hanging
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                }
            )
            
            if token_response.status_code != 200:
                logger.error(
                    "oauth_token_exchange_failed",
                    status=token_response.status_code,
                    response=token_response.text,
                    environment=env,
                )
                return RedirectResponse(url=f"{frontend_url}/login?error=token_exchange_failed")
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error("oauth_no_access_token", environment=env)
                return RedirectResponse(url=f"{frontend_url}/login?error=no_access_token")
            
            # Fetch user info from Google
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if userinfo_response.status_code != 200:
                logger.error(
                    "oauth_userinfo_failed",
                    status=userinfo_response.status_code,
                    environment=env,
                )
                return RedirectResponse(url=f"{frontend_url}/login?error=userinfo_failed")
            
            user_info = userinfo_response.json()
    
    except Exception as e:
        logger.error("oauth_exception", error=str(e), environment=env)
        return RedirectResponse(url=f"{frontend_url}/login?error=server_error")
    
    # Extract user details
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")
    
    if not email or not name:
        logger.error("oauth_incomplete_userinfo", environment=env)
        return RedirectResponse(url=f"{frontend_url}/login?error=incomplete_userinfo")
    
    # Determine user role
    role = get_user_role(email)
    
    # Create JWT token (using simple dict for now - will implement JWT properly)
    jwt_token = f"demo_token_{email}"  # TODO: Implement proper JWT
    
    logger.info(
        "oauth_login_success",
        email=email,
        role=role,
        environment=env,
        frontend=frontend_url,
    )
    
    # Build redirect URL with user info
    params = urlencode({
        "token": jwt_token,
        "email": email,
        "name": name,
        "picture": picture or "",
        "role": role,
    })
    
    redirect_url = f"{frontend_url}/auth/callback?{params}"
    
    logger.info("oauth_redirect_to_frontend", url=redirect_url)
    
    return RedirectResponse(url=redirect_url)


@router.get("/logout")
async def oauth_logout():
    """Logout endpoint - clears session"""
    # TODO: Implement session management and token invalidation
    return {"message": "Logged out successfully"}


@router.post("/google/verify")
async def verify_google_token(token_request: GoogleTokenRequest):
    """
    Verify Google Identity Services (GIS) JWT token
    
    This endpoint receives the credential token from Google's popup authentication
    and verifies it directly with Google, then creates/updates the user and returns
    an access token for the application.
    
    Args:
        token_request: Contains the JWT token from Google
        
    Returns:
        User data and application access token
    """
    try:
        # Verify token with Google
        async with httpx.AsyncClient() as client:
            # Get Google's public keys
            certs_response = await client.get(GOOGLE_CERTS_URL)
            if certs_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to fetch Google certificates"
                )
            
            # Decode and verify JWT token
            # Note: In production, use proper JWT verification with Google's public keys
            # For now, we'll verify with Google's tokeninfo endpoint
            verify_response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={token_request.token}"
            )
            
            if verify_response.status_code != 200:
                logger.error("google_token_verification_failed", status=verify_response.status_code)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google token"
                )
            
            token_data = verify_response.json()
            
            # Verify audience (client ID)
            if token_data.get("aud") != settings.GOOGLE_CLIENT_ID:
                logger.error("token_audience_mismatch", 
                           expected=settings.GOOGLE_CLIENT_ID,
                           received=token_data.get("aud"))
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token audience mismatch"
                )
            
            # Extract user info
            email = token_data.get("email")
            name = token_data.get("name")
            picture = token_data.get("picture")
            email_verified = token_data.get("email_verified", False)
            
            if not email or not email_verified:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email not verified"
                )
            
            # Determine user role
            role = get_user_role(email)
            
            # Create application access token (JWT)
            token_payload = {
                "email": email,
                "name": name,
                "picture": picture,
                "role": role,
                "exp": datetime.utcnow() + timedelta(days=7),  # 7 days expiry
                "iat": datetime.utcnow()
            }
            
            # Sign JWT with application secret
            # Note: In production, use a proper secret from environment/secrets manager
            app_secret = settings.GOOGLE_CLIENT_SECRET  # Reuse OAuth secret for now
            access_token = jwt.encode(token_payload, app_secret, algorithm="HS256")
            
            logger.info("google_signin_successful", 
                       email=email, 
                       role=role,
                       name=name)
            
            # TODO: Store/update user in database
            # user = await create_or_update_user(email, name, picture, role)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "email": email,
                "name": name,
                "picture": picture,
                "role": role,
                "expires_in": 604800  # 7 days in seconds
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("google_token_verification_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed"
        )


@router.get("/me")
async def get_current_user(request: Request):
    """Get current user info from JWT token"""
    # TODO: Implement JWT validation and user info extraction
    return {"message": "Not implemented yet"}
