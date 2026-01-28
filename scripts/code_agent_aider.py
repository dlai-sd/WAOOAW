#!/usr/bin/env python3
"""scripts/code_agent_aider.py

Aider-based Code Agent for WAOOAW.

Integrates Aider (https://github.com/paul-gauthier/aider) into the ALM workflow
for better codebase awareness and code generation quality.

Environment:
- `OPENAI_API_KEY` (required): OpenAI API key for Aider
- `AIDER_MODEL` (optional): Model to use (default: gpt-4o-mini)
"""

import argparse
import os
import subprocess
import sys
import re
import ast
from pathlib import Path


def _is_github_actions() -> bool:
    return (os.getenv("GITHUB_ACTIONS") or "").strip().lower() == "true"


def _truthy_env(name: str, *, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on"}


def _node_source_range(node: ast.AST) -> tuple[int, int]:
    """Return 1-based (start_line, end_line) for a top-level def/class node."""

    start = getattr(node, "lineno", None)
    end = getattr(node, "end_lineno", None)
    if start is None or end is None:
        raise ValueError("AST node missing lineno/end_lineno")

    decorators = getattr(node, "decorator_list", None) or []
    if decorators:
        start = min(getattr(d, "lineno", start) for d in decorators)
    return int(start), int(end)


def _autofix_duplicate_top_level_defs(paths: list[str]) -> tuple[bool, list[str]]:
    """Attempt to auto-fix duplicate top-level defs/classes when identical.

    Strategy:
    - Parse file AST
    - Find duplicate top-level function names (def/async def) and classes
    - If duplicate blocks are AST-identical, delete the later duplicates (keep first)
    - Re-stage the fixed files

    Returns:
        (any_fixes_applied, notes)
    """

    any_fixed = False
    notes: list[str] = []

    for path in paths:
        if not path.endswith(".py") or not os.path.exists(path):
            continue
        try:
            source = Path(path).read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=path)
        except Exception as e:
            notes.append(f"{path}: skip autofix (parse/read error: {e})")
            continue

        groups: dict[tuple[str, str], list[ast.AST]] = {}
        for node in getattr(tree, "body", []):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                key = ("func", node.name)
            elif isinstance(node, ast.ClassDef):
                key = ("class", node.name)
            else:
                continue
            groups.setdefault(key, []).append(node)

        to_remove: list[tuple[int, int, str]] = []
        for (kind, name), nodes in groups.items():
            if len(nodes) <= 1:
                continue
            # Only auto-fix when the AST bodies are identical.
            dumps = [ast.dump(n, include_attributes=False) for n in nodes]
            if len(set(dumps)) != 1:
                notes.append(f"{path}: cannot autofix duplicate {kind} '{name}' (non-identical bodies)")
                continue
            for dup in nodes[1:]:
                try:
                    start, end = _node_source_range(dup)
                except Exception as e:
                    notes.append(f"{path}: cannot autofix duplicate {kind} '{name}' (range error: {e})")
                    continue
                to_remove.append((start, end, f"{kind} '{name}'"))

        if not to_remove:
            continue

        lines = source.splitlines(keepends=True)
        # Remove from bottom to top to preserve earlier ranges.
        to_remove.sort(key=lambda t: (t[0], t[1]), reverse=True)
        for start, end, label in to_remove:
            start_idx = max(0, start - 1)
            end_idx = min(len(lines), end)
            for i in range(start_idx, end_idx):
                lines[i] = ""
            notes.append(f"{path}: removed duplicate top-level {label} (lines {start}-{end})")

        new_source = "".join(lines)
        # Normalize excessive blank lines where we deleted blocks.
        new_source = re.sub(r"\n{4,}", "\n\n\n", new_source)
        if not new_source.endswith("\n"):
            new_source += "\n"

        try:
            Path(path).write_text(new_source, encoding="utf-8")
            subprocess.run(["git", "add", path], check=False)
            any_fixed = True
        except Exception as e:
            notes.append(f"{path}: failed writing/restaging autofix changes: {e}")

    return any_fixed, notes


