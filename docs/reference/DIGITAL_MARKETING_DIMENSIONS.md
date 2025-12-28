# Digital Marketing Assessment - Scoring Business Rules

## Overview
This document defines the business rules and logic for scoring digital marketing dimensions. Scores are contextually adjusted based on company tier, industry, and business model to ensure fair and meaningful assessments.

---

## Company Profiling

### 1. Tier Classification
Determines company scale based on observable signals:

| Tier | Criteria | Typical Characteristics |
|------|----------|------------------------|
| **Small** | Total signals < 1,000 | Followers < 1K, DA < 30, Minimal media presence |
| **Medium** | Total signals 1K-10K | Followers 1K-10K, DA 30-60, Some media presence |
| **Large** | Total signals > 10K | Followers > 10K, DA > 60, Strong media presence |

**Calculation:** `social_followers + domain_authority + media_mentions`

### 2. Industry Classification
Determines industry category from website content, keywords, and business description:

| Industry | Keywords/Indicators | Typical Offerings |
|----------|-------------------|-------------------|
| **SaaS/Tech** | software, platform, cloud, API, app, solution | Software products, platforms |
| **E-commerce** | shop, store, buy, product, retail, cart | Online retail, marketplaces |
| **Professional Services** | consulting, agency, services, expert, advisory | Consulting, legal, accounting, marketing |
| **Manufacturing** | manufacturing, industrial, equipment, machinery | Physical products, B2B supplies |
| **Healthcare** | health, medical, care, clinic, hospital, wellness | Medical services, healthcare products |
| **Financial Services** | finance, banking, investment, insurance, wealth | Banking, investment, fintech |
| **Real Estate** | real estate, property, homes, rental, listings | Property sales, rentals, management |
| **Education** | education, learning, training, course, university | Educational services, e-learning |
| **Media/Publishing** | media, news, publishing, content, entertainment | Content creation, news, entertainment |
| **Hospitality** | hotel, restaurant, travel, tourism, booking | Travel, accommodation, food services |

### 3. Business Model Detection
Determines primary business model:

| Model | Indicators | Content Expectations |
|-------|-----------|---------------------|
| **B2B** | "enterprise", "business solutions", long sales cycles | Deep, educational content; Lower frequency OK |
| **B2C** | "consumers", "customers", quick purchases | Light, frequent content; High social presence |
| **B2B2C** | "platform", "marketplace", both businesses and consumers | Hybrid approach; Multiple content streams |

### 4. Service Complexity
Determines the complexity of offerings:

| Complexity | Examples | Content Strategy |
|------------|----------|-----------------|
| **Transactional** | Food delivery, ride sharing, e-commerce | High frequency, low depth, visual-heavy |
| **Consultative** | Legal, consulting, agency services | Low frequency, high depth, expertise-focused |
| **Enterprise** | Enterprise SaaS, industrial equipment | Very low frequency, maximum depth, technical |

---

## Dimension 1: Content Marketing

### Definition
Measures the quality, consistency, and depth of owned content creation on company properties (website, blog, resources).

### Core Metrics
- **Primary:** Blog posts per month
- **Secondary:** Content pages, resource library, whitepapers/case studies

### Base Scoring Scale (Blog Posts/Month)

| Score | Threshold | Description |
|-------|-----------|-------------|
| 1 | 0 posts | No blog or no content detected |
| 2 | 1-2 posts | Occasional content, minimal consistency |
| 3 | 3-4 posts | Monthly content, some consistency |
| 4 | 5-7 posts | Regular posting, weekly cadence |
| 5 | 8-11 posts | Consistent weekly, strong presence |
| 6 | 12-15 posts | Multiple per week, very active |
| 7 | 16+ posts | Daily or near-daily, exceptional volume |

### Context-Aware Adjustments

#### By Tier
| Tier | Adjustment | Rationale |
|------|-----------|-----------|
| Small | -20% frequency expectation | Limited resources, smaller teams |
| Medium | No adjustment | Standard expectations |
| Large | +10% frequency expectation | More resources, dedicated teams |

