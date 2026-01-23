import pytest
from unittest.mock import AsyncMock
from src.CP.BackEnd.services.auth_service import AuthService
from src.CP.BackEnd.models.user import UserLogin
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_login_user_with_retries(mock_auth_service: AuthService, mocker):
    """Test login user with retry logic"""
    mock_auth_service.authenticate_user = AsyncMock(side_effect=[Exception("Transient error"), Exception("Transient error"), "mock_user"])
    
    login_data = UserLogin(email="test@example.com", password="password")
    
    result = await mock_auth_service.login_user(login_data)
    
    assert result == "mock_user"
    assert mock_auth_service.authenticate_user.call_count == 3  # Ensure it retried 3 times

@pytest.mark.asyncio
async def test_login_user_failure(mock_auth_service: AuthService):
    """Test login user failure after retries"""
    mock_auth_service.authenticate_user = AsyncMock(side_effect=Exception("Transient error"))
    
    login_data = UserLogin(email="test@example.com", password="password")
    
    with pytest.raises(Exception, match="Failed to get user by email. Please try again later."):
        await mock_auth_service.login_user(login_data)
