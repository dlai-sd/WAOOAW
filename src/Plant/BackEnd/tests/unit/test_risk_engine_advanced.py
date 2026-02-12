"""Tests for advanced risk engine features (daily limits, ops overrides)."""

import logging
from datetime import datetime, timezone

import pytest

from integrations.delta_exchange.risk_engine import (
    RiskEngine,
    RiskLimits,
    DailyLimitTracker,
    OpsOverride,
)


class TestDailyLimitTracker:
    """Test cases for daily limit tracking."""
    
    def test_record_and_get_daily_usage(self):
        """Test recording trades and retrieving daily usage."""
        tracker = DailyLimitTracker()
        
        # Record first trade
        tracker.record_trade(
            customer_id="CUST-123",
            agent_id="AGENT-456",
            notional_inr=50000.0
        )
        
        usage = tracker.get_daily_usage(
            customer_id="CUST-123",
            agent_id="AGENT-456"
        )
        
        assert usage["trades"] == 1
        assert usage["notional"] == 50000.0
    
    def test_accumulate_multiple_trades(self):
        """Test that multiple trades accumulate correctly."""
        tracker = DailyLimitTracker()
        
        # Record 3 trades
        tracker.record_trade(customer_id="CUST-1", agent_id="AGENT-1", notional_inr=10000.0)
        tracker.record_trade(customer_id="CUST-1", agent_id="AGENT-1", notional_inr=20000.0)
        tracker.record_trade(customer_id="CUST-1", agent_id="AGENT-1", notional_inr=15000.0)
        
        usage = tracker.get_daily_usage(customer_id="CUST-1", agent_id="AGENT-1")
        
        assert usage["trades"] == 3
        assert usage["notional"] == 45000.0
    
    def test_separate_tracking_per_customer_agent(self):
        """Test that usage is tracked separately per customer/agent."""
        tracker = DailyLimitTracker()
        
        tracker.record_trade(customer_id="CUST-1", agent_id="AGENT-1", notional_inr=10000.0)
        tracker.record_trade(customer_id="CUST-2", agent_id="AGENT-1", notional_inr=20000.0)
        tracker.record_trade(customer_id="CUST-1", agent_id="AGENT-2", notional_inr=30000.0)
        
        usage1 = tracker.get_daily_usage(customer_id="CUST-1", agent_id="AGENT-1")
        usage2 = tracker.get_daily_usage(customer_id="CUST-2", agent_id="AGENT-1")
        usage3 = tracker.get_daily_usage(customer_id="CUST-1", agent_id="AGENT-2")
        
        assert usage1["trades"] == 1
        assert usage1["notional"] == 10000.0
        assert usage2["trades"] == 1
        assert usage2["notional"] == 20000.0
        assert usage3["trades"] == 1
        assert usage3["notional"] == 30000.0
    
    def test_get_usage_for_new_customer_agent(self):
        """Test getting usage for customer/agent with no trades."""
        tracker = DailyLimitTracker()
        
        usage = tracker.get_daily_usage(customer_id="NEW-CUST", agent_id="NEW-AGENT")
        
        assert usage["trades"] == 0
        assert usage["notional"] == 0.0
    
    def test_reset_daily_usage(self):
        """Test resetting daily usage for testing."""
        tracker = DailyLimitTracker()
        
        tracker.record_trade(customer_id="CUST-1", agent_id="AGENT-1", notional_inr=10000.0)
        tracker.reset_daily_usage(customer_id="CUST-1", agent_id="AGENT-1")
        
        usage = tracker.get_daily_usage(customer_id="CUST-1", agent_id="AGENT-1")
        assert usage["trades"] == 0
        assert usage["notional"] == 0.0


