-- =====================================================
-- AUDIT SCHEMA - Change Tracking and Audit Trails
-- =====================================================

-- Audit logs for all entity changes
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Entity being audited
    entity_type VARCHAR(50) NOT NULL,
    entity_id BIGINT NOT NULL,
    
    -- Action details
    action VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'view'
    action_details JSONB DEFAULT '{}',
    
    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    
    -- User and session context
    user_id BIGINT,
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    
    -- Request context
    request_id VARCHAR(255),
    api_endpoint VARCHAR(255),
    http_method VARCHAR(10),
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX(organization_id, entity_type, entity_id),
    INDEX(user_id, created_at),
    INDEX(action, created_at),
    INDEX(created_at)
);

-- Data retention policies
CREATE TABLE data_retention_policies (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    retention_days INTEGER NOT NULL,
    archive_enabled BOOLEAN DEFAULT false,
    archive_storage VARCHAR(100),
    policy_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, table_name)
);

-- Compliance tracking
CREATE TABLE compliance_events (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    compliance_type VARCHAR(50) NOT NULL, -- 'gdpr', 'hipaa', 'sox', 'custom'
    event_type VARCHAR(50) NOT NULL, -- 'data_access', 'data_export', 'data_deletion'
    entity_type VARCHAR(50),
    entity_id BIGINT,
    user_id BIGINT,
    justification TEXT,
    approval_required BOOLEAN DEFAULT false,
    approved_by BIGINT,
    approved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX(organization_id, compliance_type),
    INDEX(user_id, created_at)
);

COMMENT ON TABLE audit_logs IS 'Comprehensive audit trail for all entity changes and access';
COMMENT ON TABLE data_retention_policies IS 'Data retention policies for compliance and storage management';
COMMENT ON TABLE compliance_events IS 'Compliance-related events and approvals tracking';
