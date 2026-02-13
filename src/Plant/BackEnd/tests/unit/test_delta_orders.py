"""Tests for Delta Exchange order service."""

import httpx
import pytest

from integrations.delta_exchange.client import DeltaCredentials, DeltaExchangeClient
from integrations.delta_exchange.orders import DeltaOrderService
from integrations.delta_exchange.risk_engine import RiskEngine, RiskLimits


class TestDeltaOrderService:
    """Test cases for order placement with risk validation."""
    
    @pytest.mark.asyncio
    async def test_place_market_order_success(self):
        """Test successful market order placement."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "order_id": "ORD-12345",
                "status": "pending",
                "symbol": "BTC",
                "side": "buy",
                "quantity": 1.0
            })
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport
        )
        
        service = DeltaOrderService(client=client)
        limits = RiskLimits(
            allowed_coins=["BTC", "ETH"],
            max_units_per_order=10.0,
            max_notional_inr=1000000.0
        )
        
        result = await service.place_order(
            coin="BTC",
            side="buy",
            quantity=1.0,
            risk_limits=limits,
            order_type="market",
            estimated_price=50000.0,  # For risk validation
            correlation_id="corr-1"
        )
        
        assert result.success is True
        assert result.order_id == "ORD-12345"
        assert result.status == "pending"
        assert result.risk_check.approved is True
    
    @pytest.mark.asyncio
    async def test_place_limit_order_success(self):
        """Test successful limit order placement."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "id": "ORD-67890",
                "status": "open"
            })
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport
        )
        
        service = DeltaOrderService(client=client)
        limits = RiskLimits(allowed_coins=["ETH"])
        
        result = await service.place_order(
            coin="ETH",
            side="sell",
            quantity=5.0,
            risk_limits=limits,
            order_type="limit",
            limit_price=4000.0,
            correlation_id="corr-2"
        )
        
        assert result.success is True
        assert result.order_id == "ORD-67890"
        assert result.status == "open"
    
    @pytest.mark.asyncio
    async def test_order_rejected_by_risk_limits(self):
        """Test that order violating risk limits is rejected before API call."""
        # Mock should never be called
        call_count = {"count": 0}
        
        async def handler(request: httpx.Request) -> httpx.Response:
            call_count["count"] += 1
            return httpx.Response(200, json={"order_id": "SHOULD-NOT-SEE"})
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport
        )
        
        service = DeltaOrderService(client=client)
        limits = RiskLimits(
            allowed_coins=["BTC"],
            max_units_per_order=1.0  # Very strict limit
        )
        
        result = await service.place_order(
            coin="BTC",
            side="buy",
            quantity=10.0,  # Exceeds limit
            risk_limits=limits,
            order_type="market",
            estimated_price=50000.0
        )
        
        assert result.success is False
        assert result.error_code == "RISK_LIMIT_VIOLATION"
        assert "max_units_per_order" in result.message
        assert result.risk_check.approved is False
        assert call_count["count"] == 0  # API was never called
    
    @pytest.mark.asyncio
    async def test_disallowed_coin_rejected(self):
        """Test that disallowed coin is rejected."""
        service = DeltaOrderService(
            client=DeltaExchangeClient(
                base_url="https://test.delta.exchange",
                credentials=DeltaCredentials(api_key="key", api_secret="secret")
            )
        )
        
        limits = RiskLimits(allowed_coins=["BTC", "ETH"])
        
        result = await service.place_order(
            coin="DOGE",  # Not allowed
            side="buy",
            quantity=100.0,
            risk_limits=limits,
            order_type="market",
            estimated_price=0.1
        )
        
        assert result.success is False
        assert result.error_code == "RISK_LIMIT_VIOLATION"
        assert "DOGE" in result.message
        assert "not in allowed list" in result.message
    
    @pytest.mark.asyncio
    async def test_invalid_side_parameter(self):
        """Test validation of side parameter."""
        service = DeltaOrderService(
            client=DeltaExchangeClient(
                base_url="https://test.delta.exchange",
                credentials=DeltaCredentials(api_key="key", api_secret="secret")
            )
        )
        
        limits = RiskLimits(allowed_coins=["BTC"])
        
        result = await service.place_order(
            coin="BTC",
            side="invalid",  # Must be "buy" or "sell"
            quantity=1.0,
            risk_limits=limits,
            order_type="market",
            estimated_price=50000.0
        )
        
        assert result.success is False
        assert result.error_code == "INVALID_SIDE"
        assert "must be 'buy' or 'sell'" in result.message
    
    @pytest.mark.asyncio
    async def test_invalid_order_type(self):
        """Test validation of order_type parameter."""
        service = DeltaOrderService(
            client=DeltaExchangeClient(
                base_url="https://test.delta.exchange",
                credentials=DeltaCredentials(api_key="key", api_secret="secret")
            )
        )
        
        limits = RiskLimits(allowed_coins=["BTC"])
        
        result = await service.place_order(
            coin="BTC",
            side="buy",
            quantity=1.0,
            risk_limits=limits,
            order_type="stop_loss",  # Not supported
            estimated_price=50000.0
        )
        
        assert result.success is False
        assert result.error_code == "INVALID_ORDER_TYPE"
        assert "must be 'market' or 'limit'" in result.message
    
    @pytest.mark.asyncio
    async def test_limit_order_requires_limit_price(self):
        """Test that limit orders require limit_price parameter."""
        service = DeltaOrderService(
            client=DeltaExchangeClient(
                base_url="https://test.delta.exchange",
                credentials=DeltaCredentials(api_key="key", api_secret="secret")
            )
        )
        
        limits = RiskLimits(allowed_coins=["BTC"])
        
        result = await service.place_order(
            coin="BTC",
            side="buy",
            quantity=1.0,
            risk_limits=limits,
            order_type="limit",
            # limit_price not provided
        )
        
        assert result.success is False
        assert result.error_code == "MISSING_LIMIT_PRICE"
        assert "limit_price required" in result.message
    
    @pytest.mark.asyncio
    async def test_market_order_requires_estimated_price(self):
        """Test that market orders require estimated_price for risk validation."""
        service = DeltaOrderService(
            client=DeltaExchangeClient(
                base_url="https://test.delta.exchange",
                credentials=DeltaCredentials(api_key="key", api_secret="secret")
            )
        )
        
        limits = RiskLimits(allowed_coins=["BTC"])
        
        result = await service.place_order(
            coin="BTC",
            side="buy",
            quantity=1.0,
            risk_limits=limits,
            order_type="market",
            # estimated_price not provided
        )
        
        assert result.success is False
        assert result.error_code == "MISSING_ESTIMATED_PRICE"
        assert "estimated_price required" in result.message
    
    @pytest.mark.asyncio
    async def test_negative_quantity_rejected(self):
        """Test that negative or zero quantities are rejected."""
        service = DeltaOrderService(
            client=DeltaExchangeClient(
                base_url="https://test.delta.exchange",
                credentials=DeltaCredentials(api_key="key", api_secret="secret")
            )
        )
        
        limits = RiskLimits(allowed_coins=["BTC"])
        
        result = await service.place_order(
            coin="BTC",
            side="buy",
            quantity=-5.0,  # Invalid
            risk_limits=limits,
            order_type="market",
            estimated_price=50000.0
        )
        
        assert result.success is False
        assert result.error_code == "INVALID_QUANTITY"
        assert "must be > 0" in result.message
    
    @pytest.mark.asyncio
    async def test_exchange_error_mapped_to_result(self):
        """Test that Delta Exchange errors are mapped to DeltaOrderResult."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "Invalid API key"})
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="invalid", api_secret="invalid"),
            transport=transport,
            max_retries=0
        )
        
        service = DeltaOrderService(client=client)
        limits = RiskLimits(allowed_coins=["BTC"])
        
        result = await service.place_order(
            coin="BTC",
            side="buy",
            quantity=1.0,
            risk_limits=limits,
            order_type="market",
            estimated_price=50000.0
        )
        
        assert result.success is False
        assert result.error_code == "AUTHENTICATION_ERROR"
        assert result.order_id is None
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_mapped(self):
        """Test that rate limit errors (429) are properly mapped."""
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, json={"error": "Rate limit exceeded"})
        
        transport = httpx.MockTransport(handler)
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret"),
            transport=transport,
            max_retries=0
        )
        
        service = DeltaOrderService(client=client)
        limits = RiskLimits(allowed_coins=["BTC"])
        
        result = await service.place_order(
            coin="BTC",
            side="buy",
            quantity=1.0,
            risk_limits=limits,
            order_type="market",
            estimated_price=50000.0
        )
        
        assert result.success is False
        assert result.error_code == "RATE_LIMIT"
