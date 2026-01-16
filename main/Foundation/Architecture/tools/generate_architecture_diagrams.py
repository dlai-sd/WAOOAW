#!/usr/bin/env python3
"""
Constitutional Governance Architecture Diagram Generator

This script generates Mermaid diagrams for the constitutional governance platform.
Supports multiple diagram types:
- Mind map (hierarchical overview)
- Flow diagram (agent creation pipeline)
- Graph (component dependencies)

Usage:
    python3 generate_architecture_diagrams.py --type mindmap
    python3 generate_architecture_diagrams.py --type flow
    python3 generate_architecture_diagrams.py --type graph
    python3 generate_architecture_diagrams.py --all

To render:
    - GitHub: Just commit .md files, they render automatically
    - VS Code: Install "Markdown Preview Mermaid Support" extension
    - CLI: npm install -g @mermaid-js/mermaid-cli && mmdc -i diagram.md -o diagram.png
"""

import argparse
from typing import List


class DiagramGenerator:
    """Generate Mermaid diagrams for constitutional governance architecture"""
    
    def generate_mindmap(self) -> str:
        """Generate hierarchical mind map of all components"""
        return """```mermaid
mindmap
  root((WAOOAW Platform))
    Constitutional Foundation
      Modes & Bright Lines
      Approvals & Amendments
      Trial Support Only
    Governance Agents
      Genesis
      Systems Architect
      Vision Guardian
      Governor
    Platform Components
      AI Explorer
      Outside World Connector
      System Audit
      Unified Manifest
    Orchestration
      Framework Pattern
      Creation | Servicing | Assurance
    Reusable Components
      Certification & Approval
      Ops, Rollback, Health, Versioning, Audit
    Communication
      Policy
      Message Bus
```"""
    
    def generate_agent_creation_flow(self) -> str:
        """Generate flow diagram for agent creation pipeline"""
        return """```mermaid
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
  ```"""
    
    def generate_component_graph(self) -> str:
        """Generate dependency graph of components"""
        return """```mermaid
graph TB
    subgraph Constitutional_Foundation[Constitutional Foundation]
        CE[constitution_engine]
        GP[governance_protocols]
    end
    
    subgraph Governance_Agents[Foundational Governance Agents]
        Genesis[Genesis]
        Architect[Systems Architect]
        Guardian[Vision Guardian]
        Governor[Platform Governor]
    end
    
    subgraph Platform_Components[Foundational Platform Components]
        AI[AI Explorer]
        Connector[Outside World Connector]
        Audit[System Audit Account]
        Manifest[Unified Manifest]
    end
    
    subgraph Orchestration[Orchestration Layer]
        Framework[orchestration_framework]
        Creation[agent_creation]
        Servicing[agent_servicing]
        Operations[agent_operation_assurance]
    end
    
    subgraph Components[Reusable Components - 8 total]
        GenGate[genesis_certification_gate]
        GovApproval[governor_approval_workflow]
        ArchReview[architecture_review_pattern]
        EthicsReview[ethics_review_pattern]
        Health[health_check_protocol]
        Rollback[rollback_procedure]
        Versioning[versioning_scheme]
        AuditLog[audit_logging_requirements]
    end
    
    subgraph Communication[Communication Infrastructure]
        CommPolicy[communication_collaboration_policy]
        MsgBus[message_bus_framework]
    end
    
    %% Constitutional Foundation influences everything
    CE -.-> Genesis
    CE -.-> Architect
    CE -.-> Guardian
    CE -.-> Governor
    CE -.-> AI
    CE -.-> Connector
    
    GP --> Governor
    GP --> Genesis
    
    %% Governance Agents use Platform Components
    Genesis --> Manifest
    Architect --> Audit
    Guardian --> Audit
    
    %% Platform Components depend on each other
    AI --> Audit
    AI --> Manifest
    Connector --> Audit
    Connector --> Manifest
    Audit -.->|monitors| AI
    Audit -.->|monitors| Connector
    
    %% Orchestrations reference Framework
    Framework --> Creation
    Framework --> Servicing
    Framework --> Operations
    
    %% Orchestrations use Components
    Creation --> GenGate
    Creation --> GovApproval
    Creation --> ArchReview
    Creation --> EthicsReview
    Creation --> Rollback
    Creation --> Health
    Creation --> Versioning
    Creation --> AuditLog
    
    Servicing --> GenGate
    Servicing --> GovApproval
    Servicing --> Rollback
    Servicing --> Versioning
    
    Operations --> Health
    Operations --> GovApproval
    Operations --> AuditLog
    
    %% Orchestrations use Platform Components
    Creation --> AI
    Creation --> Connector
    Servicing --> Manifest
    Operations --> Manifest
    
    %% Communication Infrastructure underlies everything
    MsgBus -.-> Genesis
    MsgBus -.-> Architect
    MsgBus -.-> Guardian
    MsgBus -.-> AI
    MsgBus -.-> Connector
    CommPolicy -.-> MsgBus
    
    %% Governance Agents oversee Orchestrations
    Genesis -.->|certifies| Creation
    Genesis -.->|classifies| Servicing
    Architect -.->|reviews| Creation
    Guardian -.->|audits| Operations
    Governor -.->|approves| Creation
    
    style CE fill:#ffe1e1
    style GP fill:#ffe1e1
    style Genesis fill:#fff4e1
    style Architect fill:#fff4e1
    style Guardian fill:#fff4e1
    style Governor fill:#ffe1f5
    style Audit fill:#e1f5e1
    style Manifest fill:#e1f5e1
```"""
    
    def generate_trial_mode_enforcement(self) -> str:
        """Generate diagram showing trial mode enforcement across components"""
        return """```mermaid
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
```"""
    
    def save_diagram(self, diagram_type: str, content: str):
        """Save diagram to file"""
        filename = f"/workspaces/WAOOAW/main/Foundation/diagram_{diagram_type}.md"
        with open(filename, 'w') as f:
            f.write(f"# Constitutional Governance Architecture - {diagram_type.title()}\n\n")
            f.write(content)
            f.write("\n\n---\n\n")
            f.write("**How to View:**\n")
            f.write("- **GitHub**: This diagram renders automatically when viewing on GitHub\n")
            f.write("- **VS Code**: Install 'Markdown Preview Mermaid Support' extension, then preview this file\n")
            f.write("- **PNG/SVG**: Install mermaid-cli (`npm install -g @mermaid-js/mermaid-cli`) then run:\n")
            f.write(f"  ```bash\n  mmdc -i diagram_{diagram_type}.md -o diagram_{diagram_type}.png\n  ```\n")
        print(f"✅ Generated: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mermaid architecture diagrams for Constitutional Governance Platform"
    )
    parser.add_argument(
        '--type',
        choices=['mindmap', 'flow', 'graph', 'trial'],
        help='Type of diagram to generate'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate all diagram types'
    )
    
    args = parser.parse_args()
    
    generator = DiagramGenerator()
    
    if args.all or not args.type:
        print("Generating all diagrams...\n")
        generator.save_diagram('mindmap', generator.generate_mindmap())
        generator.save_diagram('flow', generator.generate_agent_creation_flow())
        generator.save_diagram('graph', generator.generate_component_graph())
        generator.save_diagram('trial', generator.generate_trial_mode_enforcement())
        print("\n✅ All diagrams generated successfully!")
    else:
        print(f"Generating {args.type} diagram...\n")
        if args.type == 'mindmap':
            generator.save_diagram('mindmap', generator.generate_mindmap())
        elif args.type == 'flow':
            generator.save_diagram('flow', generator.generate_agent_creation_flow())
        elif args.type == 'graph':
            generator.save_diagram('graph', generator.generate_component_graph())
        elif args.type == 'trial':
            generator.save_diagram('trial', generator.generate_trial_mode_enforcement())
        print(f"\n✅ {args.type.title()} diagram generated successfully!")
    
    print("\n📖 Next Steps:")
    print("  1. View in GitHub: Commit and push these files, they render automatically")
    print("  2. View in VS Code: Install 'Markdown Preview Mermaid Support' extension")
    print("  3. Export to PNG: npm install -g @mermaid-js/mermaid-cli && mmdc -i diagram_*.md -o diagram_*.png")
    print("  4. Interactive editing: https://mermaid.live/ (paste diagram code)")


if __name__ == "__main__":
    main()
