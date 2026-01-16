"""
Unit Tests for Authentication Models and Schemas
Tests email/password auth models (MVP-002)
"""

import pytest
from pydantic import ValidationError

from models.user import UserRegister, UserLogin, Token, TokenData


@pytest.mark.unit
@pytest.mark.auth
class TestUserRegisterSchema:
    """Unit tests for UserRegister schema"""

    def test_valid_user_register(self):
        """Test valid user registration data"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe",
        }

        user = UserRegister(**data)
        assert user.email == "test@example.com"
        assert user.password == "SecurePass123!"
        assert user.full_name == "John Doe"

    def test_user_register_invalid_email(self):
        """Test registration with invalid email"""
        data = {
            "email": "invalid-email",
            "password": "SecurePass123!",
            "full_name": "John Doe",
        }

        with pytest.raises(ValidationError) as exc_info:
            UserRegister(**data)

        errors = exc_info.value.errors()
        assert any("email" in str(e).lower() for e in errors)

    def test_user_register_missing_password(self):
        """Test registration without password"""
        with pytest.raises(ValidationError):
            UserRegister(
                email="test@example.com",
                full_name="John Doe",
            )

    def test_user_register_missing_full_name(self):
        """Test registration without full name"""
        with pytest.raises(ValidationError):
            UserRegister(
                email="test@example.com",
                password="SecurePass123!",
            )

    def test_user_register_email_normalization(self):
        """Test email validation (case is preserved by Pydantic v2)"""
        data = {
            "email": "TEST@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe",
        }

        user = UserRegister(**data)
        # Pydantic EmailStr validates but preserves case in v2
        # Normalization happens at service/database layer if needed
        assert user.email == "TEST@example.com"


@pytest.mark.unit
@pytest.mark.auth
class TestUserLoginSchema:
    """Unit tests for UserLogin schema"""

    def test_valid_user_login(self):
        """Test valid login credentials"""
        data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
        }

        login = UserLogin(**data)
        assert login.email == "test@example.com"
        assert login.password == "SecurePass123!"

    def test_user_login_invalid_email(self):
        """Test login with invalid email"""
        with pytest.raises(ValidationError):
            UserLogin(
                email="invalid-email",
                password="password",
            )

    def test_user_login_missing_fields(self):
        """Test login with missing fields"""
        with pytest.raises(ValidationError):
            UserLogin(email="test@example.com")


@pytest.mark.unit
@pytest.mark.auth
class TestTokenSchemas:
    """Unit tests for Token and TokenData schemas"""

    def test_valid_token_response(self):
        """Test valid token response"""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 900,
        }

        token = Token(**data)
        assert token.access_token.startswith("eyJ")
        assert token.token_type == "bearer"
        assert token.expires_in == 900

    def test_token_data_extraction(self):
        """Test TokenData schema for JWT payload"""
        data = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "token_type": "access",
        }

        token_data = TokenData(**data)
        assert token_data.user_id == "550e8400-e29b-41d4-a716-446655440000"
        assert token_data.email == "user@example.com"
        assert token_data.token_type == "access"
