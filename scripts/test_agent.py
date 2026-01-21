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
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def find_python_tests(base_path: Path) -> List[Path]:
    """Find Python test files."""
    tests = []
    for pattern in ["test_*.py", "*_test.py"]:
        tests.extend(base_path.rglob(pattern))
    # Exclude old agent backups
    return [t for t in tests if "_old.py" not in str(t)]


def run_pytest(test_files: List[Path]) -> Tuple[bool, Dict, str]:
    """Run pytest and parse results.
    
    Returns:
        (success, summary_dict, output)
    """
    if not test_files:
        return True, {"status": "no_tests"}, "No Python tests found"
    
    try:
        result = subprocess.run(
            ["pytest", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        output = result.stdout + "\n" + result.stderr
        
        # Parse summary from output
        summary = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "total": 0
        }
        
        # Look for pytest summary line
        for line in output.split("\n"):
            if " passed" in line or " failed" in line:
                # e.g., "5 passed, 2 failed in 1.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if i > 0 and parts[i-1].isdigit():
                        count = int(parts[i-1])
                        if "passed" in part:
                            summary["passed"] = count
                        elif "failed" in part:
                            summary["failed"] = count
                        elif "skipped" in part:
                            summary["skipped"] = count
                        elif "error" in part:
                            summary["errors"] = count
        
        summary["total"] = summary["passed"] + summary["failed"] + summary["skipped"] + summary["errors"]
        success = result.returncode == 0
        
        return success, summary, output
        
    except subprocess.TimeoutExpired:
        return False, {"status": "timeout"}, "Tests timed out after 10 minutes"
    except FileNotFoundError:
        return False, {"status": "not_installed"}, "pytest not installed"
    except Exception as e:
        return False, {"status": "error"}, f"Test execution failed: {e}"


def format_test_summary(success: bool, summary: Dict, output: str) -> str:
    """Format test results as markdown."""
    
    status_emoji = "✅" if success else "❌"
    title = f"## {status_emoji} Test Agent Results\n\n"
    
    if summary.get("status") == "no_tests":
        return title + "No tests found in repository.\n"
    
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
    result += f"**Status**: {'✅ All tests passed' if success else '❌ Some tests failed'}\n\n"
    result += f"**Results**:\n"
    result += f"- ✅ Passed: {passed}\n"
    result += f"- ❌ Failed: {failed}\n"
    result += f"- ⏭️ Skipped: {skipped}\n"
    result += f"- 📊 Total: {total}\n\n"
    
    if not success:
        result += "### Failed Tests\n\n"
        result += "```\n"
        # Extract failure details (first 1000 chars)
        failure_section = False
        failure_lines = []
        for line in output.split("\n"):
            if "FAILED" in line or "ERROR" in line:
                failure_section = True
            if failure_section:
                failure_lines.append(line)
                if len("\n".join(failure_lines)) > 1000:
                    break
        result += "\n".join(failure_lines[:50]) + "\n"
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
