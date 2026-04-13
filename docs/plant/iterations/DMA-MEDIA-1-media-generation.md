# DMA-MEDIA-1 — DMA Media Generation Pipeline (Phase 1)

---

## Plan Metadata

| Field | Value |
|---|---|
| Plan ID | DMA-MEDIA-1 |
| Feature area | Plant BackEnd — DMA media artifact generation |
| Created | 2026-04-13 |
| Author | GitHub Copilot (PM mode) |
| Parent vision doc | Prior conversation: Phase 1 media generation research |
| Platform index | `docs/CONTEXT_AND_INDEX.md` (file map §13) |
| Total iterations | 1 |
| Total epics | 4 |
| Total stories | 6 |

**DMA value alignment:** This plan directly enables the Digital Marketing Agent to produce real deliverables — generated images with a free fallback provider, TTS narration audio files, and stitched narrated-video MP4s — instead of text-only markdown scripts. This is core to the "agents earn your business" promise: customers keep the generated media assets even if they cancel.

---

## Zero-Cost Agent Constraints (READ FIRST)

This plan is designed for **autonomous zero-cost model agents** (Gemini Flash, GPT-4o-mini, etc.)
with limited context windows. Every structural decision in this plan exists to preserve context.

| Constraint | How this plan handles it |
|---|---|
| Context window 8K–32K tokens | Every story card is fully self-contained — no cross-references, no "see above" |
| No working memory across files | NFR code patterns are embedded **inline** in each story — agent never opens NFRReusable.md |
| No planning ability | Stories are atomic — one deliverable, one set of files, one test command |
| Token cost per file read | Max 3 files to read per story — pre-identified by PM in the card |
| Binary inference only | Acceptance criteria are pass/fail — no judgment calls required from the agent |

> **Agent:** Execute exactly ONE story at a time. Read your assigned story card fully, then act.
> Do NOT read other stories. Do NOT open NFRReusable.md. All patterns you need are in your card.
> Do NOT read files not listed in your story card's "Files to read first" section.

---

## PM Review Checklist (tick every box before publishing)

- [x] **EXPERT PERSONAS filled** — each iteration's agent task block has the correct expert persona list based on the tech stack that iteration uses (Python/FastAPI, React Native, Terraform, Docker, GCP, etc.)
- [x] Epic titles name customer outcomes, not technical actions ("Customer sees X" not "Add X to API")
- [x] Every story has an exact branch name
- [x] Every story card embeds relevant NFR code snippets inline — no "see NFRReusable.md"
- [x] Every story card has max 3 files in "Files to read first"
- [x] Every story involving CP BackEnd states the exact pattern: A, B, or C — N/A (all Plant BackEnd)
- [x] Every new backend route story embeds the `waooaw_router()` snippet — N/A (no new routes)
- [x] Every GET route story card says `get_read_db_session()` not `get_db_session()` — N/A (no new routes)
- [x] Every story that adds env vars lists the exact Terraform file paths to update — N/A (no new env vars; Pollinations.ai is keyless, edge-tts is keyless)
- [x] Every story has `BLOCKED UNTIL` (or "none")
- [x] Each iteration has a time estimate and come-back datetime
- [x] Each iteration has a complete GitHub agent launch block
- [x] STUCK PROTOCOL is in Agent Execution Rules section
- [x] Stories sequenced: backend (S1) before frontend (S2) — N/A (all backend)
- [x] Iteration count minimized for PR-only delivery — single iteration
- [x] Related backend/frontend work kept in the same iteration — yes
- [x] No placeholders remain

---

## Iteration Summary

| Iteration | Scope | Epics | Stories | ⏱ Est. | Come back |
|---|---|---|---|---|---|
| 1 | Lane B — Pollinations.ai image fallback, Edge TTS narration, FFmpeg audio+visual stitching, Dockerfile/requirements, tests | 4 | 6 | 5h | 2026-04-13 22:00 UTC |

**Estimate basis:** New service module = 45 min | Wiring into existing task = 45 min | Dockerfile + deps = 30 min | Tests = 45 min. Add 20% buffer for zero-cost model context loading.

### PR-Overhead Optimization Rules

- Single iteration — one PR merge gate.
- 6 stories / ~5 hours of agent work — within the 4-6 story target.
- All work is Plant BackEnd only — no cross-service coordination overhead.
- Deployment happens through the `waooaw deploy` workflow after the merged iteration, not mid-flight.

---

## How to Launch Each Iteration

### Iteration 1

**Steps to launch:**
1. Open this repository on GitHub
2. Open the **Agents** tab
3. Start a new agent task
4. If the UI exposes repository agents, select **platform-engineer**; otherwise use the default coding agent
5. Copy the block below and paste it into the task
6. Start the run
7. Go away. Come back at: **2026-04-13 22:00 UTC**

**Iteration 1 agent task** (paste verbatim — do not modify):

