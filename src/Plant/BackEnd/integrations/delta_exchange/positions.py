"""Position management service for Delta Exchange trading.

Handles position closing with comprehensive safety checks and validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from integrations.delta_exchange.client import DeltaExchangeClient, DeltaExchangeError


@dataclass(frozen=True)
class DeltaPosition:
    """Represents an open position."""
    
    coin: str
    side: str  # "long" or "short"
    quantity: float
    entry_price: float
    unrealized_pnl: float = 0.0
    position_id: Optional[str] = None


@dataclass(frozen=True)
class DeltaCloseResult:
    """Result of position closing operation."""
    
    success: bool
    coin: str
    quantity_closed: float
    message: Optional[str] = None
    order_id: Optional[str] = None
    error_code: Optional[str] = None
    remaining_position: Optional[float] = None


class PositionNotFoundError(Exception):
    """Raised when attempting to close a non-existent position."""
    pass


class DeltaPositionService:
    """Service for managing open positions."""
    
    def __init__(self, client: DeltaExchangeClient):
        self._client = client
    
    async def close_position(
        self,
        *,
        coin: str,
        quantity: Optional[float] = None,  # None = close all
        correlation_id: Optional[str] = None,
    ) -> DeltaCloseResult:
        """Close an open position for the specified coin.
        
        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")
            quantity: Quantity to close (None closes entire position)
            correlation_id: Request correlation ID for tracing
            
        Returns:
            DeltaCloseResult with success status and closing details
        """
        # Step 1: Query open positions to validate position exists
        # In production, would call GET /positions endpoint
        # For MVP, we'll proceed directly to close and handle errors
        
        # Build close payload
        payload: Dict = {
            "coin": coin,
        }
        
        if quantity is not None:
            if quantity <= 0:
                return DeltaCloseResult(
                    success=False,
                    coin=coin,
                    quantity_closed=0.0,
                    message=f"Invalid quantity {quantity}, must be > 0",
                    error_code="INVALID_QUANTITY"
                )
            payload["quantity"] = quantity
        
        # Step 2: Call close position API
        try:
            response = await self._client.close_position(payload, correlation_id=correlation_id)
            
            # Extract closing details from response
            closed_quantity = response.get("quantity_closed") or response.get("quantity", 0.0)
            order_id = response.get("order_id") or response.get("id")
            remaining = response.get("remaining_position")
            
            return DeltaCloseResult(
                success=True,
                coin=coin,
                quantity_closed=closed_quantity,
                message="Position closed successfully",
                order_id=order_id,
                remaining_position=remaining
            )
        
        except DeltaExchangeError as exc:
            # Map exchange errors to result
            error_code = "EXCHANGE_ERROR"
            message = str(exc)
            
            if exc.status_code == 404:
                error_code = "POSITION_NOT_FOUND"
                message = f"No open position found for {coin}"
            elif exc.status_code == 400:
                error_code = "INVALID_REQUEST"
            elif exc.status_code == 401:
                error_code = "AUTHENTICATION_ERROR"
            elif exc.status_code == 403:
                error_code = "PERMISSION_DENIED"
            
            return DeltaCloseResult(
                success=False,
                coin=coin,
                quantity_closed=0.0,
                message=message,
                error_code=error_code
            )
    
    async def get_open_positions(
        self,
        *,
        coin: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> List[DeltaPosition]:
        """Get list of open positions (stub for future implementation).
        
        Args:
            coin: Optional filter by specific coin
            correlation_id: Request correlation ID for tracing
            
        Returns:
            List of open positions
            
        Note:
            This is a stub. In production, would call GET /v2/positions endpoint.
            For Story AGP2-TRADE-1.3, we focus on the close operation.
        """
        # Stub for future implementation
        # Would call: GET /v2/positions
        # For now, return empty list
        return []
