"""Integration tests for LinkedIn Business API client.

Tests real LinkedIn integration with:
- LinkedIn UGC API authentication
- Organization page posting (text, image, article/link)
- Token validation
- Permission validation
- Error handling and retry logic
- Rate limit handling
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from integrations.social.linkedin_client import LinkedInClient
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
        platform="linkedin",
        posting_identity="LI_ORG:12345678",  # LinkedIn Organization ID
        access_token="mock_linkedin_access_token",
        refresh_token=None,  # LinkedIn uses long-lived tokens
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    ))
    resolver.update_access_token = AsyncMock()
    return resolver


@pytest.fixture
def linkedin_client(mock_resolver):
    """Create LinkedIn client with mock resolver."""
    return LinkedInClient(
        credential_resolver=mock_resolver,
        customer_id="CUST-123",
    )


class TestLinkedInClientPostToOrganization:
    """Test cases for post_to_organization method."""
    
    @pytest.mark.asyncio
    async def test_post_text_only(self, linkedin_client, mock_resolver):
        """Test successful text-only post."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "urn:li:ugcPost:1234567890",
            "lifecycleState": "PUBLISHED"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await linkedin_client.post_to_organization(
                credential_ref="CRED-test",
                organization_id="12345678",
                text="Test LinkedIn post",
            )
        
        assert result.success is True
        assert result.platform == "linkedin"
        assert result.post_id == "1234567890"
        assert "linkedin.com" in result.post_url
        assert linkedin_client.calls_made == 1
    
    @pytest.mark.asyncio
    async def test_post_with_image(self, linkedin_client, mock_resolver):
        """Test post with image."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "urn:li:ugcPost:9876543210"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await linkedin_client.post_to_organization(
                credential_ref="CRED-test",
                organization_id="12345678",
                text="Post with image",
                image_url="https://example.com/image.jpg",
            )
        
        assert result.success is True
        assert result.post_id == "9876543210"
        
        # Verify API call includes image
        call_args = mock_client.request.call_args
        json_body = call_args.kwargs.get("json")
        assert json_body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] == "IMAGE"
        assert len(json_body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"]) == 1
    
    @pytest.mark.asyncio
    async def test_post_with_link(self, linkedin_client, mock_resolver):
        """Test post with article/link."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "urn:li:ugcPost:5555555555"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await linkedin_client.post_to_organization(
                credential_ref="CRED-test",
                organization_id="12345678",
                text="Check out this article",
                link_url="https://waooaw.com/blog/post",
                link_title="WAOOAW Blog Post",
            )
        
        assert result.success is True
        
        # Verify API call includes article
        call_args = mock_client.request.call_args
        json_body = call_args.kwargs.get("json")
        assert json_body["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] == "ARTICLE"
    
    @pytest.mark.asyncio
    async def test_post_text_uses_org_id_from_credentials(self, linkedin_client, mock_resolver):
        """Test that post_text extracts organization_id from credentials."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "urn:li:ugcPost:1111111111"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await linkedin_client.post_text(
                credential_ref="CRED-test",
                text="Test using post_text",
            )
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_post_missing_org_id(self, linkedin_client, mock_resolver):
        """Test error when LinkedIn organization ID is missing."""
        # Mock resolver to return credentials without posting_identity
        mock_resolver.resolve = AsyncMock(return_value=ResolvedSocialCredentials(
            credential_ref="CRED-test",
            customer_id="CUST-123",
            platform="linkedin",
            posting_identity=None,  # Missing
            access_token="mock_token",
            refresh_token=None,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        ))
        
        with pytest.raises(SocialPlatformError) as exc_info:
            await linkedin_client.post_text(
                credential_ref="CRED-test",
                text="Test",
            )
        
        assert exc_info.value.error_code == "MISSING_ORG_ID"


class TestLinkedInClientTokenRefresh:
    """Test cases for token validation (LinkedIn doesn't have true refresh)."""
    
    @pytest.mark.asyncio
    async def test_token_validation_success(self, linkedin_client, mock_resolver):
        """Test successful token validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "abcd1234",
            "firstName": {"localized": {"en_US": "Test"}},
            "lastName": {"localized": {"en_US": "User"}}
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            token = await linkedin_client.refresh_token("CRED-test")
        
        assert token == "mock_linkedin_access_token"
    
    @pytest.mark.asyncio
    async def test_token_expired(self, linkedin_client, mock_resolver):
        """Test error when token is expired."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "message": "Expired access token",
            "serviceErrorCode": 65601
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await linkedin_client.refresh_token("CRED-test")
        
        assert exc_info.value.error_code == "TOKEN_EXPIRED"
        assert exc_info.value.is_transient is False
    
    @pytest.mark.asyncio
    async def test_auto_refresh_on_401(self, linkedin_client, mock_resolver):
        """Test automatic token refresh on 401 Unauthorized."""
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        mock_response_401.json.return_value = {
            "message": "Expired access token",
            "serviceErrorCode": 65601
        }
        
        mock_response_200_post = MagicMock()
        mock_response_200_post.status_code = 201
        mock_response_200_post.json.return_value = {
            "id": "urn:li:ugcPost:after_refresh"
        }
        
        mock_response_200_validate = MagicMock()
        mock_response_200_validate.status_code = 200
        mock_response_200_validate.json.return_value = {"id": "user123"}
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            
            # First post: 401, then GET for validation (success), then post (success)
            mock_client.request = AsyncMock(side_effect=[mock_response_401, mock_response_200_post])
            mock_client.get = AsyncMock(return_value=mock_response_200_validate)
            mock_client_class.return_value = mock_client
            
            result = await linkedin_client.post_to_organization(
                credential_ref="CRED-test",
                organization_id="12345678",
                text="Test post",
            )
        
        assert result.success is True
        assert result.post_id == "after_refresh"


class TestLinkedInClientValidateCredentials:
    """Test cases for credential validation."""
    
    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, linkedin_client, mock_resolver):
        """Test successful credential validation."""
        mock_org_response = MagicMock()
        mock_org_response.status_code = 200
        mock_org_response.json.return_value = {
            "id": 12345678,
            "name": {"localized": {"en_US": "Test Organization"}}
        }
        
        mock_role_response = MagicMock()
        mock_role_response.status_code = 200
        mock_role_response.json.return_value = {
            "elements": [
                {"organization": "urn:li:organization:12345678", "role": "ADMINISTRATOR"}
            ]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[mock_org_response, mock_role_response])
            mock_client_class.return_value = mock_client
            
            is_valid = await linkedin_client.validate_credentials("CRED-test")
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_credentials_org_not_found(self, linkedin_client, mock_resolver):
        """Test validation failure when organization not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "message": "Organization not found",
            "serviceErrorCode": 100
        }
        mock_response.text = '{"message": "Organization not found"}'
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await linkedin_client.validate_credentials("CRED-test")
        
        assert exc_info.value.error_code == "ORG_NOT_FOUND"
        assert exc_info.value.is_transient is False
    
    @pytest.mark.asyncio
    async def test_validate_credentials_no_admin_access(self, linkedin_client, mock_resolver):
        """Test validation failure when user doesn't have admin access."""
        mock_org_response = MagicMock()
        mock_org_response.status_code = 200
        mock_org_response.json.return_value = {"id": 12345678}
        
        mock_role_response = MagicMock()
        mock_role_response.status_code = 403
        mock_role_response.json.return_value = {
            "message": "Insufficient permissions",
            "serviceErrorCode": 100
        }
        mock_role_response.text = '{"message": "Insufficient permissions"}'
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[mock_org_response, mock_role_response])
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await linkedin_client.validate_credentials("CRED-test")
        
        assert exc_info.value.error_code == "PERMISSION_DENIED"


