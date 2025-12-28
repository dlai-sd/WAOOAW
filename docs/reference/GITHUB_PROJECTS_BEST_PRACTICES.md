# GitHub Projects Best Practices for WAOOAW

## Overview

GitHub offers two ways to use Projects:
1. **Repository Projects (Classic)** - Legacy, simple Kanban boards
2. **Projects V2 (Beta)** - Modern, powerful with custom fields, views, automation

For WAOOAW, we use **Projects V2** as the standard approach.

## ✅ Best Practice: Projects V2 (Recommended)

### Why Projects V2?

- **Cross-Repository**: Track work across multiple repos (future: frontend, mobile app, agents)
- **Custom Fields**: Priority, Dimension, Effort, Status, Assignee
- **Multiple Views**: Board (Kanban), Table (Spreadsheet), Roadmap (Timeline)
- **Automation**: Auto-add issues, auto-move on status change
- **Filtering**: Slice by dimension, version, priority, assignee
- **Mobile-First**: Full support in GitHub mobile app

### Standard Setup for WAOOAW

#### 1. Project Structure

```
Project: WAOOAW Development
├── View 1: 📋 Board (Kanban)
│   ├── Column: 📥 Backlog
│   ├── Column: 🎨 Design
│   ├── Column: 💻 Implementation
│   ├── Column: 🧪 Testing
│   └── Column: ✅ Done
├── View 2: 📊 Table (Spreadsheet)
│   └── Columns: Title, Status, Dimension, Priority, Assignee, Labels
├── View 3: 🗓️ Roadmap (Timeline)
│   └── Timeline by milestone due dates
└── View 4: 🔥 Critical Issues
    └── Filter: Severity = Critical
```

#### 2. Custom Fields

| Field | Type | Values | Usage |
|-------|------|--------|-------|
| **Status** | Single Select | Backlog, Design, Implementation, Testing, Done | Current phase |
| **Dimension** | Single Select | 1-15, All | Which dimension(s) affected |
| **Priority** | Single Select | P0 (Critical), P1 (High), P2 (Medium), P3 (Low) | Business priority |
| **Effort** | Number | 1-5 story points | Size estimate |
| **Version** | Single Select | v0.2.0, v0.2.1, etc. | Target release |

#### 3. Automation Workflows

```yaml
Workflow 1: Auto-Add Issues
  Trigger: Issue created with label "dimension-*"
  Action: Add to project → Status: Backlog

Workflow 2: Auto-Close on Issue Close
  Trigger: Issue closed
  Action: Status → Done

Workflow 3: Auto-Move on PR Merge
  Trigger: PR merged
  Action: Status → Done

Workflow 4: Critical Alert
  Trigger: Issue added with label "critical"
  Action: Priority → P0, notify @dlai-sd
```

## 🎯 Current Setup for WAOOAW

### Manual Setup Steps (Web UI)

Since token lacks project permissions, use web UI:

**Step 1: Create Project**
1. Go to https://github.com/dlai-sd
2. Click **"Projects"** tab
3. Click **"New project"**
4. Choose **"Board"** template
5. Name: `WAOOAW Development`
6. Description: `Track all work across 15 dimensions for AI agent marketplace`

**Step 2: Link to Repository**
1. Open project settings (⚙️ icon)
2. Click **"Manage access"**
3. Add repository: `dlai-sd/WAOOAW`
4. Permission: Read & Write

**Step 3: Configure Columns (Board View)**
1. Rename default columns:
   - Todo → **📥 Backlog**
   - In Progress → **💻 Implementation**
   - Done → **✅ Done**
2. Add new columns:
   - **🎨 Design** (between Backlog and Implementation)
   - **🧪 Testing** (between Implementation and Done)

**Step 4: Add Custom Fields**
1. Click **"+ New field"** in Table view
2. Add fields listed above (Status, Dimension, Priority, Effort, Version)

**Step 5: Add Issues #42-48**
1. Click **"Add items"** → Search "is:issue repo:dlai-sd/WAOOAW"
2. Select issues #42-48
3. Click **"Add selected"**

