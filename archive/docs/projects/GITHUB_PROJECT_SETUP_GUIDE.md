# WAOOAW Platform CoEs - GitHub Project Setup Guide

**Project Name:** WAOOAW Platform CoEs  
**Purpose:** Track development of 14 Platform Center of Excellence agents  
**Tracking Levels:** CoE Pillars, Epics, Stories  
**Created:** December 28, 2025

---

## Quick Setup Instructions

### Step 1: Create GitHub Project (Web UI)

1. Go to: https://github.com/orgs/dlai-sd/projects or https://github.com/dlai-sd/WAOOAW/projects
2. Click "New Project"
3. Choose "Board" template
4. Name: **WAOOAW Platform CoEs**
5. Description: **Track development of 14 Platform Center of Excellence agents and WowAgentFactory implementation**

### Step 2: Add All Issues to Project

Run this command to add all issues:
```bash
# List of issues to add
for issue in 68 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95; do
  echo "Adding issue #$issue to project..."
  # You'll need to do this via web UI or get project ID first
done
```

Or manually: Go to each issue and click "Add to project" → Select "WAOOAW Platform CoEs"

---

## Project Structure

### Board Columns (Kanban View)

```
┌─────────────┬──────────────────┬───────────────┬─────────────┐
│   Backlog   │   Todo (Ready)   │  In Progress  │    Done     │
├─────────────┼──────────────────┼───────────────┼─────────────┤
│ Not started │ Ready to start   │ Active work   │ Completed   │
│             │                  │               │             │
│ Stories     │ Prioritized      │ Max 3 items   │ WowVision   │
│ #75-#88     │ stories          │ at a time     │ Prime ✅    │
│             │                  │               │             │
│ CoE Quests  │ Next CoEs to     │ Current       │ #89 ✅      │
│ #90-#95     │ implement        │ Epic/Story    │             │
└─────────────┴──────────────────┴───────────────┴─────────────┘
```

### Labels to Add

Create these labels in GitHub (Settings → Labels):

| Label | Color | Description |
|-------|-------|-------------|
| `epic` | `#5319E7` (purple) | Epic-level issues |
| `story` | `#0E8A16` (green) | Story-level issues |
| `coe-pillar` | `#D73A4A` (red) | Platform CoE pillar |
| `questionnaire` | `#0075CA` (blue) | CoE questionnaire |
| `platform-coe` | `#F9D0C4` (pink) | Platform CoE work |
| `v0.3.x` | `#FBCA04` (yellow) | Version 0.3.x |
| `v0.4.x` | `#FBCA04` (yellow) | Version 0.4.x |
| `v0.5.x` | `#FBCA04` (yellow) | Version 0.5.x |
| `completed` | `#28A745` (green) | Completed work |
| `in-progress` | `#FFA500` (orange) | Currently active |
| `blocked` | `#D93F0B` (red) | Blocked/waiting |

### Milestones to Create

Go to: https://github.com/dlai-sd/WAOOAW/milestones/new

1. **v0.3.6: WowVision Prime Complete ✅**
   - Due: Jan 2026 (already done)
   - Issues: #89
   - Description: First Platform CoE agent operational

2. **v0.4.0: WowDomain Complete**
   - Due: Week 9 (Feb 2026)
   - Issues: #90
   - Description: Domain expert CoE (first Factory-created agent)

3. **v0.4.1: WowAgentFactory Complete**
   - Due: Week 8 (End of Jan 2026)
   - Issues: #68, #74-#88
   - Description: Agent creation automation complete

4. **v0.4.4: Core Infrastructure CoEs**
   - Due: Week 11 (Mid Feb 2026)
   - Issues: #91, #92
   - Description: WowQuality, WowOps, WowSecurity complete

5. **v0.5.3: Marketplace CoEs**
   - Due: Week 16 (End of Mar 2026)
   - Issues: #93, #94, #95
   - Description: Marketplace, Auth, Payment, Notification complete

6. **v0.7.0: All 14 Platform CoEs Complete**
   - Due: Week 30 (End of Apr 2026)
   - Issues: All remaining CoEs
   - Description: Platform foundation complete

---

## Project Views Configuration

### View 1: Kanban Board (Default)

**Purpose:** Day-to-day task management

