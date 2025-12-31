"""
Task-Specific Prompt Library

Centralized repository of optimized prompts for different industries and task types.
Each prompt template includes system instructions, user template, and few-shot examples.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class Industry(str, Enum):
    """Supported industries"""
    MARKETING = "marketing"
    EDUCATION = "education"
    SALES = "sales"


class TaskType(str, Enum):
    """Common task types across industries"""
    # Marketing
    CONTENT_CREATION = "content_creation"
    SOCIAL_MEDIA = "social_media"
    SEO_OPTIMIZATION = "seo_optimization"
    EMAIL_CAMPAIGN = "email_campaign"
    
    # Education
    LESSON_PLANNING = "lesson_planning"
    ASSESSMENT_CREATION = "assessment_creation"
    CONCEPT_EXPLANATION = "concept_explanation"
    HOMEWORK_HELP = "homework_help"
    
    # Sales
    OUTREACH_MESSAGE = "outreach_message"
    QUALIFICATION = "qualification"
    PROPOSAL_WRITING = "proposal_writing"
    OBJECTION_HANDLING = "objection_handling"


@dataclass
class FewShotExample:
    """Single few-shot example"""
    input: str
    output: str
    reasoning: Optional[str] = None  # For chain-of-thought


@dataclass
class PromptTemplate:
    """Complete prompt template with examples"""
    task_type: TaskType
    industry: Industry
    system_prompt: str
    user_template: str  # Use {variable} for placeholders
    few_shot_examples: List[FewShotExample] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)  # Required variables
    use_chain_of_thought: bool = False
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def format_user_prompt(self, **kwargs) -> str:
        """Format user template with provided variables"""
        missing = [v for v in self.variables if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        return self.user_template.format(**kwargs)
    
    def get_few_shot_text(self, include_reasoning: bool = False) -> str:
        """Format few-shot examples as text"""
        if not self.few_shot_examples:
            return ""
        
        examples = []
        for i, ex in enumerate(self.few_shot_examples, 1):
            text = f"Example {i}:\nInput: {ex.input}\nOutput: {ex.output}"
            if include_reasoning and ex.reasoning:
                text += f"\nReasoning: {ex.reasoning}"
            examples.append(text)
        
        return "\n\n".join(examples)


class PromptLibrary:
    """
    Centralized library of optimized prompts.
    
    Prompts are organized by industry and task type, with each including:
    - System instructions (role, guidelines, constraints)
    - User template (with variable placeholders)
    - Few-shot examples (5 per task type)
    - Chain-of-thought patterns (where applicable)
    """
    
    def __init__(self):
        self._prompts: Dict[tuple, PromptTemplate] = {}
        self._load_marketing_prompts()
        self._load_education_prompts()
        self._load_sales_prompts()
    
    def get_prompt(
        self,
        task_type: TaskType,
        industry: Industry
    ) -> Optional[PromptTemplate]:
        """Get prompt template for task type and industry"""
        return self._prompts.get((task_type, industry))
    
    def register_prompt(self, prompt: PromptTemplate):
        """Register a new prompt template"""
        key = (prompt.task_type, prompt.industry)
        self._prompts[key] = prompt
    
    def list_prompts(self, industry: Optional[Industry] = None) -> List[PromptTemplate]:
        """List all prompts, optionally filtered by industry"""
        if industry:
            return [p for (t, i), p in self._prompts.items() if i == industry]
        return list(self._prompts.values())
    
    # ============= Marketing Prompts =============
    
    def _load_marketing_prompts(self):
        """Load marketing prompt templates"""
        
        # Content Creation
        self.register_prompt(PromptTemplate(
            task_type=TaskType.CONTENT_CREATION,
            industry=Industry.MARKETING,
            system_prompt="""You are an expert content marketing strategist specializing in creating engaging, SEO-optimized content.

Your expertise:
- Understanding target audience pain points and motivations
- Crafting compelling narratives that drive action
- Optimizing content for search engines and readability
- Maintaining brand voice consistency

Guidelines:
1. Always start with a hook that captures attention
2. Use clear, benefit-driven language
3. Include specific examples and data when possible
4. End with a strong call-to-action
5. Keep paragraphs short (2-3 sentences) for readability""",
            user_template="""Create {content_type} about: {topic}

Target Audience: {audience}
Brand Voice: {brand_voice}
Word Count: {word_count}
SEO Keywords: {keywords}

