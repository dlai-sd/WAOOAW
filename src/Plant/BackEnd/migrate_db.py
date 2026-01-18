"""Run database migrations via Cloud SQL"""
import asyncio
from core.database import _connector, Base
# Import all models to ensure they're registered with Base
from models.base_entity import BaseEntity
from models.skill import Skill
from models.job_role import JobRole
from models.team import Team, Agent, Industry

async def create_tables():
    print("Initializing database connection...")
    await _connector.initialize()
    
    print("Creating tables...")
    async with _connector.engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ All tables created successfully")
    
    # List created tables
    async with _connector.engine.connect() as conn:
        result = await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        ))
        tables = [row[0] for row in result]
        print(f"\nCreated tables ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(create_tables())
