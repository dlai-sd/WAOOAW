"""Social platform integrations for marketing agent."""

from .youtube_client import YouTubeClient
from .base import SocialPlatformClient, SocialPostResult, SocialPlatformError

__all__ = [
    "YouTubeClient",
    "SocialPlatformClient",
    "SocialPostResult",
    "SocialPlatformError",
]
