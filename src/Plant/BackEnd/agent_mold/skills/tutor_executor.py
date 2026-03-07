# src/Plant/BackEnd/agent_mold/skills/tutor_executor.py
"""Minimal tutor skill processor (PLANT-MOULD-1).

Concrete BaseProcessor for tutor/education agents.
Generates a deterministic lesson plan outline from goal_config.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent_mold.processor import BaseProcessor, ProcessorInput, ProcessorOutput

if TYPE_CHECKING:
    from agent_mold.hooks import HookBus


class TutorSkill(BaseProcessor):
    """Processor for education/tutor agents.

    Unpacks ProcessorInput.goal_config (subject, level, topic, language) and
    generates a deterministic lesson plan outline.
    """

    SKILL_ID = "education.tutor.v1"

    async def process(self, input_data: ProcessorInput, hook_bus: "HookBus") -> ProcessorOutput:
        cfg = input_data.goal_config
        subject = cfg.get("subject", "Mathematics")
        level = cfg.get("level", "Class 10")
        topic = cfg.get("topic", "Introduction")
        language = cfg.get("language", "en")

        plan = {
            "subject": subject,
            "level": level,
            "topic": topic,
            "language": language,
            "outline": [
                f"1. Introduction to {topic}",
                f"2. Key concepts in {topic}",
                f"3. Worked examples",
                f"4. Practice problems",
                f"5. Quiz",
            ],
        }

        return ProcessorOutput(
            result=plan,
            metadata={"processor_type": self.processor_type()},
            correlation_id=input_data.correlation_id,
        )
