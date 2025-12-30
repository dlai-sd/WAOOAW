# Epic 5.1: Agent Memory & Context Foundation

**Status:** Planning  
**Priority:** CRITICAL  
**Story Points:** 34  
**Timeline:** 2-3 Weeks  
**Version:** 1.0.0

---

## Epic Overview

Build foundational memory and context systems for all 22 agents to enable personalized, context-aware responses. This is Phase 1 of the Budget Edition Agent Maturity Journey.

### Business Value
- **Customer Experience:** Eliminate need to repeat context, build on previous conversations
- **Efficiency:** 30% reduction in clarification requests
- **Success Rate:** 65% → 78% task success rate (+20% improvement)
- **Satisfaction:** 3.8 → 4.1 CSAT
- **Cost:** $0 additional infrastructure (uses existing Redis + PostgreSQL)

### Success Metrics
- 80%+ of tasks use session context
- 30% reduction in "I need more information" responses
- 78%+ task success rate (measured by 4-5 star ratings)
- 4.1+ average CSAT score
- <50ms context retrieval latency

---

## Architecture Components

### Existing Infrastructure (No New Costs)
```
Redis (Already Running):
├── Session context storage (TTL: 7-30 days)
├── Fast retrieval (<10ms)
└── Customer interaction buffers

PostgreSQL (Already Running):
├── Customer profiles (long-term storage)
├── Interaction history (permanent logs)
└── Analytics aggregates
```

### New Components (This Epic)
```
Memory System:
├── Session Memory Manager (Redis-based)
├── Customer Profile Builder (PostgreSQL)
├── Interaction Logger (PostgreSQL)
└── Context Injection Service (Prompt enhancement)
```

---

## Stories

### Story 5.1.1: Short-Term Session Memory (13 points)
**Priority:** CRITICAL | **Dependencies:** None

#### Description
Implement Redis-based session memory that stores last 10 interactions per customer, enabling agents to reference previous conversations within a trial or subscription period.

#### Acceptance Criteria
- ✅ Session data stored in Redis with customer-scoped keys
- ✅ TTL: 7 days for trial customers, 30 days for paid customers
- ✅ Store last 10 interactions per customer (FIFO)
- ✅ Data includes: timestamp, task_type, input, output, rating, duration
- ✅ Context retrieval takes <50ms
- ✅ Automatic cleanup on TTL expiry
- ✅ 100% of agent requests check for session context

#### Technical Tasks

**1. Create Session Memory Manager (3 days)**
```python
# File: backend/app/services/memory/session_memory.py

from typing import List, Dict, Optional
import json
from datetime import timedelta
import redis.asyncio as redis

class SessionMemoryManager:
    """Manages short-term session memory in Redis"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.max_interactions = 10
        
    async def store_interaction(
        self, 
        customer_id: str,
        interaction: Dict,
        is_trial: bool = True
    ) -> None:
        """Store interaction in session memory"""
        key = f"session:{customer_id}"
        
        # Add to list (newest first)
        await self.redis.lpush(key, json.dumps(interaction))
        
        # Trim to max size
        await self.redis.ltrim(key, 0, self.max_interactions - 1)
        
        # Set TTL
        ttl = timedelta(days=7 if is_trial else 30)
        await self.redis.expire(key, int(ttl.total_seconds()))
    
    async def get_session_context(
        self, 
        customer_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Retrieve session history"""
        key = f"session:{customer_id}"
        raw_data = await self.redis.lrange(key, 0, limit - 1)
        return [json.loads(d) for d in raw_data]
    
    async def clear_session(self, customer_id: str) -> None:
        """Clear session memory (on explicit request)"""
        key = f"session:{customer_id}"
        await self.redis.delete(key)
    
    async def get_session_summary(self, customer_id: str) -> Dict:
        """Get session statistics"""
        context = await self.get_session_context(customer_id)
        
        if not context:
            return {"has_history": False}
        
        return {
            "has_history": True,
            "interaction_count": len(context),
            "most_recent_task": context[0].get("task_type"),
            "most_recent_timestamp": context[0].get("timestamp"),
            "avg_rating": sum(c.get("rating", 0) for c in context if c.get("rating")) / len([c for c in context if c.get("rating")]) if any(c.get("rating") for c in context) else None
        }
```

