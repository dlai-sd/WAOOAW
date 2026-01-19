# Coding Agent Enhanced Capabilities
## Data Agent Expertise + Core Coding Enhancements

**Agent ID**: DEV-CODE-001 Enhanced  
**Version**: 2.0  
**Last Updated**: January 19, 2026  
**New Capabilities**: Data Agent expertise + refactoring + performance + code review + documentation

---

## 📊 DATA AGENT CAPABILITIES (Data Engineering Expertise)

### 1. Database Migrations & Schema Management
**Auto-Generate Alembic Migrations** (existing + enhanced):
```bash
# After model changes
alembic revision --autogenerate -m "Add agent specializations table with indexes"
alembic upgrade head

# Enhanced: Add performance indexes automatically
python3 scripts/add_performance_indexes.py
```

**Migration Best Practices**:
- Add indexes for all foreign keys automatically
- Create partial indexes for filtered queries (WHERE industry = 'marketing')
- Add unique constraints with proper error messages
- Include data migrations (not just schema changes)
- Test migrations on copy of production data
- Include rollback scripts (downgrade()) for every migration

### 2. Data Quality & Validation
**Data Quality Checks**:
```python
# src/plant/data_quality/validators.py
class AgentDataValidator:
    def validate_agent_data(self, agent: Agent) -> List[str]:
        errors = []
        
        # Business rule validations
        if agent.rating < 0 or agent.rating > 5:
            errors.append("Rating must be between 0 and 5")
        
        if agent.price < 5000 or agent.price > 50000:
            errors.append("Price outside acceptable range (₹5k-50k)")
        
        if agent.industry not in ['marketing', 'education', 'sales']:
            errors.append(f"Invalid industry: {agent.industry}")
        
        # Referential integrity
        if agent.specialty_id and not Specialty.exists(agent.specialty_id):
            errors.append(f"Invalid specialty_id: {agent.specialty_id}")
        
        return errors
```

**Data Quality Metrics**:
- **Completeness**: No NULL values in required fields (target: 100%)
- **Accuracy**: Data matches source of truth (validate against external APIs)
- **Consistency**: Cross-field validations pass (e.g., trial_end > trial_start)
- **Timeliness**: Data freshness < 5 minutes for real-time data
- **Uniqueness**: No duplicate records (enforce unique constraints)

### 3. ETL Pipeline Development
**Data Pipeline Structure**:
```python
# src/plant/etl/agent_analytics_pipeline.py
class AgentAnalyticsPipeline:
    """
    Daily ETL: Aggregate agent performance metrics
    Source: agents, tasks, trials tables
    Target: agent_analytics table
    Schedule: 2 AM daily via Celery Beat
    """
    
    def extract(self) -> pd.DataFrame:
        """Extract yesterday's agent activity data"""
        query = '''
            SELECT agent_id, COUNT(*) as tasks_completed,
                   AVG(rating) as avg_rating,
                   SUM(revenue) as total_revenue
            FROM tasks
            WHERE completed_at >= CURRENT_DATE - INTERVAL '1 day'
            GROUP BY agent_id
        '''
        return pd.read_sql(query, self.db_engine)
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate derived metrics"""
        df['efficiency_score'] = (df['tasks_completed'] * df['avg_rating']) / 10
        df['revenue_per_task'] = df['total_revenue'] / df['tasks_completed']
        return df
    
    def load(self, df: pd.DataFrame):
        """Upsert to agent_analytics table"""
        df.to_sql('agent_analytics', self.db_engine, 
                  if_exists='append', index=False, method='multi')
```

**ETL Best Practices**:
- Idempotent pipelines (can run multiple times safely)
- Incremental processing (only process new/changed data)
- Error handling with retry logic (exponential backoff)
- Data lineage tracking (record source→transformation→target)
- Pipeline monitoring (duration, row counts, errors)