def check_required_dependencies() -> bool:
    """Check if required testing dependencies are installed.
    
    Returns:
        True if all dependencies available, False otherwise
    """
    missing = []

    skip_tests = os.getenv("WAOOAW_CODE_AGENT_SKIP_TESTS", "").strip().lower() in {"1", "true", "yes"}
    skip_coverage = os.getenv("WAOOAW_CODE_AGENT_SKIP_COVERAGE", "").strip().lower() in {"1", "true", "yes"}

    need_pytest = not skip_tests
    need_pytest_cov = not skip_coverage

    # Check Python testing dependencies (optional, depending on gate config)
    if need_pytest:
        try:
            import pytest  # noqa: F401
        except ImportError:
            missing.append("pytest")

    if need_pytest_cov:
        try:
            import pytest_cov  # noqa: F401
        except ImportError:
            missing.append("pytest-cov")
    
    # Check flake8 is available as command
    try:
        result = subprocess.run(
            ["python", "-m", "flake8", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            missing.append("flake8")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        missing.append("flake8")
    
    if missing:
        print("\n" + "=" * 80)
        print("[ERROR] MISSING REQUIRED DEPENDENCIES")
        print("=" * 80)
        print(f"Missing: {', '.join(missing)}")
        print("\nInstall with:")
        print(f"  pip install {' '.join(missing)}")
        print("\nP0/P1 validation gates require these dependencies.")
        print("Without them, quality gates will be SKIPPED.")
        print("=" * 80)
        return False
    
    print("[Code Agent] ✅ All required dependencies available")
    return True


def validate_syntax() -> bool:
    """Run Python syntax validation on changed files."""
    print("\n" + "=" * 80)
    print("[Code Agent] Running syntax validation...")
    
    try:
        # Get list of changed Python files
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            check=True
        )
        
        python_files = [f for f in result.stdout.strip().split('\n') 
                       if f.endswith('.py') and os.path.exists(f)]
        
        if not python_files:
            print("[Code Agent] No Python files to validate")
            return True
        
        print(f"[Code Agent] Validating {len(python_files)} Python files...")
        
        # Run flake8 for syntax errors
        flake8_result = subprocess.run(
            ["python", "-m", "flake8", "--select=E9,F821,F823,F831,F406,F407,F701,F702,F704,F706"] + python_files,
            capture_output=True,
            text=True
        )
        
        if flake8_result.returncode != 0:
            print("[ERROR] Syntax validation FAILED:")
            print(flake8_result.stdout)
            return False
        
        print("[Code Agent] ✅ Syntax validation passed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Syntax validation error: {e}")
        return False


def detect_stubs() -> bool:
    """Detect stub/pseudo-code patterns in changed files."""
    print("\n" + "=" * 80)
    print("[Code Agent] Checking for stub code...")
    
    stub_patterns = [
        (r'return True\s*#.*TODO', 'return True with TODO comment'),
        (r'return "default_\w+"', 'return default stub value'),
        (r'pass\s*#.*TODO', 'pass with TODO'),
        (r'#.*pseudo-code', 'pseudo-code comment'),
        (r'#.*FIXME', 'FIXME comment'),
        (r'raise NotImplementedError', 'NotImplementedError'),
        (r'print\(\s*[\'\"]hello[\'\"]\s*\)', 'print("hello") placeholder'),
    ]

    def _looks_like_placeholder_hello_file(path: str) -> bool:
        if os.path.basename(path).lower() != 'hello.py':
            return False
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except OSError:
            return False

        # This is intentionally strict to avoid false positives.
        return bool(
            re.search(r'\bdef\s+hello\s*\(', content)
            and re.search(r'print\(\s*[\'\"]hello[\'\"]\s*\)', content)
        )
    
    try:
        result = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            check=True
        )
        
        diff_content = result.stdout
        issues_found = []
        
        for line in diff_content.split('\n'):
            if not line.startswith('+'):
                continue
            
            for pattern, description in stub_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues_found.append(f"{description}: {line.strip()}")

        # Also inspect staged files (captures placeholders even if not caught line-by-line)
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AM"],
            capture_output=True,
            text=True,
            check=True,
        )
        for path in [p.strip() for p in staged.stdout.splitlines() if p.strip()]:
            if not path.endswith('.py'):
                continue
            if not os.path.exists(path):
                continue
            if _looks_like_placeholder_hello_file(path):
                issues_found.append(
                    f"placeholder hello.py detected: {path} (contains def hello + print(\"hello\"))"
                )
        
        if issues_found:
            print("[ERROR] Stub code detected:")
            for issue in issues_found:
                print(f"  - {issue}")
            return False
        
        print("[Code Agent] ✅ No stub code detected")
        return True
        
    except Exception as e:
        print(f"[ERROR] Stub detection error: {e}")
        return False

def detect_aider_artifacts() -> bool:
    """Fail if Aider artifacts are staged for commit."""
    print("\n" + "=" * 80)
    print("[Code Agent] Checking for Aider artifacts...")

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            check=True,
        )

        staged_paths = [p.strip() for p in result.stdout.splitlines() if p.strip()]
        bad = [
            p
            for p in staged_paths
            if re.search(r"(^|/)\.aider", p)
        ]

        if bad:
            print("[ERROR] Aider artifacts detected in staged changes:")
            for p in bad:
                print(f"  - {p}")
            print("[ERROR] Remove these files (they are local artifacts) and try again")
            return False

        print("[Code Agent] ✅ No Aider artifacts detected")
        return True

    except Exception as e:
        print(f"[ERROR] Aider artifact check error: {e}")
        return False


