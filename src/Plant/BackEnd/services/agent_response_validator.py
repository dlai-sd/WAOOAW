"""Agent Response Contract + Validator.

Validates LLM responses at the API boundary to enforce structured output.
Prevents conversational filler (e.g. "I'm thrilled to present…") from leaking
through when a structured response (themes, tables, JSON) was expected.

Usage:
    from services.agent_response_validator import validate_theme_plan_response, ResponseValidationError

    try:
        validated = validate_theme_plan_response(raw_text)
    except ResponseValidationError as e:
        logger.warning("LLM response failed validation: %s", e.violations)
        # Retry or fall back to deterministic pipeline
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar, Dict, FrozenSet, List, Optional

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Conversational filler detection — phrases that signal the LLM returned
# prose instead of structured output.
# ---------------------------------------------------------------------------

_FILLER_PATTERNS = re.compile(
    r"(?i)"
    r"(i'?m\s+(thrilled|excited|happy|pleased|delighted)\s+to\b"
    r"|let\s+me\s+present"
    r"|here\s+(is|are)\s+(a|the|your)\b"
    r"|certainly!?\s"
    r"|of\s+course!?\s"
    r"|absolutely!?\s"
    r"|definitely!?\s"
    r"|i\s+would\s+be\s+happy\s+to\b"
    r"|great\s+question"
    r"|thank\s+you\s+for\s+(sharing|providing|asking)"
    r"|i'?d\s+love\s+to\s+help"
    r"|what\s+a\s+(great|wonderful|fantastic)\b"
    r")",
)


class ResponseViolation(BaseModel):
    """A single validation violation."""
    field: str
    rule: str
    detail: str


class ResponseValidationError(Exception):
    """Raised when an LLM response fails contract validation."""
    def __init__(self, violations: List[ResponseViolation]):
        self.violations = violations
        messages = [f"{v.field}: {v.detail}" for v in violations]
        super().__init__(f"Response validation failed: {'; '.join(messages)}")


# ---------------------------------------------------------------------------
# Contracts — Pydantic models that define what a valid response looks like
# ---------------------------------------------------------------------------

class DerivedThemeContract(BaseModel):
    """A single derived theme must have a non-empty title."""
    title: str = Field(..., min_length=1)
    description: str = ""
    frequency: str = "weekly"

    @field_validator("title")
    @classmethod
    def title_not_filler(cls, v: str) -> str:
        stripped = v.strip()
        if _FILLER_PATTERNS.search(stripped):
            raise ValueError(f"Title contains conversational filler: {stripped[:80]}")
        return stripped


class ThemePlanContract(BaseModel):
    """
    Contract for the theme-plan LLM response.

    Enforces:
    - master_theme is a non-empty string (not a full paragraph of filler)
    - derived_themes is a non-empty list when themes were requested
    - No top-level conversational filler
    """
    master_theme: str = Field(..., min_length=1, max_length=300)
    derived_themes: List[DerivedThemeContract] = Field(default_factory=list)
    assistant_message: Optional[str] = None
    strategy_workshop: Optional[Dict[str, Any]] = None

    @field_validator("master_theme")
    @classmethod
    def master_theme_not_filler(cls, v: str) -> str:
        stripped = v.strip()
        if _FILLER_PATTERNS.search(stripped):
            raise ValueError(f"master_theme contains conversational filler: {stripped[:80]}")
        return stripped


class StrategyWorkshopContract(BaseModel):
    """
    Contract for the strategy workshop response.

    Enforces:
    - status is within allowed values
    - assistant_message is non-empty
    - messages list is well-formed
    """
    status: str = Field(..., min_length=1)
    assistant_message: str = Field(..., min_length=1)
    checkpoint_summary: str = ""
    current_focus_question: str = ""
    next_step_options: List[str] = Field(default_factory=list)
    time_saving_note: str = ""

    ALLOWED_STATUSES: ClassVar[FrozenSet[str]] = frozenset({
        "discovery", "narrowing", "refining", "approval_ready", "approved", "draft_ready",
    })

    @field_validator("status")
    @classmethod
    def status_is_valid(cls, v: str) -> str:
        if v.lower().strip() not in cls.ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{v}'. Allowed: {sorted(cls.ALLOWED_STATUSES)}")
        return v.lower().strip()


# ---------------------------------------------------------------------------
# Public validation functions
# ---------------------------------------------------------------------------

def detect_filler(text: str) -> bool:
    """Return True if text starts with conversational filler."""
    return bool(_FILLER_PATTERNS.match(text.strip()))


def validate_theme_plan_response(
    raw_text: str,
    *,
    require_themes: bool = False,
) -> ThemePlanContract:
    """
    Validate an LLM response against the theme-plan contract.

    Args:
        raw_text: Raw string from the LLM.
        require_themes: If True, derived_themes must be non-empty.

    Returns:
        Validated ThemePlanContract.

    Raises:
        ResponseValidationError: If the response fails validation.
    """
    violations: List[ResponseViolation] = []
    cleaned = (raw_text or "").strip()

    if not cleaned:
        violations.append(ResponseViolation(
            field="raw_text",
            rule="non_empty",
            detail="LLM returned empty response",
        ))
        raise ResponseValidationError(violations)

    # Attempt JSON parse
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        # If it's not JSON, treat the whole text as a master theme
        if detect_filler(cleaned):
            violations.append(ResponseViolation(
                field="raw_text",
                rule="no_filler",
                detail=f"Response is conversational filler, not structured output: {cleaned[:100]}",
            ))
            raise ResponseValidationError(violations)

        # Use the first line as master_theme
        first_line = cleaned.splitlines()[0] if cleaned.splitlines() else cleaned
        return ThemePlanContract(master_theme=first_line[:300], derived_themes=[])

    if not isinstance(payload, dict):
        violations.append(ResponseViolation(
            field="raw_text",
            rule="must_be_object",
            detail="LLM response parsed to non-object JSON",
        ))
        raise ResponseValidationError(violations)

    # Validate through contract
    try:
        contract = ThemePlanContract(
            master_theme=payload.get("master_theme") or payload.get("theme") or "",
            derived_themes=payload.get("derived_themes") or [],
            assistant_message=payload.get("assistant_message"),
            strategy_workshop=payload.get("strategy_workshop"),
        )
    except Exception as e:
        violations.append(ResponseViolation(
            field="contract",
            rule="schema_validation",
            detail=str(e),
        ))
        raise ResponseValidationError(violations) from e

    if require_themes and not contract.derived_themes:
        violations.append(ResponseViolation(
            field="derived_themes",
            rule="non_empty_when_required",
            detail="derived_themes must not be empty when themes were requested",
        ))
        raise ResponseValidationError(violations)

    return contract


def validate_workshop_response(
    payload: Dict[str, Any],
) -> StrategyWorkshopContract:
    """
    Validate a strategy workshop response dict.

    Args:
        payload: Parsed dict from the LLM response.

    Returns:
        Validated StrategyWorkshopContract.

    Raises:
        ResponseValidationError: If the response fails validation.
    """
    violations: List[ResponseViolation] = []

    try:
        contract = StrategyWorkshopContract(
            status=payload.get("status") or "",
            assistant_message=payload.get("assistant_message") or "",
            checkpoint_summary=payload.get("checkpoint_summary") or "",
            current_focus_question=payload.get("current_focus_question") or "",
            next_step_options=payload.get("next_step_options") or [],
            time_saving_note=payload.get("time_saving_note") or "",
        )
    except Exception as e:
        violations.append(ResponseViolation(
            field="workshop_contract",
            rule="schema_validation",
            detail=str(e),
        ))
        raise ResponseValidationError(violations) from e

    # Additional check: assistant_message should not be pure filler
    if detect_filler(contract.assistant_message):
        violations.append(ResponseViolation(
            field="assistant_message",
            rule="no_filler",
            detail="assistant_message is conversational filler",
        ))
        raise ResponseValidationError(violations)

    return contract