class TestRiskEngineWithDailyLimits:
    """Test cases for daily limit enforcement."""
    
    def test_daily_trade_limit_enforced(self):
        """Test that daily trade limit is enforced."""
        tracker = DailyLimitTracker()
        engine = RiskEngine(daily_tracker=tracker)
        
        limits = RiskLimits(
            allowed_coins=["BTC"],
            daily_trade_limit=2  # Max 2 trades per day
        )
        
        # First trade should pass
        result1 = engine.validate_order(
            coin="BTC",
            quantity=1.0,
            price=50000.0,
            risk_limits=limits,
            customer_id="CUST-1",
            agent_id="AGENT-1"
        )
        assert result1.approved is True
        
        # Record first trade
        engine.record_trade(customer_id="CUST-1", agent_id="AGENT-1", quantity=1.0, price=50000.0)
        
        # Second trade should pass
        result2 = engine.validate_order(
            coin="BTC",
            quantity=1.0,
            price=50000.0,
            risk_limits=limits,
            customer_id="CUST-1",
            agent_id="AGENT-1"
        )
        assert result2.approved is True
        
        # Record second trade
        engine.record_trade(customer_id="CUST-1", agent_id="AGENT-1", quantity=1.0, price=50000.0)
        
        # Third trade should fail (exceeds limit)
        result3 = engine.validate_order(
            coin="BTC",
            quantity=1.0,
            price=50000.0,
            risk_limits=limits,
            customer_id="CUST-1",
            agent_id="AGENT-1"
        )
        assert result3.approved is False
        assert "Daily trade limit exceeded" in result3.reason
        assert result3.checked_limits["current_trades"] == 2
    
    def test_daily_notional_limit_enforced(self):
        """Test that daily notional limit is enforced."""
        tracker = DailyLimitTracker()
        engine = RiskEngine(daily_tracker=tracker)
        
        limits = RiskLimits(
            allowed_coins=["BTC"],
            daily_notional_limit=100000.0  # Max ₹1 lakh per day
        )
        
        # First trade: ₹50k should pass
        result1 = engine.validate_order(
            coin="BTC",
            quantity=1.0,
            price=50000.0,
            risk_limits=limits,
            customer_id="CUST-1",
            agent_id="AGENT-1"
        )
        assert result1.approved is True
        engine.record_trade(customer_id="CUST-1", agent_id="AGENT-1", quantity=1.0, price=50000.0)
        
        # Second trade: ₹40k should pass (total ₹90k < ₹100k)
        result2 = engine.validate_order(
            coin="BTC",
            quantity=0.8,
            price=50000.0,  # ₹40k
            risk_limits=limits,
            customer_id="CUST-1",
            agent_id="AGENT-1"
        )
        assert result2.approved is True
        engine.record_trade(customer_id="CUST-1", agent_id="AGENT-1", quantity=0.8, price=50000.0)
        
        # Third trade: ₹20k should fail (total would be ₹110k > ₹100k)
        result3 = engine.validate_order(
            coin="BTC",
            quantity=0.4,
            price=50000.0,  # ₹20k
            risk_limits=limits,
            customer_id="CUST-1",
            agent_id="AGENT-1"
        )
        assert result3.approved is False
        assert "Daily notional limit exceeded" in result3.reason
        assert result3.checked_limits["current_notional"] == 90000.0
        assert result3.checked_limits["total_notional"] == 110000.0
    
    def test_daily_limits_not_enforced_without_customer_agent_ids(self):
        """Test that daily limits are skipped if customer/agent IDs not provided."""
        engine = RiskEngine()
        
        limits = RiskLimits(
            allowed_coins=["BTC"],
            daily_trade_limit=1,  # Would normally block
            daily_notional_limit=1000.0  # Would normally block
        )
        
        # Should pass because customer/agent IDs not provided
        result = engine.validate_order(
            coin="BTC",
            quantity=10.0,
            price=50000.0,  # ₹500k >> limit
            risk_limits=limits
            # No customer_id or agent_id
        )
        
        assert result.approved is True


