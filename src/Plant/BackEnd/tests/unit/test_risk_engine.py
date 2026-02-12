"""Tests for Delta Exchange risk engine."""

import pytest

from integrations.delta_exchange.risk_engine import (
    RiskEngine,
    RiskLimits,
    RiskCheckResult,
)


class TestRiskEngine:
    """Test cases for risk validation engine."""
    
    def test_allowed_coin_check_passes(self):
        """Test that orders for allowed coins pass validation."""
        engine = RiskEngine()
        limits = RiskLimits(allowed_coins=["BTC", "ETH", "SOL"])
        
        result = engine.validate_order(
            coin="BTC",
            quantity=1.0,
            price=50000.0,
            risk_limits=limits
        )
        
        assert result.approved is True
        assert result.reason is None
        assert "allowed_coins" in result.checked_limits
    
    def test_disallowed_coin_check_fails(self):
        """Test that orders for disallowed coins fail validation."""
        engine = RiskEngine()
        limits = RiskLimits(allowed_coins=["BTC", "ETH"])
        
        result = engine.validate_order(
            coin="DOGE",
            quantity=1000.0,
            price=0.1,
            risk_limits=limits
        )
        
        assert result.approved is False
        assert "not in allowed list" in result.reason
        assert "DOGE" in result.reason
    
    def test_max_units_per_order_enforced(self):
        """Test that max_units_per_order limit is enforced."""
        engine = RiskEngine()
        limits = RiskLimits(
            allowed_coins=["BTC"],
            max_units_per_order=10.0
        )
        
        # Should fail: exceeds max units
        result = engine.validate_order(
            coin="BTC",
            quantity=15.0,
            price=50000.0,
            risk_limits=limits
        )
        
        assert result.approved is False
        assert "max_units_per_order" in result.reason
        assert "15" in result.reason
        assert "10" in result.reason
    
    def test_max_units_per_order_passes_when_under_limit(self):
        """Test that orders under max_units_per_order pass."""
        engine = RiskEngine()
        limits = RiskLimits(
            allowed_coins=["BTC"],
            max_units_per_order=10.0
        )
        
        result = engine.validate_order(
            coin="BTC",
            quantity=5.0,
            price=50000.0,
            risk_limits=limits
        )
        
        assert result.approved is True
        assert "max_units_per_order" in result.checked_limits
    
    def test_max_notional_inr_enforced(self):
        """Test that max_notional_inr limit is enforced."""
        engine = RiskEngine()
        limits = RiskLimits(
            allowed_coins=["BTC"],
            max_notional_inr=500000.0  # 5 lakh INR
        )
        
        # Should fail: 10 BTC * 60000 = 600000 > 500000
        result = engine.validate_order(
            coin="BTC",
            quantity=10.0,
            price=60000.0,
            risk_limits=limits
        )
        
        assert result.approved is False
        assert "max_notional_inr" in result.reason
        assert "600000" in result.reason
        assert "500000" in result.reason
    
    def test_max_notional_inr_passes_when_under_limit(self):
        """Test that orders under max_notional_inr pass."""
        engine = RiskEngine()
        limits = RiskLimits(
            allowed_coins=["BTC"],
            max_notional_inr=1000000.0  # 10 lakh INR
        )
        
        # Should pass: 5 BTC * 50000 = 250000 < 1000000
        result = engine.validate_order(
            coin="BTC",
            quantity=5.0,
            price=50000.0,
            risk_limits=limits
        )
        
        assert result.approved is True
        assert "max_notional_inr" in result.checked_limits
    
    def test_multiple_limits_all_checked(self):
        """Test that all configured limits are checked."""
        engine = RiskEngine()
        limits = RiskLimits(
            allowed_coins=["BTC", "ETH"],
            max_units_per_order=20.0,
            max_notional_inr=1500000.0
        )
        
        result = engine.validate_order(
            coin="ETH",
            quantity=10.0,
            price=50000.0,  # 500k notional
            risk_limits=limits
        )
        
        assert result.approved is True
        assert "allowed_coins" in result.checked_limits
        assert "max_units_per_order" in result.checked_limits
        assert "max_notional_inr" in result.checked_limits
    
    def test_first_failing_limit_stops_validation(self):
        """Test that validation returns on first failed check."""
        engine = RiskEngine()
        limits = RiskLimits(
            allowed_coins=["BTC"],
            max_units_per_order=5.0,
            max_notional_inr=100000.0
        )
        
        # Violates both limits, but should return coin check failure first
        result = engine.validate_order(
            coin="DOGE",  # Not allowed
            quantity=100.0,  # Exceeds max units
            price=10000.0,  # Exceeds notional
            risk_limits=limits
        )
        
        assert result.approved is False
        assert "not in allowed list" in result.reason
        # Should include the requested coin in checked_limits even though it failed
        assert "requested_coin" in result.checked_limits
    
    def test_validate_coin_allowed_helper(self):
        """Test the quick coin validation helper method."""
        engine = RiskEngine()
        allowed = ["BTC", "ETH", "SOL"]
        
        assert engine.validate_coin_allowed("BTC", allowed) is True
        assert engine.validate_coin_allowed("ETH", allowed) is True
        assert engine.validate_coin_allowed("DOGE", allowed) is False
        assert engine.validate_coin_allowed("XRP", allowed) is False
    
    def test_no_optional_limits_configured(self):
        """Test validation when only required limits (allowed_coins) are set."""
        engine = RiskEngine()
        limits = RiskLimits(allowed_coins=["BTC"])
        
        # Very large order should pass if no limits configured
        result = engine.validate_order(
            coin="BTC",
            quantity=1000.0,
            price=100000.0,  # 100M notional
            risk_limits=limits
        )
        
        assert result.approved is True
        # Only allowed_coins should be in checked limits
        assert "allowed_coins" in result.checked_limits
        assert "max_units_per_order" not in result.checked_limits
        assert "max_notional_inr" not in result.checked_limits
    
    def test_notional_calculation_precision(self):
        """Test that notional value calculation handles decimals correctly."""
        engine = RiskEngine()
        limits = RiskLimits(
            allowed_coins=["ETH"],
            max_notional_inr=250000.0
        )
        
        # 10.5 ETH * 23000 = 241500 (under limit)
        result = engine.validate_order(
            coin="ETH",
            quantity=10.5,
            price=23000.0,
            risk_limits=limits
        )
        
        assert result.approved is True
        
        # 11.0 ETH * 23000 = 253000 (over limit)
        result = engine.validate_order(
            coin="ETH",
            quantity=11.0,
            price=23000.0,
            risk_limits=limits
        )
        
        assert result.approved is False
        assert "253000" in result.reason