**2. Integrate with Agent Task Execution (2 days)**
```python
# File: backend/app/services/agent_service.py

async def execute_agent_task(
    agent_id: str,
    customer_id: str,
    task: Dict
) -> Dict:
    """Execute agent task with session context"""
    
    # Retrieve session context
    session_memory = SessionMemoryManager(redis_client)
    context = await session_memory.get_session_context(customer_id, limit=10)
    
    # Build enhanced prompt with context
    prompt = build_contextual_prompt(
        agent_id=agent_id,
        task=task,
        session_context=context
    )
    
    # Execute task
    result = await agent.execute(prompt)
    
    # Store interaction in session memory
    interaction = {
        "timestamp": datetime.utcnow().isoformat(),
        "task_type": task.get("type"),
        "input": task.get("description"),
        "output": result.get("output"),
        "rating": None,  # Will be updated later
        "duration_ms": result.get("duration_ms")
    }
    
    customer = await get_customer(customer_id)
    await session_memory.store_interaction(
        customer_id=customer_id,
        interaction=interaction,
        is_trial=customer.subscription_status == "trial"
    )
    
    return result
```

**3. Add Context Injection to Prompts (2 days)**
```python
# File: backend/app/services/prompt_builder.py

def build_contextual_prompt(
    agent_id: str,
    task: Dict,
    session_context: List[Dict]
) -> str:
    """Build prompt with session context"""
    
    agent = get_agent(agent_id)
    
    # Base system prompt
    prompt = f"""You are a {agent.specialty} agent.

AGENT CONTEXT:
- Specialty: {agent.specialty}
- Industry: {agent.industry}
- Strengths: {', '.join(agent.strengths)}
"""
    
    # Add session context if available
    if session_context:
        prompt += "\n\nRECENT CONVERSATION HISTORY:\n"
        
        # Include last 3 interactions
        for i, interaction in enumerate(session_context[:3], 1):
            prompt += f"\nInteraction {i} ({interaction['timestamp']}):\n"
            prompt += f"Customer requested: {interaction['input'][:200]}...\n"
            prompt += f"You provided: {interaction['output'][:200]}...\n"
            if interaction.get('rating'):
                prompt += f"Customer rating: {interaction['rating']}/5\n"
        
        prompt += "\n[Use the conversation history above to provide contextually-aware responses. Reference previous work when relevant.]\n"
    
    # Add current task
    prompt += f"""

CURRENT TASK:
{task['description']}

Provide a response that:
1. Considers the conversation history (if any)
2. Builds on previous work when relevant
3. Addresses the specific request clearly
4. Is personalized to this customer's context
"""
    
    return prompt
```

**4. Add Session Management APIs (1 day)**
```python
# File: backend/app/api/v1/memory.py

from fastapi import APIRouter, Depends
from app.services.memory.session_memory import SessionMemoryManager

router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/session/{customer_id}")
async def get_session_context(
    customer_id: str,
    limit: int = 10,
    session_memory: SessionMemoryManager = Depends()
):
    """Get session context for customer"""
    context = await session_memory.get_session_context(customer_id, limit)
    summary = await session_memory.get_session_summary(customer_id)
    
    return {
        "customer_id": customer_id,
        "summary": summary,
        "interactions": context
    }

@router.delete("/session/{customer_id}")
async def clear_session(
    customer_id: str,
    session_memory: SessionMemoryManager = Depends()
):
    """Clear session memory (customer privacy request)"""
    await session_memory.clear_session(customer_id)
    return {"status": "cleared", "customer_id": customer_id}

@router.post("/session/{customer_id}/update-rating")
async def update_interaction_rating(
    customer_id: str,
    interaction_index: int,
    rating: int,
    session_memory: SessionMemoryManager = Depends()
):
    """Update rating for specific interaction"""
    # Retrieve context
    context = await session_memory.get_session_context(customer_id)
    
    # Update rating
    if 0 <= interaction_index < len(context):
        context[interaction_index]['rating'] = rating
        
        # Re-store (Redis doesn't support in-place updates)
        key = f"session:{customer_id}"
        await session_memory.redis.delete(key)
        for interaction in reversed(context):
            await session_memory.store_interaction(customer_id, interaction)
    
    return {"status": "updated"}
```

