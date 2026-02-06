"""Marketing provider abstraction + allowlist.

Phase 1: mocked providers only (no outbound network).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Protocol, Set

from agent_mold.skills.playbook import ChannelName


@dataclass(frozen=True)
class PublishResult:
    provider_post_id: str
    provider_post_url: str


class SocialProvider(Protocol):
    def publish_text(
        self,
        *,
        channel: ChannelName,
        text: str,
        hashtags: List[str],
        credential_ref: str | None = None,
        posting_identity: str | None = None,
    ) -> PublishResult:
        ...


class ProviderAllowlist:
    def __init__(self, allowed: Set[ChannelName]):
        self._allowed = allowed

    @classmethod
    def from_env(cls) -> "ProviderAllowlist":
        raw = os.getenv("MARKETING_ALLOWED_CHANNELS", "").strip()
        if not raw:
            # Default allowlist: our 5 MVP channels.
            return cls(
                {
                    ChannelName.YOUTUBE,
                    ChannelName.INSTAGRAM,
                    ChannelName.FACEBOOK,
                    ChannelName.LINKEDIN,
                    ChannelName.WHATSAPP,
                }
            )

        allowed: Set[ChannelName] = set()
        for item in raw.split(","):
            item = item.strip().lower()
            if not item:
                continue
            allowed.add(ChannelName(item))
        return cls(allowed)

    def ensure_allowed(self, channel: ChannelName) -> None:
        if channel not in self._allowed:
            raise ValueError(f"provider_not_allowed: channel={channel.value}")


class MockSocialProvider:
    """Deterministic provider adapter for unit tests/dev.

    Returns a stable fake URL + id without any network calls.
    """

    def __init__(self, *, base_url: str = "https://mock.social.local"):
        self._base_url = base_url.rstrip("/")

    def publish_text(
        self,
        *,
        channel: ChannelName,
        text: str,
        hashtags: List[str],
        credential_ref: str | None = None,
        posting_identity: str | None = None,
    ) -> PublishResult:
        # Deterministic-ish ID based on channel + text length.
        post_id = f"{channel.value}-{len(text)}-{len(hashtags)}"
        url = f"{self._base_url}/{channel.value}/posts/{post_id}"
        return PublishResult(provider_post_id=post_id, provider_post_url=url)


def default_social_provider() -> SocialProvider:
    # For now we always use mock provider. Later: switch to real adapters.
    return MockSocialProvider()


def provider_allowlist() -> ProviderAllowlist:
    return ProviderAllowlist.from_env()

