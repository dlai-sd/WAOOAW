"""Quick test to verify DB-backed agent type API reads seeded data."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database import _connector
from services.agent_type_service import AgentTypeDefinitionService


async def test_list_definitions():
    """Test listing definitions from DB."""
    session = await _connector.get_session()
    async with session:
        service = AgentTypeDefinitionService(session)
        defs = await service.list_definitions()
        
        print(f"Found {len(defs)} definitions:")
        for d in defs:
            print(f"  - {d.agent_type_id} v{d.version}")
            print(f"    Config fields: {len(d.config_schema.fields)}")
            print(f"    Goal templates: {len(d.goal_templates)}")


if __name__ == "__main__":
    asyncio.run(test_list_definitions())
