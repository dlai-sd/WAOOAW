from __future__ import annotations

import sys
from pathlib import Path

import httpx
import pytest


# Ensure PP backend root is importable when running inside Docker.
# Some pytest import modes can change sys.path during collection.
PP_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(PP_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(PP_BACKEND_ROOT))


@pytest.fixture
def app():
    from main_proxy import app as pp_app

    return pp_app


@pytest.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
