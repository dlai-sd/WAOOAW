"""
Authentication Service Layer

Business logic for user registration, login, and authentication.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from prometheus_client import Counter, Histogram

from models.user_db import User
from models.user import UserRegister, UserLogin, UserDB, Token
from core.security import hash_password, verify_password
from core.jwt_handler import JWTHandler
from core.config import settings
import logging

# Prometheus metrics
REQUEST_COUNT = Counter('request_count', 'Total request count', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['method', 'endpoint'])

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
        """
        Register a new user with email/password.
        
        Args:
            user_data: Registration data (email, password, full_name)
            
        Returns:
            Created user (without password)
            
        Raises:
            ValueError: If email already exists
        """
        # Check if user already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        return UserDB(
            id=str(user.id),
            email=user.email,
            hashed_password=user.hashed_password,
            full_name=user.full_name,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    async def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """
        Authenticate user with email/password.
        
        Args:
            login_data: Login credentials (email, password)
            
        Returns:
            User if credentials valid, None otherwise
        """
        user = await self.get_user_by_email(login_data.email)
        
        if not user:
            return None
        
        if not verify_password(login_data.password, user.hashed_password):
            return None
        
        return user
    
    async def login_user(self, login_data: UserLogin) -> Token:
        """
        Login user and return JWT tokens.
        
        Args:
            login_data: Login credentials
            
        Returns:
            Token with access_token and refresh_token
            
        Raises:
            ValueError: If credentials invalid
        """
        user = await self.authenticate_user(login_data)
        
        if not user:
            raise ValueError("Invalid email or password")
        
        # Generate JWT tokens
        access_token = JWTHandler.create_access_token(
            user_id=str(user.id),
            email=user.email
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
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User email
            
        Returns:
            User or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User or None if not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def log_request(self, method: str, endpoint: str, duration: float, user_id: Optional[UUID] = None):
        """Log request details for monitoring."""
        logging.info(f"Request: {method} {endpoint} | Duration: {duration:.2f}s | User ID: {user_id}")
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)
