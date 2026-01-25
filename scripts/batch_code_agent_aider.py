#!/usr/bin/env python3
"""scripts/batch_code_agent_aider.py

Single-process batch Code Agent for WAOOAW.

Goal: reduce ALM Coding Agent runtime by running ONE Aider session per epic
(instead of spawning Aider once per story).

Behavior:
- Fetches all `user-story` issues for the epic
- Builds a consolidated prompt
- Runs Aider once (single repo-map/index)
- Commits once to the epic branch

Environment:
- OPENAI_API_KEY (required for OpenAI models)
- AIDER_MODEL (optional)
- GITHUB_TOKEN (required if `gh` needs auth)

Optional knobs:
- WAOOAW_BATCH_PROMPT_MAX_CHARS (default 12000): truncate story bodies
- WAOOAW_AIDER_MAP_TOKENS (default 1024): token budget for Aider repo-map (0 disables)
- WAOOAW_AIDER_MAP_REFRESH (default files): repo-map refresh policy (auto|always|files|manual)
- WAOOAW_AIDER_MAX_CHAT_HISTORY_TOKENS (default 4000): cap chat history tokens per Aider run
- WAOOAW_AIDER_ANALYSIS (default 1): run Phase-0 analysis pass and feed summary into edit passes
- WAOOAW_CODE_AGENT_SKIP_TESTS / WAOOAW_CODE_AGENT_SKIP_COVERAGE: respected via
  imported gates from `code_agent_aider.py`
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from collections import deque
from typing import Dict, List, Optional, Tuple

import re


def _env_int(name: str, default: int) -> int:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"[Batch Code Agent] ⚠️  Invalid int for {name}={raw!r}; using default {default}")
        return default


def _env_str(name: str, default: str) -> str:
    raw = (os.getenv(name) or "").strip()
    return raw or default


def _truthy_env(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on"}


def _git_ls_files() -> List[str]:
    out = _git_output(["ls-files"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def _git_grep_files(pattern: str) -> List[str]:
    result = subprocess.run(
        ["git", "grep", "-I", "-l", "--", pattern],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        return []
    return [line.strip() for line in (result.stdout or "").splitlines() if line.strip()]


def _default_seed_files() -> List[str]:
    # Seed with common WAOOAW entrypoints if present.
    candidates = [
        "src/CP/BackEnd/main.py",
        "src/CP/BackEnd/app.py",
        "src/CP/BackEnd/api/__init__.py",
        "src/PP/BackEnd/main.py",
        "src/Plant/main.py",
        "src/gateway/main.py",
        "src/gateway/app.py",
        "infrastructure/feature_flags/feature_flags.py",
    ]
    existing: List[str] = []
    for path in candidates:
        if os.path.exists(path):
            existing.append(path)
    return existing


def _parse_roots(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    roots: List[str] = []
    for part in raw.split(","):
        r = part.strip()
        if not r:
            continue
        r = r.replace("\\", "/")
        if r.endswith("/"):
            r = r[:-1]
        roots.append(r)
    # Deduplicate preserving order
    seen = set()
    out: List[str] = []
    for r in roots:
        if r not in seen:
            out.append(r)
            seen.add(r)
    return out


def discover_relevant_files(epic_number: str, stories: List[Story], *, roots: Optional[List[str]] = None) -> List[str]:
    """Pick a deterministic, limited set of files to pass to Aider.

    Aider often refuses to proceed if given only a directory path, asking the user
    to add files. Passing an explicit file list makes batch runs reliable.
    """

    all_files = _git_ls_files()

    # Prefer core code areas. Keep it small enough to not overwhelm the model.
    max_files = int(os.getenv("WAOOAW_AIDER_MAX_FILES", "14"))
    max_bytes = int(os.getenv("WAOOAW_AIDER_MAX_FILE_BYTES", str(50 * 1024)))  # 50KB
    preferred_prefixes = (
        "src/CP/",
        "src/PP/",
        "src/Plant/",
        "src/gateway/",
        "infrastructure/",
        "tests/",
    )

    roots = roots or []
    root_prefixes: Tuple[str, ...]
    if roots:
        root_prefixes = tuple((r + "/") if not r.endswith("/") else r for r in roots)
    else:
        root_prefixes = preferred_prefixes

    def is_candidate(path: str) -> bool:
        if not path.startswith(root_prefixes):
            return False
        # Avoid huge/noisy artifacts.
        lowered = path.lower()
        if any(
            frag in lowered
            for frag in (
                "package-lock.json",
                "pnpm-lock.yaml",
                "yarn.lock",
                "playwright-report/",
                "coverage.json",
                "results.json",
                "/__pycache__/",
                "/node_modules/",
            )
        ):
            return False
        # Focus on code + configs likely touched by implementation.
        if not path.endswith((
            ".py",
            ".yml",
            ".yaml",
        )):
            return False

        # Skip very large files.
        try:
            if os.path.getsize(path) > max_bytes:
                return False
        except OSError:
            return False

        return True

    candidates = [p for p in all_files if is_candidate(p)]

    # Allow a few likely-new files even if they don't exist yet.
    likely_new: List[str] = []
    for base in (roots or ["src/CP", "src/PP", "src/Plant", "src/gateway"]):
        likely_new.extend(
            [
                f"{base}/BackEnd/middleware/request_middleware.py",
                f"{base}/BackEnd/requirements.txt",
            ]
        )

    # Gateway doesn't follow the BackEnd/FrontEnd layout in this repo.
    if not roots or any(r.rstrip("/") == "src/gateway" for r in roots):
        likely_new.extend(
            [
                "src/gateway/middleware/request_middleware.py",
                "src/gateway/requirements.txt",
            ]
        )

    # Keyword-driven grep: only run grep for tokens that appear in the stories.
    combined_text = "\n".join([s.title + "\n" + s.body for s in stories]).lower()
    token_bank = [
        "auth",
        "oauth",
        "jwt",
        "token",
        "middleware",
        "pipeline",
        "request",
        "validation",
        "retry",
        "error",
        "exception",
        "docs",
        "openapi",
        "swagger",
        "sdk",
        "client",
        "monitor",
        "observability",
        "metrics",
        "logging",
        "tracing",
        f"epic #{epic_number}",
        f"{epic_number}",
    ]

    matched_files: List[str] = []
    for token in token_bank:
        if token not in combined_text:
            continue
        for f in _git_grep_files(token):
            if f in candidates:
                matched_files.append(f)

    # Deterministic order: matched first, then seeds, then a few common files.
    ordered: List[str] = []
    seen = set()

    for f in matched_files:
        if f not in seen and os.path.exists(f):
            ordered.append(f)
            seen.add(f)

    for f in _default_seed_files():
        if f not in seen:
            ordered.append(f)
            seen.add(f)

    for f in likely_new:
        if f not in seen:
            ordered.append(f)
            seen.add(f)

    # Ensure we include at least one file from each major area if available.
    if not roots:
        must_have_prefixes = (
            "src/CP/",
            "src/PP/",
            "src/Plant/",
        )
        for prefix in must_have_prefixes:
            if any(p.startswith(prefix) for p in ordered):
                continue
            for f in candidates:
                if f.startswith(prefix) and f not in seen and os.path.exists(f):
                    ordered.append(f)
                    seen.add(f)
                    break

    # If still too small, include a few top-level API modules if present.
    fallback_prefixes = (
        "src/CP/BackEnd/api/",
        "src/PP/BackEnd/api/",
        "src/Plant/api/",
        "src/gateway/",
    )
    for f in candidates:
        if len(ordered) >= max_files:
            break
        if f.startswith(fallback_prefixes) and f not in seen and os.path.exists(f):
            ordered.append(f)
            seen.add(f)

    # Final cap.
    return ordered[:max_files]


_AIDER_REQUESTS_FILE_ADD_RE = re.compile(r"^\s*Please add these files to the chat so I can", re.IGNORECASE)
_AIDER_SUGGESTED_FILE_RE = re.compile(r"^\s*\d+\s+([A-Za-z0-9_./\\-]+\.(?:py|js|ts|tsx|json|ya?ml))\b")


def _parse_aider_suggested_files(output_lines: List[str]) -> List[str]:
    suggested: List[str] = []
    for line in output_lines:
        m = _AIDER_SUGGESTED_FILE_RE.match(line.strip())
        if not m:
            continue
        path = m.group(1).strip()
        # Normalize backslashes just in case.
        path = path.replace("\\\\", "/")
        if os.path.exists(path):
            suggested.append(path)
    # Deduplicate preserving order
    seen = set()
    out: List[str] = []
    for p in suggested:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


def _git_status_paths() -> List[str]:
    """Return paths that are modified/added/renamed in the working tree."""

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        text=True,
        capture_output=True,
        check=False,
    )
    out: List[str] = []
    for raw in (result.stdout or "").splitlines():
        line = raw.rstrip("\n")
        if len(line) < 4:
            continue
        path = line[3:]
        # Handle renames: "R  old -> new"
        if "->" in path:
            path = path.split("->", 1)[1].strip()
        path = path.strip().replace("\\", "/")
        if path:
            out.append(path)
    # Deduplicate preserving order
    seen = set()
    paths: List[str] = []
    for p in out:
        if p not in seen:
            paths.append(p)
            seen.add(p)
    return paths


def _flake8_syntax_check(files: List[str]) -> Tuple[bool, str]:
    """Run flake8 syntax/undefined-name checks on the provided files."""

    py_files = [f for f in files if f.endswith(".py") and os.path.exists(f)]
    if not py_files:
        return True, ""

    flake8_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "flake8",
            "--select=E9,F821,F823,F831,F406,F407,F701,F702,F704,F706",
            "--show-source",
            "--isolated",
            *py_files,
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    ok = flake8_result.returncode == 0
    stdout = (flake8_result.stdout or "").strip()
    stderr = (flake8_result.stderr or "").strip()
    report = "\n".join([part for part in (stdout, stderr) if part]).strip()
    # Local dev environments may not have flake8; don't hard-fail the repair loop.
    if not ok and ("No module named flake8" in report or "No module named 'flake8'" in report):
        print("[Batch Code Agent] ⚠️  flake8 not available; skipping automatic repair loop")
        return True, ""
    return ok, report


def _extract_flake8_paths(report: str) -> List[str]:
    paths: List[str] = []
    seen = set()
    for line in report.splitlines():
        # Format: path:line:col: CODE message
        if ":" not in line:
            continue
        path = line.split(":", 1)[0].strip()
        if not path or not os.path.exists(path):
            continue
        if path not in seen:
            paths.append(path)
            seen.add(path)
    return paths


def _truncate_lines(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[TRUNCATED]"


def _repair_common_python_errors(*, model: str, pass_label: str) -> None:
    """Ask Aider to fix flake8-reported syntax/name errors on changed files."""

    max_rounds = int(os.getenv("WAOOAW_AIDER_REPAIR_ROUNDS", "3"))
    max_error_chars = int(os.getenv("WAOOAW_AIDER_REPAIR_MAX_CHARS", "8000"))

    for attempt in range(1, max_rounds + 1):
        changed_paths = _git_status_paths()
        ok, report = _flake8_syntax_check(changed_paths)
        if ok:
            return
        if not report:
            # flake8 signaled failure but gave no output; don't loop forever.
            print(f"[ERROR] flake8 reported failure with no output during repair (pass: {pass_label})")
            sys.exit(1)

        target_files = _extract_flake8_paths(report)
        if not target_files:
            # Fall back to all changed python files.
            target_files = [p for p in changed_paths if p.endswith(".py") and os.path.exists(p)]

        truncated_report = _truncate_lines(report, max_error_chars)

        repair_prompt = (
            f"Repair pass {attempt}/{max_rounds} for {pass_label}.\n"
            "Fix ONLY the Python issues reported by flake8 below (syntax errors, indentation, undefined names).\n"
            "Do not refactor or change behavior beyond what's required to make the code correct.\n\n"
            "flake8 output:\n"
            f"{truncated_report}\n"
        )

        print(
            f"[Batch Code Agent] [{pass_label}] Repairing flake8 issues (attempt {attempt}/{max_rounds}) on {len(target_files)} file(s)"
        )
        rc, _ = run_aider_once(repair_prompt, target_files, model)
        if rc != 0:
            print(f"[ERROR] Aider repair attempt failed with exit code {rc} (pass: {pass_label})")
            sys.exit(1)

    # Still failing after max attempts; fail fast with the latest report.
    changed_paths = _git_status_paths()
    ok, report = _flake8_syntax_check(changed_paths)
    if not ok:
        print(f"[ERROR] Unable to repair flake8 issues after {max_rounds} attempts (pass: {pass_label})")
        print(report)
        sys.exit(1)


def _repo_args() -> List[str]:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        return ["--repo", repo]
    return []


@dataclass(frozen=True)
class Story:
    number: int
    title: str
    body: str
    state: str = ""


def _run(cmd: List[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def _git_output(args: List[str]) -> str:
    result = subprocess.run(["git", *args], text=True, capture_output=True, check=False)
    return (result.stdout or "").strip()


def fetch_epic_stories(epic_number: str) -> List[Story]:
    """Fetch all user stories referencing an epic.

    We use `gh issue list` to avoid needing extra Python deps.
    """

    max_stories = int(os.getenv("WAOOAW_BATCH_MAX_STORIES", "80"))

    # Preferred: epic label grouping (fast + precise)
    label_cmd = [
        "gh",
        *_repo_args(),
        "issue",
        "list",
        "--state",
        "all",
        "--label",
        "user-story",
        "--label",
        f"epic-{epic_number}",
        "--limit",
        str(max_stories),
        "--json",
        "number,title,body,state",
    ]

    result = _run(label_cmd, check=False)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        if stderr:
            print("[Batch Code Agent] gh issue list (label query) failed:")
            print(stderr)

    items = json.loads(result.stdout or "[]") if result.returncode == 0 else []

    # Fallback: body search (slower + less precise)
    if not items:
        search_cmd = [
            "gh",
            *_repo_args(),
            "issue",
            "list",
            "--state",
            "all",
            "--label",
            "user-story",
            "--search",
            f'"Epic #{epic_number}" in:body',
            "--limit",
            str(max_stories),
            "--json",
            "number,title,body,state",
        ]

        result = _run(search_cmd, check=False)
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            if stderr:
                print("[Batch Code Agent] gh issue list (body search) failed:")
                print(stderr)

        items = json.loads(result.stdout or "[]") if result.returncode == 0 else []

    stories: List[Story] = []
    for item in items:
        body = (item.get("body") or "").strip()
        stories.append(
            Story(
                number=int(item.get("number")),
                title=(item.get("title") or "").strip(),
                body=body,
                state=(item.get("state") or "").strip(),
            )
        )

    stories.sort(key=lambda s: s.number)
    return stories


_STORY_KEY_RE_CACHE: Dict[str, re.Pattern[str]] = {}


def _story_key(epic_number: str, title: str) -> Optional[Tuple[str, int]]:
    """Extract a stable story key from an issue title.

    Accepts:
      - [US-<epic>-<index>] ...
      - [TECH-<epic>-<index>] ...

    Returns:
      (kind, index) where kind in {"US", "TECH"}.
    """

    if epic_number not in _STORY_KEY_RE_CACHE:
        _STORY_KEY_RE_CACHE[epic_number] = re.compile(
            rf"\[(US|TECH)-{re.escape(epic_number)}-(\d+)\]",
            re.IGNORECASE,
        )

    match = _STORY_KEY_RE_CACHE[epic_number].search(title)
    if not match:
        return None

    kind = match.group(1).upper()
    index = int(match.group(2))
    return (kind, index)


def normalize_stories(epic_number: str, stories: List[Story]) -> Tuple[List[Story], List[str]]:
    """Filter/dedupe stories so the batch prompt is deterministic.

    Why this exists:
    - Mislabelled issues (e.g., tech tasks tagged as user-story) can sneak in.
    - Reruns can produce duplicates (same [US-<epic>-<n>] title).

    Policy:
    - Only keep issues whose title contains a recognizable [US-<epic>-<n>] or
      [TECH-<epic>-<n>] token.
    - Dedupe by (kind, index). Prefer the issue with the longest body (more spec).
      Tie-breaker: prefer higher issue number (newer).
    """

    warnings: List[str] = []

    keyed: Dict[Tuple[str, int], Story] = {}
    dropped_unkeyed: List[int] = []
    dropped_dupes: List[Tuple[int, int, Tuple[str, int]]] = []

    for story in stories:
        key = _story_key(epic_number, story.title)
        if key is None:
            dropped_unkeyed.append(story.number)
            continue

        existing = keyed.get(key)
        if existing is None:
            keyed[key] = story
            continue

        pick_new = False
        if len(story.body) > len(existing.body):
            pick_new = True
        elif len(story.body) == len(existing.body) and story.number > existing.number:
            pick_new = True

        if pick_new:
            dropped_dupes.append((existing.number, story.number, key))
            keyed[key] = story
        else:
            dropped_dupes.append((story.number, existing.number, key))

    if dropped_unkeyed:
        warnings.append(
            "Excluded issues without [US-<epic>-<n>] or [TECH-<epic>-<n>] token: "
            + ", ".join(f"#{n}" for n in sorted(dropped_unkeyed))
        )

    if dropped_dupes:
        # Report at most 10 to keep logs tidy.
        sample = dropped_dupes[:10]
        details = "; ".join(
            f"{k[0]}-{k[1]}: kept #{kept}, dropped #{dropped}" for dropped, kept, k in sample
        )
        extra = "" if len(dropped_dupes) <= 10 else f" (+{len(dropped_dupes) - 10} more)"
        warnings.append(f"Deduped duplicate story keys: {details}{extra}")

    normalized = list(keyed.values())
    normalized.sort(key=lambda s: (_story_key(epic_number, s.title) or ("ZZ", 999999), s.number))
    return normalized, warnings


def fetch_epic_overview(epic_number: str) -> Optional[str]:
    """Fetch epic issue title/body to anchor the batch prompt in real scope."""

    cmd = [
        "gh",
        *_repo_args(),
        "issue",
        "view",
        str(epic_number),
        "--json",
        "title,body",
    ]

    result = _run(cmd, check=False)
    if result.returncode != 0:
        return None

    try:
        data = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return None

    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    if not title and not body:
        return None

    return "\n".join(
        [
            f"Epic Title: {title}" if title else "",
            "Epic Body:\n" + body if body else "",
        ]
    ).strip()


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n\n[TRUNCATED]"


def build_batch_prompt(epic_number: str, stories: List[Story]) -> str:
    max_chars = int(os.getenv("WAOOAW_BATCH_PROMPT_MAX_CHARS", "24000"))

    # Add branch context to reduce redo-work across repeated runs on same epic branch.
    commit_count = _git_output(["rev-list", "--count", "origin/main..HEAD"]) or "0"
    changed_files = _git_output(["diff", "--name-only", "origin/main...HEAD"]).splitlines()
    changed_files = [f for f in changed_files if f][:50]
    changed_files_block = "\n".join(f"- {f}" for f in changed_files) if changed_files else "- (none)"

    epic_overview = fetch_epic_overview(epic_number)
    epic_overview_block = (
        "Epic Overview (source of truth):\n" + _truncate(epic_overview, 8000) + "\n\n"
        if epic_overview
        else ""
    )

    header = (
        "Implement the following WAOOAW epic in one coherent change set.\n\n"
        f"Epic: #{epic_number}\n"
        f"Stories: {len(stories)}\n\n"
        + epic_overview_block +
        "Current branch context (already implemented work):\n"
        f"- Commits vs main: {commit_count}\n"
        "- Files changed vs main (first 50):\n"
        f"{changed_files_block}\n\n"
        "Constraints:\n"
        "- Follow existing code patterns and style\n"
        "- No TODOs/placeholders; production-ready only\n"
        "- Add/update tests where appropriate\n"
        "- Keep changes minimal and focused\n"
        "- If a story is already implemented on this branch, do not redo it\n\n"
        "Stories:\n"
    )

    per_story_budget = max(1000, max_chars // max(1, len(stories)))
    chunks: List[str] = [header]

    for story in stories:
        body = _truncate(story.body, per_story_budget)
        chunks.append(
            "\n".join(
                [
                    f"---\nStory #{story.number} [{story.state or 'UNKNOWN'}]: {story.title}",
                    body,
                ]
            )
        )

    prompt = "\n\n".join(chunks)
    if len(prompt) > max_chars:
        prompt = _truncate(prompt, max_chars)
    return prompt


def run_repo_analysis(epic_number: str, stories: List[Story], model: str) -> str:
    """Phase-0: run a bounded, non-editing Aider pass to summarize architecture.

    Notes:
    - This Aider build supports: --dry-run, --map-tokens, --map-refresh, --max-chat-history-tokens
    - We intentionally keep the prompt short (titles only) and truncate the output.
    """

    if not _truthy_env("WAOOAW_AIDER_ANALYSIS", default=True):
        return ""

    max_story_titles = _env_int("WAOOAW_AIDER_ANALYSIS_MAX_STORIES", 20)
    max_out_chars = _env_int("WAOOAW_AIDER_ANALYSIS_MAX_CHARS", 6000)

    titles_block = "\n".join(f"- {s.title}" for s in stories[:max_story_titles])
    epic_overview = fetch_epic_overview(epic_number)
    epic_overview_block = _truncate(epic_overview, 4000) if epic_overview else ""

    analysis_prompt = (
        "You are performing a READ-ONLY repository analysis for WAOOAW.\n\n"
        f"Epic: #{epic_number}\n\n"
        + (f"Epic overview (source of truth):\n{epic_overview_block}\n\n" if epic_overview_block else "")
        + "Stories (titles only):\n"
        f"{titles_block}\n\n"
        "Return a concise, structured summary:\n"
        "1) Key modules / boundaries\n"
        "2) Likely impacted areas for this epic\n"
        "3) Risky dependencies / integration points\n"
        "4) Suggested implementation order (layers)\n\n"
        "Rules:\n"
        "- Do NOT propose code diffs\n"
        "- Do NOT ask to add files\n"
        "- Keep it brief and actionable\n"
    )

    map_tokens = _env_int("WAOOAW_AIDER_MAP_TOKENS", 1024)
    map_refresh = _env_str("WAOOAW_AIDER_MAP_REFRESH", "files")
    max_hist_tokens = _env_int("WAOOAW_AIDER_MAX_CHAT_HISTORY_TOKENS", 4000)

    # Aider sometimes behaves better if at least one file is in scope.
    seed_files = [p for p in _default_seed_files() if os.path.exists(p)][:4]
    if not seed_files:
        seed_files = ["README.md"] if os.path.exists("README.md") else []

    aider_cmd = [
        "aider",
        "--yes-always",
        "--no-gitignore",
        "--no-analytics",
        "--no-auto-commits",
        "--dry-run",
        "--map-refresh",
        map_refresh,
        "--max-chat-history-tokens",
        str(max_hist_tokens),
        f"--model={model}",
        "--message",
        analysis_prompt,
        *seed_files,
    ]

    # Only pass map-tokens when non-negative; allow 0 to disable explicitly.
    aider_cmd.insert(aider_cmd.index("--map-refresh"), "--map-tokens")
    aider_cmd.insert(aider_cmd.index("--map-refresh"), str(map_tokens))

    print("[Batch Code Agent] 🔍 Phase-0: running Aider analysis pass")
    result = subprocess.run(aider_cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        print("[Batch Code Agent] ⚠️  Analysis pass failed; proceeding without summary")
        return ""

    summary = (result.stdout or "").strip()
    if not summary:
        return ""

    if len(summary) > max_out_chars:
        summary = summary[:max_out_chars].rstrip() + "\n\n[TRUNCATED]"
    return summary


def run_aider_once(prompt: str, files: List[str], model: str) -> Tuple[int, List[str]]:
    if not files:
        raise ValueError("No files provided to Aider")

    map_tokens = _env_int("WAOOAW_AIDER_MAP_TOKENS", 1024)
    map_refresh = _env_str("WAOOAW_AIDER_MAP_REFRESH", "files")
    max_hist_tokens = _env_int("WAOOAW_AIDER_MAX_CHAT_HISTORY_TOKENS", 4000)

    aider_cmd = [
        "aider",
        "--yes-always",
        "--no-gitignore",
        "--no-analytics",
        "--no-auto-commits",
        "--map-tokens",
        str(map_tokens),
        "--map-refresh",
        map_refresh,
        "--max-chat-history-tokens",
        str(max_hist_tokens),
        "--edit-format",
        "diff",
        f"--model={model}",
        "--message",
        prompt,
        "--message",
        "Proceed now: apply the changes directly in the repo. Do not ask for confirmation. Create new files if needed.",
        *files,
    ]

    print(f"[Batch Code Agent] Running single Aider session on {len(files)} files")

    process = subprocess.Popen(
        aider_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    # Avoid log spam: stream only the first N lines, but keep a tail buffer
    # so we can still detect token-limit / "add files" failures reliably.
    max_stream_lines = int(os.getenv("WAOOAW_AIDER_MAX_STREAM_LINES", "400"))
    tail_lines = int(os.getenv("WAOOAW_AIDER_TAIL_LINES", "300"))
    output_tail: deque[str] = deque(maxlen=max(50, tail_lines))
    streamed = 0
    truncated_notice_printed = False
    assert process.stdout is not None
    for line in process.stdout:
        output_tail.append(line)
        if streamed < max_stream_lines:
            print(line, end="")
            streamed += 1
        elif not truncated_notice_printed:
            truncated_notice_printed = True
            print(
                f"[Batch Code Agent] (Aider output truncated after {max_stream_lines} lines; set WAOOAW_AIDER_MAX_STREAM_LINES to increase)"
            )

    try:
        process.wait(timeout=1800)  # 30 minute batch guard
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise

    return process.returncode or 0, list(output_tail)


def commit_and_push(epic_number: str, stories: List[Story]) -> None:
    diff_check = subprocess.run(["git", "diff", "--quiet"], check=False)
    if diff_check.returncode == 0:
        print("[Batch Code Agent] No changes to commit")
        return

    subprocess.run(["git", "add", "."], check=True)

    # Reuse P0 gates from the existing per-story agent (keeps behavior aligned)
    try:
        import code_agent_aider as gates
    except Exception as e:  # pragma: no cover
        print(f"[ERROR] Failed to import gates from code_agent_aider.py: {e}")
        raise

    print("\n" + "=" * 80)
    print("[Batch Code Agent] Running P0 Quality Gates...")
    print("=" * 80)

    if not gates.check_required_dependencies():
        print("[ERROR] Missing required dependencies for gates")
        subprocess.run(["git", "reset", "HEAD"], check=False)
        sys.exit(1)

    if not gates.validate_syntax():
        print("[ERROR] P0 gate failed: syntax")
        subprocess.run(["git", "reset", "HEAD"], check=False)
        sys.exit(1)

    if not gates.detect_stubs():
        print("[ERROR] P0 gate failed: stubs")
        subprocess.run(["git", "reset", "HEAD"], check=False)
        sys.exit(1)

    story_numbers = ",".join(str(s.number) for s in stories[:10])
    if len(stories) > 10:
        story_numbers += f",+{len(stories) - 10} more"

    commit_message = (
        f"feat(epic-{epic_number}): implement {len(stories)} stories\n\n"
        f"Stories: {story_numbers}"
    )

    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)

    print("[Batch Code Agent] ✅ Changes committed and pushed")


def _print_working_tree_summary() -> None:
    diff_files = _git_output(["diff", "--name-only"]).splitlines()
    diff_files = [f for f in diff_files if f]
    print("\n" + "=" * 80)
    print("[Batch Code Agent] Local run summary (working tree)")
    print("=" * 80)
    if not diff_files:
        print("[Batch Code Agent] No working tree changes")
        return

    print(f"[Batch Code Agent] Files changed: {len(diff_files)}")
    for f in diff_files[:50]:
        print(f"- {f}")
    if len(diff_files) > 50:
        print(f"- (+{len(diff_files) - 50} more)")

    stat = subprocess.run(["git", "diff", "--stat"], text=True, capture_output=True, check=False)
    if stat.stdout:
        print("\n[Batch Code Agent] Diffstat:\n" + stat.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-process batch Aider Code Agent")
    parser.add_argument("--epic-number", required=True)
    parser.add_argument("--epic-branch", required=False)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only verify story discovery (no Aider run, no commits).",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Run Aider but do not commit/push; leave changes in working tree.",
    )
    parser.add_argument(
        "--roots",
        required=False,
        help="Comma-separated root folders to target (eg: src/CP,src/PP,src/Plant,src/gateway). If set, runs multi-pass (one Aider session per root) and commits once.",
    )
    args = parser.parse_args()

    epic_number = str(args.epic_number)

    raw_stories = fetch_epic_stories(epic_number)
    stories, warnings = normalize_stories(epic_number, raw_stories)

    print(f"[Batch Code Agent] Discovered {len(raw_stories)} labelled issues for epic #{epic_number}.")
    for w in warnings:
        print(f"[Batch Code Agent] ⚠️  {w}")

    print("[Batch Code Agent] Using story set:")
    for s in stories:
        print(f"[Batch Code Agent] - #{s.number} [{s.state or 'UNKNOWN'}] ({len(s.body)} chars) {s.title}")
    if not stories:
        print(f"[Batch Code Agent] No user stories found for epic #{epic_number}")
        print(
            "[Batch Code Agent] Expected: issues labeled 'user-story' and either labeled 'epic-<n>' or containing 'Epic #<n>' in the body."
        )
        print(
            "[Batch Code Agent] Most common root cause: gh CLI unauthenticated. In GitHub Actions, set GH_TOKEN (preferred) or GITHUB_TOKEN."
        )
        print("[Batch Code Agent] Debug: try running:")
        print(f"[Batch Code Agent]   gh issue list --state all --label user-story --label epic-{epic_number} --limit 5")
        # Exit non-zero so CI doesn't treat this as a successful coding run.
        sys.exit(2)

    if args.check_only:
        print(
            f"[Batch Code Agent] ✅ Story discovery OK for epic #{epic_number}: {len(stories)} stories"
        )
        sys.exit(0)

    model = os.getenv("AIDER_MODEL", "gpt-4o-mini")

    # Some providers (eg github_copilot/* via LiteLLM) do not use OPENAI_API_KEY.
    if not model.lower().startswith("github_copilot/") and not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY environment variable is required for model: " + model)
        print("[ERROR] Set OPENAI_API_KEY or use a provider model (eg github_copilot/*).")
        sys.exit(1)

    prompt = build_batch_prompt(epic_number, stories)
    print(f"[Batch Code Agent] Prompt size: {len(prompt)} chars")

    analysis_summary = run_repo_analysis(epic_number, stories, model)
    if analysis_summary:
        print(f"[Batch Code Agent] Phase-0 analysis summary size: {len(analysis_summary)} chars")

    roots = _parse_roots(args.roots or os.getenv("WAOOAW_AIDER_ROOTS"))
    if roots:
        print(f"[Batch Code Agent] Multi-pass roots: {', '.join(roots)}")

    def _run_one(pass_label: str, pass_roots: Optional[List[str]]) -> None:
        files = discover_relevant_files(epic_number, stories, roots=pass_roots)
        if not files:
            print(f"[Batch Code Agent] ⚠️  No candidate files found for pass: {pass_label}")
            return

        print(f"[Batch Code Agent] [{pass_label}] Passing {len(files)} files to Aider")
        for f in files[:20]:
            print(f"[Batch Code Agent] [{pass_label}] - {f}")
        if len(files) > 20:
            print(f"[Batch Code Agent] [{pass_label}] - (+{len(files) - 20} more)")

        analysis_block = (
            "\n\nARCHITECTURE SUMMARY (guidance; keep changes aligned):\n"
            + analysis_summary
            + "\n\n"
            if analysis_summary
            else "\n\n"
        )

        scoped_prompt = (
            f"IMPORTANT: Focus changes primarily under: {pass_label}. "
            "If unrelated files are required, keep changes minimal.\n"
            "Rules:\n"
            "- Do NOT expand scope by scanning unrelated folders\n"
            "- Prefer modifying only the provided files; if new files are required, keep them minimal\n"
            "- If you cannot proceed without additional files, ask for clarification rather than loading more context\n\n"
            + analysis_block
            + prompt
        )

        rc, out_lines = run_aider_once(scoped_prompt, files, model)

        token_limit_hit = any(
            ("token limit" in l.lower() or ("exceeds the" in l.lower() and "token" in l.lower()))
            for l in out_lines
        )
        if token_limit_hit:
            print(
                "[ERROR] Aider hit a token/context limit; reduce WAOOAW_AIDER_MAX_FILES or use a larger-context model"
            )
            print(
                "[ERROR] Context knobs: "
                f"AIDER_MODEL={model} "
                f"WAOOAW_AIDER_MAX_FILES={os.getenv('WAOOAW_AIDER_MAX_FILES', '14')} "
                f"WAOOAW_AIDER_MAP_TOKENS={os.getenv('WAOOAW_AIDER_MAP_TOKENS', '1024')} "
                f"WAOOAW_AIDER_MAP_REFRESH={os.getenv('WAOOAW_AIDER_MAP_REFRESH', 'files')} "
                f"WAOOAW_AIDER_MAX_CHAT_HISTORY_TOKENS={os.getenv('WAOOAW_AIDER_MAX_CHAT_HISTORY_TOKENS', '4000')}"
            )
            sys.exit(1)

        needs_files = any(_AIDER_REQUESTS_FILE_ADD_RE.search(l) for l in out_lines)
        if needs_files:
            suggested = _parse_aider_suggested_files(out_lines)
            if suggested:
                print("[Batch Code Agent] Aider requested explicit files; retrying once with suggested files added")
                merged = files + [p for p in suggested if p not in files]
                rc, out_lines = run_aider_once(scoped_prompt, merged, model)
                needs_files = any(_AIDER_REQUESTS_FILE_ADD_RE.search(l) for l in out_lines)
                token_limit_hit = any(
                    ("token limit" in l.lower() or ("exceeds the" in l.lower() and "token" in l.lower()))
                    for l in out_lines
                )
                if token_limit_hit:
                    print(
                        "[ERROR] Aider hit a token/context limit after retry; reduce WAOOAW_AIDER_MAX_FILES or use a larger-context model"
                    )
                    sys.exit(1)

        if rc != 0:
            raise subprocess.CalledProcessError(rc, ["aider"], output="".join(out_lines))
        if needs_files:
            print("[ERROR] Aider refused to proceed and asked to add files to the chat")
            sys.exit(1)

        # Repair common flake8-reported issues early so we don't fail P0 gates later.
        _repair_common_python_errors(model=model, pass_label=pass_label)

    try:
        if roots:
            for r in roots:
                _run_one(r, [r])
        else:
            _run_one("repo", None)
    except subprocess.TimeoutExpired:
        print("[ERROR] Batch Aider session timed out")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Batch Aider failed with exit code {e.returncode}")
        if e.output:
            print(e.output)
        sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] Aider is not installed. Run: pip install aider-chat")
        sys.exit(1)

    if args.no_commit:
        _print_working_tree_summary()
        return

    commit_and_push(epic_number, stories)


if __name__ == "__main__":
    main()