#### Testing Checklist
- [ ] Session memory stores 10 interactions correctly
- [ ] TTL works (7 days for trial, 30 days for paid)
- [ ] FIFO behavior (oldest interactions removed)
- [ ] Context retrieval <50ms (benchmark with 1000 customers)
- [ ] Prompts correctly inject last 3 interactions
- [ ] Agents reference previous work in responses
- [ ] Clear session API works
- [ ] No memory leaks (Redis memory stable)
- [ ] Concurrent access safe (multiple agents per customer)

#### Definition of Done
- Code reviewed and merged
- Unit tests: 90%+ coverage
- Integration tests pass with real Redis
- Load test: 1000 concurrent customers, <50ms retrieval
- Documentation: API docs, architecture diagram
- Deployed to staging, validated with 5 test customers

---

### Story 5.1.2: Customer Profile Memory (13 points)
**Priority:** HIGH | **Dependencies:** Story 5.1.1

#### Description
Build long-term customer profile system that stores business context, preferences, and goals. Profiles are built automatically from signup data and early interactions.

#### Acceptance Criteria
- ✅ PostgreSQL schema for customer profiles
- ✅ Profile includes: industry, company_size, goals, pain_points, preferences (tone, detail, format)
- ✅ Auto-build from signup form + first 3 interactions
- ✅ Injected into every agent prompt
- ✅ Profile updates on explicit feedback or detected pattern changes
- ✅ 100% of customers have profiles after 3 interactions

#### Technical Tasks

**1. Database Schema (1 day)**
```sql
-- File: backend/migrations/versions/005_customer_profiles.sql

CREATE TABLE customer_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    
    -- Business context
    industry TEXT,
    company_name TEXT,
    company_size TEXT CHECK (company_size IN ('1-10', '11-50', '51-200', '201-1000', '1000+')),
    website TEXT,
    
    -- Communication preferences
    preferences JSONB DEFAULT '{}'::jsonb,
    -- Example: {"tone": "casual", "detail_level": "high", "format": "bullets", "explanations": true}
    
    -- Goals and pain points
    goals TEXT[],
    pain_points TEXT[],
    use_cases TEXT[],
    
    -- Computed fields
    communication_style TEXT CHECK (communication_style IN ('formal', 'casual', 'balanced')),
    expertise_level TEXT CHECK (expertise_level IN ('beginner', 'intermediate', 'expert')),
    
    -- Metadata
    profile_completeness INTEGER DEFAULT 0 CHECK (profile_completeness BETWEEN 0 AND 100),
    last_updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(customer_id)
);

CREATE INDEX idx_customer_profiles_customer_id ON customer_profiles(customer_id);
CREATE INDEX idx_customer_profiles_industry ON customer_profiles(industry);
CREATE INDEX idx_customer_profiles_completeness ON customer_profiles(profile_completeness);

-- Trigger to update profile_completeness
CREATE OR REPLACE FUNCTION update_profile_completeness()
RETURNS TRIGGER AS $$
BEGIN
    NEW.profile_completeness := (
        CASE WHEN NEW.industry IS NOT NULL THEN 15 ELSE 0 END +
        CASE WHEN NEW.company_name IS NOT NULL THEN 10 ELSE 0 END +
        CASE WHEN NEW.company_size IS NOT NULL THEN 10 ELSE 0 END +
        CASE WHEN array_length(NEW.goals, 1) > 0 THEN 20 ELSE 0 END +
        CASE WHEN array_length(NEW.pain_points, 1) > 0 THEN 15 ELSE 0 END +
        CASE WHEN NEW.communication_style IS NOT NULL THEN 10 ELSE 0 END +
        CASE WHEN jsonb_array_length(NEW.preferences::jsonb) > 0 THEN 20 ELSE 0 END
    );
    NEW.last_updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_profile_completeness
    BEFORE INSERT OR UPDATE ON customer_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_profile_completeness();
```

