"""
Token endpoint for OAuth2 JWT authentication
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_service import AuthService
from models.user import UserLogin, Token
from core.database import get_db

router = APIRouter()

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 token endpoint for user login.
    
    Args:
        form_data: Contains email and password
        
    Returns:
        Token: Access token and token type
        
    Raises:
        HTTPException: If credentials are invalid
    """
    auth_service = AuthService(db)
    login_data = UserLogin(email=form_data.username, password=form_data.password)
    
    try:
        token = await auth_service.login_user(login_data)
        return token
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
