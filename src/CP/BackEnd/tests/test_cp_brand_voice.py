from __future__ import annotations

import pytest


class _FakePlantClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def request_json(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class _FakeAuditLogger:
    def __init__(self) -> None:
        self.calls = []

    async def log(self, *args, **kwargs):
        self.calls.append({"args": args, "kwargs": kwargs})


@pytest.mark.usefixtures("auth_headers")
def test_cp_brand_voice_get_proxies_success(client, auth_headers):
    from main import app
    from api.cp_brand_voice import get_plant_gateway_client

    fake = _FakePlantClient(
        type(
            "Response",
            (),
            {
                "status_code": 200,
                "json": {
                    "tone_keywords": ["warm"],
                    "vocabulary_preferences": [],
                    "messaging_patterns": [],
                    "example_phrases": [],
                    "voice_description": "Warm and clear",
                },
                "headers": {},
            },
        )()
    )
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake

    response = client.get("/api/cp/brand-voice", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["voice_description"] == "Warm and clear"
    app.dependency_overrides.clear()


@pytest.mark.usefixtures("auth_headers")
def test_cp_brand_voice_put_proxies_and_audits(client, auth_headers):
    from main import app
    from api.cp_brand_voice import get_plant_gateway_client
    from services.audit_dependency import get_audit_logger

    fake = _FakePlantClient(
        type(
            "Response",
            (),
            {
                "status_code": 200,
                "json": {
                    "tone_keywords": ["warm"],
                    "vocabulary_preferences": [],
                    "messaging_patterns": [],
                    "example_phrases": ["You can trust us."],
                    "voice_description": "Warm and clear",
                },
                "headers": {},
            },
        )()
    )
    audit = _FakeAuditLogger()
    app.dependency_overrides[get_plant_gateway_client] = lambda: fake
    app.dependency_overrides[get_audit_logger] = lambda: audit

    response = client.put(
        "/api/cp/brand-voice",
        headers=auth_headers,
        json={
            "tone_keywords": ["warm"],
            "vocabulary_preferences": [],
            "messaging_patterns": [],
            "example_phrases": ["You can trust us."],
            "voice_description": "Warm and clear",
        },
    )

    assert response.status_code == 200
    assert fake.calls[0]["method"] == "PUT"
    assert audit.calls
    app.dependency_overrides.clear()
