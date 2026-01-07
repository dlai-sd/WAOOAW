# Constitutional Governance Architecture - Flow

```mermaid
  flowchart LR
    classDef stage fill:#f7faff,stroke:#9ab,stroke-width:1px;
    classDef gate fill:#fff4e1,stroke:#d9a,stroke-width:1px;
    classDef end fill:#e1f5e1,stroke:#9ab;

    Start([Idea]):::stage --> Spec[Spec]:::stage --> MEWOW[ME-WoW]:::stage
    MEWOW --> Gate1{ME-WoW 100%?}:::gate
    Gate1 -->|No| MEWOW
    Gate1 -->|Yes| Genesis[Genesis Cert]:::stage

    Genesis --> Gate2{Pass?}:::gate
    Gate2 -->|Gaps| MEWOW
    Gate2 -->|OK| Arch[Arch Review]:::stage

    Arch --> Gate3{Pass?}:::gate
    Gate3 -->|Redesign| MEWOW
    Gate3 -->|OK| Ethics[Ethics Review]:::stage

    Ethics --> Gate4{Pass?}:::gate
    Gate4 -->|Escalate| Gov[Governor]:::stage
    Gate4 -->|OK| Gov

    Gov --> Gate5{Approve?}:::gate
    Gate5 -->|No| EndReject([Rejected]):::end
    Gate5 -->|Yes| Deploy[Deploy]:::stage

    Deploy --> Health{Health OK?}:::gate
    Health -->|No| Rollback([Rollback]):::end
    Health -->|Yes| Live([Live + 7-day monitor]):::end
  ```

---

**How to View:**
- **GitHub**: This diagram renders automatically when viewing on GitHub
- **VS Code**: Install 'Markdown Preview Mermaid Support' extension, then preview this file
- **PNG/SVG**: Install mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`) then run:
  ```bash
  mmdc -i diagram_flow.md -o diagram_flow.png
  ```
