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
        
        result = subprocess.run(
            aider_cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout (complex refactoring needs more time)
        )
        
        print("[Aider Code Agent] Aider execution completed")
        if result.stdout:
            print(result.stdout)
        
    except subprocess.TimeoutExpired:
        print("[ERROR] Aider execution timed out after 10 minutes")
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
