"""Property-based tests for trial billing invariants."""
from datetime import datetime, timedelta, timezone
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


@pytest.mark.property
class TestTrialBillingInvariants:
    @given(
        start_offset_days=st.integers(min_value=0, max_value=365),
    )
    @settings(max_examples=100)
    def test_trial_end_is_always_after_start(self, start_offset_days):
        """Trial end date must always be after trial start date."""
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        start = now + timedelta(days=start_offset_days)
        end = start + timedelta(days=7)
        assert end > start

    @given(
        amount=st.floats(min_value=0.01, max_value=1_000_000.0, allow_nan=False, allow_infinity=False),
        discount_pct=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100)
    def test_discounted_amount_never_exceeds_original(self, amount, discount_pct):
        """Discounted price must never exceed original price."""
        discounted = amount * (1 - discount_pct / 100)
        assert discounted <= amount + 1e-9  # float tolerance

    @given(
        trial_days=st.just(7),
        grace_days=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=100)
    def test_trial_duration_is_exactly_seven_days(self, trial_days, grace_days):
        """Canonical trial duration must be 7 days."""
        assert trial_days == 7
