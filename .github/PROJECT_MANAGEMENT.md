# GitHub Project Management for WAOOAW

This directory contains issue templates and automation workflows for managing WAOOAW platform development using GitHub's project management features.

## 📋 Issue Templates

### 1. Epic Template (`epic.yml`)
**Purpose**: High-level business initiatives spanning multiple stories  
**Owner**: Vision Guardian Agent → Genesis → Systems Architect  
**Usage**: `New Issue` → Select "Epic" template

**Example**:
```
Title: [EPIC] Message Queue Infrastructure
Goal: Implement message queue for decoupled event-driven architecture
Platforms: PP, CP, Plant
Priority: P0 (Critical)
Owner: Vision Guardian Agent
```

### 2. User Story Template (`story.yml`)
**Purpose**: User-facing features following INVEST principles  
**Owner**: Business Analyst Agent creates → Developer implements → Testing Agent validates  
**Usage**: `New Issue` → Select "User Story" template

**Example**:
```
Title: [STORY] Agent receives real-time task notifications
Platform: PP (Persona Portal)
Epic: #150
Story: As a Content Marketing Agent, I want to receive real-time notifications...
Acceptance Criteria:
  - [ ] Notification received within 5 seconds
  - [ ] Notification queued if offline
Priority: P1 (High)
Story Points: 5
```

### 3. Technical Task Template (`task.yml`)
**Purpose**: Technical work without direct user-facing value  
**Owner**: Systems Architect / Deployment Agent / Testing Agent  
**Usage**: `New Issue` → Select "Technical Task" template

**Example**:
```
Title: [TASK] Deploy RabbitMQ on Cloud Run
Task Type: Infrastructure
Epic: #150
Description: Create terraform stack for RabbitMQ with VPC connector
Priority: P0 (Blocking)
Owner: Deployment Agent
```

### 4. Bug Report Template (`bug.yml`)
**Purpose**: Defects, errors, unexpected behavior  
**Owner**: Testing Agent classifies → Developer fixes → Testing Agent validates  
**Usage**: `New Issue` → Select "Bug Report" template

**Example**:
```
Title: [BUG] OAuth login fails with missing client_id
Platform: CP (Customer Portal)
Environment: Demo
Severity: P0 (Critical)
Impact: 100% of CP signups blocked
```

---

## 🤖 Automated Workflows

### `project-automation.yml`

**Triggers**:
- Issue opened
- Issue labeled
- Issue closed
- PR opened
- PR merged

**Automation Features**:

1. **Auto-Triage on Issue Creation**
   - Adds issue to project board
   - Assigns agent owner based on label:
     - `epic` → Vision Guardian Agent
     - `story` → Business Analyst Agent
     - `task` → Systems Architect / Deployment / Testing Agent (based on type)
     - `bug` → Testing Agent

2. **Status Updates**
   - `in-progress` label → Comments "🚀 Status Update: In Progress"
   - `in-review` label → Comments "👀 Status Update: In Review"
   - Issue closed → Adds `done` label, comments "✅ Status Update: Done"

3. **PR-Issue Linking**
   - PR opened with "Closes #123" → Auto-links to issue, adds `in-review` label
   - PR merged → Auto-closes linked issues, comments with deployment status

4. **Project Board Movement**
   - Issues automatically move between columns based on labels/status

---

## 🎯 Workflow Example: Message Queue Epic

### Step 1: Create Epic (You)
```
New Issue → Epic template
Title: [EPIC] Message Queue Infrastructure
Goal: Implement async event-driven architecture
Assign: Vision Guardian Agent
Submit
```

### Step 2: Vision Guardian Agent Response (in issue comments)
```
✅ Vision alignment confirmed
✅ Genesis approval: async patterns allowed
✅ Escalated to Systems Architect for design

Created:
- GitHub Project: "Epic: Message Queue"
- Wiki page: /wiki/Epics/Message-Queue-Infrastructure
- Feature branch: feature/message-queue-infrastructure
```

### Step 3: Systems Architect Breakdown (creates issues)
```
Created Issues:
- #151 [ADR] Message Queue Architecture
- #152 [STORY] Base Agent publishes events
- #153 [STORY] Error Handler consumes failures
- #154 [TASK] Deploy RabbitMQ on Cloud Run
- #155 [TASK] Create MQ client library
... (15 more issues)

All issues added to Project board, Backlog column
```

### Step 4: Business Analyst Agent (creates stories)
```
For each story (#152, #153, etc.):
- Created /docs/plant/message-queue/user-stories/base-agent-publish.md
- Defined acceptance criteria
- Prioritized (P0/P1/P2)
- Assigned story points
- Moved to Ready column
```