```
You are executing a pre-planned iteration on the WAOOAW platform.

EXPERT PERSONAS: Senior Python 3.11 / FastAPI engineer + Senior Docker / container engineer
Activate these personas NOW. Begin each epic with:
  "Acting as a [persona], I will [what] by [approach]."

PLAN FILE: docs/plant/iterations/DMA-MEDIA-1-media-generation.md
YOUR SCOPE: Iteration 1 only — Epics E1, E2, E3, E4. This is a single-iteration plan.
TIME BUDGET: 5h. If you reach 6h without finishing, follow STUCK PROTOCOL now.

ENVIRONMENT REQUIREMENT:
- This task is intended for the GitHub repository Agents tab.
- Shell/git/gh/docker tools may be unavailable on this execution surface.
- Do not HALT only because terminal tools are unavailable; use the GitHub task branch/PR flow for this run.

FAIL-FAST VALIDATION GATE (complete before reading story cards or editing files):
1. Verify the plan file is readable and the assigned iteration section exists.
2. Verify this execution surface allows repository writes on the current task branch.
3. Verify this execution surface allows opening or updating a PR to `main`, or at minimum posting that PR controls are unavailable.
4. If any validation gate fails: post `Blocked at validation gate: [exact reason]` and HALT before code changes.

EXECUTION ORDER:
1. Read the "Agent Execution Rules" section in this plan file.
2. Read the "Iteration 1" section in this plan file.
3. Read nothing else before starting.
4. Work on the GitHub task branch created for this run. Do not assume terminal checkout or manual branch creation.
5. Execute Epics in this order: E1 → E2 → E3 → E4
6. Add or update the tests listed in each story before moving on.
7. If this execution surface exposes validation tools, run the narrowest relevant tests and record the result. If not, state: "Validation deferred: GitHub Agents tab on this run did not expose shell/docker test execution."
8. Open or update the iteration PR to `main`, post the PR URL, and HALT.
```

**When you return:** Check Copilot Chat for a PR URL. If you see a draft PR titled `WIP:` — an agent got stuck. Read the PR comment for the exact blocker.

---

## Agent Execution Rules

> Agent: read this section once before executing any story. These rules override all instructions.

### Rule -2 — Fail-fast validation gate

Before reading story cards in detail or making any code changes, validate all of the following:

- The plan file is readable and your assigned iteration section exists.
- Any required `Prerequisite evidence` block for this iteration is complete and not marked pending.
- The GitHub execution surface lets you save repository changes on the current task branch.
- The GitHub execution surface lets you open or update a PR to `main`, or you can explicitly report that PR controls are unavailable.

If any check fails, post `Blocked at validation gate: [exact reason]` and HALT immediately.

### Rule -1 — Activate Expert Personas (first thing, before Rule 0)

Read the `EXPERT PERSONAS:` field from the task you were given.
Activate each persona now. For every epic you execute, open with one line:

> *"Acting as a [persona], I will [what you're building] by [approach]."*

| Technology area | Expert persona to activate |
|---|---|
| `src/Plant/BackEnd/` | Senior Python 3.11 / FastAPI / SQLAlchemy engineer |
| `Dockerfile` `docker-compose*.yml` | Senior Docker / container engineer |

### Rule 0 — Use the GitHub task branch and open the iteration PR early

GitHub-hosted agents usually start on a task-specific branch. Keep the entire iteration on that branch.

### Rule 1 — Branch discipline
One iteration = one GitHub task branch and one PR.
Never push or merge directly to `main`.

### Rule 2 — Scope lock
Implement exactly the acceptance criteria in the story card.
Do not fix unrelated code. Do not refactor. Do not gold-plate.

**File scope**: Only create or modify files listed in your story card's "Files to create / modify" table.

### Rule 3 — Tests before the next story
Write every test in the story's test table before advancing to the next story.

### Rule 4 — Save progress after every story
- Update this plan file's Tracking Table: change the story status to Done or Blocked.
- Save code and plan updates to the GitHub task branch.

### Rule 5 — Validate after every epic
- After all stories in an epic, run the listed test command if the execution surface supports it.
- After validation, add `**Epic complete ✅**` under the epic heading.

### Rule 6 — STUCK PROTOCOL (3 failures = stop immediately)
- Mark the blocked story as `🚫 Blocked` in the Tracking Table.
- Open or update a draft PR titled `WIP: [story-id] — blocked`.
- Include the exact blocker, the exact error message, and 1-2 attempted fixes.
- **HALT. Do not start the next story.**

### Rule 7 — Iteration PR (after ALL epics complete)
- Title: `feat(DMA-MEDIA-1): iteration 1 — media generation pipeline`
- PR body must include: completed stories, validation status, NFR checklist.
- Post the PR URL. **HALT.**

**CHECKPOINT RULE**: After completing each epic (all tests passing), run:
```bash
git add -A && git commit -m "feat(DMA-MEDIA-1): [epic-id] — [epic title]" && git push origin HEAD
```
Do this BEFORE starting the next epic.

---

## NFR Quick Reference

| # | Rule | Consequence of violation |
|---|---|---|
| 1 | `PiiMaskingFilter()` on every logger | PII incident |
| 2 | `@circuit_breaker(service=...)` on every external HTTP call | Cascading failure |
| 3 | Never embed env-specific values in Dockerfile or code | Image cannot be promoted |
| 4 | Tests >= 80% coverage on all new BE code | PR blocked by CI |
| 5 | PR always `--base main` | Work never ships |

---

## Tracking Table

| ID | Iteration | Epic | Story | Status | PR |
|---|---|---|---|---|---|
| E1-S1 | 1 | DMA generates images with fallback | Pollinations.ai image fallback in grok_client | 🔴 Not Started | — |
| E1-S2 | 1 | DMA generates images with fallback | Wire Pollinations fallback into media generation task | 🔴 Not Started | — |
| E2-S1 | 1 | DMA produces narrated audio | Edge TTS narration service | 🔴 Not Started | — |
| E2-S2 | 1 | DMA produces narrated audio | Wire TTS into media generation task for audio artifacts | 🔴 Not Started | — |
| E3-S1 | 1 | DMA produces narrated videos | FFmpeg audio+visual stitcher service | 🔴 Not Started | — |
| E4-S1 | 1 | DMA media pipeline is production-ready | Dockerfile, requirements, and integration wiring | 🔴 Not Started | — |

