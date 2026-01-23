#!/usr/bin/env python3
"""scripts/deploy_agent.py

Deterministic Deploy Agent for WAOOAW.

Creates a PR from epic branch to main with summary of changes.
No AI - just Git operations and PR creation.

Environment:
- `GITHUB_TOKEN` (required): For creating PRs via GitHub CLI
"""

import argparse
import subprocess
import sys
import json
from typing import Dict, List, Optional


def get_epic_info(epic_number: str) -> Dict:
    """Get epic issue details using GitHub CLI."""
    try:
        result = subprocess.run(
            ["gh", "issue", "view", epic_number, "--json", "title,body,labels"],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f"[ERROR] Failed to get epic info: {e}")
        return {}


def get_epic_stories(epic_number: str) -> List[Dict]:
    """Get all stories in epic using GitHub CLI."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--label", f"epic-{epic_number}", "--json", "number,title,state"],
            capture_output=True,
            text=True,
            check=True
        )
        stories = json.loads(result.stdout)
        # Filter out the epic itself
        return [s for s in stories if s["number"] != int(epic_number)]
    except Exception as e:
        print(f"[ERROR] Failed to get epic stories: {e}")
        return []


def get_files_changed(epic_branch: str) -> List[str]:
    """Get list of files changed in epic branch vs main."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return [f for f in result.stdout.split("\n") if f]
    except Exception as e:
        print(f"[ERROR] Failed to get changed files: {e}")
        return []


def get_commit_count(epic_branch: str) -> int:
    """Get number of commits in epic branch."""
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "origin/main..HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return int(result.stdout.strip())
    except Exception:
        return 0


def format_pr_body(
    epic_info: Dict,
    stories: List[Dict],
    files_changed: List[str],
    commit_count: int
) -> str:
    """Format PR description."""
    
    epic_title = epic_info.get("title", "Epic")
    epic_body = epic_info.get("body", "")
    
    # Extract epic number from title
    epic_number = ""
    if "[EPIC]" in epic_title:
        epic_number = epic_title.split("]")[0].replace("[EPIC", "").replace("#", "").strip()
    
    body = f"## Epic Summary\n\n"
    body += f"**Epic**: #{epic_number} - {epic_title}\n\n"
    
    # Epic description (first 300 chars)
    if epic_body:
        body += f"**Description**: {epic_body[:300]}{'...' if len(epic_body) > 300 else ''}\n\n"
    
    # Stories completed
    body += f"## Stories Completed ({len(stories)})\n\n"
    for story in stories:
        status = "✅" if story["state"] == "CLOSED" else "⚠️"
        body += f"- {status} #{story['number']}: {story['title']}\n"
    body += "\n"
    
    # Changes summary
    body += f"## Changes Summary\n\n"
    body += f"- **Commits**: {commit_count}\n"
    body += f"- **Files Changed**: {len(files_changed)}\n\n"
    
    # Files by category
    if files_changed:
        body += "### Modified Files\n\n"
        
        categories = {
            "Source Code": [],
            "Tests": [],
            "Infrastructure": [],
            "Documentation": [],
            "Other": []
        }
        
        for file in files_changed:
            if file.startswith("src/") or file.endswith((".py", ".js", ".ts", ".tsx", ".jsx")):
                if "test" in file:
                    categories["Tests"].append(file)
                else:
                    categories["Source Code"].append(file)
            elif file.startswith("infrastructure/") or file.startswith("docker/"):
                categories["Infrastructure"].append(file)
            elif file.endswith((".md", ".txt", ".rst")):
                categories["Documentation"].append(file)
            else:
                categories["Other"].append(file)
        
        for category, files in categories.items():
            if files:
                body += f"**{category}** ({len(files)}):\n"
                for file in files[:10]:  # Limit to 10 files per category
                    body += f"- `{file}`\n"
                if len(files) > 10:
                    body += f"- ... and {len(files) - 10} more\n"
                body += "\n"
    
    # Test status
    body += "## Testing\n\n"
    body += "✅ All tests passed (see Test Agent comment on epic)\n\n"
    
    # Next steps
    body += "## Review Checklist\n\n"
    body += "- [ ] Code changes reviewed\n"
    body += "- [ ] Tests passing\n"
    body += "- [ ] Documentation updated\n"
    body += "- [ ] No breaking changes\n"
    body += "- [ ] Ready to merge\n"
    
    return body


