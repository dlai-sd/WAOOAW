"""
CP BackEnd consumer Pact definitions for Plant Gateway interactions.

Defines the contract interactions that CP BackEnd expects from Plant Gateway.
Pact files are written to tests/contracts/pacts/.
"""
import os
from pathlib import Path

import pytest

try:
    from pact import Consumer, Provider
    PACT_AVAILABLE = True
except ImportError:
    PACT_AVAILABLE = False

PACT_DIR = str(Path(__file__).resolve().parents[7] / "tests" / "contracts" / "pacts")
os.makedirs(PACT_DIR, exist_ok=True)

CONSUMER_NAME = "cp-backend"
PROVIDER_NAME = "plant-gateway"
MOCK_HOST = "localhost"
MOCK_PORT = 1234


@pytest.fixture(scope="module")
def pact():
    if not PACT_AVAILABLE:
        pytest.skip("pact-python not installed")
    _pact = Consumer(CONSUMER_NAME).has_pact_with(
        Provider(PROVIDER_NAME),
        host_name=MOCK_HOST,
        port=MOCK_PORT,
        pact_dir=PACT_DIR,
    )
    _pact.start_service()
    yield _pact
    _pact.stop_service()


@pytest.mark.contract
def test_otp_start(pact):
    """POST /auth/otp/start — request OTP for a phone number."""
    (
        pact
        .upon_receiving("a request to start OTP for a phone number")
        .with_request(
            method="POST",
            path="/auth/otp/start",
            headers={"Content-Type": "application/json"},
            body={"phone": "+919876543210"},
        )
        .will_respond_with(
            status=200,
            headers={"Content-Type": "application/json"},
            body={"message": "OTP sent", "otp_id": "otp-mock-001"},
        )
    )

    import requests
    with pact:
        response = requests.post(
            f"http://{MOCK_HOST}:{MOCK_PORT}/auth/otp/start",
            json={"phone": "+919876543210"},
        )
    assert response.status_code == 200


@pytest.mark.contract
def test_otp_verify(pact):
    """POST /auth/otp/verify — verify OTP and receive tokens."""
    (
        pact
        .upon_receiving("a request to verify an OTP")
        .with_request(
            method="POST",
            path="/auth/otp/verify",
            headers={"Content-Type": "application/json"},
            body={"phone": "+919876543210", "otp": "123456", "otp_id": "otp-mock-001"},
        )
        .will_respond_with(
            status=200,
            headers={"Content-Type": "application/json"},
            body={
                "access_token": "mock-access-token",
                "refresh_token": "mock-refresh-token",
                "token_type": "bearer",
            },
        )
    )

    import requests
    with pact:
        response = requests.post(
            f"http://{MOCK_HOST}:{MOCK_PORT}/auth/otp/verify",
            json={"phone": "+919876543210", "otp": "123456", "otp_id": "otp-mock-001"},
        )
    assert response.status_code == 200


@pytest.mark.contract
def test_get_agents(pact):
    """GET /agents — browse available agents."""
    (
        pact
        .upon_receiving("a request to list agents")
        .with_request(
            method="GET",
            path="/agents",
        )
        .will_respond_with(
            status=200,
            headers={"Content-Type": "application/json"},
            body=[
                {
                    "id": "agent-001",
                    "name": "Marketing Expert",
                    "status": "available",
                    "specialty": "content-marketing",
                }
            ],
        )
    )

    import requests
    with pact:
        response = requests.get(f"http://{MOCK_HOST}:{MOCK_PORT}/agents")
    assert response.status_code == 200


@pytest.mark.contract
def test_post_hire(pact):
    """POST /hire — create a hire request."""
    (
        pact
        .upon_receiving("a request to create a hire")
        .with_request(
            method="POST",
            path="/hire",
            headers={"Content-Type": "application/json"},
            body={"agent_id": "agent-001", "customer_id": "cust-001"},
        )
        .will_respond_with(
            status=201,
            headers={"Content-Type": "application/json"},
            body={"hire_id": "hire-mock-001", "status": "draft"},
        )
    )

    import requests
    with pact:
        response = requests.post(
            f"http://{MOCK_HOST}:{MOCK_PORT}/hire",
            json={"agent_id": "agent-001", "customer_id": "cust-001"},
        )
    assert response.status_code == 201
