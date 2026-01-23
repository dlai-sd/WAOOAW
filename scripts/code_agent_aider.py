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
from pathlib import Path


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
    target_dirs = []
    
    if "plant" in combined or "plant api" in combined:
        target_dirs.append("src/Plant")
    elif "cp portal" in combined or "customer portal" in combined:
        target_dirs.append("src/CP")
    elif "pp portal" in combined or "partner portal" in combined:
        target_dirs.append("src/PP")
    elif "gateway" in combined:
        target_dirs.append("src/gateway")
    
    # Default to all allowed directories if no specific match
    if not target_dirs:
        target_dirs = ["src/", "backend/", "frontend/", "infrastructure/"]
    
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
    print(f"[Aider Code Agent] Target directories: {', '.join(target_dirs)}")
    
    # Run Aider
    try:
        # Prepare Aider command
        # Use current directory (git repo root) - Aider handles subdirectory focus via repo-map
        aider_cmd = [
            "aider",
            "--yes",  # Auto-accept changes
            "--no-auto-commits",  # We'll commit manually
            f"--model={model}",
            "--message", prompt,
            "."  # Current directory (git repo root)
        ]
        
        print(f"[Aider Code Agent] Running: {' '.join(aider_cmd[:5])}...")
        
        result = subprocess.run(
            aider_cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print("[Aider Code Agent] Aider execution completed")
        if result.stdout:
            print(result.stdout)
        
    except subprocess.TimeoutExpired:
        print("[ERROR] Aider execution timed out after 5 minutes")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Aider execution failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
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
