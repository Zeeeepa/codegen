-- =====================================================
-- ANALYTICS SCHEMA - Performance Metrics and Analytics
-- =====================================================
-- This schema supports comprehensive analytics including:
-- - Performance metrics aggregation
-- - Trend analysis and reporting
-- - Cross-system correlation analysis
-- - Real-time dashboards and KPIs
-- - Predictive analytics support
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- ANALYTICS AGGREGATION TABLES
-- =====================================================

-- Daily analytics aggregates
CREATE TABLE daily_analytics (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    metric_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Task metrics
    tasks_created INTEGER DEFAULT 0,
    tasks_completed INTEGER DEFAULT 0,
    tasks_in_progress INTEGER DEFAULT 0,
    tasks_blocked INTEGER DEFAULT 0,
    avg_task_completion_time_hours DECIMAL(10,2),
    
    -- Project metrics
    projects_active INTEGER DEFAULT 0,
    projects_completed INTEGER DEFAULT 0,
    avg_project_health_score DECIMAL(5,2),
    
    -- Code metrics
    commits_count INTEGER DEFAULT 0,
    pull_requests_opened INTEGER DEFAULT 0,
    pull_requests_merged INTEGER DEFAULT 0,
    code_reviews_completed INTEGER DEFAULT 0,
    
    -- Event metrics
    total_events INTEGER DEFAULT 0,
    linear_events INTEGER DEFAULT 0,
    github_events INTEGER DEFAULT 0,
    slack_events INTEGER DEFAULT 0,
    deployment_events INTEGER DEFAULT 0,
    
    -- User activity metrics
    active_users INTEGER DEFAULT 0,
    total_user_sessions INTEGER DEFAULT 0,
    avg_session_duration_minutes DECIMAL(10,2),
    
    -- Quality metrics
    bugs_found INTEGER DEFAULT 0,
    bugs_fixed INTEGER DEFAULT 0,
    security_issues INTEGER DEFAULT 0,
    test_coverage_percentage DECIMAL(5,2),
    
    -- Performance metrics
    avg_response_time_ms DECIMAL(10,2),
    error_rate_percentage DECIMAL(5,2),
    system_uptime_percentage DECIMAL(5,2),
    
    -- Calculated at end of day
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, metric_date)
);

-- Weekly analytics aggregates
CREATE TABLE weekly_analytics (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    
    -- Aggregated metrics from daily data
    total_tasks_created INTEGER DEFAULT 0,
    total_tasks_completed INTEGER DEFAULT 0,
    task_completion_rate DECIMAL(5,2),
    avg_task_cycle_time_hours DECIMAL(10,2),
    
    -- Project progress
    projects_started INTEGER DEFAULT 0,
    projects_completed INTEGER DEFAULT 0,
    avg_project_velocity DECIMAL(10,2),
    
    -- Code activity
    total_commits INTEGER DEFAULT 0,
    total_pull_requests INTEGER DEFAULT 0,
    code_review_turnaround_hours DECIMAL(10,2),
    
    -- Team productivity
    team_velocity DECIMAL(10,2),
    collaboration_score DECIMAL(5,2),
    knowledge_sharing_events INTEGER DEFAULT 0,
    
    -- Quality trends
    defect_density DECIMAL(10,4),
    technical_debt_hours DECIMAL(10,2),
    code_quality_score DECIMAL(5,2),
    
    -- Calculated weekly
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, week_start_date)
);