**2. Profile Builder Service (3 days)**
```python
# File: backend/app/services/memory/profile_builder.py

from typing import Dict, List, Optional
import openai
import json

class CustomerProfileBuilder:
    """Builds customer profiles from interactions"""
    
    async def create_profile_from_signup(
        self,
        customer_id: str,
        signup_data: Dict
    ) -> Dict:
        """Create initial profile from signup form"""
        
        profile = {
            "customer_id": customer_id,
            "industry": signup_data.get("industry"),
            "company_name": signup_data.get("company_name"),
            "company_size": signup_data.get("company_size"),
            "website": signup_data.get("website"),
            "goals": signup_data.get("goals", []),
            "use_cases": signup_data.get("use_cases", []),
            "preferences": {},
            "communication_style": "balanced",
            "expertise_level": "intermediate"
        }
        
        await db.execute(
            "INSERT INTO customer_profiles (...) VALUES (...)",
            profile
        )
        
        return profile
    
    async def enrich_profile_from_interactions(
        self,
        customer_id: str,
        interactions: List[Dict]
    ) -> Dict:
        """Enrich profile using LLM analysis of first interactions"""
        
        if len(interactions) < 3:
            return None  # Not enough data
        
        # Build analysis prompt
        analysis_prompt = f"""Analyze these customer interactions and extract profile information:

INTERACTIONS:
{json.dumps(interactions, indent=2)}

Extract and return JSON with:
{{
    "goals": [list of customer's stated or implied goals],
    "pain_points": [list of problems or challenges mentioned],
    "communication_style": "formal" | "casual" | "balanced",
    "expertise_level": "beginner" | "intermediate" | "expert",
    "preferences": {{
        "tone": "formal" | "casual",
        "detail_level": "high" | "medium" | "low",
        "format": "bullets" | "paragraphs" | "mixed",
        "explanations": true | false
    }}
}}

Be specific and evidence-based. If unclear, omit the field.
"""
        
        # Call LLM for analysis
        response = await openai.chat.completions.create(
            model="gpt-4o-mini",  # Cheap model for analysis
            messages=[
                {"role": "system", "content": "You are an expert at analyzing customer interactions and extracting profile information."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        enrichment = json.loads(response.choices[0].message.content)
        
        # Update profile
        await db.execute("""
            UPDATE customer_profiles
            SET 
                goals = COALESCE($1, goals),
                pain_points = COALESCE($2, pain_points),
                communication_style = COALESCE($3, communication_style),
                expertise_level = COALESCE($4, expertise_level),
                preferences = COALESCE($5, preferences)
            WHERE customer_id = $6
        """, 
            enrichment.get("goals"),
            enrichment.get("pain_points"),
            enrichment.get("communication_style"),
            enrichment.get("expertise_level"),
            json.dumps(enrichment.get("preferences", {})),
            customer_id
        )
        
        return enrichment
    
    async def update_profile_from_feedback(
        self,
        customer_id: str,
        feedback: Dict
    ) -> None:
        """Update profile based on explicit feedback"""
        
        # Example: Customer says "make it more casual" -> update preferences
        if "tone" in feedback:
            await db.execute("""
                UPDATE customer_profiles
                SET preferences = jsonb_set(preferences, '{tone}', $1)
                WHERE customer_id = $2
            """, json.dumps(feedback["tone"]), customer_id)
```

