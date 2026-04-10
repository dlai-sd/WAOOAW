from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Protocol

from pydantic import BaseModel, Field

from agent_mold.skills.playbook import ArtifactType, GeneratedArtifactReference
from core.config import get_settings
from core.logging import PiiMaskingFilter


logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())


class StoredArtifact(BaseModel):
    artifact_type: ArtifactType
    uri: str = Field(..., min_length=1)
    preview_uri: Optional[str] = None
    mime_type: str = Field(..., min_length=1)
    size_bytes: int = Field(..., ge=0)
    preview_capable: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def as_generated_reference(self) -> GeneratedArtifactReference:
        return GeneratedArtifactReference(
            artifact_type=self.artifact_type,
            uri=self.uri,
            preview_uri=self.preview_uri,
            mime_type=self.mime_type,
            metadata={
                **self.metadata,
                "size_bytes": self.size_bytes,
                "preview_capable": self.preview_capable,
            },
        )


class MediaArtifactStore(Protocol):
    async def store_artifact(
        self,
        *,
        batch_id: str,
        post_id: str,
        artifact_type: ArtifactType,
        filename: str,
        content: bytes,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        preview_filename: Optional[str] = None,
        preview_content: Optional[bytes] = None,
        preview_mime_type: Optional[str] = None,
    ) -> StoredArtifact:
        ...


class LocalMediaArtifactStore:
    def __init__(
        self,
        *,
        root_dir: str,
        public_base_url: Optional[str] = None,
        max_bytes: int = 25 * 1024 * 1024,
    ) -> None:
        self._root_dir = Path(root_dir).expanduser().resolve()
        self._public_base_url = (public_base_url or "").strip().rstrip("/") or None
        self._max_bytes = max_bytes

    async def store_artifact(
        self,
        *,
        batch_id: str,
        post_id: str,
        artifact_type: ArtifactType,
        filename: str,
        content: bytes,
        mime_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        preview_filename: Optional[str] = None,
        preview_content: Optional[bytes] = None,
        preview_mime_type: Optional[str] = None,
    ) -> StoredArtifact:
        if len(content) > self._max_bytes:
            raise ValueError("artifact content exceeds configured max bytes")

        safe_batch_id = _sanitize_path_part(batch_id)
        safe_post_id = _sanitize_path_part(post_id)
        safe_filename = _sanitize_path_part(filename)
        relative_dir = Path(safe_batch_id) / safe_post_id
        target_dir = self._root_dir / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = target_dir / safe_filename
        artifact_path.write_bytes(content)

        preview_uri: Optional[str] = None
        if preview_filename and preview_content is not None and preview_mime_type:
            safe_preview_filename = _sanitize_path_part(preview_filename)
            preview_path = target_dir / safe_preview_filename
            preview_path.write_bytes(preview_content)
            preview_uri = self._build_uri(relative_dir / safe_preview_filename)

        return StoredArtifact(
            artifact_type=artifact_type,
            uri=self._build_uri(relative_dir / safe_filename),
            preview_uri=preview_uri,
            mime_type=mime_type,
            size_bytes=len(content),
            preview_capable=preview_uri is not None,
            metadata={
                **(metadata or {}),
                "storage_backend": "local",
                "relative_path": (relative_dir / safe_filename).as_posix(),
            },
        )

    def _build_uri(self, relative_path: Path) -> str:
        path_text = relative_path.as_posix()
        if self._public_base_url:
            return f"{self._public_base_url}/{path_text}"
        return f"local://{path_text}"


def _sanitize_path_part(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in value)


@lru_cache(maxsize=1)
def get_media_artifact_store() -> MediaArtifactStore:
    settings = get_settings()
    if settings.media_artifact_store_backend == "local":
        return LocalMediaArtifactStore(
            root_dir=settings.media_artifact_local_root,
            public_base_url=settings.media_artifact_public_base_url,
            max_bytes=settings.media_artifact_max_bytes,
        )
    raise ValueError(f"Unsupported media artifact store backend: {settings.media_artifact_store_backend}")