#### By Industry
| Industry | Frequency Expectation | Quality Focus |
|----------|---------------------|---------------|
| SaaS/Tech | 8-12 posts/month (score 5-6) | Tutorials, use cases, product updates |
| E-commerce | 12-20 posts/month (score 6-7) | Product guides, trends, lifestyle |
| Professional Services | 4-8 posts/month (score 5-6) | Thought leadership, expertise, insights |
| Manufacturing | 2-4 posts/month (score 5-6) | Technical specs, applications, case studies |
| Healthcare | 4-6 posts/month (score 5-6) | Patient education, research, compliance |
| Financial Services | 4-8 posts/month (score 5-6) | Market insights, guides, regulatory updates |
| Real Estate | 8-12 posts/month (score 5-6) | Listings, market trends, local guides |
| Education | 6-10 posts/month (score 5-6) | Learning resources, program updates |

#### By Business Model
| Model | Frequency Adjustment | Content Style |
|-------|---------------------|---------------|
| B2B | -30% frequency | Depth over frequency; long-form preferred |
| B2C | Standard | Balance frequency and engagement |
| B2B2C | +20% frequency | Multiple audience streams |

#### By Service Complexity
| Complexity | Frequency | Content Depth |
|------------|-----------|---------------|
| Transactional | High (12-20/month) | Short, actionable, visual |
| Consultative | Medium (4-8/month) | Deep, educational, expertise-driven |
| Enterprise | Low (2-6/month) | Maximum depth, technical, comprehensive |

### Adjusted Scoring Formula
```
adjusted_score = base_score * tier_multiplier * industry_multiplier * model_multiplier
```

### Example Scoring Scenarios

**Scenario 1: Small B2B SaaS Company**
- Raw: 4 posts/month
- Base score: 3/7
- Adjustments: Small tier (+0.5), B2B (+1.0), SaaS (neutral)
- **Final: 4.5/7 → 5/7**

**Scenario 2: Large B2C E-commerce**
- Raw: 12 posts/month
- Base score: 6/7
- Adjustments: Large tier (neutral), B2C (neutral), E-commerce (neutral)
- **Final: 6/7**

**Scenario 3: Medium Professional Services**
- Raw: 4 posts/month
- Base score: 3/7
- Adjustments: Medium (neutral), Consultative (+1.5)
- **Final: 4.5/7 → 5/7**

---

## Dimension 2: SEO Presence

### Definition
Evaluates search engine visibility and organic reach through domain authority and optimization signals.

### Core Metrics
- **Primary:** Domain Authority (0-100)
- **Secondary:** Backlinks estimate, keyword optimization signals

### Base Scoring Scale (Domain Authority)

| Score | Threshold | Description |
|-------|-----------|-------------|
| 1 | 0-19 DA | Very low authority, new or weak domain |
| 2 | 20-34 DA | Low authority, building presence |
| 3 | 35-49 DA | Moderate authority, established presence |
| 4 | 50-64 DA | Good authority, strong presence |
| 5 | 65-74 DA | High authority, competitive |
| 6 | 75-84 DA | Very high authority, industry leader |
| 7 | 85+ DA | Exceptional authority, dominant player |

### Context-Aware Adjustments

#### By Tier
- **Small:** -5 DA points expectation (new businesses, building authority)
- **Medium:** No adjustment
- **Large:** +5 DA points expectation (established players)

#### By Industry
| Industry | DA Expectations | Notes |
|----------|----------------|-------|
| SaaS/Tech | 50-70 DA competitive | High competition, SEO critical |
| E-commerce | 40-60 DA competitive | Product-focused, varies by niche |
| Professional Services | 35-55 DA competitive | Local SEO important |
| Manufacturing | 30-50 DA competitive | Technical B2B, lower DA acceptable |
| Healthcare | 45-65 DA competitive | Trust signals critical |
| Financial Services | 50-70 DA competitive | Authority crucial for trust |

