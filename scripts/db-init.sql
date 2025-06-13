# scripts/db-init.sql - Database initialization for development
-- Database initialization script for development
CREATE DATABASE IF NOT EXISTS terraform_agent_dev;

-- Create tables for storing metadata
CREATE TABLE IF NOT EXISTS terraform_generations (
    id SERIAL PRIMARY KEY,
    instruction TEXT NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    branch_name VARCHAR(255),
    pr_url TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS github_operations (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(100) NOT NULL,
    repository VARCHAR(255) NOT NULL,
    branch_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    response_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS template_usage (
    id SERIAL PRIMARY KEY,
    template_name VARCHAR(100) NOT NULL,
    usage_count INTEGER DEFAULT 1,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_terraform_generations_status ON terraform_generations(status);
CREATE INDEX IF NOT EXISTS idx_terraform_generations_created_at ON terraform_generations(created_at);
CREATE INDEX IF NOT EXISTS idx_github_operations_status ON github_operations(status);
CREATE INDEX IF NOT EXISTS idx_template_usage_name ON template_usage(template_name);

-- Insert some sample data for development
INSERT INTO template_usage (template_name, usage_count, last_used) VALUES
    ('gcp_vm', 0, CURRENT_TIMESTAMP),
    ('gcp_storage', 0, CURRENT_TIMESTAMP),
    ('gcp_network', 0, CURRENT_TIMESTAMP)
ON CONFLICT DO NOTHING;
