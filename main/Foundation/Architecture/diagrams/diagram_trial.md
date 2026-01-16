# Constitutional Governance Architecture - Trial

```mermaid
flowchart LR
    Agent[Agent in<br/>trial_support_only mode]
    
    Agent -->|AI Request| AIExplorer[AI Explorer]
    AIExplorer --> AICheck{Check Manifest:<br/>AI Prompts Allowed?}
    AICheck -->|No| AIBlock[❌ BLOCKED:<br/>No AI in trial mode]
    AICheck -->|Yes + Synthetic Data| AIAllow[✅ Execute with<br/>Synthetic Data]
    
    Agent -->|Integration Request| Connector[Outside World Connector]
    Connector --> ConnCheck{Check Manifest:<br/>Integration Allowed?}
    ConnCheck -->|No| ConnBlock[❌ BLOCKED:<br/>No production integrations]
    ConnCheck -->|Yes + Sandbox| ConnAllow[✅ Route to<br/>Sandbox Environment]
    
    Agent -->|Communication| MsgBus[Message Bus]
    MsgBus --> CommCheck{Check Policy:<br/>Receiver Allowed?}
    CommCheck -->|Customer/External| CommBlock[❌ BLOCKED:<br/>Trial can't contact customers]
    CommCheck -->|Help Desk/Governor| CommAllow[✅ Communication<br/>Allowed]
    
    Agent -->|Data Access| DataLayer[Data Layer]
    DataLayer --> DataCheck{Check Manifest:<br/>Data Scope?}
    DataCheck -->|Production Data| DataBlock[❌ BLOCKED:<br/>READ only, no COMPUTE]
    DataCheck -->|Synthetic Data| DataAllow[✅ READ allowed<br/>COMPUTE blocked]
    
    AIAllow --> Audit[System Audit Account]
    ConnAllow --> Audit
    CommAllow --> Audit
    DataAllow --> Audit
    AIBlock --> Audit
    ConnBlock --> Audit
    CommBlock --> Audit
    DataBlock --> Audit
    
    Audit --> Guardian[Vision Guardian]
    Guardian -.->|Monitors| AIExplorer
    Guardian -.->|Monitors| Connector
    Guardian -.->|Monitors| MsgBus
    Guardian -.->|Monitors| DataLayer
    
    style Agent fill:#fff4e1
    style AIBlock fill:#ffe1e1
    style ConnBlock fill:#ffe1e1
    style CommBlock fill:#ffe1e1
    style DataBlock fill:#ffe1e1
    style AIAllow fill:#e1f5e1
    style ConnAllow fill:#e1f5e1
    style CommAllow fill:#e1f5e1
    style DataAllow fill:#e1f5e1
    style Audit fill:#e1f5ff
    style Guardian fill:#ffe1f5
```

---

**How to View:**
- **GitHub**: This diagram renders automatically when viewing on GitHub
- **VS Code**: Install 'Markdown Preview Mermaid Support' extension, then preview this file
- **PNG/SVG**: Install mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`) then run:
  ```bash
  mmdc -i diagram_trial.md -o diagram_trial.png
  ```