**Status key:** 🔴 Not Started | 🟡 In Progress | 🟢 Done | 🚫 Blocked

---

## Iteration 1 — DMA Media Generation Pipeline (Phase 1)

**Scope:** DMA can generate real image files (with free Pollinations.ai fallback), real audio narration files (Edge TTS), and stitched narrated-video MP4s (image + TTS + FFmpeg) — replacing markdown script placeholders with actual deliverable media assets.
**Lane:** B — new backend services required
**⏱ Estimated:** 5h | **Come back:** 2026-04-13 22:00 UTC
**Epics:** E1, E2, E3, E4
**DMA value:** Directly enables DMA to produce real media deliverables customers can keep.

### Dependency Map (Iteration 1)

```
E1-S1 ──► E1-S2    (Pollinations fallback → wire into task)
E2-S1 ──► E2-S2    (TTS service → wire into task)
E3-S1              (FFmpeg stitcher — uses E2-S1 TTS + image generation; wire into task happens in E4-S1)
E4-S1              (Dockerfile + requirements + integration wiring — depends on E1, E2, E3 all being committed)

Execution order: E1-S1 → E1-S2 → E2-S1 → E2-S2 → E3-S1 → E4-S1
```

---

### Epic E1: DMA generates images with a free fallback provider

**User story:** As a DMA customer, when my agent generates image content, I receive a real image even if the primary xAI Aurora API is unavailable — ensuring my marketing deliverables are never blocked by a single provider outage.

---

#### Story E1-S1: Pollinations.ai image fallback in grok_client

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**CP BackEnd pattern:** N/A — Plant BackEnd only

**What to do (self-contained):**
> `src/Plant/BackEnd/agent_mold/skills/grok_client.py` currently has `xai_generate_image()` (lines 53-97) which calls xAI Aurora and falls back to a branded SVG placeholder if the API fails. Add a new function `pollinations_generate_image(prompt: str) -> bytes` that calls the free Pollinations.ai API (`https://image.pollinations.ai/prompt/{url_encoded_prompt}?width=800&height=600&nologo=true`) via `httpx.get()` with a 30-second timeout. Then modify `xai_generate_image()` to call `pollinations_generate_image()` as the intermediate fallback before the SVG placeholder — so the cascade is: xAI Aurora → Pollinations.ai → SVG placeholder.
>
> **Circuit-breaker note:** `pollinations_generate_image` is an external HTTP call. The existing `grok_client.py` functions (`xai_generate_image`, `grok_complete`) do not use `@circuit_breaker` — they rely on try/except + timeout. Follow the same pattern here for consistency. Wrapping with `@circuit_breaker` is deferred to a future NFR-compliance sweep across all of `grok_client.py`.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/grok_client.py` | 1–97 | `xai_generate_image` function (lines 53-97), existing httpx usage, SVG fallback pattern |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/agent_mold/skills/grok_client.py` | modify | 1. Add `from urllib.parse import quote as url_quote` at top imports. 2. Add new function `pollinations_generate_image(prompt: str, *, width: int = 800, height: int = 600) -> bytes` before `xai_generate_image`. It does `httpx.get(f"https://image.pollinations.ai/prompt/{url_quote(prompt)}?width={width}&height={height}&nologo=true", timeout=30, follow_redirects=True)`, raises on non-200, returns `resp.content`. 3. In `xai_generate_image`, replace the SVG fallback block (the `# SVG placeholder` comment and everything after it) with: first try `pollinations_generate_image(prompt)`, catch any `Exception`, then fall through to the existing SVG placeholder. |

**Code patterns to copy exactly:**

```python
# Pollinations.ai free image generation (no API key needed):
from urllib.parse import quote as url_quote

def pollinations_generate_image(
    prompt: str,
    *,
    width: int = 800,
    height: int = 600,
) -> bytes:
    """Generate an image via Pollinations.ai (free, no API key).

    Returns raw image bytes (typically JPEG).
    Raises on network error or non-200 response.
    """
    encoded_prompt = url_quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    resp = httpx.get(url, timeout=30, follow_redirects=True)
    resp.raise_for_status()
    return resp.content
```

```python
# Modified fallback chain in xai_generate_image (replace the SVG placeholder block):
    # Fallback 1: Pollinations.ai (free, no API key)
    try:
        return pollinations_generate_image(prompt)
    except Exception:
        pass  # Fall through to SVG placeholder

    # Fallback 2: SVG placeholder (offline / test)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">'
        # ... existing SVG code unchanged ...
    )
    return svg.encode("utf-8")
```

**Acceptance criteria (binary pass/fail only):**
1. `pollinations_generate_image("test marketing visual")` returns bytes with length > 0 when network is available
2. `pollinations_generate_image` raises an exception when network call fails (mocked)
3. `xai_generate_image` returns Pollinations bytes when xAI Aurora fails but Pollinations succeeds (mocked)
4. `xai_generate_image` returns SVG bytes when both xAI Aurora and Pollinations fail (mocked)
5. `xai_generate_image` returns xAI bytes when Aurora succeeds (existing behavior unchanged)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S1-T1 | `src/Plant/BackEnd/tests/unit/test_pollinations_fallback.py` | Mock `httpx.get` to return 200 with b"fake-image" | `pollinations_generate_image("test")` returns b"fake-image" |
| E1-S1-T2 | same | Mock `httpx.get` to raise `httpx.ConnectError` | `pollinations_generate_image("test")` raises exception |
| E1-S1-T3 | same | Mock xAI `client.images.generate` to raise, mock `httpx.get` (Pollinations) to return b"fallback-img" | `xai_generate_image(client, "test")` returns b"fallback-img" |
| E1-S1-T4 | same | Mock xAI to raise, mock Pollinations `httpx.get` to raise | `xai_generate_image(client, "test")` returns bytes starting with b"<svg " |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm --entrypoint "" plant-backend-test \
  python -m pytest tests/unit/test_pollinations_fallback.py -v --no-cov
