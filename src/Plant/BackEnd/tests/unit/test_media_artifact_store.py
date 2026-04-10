from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from agent_mold.skills.playbook import ArtifactType
from core.config import Settings
from services.media_artifact_store import LocalMediaArtifactStore


@pytest.mark.asyncio
async def test_local_media_artifact_store_persists_bytes_and_returns_provider_neutral_metadata(tmp_path: Path) -> None:
    store = LocalMediaArtifactStore(
        root_dir=str(tmp_path),
        public_base_url="https://cdn.waooaw.test/media",
        max_bytes=1024,
    )

    stored = await store.store_artifact(
        batch_id="batch-1",
        post_id="post-1",
        artifact_type=ArtifactType.TABLE,
        filename="preview.csv",
        content=b"a,b\n1,2\n",
        mime_type="text/csv",
        metadata={"generation_status": "ready"},
    )

    assert stored.uri == "https://cdn.waooaw.test/media/batch-1/post-1/preview.csv"
    assert stored.mime_type == "text/csv"
    assert stored.size_bytes == len(b"a,b\n1,2\n")
    assert stored.metadata["storage_backend"] == "local"
    assert (tmp_path / "batch-1" / "post-1" / "preview.csv").read_bytes() == b"a,b\n1,2\n"


def test_settings_reject_invalid_media_artifact_store_backend() -> None:
    with pytest.raises(ValidationError):
        Settings(media_artifact_store_backend="gcs")


def test_settings_reject_non_positive_media_artifact_max_bytes() -> None:
    with pytest.raises(ValidationError):
        Settings(media_artifact_max_bytes=0)