"""Enforcement helpers for the Agent Mold.

Goal 2: make hooks usable from real request paths.

This module provides a stable, reusable entrypoint for the current in-process
hook bus. Later phases can replace this with a message bus or a remote policy
service without changing API handlers.
"""

from __future__ import annotations

from functools import lru_cache

from agent_mold.hooks import ApprovalRequiredHook, HookBus, HookStage


@lru_cache(maxsize=1)
def default_hook_bus() -> HookBus:
    """Return the process-wide default hook bus."""

    bus = HookBus()
    bus.register(HookStage.PRE_TOOL_USE, ApprovalRequiredHook())
    return bus