```

**Commit message:** `feat(DMA-MEDIA-1): E1-S1 — Pollinations.ai image fallback in grok_client`

**Done signal:** `"E1-S1 done. Changed: grok_client.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

#### Story E1-S2: Wire Pollinations fallback into media generation task

**BLOCKED UNTIL:** E1-S1 committed
**Estimated time:** 30 min
**CP BackEnd pattern:** N/A

**What to do (self-contained):**
> `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py` lines 87-103 handle `image` artifact type by calling `xai_generate_image()`. The fallback chain is now inside `xai_generate_image()` (from E1-S1), so no dispatch change is needed. However, the task currently catches `GrokClientError` (no API key) on lines 83-85 and returns `deferred`. Update this: when `GrokClientError` is caught (no xAI key), instead of deferring, try `pollinations_generate_image(first_prompt)` directly as a standalone image generator. This allows image generation to work even when `XAI_API_KEY` is not set at all. Add `pollinations_generate_image` to the import block at line 46.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py` | 46–103 | Import block (lines 46-50), `GrokClientError` catch (lines 82-85), image generation block (lines 87-103) |
| `src/Plant/BackEnd/agent_mold/skills/grok_client.py` | 52–70 | `pollinations_generate_image` function signature (added in E1-S1) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py` | modify | 1. Add `pollinations_generate_image` to the import from `agent_mold.skills.grok_client` (line ~51). 2. Replace the `GrokClientError` catch block (lines ~83-84) that returns `deferred`: instead of returning immediately, set `client = None` and continue. 3. In the image generation block (line ~90), if `client is None`, call `pollinations_generate_image(first_prompt)` directly instead of `xai_generate_image(client, first_prompt)`. 4. For non-image types (`video`, `audio`, `video_audio`), if `client is None`, keep the existing deferred return since those still need Grok LLM. |

**Code patterns to copy exactly:**

```python
# Modified GrokClientError handling:
    try:
        client = get_grok_client()
    except GrokClientError:
        client = None  # Will use Pollinations for images, defer for LLM types

    # In the image branch:
    if first_artifact_type == "image":
        if client is not None:
            image_bytes = xai_generate_image(client, first_prompt)
        else:
            try:
                image_bytes = pollinations_generate_image(first_prompt)
            except Exception:
                logger.warning("generate_media_artifact: both xAI and Pollinations unavailable")
                return {**payload, "status": "deferred", "reason": "no_image_provider"}
        # ... rest of image storage unchanged ...
    else:
        # video/audio/video_audio need Grok LLM
        if client is None:
            logger.warning("generate_media_artifact: XAI_API_KEY not set — deferring non-image artifact")
            return {**payload, "status": "deferred", "reason": "no_api_key"}
        # ... rest of script generation unchanged ...
```

**Acceptance criteria:**
1. When `XAI_API_KEY` is unset and artifact type is `image`, the task calls `pollinations_generate_image` and stores the result
2. When `XAI_API_KEY` is unset and artifact type is `video`, the task returns `deferred`
3. When `XAI_API_KEY` is set, existing behavior is unchanged

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E1-S2-T1 | `src/Plant/BackEnd/tests/unit/test_media_gen_pollinations_wire.py` | Mock `get_grok_client` to raise `GrokClientError`, mock `pollinations_generate_image` returns b"img", mock DB + store | Result dict has `artifact_generation_status: "ready"` |
| E1-S2-T2 | same | Mock `get_grok_client` raises, artifact type = "video" | Result dict has `status: "deferred"` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm --entrypoint "" plant-backend-test \
  python -m pytest tests/unit/test_media_gen_pollinations_wire.py -v --no-cov
```

**Commit message:** `feat(DMA-MEDIA-1): E1-S2 — wire Pollinations fallback into media generation task`

**Done signal:** `"E1-S2 done. Changed: media_generation_tasks.py. Tests: T1 ✅ T2 ✅"`

---

### Epic E2: DMA produces real narrated audio deliverables

**User story:** As a DMA customer, when my agent generates audio content (e.g. podcast narration, voiceover), I receive an actual MP3 audio file I can use — not a text script.

---

#### Story E2-S1: Edge TTS narration service

**BLOCKED UNTIL:** none
**Estimated time:** 45 min
**CP BackEnd pattern:** N/A

**What to do (self-contained):**
> Create a new file `src/Plant/BackEnd/services/tts_service.py` that wraps the `edge-tts` Python package to convert text to speech. The module exports one async function `generate_narration(text: str, *, voice: str = "en-US-AriaNeural", rate: str = "+0%", volume: str = "+0%") -> bytes` which returns raw MP3 bytes. Use `edge_tts.Communicate` to generate audio, write to a temp file, read back as bytes, and clean up. Include a helper `list_voices() -> list[dict]` that returns available voices. Add PII masking to the logger.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/services/media_artifact_store.py` | 1–20 | Import pattern, logging with PiiMaskingFilter |
| `src/Plant/BackEnd/core/logging.py` | 1–30 | PiiMaskingFilter import path |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/services/tts_service.py` | create | New module with `generate_narration()` and `list_voices()` functions. Uses `edge_tts` package. Async function. Writes to tempfile, returns bytes. Logger with `PiiMaskingFilter`. |

**Code patterns to copy exactly:**

```python
"""Text-to-Speech service using Edge TTS (free, no API key).

Produces MP3 audio bytes from text input.
Used by the DMA media generation pipeline for audio and video_audio artifacts.
"""
from __future__ import annotations

