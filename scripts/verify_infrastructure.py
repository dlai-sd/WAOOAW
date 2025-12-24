#!/usr/bin/env python3
"""
Verify all infrastructure components are working correctly.
Tests: PostgreSQL, Pinecone, and optionally Anthropic (if configured).
"""

import os
import sys


def test_postgresql():
    """Test PostgreSQL connection and tables"""
    print("🗄️  Testing PostgreSQL...")
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False
    
    try:
        import psycopg2
        
        # Try to connect with timeout and IPv4 preference
        # Parse URL to add gssencmode=disable which can help with network issues
        conn_params = database_url
        if '?' in conn_params:
            conn_params += '&gssencmode=disable'
        else:
            conn_params += '?gssencmode=disable'
        
        conn = psycopg2.connect(conn_params, connect_timeout=15)
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connected to PostgreSQL: {version[0][:50]}...")
        
        # Check tables exist
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        table_count = cursor.fetchone()[0]
        print(f"✅ Found {table_count} tables")
        
        # Test insert/select
        cursor.execute("""
            INSERT INTO wowvision_state (state_key, state_value)
            VALUES ('test_verification', '{"test": true}')
            ON CONFLICT (state_key) 
            DO UPDATE SET state_value = EXCLUDED.state_value
            RETURNING state_key;
        """)
        result = cursor.fetchone()
        print(f"✅ Write test successful: {result[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ PostgreSQL test failed: {e}")
        
        # Check if it's a network connectivity issue (IPv6 - should not happen with pooler)
        if "Network is unreachable" in error_msg or "2406:" in error_msg:
            print("   ⚠️  IPv6 connectivity issue detected")
            print("   ⚠️  DATABASE_URL must use Supavisor pooler (pooler.supabase.com)")
            print("   ⚠️  Direct Supabase connections are IPv6-only")
            return False  # Hard failure - pooler should work
        
        return False


def test_pinecone():
    """Test Pinecone connection"""
    print("")
    print("🧠 Testing Pinecone...")
    
    api_key = os.getenv('PINECONE_API_KEY')
    index_host = os.getenv('PINECONE_INDEX_HOST')
    index_name = os.getenv('PINECONE_INDEX_NAME', 'wowvision-memory')
    
    print(f"   API Key present: {bool(api_key)}")
    print(f"   Index Host: {index_host or 'NOT SET'}")
    print(f"   Index Name: {index_name}")
    
    if not api_key:
        print("❌ PINECONE_API_KEY not set")
        return False
    
    if not index_host:
        print("❌ PINECONE_INDEX_HOST not set")
        return False
    
    try:
        from pinecone import Pinecone
        
        pc = Pinecone(api_key=api_key)
        
        # Get index
        index = pc.Index(index_name, host=f"https://{index_host}")
        
        # Test stats
        stats = index.describe_index_stats()
        print(f"✅ Connected to Pinecone index: {index_name}")
        print(f"✅ Vector count: {stats.get('total_vector_count', 0)}")
        print(f"✅ Dimension: {stats.get('dimension', 'N/A')}")
        
        # Test upsert
        test_vector = [0.1] * 1536  # 1536-dimension test vector
        index.upsert(vectors=[{
            'id': 'test-verification',
            'values': test_vector,
            'metadata': {'test': True}
        }])
        print("✅ Write test successful")
        
        # Test query
        results = index.query(
            vector=test_vector,
            top_k=1,
            include_metadata=True
        )
        print(f"✅ Query test successful: found {len(results.get('matches', []))} matches")
        
        return True
        
    except Exception as e:
        print(f"❌ Pinecone test failed: {e}")
        return False


def test_anthropic():
    """Test Anthropic Claude API (optional)"""
    print("")
    print("🤖 Testing Anthropic Claude API...")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("⏸️  ANTHROPIC_API_KEY not set (optional for now)")
        return None  # Not a failure, just not configured yet
    
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test simple completion
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'test successful' and nothing else."}]
        )
        
        response = message.content[0].text
        print(f"✅ Claude responded: {response}")
        print(f"✅ Tokens used: {message.usage.input_tokens + message.usage.output_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ Anthropic test failed: {e}")
        return False


def main():
    """Run all infrastructure tests"""
    print("🔍 WAOOAW Infrastructure Verification")
    print("=" * 60)
    print("")
    
    results = {
        'postgresql': test_postgresql(),
        'pinecone': test_pinecone(),
        'anthropic': test_anthropic()
    }
    
    print("")
    print("=" * 60)
    print("📊 RESULTS:")
    print("")
    
    for component, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏸️  NOT CONFIGURED"
        
        print(f"{component.upper()}: {status}")
    
    print("")
    
    # Overall status
    failures = [k for k, v in results.items() if v is False]
    warnings = [k for k, v in results.items() if v is None]
    
    if failures:
        print(f"❌ {len(failures)} component(s) failed: {', '.join(failures)}")
        sys.exit(1)
    elif warnings:
        print(f"⚠️  Infrastructure ready with warnings")
        print(f"   Components not reachable: {', '.join(warnings)}")
        print(f"   WowVision Prime can run in limited mode")
    elif results['anthropic'] is None:
        print("⚠️  Infrastructure partially ready (Anthropic not configured yet)")
        print("   WowVision Prime will run in limited mode until Claude API key added")
    else:
        print("🎉 All infrastructure components verified!")
    
    print("")
    print("Next steps:")
    if results['anthropic'] is None:
        print("1. Add Anthropic API key when credit card issue resolved")
        print("2. Run verification again: python scripts/verify_infrastructure.py")
        print("3. Test WowVision Prime: python waooaw/main.py wake_up")
    else:
        print("1. Test WowVision Prime: python waooaw/main.py wake_up")
        print("2. Deploy to GitHub Actions: see .github/workflows/wowvision-prime.yml")


if __name__ == '__main__':
    main()
