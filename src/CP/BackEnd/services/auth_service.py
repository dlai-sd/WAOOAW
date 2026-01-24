"""
Authentication Service Layer

Business logic for user registration, login, and authentication.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import asyncio
from fastapi import status, HTTPException

from models.user_db import User
from models.user import UserRegister, UserLogin, UserDB, Token
from core.security import hash_password, verify_password
from core.jwt_handler import JWTHandler
from core.config import settings
from core.error_handling import raise_http_exception

class AuthService:
    """
    Service for user authentication operations.
    
    Handles:
    - User registration (email/password)
    - User login (email/password)
    - Password verification
    - JWT token generation
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize service with database session."""
        self.db = db
    
    async def register_user(self, user_data: UserRegister) -> UserDB:
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise_http_exception(
                detail=f"User with email {user_data.email} already exists",
                code=status.HTTP_400_BAD_REQUEST
            )
        
        hashed_password = hash_password(user_data.password)
        
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        await self._retry_db_operation(lambda: self._create_user(user))
        
        return UserDB(
            id=str(user.id),
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    async def _create_user(self, user: User):
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

    async def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        user = await self.get_user_by_email(login_data.email)
        
        if not user:
            return None
        
        if not verify_password(login_data.password, user.hashed_password):
            return None
        
        return user
    
    async def login_user(self, login_data: UserLogin) -> Token:
        user = await self.authenticate_user(login_data)
        
        if not user:
            raise_http_exception("Invalid email or password", status.HTTP_401_UNAUTHORIZED)
        
        access_token = JWTHandler.create_access_token(
            user_id=str(user.id),
            email=user.email,
            tenant_id=user.tenant_id
        )
        
        refresh_token = JWTHandler.create_refresh_token(
            user_id=str(user.id),
            email=user.email
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_seconds
        )
    
    async def _retry_db_operation(self, operation, retries: int = 3):
        for attempt in range(retries):
            try:
                await operation()
                return
            except (httpx.HTTPStatusError, Exception) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise_http_exception(
                        detail="Transient error occurred. Please try again later.",
                        code=status.HTTP_503_SERVICE_UNAVAILABLE
                    )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
