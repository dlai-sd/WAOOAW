"""Integration tests for Facebook Business API client.

Tests real Facebook integration with:
- Facebook Graph API authentication
- Page posting (text, image, link)
- Token refresh
- Permission validation
- Error handling and retry logic
- Rate limit handling
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from integrations.social.facebook_client import FacebookClient
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
        platform="facebook",
        posting_identity="FB_PAGE:987654321",  # Facebook Page ID
        access_token="mock_page_access_token",
        refresh_token=None,  # Facebook uses long-lived tokens
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    ))
    resolver.update_access_token = AsyncMock()
    return resolver


@pytest.fixture
def facebook_client(mock_resolver):
    """Create Facebook client with mock resolver."""
    return FacebookClient(
        credential_resolver=mock_resolver,
        customer_id="CUST-123",
    )


class TestFacebookClientPostToPage:
    """Test cases for post_to_page method."""
    
    @pytest.mark.asyncio
    async def test_post_text_only(self, facebook_client, mock_resolver):
        """Test successful text-only post."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "987654321_123456"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await facebook_client.post_to_page(
                credential_ref="CRED-test",
                page_id="987654321",
                text="Test Facebook post",
            )
        
        assert result.success is True
        assert result.platform == "facebook"
        assert result.post_id == "987654321_123456"
        assert "facebook.com" in result.post_url
        assert facebook_client.calls_made == 1
    
    @pytest.mark.asyncio
    async def test_post_with_image(self, facebook_client, mock_resolver):
        """Test post with image."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "987654321_789012", "post_id": "987654321_789012"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await facebook_client.post_to_page(
                credential_ref="CRED-test",
                page_id="987654321",
                text="Post with photo",
                image_url="https://example.com/photo.jpg",
            )
        
        assert result.success is True
        assert result.post_id == "987654321_789012"
    
    @pytest.mark.asyncio
    async def test_post_with_link(self, facebook_client, mock_resolver):
        """Test post with link."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "987654321_345678"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await facebook_client.post_to_page(
                credential_ref="CRED-test",
                page_id="987654321",
                text="Check out this link",
                link="https://waooaw.com",
            )
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_post_text_uses_page_id_from_credentials(self, facebook_client, mock_resolver):
        """Test that post_text extracts page_id from credentials."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "987654321_111222"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await facebook_client.post_text(
                credential_ref="CRED-test",
                text="Test using post_text",
            )
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_post_missing_page_id(self, facebook_client, mock_resolver):
        """Test error when Facebook Page ID is missing."""
        # Mock resolver to return credentials without posting_identity
        mock_resolver.resolve = AsyncMock(return_value=ResolvedSocialCredentials(
            credential_ref="CRED-test",
            customer_id="CUST-123",
            platform="facebook",
            posting_identity=None,  # Missing
            access_token="mock_token",
            refresh_token=None,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        ))
        
        with pytest.raises(SocialPlatformError) as exc_info:
            await facebook_client.post_text(
                credential_ref="CRED-test",
                text="Test",
            )
        
        assert exc_info.value.error_code == "MISSING_PAGE_ID"


class TestFacebookClientTokenRefresh:
    """Test cases for token refresh."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, facebook_client, mock_resolver):
        """Test successful token refresh."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_long_lived_page_token",
            "token_type": "bearer",
            "expires_in": 5184000,  # 60 days
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            new_token = await facebook_client.refresh_token("CRED-test")
        
        assert new_token == "new_long_lived_page_token"
        
        # Verify token was updated in CP Backend
        mock_resolver.update_access_token.assert_called_once_with(
            customer_id="CUST-123",
            credential_ref="CRED-test",
            new_access_token="new_long_lived_page_token",
        )
    
    @pytest.mark.asyncio
    async def test_auto_refresh_on_401(self, facebook_client, mock_resolver):
        """Test automatic token refresh on 401 Unauthorized."""
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        mock_response_401.json.return_value = {
            "error": {
                "message": "Invalid OAuth 2.0 Access Token",
                "type": "OAuthException",
                "code": 190
            }
        }
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"id": "page_post_after_refresh"}
        
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            "access_token": "refreshed_page_token",
            "expires_in": 5184000,
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            
            # First post: 401, then GET for refresh (success), then post (success)
            mock_client.post = AsyncMock(side_effect=[mock_response_401, mock_response_200])
            mock_client.get = AsyncMock(return_value=mock_token_response)
            mock_client_class.return_value = mock_client
            
            result = await facebook_client.post_to_page(
                credential_ref="CRED-test",
                page_id="987654321",
                text="Test post",
            )
        
        assert result.success is True
        assert result.post_id == "page_post_after_refresh"
        
        # Verify token was refreshed and updated
        mock_resolver.update_access_token.assert_called_once()


class TestFacebookClientValidateCredentials:
    """Test cases for credential validation."""
    
    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, facebook_client, mock_resolver):
        """Test successful credential validation."""
        mock_page_response = MagicMock()
        mock_page_response.status_code = 200
        mock_page_response.json.return_value = {
            "id": "987654321",
            "name": "Test Page",
            "access_token": "page_token"
        }
        
        mock_perms_response = MagicMock()
        mock_perms_response.status_code = 200
        mock_perms_response.json.return_value = {
            "data": [
                {"permission": "pages_manage_posts", "status": "granted"},
                {"permission": "pages_read_engagement", "status": "granted"}
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[mock_page_response, mock_perms_response])
            mock_client_class.return_value = mock_client
            
            is_valid = await facebook_client.validate_credentials("CRED-test")
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_credentials_no_page(self, facebook_client, mock_resolver):
        """Test validation failure when no page found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Empty response = no page
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await facebook_client.validate_credentials("CRED-test")
        
        assert exc_info.value.error_code == "NO_PAGE"
        assert exc_info.value.is_transient is False


