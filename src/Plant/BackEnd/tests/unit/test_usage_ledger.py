from datetime import datetime, timedelta, timezone

import pytest

from services.usage_ledger import FileUsageLedger, InMemoryUsageLedger


def test_increment_with_limit_blocks_after_limit():
    ledger = InMemoryUsageLedger()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    for _ in range(3):
        result = ledger.increment_with_limit(
            key="k",
            limit=3,
            window=timedelta(days=1),
            now=now,
        )

    assert result.allowed is True
    assert result.value == 3

    blocked = ledger.increment_with_limit(
        key="k",
        limit=3,
        window=timedelta(days=1),
        now=now,
    )
    assert blocked.allowed is False
    assert blocked.value == 3  # unchanged when blocked


def test_increment_resets_after_window():
    ledger = InMemoryUsageLedger()
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    first = ledger.increment_with_limit(
        key="k",
        limit=1,
        window=timedelta(seconds=10),
        now=start,
    )
    assert first.allowed is True
    assert first.value == 1

    # Blocked within window
    blocked = ledger.increment_with_limit(
        key="k",
        limit=1,
        window=timedelta(seconds=10),
        now=start,
    )
    assert blocked.allowed is False
    assert blocked.value == 1

    # Allowed after reset
    after_reset = ledger.increment_with_limit(
        key="k",
        limit=1,
        window=timedelta(seconds=10),
        now=first.resets_at,
    )
    assert after_reset.allowed is True
    assert after_reset.value == 1


def test_add_spend_blocks_after_budget():
    ledger = InMemoryUsageLedger()
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    first = ledger.add_spend_with_limit(
        key="spend",
        budget_usd=10.0,
        spend_usd=3.0,
        window=timedelta(days=30),
        now=now,
    )
    assert first.allowed is True
    assert first.total_usd == 3.0

    blocked = ledger.add_spend_with_limit(
        key="spend",
        budget_usd=10.0,
        spend_usd=8.0,
        window=timedelta(days=30),
        now=now,
    )
    assert blocked.allowed is False
    assert blocked.total_usd == 3.0  # unchanged when blocked


def test_invalid_inputs_raise():
    ledger = InMemoryUsageLedger()
    with pytest.raises(ValueError):
        ledger.increment_with_limit(key="k", limit=-1, window=timedelta(days=1))
    with pytest.raises(ValueError):
        ledger.increment_with_limit(key="k", limit=1, window=timedelta(days=1), amount=0)
    with pytest.raises(ValueError):
        ledger.add_spend_with_limit(key="k", budget_usd=-1.0, spend_usd=1.0, window=timedelta(days=30))
    with pytest.raises(ValueError):
        ledger.add_spend_with_limit(key="k", budget_usd=1.0, spend_usd=-1.0, window=timedelta(days=30))


def test_file_usage_ledger_persists(tmp_path):
    path = tmp_path / "usage_ledger.json"
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    ledger = FileUsageLedger(path)
    first = ledger.increment_with_limit(
        key="k",
        limit=3,
        window=timedelta(days=1),
        now=now,
    )
    assert first.allowed is True
    assert first.value == 1

    # New instance should load state.
    ledger2 = FileUsageLedger(path)
    second = ledger2.increment_with_limit(
        key="k",
        limit=3,
        window=timedelta(days=1),
        now=now,
    )
    assert second.allowed is True
    assert second.value == 2


def test_file_usage_ledger_resets_after_window(tmp_path):
    path = tmp_path / "usage_ledger.json"
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    ledger = FileUsageLedger(path)
    first = ledger.increment_with_limit(
        key="k",
        limit=1,
        window=timedelta(seconds=10),
        now=start,
    )
    assert first.allowed is True
    assert first.value == 1

    # Allowed after reset at exactly resets_at.
    after_reset = ledger.increment_with_limit(
        key="k",
        limit=1,
        window=timedelta(seconds=10),
        now=first.resets_at,
    )
    assert after_reset.allowed is True
    assert after_reset.value == 1
