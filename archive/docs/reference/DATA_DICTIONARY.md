# MarketML Data Dictionary
**Digital Marketing Assessment Data Model & Schema**

Version: 1.1  
Last Updated: December 22, 2025  
Status: Living Document

---

## Table of Contents
1. [Overview](#overview)
2. [Core Entities](#core-entities)
3. [Company Entity](#company-entity)
4. [Location Hierarchy](#location-hierarchy)
5. [Financial Data](#financial-data)
6. [Digital Marketing Metrics](#digital-marketing-metrics)
7. [Scoring & Evaluation](#scoring--evaluation)
8. [Data Sources](#data-sources)
9. [Relationships](#relationships)
10. [Enumerations](#enumerations)

---

## Overview

The MarketML data model is designed to capture comprehensive digital marketing intelligence for companies, enabling competitive analysis across geographic regions and evaluation of digital presence effectiveness.

### Design Principles
- **Scalability**: Support for 15-100+ competitors per assessment
- **Geographic Hierarchy**: City → Region → State → Country → Globe
- **Multi-source**: Aggregate data from MCA RoC API, Groq AI, ZaubaCorp, web scraping
- **Data Quality Tracking**: Track source and completeness of each data point
- **Temporal Awareness**: Financial year tracking, company age, historical trends

---

## Core Entities

### Entity Relationship Overview
```
Assessment (Job)
    ├── Subject Company
    │   ├── Company Profile
    │   ├── Location Data
    │   ├── Financial Data
    │   ├── Digital Marketing Metrics
    │   └── Scoring Results
    │
    └── Competitors (0-100)
        ├── Company Profile
        ├── Location Data
        ├── Financial Data
        ├── Digital Marketing Metrics
        └── Scoring Results
```

---

## Company Entity

### Basic Profile

| Field Name | Data Type | Description | Source | Example |
|------------|-----------|-------------|--------|---------|
| `name` | String | Company name as searched | User Input | "Yashus Digital Marketing" |
| `company_name` | String | Official registered name | MCA RoC API / Groq AI | "YASHUS DIGITAL MARKETING PRIVATE LIMITED" |
| `cin` | String (21 chars) | Corporate Identification Number | MCA RoC API / Groq AI | "U74120PN2015PTC157176" |
| `pan` | String (10 chars) | Permanent Account Number | Groq AI / ZaubaCorp | "AABCY1234C" |
| `status` | Enum | Company legal status | MCA RoC API | "Active", "Strike Off", "Amalgamated" |
| `company_class` | Enum | Company classification | MCA RoC API | "Private", "Public", "OPC" |
| `company_category` | String | Company category | MCA RoC API | "Company limited by shares" |
| `company_subcategory` | String | Sub-classification | MCA RoC API | "Non-government company" |
| `indian_foreign` | Enum | Origin classification | MCA RoC API | "Indian", "Foreign" |
| `listing_status` | Enum | Stock listing status | MCA RoC API | "Listed", "Unlisted" |
| `nic_code` | String | National Industrial Classification | MCA RoC API | "72200" |
| `industrial_classification` | String | Industry sector | MCA RoC API | "Business Services" |

### Registration & Legal

| Field Name | Data Type | Description | Source | Example |
|------------|-----------|-------------|--------|---------|
| `date_of_incorporation` | Date (DD-MM-YYYY) | Registration date | MCA RoC API | "09-11-2015" |
| `company_age` | Integer | Years since incorporation | Calculated | 10 |
| `roc` | String | Registrar of Companies location | MCA RoC API | "ROC Pune" |
| `roc_code` | String | ROC office code | MCA RoC API | "RoC-Pune" |

### Contact Information

| Field Name | Data Type | Description | Source | Example |
|------------|-----------|-------------|--------|---------|
| `registered_address` | Text | Registered office address | MCA RoC API | "D/26, Everest Height, Viman Nagar, Pune, Maharashtra, 411014" |
| `email` | String | Contact email | Groq AI / Web Scraping | "contact@yashus.in" |
| `phone` | String | Contact phone | Groq AI / Web Scraping | "+91-20-12345678" |
| `website_url` | URL | Primary website | Web Scraping | "https://yashus.in" |

### Directors

| Field Name | Data Type | Description | Source | Example |
|------------|-----------|-------------|--------|---------|
| `directors` | Array<Object> | List of directors | Groq AI / ZaubaCorp | See Directors Schema |

#### Directors Schema
```json
{
  "name": "String - Director full name",
  "din": "String - Director Identification Number",
  "appointment_date": "Date (DD-MM-YYYY) - Appointment date"
}
```

### Data Quality Metadata

| Field Name | Data Type | Description | Possible Values |
|------------|-----------|-------------|-----------------|
| `data_quality` | Enum | Completeness indicator | "complete", "partial", "limited" |
| `data_source` | String | Primary data source | "MCA RoC API (Official Government Database)", "Groq AI + Web Search", "Legacy CIN Lookup", "Base Defaults" |
| `extraction_confidence` | Enum | AI extraction confidence | "high", "medium", "low" |
| `extraction_method` | String | Extraction technique | "groq_web_search", "mca_api", "zauba_scrape" |
| `timestamp` | ISO 8601 | Data extraction time | "2025-12-22T08:03:33.999Z" |

---

## Location Hierarchy

### Geographic Structure
Supports multi-level competitive analysis from local to global scale.

| Level | Field Name | Data Type | Description | Example |
|-------|------------|-----------|-------------|---------|
| 1 | `city` | String | City/Municipality | "Pune" |
| 2 | `region` | String | Metropolitan area/District | "Pune Metropolitan Region" |
| 3 | `state` | String | State/Province | "Maharashtra" |
| 4 | `state_code` | String (lowercase) | State identifier | "maharashtra" |
| 5 | `country` | String | Country name | "India" |
| 6 | `country_code` | String (2-letter) | ISO 3166-1 alpha-2 | "IN" |
| 7 | `globe` | Boolean | Global presence indicator | true/false |

### Location Parsing Rules
- Extract from `registered_address` field
- Parse city, state, postal code using regex
- Map state names to state codes (lowercase, no spaces)
- Default country to "India" for CIN-registered companies
- Globe flag = true if operations in 3+ countries

### Competitor Filtering by Location

| Scope | Filter Logic | Use Case |
|-------|-------------|----------|
| **City** | Same city exact match | Local market analysis (15-50 competitors) |
| **Region** | Same state + nearby cities | Regional market analysis (30-75 competitors) |
| **State** | Same state | State-wide analysis (50-100 competitors) |
| **Country** | Same country | National market (75-100+ competitors) |
| **Globe** | No location filter | Global competitive landscape |

---

## Financial Data

### Capital Structure

| Field Name | Data Type | Description | Source | Example |
|------------|-----------|-------------|--------|---------|
| `authorized_capital` | Decimal | Maximum share capital (INR) | MCA RoC API | "100000.00" |
| `paid_up_capital` | Decimal | Actually paid capital (INR) | MCA RoC API | "100000.00" |

### Current Financial Year (Latest)

| Field Name | Data Type | Description | Source | Example |
|------------|-----------|-------------|--------|---------|
| `financial_year` | String | Latest FY period | Groq AI | "FY 2023-24", "FY24" |
| `latest_revenue` | String | Revenue in original format | Groq AI | "₹1,234 Crore" |
| `revenue_inr_millions` | Decimal | Revenue in INR Crores | Calculated | 1234.00 |
| `revenue_millions` | Decimal | Revenue in USD Millions | Calculated | 14.87 |
| `revenue_display` | String | User-friendly format | Formatted | "$14.87M USD (₹1,234 Crore)" |
| `revenue_source` | String | Data source for revenue | Tracking | "Groq AI (Web Search - INR)" |
| `profit_after_tax` | String | PAT/Net Profit | Groq AI | "₹158 Crore" |
| `total_assets` | String | Total assets | Groq AI | "₹2,500 Crore" |

### Historical Revenue (5-Year Trend)

| Field Name | Data Type | Description | Source | Example |
|------------|-----------|-------------|--------|---------|
| `revenue_history` | Array<Object> | Revenue for last 5 FYs | Groq AI / Annual Reports | See Revenue History Schema |

#### Revenue History Schema
Each object in `revenue_history` array contains:

| Field Name | Data Type | Description | Example |
|------------|-----------|-------------|---------|
| `financial_year` | String | FY identifier | "FY 2023-24" |
| `year_numeric` | Integer | Calendar year end | 2024 |
| `revenue_inr_crores` | Decimal | Revenue in Crores | 1234.00 |
| `revenue_usd_millions` | Decimal | Revenue in USD Millions | 14.87 |
| `revenue_display` | String | Formatted revenue | "₹1,234 Cr ($14.87M)" |
| `profit_after_tax_crores` | Decimal | PAT in Crores | 158.00 |
| `growth_rate_yoy` | Decimal | Year-over-year % | 15.5 |
| `data_source` | String | Source of data | "Annual Report FY24" |
| `confidence` | Enum | Data confidence | "high", "medium", "low" |

**Array Order**: Most recent first (index 0 = latest year)

**Example**:
```json
"revenue_history": [
  {
    "financial_year": "FY 2023-24",
    "year_numeric": 2024,
    "revenue_inr_crores": 1234.00,
    "revenue_usd_millions": 14.87,
    "revenue_display": "₹1,234 Cr ($14.87M)",
    "profit_after_tax_crores": 158.00,
    "growth_rate_yoy": 15.5,
    "data_source": "Annual Report FY24",
    "confidence": "high"
  },
  {
    "financial_year": "FY 2022-23",
    "year_numeric": 2023,
    "revenue_inr_crores": 1070.00,
    "revenue_usd_millions": 12.89,
    "growth_rate_yoy": 12.8,
    "confidence": "medium"
  }
  // ... up to 5 years
]
```

### Revenue Growth Metrics

| Field Name | Data Type | Description | Calculation | Example |
|------------|-----------|-------------|-------------|---------|
| `revenue_cagr_3y` | Decimal | 3-year compound annual growth | ((latest/year3)^(1/3)-1)*100 | 18.5 |
| `revenue_cagr_5y` | Decimal | 5-year compound annual growth | ((latest/year5)^(1/5)-1)*100 | 22.3 |
| `revenue_trend` | Enum | Growth trajectory | "growing", "stable", "declining" | "growing" |
| `revenue_stability` | Decimal | Coefficient of variation | StdDev/Mean | 0.12 |
| `years_with_data` | Integer | Number of FYs with data | Count non-null years | 5 |

### Currency Conversion
- **INR to USD**: Divide by 83 (₹83 = $1 USD approx)
- **Crore to Lakh**: 1 Crore = 100 Lakh
- **Crore to Million USD**: 1 Crore ≈ 0.012 Million USD
- **Historical rates**: Use year-specific exchange rates when available

---

## Digital Marketing Metrics

### Website Analytics

| Field Name | Data Type | Description | Source | Range |
|------------|-----------|-------------|--------|-------|
| `domain_authority` | Integer | Moz domain authority | Web Scraping / API | 0-100 |
| `backlinks` | Integer | Number of backlinks | Web Scraping / API | 0-1000000+ |
| `page_speed` | Integer | PageSpeed score | Web Scraping / API | 0-100 |
| `mobile_optimized` | Boolean | Mobile-friendly | Web Scraping | true/false |
| `has_analytics` | Boolean | GA/tracking detected | Web Scraping | true/false |
| `structured_data` | Boolean | Schema.org markup | Web Scraping | true/false |
| `has_ssl` | Boolean | HTTPS enabled | Web Scraping | true/false |

### Content Marketing

| Field Name | Data Type | Description | Source | Range |
|------------|-----------|-------------|--------|-------|
| `blog_posts_per_month` | Decimal | Posting frequency | Web Scraping | 0-30+ |
| `content_pages` | Integer | Total content pages | Web Scraping | 0-10000+ |
| `has_blog` | Boolean | Blog section exists | Web Scraping | true/false |
| `has_case_studies` | Boolean | Case studies present | Web Scraping | true/false |
| `has_whitepapers` | Boolean | Whitepapers available | Web Scraping | true/false |
| `video_content` | Boolean | Video content present | Web Scraping | true/false |

### Social Media Presence

| Field Name | Data Type | Description | Source | Range |
|------------|-----------|-------------|--------|-------|
| `social_followers` | Integer | Total followers across platforms | API Aggregation | 0-10000000+ |
| `active_platforms` | Integer | Number of active platforms | Web Scraping | 0-10 |
| `engagement_rate` | Decimal | Social engagement % | API Aggregation | 0-100 |
| `linkedin_followers` | Integer | LinkedIn company followers | LinkedIn API | 0-1000000+ |
| `twitter_followers` | Integer | Twitter/X followers | Twitter API | 0-1000000+ |
| `facebook_likes` | Integer | Facebook page likes | Facebook API | 0-1000000+ |
| `instagram_followers` | Integer | Instagram followers | Instagram API | 0-1000000+ |
| `youtube_subscribers` | Integer | YouTube subscribers | YouTube API | 0-1000000+ |

### SEO Metrics

| Field Name | Data Type | Description | Source | Range |
|------------|-----------|-------------|--------|-------|
| `organic_keywords` | Integer | Ranking keywords | SEO Tools | 0-100000+ |
| `organic_traffic` | Integer | Monthly organic visits | SEO Tools | 0-10000000+ |
| `top_10_keywords` | Integer | Keywords in top 10 | SEO Tools | 0-10000+ |
| `meta_description` | Text | Homepage meta desc | Web Scraping | 0-160 chars |
| `meta_keywords` | Array | Meta keywords | Web Scraping | - |

### Conversion Signals

| Field Name | Data Type | Description | Source | Range |
|------------|-----------|-------------|--------|-------|
| `has_cta` | Boolean | Call-to-action present | Web Scraping | true/false |
| `has_testimonials` | Boolean | Customer testimonials | Web Scraping | true/false |
| `has_pricing` | Boolean | Pricing page exists | Web Scraping | true/false |
| `has_demo` | Boolean | Demo/trial available | Web Scraping | true/false |
| `contact_forms` | Integer | Number of contact forms | Web Scraping | 0-10 |
| `chat_widget` | Boolean | Live chat present | Web Scraping | true/false |

### Reputation & Authority

| Field Name | Data Type | Description | Source | Range |
|------------|-----------|-------------|--------|-------|
| `media_mentions` | Integer | News/media mentions | News API | 0-10000+ |
| `recent_news` | Boolean | News in last 90 days | News API | true/false |
| `review_count` | Integer | Online reviews | Review APIs | 0-100000+ |
| `average_rating` | Decimal | Average review rating | Review APIs | 0-5.0 |
| `awards` | Array<String> | Industry awards | Web Scraping | - |
| `certifications` | Array<String> | Certifications | Web Scraping | - |

---

## Scoring & Evaluation

### Dimension Scores

Based on [SCORING_BUSINESS_RULES.md](SCORING_BUSINESS_RULES.md)

| Dimension | Field Name | Data Type | Range | Weight |
|-----------|------------|-----------|-------|--------|
| Content Marketing | `content_marketing` | Integer | 1-7 | 20% |
| SEO Presence | `seo_presence` | Integer | 1-7 | 20% |
| Social Engagement | `social_engagement` | Integer | 1-7 | 15% |
| Conversion Signals | `conversion_signals` | Integer | 1-7 | 15% |
| Brand Authority | `brand_authority` | Integer | 1-7 | 15% |
| Technical Optimization | `technical_optimization` | Integer | 1-7 | 10% |
| Thought Leadership | `thought_leadership` | Integer | 1-7 | 5% |

### Aggregate Scores

| Field Name | Data Type | Description | Calculation |
|------------|-----------|-------------|-------------|
| `score` | Decimal | Overall weighted score | Σ(dimension × weight) |
| `tier` | Enum | Company size tier | "small", "medium", "large" |
| `tier_signal_total` | Integer | Tier calculation input | followers + DA + mentions |

### Contextual Adjustments

| Field Name | Data Type | Description | Values |
|------------|-----------|-------------|--------|
| `industry` | Enum | Industry category | See Industry Enum |
| `business_model` | Enum | Business model | "B2B", "B2C", "B2B/B2C" |
| `service_complexity` | Enum | Service type | "Transactional", "Consultative", "Enterprise" |

---

## Data Sources

### Source Hierarchy
Priority order for data retrieval:

| Priority | Source | Coverage | Accuracy | Cost |
|----------|--------|----------|----------|------|
| 1 | **MCA RoC API** | 2.8M+ Indian companies | 100% | TBD |
| 2 | **Groq→MCA Pipeline** | Web + MCA | 90%+ | ~$0.0006/company |
| 3 | **ZaubaCorp Scraping** | Indian companies | 70-80% | Free (rate-limited) |
| 4 | **Groq AI Direct** | Web search | 13-56% | ~$0.0006/company |
| 5 | **Base Defaults** | All companies | Assumed | Free |

### API Integrations

| API | Purpose | Fields Provided | Rate Limit |
|-----|---------|-----------------|------------|
| MCA RoC API | Official company data | 16 registration fields | TBD |
| Groq API (Llama 3.3 70B) | Data extraction | All company fields | 30 req/min |
| Google Custom Search API | Web search | Search results | 100/day free |
| Wikipedia API | Revenue lookup | Revenue data | 200 req/sec |
| LinkedIn API | Social metrics | Follower counts | Per app |
| Twitter API | Social metrics | Follower counts | Per app |

---

## Relationships

### Assessment → Companies (1:N)
One assessment job can analyze 1 subject + 0-100 competitors

```json
{
  "job_id": "uuid",
  "status": "completed",
  "result": {
    "subject": { /* Company Entity */ },
    "competitors": [ /* Array of Company Entities */ ]
  }
}
```

### Company → Location (1:1)
Each company has one primary registered location

```json
{
  "company_id": "CIN",
  "location": {
    "city": "Pune",
    "state": "Maharashtra",
    "state_code": "maharashtra",
    "country": "India"
  }
}
```

### Company → Directors (1:N)
One company has multiple directors

```json
{
  "company_id": "CIN",
  "directors": [
    {
      "name": "John Doe",
      "din": "12345678",
      "appointment_date": "01-01-2020"
    }
  ]
}
```

### Company → Financial History (1:N)
One company has multiple financial years (future enhancement)

```json
{
  "company_id": "CIN",
  "financial_history": [
    {
      "financial_year": "FY 2023-24",
      "revenue_inr_cr": 1234.00,
      "pat_inr_cr": 158.00
    }
  ]
}
```

---

## Enumerations

### Company Status
```javascript
enum CompanyStatus {
  "Active",
  "Strike Off",
  "Amalgamated",
  "Under Process of Striking off",
  "Converted to LLP",
  "Dissolved",
  "Dormant"
}
```

### Company Class
```javascript
enum CompanyClass {
  "Private",
  "Public",
  "OPC",  // One Person Company
  "Section 8",  // Non-profit
  "Unlimited"
}
```

### Tier Classification
```javascript
enum Tier {
  "small",    // signals < 1000
  "medium",   // signals 1000-10000
  "large"     // signals > 10000
}
```

### Industry Categories
```javascript
enum Industry {
  "SaaS/Tech",
  "E-commerce",
  "Professional Services",
  "Manufacturing",
  "Healthcare",
  "Financial Services",
  "Real Estate",
  "Education",
  "Media/Publishing",
  "Hospitality",
  "General"  // default
}
```

### Business Models
```javascript
enum BusinessModel {
  "B2B",
  "B2C",
  "B2B/B2C"  // Hybrid
}
```

### Data Quality Levels
```javascript
enum DataQuality {
  "complete",  // All fields from MCA
  "partial",   // Some fields from Groq/web
  "limited"    // Base defaults applied
}
```

### Indian States (State Codes)
```javascript
enum StateCode {
  "andhra pradesh", "arunachal pradesh", "assam", "bihar",
  "chhattisgarh", "goa", "gujarat", "haryana", "himachal pradesh",
  "jharkhand", "karnataka", "kerala", "madhya pradesh", "maharashtra",
  "manipur", "meghalaya", "mizoram", "nagaland", "odisha", "punjab",
  "rajasthan", "sikkim", "tamil nadu", "telangana", "tripura",
  "uttar pradesh", "uttarakhand", "west bengal",
  "delhi", "puducherry", "chandigarh", "dadra and nagar haveli",
  "daman and diu", "lakshadweep", "andaman and nicobar islands"
}
```

---

## Future Enhancements

### Planned Schema Extensions

1. **Historical Tracking** ✅ *Partially Implemented*
   - ✅ Revenue history (5-year trend) - **IMPLEMENTED**
   - ✅ Growth metrics (CAGR, YoY) - **IMPLEMENTED**
   - ⏳ Time-series data for digital metrics
   - ⏳ Monthly trend analysis (MoM growth)
   - ⏳ Seasonal patterns

2. **Competitive Intelligence**
   - Market share estimation
   - Competitive positioning matrix
   - Feature comparison tables
   - Relative performance scoring

3. **Advanced Financials**
   - ✅ 5-year revenue history - **IMPLEMENTED**
   - ⏳ P&L statement details (EBITDA, operating expenses)
   - ⏳ Balance sheet data (current ratio, quick ratio)
   - ⏳ Cash flow metrics (operating, investing, financing)
   - ⏳ Financial ratios (ROE, ROA, Debt/Equity, P/E ratio)

4. **Technology Stack**
   - Frameworks detected (React, Angular, etc.)
   - CMS platform (WordPress, Shopify, etc.)
   - Marketing tools (HubSpot, Marketo, etc.)
   - Analytics platforms

5. **Employee Data**
   - Employee count
   - Growth rate
   - Department breakdown
   - Key personnel

6. **Marketing Spend**
   - Advertising spend estimates
   - Channel breakdown
   - CAC (Customer Acquisition Cost)
   - LTV (Lifetime Value)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.1 | 2025-12-22 | Added 5-year revenue history tracking, growth metrics (CAGR), revenue trend analysis | System |
| 1.0 | 2025-12-22 | Initial data dictionary created | System |

---

## Notes

- All monetary values default to INR for Indian companies
- USD conversions use ₹83 = $1 exchange rate
- Date format standardized to DD-MM-YYYY
- All enums are case-sensitive
- NULL values represented as "Not available" in strings
- Boolean fields default to false if not detected

