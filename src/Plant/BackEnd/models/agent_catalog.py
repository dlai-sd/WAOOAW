"""Agent catalog release model for hire-ready lifecycle gating."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from core.database import Base


class AgentCatalogReleaseModel(Base):
    """Catalog release row for a hireable agent version.

    This is the Plant-owned gate between a raw Agent entity and a CP-visible,
    customer-safe marketplace listing.
    """

    __tablename__ = "agent_catalog_releases"

    release_id = Column(String, primary_key=True, nullable=False)
    agent_id = Column(String, nullable=False, index=True)
    agent_type_id = Column(String, nullable=False, index=True)
    internal_definition_version_id = Column(String, nullable=True)
    external_catalog_version = Column(String, nullable=False)

    public_name = Column(String, nullable=False)
    short_description = Column(Text, nullable=False)
    industry_name = Column(String, nullable=False)
    job_role_label = Column(String, nullable=False)

    monthly_price_inr = Column(Integer, nullable=False, default=12000)
    trial_days = Column(Integer, nullable=False, default=7)
    allowed_durations = Column(JSONB, nullable=False, default=list)
    supported_channels = Column(JSONB, nullable=False, default=list)
    approval_mode = Column(String, nullable=False, default="manual_review")

    lifecycle_state = Column(String, nullable=False, default="draft")
    approved_for_new_hire = Column(Boolean, nullable=False, default=False)
    retired_from_catalog_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("agent_id", "external_catalog_version", name="uq_agent_catalog_agent_version"),
        Index("ix_agent_catalog_releases_agent_id", "agent_id"),
        Index("ix_agent_catalog_releases_lifecycle_state", "lifecycle_state"),
        Index("ix_agent_catalog_releases_approved_for_new_hire", "approved_for_new_hire"),
    )

    def __init__(
        self,
        *,
        release_id: str,
        agent_id: str,
        agent_type_id: str,
        internal_definition_version_id: str | None,
        external_catalog_version: str,
        public_name: str,
        short_description: str,
        industry_name: str,
        job_role_label: str,
        monthly_price_inr: int,
        trial_days: int,
        allowed_durations: list[str] | None = None,
        supported_channels: list[str] | None = None,
        approval_mode: str = "manual_review",
        lifecycle_state: str = "draft",
        approved_for_new_hire: bool = False,
        retired_from_catalog_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.release_id = release_id
        self.agent_id = agent_id
        self.agent_type_id = agent_type_id
        self.internal_definition_version_id = internal_definition_version_id
        self.external_catalog_version = external_catalog_version
        self.public_name = public_name
        self.short_description = short_description
        self.industry_name = industry_name
        self.job_role_label = job_role_label
        self.monthly_price_inr = monthly_price_inr
        self.trial_days = trial_days
        self.allowed_durations = list(allowed_durations or [])
        self.supported_channels = list(supported_channels or [])
        self.approval_mode = approval_mode
        self.lifecycle_state = lifecycle_state
        self.approved_for_new_hire = approved_for_new_hire
        self.retired_from_catalog_at = retired_from_catalog_at
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now
