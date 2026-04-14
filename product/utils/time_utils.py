from datetime import datetime
from zoneinfo import ZoneInfo


def parse_zabbix_time(raw_value: str, tz_name: str) -> datetime:
    dt = datetime.strptime(raw_value, "%Y.%m.%d %H:%M:%S")
    return dt.replace(tzinfo=ZoneInfo(tz_name))


def is_night_window(dt: datetime, start_hour: int = 21, end_hour: int = 9) -> bool:
    hour = dt.hour
    return hour >= start_hour or hour < end_hour
