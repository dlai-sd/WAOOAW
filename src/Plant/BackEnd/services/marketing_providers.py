"""Marketing provider abstraction + allowlist.

Phase 1: mocked providers only (no outbound network).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Protocol, Set

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


class SocialProviderAdapter(Protocol):
    channel: ChannelName

    def publish_text(
        self,
        *,
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


@dataclass(frozen=True)
class MockChannelAdapter:
    """Deterministic per-channel provider adapter for unit tests/dev.

    Returns a stable fake URL + id without any network calls.
    """

    channel: ChannelName
    base_url: str = "https://mock.social.local"

    def publish_text(
        self,
        *,
        text: str,
        hashtags: List[str],
        credential_ref: str | None = None,
        posting_identity: str | None = None,
    ) -> PublishResult:
        base_url = self.base_url.rstrip("/")
        post_id = f"{self.channel.value}-{len(text)}-{len(hashtags)}"
        url = f"{base_url}/{self.channel.value}/posts/{post_id}"
        return PublishResult(provider_post_id=post_id, provider_post_url=url)


class RoutedSocialProvider:
    """Routes publish calls to a per-channel adapter."""

    def __init__(self, adapters: Dict[ChannelName, SocialProviderAdapter]):
        self._adapters = dict(adapters)

    def publish_text(
        self,
        *,
        channel: ChannelName,
        text: str,
        hashtags: List[str],
        credential_ref: str | None = None,
        posting_identity: str | None = None,
    ) -> PublishResult:
        adapter = self._adapters.get(channel)
        if adapter is None:
            raise ValueError(f"provider_adapter_missing: channel={channel.value}")
        return adapter.publish_text(
            text=text,
            hashtags=hashtags,
            credential_ref=credential_ref,
            posting_identity=posting_identity,
        )


def default_social_provider() -> SocialProvider:
    # Phase 1: all adapters are mocked.
    adapters: Dict[ChannelName, SocialProviderAdapter] = {
        ChannelName.YOUTUBE: MockChannelAdapter(ChannelName.YOUTUBE),
        ChannelName.INSTAGRAM: MockChannelAdapter(ChannelName.INSTAGRAM),
        ChannelName.FACEBOOK: MockChannelAdapter(ChannelName.FACEBOOK),
        ChannelName.LINKEDIN: MockChannelAdapter(ChannelName.LINKEDIN),
        ChannelName.WHATSAPP: MockChannelAdapter(ChannelName.WHATSAPP),
    }
    return RoutedSocialProvider(adapters)


def provider_allowlist() -> ProviderAllowlist:
    return ProviderAllowlist.from_env()

