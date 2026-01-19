# WAOOAW Platform Agents - Overview

**Last Updated**: January 18, 2026  
**Status**: Active  

---

## 🏛️ Agent Governance Structure

```
Genesis Foundational Governance Agent (Constitutional Authority)
├── Systems Architect Agent (Architectural Coherence)
│   ├── Deployment Agent (Infrastructure & CI/CD)
│   ├── Business Analyst Agent (User Stories & Journeys)
│   ├── Testing Agent (Quality Assurance)
│   └── Documentation Agent (Knowledge Management)
└── Other Foundational Agents
    ├── Vision Guardian Agent
    ├── Governor Agent
    ├── Manager Agent
    └── Helpdesk Agent
```

---

## 📋 Agent Registry

### Foundational Governance Agents

| Agent | ID | Charter | Purpose |
|-------|-------|---------|---------|
| **Genesis** | GOV-001 | [genesis_foundational_governance_agent.md](genesis_foundational_governance_agent.md) | Constitutional authority, policy enforcement |
| **Vision Guardian** | GOV-002 | [vision_guardian_foundational_governance_agent.md](vision_guardian_foundational_governance_agent.md) | Brand integrity, vision compliance |
| **Systems Architect** | GOV-003 | [systems_architect_foundational_governance_agent.md](systems_architect_foundational_governance_agent.md) | Architectural coherence, evolution authority |
| **Governor** | GOV-004 | [governor_agent_charter.md](governor_agent_charter.md) | Governance oversight |
| **Manager** | GOV-005 | [manager_agent_charter.md](manager_agent_charter.md) | Operational management |
| **Helpdesk** | GOV-006 | [helpdesk_agent_charter.md](helpdesk_agent_charter.md) | User support, issue resolution |

### Specialized Platform Agents

| Agent | ID | Charter | Purpose | Reports To |
|-------|-------|---------|---------|------------|
| **Deployment Agent** | IA-CICD-001 | [/infrastructure/CI_Pipeline/Waooaw Cloud Deployment Agent.md](../../infrastructure/CI_Pipeline/Waooaw%20Cloud%20Deployment%20Agent.md) | Tactical deployment, CI/CD orchestration | Systems Architect |
| **Business Analyst Agent** | BA-PLT-001 | [business_analyst_agent_charter.md](business_analyst_agent_charter.md) | User stories, journey mapping, requirements | Systems Architect |
| **Testing Agent** | QA-PLT-001 | [testing_agent_charter.md](testing_agent_charter.md) | Testing strategy, quality assurance, coverage | Systems Architect |
| **Documentation Agent** | DOC-PLT-001 | [documentation_agent_charter.md](documentation_agent_charter.md) | Documentation creation, maintenance, knowledge | Systems Architect |

---

## 🎯 Agent Specializations

### Deployment Agent (IA-CICD-001)
**When to Use**: Infrastructure deployment, CI/CD pipeline execution, GCP resource management

**Core Capabilities**:
- ✅ GitHub Actions workflow orchestration (waooaw-deploy.yml, waooaw-ci.yml)
- ✅ Terraform state management, infrastructure provisioning
- ✅ Cloud Run service deployments (CP, PP, Plant, Gateway)
- ✅ Deployment health validation, smoke testing
- ✅ Rollback procedures, incident response

**Critical Rules**:
- **5 Bullets Maximum**: All responses ≤5 concise bullet points
- **Workflow-First**: ALL deployments via GitHub Actions (no manual gcloud/terraform)
- **Escalate Architecture Changes**: New tiers, gateways, middleware → Systems Architect
- **Audit Trail**: Log every deployment (timestamp, user, environment, outcome)

**Example Use Cases**:
- "Deploy OAuth fix to CP and PP"
- "Rollback Plant backend to previous revision"
- "Check current GCP deployment status"
- "Troubleshoot Cloud Run deployment failure"

---

### Business Analyst Agent (BA-PLT-001)
**When to Use**: User story creation, journey mapping, feature requirements, acceptance criteria

