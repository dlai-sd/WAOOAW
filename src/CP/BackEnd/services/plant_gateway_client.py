"""Plant Gateway client (CP).

CP needs a customer-scoped way to interact with Plant endpoints without
allowing the browser to spoof customer_id query params.

C3 (NFR It-3): Circuit breaker wraps every request.
- Opens after 3 failures within 10 seconds; recovers after 30 seconds.
- When open: raises ServiceUnavailableError immediately (no HTTP call made).
- Shares the same CircuitBreaker + ServiceUnavailableError from plant_client.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from services.plant_client import CircuitBreaker, ServiceUnavailableError

logger = logging.getLogger(__name__)

# Module-level circuit breaker shared across all PlantGatewayClient instances
_circuit_breaker = CircuitBreaker()


@dataclass(frozen=True)
class PlantGatewayResponse:
    status_code: int
    json: Any
    headers: Dict[str, str]


class PlantGatewayClient:
    def __init__(
        self,
        *,
        base_url: str,
        timeout_seconds: float = 15.0,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._cb = circuit_breaker or _circuit_breaker

    async def request_json(
        self,
        *,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        json_body: Any = None,
        params: Optional[Dict[str, str]] = None,
    ) -> PlantGatewayResponse:
        if not self._cb.is_call_permitted():
            logger.warning(
                "plant_gateway_client: circuit open — fast-failing %s %s",
                method,
                path,
            )
            raise ServiceUnavailableError("Plant Gateway circuit is open")

        url = f"{self._base_url}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_body,
                    params=params,
                )
        except httpx.TimeoutException as exc:
            self._cb.record_failure()
            raise ServiceUnavailableError("Plant Gateway request timed out") from exc
        except httpx.ConnectError as exc:
            self._cb.record_failure()
            raise ServiceUnavailableError("Cannot connect to Plant Gateway") from exc
        except Exception as exc:
            self._cb.record_failure()
            raise ServiceUnavailableError(str(exc)) from exc

        if resp.status_code >= 500:
            self._cb.record_failure()
        else:
            self._cb.record_success()

        payload: Any = None
        try:
            payload = resp.json()
        except Exception:
            payload = resp.text
        return PlantGatewayResponse(
            status_code=resp.status_code,
            json=payload,
            headers=dict(resp.headers),
        )
