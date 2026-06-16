"""
Single source of truth for application time (US Eastern by default).

All pipeline logic, DB writes, daily caps, and sentiment calendars use this module.
External APIs that expect UTC (e.g. NewsAPI) should use ``to_utc`` / ``format_newsapi_datetime``
at the boundary only — never mix UTC into business logic elsewhere.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings

# NewsAPI and most news feeds publish/compare in UTC.
_EXTERNAL_API_TZ = ZoneInfo("UTC")


def app_tz() -> ZoneInfo:
    return ZoneInfo(settings.APP_TIMEZONE)


def now() -> datetime:
    """Current time in the application timezone (America/New_York by default)."""
    return datetime.now(app_tz())


def to_app_timezone(value: datetime) -> datetime:
    """Normalize any aware or naive datetime to the application timezone."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=_EXTERNAL_API_TZ)
    return value.astimezone(app_tz())


def to_utc(value: datetime) -> datetime:
    """Convert application (or any aware) time to UTC — for external API calls only."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=app_tz())
    return value.astimezone(_EXTERNAL_API_TZ)


def parse_external_datetime(value: str | None) -> datetime:
    """
    Parse an ISO datetime from an external feed (UTC) and return app-local time.

    Used for NewsAPI ``publishedAt`` and similar fields before DB storage.
    """
    if not value:
        return now()
    from dateutil import parser as date_parser

    parsed = date_parser.isoparse(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_EXTERNAL_API_TZ)
    return parsed.astimezone(app_tz())


def format_newsapi_datetime(value: datetime) -> str:
    """ISO string in UTC for NewsAPI ``from`` / ``to`` query params."""
    return to_utc(value).strftime("%Y-%m-%dT%H:%M:%S")


def to_local_date(value: datetime | date) -> date:
    """Calendar date in the application timezone."""
    if isinstance(value, datetime):
        return to_app_timezone(value).date()
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
