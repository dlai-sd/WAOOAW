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
from api.auth.google_oauth import verify_google_token, get_user_from_google
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
        redirect_uri = f"{settings.API_URL}/auth/google/callback"
        user_info = await get_user_from_google(code, redirect_uri)
        
        user_data = UserCreate(
            email=user_info["email"],
            name=user_info.get("name"),
            picture=user_info.get("picture"),
            provider="google",
            provider_id=user_info["id"],
        )
        user = user_store.get_or_create_user(user_data)
        tokens = create_tokens(user.id, user.email)
        
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?access_token={tokens['access_token']}&refresh_token={tokens['refresh_token']}",
            status_code=302
        )
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

