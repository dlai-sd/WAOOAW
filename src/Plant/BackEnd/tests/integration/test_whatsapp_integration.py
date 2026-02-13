"""Integration tests for WhatsApp Business API client.

Tests real WhatsApp Business integration with:
- Cloud API authentication
- Text message sending
- Template message sending
- Media message sending
- Message status tracking
- Error handling and retry logic
- Rate limit handling
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from integrations.social.whatsapp_client import WhatsAppClient
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
        platform="whatsapp",
        posting_identity="1234567890",  # phone_number_id
        access_token="mock_access_token",
        refresh_token=None,  # WhatsApp doesn't use refresh tokens
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    ))
    return resolver


@pytest.fixture
def whatsapp_client(mock_resolver):
    """Create WhatsApp client with mock resolver."""
    return WhatsAppClient(
        credential_resolver=mock_resolver,
        customer_id="CUST-123",
    )


class TestWhatsAppClientSendText:
    """Test cases for post_text method (text message sending)."""
    
    @pytest.mark.asyncio
    async def test_send_text_success(self, whatsapp_client, mock_resolver):
        """Test successful text message sending."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+1234567890", "wa_id": "1234567890"}],
            "messages": [{"id": "wamid.abc123"}]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await whatsapp_client.post_text(
                credential_ref="CRED-test",
                text="Hello from WAOOAW!",
            )
        
        assert result.success is True
        assert result.platform == "whatsapp"
        assert result.post_id == "wamid.abc123"
        assert "whatsapp://send" in result.post_url
        
        # Verify resolver was called
        mock_resolver.resolve.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_text_too_long(self, whatsapp_client):
        """Test text length validation (4096 char limit)."""
        with pytest.raises(SocialPlatformError) as exc_info:
            await whatsapp_client.post_text(
                credential_ref="CRED-test",
                text="A" * 4097,  # Exceeds 4096 char limit
            )
        
        assert exc_info.value.error_code == "TEXT_TOO_LONG"
        assert exc_info.value.is_transient is False
    
    @pytest.mark.asyncio
    async def test_send_text_with_image(self, whatsapp_client, mock_resolver):
        """Test sending text with image."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+1234567890", "wa_id": "1234567890"}],
            "messages": [{"id": "wamid.image123"}]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await whatsapp_client.post_text(
                credential_ref="CRED-test",
                text="Check out this image!",
                image_url="https://example.com/image.jpg",
            )
        
        assert result.success is True
        assert result.post_id == "wamid.image123"
    
    @pytest.mark.asyncio
    async def test_send_text_credential_resolution_error(self, whatsapp_client, mock_resolver):
        """Test credential resolution failure."""
        mock_resolver.resolve = AsyncMock(
            side_effect=CredentialResolutionError("Credential not found")
        )
        
        with pytest.raises(SocialPlatformError) as exc_info:
            await whatsapp_client.post_text(
                credential_ref="CRED-missing",
                text="Test message",
            )
        
        assert "Credential resolution failed" in exc_info.value.message
        assert exc_info.value.is_transient is False


class TestWhatsAppClientTemplateMessage:
    """Test cases for template message sending."""
    
    @pytest.mark.asyncio
    async def test_send_template_success(self, whatsapp_client, mock_resolver):
        """Test successful template message sending."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+1234567890", "wa_id": "1234567890"}],
            "messages": [{"id": "wamid.template123"}]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await whatsapp_client.send_template_message(
                credential_ref="CRED-test",
                template_name="welcome_message",
                template_params=["John", "WAOOAW"],
                language_code="en",
            )
        
        assert result.success is True
        assert result.platform == "whatsapp"
        assert result.post_id == "wamid.template123"
    
    @pytest.mark.asyncio
    async def test_send_template_missing_credentials(self, whatsapp_client, mock_resolver):
        """Test template send with missing phone_number_id."""
        # Mock resolver returning incomplete credentials
        mock_resolver.resolve = AsyncMock(return_value=ResolvedSocialCredentials(
            credential_ref="CRED-test",
            customer_id="CUST-123",
            platform="whatsapp",
            posting_identity=None,  # Missing phone_number_id
            access_token="mock_token",
            refresh_token=None,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        ))
        
        with pytest.raises(SocialPlatformError) as exc_info:
            await whatsapp_client.send_template_message(
                credential_ref="CRED-test",
                template_name="test_template",
                template_params=["test"],
            )
        
        assert exc_info.value.error_code == "MISSING_CREDENTIALS"