class TestFacebookClientErrorClassification:
    """Test cases for error classification."""
    
    def test_classify_rate_limit(self, facebook_client):
        """Test rate limit error classification."""
        error_body = {
            "error": {
                "message": "Application request limit reached",
                "type": "OAuthException",
                "code": 4
            }
        }
        
        error = facebook_client._classify_error(429, error_body)
        
        assert error.error_code == "RATE_LIMIT"
        assert error.is_transient is True
        assert error.retry_after == 3600
    
    def test_classify_auth_error(self, facebook_client):
        """Test authentication error classification."""
        error_body = {
            "error": {
                "message": "Invalid OAuth 2.0 Access Token",
                "type": "OAuthException",
                "code": 190
            }
        }
        
        error = facebook_client._classify_error(401, error_body)
        
        assert error.error_code == "AUTH_FAILED"
        assert error.is_transient is False
    
    def test_classify_permission_error(self, facebook_client):
        """Test permission denied error classification."""
        error_body = {
            "error": {
                "message": "Permissions error",
                "type": "OAuthException",
                "code": 200
            }
        }
        
        error = facebook_client._classify_error(403, error_body)
        
        assert error.error_code == "PERMISSION_DENIED"
        assert error.is_transient is False
    
    def test_classify_server_error(self, facebook_client):
        """Test server error classification."""
        error_body = {
            "error": {
                "message": "Internal server error",
                "type": "FacebookApiException",
                "code": 1
            }
        }
        
        error = facebook_client._classify_error(500, error_body)
        
        assert error.error_code == "SERVER_ERROR"
        assert error.is_transient is True
    
    def test_classify_duplicate_post(self, facebook_client):
        """Test duplicate post error classification."""
        error_body = {
            "error": {
                "message": "Duplicate status message",
                "type": "FacebookApiException",
                "code": 506
            }
        }
        
        error = facebook_client._classify_error(400, error_body)
        
        assert error.error_code == "DUPLICATE_POST"
        assert error.is_transient is False
    
    def test_classify_invalid_parameter(self, facebook_client):
        """Test invalid parameter error classification."""
        error_body = {
            "error": {
                "message": "Invalid parameter",
                "type": "FacebookApiException",
                "code": 100
            }
        }
        
        error = facebook_client._classify_error(400, error_body)
        
        assert error.error_code == "INVALID_PARAMETER"
        assert error.is_transient is False


class TestFacebookClientRetryLogic:
    """Test cases for retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, facebook_client, mock_resolver):
        """Test retry on transient errors (e.g., rate limit)."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.json.return_value = {
            "error": {"message": "Rate limit exceeded", "code": 4}
        }
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"id": "post_after_retry"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            
            # Return 429 twice, then success
            mock_client.post = AsyncMock(
                side_effect=[mock_response_429, mock_response_429, mock_response_200]
            )
            mock_client_class.return_value = mock_client
            
            result = await facebook_client.post_to_page(
                credential_ref="CRED-test",
                page_id="987654321",
                text="Test with retries",
            )
        
        assert result.success is True
        assert result.post_id == "post_after_retry"
        
        # Verify retry happened
        assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, facebook_client, mock_resolver):
        """Test no retry on permanent errors (e.g., duplicate post)."""
        mock_response_400 = MagicMock()
        mock_response_400.status_code = 400
        mock_response_400.json.return_value = {
            "error": {"message": "Duplicate status message", "code": 506}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_400)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await facebook_client.post_to_page(
                    credential_ref="CRED-test",
                    page_id="987654321",
                    text="Duplicate",
                )
        
        # Should fail immediately without retries
        assert mock_client.post.call_count == 1
        assert exc_info.value.is_transient is False


class TestFacebookClientCallTracking:
    """Test cases for API call tracking."""
    
    @pytest.mark.asyncio
    async def test_call_tracking_on_post(self, facebook_client, mock_resolver):
        """Test API calls are tracked after successful post."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "post123"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            initial_calls = facebook_client.calls_made
            await facebook_client.post_to_page(
                credential_ref="CRED-test",
                page_id="987654321",
                text="Test",
            )
        
        # Post should make 1 API call
        assert facebook_client.calls_made == initial_calls + 1
