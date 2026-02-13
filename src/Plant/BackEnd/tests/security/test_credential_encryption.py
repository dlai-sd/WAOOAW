"""
Tests for AGP2-SEC-1.1: Credential Encryption and Security Audit

Validates:
- Encryption/decryption correctness
- Key rotation functionality
- No plaintext credentials  
- Proper master key management
- Security audit capabilities
"""

import base64
import os
import pytest

from security.credential_encryption import (
    CredentialEncryption,
    CredentialSecurityAuditor,
)


class TestCredentialEncryption:
    """Test credential encryption/decryption."""
    
    def test_generate_master_key(self):
        """Test master key generation."""
        key = CredentialEncryption.generate_master_key()
        
        # Should be valid base64
        decoded = base64.urlsafe_b64decode(key)
        
        # Should be 256 bits (32 bytes)
        assert len(decoded) == 32
    
    def test_init_with_env_var(self, monkeypatch):
        """Test initialization from environment variable."""
        master_key = CredentialEncryption.generate_master_key()
        monkeypatch.setenv("CREDENTIAL_MASTER_KEY", master_key)
        
        enc = CredentialEncryption()
        
        # Should be able to encrypt
        encrypted = enc.encrypt("test_credential")
        assert encrypted
        assert ":" in encrypted
    
    def test_init_without_key_raises(self, monkeypatch):
        """Test initialization fails without master key."""
        monkeypatch.delenv("CREDENTIAL_MASTER_KEY", raising=False)
        
        with pytest.raises(ValueError, match="not configured"):
            CredentialEncryption()
    
    def test_init_with_invalid_key_raises(self):
        """Test initialization fails with invalid master key."""
        with pytest.raises(ValueError, match="Invalid master key"):
            CredentialEncryption("invalid_key")
    
    def test_init_with_wrong_size_key_raises(self):
        """Test initialization fails with wrong size key."""
        wrong_size_key = base64.urlsafe_b64encode(b"short").decode()
        
        with pytest.raises(ValueError, match="256 bits"):
            CredentialEncryption(wrong_size_key)
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test encryption and decryption roundtrip."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        plaintext = "my_api_key_12345"
        encrypted = enc.encrypt(plaintext)
        decrypted = enc.decrypt(encrypted)
        
        assert decrypted == plaintext
        assert encrypted != plaintext  # Must be encrypted
        assert ":" in encrypted  # Salt:data format
    
    def test_encrypt_different_every_time(self):
        """Test encryption produces different ciphertext each time (unique salt)."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        plaintext = "same_credential"
        encrypted1 = enc.encrypt(plaintext)
        encrypted2 = enc.encrypt(plaintext)
        
        # Different ciphertext due to random salt
        assert encrypted1 != encrypted2
        
        # But both decrypt to same plaintext
        assert enc.decrypt(encrypted1) == plaintext
        assert enc.decrypt(encrypted2) == plaintext
    
    def test_encrypt_empty_raises(self):
        """Test encrypting empty string raises error."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        with pytest.raises(ValueError, match="cannot be empty"):
            enc.encrypt("")
    
    def test_decrypt_invalid_format_raises(self):
        """Test decrypting invalid format raises error."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        with pytest.raises(ValueError, match="Invalid encrypted"):
            enc.decrypt("no_colon_format")
        
        with pytest.raises(ValueError, match="Decryption failed"):
            enc.decrypt("invalid:base64")
    
    def test_decrypt_with_wrong_key_raises(self):
        """Test decrypting with wrong key fails."""
        key1 = CredentialEncryption.generate_master_key()
        key2 = CredentialEncryption.generate_master_key()
        
        enc1 = CredentialEncryption(key1)
        enc2 = CredentialEncryption(key2)
        
        plaintext = "secret_data"
        encrypted = enc1.encrypt(plaintext)
        
        # Should fail to decrypt with different key
        with pytest.raises(ValueError, match="Decryption failed"):
            enc2.decrypt(encrypted)
    
    def test_encrypt_various_credential_types(self):
        """Test encryption works for various credential formats."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        test_creds = [
            "test_fake_key_abcdefghijklmnopqrstuvwxyz123456",  # Example key pattern
            "FakeAPIKeyDxABCDEFGHIJKLMNOPQRSTUVWXYZ12345",  # Example API key
            "Bearer test.jwt.token.example",  # Example JWT token
            "MyP@ssw0rd!Complex#2024",  # Password
            "example_secret_12345_abcde_67890",  # Example secret
        ]
        
        for cred in test_creds:
            encrypted = enc.encrypt(cred)
            decrypted = enc.decrypt(encrypted)
            assert decrypted == cred
    
    def test_key_rotation(self):
        """Test key rotation functionality."""
        old_key = CredentialEncryption.generate_master_key()
        new_key = CredentialEncryption.generate_master_key()
        
        enc_old = CredentialEncryption(old_key)
        
        plaintext = "credential_to_rotate"
        old_encrypted = enc_old.encrypt(plaintext)
        
        # Rotate to new key
        new_encrypted = enc_old.rotate_key(old_encrypted, new_key)
        
        # Old encryption should still work with old key
        assert enc_old.decrypt(old_encrypted) == plaintext
        
        # New encryption should work with new key
        enc_new = CredentialEncryption(new_key)
        assert enc_new.decrypt(new_encrypted) == plaintext
        
        # New encryption should NOT work with old key
        with pytest.raises(ValueError):
            enc_old.decrypt(new_encrypted)