**Configuration:**
- Layout: Board
- Group by: Status
- Sort by: Priority (High → Low)
- Filter: None (show all)

**Columns:**
1. **Backlog** - Status: None
2. **Todo** - Status: Todo
3. **In Progress** - Status: In Progress
4. **Done** - Status: Done

### View 2: CoE Pillars Tracker

**Purpose:** Track 14 Platform CoE agents at high level

**Configuration:**
- Layout: Table
- Group by: CoE Type (Vision, Domain, Factory, Quality, etc.)
- Columns:
  - Title
  - Status (✅ Complete / 🔄 In Progress / 📋 Planned)
  - Assignee
  - Version (v0.3.x, v0.4.x, etc.)
  - Timeline (Week #)
  - Dependencies

**Rows (14 CoEs):**
```
| CoE # | Agent Name | Status | Version | Timeline | Dependencies |
|-------|------------|--------|---------|----------|--------------|
| 1 | WowVision Prime | ✅ Complete | v0.3.6 | Week 1-4 | None |
| 2 | WowDomain | 📋 Planned | v0.4.0 | Week 9 | WowAgentFactory |
| 3 | WowAgentFactory | 🔄 In Progress | v0.4.1 | Week 5-8 | WowVision Prime |
| 4 | WowQuality | 📋 Planned | v0.4.2 | Week 10 | WowAgentFactory |
| 5 | WowOps | 📋 Planned | v0.4.3 | Week 11 | WowAgentFactory |
| 6 | WowSecurity | 📋 Planned | v0.4.4 | Week 12 | WowAgentFactory |
| 7 | WowMarketplace | 📋 Planned | v0.5.0 | Week 13-14 | WowAuth, WowPayment |
| 8 | WowAuth | 📋 Planned | v0.5.1 | Week 15 | WowSecurity |
| 9 | WowPayment | 📋 Planned | v0.5.2 | Week 16 | WowAuth |
| 10 | WowNotification | 📋 Planned | v0.5.3 | Week 17 | None |
| 11 | WowAnalytics | 📋 Planned | v0.5.4 | Week 18-19 | All CoEs |
| 12 | WowScaling | 📋 Planned | v0.5.5 | Week 20 | WowOps |
| 13 | WowIntegration | 📋 Planned | v0.5.6 | Week 21 | None |
| 14 | WowSupport | 📋 Planned | v0.5.7 | Week 22 | WowNotification |
```

### View 3: Epic Breakdown

**Purpose:** Track Epics and their Stories

**Configuration:**
- Layout: Table
- Group by: Epic (linked via "Epic:" prefix in Story body)
- Filter: Label = `epic` OR `story`
- Columns:
  - Title
  - Type (Epic/Story)
  - Status
  - Assignee
  - Story Points (estimate)

**Epic Hierarchy:**
```
Epic: WowAgentFactory (v0.4.1) [#68]
  ├── Epic 1: Agent Template System
  │   ├── Story 1.1: Base CoE Template [#74] - 3 points
  │   ├── Story 1.2: Specialization Config Schema [#75] - 2 points
  │   └── Story 1.3: Test Template Generator [#76] - 3 points
  ├── Epic 2: Code Generation Engine
  │   ├── Story 2.1: Agent Code Generator [#77] - 5 points
  │   └── Story 2.2: WowAgentFactory Agent Implementation [#78] - 5 points
  ├── Epic 3: Deployment Automation
  │   ├── Story 3.1: Staging Deployer [#79] - 3 points
  │   ├── Story 3.2: Shadow Mode Validator [#80] - 3 points
  │   └── Story 3.3: Production Deployer [#81] - 5 points
  ├── Epic 4: Vision Integration
  │   └── Story 4.1: Vision Validation Integration [#82] - 3 points
  ├── Epic 5: Testing & Quality
  │   └── Story 5.1: Unit & Integration Tests [#83] - 5 points
  └── Epic 6: Documentation
      └── Story 6.1: Factory Documentation [#88] - 2 points

Total Story Points: 39
Estimated Time: 2 weeks (Week 5-8)
```

### View 4: Timeline (Roadmap)

**Purpose:** Visual timeline of all work

**Configuration:**
- Layout: Roadmap
- Group by: Milestone
- Date field: Start date, Due date
- Color by: CoE Type

**Timeline (30 weeks):**
```
Week 1-4:   █████████ WowVision Prime (DONE) ✅
Week 5-8:   █████████ WowAgentFactory (IN PROGRESS)
Week 9:     ███ WowDomain (Factory creates)
Week 10:    ███ WowQuality (Factory creates)
Week 11:    ███ WowOps (Factory creates)
Week 12:    ███ WowSecurity (Factory creates)
Week 13-14: █████ WowMarketplace (Factory creates)
Week 15:    ███ WowAuth (Factory creates)
Week 16:    ███ WowPayment (Factory creates)
Week 17:    ███ WowNotification (Factory creates)
Week 18-19: █████ WowAnalytics (Factory creates)
Week 20:    ███ WowScaling (Factory creates)
Week 21:    ███ WowIntegration (Factory creates)
Week 22:    ███ WowSupport (Factory creates)
Week 23-30: Customer-facing agents (19+ agents)
```

### View 5: Priority Matrix

**Purpose:** Prioritize work by impact vs effort

**Configuration:**
- Layout: Board
- Group by: Priority (High, Medium, Low)
- Sort by: Impact score

**Priority Levels:**
- **P0 (Critical):** WowVision Prime ✅, WowAgentFactory 🔄
- **P1 (High):** WowDomain, WowQuality, WowOps, WowSecurity
- **P2 (Medium):** Marketplace CoEs (WowMarketplace, WowAuth, WowPayment, WowNotification)
- **P3 (Low):** Analytics, Scaling, Integration, Support

---

## Issue Organization

### Apply Labels to All Issues

**Epic Issue:**
```bash
gh issue edit 68 --add-label "epic,platform-coe,v0.4.1,in-progress"
```

**Story Issues:**
```bash
for issue in 74 75 76 77 78 79 80 81 82 83 88; do
  gh issue edit $issue --add-label "story,platform-coe,v0.4.1"
done
```

**CoE Questionnaire Issues:**
```bash
gh issue edit 89 --add-label "coe-pillar,completed,v0.3.6"  # WowVision Prime
gh issue edit 90 --add-label "coe-pillar,questionnaire,v0.4.0"  # WowDomain
gh issue edit 91 --add-label "coe-pillar,questionnaire,v0.4.2"  # WowQuality
gh issue edit 92 --add-label "coe-pillar,questionnaire,v0.4.3"  # WowOps
gh issue edit 93 --add-label "coe-pillar,questionnaire,v0.5.0"  # WowMarketplace
gh issue edit 94 --add-label "coe-pillar,questionnaire,v0.5.1"  # WowAuth
gh issue edit 95 --add-label "coe-pillar,questionnaire,v0.5.2"  # WowPayment
```

### Link Issues

**Epic → Stories:**
Add this to each Story issue description:
```markdown
**Epic:** #68 - WowAgentFactory (v0.4.1)
```

**Dependencies:**
Add this to dependent issues:
```markdown
**Depends on:** #68 (WowAgentFactory)
**Blocks:** #90 (WowDomain)
```

---

## Custom Fields to Add

Go to Project Settings → Custom Fields:

1. **CoE Type**
   - Type: Single select
   - Options: Vision, Domain, Factory, Quality, Ops, Security, Marketplace, Auth, Payment, Notification, Analytics, Scaling, Integration, Support

2. **Story Points**
   - Type: Number
   - Description: Estimated effort (1-8 points)

3. **Week Number**
   - Type: Number
   - Description: Target week (1-30)

4. **Dependencies**
   - Type: Text
   - Description: Issue numbers this depends on

5. **Budget**
   - Type: Text
   - Description: Monthly cost (e.g., "$25/month")

6. **Success Metric**
   - Type: Text
   - Description: Key metric for this CoE

---

## Automation Rules

Set up automation in Project Settings → Workflows:

### Rule 1: Auto-move to In Progress
**Trigger:** Issue assigned  
**Action:** Move to "In Progress" column

### Rule 2: Auto-move to Done
**Trigger:** Issue closed  
**Action:** Move to "Done" column, Add "completed" label

### Rule 3: Auto-assign Epic label
**Trigger:** Issue created with "Epic:" in title  
**Action:** Add "epic" label

### Rule 4: Auto-link Stories to Epic
**Trigger:** Issue created with "Epic: #XX" in body  
**Action:** Link to Epic issue

---

## Dashboard Widgets

### Widget 1: CoE Progress
**Type:** Progress bar  
**Metric:** Completed CoEs / 14 Total  
**Current:** 1/14 (7%)  
**Target:** 14/14 (100%) by Week 30

### Widget 2: Story Velocity
**Type:** Burndown chart  
**Metric:** Story points completed per week  
**Target:** 20 points/week average

### Widget 3: Timeline Status
**Type:** Gantt chart  
**Shows:** All 14 CoEs with start/end dates

### Widget 4: Budget Tracking
**Type:** Line chart  
**Metric:** Monthly cost (currently $25/month for WowVision)  
**Target:** <$500/month for all 14 CoEs

---

## Weekly Review Checklist

Use this checklist every Monday:

- [ ] Review Kanban board - move completed items to Done
- [ ] Update CoE Pillars Tracker - change status of active CoEs
- [ ] Check Timeline - adjust dates if needed
- [ ] Review blockers - resolve dependencies
- [ ] Update story points - track velocity
- [ ] Plan next week - move items from Backlog to Todo
- [ ] Update STATUS.md in repository

---

## Quick Commands Reference

### View Project (Web)
```bash
# Open project in browser
gh project list --owner dlai-sd
# Click on "WAOOAW Platform CoEs"
```

### Add Issue to Project
```bash
# Via web UI: Go to issue → Add to project
# Or use gh CLI (need project ID):
gh project item-add <PROJECT_ID> --owner dlai-sd --url https://github.com/dlai-sd/WAOOAW/issues/<ISSUE_NUMBER>
```

### Update Issue Status
```bash
# Via web UI: Drag and drop in Kanban board
# Or edit issue:
gh issue edit <ISSUE_NUMBER> --add-label "in-progress"
```

### Generate Report
```bash
# Export project data
gh project list --owner dlai-sd --format json > project_status.json
```

---

## Integration with Documentation

### Link Project in README
Add to `README.md`:
```markdown
## 📊 Project Tracking

Track platform development progress:
- [GitHub Project: WAOOAW Platform CoEs](https://github.com/orgs/dlai-sd/projects/X)
- [Epic: WowAgentFactory #68](https://github.com/dlai-sd/WAOOAW/issues/68)
- [All Platform CoE Issues](https://github.com/dlai-sd/WAOOAW/labels/platform-coe)
```

### Update STATUS.md Weekly
```markdown
## Current Sprint (Week 5)

**Epic:** WowAgentFactory (v0.4.1)  
**Progress:** 3/12 stories complete (25%)  
**On Track:** Yes ✅

**Completed This Week:**
- Story 1.1: Base CoE Template ✅
- Story 1.2: Specialization Config Schema ✅
- Story 1.3: Test Template Generator ✅

**Next Week:**
- Story 2.1: Agent Code Generator
- Story 2.2: WowAgentFactory Agent Implementation
```

---

## Success Metrics

Track these KPIs in the project:

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| CoEs Complete | 1/14 (7%) | 14/14 (100%) | 🟡 On track |
| Stories Complete | 0/12 (0%) | 12/12 (100%) | 🟢 Not started |
| Timeline Variance | 0 weeks | <2 weeks | 🟢 On schedule |
| Budget | $25/month | <$500/month | 🟢 Under budget |
| Code Reuse | 0% | >70% | ⚪ Not applicable yet |

---

## Conclusion

This GitHub Project structure provides:

✅ **CoE Pillar Tracking:** Visual progress of all 14 Platform CoEs  
✅ **Epic/Story Management:** Clear breakdown of WowAgentFactory work  
✅ **Timeline Visibility:** 30-week roadmap with dependencies  
✅ **Status Reporting:** Weekly progress tracking and KPIs  
✅ **Team Collaboration:** Kanban board for daily standup  

**Next Step:** Create the project via GitHub web UI and apply this structure! 🚀

---

**References:**
- [GitHub Projects Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [Project Views Guide](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project)
- [Automation Workflows](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project)