Additional Context: {context}""",
            variables=["content_type", "topic", "audience", "brand_voice", "word_count", "keywords", "context"],
            few_shot_examples=[
                FewShotExample(
                    input="Create blog post about: AI in Healthcare\nTarget: Hospital administrators\nVoice: Professional\nWords: 800\nKeywords: AI healthcare, patient outcomes",
                    output="# How AI is Transforming Patient Care (And Why Your Hospital Needs It Now)\n\nHospital administrators face a critical challenge: delivering better patient outcomes while managing tight budgets. Artificial intelligence offers a solution that's already saving lives—and costs.\n\n## The Reality of AI in Healthcare Today\n\nAt Stanford Hospital, AI-powered diagnostic tools reduced patient wait times by 40% while improving diagnostic accuracy by 25%. This isn't future tech—it's happening now.\n\n[Rest of 800-word article with data, examples, and ROI calculation]\n\n## Your Next Step\n\nSchedule a 15-minute consultation to see how AI can improve your hospital's outcomes. [CTA Button]"
                ),
                FewShotExample(
                    input="Create social media post about: New eco-friendly product launch\nTarget: Millennials\nVoice: Casual, enthusiastic\nWords: 150\nKeywords: sustainable, eco-friendly",
                    output="🌱 FINALLY! A water bottle that doesn't make you choose between style and sustainability.\n\nOur new EcoFlow bottle:\n✨ 100% recycled ocean plastic\n💧 Keeps drinks cold for 48hrs\n🎨 15 gorgeous colors\n♻️ Fully recyclable (again!)\n\nEvery bottle = 50 plastic bottles saved from oceans.\n\nPre-order now, ships next week. Link in bio! 🔗\n\n#SustainableLiving #EcoFriendly #PlasticFree #ConsciousConsumer"
                ),
                FewShotExample(
                    input="Create email subject line about: Flash sale - 50% off\nTarget: Existing customers\nVoice: Urgent but friendly\nWords: 10\nKeywords: sale, limited time",
                    output="⚡ Sarah, 50% OFF ends in 6 hours (yes, really!)"
                ),
                FewShotExample(
                    input="Create landing page headline about: Project management software\nTarget: Remote teams\nVoice: Confident, solution-focused\nWords: 20\nKeywords: remote collaboration, productivity",
                    output="Stop Losing Hours to Messy Communication. Manage Remote Teams Like They're in the Same Room."
                ),
                FewShotExample(
                    input="Create video script intro about: Cooking tutorial for beginners\nTarget: College students\nVoice: Encouraging, fun\nWords: 100\nKeywords: easy cooking, quick meals",
                    output="Hey! I know you're thinking: 'I can't cook.' I was you two years ago, living on ramen and regret.\n\nBut here's the thing—cooking isn't hard. It's just... misunderstood.\n\nToday, I'm showing you 5 meals that take 15 minutes, need 5 ingredients, and actually taste amazing. No fancy equipment. No chef skills. Just real food that won't break your budget or your spirit.\n\nBy the end of this video, you'll have a week of dinners planned. Let's go!"
                )
            ],
            temperature=0.8,
            max_tokens=1500
        ))
        
        # Social Media
        self.register_prompt(PromptTemplate(
            task_type=TaskType.SOCIAL_MEDIA,
            industry=Industry.MARKETING,
            system_prompt="""You are a social media strategist who creates viral, engaging content that drives real business results.

Your expertise:
- Understanding platform algorithms and best practices
- Crafting scroll-stopping hooks
- Driving engagement (likes, comments, shares)
- Balancing entertainment with business goals
- Using hashtags strategically

Guidelines:
1. First 3 words must hook attention
2. Use line breaks for mobile readability
3. Include 1-2 emojis maximum (strategic placement)
4. End with clear CTA
5. Hashtags: 3-5 relevant, mix popular and niche""",
            user_template="""Create {platform} post for: {topic}

Goal: {goal}
Target Audience: {audience}
Brand Voice: {brand_voice}
Character Limit: {char_limit}

