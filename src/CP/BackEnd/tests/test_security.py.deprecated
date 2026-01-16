"""
Unit Tests for Password Hashing and Security
Tests bcrypt password utilities (MVP-002)
"""

import pytest

from core.security import hash_password, verify_password


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordHashing:
    """Unit tests for password hashing functions"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "SecurePassword123!"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) == 60  # bcrypt hash length

    def test_hash_password_deterministic(self):
        """Test that same password produces different hashes (salt)"""
        password = "TestPassword456!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different due to random salt

    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "CorrectPassword789!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test verifying empty password"""
        password = "RealPassword"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False

    def test_hash_password_special_characters(self):
        """Test hashing password with special characters"""
        password = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_hash_password_unicode(self):
        """Test hashing password with unicode characters"""
        password = "Pàsswörd123™"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_case_sensitive(self):
        """Test password verification is case-sensitive"""
        password = "CaseSensitive"
        hashed = hash_password(password)

        assert verify_password("casesensitive", hashed) is False
        assert verify_password("CASESENSITIVE", hashed) is False
