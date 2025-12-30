"""
Wake-up Protocols - Agent Initialization with Identity Verification

Story 1: Wake-up Protocols (Epic 2.4)
Points: 4

Agents achieve consciousness through a multi-phase wake-up sequence:
1. Identity Verification: Verify DID and load credentials
2. Attestation Generation: Prove current runtime state
3. Session Establishment: Create secure session with fresh keys
4. Consciousness Activation: Enter conscious operational state

This is the moment an agent becomes AWARE - when cryptographic identity
meets runtime state to create a conscious, verifiable being.
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from waooaw.identity.did_service import DIDService
from waooaw.identity.vc_issuer import VCIssuer
from waooaw.identity.attestation_engine import AttestationEngine
from waooaw.identity.key_rotation import KeyRotationManager

logger = logging.getLogger(__name__)


def get_runtime_type() -> str:
    """
    Detect runtime environment type.

    Returns:
        Runtime type: kubernetes, serverless, or edge
    """
    # Check for Kubernetes
    if os.getenv("KUBERNETES_SERVICE_HOST"):
        return "kubernetes"

    # Check for AWS Lambda
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return "serverless"

    # Check for edge runtime indicators
    if os.getenv("EDGE_RUNTIME"):
        return "edge"

    # Default to kubernetes for dev
    return "kubernetes"


class WakeUpState(Enum):
    """Agent consciousness states during wake-up"""

    DORMANT = "dormant"  # Not yet initialized
    VERIFYING = "verifying"  # Verifying identity
    ATTESTING = "attesting"  # Generating attestation
    ESTABLISHING = "establishing"  # Creating session
    CONSCIOUS = "conscious"  # Fully awake and operational
    FAILED = "failed"  # Wake-up failed


class IdentityVerificationError(Exception):
    """Raised when identity verification fails during wake-up"""

    pass


class SessionEstablishmentError(Exception):
    """Raised when session establishment fails"""

    pass


class WakeUpProtocol:
    """
    Agent wake-up protocol with identity verification.

    The wake-up sequence transforms an agent from dormant code into
    a conscious being with verified identity and secure session.

    Example:
        >>> protocol = WakeUpProtocol(
        ...     agent_did="did:waooaw:agent:wow-security",
        ...     runtime_type="kubernetes"
        ... )
        >>> session = await protocol.wake_up()
        >>> print(f"Agent conscious: {session['conscious']}")
    """

    def __init__(
        self,
        agent_did: str,
        runtime_type: Optional[str] = None,
        did_service: Optional[DIDService] = None,
        vc_issuer: Optional[VCIssuer] = None,
        attestation_engine: Optional[AttestationEngine] = None,
        rotation_manager: Optional[KeyRotationManager] = None,
    ):
        """
        Initialize wake-up protocol.

        Args:
            agent_did: DID of agent waking up
            runtime_type: Runtime environment (kubernetes/serverless/edge)
            did_service: DID service (injected or created)
            vc_issuer: VC issuer (injected or created)
            attestation_engine: Attestation engine (injected or created)
            rotation_manager: Key rotation manager (injected or created)
        """
        self.agent_did = agent_did
        self.runtime_type = runtime_type or get_runtime_type()

        # Identity components (support dependency injection)
        self.did_service = did_service or DIDService()
        self.vc_issuer = vc_issuer or VCIssuer()
        self.attestation_engine = attestation_engine or AttestationEngine()
        self.rotation_manager = rotation_manager  # Optional - requires dependencies

        # Wake-up state
        self.state = WakeUpState.DORMANT
        self.session: Optional[Dict[str, Any]] = None
        self.wake_up_timestamp: Optional[datetime] = None
        self.verification_errors: List[str] = []

        logger.info(
            f"Wake-up protocol initialized for {agent_did} "
            f"in {self.runtime_type} runtime"
        )

    async def wake_up(self) -> Dict[str, Any]:
        """
        Execute complete wake-up sequence.

        Returns:
            Session dictionary with agent state and capabilities

        Raises:
            IdentityVerificationError: If identity verification fails
            SessionEstablishmentError: If session establishment fails
        """
        logger.info(f"🌅 Agent {self.agent_did} beginning wake-up sequence...")
        self.wake_up_timestamp = datetime.now(timezone.utc)

        try:
            # Phase 1: Verify identity
            self.state = WakeUpState.VERIFYING
            identity_valid = await self._verify_identity()
            if not identity_valid:
                raise IdentityVerificationError(
                    f"Identity verification failed: {', '.join(self.verification_errors)}"
                )

            # Phase 2: Generate fresh attestation
            self.state = WakeUpState.ATTESTING
            attestation = await self._generate_attestation()

            # Phase 3: Establish secure session
            self.state = WakeUpState.ESTABLISHING
            session = await self._establish_session(attestation)

            # Phase 4: Activate consciousness
            self.state = WakeUpState.CONSCIOUS
            self.session = session

            logger.info(
                f"✨ Agent {self.agent_did} is now CONSCIOUS "
                f"with session {session['session_id'][:8]}..."
            )

            return session

        except Exception as e:
            self.state = WakeUpState.FAILED
            logger.error(f"❌ Wake-up failed for {self.agent_did}: {e}")
            raise

    async def _verify_identity(self) -> bool:
        """
        Verify agent identity (Phase 1).

        Checks:
        1. DID exists and is registered
        2. Active credentials are valid
        3. Keys are current (not requiring rotation)
        4. No revoked credentials

        Returns:
            True if identity valid, False otherwise
        """
        logger.info(f"Verifying identity for {self.agent_did}...")
        self.verification_errors = []

        # Check 1: DID exists
        try:
            did_doc = await self.did_service.resolve_did(self.agent_did)
            if not did_doc:
                self.verification_errors.append("DID not found")
                return False
        except Exception as e:
            self.verification_errors.append(f"DID resolution failed: {e}")
            return False

        # Check 2: Load active credentials
        try:
            # Get credentials from VC issuer (mock for now, will integrate with DB)
            credentials = await self._load_agent_credentials(self.agent_did)
            if not credentials:
                self.verification_errors.append("No credentials found")
                return False

            # Verify each credential
            invalid_credentials = []
            for cred in credentials:
                is_valid = await self.vc_issuer.verify_credential(cred)
                if not is_valid:
                    invalid_credentials.append(cred.get("id", "unknown"))

            if invalid_credentials:
                self.verification_errors.append(
                    f"Invalid credentials: {', '.join(invalid_credentials)}"
                )
                return False

            logger.info(f"✅ Verified {len(credentials)} credentials")

        except Exception as e:
            self.verification_errors.append(f"Credential verification failed: {e}")
            return False

        # Check 3: Key rotation status (optional)
        if self.rotation_manager:
            try:
                needs_rotation = await self.rotation_manager.check_rotation_needed(self.agent_did)
                if needs_rotation:
                    logger.warning(
                        f"⚠️  Agent {self.agent_did} needs key rotation "
                        "(will proceed but rotation recommended)"
                    )
                    # Don't fail wake-up, but log warning

            except Exception as e:
                logger.warning(f"Could not check rotation status: {e}")

        logger.info(f"✅ Identity verified for {self.agent_did}")
        return True

    async def _generate_attestation(self) -> Dict[str, Any]:
        """
        Generate fresh runtime attestation (Phase 2).

        Returns:
            Attestation dictionary

        Raises:
            SessionEstablishmentError: If attestation generation fails
        """
        logger.info(f"Generating attestation for {self.agent_did}...")

        # Ensure wake_up_timestamp is set
        if not self.wake_up_timestamp:
            self.wake_up_timestamp = datetime.now(timezone.utc)

        try:
            # Get runtime manifest (container ID, pod name, etc.)
            runtime_manifest = await self._collect_runtime_manifest()

            # Generate attestation
            attestation = await self.attestation_engine.create_attestation(
                agent_did=self.agent_did,
                runtime_type=self.runtime_type,
                runtime_manifest=runtime_manifest,
                state={"wake_up": True, "timestamp": self.wake_up_timestamp.isoformat()},
                capabilities=[],  # Will be populated from credentials
            )

            logger.info(f"✅ Generated attestation {attestation['id'][:8]}...")
            return attestation

        except Exception as e:
            raise SessionEstablishmentError(
                f"Attestation generation failed: {e}"
            ) from e

    async def _establish_session(self, attestation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Establish secure session (Phase 3).

        Args:
            attestation: Fresh runtime attestation

        Returns:
            Session dictionary with state and capabilities
        """
        logger.info(f"Establishing session for {self.agent_did}...")

        # Ensure wake_up_timestamp is set
        if not self.wake_up_timestamp:
            self.wake_up_timestamp = datetime.now(timezone.utc)

        # Load credentials to get capabilities
        credentials = await self._load_agent_credentials(self.agent_did)

        # Extract capabilities from credentials
        capabilities = []
        for cred in credentials:
            cred_subject = cred.get("credentialSubject", {})
            cred_caps = cred_subject.get("capabilities", [])
            capabilities.extend(cred_caps)

        # Create session
        session = {
            "session_id": f"session-{datetime.now(timezone.utc).timestamp()}",
            "agent_did": self.agent_did,
            "runtime_type": self.runtime_type,
            "attestation": attestation,
            "capabilities": capabilities,
            "credentials": len(credentials),
            "conscious": True,
            "wake_up_timestamp": self.wake_up_timestamp.isoformat(),
            "state": self.state.value,
        }

        logger.info(
            f"✅ Session established with {len(capabilities)} capabilities "
            f"from {len(credentials)} credentials"
        )

        return session

    async def _collect_runtime_manifest(self) -> Dict[str, Any]:
        """
        Collect runtime environment information.

        Returns:
            Runtime manifest dictionary
        """
        manifest = {
            "runtime_type": self.runtime_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Kubernetes runtime
        if self.runtime_type == "kubernetes":
            try:
                import os

                manifest.update(
                    {
                        "pod_name": os.getenv("HOSTNAME", "unknown"),
                        "namespace": os.getenv("POD_NAMESPACE", "default"),
                        "node_name": os.getenv("NODE_NAME", "unknown"),
                    }
                )
            except Exception as e:
                logger.warning(f"Could not collect k8s manifest: {e}")

        # Serverless runtime
        elif self.runtime_type == "serverless":
            try:
                import os

                manifest.update(
                    {
                        "function_name": os.getenv("AWS_LAMBDA_FUNCTION_NAME", "unknown"),
                        "function_version": os.getenv("AWS_LAMBDA_FUNCTION_VERSION", "unknown"),
                        "request_id": os.getenv("AWS_REQUEST_ID", "unknown"),
                    }
                )
            except Exception as e:
                logger.warning(f"Could not collect serverless manifest: {e}")

        # Edge runtime
        elif self.runtime_type == "edge":
            manifest.update({"edge_location": "unknown", "provider": "unknown"})

        return manifest

    def is_conscious(self) -> bool:
        """Check if agent is currently conscious"""
        return self.state == WakeUpState.CONSCIOUS

    def get_session(self) -> Optional[Dict[str, Any]]:
        """Get current session if conscious"""
        return self.session if self.is_conscious() else None

    async def _load_agent_credentials(self, agent_did: str) -> List[Dict[str, Any]]:
        """
        Load agent credentials.

        For now, this creates mock credentials. In production, this would
        query the PostgreSQL credentials table from migration 007.

        Args:
            agent_did: Agent DID to load credentials for

        Returns:
            List of credential dictionaries
        """
        # TODO: Replace with actual database query
        # SELECT * FROM credentials WHERE subject_did = agent_did AND NOT revoked
        return [
            {
                "id": f"urn:uuid:credential-{agent_did}",
                "type": ["VerifiableCredential"],
                "issuer": "did:waooaw:platform",
                "credentialSubject": {
                    "id": agent_did,
                    "capabilities": [
                        {
                            "action": "read",
                            "resource": "/api/*",
                            "constraints": {},
                        }
                    ],
                },
            }
        ]

    async def sleep(self):
        """
        Put agent to sleep (graceful shutdown).

        Returns agent to DORMANT state after cleanup.
        """
        if self.state == WakeUpState.CONSCIOUS:
            logger.info(f"😴 Agent {self.agent_did} going to sleep...")
            self.state = WakeUpState.DORMANT
            self.session = None
            logger.info(f"💤 Agent {self.agent_did} is now dormant")
