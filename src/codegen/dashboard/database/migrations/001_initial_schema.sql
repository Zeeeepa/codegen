-- Initial database schema for Codegen Dashboard
-- Migration: 001_initial_schema
-- Created: 2024-09-17

-- Agent Runs Starred Table
CREATE TABLE IF NOT EXISTS agent_runs_starred (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    agent_run_id INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, org_id, agent_run_id)
);

-- Projects Starred Table
CREATE TABLE IF NOT EXISTS projects_starred (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    repo_name TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, org_id, repo_name)
);

-- User Preferences Table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, org_id)
);

-- Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT DEFAULT 'info',
    metadata JSONB DEFAULT '{}',
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Validation Gates Table
CREATE TABLE IF NOT EXISTS validation_gates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    repo_name TEXT NOT NULL,
    gate_config JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- PRD Dialogs Table
CREATE TABLE IF NOT EXISTS prd_dialogs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    repo_name TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow Templates Table
CREATE TABLE IF NOT EXISTS workflow_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    template_config JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dashboard Sessions Table
CREATE TABLE IF NOT EXISTS dashboard_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_runs_starred_user_org ON agent_runs_starred(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_starred_updated ON agent_runs_starred(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_projects_starred_user_org ON projects_starred(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_projects_starred_updated ON projects_starred(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_user_org ON notifications(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, org_id, read) WHERE read = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_validation_gates_user_org ON validation_gates(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_validation_gates_repo ON validation_gates(repo_name, active);
CREATE INDEX IF NOT EXISTS idx_validation_gates_active ON validation_gates(active, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_prd_dialogs_user_org ON prd_dialogs(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_prd_dialogs_repo ON prd_dialogs(repo_name, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_workflow_templates_user_org ON workflow_templates(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_workflow_templates_active ON workflow_templates(active, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_user ON dashboard_sessions(user_id, org_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_sessions_activity ON dashboard_sessions(last_activity DESC);

-- Row Level Security (RLS) Policies
ALTER TABLE agent_runs_starred ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects_starred ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_gates ENABLE ROW LEVEL SECURITY;
ALTER TABLE prd_dialogs ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)
CREATE POLICY "Users can access their own starred agent runs" ON agent_runs_starred
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own starred projects" ON projects_starred
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own preferences" ON user_preferences
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own notifications" ON notifications
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own validation gates" ON validation_gates
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own PRD dialogs" ON prd_dialogs
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own workflow templates" ON workflow_templates
    FOR ALL USING (auth.uid()::text = user_id);

CREATE POLICY "Users can access their own dashboard sessions" ON dashboard_sessions
    FOR ALL USING (auth.uid()::text = user_id);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_agent_runs_starred_updated_at BEFORE UPDATE ON agent_runs_starred
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_starred_updated_at BEFORE UPDATE ON projects_starred
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_validation_gates_updated_at BEFORE UPDATE ON validation_gates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prd_dialogs_updated_at BEFORE UPDATE ON prd_dialogs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_templates_updated_at BEFORE UPDATE ON workflow_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE agent_runs_starred IS 'Stores user-starred agent runs for quick access';
COMMENT ON TABLE projects_starred IS 'Stores user-starred projects/repositories for monitoring';
COMMENT ON TABLE user_preferences IS 'Stores user-specific dashboard preferences and settings';
COMMENT ON TABLE notifications IS 'Stores user notifications from various dashboard events';
COMMENT ON TABLE validation_gates IS 'Stores validation rules and gates for repositories';
COMMENT ON TABLE prd_dialogs IS 'Stores Product Requirements Documents for projects';
COMMENT ON TABLE workflow_templates IS 'Stores reusable workflow templates for automation';
COMMENT ON TABLE dashboard_sessions IS 'Stores active dashboard sessions for users';

-- Insert initial data (optional)
-- This could include default notification types, workflow templates, etc.

-- Migration complete
INSERT INTO migrations (version, description, applied_at) 
VALUES ('001', 'Initial database schema for Codegen Dashboard', NOW())
ON CONFLICT (version) DO NOTHING;
