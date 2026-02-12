"""Risk validation engine for Delta Exchange trading.

Enforces pre-trade risk limits to prevent violations of configured constraints.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


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
    was_overridden: bool = False  # True if ops override was applied
    override_reason: Optional[str] = None  # Justification for override


@dataclass(frozen=True)
class OpsOverride:
    """Operations override for risk limits."""
    
    operator_id: str  # Who authorized the override
    reason: str  # Why the override was granted
    timestamp: str = None  # When override was created
    
    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now(timezone.utc).isoformat())


class DailyLimitTracker:
    """Tracks daily trading activity for limit enforcement.
    
    Note: In-memory implementation for MVP. In production, should use
    persistent storage (Redis, PostgreSQL) to survive restarts and
    enable cross-instance tracking.
    """
    
    def __init__(self):
        # Structure: {customer_id: {agent_id: {date: {"trades": count, "notional": total}}}}
        self._daily_usage: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
    
    def _get_today_key(self) -> str:
        """Get today's date key (UTC)."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    def record_trade(
        self,
        *,
        customer_id: str,
        agent_id: str,
        notional_inr: float,
    ) -> None:
        """Record a trade for daily limit tracking."""
        today = self._get_today_key()
        
        if customer_id not in self._daily_usage:
            self._daily_usage[customer_id] = {}
        
        if agent_id not in self._daily_usage[customer_id]:
            self._daily_usage[customer_id][agent_id] = {}
        
        if today not in self._daily_usage[customer_id][agent_id]:
            self._daily_usage[customer_id][agent_id][today] = {
                "trades": 0,
                "notional": 0.0
            }
        
        self._daily_usage[customer_id][agent_id][today]["trades"] += 1
        self._daily_usage[customer_id][agent_id][today]["notional"] += notional_inr
        
        logger.info(
            f"Recorded trade for customer={customer_id} agent={agent_id}: "
            f"daily_trades={self._daily_usage[customer_id][agent_id][today]['trades']} "
            f"daily_notional=₹{self._daily_usage[customer_id][agent_id][today]['notional']:.2f}"
        )
    
    def get_daily_usage(
        self,
        *,
        customer_id: str,
        agent_id: str,
    ) -> Dict[str, float]:
        """Get today's usage for a customer/agent."""
        today = self._get_today_key()
        
        if (customer_id in self._daily_usage and
            agent_id in self._daily_usage[customer_id] and
            today in self._daily_usage[customer_id][agent_id]):
            return self._daily_usage[customer_id][agent_id][today]
        
        return {"trades": 0, "notional": 0.0}
    
    def reset_daily_usage(self, *, customer_id: str, agent_id: str) -> None:
        """Reset daily usage for a customer/agent (for testing)."""
        today = self._get_today_key()
        if (customer_id in self._daily_usage and
            agent_id in self._daily_usage[customer_id]):
            self._daily_usage[customer_id][agent_id][today] = {
                "trades": 0,
                "notional": 0.0
            }


class RiskValidationError(Exception):
    """Raised when a trade violates risk limits."""
    
    def __init__(self, message: str, limit_type: str):
        super().__init__(message)
        self.message = message
        self.limit_type = limit_type


