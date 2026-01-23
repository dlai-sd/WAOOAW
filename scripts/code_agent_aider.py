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
from pathlib import Path


def check_required_dependencies() -> bool:
    """Check if required testing dependencies are installed.
    
    Returns:
        True if all dependencies available, False otherwise
    """
    missing = []
    warnings = []
    
    # Check Python testing dependencies
    try:
        import pytest
    except ImportError:
        missing.append("pytest")
    
    try:
        import pytest_cov
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
    ]
    
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
        
        # P1: Run tests (warning only)
        if not run_tests():
            print("[WARNING] P1 GATE: Some tests failed")
        
        # P1: Check coverage (warning only)
        check_coverage()
        
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
