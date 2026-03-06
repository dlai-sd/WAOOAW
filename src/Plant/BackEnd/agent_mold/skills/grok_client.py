"""Thin Grok API client (OpenAI-SDK-compatible).

Uses XAI_API_KEY env var. If not set, raises GrokClientError.
Set EXECUTOR_BACKEND=grok to activate. Default is 'deterministic'.
"""
from __future__ import annotations

import os

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
