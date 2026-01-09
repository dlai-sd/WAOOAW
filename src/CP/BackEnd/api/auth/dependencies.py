"""
FastAPI dependencies for authentication
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.jwt_handler import verify_token
from models.user import User, TokenData
from api.auth.user_store import get_user_store, UserStore


# Security scheme for Swagger docs
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_store: UserStore = Depends(get_user_store)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: Bearer token from Authorization header
        user_store: User storage instance
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify and decode token
    token_data: TokenData = verify_token(token)
    
    # Ensure it's an access token
    if token_data.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    # Get user from store
    user = user_store.get_user_by_id(token_data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise None
    Useful for endpoints that work both authenticated and unauthenticated
    
    Args:
        credentials: Optional bearer token
        
    Returns:
        User if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def verify_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Verify that the provided token is a valid refresh token
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        Token data if valid refresh token
        
    Raises:
        HTTPException: If token is invalid or not a refresh token
    """
    token = credentials.credentials
    
    # Verify and decode token
    token_data: TokenData = verify_token(token)
    
    # Ensure it's a refresh token
    if token_data.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, refresh token required"
        )
    
    return token_data
