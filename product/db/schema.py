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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""