**3. Profile Injection in Prompts (2 days)**
```python
# File: backend/app/services/prompt_builder.py (extend)

async def build_contextual_prompt(
    agent_id: str,
    customer_id: str,
    task: Dict,
    session_context: List[Dict]
) -> str:
    """Build prompt with session context AND customer profile"""
    
    agent = get_agent(agent_id)
    profile = await get_customer_profile(customer_id)
    
    # Base system prompt
    prompt = f"""You are a {agent.specialty} agent.

CUSTOMER PROFILE:
- Industry: {profile.industry or 'Not specified'}
- Company: {profile.company_name or 'Not specified'} ({profile.company_size or 'Unknown size'})
- Goals: {', '.join(profile.goals) if profile.goals else 'Exploring options'}
- Pain Points: {', '.join(profile.pain_points) if profile.pain_points else 'To be discovered'}
- Communication Style: {profile.communication_style}
- Expertise Level: {profile.expertise_level}

COMMUNICATION PREFERENCES:
- Tone: {profile.preferences.get('tone', 'balanced')}
- Detail Level: {profile.preferences.get('detail_level', 'medium')}
- Format: {profile.preferences.get('format', 'mixed')}
- Include Explanations: {profile.preferences.get('explanations', True)}
"""
    
    # Add session context
    if session_context:
        prompt += "\n\nRECENT CONVERSATION HISTORY:\n"
        for i, interaction in enumerate(session_context[:3], 1):
            prompt += f"\n{i}. {interaction['task_type']}: {interaction['input'][:150]}...\n"
    
    # Add current task
    prompt += f"""

CURRENT TASK:
{task['description']}

Provide a response that:
1. Matches the customer's communication preferences
2. Aligns with their industry and expertise level
3. Addresses their stated goals and pain points
4. Builds on conversation history when relevant
"""
    
    return prompt
```

**4. Profile Management APIs (2 days)**
```python
# File: backend/app/api/v1/profiles.py

@router.get("/profiles/{customer_id}")
async def get_customer_profile(customer_id: str):
    """Get customer profile"""
    profile = await db.fetchrow(
        "SELECT * FROM customer_profiles WHERE customer_id = $1",
        customer_id
    )
    return profile

@router.patch("/profiles/{customer_id}")
async def update_customer_profile(
    customer_id: str,
    updates: Dict
):
    """Update customer profile (explicit user edits)"""
    # Build dynamic UPDATE query
    set_clauses = []
    values = []
    
    for i, (key, value) in enumerate(updates.items(), 1):
        set_clauses.append(f"{key} = ${i}")
        values.append(value)
    
    query = f"""
        UPDATE customer_profiles
        SET {', '.join(set_clauses)}
        WHERE customer_id = ${len(values) + 1}
        RETURNING *
    """
    values.append(customer_id)
    
    updated = await db.fetchrow(query, *values)
    return updated

@router.post("/profiles/{customer_id}/enrich")
async def enrich_profile(customer_id: str):
    """Trigger profile enrichment from interactions"""
    session_memory = SessionMemoryManager(redis_client)
    interactions = await session_memory.get_session_context(customer_id, limit=10)
    
    profile_builder = CustomerProfileBuilder()
    enrichment = await profile_builder.enrich_profile_from_interactions(
        customer_id, 
        interactions
    )
    
    return {
        "status": "enriched",
        "customer_id": customer_id,
        "enrichment": enrichment
    }
```

**5. Background Job: Auto-Enrichment (1 day)**
```python
# File: backend/app/workers/profile_enrichment.py

async def auto_enrich_profiles():
    """Daily job: Enrich profiles for customers with 3+ interactions"""
    
    # Find customers with incomplete profiles and 3+ interactions
    customers = await db.fetch("""
        SELECT 
            cp.customer_id,
            cp.profile_completeness
        FROM customer_profiles cp
        WHERE cp.profile_completeness < 80
        AND EXISTS (
            SELECT 1 FROM interaction_logs il
            WHERE il.customer_id = cp.customer_id
            GROUP BY il.customer_id
            HAVING COUNT(*) >= 3
        )
    """)
    
    profile_builder = CustomerProfileBuilder()
    
    for customer in customers:
        session_memory = SessionMemoryManager(redis_client)
        interactions = await session_memory.get_session_context(
            customer['customer_id'], 
            limit=10
        )
        
        await profile_builder.enrich_profile_from_interactions(
            customer['customer_id'],
            interactions
        )
        
        logging.info(f"Enriched profile for customer {customer['customer_id']}")
```

