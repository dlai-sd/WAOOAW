#!/usr/bin/env python3
"""scripts/test_agent.py

Autonomous Testing Agent for WAOOAW.

This agent is designed to run inside GitHub Actions on an epic branch:
- Uses GitHub Models (OpenAI-compatible) via `GITHUB_TOKEN`
- Inspects the diff vs `origin/main` to understand what changed
- Generates pytest tests (as file edits) using a strict JSON schema
- Writes tests into the repo safely
- Runs pytest to validate
- Commits and pushes tests onto the currently checked-out epic branch

Environment:
- `GITHUB_TOKEN` (required): Used to call GitHub Models
- `GITHUB_MODELS_ENDPOINT` (optional): Defaults to `https://models.inference.ai.azure.com/chat/completions`
- `GITHUB_MODELS_MODEL` (optional): Defaults to `gpt-4o-mini`
- `TEST_AGENT_ALLOWED_PREFIXES` (optional): Comma-separated path prefixes allowed for writes

Notes:
- This script intentionally avoids fabricating results. If tests fail, it exits non-zero.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import requests

DEFAULT_MODELS_ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class GeneratedFile:
    path: str
    content: str


def _get_allowed_prefixes() -> List[str]:
    raw = os.getenv(
        "TEST_AGENT_ALLOWED_PREFIXES",
        "backend/tests/,frontend/,src/",
    )
    return [p.strip() for p in raw.split(",") if p.strip()]


def _extract_first_json_object(text: str) -> Dict[str, Any]:
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Model response did not contain a JSON object")

    candidate = cleaned[start : end + 1]
    obj2 = json.loads(candidate)
    if not isinstance(obj2, dict):
        raise ValueError("Extracted JSON was not an object")
    return obj2


def _safe_repo_relative_path(path: str, allowed_prefixes: List[str]) -> Path:
    if path.startswith("/") or path.startswith("\\"):
        raise ValueError(f"Absolute paths are not allowed: {path}")
    if ".." in Path(path).parts:
        raise ValueError(f"Path traversal is not allowed: {path}")

    blocked_prefixes = (".git/", ".github/workflows/")
    normalized = path.replace("\\", "/")

    for blocked in blocked_prefixes:
        if normalized.startswith(blocked):
            raise ValueError(f"Writes to {blocked} are not allowed: {path}")

    if not any(normalized.startswith(prefix) for prefix in allowed_prefixes):
        raise ValueError(f"Refusing to write outside allowed prefixes. Path={path} allowed={allowed_prefixes}")

    return Path(normalized)


def call_github_models(prompt: str, model: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required to call GitHub Models")

    endpoint = os.getenv("GITHUB_MODELS_ENDPOINT", DEFAULT_MODELS_ENDPOINT)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a world-class test engineer. Return ONLY valid JSON with no markdown fences.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 4096,
    }

    resp = requests.post(endpoint, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("No choices returned from GitHub Models")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Empty content returned from GitHub Models")
    return content


def _run(cmd: List[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=False, text=True, capture_output=capture)


def _git_output(args: List[str]) -> str:
    proc = _run(["git", *args], capture=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def _build_prompt(epic_number: str, pr_base: str, story_summary: str, diff_summary: str) -> str:
    return (
        "Generate pytest tests for the changes in this branch.\n\n"
        "Rules:\n"
        "- Only output a single JSON object (no markdown)\n"
        "- Write tests under backend/tests/ (prefer unit tests) when backend code changed\n"
        "- Keep tests deterministic; avoid sleeps and network calls\n"
        "- If existing tests should be updated, include full file contents\n"
        "- Do NOT fabricate test results; we will run pytest after writing\n\n"
        "Output schema:\n"
        "{\n"
        '  \"commit_message\": \"...\",\n'
        '  \"files\": [ {\"path\": \"...\", \"content\": \"...\"} ]\n'
        "}\n\n"
        f"Epic: #{epic_number}\n"
        f"Base: {pr_base}\n"
        f"Story summary: {story_summary}\n\n"
        "Diff (summary):\n"
        f"{diff_summary}\n"
    )


def _write_files(files: List[GeneratedFile], allowed_prefixes: List[str]) -> List[Path]:
    written: List[Path] = []
    for f in files:
        rel = _safe_repo_relative_path(f.path, allowed_prefixes)
        abs_path = Path.cwd() / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(f.content, encoding="utf-8")
        written.append(rel)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomous Testing Agent for WAOOAW")
    parser.add_argument("--epic-number", required=True)
    parser.add_argument("--story-summary", default="")
    parser.add_argument("--base", default="origin/main")
    args = parser.parse_args()

    epic_number = str(args.epic_number)
    base_ref = str(args.base)
    story_summary = str(args.story_summary)

    model = os.getenv("GITHUB_MODELS_MODEL", DEFAULT_MODEL)
    allowed_prefixes = _get_allowed_prefixes()

    # Ensure base ref exists locally.
    _run(["git", "fetch", "origin", "main"], capture=False)

    diff_stat = _git_output(["diff", "--stat", f"{base_ref}...HEAD"]).strip()
    diff_names = _git_output(["diff", "--name-only", f"{base_ref}...HEAD"]).strip()

    if not diff_names:
        print("[Test Agent] No changes vs base; nothing to test")
        return

    diff_summary = (diff_stat + "\n\nFiles changed:\n" + diff_names)[:12000]

    print(f"[Test Agent] Epic #{epic_number}")
    print(f"[Test Agent] Using GitHub Models model: {model}")
    print(f"[Test Agent] Allowed write prefixes: {allowed_prefixes}")

    prompt = _build_prompt(epic_number=epic_number, pr_base=base_ref, story_summary=story_summary, diff_summary=diff_summary)

    try:
        raw = call_github_models(prompt=prompt, model=model)
        plan = _extract_first_json_object(raw)
    except Exception as exc:
        print(f"[ERROR] Model invocation/parse failed: {exc}")
        sys.exit(1)

    commit_message = plan.get("commit_message")
    file_items = plan.get("files")

    if not isinstance(commit_message, str) or not commit_message.strip():
        commit_message = f"test(epic-{epic_number}): add/update tests"
    if not isinstance(file_items, list) or not file_items:
        print("[ERROR] Plan did not include any files")
        sys.exit(1)

    files: List[GeneratedFile] = []
    for item in file_items:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        content = item.get("content")
        if isinstance(path, str) and isinstance(content, str):
            files.append(GeneratedFile(path=path, content=content))

    if not files:
        print("[ERROR] No valid file entries found in plan")
        sys.exit(1)

    try:
        written = _write_files(files, allowed_prefixes=allowed_prefixes)
    except Exception as exc:
        print(f"[ERROR] Failed writing files: {exc}")
        sys.exit(1)

    print(f"[Test Agent] Wrote {len(written)} files")
    for p in written:
        print(f"- {p}")

    # Stage and commit if any changes.
    _run(["git", "add", *[str(p) for p in written]])

    staged = _run(["git", "diff", "--cached", "--quiet"])
    if staged.returncode == 0:
        print("[Test Agent] No changes staged; skipping commit/push")
    else:
        _run(["git", "commit", "-m", commit_message])
        _run(["git", "push", "origin", "HEAD"])
        print("[Test Agent] Commit pushed")

    # Run pytest for backend if present.
    if Path("backend").exists():
        print("[Test Agent] Running pytest backend unit tests...")
        proc = _run(["pytest", "-q"], capture=True)
        print(proc.stdout)
        if proc.returncode != 0:
            print(proc.stderr)
            sys.exit(proc.returncode)

    print("[Test Agent] ✅ Tests passed")


if __name__ == "__main__":
    main()
