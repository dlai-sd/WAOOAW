#!/usr/bin/env python3
"""Probe demo domains for OpenAPI/doc endpoints.

This is a lightweight network diagnostic: it does not require auth tokens and
only reads a small response body snippet to avoid hanging.
"""

from __future__ import annotations

import ssl
import sys
import urllib.error
import urllib.request


BASES = [
    "https://cp.demo.waooaw.com",
    "https://pp.demo.waooaw.com",
    "https://plant.demo.waooaw.com",
]

PATHS = [
    "/openapi.json",
    "/api/openapi.json",
    "/api/v1/openapi.json",
    "/docs",
    "/api/docs",
    "/redoc",
    "/api/redoc",
    "/api",
    "/health",
]


def probe(url: str, timeout_s: float = 8.0) -> tuple[int | None, str | None, str | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "waooaw-probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s, context=ssl.create_default_context()) as resp:
            status = resp.status
            content_type = resp.headers.get("content-type")
            location = resp.headers.get("location")
            # read a small snippet to ensure server actually responds
            resp.read(128)
            return status, content_type, location, None
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("content-type"), e.headers.get("location"), "HTTPError"
    except Exception as e:  # noqa: BLE001
        return None, None, None, f"{type(e).__name__}: {e}"


def main() -> int:
    for base in BASES:
        print("\n==============================")
        print(f"BASE: {base}")
        print("==============================")
        for path in PATHS:
            url = base + path
            status, content_type, location, err = probe(url)
            if err:
                print(f"{path:18} -> ERROR {err}")
            else:
                extra = f" location={location}" if location else ""
                print(f"{path:18} -> {status} content-type={content_type}{extra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