---

## Dimension 3: Social Engagement

### Definition
Assesses active participation and community building on social media platforms.

### Core Metrics
- **Primary:** Total social followers
- **Secondary:** Active platforms, engagement rate, posting frequency

### Base Scoring Scale (Total Followers)

| Score | Threshold | Description |
|-------|-----------|-------------|
| 1 | 0-999 | Minimal presence, just starting |
| 2 | 1K-4.9K | Small following, growing |
| 3 | 5K-14.9K | Moderate following, active |
| 4 | 15K-39.9K | Good following, engaged community |
| 5 | 40K-74.9K | Large following, strong presence |
| 6 | 75K-99.9K | Very large following, influential |
| 7 | 100K+ | Massive following, market leader |

### Context-Aware Adjustments

#### By Business Model
| Model | Follower Expectation | Platform Priority |
|-------|---------------------|-------------------|
| B2C | Standard (as above) | Instagram, Facebook, TikTok |
| B2B | -50% followers | LinkedIn primary, Twitter secondary |
| B2B2C | Standard | Multi-platform balanced |

#### By Industry
| Industry | Follower Expectations | Key Platforms |
|----------|---------------------|---------------|
| E-commerce | High (2x standard) | Instagram, Facebook, Pinterest |
| SaaS/Tech | Medium | LinkedIn, Twitter, YouTube |
| Professional Services | Lower (0.5x standard) | LinkedIn primary |
| Consumer Brands | Very High (3x standard) | All platforms |

---

## Dimension 4: Conversion Signals

### Definition
Evaluates the effectiveness of conversion-focused elements and user journey optimization.

### Core Metrics
- **Composite Score:** CTA presence + testimonials + analytics + meta tags + social links

### Base Scoring Scale (Conversion Indicators 0-10)

| Score | Threshold | Description |
|-------|-----------|-------------|
| 1 | 0-1 | Minimal conversion elements |
| 2 | 2 | Basic presence |
| 3 | 3-4 | Some optimization |
| 4 | 5 | Moderate optimization |
| 5 | 6 | Good optimization |
| 6 | 7-8 | Very good optimization |
| 7 | 9-10 | Excellent optimization |

### Components (max 10 points)
- **CTA presence:** +3 points (critical conversion driver)
- **Testimonials:** +2 points (trust signals)
- **Analytics:** +2 points (optimization capability)
- **Meta description:** +1 point (SEO/clarity)
- **Social links:** +1 point (trust/connectivity)
- **Bonus:** +1 point (exceptional execution)

### Industry Expectations
- **E-commerce:** All elements expected (9-10 required for score 7)
- **B2B SaaS:** CTAs and analytics critical (7-8 sufficient for score 6)
- **Professional Services:** Testimonials crucial (6-7 sufficient for score 6)

---

## Dimension 5: Brand Authority

### Definition
Measures brand recognition, reputation, and market presence through external validation.

### Core Metrics
- **Primary:** Media mentions
- **Secondary:** Reviews, ratings, industry recognition

### Base Scoring Scale (Media Mentions)

| Score | Threshold | Description |
|-------|-----------|-------------|
| 1 | 0-1 | No or minimal media presence |
| 2 | 2-4 | Occasional mentions |
| 3 | 5-9 | Regular mentions, growing awareness |
| 4 | 10-19 | Good media presence, recognized |
| 5 | 20-34 | Strong presence, industry visibility |
| 6 | 35-44 | Very strong presence, thought leader |
| 7 | 45+ | Dominant presence, industry authority |

### Context Adjustments
- **Large tier:** Higher expectations (+5-10 mentions for same score)
- **B2C:** Media coverage more accessible (standard scale)
- **B2B:** Media mentions harder to achieve (-30% expectations)

---

## Dimension 6: Technical Optimization

### Definition
Assesses website technical performance, user experience, and technical SEO implementation.

### Core Metrics
- **Primary:** Page speed score (0-100)
- **Secondary:** Mobile optimization, analytics setup, structured data

