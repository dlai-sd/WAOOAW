"""Goal 5: Reference agents manufactured from AgentSpecs.

These are end-to-end proof agents for the Agent Mold:
- Two marketing agents using the certified playbook pipeline.
- One tutor agent (whiteboard-style lesson plan + quiz) with deterministic output.

They run through the same hook/policy plane and metering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agent_mold.spec import AgentSpec, DimensionName


@dataclass(frozen=True)
class ReferenceAgent:
    agent_id: str
    display_name: str
    agent_type: str
    spec: AgentSpec

    # Minimal configuration payload used by the demo runner.
    defaults: Dict[str, Any]


def _marketing_spec(agent_id: str, *, industry: str, brand_name: str) -> AgentSpec:
    return AgentSpec(
        agent_id=agent_id,
        agent_type="marketing",
        dimensions={
            DimensionName.SKILL: {
                "present": True,
                "config": {
                    "primary_playbook_id": "MARKETING.MULTICHANNEL.POST.V1",
                    "category": "marketing",
                },
            },
            DimensionName.INDUSTRY: {
                "present": True,
                "config": {
                    "industry": industry,
                },
            },
            DimensionName.TRIAL: {"present": True, "config": {}},
            DimensionName.BUDGET: {"present": True, "config": {}},
        },
    )


def _tutor_spec(agent_id: str, *, subject: str, level: str) -> AgentSpec:
    return AgentSpec(
        agent_id=agent_id,
        agent_type="tutor",
        dimensions={
            DimensionName.SKILL: {
                "present": True,
                "config": {
                    "primary_skill": "EDUCATION.LESSON.PLAN.V1",
                    "category": "education",
                },
            },
            DimensionName.INDUSTRY: {
                "present": True,
                "config": {
                    "industry": "education",
                },
            },
            DimensionName.UI: {
                "present": True,
                "config": {
                    "ui": "whiteboard",
                },
            },
            DimensionName.TRIAL: {"present": True, "config": {}},
            DimensionName.BUDGET: {"present": True, "config": {}},
        },
    )


def _trading_spec(agent_id: str) -> AgentSpec:
    return AgentSpec(
        agent_id=agent_id,
        agent_type="trading",
        dimensions={
            DimensionName.SKILL: {
                "present": True,
                "config": {
                    "primary_playbook_id": "TRADING.DELTA.FUTURES.MANUAL.V1",
                    "category": "trading",
                },
            },
            DimensionName.INTEGRATIONS: {
                "present": True,
                "config": {
                    "providers": ["delta_exchange_india"],
                },
            },
            DimensionName.INDUSTRY: {
                "present": True,
                "config": {
                    "industry": "trading",
                },
            },
            DimensionName.TRIAL: {"present": True, "config": {}},
            DimensionName.BUDGET: {"present": True, "config": {}},
        },
    )


REFERENCE_AGENTS: List[ReferenceAgent] = [
    ReferenceAgent(
        agent_id="AGT-MKT-BEAUTY-001",
        display_name="Beauty Artist Marketing Agent",
        agent_type="marketing",
        spec=_marketing_spec(
            "AGT-MKT-BEAUTY-001",
            industry="beauty",
            brand_name="Glow & Go Studio",
        ),
        defaults={
            "brand_name": "Glow & Go Studio",
            "location": "Bengaluru",
            "audience": "Brides-to-be and working professionals",
            "tone": "confident, friendly",
        },
    ),
    ReferenceAgent(
        agent_id="AGT-MKT-CAKE-001",
        display_name="Cake Shop Marketing Agent",
        agent_type="marketing",
        spec=_marketing_spec(
            "AGT-MKT-CAKE-001",
            industry="food",
            brand_name="Cake Shop",
        ),
        defaults={
            "brand_name": "Cake Shop",
            "location": "Mumbai",
            "audience": "Families, birthday planners",
            "tone": "warm, joyful",
        },
    ),
    ReferenceAgent(
        agent_id="AGT-MKT-HEALTH-001",
        display_name="Healthcare Marketing Agent",
        agent_type="marketing",
        spec=_marketing_spec(
            "AGT-MKT-HEALTH-001",
            industry="healthcare",
            brand_name="Care Clinic",
        ),
        defaults={
            "brand_name": "Care Clinic",
            "location": "Pune",
            "audience": "Patients and families",
            "tone": "clear, caring, professional",
            "language": "en",
        },
    ),
    ReferenceAgent(
        agent_id="AGT-TUTOR-WB-001",
        display_name="Tutor Agent (Whiteboard)",
        agent_type="tutor",
        spec=_tutor_spec(
            "AGT-TUTOR-WB-001",
            subject="Mathematics",
            level="Class 10",
        ),
        defaults={
            "subject": "Mathematics",
            "level": "Class 10",
            "topic": "Linear equations in two variables",
            "language": "en",
        },
    ),
    ReferenceAgent(
        agent_id="AGT-TRD-DELTA-001",
        display_name="Delta Futures Trading Agent (Manual)",
        agent_type="trading",
        spec=_trading_spec("AGT-TRD-DELTA-001"),
        defaults={
            "exchange_provider": "delta_exchange_india",
            "coin": "BTC",
            "units": 1,
            "side": "long",
            "action": "enter",
            "market": True,
        },
    ),
]


def get_reference_agent(agent_id: str) -> Optional[ReferenceAgent]:
    for agent in REFERENCE_AGENTS:
        if agent.agent_id == agent_id:
            return agent
    return None
