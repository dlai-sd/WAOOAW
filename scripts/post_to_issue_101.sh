#!/bin/bash
# Script to post update to GitHub Issue #101
# Usage: ./scripts/post_to_issue_101.sh

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed."
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI."
    echo "Run: gh auth login"
    exit 1
fi

# Read the update content from the markdown file
UPDATE_FILE="/workspaces/WAOOAW/docs/reference/ISSUE_101_UPDATE_v0.8.0.md"

if [ ! -f "$UPDATE_FILE" ]; then
    echo "Error: Update file not found at $UPDATE_FILE"
    exit 1
fi

echo "Posting update to Issue #101..."
echo ""

# Post the comment to issue #101
gh issue comment 101 --repo dlai-sd/WAOOAW --body-file "$UPDATE_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully posted update to Issue #101!"
    echo "View at: https://github.com/dlai-sd/WAOOAW/issues/101"
else
    echo ""
    echo "❌ Failed to post update. Check GitHub CLI authentication."
    exit 1
fi
