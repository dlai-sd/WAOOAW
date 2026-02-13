-- Seed demo customer for DB Updates page access
-- Run this against demo database: plant-sql-demo

-- Insert base_entity record for customer
INSERT INTO base_entity (
    id, entity_type, version_hash, status, governance_agent_id, 
    tags, created_at, updated_at
)
VALUES (
    gen_random_uuid(),
    'customer',
    'seed_v1',
    'active',
    'genesis',
    ARRAY['demo', 'testing'],
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT DO NOTHING
RETURNING id;

-- Insert customer_entity record (use the ID from above)
-- Note: You'll need to replace the UUID with the one generated above
INSERT INTO customer_entity (
    id,
    email,
    phone,
    full_name,
    business_name,
    business_industry,
    business_address,
    preferred_contact_method,
    consent
)
SELECT 
    be.id,
    'demo@waooaw.com',
    '+919999999999',
    'Demo User',
    'WAOOAW Demo Business',
    'Technology',
    'Mumbai, India',
    'email',
    true
FROM base_entity be
WHERE be.entity_type = 'customer'
  AND be.tags && ARRAY['demo']
  AND NOT EXISTS (
      SELECT 1 FROM customer_entity WHERE email = 'demo@waooaw.com'
  )
LIMIT 1;

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
