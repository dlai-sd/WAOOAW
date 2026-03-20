"""Repository for Campaign persistence operations.

Provides async CRUD operations for campaigns, daily_theme_items,
and content_posts tables.

References:
    PLANT-CONTENT-2-campaign-persistence.md — E2-S1
    repositories/deliverable_repository.py — session / flush / refresh pattern
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.campaign import CampaignModel, ContentPostModel, DailyThemeItemModel


class CampaignRepository:
    """Repository for Campaign persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialise repository with an async database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    # ── Campaign ──────────────────────────────────────────────────────────

    async def get_campaign_by_id(self, campaign_id: str) -> CampaignModel | None:
        """Fetch a campaign by primary key.

        Args:
            campaign_id: Unique campaign identifier.

        Returns:
            CampaignModel or None if not found.
        """
        stmt = select(CampaignModel).where(CampaignModel.campaign_id == campaign_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_campaigns_by_customer(
        self, customer_id: str
    ) -> list[CampaignModel]:
        """List all campaigns for a customer, newest first.

        Args:
            customer_id: Customer identifier.

        Returns:
            List of CampaignModel ordered by created_at desc.
        """
        stmt = (
            select(CampaignModel)
            .where(CampaignModel.customer_id == customer_id)
            .order_by(CampaignModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_campaigns_by_hired_instance(
        self, hired_instance_id: str
    ) -> list[CampaignModel]:
        """List all campaigns for a hired agent instance, newest first.

        Args:
            hired_instance_id: Parent hired agent identifier.

        Returns:
            List of CampaignModel ordered by created_at desc.
        """
        stmt = (
            select(CampaignModel)
            .where(CampaignModel.hired_instance_id == hired_instance_id)
            .order_by(CampaignModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_draft_campaign_by_hired_instance(
        self, hired_instance_id: str
    ) -> CampaignModel | None:
        """Return the newest draft campaign for a hired instance, if any."""
        stmt = (
            select(CampaignModel)
            .where(CampaignModel.hired_instance_id == hired_instance_id)
            .where(CampaignModel.status == "draft")
            .order_by(CampaignModel.updated_at.desc(), CampaignModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_campaign(
        self,
        hired_instance_id: str,
        customer_id: str,
        brief: dict[str, Any],
        cost_estimate: dict[str, Any],
        campaign_id: str | None = None,
        status: str = "draft",
        workflow_state: str = "brief_captured",
        brief_summary: dict[str, Any] | None = None,
        approval_state: dict[str, Any] | None = None,
        draft_deliverables: list[dict[str, Any]] | None = None,
    ) -> CampaignModel:
        """Create and persist a new campaign record.

        Args:
            hired_instance_id: Parent hired agent instance.
            customer_id: Owning customer.
            brief: Serialised CampaignBrief dict.
            cost_estimate: Serialised CostEstimate dict.
            campaign_id: Optional explicit ID (for idempotency / testing).
            status: Initial status (default "draft").

        Returns:
            Freshly flushed and refreshed CampaignModel.
        """
        now = datetime.now(timezone.utc)
        model = CampaignModel(
            campaign_id=campaign_id or f"CAM-{uuid4()}",
            hired_instance_id=hired_instance_id,
            customer_id=customer_id,
            brief=brief,
            cost_estimate=cost_estimate,
            status=status,
            workflow_state=workflow_state,
            brief_summary=brief_summary,
            approval_state=approval_state,
            draft_deliverables=draft_deliverables,
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def update_campaign_runtime(
        self,
        campaign_id: str,
        *,
        workflow_state: str,
        brief_summary: dict[str, Any],
        approval_state: dict[str, Any],
        draft_deliverables: list[dict[str, Any]],
    ) -> CampaignModel:
        existing = await self.get_campaign_by_id(campaign_id)
        if existing is None:
            raise ValueError(f"Campaign {campaign_id!r} not found")
        existing.workflow_state = workflow_state
        existing.brief_summary = brief_summary
        existing.approval_state = approval_state
        existing.draft_deliverables = draft_deliverables
        existing.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(existing)
        return existing

    async def update_campaign_status(
        self, campaign_id: str, status: str
    ) -> CampaignModel:
        """Update campaign status.

        Args:
            campaign_id: Campaign to update.
            status: New status value.

        Returns:
            Updated CampaignModel.

        Raises:
            ValueError: If campaign_id is not found.
        """
        existing = await self.get_campaign_by_id(campaign_id)
        if existing is None:
            raise ValueError(f"Campaign {campaign_id!r} not found")
        existing.status = status
        existing.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(existing)
        return existing

    async def update_campaign_brief(
        self,
        campaign_id: str,
        *,
        brief: dict[str, Any],
        cost_estimate: dict[str, Any] | None = None,
        workflow_state: str | None = None,
        brief_summary: dict[str, Any] | None = None,
    ) -> CampaignModel:
        """Replace the persisted brief for an existing campaign."""
        existing = await self.get_campaign_by_id(campaign_id)
        if existing is None:
            raise ValueError(f"Campaign {campaign_id!r} not found")
        existing.brief = brief
        if cost_estimate is not None:
            existing.cost_estimate = cost_estimate
        if workflow_state is not None:
            existing.workflow_state = workflow_state
        if brief_summary is not None:
            existing.brief_summary = brief_summary
        existing.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(existing)
        return existing

    async def upsert_draft_campaign_with_theme_items(
        self,
        *,
        hired_instance_id: str,
        customer_id: str,
        brief: dict[str, Any],
        cost_estimate: dict[str, Any],
        theme_items: list[dict[str, Any]],
        workflow_state: str = "brief_captured",
        brief_summary: dict[str, Any] | None = None,
    ) -> CampaignModel:
        """Create or update the single active draft campaign for a hired instance.

        This keeps DMA setup on one reusable draft campaign while replacing the
        derived theme list in the same session transaction.
        """
        existing = await self.get_active_draft_campaign_by_hired_instance(hired_instance_id)
        if existing is None:
            campaign = await self.create_campaign(
                hired_instance_id=hired_instance_id,
                customer_id=customer_id,
                brief=brief,
                cost_estimate=cost_estimate,
                workflow_state=workflow_state,
                brief_summary=brief_summary,
            )
        else:
            campaign = await self.update_campaign_brief(
                existing.campaign_id,
                brief=brief,
                cost_estimate=cost_estimate,
                workflow_state=workflow_state,
                brief_summary=brief_summary,
            )

        await self.replace_theme_items(campaign.campaign_id, theme_items)
        return campaign

    async def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign and its dependent rows (cascade).

        Args:
            campaign_id: Campaign to delete.

        Returns:
            True if deleted, False if not found.
        """
        existing = await self.get_campaign_by_id(campaign_id)
        if existing is None:
            return False
        await self.session.delete(existing)
        await self.session.flush()
        return True

    # ── DailyThemeItem ────────────────────────────────────────────────────

    async def get_theme_item_by_id(
        self, theme_item_id: str
    ) -> DailyThemeItemModel | None:
        """Fetch a theme item by primary key.

        Args:
            theme_item_id: Unique theme item identifier.

        Returns:
            DailyThemeItemModel or None if not found.
        """
        stmt = select(DailyThemeItemModel).where(
            DailyThemeItemModel.theme_item_id == theme_item_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_theme_items_by_campaign(
        self, campaign_id: str
    ) -> list[DailyThemeItemModel]:
        """List all theme items for a campaign, ordered by day_number.

        Args:
            campaign_id: Parent campaign identifier.

        Returns:
            List of DailyThemeItemModel ordered by day_number asc.
        """
        stmt = (
            select(DailyThemeItemModel)
            .where(DailyThemeItemModel.campaign_id == campaign_id)
            .order_by(DailyThemeItemModel.day_number.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_theme_item(
        self,
        campaign_id: str,
        day_number: int,
        scheduled_date: date,
        theme_title: str,
        theme_description: str,
        dimensions: list[str] | None = None,
        theme_item_id: str | None = None,
    ) -> DailyThemeItemModel:
        """Create and persist a daily theme item.

        Args:
            campaign_id: Parent campaign.
            day_number: 1-based day index within the campaign.
            scheduled_date: Calendar date for this theme day.
            theme_title: Short title for the day's theme.
            theme_description: Longer description / content angle guidance.
            dimensions: Optional list of content angles.
            theme_item_id: Optional explicit ID (for idempotency / testing).

        Returns:
            Freshly flushed and refreshed DailyThemeItemModel.
        """
        model = DailyThemeItemModel(
            theme_item_id=theme_item_id or f"THM-{uuid4()}",
            campaign_id=campaign_id,
            day_number=day_number,
            scheduled_date=scheduled_date,
            theme_title=theme_title,
            theme_description=theme_description,
            dimensions=dimensions or [],
            review_status="pending_review",
            approved_at=None,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def update_theme_item_review_status(
        self,
        theme_item_id: str,
        review_status: str,
        approved_at: datetime | None = None,
    ) -> DailyThemeItemModel:
        """Update the review status of a theme item.

        Args:
            theme_item_id: Theme item to update.
            review_status: New status — "pending_review", "approved", "rejected".
            approved_at: Approval timestamp (set when review_status == "approved").

        Returns:
            Updated DailyThemeItemModel.

        Raises:
            ValueError: If theme_item_id is not found.
        """
        existing = await self.get_theme_item_by_id(theme_item_id)
        if existing is None:
            raise ValueError(f"DailyThemeItem {theme_item_id!r} not found")
        existing.review_status = review_status
        if review_status == "approved":
            existing.approved_at = approved_at or datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(existing)
        return existing

    async def replace_theme_items(
        self,
        campaign_id: str,
        items: list[dict[str, Any]],
    ) -> list[DailyThemeItemModel]:
        """Replace all theme items for a campaign in one transaction."""
        await self.session.execute(
            delete(DailyThemeItemModel).where(DailyThemeItemModel.campaign_id == campaign_id)
        )
        await self.session.flush()

        persisted: list[DailyThemeItemModel] = []
        for item in items:
            persisted.append(
                await self.create_theme_item(
                    campaign_id=campaign_id,
                    day_number=int(item["day_number"]),
                    scheduled_date=item["scheduled_date"],
                    theme_title=str(item["theme_title"]),
                    theme_description=str(item["theme_description"]),
                    dimensions=list(item.get("dimensions") or []),
                    theme_item_id=item.get("theme_item_id"),
                )
            )
        return persisted

    # ── ContentPost ───────────────────────────────────────────────────────

    async def get_post_by_id(self, post_id: str) -> ContentPostModel | None:
        """Fetch a content post by primary key.

        Args:
            post_id: Unique post identifier.

        Returns:
            ContentPostModel or None if not found.
        """
        stmt = select(ContentPostModel).where(ContentPostModel.post_id == post_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_posts_by_campaign(
        self, campaign_id: str
    ) -> list[ContentPostModel]:
        """List all posts for a campaign, ordered by scheduled_publish_at.

        Args:
            campaign_id: Parent campaign identifier.

        Returns:
            List of ContentPostModel ordered by scheduled_publish_at asc.
        """
        stmt = (
            select(ContentPostModel)
            .where(ContentPostModel.campaign_id == campaign_id)
            .order_by(ContentPostModel.scheduled_publish_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_posts_by_theme_item(
        self, theme_item_id: str
    ) -> list[ContentPostModel]:
        """List all posts for a theme item.

        Args:
            theme_item_id: Parent theme item identifier.

        Returns:
            List of ContentPostModel.
        """
        stmt = (
            select(ContentPostModel)
            .where(ContentPostModel.theme_item_id == theme_item_id)
            .order_by(ContentPostModel.scheduled_publish_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_campaign_runtime_counters(self, campaign_id: str) -> dict[str, int]:
        """Return lightweight counters used to derive campaign runtime progress."""

        theme_items = await self.list_theme_items_by_campaign(campaign_id)
        posts = await self.list_posts_by_campaign(campaign_id)
        return {
            "theme_items": len(theme_items),
            "posts": len(posts),
            "pending_review_posts": sum(1 for post in posts if post.review_status == "pending_review"),
            "approved_posts": sum(1 for post in posts if post.review_status == "approved"),
            "rejected_posts": sum(1 for post in posts if post.review_status == "rejected"),
        }

    async def list_posts_due_for_publish(
        self, before: datetime | None = None
    ) -> list[ContentPostModel]:
        """List approved posts that are not yet published and are due.

        Args:
            before: Upper bound on scheduled_publish_at (defaults to now).

        Returns:
            List of ContentPostModel with review_status="approved" and
            publish_status="not_published" and scheduled_publish_at <= before.
        """
        cutoff = before or datetime.now(timezone.utc)
        stmt = (
            select(ContentPostModel)
            .where(ContentPostModel.review_status == "approved")
            .where(ContentPostModel.publish_status == "not_published")
            .where(ContentPostModel.scheduled_publish_at <= cutoff)
            .order_by(ContentPostModel.scheduled_publish_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_post(
        self,
        campaign_id: str,
        theme_item_id: str,
        destination: dict[str, Any],
        content_text: str,
        scheduled_publish_at: datetime,
        hashtags: list[str] | None = None,
        post_id: str | None = None,
        approval_id: str | None = None,
        credential_ref: str | None = None,
        visibility: str = "private",
        public_release_requested: bool = False,
    ) -> ContentPostModel:
        """Create and persist a content post.

        Args:
            campaign_id: Parent campaign.
            theme_item_id: Parent theme item.
            destination: Serialised DestinationRef dict.
            content_text: Generated post copy.
            scheduled_publish_at: Target publish datetime (UTC).
            hashtags: Optional list of hashtags.
            post_id: Optional explicit ID (for idempotency / testing).

        Returns:
            Freshly flushed and refreshed ContentPostModel.
        """
        now = datetime.now(timezone.utc)
        model = ContentPostModel(
            post_id=post_id or f"PST-{uuid4()}",
            campaign_id=campaign_id,
            theme_item_id=theme_item_id,
            destination=destination,
            content_text=content_text,
            hashtags=hashtags or [],
            scheduled_publish_at=scheduled_publish_at,
            review_status="pending_review",
            publish_status="not_published",
            approval_id=approval_id,
            credential_ref=credential_ref,
            visibility=visibility,
            public_release_requested=public_release_requested,
            publish_receipt=None,
            created_at=now,
            updated_at=now,
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return model

    async def update_post_review_status(
        self, post_id: str, review_status: str
    ) -> ContentPostModel:
        """Update the review status of a content post.

        Args:
            post_id: Post to update.
            review_status: New status — "pending_review", "approved", "rejected".

        Returns:
            Updated ContentPostModel.

        Raises:
            ValueError: If post_id is not found.
        """
        existing = await self.get_post_by_id(post_id)
        if existing is None:
            raise ValueError(f"ContentPost {post_id!r} not found")
        existing.review_status = review_status
        existing.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(existing)
        return existing

    async def update_post_publish_status(
        self,
        post_id: str,
        publish_status: str,
        publish_receipt: dict[str, Any] | None = None,
    ) -> ContentPostModel:
        """Update the publish status of a content post.

        Args:
            post_id: Post to update.
            publish_status: New status — "not_published", "published", "failed".
            publish_receipt: Adapter-specific receipt dict.

        Returns:
            Updated ContentPostModel.

        Raises:
            ValueError: If post_id is not found.
        """
        existing = await self.get_post_by_id(post_id)
        if existing is None:
            raise ValueError(f"ContentPost {post_id!r} not found")
        existing.publish_status = publish_status
        existing.publish_receipt = publish_receipt
        existing.updated_at = datetime.now(timezone.utc)
        await self.session.flush()
        await self.session.refresh(existing)
        return existing
