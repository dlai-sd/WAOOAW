"""
Authentication API routes
Handles Google OAuth login, token management, and user info
"""

import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from api.auth.dependencies import get_current_user, verify_refresh_token
from api.auth.google_oauth import get_user_from_google, verify_google_token
from api.auth.user_store import UserStore, get_user_store
from core.config import settings
from core.jwt_handler import create_tokens
from models.user import Token, User, UserCreate

router = APIRouter(prefix="/auth", tags=["authentication"])


# In-memory state storage (use Redis in production)
_state_store = {}


class GoogleTokenRequest(BaseModel):
    """Request to verify Google ID token from frontend"""

    id_token: str
    source: str = "cp"  # cp, pp, or mobile


@router.get("/google/login")
async def google_login(
    source: str = Query("cp", description="Source application: cp, pp, or mobile")
):
    """
    Initiate Google OAuth login flow

    Args:
        source: Which app is initiating login (cp, pp, mobile)

    Returns:
        Redirect to Google OAuth consent screen
    """
    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    _state_store[state] = {"source": source}

    # Build authorization URL
    redirect_uri = settings.OAUTH_REDIRECT_URI
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"state={state}&"
        f"prompt=select_account&"
        f"access_type=offline"
    )

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    user_store: UserStore = Depends(get_user_store),
):
    """
    Handle OAuth callback from Google

    Args:
        code: Authorization code from Google
        state: CSRF token to verify
        error: Error message if OAuth failed
        user_store: User storage

    Returns:
        Redirect to frontend with tokens or error
    """
    # Check for OAuth errors
    if error:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?error={error}", status_code=302
        )

    # Verify state token (CSRF protection)
    if not state or state not in _state_store:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?error=invalid_state", status_code=302
        )

    # Clean up used state
    del _state_store[state]

    # Verify code exists
    if not code:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?error=no_code", status_code=302
        )

    try:
        # Exchange code for user info
        user_info = await get_user_from_google(code, settings.OAUTH_REDIRECT_URI)

        # Create or get user
        user_data = UserCreate(
            email=user_info["email"],
            name=user_info.get("name"),
            picture=user_info.get("picture"),
            provider="google",
            provider_id=user_info["id"],
        )

        user = user_store.get_or_create_user(user_data)

        # Create JWT tokens
        tokens = create_tokens(user.id, user.email)

        # Redirect to frontend with tokens
        redirect_url = (
            f"{settings.FRONTEND_URL}/auth/callback?"
            f"access_token={tokens['access_token']}&"
            f"refresh_token={tokens['refresh_token']}&"
            f"expires_in={tokens['expires_in']}"
        )

        return RedirectResponse(url=redirect_url, status_code=302)

    except Exception as e:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?error=auth_failed&message={str(e)}",
            status_code=302,
        )


@router.post("/google/verify", response_model=Token)
async def verify_google_id_token(
    request: GoogleTokenRequest, user_store: UserStore = Depends(get_user_store)
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

        # Create JWT tokens
        tokens = create_tokens(user.id, user.email)

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
    # Verify user still exists
    user = user_store.get_user_by_id(token_data.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    # Create new token pair
    tokens = create_tokens(user.id, user.email)

    return Token(**tokens)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user
    In production, add token to blacklist in Redis

    Args:
        current_user: Authenticated user

    Returns:
        Success message
    """
    # TODO: Add token to blacklist in Redis
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
