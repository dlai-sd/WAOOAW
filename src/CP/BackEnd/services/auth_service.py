"""
Authentication Service Layer

Business logic for user registration, login, and authentication.
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.logging import get_logger
from core.tracing import start_trace, end_trace  # Assuming a tracing module is available
from models import User, UserRegister, UserDB, UserLogin, Token  # Importing necessary models
from utils import hash_password, verify_password  # Importing utility functions
from services.jwt_handler import JWTHandler  # Importing JWT handler
from config import settings  # Importing settings
import asyncio

logger = get_logger(__name__)

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
        trace_id = start_trace("register_user")  # Start tracing
        logger.info(f"Registering user: {user_data.email}", extra={"trace_id": trace_id})
        
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")
        
        hashed_password = hash_password(user_data.password)
        
        user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"User registered: {user.email}", extra={"trace_id": trace_id})
        end_trace(trace_id)  # End tracing
        
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
        trace_id = start_trace("authenticate_user")  # Start tracing
        logger.info(f"Authenticating user: {login_data.email}", extra={"trace_id": trace_id})
        
        user = await self.get_user_by_email(login_data.email)
        
        if not user:
            logger.warning(f"User not found: {login_data.email}", extra={"trace_id": trace_id})
            end_trace(trace_id)  # End tracing
            return None
        
        if not verify_password(login_data.password, user.hashed_password):
            logger.warning(f"Invalid password for user: {login_data.email}", extra={"trace_id": trace_id})
            end_trace(trace_id)  # End tracing
            return None
        
        logger.info(f"User authenticated: {user.email}", extra={"trace_id": trace_id})
        end_trace(trace_id)  # End tracing
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
        trace_id = start_trace("login_user")  # Start tracing
        logger.info(f"Logging in user: {login_data.email}", extra={"trace_id": trace_id})
        
        user = await self.authenticate_user(login_data)
        
        if not user:
            logger.error("Invalid email or password", extra={"trace_id": trace_id})
            end_trace(trace_id)  # End tracing
            raise ValueError("Invalid email or password")
        
        access_token = JWTHandler.create_access_token(
            user_id=str(user.id),
            email=user.email
        )
        
        refresh_token = JWTHandler.create_refresh_token(
            user_id=str(user.id),
            email=user.email
        )
        
        logger.info(f"User logged in: {user.email}", extra={"trace_id": trace_id})
        end_trace(trace_id)  # End tracing
        
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
        return await self.retry_on_transient_errors(
            self._get_user_by_email_internal,
            email
        )
    
    async def _get_user_by_email_internal(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def retry_on_transient_errors(self, func, *args):
        """
        Retry a function call with exponential backoff for transient errors.
        
        Args:
            func: Function to call
            *args: Arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If all retries fail
        """
        retries = 3
        for attempt in range(retries):
            try:
                return await func(*args)
            except Exception as e:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Transient error: {e}. Retrying in {wait_time}s...", extra={"attempt": attempt + 1})
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All retries failed for {func.__name__}: {e}")
                    raise

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User or None if not found
        """
        return await self.retry_on_transient_errors(
            self._get_user_by_id_internal,
            user_id
        )

    async def _get_user_by_id_internal(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
