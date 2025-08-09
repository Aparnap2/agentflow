-- AgentFlow PRD Schema Migration
-- Add tables required by PRD specifications

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES auth.users(id),
    name TEXT NOT NULL,
    plan TEXT DEFAULT 'starter',
    region TEXT DEFAULT 'us-east-1',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Update users table to include workspace relationship
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id);
ALTER TABLE auth.users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'owner';

-- Approvals table for HITL workflows
CREATE TABLE IF NOT EXISTS approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id),
    type TEXT NOT NULL, -- 'instagram_post', 'crm_update', 'financial_decision', etc.
    payload JSONB NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    requested_by TEXT NOT NULL, -- agent name
    approved_by UUID REFERENCES auth.users(id),
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Audit logs for compliance
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id),
    user_id UUID REFERENCES auth.users(id),
    agent TEXT,
    action TEXT NOT NULL,
    details JSONB,
    sensitive_flag BOOLEAN DEFAULT FALSE,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Settings table for HITL policies and configurations
CREATE TABLE IF NOT EXISTS agent_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id),
    agent_name TEXT NOT NULL,
    hitl_policies JSONB DEFAULT '{}',
    notification_routes JSONB DEFAULT '{}',
    integration_configs JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workspace_id, agent_name)
);

-- Instagram DM compliance tracking
CREATE TABLE IF NOT EXISTS instagram_dm_compliance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id),
    conversation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    last_user_message_at TIMESTAMP WITH TIME ZONE,
    response_window_expires_at TIMESTAMP WITH TIME ZONE,
    human_agent_tag_expires_at TIMESTAMP WITH TIME ZONE,
    compliance_status TEXT DEFAULT 'active', -- 'active', 'expired', 'human_tagged'
    auto_responses_sent INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workspace_id, conversation_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_approvals_workspace_status ON approvals(workspace_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_workspace_created ON audit_logs(workspace_id, created_at);
CREATE INDEX IF NOT EXISTS idx_instagram_compliance_expires ON instagram_dm_compliance(response_window_expires_at);

-- Row Level Security (RLS) policies
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE instagram_dm_compliance ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can access their workspace" ON workspaces
    FOR ALL USING (owner_id = auth.uid());

CREATE POLICY "Users can access their workspace approvals" ON approvals
    FOR ALL USING (workspace_id IN (SELECT id FROM workspaces WHERE owner_id = auth.uid()));

CREATE POLICY "Users can access their workspace audit logs" ON audit_logs
    FOR ALL USING (workspace_id IN (SELECT id FROM workspaces WHERE owner_id = auth.uid()));

CREATE POLICY "Users can access their workspace settings" ON agent_settings
    FOR ALL USING (workspace_id IN (SELECT id FROM workspaces WHERE owner_id = auth.uid()));

CREATE POLICY "Users can access their workspace compliance data" ON instagram_dm_compliance
    FOR ALL USING (workspace_id IN (SELECT id FROM workspaces WHERE owner_id = auth.uid()));