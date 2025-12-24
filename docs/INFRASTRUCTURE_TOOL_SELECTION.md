# Infrastructure Tool Selection

**WAOOAW Platform Infrastructure Decisions**

*Version 1.0 | Decision Date: 2025-12-24*

---

## Executive Summary

### Decision Overview

- **Decision Date**: 2025-12-24
- **Decided By**: dlai-sd (Platform Architect)
- **Recommended By**: WowVision (AI Assistant)
- **Decision**: **Start with FREE tier tools, upgrade as needed**

### Key Decisions

| Component | Selected Tool | Tier | Monthly Cost |
|-----------|--------------|------|--------------|
| **PostgreSQL** | Supabase | Free | $0 |
| **Vector Database** | Pinecone | Starter | $70 |
| **LLM API** | Claude Sonnet 4.5 | Pay-as-you-go | ~$20-50 |
| **Execution Environment** | GitHub Actions | Free | $0 |
| **Total** | - | - | **~$90-120/month** |

### Philosophy

**Start Lean, Scale Smart**:
- Use free tiers for infrastructure services (database, compute)
- Pay only for value-added services (AI, vector search)
- Upgrade incrementally based on actual usage
- Maintain portability (Docker-first, cloud-agnostic)

---

## Table of Contents

1. [Infrastructure Requirements](#1-infrastructure-requirements)
2. [PostgreSQL Options](#2-postgresql-options)
3. [Vector Database Options](#3-vector-database-options)
4. [LLM API Options](#4-llm-api-options)
5. [Execution Environment Options](#5-execution-environment-options)
6. [Cost Analysis](#6-cost-analysis)
7. [Current Implementation](#7-current-implementation)
8. [Future Upgrade Path](#8-future-upgrade-path)
9. [Decision Rationale](#9-decision-rationale)
10. [Quick Start Guide](#10-quick-start-guide)

---

## 1. Infrastructure Requirements

### What WowVision Prime Needs

```
┌─────────────────────────────────────────────┐
│  WowVision Prime Architecture              │
├─────────────────────────────────────────────┤
│  1. PostgreSQL (Relational Database)       │
│     - Agent memory (context, decisions)    │
│     - 10 tables (versioned storage)        │
│     - ACID transactions required           │
│     - Initial: <100MB, Growth: ~5GB/year   │
│                                             │
│  2. Vector Database (Semantic Search)      │
│     - Pinecone for similarity search       │
│     - Cost optimization (cache decisions)  │
│     - 1536-dimension embeddings            │
│     - Initial: ~10K vectors, Growth: 1M+   │
│                                             │
│  3. LLM API (Intelligence Layer)           │
│     - Claude Sonnet 4.5 (Anthropic)        │
│     - Used for 2% of decisions only        │
│     - Hybrid decision framework            │
│     - Estimated: 200 calls/day             │
│                                             │
│  4. Execution Environment                  │
│     - GitHub Actions (CI/CD)               │
│     - Scheduled workflows (every 6 hours)  │
│     - Event-driven triggers                │
│     - Timeout: 10 minutes per run          │
└─────────────────────────────────────────────┘
```

### Requirements Summary

| Component | Key Requirements | Performance Needs | Cost Sensitivity |
|-----------|-----------------|-------------------|------------------|
| **PostgreSQL** | ACID, versioning, <1s queries | 100 queries/hour | High (prefer free) |
| **Vector DB** | 1536-dim, cosine similarity, <100ms | 50 queries/hour | Medium (worth paying) |
| **LLM API** | Claude Sonnet 4.5, streaming, <5s | 200 calls/day | Low (core value) |
| **Execution** | Scheduled runs, event triggers | 24/7 availability | High (prefer free) |

---

## 2. PostgreSQL Options

### Evaluation Matrix

| Tool | Free Tier | Paid Tier | Pros | Cons | Score |
|------|-----------|-----------|------|------|-------|
| **Supabase** | ✅ 500MB, 2 projects | $25/mo (8GB) | • Easy setup<br>• Realtime subscriptions<br>• Built-in auth<br>• RESTful API<br>• Dashboard UI | • Limited storage (500MB)<br>• Pauses after 1 week inactivity | ⭐⭐⭐⭐⭐ |
| **Neon** | ✅ 3GB, 10 projects | $19/mo (unlimited) | • Generous free tier (3GB)<br>• Serverless architecture<br>• Instant branching<br>• No pause limit | • Newer service<br>• Limited docs | ⭐⭐⭐⭐ |
| **Railway** | ✅ $5 credit/mo | $5-20/mo (usage) | • Simple deployment<br>• Auto-scaling<br>• Multiple services | • Credit-based (not truly free)<br>• Can get expensive | ⭐⭐⭐ |
| **AWS RDS** | ✅ 750hr/mo (t2.micro) | $15-100/mo | • Production-grade<br>• Full control<br>• Mature service | • Complex setup<br>• Must manage backups<br>• Free tier only 12 months | ⭐⭐⭐ |
| **Heroku Postgres** | ✅ 10K rows (1GB) | $9-50/mo | • Dead simple setup<br>• Heroku ecosystem | • Row limit (not GB)<br>• Expensive for scale | ⭐⭐ |

### Detailed Comparison

#### Supabase (SELECTED ✅)

**Free Tier**:
- Storage: 500MB
- Projects: 2
- Bandwidth: Unlimited
- API Requests: Unlimited
- Realtime: 200 concurrent connections
- Auth: 50K monthly active users
- **Limitation**: Pauses after 1 week inactivity (can wake with first request)

**Paid Tier** ($25/month):
- Storage: 8GB
- Projects: Unlimited
- No pause
- Point-in-time recovery
- Daily backups

**Pros**:
- **Easiest setup**: Connection string ready in 30 seconds
- **Realtime out-of-the-box**: PostgreSQL pub/sub via WebSockets
- **RESTful API**: Auto-generated from schema (PostgREST)
- **Beautiful dashboard**: Schema editor, SQL editor, logs
- **Auth included**: JWT-based auth with social providers
- **Storage included**: File uploads with buckets

**Cons**:
- **500MB limit**: May need upgrade after ~50K agent wake cycles
- **Inactivity pause**: Wakes on first request (adds ~1s latency)
- **Vendor lock-in**: Relies on Supabase ecosystem

**Best For**: MVP, early-stage, teams wanting all-in-one solution

**Migration Path**: Standard PostgreSQL → easy to migrate out via pg_dump

---

#### Neon

**Free Tier**:
- Storage: 3GB (6x more than Supabase)
- Projects: 10
- Compute: 300 compute hours/month
- **No pause after inactivity** (major advantage)

**Paid Tier** ($19/month):
- Storage: Unlimited
- Compute: Unlimited
- Branching: Instant database branches (like Git)

**Pros**:
- **Generous free tier**: 3GB vs 500MB
- **No pause**: Always available
- **Branching**: Create database branches for testing
- **Serverless**: Auto-scale compute

**Cons**:
- **Newer service**: Less mature than competitors
- **Fewer features**: No built-in auth, storage, realtime

**Best For**: Projects needing more storage, database branching for testing

---

#### Railway

**Free Tier**:
- $5 credit per month
- ~100-200 hours of small instance

**Paid Tier**:
- Pay for what you use ($0.20/GB-month storage, $10/vCPU-month)

**Pros**:
- **Simple deployment**: `railway up` and done
- **Multi-service**: Deploy app + DB together
- **Auto-scaling**: Scales with traffic

**Cons**:
- **Not truly free**: $5 credit runs out quickly
- **Usage-based**: Hard to predict costs
- **Limited free tier**: Only for experimentation

**Best For**: Full-stack deployments, teams wanting all services in one place

---

#### AWS RDS

**Free Tier**:
- 750 hours/month of db.t2.micro (1 vCPU, 1GB RAM)
- 20GB storage
- **Only for first 12 months**

**Paid Tier**:
- db.t3.micro: ~$15/month
- db.t3.small: ~$30/month
- Storage: $0.10/GB-month

**Pros**:
- **Production-grade**: Battle-tested at scale
- **Full control**: Configure everything
- **Security**: VPC, encryption, IAM

**Cons**:
- **Complex setup**: Requires AWS knowledge
- **No forever-free tier**: Must pay after 12 months
- **Management overhead**: Backups, updates, monitoring

**Best For**: Enterprise, compliance-heavy projects, teams already on AWS

---

### Winner: **Supabase**

**Why Supabase?**
1. ✅ **Free forever** (not just 12 months)
2. ✅ **Easiest setup** (connection string in 30 seconds)
3. ✅ **Sufficient for MVP** (500MB = 50K+ wake cycles)
4. ✅ **Rich ecosystem** (auth, storage, realtime included)
5. ✅ **Standard PostgreSQL** (easy migration if needed)

**Risk Mitigation**:
- Use Docker for local development (portability)
- Keep connection string in environment variables (easy swap)
- Monitor storage usage (upgrade before 400MB)
- pg_dump backups weekly (DIY backup strategy)

---

## 3. Vector Database Options

### Evaluation Matrix

| Tool | Free Tier | Paid Tier | Pros | Cons | Score |
|------|-----------|-----------|------|------|-------|
| **Pinecone** | ❌ No free tier | $70/mo (1M vectors) | • Production-ready<br>• Lowest latency<br>• Best docs<br>• Managed service | • No free tier<br>• Expensive at scale | ⭐⭐⭐⭐⭐ |
| **Weaviate Cloud** | ✅ Free sandbox | $25/mo (100K vectors) | • Open source<br>• Free sandbox<br>• GraphQL API | • Sandbox limited<br>• Less mature | ⭐⭐⭐⭐ |
| **Qdrant Cloud** | ✅ 1GB free | $25/mo (1M vectors) | • Open source<br>• Generous free tier<br>• Fast | • Smaller ecosystem<br>• Fewer integrations | ⭐⭐⭐⭐ |
| **Milvus** | ✅ Self-hosted free | Cloud pricing varies | • Open source<br>• Highly scalable<br>• Feature-rich | • Complex setup<br>• Requires ops knowledge | ⭐⭐⭐ |
| **Chroma** | ✅ Free (embedded) | N/A (self-hosted) | • Embedded (no server)<br>• Simple API<br>• Free | • Not for production<br>• In-memory only | ⭐⭐ |

### Detailed Comparison

#### Pinecone (SELECTED ✅)

**Pricing**:
- **Starter**: $70/month
  - 1M vectors (1536 dimensions)
  - 100K queries/month
  - 1 index
- **Standard**: $0.096/million vectors/month (usage-based)

**Pros**:
- **Production-ready**: Used by OpenAI, Scale, etc.
- **Lowest latency**: <50ms query time (p99)
- **Best documentation**: Comprehensive guides, examples
- **Managed service**: Zero ops overhead
- **Native integrations**: LangChain, LlamaIndex, etc.
- **Reliability**: 99.9% SLA

**Cons**:
- **No free tier**: Must pay $70/month minimum
- **Expensive at scale**: $96/month per million vectors
- **Vendor lock-in**: Proprietary service

**Best For**: Production workloads, teams wanting zero ops

**Why Worth the Cost?**:
- **Core to product value**: Semantic search is key feature
- **Saves LLM costs**: Vector search ($70/mo) prevents ~700 LLM calls/month ($70 saved)
- **ROI positive**: Each prevented LLM call = $0.10 saved
- **Time saved**: No ops overhead = focus on features

---

#### Weaviate Cloud

**Pricing**:
- **Sandbox**: Free (limited, not for production)
- **Starter**: $25/month (100K vectors)
- **Professional**: $95/month (1M vectors)

**Pros**:
- **Open source**: Can self-host if needed
- **Free sandbox**: For development/testing
- **GraphQL API**: Flexible querying
- **Hybrid search**: Vector + keyword combined

**Cons**:
- **Sandbox limitations**: Not for production
- **Less mature**: Smaller community
- **Setup complexity**: More config required

**Best For**: Teams wanting open-source option with managed hosting

---

#### Qdrant Cloud

**Pricing**:
- **Free**: 1GB storage (~100K vectors)
- **Starter**: $25/month (1M vectors)

**Pros**:
- **Generous free tier**: 1GB for experimentation
- **Open source**: Self-host option
- **Fast**: Rust-based, low latency
- **Simple API**: RESTful + gRPC

**Cons**:
- **Smaller ecosystem**: Fewer integrations
- **Less documentation**: Compared to Pinecone
- **Free tier limited**: 1GB may not be enough

**Best For**: Cost-conscious teams, Rust enthusiasts

---

#### Milvus

**Pricing**:
- **Self-hosted**: Free (but requires infrastructure)
- **Zilliz Cloud** (managed Milvus): Pricing varies

**Pros**:
- **Open source**: Full control
- **Highly scalable**: Handles billions of vectors
- **Feature-rich**: Advanced filtering, hybrid search

**Cons**:
- **Complex setup**: Requires Kubernetes, MinIO, etc.
- **Ops overhead**: Must manage infrastructure
- **Overkill for MVP**: Too complex for small projects

**Best For**: Large-scale projects (1B+ vectors), teams with DevOps capacity

---

#### Chroma

**Pricing**:
- **Free**: Embedded mode (no server)

**Pros**:
- **Embedded**: No server, runs in-process
- **Simple API**: Minimal setup
- **Free**: No cost

**Cons**:
- **Not for production**: In-memory only, no persistence guarantees
- **No managed option**: Must self-host for persistence
- **Limited scale**: Not designed for large datasets

**Best For**: Local development, prototyping

---

### Winner: **Pinecone**

**Why Pinecone?**
1. ✅ **Production-ready** (99.9% SLA, battle-tested)
2. ✅ **Lowest latency** (<50ms queries)
3. ✅ **Zero ops overhead** (fully managed)
4. ✅ **ROI positive** (saves LLM costs)
5. ✅ **Best ecosystem** (integrations, docs, community)

**Cost Justification**:
```
Vector search cost: $70/month
LLM calls prevented: ~700/month × $0.10 = $70 saved
Net cost: $0 (break-even)

PLUS:
- Faster responses (<50ms vs 2-5s LLM)
- Better UX (instant vs waiting)
- Scalable (1M vectors ready)
```

**Alternative for Experimentation**: Use **Qdrant Cloud free tier** (1GB) during development, migrate to Pinecone for production.

---

## 4. LLM API Options

### Evaluation Matrix

| Tool | Model | Cost (Input/Output) | Pros | Cons | Score |
|------|-------|---------------------|------|------|-------|
| **Claude Sonnet 4.5** | Anthropic | $3/$15 per 1M tokens | • Best reasoning<br>• Longest context (200K)<br>• Safest outputs | • Most expensive<br>• Rate limits | ⭐⭐⭐⭐⭐ |
| **GPT-4 Turbo** | OpenAI | $10/$30 per 1M tokens | • Strong reasoning<br>• Rich ecosystem<br>• Vision support | • Very expensive<br>• Slower than Claude | ⭐⭐⭐⭐ |
| **Gemini 1.5 Pro** | Google | $1.25/$5 per 1M tokens | • Cheapest<br>• Good reasoning<br>• Multimodal | • Less reliable<br>• Weaker reasoning | ⭐⭐⭐ |
| **Mixtral 8x7B** | Together/Anyscale | $0.60/$0.60 per 1M tokens | • Open source<br>• Very cheap<br>• Fast | • Weaker reasoning<br>• Shorter context | ⭐⭐ |

### Detailed Comparison

#### Claude Sonnet 4.5 (SELECTED ✅)

**Pricing**:
- **Input**: $3 per 1M tokens (~750K words)
- **Output**: $15 per 1M tokens (~750K words)
- **Typical decision**: ~2K input + 500 output = **$0.01 per decision**

**Pros**:
- **Best reasoning**: Superior logic, fewer hallucinations
- **Longest context**: 200K tokens (entire codebase in context)
- **Safest**: Constitutional AI → less likely to produce harmful outputs
- **Streaming**: Real-time response streaming
- **Helpful**: Follows instructions precisely

**Cons**:
- **Most expensive**: 3x more than Gemini
- **Rate limits**: 50 requests/minute (sufficient for our use)

**Best For**: High-stakes decisions, complex reasoning, production agents

**Usage Estimate**:
```
200 decisions/day × $0.01 = $2/day
$2/day × 30 days = $60/month per agent
```

**Why Claude?**:
- **Quality > cost**: Agent decisions are critical
- **Hybrid framework**: Only 2% of decisions use LLM (98% free)
- **ROI**: One prevented bad decision = $1000+ saved (customer churn)

---

#### GPT-4 Turbo

**Pricing**:
- **Input**: $10 per 1M tokens
- **Output**: $30 per 1M tokens
- **Typical decision**: ~$0.03 per decision (3x Claude)

**Pros**:
- **Strong reasoning**: Nearly as good as Claude
- **Rich ecosystem**: Vast library of tools (LangChain, etc.)
- **Vision support**: Can analyze images
- **Function calling**: Native tool use

**Cons**:
- **Very expensive**: 3x Claude, 10x Gemini
- **Slower**: 5-10s response time vs Claude's 2-5s

**Best For**: Teams already on OpenAI ecosystem, vision-heavy workloads

---

#### Gemini 1.5 Pro

**Pricing**:
- **Input**: $1.25 per 1M tokens
- **Output**: $5 per 1M tokens
- **Typical decision**: ~$0.003 per decision (3x cheaper than Claude)

**Pros**:
- **Cheapest**: 2.4x cheaper than Claude
- **Good reasoning**: Acceptable for most tasks
- **Multimodal**: Handles text, images, audio
- **Fast**: 2-3s response time

**Cons**:
- **Less reliable**: More hallucinations, inconsistent quality
- **Weaker reasoning**: Struggles with complex logic
- **Newer**: Less proven at scale

**Best For**: Cost-sensitive projects, simple tasks, multimodal needs

---

#### Mixtral 8x7B (Open Source)

**Pricing**:
- **Together AI**: $0.60/$0.60 per 1M tokens
- **Anyscale**: $0.50/$0.50 per 1M tokens
- **Self-hosted**: Free (but requires GPUs)

**Pros**:
- **Very cheap**: 5x cheaper than Claude
- **Open source**: Can self-host
- **Fast**: Low latency on Together/Anyscale

**Cons**:
- **Weaker reasoning**: Not suitable for complex decisions
- **Shorter context**: 32K tokens (vs Claude's 200K)
- **Less reliable**: Higher error rate

**Best For**: Simple tasks, experimentation, cost-critical projects

---

### Winner: **Claude Sonnet 4.5**

**Why Claude?**
1. ✅ **Best reasoning** (critical for agent decisions)
2. ✅ **Longest context** (200K tokens = full codebase awareness)
3. ✅ **Safest outputs** (Constitutional AI)
4. ✅ **Proven at scale** (used by top AI companies)
5. ✅ **Worth the cost** (quality > price for decisions)

**Cost Justification**:
- **Hybrid framework**: Only 2% of decisions use LLM
- **High stakes**: One bad decision costs more than 1000 LLM calls
- **Quality multiplier**: Better reasoning = better product

**Fallback Strategy**:
- Use **Gemini 1.5 Pro** for low-stakes decisions (comments, summaries)
- Use **Claude** for high-stakes decisions (approvals, architecture changes)
- Monitor: If quality issues, switch entirely to Claude

---

## 5. Execution Environment Options

### Evaluation Matrix

| Tool | Free Tier | Paid Tier | Pros | Cons | Score |
|------|-----------|-----------|------|------|-------|
| **GitHub Actions** | ✅ 2,000 min/mo | $0.008/min | • Native to GitHub<br>• Cron scheduling<br>• Event triggers<br>• Matrix builds | • 2K min limit<br>• Cold starts | ⭐⭐⭐⭐⭐ |
| **Railway** | ✅ $5 credit | $5-20/mo | • Always-on<br>• Auto-deploy<br>• Simple setup | • Not truly free<br>• For web services | ⭐⭐⭐⭐ |
| **Render** | ✅ Free tier | $7-25/mo | • Free cron jobs<br>• Always-on option<br>• Docker support | • Free tier sleeps<br>• Cold starts | ⭐⭐⭐⭐ |
| **AWS Lambda** | ✅ 1M requests/mo | $0.20/1M requests | • Serverless<br>• Massive free tier<br>• Event-driven | • 15 min timeout<br>• Complex setup | ⭐⭐⭐ |
| **Vercel Cron** | ✅ Hobby plan | $20/mo (Pro) | • Dead simple<br>• Fast deploys | • For Next.js mainly<br>• 10s timeout | ⭐⭐ |

### Detailed Comparison

#### GitHub Actions (SELECTED ✅)

**Free Tier**:
- **Minutes**: 2,000/month
- **Storage**: 500MB artifacts
- **Concurrent jobs**: 20
- **Our usage**: ~720 minutes/month (24 wake-ups/day × 10 min each × 3 agents)

**Paid Tier** ($0.008/minute):
- Pay only for what you use beyond 2,000 min

**Pros**:
- **Native integration**: Already using GitHub for code
- **Cron scheduling**: `schedule: "*/5 * * * *"` (every 5 min)
- **Event-driven**: Triggers on commits, PRs, issues, webhooks
- **Matrix builds**: Test multiple configurations
- **Secrets management**: Built-in secrets vault
- **Artifacts**: Store logs, reports
- **Free**: 2,000 minutes = 200 agent runs/month (sufficient for MVP)

**Cons**:
- **Time limits**: 2,000 min/month on free tier
- **Cold starts**: 10-20s startup time (acceptable)
- **Max duration**: 6 hours per job (way more than needed)

**Best For**: Open-source projects, CI/CD, scheduled tasks

**Usage Estimate**:
```
3 agents × 8 wake-ups/day × 10 min each = 240 min/day
240 min/day × 30 days = 7,200 min/month
7,200 - 2,000 (free) = 5,200 min paid
5,200 × $0.008 = $41.60/month

BUT: Optimize to 5 min/run → 3,600 min/month → $12.80/month
```

**Why GitHub Actions?**:
- **Native to workflow**: Code, CI, agents all in one place
- **Sufficient free tier**: 2K min = 33 hours (enough for 3 agents)
- **Easy scaling**: Just pay per minute when needed
- **Zero ops**: No servers to manage

---

#### Railway

**Pricing**:
- **Free**: $5 credit/month (~100 hours of small instance)
- **Paid**: $5/month minimum + usage

**Pros**:
- **Always-on**: No cold starts
- **Auto-deploy**: Push to deploy
- **Multi-service**: DB + app together

**Cons**:
- **Not truly free**: $5 credit runs out
- **For web services**: Optimized for HTTP, not cron
- **Overkill**: Don't need always-on for scheduled tasks

**Best For**: Web apps, APIs, services needing 24/7 uptime

---

#### Render

**Pricing**:
- **Free**: Cron jobs available (sleeps after inactivity)
- **Paid**: $7-25/month for always-on

**Pros**:
- **Free cron jobs**: Built-in scheduling
- **Docker support**: Deploy containers easily
- **Simple setup**: `render.yaml` config

**Cons**:
- **Sleeps on free**: Cold starts on free tier
- **Less flexible**: Than GitHub Actions for CI/CD

**Best For**: Web apps, background jobs, teams not on GitHub

---

#### AWS Lambda

**Pricing**:
- **Free**: 1M requests/month, 400K GB-seconds compute
- **Paid**: $0.20 per 1M requests, $0.00001667 per GB-second

**Pros**:
- **Serverless**: Pay only when running
- **Massive free tier**: 1M requests (way more than needed)
- **Event-driven**: Triggers from anywhere

**Cons**:
- **15-minute timeout**: Not enough for long agent runs
- **Complex setup**: IAM, VPC, CloudWatch, etc.
- **Cold starts**: 1-2s (less than GitHub Actions)

**Best For**: AWS-native stacks, microservices, event-driven architectures

---

#### Vercel Cron

**Pricing**:
- **Hobby**: Free (with limits)
- **Pro**: $20/month

**Pros**:
- **Dead simple**: Add `cron` to `vercel.json`
- **Fast deploys**: Push to deploy in seconds

**Cons**:
- **For Next.js**: Mainly for Next.js apps
- **10-second timeout**: Not enough for agent runs
- **Limited flexibility**: Compared to GitHub Actions

**Best For**: Next.js apps, simple scheduled tasks

---

### Winner: **GitHub Actions**

**Why GitHub Actions?**
1. ✅ **Native integration** (already on GitHub)
2. ✅ **Sufficient free tier** (2,000 min = 33 hours)
3. ✅ **Cron scheduling** (built-in)
4. ✅ **Event-driven** (webhooks, commits, PRs)
5. ✅ **Zero ops** (no servers to manage)

**Cost Optimization**:
- Start with free tier (2,000 min)
- Optimize run time (5 min → more runs)
- Scale horizontally (more agents → pay per use)
- Fallback: Migrate to Railway/Render if costs exceed $50/month

---

## 6. Cost Analysis

### Monthly Cost Breakdown

| Component | Service | Tier | Cost | Usage |
|-----------|---------|------|------|-------|
| **PostgreSQL** | Supabase | Free | $0 | 500MB storage |
| **Vector DB** | Pinecone | Starter | $70 | 1M vectors |
| **LLM API** | Claude Sonnet 4.5 | Pay-as-you-go | $20-50 | 200-500 calls/day |
| **Execution** | GitHub Actions | Free | $0 | 2,000 min/month |
| **OpenAI Embeddings** | OpenAI | Pay-as-you-go | $0.50 | 10K embeddings/month |
| **Redis** | Railway Free / Self-hosted | Free | $0 | In-memory cache |
| **Monitoring** | GitHub Logs / Self-hosted | Free | $0 | Basic logs |
| **Total** | - | - | **$90-120** | 3 active agents |

### Cost Scaling by Usage

| Agents | PostgreSQL | Vector DB | LLM API | Execution | Total |
|--------|-----------|-----------|---------|-----------|-------|
| **1-3** | $0 (Supabase Free) | $70 (Pinecone) | $20-50 | $0 (GitHub Free) | **$90-120** |
| **4-6** | $25 (Supabase Pro) | $70 (Pinecone) | $60-150 | $10 (GitHub) | **$165-255** |
| **7-10** | $25 (Supabase Pro) | $140 (Pinecone 2M) | $140-350 | $30 (GitHub) | **$335-545** |
| **11-14** | $50 (Supabase Team) | $210 (Pinecone 3M) | $220-490 | $50 (GitHub) | **$530-800** |

### Cost per Agent

```
With current setup (3 agents):
$90-120 / 3 agents = $30-40 per agent/month

At full scale (14 agents):
$530-800 / 14 agents = $38-57 per agent/month
```

### Cost Optimization Strategies

1. **Hybrid Decision Framework**:
   - 60% decisions from cache (FREE)
   - 30% from deterministic logic (FREE)
   - 8% from vector search ($0.0001 each)
   - 2% from LLM ($0.01-0.10 each)
   - **Result**: 90%+ cost reduction vs pure LLM

2. **Batch Processing**:
   - Group similar decisions → one LLM call
   - **Result**: 5-10x fewer LLM calls

3. **Scheduled Wake Times**:
   - Wake agents every 6 hours (not every 5 min)
   - **Result**: 72x fewer GitHub Action minutes

4. **Smart Caching**:
   - Cache LLM decisions for 1 hour
   - **Result**: 30-50% fewer LLM calls

5. **Free Tier Maximization**:
   - Use Supabase (500MB free) until 400MB
   - Use GitHub Actions (2K min) until 1.8K min
   - **Result**: Delay paid upgrades by 6-12 months

### When to Upgrade

| Trigger | Current Limit | Upgrade Path | New Cost |
|---------|--------------|--------------|----------|
| **Storage > 400MB** | Supabase Free (500MB) | Supabase Pro (8GB) | +$25/mo |
| **Vectors > 800K** | Pinecone Starter (1M) | Pinecone 2M | +$70/mo |
| **GH Actions > 1,800 min** | Free (2K min) | Pay-per-use | +$10-30/mo |
| **Agents > 3** | Current setup | Scale linearly | +$30-40/agent |

---

## 7. Current Implementation

### Selected Stack

```yaml
Infrastructure:
  PostgreSQL:
    Service: Supabase
    Tier: Free
    Storage: 500MB
    Connection: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
    
  Vector Database:
    Service: Pinecone
    Tier: Starter ($70/month)
    Capacity: 1M vectors
    Index: waooaw-memory
    Dimensions: 1536
    
  LLM API:
    Service: Anthropic Claude
    Model: claude-sonnet-4.5-20250514
    Tier: Pay-as-you-go
    Cost: ~$20-50/month
    
  Execution:
    Service: GitHub Actions
    Tier: Free (2,000 min/month)
    Schedule: Every 6 hours (4x/day per agent)
    Workflow: .github/workflows/wowvision-prime.yml
    
  Caching:
    Service: Redis (Railway Free or self-hosted)
    Tier: Free
    Usage: Decision cache, session state
    
  Monitoring:
    Service: GitHub Actions logs + PostgreSQL queries
    Tier: Free
    Retention: 7 days
```

### Environment Variables

```bash
# PostgreSQL (Supabase)
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
DB_HOST=[HOST].supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=[PASSWORD]

# Pinecone
PINECONE_API_KEY=[KEY]
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX=waooaw-memory

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-[KEY]

# GitHub
GITHUB_TOKEN=ghp_[TOKEN]
GITHUB_REPO=dlai-sd/WAOOAW

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-[KEY]

# Redis (if using Railway)
REDIS_URL=redis://:[PASSWORD]@[HOST]:6379
```

### Quick Setup

```bash
# 1. Create Supabase project
# Visit: https://supabase.com/dashboard
# Create project → Get connection string

# 2. Create Pinecone index
# Visit: https://app.pinecone.io
# Create index: waooaw-memory, dimensions: 1536, metric: cosine

# 3. Get Anthropic API key
# Visit: https://console.anthropic.com
# Create API key → Copy key

# 4. Set GitHub secrets
gh secret set DATABASE_URL
gh secret set PINECONE_API_KEY
gh secret set ANTHROPIC_API_KEY
gh secret set OPENAI_API_KEY

# 5. Deploy workflow
git add .github/workflows/wowvision-prime.yml
git commit -m "Add WowVision Prime workflow"
git push

# 6. Trigger manually (test)
gh workflow run "WowVision Prime Agent"

# 7. Check logs
gh run list --workflow="WowVision Prime Agent"
gh run view [RUN_ID] --log
```

---

## 8. Future Upgrade Path

### Phase 1: MVP (Current) - **$90-120/month**
**Agents**: 1-3  
**Services**: Supabase Free, Pinecone Starter, Claude, GitHub Actions Free

**Triggers for Phase 2**:
- Storage > 400MB (approaching Supabase 500MB limit)
- Vectors > 800K (approaching Pinecone 1M limit)
- GitHub Actions > 1,800 min/month

---

### Phase 2: Growth - **$165-255/month**
**Agents**: 4-6  
**Upgrades**:
- ✅ **Supabase Pro** ($25/month): 8GB storage, no pause
- ✅ **GitHub Actions pay-per-use** (~$10/month): Beyond 2K min
- ⚠️ Consider: **Neon** (if wanting branching for testing)

**Triggers for Phase 3**:
- Agents > 6
- Vectors > 1.5M
- LLM costs > $150/month

---

### Phase 3: Scale - **$335-545/month**
**Agents**: 7-10  
**Upgrades**:
- ✅ **Pinecone 2M vectors** (+$70/month): Double capacity
- ✅ **GitHub Actions** (~$30/month): More scheduled runs
- ⚠️ Consider: **AWS RDS** (if needing advanced DB features)

**Triggers for Phase 4**:
- Agents > 10
- Need multi-region (latency)
- Need compliance (HIPAA, SOC2)

---

### Phase 4: Enterprise - **$530-800/month**
**Agents**: 11-14  
**Upgrades**:
- ✅ **Supabase Team/Enterprise**: Multi-region, SLA
- ✅ **Pinecone 3M vectors** (+$70/month): Triple capacity
- ✅ **AWS RDS or Aurora**: If needing advanced features
- ✅ **Kubernetes**: If needing custom execution environment
- ✅ **DataDog/New Relic**: Advanced monitoring

**Beyond Phase 4**:
- Self-hosted infrastructure (if costs > $2K/month)
- Dedicated GPU instances (if needing local LLMs)
- Multi-cloud (if needing 99.99% SLA)

---

## 9. Decision Rationale

### Why These Choices?

#### 1. Start with Free Tiers
**Rationale**: Minimize upfront costs, validate product-market fit before investing.

**Alternatives Considered**:
- ❌ AWS from day 1 → Complex, expensive, overkill
- ❌ Self-hosted Postgres → Ops overhead, not worth it
- ✅ Supabase/GitHub Actions → Zero cost, zero ops

---

#### 2. Pay for Value-Added Services
**Rationale**: Vector search and LLM are core product differentiators, worth paying for quality.

**Alternatives Considered**:
- ❌ Self-hosted Milvus → Too complex for MVP
- ❌ Open-source LLMs (Mixtral) → Insufficient quality
- ✅ Pinecone + Claude → Production-grade, proven

---

#### 3. Docker-First, Cloud-Agnostic
**Rationale**: Avoid vendor lock-in, maintain portability.

**Alternatives Considered**:
- ❌ Vercel/Netlify serverless → Lock-in to platform
- ❌ AWS-specific services → Hard to migrate out
- ✅ Docker + standard PostgreSQL → Easy migration

---

#### 4. Hybrid Decision Framework
**Rationale**: 90%+ cost reduction by using LLM only for complex cases.

**Alternatives Considered**:
- ❌ Pure LLM → $500-1000/month per agent (not viable)
- ❌ Pure rule-based → Inflexible, limited intelligence
- ✅ Hybrid (cache + rules + vectors + LLM) → Best of both worlds

---

#### 5. GitHub Actions over Alternatives
**Rationale**: Native to workflow, sufficient free tier, zero setup.

**Alternatives Considered**:
- ❌ Railway → Not truly free ($5 credit)
- ❌ AWS Lambda → Complex setup, not worth it for MVP
- ✅ GitHub Actions → Already using GitHub, free 2K min

---

### Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| **Supabase pauses (inactivity)** | Wake-up request adds <1s latency (acceptable) |
| **Pinecone cost grows** | Monitor vectors, upgrade only when needed |
| **LLM costs spike** | Rate limiting, caching, alert at $100/month |
| **GitHub Actions minutes exceed** | Optimize run time, migrate to Railway if costs > $50/mo |
| **Vendor lock-in** | Use Docker, standard PostgreSQL, keep migration scripts |

---

## 10. Quick Start Guide

### Prerequisites

- GitHub account (for Actions and secrets)
- Supabase account (free)
- Pinecone account (starter plan)
- Anthropic account (API key)
- OpenAI account (for embeddings, optional)

### Step-by-Step Setup

#### 1. Create Supabase Database

```bash
# Visit https://supabase.com/dashboard
# Create new project:
#   Name: waooaw-db
#   Database Password: (generate strong password)
#   Region: (closest to you)

# Copy connection string from Settings → Database → Connection string
# Example: postgresql://postgres:[PASSWORD]@[HOST].supabase.co:5432/postgres
```

#### 2. Create Pinecone Index

```bash
# Visit https://app.pinecone.io
# Create new index:
#   Name: waooaw-memory
#   Dimensions: 1536
#   Metric: cosine
#   Region: us-west1-gcp (or closest)
#   Pod Type: Starter

# Copy API key from API Keys section
```

#### 3. Get Anthropic API Key

```bash
# Visit https://console.anthropic.com
# Navigate to API Keys
# Create new key
# Copy key (starts with sk-ant-)
```

#### 4. Get OpenAI API Key (for embeddings)

```bash
# Visit https://platform.openai.com/api-keys
# Create new secret key
# Copy key (starts with sk-)
```

#### 5. Set GitHub Secrets

```bash
# Using GitHub CLI
gh secret set DATABASE_URL
# Paste Supabase connection string

gh secret set PINECONE_API_KEY
# Paste Pinecone API key

gh secret set PINECONE_ENVIRONMENT
# Enter: us-west1-gcp (or your region)

gh secret set PINECONE_INDEX
# Enter: waooaw-memory

gh secret set ANTHROPIC_API_KEY
# Paste Anthropic API key

gh secret set OPENAI_API_KEY
# Paste OpenAI API key (optional)

# Or set via GitHub UI:
# Settings → Secrets and variables → Actions → New repository secret
```

#### 6. Initialize Database Schema

```bash
# Clone repository
git clone https://github.com/dlai-sd/WAOOAW.git
cd WAOOAW

# Connect to Supabase and run schema
psql "$DATABASE_URL" < waooaw/database/base_agent_schema.sql

# Verify tables created
psql "$DATABASE_URL" -c "\dt"
```

#### 7. Deploy GitHub Actions Workflow

```bash
# Workflow already exists at .github/workflows/wowvision-prime.yml
# Just push to enable

git add .github/workflows/wowvision-prime.yml
git commit -m "Enable WowVision Prime workflow"
git push

# Verify workflow
gh workflow list
```

#### 8. Test Workflow Manually

```bash
# Trigger workflow
gh workflow run "WowVision Prime Agent"

# Check status
gh run list --workflow="WowVision Prime Agent"

# View logs
gh run view --log
```

#### 9. Monitor Costs

```bash
# Check Pinecone usage
# Visit: https://app.pinecone.io → Usage

# Check Anthropic usage
# Visit: https://console.anthropic.com → Settings → Billing

# Check GitHub Actions minutes
# Visit: GitHub → Settings → Billing → Plans and usage

# Set up alerts (recommended):
# - Pinecone: Alert at 800K vectors
# - Anthropic: Alert at $50/month
# - GitHub Actions: Alert at 1,800 min/month
```

#### 10. Verify Agent is Working

```bash
# Check recent workflow runs
gh run list --limit 5

# View latest run
gh run view

# Check database for agent activity
psql "$DATABASE_URL" -c "SELECT * FROM agent_context ORDER BY created_at DESC LIMIT 5;"

# Check Pinecone for stored memories
# Python script to verify:
python -c "
from pinecone import Pinecone
import os

pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
index = pc.Index('waooaw-memory')
print(index.describe_index_stats())
"
```

---

## Summary

### Current Setup (Phase 1: MVP)

```yaml
Total Cost: $90-120/month for 3 agents

PostgreSQL: Supabase Free (500MB)
  Cost: $0
  Upgrade Trigger: Storage > 400MB
  Upgrade Path: Supabase Pro ($25/month, 8GB)

Vector Database: Pinecone Starter (1M vectors)
  Cost: $70/month
  Upgrade Trigger: Vectors > 800K
  Upgrade Path: Pinecone 2M ($140/month)

LLM API: Claude Sonnet 4.5
  Cost: $20-50/month (200-500 calls/day)
  Optimization: Hybrid framework (only 2% of decisions)
  Upgrade Trigger: Quality issues or costs > $100/month
  Upgrade Path: Stay on Claude, optimize further

Execution: GitHub Actions Free (2,000 min/month)
  Cost: $0
  Upgrade Trigger: Minutes > 1,800/month
  Upgrade Path: Pay-per-use ($0.008/min)

Monitoring: GitHub logs + PostgreSQL
  Cost: $0
  Upgrade Trigger: Need advanced metrics
  Upgrade Path: Self-hosted Grafana or DataDog
```

### Philosophy

**Start Lean, Scale Smart**:
1. ✅ Use free tiers for infrastructure (database, compute)
2. ✅ Pay for value-added services (AI, vector search)
3. ✅ Monitor usage, upgrade proactively before hitting limits
4. ✅ Maintain portability (Docker, standard PostgreSQL)
5. ✅ Optimize continuously (caching, batching, hybrid decisions)

### Next Steps

1. ✅ Set up Supabase database
2. ✅ Create Pinecone index
3. ✅ Get API keys (Anthropic, OpenAI)
4. ✅ Configure GitHub secrets
5. ✅ Deploy GitHub Actions workflow
6. ✅ Monitor costs weekly
7. ✅ Document learnings for future agents

---

**Last Updated**: 2025-12-24  
**Version**: 1.0  
**Author**: WAOOAW Platform Team  
**Reviewed By**: dlai-sd (Platform Architect), WowVision (AI Assistant)