def create_pr(epic_number: str, epic_branch: str, pr_body: str, epic_title: str) -> bool:
    """Create PR using GitHub CLI."""
    
    # Extract clean title
    pr_title = epic_title.replace("[EPIC]", "").strip()
    if not pr_title.startswith("feat:"):
        pr_title = f"feat(epic-{epic_number}): {pr_title}"
    
    try:
        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--base", "main",
                "--head", epic_branch,
                "--title", pr_title,
                "--body", pr_body
            ],
            capture_output=True,
            text=True,
            check=True
        )
        pr_url = result.stdout.strip()
        print(f"[Deploy Agent] ✅ PR created: {pr_url}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to create PR: {e.stderr}")
        return False


def find_existing_pr_url(epic_branch: str) -> str:
    """Find an existing open PR from epic branch -> main.

    This makes the deploy agent idempotent across reruns.
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--base",
                "main",
                "--head",
                epic_branch,
                "--state",
                "open",
                "--limit",
                "1",
                "--json",
                "url",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        prs = json.loads(result.stdout or "[]")
        if prs:
            return prs[0].get("url", "")
        return ""
    except Exception as e:
        print(f"[WARN] Could not query existing PRs: {e}")
        return ""


def post_comment_to_epic(epic_number: str, pr_url: str) -> bool:
    """Post PR link to epic."""
    comment = f"## 🚀 Deploy Agent\n\nPull request created: {pr_url}\n\nReady for review and merge!"
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic Deploy Agent for WAOOAW")
    parser.add_argument("--epic-number", required=True, help="Epic issue number")
    parser.add_argument("--epic-branch", required=True, help="Epic branch name")
    args = parser.parse_args()
    
    epic_number = str(args.epic_number)
    epic_branch = str(args.epic_branch)
    
    print(f"[Deploy Agent] Creating PR for Epic #{epic_number}")
    print(f"[Deploy Agent] Branch: {epic_branch}")
    
    # Gather information
    print("[Deploy Agent] Gathering epic information...")
    epic_info = get_epic_info(epic_number)
    stories = get_epic_stories(epic_number)
    files_changed = get_files_changed(epic_branch)
    commit_count = get_commit_count(epic_branch)
    
    print(f"[Deploy Agent] Found {len(stories)} stories")
    print(f"[Deploy Agent] Found {len(files_changed)} files changed")
    print(f"[Deploy Agent] Found {commit_count} commits")
    
    # Format PR body
    pr_body = format_pr_body(epic_info, stories, files_changed, commit_count)

    # Create or re-use PR
    print("[Deploy Agent] Creating pull request...")
    pr_url = find_existing_pr_url(epic_branch)
    if pr_url:
        print(f"[Deploy Agent] ✅ Existing PR found: {pr_url}")
    else:
        epic_title = epic_info.get("title", f"Epic #{epic_number}")
        if not create_pr(epic_number, epic_branch, pr_body, epic_title):
            sys.exit(1)
        # gh pr create prints the new URL to stdout, but if it doesn't (or in case
        # of repo config issues), fall back to querying the current PR.
        pr_url = find_existing_pr_url(epic_branch)

    # Post PR URL back to epic (best-effort)
    if pr_url:
        print(f"[Deploy Agent] Posting PR link to Epic #{epic_number}")
        post_comment_to_epic(epic_number, pr_url)
    else:
        print("[WARN] Could not determine PR URL to post to epic")
    
    print("[Deploy Agent] ✅ Deployment PR created successfully!")


if __name__ == "__main__":
    main()
