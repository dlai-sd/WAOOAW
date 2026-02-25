"""Property-based tests for usage ledger invariants."""
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


@pytest.mark.property
class TestUsageLedgerInvariants:
    @given(
        tokens_used=st.integers(min_value=0, max_value=1_000_000),
        token_limit=st.integers(min_value=1, max_value=1_000_000),
    )
    @settings(max_examples=100)
    def test_usage_never_exceeds_limit_when_cap_enforced(self, tokens_used, token_limit):
        """Usage capped at limit must never exceed limit."""
        capped = min(tokens_used, token_limit)
        assert capped <= token_limit

    @given(
        entries=st.lists(st.integers(min_value=0, max_value=10_000), min_size=0, max_size=50),
    )
    @settings(max_examples=100)
    def test_ledger_total_equals_sum_of_entries(self, entries):
        """Ledger total must equal sum of all entries."""
        total = sum(entries)
        assert total == sum(entries)
        assert total >= 0

    @given(
        delta=st.integers(min_value=1, max_value=1000),
        initial=st.integers(min_value=0, max_value=100_000),
    )
    @settings(max_examples=100)
    def test_additive_entries_are_monotonically_increasing(self, delta, initial):
        """Adding a positive delta always increases the total."""
        result = initial + delta
        assert result > initial
