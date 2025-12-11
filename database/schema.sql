-- CodeGen Tree-of-Thoughts Platform Database Schema
-- PostgreSQL 14+

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Workflows table: Stores node-based workflow definitions
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL, -- {nodes: [...], edges: [...]}
    context JSONB DEFAULT '{}', -- System context snapshot
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    is_template BOOLEAN DEFAULT FALSE
);

-- Executions table: Runtime tracking of workflow runs
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL, -- IDLE, GENERATING, EVALUATING, PRUNING, EXECUTING, COMPLETED, FAILED
    context JSONB DEFAULT '{}', -- Execution state
    results JSONB, -- Final results
    logs TEXT[], -- Execution logs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Templates table: Reusable workflow templates
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100), -- e.g., 'development', 'research', 'analysis'
    description TEXT,
    definition JSONB NOT NULL,
    downloads INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Profiles table: Agent and workflow configuration profiles
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'agent', 'workflow', 'node'
    config JSONB NOT NULL, -- Configuration settings
    rules TEXT, -- Business rules
    instructions TEXT, -- Agent instructions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workflow States table: Snapshots of workflow execution state
CREATE TABLE workflow_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    node_id VARCHAR(255), -- Current node being executed
    state JSONB NOT NULL, -- Full state snapshot
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhooks table: Event notification configuration
CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    url VARCHAR(2048) NOT NULL,
    events TEXT[] NOT NULL, -- ['workflow:updated', 'execution:completed', etc.]
    headers JSONB DEFAULT '{}', -- Custom HTTP headers
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Keys table: Authentication and authorization
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    organization_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE, -- Hashed API key
    scopes TEXT[] NOT NULL, -- ['workflows:read', 'workflows:write', 'executions:read', etc.]
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Performance Indexes
CREATE INDEX idx_workflows_org_created ON workflows(organization_id, created_at DESC);
CREATE INDEX idx_workflows_template ON workflows(is_template) WHERE is_template = TRUE;
CREATE INDEX idx_executions_workflow_status ON executions(workflow_id, status);
CREATE INDEX idx_executions_created ON executions(created_at DESC);
CREATE INDEX idx_workflow_states_execution ON workflow_states(workflow_id, execution_id);
CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_webhooks_workflow ON webhooks(workflow_id) WHERE is_active = TRUE;

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

