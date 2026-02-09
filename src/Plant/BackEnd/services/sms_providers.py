"""SMS delivery providers.

NOTIF-1.3: Plant SMS provider integration (optional).

Phase-1 goals:
- Safe null provider by default.
- Optional webhook provider behind env flags.
"""

from __future__ import annotations

import os
from typing import Protocol

import httpx


class SmsProvider(Protocol):
    async def send_sms(self, *, to_phone: str, message: str) -> None: ...


class NullSmsProvider:
    async def send_sms(self, *, to_phone: str, message: str) -> None:
        return


class WebhookSmsProvider:
    def __init__(self, *, url: str, bearer_token: str | None = None) -> None:
        self._url = url
        self._bearer_token = bearer_token

    async def send_sms(self, *, to_phone: str, message: str) -> None:
        headers: dict[str, str] = {"content-type": "application/json"}
        if self._bearer_token:
            headers["authorization"] = f"Bearer {self._bearer_token}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                self._url,
                json={
                    "to_phone": to_phone,
                    "message": message,
                },
                headers=headers,
            )
            resp.raise_for_status()


def get_sms_provider() -> SmsProvider:
    provider = (os.getenv("SMS_PROVIDER") or "null").strip().lower()
    if provider != "webhook":
        return NullSmsProvider()

    url = (os.getenv("SMS_WEBHOOK_URL") or "").strip()
    if not url:
        return NullSmsProvider()

    token = (os.getenv("SMS_WEBHOOK_BEARER_TOKEN") or "").strip() or None
    return WebhookSmsProvider(url=url, bearer_token=token)
