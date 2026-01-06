# Constitutional Governance Architecture - Flow

```mermaid
flowchart TD
    Start([Agent Idea]) --> Stage1[Stage 1: Specification]
    Stage1 --> Stage2[Stage 2: ME-WoW Authoring]
    
    Stage2 --> Gate1{ME-WoW<br/>100% Complete?}
    Gate1 -->|No| Stage2
    Gate1 -->|Yes| Stage3[Stage 3: Genesis Certification]
    
    Stage3 --> Genesis[Genesis Reviews:<br/>- Scope defined<br/>- Decision boundaries<br/>- Approval gates<br/>- Data access<br/>- No violations]
    Genesis --> Gate2{Genesis<br/>Certified?}
    Gate2 -->|No - Gaps| Stage2
    Gate2 -->|Yes| Stage4[Stage 4: Architecture Review]
    
    Stage4 --> Architect[Systems Architect Reviews:<br/>- Explicit interfaces<br/>- Layer separation<br/>- Blast radius<br/>- Rollback architecture]
    Architect --> Gate3{Architecture<br/>Approved?}
    Gate3 -->|No - Redesign| Stage2
    Gate3 -->|Yes| Stage5[Stage 5: Ethics Review]
    
    Stage5 --> VisionGuardian[Vision Guardian Reviews:<br/>- Constitutional alignment<br/>- No deceptive patterns<br/>- Customer trust<br/>- Success pressure doctrine]
    VisionGuardian --> Gate4{Ethics<br/>Approved?}
    Gate4 -->|No - Governor Escalation| Governor[Platform Governor]
    Gate4 -->|Yes| Stage6[Stage 6: Governor Approval]
    
    Stage6 --> Governor
    Governor --> ApprovalChecks[Check:<br/>- Genesis certified<br/>- Architecture reviewed<br/>- Ethics reviewed<br/>- Precedent alignment<br/>- Business value]
    ApprovalChecks --> Gate5{Governor<br/>Approves?}
    Gate5 -->|No - Deny| End1([Agent Rejected])
    Gate5 -->|Yes| EmitSeed[Emit Precedent Seed]
    
    EmitSeed --> Stage7[Stage 7: Deployment]
    Stage7 --> Deploy[Deploy to Production]
    Deploy --> HealthCheck[Post-Deployment Health Check]
    HealthCheck --> Gate6{Health Check<br/>Pass?}
    Gate6 -->|No| Rollback[Automatic Rollback]
    Rollback --> End2([Deployment Failed])
    Gate6 -->|Yes| Monitoring[7-Day Monitoring Period]
    Monitoring --> End3([Agent Live])
    
    style Start fill:#e1f5e1
    style End1 fill:#ffe1e1
    style End2 fill:#ffe1e1
    style End3 fill:#e1f5e1
    style Genesis fill:#fff4e1
    style Architect fill:#fff4e1
    style VisionGuardian fill:#fff4e1
    style Governor fill:#ffe1f5
```

---

**How to View:**
- **GitHub**: This diagram renders automatically when viewing on GitHub
- **VS Code**: Install 'Markdown Preview Mermaid Support' extension, then preview this file
- **PNG/SVG**: Install mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`) then run:
  ```bash
  mmdc -i diagram_flow.md -o diagram_flow.png
  ```
