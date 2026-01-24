"""
Google OAuth integration
Handles OAuth flow and user info retrieval
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import httpx
from authlib.integrations.starlette_client import OAuth
from core.config import settings
from core.jwt_handler import create_access_token, create_refresh_token
from models.user import TokenData

# Initialize OAuth
oauth = OAuth()
router = APIRouter()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account",  # Force account selection
    },
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_user_from_google(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange an OAuth authorization code for Google user info.

    Returns a normalized payload used by the CP auth routes.
    """

    token_response = await exchange_code_for_token(code, redirect_uri)
    access_token = token_response.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth token exchange did not return access_token",
        )

    user_info = await get_user_info(access_token)
    subject = user_info.get("sub") or user_info.get("id")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google userinfo did not include subject identifier",
        )

    # Normalize to the fields expected by api.auth.routes
    return {
        "id": subject,
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "picture": user_info.get("picture"),
        **user_info,
    }


async def verify_google_token(id_token: str) -> Dict[str, Any]:
    """Verify a Google ID token using Google's tokeninfo endpoint."""

    tokeninfo_url = "https://oauth2.googleapis.com/tokeninfo"

    async with httpx.AsyncClient() as client:
        response = await client.get(tokeninfo_url, params={"id_token": id_token})

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google ID token",
        )

    token_info = response.json()
    audience = token_info.get("aud")
    if settings.GOOGLE_CLIENT_ID and audience and audience != settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google ID token audience mismatch",
        )

    return token_info

async def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token.
    
    Args:
        code: Authorization code received from Google.
        redirect_uri: The redirect URI used in the OAuth flow.
    
    Returns:
        Dictionary containing the access token and other information.
    """
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=payload)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()

async def get_user_info(access_token: str) -> Dict[str, Any]:
    """
    Retrieve user information from Google using the access token.
    
    Args:
        access_token: The access token received from Google.
    
    Returns:
        Dictionary containing user information.
    """
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(user_info_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()

@router.post("/token", response_model=Dict[str, Any])
async def token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token and refresh token.
    """
    token_response = await exchange_code_for_token(code, redirect_uri)
    access_token = token_response.get("access_token")
    user_info = await get_user_info(access_token)

    # Create JWT with tenant_id and user_id
    tenant_id = user_info.get("tenant_id")  # Assuming tenant_id is part of user_info
    user_id = user_info.get("sub")  # Assuming sub is the user_id

    jwt_access_token = create_access_token(user_id=user_id, email=user_info.get("email"), tenant_id=tenant_id)
    jwt_refresh_token = create_refresh_token(user_id=user_id, email=user_info.get("email"), tenant_id=tenant_id)

    return {
        "access_token": jwt_access_token,
        "refresh_token": jwt_refresh_token,
        "token_type": "bearer",
    }
