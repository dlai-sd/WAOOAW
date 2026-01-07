"""
Tests for DID Service - Decentralized Identifier provisioning.
"""

import pytest
from waooaw.identity.did_service import DIDService, DIDDocument
from cryptography.hazmat.primitives.asymmetric import ed25519


class TestDIDService:
    """Test DID service functionality."""
    
    def test_generate_did(self):
        """Test DID generation."""
        service = DIDService()
        
        # Test various agent names
        assert service.generate_did("WowVisionPrime") == "did:waooaw:wowvisionprime"
        assert service.generate_did("WowAgentFactory") == "did:waooaw:wowagentfactory"
        assert service.generate_did("WowDomain") == "did:waooaw:wowdomain"
        
        # Test with spaces
        assert service.generate_did("Wow Vision Prime") == "did:waooaw:wow-vision-prime"
        
    def test_generate_key_pair(self):
        """Test Ed25519 key pair generation."""
        service = DIDService()
        
        private_key, public_key = service.generate_key_pair()
        
        # Verify types
        assert isinstance(private_key, ed25519.Ed25519PrivateKey)
        assert isinstance(public_key, ed25519.Ed25519PublicKey)
        
        # Verify keys are different each time
        private_key2, public_key2 = service.generate_key_pair()
        assert private_key != private_key2
        assert public_key != public_key2
        
    def test_public_key_to_multibase(self):
        """Test public key multibase encoding."""
        service = DIDService()
        
        _, public_key = service.generate_key_pair()
        multibase = service.public_key_to_multibase(public_key)
        
        # Should start with 'z' (base58-btc)
        assert multibase.startswith('z')
        assert len(multibase) > 1
        
    def test_create_did_document(self):
        """Test DID document creation."""
        service = DIDService()
        
        # Generate keys
        _, public_key = service.generate_key_pair()
        
        # Create document
        doc = service.create_did_document(
            agent_name="WowVisionPrime",
            public_key=public_key,
            service_endpoint="https://api.waooaw.com/agents/wowvisionprime"
        )
        
        # Verify structure
        assert doc.id == "did:waooaw:wowvisionprime"
        assert doc.controller == "did:waooaw:wowvision-prime"
        assert len(doc.verification_methods) == 1
        assert len(doc.authentication) == 1
        assert len(doc.capability_invocation) == 1
        assert len(doc.service_endpoints) == 1
        
        # Verify verification method
        vm = doc.verification_methods[0]
        assert vm["id"] == "did:waooaw:wowvisionprime#key-1"
        assert vm["type"] == "Ed25519VerificationKey2020"
        assert vm["controller"] == "did:waooaw:wowvisionprime"
        assert "publicKeyMultibase" in vm
        
        # Verify service endpoint
        service_ep = doc.service_endpoints[0]
        assert service_ep["type"] == "AgentService"
        assert service_ep["serviceEndpoint"] == "https://api.waooaw.com/agents/wowvisionprime"
        
    def test_provision_agent_did(self):
        """Test complete DID provisioning."""
        service = DIDService()
        
        # Provision DID
        did_doc, private_key = service.provision_agent_did("WowDomain")
        
        # Verify document
        assert did_doc.id == "did:waooaw:wowdomain"
        assert isinstance(private_key, ed25519.Ed25519PrivateKey)
        
        # Verify timestamps
        assert did_doc.created == did_doc.updated
        
    def test_did_document_to_dict(self):
        """Test DID document serialization to dict."""
        service = DIDService()
        
        _, public_key = service.generate_key_pair()
        doc = service.create_did_document("TestAgent", public_key)
        
        doc_dict = doc.to_dict()
        
        # Verify W3C DID Core format
        assert "@context" in doc_dict
        assert "https://www.w3.org/ns/did/v1" in doc_dict["@context"]
        assert doc_dict["id"] == "did:waooaw:testagent"
        assert "verificationMethod" in doc_dict
        assert "authentication" in doc_dict
        
    def test_did_document_to_json(self):
        """Test DID document serialization to JSON."""
        service = DIDService()
        
        _, public_key = service.generate_key_pair()
        doc = service.create_did_document("TestAgent", public_key)
        
        json_str = doc.to_json()
        
        # Verify it's valid JSON
        import json
        parsed = json.loads(json_str)
        assert parsed["id"] == "did:waooaw:testagent"
        
    def test_verify_did_signature(self):
        """Test signature verification using DID document."""
        service = DIDService()
        
        # Generate keys and create document
        did_doc, private_key = service.provision_agent_did("TestAgent")
        
        # Sign a message
        message = b"Hello, WAOOAW!"
        signature = private_key.sign(message)
        
        # Verify signature using DID document
        is_valid = service.verify_did_signature(did_doc, signature, message)
        assert is_valid is True
        
        # Verify invalid signature
        wrong_message = b"Wrong message"
        is_valid = service.verify_did_signature(did_doc, signature, wrong_message)
        assert is_valid is False
        
    def test_get_did_fingerprint(self):
        """Test DID document fingerprinting."""
        service = DIDService()
        
        _, public_key = service.generate_key_pair()
        doc = service.create_did_document("TestAgent", public_key)
        
        fingerprint = service.get_did_fingerprint(doc)
        
        # Verify fingerprint format (SHA-256 hex)
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64  # SHA-256 produces 64 hex characters
        
        # Same document should produce same fingerprint
        fingerprint2 = service.get_did_fingerprint(doc)
        assert fingerprint == fingerprint2
        
    def test_guardian_controller(self):
        """Test that all agents have WowVisionPrime as controller."""
        service = DIDService()
        
        agents = ["WowDomain", "WowEvent", "WowMemory"]
        
        for agent in agents:
            did_doc, _ = service.provision_agent_did(agent)
            assert did_doc.controller == "did:waooaw:wowvision-prime"
