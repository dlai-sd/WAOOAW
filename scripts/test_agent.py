#!/usr/bin/env python3
"""scripts/test_agent.py

Deterministic Test Agent for WAOOAW.

Runs existing tests on epic branch and reports results.
No AI - just test execution and reporting.

Environment:
- `GITHUB_TOKEN` (required): For posting test results via GitHub CLI
"""

import argparse
import json
import os
import re
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


DEFAULT_TEST_ROOTS_SMOKE = [
    Path("tests"),
    # These contract tests are stable and don't require services.
    Path("main/Foundation/Architecture/APIGateway/tests"),
]

# "standard" expands into a few known-stable service suites. We intentionally do
# not scan the entire repo by default.
DEFAULT_TEST_ROOTS_STANDARD = [
    *DEFAULT_TEST_ROOTS_SMOKE,
    Path("src/CP/BackEnd/tests"),
    Path("src/gateway/middleware/tests"),
]

DEFAULT_EXCLUDE_SUBSTRINGS = [
    "/performance/",
    "/e2e/",
    "test_integration_docker.py",
    "test_e2e_",
]

DEFAULT_EXCLUDE_FILENAME_TOKENS = [
    "load",
    "perf",
    "benchmark",
]


def _iter_test_files_under(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    tests: List[Path] = []
    for pattern in ["test_*.py", "*_test.py"]:
        tests.extend(root.rglob(pattern))
    return tests


def find_python_tests(repo_root: Path) -> List[Path]:
    """Find deterministic Python test files.

    Note: We intentionally avoid scanning the entire repository (e.g. `src/**/tests`)
    because many component test suites require additional per-service configuration
    and can break epic automation runs.
    """

    tests: List[Path] = []

    # Repo-root smoke tests (non-recursive)
    for pattern in ["test_*.py", "*_test.py"]:
        tests.extend(repo_root.glob(pattern))

    scope = os.getenv("WAOOAW_TEST_SCOPE", "standard").strip().lower()
    if scope not in {"smoke", "standard"}:
        scope = "standard"

    selected_roots = (
        DEFAULT_TEST_ROOTS_SMOKE if scope == "smoke" else DEFAULT_TEST_ROOTS_STANDARD
    )

    # Selected stable test roots
    for rel_root in selected_roots:
        tests.extend(_iter_test_files_under(repo_root / rel_root))

    # Optional extra paths (colon-separated), e.g. "src/some/module/tests:other_tests"
    extra_paths = os.getenv("WAOOAW_EXTRA_TEST_PATHS", "").strip()
    if extra_paths:
        for raw in extra_paths.split(":"):
            path = (repo_root / raw.strip()).resolve()
            try:
                path.relative_to(repo_root)
            except ValueError:
                # Skip paths outside the repo root.
                continue
            tests.extend(_iter_test_files_under(path))

    exclude_substrings = list(DEFAULT_EXCLUDE_SUBSTRINGS)
    extra_exclude_substrings = os.getenv("WAOOAW_TEST_EXCLUDE_SUBSTRINGS", "").strip()
    if extra_exclude_substrings:
        exclude_substrings.extend([s.strip() for s in extra_exclude_substrings.split(":") if s.strip()])

    exclude_filename_tokens = list(DEFAULT_EXCLUDE_FILENAME_TOKENS)
    extra_exclude_tokens = os.getenv("WAOOAW_TEST_EXCLUDE_FILENAME_TOKENS", "").strip()
    if extra_exclude_tokens:
        exclude_filename_tokens.extend([s.strip() for s in extra_exclude_tokens.split(":") if s.strip()])

    # Exclude old agent backups and de-dup while preserving order
    seen: set[str] = set()
    ordered: List[Path] = []
    for test_path in tests:
        as_posix = test_path.as_posix()
        if "_old.py" in as_posix:
            continue
        if as_posix in seen:
            continue
        seen.add(as_posix)
        ordered.append(test_path)

    # Apply exclusion filters last (keeps deterministic ordering)
    filtered: List[Path] = []
    for test_path in ordered:
        as_posix = test_path.as_posix()
        lower_name = test_path.name.lower()

        if any(s in as_posix for s in exclude_substrings):
            continue
        if any(tok in lower_name for tok in exclude_filename_tokens):
            continue
        filtered.append(test_path)

    return filtered


def run_pytest(test_files: List[Path]) -> Tuple[bool, Dict, str]:
    """Run pytest and parse results.
    
    Returns:
        (success, summary_dict, output)
    """
    if not test_files:
        return True, {"status": "no_tests"}, "No Python tests found"
    
    try:
        mode = os.getenv("WAOOAW_TEST_EXECUTION_MODE", "docker").strip().lower()
        if mode == "docker" and shutil.which("docker"):
            result = _run_pytest_in_docker(test_files)
        else:
            cmd = _build_pytest_cmd(test_files, enforce_cov=_enforce_coverage())

            print("[Test Agent] Executing pytest command:")
            print("[Test Agent] " + " ".join(cmd))

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        output = result.stdout + "\n" + result.stderr
        
        # Parse summary from output
        summary = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0,
            "coverage_total": None,
        }

        # Pytest exit code 5 commonly means "no tests collected".
        # This is usually a selection/scoping issue, so surface it explicitly.
        if result.returncode == 5 and ("collected 0 items" in output.lower()):
            summary["status"] = "no_tests_collected"
        
        # Parse counts from any output line (handles collection errors / no-summary cases)
        count_patterns = {
            "passed": re.compile(r"(?P<count>\d+)\s+passed", re.IGNORECASE),
            "failed": re.compile(r"(?P<count>\d+)\s+failed", re.IGNORECASE),
            "skipped": re.compile(r"(?P<count>\d+)\s+skipped", re.IGNORECASE),
            "errors": re.compile(r"(?P<count>\d+)\s+errors?", re.IGNORECASE),
        }

        for line in output.split("\n"):
            for key, pattern in count_patterns.items():
                match = pattern.search(line)
                if match:
                    summary[key] = int(match.group("count"))

            if line.startswith("TOTAL") and "%" in line:
                # e.g. "TOTAL 123 4 97%"
                parts = line.split()
                for part in reversed(parts):
                    if part.endswith("%"):
                        try:
                            summary["coverage_total"] = float(part.rstrip("%"))
                        except ValueError:
                            summary["coverage_total"] = None
                        break
        
        summary["total"] = summary["passed"] + summary["failed"] + summary["skipped"] + summary["errors"]
        summary["returncode"] = result.returncode
        success = result.returncode == 0
        
        return success, summary, output
        
    except subprocess.TimeoutExpired:
        return False, {"status": "timeout"}, "Tests timed out after 10 minutes"
    except FileNotFoundError:
        return False, {"status": "not_installed"}, "pytest not installed"
    except Exception as e:
        return False, {"status": "error"}, f"Test execution failed: {e}"