Additional Context: {context}""",
            variables=["platform", "topic", "goal", "audience", "brand_voice", "char_limit", "context"],
            few_shot_examples=[
                FewShotExample(
                    input="Platform: LinkedIn\nTopic: Promoted to VP after 5 years\nGoal: Inspire and share lessons\nAudience: Mid-career professionals\nVoice: Authentic, humble",
                    output="5 years ago, I was fired.\n\nToday, I was promoted to VP.\n\nThe journey wasn't what I expected. Here's what I learned:\n\n1. Getting fired was the best thing that happened\n   → Forced me to face my weaknesses\n   → Found my real passion (not what I thought)\n\n2. Skills matter less than relationships\n   → 3 of my biggest opportunities came from people I helped years ago\n   → ROI of kindness: infinite\n\n3. Imposter syndrome never goes away\n   → You just get better at working with it\n   → Everyone at the top feels it too\n\n4. Work-life balance is a myth\n   → Work-life INTEGRATION is real\n   → Find work you don't need to escape from\n\n5. Your career is long\n   → Bad quarters happen\n   → Stay humble in wins, resilient in losses\n\nTo everyone grinding through tough times: Your breakthrough is closer than you think.\n\n#CareerGrowth #Leadership #ProfessionalDevelopment"
                ),
                FewShotExample(
                    input="Platform: Twitter\nTopic: New AI feature announcement\nGoal: Drive signups\nAudience: Tech early adopters\nVoice: Excited, techy",
                    output="We just shipped something wild 🤯\n\nOur AI now writes AND debugs code in real-time.\n\nI watched it fix a 200-line bug in 8 seconds.\n\nBeta access opens today. First 1000 people get lifetime pro.\n\nLink: [url]\n\n#AI #DevTools #MachineLearning"
                ),
                FewShotExample(
                    input="Platform: Instagram\nTopic: Behind-the-scenes of photoshoot\nGoal: Humanize brand\nAudience: Fashion enthusiasts\nVoice: Fun, relatable",
                    output="POV: It's 6am and we're pretending this coffee is working ☕😅\n\n10 hours, 47 outfit changes, and approximately 1 million \"just one more shot\" later...\n\nThe Spring collection drops Friday. Worth every early morning.\n\nSwipe to see what didn't make the cut 👉\n\n#BTS #FashionPhotoshoot #SpringCollection #RealTalk"
                ),
                FewShotExample(
                    input="Platform: TikTok\nTopic: Quick productivity hack\nGoal: Viral reach\nAudience: Gen Z professionals\nVoice: Fast-paced, direct",
                    output="[Text overlay: \"Productivity hack nobody talks about\"]\n\nStop starting your day with email.\n\nSeriously. Delete the app off your phone.\n\nFirst 2 hours = YOUR priorities, not everyone else's.\n\nTried it for 30 days. Finished 3x more work.\n\nYou're welcome.\n\n#ProductivityHacks #WorkSmarter #TimeManagement #CareerTips"
                ),
                FewShotExample(
                    input="Platform: Facebook\nTopic: Customer success story\nGoal: Build trust and credibility\nAudience: Small business owners\nVoice: Warm, authentic",
                    output="\"I almost gave up on my bakery last year.\"\n\nThat's what Sarah told us when she first signed up.\n\n12 months later:\n→ Revenue: +247%\n→ New customers: 1,200+\n→ 5-star reviews: 89\n→ Hired 3 employees\n\nWhat changed? She stopped doing everything herself and automated the stuff that didn't need her magic.\n\nProud to be a small part of her journey. 💙\n\nWatch her full story: [video link]\n\n#SmallBusinessSuccess #EntrepreneurLife #CustomerStory"
                )
            ],
            temperature=0.85,
            max_tokens=500
        ))
        
        # SEO Optimization
        self.register_prompt(PromptTemplate(
            task_type=TaskType.SEO_OPTIMIZATION,
            industry=Industry.MARKETING,
            system_prompt="""You are an SEO specialist who optimizes content for search engines while maintaining quality and readability.

Your expertise:
- Keyword research and placement
- On-page SEO best practices
- Search intent analysis
- Technical SEO fundamentals
- User experience optimization

Guidelines:
1. Primary keyword in title, first paragraph, and H1
2. LSI keywords naturally distributed
3. Headers (H2, H3) with keyword variations
4. Meta description: 150-160 chars, includes keyword and CTA
5. Internal linking opportunities
6. Readability: 8th-grade level maximum""",
            user_template="""Optimize for SEO:

Content: {content}
Primary Keyword: {primary_keyword}
Secondary Keywords: {secondary_keywords}
Target Search Intent: {search_intent}
Current Position: {current_position}

