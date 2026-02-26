#!/usr/bin/env python3
"""Check that every Alembic migration has a non-trivial downgrade() function.

E4-S2 Iteration 3 — Enforce reversible migration rule.

Exit codes:
  0 — all migrations have implemented downgrade()
  1 — one or more migrations are missing downgrade()

Usage:
  python scripts/check_migration_downgrades.py
  python scripts/check_migration_downgrades.py src/Plant/BackEnd/database/migrations/versions
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_DEFAULT_MIGRATIONS_DIR = (
    Path(__file__).parent.parent
    / "src/Plant/BackEnd/database/migrations/versions"
)


def _has_real_downgrade(filepath: Path) -> bool:
    """Return True if the file has a downgrade() function with a real body.

    A real body means something other than just `pass`, `...`, or
    `raise NotImplementedError(...)`.
    """
    source = filepath.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as exc:
        print(f"  ⚠️  SYNTAX ERROR  {filepath.name}: {exc}")
        return False

    for node in ast.walk(tree):
        if not (isinstance(node, ast.FunctionDef) and node.name == "downgrade"):
            continue

        body = node.body
        # Remove docstring if present
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            body = body[1:]

        if not body:
            return False

        # Trivial body: single `pass`
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            return False

        # Trivial body: single `...`
        if len(body) == 1 and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            val = body[0].value.value
            if val is ...:
                return False

        # Trivial body: single `raise NotImplementedError`
        if len(body) == 1 and isinstance(body[0], ast.Raise):
            exc_node = body[0].exc
            if exc_node is not None:
                # e.g. NotImplementedError("msg") or NotImplementedError
                match exc_node:
                    case ast.Call(func=ast.Name(id="NotImplementedError")):
                        return False
                    case ast.Name(id="NotImplementedError"):
                        return False

        return True  # Has a non-trivial body

    return False  # No downgrade() function found at all


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    migrations_dir = Path(argv[0]) if argv else _DEFAULT_MIGRATIONS_DIR

    if not migrations_dir.is_dir():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        return 1

    migration_files = sorted(migrations_dir.glob("*.py"))
    # Skip __init__ and env.py
    migration_files = [
        f for f in migration_files
        if f.name not in ("__init__.py", "env.py", "script.py.mako")
    ]

    if not migration_files:
        print(f"⚠️  No migration files found in {migrations_dir}")
        return 0

    print(f"🔍 Checking {len(migration_files)} migration(s) in {migrations_dir}\n")

    failures: list[str] = []
    for filepath in migration_files:
        if _has_real_downgrade(filepath):
            print(f"  ✅  {filepath.name}")
        else:
            print(f"  ❌  {filepath.name}  — downgrade() not implemented")
            failures.append(filepath.name)

    print()
    if failures:
        print(f"❌ {len(failures)} migration(s) missing downgrade():")
        for f in failures:
            print(f"   - {f}")
        print("\nAdd a working downgrade() to each file before merging.")
        return 1

    print(f"✅ All {len(migration_files)} migration(s) have downgrade() implemented.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
