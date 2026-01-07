"""
Tests for KeyRotationManager - Automated key rotation with credential re-issuance.

Epic 2.3: Attestation System (v0.5.3)
"""

import pytest
from datetime import datetime, timedelta, UTC
from waooaw.identity.did_service import DIDService
from waooaw.identity.did_registry import get_did_registry
from waooaw.identity.vc_issuer import VCIssuer
from waooaw.identity.key_rotation import (
    KeyRotationManager,
    KeyRotationRecord,
    RotationPolicy,
    get_key_rotation_manager
)


@pytest.fixture
def did_service():
    """DID service fixture."""
    return DIDService()


@pytest.fixture
def did_registry():
    """DID registry fixture."""
    return get_did_registry()


@pytest.fixture
def vc_issuer():
    """VC issuer fixture."""
    return VCIssuer()


@pytest.fixture
def rotation_manager(did_service, did_registry, vc_issuer):
    """Key rotation manager fixture."""
    return KeyRotationManager(did_service, did_registry, vc_issuer)


@pytest.fixture
def agent_did_doc(did_service, did_registry):
    """Create agent DID document."""
    did_doc, private_key = did_service.provision_agent_did("wowdomain")
    did_registry.register(did_doc)
    return did_doc, private_key


class TestRotationPolicy:
    """Test RotationPolicy dataclass."""
    
    def test_create_rotation_policy(self):
        """Test: Create rotation policy."""
        now = datetime.now(UTC)
        policy = RotationPolicy(
            agent_did="did:waooaw:test",
            rotation_interval_days=90,
            last_rotation=now.isoformat(),
            next_rotation=(now + timedelta(days=90)).isoformat(),
            grace_period_days=7,
            auto_rotate=True,
            key_type="Ed25519"
        )
        
        assert policy.agent_did == "did:waooaw:test"
        assert policy.rotation_interval_days == 90
        assert policy.grace_period_days == 7
        assert policy.auto_rotate is True
    
    def test_policy_to_dict(self):
        """Test: Convert policy to dictionary."""
        now = datetime.now(UTC)
        policy = RotationPolicy(
            agent_did="did:waooaw:test",
            rotation_interval_days=180,
            last_rotation=now.isoformat(),
            next_rotation=(now + timedelta(days=180)).isoformat()
        )
        
        data = policy.to_dict()
        
        assert isinstance(data, dict)
        assert data["agent_did"] == "did:waooaw:test"
        assert data["rotation_interval_days"] == 180
    
    def test_policy_from_dict(self):
        """Test: Create policy from dictionary."""
        now = datetime.now(UTC)
        data = {
            "agent_did": "did:waooaw:test",
            "rotation_interval_days": 90,
            "last_rotation": now.isoformat(),
            "next_rotation": (now + timedelta(days=90)).isoformat(),
            "grace_period_days": 7,
            "auto_rotate": True,
            "key_type": "Ed25519"
        }
        
        policy = RotationPolicy.from_dict(data)
        
        assert isinstance(policy, RotationPolicy)
        assert policy.agent_did == "did:waooaw:test"
        assert policy.rotation_interval_days == 90


class TestKeyRotationRecord:
    """Test KeyRotationRecord dataclass."""
    
    def test_create_rotation_record(self):
        """Test: Create rotation record."""
        now = datetime.now(UTC)
        record = KeyRotationRecord(
            agent_did="did:waooaw:test",
            old_key_id="did:waooaw:test#key-1",
            new_key_id="did:waooaw:test#key-2",
            rotation_date=now.isoformat(),
            reason="scheduled",
            grace_period_end=(now + timedelta(days=7)).isoformat(),
            credentials_reissued=5,
            metadata={"key_type": "Ed25519"}
        )
        
        assert record.agent_did == "did:waooaw:test"
        assert record.reason == "scheduled"
        assert record.credentials_reissued == 5
    
    def test_record_to_dict(self):
        """Test: Convert record to dictionary."""
        now = datetime.now(UTC)
        record = KeyRotationRecord(
            agent_did="did:waooaw:test",
            old_key_id="key-1",
            new_key_id="key-2",
            rotation_date=now.isoformat(),
            reason="compromised",
            grace_period_end=(now + timedelta(days=7)).isoformat()
        )
        
        data = record.to_dict()
        
        assert isinstance(data, dict)
        assert data["reason"] == "compromised"
    
    def test_record_to_json(self):
        """Test: Convert record to JSON."""
        import json
        now = datetime.now(UTC)
        record = KeyRotationRecord(
            agent_did="did:waooaw:test",
            old_key_id="key-1",
            new_key_id="key-2",
            rotation_date=now.isoformat(),
            reason="manual",
            grace_period_end=(now + timedelta(days=7)).isoformat()
        )
        
        json_str = record.to_json()
        
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["reason"] == "manual"


