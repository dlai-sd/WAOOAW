"""Unit tests for integrations.delta_exchange.hmac_auth (feat/delta-exchange-real-credentials).

Tests:
  T1: build_auth_headers returns exactly the three required keys
  T2: timestamp is a valid integer epoch string
  T3: signature is a hex string (64 chars for SHA-256)
  T4: different api_secrets produce different signatures
  T5: same inputs always produce the same signature (deterministic modulo timestamp)
  T6: method is uppercased in the signing input
  T7: DELTA_EXCHANGE_BASE_URL is the expected endpoint
"""
from __future__ import annotations

import hashlib
import hmac
import time


def test_build_auth_headers_keys():
    """T1: returned dict has exactly api-key, timestamp, signature."""
    from integrations.delta_exchange.hmac_auth import build_auth_headers

    result = build_auth_headers(
        api_key="test_key",
        api_secret="test_secret",
        method="GET",
        path="/v2/wallet/balances",
    )
    assert set(result.keys()) == {"api-key", "timestamp", "signature"}
    assert result["api-key"] == "test_key"


def test_timestamp_is_integer_string():
    """T2: timestamp is a string representation of an integer epoch."""
    from integrations.delta_exchange.hmac_auth import build_auth_headers

    result = build_auth_headers(
        api_key="k", api_secret="s", method="GET", path="/v2/profile"
    )
    ts = int(result["timestamp"])  # must not raise
    # Sanity: within 60 seconds of now
    assert abs(ts - int(time.time())) < 60


def test_signature_is_hex_string():
    """T3: signature is a 64-character lowercase hex string (SHA-256 output)."""
    from integrations.delta_exchange.hmac_auth import build_auth_headers

    result = build_auth_headers(
        api_key="k", api_secret="secret", method="GET", path="/v2/wallet/balances"
    )
    sig = result["signature"]
    assert len(sig) == 64
    assert all(c in "0123456789abcdef" for c in sig)


def test_signature_matches_manual_calculation():
    """T4: signature matches manually computed HMAC-SHA256 for the same inputs."""
    from integrations.delta_exchange.hmac_auth import build_auth_headers

    api_secret = "mysecret"
    method = "GET"
    path = "/v2/wallet/balances"

    result = build_auth_headers(api_key="k", api_secret=api_secret, method=method, path=path)
    timestamp = result["timestamp"]

    expected_message = method.upper() + timestamp + path
    expected_sig = hmac.new(
        api_secret.encode("utf-8"),
        expected_message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert result["signature"] == expected_sig


def test_different_secrets_produce_different_signatures():
    """T5: changing api_secret changes the signature."""
    from integrations.delta_exchange.hmac_auth import build_auth_headers

    h1 = build_auth_headers(api_key="k", api_secret="secret_a", method="GET", path="/v2/profile")
    h2 = build_auth_headers(api_key="k", api_secret="secret_b", method="GET", path="/v2/profile")
    assert h1["signature"] != h2["signature"]


def test_method_case_normalised():
    """T6: lowercase method produces the same signature as uppercase method."""
    from integrations.delta_exchange.hmac_auth import build_auth_headers

    h_upper = build_auth_headers(api_key="k", api_secret="s", method="GET", path="/v2/products")
    h_lower = build_auth_headers(api_key="k", api_secret="s", method="get", path="/v2/products")
    # The signatures should match because method is uppercased internally
    # BUT timestamps are re-generated so we can't compare directly — verify the message
    # by checking that the signature of h_lower uses "GET" not "get" in the message.
    ts_lower = h_lower["timestamp"]
    expected = hmac.new(
        b"s",
        ("GET" + ts_lower + "/v2/products").encode(),
        hashlib.sha256,
    ).hexdigest()
    assert h_lower["signature"] == expected


def test_base_url_constant():
    """T7: DELTA_EXCHANGE_BASE_URL and DELTA_EXCHANGE_INDIA_BASE_URL are correct."""
    from integrations.delta_exchange.hmac_auth import (
        DELTA_EXCHANGE_BASE_URL,
        DELTA_EXCHANGE_INDIA_BASE_URL,
        base_url_for_provider,
    )
    assert DELTA_EXCHANGE_BASE_URL == "https://api.delta.exchange"
    assert DELTA_EXCHANGE_INDIA_BASE_URL == "https://api.india.delta.exchange"
    assert not DELTA_EXCHANGE_BASE_URL.endswith("/")
    assert not DELTA_EXCHANGE_INDIA_BASE_URL.endswith("/")

    # Provider routing
    assert base_url_for_provider("delta_exchange_india") == DELTA_EXCHANGE_INDIA_BASE_URL
    assert base_url_for_provider("delta_exchange") == DELTA_EXCHANGE_BASE_URL
    # Unknown provider defaults to India (the app is India-first)
    assert base_url_for_provider("unknown_provider") == DELTA_EXCHANGE_INDIA_BASE_URL
