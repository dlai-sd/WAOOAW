"""
Secrets Management - Story 5.3

Secure handling of API keys, tokens, and sensitive configuration.
Part of Epic 5: Common Components.
"""
import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import base64
from pathlib import Path

logger = logging.getLogger(__name__)


class SecretNotFoundError(Exception):
    """Secret not found."""
    pass


class SecretValidationError(Exception):
    """Secret validation failed."""
    pass


@dataclass
class SecretMetadata:
    """Metadata for a secret."""
    name: str
    description: str
    required: bool = True
    env_var: Optional[str] = None
    validation_pattern: Optional[str] = None


class SecretsManager:
    """
    Secure secrets management.
    
    Features:
    - Load from environment variables
    - Load from .env files (development)
    - Validate secret format
    - Secure in-memory storage (obfuscated)
    - Audit logging
    - Integration with cloud secret stores (AWS Secrets Manager, etc.)
    
    Priority:
    1. Environment variables (production)
    2. .env file (development only)
    3. Default values (non-sensitive only)
    """
    
    def __init__(
        self,
        env_file: Optional[str] = None,
        allow_env_file: bool = True,
        environment: str = "development"
    ):
        """
        Initialize secrets manager.
        
        Args:
            env_file: Path to .env file (development only)
            allow_env_file: Whether to allow loading from .env
            environment: Environment (development, staging, production)
        """
        self.environment = environment
        self.allow_env_file = allow_env_file and environment == "development"
        
        # Obfuscated secret storage
        self._secrets: Dict[str, str] = {}
        self._metadata: Dict[str, SecretMetadata] = {}
        
        # Load .env if in development
        if self.allow_env_file and env_file:
            self._load_env_file(env_file)
        
        logger.info(
            f"SecretsManager initialized: env={environment}, "
            f"env_file_enabled={self.allow_env_file}"
        )
    
    def register_secret(
        self,
        name: str,
        description: str,
        required: bool = True,
        env_var: Optional[str] = None,
        validation_pattern: Optional[str] = None
    ) -> None:
        """
        Register a secret with metadata.
        
        Args:
            name: Secret name (internal key)
            description: Human-readable description
            required: Whether secret is required
            env_var: Environment variable name (defaults to name.upper())
            validation_pattern: Regex pattern for validation
        """
        if env_var is None:
            env_var = name.upper()
        
        metadata = SecretMetadata(
            name=name,
            description=description,
            required=required,
            env_var=env_var,
            validation_pattern=validation_pattern
        )
        
        self._metadata[name] = metadata
        
        logger.debug(f"Registered secret: {name} (env_var={env_var})")
    
    def load_secret(
        self,
        name: str,
        default: Optional[str] = None
    ) -> None:
        """
        Load secret from environment.
        
        Args:
            name: Secret name
            default: Default value (for non-required secrets)
        """
        metadata = self._metadata.get(name)
        if not metadata:
            raise ValueError(f"Secret not registered: {name}")
        
        # Try environment variable
        value = os.environ.get(metadata.env_var)
        
        # Fall back to default
        if value is None:
            if default is not None:
                value = default
            elif metadata.required:
                raise SecretNotFoundError(
                    f"Required secret not found: {name} (env: {metadata.env_var})"
                )
        
        # Validate
        if value is not None:
            self._validate_secret(name, value)
            
            # Store (obfuscated)
            self._secrets[name] = self._obfuscate(value)
            
            logger.info(f"Secret loaded: {name}")
    
    def get_secret(self, name: str) -> str:
        """
        Get secret value.
        
        Args:
            name: Secret name
            
        Returns:
            Secret value
            
        Raises:
            SecretNotFoundError: If secret not loaded
        """
        if name not in self._secrets:
            raise SecretNotFoundError(f"Secret not loaded: {name}")
        
        # Deobfuscate
        return self._deobfuscate(self._secrets[name])
    
    def get_secret_safe(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret value safely (returns None/default if not found).
        
        Args:
            name: Secret name
            default: Default value
            
        Returns:
            Secret value or default
        """
        try:
            return self.get_secret(name)
        except SecretNotFoundError:
            return default
    
    def has_secret(self, name: str) -> bool:
        """Check if secret is loaded."""
        return name in self._secrets
    
    def list_secrets(self, include_loaded_status: bool = True) -> Dict[str, Any]:
        """
        List all registered secrets.
        
        Args:
            include_loaded_status: Include whether secret is loaded
            
        Returns:
            Dict of secret metadata
        """
        result = {}
        
        for name, metadata in self._metadata.items():
            result[name] = {
                "description": metadata.description,
                "required": metadata.required,
                "env_var": metadata.env_var
            }
            
            if include_loaded_status:
                result[name]["loaded"] = name in self._secrets
        
        return result
    
    def load_all_secrets(self) -> Dict[str, bool]:
        """
        Load all registered secrets.
        
        Returns:
            Dict mapping secret name to success status
        """
        results = {}
        
        for name in self._metadata.keys():
            try:
                self.load_secret(name)
                results[name] = True
            except SecretNotFoundError as e:
                logger.warning(f"Failed to load secret {name}: {e}")
                results[name] = False
        
        return results
    
    def _load_env_file(self, env_file: str) -> None:
        """Load secrets from .env file (development only)."""
        env_path = Path(env_file)
        
        if not env_path.exists():
            logger.warning(f".env file not found: {env_file}")
            return
        
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        # Set in environment
                        os.environ[key] = value
            
            logger.info(f"Loaded .env file: {env_file}")
        
        except Exception as e:
            logger.error(f"Failed to load .env file: {e}", exc_info=True)
    
    def _validate_secret(self, name: str, value: str) -> None:
        """Validate secret format."""
        metadata = self._metadata.get(name)
        if not metadata:
            return
        
        # Check pattern
        if metadata.validation_pattern:
            import re
            if not re.match(metadata.validation_pattern, value):
                raise SecretValidationError(
                    f"Secret validation failed: {name}"
                )
    
    def _obfuscate(self, value: str) -> str:
        """Obfuscate secret for in-memory storage."""
        # Simple base64 encoding (not encryption, just obfuscation)
        return base64.b64encode(value.encode()).decode()
    
    def _deobfuscate(self, value: str) -> str:
        """Deobfuscate secret."""
        return base64.b64decode(value.encode()).decode()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get secrets statistics."""
        total_registered = len(self._metadata)
        total_loaded = len(self._secrets)
        required_count = sum(1 for m in self._metadata.values() if m.required)
        
        return {
            "total_registered": total_registered,
            "total_loaded": total_loaded,
            "required_count": required_count,
            "loading_rate": (
                total_loaded / total_registered * 100
                if total_registered > 0 else 0
            )
        }


# Global secrets manager
_global_secrets: Optional[SecretsManager] = None


def init_secrets(
    env_file: Optional[str] = None,
    environment: Optional[str] = None
) -> SecretsManager:
    """
    Initialize global secrets manager.
    
    Args:
        env_file: Path to .env file
        environment: Environment name
        
    Returns:
        SecretsManager instance
    """
    global _global_secrets
    
    if environment is None:
        environment = os.environ.get("WAOOAW_ENV", "development")
    
    _global_secrets = SecretsManager(
        env_file=env_file,
        environment=environment
    )
    
    return _global_secrets


def get_secrets() -> SecretsManager:
    """Get global secrets manager."""
    if _global_secrets is None:
        raise RuntimeError("Secrets manager not initialized. Call init_secrets() first.")
    
    return _global_secrets


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get secret."""
    return get_secrets().get_secret_safe(name, default)
