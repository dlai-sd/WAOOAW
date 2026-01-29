"""Skill playbook schemas.

A playbook is a *certifiable* artifact:
- it declares inputs
- it declares a canonical output contract
- it can be compiled into runtime adapters/templates

This is intentionally minimal for Chunk C.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SkillCategory(str, Enum):
    MARKETING = "marketing"
    EDUCATION = "education"
    SALES = "sales"
    PLATFORM = "platform"


class CanonicalMessage(BaseModel):
    """Canonical marketing message output.

    Skills produce this stable shape; channel adapters transform it.
    """

    theme: str = Field(..., min_length=1)
    core_message: str = Field(..., min_length=1)
    call_to_action: str = Field(..., min_length=1)
    key_points: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)


class ChannelName(str, Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"


class ChannelVariant(BaseModel):
    channel: ChannelName
    text: str
    hashtags: List[str] = Field(default_factory=list)


class MarketingMultiChannelOutput(BaseModel):
    canonical: CanonicalMessage
    variants: List[ChannelVariant]


class SkillPlaybookMetadata(BaseModel):
    playbook_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1, description="Semantic version")
    category: SkillCategory
    description: str = Field("", description="Short human description")

    # For Chunk C, we only support one output contract.
    output_contract: Literal["marketing_multichannel_v1"] = "marketing_multichannel_v1"


class SkillPlaybook(BaseModel):
    metadata: SkillPlaybookMetadata

    # Input schema is intentionally loose initially; we validate required keys.
    required_inputs: List[str] = Field(default_factory=list)

    # “Steps” are declarative; later we can compile these into prompts.
    steps: List[str] = Field(default_factory=list)

    # Freeform section used for certification/QA rules.
    quality_checks: List[str] = Field(default_factory=list)


class SkillExecutionInput(BaseModel):
    """Normalized input used at execution time (after customer setup + industry tuning)."""

    theme: str
    brand_name: str
    offer: Optional[str] = None
    location: Optional[str] = None
    audience: Optional[str] = None

    # Platform preferences
    tone: Optional[str] = None
    language: Optional[str] = None


class SkillExecutionResult(BaseModel):
    playbook_id: str
    output: MarketingMultiChannelOutput
    debug: Dict[str, Any] = Field(default_factory=dict)
