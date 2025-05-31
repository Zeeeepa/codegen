-- =====================================================
-- RELATIONSHIPS SCHEMA - Inter-Entity Relationship Mapping
-- =====================================================
-- This schema supports comprehensive relationship tracking including:
-- - Cross-system entity relationships
-- - Dependency mapping and analysis
-- - Relationship strength and confidence scoring
-- - Dynamic relationship discovery
-- - Relationship-based analytics
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- CORE RELATIONSHIP TABLES
-- =====================================================

-- Entity relationships - Generic relationship mapping
CREATE TABLE entity_relationships (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Source entity
    source_entity_type VARCHAR(50) NOT NULL, -- 'task', 'project', 'codebase', 'user', 'workflow'
    source_entity_id BIGINT NOT NULL,
    source_system VARCHAR(50), -- 'graph_sitter', 'codegen', 'contexten', 'linear', 'github'
    
    -- Target entity
    target_entity_type VARCHAR(50) NOT NULL,
    target_entity_id BIGINT NOT NULL,
    target_system VARCHAR(50),
    
    -- Relationship details
    relationship_type VARCHAR(100) NOT NULL, -- 'depends_on', 'triggers', 'contains', 'assigned_to', 'related_to'
    relationship_subtype VARCHAR(100), -- More specific relationship classification
    
    -- Relationship properties
    strength DECIMAL(5,2) DEFAULT 1.0, -- Relationship strength (0-100)
    confidence DECIMAL(5,2) DEFAULT 100.0, -- Confidence in relationship (0-100)
    weight DECIMAL(10,4) DEFAULT 1.0, -- Weight for graph algorithms
    
    -- Relationship metadata
    is_bidirectional BOOLEAN DEFAULT false,
    is_temporal BOOLEAN DEFAULT false, -- Time-dependent relationship
    is_inferred BOOLEAN DEFAULT false, -- Discovered vs explicitly defined
    
    -- Discovery information
    discovered_by VARCHAR(50), -- 'user', 'system', 'ml_model', 'rule_engine'
    discovery_method VARCHAR(100), -- How the relationship was discovered
    discovery_confidence DECIMAL(5,2), -- Confidence in discovery method
    
    -- Temporal aspects
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Additional context
    context_data JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX(organization_id, source_entity_type, source_entity_id),
    INDEX(organization_id, target_entity_type, target_entity_id),
    INDEX(relationship_type, strength),
    INDEX(valid_from, valid_until)
);

-- Relationship types - Define valid relationship types
CREATE TABLE relationship_types (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT,
    
    -- Type definition
    type_name VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    
    -- Type properties
    is_directional BOOLEAN DEFAULT true,
    is_hierarchical BOOLEAN DEFAULT false,
    allows_multiple BOOLEAN DEFAULT true,
    
    -- Valid entity combinations
    valid_source_types JSONB DEFAULT '[]', -- Array of valid source entity types
    valid_target_types JSONB DEFAULT '[]', -- Array of valid target entity types
    
    -- Relationship rules
    validation_rules JSONB DEFAULT '{}',
    inference_rules JSONB DEFAULT '{}',
    
    -- Visualization
    display_config JSONB DEFAULT '{}', -- How to display in UI
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_system_type BOOLEAN DEFAULT false, -- System vs user-defined
    
    -- Audit
    created_by BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(organization_id, type_name)
);

-- =====================================================
-- SPECIALIZED RELATIONSHIP TABLES
-- =====================================================

-- Task relationships - Specific task-related relationships
CREATE TABLE task_relationships (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Task relationship
    source_task_id BIGINT NOT NULL,
    target_task_id BIGINT NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- 'blocks', 'depends_on', 'relates_to', 'duplicates'
    
    -- Relationship strength
    blocking_strength DECIMAL(5,2) DEFAULT 100.0, -- How much it blocks (0-100)
    dependency_criticality VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    
    -- Temporal aspects
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Context
    created_by BIGINT,
    notes TEXT,
    
    UNIQUE(source_task_id, target_task_id, relationship_type)
);