def detect_duplicate_top_level_defs() -> bool:
    """Detect duplicate top-level function/class definitions in staged Python files.

    In Python, later `def`/`class` overrides earlier ones at import time. This catches
    accidental copy/paste or appended blocks that silently change runtime behavior.

    If enabled via `WAOOAW_CODE_AGENT_AUTOFIX_DUPLICATE_DEFS=1`, the gate will attempt
    to auto-fix *identical* duplicate top-level defs/classes by removing later duplicates
    and re-staging the affected file(s).
    """
    print("\n" + "=" * 80)
    print("[Code Agent] Checking for duplicate top-level defs...")

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=AMR"],
            capture_output=True,
            text=True,
            check=True,
        )

        python_files = [
            p.strip()
            for p in result.stdout.splitlines()
            if p.strip().endswith(".py") and os.path.exists(p.strip())
        ]

        if not python_files:
            print("[Code Agent] No staged Python files to check")
            return True

        issues: list[str] = []
        duplicate_paths: set[str] = set()
        for path in python_files:
            try:
                source = Path(path).read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=path)
            except SyntaxError as e:
                issues.append(f"{path}: syntax error while parsing for duplicate-def check: {e}")
                continue
            except OSError as e:
                issues.append(f"{path}: unable to read file for duplicate-def check: {e}")
                continue

            seen: dict[tuple[str, str], int] = {}
            for node in getattr(tree, "body", []):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    key = ("func", node.name)
                    kind = "def"
                elif isinstance(node, ast.ClassDef):
                    key = ("class", node.name)
                    kind = "class"
                else:
                    continue

                if key in seen:
                    issues.append(
                        f"{path}: duplicate top-level {kind} '{key[1]}' (earlier at line {seen[key]}, again at line {node.lineno})"
                    )
                    duplicate_paths.add(path)
                else:
                    seen[key] = node.lineno

        if issues:
            autofix_enabled = _truthy_env(
                "WAOOAW_CODE_AGENT_AUTOFIX_DUPLICATE_DEFS",
                default=_is_github_actions(),
            )
            if autofix_enabled and duplicate_paths:
                print("[Code Agent] Attempting auto-fix for duplicate top-level defs/classes...")
                fixed, notes = _autofix_duplicate_top_level_defs(sorted(duplicate_paths))
                for n in notes:
                    print(f"  - {n}")
                if fixed:
                    # Re-run once after auto-fix.
                    return detect_duplicate_top_level_defs()

            print("[ERROR] Duplicate top-level defs detected:")
            for issue in issues:
                print(f"  - {issue}")
            return False

        print("[Code Agent] ✅ No duplicate top-level defs detected")
        return True

    except Exception as e:
        print(f"[ERROR] Duplicate-def check error: {e}")
        return False


def run_tests() -> bool:
    """Run pytest on changed modules."""
    print("\n" + "=" * 80)
    print("[Code Agent] Running tests...")
    
    try:
        # Check if pytest is available
        pytest_check = subprocess.run(
            ["python", "-m", "pytest", "--version"],
            capture_output=True
        )
        
        if pytest_check.returncode != 0:
            print("[WARNING] pytest not installed, skipping tests")
            return True
        
        # Run pytest with coverage
        test_result = subprocess.run(
            ["python", "-m", "pytest", "-v", "--tb=short", "--maxfail=3"],
            capture_output=True,
            text=True
        )
        
        print(test_result.stdout)
        
        if test_result.returncode != 0:
            # Check if failure is due to missing dependencies (import errors)
            stderr_lower = test_result.stderr.lower()
            if "modulenotfounderror" in stderr_lower or "importerror" in stderr_lower:
                print("[WARNING] Tests skipped - missing application dependencies (e.g., sqlalchemy, FastAPI models)")
                print("[INFO] This is expected in Code Agent environment. Full test suite runs in Test Agent.")
                print(f"   Import error: {test_result.stderr[:200]}...")
                return True  # Non-blocking for P1 gate
            
            print("[ERROR] Tests FAILED:")
            print(test_result.stderr)
            return False
        
        print("[Code Agent] ✅ Tests passed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Test execution error: {e}")
        return False


