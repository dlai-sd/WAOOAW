# Autonomous Agent Operational Guidelines
## Rate Limits, Chunking Strategy & Escalation Matrix

**Version**: 1.0  
**Date**: January 20, 2026  
**Status**: Constitutional Guideline  
**Purpose**: Ensure all autonomous agents can handle API rate/length limits and know escalation paths

---

## 🚨 PROBLEM STATEMENT

### Issue 1: Rate/Length Limits
**Current Risk**: Autonomous agents (VG, BA, SA, Coding, Testing, Deployment) post SINGLE large comments that may:
- Exceed GitHub comment length limit (~65,535 characters)
- Trigger GitHub API rate limits (5,000 requests/hour)
- Block workflow execution if response too large

**Evidence**:
- `autonomous-vg-analysis` workflow: Posts single massive comment with full constitutional review
- `autonomous-ba-sa-trigger` workflow: Posts single comment with 5-10 user stories + wireframes
- No chunking strategy implemented

### Issue 2: Escalation Mechanism Unclear
**Current Risk**: Agents know WHEN to escalate but not HOW to escalate in GitHub workflows
- Coding Agent charter: "Escalate to Governor when encountering... " but no workflow trigger
- Testing Agent charter: "Escalate to Systems Architect if systemic issue" but no mechanism
- No standardized escalation format for autonomous workflows

---

## ✅ SOLUTION 1: CHUNKING STRATEGY FOR ALL AGENTS

### Chunking Policy (Constitutional Guideline)

**RULE**: All autonomous agents MUST divide output into chunks if:
- Single output exceeds 30,000 characters (~50% of GitHub comment limit)
- Multiple artifacts generated (e.g., 10 user stories, 10 threat assessments)

### Implementation Pattern

#### 1. Vision Guardian Chunked Output

```javascript
// In autonomous-vg-analysis workflow
const VG_ANALYSIS_SECTIONS = [
  'executive_summary',
  'constitutional_alignment',
  'business_impact_analysis',
  'gap_analysis',
  'precedent_search',
  'risk_quantification',
  'recommendation'
];

// Post each section as separate comment
for (const section of VG_ANALYSIS_SECTIONS) {
  const comment = generateVGSection(section, epicData);
  
  await github.rest.issues.createComment({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: reviewIssueNumber,
    body: `## Vision Guardian Analysis - Part ${sectionIndex + 1}/7: ${section}\n\n` + comment
  });
  
  // Rate limit protection: 500ms delay between comments
  await new Promise(resolve => setTimeout(resolve, 500));
}

// Final summary comment with score
await github.rest.issues.createComment({
  owner: context.repo.owner,
  repo: context.repo.repo,
  issue_number: reviewIssueNumber,
  body: `## ✅ Vision Guardian Analysis Complete\n\n` +
        `**Alignment Score**: ${score}/100\n` +
        `**Decision**: ${recommendation}\n` +
        `**Analysis posted in 7 parts above** ⬆️`
});
```

#### 2. Business Analyst Chunked Output

```javascript
// In autonomous-ba-sa-trigger workflow (BA section)
const USER_STORIES = generateUserStories(epicData); // 5-10 stories

// Chunk 1: Epic breakdown summary
await postComment(`## BA Analysis - Part 1/3: Epic Breakdown\n\n...`);

// Chunk 2: User stories (one comment per story)
for (const story of USER_STORIES) {
  await postComment(`## User Story #${story.id}: ${story.title}\n\n` +
                    story.acceptanceCriteria + `\n\n` +
                    story.riceScore + `\n\n` +
                    story.wireframe);
  await new Promise(resolve => setTimeout(resolve, 500)); // Rate limit protection
}

// Chunk 3: Prioritization matrix + traceability
await postComment(`## BA Analysis - Part 3/3: Prioritization & Traceability\n\n...`);
```

#### 3. Systems Architect Chunked Output

```javascript
// In autonomous-ba-sa-trigger workflow (SA section)
const ARCHITECTURE_SECTIONS = [
  'stride_threat_model',      // 10 threats
  'performance_architecture', // Caching, database
  'technical_debt_analysis',  // Debt register
  'alternatives_evaluation',  // 3+ options
  'architecture_decision_record' // Final ADR
];

