from __future__ import annotations

from datetime import datetime, timedelta

from product import cnf
from product.db.repository import AlertStateRepository
from product.models.state import AlertState


class StateService:
    def __init__(self, repository: AlertStateRepository) -> None:
        self.repository = repository

    def get_active_state(self, insight_id: str) -> AlertState | None:
        return self.repository.get_active_state(insight_id)

    def get_last_state(self, insight_id: str) -> AlertState | None:
        return self.repository.get_last_state(insight_id)

    def create_state(self, values: dict) -> int:
        return self.repository.create_state(values)

    def activate_existing_state(self, state_id: int, event_time: datetime) -> dict:
        return self.repository.activate_existing_state(state_id, event_time)

    def decrease_event_balance(self, state_id: int, event_time: datetime) -> dict:
        flap_reopen_until = event_time + timedelta(hours=cnf.FLAP_REOPEN_HOURS)
        return self.repository.decrease_event_balance(state_id, event_time, flap_reopen_until)

    def mark_state_cooldown_night(self, state_id: int) -> None:
        self.repository.mark_state_cooldown_night(state_id)

    def mark_state_closed(self, state_id: int) -> None:
        self.repository.mark_state_closed(state_id)

    def append_audit_event(self, values: dict) -> None:
        self.repository.append_audit_event(values)

    def insert_incident_history(self, values: dict) -> int:
        return self.repository.insert_incident_history(values)

    def close_incident_history(self, insight_id: str, jira_issue_key: str, close_reason: str) -> None:
        self.repository.close_incident_history(insight_id, jira_issue_key, close_reason)