Optimization Goal: {goal}""",
            variables=["content", "primary_keyword", "secondary_keywords", "search_intent", "current_position", "goal"],
            few_shot_examples=[
                FewShotExample(
                    input="Content: [Article about coffee makers]\nKeyword: best coffee maker\nSecondary: automatic coffee machine, drip coffee maker\nIntent: Comparison/buying\nPosition: Page 3\nGoal: Rank page 1",
                    output="# The 7 Best Coffee Makers of 2025 (Tested by Coffee Experts)\n\n[First paragraph optimized with primary keyword in first sentence]\n\nMeta Description: Discover the best coffee maker for your needs. We tested 37 automatic coffee machines and drip coffee makers. Expert buying guide + video reviews.\n\nH2 Sections:\n- How We Test Coffee Makers (process transparency)\n- Best Overall Coffee Maker (comparison table)\n- Best Budget Drip Coffee Maker (affordability)\n- Best Automatic Coffee Machine for Offices (commercial)\n\nSEO Improvements:\n1. Added comparison table (featured snippet opportunity)\n2. FAQ schema markup recommended\n3. Internal links: \"coffee grinder guide\", \"espresso machine reviews\"\n4. Image alt text optimization\n5. Video embed (dwell time)\n\nKeyword Density: 1.2% (optimal)\nReadability: Grade 7 (✓)"
                ),
                FewShotExample(
                    input="Content: [Service page about plumbing]\nKeyword: emergency plumber near me\nSecondary: 24/7 plumber, local plumbing service\nIntent: Local service\nPosition: Not ranking\nGoal: Local pack + top 3",
                    output="# Emergency Plumber Near Me | 24/7 Local Plumbing Service in [CITY]\n\n[First paragraph with location + service + urgency]\n\nMeta Description: Need an emergency plumber near you? Our 24/7 local plumbing service responds in 30 min. Licensed, insured, 500+ 5-star reviews. Call now: [phone]\n\nLocal SEO Optimization:\n1. Location keywords in title, H1, first paragraph\n2. Service area pages (neighborhoods)\n3. Schema: LocalBusiness + Service\n4. Google Business Profile optimization needed\n5. Review widgets (social proof)\n6. Emergency call button (mobile)\n\nContent Structure:\n- H2: Emergency Plumbing Services We Provide\n- H2: Why Choose Our Local Plumbers\n- H2: Service Areas in [CITY]\n- H2: Real Customer Reviews\n- H2: Same-Day Plumbing FAQ\n\nLocal Ranking Factors:\n→ NAP consistency across web\n→ Citation building: Yelp, Angi, HomeAdvisor\n→ Location pages for each neighborhood\n→ Click-to-call: (555) 123-4567"
                ),
                FewShotExample(
                    input="Content: [Blog about productivity]\nKeyword: how to be more productive\nSecondary: productivity tips, increase productivity\nIntent: Informational/how-to\nPosition: Page 2\nGoal: Featured snippet",
                    output="# How to Be More Productive: 11 Science-Backed Tips (2025 Guide)\n\n[First paragraph answers question directly - featured snippet target]\n\nMeta Description: Learn how to be more productive with 11 proven tips. Science-backed productivity methods that actually work. Boost your output by 40% in 30 days.\n\nFeatured Snippet Optimization:\n**Direct Answer (paragraph):**\nTo be more productive, focus on three core principles: eliminate distractions, work in focused time blocks, and prioritize high-impact tasks first. Studies show this approach increases productivity by 40% on average.\n\n**List Format (also targets snippets):**\n1. Use the Pomodoro Technique (25-min blocks)\n2. Eliminate notifications during deep work\n3. Do your hardest task first (eat the frog)\n[...etc]\n\n**Table Format:**\nTechnique | Time Required | Productivity Gain | Best For\n\nContent Enhancements:\n- Jump links (table of contents)\n- FAQ schema for \"People Also Ask\"\n- Original research/data (linkable asset)\n- Year in title (freshness signal)\n- Before/after examples\n\nInternal Links:\n- \"time management techniques\"\n- \"focus improvement guide\"\n- \"work-life balance tips\""
                ),
                FewShotExample(
                    input="Content: [E-commerce category page]\nKeyword: running shoes for women\nSecondary: women's running sneakers, best running shoes\nIntent: Commercial/buying\nPosition: Page 4\nGoal: Top 3 + shopping results",
                    output="# Women's Running Shoes | 500+ Styles from Top Brands\n\nShop the best running shoes for women at [Brand]. Free shipping, 90-day returns, expert fitting advice.\n\n[Product grid with filters]\n\nE-commerce SEO Optimization:\n\n1. **Product Schema Markup:**\n   - Price\n   - Availability\n   - Reviews/ratings\n   - Brand\n   - SKU\n\n2. **Filter Options (crawlable URLs):**\n   - By brand: Nike, Adidas, Brooks\n   - By terrain: road, trail, track\n   - By support: neutral, stability, motion control\n   - By price: Under $100, $100-150, $150+\n\n3. **Trust Signals:**\n   - 4.8/5 stars (15,234 reviews)\n   - Free shipping + returns\n   - Expert staff available\n   - Authorized retailer badges\n\n4. **Content Sections:**\n   H2: How to Choose Running Shoes (buying guide)\n   H2: Top-Rated Women's Running Sneakers\n   H2: Running Shoe Size Guide\n   H2: Customer Reviews & Photos\n\n5. **Technical SEO:**\n   - Faceted navigation parameters\n   - Canonical tags for filter combinations\n   - Mobile-optimized (60% of traffic)\n   - Core Web Vitals optimization\n   - Product image alt text with keywords\n\nGoogle Shopping Feed:\n→ Product titles optimized\n→ High-quality images (white background)\n→ GTIN/UPC included\n→ Competitive pricing"
                ),
                FewShotExample(
                    input="Content: [About page for law firm]\nKeyword: personal injury lawyer [city]\nSecondary: car accident attorney, injury law firm\nIntent: Research/evaluation\nPosition: Page 5\nGoal: First page + trust",
                    output="# [City]'s Top Personal Injury Lawyer | 25+ Years Experience\n\nRecovered $50M+ for injury victims. Free consultation. We don't get paid unless you win.\n\nMeta Description: Award-winning personal injury lawyer in [City]. Specialized in car accident cases. 95% success rate, $50M+ recovered. Free consultation: [phone].\n\nE-E-A-T Optimization (Expertise, Experience, Authoritativeness, Trust):\n\n1. **Credentials Section:**\n   - Bar admissions\n   - Years practicing (25+)\n   - Case results ($50M recovered)\n   - Awards & recognition\n   - Attorney bio with photo\n\n2. **Case Results:**\n   - Specific verdicts/settlements\n   - Before/after scenarios\n   - Client testimonials with photos\n   - Video testimonials\n\n3. **Trust Signals:**\n   - Professional photos\n   - Office location (not just mail drop)\n   - Clear attorney photos\n   - Bar association memberships\n   - Community involvement\n   - Press mentions\n\n4. **Content Strategy:**\n   H2: Our Personal Injury Law Practice Areas\n   - Car accident attorney services\n   - [Detailed practice areas]\n   \n   H2: Why Choose Our Injury Law Firm\n   - Experience\n   - Results\n   - Client service\n   \n   H2: What Clients Say\n   [Video testimonials]\n   \n   H2: Free Case Evaluation\n   [Contact form above fold]\n\n5. **Schema Markup:**\n   - LegalService\n   - Attorney\n   - Review aggregate rating\n   - FAQ\n\nLocal SEO:\n→ Google Business Profile with reviews\n→ Avvo, Justia, Martindale profiles\n→ City/neighborhood service pages\n→ Personal injury case studies (location-specific)"
                )
            ],
            temperature=0.5,
            max_tokens=2000
        ))
    
    # ============= Education Prompts =============
    
    def _load_education_prompts(self):
        """Load education prompt templates"""
        
        # Concept Explanation
        self.register_prompt(PromptTemplate(
            task_type=TaskType.CONCEPT_EXPLANATION,
            industry=Industry.EDUCATION,
            system_prompt="""You are an expert educator who explains complex concepts in simple, engaging ways.

