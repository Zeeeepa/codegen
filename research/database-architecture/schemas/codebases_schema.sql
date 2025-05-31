-- =====================================================
-- CODEBASES SCHEMA - Repository and Code Analysis Data
-- =====================================================
-- This schema supports comprehensive codebase analysis including:
-- - Repository metadata and configuration
-- - File structure and content analysis
-- - Function, class, and symbol tracking
-- - Code relationships and dependencies
-- - Integration with Graph-Sitter analysis
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =====================================================
-- CORE CODEBASE TABLES
-- =====================================================

-- Codebases table - Repository and codebase metadata
CREATE TABLE codebases (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    project_id BIGINT,
    
    -- Repository identification
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    repository_url VARCHAR(500),
    repository_type VARCHAR(50) DEFAULT 'git', -- 'git', 'svn', 'mercurial', 'local'
    
    -- Repository configuration
    default_branch VARCHAR(255) DEFAULT 'main',
    current_branch VARCHAR(255),
    current_commit_hash VARCHAR(40),
    
    -- Language and framework detection
    primary_language VARCHAR(50),
    languages JSONB DEFAULT '{}', -- Language distribution
    frameworks JSONB DEFAULT '[]', -- Detected frameworks
    build_tools JSONB DEFAULT '[]', -- Build tools (npm, maven, gradle, etc.)
    
    -- Analysis configuration
    analysis_config JSONB DEFAULT '{}', -- Graph-Sitter and analysis settings
    ignore_patterns TEXT[], -- Files/directories to ignore
    include_patterns TEXT[], -- Files/directories to include
    
    -- Status and health
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'archived', 'error', 'analyzing'
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    analysis_version VARCHAR(50), -- Version of analysis engine used
    health_score DECIMAL(5,2), -- Overall codebase health (0-100)
    
    -- Metrics
    total_files INTEGER DEFAULT 0,
    total_lines_of_code INTEGER DEFAULT 0,
    total_functions INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    
    -- Metadata and settings
    metadata JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    tags TEXT[],
    
    -- Audit fields
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT codebases_health_score_range CHECK (health_score >= 0 AND health_score <= 100),
    CONSTRAINT codebases_metrics_positive CHECK (
        total_files >= 0 AND 
        total_lines_of_code >= 0 AND 
        total_functions >= 0 AND 
        total_classes >= 0
    )
);

-- Code files table - Individual file tracking and analysis
CREATE TABLE code_files (
    id BIGSERIAL PRIMARY KEY,
    codebase_id BIGINT NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- File identification
    file_path VARCHAR(1000) NOT NULL, -- Relative path from repository root
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(20),
    
    -- File metadata
    file_type VARCHAR(50), -- 'source', 'test', 'config', 'documentation', 'asset'
    language VARCHAR(50),
    encoding VARCHAR(20) DEFAULT 'utf-8',
    
    -- File content analysis
    size_bytes BIGINT DEFAULT 0,
    lines_of_code INTEGER DEFAULT 0,
    lines_of_comments INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    
    -- Code quality metrics
    complexity_score DECIMAL(10,2),
    maintainability_index DECIMAL(5,2),
    technical_debt_minutes INTEGER DEFAULT 0,
    
    -- File hash and versioning
    content_hash VARCHAR(64), -- SHA-256 hash of file content
    last_modified TIMESTAMP WITH TIME ZONE,
    git_blame_data JSONB DEFAULT '{}', -- Git blame information
    
    -- Analysis results
    syntax_errors JSONB DEFAULT '[]',
    lint_warnings JSONB DEFAULT '[]',
    security_issues JSONB DEFAULT '[]',
    
    -- Graph-Sitter analysis
    ast_data JSONB DEFAULT '{}', -- Abstract syntax tree data
    symbol_table JSONB DEFAULT '{}', -- Symbol definitions in file
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    analysis_metadata JSONB DEFAULT '{}',
    
    -- Audit
    analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(codebase_id, file_path),
    CONSTRAINT code_files_metrics_positive CHECK (
        size_bytes >= 0 AND 
        lines_of_code >= 0 AND 
        lines_of_comments >= 0 AND 
        blank_lines >= 0
    )
);