class TestKeyRotationManager:
    """Test KeyRotationManager class."""
    
    def test_create_rotation_manager(self, rotation_manager):
        """Test: Create key rotation manager."""
        assert isinstance(rotation_manager, KeyRotationManager)
        assert rotation_manager.did_service is not None
        assert rotation_manager.did_registry is not None
        assert rotation_manager.vc_issuer is not None
    
    def test_register_rotation_policy(self, rotation_manager):
        """Test: Register rotation policy for agent."""
        policy = rotation_manager.register_rotation_policy(
            agent_did="did:waooaw:wowsecurity",
            rotation_interval_days=90,
            grace_period_days=7,
            auto_rotate=True,
            key_type="Ed25519"
        )
        
        assert isinstance(policy, RotationPolicy)
        assert policy.agent_did == "did:waooaw:wowsecurity"
        assert policy.rotation_interval_days == 90
        assert policy.grace_period_days == 7
    
    def test_register_multiple_policies(self, rotation_manager):
        """Test: Register policies for multiple agents."""
        # Security agent: 90 days
        policy1 = rotation_manager.register_rotation_policy(
            agent_did="did:waooaw:wowsecurity",
            rotation_interval_days=90
        )
        
        # Standard agent: 180 days
        policy2 = rotation_manager.register_rotation_policy(
            agent_did="did:waooaw:wowdomain",
            rotation_interval_days=180
        )
        
        assert policy1.rotation_interval_days == 90
        assert policy2.rotation_interval_days == 180
    
    def test_get_rotation_policy(self, rotation_manager):
        """Test: Get registered rotation policy."""
        rotation_manager.register_rotation_policy(
            agent_did="did:waooaw:test",
            rotation_interval_days=90
        )
        
        policy = rotation_manager.get_rotation_policy("did:waooaw:test")
        
        assert policy is not None
        assert policy.agent_did == "did:waooaw:test"
    
    def test_get_nonexistent_policy(self, rotation_manager):
        """Test: Get non-existent policy returns None."""
        policy = rotation_manager.get_rotation_policy("did:waooaw:nonexistent")
        
        assert policy is None
    
    def test_list_rotation_policies(self, rotation_manager):
        """Test: List all rotation policies."""
        rotation_manager.register_rotation_policy(
            agent_did="did:waooaw:agent1",
            rotation_interval_days=90
        )
        rotation_manager.register_rotation_policy(
            agent_did="did:waooaw:agent2",
            rotation_interval_days=180
        )
        
        policies = rotation_manager.list_rotation_policies()
        
        assert len(policies) == 2
        assert all(isinstance(p, RotationPolicy) for p in policies)
    
    def test_is_rotation_due_not_due(self, rotation_manager):
        """Test: Check rotation not due yet."""
        rotation_manager.register_rotation_policy(
            agent_did="did:waooaw:test",
            rotation_interval_days=90
        )
        
        is_due = rotation_manager.is_rotation_due("did:waooaw:test")
        
        assert is_due is False
    
    def test_list_agents_due_for_rotation(self, rotation_manager):
        """Test: List agents due for rotation."""
        # Register policy with past next_rotation date
        now = datetime.now(UTC)
        past = now - timedelta(days=1)
        
        policy = RotationPolicy(
            agent_did="did:waooaw:overdue",
            rotation_interval_days=90,
            last_rotation=(now - timedelta(days=91)).isoformat(),
            next_rotation=past.isoformat(),
            grace_period_days=7,
            auto_rotate=True
        )
        
        rotation_manager._policies["did:waooaw:overdue"] = policy
        
        due_agents = rotation_manager.list_agents_due_for_rotation()
        
        assert "did:waooaw:overdue" in due_agents
    
    def test_rotate_agent_key(self, rotation_manager, agent_did_doc):
        """Test: Rotate agent's key."""
        did_doc, private_key = agent_did_doc
        
        # Register policy
        rotation_manager.register_rotation_policy(
            agent_did=did_doc.id,
            rotation_interval_days=90
        )
        
        # Rotate key
        updated_did, new_key, rotation_record = rotation_manager.rotate_agent_key(
            agent_did=did_doc.id,
            reason="scheduled"
        )
        
        assert updated_did.id == did_doc.id
        assert len(updated_did.verification_methods) == 2  # Old + new
        assert new_key is not None
        assert isinstance(rotation_record, KeyRotationRecord)
        assert rotation_record.reason == "scheduled"
    
    def test_rotate_key_updates_policy(self, rotation_manager, agent_did_doc):
        """Test: Key rotation updates policy dates."""
        did_doc, private_key = agent_did_doc
        
        # Register policy
        rotation_manager.register_rotation_policy(
            agent_did=did_doc.id,
            rotation_interval_days=90
        )
        
        old_policy = rotation_manager.get_rotation_policy(did_doc.id)
        old_next_rotation = old_policy.next_rotation
        old_last_rotation = old_policy.last_rotation
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        # Rotate key
        rotation_manager.rotate_agent_key(did_doc.id, reason="scheduled")
        
        # Check policy was updated (same object, modified in place)
        new_policy = rotation_manager.get_rotation_policy(did_doc.id)
        
        assert new_policy is old_policy  # Same object
        assert new_policy.last_rotation != old_last_rotation
        assert new_policy.next_rotation != old_next_rotation
    
    def test_rotation_with_custom_grace_period(self, rotation_manager, agent_did_doc):
        """Test: Rotate key with custom grace period."""
        did_doc, private_key = agent_did_doc
        
        rotation_manager.register_rotation_policy(
            agent_did=did_doc.id,
            rotation_interval_days=90,
            grace_period_days=7  # Default
        )
        
        # Rotate with custom 14-day grace period
        _, _, rotation_record = rotation_manager.rotate_agent_key(
            agent_did=did_doc.id,
            reason="manual",
            grace_period_days=14
        )
        
        # Check grace period
        rotation_date = datetime.fromisoformat(
            rotation_record.rotation_date.replace('Z', '+00:00')
        )
        grace_end = datetime.fromisoformat(
            rotation_record.grace_period_end.replace('Z', '+00:00')
        )
        grace_days = (grace_end - rotation_date).days
        
        assert grace_days == 14
    
    def test_reissue_credentials(self, rotation_manager, agent_did_doc, vc_issuer):
        """Test: Re-issue credentials with new key."""
        did_doc, old_key = agent_did_doc
        
        # Create original credential
        original_cred = vc_issuer.issue_capability_credential(
            subject_did="did:waooaw:subject",
            capabilities=["can:test"],
            private_key=old_key
        )
        
        # Generate new key pair (use private key not public)
        new_private_key, _ = rotation_manager.did_service.generate_key_pair()
        
        # Re-issue credentials
        reissued = rotation_manager.reissue_credentials(
            agent_did=did_doc.id,
            credentials=[original_cred],
            new_private_key=new_private_key
        )
        
        assert len(reissued) == 1
        assert reissued[0].id != original_cred.id  # New credential ID
        assert reissued[0].credential_subject["id"] == "did:waooaw:subject"
        assert "can:test" in reissued[0].credential_subject["capabilities"]
    
    def test_deprecate_old_key(self, rotation_manager, agent_did_doc):
        """Test: Deprecate old key after grace period."""
        did_doc, private_key = agent_did_doc
        
        # Register policy and rotate
        rotation_manager.register_rotation_policy(
            agent_did=did_doc.id,
            rotation_interval_days=90
        )
        
        updated_did, new_key, rotation_record = rotation_manager.rotate_agent_key(
            agent_did=did_doc.id,
            reason="scheduled"
        )
        
        old_key_id = rotation_record.old_key_id
        
        # Deprecate old key
        final_did = rotation_manager.deprecate_old_key(
            agent_did=did_doc.id,
            key_id=old_key_id
        )
        
        # Check old key removed
        key_ids = [vm["id"] for vm in final_did.verification_methods]
        assert old_key_id not in key_ids
        assert len(final_did.verification_methods) == 1  # Only new key
    
    def test_get_rotation_history(self, rotation_manager, agent_did_doc):
        """Test: Get rotation history for agent."""
        did_doc, private_key = agent_did_doc
        
        rotation_manager.register_rotation_policy(
            agent_did=did_doc.id,
            rotation_interval_days=90
        )
        
        # Rotate twice
        rotation_manager.rotate_agent_key(did_doc.id, reason="scheduled")
        rotation_manager.rotate_agent_key(did_doc.id, reason="manual")
        
        # Get history
        history = rotation_manager.get_rotation_history(did_doc.id)
        
        assert len(history) == 2
        assert history[0].reason == "manual"  # Most recent first
        assert history[1].reason == "scheduled"
    
    def test_get_rotation_history_with_limit(self, rotation_manager, agent_did_doc):
        """Test: Get rotation history with limit."""
        did_doc, private_key = agent_did_doc
        
        rotation_manager.register_rotation_policy(
            agent_did=did_doc.id,
            rotation_interval_days=90
        )
        
        # Rotate 3 times
        for i in range(3):
            rotation_manager.rotate_agent_key(did_doc.id, reason=f"rotation_{i}")
        
        # Get last 2
        history = rotation_manager.get_rotation_history(did_doc.id, limit=2)
        
        assert len(history) == 2
    
    def test_export_rotation_metadata(self, rotation_manager, agent_did_doc):
        """Test: Export rotation metadata."""
        did_doc, private_key = agent_did_doc
        
        rotation_manager.register_rotation_policy(
            agent_did=did_doc.id,
            rotation_interval_days=90
        )
        rotation_manager.rotate_agent_key(did_doc.id, reason="scheduled")
        
        metadata = rotation_manager.export_rotation_metadata()
        
        assert "policies" in metadata
        assert "history" in metadata
        assert "exported_at" in metadata
        assert did_doc.id in metadata["policies"]
        assert did_doc.id in metadata["history"]
    
    def test_import_rotation_metadata(self, rotation_manager):
        """Test: Import rotation metadata."""
        now = datetime.now(UTC)
        
        # Create metadata
        metadata = {
            "policies": {
                "did:waooaw:test": {
                    "agent_did": "did:waooaw:test",
                    "rotation_interval_days": 90,
                    "last_rotation": now.isoformat(),
                    "next_rotation": (now + timedelta(days=90)).isoformat(),
                    "grace_period_days": 7,
                    "auto_rotate": True,
                    "key_type": "Ed25519"
                }
            },
            "history": {
                "did:waooaw:test": [
                    {
                        "agent_did": "did:waooaw:test",
                        "old_key_id": "key-1",
                        "new_key_id": "key-2",
                        "rotation_date": now.isoformat(),
                        "reason": "scheduled",
                        "grace_period_end": (now + timedelta(days=7)).isoformat(),
                        "credentials_reissued": 0,
                        "metadata": {}
                    }
                ]
            },
            "exported_at": now.isoformat()
        }
        
        # Import
        rotation_manager.import_rotation_metadata(metadata)
        
        # Verify imported
        policy = rotation_manager.get_rotation_policy("did:waooaw:test")
        assert policy is not None
        assert policy.rotation_interval_days == 90
        
        history = rotation_manager.get_rotation_history("did:waooaw:test")
        assert len(history) == 1
        assert history[0].reason == "scheduled"


