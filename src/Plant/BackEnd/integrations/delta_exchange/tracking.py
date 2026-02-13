"""Order execution tracking service for Delta Exchange trading.

Handles order status polling with exponential backoff and timeout handling.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from integrations.delta_exchange.client import DeltaExchangeClient, DeltaExchangeError


class OrderStatus(str, Enum):
    """Order execution status states."""
    
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class DeltaOrderStatus:
    """Current status of an order."""
    
    order_id: str
    status: OrderStatus
    filled_quantity: float = 0.0
    remaining_quantity: float = 0.0
    average_fill_price: Optional[float] = None
    fees: Optional[float] = None


@dataclass(frozen=True)
class OrderExecutionResult:
    """Result of tracking order to completion."""
    
    order_id: str
    final_status: OrderStatus
    filled_quantity: float
    average_fill_price: Optional[float] = None
    fees: Optional[float] = None
    timeout: bool = False
    error_message: Optional[str] = None


class OrderTracker:
    """Service for tracking order execution to completion."""
    
    def __init__(self, client: DeltaExchangeClient):
        self._client = client
    
    async def track_order_to_completion(
        self,
        *,
        order_id: str,
        timeout_seconds: int = 120,
        correlation_id: Optional[str] = None,
    ) -> OrderExecutionResult:
        """Poll order status until filled or timeout.
        
        Args:
            order_id: Order ID to track
            timeout_seconds: Maximum time to wait (default 120 seconds)
            correlation_id: Request correlation ID for tracing
            
        Returns:
            OrderExecutionResult with final execution details
            
        Note:
            Polls with exponential backoff: 1s, 2s, 4s, 8s, 15s
        """
        start_time = asyncio.get_event_loop().time()
        attempt = 0
        
        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            
            # Check timeout
            if elapsed >= timeout_seconds:
                # Get final status before timing out
                try:
                    final_status = await self.get_order_status(
                        order_id=order_id,
                        correlation_id=correlation_id
                    )
                    return OrderExecutionResult(
                        order_id=order_id,
                        final_status=final_status.status,
                        filled_quantity=final_status.filled_quantity,
                        average_fill_price=final_status.average_fill_price,
                        fees=final_status.fees,
                        timeout=True,
                        error_message=f"Timeout after {timeout_seconds}s"
                    )
                except Exception:
                    return OrderExecutionResult(
                        order_id=order_id,
                        final_status=OrderStatus.UNKNOWN,
                        filled_quantity=0.0,
                        timeout=True,
                        error_message=f"Timeout after {timeout_seconds}s, unable to get final status"
                    )
            
            # Poll order status
            try:
                status = await self.get_order_status(
                    order_id=order_id,
                    correlation_id=correlation_id
                )
                
                # Check if order is in terminal state
                if status.status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
                    return OrderExecutionResult(
                        order_id=order_id,
                        final_status=status.status,
                        filled_quantity=status.filled_quantity,
                        average_fill_price=status.average_fill_price,
                        fees=status.fees,
                        timeout=False
                    )
                
                # Order still processing, wait with backoff
                delay = self._calculate_backoff_delay(attempt)
                await asyncio.sleep(delay)
                attempt += 1
            
            except DeltaExchangeError as exc:
                # If order not found or other error, return error result
                return OrderExecutionResult(
                    order_id=order_id,
                    final_status=OrderStatus.UNKNOWN,
                    filled_quantity=0.0,
                    timeout=False,
                    error_message=str(exc)
                )
    
    async def get_order_status(
        self,
        *,
        order_id: str,
        correlation_id: Optional[str] = None,
    ) -> DeltaOrderStatus:
        """Get current order status (stub for MVP).
        
        Args:
            order_id: Order ID to check
            correlation_id: Request correlation ID for tracing
            
        Returns:
            DeltaOrderStatus with current status details
            
        Note:
            This is a stub. In production, would call GET /v2/orders/{order_id}
            For Story AGP2-TRADE-1.4, we focus on the tracking logic.
            The actual API integration would be done when connecting to real exchange.
        """
        # Stub: In production would call GET /v2/orders/{order_id}
        # For now, return a mock status to enable testing
        # Real implementation would:
        # response = await self._client._request(
        #     method="GET",
        #     path=f"/v2/orders/{order_id}",
        #     json_body={},
        #     correlation_id=correlation_id
        # )
        
        # Return stub status
        return DeltaOrderStatus(
            order_id=order_id,
            status=OrderStatus.FILLED,  # Stub assumes success
            filled_quantity=1.0,
            remaining_quantity=0.0,
            average_fill_price=50000.0,
            fees=10.0
        )
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay.
        
        Backoff schedule: 1s, 2s, 4s, 8s, then 15s for all remaining attempts
        """
        if attempt == 0:
            return 1.0
        elif attempt == 1:
            return 2.0
        elif attempt == 2:
            return 4.0
        elif attempt == 3:
            return 8.0
        else:
            return 15.0  # Cap at 15s for remaining attempts
