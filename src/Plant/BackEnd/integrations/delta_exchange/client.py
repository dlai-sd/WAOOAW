from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional

import httpx


@dataclass(frozen=True)
class DeltaCredentials:
    api_key: str
    api_secret: str  # keep in memory only


@dataclass(frozen=True)
class DeltaExchangeError(Exception):
    message: str
    status_code: Optional[int] = None
    correlation_id: Optional[str] = None

    def __str__(self) -> str:  # pragma: no cover
        parts = [self.message]
        if self.status_code is not None:
            parts.append(f"status={self.status_code}")
        if self.correlation_id:
            parts.append(f"correlation_id={self.correlation_id}")
        return " ".join(parts)


def _b64url_no_pad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _canonical_signing_payload(*, timestamp: int, method: str, path: str, body: str) -> str:
    # Intentionally simple + deterministic for tests.
    return "|".join([str(int(timestamp)), method.upper(), path, body])


def sign_delta_request(*, secret: str, timestamp: int, method: str, path: str, body: str) -> str:
    payload = _canonical_signing_payload(timestamp=timestamp, method=method, path=path, body=body)
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_no_pad(digest)


def _redact_value(value: str, secrets: Iterable[str]) -> str:
    redacted = value
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "***")
    return redacted


class DeltaExchangeClient:
    """Minimal allowlisted HTTP client wrapper for Delta Exchange (MVP).

    Note: The exact signing scheme can be swapped later; we only guarantee:
    - allowlist enforced
    - secrets not leaked in exceptions
    """

    PLACE_ORDER_PATH = "/v2/orders"
    CLOSE_POSITION_PATH = "/v2/positions/close"

    def __init__(
        self,
        *,
        base_url: str,
        credentials: DeltaCredentials,
        timeout_seconds: float = 10.0,
        max_retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._credentials = credentials
        self._timeout = timeout_seconds
        self._max_retries = max(0, int(max_retries))
        self._transport = transport

        self._allowed_paths = {
            self.PLACE_ORDER_PATH,
            self.CLOSE_POSITION_PATH,
        }

    def _headers(self, *, method: str, path: str, body_json: str, correlation_id: Optional[str]) -> Dict[str, str]:
        ts = int(time.time())
        signature = sign_delta_request(
            secret=self._credentials.api_secret,
            timestamp=ts,
            method=method,
            path=path,
            body=body_json,
        )

        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self._credentials.api_key,
            "X-SIGNATURE": signature,
            "X-TIMESTAMP": str(ts),
        }
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        return headers

    async def _request(
        self,
        *,
        method: str,
        path: str,
        json_body: Mapping[str, Any],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if path not in self._allowed_paths:
            raise DeltaExchangeError(
                f"Endpoint not allowlisted: {path}",
                status_code=None,
                correlation_id=correlation_id,
            )

        body_json = json.dumps(dict(json_body), separators=(",", ":"), sort_keys=True)
        url = f"{self._base_url}{path}"
        headers = self._headers(method=method, path=path, body_json=body_json, correlation_id=correlation_id)

        secrets = [self._credentials.api_secret, self._credentials.api_key]

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout, transport=self._transport) as client:
                    resp = await client.request(method=method, url=url, headers=headers, content=body_json)

                if resp.status_code >= 400:
                    text = ""
                    try:
                        text = resp.text
                    except Exception:
                        text = ""

                    safe_text = _redact_value(text, secrets)
                    safe_url = _redact_value(url, secrets)
                    raise DeltaExchangeError(
                        f"Delta request failed: {safe_url} {safe_text}".strip(),
                        status_code=resp.status_code,
                        correlation_id=correlation_id,
                    )

                try:
                    data = resp.json()
                except Exception as exc:  # noqa: BLE001
                    raise DeltaExchangeError(
                        "Delta response was not valid JSON",
                        status_code=resp.status_code,
                        correlation_id=correlation_id,
                    ) from exc

                if not isinstance(data, dict):
                    raise DeltaExchangeError(
                        "Delta response JSON must be an object",
                        status_code=resp.status_code,
                        correlation_id=correlation_id,
                    )

                return data

            except DeltaExchangeError:
                raise
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt >= self._max_retries:
                    msg = _redact_value(str(exc), secrets)
                    raise DeltaExchangeError(
                        f"Delta request error: {msg}",
                        status_code=None,
                        correlation_id=correlation_id,
                    ) from exc

                # Backoff: 50ms, 100ms, 200ms...
                await asyncio.sleep(0.05 * (2**attempt))

        raise DeltaExchangeError(
            "Delta request failed",
            status_code=None,
            correlation_id=correlation_id,
        ) from last_exc

    async def place_order(self, payload: Mapping[str, Any], *, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._request(
            method="POST",
            path=self.PLACE_ORDER_PATH,
            json_body=payload,
            correlation_id=correlation_id,
        )

    async def close_position(self, payload: Mapping[str, Any], *, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        return await self._request(
            method="POST",
            path=self.CLOSE_POSITION_PATH,
            json_body=payload,
            correlation_id=correlation_id,
        )
