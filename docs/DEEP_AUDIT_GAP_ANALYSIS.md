# Deep Audit Gap Analysis - CP & PP Specifications

**Date:** January 8, 2026  
**Scope:** Customer Portal (CP) + Platform Portal (PP) v1.0 specifications  
**Format:** Concise bullets (1-2 lines) with recommendations

---

## Critical Gaps (Must Fix Before Implementation)

### 1. **Missing Microservice Port Assignments**
- Gap: PP specifications reference Port 8015 (PP Gateway) but no service implementation exists in main/Foundation.md (13 services: 8001-8013)
- Recommendation: Add PP Gateway (8015), PP API Service (8016) to microservices architecture with FastAPI specs

### 2. **Genesis Agent Webhook Integration Undefined**
- Gap: PP references Genesis validation but no webhook spec (timeout, auth, payload schema, SSE progress)
- Recommendation: Already deferred to Plant phase (placeholder exists), but add API contract stub for integration testing now

### 3. **CP↔PP Data Sync Missing**
- Gap: CP creates subscriptions, PP audits them. No sync mechanism defined (eventual consistency? direct DB access? API calls?)
- Recommendation: Extend component_pp_cp_integration.yml with 3 additional event types: subscription_created, agent_provisioned, trial_started

### 4. **Mobile Push Notification Infrastructure Incomplete**
- Gap: CP requires <5min approval latency but no FCM server key, device token registration flow, or offline queue spec
- Recommendation: Add component_mobile_push_service.yml (FCM integration, token registry, offline sync protocol)

### 5. **Trial Mode Enforcement Ambiguity**
- Gap: Policy Service (8013) enforces trial mode but unclear HOW (runtime PEP intercepts? pre-deploy manifest check? both?)
- Recommendation: Update policy_runtime_enforcement.yml with PEP placement diagram (Agent Execution → PEP → AI Explorer/Integrations)

### 6. **Database Schema Mismatches**
- Gap: CP references `auth_users` table, PP references `pp_users` table. Are they same DB? Separate schemas? Cross-portal user linking?
- Recommendation: Create unified data_model.yml with 3 schemas (public.users for CP, pp_portal.users for PP, audit.logs shared)

### 7. **Stripe Webhook Security**
- Gap: CP uses Stripe for payments but no webhook signature verification, idempotency keys, or retry handling spec
- Recommendation: Add component_payment_webhook_handler.yml (Stripe signature verify, idempotent processing, Temporal saga for failures)

### 8. **Agent Workspace Filesystem Undefined**
- Gap: Agent DNA references `agents/{agent_id}/state/` directory but no storage backend (Cloud Storage? NFS? Persistent Volume?)
- Recommendation: Add agent_workspace_storage.yml (GCS bucket structure, lifecycle rules, backup/restore protocol)

### 9. **Constitutional Query API Missing**
- Gap: Agents query constitution via `constitutional_query` but no API endpoint, response schema, or cache strategy defined
- Recommendation: Add to Industry Knowledge Service (8004): `POST /v1/constitutional/query` (vector search, cache L1/L2/L3)