def _enforce_coverage() -> bool:
    enforce_cov_raw = os.getenv("WAOOAW_ENFORCE_COVERAGE", "").strip().lower()
    return enforce_cov_raw in {"1", "true", "yes", "on"}


def _build_pytest_cmd(test_files: List[Path], *, enforce_cov: bool) -> List[str]:
    cmd: List[str] = [
        sys.executable,
        "-m",
        "pytest",
        "-v",
        "--tb=short",
        "--maxfail=5",
        *[str(p) for p in test_files],
    ]

    # Optional coverage: set WAOOAW_COVERAGE=1 and optionally WAOOAW_COVERAGE_MIN
    if os.getenv("WAOOAW_COVERAGE", "").strip().lower() in {"1", "true", "yes", "on"}:
        target = os.getenv("WAOOAW_COVERAGE_TARGET", "src").strip() or "src"
        cmd.extend([f"--cov={target}", "--cov-report=term-missing"])

        cov_min_raw = os.getenv("WAOOAW_COVERAGE_MIN", "").strip()
        if cov_min_raw:
            try:
                cov_min = int(cov_min_raw)
            except ValueError:
                cov_min = 0
            if enforce_cov and cov_min > 0:
                cmd.append(f"--cov-fail-under={cov_min}")

    # Default behavior: do NOT let coverage thresholds block the epic when a subset ran.
    # This neutralizes per-service pytest.ini settings like `--cov-fail-under=76`.
    if not enforce_cov:
        cmd.append("--cov-fail-under=0")

    return cmd


