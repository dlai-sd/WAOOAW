#!/usr/bin/env python3
"""
Simulation test for Code Agent validation gates.
Tests syntax validation, stub detection without running full Aider workflow.
"""

import pytest
import subprocess
import tempfile
import os
import sys

@pytest.fixture()
def test_repo(tmp_path, monkeypatch):
    """Create and chdir into a temporary git repo for each test."""
    monkeypatch.chdir(tmp_path)
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        check=True,
        capture_output=True,
    )
    return tmp_path

def test_syntax_validation(test_repo):
    """Test that syntax errors are caught."""
    print("\n" + "="*80)
    print("TEST 1: Syntax Validation")
    print("="*80)
    
    # Create file with syntax error (like Epic #374)
    os.makedirs("src/Plant/BackEnd/api/v1", exist_ok=True)
    
    with open("src/Plant/BackEnd/api/v1/test.py", "w") as f:
        f.write('''
def example():
    """
    This is a docstring
    # Missing closing triple-quote - syntax error
''')
    
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    
    # Run flake8 syntax check
    result = subprocess.run(
        ["python", "-m", "flake8", "--select=E9,F821,F823,F831,F406,F407,F701,F702,F704,F706", 
         "src/Plant/BackEnd/api/v1/test.py"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode != 0
    print("✅ PASS: Syntax error detected")
    print(f"   Error: {result.stdout.strip()}")

def test_stub_detection(test_repo):
    """Test that stub code is caught."""
    print("\n" + "="*80)
    print("TEST 2: Stub Code Detection")
    print("="*80)
    
    # Create file with stub code (like Epic #374)
    os.makedirs("src/CP/BackEnd/middleware", exist_ok=True)
    
    with open("src/CP/BackEnd/middleware/test.py", "w") as f:
        f.write('''
def validate_request(request):
    # TODO: Implement OpenAPI validation
    return True  # Stub implementation

def get_tenant_id(request):
    return "default_tenant"  # Placeholder
''')
    
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    
    # Get diff
    result = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True,
        text=True,
        check=True
    )
    
    diff_content = result.stdout
    
    # Check for stub patterns
    stubs_found = []
    if 'return True' in diff_content and 'TODO' in diff_content:
        stubs_found.append("return True with TODO")
    if 'return "default_' in diff_content:
        stubs_found.append("return default stub")
    
    assert stubs_found
    print("✅ PASS: Stub code detected")
    for stub in stubs_found:
        print(f"   Found: {stub}")

def test_valid_code(test_repo):
    """Test that valid code passes."""
    print("\n" + "="*80)
    print("TEST 3: Valid Code Should Pass")
    print("="*80)
    
    # Create valid Python file
    os.makedirs("src/CP/BackEnd/core", exist_ok=True)
    
    with open("src/CP/BackEnd/core/valid.py", "w") as f:
        f.write('''
"""Valid Python module."""

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
''')
    
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    
    # Run syntax check
    result = subprocess.run(
        ["python", "-m", "flake8", "--select=E9,F821,F823,F831,F406,F407,F701,F702,F704,F706",
         "src/CP/BackEnd/core/valid.py"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    print("✅ PASS: Valid code accepted")

def main():
    print("="*80)
    print("Code Agent Validation Gate Simulation")
    print("="*80)
    
    # Save original directory
    orig_dir = os.getcwd()
    
    try:
        # Setup test environment
        tmpdir = setup_test_repo()
        print(f"\nTest repo: {tmpdir}")
        
        # Run tests
        results = []
        results.append(("Syntax Validation", test_syntax_validation()))
        results.append(("Stub Detection", test_stub_detection()))
        results.append(("Valid Code Pass", test_valid_code()))
        
        # Summary
        print("\n" + "="*80)
        print("SIMULATION RESULTS")
        print("="*80)
        
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        passed_count = sum(1 for _, p in results if p)
        total_count = len(results)
        
        print(f"\nTotal: {passed_count}/{total_count} tests passed")
        
        if passed_count == total_count:
            print("\n🎉 All validation gates working correctly!")
            return 0
        else:
            print("\n⚠️  Some validation gates need fixes")
            return 1
        
    finally:
        # Cleanup
        os.chdir(orig_dir)
        subprocess.run(["rm", "-rf", tmpdir], capture_output=True)

if __name__ == "__main__":
    sys.exit(main())
