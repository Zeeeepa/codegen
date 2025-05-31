-- =====================================================
-- EVALUATIONS SCHEMA - Effectiveness and Outcome Analysis
-- =====================================================
-- This schema supports comprehensive evaluation and analysis including:
-- - Task and project effectiveness tracking
-- - Performance metrics and KPIs
-- - Outcome analysis and success measurement
-- - AI agent performance evaluation
-- - Cross-system effectiveness correlation
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- CORE EVALUATION TABLES
-- =====================================================

-- Evaluation frameworks - Define evaluation criteria and methods
CREATE TABLE evaluation_frameworks (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    
    -- Framework identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    framework_type VARCHAR(50) NOT NULL, -- 'task_performance', 'project_success', 'agent_effectiveness', 'code_quality'
    version VARCHAR(20) DEFAULT '1.0',
    
    -- Framework definition
    criteria JSONB NOT NULL, -- Evaluation criteria and weights
    metrics JSONB NOT NULL, -- Metrics to collect and calculate
    scoring_method VARCHAR(50) DEFAULT 'weighted_average', -- 'weighted_average', 'composite', 'custom'
    
    -- Framework configuration
    evaluation_frequency VARCHAR(50) DEFAULT 'on_completion', -- 'real_time', 'daily', 'weekly', 'on_completion'
    auto_evaluation BOOLEAN DEFAULT false,
    threshold_config JSONB DEFAULT '{}', -- Success/failure thresholds
    
    -- Framework status
    status VARCHAR(50) DEFAULT 'active', -- 'draft', 'active', 'deprecated'
    is_default BOOLEAN DEFAULT false,
    
    -- Usage tracking
    evaluation_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    tags TEXT[],
    metadata JSONB DEFAULT '{}',
    
    -- Audit
    created_by BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    UNIQUE(organization_id, name, version)
);

-- Evaluations table - Individual evaluation instances
CREATE TABLE evaluations (
    id BIGSERIAL PRIMARY KEY,
    organization_id BIGINT NOT NULL,
    framework_id BIGINT NOT NULL REFERENCES evaluation_frameworks(id) ON DELETE CASCADE,
    
    -- Evaluation target
    target_type VARCHAR(50) NOT NULL, -- 'task', 'project', 'agent_run', 'codebase', 'workflow'
    target_id BIGINT NOT NULL,
    target_name VARCHAR(255),
    
    -- Evaluation context
    evaluation_type VARCHAR(50) NOT NULL, -- 'performance', 'quality', 'effectiveness', 'outcome'
    evaluation_period_start TIMESTAMP WITH TIME ZONE,
    evaluation_period_end TIMESTAMP WITH TIME ZONE,
    
    -- Evaluation status
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed'
    
    -- Evaluation results
    overall_score DECIMAL(10,4), -- Overall evaluation score
    max_possible_score DECIMAL(10,4) DEFAULT 100.0,
    score_percentage DECIMAL(5,2), -- Score as percentage
    
    -- Detailed results
    criteria_scores JSONB DEFAULT '{}', -- Individual criteria scores
    metric_values JSONB DEFAULT '{}', -- Raw metric values
    calculated_metrics JSONB DEFAULT '{}', -- Derived metrics
    
    -- Evaluation metadata
    evaluation_method VARCHAR(50), -- 'automatic', 'manual', 'hybrid'
    confidence_level DECIMAL(5,2), -- Confidence in evaluation (0-100)
    data_quality_score DECIMAL(5,2), -- Quality of underlying data
    
    -- Comparison and benchmarking
    baseline_score DECIMAL(10,4), -- Baseline for comparison
    improvement_percentage DECIMAL(10,4), -- Improvement over baseline
    percentile_rank DECIMAL(5,2), -- Rank compared to similar evaluations
    
    -- Recommendations and insights
    recommendations JSONB DEFAULT '[]', -- Generated recommendations
    insights JSONB DEFAULT '[]', -- Key insights from evaluation
    action_items JSONB DEFAULT '[]', -- Suggested action items
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    
    -- Audit
    evaluated_by BIGINT, -- User who triggered evaluation
    evaluated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX(organization_id, target_type, target_id),
    INDEX(framework_id, status),
    INDEX(evaluated_at)
);

-- Continue with rest of schema...