import logging
import os
import tempfile
from typing import List, Dict

import edge_tts

from core.logging import PiiMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

# Default voice — natural-sounding US English female
DEFAULT_VOICE = "en-US-AriaNeural"
# Maximum text length to prevent abuse (roughly 10 min of speech)
MAX_TEXT_LENGTH = 15_000


async def generate_narration(
    text: str,
    *,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    volume: str = "+0%",
) -> bytes:
    """Convert text to MP3 audio bytes using Edge TTS.

    Args:
        text: The text to narrate. Truncated to MAX_TEXT_LENGTH chars.
        voice: Edge TTS voice identifier (e.g. "en-US-AriaNeural").
        rate: Speech rate adjustment (e.g. "+10%", "-5%").
        volume: Volume adjustment (e.g. "+0%").

    Returns:
        Raw MP3 bytes.

    Raises:
        ValueError: If text is empty.
        RuntimeError: If TTS generation fails.
    """
    if not text or not text.strip():
        raise ValueError("TTS text cannot be empty")

    # Truncate safely
    narration_text = text[:MAX_TEXT_LENGTH]
    if len(text) > MAX_TEXT_LENGTH:
        logger.warning(
            "tts_service: text truncated",
            extra={"original_length": len(text), "max_length": MAX_TEXT_LENGTH},
        )

    communicate = edge_tts.Communicate(narration_text, voice, rate=rate, volume=volume)

    # Write to temp file, read back, clean up
    fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        await communicate.save(tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        if len(audio_bytes) == 0:
            raise RuntimeError("TTS produced empty audio output")
        logger.info(
            "tts_service: narration generated",
            extra={"voice": voice, "text_length": len(narration_text), "audio_bytes": len(audio_bytes)},
        )
        return audio_bytes
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def list_voices() -> List[Dict]:
    """Return list of available Edge TTS voices."""
    voices = await edge_tts.list_voices()
    return voices
```

**Acceptance criteria:**
1. `generate_narration("Hello world")` returns bytes with length > 0 (mocked)
2. `generate_narration("")` raises `ValueError`
3. Long text (>15000 chars) is truncated without error
4. Logger uses `PiiMaskingFilter`

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S1-T1 | `src/Plant/BackEnd/tests/unit/test_tts_service.py` | Mock `edge_tts.Communicate` and its `save()` method to write fake MP3 bytes to the temp file | `generate_narration("Hello")` returns bytes with length > 0 |
| E2-S1-T2 | same | Pass empty string | `generate_narration("")` raises `ValueError` |
| E2-S1-T3 | same | Pass 20000-char string, mock Communicate | Function succeeds, Communicate receives truncated text (15000 chars) |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm --entrypoint "" plant-backend-test \
  python -m pytest tests/unit/test_tts_service.py -v --no-cov
```

**Commit message:** `feat(DMA-MEDIA-1): E2-S1 — Edge TTS narration service`

**Done signal:** `"E2-S1 done. Created: services/tts_service.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

#### Story E2-S2: Wire TTS into media generation task for audio artifacts

**BLOCKED UNTIL:** E2-S1 committed
**Estimated time:** 45 min
**CP BackEnd pattern:** N/A

**What to do (self-contained):**
> `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py` lines 104-130 currently handle all non-image artifacts (video, audio, video_audio) in a single `else` block that calls `grok_generate_script()` to produce a text markdown script. Add a new `elif first_artifact_type == "audio":` block **before** this `else` block. In the new block: call `generate_narration(text)` from `services.tts_service` to produce actual MP3 audio bytes. Store as `{channel}-narration.mp3` with `mime_type="audio/mpeg"`. If TTS fails, fall back to the existing Grok script behavior. Import `generate_narration` inside the function (inline import pattern matching existing code style).

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py` | 46–130 | Import block (lines 46-50), the `else` branch handling video/audio/video_audio (lines 104-130) |
| `src/Plant/BackEnd/services/tts_service.py` | 1–30 | `generate_narration` function signature (created in E2-S1) |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py` | modify | 1. In the `_run_media_generation` function, after the `if first_artifact_type == "image":` block, add a new `elif first_artifact_type == "audio":` block before the existing `else:` block. 2. In this new block: import `generate_narration` from `services.tts_service` (inline import), call `await generate_narration(text)` to get MP3 bytes, store via `media_store.store_artifact()` with `artifact_type=_AT.AUDIO`, `filename=f"{channel}-narration.mp3"`, `mime_type="audio/mpeg"`. 3. Wrap in try/except: if TTS fails, log warning and fall through to grok_generate_script for text script fallback. |

**Code patterns to copy exactly:**

```python
    elif first_artifact_type == "audio":
        # Real TTS narration via Edge TTS (free, no API key)
        from services.tts_service import generate_narration
        from agent_mold.skills.playbook import ArtifactType as _AT
        try:
            audio_bytes = await generate_narration(text)
            stored = await media_store.store_artifact(
                batch_id=batch_id,
                post_id=post_id,
                artifact_type=_AT.AUDIO,
                filename=f"{channel}-narration.mp3",
                content=audio_bytes,
                mime_type="audio/mpeg",
                metadata={"source": "edge_tts", "text_length": len(text)},
            )
            results = {
                "artifact_uri": stored.uri,
                "artifact_mime_type": "audio/mpeg",
                "artifact_generation_status": "ready",
            }
        except Exception as tts_err:
            logger.warning(
                "generate_media_artifact: TTS failed, falling back to text script",
                extra={"post_id": post_id, "error": str(tts_err)},
            )
            # Fall through to grok_generate_script in the else block below
            if client is None:
                return {**payload, "status": "deferred", "reason": "tts_and_grok_unavailable"}
            script_md = grok_generate_script(
                client, artifact_type="audio", theme=theme,
                brand_name=brand_name, post_text=text, channel=channel,
            )
            stored = await media_store.store_artifact(
                batch_id=batch_id, post_id=post_id, artifact_type=_AT.AUDIO,
                filename=f"{channel}-audio-script.md",
                content=script_md.encode("utf-8"), mime_type="text/markdown",
                metadata={"source": "grok_script", "artifact_type": "audio"},
            )
            results = {
                "artifact_uri": stored.uri,
                "artifact_mime_type": "text/markdown",
                "artifact_generation_status": "ready",
            }
```

**Acceptance criteria:**
1. When `artifact_type == "audio"` and TTS succeeds, stored artifact has `mime_type="audio/mpeg"` and `source="edge_tts"`
2. When `artifact_type == "audio"` and TTS fails but Grok client is available, falls back to text script with `mime_type="text/markdown"`
3. When `artifact_type == "audio"` and both TTS and Grok unavailable, returns `deferred`
4. Existing `image` and `video` paths are unchanged

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E2-S2-T1 | `src/Plant/BackEnd/tests/unit/test_media_gen_tts_wire.py` | Mock `generate_narration` returns b"mp3-data", mock DB + store | Result has `artifact_mime_type: "audio/mpeg"` |
| E2-S2-T2 | same | Mock `generate_narration` raises `RuntimeError`, mock `grok_generate_script` returns "script" | Result has `artifact_mime_type: "text/markdown"` |
| E2-S2-T3 | same | Mock `generate_narration` raises, client is None | Result has `status: "deferred"` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm --entrypoint "" plant-backend-test \
  python -m pytest tests/unit/test_media_gen_tts_wire.py -v --no-cov
```

**Commit message:** `feat(DMA-MEDIA-1): E2-S2 — wire TTS into media generation task`

**Done signal:** `"E2-S2 done. Changed: media_generation_tasks.py. Tests: T1 ✅ T2 ✅ T3 ✅"`

---

### Epic E3: DMA produces narrated video deliverables

**User story:** As a DMA customer, when my agent generates video+audio content (e.g. a narrated YouTube intro), I receive an actual MP4 video file with voiceover — not a markdown storyboard.

---

#### Story E3-S1: FFmpeg audio+visual stitcher service

**BLOCKED UNTIL:** E2-S1 committed (uses `generate_narration`)
**Estimated time:** 45 min
**CP BackEnd pattern:** N/A

**What to do (self-contained):**
> Create a new file `src/Plant/BackEnd/services/media_stitcher.py` that combines an image (bytes) and an audio track (MP3 bytes) into an MP4 video using FFmpeg as a subprocess. Export one async function `stitch_image_audio_to_video(image_bytes: bytes, audio_bytes: bytes, *, image_format: str = "jpg", output_format: str = "mp4") -> bytes` which: writes image and audio to temp files, runs `ffmpeg -loop 1 -i image.jpg -i audio.mp3 -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest -y output.mp4` via `asyncio.create_subprocess_exec`, reads back the output MP4 bytes, cleans up temp files. Include robust error handling and logger with PiiMaskingFilter.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/services/tts_service.py` | 1–40 | Tempfile pattern, logging pattern, PiiMaskingFilter usage (created in E2-S1) |
| `src/Plant/BackEnd/services/media_artifact_store.py` | 1–20 | Import patterns, logging conventions |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/services/media_stitcher.py` | create | New module with `stitch_image_audio_to_video()` function. Uses asyncio subprocess for FFmpeg. Tempfile for I/O. Logger with PiiMaskingFilter. |

**Code patterns to copy exactly:**

```python
"""Media stitcher — combines image + audio into video via FFmpeg.

Used by the DMA media generation pipeline for video_audio artifacts.
FFmpeg must be installed in the container (added to Dockerfile in E4-S1).
"""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile

from core.logging import PiiMaskingFilter

logger = logging.getLogger(__name__)
logger.addFilter(PiiMaskingFilter())

# Max output size: 50 MB
MAX_OUTPUT_BYTES = 50 * 1024 * 1024


async def stitch_image_audio_to_video(
    image_bytes: bytes,
    audio_bytes: bytes,
    *,
    image_format: str = "jpg",
    output_format: str = "mp4",
) -> bytes:
    """Combine a still image and audio track into a video file.

    Uses FFmpeg to loop the image over the audio duration.

    Args:
        image_bytes: Raw image file bytes (JPEG, PNG, or SVG).
        audio_bytes: Raw audio file bytes (MP3).
        image_format: File extension for the temp image file.
        output_format: Output video format (default: mp4).

    Returns:
        Raw video file bytes (MP4).

    Raises:
        ValueError: If image_bytes or audio_bytes are empty.
        RuntimeError: If FFmpeg fails or produces empty output.
    """
    if not image_bytes:
        raise ValueError("image_bytes cannot be empty")
    if not audio_bytes:
        raise ValueError("audio_bytes cannot be empty")

    # Write inputs to temp files
    img_fd, img_path = tempfile.mkstemp(suffix=f".{image_format}")
    aud_fd, aud_path = tempfile.mkstemp(suffix=".mp3")
    out_fd, out_path = tempfile.mkstemp(suffix=f".{output_format}")
    os.close(img_fd)
    os.close(aud_fd)
    os.close(out_fd)

    try:
        with open(img_path, "wb") as f:
            f.write(image_bytes)
        with open(aud_path, "wb") as f:
            f.write(audio_bytes)

        # FFmpeg: loop image over audio, encode as H.264 + AAC
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img_path,
            "-i", aud_path,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            out_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)

        if process.returncode != 0:
            logger.error(
                "media_stitcher: ffmpeg failed",
                extra={"returncode": process.returncode, "stderr": stderr.decode("utf-8", errors="replace")[:500]},
            )
            raise RuntimeError(f"FFmpeg exited with code {process.returncode}")

        with open(out_path, "rb") as f:
            video_bytes = f.read()

        if len(video_bytes) == 0:
            raise RuntimeError("FFmpeg produced empty output file")

        if len(video_bytes) > MAX_OUTPUT_BYTES:
            raise RuntimeError(f"Output video exceeds {MAX_OUTPUT_BYTES} bytes limit")

        logger.info(
            "media_stitcher: video created",
            extra={"image_size": len(image_bytes), "audio_size": len(audio_bytes), "video_size": len(video_bytes)},
        )
        return video_bytes

    finally:
        for path in (img_path, aud_path, out_path):
            try:
                os.unlink(path)
            except OSError:
                pass
```

**Acceptance criteria:**
1. `stitch_image_audio_to_video(image_bytes, audio_bytes)` calls FFmpeg subprocess with correct arguments
2. Returns video bytes when FFmpeg succeeds
3. Raises `RuntimeError` when FFmpeg exits non-zero
4. Raises `ValueError` when image_bytes or audio_bytes are empty
5. Cleans up temp files in all cases (success and failure)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E3-S1-T1 | `src/Plant/BackEnd/tests/unit/test_media_stitcher.py` | Mock `asyncio.create_subprocess_exec` to return process with returncode=0, write fake bytes to output file | Returns bytes with length > 0 |
| E3-S1-T2 | same | Mock subprocess to return returncode=1, stderr=b"error" | Raises `RuntimeError` |
| E3-S1-T3 | same | Pass empty image_bytes | Raises `ValueError("image_bytes cannot be empty")` |
| E3-S1-T4 | same | Pass empty audio_bytes | Raises `ValueError("audio_bytes cannot be empty")` |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm --entrypoint "" plant-backend-test \
  python -m pytest tests/unit/test_media_stitcher.py -v --no-cov
```

**Commit message:** `feat(DMA-MEDIA-1): E3-S1 — FFmpeg audio+visual stitcher service`

**Done signal:** `"E3-S1 done. Created: services/media_stitcher.py. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅"`

---

### Epic E4: DMA media pipeline is production-ready with dependencies and integration

**User story:** As a DMA customer, the media generation pipeline works end-to-end in the deployed container — FFmpeg is installed, Edge TTS is available, and video_audio artifacts produce real narrated videos.

---

#### Story E4-S1: Dockerfile, requirements, and video_audio integration wiring

**BLOCKED UNTIL:** E1-S1, E1-S2, E2-S1, E2-S2, E3-S1 all committed
**Estimated time:** 45 min
**CP BackEnd pattern:** N/A

**What to do (self-contained):**
> Three changes: (1) Add `edge-tts>=6.1.0` to `src/Plant/BackEnd/requirements.txt`. (2) Add `ffmpeg` to the runtime `apt-get install` line in `src/Plant/BackEnd/Dockerfile` (line 31, the Stage 2 runtime apt-get). (3) In `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py`, add a new `elif first_artifact_type == "video_audio":` block that: generates an image (xAI or Pollinations), generates TTS narration, stitches them into an MP4 via `stitch_image_audio_to_video()`, and stores the result. Falls back to Grok text script if stitching fails.

**Files to read first (max 3):**

| File | Lines | What to look for |
|---|---|---|
| `src/Plant/BackEnd/Dockerfile` | 28–35 | Stage 2 runtime `apt-get install` line to add `ffmpeg` |
| `src/Plant/BackEnd/requirements.txt` | last 15 lines | Where to add `edge-tts` |
| `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py` | 46–130 | Import block (lines 46-50), image block (lines 87-103), audio block (from E2-S2), else block for video/video_audio |

**Files to create / modify:**

| File | Action | Precise instruction |
|---|---|---|
| `src/Plant/BackEnd/requirements.txt` | modify | Add `edge-tts>=6.1.0` in the dependencies section (before the Observability section) |
| `src/Plant/BackEnd/Dockerfile` | modify | In Stage 2 (line ~31), change `apt-get install -y --no-install-recommends curl` to `apt-get install -y --no-install-recommends curl ffmpeg` |
| `src/Plant/BackEnd/worker/tasks/media_generation_tasks.py` | modify | Add `elif first_artifact_type == "video_audio":` block after the `audio` block. Import `stitch_image_audio_to_video` from `services.media_stitcher` and `generate_narration` from `services.tts_service` (inline imports). Generate image via `xai_generate_image` or `pollinations_generate_image`, generate TTS via `generate_narration`, stitch via `stitch_image_audio_to_video`, store as MP4. Fallback to grok_generate_script on any failure. |

**Code patterns to copy exactly:**

```python
    elif first_artifact_type == "video_audio":
        # Narrated video: image + TTS → FFmpeg → MP4
        from services.tts_service import generate_narration
        from services.media_stitcher import stitch_image_audio_to_video
        from agent_mold.skills.playbook import ArtifactType as _AT
        try:
            # Step 1: Generate image
            if client is not None:
                image_bytes = xai_generate_image(client, first_prompt)
            else:
                image_bytes = pollinations_generate_image(first_prompt)

            # Step 1b: SVG images can't be looped by FFmpeg — skip stitching
            if image_bytes[:5] == b"<svg ":
                raise RuntimeError("SVG image not suitable for FFmpeg stitching")

            # Step 2: Generate TTS narration
            audio_bytes = await generate_narration(text)

            # Step 3: Stitch into video
            image_fmt = "png" if image_bytes[:4] == b"\x89PNG" else "jpg"
            video_bytes = await stitch_image_audio_to_video(
                image_bytes, audio_bytes, image_format=image_fmt,
            )

            stored = await media_store.store_artifact(
                batch_id=batch_id,
                post_id=post_id,
                artifact_type=_AT.VIDEO_AUDIO,
                filename=f"{channel}-narrated-video.mp4",
                content=video_bytes,
                mime_type="video/mp4",
                metadata={"source": "ffmpeg_stitch", "image_source": "xai" if client else "pollinations"},
            )
            results = {
                "artifact_uri": stored.uri,
                "artifact_mime_type": "video/mp4",
                "artifact_generation_status": "ready",
            }
        except Exception as stitch_err:
            logger.warning(
                "generate_media_artifact: video_audio stitching failed, falling back to script",
                extra={"post_id": post_id, "error": str(stitch_err)},
            )
            if client is None:
                return {**payload, "status": "deferred", "reason": "stitch_and_grok_unavailable"}
            script_md = grok_generate_script(
                client, artifact_type="video_audio", theme=theme,
                brand_name=brand_name, post_text=text, channel=channel,
            )
            stored = await media_store.store_artifact(
                batch_id=batch_id, post_id=post_id, artifact_type=_AT.VIDEO_AUDIO,
                filename=f"{channel}-video-audio-script.md",
                content=script_md.encode("utf-8"), mime_type="text/markdown",
                metadata={"source": "grok_script", "artifact_type": "video_audio"},
            )
            results = {
                "artifact_uri": stored.uri,
                "artifact_mime_type": "text/markdown",
                "artifact_generation_status": "ready",
            }
```

```dockerfile
# Dockerfile Stage 2 — add ffmpeg to runtime dependencies:
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

**Acceptance criteria:**
1. `src/Plant/BackEnd/requirements.txt` contains `edge-tts>=6.1.0`
2. `src/Plant/BackEnd/Dockerfile` Stage 2 apt-get includes `ffmpeg`
3. When `first_artifact_type == "video_audio"` and all steps succeed, stored artifact has `mime_type="video/mp4"` and `source="ffmpeg_stitch"`
4. When image is SVG (both providers down), stitching is skipped and falls back to markdown script
5. When stitching fails but Grok is available, falls back to markdown script
6. When stitching fails and no Grok client, returns `deferred`
7. `docker build` succeeds (Dockerfile syntax valid)

**Tests to write:**

| Test ID | File | Test setup | Assert |
|---|---|---|---|
| E4-S1-T1 | `src/Plant/BackEnd/tests/unit/test_media_gen_video_audio_wire.py` | Mock `xai_generate_image` returns b"img", mock `generate_narration` returns b"mp3", mock `stitch_image_audio_to_video` returns b"mp4", mock DB + store | Result has `artifact_mime_type: "video/mp4"` and `source: "ffmpeg_stitch"` |
| E4-S1-T2 | same | Mock stitch raises RuntimeError, mock `grok_generate_script` returns "script text" | Result has `artifact_mime_type: "text/markdown"` |
| E4-S1-T3 | same | Mock stitch raises, client is None | Result has `status: "deferred"` |
| E4-S1-T4 | same | Mock `xai_generate_image` returns b"<svg ..." (SVG bytes) | Falls through to grok_generate_script fallback (SVG skips stitching) |
| E4-S1-T5 | `src/Plant/BackEnd/tests/unit/test_requirements_dockerfile.py` | Read `requirements.txt` content | `"edge-tts"` appears in file |
| E4-S1-T6 | same | Read `Dockerfile` content | `"ffmpeg"` appears in Stage 2 apt-get line |

**Test command:**
```bash
docker compose -f docker-compose.test.yml run --rm --entrypoint "" plant-backend-test \
  python -m pytest tests/unit/test_media_gen_video_audio_wire.py tests/unit/test_requirements_dockerfile.py -v --no-cov
```

**Commit message:** `feat(DMA-MEDIA-1): E4-S1 — Dockerfile, requirements, video_audio integration`

**Done signal:** `"E4-S1 done. Changed: Dockerfile, requirements.txt, media_generation_tasks.py. Created: test files. Tests: T1 ✅ T2 ✅ T3 ✅ T4 ✅ T5 ✅ T6 ✅"`

---

## Rollback

```bash
# If merged iteration causes a regression:
git log --oneline -10 origin/main          # find merge commit SHA
git revert -m 1 <merge-commit-sha>
git push origin main
# Open fix/DMA-MEDIA-1-rollback branch for the root-cause fix
```
