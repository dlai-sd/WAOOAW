"""Marketing Agent flow definitions (EXEC-ENGINE-001 E8-S1).

Two flows wire the three Marketing Agent components:

  ContentCreationFlow — GoalConfigPump → ContentProcessor
                        approval gate at index 2 (after ContentProcessor, before publishing)

  PublishingFlow      — LinkedInPublisher + YouTubePublisher (parallel fan-out)

MARKETING_FLOW_REGISTRY maps flow_name → flow_def dict. The flow-runs endpoint
merges this into the main FLOW_REGISTRY at import time.
"""
from __future__ import annotations

CONTENT_CREATION_FLOW: dict = {
    "flow_name": "ContentCreationFlow",
    "sequential_steps": [
        {"step_name": "step_1", "component_type": "GoalConfigPump"},
        {"step_name": "step_2", "component_type": "ContentProcessor"},
    ],
    "approval_gate_index": 2,  # Gate fires AFTER ContentProcessor, BEFORE publishing
    "deliverable_type": "content_post",
}

PUBLISHING_FLOW: dict = {
    "flow_name": "PublishingFlow",
    "parallel_steps": [
        {"step_name": "linkedin", "component_type": "LinkedInPublisher"},
        {"step_name": "youtube", "component_type": "YouTubePublisher"},
    ],
    "deliverable_type": "content_post",
}

MARKETING_FLOW_REGISTRY: dict[str, dict] = {
    "ContentCreationFlow": CONTENT_CREATION_FLOW,
    "PublishingFlow": PUBLISHING_FLOW,
}