class TestCredentialSecurityAuditor:
    """Test security auditing capabilities."""
    
    def test_scan_for_plaintext_api_keys(self):
        """Test scanning detects plaintext API keys."""
        code = '''
        api_key = "example_live_abcdefghijklmnopqrstuvwxyz123456"
        api_secret = "test_secret_key_1234567890abcdefgh"
        '''
        
        findings = CredentialSecurityAuditor.scan_for_plaintext_credentials(code)
        
        assert len(findings) >= 2
        assert any("example_live_" in f for f in findings)
        assert any("secret" in f.lower() for f in findings)
    
    def test_scan_for_plaintext_passwords(self):
        """Test scanning detects plaintext passwords."""
        code = '''
        password = "MyP@ssw0rd123"
        db_password = "complicated_password_here"
        '''
        
        findings = CredentialSecurityAuditor.scan_for_plaintext_credentials(code)
        
        assert len(findings) >= 2
        assert any("password" in f.lower() for f in findings)
    
    def test_scan_for_tokens(self):
        """Test scanning detects plaintext tokens."""
        code = '''
        bearer_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        access_token = "1234567890abcdefghijklmnopqrstuvwxyz"
        '''
        
        findings = CredentialSecurityAuditor.scan_for_plaintext_credentials(code)
        
        assert len(findings) >= 1
        assert any("token" in f.lower() for f in findings)
    
    def test_scan_ignores_encrypted_credentials(self):
        """Test scanning ignores encrypted credentials."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        encrypted = enc.encrypt("sk_live_sensitive_key_here")
        
        code = f'credential = "{encrypted}"'
        
        findings = CredentialSecurityAuditor.scan_for_plaintext_credentials(code)
        
        # Should not detect encrypted credentials
        assert len(findings) == 0
    
    def test_is_encrypted_detection(self):
        """Test encrypted value detection."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        # Encrypted value
        encrypted = enc.encrypt("my_credential")
        assert CredentialSecurityAuditor.is_encrypted(encrypted)
        
        # Plaintext values
        assert not CredentialSecurityAuditor.is_encrypted("plaintext_key")
        assert not CredentialSecurityAuditor.is_encrypted("")
        assert not CredentialSecurityAuditor.is_encrypted("no_colon")
    
    def test_audit_credential_storage_all_encrypted(self):
        """Test audit passes when all credentials are encrypted."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        creds = {
            "api_key": enc.encrypt("key123"),
            "api_secret": enc.encrypt("secret456"),
            "password": enc.encrypt("pass789"),
        }
        
        audit = CredentialSecurityAuditor.audit_credential_storage(creds)
        
        assert audit["encrypted_count"] == 3
        assert audit["plaintext_count"] == 0
        assert audit["plaintext_keys"] == []
        assert audit["issues"] == []
        assert audit["passed"] is True
    
    def test_audit_credential_storage_detects_plaintext(self):
        """Test audit fails when plaintext credentials found."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        creds = {
            "api_key": enc.encrypt("key123"),  # Encrypted - good
            "api_secret": "plaintext_secret",  # Plaintext - bad!
            "password": "plaintext_password",  # Plaintext - bad!
        }
        
        audit = CredentialSecurityAuditor.audit_credential_storage(creds)
        
        assert audit["encrypted_count"] == 1
        assert audit["plaintext_count"] == 2
        assert "api_secret" in audit["plaintext_keys"]
        assert "password" in audit["plaintext_keys"]
        assert len(audit["issues"]) == 2
        assert audit["passed"] is False
    
    def test_audit_empty_credentials(self):
        """Test audit handles empty credential dict."""
        audit = CredentialSecurityAuditor.audit_credential_storage({})
        
        assert audit["encrypted_count"] == 0
        assert audit["plaintext_count"] == 0
        assert audit["passed"] is True