-- Monthly analytics aggregates
CREATE TABLE monthly_analytics (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    month_year VARCHAR(7) NOT NULL, -- YYYY-MM format
    month_start_date DATE NOT NULL,
    month_end_date DATE NOT NULL,
    
    -- Strategic metrics
    objectives_completed INTEGER DEFAULT 0,
    milestones_achieved INTEGER DEFAULT 0,
    roi_percentage DECIMAL(10,4),
    
    -- Resource utilization
    team_utilization_percentage DECIMAL(5,2),
    budget_utilization_percentage DECIMAL(5,2),
    infrastructure_costs DECIMAL(15,2),
    
    -- Growth metrics
    user_growth_percentage DECIMAL(10,4),
    feature_adoption_rate DECIMAL(5,2),
    customer_satisfaction_score DECIMAL(5,2),
    
    -- Innovation metrics
    experiments_conducted INTEGER DEFAULT 0,
    successful_experiments INTEGER DEFAULT 0,
    time_to_market_days DECIMAL(10,2),
    
    -- Risk and compliance
    security_incidents INTEGER DEFAULT 0,
    compliance_score DECIMAL(5,2),
    risk_mitigation_effectiveness DECIMAL(5,2),
    
    -- Calculated monthly
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, month_year)
);

-- =====================================================
-- REAL-TIME ANALYTICS TABLES
-- =====================================================

-- Real-time metrics (updated frequently)
CREATE TABLE realtime_metrics (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20),
    
    -- Context
    context_type VARCHAR(50), -- 'global', 'project', 'team', 'user'
    context_id BIGINT,
    
    -- Metadata
    tags JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timing
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    INDEX(organization_id, metric_name, recorded_at),
    INDEX(context_type, context_id),
    INDEX(expires_at)
);

-- Performance monitoring metrics
CREATE TABLE performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Service identification
    service_name VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255),
    operation VARCHAR(100),
    
    -- Performance data
    response_time_ms DECIMAL(10,3) NOT NULL,
    throughput_rps DECIMAL(10,3), -- Requests per second
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    
    -- Resource utilization
    cpu_usage_percentage DECIMAL(5,2),
    memory_usage_mb DECIMAL(10,2),
    disk_io_mb DECIMAL(10,2),
    network_io_mb DECIMAL(10,2),
    
    -- User context
    user_id BIGINT,
    session_id VARCHAR(255),
    
    -- Timing
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX(organization_id, service_name, recorded_at),
    INDEX(endpoint, recorded_at),
    INDEX(user_id, recorded_at)
);

-- =====================================================
-- DASHBOARD AND REPORTING TABLES
-- =====================================================

-- Dashboard configurations
CREATE TABLE dashboards (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Dashboard identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dashboard_type VARCHAR(50) DEFAULT 'custom', -- 'executive', 'operational', 'analytical', 'custom'
    
    -- Dashboard configuration
    layout_config JSONB NOT NULL, -- Widget layout and configuration
    data_sources JSONB DEFAULT '[]', -- Data source configurations
    refresh_interval_seconds INTEGER DEFAULT 300,
    
    -- Access control
    is_public BOOLEAN DEFAULT false,
    allowed_roles JSONB DEFAULT '[]',
    allowed_users JSONB DEFAULT '[]',
    
    -- Dashboard metadata
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    
    -- Usage tracking
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(organization_id, name)
);

