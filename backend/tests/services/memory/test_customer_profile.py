"""
Unit tests for Customer Profile Manager.

Tests cover:
- Profile CRUD operations
- Signup enrichment
- Interaction-based enrichment
- Usage pattern tracking
- 360° view generation
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.memory.customer_profile import (
    CustomerProfileManager,
    ProfileEnricher
)
from app.models.customer_profile import CustomerProfile


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_enricher():
    """Mock ProfileEnricher."""
    enricher = AsyncMock(spec=ProfileEnricher)
    enricher.enrich_from_signup = AsyncMock(return_value={
        "industry": "Healthcare",
        "company_name": "HealthCorp",
        "company_size": "51-200"
    })
    enricher.enrich_from_interactions = AsyncMock(return_value={
        "goals": "Improve patient engagement",
        "communication_style": "formal",
        "preferred_task_types": ["email_campaigns", "social_posts"]
    })
    return enricher


@pytest.fixture
def sample_profile():
    """Sample customer profile."""
    return CustomerProfile(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        industry="Healthcare",
        company_name="HealthCorp",
        company_size="51-200",
        preferences={},
        goals=None,
        preferred_agents=[],
        frequent_task_types=[],
        usage_patterns={},
        enrichment_status="pending"
    )


class TestProfileEnricher:
    """Test suite for ProfileEnricher."""
    
    @pytest.mark.asyncio
    async def test_enrich_from_signup_direct_extraction(self):
        """Test direct extraction from structured signup data."""
        enricher = ProfileEnricher(llm_client=None)
        
        signup_data = {
            "industry": "Healthcare",
            "company": "HealthCorp Inc",
            "company_size": "51-200",
            "job_title": "Marketing Director",
            "timezone": "America/New_York",
            "email_opt_in": True,
            "language": "en"
        }
        
        result = await enricher.enrich_from_signup(signup_data)
        
        assert result["industry"] == "Healthcare"
        assert result["company_name"] == "HealthCorp Inc"
        assert result["company_size"] == "51-200"
        assert result["role"] == "Marketing Director"
        assert result["preferences"]["email_notifications"] is True
    
    @pytest.mark.asyncio
    async def test_enrich_from_signup_partial_data(self):
        """Test enrichment when signup has partial data."""
        enricher = ProfileEnricher(llm_client=None)
        
        signup_data = {
            "industry": "Education",
            # Missing other fields
        }
        
        result = await enricher.enrich_from_signup(signup_data)
        
        assert result["industry"] == "Education"
        assert "company_name" not in result  # Not present
    
    @pytest.mark.asyncio
    async def test_enrich_from_interactions_no_llm(self):
        """Test fallback extraction when LLM unavailable."""
        enricher = ProfileEnricher(llm_client=None)
        
        interactions = [
            {"task_type": "social_post", "task_input": "Create post", "agent_output": "Here's a post..."},
            {"task_type": "social_post", "task_input": "Another post", "agent_output": "Another..."},
            {"task_type": "email_campaign", "task_input": "Email", "agent_output": "Email content..."},
        ]
        
        result = await enricher.enrich_from_interactions(interactions)
        
        assert "preferred_task_types" in result
        assert "social_post" in result["preferred_task_types"]
        assert result["communication_style"] == "casual"  # Default
    
    @pytest.mark.asyncio
    async def test_enrich_from_interactions_empty(self):
        """Test enrichment with no interactions."""
        enricher = ProfileEnricher(llm_client=None)
        
        result = await enricher.enrich_from_interactions([])
        
        assert result == {}


class TestCustomerProfileManager:
    """Test suite for CustomerProfileManager."""
    
    @pytest.mark.asyncio
    async def test_create_profile(self, mock_db_session, mock_enricher):
        """Test creating new profile."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        customer_id = str(uuid.uuid4())
        
        # Mock successful creation
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        initial_data = {"industry": "Healthcare"}
        profile = await manager.create_profile(customer_id, initial_data)
        
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_get_profile(self, mock_db_session, mock_enricher, sample_profile):
        """Test retrieving existing profile."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        customer_id = str(sample_profile.customer_id)
        
        # Mock database return
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_profile
        mock_db_session.execute.return_value = mock_result
        
        result = await manager.get_profile(customer_id)
        
        assert result == sample_profile
        assert mock_db_session.execute.called
    
    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, mock_db_session, mock_enricher):
        """Test retrieving non-existent profile."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        customer_id = str(uuid.uuid4())
        
        # Mock no results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await manager.get_profile(customer_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_profile(self, mock_db_session, mock_enricher, sample_profile):
        """Test updating profile."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        customer_id = str(sample_profile.customer_id)
        
        # Mock update return
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = sample_profile
        mock_db_session.execute.return_value = mock_result
        
        update_data = {"goals": "Improve efficiency"}
        result = await manager.update_profile(customer_id, update_data)
        
        assert mock_db_session.execute.called
        assert mock_db_session.commit.called
        assert mock_db_session.refresh.called
    
    @pytest.mark.asyncio
    async def test_enrich_from_signup(self, mock_db_session, mock_enricher, sample_profile):
        """Test profile enrichment from signup."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        customer_id = str(sample_profile.customer_id)
        
        # Mock get_or_create
        manager.get_or_create_profile = AsyncMock(return_value=sample_profile)
        manager.update_profile = AsyncMock(return_value=sample_profile)
        manager._log_enrichment = AsyncMock()
        
        signup_data = {
            "industry": "Healthcare",
            "company": "HealthCorp"
        }
        
        result = await manager.enrich_from_signup(customer_id, signup_data)
        
        assert mock_enricher.enrich_from_signup.called
        assert manager.update_profile.called
        assert manager._log_enrichment.called
    
    @pytest.mark.asyncio
    async def test_enrich_from_interactions(self, mock_db_session, mock_enricher, sample_profile):
        """Test profile enrichment from interactions."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        customer_id = str(sample_profile.customer_id)
        
        # Mock methods
        manager.get_or_create_profile = AsyncMock(return_value=sample_profile)
        manager.update_profile = AsyncMock(return_value=sample_profile)
        manager._log_enrichment = AsyncMock()
        
        interactions = [
            {"task_input": "Create campaign", "agent_output": "Campaign created..."},
            {"task_input": "Write email", "agent_output": "Email drafted..."},
        ]
        
        result = await manager.enrich_from_interactions(customer_id, interactions)
        
        assert mock_enricher.enrich_from_interactions.called
        assert manager.update_profile.called
    
    @pytest.mark.asyncio
    async def test_update_usage_patterns(self, mock_db_session, mock_enricher, sample_profile):
        """Test usage pattern tracking."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        customer_id = str(sample_profile.customer_id)
        
        manager.get_or_create_profile = AsyncMock(return_value=sample_profile)
        manager.update_profile = AsyncMock(return_value=sample_profile)
        
        await manager.update_usage_patterns(
            customer_id,
            agent_id="agent_marketing_001",
            task_type="social_post"
        )
        
        # Verify update was called
        assert manager.update_profile.called
        update_call = manager.update_profile.call_args
        assert "preferred_agents" in update_call[0][1]
        assert "frequent_task_types" in update_call[0][1]
    
    @pytest.mark.asyncio
    async def test_get_360_view(self, mock_db_session, mock_enricher, sample_profile):
        """Test 360° customer view."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        customer_id = str(sample_profile.customer_id)
        
        # Set up profile with data
        sample_profile.usage_patterns = {"hour_9": 5, "hour_14": 3}
        sample_profile.preferred_agents = ["agent_001", "agent_002"]
        sample_profile.frequent_task_types = ["email", "social"]
        
        manager.get_profile = AsyncMock(return_value=sample_profile)
        
        result = await manager.get_360_view(customer_id)
        
        assert "profile" in result
        assert "insights" in result
        assert "recommendations" in result
        assert result["insights"]["most_active_hour"] == 9
        assert result["insights"]["primary_agent"] == "agent_001"
    
    @pytest.mark.asyncio
    async def test_get_360_view_not_found(self, mock_db_session, mock_enricher):
        """Test 360° view for non-existent profile."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        customer_id = str(uuid.uuid4())
        
        manager.get_profile = AsyncMock(return_value=None)
        
        result = await manager.get_360_view(customer_id)
        
        assert "error" in result
    
    def test_get_most_active_hour(self, mock_db_session, mock_enricher):
        """Test finding most active hour."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        
        usage_patterns = {
            "hour_9": 10,
            "hour_14": 5,
            "hour_18": 15
        }
        
        result = manager._get_most_active_hour(usage_patterns)
        
        assert result == 18  # Highest count
    
    def test_get_most_active_hour_empty(self, mock_db_session, mock_enricher):
        """Test most active hour with no data."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        
        result = manager._get_most_active_hour({})
        
        assert result is None
    
    def test_generate_recommendations_new_user(self, mock_db_session, mock_enricher, sample_profile):
        """Test recommendations for new user."""
        manager = CustomerProfileManager(mock_db_session, mock_enricher)
        
        insights = {
            "total_interactions": 2,
            "enrichment_complete": False
        }
        
        recommendations = manager._generate_recommendations(sample_profile, insights)
        
        assert len(recommendations) > 0
        assert any("5 more tasks" in r for r in recommendations)
        assert any("Profile enrichment in progress" in r for r in recommendations)


class TestCustomerProfileModel:
    """Test CustomerProfile model."""
    
    def test_profile_to_dict(self, sample_profile):
        """Test profile serialization."""
        result = sample_profile.to_dict()
        
        assert "id" in result
        assert "customer_id" in result
        assert "industry" in result
        assert result["industry"] == "Healthcare"
    
    def test_profile_repr(self, sample_profile):
        """Test profile string representation."""
        repr_str = repr(sample_profile)
        
        assert "CustomerProfile" in repr_str
        assert "Healthcare" in repr_str


# Integration test markers
@pytest.mark.integration
class TestCustomerProfileIntegration:
    """
    Integration tests requiring real database.
    Run with: pytest -m integration
    """
    
    @pytest.mark.asyncio
    async def test_real_database_roundtrip(self):
        """Test actual database operations."""
        pytest.skip("Integration test - requires PostgreSQL")
