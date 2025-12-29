# Agent Entity Architecture

Date: 2025-12-29
Author: dlai-sd

## Overview

This document defines the Agent Entity architecture for WAOOAW. An "Agent Entity" is a logical construct representing an autonomous software agent that acts on behalf of a person, organization, or system. The goal of this document is to describe composition, technical identity, supported runtimes, attestation model, lifecycle states/events, mapping to user journeys, an implementation plan, and next steps for producing a formal JSON Schema.

This document is intended to guide engineering and product teams implementing agents across platforms and to ensure a consistent cross‑system representation of agents.

## 1. Composition

An Agent Entity is composed of several logical layers and modules:

- Core Identity
  - Stable identifier (DID or URN)
  - Human-friendly metadata: displayName, description, avatarUrl
- Capabilities (Capabilities List)
  - Declarative capability descriptors (e.g., `can:send-email`, `can:access-drive`)
  - Policy constraints per capability (scopes, rate limits, contexts)
- Credentials & Secrets
  - Encrypted key material or pointers to secure KMS / secret stores
  - Token issuance metadata (JWT/OAuth references)
- Runtime Configuration
  - Preferred runtime type (serverless, container, edge, mobile)
  - Resource constraints, environment variables, execution policies
- Attestation & Trust
  - Verifiable claims about the agent (issuer, issuanceDate, evidence)
  - Runtime attestations (signed runtime manifests)
- Observability & Audit
  - Event logging contract, telemetry endpoints, retention expectations
- Governance & Lifecycle Metadata
  - Owner, steward, creation/expiry dates, status

Each module has a minimal canonical form in the agent entity model and extension points for system-specific needs.

## 2. Technical Identity

Technical identity covers the persistent and cryptographic identifiers and the methods to bind them to the Agent Entity.

- Primary Identifier
  - Use a DID (Decentralized Identifier) where possible (did:peer, did:key, did:web, or did:example for dev).
  - If DID is not feasible, use a globally unique URN or UUID with namespace prefix.
- Key Material & Key Rotation
  - The agent should have one or more public keys associated with the DID.
  - Key rotation MUST be supported; rotations are recorded as events/attestations in the agent record.
  - Private keys are never stored in plain text in the agent record; store pointers to KMS or encrypted blobs.
- Binding Identity to Capabilities
  - Capabilities granted are signed by an authority (owner/steward) and attached as verifiable credentials.
  - Use standard formats where possible (VC, JWT) to represent delegations/permissions.
- Authentication & Authorization
  - Agents authenticate using keys (mTLS/SSH), signed request tokens (JWT), or token exchange against an authorization server.
  - Authorization checks use capability descriptors and contextual claims (time, audience, environment).

## 3. Runtimes

Agent Entities may execute or be proxied in different runtime environments. The architecture treats runtime as a pluggable component.

Common runtime categories:

- Serverless (FaaS)
  - Good for event-driven, short-lived agents.
  - Provide small cold-start, ephemeral keys via invocation-specific attestations.
- Containerized (Kubernetes)
  - Suitable for long-running or stateful agents.
  - Leverage pod identity solutions, sidecar patterns for secrets.
- Edge / IoT
  - Constrained devices with offline-first behaviour; support local attestations and sync.
- Mobile / Desktop
  - Agents embedded in user devices; bind to device identity and OS-provided attestation services.
- Hosted Proxy (Managed)
  - A central runtime that proxies requests to third-party services on behalf of agents.

Runtime considerations:
- Each runtime must provide a runtime identifier and a signed runtime manifest (see Attestations).
- Secrets access should use ephemeral credentials or workload identity providers.
- Observability hooks must be standardized (trace/span correlation using agent identifier).

## 4. Attestations

Attestations are cryptographic statements asserting facts about the agent or its runtime. They form the trust backbone for granting privileges.

Types of attestations:

- Identity attestations
  - Proof that a DID corresponds to the stated owner (issued by an identity provider).
- Capability attestations (Verifiable Credentials)
  - Signed grants stating which capabilities the agent has and any constraints.
- Runtime attestations
  - Signed statements by the runtime that the agent executed in a particular environment (hashes of code, container image digest, runtime id, timestamp).
- Key rotation attestations
  - Signed records indicating a key pair change for the agent.

Attestation properties:
- Signed by a known/trusted issuer (owner, platform, or third-party attestation service).
- Include issuance time, expiry (where applicable), and evidence references.
- Verifiable using standards (linked data proofs, JWT signatures, COSE, etc.).

Verification flows:
- At capability grant time: validate issuer PK, credential signature, and constraints.
- At invocation time: validate runtime attestation against expected runtime manifest and agent identity.
- Periodic re-attestation: scheduled re-checks for long-lived credentials and runtime proofs.

## 5. Lifecycle

Define canonical lifecycle states and events for agent entities. Represent states explicitly in the agent record and emit events for transitions.

States (recommended):
- draft — Agent created, not yet provisioned
- provisioned — Identity created and minimal keys/credentials assigned
- active — Agent is allowed to operate and receive requests
- suspended — Temporarily blocked (policy or security event)
- revoked / decommissioned — Permanently disabled; keys revoked
- expired — Reached expiry without renewal

