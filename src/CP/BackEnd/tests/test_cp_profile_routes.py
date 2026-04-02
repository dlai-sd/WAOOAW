"""Tests for PATCH /api/cp/profile — E4-S1 (CP-NAV-1 Iteration 2)."""

import pytest


@pytest.mark.unit
def test_get_profile_unauthenticated(client):
    """GET /api/cp/profile without token returns 401."""
    resp = client.get("/api/cp/profile")
    assert resp.status_code == 401


@pytest.mark.unit
def test_get_profile_authenticated(client, auth_headers):
    """GET /api/cp/profile returns the current user's profile."""
    resp = client.get("/api/cp/profile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.unit
def test_patch_profile_unauthenticated(client):
    """PATCH /api/cp/profile without token returns 401."""
    resp = client.patch("/api/cp/profile", json={"full_name": "Alice"})
    assert resp.status_code == 401


@pytest.mark.unit
def test_patch_profile_updates_full_name(client, auth_headers):
    """PATCH /api/cp/profile updates full_name."""
    resp = client.patch(
        "/api/cp/profile",
        json={"full_name": "Alice Wonderland"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Alice Wonderland"


@pytest.mark.unit
def test_patch_profile_updates_phone_and_business(client, auth_headers):
    """PATCH /api/cp/profile updates phone and business_name."""
    resp = client.patch(
        "/api/cp/profile",
        json={"phone": "+919876543210", "business_name": "ACME Ltd"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone"] == "+919876543210"
    assert data["business_name"] == "ACME Ltd"


@pytest.mark.unit
def test_patch_profile_partial_update(client, auth_headers):
    """PATCH /api/cp/profile with empty body returns unchanged profile."""
    # First set a value
    client.patch(
        "/api/cp/profile",
        json={"full_name": "Bob"},
        headers=auth_headers,
    )
    # Patch with no fields — should return same profile
    resp = client.patch("/api/cp/profile", json={}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Bob"


@pytest.mark.unit
def test_patch_profile_updates_industry(client, auth_headers):
    """PATCH /api/cp/profile updates industry."""
    resp = client.patch(
        "/api/cp/profile",
        json={"industry": "marketing"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["industry"] == "marketing"


@pytest.mark.unit
def test_patch_profile_updates_location_timezone_and_primary_language(client, auth_headers):
    """PATCH /api/cp/profile updates the new profile identity fields."""
    response = client.patch(
        "/api/cp/profile",
        json={
            "location": "Mumbai",
            "timezone": "Asia/Kolkata",
            "primary_language": "Hindi",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Mumbai"
    assert data["timezone"] == "Asia/Kolkata"
    assert data["primary_language"] == "Hindi"


@pytest.mark.unit
def test_get_profile_returns_location_timezone_and_primary_language_after_patch(client, auth_headers):
    """GET /api/cp/profile returns the newly persisted identity fields."""
    client.patch(
        "/api/cp/profile",
        json={
            "location": "Mumbai",
            "timezone": "Asia/Kolkata",
            "primary_language": "Hindi",
        },
        headers=auth_headers,
    )

    response = client.get("/api/cp/profile", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Mumbai"
    assert data["timezone"] == "Asia/Kolkata"
    assert data["primary_language"] == "Hindi"
