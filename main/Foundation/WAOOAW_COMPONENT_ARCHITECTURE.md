# WAOOAW Component Architecture

This document maps the constitutional design to implementation-ready, cloud-native components and ties each to the existing diagrams for visual reference.

## Visual References
- Mind map: [diagram_mindmap.md](Foundation/diagram_mindmap.md)
- Flow (agent creation pipeline): [diagram_flow.md](Foundation/diagram_flow.md)
- Dependency graph: [diagram_graph.md](Foundation/diagram_graph.md)
- Trial mode enforcement: [diagram_trial.md](Foundation/diagram_trial.md)

## Layered Architecture
- **Constitutional Foundation**: `foundation_constitution_engine.yaml`, `governance_protocols.yaml` — operating modes, approvals, amendments, bright-line boundaries.
- **Foundational Governance Agents**: Genesis, Systems Architect, Vision Guardian, Governor — implemented as services that certify, review, approve, and audit.
- **Foundational Platform Components**: AI Explorer, Outside World Connector, System Audit Account, Unified Agent Configuration Manifest — infrastructure building blocks all orchestrations depend on.
- **Orchestration Layer**: `orchestration_framework.yml` plus `agent_creation_orchestration.yml`, `agent_servicing_orchestration.yml`, `agent_operation_assurance.yml` — executed via a workflow engine with reusable activities.
- **Reusable Component Library (8)**: certification gate, governor approval workflow, architecture review pattern, ethics review pattern, health check protocol, rollback procedure, versioning scheme, audit logging requirements.
- **Communication Infrastructure**: `communication_collaboration_policy.yml`, `message_bus_framework.yml` — policy + transport for all inter-service and inter-agent messaging.

## Platform Services (Logical Components)
- **Governance/Policy Service**: Evaluates policies (trial, data scope, integration permissions) and drives approval workflows.
- **Workflow Orchestrator**: Runs the 7-stage agent creation pipeline and servicing/assurance flows; uses reusable activities (certification gate, architecture review, ethics review, governor approval, rollback, health check, versioning, audit emit).
- **Manifest Service**: Source of truth for agent capabilities (procedures, tools, prompts, integrations); versioned; provides diff/classify API (proposal vs evolution).
- **AI Explorer Service**: Fronts all AI API calls; prompt template registry; safety checks; cost/rate control; caching; audit emission.
- **Outside World Connector**: Fronts external integrations; credential fetch; sandbox routing; idempotency/retry; audit emission.
- **Audit Writer**: Privileged append-only logging; hash-chained entries; integrity verification jobs; implements System Audit Account behavior.
- **Health & Monitoring Service**: Standard health checks, suspension triggers, reactivation flow.
- **Precedent Seed Emitter**: Captures and stores seeds from approvals and executions.
- **Message Bus Layer**: Async transport for approvals, health events, integration requests, AI requests, and audit streams.
- **API Gateway/Ingress**: AuthN/Z enforcement, routing, rate limits; forwards to services.
- **Secrets/Credential Store**: Central vault for AI keys and integration credentials.
- **Observability Stack**: Metrics, logs, traces; dashboards and alerting.

## Data Contracts to Define
- Manifest schema (capabilities, versions, trial flags)
- Prompt template schema
- Integration request/response schema
- Approval request/decision schema
- Audit entry schema (hash-chained)
- Health event schema
- Precedent seed schema

## Cross-Cutting Policies
- Trial mode: synthetic data, sandbox routing, blocked receivers, no compute beyond READ constraints.
- Data access: scope-bound reads/writes, approval levels by operation type.
- AI safety: prompt categories, injection checks, cost/rate guards.
- Integration safety: write/delete/bulk require higher approvals, idempotency required.
- Audit invariants: everything logged via audit writer; integrity checks scheduled.

## Resilience & Runtime Expectations
- Idempotency middleware for write/integration calls.
- Retry/timeouts/circuit breakers at service edges.
- Sandbox routing tables for trial/safe runs.
- Health probes; autoscaling on queue depth/load.
- Background jobs: audit integrity verification, manifest/audit reconciliation.

## Next Implementation Steps (Tool-Agnostic)
1) Define JSON/OpenAPI schemas for manifest, prompt template, integration request/response, approval, audit entry, health event, precedent seed.
2) Author policy bundles (trial/data/AI/integration) and wire policy evaluation at gateway + service edges.
3) Scaffold workflow definitions for agent creation/servicing/assurance with activities mapped to the 8 reusable components.
4) Implement Manifest Service (versioning + diff/classifier API) and wire orchestrations to it.
5) Implement thin slices of AI Explorer and Outside World Connector with audit emission, idempotency, sandbox routing, and safety checks.
6) Set up background jobs for audit integrity verification and manifest/audit reconciliation.
