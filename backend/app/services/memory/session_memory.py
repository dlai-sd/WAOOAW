"""
Session Memory Manager - Redis-based short-term memory.

Stores last 10 interactions per customer with TTL-based expiration.
Enables agents to reference previous conversations for context-aware responses.

Epic: 5.1 Agent Memory & Context
Story: 5.1.1 Session Memory (13 points)
"""

from typing import List, Dict, Optional, Any
import json
from datetime import datetime, timedelta
from redis.asyncio import Redis
from pydantic import BaseModel, Field


class Interaction(BaseModel):
    """Single interaction record."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    task_type: str
    task_input: str
    agent_output: str
    rating: Optional[int] = None  # 1-5 stars
    duration_ms: Optional[int] = None
    agent_id: str
    success: bool = True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SessionMemoryManager:
    """
    Manages short-term session memory in Redis.
    
    Storage Strategy:
    - Key: session:{customer_id}
    - Type: Redis List (FIFO)
    - Size: Last 10 interactions
    - TTL: 7 days (trial), 30 days (paid)
    
    Performance:
    - Store: O(1) - Redis LPUSH + LTRIM
    - Retrieve: O(n) where n=10 max - Redis LRANGE
    - Target latency: <50ms
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.max_interactions = 10
        self.ttl_trial = 604800  # 7 days in seconds
        self.ttl_paid = 2592000   # 30 days in seconds
        
    def _get_key(self, customer_id: str) -> str:
        """Generate Redis key for customer session."""
        return f"session:{customer_id}"
    
    async def store_interaction(
        self,
        customer_id: str,
        interaction: Interaction,
        is_trial: bool = True
    ) -> None:
        """
        Store interaction in session memory.
        
        Args:
            customer_id: UUID of customer
            interaction: Interaction object to store
            is_trial: Whether customer is on trial (affects TTL)
            
        Raises:
            redis.ConnectionError: If Redis is unavailable
        """
        key = self._get_key(customer_id)
        
        # Serialize interaction
        data = interaction.model_dump_json()
        
        # Store in Redis list (prepend to head)
        await self.redis.lpush(key, data)
        
        # Keep only last N interactions
        await self.redis.ltrim(key, 0, self.max_interactions - 1)
        
        # Set TTL based on customer type
        ttl = self.ttl_trial if is_trial else self.ttl_paid
        await self.redis.expire(key, ttl)
    
    async def get_session_context(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Interaction]:
        """
        Retrieve session context for customer.
        
        Args:
            customer_id: UUID of customer
            limit: Maximum interactions to retrieve (default: 10)
            
        Returns:
            List of Interaction objects, newest first
        """
        key = self._get_key(customer_id)
        
        # Get all interactions (or up to limit)
        raw_data = await self.redis.lrange(key, 0, limit - 1)
        
        # Deserialize
        interactions = []
        for item in raw_data:
            try:
                data = json.loads(item)
                interactions.append(Interaction(**data))
            except (json.JSONDecodeError, ValueError) as e:
                # Log error but continue (data corruption shouldn't break system)
                print(f"Failed to parse interaction: {e}")
                continue
        
        return interactions
    
    async def get_last_n_context(
        self,
        customer_id: str,
        n: int = 3
    ) -> str:
        """
        Get formatted context string of last N interactions.
        
        This is what gets injected into agent prompts.
        
        Args:
            customer_id: UUID of customer
            n: Number of recent interactions (default: 3)
            
        Returns:
            Formatted string for prompt injection
        """
        interactions = await self.get_session_context(customer_id, limit=n)
        
        if not interactions:
            return "No previous interactions."
        
        context_lines = []
        for i, interaction in enumerate(reversed(interactions), 1):
            context_lines.append(
                f"{i}. [{interaction.agent_id}] {interaction.task_type}\n"
                f"   Task: {interaction.task_input[:100]}...\n"
                f"   Response: {interaction.agent_output[:100]}...\n"
                f"   {'✅' if interaction.success else '❌'} "
                f"{'⭐' * (interaction.rating or 0)}"
            )
        
        return "\n\n".join(context_lines)
    
    async def clear_session(self, customer_id: str) -> None:
        """
        Clear session memory for customer.
        
        Use cases:
        - Customer requests data deletion (GDPR)
        - Session expired
        - Fresh start after trial → paid conversion
        """
        key = self._get_key(customer_id)
        await self.redis.delete(key)
    
    async def get_session_stats(self, customer_id: str) -> Dict[str, Any]:
        """
        Get statistics about customer's session.
        
        Returns:
            Dict with: total_interactions, success_rate, avg_rating, ttl_remaining
        """
        key = self._get_key(customer_id)
        
        # Get all interactions
        interactions = await self.get_session_context(customer_id)
        
        if not interactions:
            return {
                "total_interactions": 0,
                "success_rate": 0.0,
                "avg_rating": 0.0,
                "ttl_remaining_seconds": 0
            }
        
        # Calculate stats
        total = len(interactions)
        successful = sum(1 for i in interactions if i.success)
        ratings = [i.rating for i in interactions if i.rating is not None]
        
        # Get TTL
        ttl = await self.redis.ttl(key)
        
        return {
            "total_interactions": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_rating": sum(ratings) / len(ratings) if ratings else 0.0,
            "ttl_remaining_seconds": ttl if ttl > 0 else 0
        }
    
    async def extend_ttl(
        self,
        customer_id: str,
        is_trial: bool = False
    ) -> None:
        """
        Extend TTL for session (e.g., when customer upgrades from trial).
        
        Args:
            customer_id: UUID of customer
            is_trial: New customer type
        """
        key = self._get_key(customer_id)
        ttl = self.ttl_trial if is_trial else self.ttl_paid
        await self.redis.expire(key, ttl)


# Utility function for prompt enhancement
def build_contextualized_prompt(
    base_prompt: str,
    customer_industry: str,
    customer_company: str,
    session_context: str
) -> str:
    """
    Build agent prompt with session context injected.
    
    Args:
        base_prompt: Original agent prompt
        customer_industry: Customer's industry
        customer_company: Customer's company name
        session_context: Formatted session history from get_last_n_context()
        
    Returns:
        Enhanced prompt with context
    """
    return f"""CUSTOMER CONTEXT:
Industry: {customer_industry}
Company: {customer_company}

RECENT INTERACTIONS:
{session_context}

NEW TASK:
{base_prompt}

Instructions:
- Use the context above to provide a personalized, contextually-aware response
- Reference previous interactions if relevant
- Build on what the customer has already learned or received
- Don't ask for information you already have in the context
"""