-- Dashboard widgets
CREATE TABLE dashboard_widgets (
    id BIGSERIAL PRIMARY KEY,
    dashboard_id BIGINT NOT NULL REFERENCES dashboards(id) ON DELETE CASCADE,
    
    -- Widget identification
    widget_name VARCHAR(255) NOT NULL,
    widget_type VARCHAR(50) NOT NULL, -- 'chart', 'metric', 'table', 'text', 'gauge'
    
    -- Widget configuration
    config JSONB NOT NULL, -- Widget-specific configuration
    data_query JSONB NOT NULL, -- Query configuration for data
    
    -- Layout
    position_x INTEGER NOT NULL,
    position_y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    
    -- Widget settings
    refresh_interval_seconds INTEGER DEFAULT 300,
    cache_duration_seconds INTEGER DEFAULT 60,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scheduled reports
CREATE TABLE scheduled_reports (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Report identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    report_type VARCHAR(50) NOT NULL, -- 'summary', 'detailed', 'executive', 'custom'
    
    -- Report configuration
    report_config JSONB NOT NULL,
    data_filters JSONB DEFAULT '{}',
    output_format VARCHAR(20) DEFAULT 'pdf', -- 'pdf', 'excel', 'csv', 'json'
    
    -- Scheduling
    schedule_cron VARCHAR(100) NOT NULL, -- Cron expression
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT true,
    
    -- Recipients
    email_recipients JSONB DEFAULT '[]',
    slack_channels JSONB DEFAULT '[]',
    
    -- Execution tracking
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    run_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Audit
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Report executions
CREATE TABLE report_executions (
    id BIGSERIAL PRIMARY KEY,
    scheduled_report_id BIGINT NOT NULL REFERENCES scheduled_reports(id) ON DELETE CASCADE,
    
    -- Execution details
    execution_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    
    -- Execution results
    output_file_path VARCHAR(1000),
    output_size_bytes BIGINT,
    record_count INTEGER,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    
    -- Delivery tracking
    delivery_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'sent', 'failed'
    delivery_attempts INTEGER DEFAULT 0
);

-- =====================================================
-- ANALYTICS FUNCTIONS AND CALCULATIONS
-- =====================================================

-- Metric calculations table
CREATE TABLE metric_calculations (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Calculation identification
    calculation_name VARCHAR(255) NOT NULL,
    calculation_type VARCHAR(50) NOT NULL, -- 'aggregation', 'trend', 'correlation', 'prediction'
    
    -- Calculation configuration
    source_tables JSONB NOT NULL, -- Tables and columns to use
    calculation_formula TEXT NOT NULL, -- SQL or formula
    parameters JSONB DEFAULT '{}',
    
    -- Scheduling
    calculation_frequency VARCHAR(50) DEFAULT 'daily', -- 'real_time', 'hourly', 'daily', 'weekly'
    last_calculated_at TIMESTAMP WITH TIME ZONE,
    next_calculation_at TIMESTAMP WITH TIME ZONE,
    
    -- Results storage
    result_table VARCHAR(100), -- Where to store results
    result_retention_days INTEGER DEFAULT 365,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    calculation_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Audit
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- TREND ANALYSIS TABLES
-- =====================================================

-- Trend analysis results
CREATE TABLE trend_analysis (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Trend identification
    metric_name VARCHAR(255) NOT NULL,
    trend_period VARCHAR(50) NOT NULL, -- 'daily', 'weekly', 'monthly', 'quarterly'
    analysis_date DATE NOT NULL,
    
    -- Trend data
    current_value DECIMAL(15,6),
    previous_value DECIMAL(15,6),
    change_amount DECIMAL(15,6),
    change_percentage DECIMAL(10,4),
    
    -- Trend analysis
    trend_direction VARCHAR(20), -- 'increasing', 'decreasing', 'stable', 'volatile'
    trend_strength DECIMAL(5,2), -- 0-100, strength of trend
    seasonality_detected BOOLEAN DEFAULT false,
    
    -- Statistical measures
    mean_value DECIMAL(15,6),
    median_value DECIMAL(15,6),
    standard_deviation DECIMAL(15,6),
    confidence_interval_lower DECIMAL(15,6),
    confidence_interval_upper DECIMAL(15,6),
    
    -- Predictions
    predicted_next_value DECIMAL(15,6),
    prediction_confidence DECIMAL(5,2),
    
    -- Context
    context_data JSONB DEFAULT '{}',
    
    -- Audit
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, metric_name, trend_period, analysis_date)
);

-- Correlation analysis
CREATE TABLE correlation_analysis (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Correlation identification
    metric_a VARCHAR(255) NOT NULL,
    metric_b VARCHAR(255) NOT NULL,
    analysis_period_start DATE NOT NULL,
    analysis_period_end DATE NOT NULL,
    
    -- Correlation results
    correlation_coefficient DECIMAL(10,6), -- -1 to 1
    correlation_strength VARCHAR(20), -- 'weak', 'moderate', 'strong'
    correlation_type VARCHAR(20), -- 'positive', 'negative', 'none'
    
    -- Statistical significance
    p_value DECIMAL(10,6),
    is_significant BOOLEAN,
    sample_size INTEGER,
    
    -- Additional analysis
    lag_correlation JSONB DEFAULT '{}', -- Time-lagged correlations
    causality_direction VARCHAR(50), -- 'a_causes_b', 'b_causes_a', 'bidirectional', 'none'
    
    -- Audit
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, metric_a, metric_b, analysis_period_start, analysis_period_end)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Daily analytics indexes
CREATE INDEX idx_daily_analytics_org_date ON daily_analytics(organization_id, metric_date);
CREATE INDEX idx_daily_analytics_date ON daily_analytics(metric_date);

-- Weekly analytics indexes
CREATE INDEX idx_weekly_analytics_org_week ON weekly_analytics(organization_id, week_start_date);

-- Monthly analytics indexes
CREATE INDEX idx_monthly_analytics_org_month ON monthly_analytics(organization_id, month_year);

-- Real-time metrics indexes
CREATE INDEX idx_realtime_metrics_org_name_time ON realtime_metrics(organization_id, metric_name, recorded_at);
CREATE INDEX idx_realtime_metrics_context ON realtime_metrics(context_type, context_id);
CREATE INDEX idx_realtime_metrics_expires ON realtime_metrics(expires_at);

-- Performance metrics indexes
CREATE INDEX idx_performance_metrics_service_time ON performance_metrics(service_name, recorded_at);
CREATE INDEX idx_performance_metrics_org_time ON performance_metrics(organization_id, recorded_at);
CREATE INDEX idx_performance_metrics_user ON performance_metrics(user_id, recorded_at);

-- Dashboard indexes
CREATE INDEX idx_dashboards_org_type ON dashboards(organization_id, dashboard_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_dashboard_widgets_dashboard ON dashboard_widgets(dashboard_id);

-- Report indexes
CREATE INDEX idx_scheduled_reports_org_active ON scheduled_reports(organization_id, is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_scheduled_reports_next_run ON scheduled_reports(next_run_at) WHERE is_active = true;
CREATE INDEX idx_report_executions_report_time ON report_executions(scheduled_report_id, started_at);

-- Trend analysis indexes
CREATE INDEX idx_trend_analysis_org_metric_date ON trend_analysis(organization_id, metric_name, analysis_date);
CREATE INDEX idx_correlation_analysis_org_metrics ON correlation_analysis(organization_id, metric_a, metric_b);

-- JSON indexes for configuration queries
CREATE INDEX idx_dashboards_layout_gin ON dashboards USING gin(layout_config) WHERE deleted_at IS NULL;
CREATE INDEX idx_realtime_metrics_tags_gin ON realtime_metrics USING gin(tags);

-- =====================================================
-- TRIGGERS FOR AUTOMATION
-- =====================================================

-- Update updated_at timestamp
CREATE TRIGGER update_dashboards_updated_at BEFORE UPDATE ON dashboards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dashboard_widgets_updated_at BEFORE UPDATE ON dashboard_widgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scheduled_reports_updated_at BEFORE UPDATE ON scheduled_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Clean up expired real-time metrics
CREATE OR REPLACE FUNCTION cleanup_expired_realtime_metrics()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM realtime_metrics 
    WHERE expires_at IS NOT NULL 
    AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS FOR COMMON ANALYTICS QUERIES
-- =====================================================

-- Current metrics overview
CREATE VIEW current_metrics_overview AS
SELECT 
    organization_id,
    metric_name,
    metric_value,
    metric_unit,
    context_type,
    context_id,
    recorded_at,
    ROW_NUMBER() OVER (PARTITION BY organization_id, metric_name, context_type, context_id ORDER BY recorded_at DESC) as rn
FROM realtime_metrics
WHERE expires_at IS NULL OR expires_at > NOW();

-- Latest daily analytics
CREATE VIEW latest_daily_analytics AS
SELECT 
    da.*,
    CASE 
        WHEN da.tasks_created > 0 THEN (da.tasks_completed::DECIMAL / da.tasks_created) * 100
        ELSE 0
    END as task_completion_rate,
    CASE 
        WHEN da.pull_requests_opened > 0 THEN (da.pull_requests_merged::DECIMAL / da.pull_requests_opened) * 100
        ELSE 0
    END as pr_merge_rate
FROM daily_analytics da
WHERE da.metric_date >= CURRENT_DATE - INTERVAL '30 days';

-- Performance summary view
CREATE VIEW performance_summary AS
SELECT 
    organization_id,
    service_name,
    DATE(recorded_at) as metric_date,
    COUNT(*) as request_count,
    AVG(response_time_ms) as avg_response_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time,
    SUM(error_count) as total_errors,
    SUM(success_count) as total_successes,
    CASE 
        WHEN SUM(error_count + success_count) > 0 
        THEN (SUM(error_count)::DECIMAL / SUM(error_count + success_count)) * 100
        ELSE 0
    END as error_rate_percentage
FROM performance_metrics
WHERE recorded_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY organization_id, service_name, DATE(recorded_at);

-- Trend summary view
CREATE VIEW trend_summary AS
SELECT 
    ta.*,
    CASE 
        WHEN ta.trend_direction = 'increasing' AND ta.change_percentage > 10 THEN 'significant_improvement'
        WHEN ta.trend_direction = 'increasing' AND ta.change_percentage > 0 THEN 'improvement'
        WHEN ta.trend_direction = 'stable' THEN 'stable'
        WHEN ta.trend_direction = 'decreasing' AND ta.change_percentage < -10 THEN 'significant_decline'
        WHEN ta.trend_direction = 'decreasing' AND ta.change_percentage < 0 THEN 'decline'
        ELSE 'unknown'
    END as trend_category,
    CASE 
        WHEN ta.trend_strength >= 80 THEN 'very_strong'
        WHEN ta.trend_strength >= 60 THEN 'strong'
        WHEN ta.trend_strength >= 40 THEN 'moderate'
        WHEN ta.trend_strength >= 20 THEN 'weak'
        ELSE 'very_weak'
    END as strength_category
FROM trend_analysis ta
WHERE ta.analysis_date >= CURRENT_DATE - INTERVAL '90 days';

-- =====================================================
-- FUNCTIONS FOR ANALYTICS CALCULATIONS
-- =====================================================

-- Function to calculate daily analytics
CREATE OR REPLACE FUNCTION calculate_daily_analytics(
    target_organization_id BIGINT,
    target_date DATE DEFAULT CURRENT_DATE
)
RETURNS BOOLEAN AS $$
DECLARE
    analytics_record daily_analytics%ROWTYPE;
BEGIN
    -- Initialize record
    analytics_record.organization_id := target_organization_id;
    analytics_record.metric_date := target_date;
    
    -- Calculate task metrics
    SELECT 
        COUNT(*) FILTER (WHERE DATE(created_at) = target_date),
        COUNT(*) FILTER (WHERE DATE(completed_at) = target_date),
        COUNT(*) FILTER (WHERE status = 'in_progress' AND DATE(created_at) <= target_date),
        COUNT(*) FILTER (WHERE status = 'blocked' AND DATE(created_at) <= target_date),
        AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 3600) FILTER (WHERE DATE(completed_at) = target_date)
    INTO 
        analytics_record.tasks_created,
        analytics_record.tasks_completed,
        analytics_record.tasks_in_progress,
        analytics_record.tasks_blocked,
        analytics_record.avg_task_completion_time_hours
    FROM tasks 
    WHERE organization_id = target_organization_id
    AND deleted_at IS NULL;
    
    -- Insert or update the record
    INSERT INTO daily_analytics (
        organization_id, metric_date, tasks_created, tasks_completed, 
        tasks_in_progress, tasks_blocked, avg_task_completion_time_hours
    ) VALUES (
        analytics_record.organization_id, analytics_record.metric_date,
        analytics_record.tasks_created, analytics_record.tasks_completed,
        analytics_record.tasks_in_progress, analytics_record.tasks_blocked,
        analytics_record.avg_task_completion_time_hours
    )
    ON CONFLICT (organization_id, metric_date) 
    DO UPDATE SET
        tasks_created = EXCLUDED.tasks_created,
        tasks_completed = EXCLUDED.tasks_completed,
        tasks_in_progress = EXCLUDED.tasks_in_progress,
        tasks_blocked = EXCLUDED.tasks_blocked,
        avg_task_completion_time_hours = EXCLUDED.avg_task_completion_time_hours,
        calculated_at = NOW();
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to detect trends
CREATE OR REPLACE FUNCTION detect_trend(
    metric_values DECIMAL[],
    confidence_threshold DECIMAL DEFAULT 0.8
)
RETURNS TABLE(
    direction VARCHAR(20),
    strength DECIMAL(5,2),
    confidence DECIMAL(5,2)
) AS $$
DECLARE
    n INTEGER;
    slope DECIMAL;
    correlation DECIMAL;
    trend_direction VARCHAR(20);
    trend_strength DECIMAL(5,2);
    trend_confidence DECIMAL(5,2);
BEGIN
    n := array_length(metric_values, 1);
    
    IF n < 3 THEN
        RETURN QUERY SELECT 'insufficient_data'::VARCHAR(20), 0.0::DECIMAL(5,2), 0.0::DECIMAL(5,2);
        RETURN;
    END IF;
    
    -- Simple linear regression slope calculation
    -- This is a simplified version - in practice, you'd use a more robust statistical method
    slope := (metric_values[n] - metric_values[1]) / (n - 1);
    
    -- Determine direction
    IF slope > 0 THEN
        trend_direction := 'increasing';
    ELSIF slope < 0 THEN
        trend_direction := 'decreasing';
    ELSE
        trend_direction := 'stable';
    END IF;
    
    -- Calculate strength (simplified)
    trend_strength := LEAST(ABS(slope) * 10, 100.0);
    
    -- Calculate confidence (simplified)
    trend_confidence := LEAST(n * 10.0, 100.0);
    
    RETURN QUERY SELECT trend_direction, trend_strength, trend_confidence;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SAMPLE DATA AND INITIALIZATION
-- =====================================================

-- Insert sample dashboard configurations
INSERT INTO dashboards (organization_id, name, dashboard_type, layout_config, created_by) VALUES
(1, 'Executive Dashboard', 'executive', 
 '{"widgets": [{"type": "metric", "title": "Active Projects", "position": {"x": 0, "y": 0, "w": 3, "h": 2}}]}', 1),
(1, 'Development Metrics', 'operational',
 '{"widgets": [{"type": "chart", "title": "Task Completion Trend", "position": {"x": 0, "y": 0, "w": 6, "h": 4}}]}', 1);

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE daily_analytics IS 'Daily aggregated analytics metrics for comprehensive performance tracking';
COMMENT ON TABLE weekly_analytics IS 'Weekly aggregated analytics for trend analysis and reporting';
COMMENT ON TABLE monthly_analytics IS 'Monthly strategic metrics and KPIs for executive reporting';
COMMENT ON TABLE realtime_metrics IS 'Real-time metrics for live dashboards and monitoring';
COMMENT ON TABLE performance_metrics IS 'System performance metrics for monitoring and optimization';
COMMENT ON TABLE dashboards IS 'Dashboard configurations for analytics visualization';
COMMENT ON TABLE scheduled_reports IS 'Automated report generation and distribution';
COMMENT ON TABLE trend_analysis IS 'Trend analysis results for predictive analytics';
COMMENT ON TABLE correlation_analysis IS 'Correlation analysis between different metrics';

COMMENT ON COLUMN daily_analytics.task_completion_rate IS 'Percentage of tasks completed on the given date';
COMMENT ON COLUMN realtime_metrics.expires_at IS 'When this metric expires and should be cleaned up';
COMMENT ON COLUMN trend_analysis.trend_strength IS 'Strength of detected trend from 0-100';
COMMENT ON COLUMN correlation_analysis.correlation_coefficient IS 'Pearson correlation coefficient between -1 and 1';

