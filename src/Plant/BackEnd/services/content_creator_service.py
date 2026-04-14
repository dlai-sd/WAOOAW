"""Content Creator Service — unified create → approve → publish flow.

Ties together ContentCreatorSkill (generation), DatabaseDraftBatchStore (persistence),
approval gates, and YouTubeAdapter (publishing) into one cohesive service.

Usage:
    service = ContentCreatorService(db)
    batch = await service.create_content(...)       # generates + persists drafts
    post  = await service.approve_post(post_id)     # customer approves a draft post
    result = await service.publish_post(post_id)    # publishes to YouTube (or other)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from agent_mold.skills.executor import execute_marketing_multichannel_v1
from agent_mold.skills.playbook import ArtifactRequest, ChannelName, SkillExecutionInput
from core.logging import PiiMaskingFilter, get_logger
from integrations.social.base import SocialPostResult
from services.database_credential_store import DatabaseCredentialStore
from services.draft_batches import (
    DatabaseDraftBatchStore,
    DraftBatchRecord,
    DraftPostRecord,
    materialize_batch_record,
)
from services.social_credential_resolver import DatabaseCredentialResolver

logger = get_logger(__name__)
logger.addFilter(PiiMaskingFilter())


class ContentCreatorError(Exception):
    """Raised when content creator operations fail."""

    def __init__(self, message: str, *, reason: str = "content_creator_error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.reason = reason
        self.details = details or {}


class ContentCreatorService:
    """Unified service: create content → customer approval → publish to platform."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._draft_store = DatabaseDraftBatchStore(db)
        self._credential_store = DatabaseCredentialStore(db)
        self._credential_resolver = DatabaseCredentialResolver(db)

    async def create_content(
        self,
        *,
        agent_id: str,
        theme: str,
        brand_name: str,
        hired_instance_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        brief_summary: Optional[str] = None,
        offer: Optional[str] = None,
        location: Optional[str] = None,
        audience: Optional[str] = None,
        tone: Optional[str] = None,
        language: Optional[str] = None,
        channels: Optional[List[ChannelName]] = None,
        youtube_credential_ref: Optional[str] = None,
        youtube_visibility: str = "private",
        public_release_requested: bool = False,
        requested_artifacts: Optional[List[ArtifactRequest]] = None,
        playbook: Any = None,
    ) -> DraftBatchRecord:
        """Generate multi-channel content drafts and persist for customer review.

        Returns a DraftBatchRecord with status "pending_review".
        """
        if playbook is None:
            from pathlib import Path
            from agent_mold.skills.loader import load_playbook

            playbook = load_playbook(
                Path(__file__).resolve().parents[1]
                / "agent_mold"
                / "playbooks"
                / "marketing"
                / "multichannel_post_v1.md"
            )

        youtube_secret_ref = await self._resolve_youtube_ref(
            hired_instance_id=hired_instance_id,
            supplied_ref=youtube_credential_ref,
        )

        result = execute_marketing_multichannel_v1(
            playbook,
            SkillExecutionInput(
                theme=theme,
                brand_name=brand_name,
                offer=offer,
                location=location,
                audience=audience,
                tone=tone,
                language=language,
                channels=channels,
                requested_artifacts=requested_artifacts,
            ),
        )

        batch_id = str(uuid4())
        posts: List[DraftPostRecord] = []
        for variant in result.output.variants:
            post_id = str(uuid4())
            posts.append(
                DraftPostRecord(
                    post_id=post_id,
                    channel=variant.channel,
                    text=variant.text,
                    hashtags=variant.hashtags,
                    credential_ref=(
                        youtube_secret_ref
                        if variant.channel == ChannelName.YOUTUBE
                        else None
                    ),
                    visibility=(
                        youtube_visibility
                        if variant.channel == ChannelName.YOUTUBE
                        else "private"
                    ),
                    public_release_requested=(
                        public_release_requested
                        if variant.channel == ChannelName.YOUTUBE
                        else False
                    ),
                )
            )

        batch = materialize_batch_record(
            DraftBatchRecord(
                batch_id=batch_id,
                agent_id=agent_id,
                hired_instance_id=hired_instance_id,
                campaign_id=campaign_id,
                customer_id=customer_id,
                theme=result.output.canonical.theme,
                brand_name=brand_name,
                brief_summary=brief_summary,
                created_at=datetime.utcnow(),
                posts=posts,
            )
        )

        await self._draft_store.save_batch(batch)
        await self._db.commit()

        logger.info(
            "Content created: batch_id=%s, agent=%s, customer=%s, posts=%d",
            batch_id,
            agent_id,
            customer_id,
            len(posts),
        )
        return batch

    async def get_batch(self, batch_id: str) -> Optional[DraftBatchRecord]:
        """Retrieve a draft batch by ID."""
        batch = await self._draft_store.get_batch(batch_id)
        if batch:
            return materialize_batch_record(batch)
        return None

    async def list_batches(
        self,
        *,
        customer_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[DraftBatchRecord]:
        """List draft batches with optional filters."""
        batches = await self._draft_store.load_batches()
        if customer_id:
            batches = [b for b in batches if b.customer_id == customer_id]
        if agent_id:
            batches = [b for b in batches if b.agent_id == agent_id]
        if status:
            batches = [b for b in batches if b.status == status]
        batches = batches[-max(1, int(limit)):]
        return [materialize_batch_record(b) for b in batches]

    async def approve_post(self, post_id: str, *, approval_id: Optional[str] = None) -> DraftPostRecord:
        """Approve a draft post for publishing.

        Sets review_status to "approved" and assigns an approval_id.
        """
        found = await self._draft_store.find_post(post_id)
        if found is None:
            raise ContentCreatorError(
                "Draft post not found",
                reason="unknown_post_id",
                details={"post_id": post_id},
            )

        _, post = found
        effective_approval_id = (approval_id or f"APR-{uuid4()}").strip()

        updated = await self._draft_store.update_post(
            post_id, review_status="approved", approval_id=effective_approval_id
        )
        if not updated:
            raise ContentCreatorError(
                "Failed to approve draft post",
                reason="update_failed",
                details={"post_id": post_id},
            )

        await self._db.commit()
        logger.info("Post approved: post_id=%s, approval_id=%s", post_id, effective_approval_id)

        # Return updated post  
        found = await self._draft_store.find_post(post_id)
        return found[1] if found else post

    async def reject_post(self, post_id: str) -> DraftPostRecord:
        """Reject a draft post."""
        found = await self._draft_store.find_post(post_id)
        if found is None:
            raise ContentCreatorError(
                "Draft post not found",
                reason="unknown_post_id",
                details={"post_id": post_id},
            )

        _, post = found
        updated = await self._draft_store.update_post(
            post_id,
            review_status="rejected",
            approval_id=None,
            execution_status="not_scheduled",
        )
        if not updated:
            raise ContentCreatorError(
                "Failed to reject draft post",
                reason="update_failed",
                details={"post_id": post_id},
            )

        await self._db.commit()
        logger.info("Post rejected: post_id=%s", post_id)
        found = await self._draft_store.find_post(post_id)
        return found[1] if found else post

    async def publish_post(self, post_id: str) -> Dict[str, Any]:
        """Publish an approved post to its target platform (currently YouTube).

        Pre-conditions:
        1. Post must be approved (review_status == "approved")
        2. Post must have a credential_ref
        3. Post's batch must have a customer_id

        Returns dict with execution_status, provider_post_id, provider_post_url.
        """
        found = await self._draft_store.find_post(post_id)
        if found is None:
            raise ContentCreatorError(
                "Draft post not found",
                reason="unknown_post_id",
                details={"post_id": post_id},
            )

        batch, post = found

        if post.review_status != "approved":
            raise ContentCreatorError(
                "Post must be approved before publishing",
                reason="not_approved",
                details={"post_id": post_id, "review_status": post.review_status},
            )

        if not post.credential_ref:
            raise ContentCreatorError(
                "No credential_ref for publishing",
                reason="missing_credential_ref",
                details={"post_id": post_id},
            )

        if not batch.customer_id:
            raise ContentCreatorError(
                "No customer_id on batch",
                reason="missing_customer_id",
                details={"post_id": post_id, "batch_id": batch.batch_id},
            )

        channel = post.channel.value if hasattr(post.channel, "value") else str(post.channel)

        if channel == "youtube":
            return await self._publish_youtube(batch, post)

        raise ContentCreatorError(
            f"Publishing to {channel} not yet supported",
            reason="unsupported_channel",
            details={"post_id": post_id, "channel": channel},
        )

    async def _publish_youtube(
        self, batch: DraftBatchRecord, post: DraftPostRecord
    ) -> Dict[str, Any]:
        """Execute YouTube publish via YouTubeClient with DB-backed credential resolution."""
        from integrations.social.youtube_client import YouTubeClient

        client = YouTubeClient(
            customer_id=batch.customer_id,
            credential_resolver=self._credential_resolver,
        )

        try:
            if post.artifact_type in {"video", "video_audio"} and post.artifact_uri:
                result = await client.post_short(
                    credential_ref=post.credential_ref,
                    video_url=post.artifact_uri,
                    title=batch.theme,
                    description=post.text,
                )
            else:
                result = await client.post_text(
                    credential_ref=post.credential_ref,
                    text=post.text,
                    image_url=(
                        post.artifact_uri
                        if getattr(post, "artifact_type", None) == "image"
                        else None
                    ),
                )
        except Exception as exc:
            await self._draft_store.update_post(
                post.post_id,
                execution_status="failed",
                last_error=str(exc),
            )
            await self._db.commit()
            logger.error("YouTube publish failed: post_id=%s, error=%s", post.post_id, exc)
            raise ContentCreatorError(
                "YouTube publish failed",
                reason="publish_failed",
                details={"post_id": post.post_id, "error": str(exc)},
            ) from exc

        await self._draft_store.update_post(
            post.post_id,
            execution_status="posted",
            provider_post_id=result.post_id,
            provider_post_url=result.post_url,
            last_error=None,
        )
        await self._db.commit()

        logger.info(
            "YouTube publish success: post_id=%s, provider_post_id=%s",
            post.post_id,
            result.post_id,
        )

        return {
            "post_id": post.post_id,
            "execution_status": "posted",
            "provider_post_id": result.post_id,
            "provider_post_url": result.post_url,
            "channel": "youtube",
        }

    async def _resolve_youtube_ref(
        self,
        *,
        hired_instance_id: Optional[str],
        supplied_ref: Optional[str],
    ) -> Optional[str]:
        """Resolve YouTube credential ref from Platform Connection or supplied value."""
        from services.marketing_credential_resolver import resolve_youtube_secret_ref

        return await resolve_youtube_secret_ref(
            self._db,
            hired_instance_id=hired_instance_id,
            supplied_ref=supplied_ref,
        )