-- Code relationships - Code-level relationships
CREATE TABLE code_relationships_extended (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    codebase_id BIGINT NOT NULL,
    
    -- Code entities
    source_file_id BIGINT,
    source_symbol_id BIGINT,
    target_file_id BIGINT,
    target_symbol_id BIGINT,
    
    -- Relationship details
    relationship_type VARCHAR(50) NOT NULL, -- 'imports', 'calls', 'extends', 'implements'
    call_frequency INTEGER DEFAULT 0, -- How often this relationship is used
    
    -- Analysis metadata
    detected_by_analysis VARCHAR(50), -- Which analysis detected this
    confidence_score DECIMAL(5,2) DEFAULT 100.0,
    
    -- Impact analysis
    change_impact_score DECIMAL(5,2), -- Impact if source changes
    coupling_strength DECIMAL(5,2), -- How tightly coupled
    
    -- Audit
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX(codebase_id, relationship_type),
    INDEX(source_file_id, target_file_id)
);

-- User relationships - Team and collaboration relationships
CREATE TABLE user_relationships (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- User relationship
    source_user_id BIGINT NOT NULL,
    target_user_id BIGINT NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- 'reports_to', 'collaborates_with', 'mentors'
    
    -- Relationship strength
    collaboration_frequency DECIMAL(5,2), -- How often they collaborate
    communication_score DECIMAL(5,2), -- Communication frequency/quality
    
    -- Context
    project_context BIGINT[], -- Projects where they collaborate
    team_context BIGINT[], -- Teams they share
    
    -- Temporal
    relationship_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    relationship_end TIMESTAMP WITH TIME ZONE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source_user_id, target_user_id, relationship_type)
);

-- =====================================================
-- RELATIONSHIP ANALYSIS TABLES
-- =====================================================

-- Relationship graphs - Precomputed relationship graphs
CREATE TABLE relationship_graphs (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Graph identification
    graph_name VARCHAR(255) NOT NULL,
    graph_type VARCHAR(50) NOT NULL, -- 'dependency', 'collaboration', 'impact', 'workflow'
    
    -- Graph scope
    entity_types JSONB NOT NULL, -- Types of entities included
    relationship_types JSONB NOT NULL, -- Types of relationships included
    filters JSONB DEFAULT '{}', -- Additional filters applied
    
    -- Graph data
    nodes JSONB NOT NULL, -- Node definitions
    edges JSONB NOT NULL, -- Edge definitions
    graph_metrics JSONB DEFAULT '{}', -- Calculated graph metrics
    
    -- Graph properties
    node_count INTEGER DEFAULT 0,
    edge_count INTEGER DEFAULT 0,
    is_directed BOOLEAN DEFAULT true,
    is_cyclic BOOLEAN,
    
    -- Analysis results
    centrality_scores JSONB DEFAULT '{}', -- Node centrality scores
    community_detection JSONB DEFAULT '{}', -- Community/cluster analysis
    critical_paths JSONB DEFAULT '[]', -- Critical paths in graph
    
    -- Generation metadata
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generation_duration_ms INTEGER,
    data_freshness TIMESTAMP WITH TIME ZONE, -- Freshness of underlying data
    
    -- Status
    status VARCHAR(50) DEFAULT 'current', -- 'current', 'stale', 'generating'
    
    UNIQUE(organization_id, graph_name, graph_type)
);