### 10. **Health Check Aggregation**
- Gap: PP monitors 13 microservices but no aggregation service (who polls? how often? where's consolidated status stored?)
- Recommendation: Add component_health_aggregator.yml (Prometheus scrape config, Grafana dashboard JSON, pp_health_checks table)

---

## High Priority Gaps (Should Fix in Sprint 1-2)

### 11. **Rate Limiting Strategy Inconsistent**
- Gap: CP uses Redis sliding window (100/1000 req/hr), PP uses "polling-based" (no rate limit?). DoS risk.
- Recommendation: Standardize on Redis sliding window for both portals (anon: 100/hr, auth: 1000/hr, admin: 10000/hr)

### 12. **Error Handling Not Unified**
- Gap: CP has component_error_handling_recovery.yml, PP has none. PP errors shown how? Toast? Modal? Logging only?
- Recommendation: Create component_pp_error_handling.yml (reuse CP patterns: toast, retry button, error codes)

### 13. **RBAC Permission Explosion**
- Gap: PP has 7 roles × 9 components = 63 permission combinations. No permission matrix or inheritance model.
- Recommendation: Add pp_rbac_permission_matrix.yml (inheritance hierarchy, wildcard permissions, deny rules)

### 14. **Audit Log Retention Mismatch**
- Gap: PP stores logs 6 months (ELK), System Audit (8010) is append-only forever. Storage cost explosion.
- Recommendation: Add lifecycle policy: Hot (30 days ELK), Warm (6 months Cloud Storage), Cold (7 years GCS Coldline for audit compliance)

### 15. **Agent Version Upgrades Race Condition**
- Gap: CP allows agent version upgrade during active run. What happens? Interrupt? Queue upgrade? Finish then upgrade?
- Recommendation: Add version_upgrade_orchestration.yml (pause runs → drain queue → blue-green switch → resume)

### 16. **Incident vs Ticket Confusion**
- Gap: PP has incidents (internal IT) and CP has tickets (customer issues). No cross-reference when incident affects customer.
- Recommendation: Update component_pp_subscription_management.yml: `incident.affected_subscriptions` auto-creates CP tickets

### 17. **Genesis Rejection Recovery Incomplete**
- Gap: Industry Manager retries retuning after Genesis rejection, but what if Genesis rejects 3x? Escalation path missing.
- Recommendation: Add escalation after 3 rejections → Platform Governor review → Manual override or permanent block

### 18. **SLA Credit Stripe Integration Missing**
- Gap: PP has SLA credit workflow but no Stripe API integration spec (credit note vs refund? prorated? tax handling?)
- Recommendation: Add stripe_credit_note_api.yml (API endpoint, tax calculation, customer notification email template)

### 19. **Knowledge Source Scraping Concurrency**
- Gap: Industry Manager schedules daily scraping (2 AM IST). What if 100 sources? Serial (slow) or parallel (rate limit risk)?
- Recommendation: Add scraping_concurrency_control.yml (Celery worker pool: 5 concurrent, exponential backoff on 429)

### 20. **Agent Handoff Rejection Loop**
- Gap: Infrastructure team rejects handoff → Agent Orchestrator fixes → resubmit. No retry limit or timeout.
- Recommendation: Add handoff_retry_policy.yml (max 3 attempts, 7-day timeout, auto-escalate to Admin)

---

## Medium Priority Gaps (Fix in Sprint 3-5)

### 21. **Forensic Access Audit Trail**
- Gap: PP users access agent run logs (forensics) but no audit of WHO accessed WHAT WHEN (compliance risk).
- Recommendation: Add pp_forensic_access_log table (user_id, subscription_id, accessed_at, fields_viewed)

### 22. **CP Dashboard Real-Time Updates**
- Gap: CP monitors agent activity but polling-based (refresh button). No WebSocket/SSE for real-time dashboard updates.
- Recommendation: Add component_realtime_updates.yml (SSE endpoint `/v1/stream/activity`, Redis Pub/Sub backend)

### 23. **Agent Conformity Test False Positives**
- Gap: Conformity test generates sample with synthetic data, but quality score may differ with real data (bias risk).
- Recommendation: Add conformity_confidence_interval.yml (run test 3x, report median + stddev, warn if variance >10%)

### 24. **Trial Extension Business Logic**
- Gap: CP enforces "no trial extensions" but user stories mention "extend trial" approval. Contradiction.
- Recommendation: Clarify: No auto-extensions. Manual Platform Governor override only (emergency basis, logged)

### 25. **Agent Activity Feed Pagination**
- Gap: CP shows live activity ("Agent X completed Y") but no pagination. 1000+ activities = page crash.
- Recommendation: Add pagination (50 items/page, cursor-based, `GET /v1/activity?cursor={token}`)

### 26. **Budget Alert Threshold Customization**
- Gap: CP hardcodes 70%/85%/100% budget alerts. Enterprise customers want custom thresholds.
- Recommendation: Add budget_alert_preferences table (customer_id, thresholds [60, 80, 95], notification_channel)

### 27. **Agent Interrupt Confirmation Dialog**
- Gap: CP allows agent interrupt but no "Are you sure?" dialog. Accidental clicks = work lost.
- Recommendation: Add interrupt_confirmation_ux.yml (modal with impact warning, require reason, 5-second countdown)

### 28. **Go-Live Checklist Incomplete**
- Gap: Go-live requires conformity test pass but doesn't check integration connectivity (API credentials expired?).
- Recommendation: Add go_live_readiness_checks.yml (test OAuth tokens, API rate limits, sandbox→production DNS)

### 29. **Subscription Plan Migration**
- Gap: CP allows upgrade/downgrade but no prorated billing calculation or effective date (immediate? next cycle?).
- Recommendation: Add subscription_plan_migration.yml (prorated calculation, effective_date options, Stripe API integration)

### 30. **Agent Team Coordination Deadlock**
- Gap: Manager delegates to 2 agents, both wait on shared resource (DB lock). No deadlock detection.
- Recommendation: Add deadlock_detection.yml (timeout 5min, detect circular wait, Manager intervenes with priority override)

---

## Low Priority Gaps (Fix in v1.1)

### 31. **Dark Mode Toggle**
- Gap: PP has dark theme default, CP has no theme toggle. User preference not persisted.
- Recommendation: Add theme_preferences table (user_id, theme, persisted in JWT claims)

### 32. **Gamification Badge Images**
- Gap: CP Learning Service tracks badges but no image assets (SVG? PNG? CDN?).
- Recommendation: Add badge_assets.yml (SVG files in Cloud Storage, CDN URL generation)

### 33. **Agent Specialty Taxonomy**
- Gap: CP filters by "specialty" but no controlled vocabulary. "Content Writing" vs "Content Creation" = duplication.
- Recommendation: Add agent_specialty_taxonomy.yml (canonical list, synonyms mapping, auto-suggest)

### 34. **Mobile App Offline Mode**
- Gap: CP mobile requires "offline mode" but approvals cached how long? What if device stolen?
- Recommendation: Add offline_cache_policy.yml (max 24hr cache, require biometric re-auth every 4hr)

### 35. **Agent Workspace Archive Format**
- Gap: Cancelled subscriptions archive workspace (30 days) but no format spec (ZIP? TAR? Encrypted?).
- Recommendation: Add workspace_archive_format.yml (TAR.GZ with AES-256, customer download link, GDPR deletion after 30d)

### 36. **Marketplace Search Relevance Tuning**
- Gap: CP uses Elasticsearch but no relevance tuning (boost fields? decay functions?).
- Recommendation: Add search_relevance_config.yml (boost: name^3, specialty^2, description^1, recency decay)

### 37. **Agent Rating Spam Detection**
- Gap: CP shows agent ratings but no spam detection (bot reviews? competitor sabotage?).
- Recommendation: Add rating_validation.yml (verified purchase check, ML spam detector, manual review queue)

### 38. **Invoice Generation**
- Gap: CP mentions "billing" but no invoice PDF generation or email delivery.
- Recommendation: Add invoice_generation.yml (Stripe invoice API, PDF template, SendGrid attachment)

### 39. **Agent Performance Benchmarking**
- Gap: PP shows agent health score but no industry benchmarks (is 4.2/5 good or bad?).
- Recommendation: Add performance_benchmarks.yml (industry percentiles, peer comparison, trend analysis)

### 40. **Precedent Seed Versioning**
- Gap: Agents cache precedents.json but no version tracking (when was seed added? by whom?).
- Recommendation: Add precedent_versioning.yml (seed_id, version, author, created_at, deprecation_date)

---

## Design Inconsistencies (Refactor in Sprint 6+)

### 41. **Port Numbering Scheme**
- Gap: Services numbered 8001-8013, then PP uses 8015. Why skip 8014? Reserving for future service?
- Recommendation: Document port allocation strategy (8014 reserved for Event Bus, 8017-8020 reserved for Plant phase agents)

### 42. **YAML vs Markdown Documentation**
- Gap: Some components have .yml specs, others have .md guides. No consistent format.
- Recommendation: Standardize: .yml for machine-readable specs, .md for human guides, both required

### 43. **API Versioning Strategy**
- Gap: APIs use `/v1/` but no deprecation policy or migration guide for v2.
- Recommendation: Add api_versioning_policy.yml (support v1 for 12 months after v2 release, sunset schedule)

### 44. **Error Code Ranges**
- Gap: CP uses 4xxx/5xxx HTTP codes but no application error codes (WAOOAW-specific).
- Recommendation: Add error_code_registry.yml (AUTH-001, TRIAL-002, AGENT-003, PAYMENT-004 ranges)

### 45. **Logging Verbosity**
- Gap: Different services log at different levels (DEBUG vs INFO vs ERROR). No unified policy.
- Recommendation: Add logging_standards.yml (Prod: ERROR, Staging: INFO, Dev: DEBUG, structured JSON format)

### 46. **Database Connection Pooling**
- Gap: Multiple services connect to PostgreSQL but no connection pool config (PgBouncer? SQLAlchemy pool?).
- Recommendation: Add db_connection_pool.yml (PgBouncer 100 real, 1000 virtual, per-service limits)

### 47. **Service Discovery**
- Gap: Services hardcode URLs (http://localhost:8001). How do services find each other in production?
- Recommendation: Add service_discovery.yml (Cloud Run internal URLs, DNS-based, health check integration)

### 48. **Secrets Rotation**
- Gap: JWT secrets, OAuth keys in Secret Manager but no rotation policy or zero-downtime rotation.
- Recommendation: Add secrets_rotation_policy.yml (90-day rotation, dual-key validation during transition)

### 49. **Backup & Disaster Recovery**
- Gap: PostgreSQL mentioned but no backup schedule, RPO/RTO targets, or restore testing.
- Recommendation: Add backup_dr_policy.yml (Daily backups, 7-day retention, RTO 4hr, RPO 15min, quarterly restore drill)

### 50. **Cost Monitoring**
- Gap: Platform mentions costs (₹8K-18K/month) but no cost attribution (which customer? which agent?).
- Recommendation: Add cost_attribution.yml (GCP labels, BigQuery export, per-customer cost dashboard)

---

## Constitutional Compliance Gaps

### 51. **Genesis Override Mechanism Missing**
- Gap: Admin cannot override Genesis rejection (correct) but no emergency "break glass" for Platform Governor.
- Recommendation: Add constitutional_emergency_override.yml (Platform Governor only, requires 2-person approval, audit log, 24hr review)

### 52. **Customer Data Sovereignty Enforcement**
- Gap: Constitution says "no customer core data access" but no technical enforcement (row-level security? views?).
- Recommendation: Add rls_policy.yml (PostgreSQL RLS on customer_data table, PP users denied SELECT, audit log on violations)

### 53. **Deny-By-Default Not Enforced**
- Gap: Constitution requires deny-by-default but no PEP intercept on every agent action (gap in enforcement).
- Recommendation: Add pep_enforcement_matrix.yml (Agent Execution → PEP → AI Explorer/Integrations, all external calls blocked unless allowlisted)

### 54. **Approval Timeout Handling**
- Gap: Governor has 24hr to approve/veto but what if offline? Agent pauses forever?
- Recommendation: Add approval_timeout_policy.yml (24hr timeout → escalate to Deputy Governor → default DENY if no response)

### 55. **Agent Suspension Criteria Vague**
- Gap: Genesis can suspend agents but criteria unclear (constitutional violation? performance degradation? both?).
- Recommendation: Add agent_suspension_criteria.yml (5 triggers: constitutional violation, error rate >10%, Genesis decertification, security incident, customer complaint)

---

## Integration Gaps (Cross-Service)

### 56. **Temporal Workflow Versioning**
- Gap: Agent creation uses Temporal 7-stage pipeline but no workflow versioning (breaking changes = stuck workflows).
- Recommendation: Add temporal_workflow_versioning.yml (semantic versioning, backward compatibility, migration guide)

### 57. **Pub/Sub Message Ordering**
- Gap: PP→CP integration uses Pub/Sub but no ordering guarantees (subscription_canceled arrives before agent_status_changed).
- Recommendation: Add pubsub_ordering_config.yml (ordering_key = subscription_id, enable ordering per subscription)

### 58. **Elasticsearch Index Aliases**
- Gap: CP uses Elasticsearch for search but no index aliases (reindex downtime during schema changes).
- Recommendation: Add elasticsearch_alias_strategy.yml (blue-green indexes, zero-downtime reindex)

### 59. **Redis Cache Invalidation**
- Gap: Multiple services cache data in Redis but no invalidation protocol (stale data risk).
- Recommendation: Add cache_invalidation_protocol.yml (Pub/Sub cache-invalidate topic, TTL-based expiry, cache-aside pattern)

### 60. **Inter-Service Authentication**
- Gap: Services call each other but no mutual TLS or service account tokens (SSRF risk).
- Recommendation: Add inter_service_auth.yml (Google-managed service identities, Cloud Run IAM, mTLS between services)

---

## Summary

**Total Gaps Identified:** 60  
**Critical (Must Fix):** 10  
**High Priority:** 10  
**Medium Priority:** 10  
**Low Priority:** 10  
**Design Inconsistencies:** 10  
**Constitutional Compliance:** 5  
**Integration Gaps:** 5

**Estimated Effort to Resolve:**
- Critical (10): 2-3 weeks (block implementation start)
- High (10): 3-4 weeks (Sprint 1-2)
- Medium (10): 4-6 weeks (Sprint 3-5)
- Low (10): 6-8 weeks (v1.1)
- Design (10): Ongoing refactor (Sprint 6+)
- Constitutional (5): 1 week (parallel to Sprint 1)
- Integration (5): 2 weeks (Sprint 2-3)

**Recommendation:** Fix Critical + Constitutional gaps (11 items, 3-4 weeks) before implementation kickoff. Tackle High Priority in parallel with Sprint 1.