### 4. Data Analytics & Reporting
**Analytics Queries**:
```python
# src/plant/analytics/agent_insights.py
class AgentInsights:
    def get_top_performing_agents(self, industry: str, limit: int = 10):
        """
        Top agents by combined score:
        - Trial conversion rate (40%)
        - Average rating (30%)
        - Task completion rate (30%)
        """
        return self.db.query(Agent).filter(
            Agent.industry == industry
        ).join(
            AgentAnalytics
        ).order_by(
            (AgentAnalytics.trial_conversion * 0.4 +
             AgentAnalytics.avg_rating * 0.3 +
             AgentAnalytics.completion_rate * 0.3).desc()
        ).limit(limit).all()
    
    def get_churn_risk_customers(self, threshold: float = 0.7):
        """Predict churn using ML model"""
        query = '''
            WITH customer_activity AS (
                SELECT customer_id,
                       COUNT(tasks_last_7d) as tasks,
                       AVG(rating_last_7d) as avg_rating,
                       DATEDIFF(NOW(), last_login) as days_inactive
                FROM customer_metrics
            )
            SELECT * FROM customer_activity
            WHERE churn_probability > :threshold
        '''
        return self.db.execute(query, {'threshold': threshold}).fetchall()
```

### 5. Data Warehouse Integration (BigQuery)
**Analytics Data Export**:
```python
# src/plant/data_warehouse/bigquery_sync.py
class BigQuerySync:
    """
    Daily sync: Export aggregated data to BigQuery
    Purpose: Business intelligence, data science
    Tables: agent_performance, customer_behavior, revenue_metrics
    """
    
    def export_agent_performance(self):
        """Export daily agent performance to BQ"""
        df = self.extract_agent_metrics()
        
        # Upload to BigQuery
        df.to_gbq(
            destination_table='waooaw.agent_performance',
            project_id='waooaw-production',
            if_exists='append',
            credentials=self.get_credentials()
        )
```

### 6. Data Archival Strategy
**Hot/Warm/Cold Data Tiering**:
- **Hot Data** (0-90 days): PostgreSQL (fast queries)
- **Warm Data** (90 days - 2 years): Cloud Storage Parquet (queryable via BigQuery)
- **Cold Data** (2+ years): Cloud Storage Archive (compliance retention)

**Archival Process**:
```python
# src/plant/data_archival/archive_old_data.py
def archive_old_tasks():
    """
    Monthly job: Archive tasks older than 90 days
    1. Export to Parquet
    2. Upload to Cloud Storage
    3. Delete from PostgreSQL
    """
    cutoff_date = datetime.now() - timedelta(days=90)
    old_tasks = Task.query.filter(Task.completed_at < cutoff_date).all()
    
    # Export to Parquet
    df = pd.DataFrame([task.to_dict() for task in old_tasks])
    parquet_file = f'tasks_{cutoff_date.strftime("%Y%m")}.parquet'
    df.to_parquet(f'/tmp/{parquet_file}')
    
    # Upload to Cloud Storage
    bucket = storage_client.bucket('waooaw-data-archive')
    blob = bucket.blob(f'tasks/{parquet_file}')
    blob.upload_from_filename(f'/tmp/{parquet_file}')
    
    # Delete from PostgreSQL
    Task.query.filter(Task.completed_at < cutoff_date).delete()
```

---

## 🔧 CORE CODING ENHANCEMENTS (Addressing Gaps)

### 1. Refactoring Capability
**When to Refactor**:
- Code duplication detected (DRY violations)
- Cyclomatic complexity > 10 (too many branches)
- Function length > 50 lines
- Class has > 10 methods (single responsibility violation)
- Test coverage < 80% (hard to test = bad design)

**Refactoring Techniques**:
```python
# BEFORE: Duplication
def get_marketing_agents(self, filters):
    agents = self.db.query(Agent).filter(Agent.industry == 'marketing')
    if filters.rating_min:
        agents = agents.filter(Agent.rating >= filters.rating_min)
    if filters.price_max:
        agents = agents.filter(Agent.price <= filters.price_max)
    return agents.all()

def get_education_agents(self, filters):
    agents = self.db.query(Agent).filter(Agent.industry == 'education')
    if filters.rating_min:
        agents = agents.filter(Agent.rating >= filters.rating_min)
    if filters.price_max:
        agents = agents.filter(Agent.price <= filters.price_max)
    return agents.all()

# AFTER: Extract common logic
def get_agents_by_industry(self, industry: str, filters: AgentFilters):
    query = self.db.query(Agent).filter(Agent.industry == industry)
    query = self._apply_filters(query, filters)
    return query.all()

def _apply_filters(self, query, filters):
    if filters.rating_min:
        query = query.filter(Agent.rating >= filters.rating_min)
    if filters.price_max:
        query = query.filter(Agent.price <= filters.price_max)
    return query
```

