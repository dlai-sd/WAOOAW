"""
Mock Feature Flag Service for E2E Testing
"""

from typing import Optional, Dict, Any


class FeatureFlagContext:
    """Mock feature flag context"""
    def __init__(
        self, 
        user_id: str, 
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        trial_mode: bool = False,
        roles: Optional[list] = None,
        gateway_type: str = "CP",
        role: str = "customer"
    ):
        self.user_id = user_id
        self.customer_id = customer_id
        self.email = email
        self.trial_mode = trial_mode
        self.roles = roles or []
        self.gateway_type = gateway_type
        self.role = role


class FeatureFlagService:
    """Mock feature flag service for testing"""
    
    def __init__(self):
        self.flags = {
            "trial_mode_sandbox_routing": True,
            "governor_approval_required": True,
            "budget_enforcement": True,
            "rate_limiting": True,
            "audit_logging": True
        }
    
    def is_enabled(self, flag_name: str, context: Optional[FeatureFlagContext] = None) -> bool:
        """Check if a feature flag is enabled"""
        return self.flags.get(flag_name, False)
    
    def get_variant(self, flag_name: str, context: Optional[FeatureFlagContext] = None) -> str:
        """Get feature flag variant"""
        return "enabled" if self.is_enabled(flag_name, context) else "disabled"
    
    def get_all_flags(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self.flags.copy()
