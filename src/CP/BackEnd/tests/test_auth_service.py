import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock
from services.auth_service import AuthService
from models.user import UserRegister, UserLogin

@pytest.mark.asyncio
async def test_register_user_success():
    db = AsyncMock(spec=AsyncSession)
    auth_service = AuthService(db)
    
    user_data = UserRegister(email="test@example.com", password="password", full_name="Test User")
    
    result = await auth_service.register_user(user_data)
    
    assert result.email == user_data.email
    assert result.full_name == user_data.full_name

@pytest.mark.asyncio
async def test_register_user_existing_email():
    db = AsyncMock(spec=AsyncSession)
    auth_service = AuthService(db)
    
    user_data = UserRegister(email="existing@example.com", password="password", full_name="Test User")
    
    # Simulate existing user
    db.execute.return_value.scalar_one_or_none.return_value = True
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.register_user(user_data)
    
    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail

@pytest.mark.asyncio
async def test_login_user_success():
    db = AsyncMock(spec=AsyncSession)
    auth_service = AuthService(db)
    
    login_data = UserLogin(email="test@example.com", password="password")
    
    # Simulate user authentication
    db.execute.return_value.scalar_one_or_none.return_value = AsyncMock(hashed_password="hashed_password")
    
    result = await auth_service.login_user(login_data)
    
    assert result.access_token is not None

@pytest.mark.asyncio
async def test_login_user_invalid_credentials():
    db = AsyncMock(spec=AsyncSession)
    auth_service = AuthService(db)
    
    login_data = UserLogin(email="test@example.com", password="wrong_password")
    
    # Simulate user not found
    db.execute.return_value.scalar_one_or_none.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await auth_service.login_user(login_data)
    
    assert exc_info.value.status_code == 401
    assert "Invalid email or password" in exc_info.value.detail
