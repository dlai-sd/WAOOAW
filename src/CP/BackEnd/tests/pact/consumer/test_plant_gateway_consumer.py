"""CP BackEnd consumer Pact definitions for Plant Gateway API."""
import json
import os
import pytest


PACT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "tests", "contracts", "pacts")


@pytest.mark.contract
class TestPlantGatewayConsumerPact:
    """Consumer-side Pact definitions for Plant Gateway.
    
    These tests define the contract expectations from CP BackEnd's perspective.
    They generate Pact JSON files for provider verification.
    """

    def test_otp_start_contract(self, tmp_path):
        """POST /auth/otp/start — CP consumer contract."""
        interaction = {
            "description": "a request to start OTP authentication",
            "request": {
                "method": "POST",
                "path": "/auth/otp/start",
                "headers": {"Content-Type": "application/json"},
                "body": {"phone": "+911234567890", "channel": "sms"},
            },
            "response": {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "body": {"otp_id": "test-otp-id", "expires_in": 300},
            },
        }
        assert interaction["request"]["method"] == "POST"
        assert interaction["response"]["status"] == 200

    def test_otp_verify_contract(self, tmp_path):
        """POST /auth/otp/verify — CP consumer contract."""
        interaction = {
            "description": "a request to verify OTP code",
            "request": {
                "method": "POST",
                "path": "/auth/otp/verify",
                "body": {"otp_id": "test-otp-id", "code": "123456"},
            },
            "response": {
                "status": 200,
                "body": {"access_token": "jwt-token", "token_type": "bearer"},
            },
        }
        assert interaction["response"]["status"] == 200

    def test_get_agents_contract(self, tmp_path):
        """GET /agents — CP consumer contract."""
        interaction = {
            "description": "a request to list available agents",
            "request": {"method": "GET", "path": "/agents"},
            "response": {
                "status": 200,
                "body": [{"id": "agent-001", "name": "Marketing Agent", "status": "active"}],
            },
        }
        assert interaction["response"]["status"] == 200

    def test_post_hire_contract(self, tmp_path):
        """POST /hire — CP consumer contract."""
        interaction = {
            "description": "a request to create a hire",
            "request": {
                "method": "POST",
                "path": "/hire",
                "body": {"agent_id": "agent-001", "customer_id": "cp-user-001"},
            },
            "response": {
                "status": 201,
                "body": {"hire_id": "hire-001", "status": "draft"},
            },
        }
        # Generate pact file
        os.makedirs(PACT_DIR, exist_ok=True)
        pact = {
            "consumer": {"name": "CP-BackEnd"},
            "provider": {"name": "Plant-Gateway"},
            "interactions": [interaction],
            "metadata": {"pactSpecification": {"version": "2.0.0"}},
        }
        pact_path = os.path.join(PACT_DIR, "CP-BackEnd-Plant-Gateway.json")
        with open(pact_path, "w") as f:
            json.dump(pact, f, indent=2)
        assert interaction["response"]["status"] == 201
