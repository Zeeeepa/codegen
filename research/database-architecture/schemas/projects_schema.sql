-- =====================================================
-- PROJECTS SCHEMA - Project and Workflow Management
-- =====================================================
-- This schema supports comprehensive project management including:
-- - Project lifecycle and metadata management
-- - Team collaboration and resource allocation
-- - Workflow definition and execution
-- - Project analytics and reporting
-- - Integration with tasks and codebases
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- CORE PROJECT TABLES
-- =====================================================

-- Projects table - Core project management
CREATE TABLE projects (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Project identification
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100), -- URL-friendly identifier
    display_name VARCHAR(255),
    description TEXT,
    
    -- Project classification
    project_type VARCHAR(50) DEFAULT 'general', -- 'general', 'software', 'research', 'maintenance'
    category VARCHAR(100), -- Custom categorization
    priority INTEGER DEFAULT 0, -- Project priority (0-100)
    
    -- Project status and lifecycle
    status VARCHAR(50) NOT NULL DEFAULT 'planning', -- 'planning', 'active', 'on_hold', 'completed', 'cancelled', 'archived'
    phase VARCHAR(50), -- Current project phase
    health_status VARCHAR(20) DEFAULT 'healthy', -- 'healthy', 'at_risk', 'critical'
    
    -- Project ownership and team
    owner_id BIGINT NOT NULL, -- Project owner/manager
    lead_id BIGINT, -- Technical lead
    sponsor_id BIGINT, -- Project sponsor
    
    -- Project timeline
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    
    -- Budget and resources
    budget_allocated DECIMAL(15,2),
    budget_spent DECIMAL(15,2),
    estimated_hours DECIMAL(10,2),
    actual_hours DECIMAL(10,2),
    
    -- Project metrics
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    task_count INTEGER DEFAULT 0,
    completed_task_count INTEGER DEFAULT 0,
    
    -- Project configuration
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    tags TEXT[],
    labels JSONB DEFAULT '[]',
    
    -- External integrations
    external_ids JSONB DEFAULT '{}', -- IDs in external systems (Linear, Jira, etc.)
    integration_settings JSONB DEFAULT '{}',
    
    -- Audit fields
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT projects_priority_range CHECK (priority >= 0 AND priority <= 100),
    CONSTRAINT projects_completion_range CHECK (completion_percentage >= 0 AND completion_percentage <= 100),
    CONSTRAINT projects_budget_positive CHECK (budget_allocated >= 0 AND budget_spent >= 0),
    CONSTRAINT projects_hours_positive CHECK (estimated_hours >= 0 AND actual_hours >= 0),
    CONSTRAINT projects_dates_logical CHECK (
        (planned_end_date IS NULL OR planned_start_date IS NULL OR planned_end_date >= planned_start_date) AND
        (actual_end_date IS NULL OR actual_start_date IS NULL OR actual_end_date >= actual_start_date)
    )
);

-- Project teams - Team membership and roles
CREATE TABLE project_teams (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    
    -- Role and permissions
    role VARCHAR(50) NOT NULL DEFAULT 'member', -- 'owner', 'lead', 'member', 'contributor', 'viewer'
    permissions JSONB DEFAULT '[]', -- Specific permissions
    
    -- Allocation and capacity
    allocation_percentage DECIMAL(5,2) DEFAULT 100.00, -- % of time allocated to project
    hourly_rate DECIMAL(10,2), -- Billing rate if applicable
    
    -- Membership timeline
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    left_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    added_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(project_id, user_id, joined_at),
    CONSTRAINT project_teams_allocation_range CHECK (allocation_percentage >= 0 AND allocation_percentage <= 100),
    CONSTRAINT project_teams_rate_positive CHECK (hourly_rate >= 0)
);