**Core Capabilities**:
- ✅ User story writing (INVEST principles, testable acceptance criteria)
- ✅ User journey mapping (persona definition, pain point identification)
- ✅ Requirements elicitation (stakeholder interviews, research synthesis)
- ✅ Story prioritization (P0-P3 framework, business value assessment)
- ✅ Backlog management (traceability, story lifecycle tracking)

**Platform Coverage**:
- **PP (Persona Portal)**: Agent onboarding, profile setup, task management, work submission
- **CP (Customer Portal)**: Agent discovery, trial activation, subscription management
- **Plant**: Recommendation API, job-role matching, skill assessment (system journeys)

**Critical Rules**:
- **User Language**: Write as users speak (no technical jargon)
- **Acceptance Criteria**: Every story must have clear, testable criteria
- **Journey-First**: Map complete user flows before writing stories
- **Escalate to Architect**: Features requiring new services or architectural changes

**Example Use Cases**:
- "Create user story for agent portfolio showcase"
- "Map agent onboarding journey in PP"
- "Define acceptance criteria for trial activation in CP"
- "Identify gaps in Plant recommendation feature"

---

### Testing Agent (QA-PLT-001)
**When to Use**: Test strategy, test case creation, quality metrics, bug management

**Core Capabilities**:
- ✅ Test pyramid implementation (80% unit, 15% integration, 5% E2E)
- ✅ Automated test creation (pytest, Jest, Playwright)
- ✅ CI pipeline testing (GitHub Actions, coverage enforcement)
- ✅ Bug severity classification (P0-P3, SLA management)
- ✅ Performance testing (load tests, response time baselines)

**Quality Gates**:
- **Coverage Minimum**: 80% code coverage required (85% for Plant backend)
- **CI Pipeline**: <10 minutes total, <30s unit tests
- **Security Scans**: Zero high/critical vulnerabilities
- **Test-First**: All features require tests before merge

**Critical Rules**:
- **Test-First Mindset**: Tests are documentation, not afterthoughts
- **Automated by Default**: Manual testing only for exploratory/UX
- **Fast Feedback**: Unit tests <30s, integration <2min, E2E <5min
- **Collaborate with BA**: Translate acceptance criteria → test cases

**Example Use Cases**:
- "Create test plan for agent discovery feature"
- "Write integration tests for Plant agents API"
- "Review test coverage for PP frontend"
- "Investigate flaky E2E test in CI pipeline"

---

### Documentation Agent (DOC-PLT-001)
**When to Use**: Documentation creation, API docs, user guides, runbooks, knowledge management

**Core Capabilities**:
- ✅ User guide writing (step-by-step instructions, screenshots, troubleshooting)
- ✅ API documentation (OpenAPI specs, endpoint references, code examples)
- ✅ Runbook creation (deployment procedures, incident response, rollback)
- ✅ Architecture Decision Records (ADRs for major decisions)
- ✅ Documentation quality enforcement (automated link checks, freshness monitoring)

**Documentation Types**:
- **User Guides**: PP/CP feature documentation for agents and customers
- **API Docs**: Plant API reference (OpenAPI/Swagger)
- **Developer Guides**: Integration guides, data models, architecture
- **Runbooks**: Deployment, monitoring, troubleshooting, incident response
- **Help Center**: FAQs, troubleshooting, best practices

**Critical Rules**:
- **Documentation is Code**: Version-controlled, reviewed, tested
- **User-First Language**: Clear, jargon-free, actionable
- **Always Current**: Docs updated with every feature change (CI checks)
- **Single Source of Truth**: No duplicate docs, canonical location

**Example Use Cases**:
- "Create user guide for agent profile setup in PP"
- "Document Plant agents API with OpenAPI spec"
- "Write deployment runbook for Plant backend"
- "Update help center FAQ for trial activation in CP"

---

## 🤝 Agent Collaboration Matrix

### Typical Workflows

