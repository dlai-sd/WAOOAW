"""Base classes and types for social platform integrations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SocialPostResult:
    """Result of a social media post operation."""
    
    success: bool
    platform: str
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    posted_at: Optional[datetime] = None
    raw_response: Optional[dict] = None


class SocialPlatformError(Exception):
    """Base exception for social platform errors."""
    
    def __init__(
        self,
        message: str,
        platform: str,
        error_code: Optional[str] = None,
        is_transient: bool = False,
        retry_after: Optional[int] = None
    ):
        super().__init__(message)
        self.platform = platform
        self.error_code = error_code
        self.is_transient = is_transient
        self.retry_after = retry_after


class SocialPlatformClient(ABC):
    """Abstract base class for social platform clients."""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
    
    @abstractmethod
    async def post_text(
        self,
        credential_ref: str,
        text: str,
        image_url: Optional[str] = None
    ) -> SocialPostResult:
        """Post text with optional image to the platform.
        
        Args:
            credential_ref: Reference to stored credentials
            text: Text content to post
            image_url: Optional image URL to attach
            
        Returns:
            SocialPostResult with post details
            
        Raises:
            SocialPlatformError: If posting fails
        """
        pass
    
    @abstractmethod
    async def refresh_token(self, credential_ref: str) -> str:
        """Refresh OAuth2 token for the credential.
        
        Args:
            credential_ref: Reference to stored credentials
            
        Returns:
            New access token
            
        Raises:
            SocialPlatformError: If token refresh fails
        """
        pass
    
    @abstractmethod
    async def validate_credentials(self, credential_ref: str) -> bool:
        """Validate that credentials are valid and have required permissions.
        
        Args:
            credential_ref: Reference to stored credentials
            
        Returns:
            True if credentials are valid
            
        Raises:
            SocialPlatformError: If validation fails
        """
        pass
