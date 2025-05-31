-- =====================================================
-- INDEXES SCHEMA - Advanced Indexing Strategies
-- =====================================================

-- Core foundation tables (organizations, users)
CREATE TABLE organizations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

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

-- Advanced indexing strategies
CREATE INDEX CONCURRENTLY idx_organizations_slug_active ON organizations(slug) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_org_email ON users(organization_id, email) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_role_active ON users(role) WHERE deleted_at IS NULL;

-- Composite indexes for common query patterns
CREATE INDEX CONCURRENTLY idx_users_org_role_created ON users(organization_id, role, created_at) WHERE deleted_at IS NULL;

-- Partial indexes for performance
CREATE INDEX CONCURRENTLY idx_active_users ON users(organization_id) WHERE deleted_at IS NULL AND role != 'inactive';

-- JSON indexes for settings queries
CREATE INDEX CONCURRENTLY idx_organizations_settings_gin ON organizations USING gin(settings) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_users_settings_gin ON users USING gin(settings) WHERE deleted_at IS NULL;

-- Function-based indexes
CREATE INDEX CONCURRENTLY idx_users_email_lower ON users(lower(email)) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_organizations_name_lower ON organizations(lower(name)) WHERE deleted_at IS NULL;

-- Covering indexes for read-heavy queries
CREATE INDEX CONCURRENTLY idx_users_org_covering ON users(organization_id) INCLUDE (name, email, role) WHERE deleted_at IS NULL;

-- Time-based partitioning support indexes
CREATE INDEX CONCURRENTLY idx_users_created_month ON users(date_trunc('month', created_at));
CREATE INDEX CONCURRENTLY idx_organizations_created_month ON organizations(date_trunc('month', created_at));

-- Full-text search indexes
CREATE INDEX CONCURRENTLY idx_users_name_fts ON users USING gin(to_tsvector('english', name)) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_organizations_name_fts ON organizations USING gin(to_tsvector('english', name)) WHERE deleted_at IS NULL;

-- Trigram indexes for fuzzy search
CREATE INDEX CONCURRENTLY idx_users_name_trgm ON users USING gin(name gin_trgm_ops) WHERE deleted_at IS NULL;
CREATE INDEX CONCURRENTLY idx_organizations_name_trgm ON organizations USING gin(name gin_trgm_ops) WHERE deleted_at IS NULL;

COMMENT ON SCHEMA public IS 'Advanced indexing strategies for optimal query performance across all entity types';
