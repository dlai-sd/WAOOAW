"""
Google OAuth integration
Handles OAuth flow and user info retrieval
"""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
import httpx
from authlib.integrations.starlette_client import OAuth
from core.config import settings
from core.jwt_handler import create_tokens
from models.user import User  # Assuming User model exists

router = APIRouter()
oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account",
    },
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/token", response_model=Dict[str, Any])
async def login(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    OAuth2 token endpoint to return JWT.
    """
    token_response = await exchange_code_for_token(code, redirect_uri)
    access_token = token_response.get("access_token")
    user_info = await get_user_info(access_token)

    # Create JWT with tenant_id and user_id
    user_id = user_info.get("sub")  # Assuming 'sub' is the user ID from Google
    tenant_id = user_info.get("email").split('@')[1]  # Example tenant extraction

    tokens = create_tokens(user_id, user_info.get("email"), tenant_id)
    return tokens


async def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token
    """
    # Existing implementation


async def get_user_info(access_token: str) -> Dict[str, Any]:
    """
    Get user information from Google
    """
    # Existing implementation


async def verify_google_token(id_token: str) -> Dict[str, Any]:
    """Verify Google ID token from frontend"""
    # Existing implementation