### Base Scoring Scale (Page Speed)

| Score | Threshold | Description |
|-------|-----------|-------------|
| 1 | 0-49 | Poor performance, needs work |
| 2 | 50-59 | Below average, improvement needed |
| 3 | 60-69 | Average performance |
| 4 | 70-79 | Good performance |
| 5 | 80-89 | Very good performance |
| 6 | 90-94 | Excellent performance |
| 7 | 95+ | Outstanding performance |

### Universal Expectations
Technical optimization is less industry-dependent. All companies should aim for 70+ page speed regardless of tier or industry.

---

## Dimension 7: Thought Leadership

### Definition
Evaluates the company's position as an industry expert through speaking, research, and influence.

### Core Metrics
- **Primary:** Speaking engagements estimate
- **Secondary:** LinkedIn presence, published research, webinars

### Base Scoring Scale (Speaking Engagements/Year)

| Score | Threshold | Description |
|-------|-----------|-------------|
| 1 | 0 | No thought leadership signals |
| 2 | 1 | Minimal participation |
| 3 | 2-3 | Some industry involvement |
| 4 | 4-6 | Regular participation |
| 5 | 7-9 | Active thought leader |
| 6 | 10-12 | Influential expert |
| 7 | 13+ | Industry authority |

### Context Adjustments

#### By Industry
| Industry | Importance Weight | Expected Level |
|----------|------------------|----------------|
| Professional Services | Critical (1.5x weight) | 4-6 engagements for score 6 |
| SaaS/Tech | Important (1.2x weight) | Active conference presence |
| E-commerce | Low importance (0.7x weight) | Not critical for success |
| Manufacturing | Medium (1.0x weight) | Trade shows, technical papers |

#### By Tier
- **Small:** 1-2 engagements = score 5 (limited resources)
- **Medium:** 4-6 engagements = score 5 (growing presence)
- **Large:** 10+ engagements = score 5 (expected for scale)

---

## Overall Score Calculation

### Weighted Average by Tier

**Small Business Weights:**
```
content_marketing: 20%
seo_presence: 20%
social_engagement: 15%
conversion_signals: 20%
brand_authority: 5%
technical_optimization: 10%
thought_leadership: 10%
```

**Medium Business Weights:**
```
content_marketing: 20%
seo_presence: 20%
social_engagement: 15%
conversion_signals: 15%
brand_authority: 10%
technical_optimization: 10%
thought_leadership: 10%
```

**Large Business Weights:**
```
content_marketing: 10%
seo_presence: 20%
social_engagement: 15%
conversion_signals: 15%
brand_authority: 20%
technical_optimization: 10%
thought_leadership: 10%
```

### Formula
```
overall_score = Σ(dimension_score * dimension_weight)
```

---

## Implementation Notes

### Detection Methods

**Industry Detection:**
1. Scrape website for industry keywords
2. Analyze meta tags and descriptions
3. Check domain/company name patterns
4. Fallback: "General" industry

**Business Model Detection:**
1. Look for B2B indicators: "enterprise", "business", "solutions"
2. Look for B2C indicators: "shop", "buy now", "customers"
3. Analyze pricing pages (self-service vs. contact sales)
4. Default: Assume B2B if unclear

**Service Complexity:**
1. Analyze product/service descriptions
2. Check pricing transparency (high = transactional, low = enterprise)
3. Look for "request demo" vs "buy now" CTAs

### Scoring Adjustments Priority
1. **Tier adjustment** (most fundamental)
2. **Industry adjustment** (context-specific)
3. **Business model adjustment** (go-to-market strategy)
4. **Cap at 7, floor at 1** (no fractional scores in final display)

### Future Enhancements
- Machine learning for industry classification
- Competitor benchmarking within industry
- Regional/geographic adjustments
- Seasonal trend analysis
- Historical trend tracking

---

## Change Log
- **2025-12-21:** Initial business rules documentation
- **Version:** 1.0
- **Status:** Active, subject to refinement based on real-world data