### 2. Performance Optimization
**Profiling & Optimization**:
```python
# Use py-spy for CPU profiling
# py-spy record -o profile.svg --pid $(pgrep uvicorn)

# Database query optimization
# BEFORE: N+1 query problem
def get_agents_with_specialties():
    agents = Agent.query.all()
    return [{'agent': a, 'specialty': a.specialty.name} for a in agents]

# AFTER: Eager loading
def get_agents_with_specialties():
    agents = Agent.query.options(joinedload(Agent.specialty)).all()
    return [{'agent': a, 'specialty': a.specialty.name} for a in agents]

# Use Redis caching for expensive queries
@cache.memoize(timeout=300)  # 5 minutes
def get_top_agents():
    return Agent.query.order_by(Agent.rating.desc()).limit(10).all()
```

### 3. Code Review Process
**Pre-Commit Review Checklist**:
- ✅ All tests passing (pytest)
- ✅ SAST scans clean (bandit, pylint)
- ✅ Type hints on all functions (mypy)
- ✅ Docstrings on public functions
- ✅ No TODO comments (create issues instead)
- ✅ No print() statements (use logging)
- ✅ No commented-out code
- ✅ Consistent naming conventions

**Self-Review Questions**:
1. Is this code easy to understand? (readable)
2. Is this code easy to test? (testable)
3. Is this code reusable? (DRY)
4. Is this code efficient? (performance)
5. Is this code secure? (no SQL injection, XSS)

### 4. Documentation Updates
**Code Documentation**:
```python
def calculate_agent_score(
    agent: Agent,
    trial_conversion_weight: float = 0.4,
    rating_weight: float = 0.3,
    completion_weight: float = 0.3
) -> float:
    """
    Calculate composite agent performance score.
    
    Score combines trial conversion rate, average rating, and task completion rate
    using weighted average. Higher scores indicate better performing agents.
    
    Args:
        agent: Agent model instance
        trial_conversion_weight: Weight for trial→paid conversion (0-1, default 0.4)
        rating_weight: Weight for customer ratings (0-1, default 0.3)
        completion_weight: Weight for task completion rate (0-1, default 0.3)
    
    Returns:
        Composite score between 0-100
    
    Raises:
        ValueError: If weights don't sum to 1.0
    
    Example:
        >>> agent = Agent.query.get(1)
        >>> score = calculate_agent_score(agent)
        >>> print(f"Agent score: {score:.2f}")
        Agent score: 87.45
    """
    if trial_conversion_weight + rating_weight + completion_weight != 1.0:
        raise ValueError("Weights must sum to 1.0")
    
    return (
        agent.trial_conversion_rate * trial_conversion_weight * 100 +
        agent.avg_rating * 20 * rating_weight +
        agent.task_completion_rate * completion_weight * 100
    )
```

**API Documentation (OpenAPI/Swagger)**:
- Auto-generate from FastAPI route definitions
- Include request/response examples
- Document error codes and messages
- Provide curl examples for each endpoint

**README Updates**:
- Update setup instructions if dependencies added
- Document new environment variables
- Add usage examples for new features
- Update architecture diagrams if structure changed

### 5. Database Optimization
**Query Optimization**:
```sql
-- BEFORE: Slow query (no index on industry)
EXPLAIN ANALYZE
SELECT * FROM agents WHERE industry = 'marketing';

-- AFTER: Add index
CREATE INDEX idx_agents_industry ON agents(industry);

-- Composite index for common filter combination
CREATE INDEX idx_agents_industry_rating ON agents(industry, rating DESC);

-- Partial index for active agents only
CREATE INDEX idx_agents_active ON agents(status) WHERE status = 'active';
```

**Query Plan Analysis**:
```python
# Enable query logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Analyze slow queries
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.1:  # Log queries > 100ms
        logger.warning(f"Slow query ({total:.2f}s): {statement}")
```

---

## 🎯 SUCCESS METRICS

### Data Quality
- 100% completeness for required fields
- < 0.1% data validation errors
- Zero data loss in ETL pipelines
- < 5 min data freshness for real-time data

### Code Quality
- 87%+ test coverage (up from 85%)
- < 5 cyclomatic complexity average
- Zero TODO comments in main branch
- 100% type hint coverage

### Performance
- < 50ms P95 database query time
- < 100ms P95 API endpoint time
- < 1% cache miss rate
- Zero N+1 query problems

### Documentation
- 100% public API documented
- 100% functions have docstrings
- README up to date
- Architecture diagrams current

---

**See also**: [Testing Agent Enhanced](testing_agent_enhanced_capabilities.md) for Security + Performance testing