#### Testing Checklist
- [ ] Profile schema created successfully
- [ ] Profiles auto-created on customer signup
- [ ] LLM enrichment extracts goals, pain points, preferences correctly
- [ ] Enrichment runs after 3rd interaction
- [ ] Profile completeness score calculated correctly
- [ ] Prompts inject profile data
- [ ] Agents adapt tone/detail based on preferences
- [ ] Profile update APIs work
- [ ] Background enrichment job runs daily
- [ ] 90%+ profile completeness after 5 interactions

#### Definition of Done
- Schema migrated to staging and production
- Profile builder service tested with 20 sample customers
- LLM extraction accuracy >85% (manual review)
- All APIs documented and tested
- Background job scheduled (daily at 2am)
- Agents demonstrably use profile data in responses

---

### Story 5.1.3: Interaction History & Analytics (8 points)
**Priority:** MEDIUM | **Dependencies:** Story 5.1.1, 5.1.2

#### Description
Log all agent interactions to PostgreSQL for permanent history, analytics, and future learning. Enable queries for customer patterns and agent performance.

#### Acceptance Criteria
- ✅ PostgreSQL table for interaction logs (permanent storage)
- ✅ Log: agent_id, customer_id, task_type, input, output, duration, rating, timestamp
- ✅ Indexed for fast queries (customer_id, agent_id, task_type, rating, created_at)
- ✅ Analytics queries: Customer's most common tasks, agent success rates by task type
- ✅ 100% of interactions logged within 500ms of completion
- ✅ No performance impact on agent execution

#### Technical Tasks

**1. Database Schema (1 day)**
```sql
-- File: backend/migrations/versions/006_interaction_logs.sql

CREATE TABLE interaction_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Entities
    agent_id UUID REFERENCES agents(id),
    customer_id UUID REFERENCES customers(id),
    
    -- Task details
    task_type TEXT NOT NULL,
    task_description TEXT,
    task_input JSONB,
    
    -- Results
    output TEXT,
    output_format TEXT,
    
    -- Performance
    duration_ms INTEGER,
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    
    -- Feedback
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    feedback_tags TEXT[],
    
    -- Metadata
    session_id TEXT,
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_interaction_logs_customer_id ON interaction_logs(customer_id);
CREATE INDEX idx_interaction_logs_agent_id ON interaction_logs(agent_id);
CREATE INDEX idx_interaction_logs_task_type ON interaction_logs(task_type);
CREATE INDEX idx_interaction_logs_rating ON interaction_logs(rating) WHERE rating IS NOT NULL;
CREATE INDEX idx_interaction_logs_created_at ON interaction_logs(created_at DESC);
CREATE INDEX idx_interaction_logs_customer_created ON interaction_logs(customer_id, created_at DESC);

-- Composite index for analytics
CREATE INDEX idx_interaction_logs_analytics ON interaction_logs(agent_id, task_type, rating, created_at);
```

**2. Logging Service (2 days)**
```python
# File: backend/app/services/logging/interaction_logger.py

class InteractionLogger:
    """Logs all agent interactions to PostgreSQL"""
    
    async def log_interaction(
        self,
        agent_id: str,
        customer_id: str,
        task: Dict,
        result: Dict,
        metadata: Dict = None
    ) -> str:
        """Log interaction"""
        
        interaction_id = await db.fetchval("""
            INSERT INTO interaction_logs (
                agent_id, customer_id, task_type, task_description,
                task_input, output, duration_ms, tokens_used,
                cost_usd, session_id, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
            RETURNING id
        """,
            agent_id,
            customer_id,
            task.get("type"),
            task.get("description"),
            json.dumps(task.get("input", {})),
            result.get("output"),
            result.get("duration_ms"),
            result.get("tokens_used"),
            result.get("cost_usd"),
            metadata.get("session_id") if metadata else None
        )
        
        return interaction_id
    
    async def update_feedback(
        self,
        interaction_id: str,
        rating: int,
        feedback_text: str = None,
        feedback_tags: List[str] = None
    ) -> None:
        """Update interaction with customer feedback"""
        
        await db.execute("""
            UPDATE interaction_logs
            SET 
                rating = $1,
                feedback_text = $2,
                feedback_tags = $3,
                updated_at = NOW()
            WHERE id = $4
        """, rating, feedback_text, feedback_tags, interaction_id)
```

