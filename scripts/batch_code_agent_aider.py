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
- OPENAI_API_KEY (required)
- AIDER_MODEL (optional)
- GITHUB_TOKEN (required if `gh` needs auth)

Optional knobs:
- WAOOAW_BATCH_PROMPT_MAX_CHARS (default 12000): truncate story bodies
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
from typing import List


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
        items = json.loads(result.stdout or "[]") if result.returncode == 0 else []

    stories: List[Story] = []
    for item in items:
        body = (item.get("body") or "").strip()
        stories.append(
            Story(
                number=int(item.get("number")),
                title=(item.get("title") or "").strip(),
                body=body,
            )
        )

    stories.sort(key=lambda s: s.number)
    return stories


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n\n[TRUNCATED]"


def build_batch_prompt(epic_number: str, stories: List[Story]) -> str:
    max_chars = int(os.getenv("WAOOAW_BATCH_PROMPT_MAX_CHARS", "12000"))

    # Add branch context to reduce redo-work across repeated runs on same epic branch.
    commit_count = _git_output(["rev-list", "--count", "origin/main..HEAD"]) or "0"
    changed_files = _git_output(["diff", "--name-only", "origin/main...HEAD"]).splitlines()
    changed_files = [f for f in changed_files if f][:50]
    changed_files_block = "\n".join(f"- {f}" for f in changed_files) if changed_files else "- (none)"

    header = (
        "Implement the following WAOOAW epic in one coherent change set.\n\n"
        f"Epic: #{epic_number}\n"
        f"Stories: {len(stories)}\n\n"
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
                    f"---\nStory #{story.number}: {story.title}",
                    body,
                ]
            )
        )

    prompt = "\n\n".join(chunks)
    if len(prompt) > max_chars:
        prompt = _truncate(prompt, max_chars)
    return prompt


def run_aider_once(prompt: str, target_path: str, model: str) -> None:
    aider_cmd = [
        "aider",
        "--yes",
        "--no-auto-commits",
        f"--model={model}",
        "--message",
        prompt,
        target_path,
    ]

    print(f"[Batch Code Agent] Running single Aider session on: {target_path}")

    process = subprocess.Popen(
        aider_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    output_lines: List[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        output_lines.append(line)

    try:
        process.wait(timeout=1800)  # 30 minute batch guard
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, aider_cmd, output="".join(output_lines))


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-process batch Aider Code Agent")
    parser.add_argument("--epic-number", required=True)
    parser.add_argument("--epic-branch", required=False)
    args = parser.parse_args()

    epic_number = str(args.epic_number)

    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY environment variable is required")
        sys.exit(1)

    model = os.getenv("AIDER_MODEL", "gpt-4o-mini")

    stories = fetch_epic_stories(epic_number)
    if not stories:
        print(f"[Batch Code Agent] No user stories found for epic #{epic_number}")
        return

    prompt = build_batch_prompt(epic_number, stories)

    # Always use repo root for full context in batch mode.
    target_path = "."

    try:
        run_aider_once(prompt, target_path, model)
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

    commit_and_push(epic_number, stories)


if __name__ == "__main__":
    main()
