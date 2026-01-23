"""
OAuth2 authentication routes
"""

from fastapi import APIRouter, Depends
from core.jwt_handler import create_tokens
from models.user import User

router = APIRouter()

@router.post("/token")
async def token(username: str, password: str):
    """
    OAuth2 token endpoint to generate access and refresh tokens.

    Args:
        username: User's username
        password: User's password

    Returns:
        Dictionary with access_token and refresh_token
    """
    # Here you would validate the user credentials
    user = User(username=username)  # Mock user for demonstration
    tokens = create_tokens(user.user_id, user.tenant_id)
    return tokens