**3. Analytics Queries (2 days)**
```python
# File: backend/app/services/analytics/interaction_analytics.py

class InteractionAnalytics:
    """Analytics on interaction history"""
    
    async def get_customer_task_patterns(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get customer's most common task types"""
        
        return await db.fetch("""
            SELECT 
                task_type,
                COUNT(*) as frequency,
                AVG(rating) as avg_rating,
                MAX(created_at) as last_requested
            FROM interaction_logs
            WHERE customer_id = $1 AND rating IS NOT NULL
            GROUP BY task_type
            ORDER BY frequency DESC
            LIMIT $2
        """, customer_id, limit)
    
    async def get_agent_performance(
        self,
        agent_id: str,
        days: int = 30
    ) -> Dict:
        """Get agent performance metrics"""
        
        stats = await db.fetchrow("""
            SELECT 
                COUNT(*) as total_tasks,
                AVG(rating) as avg_rating,
                SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END)::FLOAT / 
                    NULLIF(COUNT(*), 0) as success_rate,
                AVG(duration_ms) as avg_duration_ms,
                SUM(cost_usd) as total_cost
            FROM interaction_logs
            WHERE agent_id = $1 
            AND created_at > NOW() - INTERVAL '$2 days'
            AND rating IS NOT NULL
        """, agent_id, days)
        
        return dict(stats)
    
    async def get_agent_performance_by_task_type(
        self,
        agent_id: str,
        days: int = 30
    ) -> List[Dict]:
        """Get agent performance broken down by task type"""
        
        return await db.fetch("""
            SELECT 
                task_type,
                COUNT(*) as total_tasks,
                AVG(rating) as avg_rating,
                SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END)::FLOAT / 
                    NULLIF(COUNT(*), 0) as success_rate
            FROM interaction_logs
            WHERE agent_id = $1 
            AND created_at > NOW() - INTERVAL '$2 days'
            AND rating IS NOT NULL
            GROUP BY task_type
            ORDER BY total_tasks DESC
        """, agent_id, days)
    
    async def get_failing_task_types(
        self,
        days: int = 7,
        min_failures: int = 3
    ) -> List[Dict]:
        """Identify task types with high failure rates (for improvement)"""
        
        return await db.fetch("""
            SELECT 
                task_type,
                agent_id,
                COUNT(*) as failure_count,
                AVG(rating) as avg_rating,
                array_agg(DISTINCT feedback_tags) as common_issues
            FROM interaction_logs
            WHERE rating < 3
            AND created_at > NOW() - INTERVAL '$1 days'
            GROUP BY task_type, agent_id
            HAVING COUNT(*) >= $2
            ORDER BY failure_count DESC
        """, days, min_failures)
```

**4. Integration with Agent Execution (1 day)**
```python
# File: backend/app/services/agent_service.py (extend)

async def execute_agent_task(
    agent_id: str,
    customer_id: str,
    task: Dict
) -> Dict:
    """Execute agent task with full logging"""
    
    # ... existing context retrieval ...
    
    # Execute task
    start_time = time.time()
    result = await agent.execute(prompt)
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Log interaction
    logger = InteractionLogger()
    interaction_id = await logger.log_interaction(
        agent_id=agent_id,
        customer_id=customer_id,
        task=task,
        result={
            "output": result.get("output"),
            "duration_ms": duration_ms,
            "tokens_used": result.get("usage", {}).get("total_tokens"),
            "cost_usd": calculate_cost(result.get("usage"))
        }
    )
    
    # Store in session memory
    # ... existing code ...
    
    return {
        **result,
        "interaction_id": interaction_id
    }
```

