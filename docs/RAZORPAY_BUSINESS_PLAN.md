# WAOOAW — Business Plan
## Prepared for Razorpay Merchant Onboarding

**Business Name:** WAOOAW Technology Private Limited  
**Website:** waooaw.com  
**Date:** March 2026  
**Business Category:** Software / SaaS / AI Marketplace  

---

## Page 1 — Business Overview & Model

### What We Do

WAOOAW ("WAH-oo-ah") is India's first **AI agent marketplace** where specialized AI agents earn
business by demonstrating measurable value *before* the customer pays. The name is a palindrome —
quality from any angle.

Businesses waste time and money buying AI tools that fail to deliver. WAOOAW solves this with a
**try-before-hire** model: customers get a full 7-day free trial, keep all deliverables (content,
reports, analysis), and only pay if they see value.

### Legal & Operational Details

| Field | Detail |
|-------|--------|
| Entity type | Private Limited Company (to be incorporated) / Technology Startup |
| Founders | Platform Governor (single operator) |
| Operating since | 2025 (beta), 2026 (public launch) |
| Primary market | India — SMEs, startups, EdTech companies, D2C brands |
| Platform URL | cp.waooaw.com (Customer Portal), pp.waooaw.com (Admin Portal) |
| Contact email | ops@waooaw.com |
| GCP project | waooaw-oauth (Asia South 1 — Mumbai) |

### Product

The platform hosts **19+ specialized AI agents** across three verticals:

| Industry | Agents | Examples |
|----------|--------|---------|
| Marketing | 7 | Content Marketing, SEO, Social Media, Email, PPC, Brand Strategy, Influencer |
| Education | 7 | Math Tutor (JEE/NEET), Science (CBSE), English, Test Prep, Career Counseling, Study Planning, Homework Help |
| Sales | 5 | SDR (B2B SaaS), Account Executive, Sales Enablement, CRM Management, Lead Generation |

Each agent has a unique personality, real-time availability status (Available / Working / Offline),
verifiable skill certifications, and a constitutional governance trail logged in an immutable
PostgreSQL audit chain.

### Revenue Model

| Plan | Price | Description |
|------|-------|-------------|
| Single Agent | ₹8,000 – ₹18,000 / month | One specialized AI agent, skill-tier pricing |
| Team Package | ₹19,000 – ₹30,000 / month | Manager AI + 2–4 specialist agents, coordinated work |
| Trial | Free (7 days) | Full access, keep all deliverables regardless of decision |

**Payment cycle:** Monthly recurring subscription charged at end of 7-day trial on day 8 if the
customer opts in. Customers must actively confirm before any charge.

**Payment gateway:** Razorpay — used for Razorpay Order creation, payment verification, and
recurring subscription billing.

---

## Page 2 — Market Opportunity & Platform Technology

### Market Opportunity

| Dimension | Detail |
|-----------|--------|
| Problem | SMEs want AI assistance but face high upfront risk — no proof of value, no comparison options, no governance |
| Gap | No AI marketplace in India follows a talent-hire model (compare: Upwork/Fiverr for humans — nothing equivalent for AI agents) |
| Target customers | Indian SMEs, D2C brands, EdTech startups, marketing agencies, B2B SaaS sales teams |
| TAM | India's AI services market is projected at ₹18,000 Cr by 2028 (NASSCOM) |
| Pricing sweet spot | ₹8K–18K/month makes professional AI work accessible to SMEs that cannot afford ₹5L+/year agency retainers |

### Differentiation

1. **Try Before Hire** — 7-day trial with zero risk, keep all deliverables. No competitor offers this.
2. **Constitutional Governance** — every agent action is logged with RSA-signed amendments and an
   immutable SHA-256 hash chain. Customers can audit every decision an agent made on their behalf.
3. **Marketplace DNA** — agents have personality, status, ratings, and specializations (not generic
   SaaS feature lists). Browsing feels like hiring talent, not buying software.
4. **Single Governor model** — one human (Platform Governor) reviews and approves all agent
   certifications, emergency budgets, and policy exceptions. Scales to 19+ agents.

### Technical Architecture (Summary for Razorpay)

The platform runs on **Google Cloud Platform (GCP) Cloud Run** in the Mumbai region
(`asia-south1`). All services are containerized with no vendor lock-in (adapters over direct SDK
calls).

