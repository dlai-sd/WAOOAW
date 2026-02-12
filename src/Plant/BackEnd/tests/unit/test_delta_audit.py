"""Tests for Delta Exchange trading audit trail."""

import logging

import pytest

from integrations.delta_exchange.audit import TradeAuditLogger, get_audit_logger


class TestTradeAuditLogger:
    """Test cases for trade audit logging."""
    
    @pytest.mark.asyncio
    async def test_log_trade_intent(self, caplog):
        """Test logging of customer trade approval."""
        logger = TradeAuditLogger()
        
        with caplog.at_level(logging.INFO):
            await logger.log_trade_intent(
                customer_id="CUST-123",
                agent_id="AGENT-456",
                coin="BTC",
                side="buy",
                quantity=1.5,
                price=50000.0,
                order_type="limit",
                correlation_id="test-intent-123"
            )
        
        assert "trade_intent" in caplog.text
        assert "CUST-123" in caplog.text
        assert "AGENT-456" in caplog.text
        assert "BTC" in caplog.text
        assert "approved" in caplog.text
        assert "test-intent-123" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_risk_check_passed(self, caplog):
        """Test logging of successful risk check."""
        logger = TradeAuditLogger()
        
        risk_result = {
            "approved": True,
            "checked_limits": ["allowed_coins", "max_units_per_order"]
        }
        
        with caplog.at_level(logging.INFO):
            await logger.log_risk_check(
                customer_id="CUST-123",
                agent_id="AGENT-456",
                coin="ETH",
                side="sell",
                quantity=5.0,
                price=3000.0,
                risk_check_result=risk_result,
                correlation_id="test-risk-123"
            )
        
        assert "Risk check" in caplog.text
        assert "ETH" in caplog.text
        assert "PASSED" in caplog.text
        assert str(risk_result) in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_risk_check_rejected(self, caplog):
        """Test logging of failed risk check."""
        logger = TradeAuditLogger()
        
        risk_result = {
            "approved": False,
            "reason": "Coin 'DOGE' not in allowed list"
        }
        
        with caplog.at_level(logging.INFO):
            await logger.log_risk_check(
                customer_id="CUST-123",
                agent_id="AGENT-456",
                coin="DOGE",
                side="buy",
                quantity=1000.0,
                price=0.08,
                risk_check_result=risk_result,
                correlation_id="test-risk-456"
            )
        
        assert "Risk check" in caplog.text
        assert "DOGE" in caplog.text
        assert "REJECTED" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_trade_executed(self, caplog):
        """Test logging of successful order placement."""
        logger = TradeAuditLogger()
        
        with caplog.at_level(logging.INFO):
            await logger.log_trade_executed(
                customer_id="CUST-123",
                agent_id="AGENT-456",
                coin="BTC",
                side="buy",
                quantity=0.5,
                price=49500.0,
                order_id="DX-ORDER-789",
                order_type="limit",
                correlation_id="test-exec-123"
            )
        
        assert "trade_executed" in caplog.text
        assert "DX-ORDER-789" in caplog.text
        assert "placed" in caplog.text
        assert "49500.0" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_order_filled(self, caplog):
        """Test logging of order execution completion."""
        logger = TradeAuditLogger()
        
        with caplog.at_level(logging.INFO):
            await logger.log_order_filled(
                customer_id="CUST-123",
                agent_id="AGENT-456",
                coin="ETH",
                side="sell",
                quantity=2.0,
                fill_price=3050.0,
                order_id="DX-ORDER-999",
                fees=15.0,
                slippage=0.5,
                correlation_id="test-fill-123"
            )
        
        assert "order_filled" in caplog.text
        assert "DX-ORDER-999" in caplog.text
        assert "filled" in caplog.text
        assert "3050.0" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_trade_failed(self, caplog):
        """Test logging of trade failure."""
        logger = TradeAuditLogger()
        
        with caplog.at_level(logging.ERROR):
            await logger.log_trade_failed(
                customer_id="CUST-123",
                agent_id="AGENT-456",
                coin="BTC",
                side="buy",
                quantity=10.0,
                price=50000.0,
                error_code="INSUFFICIENT_FUNDS",
                error_message="Account balance insufficient for trade",
                order_id="DX-ORDER-ERROR",
                correlation_id="test-fail-123"
            )
        
        assert "trade_failed" in caplog.text
        assert "FAILED" in caplog.text
        assert "INSUFFICIENT_FUNDS" in caplog.text
        assert "Account balance insufficient" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_trade_event_generic(self, caplog):
        """Test generic trade event logging."""
        logger = TradeAuditLogger()
        
        with caplog.at_level(logging.INFO):
            await logger.log_trade_event(
                customer_id="CUST-789",
                agent_id="AGENT-012",
                event_type="custom_event",
                coin="SOL",
                side="buy",
                quantity=100.0,
                price=25.0,
                status="processing",
                correlation_id="test-generic-123"
            )
        
        assert "custom_event" in caplog.text
        assert "SOL" in caplog.text
        assert "100.0" in caplog.text
        assert "processing" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_event_with_all_optional_fields(self, caplog):
        """Test logging with all optional fields populated."""
        logger = TradeAuditLogger()
        
        with caplog.at_level(logging.INFO):
            await logger.log_trade_event(
                customer_id="CUST-999",
                agent_id="AGENT-999",
                event_type="trade_executed",
                coin="ADA",
                side="sell",
                quantity=1000.0,
                price=0.45,
                order_id="DX-FULL-DETAIL",
                status="success",
                error_details={"extra": "info"},
                risk_check_result={"approved": True},
                correlation_id="test-full-123"
            )
        
        assert "DX-FULL-DETAIL" in caplog.text
        assert "ADA" in caplog.text
        assert "0.45" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_event_calculates_notional(self, caplog):
        """Test that notional value is calculated from price and quantity."""
        logger = TradeAuditLogger()
        
        with caplog.at_level(logging.INFO):
            await logger.log_trade_event(
                customer_id="CUST-123",
                agent_id="AGENT-456",
                event_type="trade_executed",
                coin="BTC",
                side="buy",
                quantity=2.0,
                price=50000.0,  # Notional = 2.0 * 50000.0 = 100000.0
                status="placed",
                correlation_id="test-notional-123"
            )
        
        # Notional should be logged in audit record
        assert "100000" in caplog.text or "100000.0" in caplog.text


