ALERT_STATE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS trmetrics.availconf.alert_state (
    id BIGSERIAL PRIMARY KEY,
    insight_id TEXT NOT NULL,
    short_name TEXT,
    full_name TEXT,
    trigger_name TEXT,
    recipients TEXT[],
    ktalk_room_id TEXT,
    ktalk_thread_id TEXT,
    jira_issue_key TEXT,
    event_balance INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    last_event1_at TIMESTAMPTZ,
    last_event0_at TIMESTAMPTZ,
    flap_reopen_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_alert_state_insight_id_created_at
    ON trmetrics.availconf.alert_state (insight_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_alert_state_insight_id_status
    ON trmetrics.availconf.alert_state (insight_id, status);
"""

ALERT_STATE_AUDIT_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS trmetrics.availconf.alert_state_audit (
    id BIGSERIAL PRIMARY KEY,
    alert_state_id BIGINT,
    insight_id TEXT NOT NULL,
    event_value INTEGER NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    action TEXT NOT NULL,
    note TEXT,
    decision_code TEXT,
    jira_issue_key TEXT,
    ktalk_thread_id TEXT,
    payload_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE trmetrics.availconf.alert_state_audit
ADD COLUMN IF NOT EXISTS decision_code TEXT,
ADD COLUMN IF NOT EXISTS jira_issue_key TEXT,
ADD COLUMN IF NOT EXISTS ktalk_thread_id TEXT,
ADD COLUMN IF NOT EXISTS payload_json JSONB;
"""

ALERT_INCIDENTS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS trmetrics.availconf.alert_incidents (
    id BIGSERIAL PRIMARY KEY,
    insight_id TEXT NOT NULL,
    short_name TEXT,
    full_name TEXT,
    trigger_name TEXT,
    trigger_time TIMESTAMPTZ,
    recipients TEXT[],
    jira_issue_key TEXT,
    ktalk_thread_id TEXT,
    ktalk_room_id TEXT,
    opened_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMPTZ,
    close_reason TEXT
);
"""

AD_KTALK_USER_MAP_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS trmetrics.availconf.ad_ktalk_user_map (
    ad_login TEXT PRIMARY KEY,
    ad_display_name TEXT,
    ktalk_mention_id TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""
