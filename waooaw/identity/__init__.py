"""
WAOOAW Identity System

Provides DID (Decentralized Identifier) provisioning, verification,
capability management, verifiable credentials, runtime attestation,
and automated key rotation for all Platform CoE agents.
"""

from waooaw.identity.did_service import DIDService, DIDDocument
from waooaw.identity.did_registry import DIDRegistry
from waooaw.identity.vc_issuer import VCIssuer, VerifiableCredential
from waooaw.identity.capability_validator import CapabilityValidator
from waooaw.identity.attestation_engine import (
    AttestationEngine,
    RuntimeAttestation,
    AttestationClaim
)
from waooaw.identity.key_rotation import (
    KeyRotationManager,
    KeyRotationRecord,
    RotationPolicy
)

__all__ = [
    'DIDService',
    'DIDDocument',
    'DIDRegistry',
    'VCIssuer',
    'VerifiableCredential',
    'CapabilityValidator',
    'AttestationEngine',
    'RuntimeAttestation',
    'AttestationClaim',
    'KeyRotationManager',
    'KeyRotationRecord',
    'RotationPolicy',
]
