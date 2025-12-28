#!/bin/bash

# WAOOAW Platform CoEs - Project Setup Script
# This script applies labels, milestones, and organization to all issues

echo "🚀 Setting up WAOOAW Platform CoEs Project..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to add labels to an issue
add_labels() {
    local issue=$1
    shift
    local labels="$@"
    echo -e "${BLUE}Adding labels to issue #$issue: $labels${NC}"
    gh issue edit $issue --add-label "$labels" 2>&1
}

# Function to set milestone
set_milestone() {
    local issue=$1
    local milestone=$2
    echo -e "${BLUE}Setting milestone for issue #$issue: $milestone${NC}"
    gh issue edit $issue --milestone "$milestone" 2>&1
}

echo ""
echo "📋 Step 1: Creating Labels..."
echo "---"

# Create labels if they don't exist
gh label create "epic" --color "5319E7" --description "Epic-level issues" 2>/dev/null || echo "Label 'epic' already exists"
gh label create "story" --color "0E8A16" --description "Story-level issues" 2>/dev/null || echo "Label 'story' already exists"
gh label create "coe-pillar" --color "D73A4A" --description "Platform CoE pillar" 2>/dev/null || echo "Label 'coe-pillar' already exists"
gh label create "questionnaire" --color "0075CA" --description "CoE questionnaire" 2>/dev/null || echo "Label 'questionnaire' already exists"
gh label create "platform-coe" --color "F9D0C4" --description "Platform CoE work" 2>/dev/null || echo "Label 'platform-coe' already exists"
gh label create "v0.3.x" --color "FBCA04" --description "Version 0.3.x" 2>/dev/null || echo "Label 'v0.3.x' already exists"
gh label create "v0.4.x" --color "FBCA04" --description "Version 0.4.x" 2>/dev/null || echo "Label 'v0.4.x' already exists"
gh label create "v0.5.x" --color "FBCA04" --description "Version 0.5.x" 2>/dev/null || echo "Label 'v0.5.x' already exists"
gh label create "completed" --color "28A745" --description "Completed work" 2>/dev/null || echo "Label 'completed' already exists"
gh label create "in-progress" --color "FFA500" --description "Currently active" 2>/dev/null || echo "Label 'in-progress' already exists"
gh label create "blocked" --color "D93F0B" --description "Blocked/waiting" 2>/dev/null || echo "Label 'blocked' already exists"

echo -e "${GREEN}✅ Labels created${NC}"

echo ""
echo "📋 Step 2: Creating Milestones..."
echo "---"

# Create milestones
gh api repos/dlai-sd/WAOOAW/milestones -f title="v0.3.6: WowVision Prime Complete" -f state="closed" -f description="First Platform CoE agent operational" -f due_on="2026-01-31T00:00:00Z" 2>/dev/null || echo "Milestone v0.3.6 exists"
gh api repos/dlai-sd/WAOOAW/milestones -f title="v0.4.0: WowDomain Complete" -f state="open" -f description="Domain expert CoE (first Factory-created agent)" -f due_on="2026-02-28T00:00:00Z" 2>/dev/null || echo "Milestone v0.4.0 exists"
gh api repos/dlai-sd/WAOOAW/milestones -f title="v0.4.1: WowAgentFactory Complete" -f state="open" -f description="Agent creation automation complete" -f due_on="2026-01-31T00:00:00Z" 2>/dev/null || echo "Milestone v0.4.1 exists"
gh api repos/dlai-sd/WAOOAW/milestones -f title="v0.4.4: Core Infrastructure CoEs" -f state="open" -f description="WowQuality, WowOps, WowSecurity complete" -f due_on="2026-03-15T00:00:00Z" 2>/dev/null || echo "Milestone v0.4.4 exists"
gh api repos/dlai-sd/WAOOAW/milestones -f title="v0.5.3: Marketplace CoEs" -f state="open" -f description="Marketplace, Auth, Payment, Notification complete" -f due_on="2026-03-31T00:00:00Z" 2>/dev/null || echo "Milestone v0.5.3 exists"
gh api repos/dlai-sd/WAOOAW/milestones -f title="v0.7.0: All Platform CoEs Complete" -f state="open" -f description="Platform foundation complete" -f due_on="2026-04-30T00:00:00Z" 2>/dev/null || echo "Milestone v0.7.0 exists"

echo -e "${GREEN}✅ Milestones created${NC}"

echo ""
echo "📋 Step 3: Applying Labels to Issues..."
echo "---"

# Epic Issue
add_labels 68 "epic,platform-coe,v0.4.x,in-progress"

# Story Issues (WowAgentFactory)
add_labels 74 "story,platform-coe,v0.4.x"
add_labels 75 "story,platform-coe,v0.4.x"
add_labels 76 "story,platform-coe,v0.4.x"
add_labels 77 "story,platform-coe,v0.4.x"
add_labels 78 "story,platform-coe,v0.4.x"
add_labels 79 "story,platform-coe,v0.4.x"
add_labels 80 "story,platform-coe,v0.4.x"
add_labels 81 "story,platform-coe,v0.4.x"
add_labels 82 "story,platform-coe,v0.4.x"
add_labels 83 "story,platform-coe,v0.4.x"
add_labels 88 "story,platform-coe,v0.4.x"

# CoE Questionnaire Issues
add_labels 89 "coe-pillar,platform-coe,completed,v0.3.x"  # WowVision Prime
add_labels 90 "coe-pillar,questionnaire,platform-coe,v0.4.x"  # WowDomain
add_labels 91 "coe-pillar,questionnaire,platform-coe,v0.4.x"  # WowQuality
add_labels 92 "coe-pillar,questionnaire,platform-coe,v0.4.x"  # WowOps
add_labels 93 "coe-pillar,questionnaire,platform-coe,v0.5.x"  # WowMarketplace
add_labels 94 "coe-pillar,questionnaire,platform-coe,v0.5.x"  # WowAuth
add_labels 95 "coe-pillar,questionnaire,platform-coe,v0.5.x"  # WowPayment

echo -e "${GREEN}✅ Labels applied to all issues${NC}"

echo ""
echo "📋 Step 4: Setting Milestones..."
echo "---"

set_milestone 68 "v0.4.1: WowAgentFactory Complete"
set_milestone 89 "v0.3.6: WowVision Prime Complete"
set_milestone 90 "v0.4.0: WowDomain Complete"
set_milestone 91 "v0.4.4: Core Infrastructure CoEs"
set_milestone 92 "v0.4.4: Core Infrastructure CoEs"
set_milestone 93 "v0.5.3: Marketplace CoEs"
set_milestone 94 "v0.5.3: Marketplace CoEs"
set_milestone 95 "v0.5.3: Marketplace CoEs"

# Story issues to Factory milestone
for issue in 74 75 76 77 78 79 80 81 82 83 88; do
    set_milestone $issue "v0.4.1: WowAgentFactory Complete"
done

echo -e "${GREEN}✅ Milestones assigned${NC}"

echo ""
echo "📋 Step 5: Summary..."
echo "---"

echo -e "${YELLOW}Issues organized:${NC}"
echo "  • Epic: #68 (WowAgentFactory)"
echo "  • Stories: #74-#88 (12 stories)"
echo "  • CoE Pillars: #89-#95 (7 questionnaires)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Create GitHub Project via web UI:"
echo "     https://github.com/dlai-sd/WAOOAW/projects/new"
echo "  2. Name: 'WAOOAW Platform CoEs'"
echo "  3. Add all issues to project"
echo "  4. Configure views (Kanban, CoE Tracker, Roadmap)"
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
