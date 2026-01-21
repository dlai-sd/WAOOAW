#!/usr/bin/env python3
"""scripts/code_agent.py

Autonomous Code Agent for WAOOAW.

This agent is designed to run inside GitHub Actions:
- Uses GitHub Models (OpenAI-compatible) via `GITHUB_TOKEN`
- Generates a structured file-change plan (JSON)
- Writes files into the repo safely
- Commits and pushes directly onto the currently checked-out epic branch

Environment:
- `GITHUB_TOKEN` (required): Used to call GitHub Models
- `GITHUB_MODELS_ENDPOINT` (optional): Defaults to `https://models.inference.ai.azure.com/chat/completions`
- `GITHUB_MODELS_MODEL` (optional): Defaults to `gpt-4o-mini`
- `CODE_AGENT_ALLOWED_PREFIXES` (optional): Comma-separated path prefixes allowed for writes
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
from typing import Any, Dict, List, Optional

import requests


DEFAULT_MODELS_ENDPOINT = "https://models.inference.ai.azure.com/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class GeneratedFile:
  path: str
  content: str


def _get_allowed_prefixes() -> List[str]:
  raw = os.getenv(
    "CODE_AGENT_ALLOWED_PREFIXES",
    "src/,backend/,frontend/,infrastructure/",
  )
  prefixes = [p.strip() for p in raw.split(",") if p.strip()]
  return prefixes


def _extract_first_json_object(text: str) -> Dict[str, Any]:
  """Extract the first JSON object from a model response.

  Models sometimes wrap JSON in markdown fences or add extra text.
  This function finds the first plausible object and parses it.
  """

  # Fast path: direct JSON
  try:
    obj = json.loads(text)
    if isinstance(obj, dict):
      return obj
  except Exception:
    pass

  # Strip common fences
  cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE | re.MULTILINE)

  # Heuristic: take substring from first '{' to last '}'
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

  # Block writing into git internals or workflow definitions (safety).
  blocked_prefixes = (".git/", ".github/workflows/")
  for blocked in blocked_prefixes:
    if path.replace("\\", "/").startswith(blocked):
      raise ValueError(f"Writes to {blocked} are not allowed: {path}")

  normalized = path.replace("\\", "/")
  if not any(normalized.startswith(prefix) for prefix in allowed_prefixes):
    raise ValueError(
      f"Refusing to write outside allowed prefixes. Path={path} allowed={allowed_prefixes}"
    )
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
        "content": (
          "You are a world-class software engineer. "
          "Return ONLY valid JSON with no markdown fences."
        ),
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


def _build_prompt(epic_number: str, issue_number: str, story_title: str, story_body: str) -> str:
  return (
    "Implement the following WAOOAW user story as production-grade code changes.\n\n"
    "Hard requirements:\n"
    "- PEP8 formatting (Python), type hints everywhere, Google-style docstrings\n"
    "- 100% testable code (add/update tests when reasonable)\n"
    "- No secrets/hardcoded credentials\n"
    "- No TODOs/placeholders\n"
    "- Keep changes minimal and targeted to the story\n"
    "\n"
    "Output MUST be a single JSON object with this schema:\n"
    "{\n"
    '  \"commit_message\": \"...\",\n'
    '  \"files\": [\n'
    "    {\"path\": \"relative/path.ext\", \"content\": \"full file contents\"}\n"
    "  ]\n"
    "}\n\n"
    f"Epic: #{epic_number}\n"
    f"Story Issue: #{issue_number}\n"
    f"Title: {story_title}\n\n"
    "Story Body:\n"
    f"{story_body}\n"
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


def _run_git(args: List[str]) -> None:
  subprocess.run(["git", *args], check=True)


def main() -> None:
  parser = argparse.ArgumentParser(description="Autonomous Code Agent for WAOOAW")
  parser.add_argument("--epic-number", required=True)
  parser.add_argument("--issue-number", required=True)
  parser.add_argument("--story-title", required=True)
  parser.add_argument("--story-body", required=True)
  args = parser.parse_args()

  epic_number = str(args.epic_number)
  issue_number = str(args.issue_number)
  story_title = str(args.story_title)
  story_body = str(args.story_body)

  model = os.getenv("GITHUB_MODELS_MODEL", DEFAULT_MODEL)
  allowed_prefixes = _get_allowed_prefixes()

  prompt = _build_prompt(epic_number, issue_number, story_title, story_body)
  print(f"[Code Agent] Epic #{epic_number} Story #{issue_number}")
  print(f"[Code Agent] Using GitHub Models model: {model}")
  print(f"[Code Agent] Allowed write prefixes: {allowed_prefixes}")

  try:
    raw = call_github_models(prompt=prompt, model=model)
    plan = _extract_first_json_object(raw)
  except Exception as exc:
    print(f"[ERROR] Model invocation/parse failed: {exc}")
    sys.exit(1)

  commit_message = plan.get("commit_message")
  file_items = plan.get("files")
  if not isinstance(commit_message, str) or not commit_message.strip():
    commit_message = f"feat(epic-{epic_number}): implement story #{issue_number}"
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

  print(f"[Code Agent] Wrote {len(written)} files")
  for p in written:
    print(f"- {p}")

  try:
    _run_git(["add", *[str(p) for p in written]])

    # Skip empty commits.
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], check=False)
    if diff.returncode == 0:
      print("[Code Agent] No changes staged; skipping commit/push")
      return

    _run_git(["commit", "-m", commit_message])
    _run_git(["push", "origin", "HEAD"])
    print("[Code Agent] Commit pushed to current branch")
  except Exception as exc:
    print(f"[ERROR] Git commit/push failed: {exc}")
    sys.exit(1)


if __name__ == "__main__":
  main()
