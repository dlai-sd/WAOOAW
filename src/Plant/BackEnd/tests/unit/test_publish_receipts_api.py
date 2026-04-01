from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.database import get_read_db_session
from models.publish_receipt import PublishReceiptModel


@pytest.mark.unit
def test_get_publish_receipts_returns_list(test_client):
    from main import app

    async def _fake_read_db():
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [
            PublishReceiptModel(
                id="receipt-1",
                post_id="post-1",
                destination_type="youtube",
                success=True,
                platform_post_id="yt-1",
                published_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
            )
        ]
        db.execute.return_value = result
        yield db

    app.dependency_overrides[get_read_db_session] = _fake_read_db
    try:
        response = test_client.get("/api/v1/publish-receipts/inst-1")
    finally:
        app.dependency_overrides.pop(get_read_db_session, None)

    assert response.status_code == 200
    assert response.json()[0]["post_id"] == "post-1"
    assert response.json()[0]["platform_post_id"] == "yt-1"
