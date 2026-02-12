"""Tests for Delta Exchange order tracking service."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from integrations.delta_exchange.client import DeltaCredentials, DeltaExchangeClient, DeltaExchangeError
from integrations.delta_exchange.tracking import (
    OrderTracker,
    OrderStatus,
    DeltaOrderStatus,
    OrderExecutionResult,
)


class TestOrderTracker:
    """Test cases for order execution tracking."""
    
    @pytest.mark.asyncio
    async def test_track_order_immediate_fill(self):
        """Test tracking order that fills immediately."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        tracker = OrderTracker(client=client)
        
        # Mock get_order_status to return FILLED immediately
        async def mock_get_status(*args, **kwargs):
            return DeltaOrderStatus(
                order_id="ORD-123",
                status=OrderStatus.FILLED,
                filled_quantity=5.0,
                remaining_quantity=0.0,
                average_fill_price=50000.0,
                fees=25.0
            )
        
        tracker.get_order_status = AsyncMock(side_effect=mock_get_status)
        
        result = await tracker.track_order_to_completion(
            order_id="ORD-123",
            timeout_seconds=30
        )
        
        assert result.order_id == "ORD-123"
        assert result.final_status == OrderStatus.FILLED
        assert result.filled_quantity == 5.0
        assert result.average_fill_price == 50000.0
        assert result.fees == 25.0
        assert result.timeout is False
        assert tracker.get_order_status.await_count == 1
    
    @pytest.mark.asyncio
    async def test_track_order_with_retries(self):
        """Test tracking order that fills after multiple polls."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        tracker = OrderTracker(client=client)
        
        poll_count = {"count": 0}
        
        async def mock_get_status(*args, **kwargs):
            poll_count["count"] += 1
            if poll_count["count"] < 3:
                # First 2 polls: pending
                return DeltaOrderStatus(
                    order_id="ORD-456",
                    status=OrderStatus.OPEN,
                    filled_quantity=0.0,
                    remaining_quantity=10.0
                )
            else:
                # 3rd poll: filled
                return DeltaOrderStatus(
                    order_id="ORD-456",
                    status=OrderStatus.FILLED,
                    filled_quantity=10.0,
                    remaining_quantity=0.0,
                    average_fill_price=3000.0,
                    fees=15.0
                )
        
        tracker.get_order_status = AsyncMock(side_effect=mock_get_status)
        
        result = await tracker.track_order_to_completion(
            order_id="ORD-456",
            timeout_seconds=60
        )
        
        assert result.final_status == OrderStatus.FILLED
        assert result.filled_quantity == 10.0
        assert poll_count["count"] == 3
        assert result.timeout is False
    
    @pytest.mark.asyncio
    async def test_track_order_cancelled(self):
        """Test tracking order that gets cancelled."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        tracker = OrderTracker(client=client)
        
        async def mock_get_status(*args, **kwargs):
            return DeltaOrderStatus(
                order_id="ORD-789",
                status=OrderStatus.CANCELLED,
                filled_quantity=0.0,
                remaining_quantity=0.0
            )
        
        tracker.get_order_status = AsyncMock(side_effect=mock_get_status)
        
        result = await tracker.track_order_to_completion(
            order_id="ORD-789"
        )
        
        assert result.final_status == OrderStatus.CANCELLED
        assert result.filled_quantity == 0.0
        assert result.timeout is False
    
    @pytest.mark.asyncio
    async def test_track_order_rejected(self):
        """Test tracking order that gets rejected."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        tracker = OrderTracker(client=client)
        
        async def mock_get_status(*args, **kwargs):
            return DeltaOrderStatus(
                order_id="ORD-REJ",
                status=OrderStatus.REJECTED,
                filled_quantity=0.0,
                remaining_quantity=0.0
            )
        
        tracker.get_order_status = AsyncMock(side_effect=mock_get_status)
        
        result = await tracker.track_order_to_completion(
            order_id="ORD-REJ"
        )
        
        assert result.final_status == OrderStatus.REJECTED
        assert result.filled_quantity == 0.0
    
    @pytest.mark.asyncio
    async def test_track_order_timeout(self):
        """Test timeout behavior when order doesn't fill in time."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        tracker = OrderTracker(client=client)
        
        # Always return pending status
        async def mock_get_status(*args, **kwargs):
            return DeltaOrderStatus(
                order_id="ORD-SLOW",
                status=OrderStatus.OPEN,
                filled_quantity=0.0,
                remaining_quantity=5.0
            )
        
        tracker.get_order_status = AsyncMock(side_effect=mock_get_status)
        
        # Use very short timeout for test
        result = await tracker.track_order_to_completion(
            order_id="ORD-SLOW",
            timeout_seconds=2  # 2 seconds
        )
        
        assert result.timeout is True
        assert "Timeout" in result.error_message
        # Should have made at least one status check
        assert tracker.get_order_status.await_count >= 1
    
    @pytest.mark.asyncio
    async def test_track_order_api_error(self):
        """Test handling of API errors during tracking."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        tracker = OrderTracker(client=client)
        
        async def mock_get_status_error(*args, **kwargs):
            raise DeltaExchangeError("Order not found", status_code=404)
        
        tracker.get_order_status = AsyncMock(side_effect=mock_get_status_error)
        
        result = await tracker.track_order_to_completion(
            order_id="ORD-NOTFOUND"
        )
        
        assert result.final_status == OrderStatus.UNKNOWN
        assert result.filled_quantity == 0.0
        assert result.timeout is False
        assert "not found" in result.error_message.lower()
    
    def test_backoff_delay_calculation(self):
        """Test exponential backoff delay calculation."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        tracker = OrderTracker(client=client)
        
        # Test backoff schedule: 1s, 2s, 4s, 8s, 15s, 15s, ...
        assert tracker._calculate_backoff_delay(0) == 1.0
        assert tracker._calculate_backoff_delay(1) == 2.0
        assert tracker._calculate_backoff_delay(2) == 4.0
        assert tracker._calculate_backoff_delay(3) == 8.0
        assert tracker._calculate_backoff_delay(4) == 15.0
        assert tracker._calculate_backoff_delay(5) == 15.0
        assert tracker._calculate_backoff_delay(10) == 15.0
    
    @pytest.mark.asyncio
    async def test_track_order_partially_filled(self):
        """Test tracking order with partial fills."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        tracker = OrderTracker(client=client)
        
        poll_count = {"count": 0}
        
        async def mock_get_status(*args, **kwargs):
            poll_count["count"] += 1
            if poll_count["count"] == 1:
                # First poll: partially filled
                return DeltaOrderStatus(
                    order_id="ORD-PARTIAL",
                    status=OrderStatus.PARTIALLY_FILLED,
                    filled_quantity=3.0,
                    remaining_quantity=2.0,
                    average_fill_price=48000.0
                )
            else:
                # Second poll: fully filled
                return DeltaOrderStatus(
                    order_id="ORD-PARTIAL",
                    status=OrderStatus.FILLED,
                    filled_quantity=5.0,
                    remaining_quantity=0.0,
                    average_fill_price=48500.0,
                    fees=12.5
                )
        
        tracker.get_order_status = AsyncMock(side_effect=mock_get_status)
        
        result = await tracker.track_order_to_completion(
            order_id="ORD-PARTIAL"
        )
        
        assert result.final_status == OrderStatus.FILLED
        assert result.filled_quantity == 5.0
        assert result.average_fill_price == 48500.0
        assert poll_count["count"] == 2
    
    @pytest.mark.asyncio
    async def test_track_order_with_correlation_id(self):
        """Test that correlation_id is passed to get_order_status."""
        client = DeltaExchangeClient(
            base_url="https://test.delta.exchange",
            credentials=DeltaCredentials(api_key="key", api_secret="secret")
        )
        
        tracker = OrderTracker(client=client)
        captured_args = {}
        
        async def mock_get_status(*args, **kwargs):
            captured_args.update(kwargs)
            return DeltaOrderStatus(
                order_id="ORD-CORR",
                status=OrderStatus.FILLED,
                filled_quantity=1.0
            )
        
        tracker.get_order_status = AsyncMock(side_effect=mock_get_status)
        
        result = await tracker.track_order_to_completion(
            order_id="ORD-CORR",
            correlation_id="test-corr-999"
        )
        
        assert result.final_status == OrderStatus.FILLED
        assert captured_args.get("correlation_id") == "test-corr-999"
