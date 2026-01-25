"""
Authentication API routes
Handles Google OAuth login, token management, and user info
"""

import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from api.auth.dependencies import get_current_user, verify_refresh_token, get_user_from_google
from api.auth.google_oauth import verify_google_token
from api.auth.google_auth import google_login, google_callback
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
    """Health check for auth service"""
    return {
        "status": "healthy",
        "service": "authentication",
        "oauth_configured": bool(settings.GOOGLE_CLIENT_ID),
    }