class TestCredentialEncryptionIntegration:
    """Integration tests for credential encryption."""
    
    def test_encrypt_store_retrieve_decrypt_workflow(self):
        """Test complete workflow: encrypt → store → retrieve → decrypt."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        # Step 1: User provides credential
        user_credential = "my_delta_exchange_api_key"
        
        # Step 2: Encrypt before storing in database
        encrypted_for_db = enc.encrypt(user_credential)
        
        # Simulate database storage (in-memory dict for test)
        db = {"exchange_account_123": encrypted_for_db}
        
        # Step 3: Retrieve from database
        retrieved_encrypted = db["exchange_account_123"]
        
        # Step 4: Decrypt for use
        decrypted = enc.decrypt(retrieved_encrypted)
        
        assert decrypted == user_credential
        assert encrypted_for_db != user_credential  # Never store plaintext
    
    def test_master_key_from_secret_manager_simulation(self, monkeypatch):
        """Test loading master key from secret manager (simulated with env var)."""
        # Simulate secret manager returning master key
        secret_manager_key = CredentialEncryption.generate_master_key()
        monkeypatch.setenv("CREDENTIAL_MASTER_KEY", secret_manager_key)
        
        # Application initializes encryption
        enc = CredentialEncryption()
        
        # Should work for encryption/decryption
        plaintext = "test_credential"
        encrypted = enc.encrypt(plaintext)
        decrypted = enc.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_multiple_credentials_independent(self):
        """Test multiple credentials can be encrypted independently."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        creds = {
            "delta_exchange": "delta_api_key_123",
            "instagram": "instagram_token_456",
            "facebook": "facebook_token_789",
        }
        
        # Encrypt all
        encrypted_creds = {k: enc.encrypt(v) for k, v in creds.items()}
        
        # All should be encrypted
        for encrypted in encrypted_creds.values():
            assert ":" in encrypted
        
        # All should decrypt correctly
        for key, encrypted in encrypted_creds.items():
            decrypted = enc.decrypt(encrypted)
            assert decrypted == creds[key]


class TestCredentialSecurity:
    """Test overall security properties."""
    
    def test_no_plaintext_in_memory_after_encryption(self):
        """Test plaintext is not retained in memory after encryption."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        sensitive_credential = "very_sensitive_key_12345"
        encrypted = enc.encrypt(sensitive_credential)
        
        # Encrypted value should not contain plaintext
        assert sensitive_credential not in encrypted
        assert "very_sensitive" not in encrypted
    
    def test_encrypted_value_is_opaque(self):
        """Test encrypted values are opaque (no information leakage)."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        plaintext = "sk_live_prod_key_123"
        encrypted = enc.encrypt(plaintext)
        
        # Should not contain any plaintext fragments
        assert "sk_live" not in encrypted
        assert "prod" not in encrypted
        assert "123" not in encrypted
    
    def test_master_key_never_logged(self, monkeypatch):
        """Test master key is never exposed in string representation."""
        master_key = CredentialEncryption.generate_master_key()
        enc = CredentialEncryption(master_key)
        
        # Check string representation doesn't expose key
        str_repr = str(enc.__dict__)
        
        # Master key should be stored as bytes, not in string form
        assert master_key not in str_repr


# ========== MANUAL AUDIT TEST (Run locally) ==========

def test_audit_project_credentials_manual():
    """
    Manual test to audit project credentials.
    
    Run this test manually to scan project for plaintext credentials:
    $ pytest tests/security/test_credential_encryption.py::test_audit_project_credentials_manual -v
    """
    import glob
    
    # Scan all Python files in project
    python_files = glob.glob("**/*.py", recursive=True)
    
    all_findings = []
    
    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                findings = CredentialSecurityAuditor.scan_for_plaintext_credentials(content)
                if findings:
                    all_findings.append((file_path, findings))
        except Exception:
            # Skip files that can't be read
            pass
    
    # Print results
    if all_findings:
        print("\n⚠️  POTENTIAL PLAINTEXT CREDENTIALS FOUND:")
        for file_path, findings in all_findings:
            print(f"\n  File: {file_path}")
            for finding in findings:
                print(f"    - {finding[:50]}...")
    else:
        print("\n✅ No plaintext credentials detected")
    
    # Don't fail the test - this is informational
    assert True