// Post each section separately
for (const section of ARCHITECTURE_SECTIONS) {
  await postComment(`## SA Analysis - ${section}\n\n...`);
  await new Promise(resolve => setTimeout(resolve, 500));
}
```

### Rate Limit Protection Pattern

```javascript
// Reusable function for all workflows
async function postCommentWithRateLimit(github, context, issueNumber, body, delayMs = 500) {
  try {
    const response = await github.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: issueNumber,
      body: body
    });
    
    core.info(`Comment posted: ${response.data.id}`);
    
    // Wait before next request to avoid rate limits
    await new Promise(resolve => setTimeout(resolve, delayMs));
    
    return response;
  } catch (error) {
    // Handle rate limit errors
    if (error.status === 403 && error.message.includes('rate limit')) {
      const resetTime = error.response.headers['x-ratelimit-reset'];
      const waitMs = (resetTime * 1000) - Date.now();
      core.warning(`Rate limited. Waiting ${waitMs}ms until reset...`);
      await new Promise(resolve => setTimeout(resolve, waitMs));
      
      // Retry
      return postCommentWithRateLimit(github, context, issueNumber, body, delayMs);
    }
    
    throw error;
  }
}
```

### Character Count Check Pattern

```javascript
function shouldChunk(content, maxChars = 30000) {
  return content.length > maxChars;
}