Events (examples):
- create
- provision (identity and runtime resources created)
- grant-capability
- revoke-capability
- rotate-key
- start-runtime / stop-runtime
- suspected-compromise
- suspend
- resume
- decommission

Guidelines:
- Record event metadata and produce an audit trail linked to the agent identifier.
- Ensure state transitions are validated by policy (e.g., only owner or governance role can decommission).
- Support soft-delete with retainable audit logs for forensic needs.

## 6. Mapping to User Journeys

Below are example user journeys and how they map to the Agent Entity model.

1) Onboard a Personal Assistant Agent (user-driven)
- User creates agent -> agent record in draft
- Owner verifies identity -> provisioned (DID created, keys generated/stored)
- User configures capabilities (email, calendar) -> capability attestations issued
- User launches agent on a runtime (mobile or serverless) -> runtime attestation and active state
- Ongoing: agent logs events, user can inspect capabilities and revoke when desired

2) Enterprise App Integration (admin-driven)
- IT admin creates an agent template with default policies
- Agent provisioned with enterprise-owned DID and KMS pointers
- Admin grants scoped capabilities for data access; these are expressed as VCs
- Runtime is a managed cluster with workload identity; runtime manifests created
- Operations: rotate keys, audit logs, suspend if policy triggers

3) Third‑party Delegation
- User delegates limited capability to a third party agent (time-boxed)
- Delegation recorded as a verifiable credential signed by owner
- Third‑party runtime must present runtime attestation to use capabilities
- Revoke by revoking the credential or disabling the agent

4) Emergency Recovery
- Agent suspected compromise -> emit suspected-compromise event
- System auto-suspends or revokes keys, notifies owner
- Recovery flow: rotate keys, re-provision runtime, re-attest

In all journeys the UI/UX surfaces are simple views over the canonical Agent Entity record: identity, capabilities, active runtimes, audit events, and governance controls.

## 7. Implementation Plan

Phased plan with milestones and deliverables.

Phase 0 — Schema & API (2–3 sprints)
- Produce canonical JSON Schema for Agent Entity (core + extension points).
- Implement CRUD API endpoints for agent records (create, read, update, delete, list).
- Define event model (webhooks / event stream) for lifecycle events.

Phase 1 — Identity & Attestation (2–4 sprints)
- Integrate DID method(s) or global identifier provider.
- Implement key management patterns (KMS integration, key rotation primitives).
- Introduce verifiable credentials support for capability grants.
- Implement runtime attestation ingestion and verification pipeline.

Phase 2 — Runtimes & Delegation (3–6 sprints)
- Provide runtime adapters: serverless, container, and hosted proxy.
- Implement workload identity to bind runtime to agent DIDs.
- Create delegation UI and APIs (issue/revoke capability VCs).

Phase 3 — Security & Governance (ongoing)
- Harden attestation verification, revocation lists, and CRL-equivalents for VCs.
- Integrate audit/forensics workflows, retention policies.
- Provide role-based access controls and approval workflows for sensitive capabilities.

Phase 4 — Monitoring & Developer Experience
- Telemetry dashboards, simulation harness for agent behaviours.
- SDKs and CLI for common agent operations (provision, rotate, attest).

Deliverables per phase should include API docs, reference implementations, test suites, and an integration guide.

## 8. JSON Schema — Next Steps

The first concrete artifact should be a versioned JSON Schema (or OpenAPI component schema) describing the Agent Entity canonical record. Below is a suggested minimal schema sketch and next steps for finalization.

Example skeleton (informal) — this MUST be translated to a full JSON Schema file under `schemas/agent-entity.schema.json` and published in the API docs.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Agent Entity",
  "type": "object",
  "required": ["id", "metadata", "identity"],
  "properties": {
    "id": {"type": "string", "description": "Canonical identifier (DID or URN)"},
    "metadata": {
      "type": "object",
      "properties": {
        "displayName": {"type": "string"},
        "description": {"type": "string"},
        "avatarUrl": {"type": "string", "format": "uri"},
        "createdAt": {"type": "string", "format": "date-time"},
        "owner": {"type": "string"}
      }
    },
    "identity": {
      "type": "object",
      "properties": {
        "did": {"type": "string"},
        "publicKeys": {
          "type": "array",
          "items": {"type": "object", "properties": {"id": {"type": "string"}, "type": {"type": "string"}, "publicKeyPem": {"type": "string"}}}
        }
      }
    },
    "capabilities": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "constraints": {"type": "object"},
          "attestation": {"type": "object"}
        }
      }
    },
    "runtimes": {
      "type": "array",
      "items": {"type": "object", "properties": {"runtimeId": {"type": "string"}, "type": {"type": "string"}, "manifest": {"type": "object"}}}
    },
    "lifecycle": {"type": "object", "properties": {"state": {"type": "string"}, "events": {"type": "array"}}},
    "attestations": {"type": "array"}
  }
}
