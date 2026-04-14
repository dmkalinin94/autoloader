from datetime import datetime


def should_reuse_night_incident(
    now_dt: datetime,
    is_night: bool,
    last_event0_at: datetime | None,
    flap_reopen_until: datetime | None,
) -> bool:
    if not is_night:
        return False
    if last_event0_at is None:
        return False
    if flap_reopen_until is None:
        return False
    return now_dt <= flap_reopen_until
