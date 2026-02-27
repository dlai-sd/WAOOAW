#!/usr/bin/env python3
"""
P-3 migration: swap bare APIRouter() for waooaw_router() in all api/ files.

Usage:  python scripts/migrate_p3_routers.py
Safe to re-run (idempotent).
"""
import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent  # /workspaces/WAOOAW

TARGETS = [
    (WORKSPACE / "src/CP/BackEnd/api",        "core.routing"),
    (WORKSPACE / "src/Plant/BackEnd/api",     "core.routing"),
]


def migrate_file(path: Path, routing_module: str) -> bool:
    """Return True if file was changed."""
    original = path.read_text()
    text = original

    # Skip if already migrated
    if "waooaw_router" in text and "router = APIRouter(" not in text:
        return False

    # Skip if no bare APIRouter() instantiation
    if "router = APIRouter(" not in text:
        return False

    # 1. Change instantiation
    text = text.replace("router = APIRouter(", "router = waooaw_router(")

    # 2. Add waooaw_router import (only once)
    if f"from {routing_module} import waooaw_router" not in text:
        # Insert after the last "from fastapi import ..." block
        # Find the line that imports APIRouter (may be combined with others)
        lines = text.splitlines(keepends=True)
        insert_after = -1
        for i, line in enumerate(lines):
            if re.match(r"^from fastapi import", line):
                insert_after = i
        if insert_after >= 0:
            lines.insert(
                insert_after + 1,
                f"from {routing_module} import waooaw_router  # P-3\n",
            )
            text = "".join(lines)
        else:
            # Fallback: prepend after the module docstring block
            text = f"from {routing_module} import waooaw_router  # P-3\n" + text

    # 3. Remove APIRouter from fastapi imports (to satisfy the ruff ban)
    #    Handles patterns like:
    #      from fastapi import APIRouter
    #      from fastapi import APIRouter, X
    #      from fastapi import X, APIRouter
    #      from fastapi import X, APIRouter, Y
    def strip_apirouter(m: re.Match) -> str:
        items = [x.strip() for x in m.group(1).split(",")]
        items = [x for x in items if x != "APIRouter"]
        if not items:
            return ""  # entire import line becomes empty — remove it
        return f"from fastapi import {', '.join(items)}"

    text = re.sub(
        r"from fastapi import ([\w ,]+)",
        strip_apirouter,
        text,
    )
    # Remove blank lines left by a fully-removed import
    text = re.sub(r"\n{3,}", "\n\n", text)

    if text == original:
        return False

    path.write_text(text)
    return True


def main():
    changed = []
    skipped = []
    for api_dir, routing_module in TARGETS:
        if not api_dir.exists():
            print(f"[WARN] Directory not found: {api_dir}")
            continue
        for path in sorted(api_dir.rglob("*.py")):
            if "__pycache__" in str(path) or path.name == "__init__.py":
                continue
            try:
                if migrate_file(path, routing_module):
                    changed.append(path)
                    print(f"  ✓ {path.relative_to(WORKSPACE)}")
                else:
                    skipped.append(path)
            except Exception as exc:
                print(f"  ✗ {path.relative_to(WORKSPACE)}: {exc}", file=sys.stderr)

    print(f"\nChanged: {len(changed)}  |  Skipped (no bare APIRouter): {len(skipped)}")


if __name__ == "__main__":
    main()
