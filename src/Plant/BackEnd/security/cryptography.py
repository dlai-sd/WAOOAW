"""
Cryptography utilities - RSA key generation + signing
"""

import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from typing import Tuple

from core.config import settings


def generate_rsa_keypair() -> Tuple[str, str]:
    """
    Generate RSA keypair for amendment signing.
    
    Returns:
        Tuple[str, str]: (private_key_pem, public_key_pem)
        
    Example:
        >>> private_pem, public_pem = generate_rsa_keypair()
        >>> # Store private_pem in Secret Manager, public_pem with entity
    """
    
    # Generate private key (RSA-4096 or RSA-2048 per settings)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=settings.rsa_key_size,
        backend=default_backend()
    )
    
    # Export private key (PEM format)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    # Export public key (PEM format)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    return private_pem, public_pem


def sign_data(data: str, private_key_pem: str) -> str:
    """
    Sign data using RSA-SHA256.
    
    Args:
        data: Data to sign (JSON string recommended)
        private_key_pem: RSA private key (PEM format)
        
    Returns:
        str: Base64-encoded signature
        
    Example:
        >>> signature = sign_data(json.dumps(amendment), private_key_pem)
    """
    
    # Load private key from PEM
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
        backend=default_backend()
    )
    
    # Sign with RSA-PSS (probabilistic signature scheme)
    signature = private_key.sign(
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Return base64-encoded signature
    return base64.b64encode(signature).decode()


def verify_signature(data: str, signature_b64: str, public_key_pem: str) -> bool:
    """
    Verify RSA-SHA256 signature (third-party verifiable).
    
    Args:
        data: Original data that was signed
        signature_b64: Base64-encoded signature
        public_key_pem: RSA public key (PEM format)
        
    Returns:
        bool: True if signature is valid, False otherwise
        
    Example:
        >>> if verify_signature(data, signature, public_key_pem):
        ...     print("Signature is authentic")
    """
    
    try:
        # Load public key from PEM
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        # Decode signature from base64
        signature = base64.b64decode(signature_b64)
        
        # Verify signature
        public_key.verify(
            signature,
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return True
    except Exception:
        return False
"""
Cryptography utilities - RSA key generation + signing
"""

import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from typing import Tuple

from core.config import settings


def generate_rsa_keypair() -> Tuple[str, str]:
    """
    Generate RSA keypair for amendment signing.
    
    Returns:
        Tuple[str, str]: (private_key_pem, public_key_pem)
        
    Example:
        >>> private_pem, public_pem = generate_rsa_keypair()
        >>> # Store private_pem in Secret Manager, public_pem with entity
    """
    
    # Generate private key (RSA-4096 or RSA-2048 per settings)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=settings.rsa_key_size,
        backend=default_backend()
    )
    
    # Export private key (PEM format)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    # Export public key (PEM format)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    return private_pem, public_pem


def sign_data(data: str, private_key_pem: str) -> str:
    """
    Sign data using RSA-SHA256.
    
    Args:
        data: Data to sign (JSON string recommended)
        private_key_pem: RSA private key (PEM format)
        
    Returns:
        str: Base64-encoded signature
        
    Example:
        >>> signature = sign_data(json.dumps(amendment), private_key_pem)
    """
    
    # Load private key from PEM
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
        backend=default_backend()
    )
    
    # Sign with RSA-PSS (probabilistic signature scheme)
    signature = private_key.sign(
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Return base64-encoded signature
    return base64.b64encode(signature).decode()


def verify_signature(data: str, signature_b64: str, public_key_pem: str) -> bool:
    """
    Verify RSA-SHA256 signature (third-party verifiable).
    
    Args:
        data: Original data that was signed
        signature_b64: Base64-encoded signature
        public_key_pem: RSA public key (PEM format)
        
    Returns:
        bool: True if signature is valid, False otherwise
        
    Example:
        >>> if verify_signature(data, signature, public_key_pem):
        ...     print("Signature is authentic")
    """
    
    try:
        # Load public key from PEM
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        # Decode signature from base64
        signature = base64.b64decode(signature_b64)
        
        # Verify signature
        public_key.verify(
            signature,
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return True
    except Exception:
        return False
"""
Cryptography utilities - RSA key generation + signing
"""

import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from typing import Tuple

from core.config import settings


def generate_rsa_keypair() -> Tuple[str, str]:
    """
    Generate RSA keypair for amendment signing.
    
    Returns:
        Tuple[str, str]: (private_key_pem, public_key_pem)
        
    Example:
        >>> private_pem, public_pem = generate_rsa_keypair()
        >>> # Store private_pem in Secret Manager, public_pem with entity
    """
    
    # Generate private key (RSA-4096 or RSA-2048 per settings)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=settings.rsa_key_size,
        backend=default_backend()
    )
    
    # Export private key (PEM format)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    # Export public key (PEM format)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    return private_pem, public_pem


def sign_data(data: str, private_key_pem: str) -> str:
    """
    Sign data using RSA-SHA256.
    
    Args:
        data: Data to sign (JSON string recommended)
        private_key_pem: RSA private key (PEM format)
        
    Returns:
        str: Base64-encoded signature
        
    Example:
        >>> signature = sign_data(json.dumps(amendment), private_key_pem)
    """
    
    # Load private key from PEM
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
        backend=default_backend()
    )
    
    # Sign with RSA-PSS (probabilistic signature scheme)
    signature = private_key.sign(
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Return base64-encoded signature
    return base64.b64encode(signature).decode()


def verify_signature(data: str, signature_b64: str, public_key_pem: str) -> bool:
    """
    Verify RSA-SHA256 signature (third-party verifiable).
    
    Args:
        data: Original data that was signed
        signature_b64: Base64-encoded signature
        public_key_pem: RSA public key (PEM format)
        
    Returns:
        bool: True if signature is valid, False otherwise
        
    Example:
        >>> if verify_signature(data, signature, public_key_pem):
        ...     print("Signature is authentic")
    """
    
    try:
        # Load public key from PEM
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        # Decode signature from base64
        signature = base64.b64decode(signature_b64)
        
        # Verify signature
        public_key.verify(
            signature,
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return True
    except Exception:
        return False
