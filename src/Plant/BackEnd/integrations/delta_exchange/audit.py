"""Audit trail and usage events for Delta Exchange trading operations.

Provides complete audit trail for compliance and troubleshooting.
All trading actions are logged with immutable records.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TradeAuditLogger:
    """Audit logger for Delta Exchange trading operations.
    
    Note: Current implementation logs to Python logging. In production,
    should integrate with:
    - Usage events system (for customer billing/analytics)
    - Structured logging (JSON logs for log aggregation)
    - Audit database (for compliance queries and immutable storage)
    """
    
    def __init__(self):
        pass
    
    async def log_trade_event(
        self,
        *,
        customer_id: str,
        agent_id: str,
        event_type: str,
        coin: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        order_id: Optional[str] = None,
        status: str = "pending",
        error_details: Optional[Dict] = None,
        risk_check_result: Optional[Dict] = None,
        correlation_id: str,
    ) -> None:
        """Log a trading event to the audit trail.
        
        Args:
            customer_id: Customer identifier
            agent_id: Agent instance identifier
            event_type: Type of trade event (trade_intent, risk_check, trade_executed, order_filled, trade_failed)
            coin: Trading pair symbol
            side: Order side (buy/sell)
            quantity: Order quantity in units
            price: Order price (for limit) or fill price (for execution)
            order_id: Exchange order ID (if available)
            status: Trade status (pending, success, failed)
            error_details: Error information for failed trades
            risk_check_result: Risk validation details
            correlation_id: Request correlation ID for tracing
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Build audit record
        audit_record = {
            "timestamp": timestamp,
            "event_type": event_type,
            "customer_id": customer_id,
            "agent_id": agent_id,
            "coin": coin,
            "side": side,
            "quantity": quantity,
            "status": status,
            "correlation_id": correlation_id,
        }
        
        # Add optional fields
        if price is not None:
            audit_record["price"] = price
            audit_record["notional_inr"] = quantity * price
        
        if order_id is not None:
            audit_record["order_id"] = order_id
        
        if error_details is not None:
            audit_record["error_details"] = error_details
        
        if risk_check_result is not None:
            audit_record["risk_check"] = risk_check_result
        
        # Log at appropriate level based on status
        if status == "failed":
            logger.error(
                f"[{correlation_id}] Trade event: {event_type} FAILED - "
                f"customer={customer_id} agent={agent_id} coin={coin} side={side} "
                f"quantity={quantity} order_id={order_id} error={error_details}",
                extra={"audit_record": audit_record}
            )
        elif event_type == "risk_check":
            # Include status in risk check logs
            logger.info(
                f"[{correlation_id}] Risk check {status.upper()} - "
                f"customer={customer_id} agent={agent_id} coin={coin} side={side} "
                f"quantity={quantity} price={price} result={risk_check_result}",
                extra={"audit_record": audit_record}
            )
        else:
            # Include all key fields in standard trade event logs
            log_parts = [
                f"[{correlation_id}] Trade event: {event_type} -",
                f"customer={customer_id}",
                f"agent={agent_id}",
                f"coin={coin}",
                f"side={side}",
                f"quantity={quantity}",
            ]
            
            if price is not None:
                log_parts.append(f"price={price}")
                log_parts.append(f"notional=₹{quantity * price:.2f}")
            
            if order_id is not None:
                log_parts.append(f"order_id={order_id}")
            
            log_parts.append(f"status={status}")
            
            logger.info(" ".join(log_parts), extra={"audit_record": audit_record})
    
    async def log_trade_intent(
        self,
        *,
        customer_id: str,
        agent_id: str,
        coin: str,
        side: str,
        quantity: float,
        price: Optional[float],
        order_type: str,
        correlation_id: str,
    ) -> None:
        """Log customer approval of trade draft.
        
        This event marks the customer's intent to execute a trade.
        """
        await self.log_trade_event(
            customer_id=customer_id,
            agent_id=agent_id,
            event_type="trade_intent",
            coin=coin,
            side=side,
            quantity=quantity,
            price=price,
            status="approved",
            correlation_id=correlation_id,
        )
    
    async def log_risk_check(
        self,
        *,
        customer_id: str,
        agent_id: str,
        coin: str,
        side: str,
        quantity: float,
        price: float,
        risk_check_result: Dict,
        correlation_id: str,
    ) -> None:
        """Log risk validation check result.
        
        Records the outcome of pre-trade risk limit validation.
        """
        status = "passed" if risk_check_result.get("approved") else "rejected"
        
        await self.log_trade_event(
            customer_id=customer_id,
            agent_id=agent_id,
            event_type="risk_check",
            coin=coin,
            side=side,
            quantity=quantity,
            price=price,
            status=status,
            risk_check_result=risk_check_result,
            correlation_id=correlation_id,
        )
    
    async def log_trade_executed(
        self,
        *,
        customer_id: str,
        agent_id: str,
        coin: str,
        side: str,
        quantity: float,
        price: Optional[float],
        order_id: str,
        order_type: str,
        correlation_id: str,
    ) -> None:
        """Log successful order placement.
        
        Records that the order was submitted to the exchange successfully.
        """
        await self.log_trade_event(
            customer_id=customer_id,
            agent_id=agent_id,
            event_type="trade_executed",
            coin=coin,
            side=side,
            quantity=quantity,
            price=price,
            order_id=order_id,
            status="placed",
            correlation_id=correlation_id,
        )
    
    async def log_order_filled(
        self,
        *,
        customer_id: str,
        agent_id: str,
        coin: str,
        side: str,
        quantity: float,
        fill_price: float,
        order_id: str,
        fees: Optional[float] = None,
        slippage: Optional[float] = None,
        correlation_id: str,
    ) -> None:
        """Log order execution completion.
        
        Records the final execution details including fill price, fees, slippage.
        """
        execution_details = {}
        if fees is not None:
            execution_details["fees"] = fees
        if slippage is not None:
            execution_details["slippage"] = slippage
        
        await self.log_trade_event(
            customer_id=customer_id,
            agent_id=agent_id,
            event_type="order_filled",
            coin=coin,
            side=side,
            quantity=quantity,
            price=fill_price,
            order_id=order_id,
            status="filled",
            error_details=execution_details if execution_details else None,
            correlation_id=correlation_id,
        )
    
    async def log_trade_failed(
        self,
        *,
        customer_id: str,
        agent_id: str,
        coin: str,
        side: str,
        quantity: float,
        price: Optional[float],
        error_code: str,
        error_message: str,
        order_id: Optional[str] = None,
        correlation_id: str,
    ) -> None:
        """Log trade failure.
        
        Records order placement or execution failures with error details.
        """
        error_details = {
            "error_code": error_code,
            "error_message": error_message,
        }
        
        await self.log_trade_event(
            customer_id=customer_id,
            agent_id=agent_id,
            event_type="trade_failed",
            coin=coin,
            side=side,
            quantity=quantity,
            price=price,
            order_id=order_id,
            status="failed",
            error_details=error_details,
            correlation_id=correlation_id,
        )


# Global audit logger instance
_audit_logger: Optional[TradeAuditLogger] = None


def get_audit_logger() -> TradeAuditLogger:
    """Get the global trade audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = TradeAuditLogger()
    return _audit_logger
