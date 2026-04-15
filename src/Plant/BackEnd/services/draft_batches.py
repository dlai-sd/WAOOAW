"""Draft batch storage.

Marketing drafts are persisted in PostgreSQL and accessed through an async store.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agent_mold.skills.playbook import ChannelName, GeneratedArtifactReference
from models.marketing_draft import MarketingDraftBatchModel, MarketingDraftPostModel


_UNSET = object()


DraftReviewStatus = Literal["pending_review", "approved", "changes_requested", "rejected"]
DraftExecutionStatus = Literal["not_scheduled", "scheduled", "running", "posted", "failed"]
DraftArtifactType = Literal["text", "table", "image", "audio", "video", "video_audio"]
DraftArtifactGenerationStatus = Literal["not_requested", "queued", "running", "ready", "failed"]


class DraftPostRecord(BaseModel):
    post_id: str = Field(..., min_length=1)
    channel: ChannelName
    text: str = Field(..., min_length=1)
    hashtags: List[str] = Field(default_factory=list)
    artifact_type: DraftArtifactType = "text"
    artifact_uri: Optional[str] = None
    artifact_preview_uri: Optional[str] = None
    artifact_mime_type: Optional[str] = None
    artifact_metadata: Dict[str, Any] = Field(default_factory=dict)
    artifact_generation_status: DraftArtifactGenerationStatus = "not_requested"
    artifact_job_id: Optional[str] = None
    generated_artifacts: List[GeneratedArtifactReference] = Field(default_factory=list)

    review_status: DraftReviewStatus = "pending_review"
    approval_id: Optional[str] = None
    credential_ref: Optional[str] = None
    execution_status: DraftExecutionStatus = "not_scheduled"
    visibility: str = "private"
    public_release_requested: bool = False

    scheduled_at: Optional[datetime] = None

    attempts: int = 0
    last_error: Optional[str] = None

    provider_post_id: Optional[str] = None
    provider_post_url: Optional[str] = None
    publish_ready: bool = False
    publish_readiness_hint: Optional[str] = None


class DraftBatchRecord(BaseModel):
    batch_id: str = Field(..., min_length=1)
    batch_type: str = "direct"  # theme | content | direct
    parent_batch_id: Optional[str] = None
    agent_id: str = Field(..., min_length=1)
    hired_instance_id: Optional[str] = None
    campaign_id: Optional[str] = None
    customer_id: Optional[str] = None

    theme: str = Field(..., min_length=1)
    brand_name: str = Field(..., min_length=1)
    brief_summary: Optional[str] = None

    created_at: datetime
    status: DraftReviewStatus = "pending_review"
    workflow_state: str = "draft_ready_for_review"

    posts: List[DraftPostRecord] = Field(default_factory=list)


class DatabaseDraftBatchStore:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_batch(self, batch: DraftBatchRecord) -> None:
        batch_model = MarketingDraftBatchModel(
            batch_id=batch.batch_id,
            batch_type=batch.batch_type,
            parent_batch_id=batch.parent_batch_id,
            agent_id=batch.agent_id,
            hired_instance_id=batch.hired_instance_id,
            campaign_id=batch.campaign_id,
            customer_id=batch.customer_id,
            theme=batch.theme,
            brand_name=batch.brand_name,
            brief_summary=batch.brief_summary,
            created_at=batch.created_at,
            status=batch.status,
            workflow_state=batch.workflow_state,
        )
        for post in batch.posts:
            batch_model.posts.append(self._record_to_post_model(post, batch.campaign_id))
        self._session.add(batch_model)
        await self._session.flush()

    async def find_post(self, post_id: str) -> tuple[DraftBatchRecord, DraftPostRecord] | None:
        result = await self._session.execute(
            select(MarketingDraftPostModel)
            .options(
                selectinload(MarketingDraftPostModel.batch)
                .selectinload(MarketingDraftBatchModel.posts)
            )
            .where(MarketingDraftPostModel.post_id == post_id)
        )
        post_model = result.scalars().first()
        if post_model is None or post_model.batch is None:
            return None
        batch = self._batch_model_to_record(post_model.batch)
        match = next((post for post in batch.posts if post.post_id == post_id), None)
        if match is None:
            return None
        return batch, match

    async def get_batch(self, batch_id: str) -> DraftBatchRecord | None:
        result = await self._session.execute(
            select(MarketingDraftBatchModel)
            .options(selectinload(MarketingDraftBatchModel.posts))
            .where(MarketingDraftBatchModel.batch_id == batch_id)
        )
        model = result.scalars().first()
        return self._batch_model_to_record(model) if model is not None else None

    async def load_batches(self) -> List[DraftBatchRecord]:
        result = await self._session.execute(
            select(MarketingDraftBatchModel)
            .options(selectinload(MarketingDraftBatchModel.posts))
            .order_by(MarketingDraftBatchModel.created_at.asc())
        )
        return [self._batch_model_to_record(model) for model in result.scalars().all()]

    async def update_post(
        self,
        post_id: str,
        *,
        artifact_type: DraftArtifactType | object = _UNSET,
        artifact_uri: str | None | object = _UNSET,
        artifact_preview_uri: str | None | object = _UNSET,
        artifact_mime_type: str | None | object = _UNSET,
        artifact_metadata: Dict[str, Any] | object = _UNSET,
        artifact_generation_status: DraftArtifactGenerationStatus | object = _UNSET,
        artifact_job_id: str | None | object = _UNSET,
        generated_artifacts: List[GeneratedArtifactReference] | List[Dict[str, Any]] | object = _UNSET,
        review_status: DraftReviewStatus | object = _UNSET,
        approval_id: str | None | object = _UNSET,
        credential_ref: str | None | object = _UNSET,
        execution_status: DraftExecutionStatus | object = _UNSET,
        visibility: str | object = _UNSET,
        public_release_requested: bool | object = _UNSET,
        scheduled_at: datetime | None | object = _UNSET,
        attempts: int | object = _UNSET,
        last_error: str | None | object = _UNSET,
        provider_post_id: str | None | object = _UNSET,
        provider_post_url: str | None | object = _UNSET,
    ) -> bool:
        result = await self._session.execute(
            select(MarketingDraftPostModel)
            .options(
                selectinload(MarketingDraftPostModel.batch)
                .selectinload(MarketingDraftBatchModel.posts)
            )
            .where(MarketingDraftPostModel.post_id == post_id)
        )
        post_model = result.scalars().first()
        if post_model is None:
            return False

        if artifact_type is not _UNSET:
            post_model.artifact_type = artifact_type
        if artifact_uri is not _UNSET:
            post_model.artifact_uri = artifact_uri
        if artifact_preview_uri is not _UNSET:
            post_model.artifact_preview_uri = artifact_preview_uri
        if artifact_mime_type is not _UNSET:
            post_model.artifact_mime_type = artifact_mime_type
        if artifact_metadata is not _UNSET:
            post_model.artifact_metadata = artifact_metadata
        if artifact_generation_status is not _UNSET:
            post_model.artifact_generation_status = artifact_generation_status
        if artifact_job_id is not _UNSET:
            post_model.artifact_job_id = artifact_job_id
        if generated_artifacts is not _UNSET:
            post_model.generated_artifacts = [
                artifact.model_dump(mode="json") if isinstance(artifact, GeneratedArtifactReference) else artifact
                for artifact in generated_artifacts
            ]
        if review_status is not _UNSET:
            post_model.review_status = review_status
        if approval_id is not _UNSET:
            post_model.approval_id = approval_id
        if credential_ref is not _UNSET:
            post_model.credential_ref = credential_ref
        if execution_status is not _UNSET:
            post_model.execution_status = execution_status
        if visibility is not _UNSET:
            post_model.visibility = visibility
        if public_release_requested is not _UNSET:
            post_model.public_release_requested = public_release_requested
        if scheduled_at is not _UNSET:
            post_model.scheduled_at = scheduled_at
        if attempts is not _UNSET:
            post_model.attempts = attempts
        if last_error is not _UNSET:
            post_model.last_error = last_error
        if provider_post_id is not _UNSET:
            post_model.provider_post_id = provider_post_id
        if provider_post_url is not _UNSET:
            post_model.provider_post_url = provider_post_url
        post_model.updated_at = datetime.now(timezone.utc)

        if post_model.batch is not None:
            self._sync_batch_status(post_model.batch)

        await self._session.flush()
        return True

    def _sync_batch_status(self, batch_model: MarketingDraftBatchModel) -> None:
        statuses = [post.review_status for post in batch_model.posts]
        if statuses and all(status == "approved" for status in statuses):
            batch_model.status = "approved"
        elif any(status == "changes_requested" for status in statuses):
            batch_model.status = "changes_requested"
        elif any(status == "rejected" for status in statuses):
            batch_model.status = "rejected"
        else:
            batch_model.status = "pending_review"

    def _batch_model_to_record(self, model: MarketingDraftBatchModel) -> DraftBatchRecord:
        return materialize_batch_record(DraftBatchRecord(
            batch_id=model.batch_id,
            batch_type=getattr(model, 'batch_type', 'direct') or 'direct',
            parent_batch_id=getattr(model, 'parent_batch_id', None),
            agent_id=model.agent_id,
            hired_instance_id=model.hired_instance_id,
            campaign_id=model.campaign_id,
            customer_id=model.customer_id,
            theme=model.theme,
            brand_name=model.brand_name,
            brief_summary=model.brief_summary,
            created_at=model.created_at,
            status=model.status,
            workflow_state=model.workflow_state,
            posts=[self._post_model_to_record(post) for post in model.posts],
        ))

    def _post_model_to_record(self, model: MarketingDraftPostModel) -> DraftPostRecord:
        return materialize_post_record(DraftPostRecord(
            post_id=model.post_id,
            channel=ChannelName(model.channel),
            text=model.text,
            hashtags=list(model.hashtags or []),
            artifact_type=model.artifact_type or "text",
            artifact_uri=model.artifact_uri,
            artifact_preview_uri=model.artifact_preview_uri,
            artifact_mime_type=model.artifact_mime_type,
            artifact_metadata=dict(model.artifact_metadata or {}),
            artifact_generation_status=model.artifact_generation_status or "not_requested",
            artifact_job_id=model.artifact_job_id,
            generated_artifacts=[
                GeneratedArtifactReference.model_validate(artifact)
                for artifact in (model.generated_artifacts or [])
            ],
            review_status=model.review_status,
            approval_id=model.approval_id,
            credential_ref=model.credential_ref,
            execution_status=model.execution_status,
            visibility=model.visibility,
            public_release_requested=model.public_release_requested,
            scheduled_at=model.scheduled_at,
            attempts=model.attempts,
            last_error=model.last_error,
            provider_post_id=model.provider_post_id,
            provider_post_url=model.provider_post_url,
        ))

    def _record_to_post_model(
        self,
        record: DraftPostRecord,
        campaign_id: str | None,
    ) -> MarketingDraftPostModel:
        return MarketingDraftPostModel(
            post_id=record.post_id,
            campaign_id=campaign_id,
            channel=record.channel.value,
            text=record.text,
            hashtags=record.hashtags,
            artifact_type=record.artifact_type,
            artifact_uri=record.artifact_uri,
            artifact_preview_uri=record.artifact_preview_uri,
            artifact_mime_type=record.artifact_mime_type,
            artifact_metadata=record.artifact_metadata,
            artifact_generation_status=record.artifact_generation_status,
            artifact_job_id=record.artifact_job_id,
            generated_artifacts=[artifact.model_dump(mode="json") for artifact in record.generated_artifacts],
            review_status=record.review_status,
            approval_id=record.approval_id,
            credential_ref=record.credential_ref,
            execution_status=record.execution_status,
            visibility=record.visibility,
            public_release_requested=record.public_release_requested,
            scheduled_at=record.scheduled_at,
            attempts=record.attempts,
            last_error=record.last_error,
            provider_post_id=record.provider_post_id,
            provider_post_url=record.provider_post_url,
        )


def _build_publish_readiness_hint(post: DraftPostRecord) -> Optional[str]:
    if post.review_status != "approved":
        return "approval_required"
    if post.artifact_generation_status in {"queued", "running"}:
        return "artifact_generation_pending"
    if post.artifact_generation_status == "failed":
        return "artifact_generation_failed"
    if post.execution_status == "failed":
        return "publish_failed"
    if post.artifact_type != "text" and post.artifact_type != "table" and not post.artifact_uri:
        return "artifact_uri_missing"
    return None


def materialize_post_record(post: DraftPostRecord) -> DraftPostRecord:
    hint = _build_publish_readiness_hint(post)
    return post.model_copy(
        update={
            "publish_ready": hint is None,
            "publish_readiness_hint": hint,
        }
    )


def materialize_batch_record(batch: DraftBatchRecord) -> DraftBatchRecord:
    return batch.model_copy(update={"posts": [materialize_post_record(post) for post in batch.posts]})
