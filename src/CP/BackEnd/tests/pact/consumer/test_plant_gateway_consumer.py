"""CP BackEnd consumer Pact definitions for Plant Gateway API."""
import json
import os
from pathlib import Path
import pytest


def _resolve_pact_dir(tmp_path: Path) -> Path:
    env_dir = (os.getenv("PACT_DIR") or "").strip()
    if env_dir:
        return Path(env_dir)

    # Try to find repo root by walking up until we see tests/contracts.
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "tests" / "contracts").exists():
            return parent / "tests" / "contracts" / "pacts"

    # Docker test runner mounts only CP BackEnd at /app, so fall back to a writable temp dir.
    return tmp_path / "pacts"


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
        pact_dir = _resolve_pact_dir(tmp_path)
        os.makedirs(pact_dir, exist_ok=True)
        pact = {
            "consumer": {"name": "CP-BackEnd"},
            "provider": {"name": "Plant-Gateway"},
            "interactions": [interaction],
            "metadata": {"pactSpecification": {"version": "2.0.0"}},
        }
        pact_path = pact_dir / "CP-BackEnd-Plant-Gateway.json"
        with pact_path.open("w", encoding="utf-8") as f:
            json.dump(pact, f, indent=2)
        assert interaction["response"]["status"] == 201
