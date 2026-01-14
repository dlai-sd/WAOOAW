-- Initialize WAOOAW Plant Development Database
-- This script runs automatically when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create test database
SELECT 'CREATE DATABASE waooaw_plant_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'waooaw_plant_test')\gexec

-- Connect to test database and enable extensions
\c waooaw_plant_test
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Switch back to main database
\c waooaw_plant_dev

-- Display installed extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'uuid-ossp');

-- Display database info
SELECT 
    current_database() as database_name,
    current_user as user_name,
    version() as postgres_version;