**Step 6: Organize Issues by Status**

| Issue | Status | Justification |
|-------|--------|---------------|
| #42: Base Agent Architecture | ✅ Done | Completed v0.2.0 |
| #43: Message Bus Architecture | ✅ Done | Completed v0.2.1 |
| #44: Message Handler Design | ✅ Done | Completed v0.2.2 |
| #45: MessageBus Class | 💻 Implementation | Ready to code |
| #46: MessageHandler Class | 💻 Implementation | Depends on #45 |
| #47: Base Agent Integration | 💻 Implementation | Depends on #46 |
| #48: Redis Persistence Gap | 🔥 Backlog (P0) | Critical, quick fix |

**Step 7: Enable Workflows**
1. Project Settings → **"Workflows"**
2. Enable: "Auto-add to project" (for new issues with labels)
3. Enable: "Item closed" → Move to Done
4. Enable: "Pull request merged" → Move to Done

## 📱 Mobile App Usage

### Accessing Project

1. Open **GitHub mobile app**
2. Tap **profile icon** → Your profile
3. Tap **"Projects"** tab
4. Tap **"WAOOAW Development"**

### Views Available on Mobile

- **📋 Board View**: Drag cards between columns
- **📊 List View**: Compact list with filters
- **🔍 Search**: Find issues quickly

### Mobile Workflows

**Update Task Status:**
```
1. Tap issue card
2. Tap "Status" field
3. Select new status (Backlog → Implementation → Testing → Done)
```

**Check Off Subtasks:**
```
1. Tap issue card
2. Scroll to task checklist
3. Tap checkbox to mark complete
```

**Comment with Copilot:**
```
1. Tap issue card → "Comment"
2. Type: "@github-copilot implement the priority queue in MessageHandler"
3. Post → Copilot responds with code
```

**Filter View:**
```
1. Tap filter icon 🔍
2. Select: "Label: dimension-7" → See all communication protocol issues
3. Select: "Status: Implementation" → See what's being coded
4. Select: "Priority: P0" → See critical items
```

## 🖥️ Desktop Workflows

### Using Project for Development

**Morning Standup:**
```
1. Open project Board view
2. Check "Implementation" column
3. Move your assigned issue if status changed
4. Comment updates: "Completed MessageBus.send(), working on receive()"
```

**Starting New Task:**
```
1. Find issue in Backlog with Priority P1+
2. Assign to yourself
3. Move to "Implementation"
4. Create feature branch: git checkout -b feature/issue-45-messagebus
5. Reference in commits: "feat(messaging): implement MessageBus class (#45)"
```

**Code Review:**
```
1. PR merged → Issue auto-moves to Done
2. Update checklist in issue
3. Comment: "✅ Completed. Tested with 100 messages. Coverage: 87%"
```

**Tracking Progress:**
```
1. Table view → Sort by "Status"
2. Count: Done (3) / Total (7) = 43% complete
3. Roadmap view → See milestone progress
```

### Integration with Copilot

**In Issue Comments:**
```markdown
@github-copilot I need help with issue #45. 

Looking at docs/MESSAGE_BUS_ARCHITECTURE.md, can you:
1. Generate the MessageBus class structure
2. Implement the priority queue logic
3. Add unit tests

Context: 5 priority streams (p1-p5), Redis Streams backend.
```

**In PR Comments:**
```markdown
@github-copilot review this MessageBus implementation.

Check for:
- ✅ At-least-once delivery correctness
- ✅ Consumer group handling
- ✅ Error handling and DLQ
- ✅ Test coverage
```

## 🎯 Slice & Dice Views

### View 1: By Dimension
```
Filter: Label contains "dimension-7"
→ See all Communication Protocol work
```

### View 2: By Phase
```
Filter: Status = "Implementation"
→ See what's actively being coded
```

### View 3: By Version
```
Filter: Label = "v0.2.3"
→ See all work in current sprint
```

### View 4: By Severity
```
Filter: Label = "critical"
→ See critical issues requiring immediate attention
```