-- Code symbols table - Functions, classes, variables, etc.
CREATE TABLE code_symbols (
    id BIGSERIAL PRIMARY KEY,
    file_id BIGINT NOT NULL REFERENCES code_files(id) ON DELETE CASCADE,
    codebase_id BIGINT NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Symbol identification
    name VARCHAR(255) NOT NULL,
    qualified_name VARCHAR(1000), -- Fully qualified name including namespace
    symbol_type VARCHAR(50) NOT NULL, -- 'function', 'class', 'variable', 'constant', 'interface', 'enum'
    visibility VARCHAR(20) DEFAULT 'public', -- 'public', 'private', 'protected', 'internal'
    
    -- Symbol location
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    start_column INTEGER,
    end_column INTEGER,
    
    -- Symbol signature and metadata
    signature TEXT, -- Function signature, class definition, etc.
    return_type VARCHAR(255),
    parameters JSONB DEFAULT '[]', -- Parameter information
    decorators JSONB DEFAULT '[]', -- Decorators/annotations
    
    -- Code quality metrics
    complexity_score DECIMAL(10,2),
    lines_of_code INTEGER DEFAULT 0,
    parameter_count INTEGER DEFAULT 0,
    
    -- Documentation
    docstring TEXT,
    comments JSONB DEFAULT '[]',
    
    -- Symbol relationships
    parent_symbol_id BIGINT REFERENCES code_symbols(id) ON DELETE SET NULL,
    namespace_path VARCHAR(500), -- Namespace hierarchy
    
    -- Analysis data
    usage_count INTEGER DEFAULT 0, -- How many times this symbol is referenced
    is_exported BOOLEAN DEFAULT false,
    is_deprecated BOOLEAN DEFAULT false,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    analysis_metadata JSONB DEFAULT '{}',
    
    -- Audit
    analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT code_symbols_lines_valid CHECK (end_line >= start_line),
    CONSTRAINT code_symbols_metrics_positive CHECK (
        lines_of_code >= 0 AND 
        parameter_count >= 0 AND 
        usage_count >= 0
    )
);

-- Code relationships table - Dependencies, imports, calls, etc.
CREATE TABLE code_relationships (
    id BIGSERIAL PRIMARY KEY,
    codebase_id BIGINT NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Source and target identification
    source_type VARCHAR(50) NOT NULL, -- 'file', 'symbol', 'module'
    source_id BIGINT NOT NULL,
    source_file_id BIGINT REFERENCES code_files(id) ON DELETE CASCADE,
    
    target_type VARCHAR(50) NOT NULL,
    target_id BIGINT,
    target_file_id BIGINT REFERENCES code_files(id) ON DELETE SET NULL,
    target_external VARCHAR(500), -- External dependencies (npm packages, etc.)
    
    -- Relationship details
    relationship_type VARCHAR(50) NOT NULL, -- 'imports', 'calls', 'extends', 'implements', 'uses', 'references'
    relationship_strength DECIMAL(5,2) DEFAULT 1.0, -- Strength of relationship (0-1)
    
    -- Location information
    source_line INTEGER,
    source_column INTEGER,
    
    -- Relationship metadata
    import_alias VARCHAR(255), -- Alias used in import
    is_dynamic BOOLEAN DEFAULT false, -- Dynamic vs static relationship
    is_conditional BOOLEAN DEFAULT false, -- Conditional relationship
    
    -- Context
    context_data JSONB DEFAULT '{}', -- Additional context about relationship
    
    -- Audit
    analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for polymorphic relationships
    INDEX(source_type, source_id),
    INDEX(target_type, target_id),
    INDEX(codebase_id, relationship_type)
);

-- =====================================================
-- CODEBASE ANALYSIS AND METRICS
-- =====================================================

