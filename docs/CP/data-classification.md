# Data Classification Register

**Version:** 1.0  
**Iteration:** 6 — Compliance (E1-S1)  
**Status:** Approved  
**Retention review date:** Annually

This register formally classifies every column in every table that holds customer data.
All engineering decisions about logging, encryption, retention, and erasure obligations
follow the classifications defined here.

---

## Classification Definitions

| Class | Description | Examples |
|-------|-------------|---------|
| **PII** | Directly identifies or relates to a natural person | email, phone, full_name, ip_address |
| **Business data** | Company/organisation information — not personal | business_name, gst_number, industry |
| **System data** | Technical metadata — no identifying information | id, created_at, status codes, hashes |

---

## Retention Periods

| Class | Retention | Rationale |
|-------|-----------|-----------|
| PII | Account active + 1 year after deletion | Legal minimum; GDPR Art. 5(1)(e) storage limitation |
| Business data | Account active + 3 years | Legal/audit obligations (GST, contracts) |
| System data | 2 years | Operational debugging; then archived or deleted |

---

## Tables

### `base_entity` (shared supertype)

| Column | Type | Class | Retention | Notes |
|--------|------|-------|-----------|-------|
| `id` | UUID | System | 2 years | Primary key — no personal data |
| `entity_type` | text | System | 2 years | Discriminator column |
| `created_at` | timestamptz | System | 2 years | |
| `updated_at` | timestamptz | System | 2 years | |
| `deleted_at` | timestamptz | System | 2 years | Soft-delete marker |
| `status` | text | System | 2 years | Entity lifecycle status |
| `version_hash` | text | System | 2 years | Content hash for audit integrity |
| `amendment_history` | jsonb | System | 2 years | Append-only amendment log |
| `evolution_markers` | jsonb | System | 2 years | |
| `l0_compliance_status` | text | System | 2 years | Constitutional alignment |
| `amendment_alignment` | text | System | 2 years | |
| `drift_detector` | text | System | 2 years | |
| `append_only` | boolean | System | 2 years | |
| `hash_chain_sha256` | text | System | 2 years | Tamper-evidence |
| `tamper_proof` | boolean | System | 2 years | |
| `tags` | jsonb | System | 2 years | |
| `custom_attributes` | jsonb | System | 2 years | Must not store PII in free-form attributes |
| `governance_notes` | text | System | 2 years | |
| `parent_id` | UUID | System | 2 years | Foreign key |
| `child_ids` | UUID[] | System | 2 years | Foreign keys |
| `governance_agent_id` | UUID | System | 2 years | |
| `external_id` | text | System | 2 years | External reference — must not store email |

---

### `customer_entity` (extends `base_entity`)

| Column | Type | Class | Retention | Erasure behaviour |
|--------|------|-------|-----------|-------------------|
| `id` | UUID | System | 2 years | Preserved (structure) |
| `email` | text | **PII** | Active + 1 yr | Replaced with `redacted_{id}@erased.invalid` |
| `phone` | text | **PII** | Active + 1 yr | Replaced with `REDACTED` |
| `full_name` | text | **PII** | Active + 1 yr | Replaced with `REDACTED` |
| `business_name` | text | Business | Active + 3 yr | Not erased |
| `business_industry` | text | Business | Active + 3 yr | Not erased |
| `business_address` | text | **PII** | Active + 1 yr | Replaced with `REDACTED` |
| `website` | text | Business | Active + 3 yr | Not erased |
| `gst_number` | text | Business | Active + 3 yr | Not erased (tax record) |
| `preferred_contact_method` | text | System | 2 years | Not erased |
| `consent` | boolean | System | 2 years | Not erased (legal record) |
| `token_version` | integer | System | 2 years | Not erased |

**Logging rules for `customer_entity`:**
- `email` — ❌ NEVER log in plaintext; mask to `u***@domain.com`
- `phone` — ❌ NEVER log in plaintext; mask to `+91*****XXXX`
- `full_name` — ❌ NEVER log in plaintext; mask to initials `J.D.`
- `business_address` — ❌ NEVER log in plaintext; omit or mask
- Other columns — ✅ Safe to log (no personal data)

---

### `audit_logs`

| Column | Type | Class | Retention | Notes |
|--------|------|-------|-----------|-------|
| `id` | UUID | System | 2 years | |
| `timestamp` | timestamptz | System | 2 years | Archive after 2 years (E4-S1, iter 7) |
| `user_id` | UUID | System | 2 years | References customer — no PII itself |
| `email` | text | **PII** | Active + 1 yr | Redacted to `REDACTED` on erasure |
| `ip_address` | text | **PII** | Active + 1 yr | Mask last octet in logs |
| `user_agent` | text | **PII** | Active + 1 yr | Truncate in logs |
| `screen` | text | System | 2 years | |
| `action` | text | System | 2 years | |
| `outcome` | text | System | 2 years | |
| `detail` | text | System | 2 years | Must not contain raw PII |
| `metadata` | jsonb | System | 2 years | Must not contain raw email/phone |
| `correlation_id` | text | System | 2 years | |
| `deleted_at` | timestamptz | System | 2 years | Soft-delete; erasure records flagged |

**Logging rules:** audit_logs rows are themselves the audit trail — they are never
logged to the application log. The `email` column is redacted during customer erasure.

---

### `otp_sessions`

| Column | Type | Class | Retention | Notes |
|--------|------|-------|-----------|-------|
| `otp_id` | UUID | System | Until expiry or 30d after verification | |
| `channel` | text | System | Same as above | `email` or `phone` |
| `destination` | text | **PII** | Until expiry or 30d after verification | Email or phone |
| `otp_code` | text | **PII** | Until expiry | ❌ NEVER LOG UNDER ANY CIRCUMSTANCES |
| `expires_at` | timestamptz | System | Same | |
| `verified_at` | timestamptz | System | Same | |
| `registration_id` | UUID | System | Same | |

**Logging rules:**
- `otp_code` — ❌ **ABSOLUTE BAN** — any log line containing `otp_code` is a security bug
- `destination` — ❌ NEVER log in plaintext; mask email/phone

---

## Logging Policy Summary

| Field | Allowed in logs | Masking rule |
|-------|----------------|--------------|
| `email` | ✅ Masked only | `u***@domain.com` |
| `phone` | ✅ Masked only | `+91*****XXXX` |
| `full_name` | ✅ Masked only | `J.D.` (initials) |
| `ip_address` | ✅ Masked only | `192.168.1.XXX` |
| `user_agent` | ✅ Truncated | First 30 chars + `…` |
| `otp_code` | ❌ NEVER | No exceptions |
| `business_name` | ✅ Plain | Not personal data |
| `gst_number` | ✅ Plain | Not personal data |
| IDs (UUIDs) | ✅ Plain | No personal data |
| Timestamps | ✅ Plain | No personal data |

---

## Review Process

- This register is reviewed annually or when new tables/columns are added.
- Any PR adding a new column **must** add a row to this register.
- Engineering lead signs off before any new PII column enters production.
