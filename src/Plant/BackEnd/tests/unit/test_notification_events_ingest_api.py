import pytest


@pytest.mark.unit
def test_notification_events_ingest_requires_registration_key(test_client, monkeypatch):
    from services import notification_events

    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-registration-key")
    notification_events.default_notification_event_store.cache_clear()

    resp = test_client.post(
        "/api/v1/notifications/events",
        json={"event_type": "otp_sent", "metadata": {"flow": "registration"}},
    )
    assert resp.status_code == 401


@pytest.mark.unit
def test_notification_events_ingest_appends_event(test_client, monkeypatch):
    from services import notification_events

    monkeypatch.setenv("CP_REGISTRATION_KEY", "test-registration-key")
    notification_events.default_notification_event_store.cache_clear()

    resp = test_client.post(
        "/api/v1/notifications/events",
        json={"event_type": "otp_sent", "metadata": {"flow": "registration"}},
        headers={"X-CP-Registration-Key": "test-registration-key"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    store = notification_events.get_notification_event_store()
    rows = store.list_records(limit=10)
    assert any(r.event_type == "otp_sent" for r in rows)
