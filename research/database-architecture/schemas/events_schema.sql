-- =====================================================
-- EVENTS SCHEMA - Multi-Platform Event Tracking (ClickHouse)
-- =====================================================
-- This schema supports comprehensive event tracking including:
-- - Multi-platform event ingestion (Linear, Slack, GitHub, deployments)
-- - Real-time event processing and correlation
-- - Time-series analytics and reporting
-- - Event-driven workflow triggers
-- - Cross-system event correlation
-- =====================================================

-- =====================================================
-- CORE EVENT TABLES
-- =====================================================

-- Main events table - Core event storage with partitioning
CREATE TABLE events (
    -- Event identification
    id UUID DEFAULT generateUUIDv4(),
    event_id String, -- External event ID from source system
    organization_id UInt64,
    
    -- Event classification
    event_type LowCardinality(String), -- 'task_created', 'pr_opened', 'deployment_started', etc.
    event_category LowCardinality(String), -- 'task', 'code', 'deployment', 'communication'
    source_platform LowCardinality(String), -- 'linear', 'slack', 'github', 'deployment', 'system'
    source_system String, -- Specific system within platform
    
    -- Event context
    user_id Nullable(UInt64),
    project_id Nullable(UInt64),
    task_id Nullable(UInt64),
    codebase_id Nullable(UInt64),
    workflow_id Nullable(UInt64),
    
    -- Event payload
    event_data String, -- JSON string containing event details
    event_version LowCardinality(String) DEFAULT '1.0', -- Event schema version
    
    -- Event metadata
    correlation_id Nullable(String), -- For correlating related events
    session_id Nullable(String), -- User session identifier
    trace_id Nullable(String), -- Distributed tracing identifier
    
    -- Timing information
    timestamp DateTime64(3) DEFAULT now64(),
    source_timestamp Nullable(DateTime64(3)), -- Original timestamp from source
    processed_at Nullable(DateTime64(3)),
    
    -- Event properties
    severity LowCardinality(String) DEFAULT 'info', -- 'debug', 'info', 'warning', 'error', 'critical'
    is_synthetic Bool DEFAULT false, -- Generated vs real events
    is_test Bool DEFAULT false, -- Test vs production events
    
    -- Processing status
    processing_status LowCardinality(String) DEFAULT 'pending', -- 'pending', 'processed', 'failed', 'skipped'
    retry_count UInt8 DEFAULT 0,
    
    -- Geographic and technical context
    ip_address Nullable(IPv4),
    user_agent Nullable(String),
    geo_country Nullable(String),
    geo_city Nullable(String),
    
    -- Indexes for efficient querying
    INDEX idx_org_time (organization_id, timestamp),
    INDEX idx_event_type (event_type),
    INDEX idx_source_platform (source_platform),
    INDEX idx_correlation (correlation_id),
    INDEX idx_user_time (user_id, timestamp),
    INDEX idx_project_time (project_id, timestamp)
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (organization_id, event_type, timestamp)
SETTINGS index_granularity = 8192;

-- Event attributes table - EAV pattern for flexible event properties
CREATE TABLE event_attributes (
    event_id UUID,
    attribute_name LowCardinality(String),
    attribute_value String,
    attribute_type LowCardinality(String), -- 'string', 'number', 'boolean', 'datetime', 'json'
    attribute_category LowCardinality(String), -- 'metadata', 'payload', 'context', 'metric'
    timestamp DateTime64(3),
    
    INDEX idx_event_attr (event_id, attribute_name),
    INDEX idx_attr_name_value (attribute_name, attribute_value),
    INDEX idx_timestamp (timestamp)
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_id, attribute_name, timestamp)
SETTINGS index_granularity = 8192;

-- Event relationships - Links between related events
CREATE TABLE event_relationships (
    id UUID DEFAULT generateUUIDv4(),
    source_event_id UUID,
    target_event_id UUID,
    relationship_type LowCardinality(String), -- 'triggers', 'caused_by', 'follows', 'correlates_with'
    relationship_strength Float32 DEFAULT 1.0, -- 0.0 to 1.0
    confidence_score Float32 DEFAULT 1.0, -- Confidence in the relationship
    
    -- Context
    detected_by LowCardinality(String), -- 'system', 'rule', 'ml_model', 'user'
    detection_metadata String, -- JSON metadata about detection
    
    -- Timing
    created_at DateTime64(3) DEFAULT now64(),
    
    INDEX idx_source_event (source_event_id),
    INDEX idx_target_event (target_event_id),
    INDEX idx_relationship_type (relationship_type)
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (source_event_id, target_event_id, created_at)
SETTINGS index_granularity = 8192;

-- =====================================================
-- PLATFORM-SPECIFIC EVENT TABLES
-- =====================================================

-- Linear events - Task and project management events
CREATE TABLE linear_events (
    event_id UUID,
    linear_event_id String,
    organization_id UInt64,
    
    -- Linear-specific context
    team_id Nullable(String),
    issue_id Nullable(String),
    project_id Nullable(String),
    user_id Nullable(String),
    
    -- Event details
    action LowCardinality(String), -- 'create', 'update', 'delete', 'assign', etc.
    entity_type LowCardinality(String), -- 'issue', 'project', 'comment', 'attachment'
    
    -- Linear data
    issue_data String, -- JSON data for issue events
    project_data String, -- JSON data for project events
    user_data String, -- JSON data for user events
    
    -- Changes tracking
    changes String, -- JSON of what changed
    previous_values String, -- JSON of previous values
    
    timestamp DateTime64(3),
    
    INDEX idx_linear_org_time (organization_id, timestamp),
    INDEX idx_linear_issue (issue_id),
    INDEX idx_linear_project (project_id),
    INDEX idx_linear_action (action)
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (organization_id, linear_event_id, timestamp)
SETTINGS index_granularity = 8192;

-- GitHub events - Code repository events
CREATE TABLE github_events (
    event_id UUID,
    github_event_id String,
    organization_id UInt64,
    
    -- GitHub-specific context
    repository_name String,
    repository_id Nullable(UInt64),
    actor_login String,
    actor_id Nullable(UInt64),
    
    -- Event details
    event_type LowCardinality(String), -- 'push', 'pull_request', 'issues', 'deployment', etc.
    action LowCardinality(String), -- 'opened', 'closed', 'merged', 'created', etc.
    
    -- GitHub data
    payload String, -- Full GitHub webhook payload
    
    -- Common extracted fields
    branch_name Nullable(String),
    commit_sha Nullable(String),
    pull_request_number Nullable(UInt32),
    issue_number Nullable(UInt32),
    
    timestamp DateTime64(3),
    
    INDEX idx_github_org_time (organization_id, timestamp),
    INDEX idx_github_repo (repository_name),
    INDEX idx_github_actor (actor_login),
    INDEX idx_github_event_type (event_type),
    INDEX idx_github_pr (pull_request_number),
    INDEX idx_github_commit (commit_sha)
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (organization_id, repository_name, timestamp)
SETTINGS index_granularity = 8192;

-- Slack events - Communication and collaboration events
CREATE TABLE slack_events (
    event_id UUID,
    slack_event_id String,
    organization_id UInt64,
    
    -- Slack-specific context
    team_id String,
    channel_id Nullable(String),
    user_id Nullable(String),
    thread_ts Nullable(String),
    
    -- Event details
    event_type LowCardinality(String), -- 'message', 'reaction_added', 'channel_created', etc.
    subtype LowCardinality(String), -- Message subtypes
    
    -- Message content (if applicable)
    text Nullable(String),
    blocks String, -- JSON blocks for rich messages
    attachments String, -- JSON attachments
    
    -- Slack data
    event_data String, -- Full Slack event data
    
    -- Bot detection
    is_bot Bool DEFAULT false,
    bot_id Nullable(String),
    
    timestamp DateTime64(3),
    
    INDEX idx_slack_org_time (organization_id, timestamp),
    INDEX idx_slack_channel (channel_id),
    INDEX idx_slack_user (user_id),
    INDEX idx_slack_event_type (event_type),
    INDEX idx_slack_thread (thread_ts)
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (organization_id, team_id, timestamp)
SETTINGS index_granularity = 8192;

-- Deployment events - Application deployment and infrastructure events
CREATE TABLE deployment_events (
    event_id UUID,
    deployment_id String,
    organization_id UInt64,
    
    -- Deployment context
    environment LowCardinality(String), -- 'development', 'staging', 'production'
    service_name String,
    version String,
    
    -- Event details
    event_type LowCardinality(String), -- 'started', 'completed', 'failed', 'rolled_back'
    deployment_strategy LowCardinality(String), -- 'blue_green', 'rolling', 'canary'
    
    -- Deployment metadata
    commit_sha Nullable(String),
    branch_name Nullable(String),
    triggered_by Nullable(String),
    
    -- Performance metrics
    duration_seconds Nullable(UInt32),
    success Bool DEFAULT true,
    error_message Nullable(String),
    
    -- Infrastructure details
    infrastructure_data String, -- JSON with infrastructure details
    
    timestamp DateTime64(3),
    
    INDEX idx_deployment_org_time (organization_id, timestamp),
    INDEX idx_deployment_service (service_name),
    INDEX idx_deployment_env (environment),
    INDEX idx_deployment_version (version),
    INDEX idx_deployment_commit (commit_sha)
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (organization_id, service_name, timestamp)
SETTINGS index_granularity = 8192;

-- =====================================================
-- ANALYTICS AND AGGREGATION TABLES
-- =====================================================

-- Hourly event aggregations
CREATE MATERIALIZED VIEW event_hourly_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (organization_id, event_type, source_platform, hour)
AS SELECT
    organization_id,
    event_type,
    source_platform,
    toStartOfHour(timestamp) as hour,
    count() as event_count,
    uniq(user_id) as unique_users,
    uniq(session_id) as unique_sessions,
    countIf(severity = 'error') as error_count,
    countIf(severity = 'warning') as warning_count
FROM events
GROUP BY organization_id, event_type, source_platform, hour;

-- Daily event aggregations
CREATE MATERIALIZED VIEW event_daily_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, event_type, source_platform, date)
AS SELECT
    organization_id,
    event_type,
    source_platform,
    toDate(timestamp) as date,
    count() as event_count,
    uniq(user_id) as unique_users,
    uniq(session_id) as unique_sessions,
    uniq(project_id) as unique_projects,
    countIf(severity = 'error') as error_count,
    countIf(severity = 'warning') as warning_count,
    countIf(is_synthetic = true) as synthetic_count
FROM events
GROUP BY organization_id, event_type, source_platform, date;

-- User activity aggregations
CREATE MATERIALIZED VIEW user_activity_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, user_id, date)
AS SELECT
    organization_id,
    user_id,
    toDate(timestamp) as date,
    count() as total_events,
    uniq(event_type) as unique_event_types,
    uniq(source_platform) as unique_platforms,
    uniq(project_id) as unique_projects,
    min(timestamp) as first_activity,
    max(timestamp) as last_activity
FROM events
WHERE user_id IS NOT NULL
GROUP BY organization_id, user_id, date;

-- Project activity aggregations
CREATE MATERIALIZED VIEW project_activity_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (organization_id, project_id, date)
AS SELECT
    organization_id,
    project_id,
    toDate(timestamp) as date,
    count() as total_events,
    uniq(event_type) as unique_event_types,
    uniq(user_id) as unique_users,
    uniq(source_platform) as unique_platforms,
    countIf(event_category = 'task') as task_events,
    countIf(event_category = 'code') as code_events,
    countIf(event_category = 'deployment') as deployment_events
FROM events
WHERE project_id IS NOT NULL
GROUP BY organization_id, project_id, date;

-- =====================================================
-- EVENT PROCESSING AND WORKFLOW TABLES
-- =====================================================

-- Event processing rules
CREATE TABLE event_processing_rules (
    id UUID DEFAULT generateUUIDv4(),
    organization_id UInt64,
    rule_name String,
    
    -- Rule configuration
    event_filters String, -- JSON filters for matching events
    conditions String, -- JSON conditions for rule execution
    actions String, -- JSON actions to take
    
    -- Rule metadata
    is_active Bool DEFAULT true,
    priority UInt8 DEFAULT 50, -- 0-100, higher = higher priority
    
    -- Execution tracking
    execution_count UInt64 DEFAULT 0,
    last_executed_at Nullable(DateTime64(3)),
    
    -- Audit
    created_by UInt64,
    created_at DateTime64(3) DEFAULT now64(),
    updated_at DateTime64(3) DEFAULT now64()
    
) ENGINE = MergeTree()
ORDER BY (organization_id, priority, id)
SETTINGS index_granularity = 8192;

-- Event processing executions
CREATE TABLE event_processing_executions (
    id UUID DEFAULT generateUUIDv4(),
    rule_id UUID,
    event_id UUID,
    organization_id UInt64,
    
    -- Execution details
    execution_status LowCardinality(String), -- 'success', 'failure', 'skipped'
    actions_executed String, -- JSON of actions that were executed
    execution_result String, -- JSON result of execution
    error_message Nullable(String),
    
    -- Timing
    started_at DateTime64(3) DEFAULT now64(),
    completed_at Nullable(DateTime64(3)),
    duration_ms UInt32,
    
    INDEX idx_rule_execution (rule_id, started_at),
    INDEX idx_event_execution (event_id),
    INDEX idx_org_execution (organization_id, started_at)
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(started_at)
ORDER BY (rule_id, started_at)
SETTINGS index_granularity = 8192;

-- Event correlation patterns
CREATE TABLE event_correlation_patterns (
    id UUID DEFAULT generateUUIDv4(),
    organization_id UInt64,
    pattern_name String,
    
    -- Pattern definition
    pattern_config String, -- JSON configuration for pattern matching
    time_window_seconds UInt32, -- Time window for correlation
    min_events UInt8 DEFAULT 2, -- Minimum events to trigger pattern
    
    -- Pattern metadata
    is_active Bool DEFAULT true,
    confidence_threshold Float32 DEFAULT 0.8,
    
    -- Detection tracking
    detection_count UInt64 DEFAULT 0,
    last_detected_at Nullable(DateTime64(3)),
    
    -- Audit
    created_by UInt64,
    created_at DateTime64(3) DEFAULT now64()
    
) ENGINE = MergeTree()
ORDER BY (organization_id, id)
SETTINGS index_granularity = 8192;

-- =====================================================
-- PERFORMANCE OPTIMIZATION TABLES
-- =====================================================

-- Event sampling for high-volume scenarios
CREATE TABLE event_samples (
    sample_id UUID DEFAULT generateUUIDv4(),
    original_event_id UUID,
    organization_id UInt64,
    
    -- Sampling metadata
    sample_rate Float32, -- 0.0 to 1.0
    sample_reason LowCardinality(String), -- 'random', 'rate_limit', 'debug'
    
    -- Sampled event data (subset of original)
    event_type LowCardinality(String),
    source_platform LowCardinality(String),
    timestamp DateTime64(3),
    
    INDEX idx_sample_org_time (organization_id, timestamp),
    INDEX idx_sample_original (original_event_id)
    
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (organization_id, timestamp)
SETTINGS index_granularity = 8192;

-- =====================================================
-- FUNCTIONS AND PROCEDURES
-- =====================================================

-- Function to get event timeline for a project
CREATE VIEW project_event_timeline AS
SELECT 
    e.id,
    e.event_type,
    e.source_platform,
    e.timestamp,
    e.user_id,
    e.project_id,
    e.event_data,
    ea.attribute_name,
    ea.attribute_value
FROM events e
LEFT JOIN event_attributes ea ON e.id = ea.event_id
WHERE e.project_id IS NOT NULL
ORDER BY e.project_id, e.timestamp DESC;

-- Function to get user activity summary
CREATE VIEW user_activity_summary AS
SELECT 
    organization_id,
    user_id,
    count() as total_events,
    uniq(event_type) as unique_event_types,
    uniq(source_platform) as unique_platforms,
    min(timestamp) as first_activity,
    max(timestamp) as last_activity,
    countIf(timestamp >= now() - INTERVAL 1 DAY) as events_last_24h,
    countIf(timestamp >= now() - INTERVAL 7 DAY) as events_last_7d,
    countIf(timestamp >= now() - INTERVAL 30 DAY) as events_last_30d
FROM events
WHERE user_id IS NOT NULL
GROUP BY organization_id, user_id;

-- =====================================================
-- DATA RETENTION POLICIES
-- =====================================================

-- TTL for old event data (configurable per organization)
ALTER TABLE events 
ADD COLUMN ttl_date Date MATERIALIZED toDate(timestamp + INTERVAL 365 DAY);

-- TTL for event attributes
ALTER TABLE event_attributes 
ADD COLUMN ttl_date Date MATERIALIZED toDate(timestamp + INTERVAL 365 DAY);

-- TTL for aggregated data (keep longer)
ALTER TABLE event_hourly_stats 
ADD COLUMN ttl_date Date MATERIALIZED toDate(hour + INTERVAL 730 DAY);

ALTER TABLE event_daily_stats 
ADD COLUMN ttl_date Date MATERIALIZED toDate(date + INTERVAL 1095 DAY);

-- =====================================================
-- SAMPLE QUERIES AND USAGE EXAMPLES
-- =====================================================

-- Example: Get recent events for a project
-- SELECT * FROM events 
-- WHERE project_id = 123 
-- AND timestamp >= now() - INTERVAL 7 DAY 
-- ORDER BY timestamp DESC 
-- LIMIT 100;

-- Example: Get event correlation for a user session
-- SELECT e1.event_type as source_event, e2.event_type as target_event, count() as correlation_count
-- FROM events e1
-- JOIN events e2 ON e1.session_id = e2.session_id 
-- WHERE e1.timestamp < e2.timestamp 
-- AND e2.timestamp <= e1.timestamp + INTERVAL 1 HOUR
-- GROUP BY e1.event_type, e2.event_type
-- ORDER BY correlation_count DESC;

-- Example: Get daily activity metrics
-- SELECT 
--     toDate(timestamp) as date,
--     source_platform,
--     count() as event_count,
--     uniq(user_id) as unique_users
-- FROM events 
-- WHERE organization_id = 1 
-- AND timestamp >= now() - INTERVAL 30 DAY
-- GROUP BY date, source_platform
-- ORDER BY date DESC;

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

-- Table comments
ALTER TABLE events ADD COMMENT 'Core event storage table with time-series partitioning for multi-platform event tracking';
ALTER TABLE event_attributes ADD COMMENT 'Flexible event attributes using EAV pattern for extensible event properties';
ALTER TABLE event_relationships ADD COMMENT 'Relationships and correlations between events for workflow analysis';
ALTER TABLE linear_events ADD COMMENT 'Linear-specific events for task and project management tracking';
ALTER TABLE github_events ADD COMMENT 'GitHub events for code repository activity tracking';
ALTER TABLE slack_events ADD COMMENT 'Slack events for communication and collaboration tracking';
ALTER TABLE deployment_events ADD COMMENT 'Deployment and infrastructure events for DevOps tracking';

-- Column comments for key fields
ALTER TABLE events ADD COMMENT FOR COLUMN event_data 'JSON payload containing full event details from source system';
ALTER TABLE events ADD COMMENT FOR COLUMN correlation_id 'Identifier for correlating related events across systems';
ALTER TABLE events ADD COMMENT FOR COLUMN processing_status 'Status of event processing for workflow automation';
ALTER TABLE event_attributes ADD COMMENT FOR COLUMN attribute_type 'Data type of attribute value for proper parsing and querying';
ALTER TABLE event_relationships ADD COMMENT FOR COLUMN relationship_strength 'Strength of relationship from 0.0 to 1.0 for weighted analysis';