-- Project milestones - Key project checkpoints
CREATE TABLE project_milestones (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Milestone identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    milestone_type VARCHAR(50) DEFAULT 'general', -- 'general', 'release', 'deadline', 'review'
    
    -- Milestone status
    status VARCHAR(50) DEFAULT 'planned', -- 'planned', 'in_progress', 'completed', 'missed', 'cancelled'
    priority INTEGER DEFAULT 0,
    
    -- Milestone timeline
    planned_date DATE,
    actual_date DATE,
    
    -- Milestone criteria
    completion_criteria JSONB DEFAULT '[]', -- List of criteria for completion
    deliverables JSONB DEFAULT '[]', -- Expected deliverables
    
    -- Dependencies
    depends_on_milestone_ids BIGINT[], -- Array of milestone IDs this depends on
    
    -- Metrics
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT project_milestones_priority_range CHECK (priority >= 0 AND priority <= 100),
    CONSTRAINT project_milestones_completion_range CHECK (completion_percentage >= 0 AND completion_percentage <= 100)
);

-- =====================================================
-- WORKFLOW MANAGEMENT
-- =====================================================

-- Workflows table - Workflow definitions
CREATE TABLE workflows (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    project_id BIGINT REFERENCES projects(id) ON DELETE SET NULL,
    
    -- Workflow identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_type VARCHAR(50) DEFAULT 'general', -- 'general', 'ci_cd', 'approval', 'automation'
    
    -- Workflow definition
    definition JSONB NOT NULL, -- Workflow steps and configuration
    version VARCHAR(20) DEFAULT '1.0',
    
    -- Workflow status
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- 'draft', 'active', 'inactive', 'deprecated'
    is_template BOOLEAN DEFAULT false,
    
    -- Workflow configuration
    trigger_conditions JSONB DEFAULT '{}', -- When to trigger workflow
    input_schema JSONB DEFAULT '{}', -- Expected input format
    output_schema JSONB DEFAULT '{}', -- Expected output format
    
    -- Execution settings
    timeout_minutes INTEGER DEFAULT 60,
    retry_count INTEGER DEFAULT 0,
    parallel_execution BOOLEAN DEFAULT false,
    
    -- Usage tracking
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT workflows_timeout_positive CHECK (timeout_minutes > 0),
    CONSTRAINT workflows_retry_positive CHECK (retry_count >= 0)
);

-- Workflow executions - Workflow run instances
CREATE TABLE workflow_executions (
    id BIGSERIAL PRIMARY KEY,
    workflow_id BIGINT NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    organization_id BIGINT NOT NULL,
    project_id BIGINT,
    
    -- Execution identification
    execution_id UUID DEFAULT uuid_generate_v4(),
    parent_execution_id BIGINT REFERENCES workflow_executions(id) ON DELETE SET NULL,
    
    -- Execution context
    triggered_by VARCHAR(50) NOT NULL, -- 'user', 'schedule', 'webhook', 'event', 'api'
    triggered_by_user_id BIGINT,
    trigger_data JSONB DEFAULT '{}',
    
    -- Execution status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled', 'timeout'
    current_step VARCHAR(255),
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    
    -- Execution data
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    execution_log JSONB DEFAULT '[]', -- Step-by-step execution log
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    retry_attempt INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT workflow_executions_progress_range CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT workflow_executions_retry_positive CHECK (retry_attempt >= 0)
);

-- Workflow steps - Individual workflow step executions
CREATE TABLE workflow_step_executions (
    id BIGSERIAL PRIMARY KEY,
    execution_id BIGINT NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    
    -- Step identification
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(50) NOT NULL, -- 'action', 'condition', 'loop', 'parallel', 'human'
    step_order INTEGER NOT NULL,
    
    -- Step status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'skipped'
    
    -- Step data
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    configuration JSONB DEFAULT '{}',
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    retry_attempt INTEGER DEFAULT 0,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT workflow_step_executions_order_positive CHECK (step_order >= 0),
    CONSTRAINT workflow_step_executions_retry_positive CHECK (retry_attempt >= 0)
);