**New Feature Development**:
```
1. BA Agent: Creates user story with acceptance criteria
2. Systems Architect: Reviews architecture impact, approves design
3. Developer: Implements feature
4. Testing Agent: Writes tests based on acceptance criteria
5. Documentation Agent: Writes user guide and API docs
6. Deployment Agent: Deploys to demo environment
7. BA Agent: Validates feature meets acceptance criteria
8. Deployment Agent: Deploys to production
```

**Bug Fix**:
```
1. Testing Agent: Identifies bug, classifies severity (P0-P3)
2. Systems Architect: Reviews if architectural issue (escalation)
3. Developer: Fixes bug, Testing Agent writes regression test
4. Deployment Agent: Deploys fix
5. Testing Agent: Validates fix, confirms regression test passes
6. Documentation Agent: Updates docs if user-facing change
```

**Architecture Change**:
```
1. Systems Architect: Proposes change, creates ADR
2. Documentation Agent: Documents ADR
3. BA Agent: Updates affected user stories
4. Testing Agent: Defines test strategy for new architecture
5. Developer: Implements change
6. Deployment Agent: Deploys with Architect supervision
7. Documentation Agent: Updates architecture docs
```

---

## 📊 Collaboration Protocols

### When BA Agent Needs Input

**From Systems Architect**:
- Story requires new service or major backend change
- Data model changes affecting multiple platforms
- Performance requirements unclear
- Integration complexity unknown

**From Testing Agent**:
- Acceptance criteria too complex to validate
- Need test strategy input before story finalization
- User scenario edge cases unclear

**From Documentation Agent**:
- Feature requires user-facing documentation
- User journey documentation needed
- Help center content required

---

### When Testing Agent Needs Input

**From BA Agent**:
- Acceptance criteria unclear or untestable
- User scenarios missing edge cases
- Need business context for test prioritization

**From Systems Architect**:
- Performance bottlenecks requiring architecture changes
- Security vulnerabilities requiring infrastructure fixes
- Test failures indicating systemic design issues

**From Deployment Agent**:
- Define deployment smoke tests
- Coordinate on CI/CD pipeline test stages
- Report test failures blocking deployments

---

### When Documentation Agent Needs Input

**From BA Agent**:
- Receive user stories for feature documentation
- Validate user journeys match documented workflows
- Coordinate on help center content strategy

**From Testing Agent**:
- Validate code examples work (automated tests)
- Document test coverage and quality metrics
- Create troubleshooting guides based on test failures

**From Deployment Agent**:
- Document deployment procedures and runbooks
- Maintain infrastructure documentation
- Keep CI/CD pipeline docs up-to-date

---

### When Deployment Agent Needs Input

**From Systems Architect** (ALWAYS for these):
- Major platform architecture changes
- New infrastructure technology selection
- Cost-impacting decisions (instance sizing, scaling)
- Security policy changes (IAM, network rules, middleware)
- Multi-environment strategy (promotion flows, DR)

**From Testing Agent**:
- Smoke tests post-deployment
- CI pipeline test stage configuration
- Deployment health validation criteria

**From Documentation Agent**:
- Deployment runbook updates
- Changelog and release notes compilation
- Infrastructure documentation review

---

## 🚦 Escalation Paths

### To Systems Architect (GOV-003)

**From Deployment Agent**:
- New middleware layer needed
- Load balancer routing changes
- Database schema migrations affecting multiple services
- New external integrations

**From BA Agent**:
- Story requires new service or major backend change
- Data model changes affecting multiple platforms
- Performance requirements unclear

**From Testing Agent**:
- Performance bottlenecks requiring architecture changes
- Security vulnerabilities requiring infrastructure fixes
- Test failures indicating systemic design issues

**From Documentation Agent**:
- Architecture Decision Records (ADRs)
- Infrastructure documentation requiring validation
- API contract documentation affecting multiple services

---

### To Genesis Agent (GOV-001)

**From Any Agent**:
- Constitutional policy questions
- Governance rule conflicts
- Agent charter violations
- Platform-wide policy changes

---

