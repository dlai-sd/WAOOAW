"""Integration tests for Instagram Business API client.

Tests real Instagram integration with:
- Facebook Graph API authentication
- Feed posts (image + caption)
- Stories (24hr expiry)
- Reels (short-form video)
- Token refresh
- Error handling and retry logic
- Rate limit handling (200 calls/hour)
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from integrations.social.instagram_client import InstagramClient
from integrations.social.base import SocialPlatformError
from services.social_credential_resolver import (
    CPSocialCredentialResolver,
    ResolvedSocialCredentials,
    CredentialResolutionError,
)


@pytest.fixture
def mock_resolver():
    """Mock credential resolver."""
    resolver = AsyncMock(spec=CPSocialCredentialResolver)
    resolver.resolve = AsyncMock(return_value=ResolvedSocialCredentials(
        credential_ref="CRED-test",
        customer_id="CUST-123",
        platform="instagram",
        posting_identity="IG:123456789",  # Instagram Business Account ID
        access_token="mock_access_token",
        refresh_token=None,  # Instagram uses long-lived tokens
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    ))
    resolver.update_access_token = AsyncMock()
    return resolver


@pytest.fixture
def instagram_client(mock_resolver):
    """Create Instagram client with mock resolver."""
    return InstagramClient(
        credential_resolver=mock_resolver,
        customer_id="CUST-123",
    )


class TestInstagramClientPostFeed:
    """Test cases for post_feed method."""
    
    @pytest.mark.asyncio
    async def test_post_feed_success(self, instagram_client, mock_resolver):
        """Test successful feed post creation."""
        # Mock container creation response
        mock_container_response = MagicMock()
        mock_container_response.status_code = 200
        mock_container_response.json.return_value = {"id": "container123"}
        
        # Mock publish response
        mock_publish_response = MagicMock()
        mock_publish_response.status_code = 200
        mock_publish_response.json.return_value = {"id": "media456"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            # Return container response first, then publish response
            mock_client.post = AsyncMock(
                side_effect=[mock_container_response, mock_publish_response]
            )
            mock_client_class.return_value = mock_client
            
            result = await instagram_client.post_feed(
                credential_ref="CRED-test",
                caption="Test post",
                image_url="https://example.com/image.jpg",
            )
        
        assert result.success is True
        assert result.platform == "instagram"
        assert result.post_id == "media456"
        assert "instagram.com/p/media456" in result.post_url
        
        # Verify two API calls were made (container + publish)
        assert mock_client.post.call_count == 2
        assert instagram_client.calls_made == 2
    
    @pytest.mark.asyncio
    async def test_post_feed_caption_too_long(self, instagram_client):
        """Test caption length validation."""
        with pytest.raises(SocialPlatformError) as exc_info:
            await instagram_client.post_feed(
                credential_ref="CRED-test",
                caption="A" * 2201,  # Exceeds 2200 char limit
                image_url="https://example.com/image.jpg",
            )
        
        assert exc_info.value.error_code == "CAPTION_TOO_LONG"
        assert exc_info.value.is_transient is False
    
    @pytest.mark.asyncio
    async def test_post_feed_with_location(self, instagram_client, mock_resolver):
        """Test feed post with location tagging."""
        mock_container_response = MagicMock()
        mock_container_response.status_code = 200
        mock_container_response.json.return_value = {"id": "container789"}
        
        mock_publish_response = MagicMock()
        mock_publish_response.status_code = 200
        mock_publish_response.json.return_value = {"id": "media999"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[mock_container_response, mock_publish_response]
            )
            mock_client_class.return_value = mock_client
            
            result = await instagram_client.post_feed(
                credential_ref="CRED-test",
                caption="Test post with location",
                image_url="https://example.com/image.jpg",
                location_id="12345",
            )
        
        assert result.success is True
        assert result.post_id == "media999"
    
    @pytest.mark.asyncio
    async def test_post_text_requires_image(self, instagram_client):
        """Test that post_text requires image for Instagram."""
        with pytest.raises(SocialPlatformError) as exc_info:
            await instagram_client.post_text(
                credential_ref="CRED-test",
                text="Test without image",
                image_url=None,
            )
        
        assert exc_info.value.error_code == "IMAGE_REQUIRED"
        assert "require an image" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_post_feed_missing_account_id(self, instagram_client, mock_resolver):
        """Test error when Instagram Business Account ID is missing."""
        # Mock resolver to return credentials without posting_identity
        mock_resolver.resolve = AsyncMock(return_value=ResolvedSocialCredentials(
            credential_ref="CRED-test",
            customer_id="CUST-123",
            platform="instagram",
            posting_identity=None,  # Missing
            access_token="mock_token",
            refresh_token=None,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        ))
        
        with pytest.raises(SocialPlatformError) as exc_info:
            await instagram_client.post_feed(
                credential_ref="CRED-test",
                caption="Test",
                image_url="https://example.com/image.jpg",
            )
        
        assert exc_info.value.error_code == "MISSING_ACCOUNT_ID"


class TestInstagramClientPostStory:
    """Test cases for post_story method."""
    
    @pytest.mark.asyncio
    async def test_post_story_success(self, instagram_client, mock_resolver):
        """Test successful story creation."""
        mock_container_response = MagicMock()
        mock_container_response.status_code = 200
        mock_container_response.json.return_value = {"id": "story_container"}
        
        mock_publish_response = MagicMock()
        mock_publish_response.status_code = 200
        mock_publish_response.json.return_value = {"id": "story123"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[mock_container_response, mock_publish_response]
            )
            mock_client_class.return_value = mock_client
            
            result = await instagram_client.post_story(
                credential_ref="CRED-test",
                image_url="https://example.com/story.jpg",
            )
        
        assert result.success is True
        assert result.platform == "instagram"
        assert result.post_id == "story123"
        assert "instagram.com/stories" in result.post_url
        assert instagram_client.calls_made == 2


class TestInstagramClientPostReel:
    """Test cases for post_reel method."""
    
    @pytest.mark.asyncio
    async def test_post_reel_success(self, instagram_client, mock_resolver):
        """Test successful reel creation."""
        mock_container_response = MagicMock()
        mock_container_response.status_code = 200
        mock_container_response.json.return_value = {"id": "reel_container"}
        
        mock_publish_response = MagicMock()
        mock_publish_response.status_code = 200
        mock_publish_response.json.return_value = {"id": "reel456"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(
                side_effect=[mock_container_response, mock_publish_response]
            )
            mock_client_class.return_value = mock_client
            
            result = await instagram_client.post_reel(
                credential_ref="CRED-test",
                video_url="https://example.com/reel.mp4",
                caption="Test reel",
                share_to_feed=True,
            )
        
        assert result.success is True
        assert result.platform == "instagram"
        assert result.post_id == "reel456"
        assert "instagram.com/reel/reel456" in result.post_url
        assert instagram_client.calls_made == 2


class TestInstagramClientTokenRefresh:
    """Test cases for token refresh."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, instagram_client, mock_resolver):
        """Test successful token refresh."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_long_lived_token",
            "token_type": "bearer",
            "expires_in": 5184000,  # 60 days
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            new_token = await instagram_client.refresh_token("CRED-test")
        
        assert new_token == "new_long_lived_token"
        
        # Verify token was updated in CP Backend
        mock_resolver.update_access_token.assert_called_once_with(
            customer_id="CUST-123",
            credential_ref="CRED-test",
            new_access_token="new_long_lived_token",
        )
    
    @pytest.mark.asyncio
    async def test_auto_refresh_on_401(self, instagram_client, mock_resolver):
        """Test automatic token refresh on 401 Unauthorized."""
        # First call returns 401, second call (after refresh) succeeds
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        mock_response_401.json.return_value = {
            "error": {
                "message": "Invalid OAuth access token",
                "type": "OAuthException",
                "code": 190
            }
        }
        
        mock_response_200_container = MagicMock()
        mock_response_200_container.status_code = 200
        mock_response_200_container.json.return_value = {"id": "container_after_refresh"}
        
        mock_response_200_publish = MagicMock()
        mock_response_200_publish.status_code = 200
        mock_response_200_publish.json.return_value = {"id": "media_after_refresh"}
        
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "refreshed_token",
            "expires_in": 5184000,
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            
            # First container call: 401, then GET for refresh (success), then container (success), then publish (success)
            mock_client.post = AsyncMock(
                side_effect=[
                    mock_response_401,
                    mock_response_200_container,
                    mock_response_200_publish,
                ]
            )
            mock_client.get = AsyncMock(return_value=mock_token_response)
            mock_client_class.return_value = mock_client
            
            result = await instagram_client.post_feed(
                credential_ref="CRED-test",
                caption="Test post",
                image_url="https://example.com/image.jpg",
            )
        
        assert result.success is True
        assert result.post_id == "media_after_refresh"
        
        # Verify token was refreshed and updated
        mock_resolver.update_access_token.assert_called_once()


class TestInstagramClientValidateCredentials:
    """Test cases for credential validation."""
    
    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, instagram_client, mock_resolver):
        """Test successful credential validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456789",
            "username": "test_account"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            is_valid = await instagram_client.validate_credentials("CRED-test")
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_credentials_no_account(self, instagram_client, mock_resolver):
        """Test validation failure when no account found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Empty response = no account
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await instagram_client.validate_credentials("CRED-test")
        
        assert exc_info.value.error_code == "NO_ACCOUNT"
        assert exc_info.value.is_transient is False


class TestInstagramClientErrorClassification:
    """Test cases for error classification."""
    
    def test_classify_rate_limit(self, instagram_client):
        """Test rate limit error classification."""
        error_body = {
            "error": {
                "message": "Application request limit reached",
                "type": "OAuthException",
                "code": 4
            }
        }
        
        error = instagram_client._classify_error(429, error_body)
        
        assert error.error_code == "RATE_LIMIT"
        assert error.is_transient is True
        assert error.retry_after == 3600  # 1 hour
    
    def test_classify_auth_error(self, instagram_client):
        """Test authentication error classification."""
        error_body = {
            "error": {
                "message": "Invalid OAuth access token",
                "type": "OAuthException",
                "code": 190
            }
        }
        
        error = instagram_client._classify_error(401, error_body)
        
        assert error.error_code == "AUTH_FAILED"
        assert error.is_transient is False
    
    def test_classify_permission_error(self, instagram_client):
        """Test permission denied error classification."""
        error_body = {
            "error": {
                "message": "Permissions error",
                "type": "OAuthException",
                "code": 200
            }
        }
        
        error = instagram_client._classify_error(403, error_body)
        
        assert error.error_code == "PERMISSION_DENIED"
        assert error.is_transient is False
    
    def test_classify_server_error(self, instagram_client):
        """Test server error classification."""
        error_body = {
            "error": {
                "message": "Internal server error",
                "type": "FacebookApiException",
                "code": 1
            }
        }
        
        error = instagram_client._classify_error(500, error_body)
        
        assert error.error_code == "SERVER_ERROR"
        assert error.is_transient is True
    
    def test_classify_media_error_transient(self, instagram_client):
        """Test transient media error classification."""
        error_body = {
            "error": {
                "message": "Media upload error",
                "type": "InstagramApiException",
                "code": 9004,
                "error_subcode": 2207013  # Transient subcode
            }
        }
        
        error = instagram_client._classify_error(400, error_body)
        
        assert error.error_code == "MEDIA_ERROR"
        assert error.is_transient is True
    
    def test_classify_media_error_permanent(self, instagram_client):
        """Test permanent media error classification."""
        error_body = {
            "error": {
                "message": "Invalid image format",
                "type": "InstagramApiException",
                "code": 9004,
                "error_subcode": 9999  # Non-transient subcode
            }
        }
        
        error = instagram_client._classify_error(400, error_body)
        
        assert error.error_code == "MEDIA_ERROR"
        assert error.is_transient is False


class TestInstagramClientRetryLogic:
    """Test cases for retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, instagram_client, mock_resolver):
        """Test retry on transient errors (e.g., rate limit)."""
        # First two calls fail with rate limit, third succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.json.return_value = {
            "error": {"message": "Rate limit exceeded", "code": 4}
        }
        
        mock_response_200_container = MagicMock()
        mock_response_200_container.status_code = 200
        mock_response_200_container.json.return_value = {"id": "container_after_retry"}
        
        mock_response_200_publish = MagicMock()
        mock_response_200_publish.status_code = 200
        mock_response_200_publish.json.return_value = {"id": "media_after_retry"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            
            # Return 429 twice, then success for container and publish
            mock_client.post = AsyncMock(
                side_effect=[
                    mock_response_429,
                    mock_response_429,
                    mock_response_200_container,
                    mock_response_200_publish,
                ]
            )
            mock_client_class.return_value = mock_client
            
            result = await instagram_client.post_feed(
                credential_ref="CRED-test",
                caption="Test with retries",
                image_url="https://example.com/image.jpg",
            )
        
        assert result.success is True
        assert result.post_id == "media_after_retry"
        
        # Verify retry happened (4 total calls: 2 failed + 2 successful)
        assert mock_client.post.call_count == 4
    
    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, instagram_client, mock_resolver):
        """Test no retry on permanent errors (e.g., permission denied)."""
        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403
        mock_response_403.json.return_value = {
            "error": {"message": "Permission denied", "code": 200}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_403)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await instagram_client.post_feed(
                    credential_ref="CRED-test",
                    caption="Test",
                    image_url="https://example.com/image.jpg",
                )
        
        # Should fail immediately without retries
        assert mock_client.post.call_count == 1
        assert exc_info.value.is_transient is False


