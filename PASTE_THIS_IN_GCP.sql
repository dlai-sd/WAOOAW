-- ============================================================================
-- Manual Demo Customer Seed Script (One-Time Execution)
-- ============================================================================
-- Purpose: Create demo@waooaw.com customer for DB Updates authentication
-- Database: plant (plant-sql-demo instance)
-- Environment: demo
-- 
-- NOTE: This is now automated via migration 014_seed_demo_customer.py
--       Only run this manually if migration hasn't been applied yet.
-- ============================================================================

DO $$
DECLARE
    existing_customer_id UUID;
    new_base_id UUID;
BEGIN
    -- Check if customer already exists
    SELECT id INTO existing_customer_id 
    FROM customer_entity 
    WHERE email = 'demo@waooaw.com';
    
    IF existing_customer_id IS NULL THEN
        -- Generate new UUID
        new_base_id := gen_random_uuid();
        
        -- Create base_entity (let defaults handle JSON columns)
        INSERT INTO base_entity (
            id, entity_type, version_hash, status, governance_agent_id, tags
        )
        VALUES (
            new_base_id, 'customer', 'seed_v1', 'active', 'genesis', 
            ARRAY['demo', 'testing']
        );
        
        -- Create customer_entity
        INSERT INTO customer_entity (
            id, email, phone, full_name, business_name, business_industry,
            business_address, preferred_contact_method, consent
        )
        VALUES (
            new_base_id, 'demo@waooaw.com', '+919999999999', 'Demo User', 
            'WAOOAW Demo Business', 'Technology', 'Mumbai, India', 'email', true
        );
        
        RAISE NOTICE 'Created new customer: %', new_base_id;
    ELSE
        RAISE NOTICE 'Customer already exists with id: %', existing_customer_id;
    END IF;
END $$;

-- Verify it worked
SELECT 
    c.id, 
    c.email, 
    c.full_name, 
    c.business_name, 
    be.created_at
FROM customer_entity c
JOIN base_entity be ON c.id = be.id
WHERE c.email = 'demo@waooaw.com';

-- ============================================================================
-- Expected Output: 1 row with demo@waooaw.com details
-- ============================================================================