class TestOpsOverride:
    """Test cases for operations override capability."""
    
    def test_ops_override_bypasses_all_limits(self):
        """Test that ops override bypasses all risk limits."""
        engine = RiskEngine()
        
        # Very restrictive limits
        limits = RiskLimits(
            allowed_coins=["BTC"],
            max_units_per_order=1.0,
            max_notional_inr=50000.0
        )
        
        # Order that would normally violate limits
        override = OpsOverride(
            operator_id="ops@example.com",
            reason="Emergency trade for VIP customer"
        )
        
        result = engine.validate_order(
            coin="BTC",
            quantity=100.0,  # Exceeds max_units_per_order
            price=60000.0,  # ₹6M exceeds max_notional_inr
            risk_limits=limits,
            ops_override=override
        )
        
        assert result.approved is True
        assert result.was_overridden is True
        assert result.override_reason == "Emergency trade for VIP customer"
        assert result.checked_limits.get("override_applied") is True
    
    def test_ops_override_bypasses_daily_limits(self):
        """Test that ops override bypasses daily limits."""
        tracker = DailyLimitTracker()
        engine = RiskEngine(daily_tracker=tracker)
        
        limits = RiskLimits(
            allowed_coins=["BTC"],
            daily_trade_limit=1
        )
        
        # Exhaust daily limit
        engine.validate_order(
            coin="BTC", quantity=1.0, price=50000.0, risk_limits=limits,
            customer_id="CUST-1", agent_id="AGENT-1"
        )
        engine.record_trade(customer_id="CUST-1", agent_id="AGENT-1", quantity=1.0, price=50000.0)
        
        # Trade would normally fail, but override allows it
        override = OpsOverride(
            operator_id="admin@example.com",
            reason="Customer service escalation"
        )
        
        result = engine.validate_order(
            coin="BTC", quantity=1.0, price=50000.0, risk_limits=limits,
            customer_id="CUST-1", agent_id="AGENT-1",
            ops_override=override
        )
        
        assert result.approved is True
        assert result.was_overridden is True
    
    def test_ops_override_has_timestamp(self):
        """Test that OpsOverride automatically adds timestamp."""
        override = OpsOverride(
            operator_id="ops@example.com",
            reason="Test override"
        )
        
        assert override.timestamp is not None
        # Should be valid ISO format
        datetime.fromisoformat(override.timestamp)


class TestRiskCheckLogging:
    """Test cases for risk check logging."""
    
    def test_risk_check_passed_logged(self, caplog):
        """Test that successful risk checks are logged."""
        with caplog.at_level(logging.INFO):
            engine = RiskEngine()
            limits = RiskLimits(allowed_coins=["BTC"])
            
            engine.validate_order(
                coin="BTC",
                quantity=1.0,
                price=50000.0,
                risk_limits=limits,
                correlation_id="test-123"
            )
            
            assert "Risk check PASSED" in caplog.text
            assert "test-123" in caplog.text
            assert "coin=BTC" in caplog.text
    
    def test_risk_check_failed_logged(self, caplog):
        """Test that failed risk checks are logged."""
        with caplog.at_level(logging.WARNING):
            engine = RiskEngine()
            limits = RiskLimits(allowed_coins=["BTC"], max_units_per_order=1.0)
            
            engine.validate_order(
                coin="BTC",
                quantity=10.0,  # Exceeds limit
                price=50000.0,
                risk_limits=limits,
                correlation_id="test-456"
            )
            
            assert "Risk check FAILED" in caplog.text
            assert "test-456" in caplog.text
            assert "quantity exceeds max_units_per_order" in caplog.text
    
    def test_ops_override_logged(self, caplog):
        """Test that ops overrides are logged."""
        with caplog.at_level(logging.WARNING):
            engine = RiskEngine()
            limits = RiskLimits(allowed_coins=["BTC"])
            override = OpsOverride(operator_id="admin", reason="Test")
            
            engine.validate_order(
                coin="BTC",
                quantity=1.0,
                price=50000.0,
                risk_limits=limits,
                ops_override=override
            )
            
            assert "Risk check OVERRIDDEN by ops" in caplog.text
            assert "operator=admin" in caplog.text
            assert "reason=Test" in caplog.text
