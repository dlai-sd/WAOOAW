# Archived Portal Planning Documents

**Date**: January 1, 2026  
**Reason**: Superseded by PLATFORM_PORTAL_MASTER_PLAN.md

## Contents

- `EPIC_4.1_MAINTENANCE_PORTAL.md` - Empty original maintenance portal epic
- `EPIC_5.1_OPERATIONAL_PORTAL.md` - Original operational portal epic (102 points)
- `EXECUTION_PLAN_EPIC_5.1.md` - Original execution plan (225 points, React-based)

## Why Archived?

Decision made to rebuild portal with **Reflex (Pure Python)** instead of React/TypeScript.
All planning consolidated into single master plan (246 points, 14 weeks, 5 phases).

## New Plan

See: `/docs/platform/PLATFORM_PORTAL_MASTER_PLAN.md`

**Key Changes**:
- Framework: Reflex (Pure Python) instead of React + TypeScript
- Scope: 246 points (14 stories) instead of 225 points
- Duration: 14 weeks with 5 clear phases
- Team: Python-only developers (no JS skills required)
- Architecture: 100% Python frontend + FastAPI backend

## Story Documents (Still Active)

These story documents are **NOT** archived - they remain active implementation guides:
- STORY_5.1.0_COMMON_PLATFORM_COMPONENTS.md
- STORY_5.1.7_CONTEXT_OBSERVABILITY.md
- STORY_5.1.8_REALTIME_MESSAGE_QUEUE_MONITORING.md
- STORY_5.1.9_REALTIME_ORCHESTRATION_MONITORING.md
- STORY_5.1.10_AGENT_FACTORY_MODE.md
- STORY_5.1.11_AGENT_SERVICING_MODE.md
- STORY_5.1.12_TECHNICAL_HELPDESK_MODE.md

These will be implemented in Reflex (Python) instead of React (TypeScript).