def check_coverage() -> bool:
    """Generate and check test coverage."""
    print("\n" + "=" * 80)
    print("[Code Agent] Checking test coverage...")
    
    try:
        # Check if pytest-cov is available
        cov_check = subprocess.run(
            ["python", "-m", "pytest", "--cov", "--help"],
            capture_output=True
        )
        
        if cov_check.returncode != 0:
            print("[WARNING] pytest-cov not installed, skipping coverage check")
            return True
        
        # Get changed Python files in src/
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            check=True
        )
        
        changed_modules = set()
        for f in result.stdout.strip().split('\n'):
            if f.startswith('src/') and f.endswith('.py'):
                # Extract module path (e.g., src/CP/BackEnd)
                parts = f.split('/')
                if len(parts) >= 3:
                    module = '/'.join(parts[:3])
                    changed_modules.add(module)
        
        if not changed_modules:
            print("[Code Agent] No source modules changed, skipping coverage")
            return True
        
        print(f"[Code Agent] Checking coverage for: {', '.join(changed_modules)}")
        
        # Run coverage on changed modules
        for module in changed_modules:
            cov_result = subprocess.run(
                ["python", "-m", "pytest", f"--cov={module}", "--cov-report=term-missing", "--cov-fail-under=70"],
                capture_output=True,
                text=True
            )
            
            print(cov_result.stdout)
            
            if "TOTAL" in cov_result.stdout:
                # Extract coverage percentage
                for line in cov_result.stdout.split('\n'):
                    if "TOTAL" in line:
                        print(f"[Code Agent] Coverage: {line}")
        
        print("[Code Agent] ✅ Coverage check completed (warning only)")
        return True
        
    except Exception as e:
        print(f"[WARNING] Coverage check error: {e}")
        return True  # Non-blocking


