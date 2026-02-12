"""Order placement service for Delta Exchange trading.

Handles order placement with comprehensive risk validation and error handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from integrations.delta_exchange.client import DeltaExchangeClient, DeltaExchangeError
from integrations.delta_exchange.risk_engine import RiskEngine, RiskLimits, RiskCheckResult, OpsOverride


@dataclass(frozen=True)
class DeltaOrderResult:
    """Result of order placement operation."""
    
    success: bool
    order_id: Optional[str] = None
    status: Optional[str] = None  # "pending", "open", "filled", etc.
    message: Optional[str] = None
    risk_check: Optional[RiskCheckResult] = None
    error_code: Optional[str] = None


class OrderValidationError(Exception):
    """Raised when order parameters are invalid."""
    pass


class DeltaOrderService:
    """High-level service for placing orders with risk validation."""
    
    def __init__(self, client: DeltaExchangeClient, risk_engine: Optional[RiskEngine] = None):
        self._client = client
        self._risk_engine = risk_engine or RiskEngine()
    
    async def place_order(
        self,
        *,
        coin: str,
        side: str,  # "buy" or "sell"
        quantity: float,
        risk_limits: RiskLimits,
        order_type: str = "market",
        limit_price: Optional[float] = None,
        estimated_price: Optional[float] = None,  # For market orders risk validation
        customer_id: Optional[str] = None,  # For daily limit tracking
        agent_id: Optional[str] = None,  # For daily limit tracking
        ops_override: Optional[Dict] = None,  # For ops override capability
        correlation_id: Optional[str] = None,
    ) -> DeltaOrderResult:
        """Place an order with pre-trade risk validation.
        
        Args:
            coin: Trading pair symbol (e.g., "BTC", "ETH")
            side: "buy" or "sell"
            quantity: Order quantity in units
            risk_limits: Risk configuration to enforce
            order_type: "market" or "limit"
            limit_price: Required for limit orders, ignored for market orders
            estimated_price: Estimated execution price for market orders (for risk checks)
            customer_id: Customer ID for daily limit tracking (optional)
            agent_id: Agent ID for daily limit tracking (optional)
            ops_override: Ops override dict with operator_id and reason (optional)
            correlation_id: Request correlation ID for tracing
            
        Returns:
            DeltaOrderResult with success status and order details
        """
        # Validate basic parameters
        if side not in ("buy", "sell"):
            return DeltaOrderResult(
                success=False,
                message=f"Invalid side '{side}', must be 'buy' or 'sell'",
                error_code="INVALID_SIDE"
            )
        
        if order_type not in ("market", "limit"):
            return DeltaOrderResult(
                success=False,
                message=f"Invalid order_type '{order_type}', must be 'market' or 'limit'",
                error_code="INVALID_ORDER_TYPE"
            )
        
        if order_type == "limit" and limit_price is None:
            return DeltaOrderResult(
                success=False,
                message="limit_price required for limit orders",
                error_code="MISSING_LIMIT_PRICE"
            )
        
        if quantity <= 0:
            return DeltaOrderResult(
                success=False,
                message=f"Invalid quantity {quantity}, must be > 0",
                error_code="INVALID_QUANTITY"
            )
        
        # Determine price for risk validation
        price_for_risk_check = limit_price if order_type == "limit" else estimated_price
        if price_for_risk_check is None:
            return DeltaOrderResult(
                success=False,
                message="estimated_price required for market order risk validation",
                error_code="MISSING_ESTIMATED_PRICE"
            )
        
        # Run risk validation
        ops_override_obj = None
        if ops_override is not None:
            ops_override_obj = OpsOverride(
                operator_id=ops_override.get("operator_id", "unknown"),
                reason=ops_override.get("reason", "No reason provided")
            )
        
        risk_check = self._risk_engine.validate_order(
            coin=coin,
            quantity=quantity,
            price=price_for_risk_check,
            risk_limits=risk_limits,
            customer_id=customer_id,
            agent_id=agent_id,
            ops_override=ops_override_obj,
            correlation_id=correlation_id
        )
        
        if not risk_check.approved:
            return DeltaOrderResult(
                success=False,
                message=risk_check.reason,
                risk_check=risk_check,
                error_code="RISK_LIMIT_VIOLATION"
            )
        
        # Build order payload
        payload: Dict = {
            "symbol": coin,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
        }
        
        if order_type == "limit":
            payload["limit_price"] = limit_price
        
        # Place order via API
        try:
            response = await self._client.place_order(payload, correlation_id=correlation_id)
            
            # Extract order details from response
            order_id = response.get("order_id") or response.get("id")
            status = response.get("status", "unknown")
            
            # Record trade for daily limit tracking (if customer/agent IDs provided)
            if customer_id and agent_id:
                self._risk_engine.record_trade(
                    customer_id=customer_id,
                    agent_id=agent_id,
                    quantity=quantity,
                    price=price_for_risk_check
                )
            
            return DeltaOrderResult(
                success=True,
                order_id=order_id,
                status=status,
                message="Order placed successfully",
                risk_check=risk_check
            )
        
        except DeltaExchangeError as exc:
            # Map Delta Exchange errors to result
            error_code = "EXCHANGE_ERROR"
            if exc.status_code == 401:
                error_code = "AUTHENTICATION_ERROR"
            elif exc.status_code == 403:
                error_code = "PERMISSION_DENIED"
            elif exc.status_code == 400:
                error_code = "INVALID_REQUEST"
            elif exc.status_code == 429:
                error_code = "RATE_LIMIT"
            
            return DeltaOrderResult(
                success=False,
                message=str(exc),
                error_code=error_code,
                risk_check=risk_check
            )
