"""Publisher Engine — plug-and-play destination registry.

Adding a new publish destination:
1. Create a new file e.g. agent_mold/skills/adapters_linkedin.py
2. Define class LinkedInAdapter(DestinationAdapter)
3. Register: registry.register("linkedin", LinkedInAdapter)

The registry is populated at app startup from env config.
No other files need to change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Type

from agent_mold.skills.content_models import PublishInput, PublishReceipt


class DestinationAdapter(ABC):
    """Abstract base class for all publish destination adapters.

    Every adapter must implement publish(). It receives a PublishInput
    and returns a PublishReceipt. It must be stateless — all auth
    credentials are referenced by key in inp.credential_ref.
    """

    DESTINATION_TYPE: str = ""  # Must be set by each subclass

    @abstractmethod
    def publish(self, inp: PublishInput) -> PublishReceipt:
        """Publish the post to the destination platform.

        Must be idempotent — calling twice with the same post_id
        must not create duplicate posts.
        """
        ...

    def estimate_cost(self, inp: PublishInput) -> float:
        """Optional: return cost in USD for this publish call. Default: free."""
        return 0.0


class DestinationRegistry:
    """Maps destination_type string → DestinationAdapter class.

    Thread-safe for reads (register only at startup).
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[DestinationAdapter]] = {}

    def register(self, destination_type: str, adapter_class: Type[DestinationAdapter]) -> None:
        self._registry[destination_type.lower()] = adapter_class

    def get(self, destination_type: str) -> Optional[Type[DestinationAdapter]]:
        return self._registry.get(destination_type.lower())

    def list_registered(self) -> List[str]:
        return list(self._registry.keys())

    def is_registered(self, destination_type: str) -> bool:
        return destination_type.lower() in self._registry


class PublisherEngine:
    """Orchestrates publishing across multiple destinations.

    Usage:
        engine = PublisherEngine(registry)
        receipt = engine.publish(publish_input)
    """

    def __init__(self, registry: DestinationRegistry) -> None:
        self._registry = registry

    def publish(self, inp: PublishInput) -> PublishReceipt:
        dest_type = inp.post.destination.destination_type.lower()
        adapter_class = self._registry.get(dest_type)
        if adapter_class is None:
            return PublishReceipt(
                post_id=inp.post.post_id,
                destination_type=dest_type,
                success=False,
                error=f"No adapter registered for destination_type '{dest_type}'. "
                      f"Registered: {self._registry.list_registered()}",
            )
        adapter = adapter_class()
        try:
            return adapter.publish(inp)
        except Exception as exc:
            return PublishReceipt(
                post_id=inp.post.post_id,
                destination_type=dest_type,
                success=False,
                error=str(exc),
            )


# ── Default registry (populated at module import) ─────────────────────────────
# Import adapters here and register. New adapters = add two lines below.

def build_default_registry() -> DestinationRegistry:
    from agent_mold.skills.adapters_publish import SimulatedAdapter
    registry = DestinationRegistry()
    registry.register("simulated", SimulatedAdapter)
    registry.register("x", SimulatedAdapter)          # X/Twitter: simulated in Phase 1
    registry.register("twitter", SimulatedAdapter)    # alias
    # Phase 2: uncomment when OAuth adapters are built
    # from agent_mold.skills.adapters_linkedin import LinkedInAdapter
    # registry.register("linkedin", LinkedInAdapter)
    return registry


default_registry = build_default_registry()
default_engine = PublisherEngine(default_registry)
