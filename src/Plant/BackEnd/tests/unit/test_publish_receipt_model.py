from __future__ import annotations

import uuid

import pytest

from models.publish_receipt import PublishReceiptModel


@pytest.mark.unit
def test_publish_receipt_model_instantiation_generates_fields():
    receipt = PublishReceiptModel(
        post_id="p1",
        destination_type="youtube",
        success=True,
        platform_post_id="yt123",
    )

    assert receipt.post_id == "p1"
    assert receipt.destination_type == "youtube"
    assert receipt.success is True
    assert receipt.platform_post_id == "yt123"
    assert uuid.UUID(receipt.id)
    assert receipt.created_at is not None
