"""Thin Grok API client (OpenAI-SDK-compatible).

Uses XAI_API_KEY env var. If not set, raises GrokClientError.
Set EXECUTOR_BACKEND=grok to activate. Default is 'deterministic'.

Image generation uses xai-grok-2-image-1212 (Aurora) via the same key.
Video/audio types use grok_complete() to produce production-ready scripts.
"""
from __future__ import annotations

import base64
import os
from typing import Optional

import httpx
from openai import OpenAI  # openai>=1.0 — must be in requirements.txt


class GrokClientError(Exception):
    pass


def get_grok_client() -> OpenAI:
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise GrokClientError("XAI_API_KEY is not set. Set EXECUTOR_BACKEND=deterministic or provide the key.")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1",
    )


def grok_complete(
    client: OpenAI,
    system: str,
    user: str,
    model: str = "grok-3-latest",
    temperature: float = 0.7,
) -> str:
    """Single chat completion call. Returns assistant message text."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def xai_generate_image(
    client: OpenAI,
    prompt: str,
    *,
    model: str = "grok-2-image-1212",
    n: int = 1,
) -> bytes:
    """Generate an image via XAI Aurora. Returns raw JPEG/PNG bytes.

    Falls back to a branded SVG placeholder if the API returns a URL that
    cannot be fetched (e.g. in test environments).
    """
    response = client.images.generate(
        model=model,
        prompt=prompt,
        n=n,
        response_format="url",
    )
    image_url: Optional[str] = None
    if response.data:
        image_url = response.data[0].url or getattr(response.data[0], "b64_json", None)

    # If the API returned base64 directly
    if image_url and "data:image" in image_url:
        raw_b64 = image_url.split(",", 1)[-1]
        return base64.b64decode(raw_b64)

    if image_url and image_url.startswith("http"):
        try:
            resp = httpx.get(image_url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            return resp.content
        except Exception:
            pass  # Fall through to placeholder

    # SVG placeholder (offline / test) — minimal branded image
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">'
        f'<rect width="100%" height="100%" fill="#0a0a0a"/>'
        f'<text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" '
        f'font-family="sans-serif" font-size="28" fill="#00f2fe">WAOOAW</text>'
        f'<text x="50%" y="58%" dominant-baseline="middle" text-anchor="middle" '
        f'font-family="sans-serif" font-size="16" fill="#667eea">{prompt[:80]}</text>'
        f'</svg>'
    )
    return svg.encode("utf-8")


def grok_generate_script(
    client: OpenAI,
    artifact_type: str,
    theme: str,
    brand_name: str,
    post_text: str,
    *,
    channel: str = "youtube",
) -> str:
    """Generate a production-ready script for video, audio, or video+audio artifacts.

    Returns markdown text suitable for import into HeyGen, ElevenLabs, Runway, etc.
    """
    type_instructions = {
        "video": (
            "a professional YouTube video script with:\n"
            "- Title and description (SEO-optimised)\n"
            "- Shot-by-shot storyboard (Scene #, Visual, B-roll, Duration)\n"
            "- On-screen text / captions\n"
            "- CTA at the end\n"
            "Format in Markdown."
        ),
        "audio": (
            "a voiceover narration script with:\n"
            "- Speaker notes (pace, tone, emphasis)\n"
            "- Full narration text paragraph by paragraph\n"
            "- Suggested background music mood\n"
            "Format in Markdown."
        ),
        "video_audio": (
            "a complete narrated video production package with:\n"
            "- Title, description, and tags\n"
            "- Shot-by-shot storyboard table (Scene, Visual, Narration, Duration, B-roll)\n"
            "- Full voiceover transcript\n"
            "- On-screen text\n"
            "- CTA\n"
            "Format in Markdown — ready to paste into HeyGen or Runway."
        ),
    }
    instructions = type_instructions.get(artifact_type, type_instructions["video"])
    system = (
        f"You are a world-class content production writer for {brand_name}. "
        f"You create compelling {channel} content that drives engagement and conversions."
    )
    user = (
        f"Theme: {theme}\n"
        f"Brand: {brand_name}\n"
        f"Post caption: {post_text}\n\n"
        f"Create {instructions}"
    )
    return grok_complete(client, system, user, temperature=0.75)