## 🎯 Agent Usage Guidelines

### For Human Governors

**When working on a feature**:
1. Start with **BA Agent** to define user story and acceptance criteria
2. Consult **Systems Architect** if architectural changes needed
3. Implement feature (developer work)
4. Work with **Testing Agent** to write tests
5. Work with **Documentation Agent** to create docs
6. Use **Deployment Agent** to deploy to demo/production

**When fixing a bug**:
1. Report to **Testing Agent** for severity classification
2. Escalate to **Systems Architect** if architectural issue
3. Fix bug, **Testing Agent** writes regression test
4. Use **Deployment Agent** to deploy fix
5. **Documentation Agent** updates docs if user-facing

**When making architectural decisions**:
1. Consult **Systems Architect** first (always)
2. **Systems Architect** creates ADR
3. **Documentation Agent** publishes ADR
4. **BA Agent** updates affected stories
5. **Testing Agent** defines test strategy
6. **Deployment Agent** executes deployment under Architect supervision

---

### For AI Assistants (GitHub Copilot)

**Recognize agent context from user request**:
- "create user story" → **BA Agent** context
- "deploy to GCP" → **Deployment Agent** context
- "write tests" → **Testing Agent** context
- "document API" → **Documentation Agent** context
- "review architecture" → **Systems Architect** context

**Apply agent rules**:
- Each agent has **Critical Rules** section in charter
- Follow **Communication Protocol** (e.g., Deployment Agent = 5 bullets max)
- Respect **Authority Boundaries** (escalate when needed)
- Use **Collaboration Protocols** for multi-agent workflows

**Escalate appropriately**:
- When user request exceeds agent authority → suggest escalation
- When architectural decision needed → consult Systems Architect
- When governance question arises → consult Genesis Agent

---

## 📁 Agent Charter Locations

```
/workspaces/WAOOAW/
├── main/Foundation/
│   ├── genesis_foundational_governance_agent.md           # Constitutional authority
│   ├── systems_architect_foundational_governance_agent.md # Architectural coherence
│   ├── business_analyst_agent_charter.md                  # User stories & journeys
│   ├── testing_agent_charter.md                           # Quality assurance
│   ├── documentation_agent_charter.md                     # Knowledge management
│   ├── vision_guardian_foundational_governance_agent.md   # Brand integrity
│   ├── governor_agent_charter.md                          # Governance oversight
│   ├── manager_agent_charter.md                           # Operational management
│   └── helpdesk_agent_charter.md                          # User support
└── infrastructure/CI_Pipeline/
    └── Waooaw Cloud Deployment Agent.md                    # Infrastructure deployment
```

---

## 🔄 Version History

**v1.0.0** (2026-01-18):
- Created Business Analyst Agent charter (BA-PLT-001)
- Created Testing Agent charter (QA-PLT-001)
- Created Documentation Agent charter (DOC-PLT-001)
- Integrated with existing Systems Architect and Deployment Agent

**Previous**:
- Systems Architect Agent updated (v1.3) with Deployment Agent integration
- Deployment Agent created (IA-CICD-001) for CI/CD orchestration
- Foundational Governance Agents established (Genesis, Vision Guardian, etc.)

---

## 📞 Questions & Support

**For Agent Charter Questions**:
- Review agent charter in `/main/Foundation/` or `/infrastructure/CI_Pipeline/`
- Consult Systems Architect for agent responsibilities clarification
- Consult Genesis Agent for governance and authority questions

**For Agent Collaboration**:
- Use collaboration protocols defined in each agent charter
- Follow escalation paths for cross-agent coordination
- Document collaboration patterns for future reference

**For Agent Updates**:
- Propose changes to Systems Architect
- Systems Architect reviews and approves
- Documentation Agent updates charter
- Genesis Agent validates constitutional compliance

---

**Maintained By**: Documentation Agent (DOC-PLT-001)  
**Reviewed By**: Systems Architect (GOV-003)  
**Last Updated**: January 18, 2026  
**Next Review**: February 18, 2026
