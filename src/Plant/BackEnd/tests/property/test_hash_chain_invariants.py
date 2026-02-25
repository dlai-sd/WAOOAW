"""
Property-based tests for hash chain invariants.

Invariants under test:
  1. SHA-256 output is always exactly 64 hex characters.
  2. Hash chain with same data always produces the same hash (determinism).
  3. Any tampered data in the chain fails validate_chain.
"""
import json
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from security.hash_chain import calculate_sha256, create_hash_link, validate_chain


@pytest.mark.property
class TestHashChainInvariants:

    @given(data=st.text(min_size=0, max_size=1000))
    @settings(max_examples=100)
    def test_sha256_output_is_always_64_chars(self, data: str) -> None:
        """SHA-256 hex digest must always be exactly 64 characters."""
        result = calculate_sha256(data)
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    @given(
        previous_hash=st.text(alphabet="0123456789abcdef", min_size=64, max_size=64),
        current_data=st.text(min_size=1, max_size=500),
    )
    @settings(max_examples=100)
    def test_hash_chain_is_deterministic(self, previous_hash: str, current_data: str) -> None:
        """Same inputs must always produce the same hash link."""
        hash1 = create_hash_link(previous_hash, current_data)
        hash2 = create_hash_link(previous_hash, current_data)
        assert hash1 == hash2

    @given(
        items=st.lists(
            st.fixed_dictionaries({"id": st.integers(), "value": st.text(min_size=1, max_size=50)}),
            min_size=2,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_valid_chain_passes_validation(self, items: list) -> None:
        """A correctly built chain must pass validate_chain."""
        hashes = []
        prev = ""
        for item in items:
            data_str = json.dumps(item, sort_keys=True)
            link = create_hash_link(prev, data_str)
            hashes.append(link)
            prev = link

        result = validate_chain(items, hashes)
        assert result.get("valid") is True

    @given(
        items=st.lists(
            st.fixed_dictionaries({"id": st.integers(), "value": st.text(min_size=1, max_size=50)}),
            min_size=2,
            max_size=5,
        ),
        tamper_index=st.integers(min_value=0, max_value=4),
    )
    @settings(max_examples=100)
    def test_tampered_data_fails_validation(self, items: list, tamper_index: int) -> None:
        """Tampered data at any position must cause validate_chain to fail."""
        if tamper_index >= len(items):
            return  # skip when index out of range for this example

        # Build a valid chain first
        hashes = []
        prev = ""
        for item in items:
            data_str = json.dumps(item, sort_keys=True)
            link = create_hash_link(prev, data_str)
            hashes.append(link)
            prev = link

        # Tamper with one item's data
        tampered_items = [dict(it) for it in items]
        tampered_items[tamper_index]["value"] = tampered_items[tamper_index]["value"] + "_tampered"

        result = validate_chain(tampered_items, hashes)
        assert result.get("valid") is False