class RiskEngine:
    """Pre-trade risk validation engine with daily limit tracking."""
    
    def __init__(self, daily_tracker: Optional[DailyLimitTracker] = None):
        self._daily_tracker = daily_tracker or DailyLimitTracker()
    
    def validate_order(
        self,
        *,
        coin: str,
        quantity: float,
        price: float,
        risk_limits: RiskLimits,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        ops_override: Optional[OpsOverride] = None,
        correlation_id: Optional[str] = None,
    ) -> RiskCheckResult:
        """Validate an order against configured risk limits.
        
        Args:
            coin: Trading pair symbol (e.g., "BTC")
            quantity: Order quantity in units
            price: Order price (for limit orders) or estimated price (market orders)
            risk_limits: Risk configuration to enforce
            customer_id: Customer ID for daily limit tracking
            agent_id: Agent ID for daily limit tracking
            ops_override: Optional ops override to bypass limits
            correlation_id: Request correlation ID for logging
            
        Returns:
            RiskCheckResult indicating approval or rejection
        """
        log_context = f"[{correlation_id}] " if correlation_id else ""
        checked = {}
        notional_value = quantity * price
        
        # If ops override provided, log and approve
        if ops_override is not None:
            logger.warning(
                f"{log_context}Risk check OVERRIDDEN by ops: "
                f"operator={ops_override.operator_id} reason={ops_override.reason} "
                f"coin={coin} quantity={quantity} notional=₹{notional_value:.2f}"
            )
            return RiskCheckResult(
                approved=True,
                reason=None,
                checked_limits={"override_applied": True},
                was_overridden=True,
                override_reason=ops_override.reason
            )
        
        # Check 1: Coin must be in allowed list
        if coin not in risk_limits.allowed_coins:
            logger.warning(
                f"{log_context}Risk check FAILED: coin not allowed - "
                f"coin={coin} allowed={risk_limits.allowed_coins}"
            )
            return RiskCheckResult(
                approved=False,
                reason=f"Coin '{coin}' not in allowed list: {risk_limits.allowed_coins}",
                checked_limits={"allowed_coins": risk_limits.allowed_coins, "requested_coin": coin}
            )
        checked["allowed_coins"] = True
        
        # Check 2: Quantity must not exceed max units per order
        if risk_limits.max_units_per_order is not None:
            if quantity > risk_limits.max_units_per_order:
                logger.warning(
                    f"{log_context}Risk check FAILED: quantity exceeds max_units_per_order - "
                    f"quantity={quantity} max={risk_limits.max_units_per_order}"
                )
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
            if notional_value > risk_limits.max_notional_inr:
                logger.warning(
                    f"{log_context}Risk check FAILED: notional exceeds max_notional_inr - "
                    f"notional=₹{notional_value:.2f} max=₹{risk_limits.max_notional_inr:.2f}"
                )
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
        
        # Check 4: Daily trade limit (if customer/agent IDs provided)
        if customer_id and agent_id and risk_limits.daily_trade_limit is not None:
            daily_usage = self._daily_tracker.get_daily_usage(
                customer_id=customer_id,
                agent_id=agent_id
            )
            current_trades = daily_usage["trades"]
            
            if current_trades >= risk_limits.daily_trade_limit:
                logger.warning(
                    f"{log_context}Risk check FAILED: daily trade limit exceeded - "
                    f"current_trades={current_trades} limit={risk_limits.daily_trade_limit}"
                )
                return RiskCheckResult(
                    approved=False,
                    reason=f"Daily trade limit exceeded: {current_trades}/{risk_limits.daily_trade_limit} trades today",
                    checked_limits={
                        "daily_trade_limit": risk_limits.daily_trade_limit,
                        "current_trades": current_trades
                    }
                )
            checked["daily_trade_limit"] = True
        
        # Check 5: Daily notional limit (if customer/agent IDs provided)
        if customer_id and agent_id and risk_limits.daily_notional_limit is not None:
            daily_usage = self._daily_tracker.get_daily_usage(
                customer_id=customer_id,
                agent_id=agent_id
            )
            current_notional = daily_usage["notional"]
            total_notional = current_notional + notional_value
            
            if total_notional > risk_limits.daily_notional_limit:
                logger.warning(
                    f"{log_context}Risk check FAILED: daily notional limit exceeded - "
                    f"current=₹{current_notional:.2f} + new=₹{notional_value:.2f} = "
                    f"₹{total_notional:.2f} > limit=₹{risk_limits.daily_notional_limit:.2f}"
                )
                return RiskCheckResult(
                    approved=False,
                    reason=f"Daily notional limit exceeded: ₹{total_notional:.2f} > ₹{risk_limits.daily_notional_limit:.2f}",
                    checked_limits={
                        "daily_notional_limit": risk_limits.daily_notional_limit,
                        "current_notional": current_notional,
                        "requested_notional": notional_value,
                        "total_notional": total_notional
                    }
                )
            checked["daily_notional_limit"] = True
        
        # All checks passed
        logger.info(
            f"{log_context}Risk check PASSED - "
            f"coin={coin} quantity={quantity} notional=₹{notional_value:.2f} "
            f"checks={list(checked.keys())}"
        )
        
        return RiskCheckResult(
            approved=True,
            reason=None,
            checked_limits=checked
        )
    
    def record_trade(
        self,
        *,
        customer_id: str,
        agent_id: str,
        quantity: float,
        price: float,
    ) -> None:
        """Record a completed trade for daily limit tracking."""
        notional_inr = quantity * price
        self._daily_tracker.record_trade(
            customer_id=customer_id,
            agent_id=agent_id,
            notional_inr=notional_inr
        )
    
    def validate_coin_allowed(self, coin: str, allowed_coins: List[str]) -> bool:
        """Quick check if coin is allowed."""
        return coin in allowed_coins
