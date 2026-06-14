"""Application timezone helpers (Eastern Time by default)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings


def app_tz() -> ZoneInfo:
    return ZoneInfo(settings.APP_TIMEZONE)


def now() -> datetime:
    """Current time in the application timezone (America/New_York by default)."""
    return datetime.now(app_tz())


def to_local_date(value: datetime | date) -> date:
    """Calendar date in the application timezone."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=app_tz())
        return value.astimezone(app_tz()).date()
    return value


def calendar_day_bounds(value: datetime | date | None = None) -> tuple[datetime, datetime]:
    """
    Application-timezone calendar day as [start, end) with tz-aware datetimes.

    Used for daily LLM caps, sentiment rollups, and alert windows.
    """
    tz = app_tz()
    local_date = to_local_date(value if value is not None else now())
    start = datetime.combine(local_date, datetime.min.time(), tzinfo=tz)
    return start, start + timedelta(days=1)


def start_of_local_day(value: datetime) -> datetime:
    """Midnight at the start of the local calendar day containing ``value``."""
    start, _ = calendar_day_bounds(value)
    return start
