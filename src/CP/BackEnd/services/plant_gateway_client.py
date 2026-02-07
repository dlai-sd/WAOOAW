"""Plant Gateway client (CP).

CP needs a customer-scoped way to interact with Plant endpoints without
allowing the browser to spoof customer_id query params.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass(frozen=True)
class PlantGatewayResponse:
    status_code: int
    json: Any
    headers: Dict[str, str]


class PlantGatewayClient:
    def __init__(self, *, base_url: str, timeout_seconds: float = 15.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def request_json(
        self,
        *,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Any = None,
        params: Optional[Dict[str, str]] = None,
    ) -> PlantGatewayResponse:
        url = f"{self._base_url}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.request(method=method, url=url, headers=headers, json=json_body, params=params)
        payload: Any = None
        try:
            payload = resp.json()
        except Exception:
            payload = resp.text
        return PlantGatewayResponse(status_code=resp.status_code, json=payload, headers=dict(resp.headers))