class TestLinkedInClientErrorClassification:
    """Test cases for error classification."""
    
    def test_classify_rate_limit(self, linkedin_client):
        """Test rate limit error classification."""
        error_body = {
            "message": "Application request limit reached",
            "serviceErrorCode": 100
        }
        
        error = linkedin_client._classify_error(429, error_body)
        
        assert error.error_code == "RATE_LIMIT"
        assert error.is_transient is True
        assert error.retry_after == 3600
    
    def test_classify_auth_error(self, linkedin_client):
        """Test authentication error classification."""
        error_body = {
            "message": "Invalid access token",
            "serviceErrorCode": 65601
        }
        
        error = linkedin_client._classify_error(401, error_body)
        
        assert error.error_code == "AUTH_FAILED"
        assert error.is_transient is False
    
    def test_classify_permission_error(self, linkedin_client):
        """Test permission denied error classification."""
        error_body = {
            "message": "Insufficient permissions for organization",
            "serviceErrorCode": 100
        }
        
        error = linkedin_client._classify_error(403, error_body)
        
        assert error.error_code == "PERMISSION_DENIED"
        assert error.is_transient is False
    
    def test_classify_server_error(self, linkedin_client):
        """Test server error classification."""
        error_body = {
            "message": "Internal server error",
            "serviceErrorCode": 0
        }
        
        error = linkedin_client._classify_error(500, error_body)
        
        assert error.error_code == "SERVER_ERROR"
        assert error.is_transient is True
    
    def test_classify_invalid_parameter(self, linkedin_client):
        """Test invalid parameter error classification."""
        error_body = {
            "message": "Missing required field: text",
            "serviceErrorCode": 100
        }
        
        error = linkedin_client._classify_error(400, error_body)
        
        assert error.error_code == "INVALID_PARAMETER"
        assert error.is_transient is False


