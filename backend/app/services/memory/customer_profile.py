"""
Customer Profile Manager - PostgreSQL-based long-term memory.

Stores enriched customer profiles for personalized agent responses.

Epic: 5.1 Agent Memory & Context
Story: 5.1.2 Customer Profiles (13 points)
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
import json
import uuid

from app.models.customer_profile import CustomerProfile, ProfileEnrichmentLog


class ProfileEnricher:
    """
    LLM-powered profile enrichment.
    
    Extracts structured information from unstructured interaction data.
    Uses GPT-4o-mini for cost-effectiveness ($0.15/1M input tokens).
    """
    
    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: OpenAI or Anthropic client (optional for testing)
        """
        self.llm = llm_client
        self.model = "gpt-4o-mini"
    
    async def enrich_from_signup(self, signup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract profile information from signup form.
        
        Args:
            signup_data: Raw signup form data
            
        Returns:
            Enriched profile fields
        """
        # Direct extraction (no LLM needed for structured signup data)
        enriched = {
            "industry": signup_data.get("industry"),
            "company_name": signup_data.get("company"),
            "company_size": signup_data.get("company_size"),
            "role": signup_data.get("job_title"),
            "timezone": signup_data.get("timezone"),
            "preferences": {
                "email_notifications": signup_data.get("email_opt_in", True),
                "language": signup_data.get("language", "en"),
            }
        }
        
        return {k: v for k, v in enriched.items() if v is not None}
    
    async def enrich_from_interactions(
        self,
        interactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract profile insights from conversation history.
        
        Uses LLM to identify:
        - Goals and objectives
        - Pain points
        - Communication style
        - Behavioral patterns
        
        Args:
            interactions: List of interaction dicts with task_input, agent_output
            
        Returns:
            Enriched profile fields
        """
        if not interactions:
            return {}
        
        # If no LLM, use fallback
        if not self.llm:
            return self._fallback_extraction(interactions)
        
        # Build context from interactions
        context = self._build_interaction_context(interactions)
        
        prompt = f"""Analyze these customer interactions and extract profile insights.

INTERACTIONS:
{context}

Extract the following in JSON format:
1. goals: What is the customer trying to achieve? (1 sentence)
2. pain_points: What challenges do they face? (1 sentence)
3. communication_style: 'formal', 'casual', or 'technical'
4. preferred_task_types: List of task types they request most (max 3)

Return ONLY valid JSON with these keys.
"""
        
        try:
            # Call LLM
            response = await self._call_llm(prompt)
            extracted = json.loads(response)
            return extracted
            
        except Exception as e:
            print(f"Enrichment failed: {e}")
            # Fallback on error
            return self._fallback_extraction(interactions)
    
    def _build_interaction_context(self, interactions: List[Dict]) -> str:
        """Format interactions for LLM context."""
        lines = []
        for i, interaction in enumerate(interactions[:5], 1):  # Last 5
            lines.append(
                f"{i}. Task: {interaction.get('task_input', '')}\n"
                f"   Response: {interaction.get('agent_output', '')[:200]}..."
            )
        return "\n\n".join(lines)
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API (OpenAI or Anthropic)."""
        # TODO: Implement actual LLM call
        # For now, return mock response
        return '{"goals": "Improve marketing efficiency", "pain_points": "Limited resources", "communication_style": "casual", "preferred_task_types": ["social_media", "email_campaigns"]}'
    
    def _fallback_extraction(self, interactions: List[Dict]) -> Dict[str, Any]:
        """Simple rule-based extraction when LLM unavailable."""
        task_types = [i.get("task_type", "unknown") for i in interactions]
        task_type_counts = {}
        for t in task_types:
            task_type_counts[t] = task_type_counts.get(t, 0) + 1
        
        top_tasks = sorted(task_type_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "preferred_task_types": [t[0] for t in top_tasks],
            "communication_style": "casual",  # Default
        }


class CustomerProfileManager:
    """
    Manages long-term customer profiles in PostgreSQL.
    
    Responsibilities:
    - CRUD operations for profiles
    - Profile enrichment coordination
    - Usage pattern tracking
    - 360° customer view
    """
    
    def __init__(self, db_session: AsyncSession, enricher: Optional[ProfileEnricher] = None):
        self.db = db_session
        self.enricher = enricher or ProfileEnricher()
    
    async def get_profile(self, customer_id: str) -> Optional[CustomerProfile]:
        """
        Get customer profile by customer_id.
        
        Args:
            customer_id: UUID string of customer
            
        Returns:
            CustomerProfile or None if not found
        """
        stmt = select(CustomerProfile).where(CustomerProfile.customer_id == uuid.UUID(customer_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_or_create_profile(self, customer_id: str) -> CustomerProfile:
        """Get existing profile or create new one."""
        profile = await self.get_profile(customer_id)
        if not profile:
            profile = await self.create_profile(customer_id)
        return profile
    
    async def create_profile(
        self,
        customer_id: str,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> CustomerProfile:
        """
        Create new customer profile.
        
        Args:
            customer_id: UUID string of customer
            initial_data: Optional initial profile data (e.g., from signup)
            
        Returns:
            Created CustomerProfile
        """
        profile = CustomerProfile(
            customer_id=uuid.UUID(customer_id),
            **(initial_data or {})
        )
        
        self.db.add(profile)
        
        try:
            await self.db.commit()
            await self.db.refresh(profile)
            return profile
        except IntegrityError:
            await self.db.rollback()
            # Profile already exists, fetch it
            return await self.get_profile(customer_id)
    
    async def update_profile(
        self,
        customer_id: str,
        data: Dict[str, Any]
    ) -> CustomerProfile:
        """
        Update existing profile with new data.
        
        Args:
            customer_id: UUID string of customer
            data: Fields to update
            
        Returns:
            Updated CustomerProfile
        """
        stmt = (
            update(CustomerProfile)
            .where(CustomerProfile.customer_id == uuid.UUID(customer_id))
            .values(**data, updated_at=datetime.utcnow())
            .returning(CustomerProfile)
        )
        
        result = await self.db.execute(stmt)
        await self.db.commit()
        
        profile = result.scalar_one()
        await self.db.refresh(profile)
        return profile
    
    async def enrich_from_signup(
        self,
        customer_id: str,
        signup_data: Dict[str, Any]
    ) -> CustomerProfile:
        """
        Enrich profile from signup form data.
        
        Args:
            customer_id: UUID string of customer
            signup_data: Raw signup form data
            
        Returns:
            Enriched CustomerProfile
        """
        # Extract structured fields
        enriched_data = await self.enricher.enrich_from_signup(signup_data)
        
        # Get or create profile
        profile = await self.get_or_create_profile(customer_id)
        
        # Update with enriched data
        profile = await self.update_profile(customer_id, enriched_data)
        
        # Log enrichment
        await self._log_enrichment(
            profile.id,
            source="signup",
            source_data=signup_data,
            extracted_fields=enriched_data,
            status="success"
        )
        
        return profile
    
    async def enrich_from_interactions(
        self,
        customer_id: str,
        interactions: List[Dict[str, Any]]
    ) -> CustomerProfile:
        """
        Enrich profile from interaction history.
        
        Uses LLM to extract goals, pain points, communication style.
        Should be called after first 3 interactions.
        
        Args:
            customer_id: UUID string of customer
            interactions: List of interaction dicts
            
        Returns:
            Enriched CustomerProfile
        """
        profile = await self.get_or_create_profile(customer_id)
        
        # Extract insights
        enriched_data = await self.enricher.enrich_from_interactions(interactions)
        
        if enriched_data:
            # Merge with existing data (don't overwrite)
            update_data = {}
            for key, value in enriched_data.items():
                if key == "preferred_task_types" and value:
                    # Merge with existing preferred tasks
                    existing = profile.frequent_task_types or []
                    update_data["frequent_task_types"] = list(set(existing + value))
                elif not getattr(profile, key, None):
                    # Only update if field is empty
                    update_data[key] = value
            
            if update_data:
                update_data["enrichment_status"] = "enriched"
                update_data["last_enrichment_at"] = datetime.utcnow()
                profile = await self.update_profile(customer_id, update_data)
                
                # Log enrichment
                await self._log_enrichment(
                    profile.id,
                    source="interaction",
                    source_data={"interaction_count": len(interactions)},
                    extracted_fields=enriched_data,
                    status="success"
                )
        
        return profile
    
    async def update_usage_patterns(
        self,
        customer_id: str,
        agent_id: str,
        task_type: str
    ) -> None:
        """
        Update usage patterns based on new interaction.
        
        Tracks:
        - Preferred agents
        - Frequent task types
        - Usage time patterns
        
        Args:
            customer_id: UUID string of customer
            agent_id: Agent used
            task_type: Type of task
        """
        profile = await self.get_or_create_profile(customer_id)
        
        # Update preferred agents
        preferred = profile.preferred_agents or []
        if agent_id not in preferred:
            preferred.append(agent_id)
        elif len(preferred) > 1:
            # Move to front (most recent)
            preferred.remove(agent_id)
            preferred.insert(0, agent_id)
        
        # Keep only top 5
        preferred = preferred[:5]
        
        # Update frequent task types
        tasks = profile.frequent_task_types or []
        if task_type not in tasks:
            tasks.append(task_type)
        
        # Update usage patterns (time of day, day of week)
        now = datetime.utcnow()
        patterns = profile.usage_patterns or {}
        hour = now.hour
        
        hour_key = f"hour_{hour}"
        patterns[hour_key] = patterns.get(hour_key, 0) + 1
        
        # Update profile
        await self.update_profile(
            customer_id,
            {
                "preferred_agents": preferred,
                "frequent_task_types": tasks,
                "usage_patterns": patterns,
            }
        )
    
    async def get_360_view(self, customer_id: str) -> Dict[str, Any]:
        """
        Get complete 360° view of customer.
        
        Combines profile data with computed insights.
        
        Returns:
            Dict with: profile, insights, recommendations
        """
        profile = await self.get_profile(customer_id)
        
        if not profile:
            return {"error": "Profile not found"}
        
        # Compute insights
        insights = {
            "total_interactions": sum(profile.usage_patterns.values()) if profile.usage_patterns else 0,
            "most_active_hour": self._get_most_active_hour(profile.usage_patterns or {}),
            "primary_agent": profile.preferred_agents[0] if profile.preferred_agents else None,
            "top_task_type": profile.frequent_task_types[0] if profile.frequent_task_types else None,
            "enrichment_complete": profile.enrichment_status == "enriched",
        }
        
        return {
            "profile": profile.to_dict(),
            "insights": insights,
            "recommendations": self._generate_recommendations(profile, insights)
        }
    
    def _get_most_active_hour(self, usage_patterns: Dict) -> Optional[int]:
        """Find hour with most activity."""
        if not usage_patterns:
            return None
        
        hour_counts = [(k.replace("hour_", ""), v) for k, v in usage_patterns.items() if k.startswith("hour_")]
        if not hour_counts:
            return None
        
        most_active = max(hour_counts, key=lambda x: x[1])
        return int(most_active[0])
    
    def _generate_recommendations(self, profile: CustomerProfile, insights: Dict) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []
        
        if insights["total_interactions"] < 5:
            recommendations.append("Complete 5 more tasks to unlock advanced features")
        
        if not profile.goals:
            recommendations.append("Share your goals for more personalized recommendations")
        
        if profile.enrichment_status != "enriched":
            recommendations.append("Profile enrichment in progress - better suggestions coming soon")
        
        return recommendations
    
    async def _log_enrichment(
        self,
        profile_id: uuid.UUID,
        source: str,
        source_data: Dict,
        extracted_fields: Dict,
        status: str,
        llm_model: Optional[str] = None,
        llm_tokens: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        """Log profile enrichment operation."""
        log = ProfileEnrichmentLog(
            profile_id=profile_id,
            source=source,
            source_data=source_data,
            extracted_fields=extracted_fields,
            status=status,
            llm_model=llm_model,
            llm_tokens=llm_tokens,
            error_message=error_message
        )
        
        self.db.add(log)
        await self.db.commit()
