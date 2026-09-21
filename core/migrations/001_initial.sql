CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    external_provider TEXT,
    external_subject TEXT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (external_provider, external_subject)
);

CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS organization_memberships (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    organization_id TEXT NOT NULL REFERENCES organizations(id),
    role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (user_id, organization_id)
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organizations(id),
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    project_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (organization_id, slug)
);

CREATE TABLE IF NOT EXISTS project_memberships (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (project_id, user_id)
);

CREATE TABLE IF NOT EXISTS module_access (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organizations(id),
    project_id TEXT REFERENCES projects(id),
    module_key TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'disabled',
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_module_access_project
    ON module_access (organization_id, project_id, module_key) WHERE project_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_module_access_organization
    ON module_access (organization_id, module_key) WHERE project_id IS NULL;

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    user_id TEXT REFERENCES users(id),
    organization_id TEXT REFERENCES organizations(id),
    project_id TEXT REFERENCES projects(id),
    module TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS usage_events (
    id TEXT PRIMARY KEY,
    event_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT REFERENCES users(id),
    organization_id TEXT REFERENCES organizations(id),
    project_id TEXT REFERENCES projects(id),
    module_key TEXT,
    feature TEXT,
    source_service TEXT,
    quantity NUMERIC NOT NULL DEFAULT 0,
    unit TEXT NOT NULL,
    idempotency_key TEXT,
    correlation_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_usage_idempotency
    ON usage_events (source_service, idempotency_key) WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS suite_user_map (
    id TEXT PRIMARY KEY, suite_user_id TEXT UNIQUE NOT NULL, core_user_id TEXT NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS suite_organization_map (
    id TEXT PRIMARY KEY, suite_organization_id TEXT UNIQUE NOT NULL, core_organization_id TEXT NOT NULL REFERENCES organizations(id),
    created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS suite_project_map (
    id TEXT PRIMARY KEY, suite_organization_id TEXT NOT NULL, suite_project_id TEXT NOT NULL,
    core_project_id TEXT NOT NULL REFERENCES projects(id), created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (suite_organization_id, suite_project_id)
);
CREATE TABLE IF NOT EXISTS pos_user_map (
    id TEXT PRIMARY KEY, pos_user_id TEXT UNIQUE NOT NULL, core_user_id TEXT NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS pos_restaurant_map (
    id TEXT PRIMARY KEY, pos_restaurant_id TEXT UNIQUE NOT NULL, core_organization_id TEXT NOT NULL REFERENCES organizations(id),
    core_project_id TEXT NOT NULL REFERENCES projects(id), created_at TIMESTAMPTZ NOT NULL, updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_audit_organization ON audit_events (organization_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_audit_project ON audit_events (project_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_audit_actor ON audit_events (user_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_audit_module ON audit_events (module, timestamp);
CREATE INDEX IF NOT EXISTS ix_audit_correlation ON audit_events (correlation_id);
CREATE INDEX IF NOT EXISTS ix_usage_organization ON usage_events (organization_id, event_timestamp);
CREATE INDEX IF NOT EXISTS ix_usage_project ON usage_events (project_id, event_timestamp);
CREATE INDEX IF NOT EXISTS ix_usage_user ON usage_events (user_id, event_timestamp);
CREATE INDEX IF NOT EXISTS ix_usage_module ON usage_events (module_key, event_timestamp);