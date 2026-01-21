#!/usr/bin/env python3
"""scripts/deploy_agent.py

Autonomous Deployment Agent for WAOOAW.

What it does (real, not aspirational):
- Uses GitHub Models via `GITHUB_TOKEN` to propose deployment-related repo changes
  based on the diff vs `origin/main` (e.g., Dockerfiles, compose, terraform, k8s manifests,
  deploy scripts under infrastructure/ or scripts/)
- Writes changes only under safe prefixes
- Commits and pushes onto the currently checked-out epic branch

What it does NOT do:
- It does not run cloud deployments (no gcloud/terraform apply). That must stay human-approved.
- It does not claim success unless validations run.

Environment:
- `GITHUB_TOKEN` (required)
- `GITHUB_MODELS_ENDPOINT` (optional)
- `GITHUB_MODELS_MODEL` (optional)
- `DEPLOY_AGENT_ALLOWED_PREFIXES` (optional): defaults to `infrastructure/,docker/,scripts/`
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
        "DEPLOY_AGENT_ALLOWED_PREFIXES",
        "infrastructure/,docker/,scripts/",
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
                "content": "You are a senior DevOps engineer. Return ONLY valid JSON with no markdown fences.",
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


def _build_prompt(epic_number: str, base_ref: str, diff_summary: str) -> str:
    return (
        "Based on the diff vs main, propose any required deployment/infrastructure updates.\n\n"
        "Rules:\n"
        "- Only output a single JSON object (no markdown)\n"
        "- Only write under infrastructure/, docker/, or scripts/\n"
        "- Avoid destructive changes; prefer additive/minimal edits\n"
        "- Do not include secrets\n\n"
        "Output schema:\n"
        "{\n"
        '  \"commit_message\": \"...\",\n'
        '  \"files\": [ {\"path\": \"...\", \"content\": \"...\"} ]\n'
        "}\n\n"
        f"Epic: #{epic_number}\n"
        f"Base: {base_ref}\n\n"
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
    parser = argparse.ArgumentParser(description="Autonomous Deployment Agent for WAOOAW")
    parser.add_argument("--epic-number", required=True)
    parser.add_argument("--base", default="origin/main")
    args = parser.parse_args()

    epic_number = str(args.epic_number)
    base_ref = str(args.base)

    model = os.getenv("GITHUB_MODELS_MODEL", DEFAULT_MODEL)
    allowed_prefixes = _get_allowed_prefixes()

    _run(["git", "fetch", "origin", "main"], capture=False)

    diff_stat = _git_output(["diff", "--stat", f"{base_ref}...HEAD"]).strip()
    diff_names = _git_output(["diff", "--name-only", f"{base_ref}...HEAD"]).strip()

    if not diff_names:
        print("[Deploy Agent] No changes vs base; nothing to update")
        return

    diff_summary = (diff_stat + "\n\nFiles changed:\n" + diff_names)[:12000]

    print(f"[Deploy Agent] Epic #{epic_number}")
    print(f"[Deploy Agent] Using GitHub Models model: {model}")
    print(f"[Deploy Agent] Allowed write prefixes: {allowed_prefixes}")

    prompt = _build_prompt(epic_number=epic_number, base_ref=base_ref, diff_summary=diff_summary)

    try:
        raw = call_github_models(prompt=prompt, model=model)
        plan = _extract_first_json_object(raw)
    except Exception as exc:
        print(f"[ERROR] Model invocation/parse failed: {exc}")
        sys.exit(1)

    commit_message = plan.get("commit_message")
    file_items = plan.get("files")

    if not isinstance(commit_message, str) or not commit_message.strip():
        commit_message = f"chore(epic-{epic_number}): update deployment assets"
    if not isinstance(file_items, list) or not file_items:
        print("[Deploy Agent] No deployment changes proposed; exiting")
        return

    files: List[GeneratedFile] = []
    for item in file_items:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        content = item.get("content")
        if isinstance(path, str) and isinstance(content, str):
            files.append(GeneratedFile(path=path, content=content))

    if not files:
        print("[Deploy Agent] No valid file entries found; exiting")
        return

    try:
        written = _write_files(files, allowed_prefixes=allowed_prefixes)
    except Exception as exc:
        print(f"[ERROR] Failed writing files: {exc}")
        sys.exit(1)

    print(f"[Deploy Agent] Wrote {len(written)} files")
    for p in written:
        print(f"- {p}")

    _run(["git", "add", *[str(p) for p in written]])

    staged = _run(["git", "diff", "--cached", "--quiet"])
    if staged.returncode == 0:
        print("[Deploy Agent] No changes staged; skipping commit/push")
        return

    _run(["git", "commit", "-m", commit_message])
    _run(["git", "push", "origin", "HEAD"])
    print("[Deploy Agent] Commit pushed")


if __name__ == "__main__":
    main()
