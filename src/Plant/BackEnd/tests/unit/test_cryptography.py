"""
Unit tests for cryptography utilities
"""

import pytest

from security.cryptography import generate_rsa_keypair, sign_data, verify_signature


class TestRSAKeypairGeneration:
    """Test RSA keypair generation."""
    
    def test_generate_keypair_returns_pem_strings(self):
        """Test that generate_rsa_keypair returns PEM-formatted keys."""
        private_pem, public_pem = generate_rsa_keypair()
        
        assert "BEGIN PRIVATE KEY" in private_pem
        assert "END PRIVATE KEY" in private_pem
        assert "BEGIN PUBLIC KEY" in public_pem
        assert "END PUBLIC KEY" in public_pem


class TestRSASigning:
    """Test RSA data signing."""
    
    def test_sign_data_returns_base64_signature(self, rsa_keypair):
        """Test that sign_data returns base64-encoded signature."""
        private_pem, _ = rsa_keypair
        data = "Hello, World!"
        
        signature = sign_data(data, private_pem)
        
        assert signature is not None
        assert len(signature) > 0
        assert isinstance(signature, str)
    
    def test_verify_signature_succeeds_with_correct_key(self, rsa_keypair):
        """Test that signature verification succeeds with correct key."""
        private_pem, public_pem = rsa_keypair
        data = "Hello, World!"
        
        signature = sign_data(data, private_pem)
        is_valid = verify_signature(data, signature, public_pem)
        
        assert is_valid is True
    
    def test_verify_signature_fails_with_wrong_key(self, rsa_keypair):
        """Test that signature verification fails with wrong key."""
        private_pem, _ = rsa_keypair
        _, wrong_public_pem = generate_rsa_keypair()
        data = "Hello, World!"
        
        signature = sign_data(data, private_pem)
        is_valid = verify_signature(data, signature, wrong_public_pem)
        
        assert is_valid is False
    
    def test_verify_signature_fails_with_tampered_data(self, rsa_keypair):
        """Test that signature verification fails with tampered data."""
        private_pem, public_pem = rsa_keypair
        data = "Hello, World!"
        
        signature = sign_data(data, private_pem)
        tampered_data = "Hello, World! (tampered)"
        is_valid = verify_signature(tampered_data, signature, public_pem)
        
        assert is_valid is False