-- =====================================================
-- PROJECT ANALYTICS AND REPORTING
-- =====================================================

-- Project metrics (daily aggregates)
CREATE TABLE project_metrics (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Task metrics
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    in_progress_tasks INTEGER DEFAULT 0,
    blocked_tasks INTEGER DEFAULT 0,
    overdue_tasks INTEGER DEFAULT 0,
    
    -- Time metrics
    planned_hours DECIMAL(10,2) DEFAULT 0,
    actual_hours DECIMAL(10,2) DEFAULT 0,
    remaining_hours DECIMAL(10,2) DEFAULT 0,
    
    -- Team metrics
    active_team_members INTEGER DEFAULT 0,
    total_team_members INTEGER DEFAULT 0,
    
    -- Quality metrics
    bugs_found INTEGER DEFAULT 0,
    bugs_fixed INTEGER DEFAULT 0,
    code_reviews_completed INTEGER DEFAULT 0,
    
    -- Velocity metrics
    story_points_completed DECIMAL(10,2) DEFAULT 0,
    velocity_trend DECIMAL(10,2), -- Moving average velocity
    
    -- Budget metrics
    budget_spent_today DECIMAL(15,2) DEFAULT 0,
    budget_remaining DECIMAL(15,2),
    
    -- Health indicators
    health_score DECIMAL(5,2), -- Overall project health (0-100)
    risk_level VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    
    -- Calculated metrics
    completion_percentage DECIMAL(5,2),
    schedule_variance_days INTEGER, -- Positive = ahead, negative = behind
    budget_variance_percentage DECIMAL(5,2),
    
    -- Audit
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(project_id, metric_date)
);

-- Project reports - Generated reports and dashboards
CREATE TABLE project_reports (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Report identification
    report_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- 'status', 'performance', 'budget', 'risk', 'custom'
    
    -- Report configuration
    report_config JSONB DEFAULT '{}',
    filters JSONB DEFAULT '{}',
    
    -- Report data
    report_data JSONB NOT NULL,
    summary JSONB DEFAULT '{}',
    
    -- Report metadata
    period_start DATE,
    period_end DATE,
    generated_for_user_id BIGINT,
    
    -- Report status
    status VARCHAR(50) DEFAULT 'generated', -- 'generated', 'shared', 'archived'
    is_scheduled BOOLEAN DEFAULT false,
    schedule_config JSONB DEFAULT '{}',
    
    -- Audit
    generated_by BIGINT NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT project_reports_period_logical CHECK (
        period_end IS NULL OR period_start IS NULL OR period_end >= period_start
    )
);

-- =====================================================
-- PROJECT TEMPLATES AND STANDARDS
-- =====================================================