-- Relationship patterns - Discovered relationship patterns
CREATE TABLE relationship_patterns (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Pattern identification
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL, -- 'workflow', 'dependency', 'collaboration', 'anti_pattern'
    
    -- Pattern definition
    pattern_structure JSONB NOT NULL, -- Structure of the pattern
    entity_roles JSONB NOT NULL, -- Roles of entities in pattern
    relationship_sequence JSONB DEFAULT '[]', -- Sequence of relationships
    
    -- Pattern metrics
    occurrence_count INTEGER DEFAULT 0,
    confidence_score DECIMAL(5,2) DEFAULT 0,
    support_score DECIMAL(5,2) DEFAULT 0, -- How often pattern occurs
    
    -- Pattern analysis
    is_beneficial BOOLEAN, -- Whether pattern is beneficial
    impact_score DECIMAL(5,2), -- Impact of this pattern
    recommendations JSONB DEFAULT '[]', -- Recommendations based on pattern
    
    -- Discovery metadata
    discovered_by VARCHAR(50), -- 'ml_model', 'rule_engine', 'user'
    discovery_algorithm VARCHAR(100),
    last_detected_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- RELATIONSHIP ANALYTICS
-- =====================================================

-- Relationship metrics - Calculated relationship metrics
CREATE TABLE relationship_metrics (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Entity metrics
    total_entities INTEGER DEFAULT 0,
    total_relationships INTEGER DEFAULT 0,
    avg_relationships_per_entity DECIMAL(10,2),
    
    -- Relationship type distribution
    relationship_type_distribution JSONB DEFAULT '{}',
    
    -- Graph metrics
    graph_density DECIMAL(10,6), -- How connected the graph is
    avg_path_length DECIMAL(10,2), -- Average shortest path
    clustering_coefficient DECIMAL(10,6), -- How clustered the graph is
    
    -- Centrality metrics
    most_central_entities JSONB DEFAULT '[]', -- Entities with highest centrality
    bottleneck_entities JSONB DEFAULT '[]', -- Entities that are bottlenecks
    
    -- Change metrics
    new_relationships_count INTEGER DEFAULT 0,
    removed_relationships_count INTEGER DEFAULT 0,
    modified_relationships_count INTEGER DEFAULT 0,
    
    -- Quality metrics
    avg_relationship_confidence DECIMAL(5,2),
    inferred_relationships_percentage DECIMAL(5,2),
    
    -- Calculated at end of day
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, metric_date)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Entity relationships indexes
CREATE INDEX idx_entity_relationships_source ON entity_relationships(organization_id, source_entity_type, source_entity_id);
CREATE INDEX idx_entity_relationships_target ON entity_relationships(organization_id, target_entity_type, target_entity_id);
CREATE INDEX idx_entity_relationships_type ON entity_relationships(relationship_type, strength);
CREATE INDEX idx_entity_relationships_temporal ON entity_relationships(valid_from, valid_until);
CREATE INDEX idx_entity_relationships_discovery ON entity_relationships(discovered_by, is_inferred);

-- Specialized relationship indexes
CREATE INDEX idx_task_relationships_source ON task_relationships(source_task_id, relationship_type);
CREATE INDEX idx_task_relationships_target ON task_relationships(target_task_id, relationship_type);
CREATE INDEX idx_code_relationships_ext_codebase ON code_relationships_extended(codebase_id, relationship_type);
CREATE INDEX idx_user_relationships_source ON user_relationships(source_user_id, relationship_type);

-- Graph and pattern indexes
CREATE INDEX idx_relationship_graphs_org_type ON relationship_graphs(organization_id, graph_type, status);
CREATE INDEX idx_relationship_patterns_org_type ON relationship_patterns(organization_id, pattern_type);
CREATE INDEX idx_relationship_patterns_confidence ON relationship_patterns(confidence_score, occurrence_count);

-- Metrics indexes
CREATE INDEX idx_relationship_metrics_org_date ON relationship_metrics(organization_id, metric_date);

-- JSON indexes for complex queries
CREATE INDEX idx_entity_relationships_context_gin ON entity_relationships USING gin(context_data);
CREATE INDEX idx_relationship_graphs_nodes_gin ON relationship_graphs USING gin(nodes);
CREATE INDEX idx_relationship_patterns_structure_gin ON relationship_patterns USING gin(pattern_structure);

-- =====================================================
-- TRIGGERS FOR AUTOMATION
-- =====================================================

-- Update updated_at timestamp
CREATE TRIGGER update_entity_relationships_updated_at BEFORE UPDATE ON entity_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_relationship_types_updated_at BEFORE UPDATE ON relationship_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Validate relationship types
CREATE OR REPLACE FUNCTION validate_relationship_type()
RETURNS TRIGGER AS $$
DECLARE
    type_config RECORD;
BEGIN
    -- Get relationship type configuration
    SELECT * INTO type_config
    FROM relationship_types rt
    WHERE rt.type_name = NEW.relationship_type
    AND (rt.organization_id = NEW.organization_id OR rt.organization_id IS NULL)
    AND rt.is_active = true
    AND rt.deleted_at IS NULL;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid relationship type: %', NEW.relationship_type;
    END IF;
    
    -- Validate source and target entity types
    IF type_config.valid_source_types IS NOT NULL THEN
        IF NOT (type_config.valid_source_types ? NEW.source_entity_type) THEN
            RAISE EXCEPTION 'Invalid source entity type % for relationship type %', 
                NEW.source_entity_type, NEW.relationship_type;
        END IF;
    END IF;
    
    IF type_config.valid_target_types IS NOT NULL THEN
        IF NOT (type_config.valid_target_types ? NEW.target_entity_type) THEN
            RAISE EXCEPTION 'Invalid target entity type % for relationship type %', 
                NEW.target_entity_type, NEW.relationship_type;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER validate_relationship_type_trigger 
    BEFORE INSERT OR UPDATE ON entity_relationships
    FOR EACH ROW EXECUTE FUNCTION validate_relationship_type();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Active relationships view
CREATE VIEW active_relationships AS
SELECT 
    er.*,
    rt.display_name as relationship_display_name,
    rt.is_directional,
    rt.is_hierarchical,
    CASE 
        WHEN er.strength >= 80 THEN 'strong'
        WHEN er.strength >= 60 THEN 'medium'
        WHEN er.strength >= 40 THEN 'weak'
        ELSE 'very_weak'
    END as strength_category,
    CASE 
        WHEN er.confidence >= 90 THEN 'high'
        WHEN er.confidence >= 70 THEN 'medium'
        ELSE 'low'
    END as confidence_category
FROM entity_relationships er
LEFT JOIN relationship_types rt ON er.relationship_type = rt.type_name 
    AND (rt.organization_id = er.organization_id OR rt.organization_id IS NULL)
WHERE er.deleted_at IS NULL
AND (er.valid_until IS NULL OR er.valid_until > NOW())
AND rt.deleted_at IS NULL;

-- Relationship summary by entity
CREATE VIEW entity_relationship_summary AS
SELECT 
    organization_id,
    source_entity_type,
    source_entity_id,
    COUNT(*) as outgoing_relationships,
    COUNT(DISTINCT relationship_type) as relationship_types_count,
    AVG(strength) as avg_relationship_strength,
    COUNT(*) FILTER (WHERE is_inferred = true) as inferred_count,
    COUNT(*) FILTER (WHERE is_inferred = false) as explicit_count
FROM entity_relationships
WHERE deleted_at IS NULL
AND (valid_until IS NULL OR valid_until > NOW())
GROUP BY organization_id, source_entity_type, source_entity_id

UNION ALL

SELECT 
    organization_id,
    target_entity_type as source_entity_type,
    target_entity_id as source_entity_id,
    COUNT(*) as incoming_relationships,
    COUNT(DISTINCT relationship_type) as relationship_types_count,
    AVG(strength) as avg_relationship_strength,
    COUNT(*) FILTER (WHERE is_inferred = true) as inferred_count,
    COUNT(*) FILTER (WHERE is_inferred = false) as explicit_count
FROM entity_relationships
WHERE deleted_at IS NULL
AND (valid_until IS NULL OR valid_until > NOW())
GROUP BY organization_id, target_entity_type, target_entity_id;

-- =====================================================
-- FUNCTIONS FOR RELATIONSHIP ANALYSIS
-- =====================================================

-- Function to find shortest path between entities
CREATE OR REPLACE FUNCTION find_shortest_path(
    org_id BIGINT,
    source_type VARCHAR(50),
    source_id BIGINT,
    target_type VARCHAR(50),
    target_id BIGINT,
    max_depth INTEGER DEFAULT 6
)
RETURNS TABLE(
    path_length INTEGER,
    path_entities JSONB,
    path_relationships JSONB
) AS $$
WITH RECURSIVE path_search AS (
    -- Base case: direct relationships
    SELECT 
        1 as depth,
        ARRAY[ROW(source_entity_type, source_entity_id)::entity_ref] as path_entities,
        ARRAY[relationship_type] as path_relationships,
        target_entity_type,
        target_entity_id
    FROM entity_relationships
    WHERE organization_id = org_id
    AND source_entity_type = source_type
    AND source_entity_id = source_id
    AND deleted_at IS NULL
    AND (valid_until IS NULL OR valid_until > NOW())
    
    UNION ALL
    
    -- Recursive case: extend paths
    SELECT 
        ps.depth + 1,
        ps.path_entities || ROW(er.source_entity_type, er.source_entity_id)::entity_ref,
        ps.path_relationships || er.relationship_type,
        er.target_entity_type,
        er.target_entity_id
    FROM path_search ps
    JOIN entity_relationships er ON 
        ps.target_entity_type = er.source_entity_type
        AND ps.target_entity_id = er.source_entity_id
    WHERE ps.depth < max_depth
    AND er.organization_id = org_id
    AND er.deleted_at IS NULL
    AND (er.valid_until IS NULL OR er.valid_until > NOW())
    -- Prevent cycles
    AND NOT ROW(er.target_entity_type, er.target_entity_id)::entity_ref = ANY(ps.path_entities)
)
SELECT 
    depth as path_length,
    to_jsonb(path_entities || ROW(target_entity_type, target_entity_id)::entity_ref) as path_entities,
    to_jsonb(path_relationships) as path_relationships
FROM path_search
WHERE target_entity_type = target_type
AND target_entity_id = target_id
ORDER BY depth
LIMIT 1;
$$ LANGUAGE SQL;

-- Function to calculate entity centrality
CREATE OR REPLACE FUNCTION calculate_entity_centrality(
    org_id BIGINT,
    entity_type VARCHAR(50),
    entity_id BIGINT
)
RETURNS DECIMAL(10,6) AS $$
DECLARE
    in_degree INTEGER;
    out_degree INTEGER;
    total_entities INTEGER;
    centrality DECIMAL(10,6);
BEGIN
    -- Count incoming relationships
    SELECT COUNT(*) INTO in_degree
    FROM entity_relationships
    WHERE organization_id = org_id
    AND target_entity_type = entity_type
    AND target_entity_id = entity_id
    AND deleted_at IS NULL
    AND (valid_until IS NULL OR valid_until > NOW());
    
    -- Count outgoing relationships
    SELECT COUNT(*) INTO out_degree
    FROM entity_relationships
    WHERE organization_id = org_id
    AND source_entity_type = entity_type
    AND source_entity_id = entity_id
    AND deleted_at IS NULL
    AND (valid_until IS NULL OR valid_until > NOW());
    
    -- Count total entities of this type
    SELECT COUNT(DISTINCT source_entity_id) INTO total_entities
    FROM entity_relationships
    WHERE organization_id = org_id
    AND source_entity_type = entity_type
    AND deleted_at IS NULL;
    
    -- Calculate degree centrality
    IF total_entities > 1 THEN
        centrality := (in_degree + out_degree)::DECIMAL / (total_entities - 1);
    ELSE
        centrality := 0;
    END IF;
    
    RETURN centrality;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SAMPLE DATA AND INITIALIZATION
-- =====================================================

-- Insert standard relationship types
INSERT INTO relationship_types (type_name, display_name, description, is_directional, valid_source_types, valid_target_types, is_system_type) VALUES
('depends_on', 'Depends On', 'Source entity depends on target entity', true, '["task", "project", "workflow"]', '["task", "project", "codebase"]', true),
('blocks', 'Blocks', 'Source entity blocks target entity', true, '["task", "issue"]', '["task", "issue"]', true),
('contains', 'Contains', 'Source entity contains target entity', true, '["project", "codebase"]', '["task", "file", "function"]', true),
('assigned_to', 'Assigned To', 'Source entity is assigned to target entity', true, '["task", "project"]', '["user", "team"]', true),
('collaborates_with', 'Collaborates With', 'Entities collaborate together', false, '["user"]', '["user"]', true);

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE entity_relationships IS 'Generic relationship mapping between any types of entities across systems';
COMMENT ON TABLE relationship_types IS 'Defines valid relationship types and their properties';
COMMENT ON TABLE task_relationships IS 'Specialized relationships between tasks with blocking and dependency information';
COMMENT ON TABLE code_relationships_extended IS 'Extended code relationships with analysis metadata and impact scoring';
COMMENT ON TABLE user_relationships IS 'Team and collaboration relationships between users';
COMMENT ON TABLE relationship_graphs IS 'Precomputed relationship graphs for visualization and analysis';
COMMENT ON TABLE relationship_patterns IS 'Discovered patterns in relationships for optimization insights';
COMMENT ON TABLE relationship_metrics IS 'Daily aggregated metrics about relationships and graph properties';

COMMENT ON COLUMN entity_relationships.strength IS 'Relationship strength from 0-100, higher values indicate stronger relationships';
COMMENT ON COLUMN entity_relationships.confidence IS 'Confidence in relationship accuracy from 0-100';
COMMENT ON COLUMN entity_relationships.is_inferred IS 'Whether relationship was discovered automatically vs explicitly defined';
COMMENT ON COLUMN relationship_graphs.centrality_scores IS 'Calculated centrality scores for nodes in the graph';
COMMENT ON COLUMN relationship_patterns.support_score IS 'How frequently this pattern occurs in the data';