### View 5: By Type
```
Filter: Label = "design" | "implementation" | "gap"
→ See work by category
```

## 📊 Reporting & Metrics

### Velocity Tracking

**Weekly Velocity:**
```
Table view → Filter: Closed this week
Count issues × Average effort points = Velocity
Example: 3 issues × 3 points = 9 points/week
```

**Burndown:**
```
1. Roadmap view → Group by milestone
2. Track: Open issues over time
3. Goal: Trend towards 0 by milestone due date
```

### Dimension Progress

**Track per-dimension completion:**
```sql
SELECT 
  dimension,
  COUNT(*) as total,
  SUM(CASE WHEN status='Done' THEN 1 ELSE 0 END) as completed,
  ROUND(100.0 * completed / total, 1) as pct_complete
FROM issues
GROUP BY dimension
ORDER BY pct_complete ASC
```

## 🔄 Workflow Example: Issue #45 (MessageBus Implementation)

```
Day 1: Planning
├── Mobile app: Assign issue to yourself
├── Move status: Backlog → Implementation
├── Comment: "@github-copilot review MESSAGE_BUS_ARCHITECTURE.md and list implementation steps"
└── Copilot responds with 8-step plan

Day 2-3: Implementation
├── Create branch: feature/issue-45-messagebus
├── Implement MessageBus class (~800 LOC)
├── Check off tasks in issue checklist (mobile app)
└── Commit: "feat(messaging): implement MessageBus send/receive (#45)"

Day 4: Testing
├── Move status: Implementation → Testing
├── Write unit tests (80% coverage target)
├── Comment: "✅ Tests passing, coverage 87%"
└── Create PR: "Implement MessageBus class (#45)"

Day 5: Review & Merge
├── PR review with Copilot
├── Merge PR → Issue auto-moves to Done
├── Comment final metrics: "800 LOC, 87% coverage, 0 bugs"
└── Version tag: v0.2.3 released
```

## 🚀 Advanced Features

### Custom Queries

**Filter Syntax:**
```
status:Implementation assignee:@me label:dimension-7
→ My active communication protocol tasks

is:issue is:open label:critical -label:bug
→ Critical non-bug issues

is:issue closed:>2024-12-20 label:v0.2.2
→ Issues completed in last week for v0.2.2
```

### Automation Ideas

**Auto-Label by Keyword:**
```yaml
Trigger: Issue title contains "Message" or "Communication"
Action: Add label "dimension-7"
```

**Auto-Assign by Specialty:**
```yaml
Trigger: Issue label = "dimension-7"
Action: Assign to @messaging-team
```

**SLA Alerts:**
```yaml
Trigger: Issue open for 7+ days with no activity
Action: Add label "stale", comment "@assignee needs update"
```

## 📚 Resources

- **GitHub Projects Docs**: https://docs.github.com/en/issues/planning-and-tracking-with-projects
- **Projects V2 GraphQL API**: https://docs.github.com/en/graphql/reference/objects#projectv2
- **Mobile App Guide**: https://github.com/mobile
- **Copilot in Issues**: https://docs.github.com/en/copilot/github-copilot-chat/using-github-copilot-chat-in-githubcom

## ✅ Current Status for WAOOAW

**Setup Progress:**
- ✅ Repository created
- ✅ Issue templates configured
- ✅ Labels created (dimensions, types, versions, severity)
- ✅ Milestones created (Foundation, Communication Infrastructure, Week 1-2)
- ✅ Issues #42-48 created (3 closed, 4 open)
- ⏳ **Project board needs manual setup** (see steps above)

**Next Steps:**
1. Follow manual setup steps above to create project
2. Link project to WAOOAW repository
3. Add issues #42-48 to project
4. Configure Status field and organize by column
5. Enable automation workflows
6. Test mobile app access

**Estimated Time:** 10-15 minutes for complete project setup

---

**Note:** This document serves as the standard operating procedure for using GitHub Projects with WAOOAW. All team members should follow these practices for consistent project management.
