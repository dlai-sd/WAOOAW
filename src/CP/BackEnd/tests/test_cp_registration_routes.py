import json

import pytest


@pytest.mark.unit
def test_cp_register_happy_path_mints_id_and_normalizes(client, monkeypatch, tmp_path):
    store_path = tmp_path / "cp_registrations.jsonl"
    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(store_path))

    from services import cp_registrations

    cp_registrations.default_cp_registration_store.cache_clear()

    payload = {
        "fullName": "  Test User  ",
        "businessName": "  ACME Inc ",
        "businessIndustry": "marketing",
        "businessAddress": "Bengaluru, Karnataka, India",
        "email": "TEST@EXAMPLE.COM",
        "phone": "+91 98765 43210",
        "website": "https://example.com",
        "gstNumber": "29ABCDE1234F2Z5",
        "preferredContactMethod": "email",
        "consent": True,
    }

    resp = client.post("/api/cp/auth/register", json=payload)
    assert resp.status_code == 201
    body = resp.json()

    assert body["registration_id"].startswith("REG-")
    assert body["email"] == "test@example.com"
    assert body["phone"] == "+919876543210"

    lines = store_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    stored = json.loads(lines[0])
    assert stored["registration_id"] == body["registration_id"]
    assert stored["email"] == "test@example.com"
    assert stored["phone"] == "+919876543210"


@pytest.mark.unit
def test_cp_register_requires_consent(client, monkeypatch, tmp_path):
    store_path = tmp_path / "cp_registrations.jsonl"
    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(store_path))

    from services import cp_registrations

    cp_registrations.default_cp_registration_store.cache_clear()

    payload = {
        "fullName": "Test User",
        "businessName": "ACME",
        "businessIndustry": "marketing",
        "businessAddress": "Bengaluru",
        "email": "test@example.com",
        "phone": "+919876543210",
        "preferredContactMethod": "email",
        "consent": False,
    }

    resp = client.post("/api/cp/auth/register", json=payload)
    assert resp.status_code == 422


@pytest.mark.unit
def test_cp_register_rejects_bad_phone_format(client, monkeypatch, tmp_path):
    store_path = tmp_path / "cp_registrations.jsonl"
    monkeypatch.setenv("CP_REGISTRATIONS_STORE_PATH", str(store_path))

    from services import cp_registrations

    cp_registrations.default_cp_registration_store.cache_clear()

    payload = {
        "fullName": "Test User",
        "businessName": "ACME",
        "businessIndustry": "marketing",
        "businessAddress": "Bengaluru",
        "email": "test@example.com",
        "phone": "nope",
        "preferredContactMethod": "email",
        "consent": True,
    }

    resp = client.post("/api/cp/auth/register", json=payload)
    assert resp.status_code == 422
