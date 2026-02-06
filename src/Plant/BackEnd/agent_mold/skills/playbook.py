"""Skill playbook schemas.

A playbook is a *certifiable* artifact:
- it declares inputs
- it declares a canonical output contract
- it can be compiled into runtime adapters/templates

This is intentionally minimal for Chunk C.
"""

from __future__ import annotations

from enum import Enum
import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, root_validator


class SkillCategory(str, Enum):
    MARKETING = "marketing"
    EDUCATION = "education"
    SALES = "sales"
    PLATFORM = "platform"


class CanonicalMessage(BaseModel):
    """Canonical marketing message output.

    Skills produce this stable shape; channel adapters transform it.
    """

    schema_version: Literal["1.0"] = Field(
        default="1.0",
        description="Canonical message schema version",
    )

    theme: str = Field(..., min_length=1)
    core_message: str = Field(..., min_length=1)
    call_to_action: str = Field(..., min_length=1)
    key_points: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)


class ChannelName(str, Enum):
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"


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

    @root_validator(skip_on_failure=True)
    def _validate_version_semver(cls, values: Dict[str, Any]):  # type: ignore[override]
        version = values.get("version")
        if not isinstance(version, str) or not version.strip():
            raise ValueError("metadata.version must be a non-empty string")

        # Minimal semver check: X.Y.Z (no prerelease/build for now).
        if not re.fullmatch(r"\d+\.\d+\.\d+", version.strip()):
            raise ValueError("metadata.version must be semantic version 'X.Y.Z'")

        playbook_id = values.get("playbook_id")
        if not isinstance(playbook_id, str) or not playbook_id.strip():
            raise ValueError("metadata.playbook_id must be a non-empty string")
        return values


class SkillPlaybook(BaseModel):
    metadata: SkillPlaybookMetadata

    # Input schema is intentionally loose initially; we validate required keys.
    required_inputs: List[str] = Field(default_factory=list)

    # “Steps” are declarative; later we can compile these into prompts.
    steps: List[str] = Field(default_factory=list)

    # Freeform section used for certification/QA rules.
    quality_checks: List[str] = Field(default_factory=list)

    @root_validator(skip_on_failure=True)
    def _validate_lists(cls, values: Dict[str, Any]):  # type: ignore[override]
        required_inputs = values.get("required_inputs") or []
        steps = values.get("steps") or []
        quality_checks = values.get("quality_checks") or []

        if not isinstance(required_inputs, list) or not all(isinstance(x, str) and x.strip() for x in required_inputs):
            raise ValueError("required_inputs must be a list of non-empty strings")
        if len(set(required_inputs)) != len(required_inputs):
            raise ValueError("required_inputs must not contain duplicates")

        if not isinstance(steps, list) or not steps or not all(isinstance(x, str) and x.strip() for x in steps):
            raise ValueError("steps must be a non-empty list of non-empty strings")

        if not isinstance(quality_checks, list) or not all(isinstance(x, str) and x.strip() for x in quality_checks):
            raise ValueError("quality_checks must be a list of non-empty strings")

        return values


class PlaybookCertificationResult(BaseModel):
    certifiable: bool
    issues: List[str] = Field(default_factory=list)


def certify_playbook(playbook: SkillPlaybook) -> PlaybookCertificationResult:
    """Return whether a schema-valid playbook is certifiable.

    Certification is intentionally minimal in Epic 3.1:
    - QA rubric must be present (quality_checks non-empty)
    - Output-contract-specific required inputs must exist
    """

    issues: List[str] = []

    if not playbook.quality_checks:
        issues.append("Missing QA rubric: quality_checks must be non-empty")

    if playbook.metadata.output_contract == "marketing_multichannel_v1":
        required = set(playbook.required_inputs)
        for key in ("theme", "brand_name"):
            if key not in required:
                issues.append(f"Missing required_inputs entry: {key}")

    return PlaybookCertificationResult(certifiable=len(issues) == 0, issues=issues)


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

    # Optional channel selection (defaults to the executor's standard set).
    channels: Optional[List[ChannelName]] = None


class SkillExecutionResult(BaseModel):
    playbook_id: str
    output: MarketingMultiChannelOutput
    debug: Dict[str, Any] = Field(default_factory=dict)
