#!/usr/bin/env python3
"""Validate actions/github-script inline JS blocks.

This is a fast, local guardrail to catch syntax errors (e.g. stray `catch`) in
`.github/workflows/*.yml` before waiting on a full Actions run.

It extracts `script: |` blocks from steps that use `actions/github-script@...`,
wraps them in an async IIFE (so top-level `await` is valid), and runs a syntax
check via:
- local `node --check` if Node is installed, else
- `docker run node:<tag> node --check` as a fallback.

No third-party Python deps.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class ScriptBlock:
    path: Path
    start_line: int  # 1-based, points at first line of script content
    content: str


_GH_SCRIPT_USES_RE = re.compile(r"^\s*uses:\s*actions/github-script@", re.IGNORECASE)
_SCRIPT_BLOCK_RE = re.compile(r"^\s*script:\s*\|\s*$")

# Replace GitHub Actions expressions with something JS-safe.
_EXPR_RE = re.compile(r"\$\{\{[^}]*\}\}")


def _indent_len(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _dedent_block(lines: List[str]) -> str:
    non_empty = [ln for ln in lines if ln.strip()]
    if not non_empty:
        return ""
    min_indent = min(_indent_len(ln) for ln in non_empty)
    return "".join(ln[min_indent:] if len(ln) >= min_indent else ln for ln in lines)


def extract_github_script_blocks(path: Path) -> List[ScriptBlock]:
    text_lines = path.read_text(encoding="utf-8", errors="replace").splitlines(True)
    blocks: List[ScriptBlock] = []

    i = 0
    while i < len(text_lines):
        if not _GH_SCRIPT_USES_RE.match(text_lines[i]):
            i += 1
            continue

        # Find the next `script: |` line.
        j = i + 1
        while j < len(text_lines) and not _SCRIPT_BLOCK_RE.match(text_lines[j]):
            j += 1
        if j >= len(text_lines):
            break

        script_key_indent = _indent_len(text_lines[j])

        # Capture content lines (more indented than the `script:` key line).
        k = j + 1
        content_lines: List[str] = []
        while k < len(text_lines):
            ln = text_lines[k]
            if ln.strip() and _indent_len(ln) <= script_key_indent:
                break
            # blank lines are part of the block
            content_lines.append(ln)
            k += 1

        content = _dedent_block(content_lines)
        blocks.append(
            ScriptBlock(
                path=path,
                start_line=j + 2,  # first content line is after `script: |`
                content=content,
            )
        )
        i = k

    return blocks


def _which(cmd: str) -> str:
    from shutil import which

    return which(cmd) or ""


def _run_node_check(js_path: Path) -> Tuple[int, str]:
    """Return (exit_code, combined_output)."""
    if _which("node"):
        proc = subprocess.run(
            ["node", "--check", str(js_path)],
            capture_output=True,
            text=True,
        )
        return proc.returncode, (proc.stdout + proc.stderr)

    # Fallback to Docker (works in Codespaces/devcontainers).
    if not _which("docker"):
        return 2, "Neither 'node' nor 'docker' is available to validate JS syntax."

    # Use a pinned major to keep behavior stable.
    image = os.environ.get("WAOOAW_NODE_IMAGE", "node:20-alpine")

    # Mount the temp dir into the container and run node --check on the mounted file.
    proc = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{js_path.parent}:/work",
            "-w",
            "/work",
            image,
            "node",
            "--check",
            f"/work/{js_path.name}",
        ],
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout + proc.stderr)


def validate_files(paths: Iterable[Path]) -> int:
    any_failed = False

    for path in paths:
        if not path.exists():
            print(f"[workflow-js] ERROR: file not found: {path}")
            return 2

        blocks = extract_github_script_blocks(path)
        if not blocks:
            print(f"[workflow-js] OK: {path} (no github-script blocks)")
            continue

        print(f"[workflow-js] Checking {path} ({len(blocks)} github-script block(s))")

        for idx, block in enumerate(blocks, start=1):
            sanitized = _EXPR_RE.sub("__EXPR__", block.content)
            wrapped = (
                f"// source: {block.path}:{block.start_line}\n"
                f"(async () => {{\n{sanitized}\n}})().catch((e) => {{\n"
                f"  console.error(e && e.stack ? e.stack : String(e));\n"
                f"  process.exit(1);\n"
                f"}});\n"
            )

            with tempfile.TemporaryDirectory(prefix="waooaw-workflow-js-") as tmpdir:
                js_path = Path(tmpdir) / f"github-script-{path.name}-{idx}.js"
                js_path.write_text(wrapped, encoding="utf-8")

                code, out = _run_node_check(js_path)
                if code != 0:
                    any_failed = True
                    print(
                        f"[workflow-js] FAIL: {path} block #{idx} (starts near line {block.start_line})"
                    )
                    if out.strip():
                        print(out.strip())
                    else:
                        print("(no output)")

    if any_failed:
        print("[workflow-js] ❌ One or more github-script blocks have syntax errors.")
        return 1

    print("[workflow-js] ✅ All github-script blocks passed syntax check.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="+",
        help="Workflow YAML files to check (e.g. .github/workflows/project-automation.yml)",
    )
    args = parser.parse_args()

    exit_code = validate_files([Path(p) for p in args.paths])
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
