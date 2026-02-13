-- Copy this SQL and paste it into pp.demo.waooaw.com/db-updates

WITH new_customer AS (
    INSERT INTO base_entity (
        entity_type, version_hash, status, governance_agent_id, tags, created_at, updated_at
    )
    VALUES (
        'customer', 'seed_v1', 'active', 'genesis', 
        ARRAY['demo', 'testing'], CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    )
    ON CONFLICT DO NOTHING
    RETURNING id
)
INSERT INTO customer_entity (
    id, email, phone, full_name, business_name, business_industry,
    business_address, preferred_contact_method, consent
)
SELECT 
    id, 'demo@waooaw.com', '+919999999999', 'Demo User', 
    'WAOOAW Demo Business', 'Technology', 'Mumbai, India', 'email', true
FROM new_customer
ON CONFLICT (email) DO NOTHING;

-- Verify insertion
SELECT 
    c.id,
    c.email,
    c.full_name,
    c.business_name,
    be.created_at
FROM customer_entity c
JOIN base_entity be ON c.id = be.id
WHERE c.email = 'demo@waooaw.com';
