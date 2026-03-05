#!/bin/bash
# =============================================================================
# PostgreSQL Initialization — Create OmniNode Databases
# =============================================================================
# This script runs once when the PostgreSQL container is first initialized.
# It creates the required databases for each OmniNode service.
# =============================================================================
set -e

echo "🗄️  Creating OmniNode databases..."

# Create databases for each service
for db in "${OMNIBASE_INFRA_DB}" "${OMNIINTELLIGENCE_DB}" "${OMNIMEMORY_DB}" "${OMNIDASH_ANALYTICS_DB}"; do
    if [ -n "$db" ]; then
        echo "  Creating database: $db"
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
            SELECT 'CREATE DATABASE "$db"' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
EOSQL
    fi
done

echo "✅ OmniNode databases created successfully"

# =============================================================================
# Create core schema tables for omnibase_infra
# =============================================================================
echo "📋 Initializing omnibase_infra schema..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${OMNIBASE_INFRA_DB}" <<-'EOSQL'
    -- Node registration table
    CREATE TABLE IF NOT EXISTS node_registrations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        node_id TEXT NOT NULL UNIQUE,
        node_type TEXT NOT NULL,
        version TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'registered',
        capabilities JSONB DEFAULT '{}',
        metadata JSONB DEFAULT '{}',
        registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        last_heartbeat_at TIMESTAMPTZ
    );

    -- Contracts topics table
    CREATE TABLE IF NOT EXISTS contracts_topics (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        topic_name TEXT NOT NULL UNIQUE,
        node_id TEXT NOT NULL,
        direction TEXT NOT NULL CHECK (direction IN ('subscribe', 'publish')),
        schema_version TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- Agent routing decisions
    CREATE TABLE IF NOT EXISTS agent_routing_decisions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id TEXT,
        correlation_id TEXT,
        prompt_preview TEXT,
        selected_agent TEXT NOT NULL,
        confidence FLOAT,
        routing_method TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- Agent execution logs
    CREATE TABLE IF NOT EXISTS agent_execution_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        session_id TEXT,
        correlation_id TEXT,
        agent_id TEXT NOT NULL,
        action TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'started',
        duration_ms INTEGER,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- Database metadata
    CREATE TABLE IF NOT EXISTS db_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    INSERT INTO db_metadata (key, value) VALUES ('schema_version', '004')
    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

    CREATE INDEX IF NOT EXISTS idx_routing_decisions_session ON agent_routing_decisions(session_id);
    CREATE INDEX IF NOT EXISTS idx_routing_decisions_created ON agent_routing_decisions(created_at);
    CREATE INDEX IF NOT EXISTS idx_execution_logs_session ON agent_execution_logs(session_id);
    CREATE INDEX IF NOT EXISTS idx_execution_logs_created ON agent_execution_logs(created_at);
EOSQL

# =============================================================================
# Create omniintelligence schema
# =============================================================================
echo "🧠 Initializing omniintelligence schema..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${OMNIINTELLIGENCE_DB}" <<-'EOSQL'
    -- Pattern storage
    CREATE TABLE IF NOT EXISTS patterns (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pattern_name TEXT NOT NULL,
        pattern_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'provisional',
        confidence FLOAT DEFAULT 0.0,
        source TEXT,
        content JSONB NOT NULL DEFAULT '{}',
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        promoted_at TIMESTAMPTZ,
        deprecated_at TIMESTAMPTZ
    );

    -- Pattern feedback
    CREATE TABLE IF NOT EXISTS pattern_feedback (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        pattern_id UUID REFERENCES patterns(id),
        session_id TEXT,
        outcome TEXT NOT NULL,
        confidence_delta FLOAT DEFAULT 0.0,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- Intent classifications
    CREATE TABLE IF NOT EXISTS intent_classifications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        prompt_hash TEXT NOT NULL,
        intent TEXT NOT NULL,
        confidence FLOAT NOT NULL,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_patterns_status ON patterns(status);
    CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type);
    CREATE INDEX IF NOT EXISTS idx_intent_classifications_created ON intent_classifications(created_at);
EOSQL

# =============================================================================
# Create omnidash_analytics schema
# =============================================================================
echo "📊 Initializing omnidash_analytics schema..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "${OMNIDASH_ANALYTICS_DB}" <<-'EOSQL'
    -- LLM cost aggregates (for Cost Trends dashboard)
    CREATE TABLE IF NOT EXISTS llm_cost_aggregates (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        period_start TIMESTAMPTZ NOT NULL,
        period_end TIMESTAMPTZ NOT NULL,
        model TEXT NOT NULL,
        provider TEXT NOT NULL,
        total_tokens INTEGER DEFAULT 0,
        prompt_tokens INTEGER DEFAULT 0,
        completion_tokens INTEGER DEFAULT 0,
        total_cost_usd NUMERIC(12,6) DEFAULT 0.0,
        request_count INTEGER DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- Skill executions (for Skill dashboard)
    CREATE TABLE IF NOT EXISTS skill_executions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        skill_name TEXT NOT NULL,
        session_id TEXT,
        status TEXT NOT NULL DEFAULT 'started',
        duration_ms INTEGER,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    -- Injection effectiveness
    CREATE TABLE IF NOT EXISTS injection_effectiveness (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        channel TEXT NOT NULL,
        hit_rate FLOAT,
        token_savings INTEGER,
        latency_ms INTEGER,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );

    CREATE INDEX IF NOT EXISTS idx_cost_aggregates_period ON llm_cost_aggregates(period_start);
    CREATE INDEX IF NOT EXISTS idx_skill_executions_created ON skill_executions(created_at);
EOSQL

echo "✅ All OmniNode database schemas initialized"

