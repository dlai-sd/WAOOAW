"""
Feature Flag Management for WAOOAW Gateway
Version: 1.0
Purpose: LaunchDarkly integration for runtime feature toggles

Flags:
- enable_trial_mode: Enable/disable trial user restrictions (L0-02)
- enable_governor_approval: Enable/disable Governor approval workflow (L0-01)
- enable_budget_enforcement: Enable/disable budget caps (L0-03)
- enable_sandbox_routing: Enable/disable trial sandbox routing (L0-04)
- enable_rbac_pp: Enable/disable Partner Platform RBAC (L0-05)
- enable_audit_logging: Enable/disable audit log writes
- enable_opa_caching: Enable/disable OPA decision caching
- budget_alert_threshold_warning: Budget utilization % for warning alerts (default: 80)
- budget_alert_threshold_high: Budget utilization % for high alerts (default: 95)
- budget_alert_threshold_critical: Budget utilization % for critical alerts (default: 100)

Usage:
    from infrastructure.feature_flags import feature_flags, FeatureFlagContext
    
    # Check if feature is enabled
    context = FeatureFlagContext(user_id="user-123", customer_id="cust-456", trial_mode=True)
    if feature_flags.is_enabled("enable_trial_mode", context):
        # Apply trial restrictions
        pass
    
    # Get numeric variation
    threshold = feature_flags.get_variation("budget_alert_threshold_warning", context, default=80)
"""

import os
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass
import ldclient
from ldclient import Context
from ldclient.config import Config

logger = logging.getLogger(__name__)

# LaunchDarkly SDK key (from environment or Secret Manager)
LD_SDK_KEY = os.environ.get("LAUNCHDARKLY_SDK_KEY")

# Default flag values (used when LaunchDarkly is unavailable)
DEFAULT_FLAGS = {
    "enable_trial_mode": True,
    "enable_governor_approval": True,
    "enable_budget_enforcement": True,
    "enable_sandbox_routing": True,
    "enable_rbac_pp": True,
    "enable_audit_logging": True,
    "enable_opa_caching": True,
    "budget_alert_threshold_warning": 80,
    "budget_alert_threshold_high": 95,
    "budget_alert_threshold_critical": 100,
}


@dataclass
class FeatureFlagContext:
    """
    Context for feature flag evaluation.
    
    Attributes:
        user_id: User ID (required)
        customer_id: Customer ID (optional, for customer-specific flags)
        email: User email (optional, for targeting by email)
        trial_mode: Whether user is in trial mode (optional)
        roles: User roles (optional, for role-based flags)
        gateway_type: "CP" or "PP" (optional, for gateway-specific flags)
        environment: "dev", "staging", "prod" (from env var)
        custom_attrs: Additional custom attributes for targeting
    """
    user_id: str
    customer_id: Optional[str] = None
    email: Optional[str] = None
    trial_mode: Optional[bool] = None
    roles: Optional[list] = None
    gateway_type: Optional[str] = None
    environment: Optional[str] = None
    custom_attrs: Optional[Dict[str, Any]] = None
    
    def to_ld_context(self) -> Context:
        """
        Convert to LaunchDarkly Context object.
        
        Returns:
            LaunchDarkly Context for evaluation
        """
        # Primary user context
        user_builder = Context.builder(self.user_id)
        user_builder.kind("user")
        user_builder.name(self.email or self.user_id)
        
        if self.email:
            user_builder.set("email", self.email)
        if self.trial_mode is not None:
            user_builder.set("trial_mode", self.trial_mode)
        if self.roles:
            user_builder.set("roles", self.roles)
        if self.gateway_type:
            user_builder.set("gateway_type", self.gateway_type)
        if self.environment:
            user_builder.set("environment", self.environment)
        
        # Add custom attributes
        if self.custom_attrs:
            for key, value in self.custom_attrs.items():
                user_builder.set(key, value)
        
        # Multi-context with user and customer (if provided)
        if self.customer_id:
            customer_builder = Context.builder(self.customer_id)
            customer_builder.kind("customer")
            return Context.multi_builder().add(user_builder.build()).add(customer_builder.build()).build()
        
        return user_builder.build()