### Step 5: Developer Implementation
```
1. Create branch: feature/mq-base-agent
2. Implement feature
3. Write tests
4. Create PR: "Closes #152"
5. Automation: Adds in-review label to #152
```

### Step 6: Testing Agent Validation
```
1. Reviews PR tests
2. Validates acceptance criteria
3. Approves PR
```

### Step 7: Merge & Close
```
1. PR merged to main
2. Automation: Closes issue #152
3. Automation: Comments "✅ Closed via PR #XYZ"
4. Automation: Moves to Done column
```

---

## 📊 GitHub Insights Usage

**Track Progress**:
- Go to `Insights` → `Pulse` for weekly activity
- Track issues closed per week (velocity)
- Track cycle time (issue open → done)

**Agent Productivity**:
- `Insights` → `Contributors` shows agent activity
- Filter by agent labels to see workload distribution

**Project Board Metrics**:
- Issues in each column (Backlog, Ready, In Progress, Review, Done)
- Average time in each column
- Blocked issues

---

## 🗂️ Project Board Setup

**Columns**:
1. **Backlog**: Issues created but not ready for work
2. **Ready**: Issues refined, acceptance criteria clear, ready to implement
3. **In Progress**: Actively being worked on (add `in-progress` label)
4. **Review**: PR created, awaiting validation (add `in-review` label)
5. **Done**: Issue closed, work deployed

**Custom Fields** (optional):
- `Agent Owner`: Vision Guardian / Systems Architect / BA / Testing / Deployment / Documentation
- `Component`: base-agent / error-handling / pp / cp / plant / gateway / infrastructure
- `Story Points`: 1, 2, 3, 5, 8, 13
- `Priority`: P0, P1, P2, P3

---

## 📚 Wiki Structure

**Create Wiki Pages**:
1. `Home`: Overview, navigation, agent charter links
2. `Epics/`: One page per epic with vision, architecture, progress
3. `ADRs/`: Architecture Decision Records for major decisions
4. `Runbooks/`: Deployment, incident response, troubleshooting
5. `FAQs/`: Common questions, agent responsibilities, processes

**Example Wiki Pages**:
```
/wiki/
├── Home
├── Epics/
│   └── Message-Queue-Infrastructure
├── ADRs/
│   └── ADR-001-Message-Queue-Architecture
├── Runbooks/
│   ├── Deployment-Process
│   ├── Incident-Response
│   └── Agent-Escalation-Paths
└── FAQs/
    ├── GitHub-Project-Management
    ├── Agent-Responsibilities
    └── Issue-Template-Usage
```

---

## 🔧 Configuration

### Required GitHub Variables

Set in `Settings` → `Secrets and variables` → `Actions` → `Variables`:

```
PROJECT_URL: https://github.com/orgs/dlai-sd/projects/1
(or https://github.com/users/dlai-sd/projects/1 for personal repo)
```

### Required GitHub Secrets

(None currently - uses default GITHUB_TOKEN)

---

## 🚀 Next Steps

1. **Create First Project Board**:
   - Go to `Projects` → `New project`
   - Select "Table" view
   - Add columns: Backlog, Ready, In Progress, Review, Done
   - Save project URL to GitHub variable

2. **Create First Epic**:
   - `New Issue` → Select "Epic" template
   - Fill in business goal, scope, success metrics
   - Assign to Vision Guardian Agent
   - Submit

3. **Enable Wiki**:
   - `Settings` → `Features` → Check "Wikis"
   - Create Home page with navigation structure

4. **Monitor Automation**:
   - Go to `Actions` tab
   - Watch `project-automation.yml` workflow runs
   - Check issue comments for automation feedback

---

## 📖 References

- [Agent Charters](/main/Foundation/AGENTS_OVERVIEW.md)
- [Business Analyst Charter](/main/Foundation/business_analyst_agent_charter.md)
- [Testing Agent Charter](/main/Foundation/testing_agent_charter.md)
- [Documentation Agent Charter](/main/Foundation/documentation_agent_charter.md)
- [Deployment Agent Charter](/infrastructure/CI_Pipeline/Waooaw%20Cloud%20Deployment%20Agent.md)
- [Systems Architect Charter](/main/Foundation/systems_architect_foundational_governance_agent.md)

---

**Maintained By**: Documentation Agent (DOC-PLT-001)  
**Last Updated**: January 18, 2026  
**Status**: ✅ Active on feature/github-project-management branch