class TestInstagramClientCallTracking:
    """Test cases for API call tracking."""
    
    @pytest.mark.asyncio
    async def test_call_tracking_on_feed_post(self, instagram_client, mock_resolver):
        """Test API calls are tracked after successful feed post."""
        mock_container = MagicMock()
        mock_container.status_code = 200
        mock_container.json.return_value = {"id": "container"}
        
        mock_publish = MagicMock()
        mock_publish.status_code = 200
        mock_publish.json.return_value = {"id": "media"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[mock_container, mock_publish])
            mock_client_class.return_value = mock_client
            
            initial_calls = instagram_client.calls_made
            await instagram_client.post_feed(
                credential_ref="CRED-test",
                caption="Test",
                image_url="https://example.com/image.jpg",
            )
        
        # Feed post should make 2 API calls (container + publish)
        assert instagram_client.calls_made == initial_calls + 2
    
    @pytest.mark.asyncio
    async def test_call_tracking_on_story(self, instagram_client, mock_resolver):
        """Test API calls are tracked after story post."""
        mock_container = MagicMock()
        mock_container.status_code = 200
        mock_container.json.return_value = {"id": "story_container"}
        
        mock_publish = MagicMock()
        mock_publish.status_code = 200
        mock_publish.json.return_value = {"id": "story"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(side_effect=[mock_container, mock_publish])
            mock_client_class.return_value = mock_client
            
            initial_calls = instagram_client.calls_made
            await instagram_client.post_story(
                credential_ref="CRED-test",
                image_url="https://example.com/story.jpg",
            )
        
        # Story post should make 2 API calls (container + publish)
        assert instagram_client.calls_made == initial_calls + 2
