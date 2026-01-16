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
- **Governance/Policy Service**: Evaluates policies (trial, data scope, integration permissions) and drives approval workflows; PDP source of truth in [main/Foundation/policy_runtime_enforcement.yml](main/Foundation/policy_runtime_enforcement.yml) with attested decisions. **Tool:** Open Policy Agent (OPA) on Cloud Run.
- **Workflow Orchestrator**: Runs the 7-stage agent creation pipeline and servicing/assurance flows; uses reusable activities (certification gate, architecture review, ethics review, governor approval, rollback, health check, versioning, audit emit). **Tool:** Python async orchestrator service on Cloud Run.
- **Manifest Service**: Source of truth for agent capabilities (procedures, tools, prompts, integrations); versioned; provides diff/classify API (proposal vs evolution). **Tool:** FastAPI + Tortoise ORM on Cloud Run.
- **AI Explorer Service**: Fronts all AI API calls; prompt template registry; safety checks; cost/rate control; caching; audit emission. **Tools:** Groq (primary), OpenAI GPT-4o (fallback), Cloud Run.
- **Outside World Connector**: Fronts external integrations; credential fetch; sandbox routing; idempotency/retry; audit emission. **Tool:** FastAPI service on Cloud Run.
- **Audit Writer**: Privileged append-only logging; hash-chained entries; integrity verification jobs; implements System Audit Account behavior. **Tool:** PostgreSQL Cloud SQL with triggers, Cloud Run service.
- **Health & Monitoring Service**: Standard health checks, suspension triggers, reactivation flow. **Tool:** Cloud Run health endpoints + Cloud Monitoring alerts.
- **Precedent Seed Emitter**: Captures and stores seeds from approvals and executions. **Tool:** PostgreSQL jsonb storage + query API on Cloud Run.
- **Message Bus Layer**: Async transport for approvals, health events, integration requests, AI requests, and audit streams (topics + schemas in [main/Foundation/template/message_bus_framework.yml](main/Foundation/template/message_bus_framework.yml)). **Tool:** Google Cloud Pub/Sub with JSON Schema validation.
- **API Gateway/Ingress**: AuthN/Z enforcement, rate/quotas, schema validation, PDP/PEP handoff in [main/Foundation/security/api_gateway_policy.yml](main/Foundation/security/api_gateway_policy.yml). **Tool:** Cloud Run service with OPA integration.
- **Secrets/Credential Store**: Central vault tenancy/rotation in [main/Foundation/security/secrets_management_policy.yml](main/Foundation/security/secrets_management_policy.yml). **Tool:** Google Secret Manager.
- **Observability Stack**: Metrics, traces, logs, dashboards in [main/Foundation/observability_stack.yml](main/Foundation/observability_stack.yml). **Tool:** Google Cloud Monitoring + Cloud Logging + Cloud Trace.
- **Resilience Policy**: SLOs, circuit breakers, backpressure rules in [main/Foundation/resilience_runtime_expectations.yml](main/Foundation/resilience_runtime_expectations.yml). **Tool:** Custom Python middleware on Cloud Run.

## Data Contracts to Define
- Canonical definitions live in [main/Foundation/contracts/data_contracts.yml](main/Foundation/contracts/data_contracts.yml).

## Policy Enforcement & Trial Routing
- Runtime PDP/PEP split, deny-by-default, and attested decisions: [main/Foundation/policy_runtime_enforcement.yml](main/Foundation/policy_runtime_enforcement.yml)
- Trial/sandbox routing tables for AI + integrations: [main/Foundation/trial_sandbox_routing.yml](main/Foundation/trial_sandbox_routing.yml)

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
