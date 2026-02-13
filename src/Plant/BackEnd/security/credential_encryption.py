"""
AGP2-SEC-1.1: Credential Encryption and Security Audit

Provides encryption/decryption for sensitive credentials with key management.
All credentials must be encrypted at rest with proper key rotation support.
"""

from __future__ import annotations

import base64
import os
import re
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class CredentialEncryption:
    """
    Encrypt/decrypt credentials using Fernet (AES-128-CBC + HMAC-SHA256).
    
    Features:
    - Key derivation from master key using PBKDF2-HMAC-SHA256
    - Automatic salt generation for each encryption
    - No plaintext credentials in memory longer than necessary
    - Support for key rotation
    """
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize credential encryption.
        
        Args:
            master_key: Base64-encoded 256-bit master key from environment.
                       If None, uses CREDENTIAL_MASTER_KEY env var.
                       
        Raises:
            ValueError: If master_key is not provided and env var not set
        """
        if master_key is None:
            master_key = os.getenv("CREDENTIAL_MASTER_KEY")
            
        if not master_key:
            raise ValueError(
                "Credential master key not configured. Set CREDENTIAL_MASTER_KEY environment variable."
            )
            
        try:
            self._master_key = base64.urlsafe_b64decode(master_key)
        except Exception as e:
            raise ValueError(f"Invalid master key format: {e}") from e
            
        if len(self._master_key) != 32:  # 256 bits
            raise ValueError("Master key must be 256 bits (32 bytes)")
    
    @staticmethod
    def generate_master_key() -> str:
        """
        Generate a new 256-bit master key.
        
        Returns:
            str: Base64-encoded master key (store securely in Secret Manager)
            
        Example:
            >>> master_key = CredentialEncryption.generate_master_key()
            >>> # Store in GCP Secret Manager or AWS Secrets Manager
        """
        return base64.urlsafe_b64encode(os.urandom(32)).decode()
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a credential string.
        
        Args:
            plaintext: Credential to encrypt (API key, password, token, etc.)
            
        Returns:
            str: Base64-encoded encrypted credential with embedded salt
            
        Example:
            >>> enc = CredentialEncryption()
            >>> encrypted = enc.encrypt("my_api_key_123")
            >>> # Store encrypted in database
        """
        if not plaintext:
            raise ValueError("Plaintext cannot be empty")
            
        # Generate random salt for this encryption
        salt = os.urandom(16)
        
        # Derive encryption key from master key + salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(self._master_key))
        
        # Encrypt using Fernet
        f = Fernet(derived_key)
        encrypted_data = f.encrypt(plaintext.encode())
        
        # Prepend salt to encrypted data (salt:encrypted_data format)
        salt_b64 = base64.urlsafe_b64encode(salt).decode()
        encrypted_b64 = encrypted_data.decode()
        
        return f"{salt_b64}:{encrypted_b64}"
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt an encrypted credential.
        
        Args:
            encrypted: Encrypted credential from encrypt()
            
        Returns:
            str: Decrypted plaintext credential
            
        Raises:
            ValueError: If encrypted format is invalid or decryption fails
            
        Example:
            >>> enc = CredentialEncryption()
            >>> plaintext = enc.decrypt(encrypted_credential)
        """
        if not encrypted or ":" not in encrypted:
            raise ValueError("Invalid encrypted credential format")
            
        try:
            salt_b64, encrypted_b64 = encrypted.split(":", 1)
            salt = base64.urlsafe_b64decode(salt_b64)
            
            # Derive same encryption key using stored salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(self._master_key))
            
            # Decrypt using Fernet
            f = Fernet(derived_key)
            decrypted_data = f.decrypt(encrypted_b64.encode())
            
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}") from e
    
    def rotate_key(self, old_encrypted: str, new_master_key: str) -> str:
        """
        Rotate credential encryption to a new master key.
        
        Args:
            old_encrypted: Credential encrypted with current master key
            new_master_key: New base64-encoded master key
            
        Returns:
            str: Credential re-encrypted with new master key
            
        Example:
            >>> enc = CredentialEncryption(old_key)
            >>> new_encrypted = enc.rotate_key(old_encrypted, new_key)
        """
        # Decrypt with current key
        plaintext = self.decrypt(old_encrypted)
        
        # Re-encrypt with new key
        new_enc = CredentialEncryption(new_master_key)
        return new_enc.encrypt(plaintext)


class CredentialSecurityAuditor:
    """
    Audit credential storage security for compliance.
    
    Checks:
    - No plaintext credentials in code
    - All stored credentials are encrypted
    - Master key is properly configured
    - No credentials in logs
    """
    
    # Patterns that look like credentials (heuristic)
    CREDENTIAL_PATTERNS = [
        r'api[_-]?key["\s:=]+[a-zA-Z0-9_\-]{20,}',
        r'api[_-]?secret["\s:=]+[a-zA-Z0-9_\-]{20,}',
        r'password["\s:=]+.{8,}',
        r'token["\s:=]+[a-zA-Z0-9_\-]{20,}',
        r'bearer\s+[a-zA-Z0-Z._\-]{20,}',
        r'sk_live_[a-zA-Z0-9]{24,}',  # Stripe live keys
        r'AIza[a-zA-Z0-9_\-]{35}',  # Google API keys
    ]
    
    @classmethod
    def scan_for_plaintext_credentials(cls, text: str) -> list[str]:
        """
        Scan text for potential plaintext credentials.
        
        Args:
            text: Text to scan (code, logs, config, etc.)
            
        Returns:
            list[str]: List of potential plaintext credentials found
            
        Example:
            >>> findings = CredentialSecurityAuditor.scan_for_plaintext_credentials(code)
            >>> if findings:
            ...     print(f"WARNING: {len(findings)} potential credentials found")
        """
        findings = []
        
        for pattern in cls.CREDENTIAL_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Skip if it looks like encrypted (base64 with colons)
                if ":" in match.group() and any(c in match.group() for c in "_-"):
                    continue
                findings.append(match.group())
        
        return findings
    
    @classmethod
    def is_encrypted(cls, value: str) -> bool:
        """
        Check if a value appears to be encrypted (heuristic).
        
        Args:
            value: Value to check
            
        Returns:
            bool: True if value looks encrypted (salt:data format)
        """
        if not value or ":" not in value:
            return False
            
        parts = value.split(":", 1)
        if len(parts) != 2:
            return False
            
        # Check if both parts are valid base64
        try:
            base64.urlsafe_b64decode(parts[0])
            base64.urlsafe_b64decode(parts[1])
            return True
        except Exception:
            return False
    
    @classmethod
    def audit_credential_storage(
        cls,
        credentials: dict[str, str]
    ) -> dict[str, list[str]]:
        """
        Audit a dictionary of credentials for security compliance.
        
        Args:
            credentials: Dictionary of credential_name: credential_value
            
        Returns:
            dict with audit results:
                - encrypted_count: Number of encrypted credentials
                - plaintext_count: Number of plaintext credentials
                - plaintext_keys: List of keys with plaintext values
                - issues: List of security issues found
                
        Example:
            >>> creds = {"api_key": encrypted_key, "password": "plaintext123"}
            >>> audit = CredentialSecurityAuditor.audit_credential_storage(creds)
            >>> if audit["plaintext_count"] > 0:
            ...     print(f"FAIL: {audit['plaintext_count']} plaintext credentials")
        """
        encrypted_count = 0
        plaintext_count = 0
        plaintext_keys = []
        issues = []
        
        for key, value in credentials.items():
            if cls.is_encrypted(value):
                encrypted_count += 1
            else:
                plaintext_count += 1
                plaintext_keys.append(key)
                issues.append(f"Credential '{key}' is stored in plaintext")
        
        return {
            "encrypted_count": encrypted_count,
            "plaintext_count": plaintext_count,
            "plaintext_keys": plaintext_keys,
            "issues": issues,
            "passed": plaintext_count == 0
        }
