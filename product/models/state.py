from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class AlertState:
    id: int
    insight_id: str
    short_name: str | None
    full_name: str | None
    trigger_name: str | None
    recipients: list[str] | None
    ktalk_room_id: str | None
    ktalk_thread_id: str | None
    jira_issue_key: str | None
    event_balance: int
    status: str
    last_event1_at: datetime | None
    last_event0_at: datetime | None
    flap_reopen_until: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: dict | None) -> "AlertState | None":
        if row is None:
            return None
        return cls(
            id=row["id"],
            insight_id=row["insight_id"],
            short_name=row.get("short_name"),
            full_name=row.get("full_name"),
            trigger_name=row.get("trigger_name"),
            recipients=row.get("recipients"),
            ktalk_room_id=row.get("ktalk_room_id"),
            ktalk_thread_id=row.get("ktalk_thread_id"),
            jira_issue_key=row.get("jira_issue_key"),
            event_balance=row.get("event_balance", 0),
            status=row.get("status", "active"),
            last_event1_at=row.get("last_event1_at"),
            last_event0_at=row.get("last_event0_at"),
            flap_reopen_until=row.get("flap_reopen_until"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
