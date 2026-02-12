"""Risk validation engine for Delta Exchange trading.

Enforces pre-trade risk limits to prevent violations of configured constraints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class RiskLimits:
    """Risk configuration for trading operations."""
    
    allowed_coins: List[str]  # Whitelist of tradeable coins
    max_units_per_order: Optional[float] = None  # Max quantity per single order
    max_notional_inr: Optional[float] = None  # Max order value in INR
    daily_trade_limit: Optional[int] = None  # Max trades per day
    daily_notional_limit: Optional[float] = None  # Max total notional per day


@dataclass(frozen=True)
class RiskCheckResult:
    """Result of risk validation check."""
    
    approved: bool
    reason: Optional[str] = None  # Rejection reason if not approved
    checked_limits: dict = None  # Details of applied limits


class RiskValidationError(Exception):
    """Raised when a trade violates risk limits."""
    
    def __init__(self, message: str, limit_type: str):
        super().__init__(message)
        self.message = message
        self.limit_type = limit_type


class RiskEngine:
    """Pre-trade risk validation engine."""
    
    def __init__(self):
        # In future, this could track daily usage across requests
        pass
    
    def validate_order(
        self,
        *,
        coin: str,
        quantity: float,
        price: float,
        risk_limits: RiskLimits,
    ) -> RiskCheckResult:
        """Validate an order against configured risk limits.
        
        Args:
            coin: Trading pair symbol (e.g., "BTC")
            quantity: Order quantity in units
            price: Order price (for limit orders) or estimated price (market orders)
            risk_limits: Risk configuration to enforce
            
        Returns:
            RiskCheckResult indicating approval or rejection
            
        Raises:
            RiskValidationError: If order violates any limit
        """
        checked = {}
        
        # Check 1: Coin must be in allowed list
        if coin not in risk_limits.allowed_coins:
            return RiskCheckResult(
                approved=False,
                reason=f"Coin '{coin}' not in allowed list: {risk_limits.allowed_coins}",
                checked_limits={"allowed_coins": risk_limits.allowed_coins, "requested_coin": coin}
            )
        checked["allowed_coins"] = True
        
        # Check 2: Quantity must not exceed max units per order
        if risk_limits.max_units_per_order is not None:
            if quantity > risk_limits.max_units_per_order:
                return RiskCheckResult(
                    approved=False,
                    reason=f"Order quantity {quantity} exceeds max_units_per_order {risk_limits.max_units_per_order}",
                    checked_limits={
                        "max_units_per_order": risk_limits.max_units_per_order,
                        "requested_quantity": quantity
                    }
                )
            checked["max_units_per_order"] = True
        
        # Check 3: Notional value must not exceed max notional
        if risk_limits.max_notional_inr is not None:
            notional_value = quantity * price
            if notional_value > risk_limits.max_notional_inr:
                return RiskCheckResult(
                    approved=False,
                    reason=f"Order notional ₹{notional_value:.2f} exceeds max_notional_inr ₹{risk_limits.max_notional_inr:.2f}",
                    checked_limits={
                        "max_notional_inr": risk_limits.max_notional_inr,
                        "requested_notional": notional_value,
                        "quantity": quantity,
                        "price": price
                    }
                )
            checked["max_notional_inr"] = True
        
        # All checks passed
        return RiskCheckResult(
            approved=True,
            reason=None,
            checked_limits=checked
        )
    
    def validate_coin_allowed(self, coin: str, allowed_coins: List[str]) -> bool:
        """Quick check if coin is allowed."""
        return coin in allowed_coins