**5. Analytics APIs (1 day)**
```python
# File: backend/app/api/v1/analytics.py

@router.get("/analytics/customers/{customer_id}/patterns")
async def get_customer_patterns(customer_id: str):
    """Get customer's task patterns"""
    analytics = InteractionAnalytics()
    patterns = await analytics.get_customer_task_patterns(customer_id)
    return {"customer_id": customer_id, "patterns": patterns}

@router.get("/analytics/agents/{agent_id}/performance")
async def get_agent_performance(
    agent_id: str,
    days: int = 30
):
    """Get agent performance metrics"""
    analytics = InteractionAnalytics()
    performance = await analytics.get_agent_performance(agent_id, days)
    by_task = await analytics.get_agent_performance_by_task_type(agent_id, days)
    
    return {
        "agent_id": agent_id,
        "period_days": days,
        "overall": performance,
        "by_task_type": by_task
    }

@router.get("/analytics/failing-tasks")
async def get_failing_tasks(days: int = 7):
    """Get task types with high failure rates"""
    analytics = InteractionAnalytics()
    failing = await analytics.get_failing_task_types(days)
    return {"period_days": days, "failing_tasks": failing}
```

#### Testing Checklist
- [ ] All interactions logged to PostgreSQL
- [ ] Logging doesn't slow down task execution (<50ms overhead)
- [ ] Indexes improve query performance (queries <100ms)
- [ ] Customer pattern queries return accurate results
- [ ] Agent performance metrics correct
- [ ] Failing task detection works
- [ ] APIs return data quickly (<200ms)
- [ ] No data loss under high load (1000 concurrent tasks)

#### Definition of Done
- Schema migrated, indexes created
- Logging integrated into all agent executions
- Analytics queries tested with 1000+ sample interactions
- APIs documented
- Dashboard in maintenance portal uses these analytics
- Performance benchmarked: <50ms logging overhead, <100ms query time

---

## Cross-Story Requirements

### Testing Strategy
1. **Unit Tests:** Each service tested independently (90%+ coverage)
2. **Integration Tests:** Test full flow (task → context retrieval → execution → logging)
3. **Load Tests:** 1000 concurrent customers, 100 tasks/second
4. **Accuracy Tests:** Verify context improves agent responses (manual review of 50 tasks)

### Deployment Plan
1. **Week 1:** Stories 5.1.1 and 5.1.2 to staging
2. **Week 2:** Test with 10 beta customers
3. **Week 3:** Story 5.1.3 + full rollout to production

### Monitoring
- **Metrics:** Context retrieval latency, profile completeness, logging throughput
- **Alerts:** Context retrieval >100ms, logging failures, Redis memory >80%
- **Dashboards:** Session memory usage, profile enrichment status, interaction log growth

---

## Success Validation

### Before (Baseline)
- Task Success Rate: 65%
- First-Time Resolution: 45%
- CSAT: 3.8/5.0
- Clarification Requests: ~40% of tasks

### After (Target)
- Task Success Rate: 78%+ (13% improvement)
- First-Time Resolution: 60%+ (15% improvement)
- CSAT: 4.1+/5.0 (0.3 improvement)
- Clarification Requests: <25% of tasks (-37%)

### Measurement
- **A/B Test:** 50% of customers get new memory system, 50% get old (random assignment)
- **Duration:** 2 weeks
- **Sample Size:** 100+ customers per group
- **Decision:** If success rate improves >10%, roll out to 100%

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Redis memory exhaustion | Low | High | Monitor usage, set max memory limits, TTL enforcement |
| Profile enrichment LLM costs | Medium | Low | Use GPT-4o-mini ($0.15/1M tokens), batch processing |
| Context doesn't improve responses | Medium | High | Manual review of 50 tasks, iterate on prompt templates |
| PostgreSQL storage growth | Low | Medium | Partition interaction_logs by month, archive old data |

---

## Next Steps After Epic Completion

1. **Measure Impact:** Run A/B test for 2 weeks, analyze results
2. **Epic 5.2:** If success rate improves >10%, proceed to Prompt Engineering & Knowledge Base
3. **Iterate:** If improvement <10%, refine context injection and profile enrichment
4. **Document:** Write customer-facing docs on how agents remember context

---

**Document Owner:** Product + Engineering Team  
**Review Date:** After 2-week A/B test  
**Expand Trigger:** If any story >13 points or takes >1 week