class TestGetAuditLogger:
    """Test cases for audit logger singleton."""
    
    def test_get_audit_logger_returns_instance(self):
        """Test that get_audit_logger returns a TradeAuditLogger instance."""
        logger = get_audit_logger()
        assert isinstance(logger, TradeAuditLogger)
    
    def test_get_audit_logger_returns_same_instance(self):
        """Test that get_audit_logger returns the same instance (singleton)."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        assert logger1 is logger2


class TestAuditLoggerIntegration:
    """Integration tests for audit logger with trading workflow."""
    
    async def test_full_trade_lifecycle_audit_trail(self, caplog):
        """Test complete audit trail for a full trade lifecycle."""
        logger = TradeAuditLogger()
        
        correlation_id = "test-lifecycle-789"
        customer_id = "CUST-FULL"
        agent_id = "AGENT-FULL"
        coin = "BTC"
        side = "buy"
        quantity = 0.1
        price = 50000.0
        
        with caplog.at_level(logging.INFO):
            # Step 1: Customer approves trade
            await logger.log_trade_intent(
                customer_id=customer_id,
                agent_id=agent_id,
                coin=coin,
                side=side,
                quantity=quantity,
                price=price,
                order_type="limit",
                correlation_id=correlation_id
            )
            
            # Step 2: Risk check passes
            await logger.log_risk_check(
                customer_id=customer_id,
                agent_id=agent_id,
                coin=coin,
                side=side,
                quantity=quantity,
                price=price,
                risk_check_result={"approved": True},
                correlation_id=correlation_id
            )
            
            # Step 3: Order placed
            await logger.log_trade_executed(
                customer_id=customer_id,
                agent_id=agent_id,
                coin=coin,
                side=side,
                quantity=quantity,
                price=price,
                order_id="DX-LIFECYCLE-123",
                order_type="limit",
                correlation_id=correlation_id
            )
            
            # Step 4: Order filled
            await logger.log_order_filled(
                customer_id=customer_id,
                agent_id=agent_id,
                coin=coin,
                side=side,
                quantity=quantity,
                fill_price=50100.0,
                order_id="DX-LIFECYCLE-123",
                fees=25.0,
                slippage=100.0,
                correlation_id=correlation_id
            )
        
        # Verify all steps are logged
        assert "trade_intent" in caplog.text
        assert "Risk check" in caplog.text  # Changed from "risk_check" to match log format
        assert "trade_executed" in caplog.text
        assert "order_filled" in caplog.text
        assert caplog.text.count(correlation_id) == 4
