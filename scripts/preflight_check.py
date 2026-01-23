#!/usr/bin/env python3
"""scripts/preflight_check.py

Preflight validation to catch errors BEFORE starting expensive epic processing.

Run this before creating epics to validate:
1. GitHub API connectivity and rate limits
2. Python testing dependencies (pytest, pytest-cov, flake8)
3. OpenAI API key availability
4. Git repository state
5. Aider installation

Usage:
    python scripts/preflight_check.py
    
Exit codes:
    0: All checks passed ✅
    1: Critical failures detected ❌
    2: Warnings present (non-blocking) ⚠️
"""

import os
import subprocess
import sys
import json
from typing import Tuple, List


class Colors:
    """Terminal colors for output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")


def print_check(name: str, status: str, message: str = ""):
    """Print check result."""
    if status == "PASS":
        icon = f"{Colors.GREEN}✅{Colors.END}"
    elif status == "WARN":
        icon = f"{Colors.YELLOW}⚠️{Colors.END}"
    else:
        icon = f"{Colors.RED}❌{Colors.END}"
    
    print(f"{icon} {name:<50} {message}")


def check_github_api() -> Tuple[str, str]:
    """Check GitHub API connectivity and rate limits."""
    try:
        result = subprocess.run(
            ["gh", "api", "rate_limit", "--jq", ".resources.core"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return "FAIL", "GitHub CLI not authenticated or not installed"
        
        data = json.loads(result.stdout)
        remaining = data['remaining']
        limit = data['limit']
        
        if remaining < 100:
            return "WARN", f"Low rate limit: {remaining}/{limit} remaining"
        
        return "PASS", f"{remaining}/{limit} requests remaining"
        
    except subprocess.TimeoutExpired:
        return "FAIL", "GitHub API timeout (network issue?)"
    except FileNotFoundError:
        return "FAIL", "GitHub CLI (gh) not installed"
    except Exception as e:
        return "FAIL", f"Error: {str(e)}"


def check_github_status() -> Tuple[str, str]:
    """Check GitHub platform status."""
    try:
        result = subprocess.run(
            ["curl", "-s", "https://www.githubstatus.com/api/v2/status.json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return "WARN", "Could not check GitHub status"
        
        data = json.loads(result.stdout)
        indicator = data['status']['indicator']
        
        if indicator == 'none':
            return "PASS", "All GitHub systems operational"
        elif indicator == 'minor':
            return "WARN", f"Minor GitHub incidents detected"
        else:
            return "FAIL", f"GitHub incidents: {indicator}"
            
    except Exception as e:
        return "WARN", f"Could not verify GitHub status: {str(e)}"


def check_python_dependencies() -> Tuple[str, str]:
    """Check required Python testing dependencies."""
    missing = []
    
    # Check pytest
    try:
        import pytest
    except ImportError:
        missing.append("pytest")
    
    # Check pytest-cov
    try:
        import pytest_cov
    except ImportError:
        missing.append("pytest-cov")
    
    # Check flake8
    try:
        result = subprocess.run(
            ["python", "-m", "flake8", "--version"],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            missing.append("flake8")
    except:
        missing.append("flake8")
    
    if missing:
        return "FAIL", f"Missing: {', '.join(missing)} (install: pip install {' '.join(missing)})"
    
    return "PASS", "pytest, pytest-cov, flake8 installed"


def check_aider() -> Tuple[str, str]:
    """Check Aider installation."""
    try:
        result = subprocess.run(
            ["aider", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return "FAIL", "Aider not installed (install: pip install aider-chat)"
        
        version = result.stdout.strip()
        return "PASS", f"Aider {version} installed"
        
    except FileNotFoundError:
        return "FAIL", "Aider not found (install: pip install aider-chat)"
    except Exception as e:
        return "FAIL", f"Error checking Aider: {str(e)}"


def check_openai_api_key() -> Tuple[str, str]:
    """Check OpenAI API key availability."""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        return "FAIL", "OPENAI_API_KEY environment variable not set"
    
    if len(api_key) < 20:
        return "FAIL", "OPENAI_API_KEY appears invalid (too short)"
    
    return "PASS", f"API key set ({api_key[:10]}...)"


def check_git_state() -> Tuple[str, str]:
    """Check git repository state."""
    try:
        # Check if in git repo
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return "FAIL", "Not in a git repository"
        
        # Check for uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            return "WARN", "Uncommitted changes detected (may cause conflicts)"
        
        # Check current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        branch = result.stdout.strip()
        if branch == "main":
            return "WARN", "On main branch (epics should use feature branches)"
        
        return "PASS", f"On branch '{branch}', no uncommitted changes"
        
    except Exception as e:
        return "FAIL", f"Git error: {str(e)}"


def check_docker() -> Tuple[str, str]:
    """Check Docker availability (for test services)."""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return "WARN", "Docker not running (needed for integration tests)"
        
        return "PASS", "Docker running"
        
    except FileNotFoundError:
        return "WARN", "Docker not installed (optional for unit tests)"
    except Exception as e:
        return "WARN", f"Docker check failed: {str(e)}"


def main():
    """Run all preflight checks."""
    print_header("🚀 WAOOAW PREFLIGHT CHECK")
    print("Validating environment before epic processing...")
    
    checks = [
        ("GitHub API Connectivity", check_github_api),
        ("GitHub Platform Status", check_github_status),
        ("Python Test Dependencies", check_python_dependencies),
        ("Aider Installation", check_aider),
        ("OpenAI API Key", check_openai_api_key),
        ("Git Repository State", check_git_state),
        ("Docker (Optional)", check_docker),
    ]
    
    failures = []
    warnings = []
    
    print_header("Running Checks")
    
    for name, check_func in checks:
        status, message = check_func()
        print_check(name, status, message)
        
        if status == "FAIL":
            failures.append(f"{name}: {message}")
        elif status == "WARN":
            warnings.append(f"{name}: {message}")
    
    # Summary
    print_header("Summary")
    
    if failures:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ CRITICAL FAILURES ({len(failures)}){Colors.END}")
        for failure in failures:
            print(f"  {Colors.RED}• {failure}{Colors.END}")
        
        print(f"\n{Colors.BOLD}Action Required:{Colors.END}")
        print("  Fix critical failures before creating epics.")
        print("  Without these, Code Agent will fail after 30+ min of processing.")
        
        if warnings:
            print(f"\n{Colors.YELLOW}⚠️  WARNINGS ({len(warnings)}){Colors.END}")
            for warning in warnings:
                print(f"  {Colors.YELLOW}• {warning}{Colors.END}")
        
        return 1
    
    elif warnings:
        print(f"\n{Colors.YELLOW}⚠️  WARNINGS ({len(warnings)}){Colors.END}")
        for warning in warnings:
            print(f"  {Colors.YELLOW}• {warning}{Colors.END}")
        
        print(f"\n{Colors.GREEN}✅ Core checks passed{Colors.END}")
        print("  You can proceed, but warnings should be addressed.")
        
        return 2
    
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL CHECKS PASSED{Colors.END}")
        print("  Environment ready for epic processing!")
        
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