function chunkContent(content, maxChars = 30000) {
  const chunks = [];
  let currentChunk = '';
  
  // Split by markdown headers (##)
  const sections = content.split(/(?=^## )/m);
  
  for (const section of sections) {
    if ((currentChunk + section).length > maxChars) {
      chunks.push(currentChunk);
      currentChunk = section;
    } else {
      currentChunk += section;
    }
  }
  
  if (currentChunk) chunks.push(currentChunk);
  
  return chunks;
}
```

---

## ✅ SOLUTION 2: ESCALATION MATRIX & WORKFLOW TRIGGERS

### Escalation Paths (Who Raises to Whom)

```yaml
escalation_matrix:
  vision_guardian:
    escalates_to:
      - genesis:
          when:
            - "Constitutional interpretation uncertain"
            - "Conflict between L0 principles"
            - "Precedent-setting decision required"
            - "Epic proposes constitutional amendment"
          workflow: "Create issue with label 'genesis-escalation'"
          sla: "4 hours (Genesis responds)"
          
      - governor:
          when:
            - "Score < 80 AND recommendation = REVISE/REJECT"
            - "Manual review required for risky epic"
          workflow: "Comment on VG review issue, tag @governor"
          sla: "24 hours (Governor responds)"
  
  business_analyst:
    escalates_to:
      - vision_guardian:
          when:
            - "Epic scope conflicts with brand DNA"
            - "UX design violates WCAG 2.1 AA accessibility"
            - "Prioritization conflicts with product vision"
          workflow: "Comment on epic, tag 'vision-guardian-escalation'"
          sla: "4 hours"
          
      - systems_architect:
          when:
            - "User story requires architecture change"
            - "Performance target unclear (need SA definition)"
            - "Data model ambiguity"
          workflow: "Comment on epic, tag 'architect-escalation'"
          sla: "4 hours"
          
      - governor:
          when:
            - "Scope ambiguity blocking all user stories"
            - "Customer requirement contradicts constitution"
          workflow: "Create escalation issue with '3 probable solutions' format"
          sla: "24 hours"
  
  systems_architect:
    escalates_to:
      - vision_guardian:
          when:
            - "Architecture decision has ethics implications"
            - "Security control weakens constitutional posture"
            - "Compliance requirement conflicts with L0"
          workflow: "Comment on epic, tag 'vision-guardian-escalation'"
          sla: "4 hours"
          
      - governor:
          when:
            - "Major architecture gap not in epic scope"
            - "Cost-impacting decision (infrastructure sizing)"
            - "Technical blocker (GCP API limitation)"
          workflow: "Create escalation issue with '3 probable solutions' format"
          sla: "24 hours"
          
      - platform_governor:
          when:
            - "Platform budget at 95% utilization"
            - "Infrastructure quota exceeded"
            - "Multi-customer impact decision"
          workflow: "Create issue with label 'platform-governor-escalation'"
          sla: "4 hours"
  
  coding_agent:
    escalates_to:
      - systems_architect:
          when:
            - "Missing critical component not in SA analysis"
            - "Performance target can't be met with current design"
            - "Database schema change required"
          workflow: "Comment on epic, tag 'architect-escalation'"
          sla: "4 hours"
          
      - business_analyst:
          when:
            - "User stories conflict with each other"
            - "Acceptance criteria ambiguous"
            - "Missing edge case not in stories"
          workflow: "Comment on epic, tag 'ba-escalation'"
          sla: "4 hours"
          
      - governor:
          when:
            - "Security vulnerability discovered requiring design change"
            - "Technical blocker (dependency deprecation)"
            - "Scope ambiguity blocking implementation"
          workflow: "Create escalation issue with '3 probable solutions' format"
          sla: "24 hours"
  
  testing_agent:
    escalates_to:
      - systems_architect:
          when:
            - "Systemic performance issue (all tests fail P95 target)"
            - "Infrastructure issue (test environment unreliable)"
            - "Security scan reveals critical vulnerabilities"
          workflow: "Comment on epic, tag 'architect-escalation'"
          sla: "4 hours"
          
      - coding_agent:
          when:
            - "Test coverage < 80% after multiple attempts"
            - "Unit tests missing for critical path"
            - "Code doesn't match acceptance criteria"
          workflow: "Comment on epic, tag 'coding-agent-fix-needed'"
          sla: "4 hours"
          
      - governor:
          when:
            - "Cannot validate acceptance criteria (too ambiguous)"
            - "Performance target impossible (needs scope change)"
          workflow: "Create escalation issue with '3 probable solutions' format"
          sla: "24 hours"
  
  deployment_agent:
    escalates_to:
      - systems_architect:
          when:
            - "Infrastructure architecture gap"
            - "GCP quota/API limitation"
            - "Cost exceeds budget (instance sizing)"
          workflow: "Comment on epic, tag 'architect-escalation'"
          sla: "4 hours"
          
      - governor:
          when:
            - "Severity 1 incident (customer-impacting)"
            - "Deployment rollback required"
            - "Infrastructure budget overrun"
          workflow: "Create escalation issue, page Governor immediately"
          sla: "Immediate (Severity 1)"
```

### ⚠️ ESCALATION RULES (Constitutional Requirement)

**RULE #1: ALL escalations MUST include 3 probable solutions**
- ❌ **FORBIDDEN**: "I found a problem, please help" (no solutions)
- ✅ **REQUIRED**: "I found a problem, here are 3 solutions with pros/cons/effort, I prefer Option 1 because..."

**RULE #2: Escalations have 3-attempt limit**
- Attempt 1: Agent A → Agent B (e.g., Coding → SA)
- Attempt 2: Agent B responds, Agent A re-escalates if not resolved
- Attempt 3: Final attempt between Agent A and B
- **After 3 attempts**: Auto-escalate to Governor with full history

**RULE #3: Governor decisions are FINAL**
- Governor cannot re-escalate same issue back to agents
- Governor must select one of the 3 proposed solutions OR provide alternative
- Decision becomes precedent seed if affects future epics

### Escalation Workflow Implementation

#### Escalation Issue Workflow (New)

```yaml
# .github/workflows/project-automation.yml
  autonomous-escalation-handler:
    name: Autonomous Escalation Handler
    runs-on: ubuntu-latest
    if: |
      github.event_name == 'issues' &&
      github.event.action == 'opened' &&
      contains(github.event.issue.title, '[ESCALATION]')
    permissions:
      issues: write
    steps:
      - name: Validate Escalation Format
        uses: actions/github-script@v7
        with:
          script: |
            const issue = context.payload.issue;
            const body = issue.body || '';
            
            // VALIDATE: Must have 3 probable solutions
            const option1 = body.includes('#### Option 1:');
            const option2 = body.includes('#### Option 2:');
            const option3 = body.includes('#### Option 3:');
            const hasRecommendation = body.includes('### Recommendation');
            
            if (!option1 || !option2 || !option3 || !hasRecommendation) {
              // REJECT escalation - missing solutions
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                body: `❌ **ESCALATION REJECTED: Missing Required Format**\n\n` +
                      `All escalations MUST include:\n` +
                      `- ✅ Option 1 with pros/cons/effort/risk\n` +
                      `- ✅ Option 2 with pros/cons/effort/risk\n` +
                      `- ✅ Option 3 with pros/cons/effort/risk\n` +
                      `- ✅ Recommendation with rationale\n\n` +
                      `Please update this issue body to include 3 probable solutions.\n\n` +
                      `**Constitutional Requirement**: AUTONOMOUS_AGENT_OPERATIONAL_GUIDELINES.md Rule #1`
              });
              
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                labels: ['escalation-invalid']
              });
              
              return;
            }
            
            core.info('Escalation format validated: 3 solutions present ✅');

      - name: Track Escalation Attempts
        uses: actions/github-script@v7
        with:
          script: |
            const issue = context.payload.issue;
            const body = issue.body || '';
            
            // Extract epic number
            const epicMatch = body.match(/\*\*Epic\*\*:\s*#(\d+)/);
            const epicNumber = epicMatch ? epicMatch[1] : null;
            
            if (!epicNumber) {
              core.warning('No epic number found in escalation');
              return;
            }
            
            // Check escalation history for this epic
            const allIssues = await github.paginate(github.rest.issues.listForRepo, {
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'all',
              labels: 'escalation'
            }); (MANDATORY - All 3 Required)

#### Option 1: [Solution Name] ⭐ PREFERRED
**Approach**: [How it works in 2-3 sentences]
**Pros**: 
- [Specific benefit 1]
- [Specific benefit 2]
**Cons**: 
- [Specific drawback 1]
- [Specific drawback 2]
**Effort**: [Low (< 4 hours) | Medium (4-16 hours) | High (> 16 hours)]
**Risk**: [Low | Medium | High]
**ETA**: [Specific time estimate]
**Cost Impact**: [None | Low (< ₹1000) | Medium (₹1000-5000) | High (> ₹5000)]

#### Option 2: [Alternative Solution]
**Approach**: [How it works in 2-3 sentences]
**Pros**: 
- [Specific benefit 1]
- [Specific benefit 2]
**Cons**: 
- [Specific drawback 1]
- [Specific drawback 2]
**Effort**: [Low | Medium | High]
**Risk**: [Low | Medium | High]
**ETA**: [Specific time estimate]
**Cost Impact**: [None | Low | Medium | High]

#### Option 3: [Fallback Solution]
**Approach**: [How it works in 2-3 sentences]
**Pros**: 
- [Specific benefit 1]
- [Specific benefit 2]
**Cons**: 
- [Specific drawback 1]
- [Specific drawback 2]
**Effort**: [Low | Medium | High]
**Risk**: [Low | Medium | High]
**ETA**: [Specific time estimate]
**Cost Impact**: [None | Low | Medium | High]

### Recommendation (MANDATORY)
I prefer **Option [1/2/3]** because:
1. [Specific reason 1 tied to WAOOAW constitution/goals] ✅

- [ ] Update `autonomous-vg-analysis` workflow
  - [ ] Add chunking logic for 7 sections
  - [ ] Add rate limit protection (500ms delays)
  - [ ] Add character count check
  - [ ] Test with long epic (>50k characters)

- [ ] Update `autonomous-ba-sa-trigger` workflow
  - [ ] BA: Chunk user stories (1 per comment)
  - [ ] BA: Separate prioritization matrix
  - [ ] SA: Chunk STRIDE threats, performance, ADR
  - [ ] Test with 10 user stories

- [ ] Update `trigger-coding-agent` workflow
  - [ ] Check if agent prompt exceeds 30k chars
  - [ ] Chunk implementation phases if needed

- [ ] Update `trigger-deployment-agent` workflow
  - [ ] Chunk infrastructure code sections

### Phase 2: Add Escalation Workflows (High Priority) ✅

- [ ] Create `autonomous-escalation-handler` workflow
  - [ ] **VALIDATE**: Check for 3 probable solutions (MANDATORY)
  - [ ] **REJECT**: If missing solutions format, reject escalation with error message
  - [ ] **TRACK**: Count escalation attempts (1, 2, or 3)
  - [ ] **AUTO-ESCALATE**: After 3 attempts, route to Governor for FINAL decision
  - [ ] **ROUTE**: Parse escalation target from issue body
  - [ ] **NOTIFY**: Notify epic with escalation link and attempt number
  - [ ] **SLA TRACKING**: Track response time (4 hours agents, 24 hours Governor)

- [ ] Add escalation validation rules
  - [ ] Validate "3 probable solutions" format
  - [ ] Validate "Recommendation" section present
  - [ ] Validate cost impact specified
  - [ ] Reject invalid escalations with helpful error message

- [ ] Add 3-attempt tracking
  - [ ] Query past escalations for same epic + problem
  - [ ] Display attempt counter (1/3, 2/3, 3/3)
  - [ ] After 3 attempts: Auto-add Governor label
  - [ ] After 3 attempts: Post history of all attempts
  - [ ] After 3 attempts: Notify Governor decision is FINAL

- [ ] Update agent charters with escalation rules
  - [ ] VG charter: Add "3 solutions mandatory" rule
  - [ ] BA charter: Add "3 solutions mandatory" rule
  - [ ] SA charter: Add "3 solutions mandatory" rule
  - [ ] Coding charter: Already has format ✅, add 3-attempt rule
  - [ ] Testing charter: Add "3 solutions mandatory" rule
  - [ ] Deployment charter: Add "3 solutions mandatory" rule

### Phase 3: Testing & Validation

- [ ] Test VG chunked output with synthetic epic
- [ ] Test BA/SA chunked output with 10 user stories
- [ ] Test escalation workflow (Coding → SA) - Valid format
- [ ] Test escalation workflow - **Invalid format (no solutions)** → Should reject
- [ ] Test escalation workflow - **3 attempts** → Should auto-escalate to Governor
- [ **100% of escalations include 3 probable solutions** (MANDATORY validation)
- ✅ **Zero escalation loops > 3 attempts** (auto-escalate to Governor)
- ✅ **100% of Governor decisions are FINAL** (no further escalation)
- ✅ 90%+ escalations resolved within SLA (4 hours for agents, 24 hours for Governor)
- ✅ Zero escalations lost (no mechanism → workflow triggers)
- ✅ Zero "help me" escalations (all must have solutions)

**Quality Metrics**:
- ✅ Average escalation attempts before resolution: Target < 1.5
- ✅ Escalations reaching Governor (3 attempts): Target < 10%
- ✅ Escalation format validation pass rate: Target 100%

When Governor provides final decision after 3 attempts:

```markdown
## 🏛️ GOVERNOR FINAL DECISION (Binding)

**Decision**: [APPROVE Option N | PROPOSE Alternative]

**Selected Option**: Option [1/2/3] OR [Alternative description]

**Rationale**: 
[Governor's reasoning for final decision]

**Constitutional Impact**:
- Precedent Seed: [Yes/No] - [If yes, describe precedent]
- Affects Future Epics: [Yes/No]

**Implementation Directive**:
[Clear directive to agents - no further escalation allowed]

**Decision is FINAL**: No further escalation on this issue permitted.

---
**Audit**: This decision becomes precedent seed #PREC-GOV-[ID.title} (${e.state})`
                      ).join('\n') + '\n\n' +
                      `Per AUTONOMOUS_AGENT_OPERATIONAL_GUIDELINES.md Rule #2:\n` +
                      `After 3 attempts, escalation routes to Governor for FINAL decision.\n\n` +
                      `@${context.repo.owner} **Governor review required.**\n\n` +
                      `Governor: Please select one of the 3 proposed solutions or provide alternative.\n` +
                      `Your decision is FINAL and becomes precedent seed.`
              });
              
              // Change label to Governor escalation
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                labels: ['needs-governor-review', 'escalation-final-attempt']
              });
              
              // Notify epic
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: parseInt(epicNumber),
                body: `🚨🚨🚨 **ESCALATION TO GOVERNOR (Final Attempt)**\n\n` +
                      `Issue #${issue.number} has reached 3 escalation attempts.\n` +
                      `Governor decision required to break deadlock.\n\n` +
                      `Epic work paused until Governor provides final decision.`
              });
              
              return;
            }

      - name: Route Escalation to Target Agent
        uses: actions/github-script@v7
        with:
          script: |
            const issue = context.payload.issue;
            const title = issue.title;
            const body = issue.body || '';
            
            // Skip if already escalated to Governor (3 attempts)
            const labels = issue.labels.map(l => l.name);
            if (labels.includes('needs-governor-review')) {
              core.info('Already escalated to Governor, skipping agent routing');
              return;
            }
            
            // Extract epic number
            const epicMatch = body.match(/\*\*Epic\*\*:\s*#(\d+)/);
            const epicNumber = epicMatch ? epicMatch[1] : null;
            
            // Determine escalation target from issue body
            let targetAgent = null;
            let targetLabel = null;
            
            if (body.includes('Escalate to: Systems Architect')) {
              targetAgent = 'Systems Architect';
              targetLabel = 'architect-escalation';
            } else if (body.includes('Escalate to: Vision Guardian')) {
              targetAgent = 'Vision Guardian';
              targetLabel = 'vision-guardian-escalation';
            } else if (body.includes('Escalate to: Business Analyst')) {
              targetAgent = 'Business Analyst';
              targetLabel = 'ba-escalation';
            } else if (body.includes('Escalate to: Governor')) {
              targetAgent = 'Governor';
              targetLabel = 'needs-governor-review';
            } else if (body.includes('Escalate to: Platform Governor')) {
              targetAgent = 'Platform Governor';
              targetLabel = 'platform-governor-escalation';
            }
            
            if (targetAgent && targetLabel) {
              // Add label
              await github.rest.issues.addLabels({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: issue.number,
                labels: [targetLabel, 'escalation']
              });
              
              // Notify on epic if epic number found
              if (epicNumber) {
                await github.rest.issues.createComment({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: parseInt(epicNumber),
                  body: `🚨 **Escalation Raised**: ${title}\n\n` +
                        `**Target**: ${targetAgent}\n` +
                        `**Issue**: #${issue.number}\n\n` +
                        `Awaiting ${targetAgent} response (SLA: 4 hours)...`
                });
              }
              
              core.info(`Escalation routed to ${targetAgent}`);
            }
```

#### Standard Escalation Comment Format

All agents MUST use this format when escalating via comment:

```markdown
## 🚨 ESCALATION: [Agent Name] → [Target Agent]

**Epic**: #[N]
**From Agent**: [VG | BA | SA | Coding | Testing | Deployment]
**To Agent**: [Target Agent Name]
**Severity**: [Low | Medium | High | Critical]

### Problem Statement
[2-3 sentences describing the blocker/gap]

### Context
- **Current Phase**: [VG Analysis | BA Breakdown | SA Design | Implementation | Testing | Deployment]
- **Affected Artifacts**: [User stories, ADRs, code files]
- **Impact**: [What breaks if not addressed]
- **Discovery Point**: [When/how discovered]

### Probable Solutions

#### Option 1: [Solution Name] ⭐ PREFERRED
**Approach**: [How it works]
**Pros**: [Benefits list]
**Cons**: [Drawbacks list]
**Effort**: [Low | Medium | High]
**Risk**: [Low | Medium | High]
**ETA**: [Time estimate]

#### Option 2: [Alternative Solution]
**Approach**: [How it works]
**Pros**: [Benefits]
**Cons**: [Drawbacks]
**Effort**: [Estimate]
**Risk**: [Level]
**ETA**: [Time]

#### Option 3: [Fallback Solution]
**Approach**: [How it works]
**Pros**: [Benefits]
**Cons**: [Drawbacks]
**Effort**: [Estimate]
**Risk**: [Level]
**ETA**: [Time]

### Recommendation
I prefer **Option [N]** because [specific rationale tied to WAOOAW constitution/goals].

### Required Decision
Please respond with:
- Selected option (1, 2, or 3)
- OR alternative guidance
- Within SLA: [4 hours | 24 hours]

---
**Labels**: escalation, [target-agent-label], epic-[N]
```

---

## 📋 IMPLEMENTATION CHECKLIST

### Phase 1: Update All Agent Workflows with Chunking (Immediate)

- [ ] Update `autonomous-vg-analysis` workflow
  - [ ] Add chunking logic for 7 sections
  - [ ] Add rate limit protection (500ms delays)
  - [ ] Add character count check
  - [ ] Test with long epic (>50k characters)

- [ ] Update `autonomous-ba-sa-trigger` workflow
  - [ ] BA: Chunk user stories (1 per comment)
  - [ ] BA: Separate prioritization matrix
  - [ ] SA: Chunk STRIDE threats, performance, ADR
  - [ ] Test with 10 user stories

- [ ] Update `trigger-coding-agent` workflow
  - [ ] Check if agent prompt exceeds 30k chars
  - [ ] Chunk implementation phases if needed

- [ ] Update `trigger-deployment-agent` workflow
  - [ ] Chunk infrastructure code sections

### Phase 2: Add Escalation Workflows (High Priority)

- [ ] Create `autonomous-escalation-handler` workflow
  - [ ] Parse escalation target from issue body
  - [ ] Route to correct agent with label
  - [ ] Notify epic with escalation link
  - [ ] Track escalation SLA

- [ ] Add escalation comment trigger
  - [ ] Detect escalation keywords in comments
  - [ ] Create escalation issue automatically
  - [ ] Tag target agent

- [ ] Update agent charters with workflow examples
  - [ ] VG charter: Add workflow escalation section
  - [ ] BA charter: Add workflow escalation section
  - [ ] SA charter: Add workflow escalation section
  - [ ] Coding charter: Already has format, add workflow trigger
  - [ ] Testing charter: Add workflow escalation section
  - [ ] Deployment charter: Add workflow escalation section

### Phase 3: Testing & Validation

- [ ] Test VG chunked output with synthetic epic
- [ ] Test BA/SA chunked output with 10 user stories
- [ ] Test escalation workflow (Coding → SA)
- [ ] Test escalation workflow (SA → Governor)
- [ ] Validate rate limit protection (post 20 comments in sequence)

---

## 🎯 SUCCESS METRICS

**Chunking Success**:
- ✅ Zero comment length limit errors (currently at risk)
- ✅ Zero rate limit errors in workflows
- ✅ All agent outputs readable (not truncated)

**Escalation Success**:
- ✅ 100% of escalations follow standard format
- ✅ 90%+ escalations resolved within SLA (4 hours for agents, 24 hours for Governor)
- ✅ Zero escalations lost (no mechanism → workflow triggers)

---

## 📚 REFERENCES

**Existing Escalation Formats** (to preserve):
- Coding Agent Charter (lines 310-370): `[ESCALATION]` issue format with 3 probable solutions ✅
- Deployment Agent Enhanced Capabilities: Same escalation format as Coding Agent ✅
- Testing Agent Charter: Escalates to SA but no format specified (needs standardization)

**Constitutional Authority**:
- Foundation.md: L0 principles for escalation boundaries
- Governor Agent Charter (lines 374-410): Escalation to Platform Governor process
- Genesis Agent Charter (lines 263-290): Precedent seed deferral escalation

---

**Status**: Ready for implementation  
**Next Steps**: 
1. Implement chunking in all 3 workflows (VG, BA/SA, Coding trigger)
2. Add escalation handler workflow
3. Test with new epic after Epic #172 deleted
4. Update agent charters with workflow examples
