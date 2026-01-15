"""Create database tables via SQLAlchemy"""
import asyncio
import sys
from core.database import _connector, Base
from models.base_entity import BaseEntity
from models.skill import Skill
from models.job_role import JobRole
from models.team import Team, Agent, Industry

async def main():
    try:
        print("Connecting to database...")
        await _connector.initialize()
        print("✅ Connection successful")
        
        print("Creating tables...")
        async with _connector.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ All tables created successfully")
        
        # List tables
        from sqlalchemy import text
        async with _connector.engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            ))
            tables = [row[0] for row in result]
            print(f"\nCreated {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")
        
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