```
Customer Browser → CP Frontend (React 18 + TypeScript)
                 → CP Backend  (FastAPI, Python 3.11, port 8020)
                 → Plant Gateway (FastAPI, auth/RBAC/policy, port 8000)
                 → Plant Backend  (FastAPI, PostgreSQL 15, port 8001)
                                   ↕
                        Razorpay API (order creation + webhooks)
```

**Payment flow:**
1. Customer completes 7-day trial and clicks "Hire Agent"
2. CP Backend calls Plant Gateway → Plant Backend → Razorpay Order API
3. Razorpay Checkout renders in browser (hosted checkout — PCI-compliant)
4. On payment success, Plant Backend records `subscription.status = active` in PostgreSQL
5. Monthly auto-charge via Razorpay recurring subscription (Razorpay handles mandate)

**Data security:**
- JWT authentication (HS256) + Google OAuth2 + OTP + 2FA (TOTP)
- Cloudflare Turnstile CAPTCHA on all auth flows
- All credentials encrypted at rest (AES-256) via GCP Secret Manager
- PII masking on all logs (email/phone never written to stdout)
- Razorpay keys stored exclusively in GCP Secret Manager — never in code or config files

---

## Page 3 — Financial Projections & Razorpay Usage

### Projected Transaction Volume

| Period | Active Customers | Avg Subscription | Monthly GMV | Annual GMV |
|--------|-----------------|-----------------|-------------|------------|
| Month 1–3 (Test Mode) | 0 paid, trial only | — | ₹0 | — |
| Month 4–6 (Early Adopters) | 10–25 | ₹10,000 | ₹1,00,000 – ₹2,50,000 | — |
| Month 7–12 (Growth) | 50–100 | ₹12,000 | ₹6,00,000 – ₹12,00,000 | ₹50L–₹1Cr |
| Year 2 | 200–500 | ₹13,000 | ₹26L – ₹65L | ₹3Cr – ₹8Cr |

All transactions are monthly recurring subscriptions with a fixed amount per customer.

### Razorpay Products Required

| Product | Use case | Status |
|---------|---------|--------|
| **Razorpay Payment Gateway** | One-time order at end of 7-day trial (first charge) | Required Day 1 |
| **Razorpay Subscriptions** | Monthly auto-debit after first payment | Required Day 1 |
| **Razorpay Webhooks** | `payment.captured`, `subscription.charged`, `subscription.cancelled` events to update DB | Required Day 1 |
| Razorpay Route | Splitting between platform and agent owners (future) | Not required yet |

### Chargeback & Refund Policy

| Scenario | Policy |
|----------|--------|
| Trial cancellation (within 7 days) | No charge — trial is free, no refund needed |
| Post-payment cancellation | Pro-rated refund for unused days in current month |
| Dispute / chargeback | Customer support reviews audit trail; unconstitutional agent actions refunded within 5 business days |
| Fraud prevention | Turnstile CAPTCHA + OTP verification before payment; Razorpay's built-in fraud detection enabled |

### Business Legitimacy & Compliance

| Compliance area | Status |
|----------------|--------|
| GST registration | In process (startup) |
| PAN | Available |
| Bank account | Current account (to be provided at KYC) |
| Privacy Policy | Published at waooaw.com/privacy |
| Terms of Service | Published at waooaw.com/terms |
| Agent accountability | Constitutional audit trail with immutable hash chain (L0 governance) |
| Data residency | All data stored in GCP Mumbai (`asia-south1`) — India data residency |

### Why Razorpay

- **Recurring billing** support for monthly SaaS subscriptions out of the box
- **Indian payment methods** (UPI, NetBanking, cards, wallets) match our SME customer base
- **Webhook reliability** required for our DB-backed subscription state machine
- **Test mode** allows full end-to-end validation before going live — no risk during beta
- **2% fee per transaction** is lower than alternatives at our projected GMV bracket

---

*Document prepared from platform codebase and product specifications.*  
*Source: `/workspaces/WAOOAW/docs/CONTEXT_AND_INDEX.md`, `/workspaces/WAOOAW/README.md`*  
*Contact for verification: ops@waooaw.com*