class TestRotationReasons:
    """Test different rotation reasons."""
    
    def test_scheduled_rotation(self, rotation_manager, agent_did_doc):
        """Test: Scheduled rotation."""
        did_doc, _ = agent_did_doc
        rotation_manager.register_rotation_policy(did_doc.id, 90)
        
        _, _, record = rotation_manager.rotate_agent_key(did_doc.id, reason="scheduled")
        
        assert record.reason == "scheduled"
    
    def test_compromised_rotation(self, rotation_manager, agent_did_doc):
        """Test: Rotation due to compromise."""
        did_doc, _ = agent_did_doc
        rotation_manager.register_rotation_policy(did_doc.id, 90)
        
        _, _, record = rotation_manager.rotate_agent_key(did_doc.id, reason="compromised")
        
        assert record.reason == "compromised"
    
    def test_manual_rotation(self, rotation_manager, agent_did_doc):
        """Test: Manual rotation."""
        did_doc, _ = agent_did_doc
        rotation_manager.register_rotation_policy(did_doc.id, 90)
        
        _, _, record = rotation_manager.rotate_agent_key(did_doc.id, reason="manual")
        
        assert record.reason == "manual"


class TestRotationSingleton:
    """Test key rotation manager singleton."""
    
    def test_get_key_rotation_manager_requires_dependencies(self):
        """Test: First call requires dependencies."""
        with pytest.raises(ValueError, match="requires did_service"):
            get_key_rotation_manager()
