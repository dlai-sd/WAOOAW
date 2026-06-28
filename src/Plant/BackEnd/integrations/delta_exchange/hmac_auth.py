"""Delta Exchange REST API — HMAC-SHA256 request signing.

Authentication format (all environments except test):
  message   = METHOD + str(timestamp_seconds) + path
  signature = HMAC-SHA256(api_secret, message).hexdigest()

Required headers on every authenticated request:
  api-key   : <api_key>
  timestamp : <unix_epoch_seconds_as_string>
  signature : <hex_digest>

Reference: https://docs.delta.exchange/#authentication

Note: this module intentionally contains NO httpx / networking code.
It is pure crypto so it can be unit-tested without any I/O.
NEVER log api_key, api_secret, or the returned signature dict.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Dict

# Public base URLs for Delta Exchange.
# These are SEPARATE platforms with separate accounts — a key from one
# will NOT work on the other.
DELTA_EXCHANGE_BASE_URL = "https://api.delta.exchange"          # International (crypto futures)
DELTA_EXCHANGE_INDIA_BASE_URL = "https://api.india.delta.exchange"  # India platform

# Provider-string → base URL mapping.  Add new providers here as needed.
PROVIDER_BASE_URL: dict[str, str] = {
    "delta_exchange_india": DELTA_EXCHANGE_INDIA_BASE_URL,
    "delta_exchange": DELTA_EXCHANGE_BASE_URL,
}


def base_url_for_provider(exchange_provider: str) -> str:
    """Return the correct base URL for a given exchange_provider string."""
    return PROVIDER_BASE_URL.get(exchange_provider, DELTA_EXCHANGE_INDIA_BASE_URL)


def build_auth_headers(
    *,
    api_key: str,
    api_secret: str,
    method: str,
    path: str,
) -> Dict[str, str]:
    """Return Delta Exchange authentication headers for one request.

    Args:
        api_key:    Delta Exchange API key (never logged).
        api_secret: Delta Exchange API secret used for signing (never logged).
        method:     HTTP method string — "GET", "POST", "DELETE", etc.
        path:       Request path **without** query string, e.g. "/v2/wallet/balances".
                    Delta Exchange's signature covers the path only, not the query string.

    Returns:
        Dict with exactly three keys: "api-key", "timestamp", "signature".
        Caller should merge these into the outgoing request headers.

    Security rules:
        - Never pass the returned dict to a logger.
        - Never cache the returned dict; generate fresh headers per request
          (the timestamp makes each signature unique).
    """
    timestamp = str(int(time.time()))
    # Delta Exchange signature data: METHOD + timestamp + path  (no query string, no body for GETs)
    message = method.upper() + timestamp + path
    signature = hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "api-key": api_key,
        "timestamp": timestamp,
        "signature": signature,
    }
