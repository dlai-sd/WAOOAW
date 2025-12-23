# Agent Creation Factory - Quick Start Guide

## 🎯 Overview

The Agent Creation Factory is WAOOAW's systematic approach to creating AI agent employees for any industry using the **Kitchen Analogy**:

- 🧂 **Ingredients** - Basic building blocks (AI models, APIs, tools)
- 🍲 **Components** - Reusable modules (Subject Matter Experts, engines)
- 📖 **Recipes** - Individual agent roles (complete definitions)
- 📚 **Cookbooks** - Full agent teams (bundled for industries)

## 📚 Documentation

See [AGENT_CREATION_FACTORY.md](../docs/AGENT_CREATION_FACTORY.md) for complete documentation.

## 🚀 Quick Start

### 1. Start Backend API

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at:
- API Base: http://localhost:8000
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/api/docs

### 2. Start Frontend

```bash
cd frontend
python -m http.server 8080
```

Frontend will be available at:
- Domain Designer: http://localhost:8080/domain-designer.html

## 🔧 API Endpoints

### Domain Management

```bash
# List all domains
GET /api/domain-factory/domains

# Get domain details
GET /api/domain-factory/domains/{domain_id}

# Create new domain
POST /api/domain-factory/domains

# Update domain
PUT /api/domain-factory/domains/{domain_id}
```

### Components

```bash
# List ingredients
GET /api/domain-factory/domains/{domain_id}/ingredients

# List components
GET /api/domain-factory/domains/{domain_id}/components

# List recipes (agent roles)
GET /api/domain-factory/domains/{domain_id}/recipes

# Get cookbook (team structure)
GET /api/domain-factory/domains/{domain_id}/cookbook
```

### Domain Specification Manager

```bash
# Start interview for new industry
POST /api/domain-factory/domain-spec-manager/interview?industry_name=YourIndustry

# Generate specification from interview
POST /api/domain-factory/domain-spec-manager/generate

# Validate specification
GET /api/domain-factory/domain-spec-manager/validate/{domain_id}
```

### Templates

```bash
# Get domain template
GET /api/domain-factory/templates/domain

# Get recipe template
GET /api/domain-factory/templates/recipe
```

## 💡 Usage Examples

### Example 1: List Available Domains

```bash
curl http://localhost:8000/api/domain-factory/domains
```

Response:
```json
{
  "domains": [
    {
      "id": "digital-marketing",
      "name": "Digital Marketing",
      "description": "Complete AI agent workforce for digital marketing operations"
    },
    {
      "id": "healthcare",
      "name": "Healthcare",
      "description": "AI agent workforce for healthcare providers"
    }
  ],
  "total": 2
}
```

### Example 2: Get Domain Details

```bash
curl http://localhost:8000/api/domain-factory/domains/digital-marketing
```

### Example 3: Start Domain Interview

```bash
curl -X POST "http://localhost:8000/api/domain-factory/domain-spec-manager/interview?industry_name=Real%20Estate"
```

Response includes 10 questions to gather information about the new industry.

### Example 4: Create New Agent Recipe

```bash
curl -X POST http://localhost:8000/api/domain-factory/domains/digital-marketing/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "id": "content-writer",
    "domain_id": "digital-marketing",
    "name": "Content Writer Agent",
    "role": "Write blog posts and articles",
    "base_price": 10000,
    "currency": "INR"
  }'
```

## 🎨 Frontend Usage

1. **Navigate to Domain Designer**: http://localhost:8080/domain-designer.html

2. **View Existing Domains**:
   - Browse Digital Marketing, Healthcare, Sales domains
   - Click on domain cards to view details

3. **Create New Industry**:
   - Click "Create New Industry Domain"
   - Enter industry name (e.g., "Real Estate")
   - Answer 10 questions from Domain Specification Manager
   - Review generated specification
   - Approve and deploy

## 🏗️ Architecture

### Data Models

```python
# Core models (see backend/app/models/domain_factory.py)
- Domain: Industry domain metadata
- Ingredient: Building blocks (AI models, APIs)
- Component: Reusable modules (SMEs, engines)
- Recipe: Agent role definitions
- Cookbook: Complete team structures
```

### Database Schema

