"""
Property-based tests for InMemoryUsageLedger invariants.

Invariants under test:
  1. Counter value never exceeds the declared limit.
  2. resets_at is always in the future relative to the `now` passed to increment.
  3. Spend total is monotonically increasing within a single window.
"""
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from services.usage_ledger import InMemoryUsageLedger


@pytest.mark.property
class TestUsageLedgerInvariants:

    @given(
        limit=st.integers(min_value=1, max_value=100),
        attempts=st.integers(min_value=1, max_value=200),
    )
    @settings(max_examples=100)
    def test_counter_never_exceeds_limit(self, limit: int, attempts: int) -> None:
        """Counter value must never exceed the declared limit."""
        ledger = InMemoryUsageLedger()
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        window = timedelta(hours=1)

        last_result = None
        for _ in range(attempts):
            last_result = ledger.increment_with_limit(
                key="test-key",
                limit=limit,
                window=window,
                now=now,
            )

        assert last_result is not None
        assert last_result.value <= limit

    @given(
        limit=st.integers(min_value=1, max_value=50),
        window_hours=st.integers(min_value=1, max_value=72),
    )
    @settings(max_examples=100)
    def test_resets_at_is_always_in_future(self, limit: int, window_hours: int) -> None:
        """resets_at is always strictly after `now`."""
        ledger = InMemoryUsageLedger()
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        window = timedelta(hours=window_hours)

        result = ledger.increment_with_limit(
            key="future-key",
            limit=limit,
            window=window,
            now=now,
        )

        assert result.resets_at > now

    @given(
        amounts=st.lists(
            st.floats(min_value=0.01, max_value=10.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=30,
        ),
        budget=st.floats(min_value=100.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_spend_total_monotonically_increases(self, amounts: list, budget: float) -> None:
        """Spend total must be monotonically non-decreasing within a single window."""
        ledger = InMemoryUsageLedger()
        now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        window = timedelta(hours=24)

        previous_total = 0.0
        for amount in amounts:
            result = ledger.add_spend_with_limit(
                key="spend-key",
                spend_usd=amount,
                limit_usd=budget,
                window=window,
                now=now,
            )
            if result.allowed:
                assert result.total_usd >= previous_total
                previous_total = result.total_usd