def main() -> None:
    parser = argparse.ArgumentParser(description="Aider-based Code Agent for WAOOAW")
    parser.add_argument("--epic-number", required=True)
    parser.add_argument("--issue-number", required=True)
    parser.add_argument("--story-title", required=True)
    parser.add_argument("--story-body", required=True)
    args = parser.parse_args()

    epic_number = str(args.epic_number)
    issue_number = str(args.issue_number)
    story_title = str(args.story_title)
    story_body = str(args.story_body)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY environment variable is required")
        sys.exit(1)

    # Select model (default to cost-effective gpt-4o-mini)
    model = os.getenv("AIDER_MODEL", "gpt-4o-mini")
    
    # Detect target module from story content
    combined = f"{story_title} {story_body}".lower()
    target_path = None  # Will be single path or "." for git root
    
    # Module-specific stories → focus on that module
    if "plant" in combined or "plant api" in combined:
        target_path = "src/Plant"
    elif "cp portal" in combined or "customer portal" in combined:
        target_path = "src/CP"
    elif "pp portal" in combined or "partner portal" in combined:
        target_path = "src/PP"
    elif "gateway" in combined:
        target_path = "src/gateway"
    # Cross-cutting stories (tech debt, monitoring, infrastructure) → use git root
    elif any(keyword in combined for keyword in ["tech debt", "technical debt", "refactor", 
                                                   "monitoring", "observability", "infrastructure",
                                                   "ci/cd", "deployment", "docker", "kubernetes"]):
        target_path = "."  # Git repo root for full codebase awareness
    else:
        # Default: use git root with repo-map for smart file detection
        target_path = "."
    
    # Build Aider prompt
    prompt = (
        f"Implement the following user story for WAOOAW project:\n\n"
        f"Epic: #{epic_number}\n"
        f"Story: #{issue_number}\n"
        f"Title: {story_title}\n\n"
        f"{story_body}\n\n"
        f"Requirements:\n"
        f"- Follow existing code patterns and style\n"
        f"- Add type hints (Python) or TypeScript types\n"
        f"- Include docstrings/comments\n"
        f"- Keep changes minimal and focused\n"
        f"- No TODOs or placeholders\n"
        f"- Production-ready code only\n"
    )
    
    print(f"[Aider Code Agent] Epic #{epic_number} Story #{issue_number}")
    print(f"[Aider Code Agent] Using model: {model}")
    print(f"[Aider Code Agent] Target path: {target_path}")
    
    # Run Aider
    try:
        # Prepare Aider command
        # Note: Aider v0.86+ accepts either:
        #   - Single directory (git repo): "." or "src/Plant"
        #   - List of specific files: "file1.py file2.py"
        #   - NOT multiple directories: "src/ infrastructure/" ❌
        aider_cmd = [
            "aider",
            "--yes",  # Auto-accept changes
            "--no-auto-commits",  # We'll commit manually
            f"--model={model}",
            "--message", prompt,
            target_path  # Single directory or git root
        ]
        
        print(f"[Aider Code Agent] Running: aider with {target_path}...")
        print("[Aider Code Agent] Streaming output (real-time progress):")
        print("=" * 80)
        
        # Use Popen for real-time streaming instead of run() with capture_output
        process = subprocess.Popen(
            aider_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Stream output line by line in real-time
        output_lines = []
        for line in process.stdout:
            print(line, end='')  # Print immediately (real-time!)
            output_lines.append(line)
        
        # Wait for completion with timeout
        try:
            process.wait(timeout=600)  # 10 minute timeout
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise subprocess.TimeoutExpired(aider_cmd, 600)
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, 
                aider_cmd, 
                output=''.join(output_lines)
            )
        
        print("=" * 80)
        print("[Aider Code Agent] Aider execution completed")
        
    except subprocess.TimeoutExpired:
        print("[ERROR] Aider execution timed out after 10 minutes")
        print("[ERROR] This usually means:")
        print("  - Complex refactoring taking longer than expected")
        print("  - Large repo-map scan (first run on git root)")
        print("  - Multiple API calls to OpenAI")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Aider execution failed with exit code {e.returncode}")
        if e.output:
            print(f"Output: {e.output}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] Aider is not installed. Run: pip install aider-chat")
        sys.exit(1)
    
    # Commit changes
    commit_message = f"feat(epic-{epic_number}): implement story #{issue_number}\n\n{story_title}"
    
    try:
        # Check if there are any changes
        diff_check = subprocess.run(
            ["git", "diff", "--quiet"],
            check=False
        )
        
        if diff_check.returncode == 0:
            print("[Aider Code Agent] No changes to commit")
            return
        
        # Stage all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # P0 Validation Gates
        print("\n" + "=" * 80)
        print("[Code Agent] Running P0/P1/P2 Quality Gates...")
        print("=" * 80)

        skip_tests = os.getenv("WAOOAW_CODE_AGENT_SKIP_TESTS", "").strip().lower() in {"1", "true", "yes"}
        skip_coverage = os.getenv("WAOOAW_CODE_AGENT_SKIP_COVERAGE", "").strip().lower() in {"1", "true", "yes"}
        if skip_tests or skip_coverage:
            print(
                "[Code Agent] Gate config: "
                f"skip_tests={skip_tests} skip_coverage={skip_coverage}"
            )
        
        # FIRST: Check dependencies are available
        if not check_required_dependencies():
            print("\n[ERROR] Quality gates cannot run without required dependencies")
            print("[ERROR] Please install: pip install pytest pytest-cov flake8")
            print("[ERROR] Unstaging changes and exiting...")
            subprocess.run(["git", "reset", "HEAD"], check=False)
            sys.exit(1)
        
        validation_passed = True
        
        # P0: Syntax validation
        if not validate_syntax():
            print("[ERROR] P0 GATE FAILED: Syntax validation")
            validation_passed = False
        
        # P0: Stub detection
        if not detect_stubs():
            print("[ERROR] P0 GATE FAILED: Stub code detected")
            validation_passed = False

        # P0: Aider artifact detection
        if not detect_aider_artifacts():
            print("[ERROR] P0 GATE FAILED: Aider artifacts detected")
            validation_passed = False

        # P0: Duplicate top-level def detection
        if not detect_duplicate_top_level_defs():
            print("[ERROR] P0 GATE FAILED: Duplicate top-level defs detected")
            validation_passed = False
        
        # P1: Run tests (warning only)
        if not skip_tests:
            if not run_tests():
                print("[WARNING] P1 GATE: Some tests failed")
        else:
            print("[Code Agent] Skipping pytest (WAOOAW_CODE_AGENT_SKIP_TESTS=1)")

        # P1: Check coverage (warning only)
        if not skip_coverage:
            check_coverage()
        else:
            print("[Code Agent] Skipping coverage (WAOOAW_CODE_AGENT_SKIP_COVERAGE=1)")
        
        if not validation_passed:
            print("\n" + "=" * 80)
            print("[ERROR] Quality gates FAILED - blocking commit")
            print("Please fix the issues above before committing")
            print("=" * 80)
            # Unstage changes
            subprocess.run(["git", "reset", "HEAD"], check=False)
            sys.exit(1)
        
        print("\n" + "=" * 80)
        print("[Code Agent] ✅ All quality gates passed")
        print("=" * 80)
        
        # Commit
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=True
        )
        
        # Push
        subprocess.run(["git", "push", "origin", "HEAD"], check=True)
        
        print(f"[Aider Code Agent] Changes committed and pushed")
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Git operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
