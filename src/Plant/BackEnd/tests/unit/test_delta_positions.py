"""Tests for Delta Exchange position management service."""

import httpx
import pytest

from integrations.delta_exchange.client import DeltaCredentials, DeltaExchangeClient
from integrations.delta_exchange.positions import DeltaPositionService, DeltaPosition


class TestDeltaPositionService:
    """Test cases for position closing with safety checks."""
    
    @pytest.mark.asyncio
    async def test_close_full_position_success(self):
        """Test successful closing of entire position."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "order_id": "CLOSE-12345",
                "quantity_closed": 5.0,
                "remaining_position": 0.0,
                "coin": "BTC"
            })
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport
        )
        
        service = DeltaPositionService(client=client)
        
        result = await service.close_position(
            coin="BTC",
            correlation_id="corr-1"
        )
        
        assert result.success is True
        assert result.coin == "BTC"
        assert result.quantity_closed == 5.0
        assert result.remaining_position == 0.0
        assert result.order_id == "CLOSE-12345"
        assert "successfully" in result.message
    
    @pytest.mark.asyncio
    async def test_close_partial_position_success(self):
        """Test successful closing of partial position."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "id": "CLOSE-67890",
                "quantity": 3.0,
                "remaining_position": 2.0
            })
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport
        )
        
        service = DeltaPositionService(client=client)
        
        result = await service.close_position(
            coin="ETH",
            quantity=3.0,
            correlation_id="corr-2"
        )
        
        assert result.success is True
        assert result.coin == "ETH"
        assert result.quantity_closed == 3.0
        assert result.remaining_position == 2.0
        assert result.order_id == "CLOSE-67890"
    
    @pytest.mark.asyncio
    async def test_close_position_not_found(self):
        """Test error when trying to close non-existent position."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={
                "error": "Position not found"
            })
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport,
            max_retries=0
        )
        
        service = DeltaPositionService(client=client)
        
        result = await service.close_position(
            coin="SOL",
            correlation_id="corr-3"
        )
        
        assert result.success is False
        assert result.error_code == "POSITION_NOT_FOUND"
        assert "No open position found" in result.message
        assert "SOL" in result.message
        assert result.quantity_closed == 0.0
    
    @pytest.mark.asyncio
    async def test_close_negative_quantity_rejected(self):
        """Test that negative quantity is rejected before API call."""
        # API should never be called
        call_count = {"count": 0}
        
        async def handler(request: httpx.Request) -> httpx.Response:
            call_count["count"] += 1
            return httpx.Response(200, json={"ok": True})
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport
        )
        
        service = DeltaPositionService(client=client)
        
        result = await service.close_position(
            coin="BTC",
            quantity=-5.0
        )
        
        assert result.success is False
        assert result.error_code == "INVALID_QUANTITY"
        assert "must be > 0" in result.message
        assert call_count["count"] == 0  # API was never called
    
    @pytest.mark.asyncio
    async def test_close_zero_quantity_rejected(self):
        """Test that zero quantity is rejected."""
        service = DeltaPositionService(
            client=DeltaExchangeClient(
                base_url="https://test.delta.exchange",
                credentials=DeltaCredentials(api_key="key", api_secret="secret")
            )
        )
        
        result = await service.close_position(
            coin="ETH",
            quantity=0.0
        )
        
        assert result.success is False
        assert result.error_code == "INVALID_QUANTITY"
    
    @pytest.mark.asyncio
    async def test_close_position_authentication_error(self):
        """Test handling of authentication errors."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "Invalid API key"})
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="invalid", api_secret="invalid"),
            transport=transport,
            max_retries=0
        )
        
        service = DeltaPositionService(client=client)
        
        result = await service.close_position(
            coin="BTC",
            correlation_id="corr-4"
        )
        
        assert result.success is False
        assert result.error_code == "AUTHENTICATION_ERROR"
    
    @pytest.mark.asyncio
    async def test_close_position_permission_denied(self):
        """Test handling of permission denied errors (403)."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, json={"error": "Insufficient permissions"})
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport,
            max_retries=0
        )
        
        service = DeltaPositionService(client=client)
        
        result = await service.close_position(
            coin="BTC"
        )
        
        assert result.success is False
        assert result.error_code == "PERMISSION_DENIED"
    
    @pytest.mark.asyncio
    async def test_close_position_invalid_request(self):
        """Test handling of invalid request errors (400)."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(400, json={"error": "Invalid parameters"})
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport,
            max_retries=0
        )
        
        service = DeltaPositionService(client=client)
        
        result = await service.close_position(
            coin="BTC",
            quantity=999999.0  # Perhaps too large
        )
        
        assert result.success is False
        assert result.error_code == "INVALID_REQUEST"
    
    @pytest.mark.asyncio
    async def test_close_position_with_correlation_id(self):
        """Test that correlation_id is passed through to client."""
        captured = {}
        
        async def handler(request: httpx.Request) -> httpx.Response:
            captured["headers"] = dict(request.headers)
            return httpx.Response(200, json={"quantity_closed": 1.0})
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport
        )
        
        service = DeltaPositionService(client=client)
        
        result = await service.close_position(
            coin="BTC",
            correlation_id="test-corr-123"
        )
        
        assert result.success is True
        assert captured["headers"].get("x-correlation-id") == "test-corr-123"
    
    @pytest.mark.asyncio
    async def test_get_open_positions_stub(self):
        """Test get_open_positions returns empty list (stub implementation)."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        service = DeltaPositionService(client=client)
        
        positions = await service.get_open_positions(coin="BTC")
        
        # Stub returns empty list for now
        assert positions == []
        assert isinstance(positions, list)