class TestLinkedInClientRetryLogic:
    """Test cases for retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, linkedin_client, mock_resolver):
        """Test retry on transient errors (e.g., rate limit)."""
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.json.return_value = {
            "message": "Rate limit exceeded",
            "serviceErrorCode": 100
        }
        
        mock_response_201 = MagicMock()
        mock_response_201.status_code = 201
        mock_response_201.json.return_value = {
            "id": "urn:li:ugcPost:after_retry"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            
            # Return 429 twice, then success
            mock_client.request = AsyncMock(
                side_effect=[mock_response_429, mock_response_429, mock_response_201]
            )
            mock_client_class.return_value = mock_client
            
            result = await linkedin_client.post_to_organization(
                credential_ref="CRED-test",
                organization_id="12345678",
                text="Test with retries",
            )
        
        assert result.success is True
        assert result.post_id == "after_retry"
        
        # Verify retry happened
        assert mock_client.request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, linkedin_client, mock_resolver):
        """Test no retry on permanent errors (e.g., invalid parameter)."""
        mock_response_400 = MagicMock()
        mock_response_400.status_code = 400
        mock_response_400.json.return_value = {
            "message": "Missing required field",
            "serviceErrorCode": 100
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_400)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await linkedin_client.post_to_organization(
                    credential_ref="CRED-test",
                    organization_id="12345678",
                    text="Invalid",
                )
        
        # Should fail immediately without retries
        assert mock_client.request.call_count == 1
        assert exc_info.value.is_transient is False


class TestLinkedInClientCallTracking:
    """Test cases for API call tracking."""
    
    @pytest.mark.asyncio
    async def test_call_tracking_on_post(self, linkedin_client, mock_resolver):
        """Test API calls are tracked after successful post."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "urn:li:ugcPost:123"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            initial_calls = linkedin_client.calls_made
            await linkedin_client.post_to_organization(
                credential_ref="CRED-test",
                organization_id="12345678",
                text="Test",
            )
        
        # Post should make 1 API call
        assert linkedin_client.calls_made == initial_calls + 1
