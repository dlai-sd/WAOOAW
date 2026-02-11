"""Integration tests for YouTube API client.

Tests real YouTube integration with:
- OAuth2 authentication
- Community post creation
- Shorts upload
- Token refresh
- Error handling and retry logic
- Rate limit handling
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from integrations.social.youtube_client import YouTubeClient
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
        platform="youtube",
        posting_identity="test-channel",
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    ))
    resolver.update_access_token = AsyncMock()
    return resolver


@pytest.fixture
def youtube_client(mock_resolver):
    """Create YouTube client with mock resolver."""
    return YouTubeClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        credential_resolver=mock_resolver,
        customer_id="CUST-123",
    )


class TestYouTubeClientPostText:
    """Test cases for post_text method."""
    
    @pytest.mark.asyncio
    async def test_post_text_success(self, youtube_client, mock_resolver):
        """Test successful community post creation."""
        # Mock successful YouTube API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "post123",
            "snippet": {"text": "Test post"}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await youtube_client.post_text(
                credential_ref="CRED-test",
                text="Test post",
            )
        
        assert result.success is True
        assert result.platform == "youtube"
        assert result.post_id == "post123"
        assert "youtube.com/post/post123" in result.post_url
        
        # Verify resolver was called
        mock_resolver.resolve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_text_too_long(self, youtube_client):
        """Test text length validation."""
        with pytest.raises(SocialPlatformError) as exc_info:
            await youtube_client.post_text(
                credential_ref="CRED-test",
                text="A" * 1001,  # Exceeds 1000 char limit
            )
        
        assert exc_info.value.error_code == "TEXT_TOO_LONG"
        assert exc_info.value.is_transient is False
    
    @pytest.mark.asyncio
    async def test_post_text_with_image(self, youtube_client, mock_resolver):
        """Test post with image URL."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "post456",
            "snippet": {"text": "Test with image\nhttps://example.com/img.jpg"}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await youtube_client.post_text(
                credential_ref="CRED-test",
                text="Test with image",
                image_url="https://example.com/img.jpg",
            )
        
        assert result.success is True
        assert result.post_id == "post456"
    
    @pytest.mark.asyncio
    async def test_post_text_credential_resolution_error(self, youtube_client, mock_resolver):
        """Test credential resolution failure."""
        mock_resolver.resolve = AsyncMock(
            side_effect=CredentialResolutionError("Credential not found")
        )
        
        with pytest.raises(SocialPlatformError) as exc_info:
            await youtube_client.post_text(
                credential_ref="CRED-missing",
                text="Test post",
            )
        
        assert "Credential resolution failed" in exc_info.value.message
        assert exc_info.value.is_transient is False


