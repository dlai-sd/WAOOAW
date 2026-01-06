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
  root((Constitutional<br/>Governance<br/>Platform))
    [Constitutional Foundation]
      constitution_engine
        ::icon(fa fa-balance-scale)
        Operating Modes
        Bright Line Principles
      governance_protocols
        ::icon(fa fa-gavel)
        Governor Escalation
        Approval Workflows
        Break Glass
    
    [Foundational Governance Agents]
      Genesis
        ::icon(fa fa-certificate)
        Agent Certification
        Proposal vs Evolution
      Systems Architect
        ::icon(fa fa-building)
        Architecture Review
        Blast Radius
      Vision Guardian
        ::icon(fa fa-eye)
        Constitutional Compliance
        Ethics Review
    
    [Platform Components]
      AI Explorer
        ::icon(fa fa-robot)
        AI API Layer
        Prompt Certification
      Outside World Connector
        ::icon(fa fa-plug)
        External Integrations
        Credential Vault
      System Audit Account
        ::icon(fa fa-lock)
        Privileged Logging
        Breaks Circular Dependency
      Unified Manifest
        ::icon(fa fa-file-contract)
        Single Source of Truth
        Capability Tracking
    
    [Orchestration Framework]
      13-Component Pattern
        ::icon(fa fa-sitemap)
        Entry/Exit Conditions
        Quality Gates
        State Machine
      Agent Orchestrations
        ::icon(fa fa-code-branch)
        Creation Pipeline
        Servicing Tracks
        Operation Assurance
    
    [Reusable Components]
      Certification
        ::icon(fa fa-check-circle)
        Genesis Gate
        Governor Approval
        Architecture Review
        Ethics Review
      Operations
        ::icon(fa fa-heartbeat)
        Health Checks
        Rollback Procedures
        Versioning
        Audit Logging
    
    [Communication]
      Policy Layer
        ::icon(fa fa-comments)
        5 Communication Patterns
        6 Relation Types
      Technical Layer
        ::icon(fa fa-network-wired)
        Message Bus
        Routing & Security
```"""
    
    def generate_agent_creation_flow(self) -> str:
        """Generate flow diagram for agent creation pipeline"""
        return """```mermaid
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
