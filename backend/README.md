# Agent Creation Factory - Quick Start Guide

## 🎯 Overview

The Agent Creation Factory is WAOOAW's systematic framework for creating AI agent workforces using a clear, modular architecture:

**Components → Skills → Roles → Teams**

## 📚 Documentation

See [AGENT_CREATION_FACTORY.md](../docs/AGENT_CREATION_FACTORY.md) for complete documentation.

## 🚀 Quick Start

### 1. Start Backend API

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API available at:
- Base: http://localhost:8000
- Health: http://localhost:8000/health
- Docs: http://localhost:8000/api/docs

### 2. Start Frontend

```bash
cd frontend
python -m http.server 8080
```

Frontend at: http://localhost:8080/domain-designer.html

## 🔧 API Endpoints

### Domain Management

```bash
# List all domains
GET /api/domain-factory/domains

# Get domain details
GET /api/domain-factory/domains/{domain_id}

# Create new domain
POST /api/domain-factory/domains
```

### Components, Skills, Roles, Teams

```bash
# Components (technical infrastructure)
GET /api/domain-factory/domains/{domain_id}/components

# Skills (modular capabilities)
GET /api/domain-factory/domains/{domain_id}/skills

# Roles (complete agents)
GET /api/domain-factory/domains/{domain_id}/roles

# Team (bundled workforce)
GET /api/domain-factory/domains/{domain_id}/team
```

### Domain Specification Manager

```bash
# Start interview for new industry
POST /api/domain-factory/domain-spec-manager/interview?industry_name=YourIndustry

# Generate specification
POST /api/domain-factory/domain-spec-manager/generate

# Validate specification
GET /api/domain-factory/domain-spec-manager/validate/{domain_id}
```

## 💡 Architecture

```
Domain (e.g., Digital Marketing)
  ↓
Components (Technical Infrastructure)
  - GPT-4, Claude, Llama (LLMs)
  - Google Analytics API
  - LinkedIn/Twitter APIs
  ↓
Skills (Modular Capabilities)
  - Blog Writing (₹3K/mo)
  - SEO Analysis (₹4K/mo)
  - Social Posting (₹2.5K/mo)
  ↓
Roles (Complete Agents)
  - Content Marketing Agent (₹15K/mo)
  - Social Media Manager (₹12K/mo)
  ↓
Teams (Bundled Workforces)
  - Marketing Workforce (₹75K/mo, 20% discount)
```

## 📊 Business Model

- **85% revenue**: Role subscriptions (₹8-30K/month)
- **10% revenue**: Skills marketplace (individual skills ₹2-5K/month)
- **5% revenue**: Enterprise features

## 🎯 Examples

### List Domains
```bash
curl http://localhost:8000/api/domain-factory/domains
```

### Get Domain Details
```bash
curl http://localhost:8000/api/domain-factory/domains/digital-marketing
```

### Start Interview
```bash
curl -X POST "http://localhost:8000/api/domain-factory/domain-spec-manager/interview?industry_name=Real%20Estate"
```

---

**Version**: 2.0.0  
**Status**: ✅ Aligned with WAOOAW Vision  
**Last Updated**: December 23, 2025
