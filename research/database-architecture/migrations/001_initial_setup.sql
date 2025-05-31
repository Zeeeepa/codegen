-- =====================================================
-- INITIAL SETUP MIGRATION
-- =====================================================
-- This migration sets up the foundational database structure
-- for the comprehensive database architecture supporting
-- Graph-Sitter, Codegen SDK, and Contexten integration.
-- =====================================================

-- Create schema version tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    migration_sql TEXT NOT NULL,
    rollback_sql TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_by VARCHAR(255) NOT NULL
);

-- Record this migration
INSERT INTO schema_migrations (version, description, migration_sql, applied_by) VALUES
('001', 'Initial database setup with core tables', 'Initial setup migration', 'system');

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create organizations table
CREATE TABLE organizations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create users table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create basic indexes
CREATE INDEX idx_organizations_slug ON organizations(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_org_email ON users(organization_id, email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role) WHERE deleted_at IS NULL;

-- Create update triggers
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default organization for development
INSERT INTO organizations (name, slug) VALUES ('Default Organization', 'default');

-- Insert system user
INSERT INTO users (organization_id, email, name, role) VALUES 
(1, 'system@example.com', 'System User', 'admin');

COMMENT ON TABLE organizations IS 'Core organizations table for multi-tenant architecture';
COMMENT ON TABLE users IS 'Users table with organization-based access control';