```sql
-- Main tables
domains
ingredients
components
recipes
cookbooks

-- Relationship tables
component_ingredients
recipe_ingredients
recipe_components
cookbook_recipes
```

See [AGENT_CREATION_FACTORY.md](../docs/AGENT_CREATION_FACTORY.md) for complete schema.

## 📖 Kitchen Analogy Explained

### Ingredients 🧂
**What**: Basic building blocks
**Examples**:
- NLP Engine (GPT-4, Claude)
- Analytics APIs (Google Analytics)
- Social Media APIs (Facebook, LinkedIn)
- SEO Tools (Ahrefs, SEMrush)

### Components 🍲
**What**: Pre-built, reusable modules
**Examples**:
- Digital Marketing SME (expertise module)
- Content Writing Engine
- Analytics Dashboard Generator
- Email Automation Engine

### Recipes 📖
**What**: Complete agent role definitions
**Examples**:
- Content Marketing Specialist
  - Uses: NLP Engine, SEO Tools
  - Components: Marketing SME, Content Engine
  - Deliverables: 8 blog posts/month
  - Price: ₹12,000/month

### Cookbooks 📚
**What**: Full agent teams for an industry
**Examples**:
- Digital Marketing Workforce
  - 7 agents: Content, SEO, Social Media, Email, PPC, Brand, Sales
  - Individual sum: ₹84,000/month
  - Bundle price: ₹67,200/month (20% discount)

## 🤖 The Domain Specification Manager Agent

**Role**: The AI agent that creates other AI agents

**Capabilities**:
1. Interviews domain designers (10 key questions)
2. Researches industry requirements
3. Generates complete domain specifications
4. Creates ingredients, components, recipes, cookbooks
5. Validates specifications for completeness
6. Maintains templates for easy onboarding

**Usage**:
```javascript
// Start interview
const interview = await startDomainInterview("Real Estate");

// Answer 10 questions about:
// - Key roles in industry
// - Tools and systems used
// - Essential skills
// - Regulatory requirements
// - Target customers
// - Typical deliverables
// - Subscription tiers
// - Pricing
// - Specializations
// - Unique challenges

// Generate specification
const spec = await generateDomainSpec(answers);

// Result: Complete domain with ingredients, components, recipes, cookbook
```

## 🎯 Existing Domains

### Digital Marketing
- **Agents**: 7 (Content, SEO, Social Media, Email, PPC, Brand, Sales)
- **Team Price**: ₹67,200/month
- **Target**: SMBs, startups, agencies

### Healthcare
- **Agents**: 6 (Medical Scribe, Patient Coordinator, Billing, etc.)
- **Team Price**: ₹72,000/month
- **Target**: Clinics, private practices, telemedicine

### Sales
- **Agents**: 5 (SDR, Account Executive, CRM Manager, etc.)
- **Team Price**: ₹60,000/month
- **Target**: B2B sales teams, startups

## 🔐 Agent Inheritance System

**Every agent automatically inherits**:
1. ✅ Ethics & Code of Conduct (general + domain-specific)
2. ✅ Learning & Continuous Improvement (RLHF)
3. ✅ Subscription Management & Limits
4. ✅ Communication Protocol (reports, notifications)
5. ✅ Security & Compliance (encryption, audit trails)
6. ✅ Quality Assurance (self-checking, validation)

## 📈 Roadmap

- [ ] Database integration (PostgreSQL)
- [ ] Real-time specification generation using AI
- [ ] Advanced validation logic
- [ ] Domain version control
- [ ] A/B testing for agent configurations
- [ ] Performance analytics per domain
- [ ] Cross-domain component sharing

## 🤝 Contributing

To add a new industry domain:

1. Use the Domain Specification Manager interview
2. Or manually create specification using template
3. Submit PR with complete domain definition
4. Include: ingredients, components, recipes, cookbook
5. Add Sales & Marketing meta-agent for the industry

## 📞 Support

For questions or issues:
- See full documentation: [AGENT_CREATION_FACTORY.md](../docs/AGENT_CREATION_FACTORY.md)
- API Reference: http://localhost:8000/api/docs
- GitHub Issues: [Create issue](https://github.com/dlai-sd/WAOOAW/issues)

---

**Last Updated**: December 23, 2025  
**Version**: 1.0.0  
**Status**: Foundation Complete - Ready for Database Integration