-- Codebase analysis sessions
CREATE TABLE codebase_analysis_sessions (
    id BIGSERIAL PRIMARY KEY,
    codebase_id BIGINT NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Session identification
    session_id UUID DEFAULT uuid_generate_v4(),
    analysis_type VARCHAR(50) NOT NULL, -- 'full', 'incremental', 'targeted'
    trigger_type VARCHAR(50) NOT NULL, -- 'manual', 'scheduled', 'webhook', 'api'
    
    -- Session configuration
    config JSONB DEFAULT '{}',
    include_patterns TEXT[],
    exclude_patterns TEXT[],
    
    -- Session status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Results summary
    files_analyzed INTEGER DEFAULT 0,
    symbols_found INTEGER DEFAULT 0,
    relationships_found INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    
    -- Results
    results_summary JSONB DEFAULT '{}',
    
    -- Audit
    triggered_by BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Code quality metrics (daily aggregates)
CREATE TABLE codebase_quality_metrics (
    id BIGSERIAL PRIMARY KEY,
    codebase_id BIGINT NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- File metrics
    total_files INTEGER DEFAULT 0,
    source_files INTEGER DEFAULT 0,
    test_files INTEGER DEFAULT 0,
    config_files INTEGER DEFAULT 0,
    
    -- Code metrics
    total_lines_of_code INTEGER DEFAULT 0,
    total_lines_of_comments INTEGER DEFAULT 0,
    total_blank_lines INTEGER DEFAULT 0,
    
    -- Symbol metrics
    total_functions INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    total_variables INTEGER DEFAULT 0,
    total_constants INTEGER DEFAULT 0,
    
    -- Quality metrics
    average_complexity DECIMAL(10,2),
    max_complexity DECIMAL(10,2),
    average_maintainability DECIMAL(5,2),
    technical_debt_hours DECIMAL(10,2),
    
    -- Issue counts
    syntax_errors INTEGER DEFAULT 0,
    lint_warnings INTEGER DEFAULT 0,
    security_issues INTEGER DEFAULT 0,
    
    -- Test coverage (if available)
    test_coverage_percentage DECIMAL(5,2),
    
    -- Language distribution
    language_distribution JSONB DEFAULT '{}',
    
    -- Calculated metrics
    code_to_comment_ratio DECIMAL(5,2),
    test_to_source_ratio DECIMAL(5,2),
    
    -- Audit
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(codebase_id, metric_date)
);

-- Code hotspots - Files that change frequently or have issues
CREATE TABLE code_hotspots (
    id BIGSERIAL PRIMARY KEY,
    codebase_id BIGINT NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    file_id BIGINT NOT NULL REFERENCES code_files(id) ON DELETE CASCADE,
    
    -- Hotspot metrics
    change_frequency INTEGER DEFAULT 0, -- Number of changes in analysis period
    bug_count INTEGER DEFAULT 0, -- Number of bugs found in this file
    complexity_score DECIMAL(10,2),
    
    -- Risk assessment
    risk_level VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    risk_factors JSONB DEFAULT '[]',
    
    -- Recommendations
    recommendations JSONB DEFAULT '[]',
    
    -- Analysis period
    analysis_start_date DATE NOT NULL,
    analysis_end_date DATE NOT NULL,
    
    -- Audit
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(codebase_id, file_id, analysis_start_date, analysis_end_date)
);

-- =====================================================
-- EXTERNAL DEPENDENCIES AND PACKAGES
-- =====================================================

-- External dependencies (npm, pip, maven, etc.)
CREATE TABLE external_dependencies (
    id BIGSERIAL PRIMARY KEY,
    codebase_id BIGINT NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Package identification
    package_name VARCHAR(255) NOT NULL,
    package_version VARCHAR(100),
    package_manager VARCHAR(50), -- 'npm', 'pip', 'maven', 'gradle', 'composer', etc.
    
    -- Dependency details
    dependency_type VARCHAR(50) DEFAULT 'runtime', -- 'runtime', 'development', 'test', 'build'
    is_direct BOOLEAN DEFAULT true, -- Direct vs transitive dependency
    
    -- Version constraints
    version_constraint VARCHAR(100), -- Original version constraint from package file
    resolved_version VARCHAR(100), -- Actual resolved version
    
    -- Security and quality
    has_vulnerabilities BOOLEAN DEFAULT false,
    vulnerability_count INTEGER DEFAULT 0,
    vulnerability_severity VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    
    -- License information
    license VARCHAR(100),
    license_compatibility VARCHAR(50), -- 'compatible', 'incompatible', 'unknown'
    
    -- Usage tracking
    import_count INTEGER DEFAULT 0, -- How many files import this dependency
    usage_locations JSONB DEFAULT '[]', -- Where this dependency is used
    
    -- Metadata
    description TEXT,
    homepage_url VARCHAR(500),
    repository_url VARCHAR(500),
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_checked_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(codebase_id, package_name, package_manager)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Codebase indexes
CREATE INDEX idx_codebases_organization_status ON codebases(organization_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_codebases_project ON codebases(project_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_codebases_language ON codebases(primary_language) WHERE deleted_at IS NULL;
CREATE INDEX idx_codebases_last_analyzed ON codebases(last_analyzed_at) WHERE deleted_at IS NULL;

-- Code files indexes
CREATE INDEX idx_code_files_codebase_type ON code_files(codebase_id, file_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_code_files_language ON code_files(language) WHERE deleted_at IS NULL;
CREATE INDEX idx_code_files_path_search ON code_files USING gin(to_tsvector('english', file_path)) WHERE deleted_at IS NULL;
CREATE INDEX idx_code_files_complexity ON code_files(complexity_score) WHERE deleted_at IS NULL;
CREATE INDEX idx_code_files_size ON code_files(size_bytes) WHERE deleted_at IS NULL;

-- Code symbols indexes
CREATE INDEX idx_code_symbols_file ON code_symbols(file_id);
CREATE INDEX idx_code_symbols_codebase_type ON code_symbols(codebase_id, symbol_type);
CREATE INDEX idx_code_symbols_name_search ON code_symbols USING gin(to_tsvector('english', name));
CREATE INDEX idx_code_symbols_qualified_name ON code_symbols(qualified_name);
CREATE INDEX idx_code_symbols_parent ON code_symbols(parent_symbol_id);
CREATE INDEX idx_code_symbols_complexity ON code_symbols(complexity_score);
CREATE INDEX idx_code_symbols_usage ON code_symbols(usage_count);

-- Code relationships indexes
CREATE INDEX idx_code_relationships_source ON code_relationships(source_type, source_id);
CREATE INDEX idx_code_relationships_target ON code_relationships(target_type, target_id);
CREATE INDEX idx_code_relationships_type ON code_relationships(codebase_id, relationship_type);
CREATE INDEX idx_code_relationships_files ON code_relationships(source_file_id, target_file_id);

-- Analysis and metrics indexes
CREATE INDEX idx_analysis_sessions_codebase_status ON codebase_analysis_sessions(codebase_id, status);
CREATE INDEX idx_analysis_sessions_created ON codebase_analysis_sessions(created_at);
CREATE INDEX idx_quality_metrics_codebase_date ON codebase_quality_metrics(codebase_id, metric_date);
CREATE INDEX idx_hotspots_codebase_risk ON code_hotspots(codebase_id, risk_level);

-- Dependencies indexes
CREATE INDEX idx_external_deps_codebase_manager ON external_dependencies(codebase_id, package_manager);
CREATE INDEX idx_external_deps_vulnerabilities ON external_dependencies(has_vulnerabilities, vulnerability_severity);
CREATE INDEX idx_external_deps_package_name ON external_dependencies(package_name);

-- JSON indexes for metadata queries
CREATE INDEX idx_codebases_metadata_gin ON codebases USING gin(metadata) WHERE deleted_at IS NULL;
CREATE INDEX idx_code_files_ast_gin ON code_files USING gin(ast_data) WHERE deleted_at IS NULL;
CREATE INDEX idx_code_symbols_metadata_gin ON code_symbols USING gin(metadata);

-- =====================================================
-- TRIGGERS FOR AUTOMATION
-- =====================================================

-- Update updated_at timestamp
CREATE TRIGGER update_codebases_updated_at BEFORE UPDATE ON codebases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_files_updated_at BEFORE UPDATE ON code_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_symbols_updated_at BEFORE UPDATE ON code_symbols
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update codebase metrics when files change
CREATE OR REPLACE FUNCTION update_codebase_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update codebase totals when files are added/updated/deleted
    UPDATE codebases SET
        total_files = (
            SELECT COUNT(*) 
            FROM code_files 
            WHERE codebase_id = COALESCE(NEW.codebase_id, OLD.codebase_id) 
            AND deleted_at IS NULL
        ),
        total_lines_of_code = (
            SELECT COALESCE(SUM(lines_of_code), 0)
            FROM code_files 
            WHERE codebase_id = COALESCE(NEW.codebase_id, OLD.codebase_id) 
            AND deleted_at IS NULL
        ),
        total_functions = (
            SELECT COUNT(*)
            FROM code_symbols cs
            JOIN code_files cf ON cs.file_id = cf.id
            WHERE cf.codebase_id = COALESCE(NEW.codebase_id, OLD.codebase_id)
            AND cs.symbol_type = 'function'
            AND cf.deleted_at IS NULL
        ),
        total_classes = (
            SELECT COUNT(*)
            FROM code_symbols cs
            JOIN code_files cf ON cs.file_id = cf.id
            WHERE cf.codebase_id = COALESCE(NEW.codebase_id, OLD.codebase_id)
            AND cs.symbol_type = 'class'
            AND cf.deleted_at IS NULL
        ),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.codebase_id, OLD.codebase_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

CREATE TRIGGER update_codebase_metrics_on_file_change 
    AFTER INSERT OR UPDATE OR DELETE ON code_files
    FOR EACH ROW EXECUTE FUNCTION update_codebase_metrics();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Codebase overview with metrics
CREATE VIEW codebase_overview AS
SELECT 
    c.*,
    p.name as project_name,
    u.name as creator_name,
    qm.average_complexity,
    qm.technical_debt_hours,
    qm.test_coverage_percentage,
    qm.syntax_errors,
    qm.lint_warnings,
    qm.security_issues,
    CASE 
        WHEN c.last_analyzed_at IS NULL THEN 'never'
        WHEN c.last_analyzed_at < NOW() - INTERVAL '7 days' THEN 'stale'
        WHEN c.last_analyzed_at < NOW() - INTERVAL '1 day' THEN 'outdated'
        ELSE 'current'
    END as analysis_freshness
FROM codebases c
LEFT JOIN projects p ON c.project_id = p.id
LEFT JOIN users u ON c.created_by = u.id
LEFT JOIN codebase_quality_metrics qm ON c.id = qm.codebase_id 
    AND qm.metric_date = CURRENT_DATE
WHERE c.deleted_at IS NULL;

-- File complexity analysis
CREATE VIEW file_complexity_analysis AS
SELECT 
    cf.*,
    c.name as codebase_name,
    CASE 
        WHEN cf.complexity_score IS NULL THEN 'unknown'
        WHEN cf.complexity_score <= 10 THEN 'low'
        WHEN cf.complexity_score <= 20 THEN 'medium'
        WHEN cf.complexity_score <= 50 THEN 'high'
        ELSE 'very_high'
    END as complexity_level,
    (cf.lines_of_code::DECIMAL / NULLIF(cf.lines_of_code + cf.lines_of_comments + cf.blank_lines, 0)) * 100 as code_density_percentage
FROM code_files cf
JOIN codebases c ON cf.codebase_id = c.id
WHERE cf.deleted_at IS NULL
AND c.deleted_at IS NULL;

-- Symbol usage analysis
CREATE VIEW symbol_usage_analysis AS
SELECT 
    cs.*,
    cf.file_path,
    c.name as codebase_name,
    CASE 
        WHEN cs.usage_count = 0 THEN 'unused'
        WHEN cs.usage_count <= 5 THEN 'low_usage'
        WHEN cs.usage_count <= 20 THEN 'medium_usage'
        ELSE 'high_usage'
    END as usage_level,
    CASE 
        WHEN cs.complexity_score IS NULL THEN 'unknown'
        WHEN cs.complexity_score <= 5 THEN 'simple'
        WHEN cs.complexity_score <= 10 THEN 'moderate'
        WHEN cs.complexity_score <= 20 THEN 'complex'
        ELSE 'very_complex'
    END as complexity_level
FROM code_symbols cs
JOIN code_files cf ON cs.file_id = cf.id
JOIN codebases c ON cs.codebase_id = c.id
WHERE cf.deleted_at IS NULL
AND c.deleted_at IS NULL;

-- Dependency analysis view
CREATE VIEW dependency_analysis AS
SELECT 
    ed.*,
    c.name as codebase_name,
    CASE 
        WHEN ed.has_vulnerabilities THEN 'vulnerable'
        WHEN ed.last_checked_at < NOW() - INTERVAL '30 days' THEN 'needs_check'
        ELSE 'safe'
    END as security_status,
    CASE 
        WHEN ed.import_count = 0 THEN 'unused'
        WHEN ed.import_count <= 3 THEN 'low_usage'
        WHEN ed.import_count <= 10 THEN 'medium_usage'
        ELSE 'high_usage'
    END as usage_level
FROM external_dependencies ed
JOIN codebases c ON ed.codebase_id = c.id
WHERE c.deleted_at IS NULL;

-- =====================================================
-- FUNCTIONS FOR ANALYSIS
-- =====================================================

-- Function to calculate codebase health score
CREATE OR REPLACE FUNCTION calculate_codebase_health_score(codebase_id BIGINT)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    health_score DECIMAL(5,2) := 100.0;
    metrics RECORD;
    vulnerability_penalty DECIMAL(5,2);
    complexity_penalty DECIMAL(5,2);
    coverage_bonus DECIMAL(5,2);
BEGIN
    -- Get latest metrics
    SELECT * INTO metrics
    FROM codebase_quality_metrics
    WHERE codebase_quality_metrics.codebase_id = calculate_codebase_health_score.codebase_id
    ORDER BY metric_date DESC
    LIMIT 1;
    
    IF metrics IS NULL THEN
        RETURN NULL; -- No metrics available
    END IF;
    
    -- Penalty for security issues
    vulnerability_penalty := LEAST(metrics.security_issues * 5.0, 30.0);
    health_score := health_score - vulnerability_penalty;
    
    -- Penalty for high complexity
    IF metrics.average_complexity > 20 THEN
        complexity_penalty := LEAST((metrics.average_complexity - 20) * 2.0, 25.0);
        health_score := health_score - complexity_penalty;
    END IF;
    
    -- Penalty for syntax errors
    health_score := health_score - LEAST(metrics.syntax_errors * 2.0, 20.0);
    
    -- Penalty for lint warnings
    health_score := health_score - LEAST(metrics.lint_warnings * 0.1, 10.0);
    
    -- Bonus for test coverage
    IF metrics.test_coverage_percentage IS NOT NULL THEN
        coverage_bonus := metrics.test_coverage_percentage * 0.2;
        health_score := health_score + LEAST(coverage_bonus, 20.0);
    END IF;
    
    -- Ensure score is within bounds
    RETURN GREATEST(0.0, LEAST(100.0, health_score));
END;
$$ LANGUAGE plpgsql;

-- Function to find circular dependencies
CREATE OR REPLACE FUNCTION find_circular_dependencies(codebase_id BIGINT)
RETURNS TABLE(
    cycle_path TEXT,
    cycle_length INTEGER
) AS $$
WITH RECURSIVE dependency_paths AS (
    -- Start with all direct dependencies
    SELECT 
        cr.source_id,
        cr.target_id,
        ARRAY[cr.source_id] as path,
        1 as depth
    FROM code_relationships cr
    WHERE cr.codebase_id = find_circular_dependencies.codebase_id
    AND cr.relationship_type IN ('imports', 'uses', 'calls')
    
    UNION ALL
    
    -- Follow the dependency chain
    SELECT 
        dp.source_id,
        cr.target_id,
        dp.path || cr.source_id,
        dp.depth + 1
    FROM dependency_paths dp
    JOIN code_relationships cr ON dp.target_id = cr.source_id
    WHERE cr.codebase_id = find_circular_dependencies.codebase_id
    AND cr.relationship_type IN ('imports', 'uses', 'calls')
    AND dp.depth < 50 -- Prevent infinite recursion
    AND NOT cr.source_id = ANY(dp.path) -- Prevent immediate cycles
)
SELECT 
    array_to_string(dp.path || dp.target_id, ' -> ') as cycle_path,
    dp.depth + 1 as cycle_length
FROM dependency_paths dp
WHERE dp.target_id = dp.source_id -- Found a cycle
ORDER BY dp.depth;
$$ LANGUAGE SQL;

-- =====================================================
-- SAMPLE DATA AND INITIALIZATION
-- =====================================================

-- Insert sample analysis configurations
INSERT INTO codebase_analysis_sessions (codebase_id, analysis_type, trigger_type, status, triggered_by) VALUES
(1, 'full', 'manual', 'completed', 1),
(1, 'incremental', 'scheduled', 'completed', 1);

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE codebases IS 'Core codebase metadata and configuration for repository analysis';
COMMENT ON TABLE code_files IS 'Individual file tracking with analysis results and metrics';
COMMENT ON TABLE code_symbols IS 'Functions, classes, and other code symbols with their metadata';
COMMENT ON TABLE code_relationships IS 'Dependencies and relationships between code elements';
COMMENT ON TABLE codebase_analysis_sessions IS 'Tracking of analysis runs and their results';
COMMENT ON TABLE codebase_quality_metrics IS 'Daily aggregated quality metrics for codebases';
COMMENT ON TABLE code_hotspots IS 'Files identified as problematic or high-risk areas';
COMMENT ON TABLE external_dependencies IS 'External packages and dependencies used by codebases';

COMMENT ON COLUMN codebases.health_score IS 'Overall codebase health score from 0-100 based on various quality metrics';
COMMENT ON COLUMN code_files.complexity_score IS 'Cyclomatic complexity or similar complexity metric for the file';
COMMENT ON COLUMN code_symbols.qualified_name IS 'Fully qualified symbol name including namespace/module path';
COMMENT ON COLUMN code_relationships.relationship_strength IS 'Strength of relationship from 0-1, higher values indicate stronger coupling';

