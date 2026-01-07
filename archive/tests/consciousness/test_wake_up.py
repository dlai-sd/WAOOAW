"""
Tests for Wake-up Protocols

Story 1: Wake-up Protocols (Epic 2.4)
Coverage target: >95%

Tests verify:
1. Complete wake-up sequence (identity → attestation → session → conscious)
2. Identity verification (DID resolution, credential validation, key status)
3. Attestation generation (runtime manifest, fresh signatures)
4. Session establishment (capabilities, secure state)
5. Error handling (invalid identity, failed attestation, session errors)
6. State transitions (dormant → verifying → attesting → establishing → conscious)
7. Sleep/wake cycles (graceful shutdown, re-awakening)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from waooaw.consciousness.wake_up import (
    WakeUpProtocol,
    WakeUpState,
    IdentityVerificationError,
    SessionEstablishmentError,
)


@pytest.fixture
def agent_did():
    """Test agent DID"""
    return "did:waooaw:agent:test-agent"


@pytest.fixture
def mock_did_service():
    """Mock DID service"""
    service = AsyncMock()
    service.resolve_did = AsyncMock(
        return_value={
            "id": "did:waooaw:agent:test-agent",
            "verificationMethod": [
                {
                    "id": "did:waooaw:agent:test-agent#key-1",
                    "type": "Ed25519VerificationKey2020",
                    "controller": "did:waooaw:agent:test-agent",
                    "publicKeyMultibase": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
                }
            ],
        }
    )
    return service


@pytest.fixture
def mock_vc_issuer():
    """Mock VC issuer"""
    issuer = AsyncMock()
    issuer.verify_credential = AsyncMock(return_value=True)
    return issuer


@pytest.fixture
def mock_attestation_engine():
    """Mock attestation engine"""
    engine = AsyncMock()
    engine.create_attestation = AsyncMock(
        return_value={
            "id": "attestation-123",
            "agent_did": "did:waooaw:agent:test-agent",
            "runtime_type": "kubernetes",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signature": "mock-signature",
        }
    )
    return engine


@pytest.fixture
def mock_rotation_manager():
    """Mock key rotation manager"""
    manager = AsyncMock()
    manager.check_rotation_needed = AsyncMock(return_value=False)
    return manager


@pytest.fixture
def wake_up_protocol(
    agent_did,
    mock_did_service,
    mock_vc_issuer,
    mock_attestation_engine,
    mock_rotation_manager,
):
    """Wake-up protocol with mocked dependencies"""
    return WakeUpProtocol(
        agent_did=agent_did,
        runtime_type="kubernetes",
        did_service=mock_did_service,
        vc_issuer=mock_vc_issuer,
        attestation_engine=mock_attestation_engine,
        rotation_manager=mock_rotation_manager,
    )


class TestWakeUpSequence:
    """Tests for complete wake-up sequence"""

    @pytest.mark.asyncio
    async def test_successful_wake_up(self, wake_up_protocol):
        """Test complete successful wake-up sequence"""
        # Execute wake-up
        session = await wake_up_protocol.wake_up()

        # Verify session
        assert session["agent_did"] == "did:waooaw:agent:test-agent"
        assert session["runtime_type"] == "kubernetes"
        assert session["conscious"] is True
        assert "attestation" in session
        assert "capabilities" in session
        assert len(session["capabilities"]) > 0

        # Verify state
        assert wake_up_protocol.state == WakeUpState.CONSCIOUS
        assert wake_up_protocol.is_conscious()
        assert wake_up_protocol.get_session() == session

    @pytest.mark.asyncio
    async def test_wake_up_state_transitions(self, wake_up_protocol):
        """Test state transitions during wake-up"""
        # Initial state
        assert wake_up_protocol.state == WakeUpState.DORMANT

        # Mock to track state changes
        states_seen = []

        original_verify = wake_up_protocol._verify_identity
        original_generate = wake_up_protocol._generate_attestation
        original_establish = wake_up_protocol._establish_session

        async def track_verify(*args, **kwargs):
            states_seen.append(wake_up_protocol.state)
            return await original_verify(*args, **kwargs)

        async def track_generate(*args, **kwargs):
            states_seen.append(wake_up_protocol.state)
            return await original_generate(*args, **kwargs)

        async def track_establish(*args, **kwargs):
            states_seen.append(wake_up_protocol.state)
            return await original_establish(*args, **kwargs)

        wake_up_protocol._verify_identity = track_verify
        wake_up_protocol._generate_attestation = track_generate
        wake_up_protocol._establish_session = track_establish

        # Execute wake-up
        await wake_up_protocol.wake_up()

        # Verify state sequence
        assert WakeUpState.VERIFYING in states_seen
        assert WakeUpState.ATTESTING in states_seen
        assert WakeUpState.ESTABLISHING in states_seen
        assert wake_up_protocol.state == WakeUpState.CONSCIOUS

    @pytest.mark.asyncio
    async def test_wake_up_with_multiple_capabilities(self, wake_up_protocol):
        """Test wake-up with multiple credentials and capabilities"""
        # Mock multiple credentials
        wake_up_protocol._load_agent_credentials = AsyncMock(
            return_value=[
                {
                    "id": "cred-1",
                    "credentialSubject": {
                        "capabilities": [
                            {"action": "read", "resource": "/data/*"},
                            {"action": "write", "resource": "/data/*"},
                        ]
                    },
                },
                {
                    "id": "cred-2",
                    "credentialSubject": {
                        "capabilities": [{"action": "execute", "resource": "/jobs/*"}]
                    },
                },
            ]
        )

        session = await wake_up_protocol.wake_up()

        # Verify all capabilities loaded
        assert len(session["capabilities"]) == 3
        assert session["credentials"] == 2


class TestIdentityVerification:
    """Tests for identity verification phase"""

    @pytest.mark.asyncio
    async def test_verify_identity_success(self, wake_up_protocol):
        """Test successful identity verification"""
        is_valid = await wake_up_protocol._verify_identity()

        assert is_valid is True
        assert len(wake_up_protocol.verification_errors) == 0

        # Verify DID resolved
        wake_up_protocol.did_service.resolve_did.assert_called_once()

        # Verify credentials verified
        wake_up_protocol.vc_issuer.verify_credential.assert_called()

    @pytest.mark.asyncio
    async def test_verify_identity_did_not_found(self, wake_up_protocol):
        """Test identity verification with missing DID"""
        wake_up_protocol.did_service.resolve_did = AsyncMock(return_value=None)

        is_valid = await wake_up_protocol._verify_identity()

        assert is_valid is False
        assert "DID not found" in wake_up_protocol.verification_errors

    @pytest.mark.asyncio
    async def test_verify_identity_no_credentials(self, wake_up_protocol):
        """Test identity verification with no credentials"""
        wake_up_protocol._load_agent_credentials = AsyncMock(return_value=[])

        is_valid = await wake_up_protocol._verify_identity()

        assert is_valid is False
        assert "No credentials found" in wake_up_protocol.verification_errors

    @pytest.mark.asyncio
    async def test_verify_identity_invalid_credential(self, wake_up_protocol):
        """Test identity verification with invalid credential"""
        wake_up_protocol.vc_issuer.verify_credential = AsyncMock(return_value=False)

        is_valid = await wake_up_protocol._verify_identity()

        assert is_valid is False
        assert any("Invalid credentials" in err for err in wake_up_protocol.verification_errors)

    @pytest.mark.asyncio
    async def test_verify_identity_rotation_needed_warning(self, wake_up_protocol):
        """Test identity verification with rotation needed (warning, not failure)"""
        wake_up_protocol.rotation_manager.check_rotation_needed = AsyncMock(return_value=True)

        is_valid = await wake_up_protocol._verify_identity()

        # Should still succeed (rotation is a warning, not a failure)
        assert is_valid is True


class TestAttestationGeneration:
    """Tests for attestation generation phase"""

    @pytest.mark.asyncio
    async def test_generate_attestation_success(self, wake_up_protocol):
        """Test successful attestation generation"""
        attestation = await wake_up_protocol._generate_attestation()

        assert attestation["id"] == "attestation-123"
        assert attestation["agent_did"] == "did:waooaw:agent:test-agent"
        assert attestation["runtime_type"] == "kubernetes"
        assert "signature" in attestation

        # Verify engine called
        wake_up_protocol.attestation_engine.create_attestation.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_attestation_failure(self, wake_up_protocol):
        """Test attestation generation failure"""
        wake_up_protocol.attestation_engine.create_attestation = AsyncMock(
            side_effect=Exception("Attestation failed")
        )

        with pytest.raises(SessionEstablishmentError) as exc_info:
            await wake_up_protocol._generate_attestation()

        assert "Attestation generation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch.dict("os.environ", {"HOSTNAME": "test-pod", "POD_NAMESPACE": "production"})
    async def test_collect_runtime_manifest_kubernetes(self, wake_up_protocol):
        """Test runtime manifest collection in Kubernetes"""
        manifest = await wake_up_protocol._collect_runtime_manifest()

        assert manifest["runtime_type"] == "kubernetes"
        assert manifest["pod_name"] == "test-pod"
        assert manifest["namespace"] == "production"

    @pytest.mark.asyncio
    async def test_collect_runtime_manifest_serverless(self, agent_did):
        """Test runtime manifest collection in serverless"""
        protocol = WakeUpProtocol(agent_did=agent_did, runtime_type="serverless")

        with patch.dict(
            "os.environ",
            {
                "AWS_LAMBDA_FUNCTION_NAME": "test-function",
                "AWS_LAMBDA_FUNCTION_VERSION": "1",
            },
        ):
            manifest = await protocol._collect_runtime_manifest()

        assert manifest["runtime_type"] == "serverless"
        assert manifest["function_name"] == "test-function"


class TestSessionEstablishment:
    """Tests for session establishment phase"""

    @pytest.mark.asyncio
    async def test_establish_session_success(self, wake_up_protocol):
        """Test successful session establishment"""
        attestation = {
            "id": "attestation-123",
            "signature": "mock-sig",
        }

        session = await wake_up_protocol._establish_session(attestation)

        assert session["agent_did"] == "did:waooaw:agent:test-agent"
        assert session["runtime_type"] == "kubernetes"
        assert session["attestation"] == attestation
        assert session["conscious"] is True
        assert "session_id" in session
        assert "capabilities" in session
        assert "wake_up_timestamp" in session

    @pytest.mark.asyncio
    async def test_establish_session_loads_capabilities(self, wake_up_protocol):
        """Test session establishment loads all capabilities"""
        attestation = {"id": "attestation-123"}

        session = await wake_up_protocol._establish_session(attestation)

        # Verify capabilities extracted from credentials
        assert len(session["capabilities"]) > 0
        assert session["credentials"] == 1


class TestErrorHandling:
    """Tests for error handling during wake-up"""

    @pytest.mark.asyncio
    async def test_wake_up_identity_verification_failure(self, wake_up_protocol):
        """Test wake-up failure during identity verification"""
        wake_up_protocol.did_service.resolve_did = AsyncMock(return_value=None)

        with pytest.raises(IdentityVerificationError) as exc_info:
            await wake_up_protocol.wake_up()

        assert "Identity verification failed" in str(exc_info.value)
        assert wake_up_protocol.state == WakeUpState.FAILED

    @pytest.mark.asyncio
    async def test_wake_up_attestation_failure(self, wake_up_protocol):
        """Test wake-up failure during attestation"""
        wake_up_protocol.attestation_engine.create_attestation = AsyncMock(
            side_effect=Exception("Attestation error")
        )

        with pytest.raises(SessionEstablishmentError):
            await wake_up_protocol.wake_up()

        assert wake_up_protocol.state == WakeUpState.FAILED

    @pytest.mark.asyncio
    async def test_wake_up_session_establishment_failure(self, wake_up_protocol):
        """Test wake-up failure during session establishment"""
        wake_up_protocol._load_agent_credentials = AsyncMock(
            side_effect=Exception("Credential error")
        )

        with pytest.raises(Exception):
            await wake_up_protocol.wake_up()

        assert wake_up_protocol.state == WakeUpState.FAILED


class TestSleepCycle:
    """Tests for sleep/wake cycles"""

    @pytest.mark.asyncio
    async def test_sleep_from_conscious_state(self, wake_up_protocol):
        """Test putting conscious agent to sleep"""
        # Wake up first
        session = await wake_up_protocol.wake_up()
        assert wake_up_protocol.is_conscious()

        # Sleep
        await wake_up_protocol.sleep()

        # Verify dormant
        assert wake_up_protocol.state == WakeUpState.DORMANT
        assert not wake_up_protocol.is_conscious()
        assert wake_up_protocol.get_session() is None

    @pytest.mark.asyncio
    async def test_sleep_wake_cycle(self, wake_up_protocol):
        """Test complete sleep/wake cycle"""
        # First wake
        session1 = await wake_up_protocol.wake_up()
        session1_id = session1["session_id"]

        # Sleep
        await wake_up_protocol.sleep()

        # Wake again
        session2 = await wake_up_protocol.wake_up()
        session2_id = session2["session_id"]

        # Verify new session created
        assert session1_id != session2_id
        assert wake_up_protocol.is_conscious()


class TestStateQueries:
    """Tests for state query methods"""

    @pytest.mark.asyncio
    async def test_is_conscious_before_wake(self, wake_up_protocol):
        """Test is_conscious before wake-up"""
        assert not wake_up_protocol.is_conscious()

    @pytest.mark.asyncio
    async def test_is_conscious_after_wake(self, wake_up_protocol):
        """Test is_conscious after wake-up"""
        await wake_up_protocol.wake_up()
        assert wake_up_protocol.is_conscious()

    @pytest.mark.asyncio
    async def test_get_session_before_wake(self, wake_up_protocol):
        """Test get_session before wake-up"""
        assert wake_up_protocol.get_session() is None

    @pytest.mark.asyncio
    async def test_get_session_after_wake(self, wake_up_protocol):
        """Test get_session after wake-up"""
        session = await wake_up_protocol.wake_up()
        assert wake_up_protocol.get_session() == session
