from __future__ import annotations

import difflib
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "relative_path",
    [
        "__init__.py",
        "audit.py",
        "auth.py",
        "budget.py",
        "error_handler.py",
        "error_handler_new.py",
        "error_handler_old.py",
        "policy.py",
        "rbac.py",
    ],
)
def test_gateway_middleware_files_are_identical(relative_path: str) -> None:
    """Prevent middleware drift between shared gateway and Plant gateway.

    Plant Gateway vendors the shared middleware for Docker/runtime reasons.
    This test ensures the implementations stay byte-identical.
    """

    repo_root = Path(__file__).resolve().parents[1]
    shared_path = repo_root / "src" / "gateway" / "middleware" / relative_path
    plant_path = repo_root / "src" / "Plant" / "Gateway" / "middleware" / relative_path

    assert shared_path.exists(), f"Missing shared middleware file: {shared_path}"
    assert plant_path.exists(), f"Missing Plant middleware file: {plant_path}"

    shared_text = shared_path.read_text(encoding="utf-8")
    plant_text = plant_path.read_text(encoding="utf-8")

    if shared_text != plant_text:
        diff = "".join(
            difflib.unified_diff(
                shared_text.splitlines(keepends=True),
                plant_text.splitlines(keepends=True),
                fromfile=str(shared_path.relative_to(repo_root)),
                tofile=str(plant_path.relative_to(repo_root)),
            )
        )
        # Keep pytest output readable.
        raise AssertionError(f"Middleware drift detected in {relative_path}:\n{diff[:8000]}")