-- Project templates - Reusable project structures
CREATE TABLE project_templates (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) DEFAULT 'general',
    
    -- Template configuration
    template_data JSONB NOT NULL, -- Project structure and defaults
    task_templates JSONB DEFAULT '[]', -- Default tasks to create
    milestone_templates JSONB DEFAULT '[]', -- Default milestones
    workflow_templates JSONB DEFAULT '[]', -- Default workflows
    
    -- Template settings
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false, -- Available to all organizations
    usage_count INTEGER DEFAULT 0,
    
    -- Template metadata
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Project indexes
CREATE INDEX idx_projects_organization_status ON projects(organization_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_owner ON projects(owner_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_dates ON projects(planned_start_date, planned_end_date) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_priority ON projects(priority DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_health ON projects(health_status) WHERE deleted_at IS NULL;

-- Team indexes
CREATE INDEX idx_project_teams_project ON project_teams(project_id) WHERE left_at IS NULL;
CREATE INDEX idx_project_teams_user ON project_teams(user_id) WHERE left_at IS NULL;
CREATE INDEX idx_project_teams_role ON project_teams(project_id, role) WHERE left_at IS NULL;

-- Milestone indexes
CREATE INDEX idx_project_milestones_project_status ON project_milestones(project_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_project_milestones_dates ON project_milestones(planned_date, actual_date) WHERE deleted_at IS NULL;

-- Workflow indexes
CREATE INDEX idx_workflows_organization_status ON workflows(organization_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_workflows_project ON workflows(project_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_workflows_type ON workflows(workflow_type) WHERE deleted_at IS NULL;

-- Execution indexes
CREATE INDEX idx_workflow_executions_workflow_status ON workflow_executions(workflow_id, status);
CREATE INDEX idx_workflow_executions_triggered_by ON workflow_executions(triggered_by_user_id, created_at);
CREATE INDEX idx_workflow_executions_project ON workflow_executions(project_id, created_at);

-- Step execution indexes
CREATE INDEX idx_workflow_step_executions_execution ON workflow_step_executions(execution_id, step_order);
CREATE INDEX idx_workflow_step_executions_status ON workflow_step_executions(status, created_at);

-- Metrics indexes
CREATE INDEX idx_project_metrics_project_date ON project_metrics(project_id, metric_date);
CREATE INDEX idx_project_metrics_date ON project_metrics(metric_date);

-- JSON indexes for metadata queries
CREATE INDEX idx_projects_metadata_gin ON projects USING gin(metadata) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_settings_gin ON projects USING gin(settings) WHERE deleted_at IS NULL;
CREATE INDEX idx_workflows_definition_gin ON workflows USING gin(definition) WHERE deleted_at IS NULL;

-- Full-text search indexes
CREATE INDEX idx_projects_name_search ON projects USING gin(to_tsvector('english', name)) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_description_search ON projects USING gin(to_tsvector('english', description)) WHERE deleted_at IS NULL;

-- =====================================================
-- TRIGGERS FOR AUTOMATION
-- =====================================================

-- Update updated_at timestamp
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_teams_updated_at BEFORE UPDATE ON project_teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_milestones_updated_at BEFORE UPDATE ON project_milestones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update project metrics when tasks change
CREATE OR REPLACE FUNCTION update_project_task_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update project task counts when tasks are added/updated/deleted
    UPDATE projects SET
        task_count = (
            SELECT COUNT(*) 
            FROM tasks 
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id) 
            AND deleted_at IS NULL
        ),
        completed_task_count = (
            SELECT COUNT(*) 
            FROM tasks 
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id) 
            AND status = 'completed'
            AND deleted_at IS NULL
        ),
        completion_percentage = (
            SELECT CASE 
                WHEN COUNT(*) = 0 THEN 0
                ELSE (COUNT(*) FILTER (WHERE status = 'completed')::DECIMAL / COUNT(*)) * 100
            END
            FROM tasks 
            WHERE project_id = COALESCE(NEW.project_id, OLD.project_id) 
            AND deleted_at IS NULL
        ),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.project_id, OLD.project_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ language 'plpgsql';

-- Note: This trigger would be created after the tasks table exists
-- CREATE TRIGGER update_project_metrics_on_task_change 
--     AFTER INSERT OR UPDATE OR DELETE ON tasks
--     FOR EACH ROW EXECUTE FUNCTION update_project_task_metrics();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Active projects with team and metrics
CREATE VIEW active_projects_overview AS
SELECT 
    p.*,
    u_owner.name as owner_name,
    u_lead.name as lead_name,
    team_stats.team_size,
    team_stats.active_members,
    pm.health_score,
    pm.completion_percentage as current_completion,
    pm.schedule_variance_days,
    pm.budget_variance_percentage,
    CASE 
        WHEN p.planned_end_date IS NULL THEN NULL
        WHEN p.planned_end_date < CURRENT_DATE AND p.status != 'completed' THEN 'overdue'
        WHEN p.planned_end_date <= CURRENT_DATE + INTERVAL '7 days' THEN 'due_soon'
        ELSE 'on_track'
    END as schedule_status
FROM projects p
LEFT JOIN users u_owner ON p.owner_id = u_owner.id
LEFT JOIN users u_lead ON p.lead_id = u_lead.id
LEFT JOIN (
    SELECT 
        project_id,
        COUNT(*) as team_size,
        COUNT(*) FILTER (WHERE left_at IS NULL) as active_members
    FROM project_teams
    GROUP BY project_id
) team_stats ON p.id = team_stats.project_id
LEFT JOIN project_metrics pm ON p.id = pm.project_id AND pm.metric_date = CURRENT_DATE
WHERE p.deleted_at IS NULL
AND p.status IN ('planning', 'active');

-- Project timeline view
CREATE VIEW project_timeline AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    'project' as item_type,
    p.name as item_name,
    p.planned_start_date as start_date,
    p.planned_end_date as end_date,
    p.status,
    NULL as milestone_id
FROM projects p
WHERE p.deleted_at IS NULL

UNION ALL

SELECT 
    pm.project_id,
    p.name as project_name,
    'milestone' as item_type,
    pm.name as item_name,
    pm.planned_date as start_date,
    pm.planned_date as end_date,
    pm.status,
    pm.id as milestone_id
FROM project_milestones pm
JOIN projects p ON pm.project_id = p.id
WHERE pm.deleted_at IS NULL
AND p.deleted_at IS NULL

ORDER BY project_id, start_date;

-- Workflow execution summary
CREATE VIEW workflow_execution_summary AS
SELECT 
    w.id as workflow_id,
    w.name as workflow_name,
    w.workflow_type,
    COUNT(we.id) as total_executions,
    COUNT(we.id) FILTER (WHERE we.status = 'completed') as successful_executions,
    COUNT(we.id) FILTER (WHERE we.status = 'failed') as failed_executions,
    COUNT(we.id) FILTER (WHERE we.status IN ('pending', 'running')) as active_executions,
    AVG(we.duration_seconds) FILTER (WHERE we.status = 'completed') as avg_duration_seconds,
    MAX(we.created_at) as last_execution_at,
    CASE 
        WHEN COUNT(we.id) = 0 THEN 0
        ELSE (COUNT(we.id) FILTER (WHERE we.status = 'completed')::DECIMAL / COUNT(we.id)) * 100
    END as success_rate_percentage
FROM workflows w
LEFT JOIN workflow_executions we ON w.id = we.workflow_id
WHERE w.deleted_at IS NULL
GROUP BY w.id, w.name, w.workflow_type;

-- =====================================================
-- FUNCTIONS FOR PROJECT MANAGEMENT
-- =====================================================

-- Function to calculate project health score
CREATE OR REPLACE FUNCTION calculate_project_health_score(project_id BIGINT)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    health_score DECIMAL(5,2) := 100.0;
    project_data RECORD;
    metrics RECORD;
    schedule_penalty DECIMAL(5,2);
    budget_penalty DECIMAL(5,2);
    task_penalty DECIMAL(5,2);
BEGIN
    -- Get project data
    SELECT * INTO project_data
    FROM projects
    WHERE id = project_id AND deleted_at IS NULL;
    
    IF project_data IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Get latest metrics
    SELECT * INTO metrics
    FROM project_metrics
    WHERE project_metrics.project_id = calculate_project_health_score.project_id
    ORDER BY metric_date DESC
    LIMIT 1;
    
    IF metrics IS NULL THEN
        RETURN 50.0; -- Default score if no metrics
    END IF;
    
    -- Schedule variance penalty
    IF metrics.schedule_variance_days < 0 THEN
        schedule_penalty := LEAST(ABS(metrics.schedule_variance_days) * 2.0, 30.0);
        health_score := health_score - schedule_penalty;
    END IF;
    
    -- Budget variance penalty
    IF metrics.budget_variance_percentage < 0 THEN
        budget_penalty := LEAST(ABS(metrics.budget_variance_percentage) * 0.5, 25.0);
        health_score := health_score - budget_penalty;
    END IF;
    
    -- Task completion penalty
    IF metrics.total_tasks > 0 THEN
        task_penalty := (1.0 - (metrics.completed_tasks::DECIMAL / metrics.total_tasks)) * 20.0;
        health_score := health_score - task_penalty;
    END IF;
    
    -- Blocked tasks penalty
    IF metrics.blocked_tasks > 0 THEN
        health_score := health_score - LEAST(metrics.blocked_tasks * 3.0, 15.0);
    END IF;
    
    -- Overdue tasks penalty
    IF metrics.overdue_tasks > 0 THEN
        health_score := health_score - LEAST(metrics.overdue_tasks * 5.0, 20.0);
    END IF;
    
    -- Ensure score is within bounds
    RETURN GREATEST(0.0, LEAST(100.0, health_score));
END;
$$ LANGUAGE plpgsql;

-- Function to get project dependencies
CREATE OR REPLACE FUNCTION get_project_dependencies(project_id BIGINT)
RETURNS TABLE(
    dependency_type VARCHAR(50),
    dependency_name VARCHAR(255),
    dependency_status VARCHAR(50),
    blocking_factor DECIMAL(5,2)
) AS $$
BEGIN
    -- Get task dependencies that might block the project
    RETURN QUERY
    SELECT 
        'task_dependency'::VARCHAR(50) as dependency_type,
        t.title as dependency_name,
        t.status as dependency_status,
        CASE 
            WHEN t.status = 'completed' THEN 0.0
            WHEN t.status = 'blocked' THEN 100.0
            WHEN t.priority > 80 THEN 75.0
            ELSE 25.0
        END as blocking_factor
    FROM tasks t
    JOIN task_dependencies td ON t.id = td.depends_on_task_id
    JOIN tasks dependent_task ON td.task_id = dependent_task.id
    WHERE dependent_task.project_id = get_project_dependencies.project_id
    AND t.status != 'completed'
    AND t.deleted_at IS NULL
    AND dependent_task.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SAMPLE DATA AND INITIALIZATION
-- =====================================================

-- Insert sample project templates
INSERT INTO project_templates (organization_id, name, description, template_data, created_by) VALUES
(1, 'Software Development Project', 'Standard template for software development projects',
 '{"phases": ["planning", "development", "testing", "deployment"], "default_workflows": ["ci_cd", "code_review"]}', 1),
(1, 'Research Project', 'Template for research and analysis projects',
 '{"phases": ["research", "analysis", "documentation", "presentation"], "default_milestones": ["research_complete", "analysis_complete"]}', 1);

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE projects IS 'Core project management table supporting comprehensive project lifecycle management';
COMMENT ON TABLE project_teams IS 'Project team membership with roles and allocation tracking';
COMMENT ON TABLE project_milestones IS 'Project milestones and key checkpoints with dependencies';
COMMENT ON TABLE workflows IS 'Workflow definitions for project automation and process management';
COMMENT ON TABLE workflow_executions IS 'Individual workflow execution instances with status tracking';
COMMENT ON TABLE workflow_step_executions IS 'Individual workflow step executions for detailed tracking';
COMMENT ON TABLE project_metrics IS 'Daily aggregated project metrics for performance analysis';
COMMENT ON TABLE project_reports IS 'Generated project reports and dashboard data';
COMMENT ON TABLE project_templates IS 'Reusable project templates for standardization';

COMMENT ON COLUMN projects.health_status IS 'Overall project health: healthy, at_risk, or critical';
COMMENT ON COLUMN projects.completion_percentage IS 'Project completion percentage based on tasks and milestones';
COMMENT ON COLUMN project_teams.allocation_percentage IS 'Percentage of team member time allocated to this project';
COMMENT ON COLUMN workflows.definition IS 'JSON workflow definition including steps, conditions, and actions';
COMMENT ON COLUMN project_metrics.health_score IS 'Calculated project health score from 0-100 based on various factors';

