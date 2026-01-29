"""Playbook loader (Markdown + YAML frontmatter).

Frontmatter format (marketingskills-style):
---
playbook_id: MARKETING.MULTICHANNEL.POST.V1
name: Multi-channel themed post
version: 1.0.0
category: marketing
description: Create a canonical marketing message and adapt to channels.
output_contract: marketing_multichannel_v1
required_inputs: [theme, brand_name]
steps:
  - Draft canonical message
  - Adapt to LinkedIn
  - Adapt to Instagram
quality_checks:
  - No false claims
  - Match tone
---

Body can include additional narrative (ignored for now).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

from agent_mold.skills.playbook import SkillPlaybook


@dataclass(frozen=True)
class PlaybookLoadError(Exception):
    message: str


def _split_frontmatter(markdown_text: str) -> Tuple[str, str]:
    """Return (frontmatter_yaml, body). Raises if malformed."""

    lines = markdown_text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise PlaybookLoadError("Playbook is missing YAML frontmatter '---' header")

    # Find closing ---
    try:
        end_index = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration as exc:
        raise PlaybookLoadError("Playbook YAML frontmatter missing closing '---'") from exc

    frontmatter = "\n".join(lines[1:end_index]).strip()
    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return frontmatter, body


def load_playbook(path: Path) -> SkillPlaybook:
    if not path.exists():
        raise PlaybookLoadError(f"Playbook not found: {path}")

    text = path.read_text(encoding="utf-8")
    frontmatter_yaml, _body = _split_frontmatter(text)

    try:
        raw: Dict[str, Any] = yaml.safe_load(frontmatter_yaml) or {}
    except yaml.YAMLError as exc:
        raise PlaybookLoadError(f"Invalid YAML frontmatter: {exc}") from exc

    # Convert flat frontmatter dict into SkillPlaybook shape.
    metadata_keys = {
        "playbook_id",
        "name",
        "version",
        "category",
        "description",
        "output_contract",
    }

    metadata = {k: raw.get(k) for k in metadata_keys if k in raw}
    playbook_dict = {
        "metadata": metadata,
        "required_inputs": raw.get("required_inputs") or [],
        "steps": raw.get("steps") or [],
        "quality_checks": raw.get("quality_checks") or [],
    }

    try:
        return SkillPlaybook.model_validate(playbook_dict)
    except Exception as exc:  # noqa: BLE001
        raise PlaybookLoadError(f"Playbook failed schema validation: {exc}") from exc
