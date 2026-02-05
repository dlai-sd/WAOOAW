"""Channel adapters.

Channel adapters transform canonical outputs into platform-specific variants.
This is intentionally deterministic (no LLM usage) for Chunk C.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from agent_mold.skills.playbook import CanonicalMessage, ChannelName, ChannelVariant


def _normalize_hashtags(tags: List[str]) -> List[str]:
    normalized: List[str] = []
    for tag in tags:
        tag = tag.strip()
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = f"#{tag}"
        normalized.append(tag)
    # stable order
    return sorted(set(normalized), key=lambda s: s.lower())


@dataclass(frozen=True)
class LinkedInConstraints:
    max_chars: int = 3000


@dataclass(frozen=True)
class InstagramConstraints:
    max_chars: int = 2200


@dataclass(frozen=True)
class YouTubeConstraints:
    # Roughly: title <= 100, description <= 5000
    max_chars: int = 5100


@dataclass(frozen=True)
class FacebookConstraints:
    max_chars: int = 63206


@dataclass(frozen=True)
class WhatsAppConstraints:
    max_chars: int = 1024


def adapt_linkedin(canonical: CanonicalMessage, *, constraints: LinkedInConstraints = LinkedInConstraints()) -> ChannelVariant:
    hashtags = _normalize_hashtags(canonical.hashtags)
    body = canonical.core_message

    if canonical.key_points:
        bullets = "\n".join(f"• {p}" for p in canonical.key_points)
        body = f"{body}\n\n{bullets}"

    text = f"{body}\n\n{canonical.call_to_action}"
    if hashtags:
        text = f"{text}\n\n" + " ".join(hashtags[:15])

    # Simple truncation safety
    if len(text) > constraints.max_chars:
        text = text[: constraints.max_chars - 3].rstrip() + "..."

    return ChannelVariant(channel=ChannelName.LINKEDIN, text=text, hashtags=hashtags)


def adapt_instagram(canonical: CanonicalMessage, *, constraints: InstagramConstraints = InstagramConstraints()) -> ChannelVariant:
    hashtags = _normalize_hashtags(canonical.hashtags)

    text = f"{canonical.core_message}\n\n{canonical.call_to_action}"
    if hashtags:
        text = f"{text}\n\n" + " ".join(hashtags[:25])

    if len(text) > constraints.max_chars:
        text = text[: constraints.max_chars - 3].rstrip() + "..."

    return ChannelVariant(channel=ChannelName.INSTAGRAM, text=text, hashtags=hashtags)


def adapt_youtube(canonical: CanonicalMessage, *, constraints: YouTubeConstraints = YouTubeConstraints()) -> ChannelVariant:
    hashtags = _normalize_hashtags(canonical.hashtags)

    title = canonical.theme.strip()
    if len(title) > 100:
        title = title[:97].rstrip() + "..."

    lines: List[str] = [
        f"Title: {title}",
        "",
        canonical.core_message.strip(),
    ]

    if canonical.key_points:
        lines.append("")
        lines.append("Key points:")
        lines.extend(f"- {p}" for p in canonical.key_points)

    lines.append("")
    lines.append(canonical.call_to_action.strip())

    if hashtags:
        lines.append("")
        lines.append(" ".join(hashtags[:15]))

    text = "\n".join(lines).strip()
    if len(text) > constraints.max_chars:
        text = text[: constraints.max_chars - 3].rstrip() + "..."

    return ChannelVariant(channel=ChannelName.YOUTUBE, text=text, hashtags=hashtags)


def adapt_facebook(canonical: CanonicalMessage, *, constraints: FacebookConstraints = FacebookConstraints()) -> ChannelVariant:
    hashtags = _normalize_hashtags(canonical.hashtags)

    body = canonical.core_message
    if canonical.key_points:
        bullets = "\n".join(f"• {p}" for p in canonical.key_points)
        body = f"{body}\n\n{bullets}"

    text = f"{body}\n\n{canonical.call_to_action}"
    if hashtags:
        text = f"{text}\n\n" + " ".join(hashtags[:20])

    if len(text) > constraints.max_chars:
        text = text[: constraints.max_chars - 3].rstrip() + "..."

    return ChannelVariant(channel=ChannelName.FACEBOOK, text=text, hashtags=hashtags)


def adapt_whatsapp(canonical: CanonicalMessage, *, constraints: WhatsAppConstraints = WhatsAppConstraints()) -> ChannelVariant:
    hashtags = _normalize_hashtags(canonical.hashtags)

    # WhatsApp: short, high-signal.
    headline = canonical.core_message
    if len(headline) > 240:
        headline = headline[:237].rstrip() + "..."

    text = f"{headline}\n\n{canonical.call_to_action}"
    if hashtags:
        text = f"{text}\n" + " ".join(hashtags[:5])

    if len(text) > constraints.max_chars:
        text = text[: constraints.max_chars - 3].rstrip() + "..."

    return ChannelVariant(channel=ChannelName.WHATSAPP, text=text, hashtags=hashtags)