Your teaching philosophy:
- Meet students where they are (adapt to their level)
- Use analogies and real-world examples
- Break complex ideas into smaller steps
- Check for understanding throughout
- Encourage questions and curiosity

Guidelines:
1. Start with what they already know
2. Introduce ONE new concept at a time
3. Use concrete examples before abstract
4. Include visual descriptions (if helpful)
5. End with a simple check-for-understanding question""",
            user_template="""Explain: {concept}

Student Level: {level}
Prior Knowledge: {prior_knowledge}
Learning Style: {learning_style}
Common Confusion: {common_confusion}

Goal: {goal}""",
            variables=["concept", "level", "prior_knowledge", "learning_style", "common_confusion", "goal"],
            few_shot_examples=[
                FewShotExample(
                    input="Concept: Photosynthesis\nLevel: 8th grade\nPrior: Basic plant biology\nStyle: Visual learner\nConfusion: Where energy comes from\nGoal: Understand the process",
                    output="Think of plants as having tiny solar panels in their leaves.\n\n**What You Already Know:**\nYou know plants need sunlight, water, and air to survive. But WHY?\n\n**The Simple Answer:**\nPlants are making food (sugar) using sunlight as energy. This process is called photosynthesis (photo = light, synthesis = making).\n\n**The Step-by-Step:**\n\n1. **Sunlight hits the leaf**\n   → Imagine tiny green solar panels (chloroplasts) catching the light\n\n2. **Plant takes in CO₂ from air**\n   → Through tiny holes in leaves (stomata)\n   → Think: plant is \"breathing in\"\n\n3. **Plant absorbs water from roots**\n   → Travels up through stem to leaves\n   → Like water through a straw\n\n4. **Magic happens: light energy converts these into sugar**\n   → Chemical equation: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂\n   → Translation: carbon dioxide + water + sunlight → sugar + oxygen\n\n5. **Plant uses sugar for energy**\n   → Just like you use food for energy\n\n**The Bonus:**\nOxygen is released as a \"waste product\"—which is lucky for us because we need it to breathe!\n\n**Check Your Understanding:**\nIf you put a plant in a dark closet for a week, what would happen and why?\n\n(Answer: It couldn't make food without sunlight, so it would start to die—like you going without eating.)"
                ),
                FewShotExample(
                    input="Concept: Quadratic equations\nLevel: 10th grade (Algebra 2)\nPrior: Linear equations, basic factoring\nStyle: Logical/sequential\nConfusion: Why we have two solutions\nGoal: Solve ax²+bx+c=0",
                    output="**What You Already Know:**\nIn linear equations (like 2x + 3 = 7), you get ONE answer: x = 2.\n\nWith quadratic equations, you get TWO answers. Here's why that makes sense:\n\n**The Intuition:**\nThink about throwing a ball. It goes up, then comes down. It crosses the same height (say, 5 feet) at TWO different times:\n- Once on the way up\n- Once on the way down\n\nQuadratic equations model this parabola shape, so two solutions = two points where the curve crosses a line.\n\n**Solving ax² + bx + c = 0:**\n\n**Method 1: Factoring** (when it's easy)\n\nExample: x² + 5x + 6 = 0\n\n1. Find two numbers that:\n   - Multiply to give c (6)\n   - Add to give b (5)\n   → Numbers are 2 and 3\n\n2. Factor: (x + 2)(x + 3) = 0\n\n3. Set each equal to zero:\n   - x + 2 = 0 → x = -2\n   - x + 3 = 0 → x = -3\n\nSolutions: x = -2 or x = -3\n\n**Method 2: Quadratic Formula** (always works)\n\nFor ax² + bx + c = 0:\n\nx = [-b ± √(b² - 4ac)] / 2a\n\nExample: 2x² + 5x - 3 = 0\n- a = 2, b = 5, c = -3\n\nx = [-5 ± √(25 - 4(2)(-3))] / 4\nx = [-5 ± √49] / 4\nx = [-5 ± 7] / 4\n\nTwo solutions:\nx = (-5 + 7)/4 = 1/2\nx = (-5 - 7)/4 = -3\n\n**Why Two Solutions Makes Sense:**\nThe ± sign in the formula gives you both solutions (one with +, one with -).\n\n**Check Your Understanding:**\nSolve: x² - 4 = 0\n(Hint: This one's easy to factor!)\n\n(Answer: x = 2 or x = -2, because both 2² and (-2)² equal 4)"
                ),
                FewShotExample(
                    input="Concept: Supply and demand\nLevel: High school economics\nPrior: Basic understanding of buying/selling\nStyle: Real-world examples\nConfusion: Why prices change\nGoal: Understand market equilibrium",
                    output="Let's talk about why concert tickets for Taylor Swift cost $500 but a banana costs $0.50.\n\n**Supply and Demand in 10 Seconds:**\n- High demand + low supply = high prices\n- Low demand + high supply = low prices\n\n**Real Example: PlayStation 5 Launch (2020)**\n\nDay 1:\n- Supply: 100,000 consoles available\n- Demand: 5 million people want one\n- Result: Instant sellout, scalpers charging $1,200 (retail was $500)\n\nWhy? Way more demand than supply → price goes up.\n\n6 Months Later:\n- Supply: Sony makes more (500,000 available)\n- Demand: Still high but some people already bought\n- Result: Easier to find, scalper prices drop to $800\n\nWhy? Supply increasing + demand staying same = price drops.\n\n1 Year Later:\n- Supply: Plenty available in stores\n- Demand: Most hardcore fans already have one\n- Result: Selling at retail price ($500), sometimes on sale\n\nWhy? Supply met demand = market equilibrium (balanced price).\n\n**The Graph:**\n```\nPrice\n  ↑\n  |     Supply ↗\n  |       ⚡ (equilibrium point)\n  |    Demand ↘\n  |_______________→ Quantity\n```\n\nWhere the lines cross = equilibrium price (balanced).\n\n**Why It Matters:**\n- Shortage? Prices rise (PS5, concert tickets, gas during crisis)\n- Surplus? Prices fall (bananas, last year's iPhone, clearance sales)\n\n**Check Your Understanding:**\nIf a new iPhone launches and Apple can't make enough to meet demand, what happens to:\n1. The retail price? (Hint: Apple keeps it fixed at $999)\n2. The resale price? (Hint: What do scalpers do?)\n\n(Answer: 1) Retail stays $999, but good luck finding one. 2) Resale prices skyrocket to $1,500+ because demand > supply.)"
                ),
                FewShotExample(
                    input="Concept: Newton's Third Law\nLevel: Middle school physics\nPrior: Basic understanding of force\nStyle: Hands-on/kinesthetic\nConfusion: How forces are 'equal and opposite'\nGoal: Understand action-reaction pairs",
                    output="**Newton's Third Law: For every action, there's an equal and opposite reaction.**\n\nSounds confusing. Let's make it physical.\n\n**Try This Right Now:**\n1. Put your hands together (like praying)\n2. Push your right hand against your left hand\n3. What do you feel?\n\nYour RIGHT hand feels the LEFT hand pushing back, right?\nYour LEFT hand feels the RIGHT hand pushing back.\n\nBoth hands feel the SAME force, just in OPPOSITE directions.\n\nThat's Newton's Third Law.\n\n**Real Examples:**\n\n**Example 1: Jumping**\n- Action: Your feet push DOWN on the ground\n- Reaction: Ground pushes UP on your feet (launching you into the air)\n\nWhy you can't jump on ice: Ice can't push back effectively (slippery), so no reaction force.\n\n**Example 2: Swimming**\n- Action: You push water BACKWARD with your hands\n- Reaction: Water pushes YOU forward\n\nWhy you move forward even though you're pushing backward!\n\n**Example 3: Rocket Launch**\n- Action: Rocket pushes hot gas DOWNWARD (out the bottom)\n- Reaction: Hot gas pushes rocket UPWARD\n\nNo air needed! Works in space because the reaction comes from the gas itself.\n\n**The Confusing Part (Let's Clear It Up):**\n\n\"If forces are equal and opposite, why does anything move?\"\n\nBecause the forces act on DIFFERENT objects!\n\n- When you jump: Force on ground (downward) vs. force on YOU (upward)\n- The ground is WAY heavier, so it doesn't move much\n- But YOU are lighter, so you launch into the air\n\n**Check Your Understanding:**\nYou're in a canoe and push against a dock to leave shore. What are the action-reaction forces? Which object moves more and why?\n\n(Answer: Action = you push dock. Reaction = dock pushes canoe. Canoe moves more because it's lighter than the dock + entire Earth!)"
                ),
                FewShotExample(
                    input="Concept: Cell division (mitosis)\nLevel: High school biology\nPrior: Knows cells are building blocks of life\nStyle: Visual learner\nConfusion: Why cells divide\nGoal: Understand mitosis stages",
                    output="**Why Do Cells Divide?**\n\nThink of a city. As it grows, you need to split it into neighborhoods (zones) so services (mail, power, police) can reach everyone efficiently.\n\nCells divide for the same reason:\n1. Growth (baby → adult = trillions of cell divisions)\n2. Repair (healing a cut = new cells replacing damaged ones)\n3. Replacement (skin cells die and shed constantly)\n\n**Mitosis: Copying One Cell Into Two Identical Cells**\n\nThink of mitosis as photocopying:\n- Original document = parent cell\n- Two copies = two daughter cells (identical twins)\n\n**The Stages (Easy Acronym: IPMAT)**\n\n**I - Interphase** (Cell prepares)\n- DNA copies itself (now you have 2x the genetic material)\n- Think: Photocopier making a duplicate before cutting the paper\n\n**P - Prophase** (Getting organized)\n- DNA condenses into visible chromosomes (looks like X shapes)\n- Nuclear membrane dissolves\n- Think: Packing boxes before moving day\n\n**M - Metaphase** (Line 'em up)\n- Chromosomes line up in the center of the cell\n- Spindle fibers attach (like ropes)\n- Think: Tug-of-war teams lining up before pulling\n\n**A - Anaphase** (Splitsville)\n- Chromosomes pull apart to opposite ends\n- Now each end has one complete set\n- Think: Tug-of-war—each team pulls their rope to their side\n\n**T - Telophase** (Two new cells)\n- New nuclear membranes form around each set\n- Cell membrane pinches in the middle (cytokinesis)\n- Think: Cutting a sandwich in half—now you have two\n\n**Visual Analogy:**\n```\nInterphase:  ⭕ (1 cell, DNA doubles inside)\nProphase:    ⭕ with XX visible inside\nMetaphase:   ⭕ with XX lined up in center\nAnaphase:    ⭕ with X→ ←X pulling apart\nTelophase:   ⭕⭕ (two separate cells forming)\nResult:      ⭕  ⭕ (two identical cells)\n```\n\n**The Key Point:**\nEach daughter cell gets IDENTICAL DNA to the parent. That's why mitosis is for growth and repair (not creating diversity—that's meiosis, different process).\n\n**Check Your Understanding:**\nA skin cell has 46 chromosomes. After mitosis, how many chromosomes does each new cell have?\n\n(Answer: 46. Each daughter cell is an identical copy!)"
                )
            ],
            use_chain_of_thought=True,
            temperature=0.7,
            max_tokens=1500
        ))
    
    # ============= Sales Prompts =============
    
    def _load_sales_prompts(self):
        """Load sales prompt templates"""
        
        # Outreach Message
        self.register_prompt(PromptTemplate(
            task_type=TaskType.OUTREACH_MESSAGE,
            industry=Industry.SALES,
            system_prompt="""You are a top-performing sales development representative (SDR) who crafts personalized, value-driven outreach messages.

