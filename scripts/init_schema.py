#!/usr/bin/env python3
"""
Initialize WAOOAW database schema.

This script creates all required tables for the agent system.
Run once after setting up a new database.
"""

import os
import sys
import psycopg2

def init_schema():
    """Initialize database schema from SQL file"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        return False
    
    print("🗄️  Initializing WAOOAW database schema...")
    print("")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url, connect_timeout=10)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Read schema file
        schema_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'waooaw',
            'database',
            'base_agent_schema.sql'
        )
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        print(f"✅ Loaded schema from {schema_path}")
        
        # Execute schema
        cursor.execute(schema_sql)
        
        print("✅ Schema created successfully")
        
        # Verify tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("")
        print("🎉 Database initialization complete!")
        return True
        
    except Exception as e:
        print(f"❌ Schema initialization failed: {e}")
        return False


if __name__ == '__main__':
    success = init_schema()
    sys.exit(0 if success else 1)
