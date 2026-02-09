from __future__ import annotations

from datetime import datetime, timezone

from services.notification_delivery_store import default_notification_delivery_store
from services.notification_events import NotificationEventRecord, default_notification_event_store


class _CapturingEmailProvider:
    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def send_email(self, *, to_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
        self.sent.append(
            {
                "to_email": to_email,
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body or "",
            }
        )


def test_process_email_notifications_sends_and_dedupes(test_client, monkeypatch):
    # Fresh stores for deterministic assertions.
    default_notification_event_store.cache_clear()
    default_notification_delivery_store.cache_clear()

    provider = _CapturingEmailProvider()
    monkeypatch.setattr("api.v1.notifications.get_email_provider", lambda: provider)

    store = default_notification_event_store()
    store.append(
        NotificationEventRecord(
            created_at=datetime(2026, 2, 9, 0, 0, 0, tzinfo=timezone.utc),
            event_type="payment_success",
            subscription_id="SUB-1",
            order_id="ORDER-1",
            metadata={"to_email": "buyer@example.com"},
        )
    )

    r1 = test_client.post("/api/v1/notifications/process-email", json={"limit": 50})
    assert r1.status_code == 200
    assert r1.json() == {"scanned": 1, "sent": 1, "skipped": 0}
    assert len(provider.sent) == 1
    assert provider.sent[0]["to_email"] == "buyer@example.com"
    assert "Payment confirmed" in provider.sent[0]["subject"]

    r2 = test_client.post("/api/v1/notifications/process-email", json={"limit": 50})
    assert r2.status_code == 200
    assert r2.json() == {"scanned": 1, "sent": 0, "skipped": 1}
    assert len(provider.sent) == 1


def test_process_email_notifications_sends_for_otp_sent(test_client, monkeypatch):
    default_notification_event_store.cache_clear()
    default_notification_delivery_store.cache_clear()

    provider = _CapturingEmailProvider()
    monkeypatch.setattr("api.v1.notifications.get_email_provider", lambda: provider)

    store = default_notification_event_store()
    store.append(
        NotificationEventRecord(
            created_at=datetime(2026, 2, 9, 0, 0, 0, tzinfo=timezone.utc),
            event_type="otp_sent",
            metadata={
                "to_email": "buyer@example.com",
                "flow": "registration",
                "channel": "email",
                "destination_masked": "b***r@example.com",
                "expires_in_seconds": 300,
            },
        )
    )

    r1 = test_client.post("/api/v1/notifications/process-email", json={"limit": 50})
    assert r1.status_code == 200
    assert r1.json() == {"scanned": 1, "sent": 1, "skipped": 0}
    assert len(provider.sent) == 1
    assert provider.sent[0]["to_email"] == "buyer@example.com"
    assert "OTP" in provider.sent[0]["subject"]

    r2 = test_client.post("/api/v1/notifications/process-email", json={"limit": 50})
    assert r2.status_code == 200
    assert r2.json() == {"scanned": 1, "sent": 0, "skipped": 1}
    assert len(provider.sent) == 1