class TestWhatsAppClientMessageStatus:
    """Test cases for message status tracking."""
    
    @pytest.mark.asyncio
    async def test_get_message_status(self, whatsapp_client, mock_resolver):
        """Test message status retrieval."""
        # WhatsApp uses webhooks, so this returns a placeholder
        status = await whatsapp_client.get_message_status(
            credential_ref="CRED-test",
            message_id="wamid.abc123",
        )
        
        assert status["message_id"] == "wamid.abc123"
        assert "webhook" in status["note"].lower()


class TestWhatsAppClientValidateCredentials:
    """Test cases for credential validation."""
    
    @pytest.mark.asyncio
    async def test_validate_credentials_success(self, whatsapp_client, mock_resolver):
        """Test successful credential validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "1234567890",
            "display_phone_number": "+1 (234) 567-8900",
            "verified_name": "WAOOAW Business"
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            is_valid = await whatsapp_client.validate_credentials("CRED-test")
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_credentials_no_phone(self, whatsapp_client, mock_resolver):
        """Test validation failure when phone number not found."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}  # Empty response = no phone found
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await whatsapp_client.validate_credentials("CRED-test")
        
        assert exc_info.value.error_code == "PHONE_NOT_FOUND"
        assert exc_info.value.is_transient is False
    
    @pytest.mark.asyncio
    async def test_validate_credentials_missing_phone_id(self, whatsapp_client, mock_resolver):
        """Test validation with missing phone_number_id."""
        # Mock resolver returning credentials without phone_number_id
        mock_resolver.resolve = AsyncMock(return_value=ResolvedSocialCredentials(
            credential_ref="CRED-test",
            customer_id="CUST-123",
            platform="whatsapp",
            posting_identity=None,  # Missing
            access_token="mock_token",
            refresh_token=None,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        ))
        
        with pytest.raises(SocialPlatformError) as exc_info:
            await whatsapp_client.validate_credentials("CRED-test")
        
        assert exc_info.value.error_code == "MISSING_PHONE_NUMBER_ID"


class TestWhatsAppClientTokenRefresh:
    """Test cases for token refresh (WhatsApp uses long-lived tokens)."""
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, whatsapp_client, mock_resolver):
        """Test token refresh (returns same token for WhatsApp)."""
        token = await whatsapp_client.refresh_token("CRED-test")
        
        # WhatsApp tokens don't expire, so should return existing token
        assert token == "mock_access_token"


class TestWhatsAppClientErrorClassification:
    """Test cases for error classification."""
    
    def test_classify_rate_limit(self, whatsapp_client):
        """Test rate limit error classification."""
        error_body = {
            "error": {
                "message": "Rate limit exceeded",
                "code": 4,
                "type": "OAuthException"
            }
        }
        
        error = whatsapp_client._classify_error(429, error_body)
        
        assert error.error_code == "RATE_LIMIT"
        assert error.is_transient is True
        assert error.retry_after == 60
    
    def test_classify_auth_error(self, whatsapp_client):
        """Test authentication error classification."""
        error_body = {
            "error": {
                "message": "Invalid OAuth access token",
                "code": 190,
                "type": "OAuthException"
            }
        }
        
        error = whatsapp_client._classify_error(401, error_body)
        
        assert error.error_code == "AUTH_FAILED"
        assert error.is_transient is False
    
    def test_classify_invalid_phone(self, whatsapp_client):
        """Test invalid phone number error classification."""
        error_body = {
            "error": {
                "message": "Invalid phone number format",
                "code": 100,
                "type": "InvalidParameterException"
            }
        }
        
        error = whatsapp_client._classify_error(400, error_body)
        
        assert error.error_code == "INVALID_PHONE"
        assert error.is_transient is False
    
    def test_classify_template_error(self, whatsapp_client):
        """Test template error classification."""
        error_body = {
            "error": {
                "message": "Template does not exist",
                "code": 132,
                "type": "MessageTemplateNotFound"
            }
        }
        
        error = whatsapp_client._classify_error(400, error_body)
        
        assert error.error_code == "TEMPLATE_ERROR"
        assert error.is_transient is False
    
    def test_classify_server_error(self, whatsapp_client):
        """Test server error classification."""
        error_body = {
            "error": {
                "message": "Internal server error",
                "code": 1,
                "type": "ServerError"
            }
        }
        
        error = whatsapp_client._classify_error(500, error_body)
        
        assert error.error_code == "SERVER_ERROR"
        assert error.is_transient is True


