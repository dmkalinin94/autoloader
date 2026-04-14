GET_ACTIVE_STATE = """
SELECT
    id,
    insight_id,
    short_name,
    full_name,
    trigger_name,
    recipients,
    ktalk_room_id,
    ktalk_thread_id,
    jira_issue_key,
    event_balance,
    status,
    last_event1_at,
    last_event0_at,
    flap_reopen_until,
    created_at,
    updated_at
FROM trmetrics.availconf.alert_state
WHERE insight_id = %(insight_id)s
  AND status = 'active'
ORDER BY id DESC
LIMIT 1;
"""

GET_LAST_STATE = """
SELECT
    id,
    insight_id,
    short_name,
    full_name,
    trigger_name,
    recipients,
    ktalk_room_id,
    ktalk_thread_id,
    jira_issue_key,
    event_balance,
    status,
    last_event1_at,
    last_event0_at,
    flap_reopen_until,
    created_at,
    updated_at
FROM trmetrics.availconf.alert_state
WHERE insight_id = %(insight_id)s
ORDER BY id DESC
LIMIT 1;
"""

CREATE_STATE = """
INSERT INTO trmetrics.availconf.alert_state (
    insight_id,
    short_name,
    full_name,
    trigger_name,
    recipients,
    ktalk_room_id,
    ktalk_thread_id,
    jira_issue_key,
    event_balance,
    status,
    last_event1_at,
    created_at,
    updated_at
)
VALUES (
    %(insight_id)s,
    %(short_name)s,
    %(full_name)s,
    %(trigger_name)s,
    %(recipients)s,
    %(ktalk_room_id)s,
    %(ktalk_thread_id)s,
    %(jira_issue_key)s,
    %(event_balance)s,
    %(status)s,
    %(last_event1_at)s,
    NOW(),
    NOW()
)
RETURNING id;
"""

ACTIVATE_EXISTING_STATE = """
UPDATE trmetrics.availconf.alert_state
SET
    status = 'active',
    event_balance = GREATEST(COALESCE(event_balance, 0) + %(delta)s, 1),
    last_event1_at = %(event_time)s,
    updated_at = NOW()
WHERE id = %(state_id)s
RETURNING id, ktalk_thread_id, jira_issue_key, event_balance;
"""

DECREASE_EVENT_BALANCE = """
UPDATE trmetrics.availconf.alert_state
SET
    event_balance = GREATEST(COALESCE(event_balance, 0) - %(delta)s, 0),
    last_event0_at = %(event_time)s,
    flap_reopen_until = %(event_time)s + INTERVAL '3 hours',
    updated_at = NOW()
WHERE id = %(state_id)s
RETURNING id, event_balance, ktalk_thread_id, jira_issue_key, last_event0_at, flap_reopen_until;
"""

MARK_STATE_CLOSED = """
UPDATE trmetrics.availconf.alert_state
SET
    status = 'closed',
    updated_at = NOW()
WHERE id = %(state_id)s;
"""

APPEND_AUDIT_EVENT = """
INSERT INTO trmetrics.availconf.alert_state_audit (
    alert_state_id,
    insight_id,
    event_value,
    event_time,
    action,
    note,
    created_at
)
VALUES (
    %(alert_state_id)s,
    %(insight_id)s,
    %(event_value)s,
    %(event_time)s,
    %(action)s,
    %(note)s,
    NOW()
);
"""