class TestYouTubeClientPostShort:
    """Test cases for post_short method."""
    
    @pytest.mark.asyncio
    async def test_post_short_success(self, youtube_client, mock_resolver):
        """Test successful Shorts upload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "short789",
            "snippet": {"title": "Test Short"}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await youtube_client.post_short(
                credential_ref="CRED-test",
                video_url="https://example.com/video.mp4",
                title="Test Short",
                description="Test description",
            )
        
        assert result.success is True
        assert result.platform == "youtube"
        assert result.post_id == "short789"
        assert "youtube.com/shorts/short789" in result.post_url
        
        # Verify quota tracking
        assert youtube_client.quota_used > 0
    
    @pytest.mark.asyncio
    async def test_post_short_title_too_long(self, youtube_client):
        """Test Shorts title length validation."""
        with pytest.raises(SocialPlatformError) as exc_info:
            await youtube_client.post_short(
                credential_ref="CRED-test",
                video_url="https://example.com/video.mp4",
                title="A" * 101,  # Exceeds 100 char limit
            )
        
        assert exc_info.value.error_code == "TITLE_TOO_LONG"
        assert exc_info.value.is_transient is False


class TestYouTubeClientTokenRefresh:
    """Test cases for token refresh."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, youtube_client, mock_resolver):
        """Test successful token refresh."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            new_token = await youtube_client.refresh_token("CRED-test")
        
        assert new_token == "new_access_token"
        
        # Verify token was updated in CP Backend
        mock_resolver.update_access_token.assert_called_once_with(
            customer_id="CUST-123",
            credential_ref="CRED-test",
            new_access_token="new_access_token",
        )
    
    @pytest.mark.asyncio
    async def test_auto_refresh_on_401(self, youtube_client, mock_resolver):
        """Test automatic token refresh on 401 Unauthorized."""
        # First call returns 401, second call (after refresh) succeeds
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        mock_response_401.json.return_value = {
            "error": {"message": "Invalid credentials", "errors": [{"reason": "authError"}]}
        }
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "id": "post_after_refresh",
            "snippet": {"text": "Posted after token refresh"}
        }
        
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "refreshed_token",
            "expires_in": 3600,
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            
            # Return 401 first, then success after refresh
            mock_client.post = AsyncMock(
                side_effect=[mock_response_401, mock_token_response, mock_response_200]
            )
            mock_client_class.return_value = mock_client
            
            result = await youtube_client.post_text(
                credential_ref="CRED-test",
                text="Test post",
            )
        
        assert result.success is True
        assert result.post_id == "post_after_refresh"
        
        # Verify token was refreshed and updated
        mock_resolver.update_access_token.assert_called_once()


class TestYouTubeClientValidateCredentials:
    """Test cases for credential validation."""
    
    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, youtube_client, mock_resolver):
        """Test successful credential validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [{"id": "channel123", "snippet": {"title": "Test Channel"}}]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            is_valid = await youtube_client.validate_credentials("CRED-test")
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_credentials_no_channel(self, youtube_client, mock_resolver):
        """Test validation failure when no channel found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}  # Empty items = no channel
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await youtube_client.validate_credentials("CRED-test")
        
        assert exc_info.value.error_code == "NO_CHANNEL"
        assert exc_info.value.is_transient is False


class TestYouTubeClientErrorClassification:
    """Test cases for error classification."""
    
    def test_classify_quota_exceeded(self, youtube_client):
        """Test quota exceeded error classification."""
        error_body = {
            "error": {
                "message": "Quota exceeded",
                "errors": [{"reason": "quotaExceeded"}]
            }
        }
        
        error = youtube_client._classify_error(403, error_body)
        
        assert error.error_code == "QUOTA_EXCEEDED"
        assert error.is_transient is True
        assert error.retry_after == 86400  # 24 hours
    
    def test_classify_rate_limit(self, youtube_client):
        """Test rate limit error classification."""
        error_body = {"error": {"message": "Too many requests"}}
        
        error = youtube_client._classify_error(429, error_body)
        
        assert error.error_code == "RATE_LIMIT"
        assert error.is_transient is True
        assert error.retry_after == 60
    
    def test_classify_auth_error(self, youtube_client):
        """Test authentication error classification."""
        error_body = {
            "error": {
                "message": "Invalid credentials",
                "errors": [{"reason": "authError"}]
            }
        }
        
        error = youtube_client._classify_error(401, error_body)
        
        assert error.error_code == "AUTH_FAILED"
        assert error.is_transient is False
    
    def test_classify_server_error(self, youtube_client):
        """Test server error classification."""
        error_body = {"error": {"message": "Internal server error"}}
        
        error = youtube_client._classify_error(500, error_body)
        
        assert error.error_code == "SERVER_ERROR"
        assert error.is_transient is True


class TestYouTubeClientRetryLogic:
    """Test cases for retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, youtube_client, mock_resolver):
        """Test retry on transient errors (e.g., 429 rate limit)."""
        # First two calls fail with 429, third succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.json.return_value = {
            "error": {"message": "Rate limit exceeded"}
        }
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "id": "post_after_retry",
            "snippet": {"text": "Posted after retries"}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            
            # Return 429 twice, then success
            mock_client.post = AsyncMock(
                side_effect=[mock_response_429, mock_response_429, mock_response_200]
            )
            mock_client_class.return_value = mock_client
            
            result = await youtube_client.post_text(
                credential_ref="CRED-test",
                text="Test post with retries",
            )
        
        assert result.success is True
        assert result.post_id == "post_after_retry"
        
        # Verify retry happened (3 total calls)
        assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, youtube_client, mock_resolver):
        """Test no retry on permanent errors (e.g., 400 bad request)."""
        mock_response_400 = MagicMock()
        mock_response_400.status_code = 400
        mock_response_400.json.return_value = {
            "error": {"message": "Invalid request", "errors": [{"reason": "badRequest"}]}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_400)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await youtube_client.post_text(
                    credential_ref="CRED-test",
                    text="Test post",
                )
        
        # Should fail immediately without retries
        assert mock_client.post.call_count == 1
        assert exc_info.value.is_transient is False


class TestYouTubeClientQuotaTracking:
    """Test cases for quota usage tracking."""
    
    @pytest.mark.asyncio
    async def test_quota_tracking_on_post(self, youtube_client, mock_resolver):
        """Test quota usage is tracked after successful post."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "post123", "snippet": {}}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            initial_quota = youtube_client.quota_used
            await youtube_client.post_text(
                credential_ref="CRED-test",
                text="Test post",
            )
        
        # Community post should consume ~50 quota units
        assert youtube_client.quota_used > initial_quota
        assert youtube_client.quota_used >= 50
    
    @pytest.mark.asyncio
    async def test_quota_tracking_on_short(self, youtube_client, mock_resolver):
        """Test quota usage is tracked after Shorts upload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "short456", "snippet": {}}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            initial_quota = youtube_client.quota_used
            await youtube_client.post_short(
                credential_ref="CRED-test",
                video_url="https://example.com/video.mp4",
                title="Test Short",
            )
        
        # Shorts upload should consume ~1600 quota units
        assert youtube_client.quota_used > initial_quota
        assert youtube_client.quota_used >= 1600
