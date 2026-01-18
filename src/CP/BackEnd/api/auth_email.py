"""
Email/Password Authentication Endpoints

FastAPI routes for user registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.user import UserRegister, UserLogin, Token, UserDB
from models.user_db import User
from services.auth_service import AuthService
from services.auth_dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get auth service instance."""
    return AuthService(db)


@router.post(
    "/register",
    response_model=UserDB,
    status_code=status.HTTP_201_CREATED,
    summary="Register User",
    description="Register a new user with email and password"
)
async def register(
    user_data: UserRegister,
    service: AuthService = Depends(get_auth_service)
) -> UserDB:
    """
    Register a new user.
    
    **Request Body:**
    - email: Valid email address (unique)
    - password: Password (min 8 characters recommended)
    - full_name: User's full name
    
    **Returns:**
    - User object with id, email, full_name (without password)
    
    **Errors:**
    - 400: Email already registered
    - 422: Validation error (invalid email format, etc.)
    """
    try:
        user = await service.register_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="Login with email and password to get JWT tokens"
)
async def login(
    login_data: UserLogin,
    service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Login with email and password.
    
    **Request Body:**
    - email: User's email
    - password: User's password
    
    **Returns:**
    - access_token: JWT token for API requests (expires in 15 mins)
    - refresh_token: Long-lived token to refresh access token (expires in 7 days)
    - token_type: "bearer"
    - expires_in: Access token lifetime in seconds
    
    **Usage:**
    ```
    # Store tokens
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
    
    # Use in requests
    fetch('/api/v1/trials', {
      headers: {
        'Authorization': `Bearer ${access_token}`
      }
    })
    ```
    
    **Errors:**
    - 401: Invalid email or password
    """
    try:
        tokens = await service.login_user(login_data)
        return tokens
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.get(
    "/me",
    response_model=UserDB,
    summary="Get Current User",
    description="Get current authenticated user's profile"
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserDB:
    """
    Get current user profile.
    
    Requires authentication (Bearer token in Authorization header).
    
    **Headers:**
    - Authorization: Bearer <access_token>
    
    **Returns:**
    - User profile (id, email, full_name, created_at, updated_at)
    
    **Errors:**
    - 401: Invalid or missing token
    """
    return UserDB(
        id=str(current_user.id),
        email=current_user.email,
        hashed_password=current_user.hashed_password,
        full_name=current_user.full_name,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Logout current user (client-side token removal)"
)
async def logout():
    """
    Logout user.
    
    Since we use stateless JWT tokens, logout is handled client-side
    by removing tokens from storage.
    
    **Client-Side Action:**
    ```javascript
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    ```
    
    **Note:** Tokens remain valid until expiry. For true revocation,
    implement token blacklist (future enhancement).
    
    **Returns:**
    - 204 No Content
    """
    pass  # Client handles token removal
