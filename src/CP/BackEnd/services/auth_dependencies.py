"""
Auth dependencies for FastAPI

Provides dependency functions for authentication.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from core.database import get_db
from core.jwt_handler import JWTHandler
from services.auth_service import AuthService
from models.user_db import User

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Usage in routes:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email}
    
    Args:
        credentials: HTTP Authorization Bearer token
        db: Database session
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException 401: If token invalid or user not found
    """
    # Decode JWT token
    token_data = JWTHandler.decode_token(credentials.credentials)
    
    # Get user from database
    service = AuthService(db)
    user = await service.get_user_by_id(UUID(token_data.user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token provided, otherwise None.
    
    Useful for optional authentication endpoints.
    
    Args:
        credentials: Optional HTTP Authorization Bearer token
        db: Database session
        
    Returns:
        User if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
