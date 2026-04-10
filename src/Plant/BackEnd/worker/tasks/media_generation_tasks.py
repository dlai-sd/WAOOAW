from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Tuple
from uuid import uuid4

from core.logging import get_logger
from worker.celery_app import celery_app


logger = get_logger(__name__)


@celery_app.task(
    name="generate_media_artifact",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
    acks_late=True,
)
def generate_media_artifact(self, payload: Dict[str, Any]) -> Dict[str, Any]:  # noqa: ARG001
    """Generate image/video/audio artifacts and update the draft post DB row.

    Artifact type dispatch:
    - image      → XAI Aurora image generation (xai_generate_image)
    - video      → Grok text LLM video script  (grok_generate_script)
    - audio      → Grok text LLM audio/narration script
    - video_audio→ Grok text LLM combined storyboard + narration
    """
    try:
        return asyncio.get_event_loop().run_until_complete(_run_media_generation(payload))
    except RuntimeError:
        # New event loop when called from a non-async context
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_run_media_generation(payload))
        finally:
            loop.close()


async def _run_media_generation(payload: Dict[str, Any]) -> Dict[str, Any]:
    from agent_mold.skills.grok_client import (
        GrokClientError,
        get_grok_client,
        grok_generate_script,
        xai_generate_image,
    )
    from services.draft_batches import DatabaseDraftBatchStore
    from services.media_artifact_store import get_media_artifact_store
    from core.database import get_db_session
    from sqlalchemy.ext.asyncio import AsyncSession

    batch_id: str = payload.get("batch_id", "")
    post_id: str = payload.get("post_id", "")
    channel: str = payload.get("channel", "youtube")
    theme: str = payload.get("theme", "")
    brand_name: str = payload.get("brand_name", "")
    text: str = payload.get("text", "")
    requested_artifacts = payload.get("requested_artifacts", [])

    if not (batch_id and post_id):
        logger.warning("generate_media_artifact: missing batch_id or post_id", extra={"payload_keys": list(payload)})
        return {**payload, "status": "skipped", "reason": "missing_ids"}

    # Determine artifact type from first requested artifact
    first_artifact_type: str = "image"
    first_prompt: str = f"Create a {channel} marketing visual for: {theme} — {brand_name}"
    if requested_artifacts:
        first = requested_artifacts[0]
        first_artifact_type = first.get("artifact_type", "image")
        first_prompt = first.get("prompt", first_prompt)

    media_store = get_media_artifact_store()
    results: Dict[str, Any] = {}

    try:
        client = get_grok_client()
    except GrokClientError:
        logger.warning("generate_media_artifact: XAI_API_KEY not set — leaving artifact queued")
        return {**payload, "status": "deferred", "reason": "no_api_key"}

    # --- Generate the artifact ---
    if first_artifact_type == "image":
        image_bytes = xai_generate_image(client, first_prompt)
        mime = "image/svg+xml" if image_bytes[:5] == b"<svg " else "image/jpeg"
        ext = "svg" if mime == "image/svg+xml" else "jpg"
        stored = await media_store.store_artifact(
            batch_id=batch_id,
            post_id=post_id,
            artifact_type=__import__("agent_mold.skills.playbook", fromlist=["ArtifactType"]).ArtifactType.IMAGE,
            filename=f"{channel}-image.{ext}",
            content=image_bytes,
            mime_type=mime,
            metadata={"source": "xai_aurora", "prompt": first_prompt},
        )
        results = {
            "artifact_uri": stored.uri,
            "artifact_mime_type": stored.mime_type,
            "artifact_generation_status": "ready",
        }
    else:
        # video, audio, video_audio → Grok text script
        script_md = grok_generate_script(
            client,
            artifact_type=first_artifact_type,
            theme=theme,
            brand_name=brand_name,
            post_text=text,
            channel=channel,
        )
        from agent_mold.skills.playbook import ArtifactType as _AT
        _type_map = {
            "video": _AT.VIDEO,
            "audio": _AT.AUDIO,
            "video_audio": _AT.VIDEO_AUDIO,
        }
        _art_type = _type_map.get(first_artifact_type, _AT.VIDEO)
        stored = await media_store.store_artifact(
            batch_id=batch_id,
            post_id=post_id,
            artifact_type=_art_type,
            filename=f"{channel}-{first_artifact_type}-script.md",
            content=script_md.encode("utf-8"),
            mime_type="text/markdown",
            metadata={"source": "grok_script", "artifact_type": first_artifact_type},
        )
        results = {
            "artifact_uri": stored.uri,
            "artifact_mime_type": "text/markdown",
            "artifact_generation_status": "ready",
        }

    # --- Persist result to DB ---
    try:
        async for db in get_db_session():
            store = DatabaseDraftBatchStore(db)
            await store.update_post(
                post_id,
                artifact_uri=results.get("artifact_uri"),
                artifact_mime_type=results.get("artifact_mime_type"),
                artifact_generation_status="ready",
                artifact_job_id=None,
            )
            await db.commit()
            break
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "generate_media_artifact: failed to persist artifact update",
            extra={"post_id": post_id, "error": str(exc)},
        )
        return {**payload, **results, "db_persist": "failed"}

    logger.info(
        "generate_media_artifact: completed",
        extra={"post_id": post_id, "artifact_type": first_artifact_type, "uri": results.get("artifact_uri")},
    )
    return {**payload, **results}


def enqueue_media_generation_job(*, payload: Dict[str, Any]) -> Tuple[str, str]:
    job_id = str(payload.get("job_id") or uuid4())
    queue_enabled = os.getenv("MEDIA_ARTIFACT_QUEUE_ENABLED", "false").strip().lower() == "true"
    if not queue_enabled:
        return job_id, "deferred"

    try:
        generate_media_artifact.apply_async(kwargs={"payload": {**payload, "job_id": job_id}}, task_id=job_id)
        return job_id, "celery"
    except Exception as exc:
        logger.warning(
            "Failed to enqueue media artifact job; leaving draft in deferred queued state",
            extra={"artifact_job_id": job_id, "error": str(exc)},
        )
        return job_id, "deferred"
