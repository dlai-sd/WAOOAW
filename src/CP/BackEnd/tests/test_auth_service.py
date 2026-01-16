"""
Unit Tests for Auth Service
Tests authentication business logic (MVP-002)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from services.auth_service import AuthService
from models.user import UserRegister, UserLogin
from models.user_db import User


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.asyncio
class TestAuthService:
    """Unit tests for AuthService"""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def auth_service(self, mock_db_session):
        """Create AuthService instance"""
        return AuthService(mock_db_session)

    @patch("services.auth_service.hash_password")
    async def test_register_user_success(
        self, mock_hash, auth_service, mock_db_session
    ):
        """Test successful user registration"""
        mock_hash.return_value = "hashed_password"
        
        # Mock email check (no existing user)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        user_data = UserRegister(
            email="newuser@example.com",
            password="SecurePass123!",
            full_name="New User",
        )

        user = await auth_service.register_user(user_data)

        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.hashed_password == "hashed_password"
        mock_db_session.commit.assert_awaited_once()

    @patch("services.auth_service.hash_password")
    async def test_register_user_duplicate_email(
        self, mock_hash, auth_service, mock_db_session
    ):
        """Test registration with existing email"""
        # Mock existing user found
        existing_user = User(
            id=uuid4(),
            email="existing@example.com",
            hashed_password="hash",
            full_name="Existing User",
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db_session.execute.return_value = mock_result

        user_data = UserRegister(
            email="existing@example.com",
            password="password",
            full_name="New User",
        )

        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register_user(user_data)

    @patch("services.auth_service.verify_password")
    async def test_authenticate_user_success(
        self, mock_verify, auth_service, mock_db_session
    ):
        """Test successful authentication"""
        mock_verify.return_value = True

        # Mock user found
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result

        authenticated_user = await auth_service.authenticate_user(
            "test@example.com", "correct_password"
        )

        assert authenticated_user == user
        mock_verify.assert_called_once_with(
            "correct_password", "hashed_password"
        )

    @patch("services.auth_service.verify_password")
    async def test_authenticate_user_wrong_password(
        self, mock_verify, auth_service, mock_db_session
    ):
        """Test authentication with wrong password"""
        mock_verify.return_value = False

        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Invalid credentials"):
            await auth_service.authenticate_user(
                "test@example.com", "wrong_password"
            )

    async def test_authenticate_user_not_found(
        self, auth_service, mock_db_session
    ):
        """Test authentication with non-existent user"""
        # Mock no user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Invalid credentials"):
            await auth_service.authenticate_user(
                "nonexistent@example.com", "password"
            )

    @patch("services.auth_service.JWTHandler")
    @patch("services.auth_service.verify_password")
    async def test_login_user_success(
        self, mock_verify, mock_jwt, auth_service, mock_db_session
    ):
        """Test successful login with JWT token generation"""
        mock_verify.return_value = True
        
        # Mock JWT token creation
        mock_jwt_instance = MagicMock()
        mock_jwt_instance.create_tokens.return_value = {
            "access_token": "access_token_123",
            "refresh_token": "refresh_token_456",
            "expires_in": 900,
        }
        mock_jwt.return_value = mock_jwt_instance

        # Mock user
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result

        login_data = UserLogin(
            email="test@example.com",
            password="correct_password",
        )

        tokens = await auth_service.login_user(login_data)

        assert tokens["access_token"] == "access_token_123"
        assert tokens["refresh_token"] == "refresh_token_456"
        assert tokens["token_type"] == "bearer"

    async def test_get_user_by_email(
        self, auth_service, mock_db_session
    ):
        """Test getting user by email"""
        user = User(
            id=uuid4(),
            email="find@example.com",
            hashed_password="hash",
            full_name="Find Me",
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result

        found_user = await auth_service.get_user_by_email(
            "find@example.com"
        )

        assert found_user == user

    async def test_get_user_by_id(
        self, auth_service, mock_db_session
    ):
        """Test getting user by ID"""
        user_id = uuid4()
        user = User(
            id=user_id,
            email="user@example.com",
            hashed_password="hash",
            full_name="User",
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result

        found_user = await auth_service.get_user_by_id(user_id)

        assert found_user == user
        assert found_user.id == user_id