class TestWhatsAppClientRetryLogic:
    """Test cases for retry logic with exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, whatsapp_client, mock_resolver):
        """Test retry on transient errors (e.g., 429 rate limit)."""
        # First two calls fail with 429, third succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.json.return_value = {
            "error": {"message": "Rate limit exceeded", "code": 4}
        }
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+1234567890", "wa_id": "1234567890"}],
            "messages": [{"id": "wamid.retry123"}]
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
            
            result = await whatsapp_client.post_text(
                credential_ref="CRED-test",
                text="Test message with retries",
            )
        
        assert result.success is True
        assert result.post_id == "wamid.retry123"
        
        # Verify retry happened (3 total calls)
        assert mock_client.post.call_count == 3
    
    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, whatsapp_client, mock_resolver):
        """Test no retry on permanent errors (e.g., 400 bad request)."""
        mock_response_400 = MagicMock()
        mock_response_400.status_code = 400
        mock_response_400.json.return_value = {
            "error": {
                "message": "Invalid phone number",
                "code": 100,
                "type": "InvalidParameterException"
            }
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response_400)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(SocialPlatformError) as exc_info:
                await whatsapp_client.post_text(
                    credential_ref="CRED-test",
                    text="Test message",
                )
        
        # Should fail immediately without retries
        assert mock_client.post.call_count == 1
        assert exc_info.value.is_transient is False


class TestWhatsAppClientMediaMessages:
    """Test cases for media message sending (images, documents, etc.)."""
    
    @pytest.mark.asyncio
    async def test_send_image_with_caption(self, whatsapp_client, mock_resolver):
        """Test sending image with caption."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+1234567890", "wa_id": "1234567890"}],
            "messages": [{"id": "wamid.media456"}]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            result = await whatsapp_client.post_text(
                credential_ref="CRED-test",
                text="Product showcase",
                image_url="https://example.com/product.jpg",
            )
        
        assert result.success is True
        assert result.post_id == "wamid.media456"


class TestWhatsAppClientIntegration:
    """End-to-end integration test scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_message_lifecycle(self, whatsapp_client, mock_resolver):
        """Test complete message send and status check flow."""
        # 1. Send message
        mock_send_response = MagicMock()
        mock_send_response.status_code = 200
        mock_send_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+1234567890", "wa_id": "1234567890"}],
            "messages": [{"id": "wamid.lifecycle123"}]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_send_response)
            mock_client_class.return_value = mock_client
            
            send_result = await whatsapp_client.post_text(
                credential_ref="CRED-test",
                text="Lifecycle test message",
            )
        
        assert send_result.success is True
        message_id = send_result.post_id
        
        # 2. Check message status
        status = await whatsapp_client.get_message_status(
            credential_ref="CRED-test",
            message_id=message_id,
        )
        
        assert status["message_id"] == message_id
    
    @pytest.mark.asyncio
    async def test_credential_validation_before_send(self, whatsapp_client, mock_resolver):
        """Test validating credentials before sending message."""
        # 1. Validate credentials
        mock_validate_response = MagicMock()
        mock_validate_response.status_code = 200
        mock_validate_response.json.return_value = {
            "id": "1234567890",
            "display_phone_number": "+1 (234) 567-8900",
            "verified_name": "WAOOAW Business"
        }
        
        # 2. Send message
        mock_send_response = MagicMock()
        mock_send_response.status_code = 200
        mock_send_response.json.return_value = {
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+1234567890", "wa_id": "1234567890"}],
            "messages": [{"id": "wamid.validated123"}]
        }
        
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_validate_response)
            mock_client.post = AsyncMock(return_value=mock_send_response)
            mock_client_class.return_value = mock_client
            
            # Validate first
            is_valid = await whatsapp_client.validate_credentials("CRED-test")
            assert is_valid is True
            
            # Then send
            result = await whatsapp_client.post_text(
                credential_ref="CRED-test",
                text="Message after validation",
            )
            assert result.success is True