class FeatureFlagService:
    """
    Feature flag service using LaunchDarkly.
    
    Provides:
    - Boolean flag evaluation (is_enabled)
    - Numeric/string variation (get_variation)
    - Graceful degradation (fallback to defaults if LD unavailable)
    - Caching for performance
    """
    
    def __init__(self, sdk_key: Optional[str] = None):
        """
        Initialize LaunchDarkly client.
        
        Args:
            sdk_key: LaunchDarkly SDK key (defaults to LD_SDK_KEY env var)
        """
        self.sdk_key = sdk_key or LD_SDK_KEY
        self.client: Optional[ldclient.LDClient] = None
        self.is_available = False
        
        if self.sdk_key:
            try:
                config = Config(
                    sdk_key=self.sdk_key,
                    stream=True,  # Use streaming for real-time updates
                    events_enabled=True,  # Send analytics events
                    diagnostic_opt_out=False,  # Enable diagnostics
                )
                self.client = ldclient.LDClient(config=config)
                
                # Wait for initialization (up to 5 seconds)
                if self.client.is_initialized():
                    self.is_available = True
                    logger.info("LaunchDarkly client initialized successfully")
                else:
                    logger.warning("LaunchDarkly client initialization timeout, using defaults")
            except Exception as e:
                logger.error(f"Failed to initialize LaunchDarkly client: {e}")
        else:
            logger.warning("LaunchDarkly SDK key not provided, using default flags")
    
    def is_enabled(
        self,
        flag_key: str,
        context: FeatureFlagContext,
        default: bool = False
    ) -> bool:
        """
        Check if boolean feature flag is enabled.
        
        Args:
            flag_key: Feature flag key (e.g., "enable_trial_mode")
            context: Evaluation context (user, customer, etc.)
            default: Default value if flag not found or LD unavailable
        
        Returns:
            True if enabled, False otherwise
        """
        if not self.is_available or not self.client:
            # Fallback to defaults
            return DEFAULT_FLAGS.get(flag_key, default)
        
        try:
            ld_context = context.to_ld_context()
            result = self.client.variation(flag_key, ld_context, default)
            logger.debug(f"Flag {flag_key} evaluated to {result} for user {context.user_id}")
            return result
        except Exception as e:
            logger.error(f"Error evaluating flag {flag_key}: {e}")
            return DEFAULT_FLAGS.get(flag_key, default)
    
    def get_variation(
        self,
        flag_key: str,
        context: FeatureFlagContext,
        default: Any = None
    ) -> Any:
        """
        Get feature flag variation (string, number, JSON).
        
        Args:
            flag_key: Feature flag key
            context: Evaluation context
            default: Default value if flag not found or LD unavailable
        
        Returns:
            Flag value (string, number, dict, etc.)
        """
        if not self.is_available or not self.client:
            return DEFAULT_FLAGS.get(flag_key, default)
        
        try:
            ld_context = context.to_ld_context()
            result = self.client.variation(flag_key, ld_context, default)
            logger.debug(f"Flag {flag_key} variation: {result} for user {context.user_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting variation for flag {flag_key}: {e}")
            return DEFAULT_FLAGS.get(flag_key, default)
    
    def get_all_flags(self, context: FeatureFlagContext) -> Dict[str, Any]:
        """
        Get all flag values for a context.
        
        Args:
            context: Evaluation context
        
        Returns:
            Dictionary of {flag_key: value}
        """
        if not self.is_available or not self.client:
            return DEFAULT_FLAGS.copy()
        
        try:
            ld_context = context.to_ld_context()
            return self.client.all_flags_state(ld_context).to_json_dict()
        except Exception as e:
            logger.error(f"Error getting all flags: {e}")
            return DEFAULT_FLAGS.copy()
    
    def close(self):
        """Close LaunchDarkly client (for cleanup)."""
        if self.client:
            self.client.close()
            logger.info("LaunchDarkly client closed")


# Global singleton instance
feature_flags = FeatureFlagService()


# Helper functions for common flags

def is_trial_mode_enabled(context: FeatureFlagContext) -> bool:
    """Check if trial mode restrictions are enabled."""
    return feature_flags.is_enabled("enable_trial_mode", context, default=True)


def is_governor_approval_enabled(context: FeatureFlagContext) -> bool:
    """Check if Governor approval workflow is enabled."""
    return feature_flags.is_enabled("enable_governor_approval", context, default=True)


def is_budget_enforcement_enabled(context: FeatureFlagContext) -> bool:
    """Check if budget caps are enforced."""
    return feature_flags.is_enabled("enable_budget_enforcement", context, default=True)


def is_sandbox_routing_enabled(context: FeatureFlagContext) -> bool:
    """Check if trial users should be routed to sandbox."""
    return feature_flags.is_enabled("enable_sandbox_routing", context, default=True)


def is_rbac_pp_enabled(context: FeatureFlagContext) -> bool:
    """Check if Partner Platform RBAC is enabled."""
    return feature_flags.is_enabled("enable_rbac_pp", context, default=True)


def get_budget_thresholds(context: FeatureFlagContext) -> Dict[str, float]:
    """
    Get budget alert thresholds.
    
    Returns:
        {
            "warning": 80.0,
            "high": 95.0,
            "critical": 100.0
        }
    """
    return {
        "warning": feature_flags.get_variation("budget_alert_threshold_warning", context, 80),
        "high": feature_flags.get_variation("budget_alert_threshold_high", context, 95),
        "critical": feature_flags.get_variation("budget_alert_threshold_critical", context, 100),
    }


# Example usage in middleware
"""
from infrastructure.feature_flags import feature_flags, FeatureFlagContext

# In middleware
async def policy_middleware(request: Request, call_next):
    # Extract user context from JWT
    jwt = request.state.jwt
    context = FeatureFlagContext(
        user_id=jwt["user_id"],
        customer_id=jwt.get("customer_id"),
        email=jwt.get("email"),
        trial_mode=jwt.get("trial_mode", False),
        roles=jwt.get("roles", []),
        gateway_type="CP",  # or "PP"
        environment=os.environ.get("ENVIRONMENT", "prod")
    )
    
    # Check if trial mode enforcement is enabled
    if is_trial_mode_enabled(context) and jwt.get("trial_mode"):
        # Query OPA for trial restrictions
        opa_result = await query_opa_policy("trial_mode", request_input)
        if not opa_result["allow"]:
            return JSONResponse(
                status_code=429,
                content={"error": opa_result["deny_reason"]}
            )
    
    # Check budget enforcement
    if is_budget_enforcement_enabled(context):
        thresholds = get_budget_thresholds(context)
        # Use thresholds for alerts
        pass
    
    response = await call_next(request)
    return response
"""