Your expertise:
- Researching prospects thoroughly
- Leading with value, not product features
- Creating genuine curiosity
- Respecting the prospect's time
- Following up persistently without being pushy

Guidelines:
1. Subject line: Personalized, curiosity-driven (5-7 words)
2. Opening: Reference something specific about them/their company
3. Value prop: Focus on THEIR problem, not your solution
4. CTA: Low-commitment ask (15-min call, quick question)
5. Length: 75-150 words maximum
6. Tone: Professional but human (no corporate jargon)""",
            user_template="""Create outreach message:

Prospect: {prospect_name}
Company: {company}
Role: {role}
Industry: {industry}
Research Notes: {research_notes}

Our Value Prop: {value_prop}
Goal: {goal}
Channel: {channel}""",
            variables=["prospect_name", "company", "role", "industry", "research_notes", "value_prop", "goal", "channel"],
            few_shot_examples=[
                FewShotExample(
                    input="Prospect: Sarah Chen\nCompany: TechStart (50 employees, B2B SaaS)\nRole: VP Sales\nIndustry: Sales enablement software\nResearch: Just raised Series A, hiring 10 SDRs\nValue: We help sales teams ramp new hires 50% faster\nGoal: Book discovery call\nChannel: LinkedIn",
                    output="**Subject:** Congrats on the Series A, Sarah!\n\n**Message:**\nSaw TechStart raised $5M—congrats! 🎉\n\nI noticed you're hiring 10 SDRs (LinkedIn posts). Having onboarded sales teams at 3 startups, I know the pain: New reps take 4-6 months to ramp, and you need them productive NOW.\n\nWe've helped Series A companies cut ramp time in half. One client (similar stage) had new SDRs booking meetings in Week 2.\n\nWorth a 15-min conversation? I promise to keep it tight.\n\n- Alex\nP.S. No pressure if timing's off—happy to share our onboarding playbook either way."
                ),
                FewShotExample(
                    input="Prospect: Michael Torres\nCompany: RetailCo (2,000 employees, e-commerce)\nRole: Director of Operations\nIndustry: Retail/E-commerce\nResearch: Mentioned supply chain issues in recent interview\nValue: Inventory optimization software (reduce stockouts by 40%)\nGoal: Get response/interest\nChannel: Email (cold)",
                    output="**Subject:** Your Retail Dive interview (supply chain)\n\n**Body:**\nHi Michael,\n\nRead your interview in Retail Dive last week—your point about supply chain complexity hit home.\n\nYou mentioned stockouts costing RetailCo $2M+ in lost sales last Q4. We work with mid-market retailers facing the same issue.\n\nOur clients (similar size to RetailCo) reduced stockouts by 40% in 90 days using predictive inventory optimization.\n\nInterested in seeing how? I can walk you through a quick 10-min demo tailored to your supply chain.\n\nLet me know—happy to send over a case study first if you prefer.\n\nBest,\nJessica\n\n---\nJessica Park | Enterprise Sales\nSupplyAI | jessica@supplyai.com"
                ),
                FewShotExample(
                    input="Prospect: David Kim\nCompany: FinanceHub (banking/fintech)\nRole: CTO\nIndustry: Financial services\nResearch: Company launched mobile app 6 months ago\nValue: API security platform (prevent data breaches)\nGoal: Book technical demo\nChannel: Email (warm intro via mutual connection)",
                    output="**Subject:** Intro from James @ Sequoia (API security)\n\n**Body:**\nHi David,\n\nJames Wu (Sequoia) suggested I reach out—he mentioned FinanceHub's mobile app is scaling fast.\n\nQuick context: We help fintechs secure their APIs. With mobile banking apps, API attacks are the #1 vector for breaches (Verizon 2024 report: 62% of fintech breaches).\n\nGiven you're processing transactions at scale now, figured it might be worth a conversation.\n\nI'd love to show you how we protect similar apps (including 2 of the top 10 neobanks). 20-minute technical walkthrough?\n\nLet me know what works.\n\n- Marcus\n\nP.S. Referencing James but no pressure—happy to share our security assessment framework regardless."
                ),
                FewShotExample(
                    input="Prospect: Emily Rodriguez\nCompany: HealthTech Inc (healthcare software)\nRole: CEO\nIndustry: Healthcare/HIPAA\nResearch: Recently posted about patient data compliance challenges\nValue: HIPAA-compliant cloud infrastructure\nGoal: Get meeting\nChannel: LinkedIn + Email combo",
                    output="**LinkedIn Message:**\nEmily, saw your post about HIPAA compliance headaches. Been there—at my last company, we failed an audit and spent 6 months fixing it.\n\nMind if I share what we learned? Might save you some pain.\n\n---\n\n**Follow-up Email (if no response after 3 days):**\n**Subject:** HIPAA compliance (your LinkedIn post)\n\nHi Emily,\n\nSent you a note on LinkedIn but figured email might be easier.\n\nYour post about patient data compliance resonated. Most healthcare startups underestimate HIPAA until an audit hits—then it's a 6-month fire drill.\n\nWe built infrastructure specifically for healthcare companies tired of compliance anxiety. Our clients pass audits first try and spend 80% less time on security paperwork.\n\nWorth a conversation? I can show you:\n1. How others handle the same challenges\n2. A 10-min compliance assessment (free)\n\nLet me know if Friday works.\n\nBest,\nRyan\n\n---\nRyan Martinez | Healthcare Solutions\nCloudHealth | ryan@cloudhealth.com | (555) 234-5678"
                ),
                FewShotExample(
                    input="Prospect: Amanda Foster\nCompany: MarketingPro (marketing agency, 30 people)\nRole: Founder\nIndustry: Marketing/advertising\nResearch: Agency recently lost a big client (public news)\nValue: Client reporting automation (save 10 hrs/week per account)\nGoal: Provide value first, then book call\nChannel: Email",
                    output="**Subject:** Saw the news about [Client]—here's something that might help\n\n**Body:**\nHi Amanda,\n\nSaw MarketingPro parted ways with [Client] last month. Never easy, regardless of circumstances.\n\nI run sales for a tool that helps agencies scale without scaling headcount—specifically, automating client reporting.\n\nThought you might find this useful (no strings attached):\n→ Free template: \"How to Land 5 Clients Without Hiring\"\n→ Includes our agency playbook\n\n[Download link]\n\nIf you find it helpful and want to chat about how agencies your size use automation to grow, I'm happy to walk you through it (20 min max).\n\nEither way, hope the template helps.\n\nCheers,\nSarah\n\n---\nSarah Chen | Agency Partnerships\nReportDash | sarah@reportdash.com\n\nP.S. We work with 50+ agencies (10-100 people). Happy to intro you to a couple if you want the real scoop."
                )
            ],
            temperature=0.75,
            max_tokens=800
        ))


# Global instance
prompt_library = PromptLibrary()
