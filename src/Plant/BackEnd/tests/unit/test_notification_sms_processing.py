from __future__ import annotations

from datetime import datetime, timezone

from services.notification_delivery_store import default_notification_delivery_store
from services.notification_events import NotificationEventRecord, default_notification_event_store


class _CapturingSmsProvider:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    async def send_sms(self, *, to_phone: str, message: str) -> None:
        self.sent.append({"to_phone": to_phone, "message": message})


def test_process_sms_notifications_sends_and_dedupes(test_client, monkeypatch):
    default_notification_event_store.cache_clear()
    default_notification_delivery_store.cache_clear()

    provider = _CapturingSmsProvider()
    monkeypatch.setattr("api.v1.notifications.get_sms_provider", lambda: provider)

    store = default_notification_event_store()
    store.append(
        NotificationEventRecord(
            created_at=datetime(2026, 2, 9, 0, 0, 0, tzinfo=timezone.utc),
            event_type="cancel_effective",
            subscription_id="SUB-9",
            metadata={"to_phone": "+15551234567", "ended_at": "2026-02-09T00:00:00Z"},
        )
    )

    r1 = test_client.post("/api/v1/notifications/process-sms", json={"limit": 50})
    assert r1.status_code == 200
    assert r1.json() == {"scanned": 1, "sent": 1, "skipped": 0}
    assert len(provider.sent) == 1
    assert provider.sent[0]["to_phone"] == "+15551234567"
    assert "Subscription ended" in provider.sent[0]["message"]

    r2 = test_client.post("/api/v1/notifications/process-sms", json={"limit": 50})
    assert r2.status_code == 200
    assert r2.json() == {"scanned": 1, "sent": 0, "skipped": 1}
    assert len(provider.sent) == 1


def test_process_sms_notifications_sends_for_otp_sent(test_client, monkeypatch):
    default_notification_event_store.cache_clear()
    default_notification_delivery_store.cache_clear()

    provider = _CapturingSmsProvider()
    monkeypatch.setattr("api.v1.notifications.get_sms_provider", lambda: provider)

    store = default_notification_event_store()
    store.append(
        NotificationEventRecord(
            created_at=datetime(2026, 2, 9, 0, 0, 0, tzinfo=timezone.utc),
            event_type="otp_sent",
            metadata={
                "to_phone": "+15551234567",
                "flow": "login",
                "channel": "phone",
                "destination_masked": "+15***67",
                "expires_in_seconds": 300,
            },
        )
    )

    r1 = test_client.post("/api/v1/notifications/process-sms", json={"limit": 50})
    assert r1.status_code == 200
    assert r1.json() == {"scanned": 1, "sent": 1, "skipped": 0}
    assert len(provider.sent) == 1
    assert provider.sent[0]["to_phone"] == "+15551234567"
    assert "OTP" in provider.sent[0]["message"]

    r2 = test_client.post("/api/v1/notifications/process-sms", json={"limit": 50})
    assert r2.status_code == 200
    assert r2.json() == {"scanned": 1, "sent": 0, "skipped": 1}
    assert len(provider.sent) == 1
