"""Seed script for agent_type_definitions table.

Seeds Marketing and Trading agent type definitions for dev/test environments.
Run via: docker compose exec plant-backend python database/seeds/agent_type_definitions_seed.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.v1.agent_types_simple import _marketing_definition, _trading_definition
from core.database import _connector
from repositories.agent_type_repository import AgentTypeDefinitionRepository


async def seed_agent_type_definitions():
    """Seed agent_type_definitions table with Marketing and Trading definitions."""
    
    print("Starting agent_type_definitions seed...")
    
    # Get async session
    session = await _connector.get_session()
    async with session:
        repo = AgentTypeDefinitionRepository(session)
        
        # Get definitions from in-memory implementation
        marketing_def = _marketing_definition()
        trading_def = _trading_definition()
        
        definitions = [marketing_def, trading_def]
        
        for definition in definitions:
            agent_type_id = definition.agent_type_id
            version = definition.version
            
            # Check if already exists
            existing = await repo.get_by_id_and_version(agent_type_id, version)
            
            if existing:
                print(f"  ⏭  {agent_type_id} v{version} already exists, skipping")
                continue
            
            # Create new definition
            payload = definition.model_dump()
            await repo.create(
                agent_type_id=agent_type_id,
                version=version,
                payload=payload,
            )
            print(f"  ✓ Created {agent_type_id} v{version}")
        
        await session.commit()
        print("✓ Agent type definitions seed complete")


if __name__ == "__main__":
    asyncio.run(seed_agent_type_definitions())
