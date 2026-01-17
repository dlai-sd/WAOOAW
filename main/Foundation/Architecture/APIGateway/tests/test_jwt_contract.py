#!/usr/bin/env python3
"""
JWT Contract Validation Tests
Version: 1.0
Owner: Platform Team
"""

import jwt
import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

# Test secrets (DO NOT use in production)
TEST_JWT_SECRET_CP = "test-secret-cp-12345"
TEST_JWT_SECRET_PP = "test-secret-pp-67890"


class TestJWTContractValidation:
    """Test suite for JWT contract specification compliance."""
    
    def generate_valid_cp_token(self, **overrides) -> str:
        """Generate valid CP JWT token with optional field overrides."""
        now = datetime.utcnow()
        payload = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "customer_id": "cust_test_001",
            "roles": ["customer_user"],
            "governor_agent_id": None,
            "trial_mode": True,
            "trial_expires_at": (now + timedelta(days=7)).isoformat() + "Z",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=24)).timestamp()),
            "iss": "cp.waooaw.com",
            "sub": "550e8400-e29b-41d4-a716-446655440000"
        }
        payload.update(overrides)
        return jwt.encode(payload, TEST_JWT_SECRET_CP, algorithm="HS256")
    
    def generate_valid_pp_token(self, **overrides) -> str:
        """Generate valid PP JWT token with optional field overrides."""
        now = datetime.utcnow()
        payload = {
            "user_id": "admin-001",
            "email": "admin@waooaw.com",
            "customer_id": "internal",
            "roles": ["admin"],
            "governor_agent_id": "gov_agent_supreme",
            "trial_mode": False,
            "trial_expires_at": None,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=24)).timestamp()),
            "iss": "pp.waooaw.com",
            "sub": "admin-001"
        }
        payload.update(overrides)
        return jwt.encode(payload, TEST_JWT_SECRET_PP, algorithm="HS256")
    
    def validate_token(self, token: str, secret: str, issuer: str) -> Dict[str, Any]:
        """Validate JWT token according to contract."""
        try:
            claims = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                issuer=issuer,
                options={
                    "require": ["user_id", "email", "customer_id", "roles", 
                               "iat", "exp", "iss", "sub"],
                    "verify_exp": True,
                    "verify_iat": True
                }
            )
            
            # Additional validation
            if claims["exp"] - claims["iat"] > 86400:
                raise ValueError("Token lifetime exceeds 24 hours")
            
            if claims["trial_mode"] and not claims.get("trial_expires_at"):
                raise ValueError("trial_mode=true requires trial_expires_at")
            
            if not claims["roles"]:
                raise ValueError("roles array cannot be empty")
            
            return claims
        except Exception as e:
            raise ValueError(f"Token validation failed: {str(e)}")
    
    # Test: Valid CP Trial User Token
    def test_valid_cp_trial_token(self):
        """PASS: Valid CP trial user token validates successfully."""
        token = self.generate_valid_cp_token()
        claims = self.validate_token(token, TEST_JWT_SECRET_CP, "cp.waooaw.com")
        
        assert claims["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert claims["email"] == "test@example.com"
        assert claims["trial_mode"] is True
        assert claims["trial_expires_at"] is not None
        assert "customer_user" in claims["roles"]
        print("✅ Valid CP trial token test passed")
    
    # Test: Valid PP Admin Token
    def test_valid_pp_admin_token(self):
        """PASS: Valid PP admin token validates successfully."""
        token = self.generate_valid_pp_token()
        claims = self.validate_token(token, TEST_JWT_SECRET_PP, "pp.waooaw.com")
        
        assert claims["user_id"] == "admin-001"
        assert claims["email"] == "admin@waooaw.com"
        assert claims["trial_mode"] is False
        assert claims["governor_agent_id"] == "gov_agent_supreme"
        assert "admin" in claims["roles"]
        print("✅ Valid PP admin token test passed")
    
    # Test: Expired Token
    def test_expired_token(self):
        """FAIL: Expired token should be rejected."""
        past = datetime.utcnow() - timedelta(days=2)
        token = self.generate_valid_cp_token(
            iat=int(past.timestamp()),
            exp=int((past + timedelta(hours=1)).timestamp())
        )
        
        try:
            self.validate_token(token, TEST_JWT_SECRET_CP, "cp.waooaw.com")
            raise AssertionError("Expected token validation to fail")
        except (jwt.ExpiredSignatureError, ValueError):
            print("✅ Expired token rejection test passed")
    
    # Test: Invalid Issuer
    def test_invalid_issuer(self):
        """FAIL: Token with wrong issuer should be rejected."""
        token = self.generate_valid_cp_token()
        
        with pytest.raises((jwt.InvalidIssuerError, ValueError)):
            self.validate_token(token, TEST_JWT_SECRET_CP, "wrong.waooaw.com")
        print("✅ Invalid issuer rejection test passed")
    
    # Test: Invalid Signature
    def test_invalid_signature(self):
        """FAIL: Token with invalid signature should be rejected."""
        token = self.generate_valid_cp_token()
        
        with pytest.raises((jwt.InvalidSignatureError, ValueError)):
            self.validate_token(token, "wrong-secret", "cp.waooaw.com")
        print("✅ Invalid signature rejection test passed")
    
    # Test: Missing Required Field
    def test_missing_user_id(self):
        """FAIL: Token missing user_id should be rejected."""
        now = datetime.utcnow()
        payload = {
            # "user_id" missing
            "email": "test@example.com",
            "customer_id": "cust_test",
            "roles": ["customer_user"],
            "governor_agent_id": None,
            "trial_mode": False,
            "trial_expires_at": None,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=24)).timestamp()),
            "iss": "cp.waooaw.com",
            "sub": "test-user"
        }
        token = jwt.encode(payload, TEST_JWT_SECRET_CP, algorithm="HS256")
        
        with pytest.raises((jwt.MissingRequiredClaimError, ValueError)):
            self.validate_token(token, TEST_JWT_SECRET_CP, "cp.waooaw.com")
        print("✅ Missing user_id rejection test passed")
    
    # Test: Empty Roles Array
    def test_empty_roles_array(self):
        """FAIL: Token with empty roles array should be rejected."""
        token = self.generate_valid_cp_token(roles=[])
        
        with pytest.raises(ValueError, match="roles array cannot be empty"):
            self.validate_token(token, TEST_JWT_SECRET_CP, "cp.waooaw.com")
        print("✅ Empty roles rejection test passed")
    
    # Test: Trial Mode Without Expiration
    def test_trial_mode_without_expiration(self):
        """FAIL: trial_mode=true without trial_expires_at should be rejected."""
        token = self.generate_valid_cp_token(
            trial_mode=True,
            trial_expires_at=None
        )
        
        with pytest.raises(ValueError, match="trial_mode=true requires trial_expires_at"):
            self.validate_token(token, TEST_JWT_SECRET_CP, "cp.waooaw.com")
        print("✅ Trial mode validation test passed")
    
    # Test: Token Lifetime Exceeds 24 Hours
    def test_token_lifetime_too_long(self):
        """FAIL: Token with lifetime > 24 hours should be rejected."""
        now = datetime.utcnow()
        token = self.generate_valid_cp_token(
            iat=int(now.timestamp()),
            exp=int((now + timedelta(hours=25)).timestamp())
        )
        
        with pytest.raises(ValueError, match="Token lifetime exceeds 24 hours"):
            self.validate_token(token, TEST_JWT_SECRET_CP, "cp.waooaw.com")
        print("✅ Token lifetime validation test passed")
    
    # Test: All PP Roles
    def test_pp_role_hierarchy(self):
        """PASS: All PP roles should be valid."""
        pp_roles = [
            "admin",
            "subscription_manager",
            "agent_orchestrator",
            "infrastructure_engineer",
            "helpdesk_agent",
            "industry_manager",
            "viewer"
        ]
        
        for role in pp_roles:
            token = self.generate_valid_pp_token(roles=[role])
            claims = self.validate_token(token, TEST_JWT_SECRET_PP, "pp.waooaw.com")
            assert role in claims["roles"]
        
        print(f"✅ All {len(pp_roles)} PP roles validated")
    
    # Test: Token Size
    def test_token_size_reasonable(self):
        """PASS: Token size should be under 2KB."""
        token = self.generate_valid_cp_token()
        token_size = len(token.encode('utf-8'))
        
        assert token_size < 2048, f"Token too large: {token_size} bytes"
        print(f"✅ Token size OK: {token_size} bytes")
    
    # Test: Decode and Re-encode
    def test_token_roundtrip(self):
        """PASS: Token should survive decode/re-encode cycle."""
        token1 = self.generate_valid_cp_token()
        claims = self.validate_token(token1, TEST_JWT_SECRET_CP, "cp.waooaw.com")
        
        token2 = jwt.encode(claims, TEST_JWT_SECRET_CP, algorithm="HS256")
        claims2 = self.validate_token(token2, TEST_JWT_SECRET_CP, "cp.waooaw.com")
        
        # iat/exp might differ slightly, compare other fields
        assert claims["user_id"] == claims2["user_id"]
        assert claims["email"] == claims2["email"]
        assert claims["roles"] == claims2["roles"]
        print("✅ Token roundtrip test passed")


def run_all_tests():
    """Run all JWT contract validation tests."""
    suite = TestJWTContractValidation()
    
    print("\n" + "="*60)
    print("JWT CONTRACT VALIDATION TEST SUITE")
    print("="*60 + "\n")
    
    tests = [
        suite.test_valid_cp_trial_token,
        suite.test_valid_pp_admin_token,
        suite.test_expired_token,
        suite.test_invalid_issuer,
        suite.test_invalid_signature,
        suite.test_missing_user_id,
        suite.test_empty_roles_array,
        suite.test_trial_mode_without_expiration,
        suite.test_token_lifetime_too_long,
        suite.test_pp_role_hierarchy,
        suite.test_token_size_reasonable,
        suite.test_token_roundtrip
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
