"""
Unit tests for SHA-256 hash chain utilities
"""

import pytest

from security.hash_chain import calculate_sha256, create_hash_link, validate_chain


class TestSHA256Calculation:
    """Test SHA-256 hash calculation."""
    
    def test_calculate_sha256_returns_hex_digest(self):
        """Test that calculate_sha256 returns hex string."""
        data = "Hello, World!"
        hash_value = calculate_sha256(data)
        
        assert hash_value is not None
        assert len(hash_value) == 64  # SHA-256 produces 64-char hex
        assert isinstance(hash_value, str)
    
    def test_calculate_sha256_deterministic(self):
        """Test that same data produces same hash."""
        data = "Test data"
        hash1 = calculate_sha256(data)
        hash2 = calculate_sha256(data)
        
        assert hash1 == hash2


class TestHashLinking:
    """Test hash chain linking."""
    
    def test_create_hash_link_combines_previous_and_current(self):
        """Test that create_hash_link chains hashes together."""
        previous_hash = calculate_sha256("data1")
        current_data = "data2"
        
        link = create_hash_link(previous_hash, current_data)
        
        assert link is not None
        assert len(link) == 64
        assert link != previous_hash
        assert link != calculate_sha256(current_data)


class TestChainValidation:
    """Test hash chain validation."""
    
    def test_validate_chain_passes_for_valid_chain(self):
        """Test that valid chain passes validation."""
        amendments = [
            {"data": {"field": "value1"}},
            {"data": {"field": "value2"}},
            {"data": {"field": "value3"}},
        ]
        
        hash_chain = []
        for i, amendment in enumerate(amendments):
            if i == 0:
                h = calculate_sha256(str(amendment))
            else:
                h = create_hash_link(hash_chain[i-1], str(amendment))
            hash_chain.append(h)
        
        result = validate_chain(amendments, hash_chain)
        
        assert result["intact"] is True
        assert result["broken_at_index"] is None
    
    def test_validate_chain_detects_tampering(self):
        """Test that tampered chain is detected."""
        amendments = [
            {"data": {"field": "value1"}},
            {"data": {"field": "value2"}},
        ]
        
        hash_chain = [
            calculate_sha256(str(amendments[0])),
            "tampered_hash"  # Invalid hash
        ]
        
        result = validate_chain(amendments, hash_chain)
        
        assert result["intact"] is False
        assert result["broken_at_index"] == 1
