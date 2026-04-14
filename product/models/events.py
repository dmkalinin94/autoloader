from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class EventPayload:
    event: str
    insight_id: str
    groups: str
    trigger_time_raw: str
    trigger_name: str
    message: str


@dataclass(slots=True)
class ParsedEvent:
    event_value: int
    insight_id: str
    groups: str
    trigger_time: datetime
    trigger_name: str
    message: str
