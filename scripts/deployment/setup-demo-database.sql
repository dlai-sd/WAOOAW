-- WAOOAW Demo Database Schema Setup
-- Run this script in Cloud SQL after connecting with:
-- gcloud sql connect waooaw-db --user=postgres

-- Create demo schema
CREATE SCHEMA IF NOT EXISTS demo;
SET search_path TO demo;

-- Create agents table
CREATE TABLE IF NOT EXISTS agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(50) NOT NULL,
    specialty VARCHAR(255),
    rating DECIMAL(3,1) CHECK (rating >= 0 AND rating <= 5),
    status VARCHAR(20) DEFAULT 'offline',
    price VARCHAR(50),
    avatar VARCHAR(10),
    activity VARCHAR(255),
    retention VARCHAR(10),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(20) DEFAULT 'viewer',
    google_id VARCHAR(255) UNIQUE,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Create trials table
CREATE TABLE IF NOT EXISTS trials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    agent_id INTEGER REFERENCES agents(id),
    status VARCHAR(20) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE
);

-- Insert seed data for demo
INSERT INTO agents (name, industry, specialty, rating, status, price, avatar, activity, retention, description) VALUES
('Content Marketing Agent', 'marketing', 'Healthcare', 4.9, 'available', '₹12,000/month', 'CM', 'Posted 23 times today', '98%', 'Specialized in healthcare content creation with deep industry knowledge'),
('Math Tutor Agent', 'education', 'JEE/NEET', 4.8, 'working', '₹8,000/month', 'MT', '5 sessions today', '95%', 'Expert math tutor for competitive exam preparation'),
('SDR Agent', 'sales', 'B2B SaaS', 5.0, 'available', '₹15,000/month', 'SDR', '12 leads generated', '99%', 'B2B sales development representative with proven track record'),
('Social Media Agent', 'marketing', 'B2B', 4.7, 'available', '₹10,000/month', 'SM', 'Posted 15 times today', '96%', 'Social media management for B2B companies'),
('Science Tutor Agent', 'education', 'CBSE', 4.9, 'available', '₹8,000/month', 'ST', '8 sessions today', '97%', 'CBSE curriculum expert for grades 6-12'),
('Account Executive Agent', 'sales', 'Enterprise', 4.8, 'working', '₹18,000/month', 'AE', '5 deals closing', '98%', 'Enterprise sales specialist'),
('SEO Agent', 'marketing', 'E-commerce', 4.6, 'available', '₹11,000/month', 'SEO', '20 keywords ranked', '94%', 'E-commerce SEO optimization expert');

-- Create indexes for performance
CREATE INDEX idx_agents_industry ON agents(industry);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_trials_user_id ON trials(user_id);
CREATE INDEX idx_trials_agent_id ON trials(agent_id);

-- Verify data
SELECT COUNT(*) as agent_count FROM agents;
SELECT name, industry, rating, status FROM agents ORDER BY rating DESC;

\echo 'Demo schema setup complete!'
