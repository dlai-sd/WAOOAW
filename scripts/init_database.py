#!/usr/bin/env python3
"""
Initialize WAOOAW PostgreSQL database with all required tables.
Runs both vision schema (5 tables) and base agent schema (10 tables).
"""

import os
import sys
import psycopg2
from pathlib import Path


def init_database():
    """Initialize database with all schemas"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not set")
        print("   Set it with: export DATABASE_URL='postgresql://...'")
        sys.exit(1)
    
    print("🗄️  Connecting to PostgreSQL...")
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected successfully")
        print("")
        
        # Get script directory
        script_dir = Path(__file__).parent.parent
        
        # Load and execute vision schema (5 tables)
        print("📋 Creating vision schema tables...")
        
        vision_schema_path = script_dir / 'vision' / 'schema.sql'
        if not vision_schema_path.exists():
            print(f"❌ Vision schema not found: {vision_schema_path}")
            sys.exit(1)
        
        with open(vision_schema_path, 'r') as f:
            vision_schema = f.read()
        
        cursor.execute(vision_schema)
        print("✅ Created 5 vision tables: agent_context, agent_decisions, vision_violations, human_escalations, agent_health")
        
        # Load and execute base agent schema (10 tables)
        print("")
        print("📋 Creating base agent schema tables...")
        
        base_schema_path = script_dir / 'waooaw' / 'database' / 'base_agent_schema.sql'
        if not base_schema_path.exists():
            print(f"❌ Base agent schema not found: {base_schema_path}")
            sys.exit(1)
        
        with open(base_schema_path, 'r') as f:
            base_schema = f.read()
        
        cursor.execute(base_schema)
        print("✅ Created 10 base agent tables:")
        print("   - wowvision_memory (agent long-term memory)")
        print("   - conversation_sessions (chat history)")
        print("   - conversation_messages (message log)")
        print("   - knowledge_base (learned patterns)")
        print("   - decision_cache (cost optimization)")
        print("   - wowvision_state (operational state)")
        print("   - agent_handoffs (cross-CoE coordination)")
        print("   - agent_metrics (performance tracking)")
        
        # Initialize default state
        print("")
        print("📋 Initializing default state...")
        
        cursor.execute("""
            INSERT INTO wowvision_state (state_key, state_value)
            VALUES 
                ('current_phase', '{"phase": "phase1-documentation", "started": "2025-12-24"}'),
                ('last_wake_up', '{"timestamp": null, "tasks_completed": 0}'),
                ('pending_escalations', '{"count": 0, "issues": []}'),
                ('learning_queue', '{"items": []}'),
                ('health', '{"status": "healthy", "uptime_hours": 0}')
            ON CONFLICT (state_key) DO NOTHING;
        """)
        
        print("✅ Default state initialized")
        
        # Verify table creation
        print("")
        print("🔍 Verifying tables...")
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("")
        print("🎉 Database initialization complete!")
        print("")
        print("Next steps:")
        print("1. Test connection: python scripts/verify_infrastructure.py")
        print("2. Run WowVision Prime: python waooaw/main.py wake_up")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    init_database()