def _run_pytest_in_docker(test_files: List[Path]) -> subprocess.CompletedProcess[str]:
    repo_root = Path.cwd().resolve()
    dockerfile = repo_root / "tests" / "Dockerfile.test"
    image = os.getenv("WAOOAW_DOCKER_TEST_IMAGE", "waooaw-test-runner:py311").strip()

    if not dockerfile.exists():
        raise FileNotFoundError(f"Missing {dockerfile.as_posix()}")

    # Build (cached) test runner image.
    subprocess.run(
        [
            "docker",
            "build",
            "-f",
            dockerfile.as_posix(),
            "-t",
            image,
            repo_root.as_posix(),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    enforce_cov = _enforce_coverage()

    pytest_cmd = _build_pytest_cmd(test_files, enforce_cov=enforce_cov)
    # Replace the leading interpreter invocation; inside the container we always call `python`.
    pytest_cmd[0:1] = ["python"]

    cmd: List[str] = [
        "docker",
        "run",
        "--rm",
        "--network",
        "host",
        "-v",
        f"{repo_root.as_posix()}:/repo",
        "-w",
        "/repo",
        # Pass through test/runtime env vars
        "-e",
        f"TEST_MODE={os.getenv('TEST_MODE', '')}",
        "-e",
        f"TEST_DATABASE_URL={os.getenv('TEST_DATABASE_URL', '')}",
        "-e",
        f"TEST_REDIS_URL={os.getenv('TEST_REDIS_URL', '')}",
        "-e",
        f"WAOOAW_TEST_SCOPE={os.getenv('WAOOAW_TEST_SCOPE', '')}",
        "-e",
        f"WAOOAW_COVERAGE={os.getenv('WAOOAW_COVERAGE', '')}",
        "-e",
        f"WAOOAW_COVERAGE_TARGET={os.getenv('WAOOAW_COVERAGE_TARGET', '')}",
        "-e",
        f"WAOOAW_COVERAGE_MIN={os.getenv('WAOOAW_COVERAGE_MIN', '')}",
        "-e",
        f"WAOOAW_ENFORCE_COVERAGE={os.getenv('WAOOAW_ENFORCE_COVERAGE', '')}",
        "-e",
        "PYTHONPATH=src/CP/BackEnd",
        image,
        *pytest_cmd,
    ]

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )


def format_test_summary(success: bool, summary: Dict, output: str) -> str:
    """Format test results as markdown."""
    
    status_emoji = "✅" if success else "❌"
    title = f"## {status_emoji} Test Agent Results\n\n"
    
    if summary.get("status") == "no_tests":
        return title + "No tests found in repository.\n"

    if summary.get("status") == "no_tests_collected":
        # Keep this as a failure, but make the root cause obvious.
        result = title
        result += "**Status**: ❌ Pytest collected 0 tests (selection/scope issue)\n\n"
        result += "### ❌ Action Required\n\n"
        result += "Pytest exited with code 5 (no tests collected). This usually means the Test Agent selected paths with no runnable tests, or collection failed before discovery.\n\n"
        result += "### Failure Output (tail)\n\n"
        result += "```\n"
        lines = [l for l in output.split("\n") if l is not None]
        tail = lines[-120:] if len(lines) > 120 else lines
        result += "\n".join(tail).strip() + "\n"
        result += "```\n"
        return result
    
    if summary.get("status") == "not_installed":
        return title + "⚠️ pytest not installed. Install with: `pip install pytest`\n"
    
    if summary.get("status") == "timeout":
        return title + "⏱️ Tests timed out after 10 minutes.\n"
    
    if summary.get("status") == "error":
        return title + f"❌ Error: {output[:500]}\n"
    
    # Format normal results
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    skipped = summary.get("skipped", 0)
    total = summary.get("total", 0)
    
    result = title
    scope = os.getenv("WAOOAW_TEST_SCOPE", "standard")
    mode = os.getenv("WAOOAW_TEST_EXECUTION_MODE", "docker")
    coverage_gate = "ENFORCED" if _enforce_coverage() else "RELAXED (subset-friendly)"
    result += f"**Execution**: {mode}\\n"
    result += f"**Scope**: {scope}\\n"
    result += f"**Coverage gate**: {coverage_gate}\\n\\n"
    result += f"**Status**: {'✅ All tests passed' if success else '❌ Some tests failed'}\n\n"
    result += f"**Results**:\n"
    result += f"- ✅ Passed: {passed}\n"
    result += f"- ❌ Failed: {failed}\n"
    result += f"- ⏭️ Skipped: {skipped}\n"
    result += f"- 📊 Total: {total}\n\n"

    cov_total = summary.get("coverage_total")
    if cov_total is not None:
        result += f"**Coverage (TOTAL)**: {cov_total:.1f}%\n\n"
    
    if not success:
        returncode = summary.get("returncode")
        if returncode is not None:
            result += f"**Pytest exit code**: {returncode}\n\n"

        result += "### Failure Output (tail)\n\n"
        result += "```\n"
        lines = [l for l in output.split("\n") if l is not None]
        tail = lines[-120:] if len(lines) > 120 else lines
        result += "\n".join(tail).strip() + "\n"
        result += "```\n\n"
    
    # Next steps
    if success:
        result += "### ✅ Next Steps\n\n"
        result += "All tests passed! Deploy Agent will create a PR to merge this epic.\n"
    else:
        result += "### ❌ Action Required\n\n"
        result += "Tests failed. Please fix failing tests before deployment.\n"
        result += "Epic will be labeled with `needs-fix`.\n"
    
    return result


def post_comment_to_epic(epic_number: str, comment: str) -> bool:
    """Post comment to epic using GitHub CLI."""
    try:
        subprocess.run(
            ["gh", "issue", "comment", epic_number, "--body", comment],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to post comment: {e.stderr}")
        return False


def add_label_to_epic(epic_number: str, label: str) -> bool:
    """Add label to epic using GitHub CLI."""
    try:
        subprocess.run(
            ["gh", "issue", "edit", epic_number, "--add-label", label],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to add label: {e.stderr}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic Test Agent for WAOOAW")
    parser.add_argument("--epic-number", required=True, help="Epic issue number")
    parser.add_argument("--epic-branch", required=True, help="Epic branch name")
    args = parser.parse_args()
    
    epic_number = str(args.epic_number)
    epic_branch = str(args.epic_branch)
    
    print(f"[Test Agent] Running tests for Epic #{epic_number}")
    print(f"[Test Agent] Branch: {epic_branch}")
    
    # Find test files
    repo_root = Path.cwd()
    test_files = find_python_tests(repo_root)
    
    print(f"[Test Agent] Found {len(test_files)} Python test files")
    for path in test_files:
        try:
            rel = path.relative_to(repo_root)
            print(f"[Test Agent] - {rel.as_posix()}")
        except ValueError:
            print(f"[Test Agent] - {path.as_posix()}")
    
    # Run tests
    success, summary, output = run_pytest(test_files)
    
    # Format summary
    comment = format_test_summary(success, summary, output)
    
    print("[Test Agent] Test Results:")
    print(comment)
    
    # Post to GitHub
    print(f"[Test Agent] Posting results to Epic #{epic_number}...")
    if not post_comment_to_epic(epic_number, comment):
        print("[ERROR] Failed to post results to GitHub")
        sys.exit(1)
    
    # Add label if failed
    if not success:
        print(f"[Test Agent] Adding 'needs-fix' label to Epic #{epic_number}")
        add_label_to_epic(epic_number, "needs-fix")
        print("[Test Agent] ❌ Tests failed")
        sys.exit(1)
    
    print("[Test Agent] ✅ All tests passed!")


if __name__ == "__main__":
    main()
